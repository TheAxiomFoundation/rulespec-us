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
- In ``pinned`` verifier mode, encoder main merges change nothing; a change of
  the pin (``axiom_encode_ref``) or of the mode runs every file.

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
# The shared validator's step that prints the per-file failure summary, and
# its aggregate job, whose failure only mirrors the matrix legs.
VALIDATION_STEP = "Validate RuleSpec YAML"
AGGREGATE_JOB = "validate / validate"
LEG_PREFIX = "validate / validate ("
STATE_KEYS = (
    "encoder_main",
    "axiom_encode_ref",
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
    if state.get("encoder_verifier") not in ("pinned", "main"):
        return None
    if _parse_time(state.get("last_full_at")) is None:
        return None
    if not isinstance(state.get("pending_full", False), bool):
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
        if state.get("pending_full"):
            full = True
            reasons.append("the last run left failing files without issues")
        last_full = _parse_time(state["last_full_at"])
        if now - last_full >= FULL_INTERVAL:
            full = True
            reasons.append(f"weekly full run (last full run {state['last_full_at']})")
        if state["encoder_verifier"] != current["encoder_verifier"]:
            full = True
            reasons.append("encoder verifier mode changed")
        if state["axiom_encode_ref"] != current["axiom_encode_ref"]:
            full = True
            reasons.append("encoder pin (producer floor) changed")
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
    # In pinned mode the verifier is the pin, which the check above covers;
    # encoder main merges cannot change its results.
    if (
        state is not None
        and current["encoder_verifier"] == "main"
        and state["encoder_main"] != current["encoder_main"]
    ):
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
        **{
            key: current[key]
            for key in (*STATE_KEYS, "corpus_release", "encoder_verifier")
        },
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

    return sorted(set(_failure_summary(log, workspace)[0]))


def _failure_summary(log: str, workspace: str = "") -> tuple[list[str], int]:
    """Return the listed failing files and the counts the summaries declare."""

    failed: list[str] = []
    declared = 0
    collecting = False
    for raw in log.splitlines():
        line = _LOG_PREFIX_RE.sub("", raw, count=1).rstrip()
        header = re.search(r"(\d+) of \d+ file\(s\) failed:$", line)
        if header:
            declared += int(header.group(1))
            collecting = True
            continue
        if collecting:
            match = re.fullmatch(r"\s*- (\S+)", line)
            if match:
                module = _relative_module(match.group(1), workspace)
                # An unexpected path still counts, so the totals disagree.
                failed.append(module if module is not None else "")
                continue
            collecting = False
    return failed, declared


_CHUNK_RE = re.compile(r"RULESPEC_VALIDATION_CHUNK files=(\d+) status=(\d+) single=(.+)$")
_CHUNKS_RE = re.compile(r"RULESPEC_VALIDATION_CHUNKS total=(\d+)$")


def _validator_failed_file(segment: list[str], module: str, workspace: str) -> bool:
    """True when the validator reached ``module`` and reported it as failed."""

    reached = False
    for raw in segment:
        line = _LOG_PREFIX_RE.sub("", raw, count=1).rstrip()
        if line.startswith("File: "):
            reached = _relative_module(line[len("File: ") :], workspace) == module
        elif reached and line == "Result: ✗ FAILED":
            return True
    return False


def leg_failures(log: str, workspace: str = "") -> tuple[set[str], bool]:
    """Return a leg's failing files and whether every failed chunk is explained.

    The shared validator ends each worker's log with a chunk result line.
    A failed chunk is explained by its file (a one-file chunk) or by a
    summary that lists exactly the declared number of files. A leg with no
    chunk lines, or with a failed chunk that is not explained, is not.
    """

    failed: set[str] = set()
    segment: list[str] = []
    chunks = 0
    totals: list[int] = []
    explained = True
    failed_chunks = 0
    for raw in log.splitlines():
        line = _LOG_PREFIX_RE.sub("", raw, count=1).rstrip()
        total = _CHUNKS_RE.search(line)
        if total:
            totals.append(int(total.group(1)))
            continue
        match = _CHUNK_RE.search(line)
        if not match:
            segment.append(raw)
            continue
        chunks += 1
        files, status, single = int(match.group(1)), int(match.group(2)), match.group(3)
        if status != 0:
            failed_chunks += 1
            listed, declared = _failure_summary("\n".join(segment), workspace)
            module = _relative_module(single, workspace) if single != "-" else None
            # A one-file chunk names its file only when the validator reached
            # it; a setup failure (engine, supervisor) blames no file.
            if (
                files == 1
                and module is not None
                and _validator_failed_file(segment, module, workspace)
            ):
                failed.add(module)
            elif listed and "" not in listed and len(listed) == declared:
                failed.update(listed)
            else:
                explained = False
        segment = []
    # Every chunk line must be present: a lost line would merge its chunk
    # into the next one and could drop a failure.
    if chunks == 0 or failed_chunks == 0 or totals != [chunks]:
        explained = False
    return failed, explained


def report(
    *,
    plan_result: dict,
    jobs: list[dict],
    validate_result: str,
    open_issue_paths: list[str],
    run_url: str,
    workspace: str = "",
) -> dict:
    """Return the issue actions for one finished drift run.

    ``jobs`` holds each finished validate job's ``conclusion`` and ``log``.
    A job that failed without a per-file summary (a timeout, a guard or
    audit failure, a crash) makes the whole report an error, so the state
    does not advance and the next run reports again.
    """

    if validate_result not in ("success", "failure"):
        return {"error": f"validation did not finish ({validate_result})"}
    failed: set[str] = set()
    unexplained = []
    for job in jobs:
        name = str(job.get("name", "validate"))
        conclusion = job.get("conclusion")
        if name == AGGREGATE_JOB:
            continue
        leg = name.startswith(LEG_PREFIX)
        if conclusion == "success" or (conclusion == "skipped" and not leg):
            continue
        # A leg is explained only by its validation step; a later step
        # (companion tests, proofs, money atoms) failing stops the report
        # with an error naming the leg, so a person looks at the run.
        leg_failed, explained = leg_failures(str(job.get("log", "")), workspace)
        failed.update(leg_failed)
        if not (
            leg
            and conclusion == "failure"
            and explained
            and set(job.get("failed_steps") or []) == {VALIDATION_STEP}
        ):
            unexplained.append(name)
    if unexplained:
        return {
            "error": "validation failed without per-file results in: "
            + ", ".join(sorted(unexplained))
        }
    if validate_result == "failure" and not failed:
        return {"error": "validation failed without per-file results; read the run"}
    reasons = "; ".join(plan_result.get("reasons", [])) or "scheduled"
    known = set(open_issue_paths)
    new = sorted(path for path in failed if path not in known)
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
    plan_parser.add_argument("--encoder-verifier", choices=("pinned", "main"), required=True)
    plan_parser.add_argument("--encoder-prs")
    plan_parser.add_argument("--force-full", action="store_true")
    plan_parser.add_argument("--repo", type=Path, default=Path("."))
    plan_parser.add_argument("--output", type=Path, required=True)
    report_parser = sub.add_parser("report")
    report_parser.add_argument("--plan", required=True)
    report_parser.add_argument(
        "--jobs", required=True, help="JSON list of {name, conclusion, log_file}"
    )
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
            "encoder_verifier": args.encoder_verifier,
            "axiom_encode_ref": pins["axiom_encode_ref"],
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
        listed = _load_json(args.jobs)
        jobs = [
            {
                "name": item.get("name"),
                "conclusion": item.get("conclusion"),
                "log": Path(item["log_file"]).read_text(
                    encoding="utf-8", errors="replace"
                ),
            }
            for item in (listed if isinstance(listed, list) else [])
            if isinstance(item, dict) and isinstance(item.get("log_file"), str)
        ]
        result = report(
            plan_result=plan_result,
            jobs=jobs,
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
