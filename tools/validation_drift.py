"""Plan and report the event-driven validation drift run (axiom-encode#2094).

The drift run replaces the scheduled full validation of every file
(rulespec-us#1274). It runs at most once a day, and only when something that
can change validation results changed since the last drift run:

- an axiom-encode main merge that declares ``Validation effect: loosen`` or
  ``tighten`` (encoder pull requests must declare it, axiom-encode#2101);
- the rules-engine pin or the corpus pin or release.

Scope:

- ``tighten`` or ``loosen``, an undeclared or invalid effect, an encoder
  commit without a merged PR, an engine, composer or corpus pin or release,
  no previous state, or 7 days since the last full run: every file (full).
  A corpus pin runs every file because the workflow cannot yet derive which
  files cite the changed provisions. ``loosen`` also runs every file: the
  shared validator skips waived files, so a waived-only run would check
  nothing; scoping it needs a validator mode that validates waived files.
- ``none`` only, or nothing changed: no run.

Report: each failing file opens or updates one issue titled
``Validation drift: <path>`` with the ``validation-drift`` and
``re-encode-queue`` labels, which is the re-encode queue entry. At most
``MAX_NEW_ISSUES`` issues open per run; the rest are listed in the summary.
Issues are never closed automatically: the validator lists failures only, so
a missing failure does not prove that the file was validated. There is no
single red-forever issue.

``plan`` and ``report`` are pure functions over JSON and text; the workflow
does every GitHub call.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

STATE_SCHEMA = "rulespec-us/validation-drift-state/v1"
FULL_INTERVAL = timedelta(days=7)
MAX_NEW_ISSUES = 50
STATE_KEYS = (
    "encoder_main",
    "axiom_rules_engine_ref",
    "axiom_compose_ref",
    "axiom_corpus_ref",
)
ISSUE_TITLE_PREFIX = "Validation drift: "
ISSUE_LABELS = ("validation-drift", "re-encode-queue")
EFFECTS = ("none", "loosen", "tighten")
_EFFECT_RE = re.compile(r"^\s*validation effect\s*:\s*(\S+)\s*$", re.I | re.M)
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_MODULE_RE = re.compile(r"[a-z]{2}(?:-[a-z0-9]+)*/[^\s]+\.ya?ml")
_LOG_PREFIX_RE = re.compile(r"^.*?\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z ?")


def declared_effect(body: str | None) -> str | None:
    """Return the one declared effect of an encoder PR body, or None."""

    text = re.sub(r"<!--.*?-->", "", body or "", flags=re.S)
    effects = _EFFECT_RE.findall(text)
    if len(effects) != 1:
        return None
    effect = effects[0].strip("`*_").lower()
    return effect if effect in EFFECTS else None


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def valid_state(state: object) -> dict | None:
    """Return a previous state that this tool wrote, or None."""

    if not isinstance(state, dict) or state.get("schema") != STATE_SCHEMA:
        return None
    for key in STATE_KEYS:
        if not isinstance(state.get(key), str) or not _COMMIT_RE.fullmatch(state[key]):
            return None
    if not isinstance(state.get("corpus_release"), list):
        return None
    if _parse_time(state.get("last_full_at")) is None:
        return None
    return state


def plan(
    *,
    previous: object,
    current: dict,
    encoder_prs: list[dict] | None,
    now: datetime,
    force_full: bool = False,
) -> dict:
    """Return {scope, reasons, targets, state} for one drift run."""

    state = valid_state(previous)
    if state is not None and _parse_time(state["last_full_at"]) > now:
        state = None  # a future full run is not a state this tool wrote
    reasons: list[str] = []
    full = False
    if force_full:
        full, reasons = True, ["full run requested"]
    elif state is None:
        full, reasons = True, ["no previous drift state"]
    else:
        last_full = _parse_time(state["last_full_at"])
        if now - last_full >= FULL_INTERVAL:
            full = True
            reasons.append(f"weekly full run (last full run {state['last_full_at']})")
        if state["axiom_rules_engine_ref"] != current["axiom_rules_engine_ref"]:
            full = True
            reasons.append("rules-engine pin changed")
        if state["axiom_compose_ref"] != current["axiom_compose_ref"]:
            full = True
            reasons.append("composer pin changed")
        if (
            state["axiom_corpus_ref"] != current["axiom_corpus_ref"]
            or state["corpus_release"] != current["corpus_release"]
        ):
            full = True
            reasons.append(
                "corpus pin or release changed (citing files are not derivable yet)"
            )
    if state is not None and state["encoder_main"] != current["encoder_main"]:
        if encoder_prs is None:
            full = True
            reasons.append("encoder merges could not be listed")
        else:
            for pr in sorted(encoder_prs, key=lambda item: item.get("number") or 0):
                if pr.get("number") is None:
                    full = True
                    reasons.append(f"encoder commit {pr.get('commit')} has no merged PR")
                    continue
                effect = declared_effect(pr.get("body"))
                label = f"axiom-encode#{pr.get('number')}"
                if effect in (None, "tighten", "loosen"):
                    full = True
                    reasons.append(f"{label}: {effect or 'undeclared'} validation effect")
    new_state = {
        "schema": STATE_SCHEMA,
        **{key: current[key] for key in (*STATE_KEYS, "corpus_release")},
        "last_full_at": (
            now.isoformat()
            if full
            else (state["last_full_at"] if state else now.isoformat())
        ),
    }
    if full:
        return {"scope": "full", "reasons": reasons, "targets": [], "state": new_state}
    return {
        "scope": "skip",
        "reasons": reasons or ["nothing that affects validation changed"],
        "targets": [],
        "state": new_state,
    }


def _relative_module(path: str, workspace: str) -> str | None:
    """Map a validator path (absolute under the workspace) to a module path."""

    if workspace and path.startswith(workspace.rstrip("/") + "/"):
        path = path[len(workspace.rstrip("/")) + 1 :]
    return path if _MODULE_RE.fullmatch(path) else None


def failing_files(log: str, workspace: str = "") -> list[str]:
    """Return the files that `axiom-encode validate` listed as failed."""

    failed: set[str] = set()
    collecting = False
    for raw in log.splitlines():
        line = _LOG_PREFIX_RE.sub("", raw, count=1).rstrip()
        if re.search(r"\d+ of \d+ file\(s\) failed:$", line):
            collecting = True
            continue
        if collecting:
            match = re.fullmatch(r"\s*- (\S+)", line)
            module = _relative_module(match.group(1), workspace) if match else None
            if module is not None:
                failed.add(module)
                continue
            collecting = False
    return sorted(failed)


def report(
    *,
    plan_result: dict,
    log: str,
    validate_result: str,
    open_issue_paths: list[str],
    run_url: str,
    workspace: str = "",
) -> dict:
    """Return the issue actions for one finished drift run."""

    failed = failing_files(log, workspace)
    if validate_result not in ("success", "failure"):
        return {"error": f"validation did not finish ({validate_result})"}
    if validate_result == "failure" and not failed:
        return {"error": "validation failed without per-file results; read the run"}
    reasons = "; ".join(plan_result.get("reasons", [])) or "scheduled"
    known = set(open_issue_paths)
    new = [path for path in failed if path not in known]
    opened = [
        {
            "path": path,
            "title": ISSUE_TITLE_PREFIX + path,
            "body": (
                f"The validation drift run failed for `{path}`.\n\n"
                f"- Run: {run_url}\n- Scope: {plan_result['scope']} ({reasons})\n\n"
                "This file entered the re-encode queue (label `re-encode-queue`). "
                "Close this issue when the file is re-encoded or fixed."
            ),
        }
        for path in new[:MAX_NEW_ISSUES]
    ]
    return {
        "open": opened,
        "update": sorted(path for path in failed if path in known),
        "deferred": new[MAX_NEW_ISSUES:],
        "labels": list(ISSUE_LABELS),
    }


def _load_json(path: str | None) -> object:
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main(argv: list[str] | None = None) -> int:
    import tomllib

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("--previous-state")
    plan_parser.add_argument("--encoder-main", required=True)
    plan_parser.add_argument("--encoder-prs")
    plan_parser.add_argument("--force-full", action="store_true")
    plan_parser.add_argument("--repo", type=Path, default=Path("."))
    plan_parser.add_argument("--output", type=Path, required=True)
    report_parser = sub.add_parser("report")
    report_parser.add_argument("--plan", required=True)
    report_parser.add_argument("--log", type=Path, required=True)
    report_parser.add_argument("--validate-result", required=True)
    report_parser.add_argument("--open-issues", required=True)
    report_parser.add_argument("--run-url", required=True)
    report_parser.add_argument("--workspace", default="")
    report_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "plan":
        if not _COMMIT_RE.fullmatch(args.encoder_main):
            parser.error("--encoder-main must be a full commit")
        repo = args.repo
        pins = tomllib.loads((repo / ".axiom/workflow-toolchain.toml").read_text())[
            "workflow_toolchain"
        ]
        toolchain = tomllib.loads((repo / ".axiom/toolchain.toml").read_text())[
            "toolchain"
        ]
        current = {
            "encoder_main": args.encoder_main,
            "axiom_rules_engine_ref": pins["axiom_rules_engine_ref"],
            "axiom_compose_ref": pins["axiom_compose_ref"],
            "axiom_corpus_ref": pins["axiom_corpus_ref"],
            "corpus_release": [
                toolchain.get("axiom_corpus_release"),
                toolchain.get("axiom_corpus_release_content_sha256"),
            ],
        }
        prs = _load_json(args.encoder_prs)
        result = plan(
            previous=_load_json(args.previous_state),
            current=current,
            encoder_prs=prs if isinstance(prs, list) else None,
            now=datetime.now().astimezone(),
            force_full=args.force_full,
        )
    else:
        plan_result = _load_json(args.plan)
        if not isinstance(plan_result, dict):
            parser.error("--plan is unreadable")
        issues = _load_json(args.open_issues)
        open_paths = [
            item["title"][len(ISSUE_TITLE_PREFIX) :]
            for item in (issues if isinstance(issues, list) else [])
            if isinstance(item, dict)
            and isinstance(item.get("title"), str)
            and item["title"].startswith(ISSUE_TITLE_PREFIX)
        ]
        result = report(
            plan_result=plan_result,
            log=args.log.read_text(encoding="utf-8", errors="replace"),
            validate_result=args.validate_result,
            open_issue_paths=open_paths,
            run_url=args.run_url,
            workspace=args.workspace,
        )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "state"}, indent=2)[:4000])
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
