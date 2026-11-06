"""Plan and report the event-driven validation drift run (axiom-encode#2094).

The drift run replaces the scheduled full validation of every file
(rulespec-us#1274). It runs at most once a day, and only when something that
can change validation results changed since the last drift run:

- an axiom-encode main merge that declares ``Validation effect: loosen`` or
  ``tighten`` (encoder pull requests must declare it, axiom-encode#2101);
- the rules-engine pin or the corpus pin or release.

Scope:

- ``tighten``, an undeclared or invalid effect, an engine pin, a corpus pin,
  no previous state, or 7 days since the last full run: every file (full).
  A corpus pin runs every file because the workflow cannot yet derive which
  files cite the changed provisions.
- ``loosen`` only: the waived files (keys of known-validation-gaps.yaml), so
  that waivers that are no longer needed show up.
- ``none`` only, or nothing changed: no run.

Report: each failing file opens or updates one issue titled
``Validation drift: <path>`` with the ``validation-drift`` and
``re-encode-queue`` labels, which is the re-encode queue entry. A file in
scope that passes closes its open drift issue. There is no single
red-forever issue.

``plan`` and ``report`` are pure functions over JSON and text; the workflow
does every GitHub call.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath

STATE_SCHEMA = "rulespec-us/validation-drift-state/v1"
FULL_INTERVAL = timedelta(days=7)
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
    for key in ("encoder_main", "axiom_rules_engine_ref", "axiom_corpus_ref"):
        if not isinstance(state.get(key), str) or not _COMMIT_RE.fullmatch(state[key]):
            return None
    if not isinstance(state.get("corpus_release"), list):
        return None
    if _parse_time(state.get("last_full_at")) is None:
        return None
    return state


def waived_files(ledger: object, repo: Path | None = None) -> list[str]:
    records = ledger.get("validate_failures") if isinstance(ledger, dict) else None
    if not isinstance(records, dict):
        raise ValueError("known-validation-gaps.yaml has no validate_failures mapping")
    files = []
    for path in records:
        if not isinstance(path, str) or not _MODULE_RE.fullmatch(path):
            raise ValueError(f"invalid waived path: {path!r}")
        if any(part in {"", ".", ".."} for part in PurePosixPath(path).parts):
            raise ValueError(f"invalid waived path: {path!r}")
        if repo is None or (repo / path).is_file():
            files.append(path)
    return sorted(files)


def plan(
    *,
    previous: object,
    current: dict,
    encoder_prs: list[dict] | None,
    ledger: object,
    now: datetime,
    force_full: bool = False,
    repo: Path | None = None,
) -> dict:
    """Return {scope, reasons, targets, state} for one drift run."""

    state = valid_state(previous)
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
        if (
            state["axiom_corpus_ref"] != current["axiom_corpus_ref"]
            or state["corpus_release"] != current["corpus_release"]
        ):
            full = True
            reasons.append(
                "corpus pin or release changed (citing files are not derivable yet)"
            )
    loosen = False
    if state is not None and state["encoder_main"] != current["encoder_main"]:
        if encoder_prs is None:
            full = True
            reasons.append("encoder merges could not be listed")
        else:
            for pr in sorted(encoder_prs, key=lambda item: item.get("number", 0)):
                effect = declared_effect(pr.get("body"))
                label = f"axiom-encode#{pr.get('number')}"
                if effect in (None, "tighten"):
                    full = True
                    reasons.append(f"{label}: {effect or 'undeclared'} validation effect")
                elif effect == "loosen":
                    loosen = True
                    reasons.append(f"{label}: loosen")
    new_state = {
        "schema": STATE_SCHEMA,
        **{
            key: current[key]
            for key in (
                "encoder_main",
                "axiom_rules_engine_ref",
                "axiom_corpus_ref",
                "corpus_release",
            )
        },
        "last_full_at": (
            now.isoformat()
            if full
            else (state["last_full_at"] if state else now.isoformat())
        ),
    }
    if full:
        return {"scope": "full", "reasons": reasons, "targets": [], "state": new_state}
    if loosen:
        targets = waived_files(ledger, repo)
        if targets:
            return {
                "scope": "waived",
                "reasons": reasons,
                "targets": targets,
                "state": new_state,
            }
        reasons.append("no waived files")
    return {
        "scope": "skip",
        "reasons": reasons or ["nothing that affects validation changed"],
        "targets": [],
        "state": new_state,
    }


def failing_files(log: str) -> list[str]:
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
            if match and _MODULE_RE.fullmatch(match.group(1)):
                failed.add(match.group(1))
                continue
            collecting = False
    return sorted(failed)


def report(
    *,
    plan_result: dict,
    log: str,
    validate_result: str,
    open_issue_paths: list[str],
    all_files: list[str],
    run_url: str,
) -> dict:
    """Return the issue actions for one finished drift run."""

    failed = failing_files(log)
    if validate_result not in ("success", "failure"):
        return {"error": f"validation did not finish ({validate_result})"}
    if validate_result == "failure" and not failed:
        return {"error": "validation failed without per-file results; read the run"}
    scope = plan_result["scope"]
    in_scope = set(all_files) if scope == "full" else set(plan_result["targets"])
    reasons = "; ".join(plan_result.get("reasons", [])) or "scheduled"
    opened = [
        {
            "path": path,
            "title": ISSUE_TITLE_PREFIX + path,
            "body": (
                f"The validation drift run failed for `{path}`.\n\n"
                f"- Run: {run_url}\n- Scope: {scope} ({reasons})\n\n"
                "This file entered the re-encode queue (label `re-encode-queue`). "
                "A drift run that passes this file closes this issue."
            ),
        }
        for path in failed
    ]
    closed = sorted(
        path for path in open_issue_paths if path in in_scope and path not in failed
    )
    return {"open": opened, "close": closed, "labels": list(ISSUE_LABELS)}


def _load_json(path: str | None) -> object:
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main(argv: list[str] | None = None) -> int:
    import tomllib

    import yaml

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
    report_parser.add_argument("--repo", type=Path, default=Path("."))
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
            ledger=yaml.safe_load((repo / "known-validation-gaps.yaml").read_text()),
            now=datetime.now().astimezone(),
            force_full=args.force_full,
            repo=repo,
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
        all_files = sorted(
            path.relative_to(args.repo).as_posix()
            for root in args.repo.iterdir()
            if root.is_dir() and re.fullmatch(r"[a-z]{2}(?:-[a-z0-9]+)*", root.name)
            for path in root.rglob("*.y*ml")
            if not path.name.endswith((".test.yaml", ".test.yml"))
        )
        result = report(
            plan_result=plan_result,
            log=args.log.read_text(encoding="utf-8", errors="replace"),
            validate_result=args.validate_result,
            open_issue_paths=open_paths,
            all_files=all_files,
            run_url=args.run_url,
        )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "state"}, indent=2)[:4000])
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
