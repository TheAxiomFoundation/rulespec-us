"""Check that every validation waiver cites an open issue.

`known-validation-gaps.yaml` waives modules that fail validation, and each
record names an owner, an issue and an expiry date. The shared validate
workflow checks that the issue field has the shape of an issue URL. Nothing
there asks GitHub about the issue, so a waiver can go on citing an issue that
has closed.

This tool asks. It reads each module's current record, which is its `pending`
record when it has one and its `active` record otherwise, and passes only when
GitHub says the cited issue is open. `pending` wins because a re-point lands in
two steps: the stage step adds a `pending` record and leaves the old `active`
record in place, and the consume step promotes it. A module between the two
steps cites the issue its next record names.

The check needs the network and asks about state only. It can't say whether an
open issue concerns the module, and an issue closes outside any pull request.
So `.github/workflows/waiver-issues.yml` runs it on ledger changes and daily,
as a check outside the required set, and a red scheduled or main run opens one
alarm issue.

Any answer other than an open issue fails: a closed issue, a pull request, a
moved or missing issue, an exhausted rate limit, or an API outage.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.error
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import yaml

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import source_conflicts as sc  # noqa: E402 - beside this file

LEDGER = "known-validation-gaps.yaml"
# The encoder's ISSUE_RE (axiom_encode/validation_waivers.py), with the
# repository and number captured. tests/test_waiver_issues.py compares them.
ISSUE_RE = re.compile(
    rf"^https://github\.com/{sc.ORGANISATION}/"
    r"(?P<repo>[A-Za-z0-9_.-]+)/issues/(?P<number>[1-9][0-9]*)$"
)


def citations(ledger: Any) -> tuple[dict[str, list[str]], list[str]]:
    """Each cited URL with the modules whose current record cites it, and shape problems."""

    failures = ledger.get("validate_failures") if isinstance(ledger, Mapping) else None
    if not isinstance(failures, Mapping):
        return {}, [f"{LEDGER} has no validate_failures mapping"]
    cited: dict[str, list[str]] = {}
    problems: list[str] = []
    for module, entry in failures.items():
        record = entry.get("pending", entry.get("active")) if isinstance(entry, Mapping) else None
        issue = record.get("issue") if isinstance(record, Mapping) else None
        match = ISSUE_RE.fullmatch(issue) if isinstance(issue, str) else None
        if match is None or match["repo"] in {".", ".."}:
            problems.append(f"{module}: its current record cites no issue URL: {issue!r}")
        else:
            cited.setdefault(issue, []).append(str(module))
    return cited, problems


def issue_problem(url: str, get: Callable[[str], Any]) -> str | None:
    """Why `url` is not an open issue, or None when it is."""

    match = ISSUE_RE.fullmatch(url)
    if match is None:
        return f"{url} is not an issue URL"
    try:
        answer = get(f"/repos/{sc.ORGANISATION}/{match['repo']}/issues/{match['number']}")
    except urllib.error.HTTPError as exc:
        remaining = exc.headers.get("x-ratelimit-remaining") if exc.headers is not None else None
        if exc.code in (403, 429) and remaining == "0":
            return f"{url} can't be read: GitHub's API rate limit is used up"
        if 300 <= exc.code < 400:
            return f"{url} moved: GitHub redirected the request ({exc.code})"
        return f"{url} can't be read: GitHub answered {exc.code} ({exc.reason})"
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return f"{url} can't be read: {exc}"
    if not isinstance(answer, Mapping):
        return f"{url} can't be read: the answer is not a JSON object"
    if "pull_request" in answer:
        return f"{url} is a pull request, not an issue"
    state = answer.get("state")
    return None if state == "open" else f"{url} is {state!r}, not open"


def check(ledger: Any, get: Callable[[str], Any]) -> list[str]:
    """Every reason the ledger fails, sorted, each cited issue asked about once."""

    cited, problems = citations(ledger)
    for url, modules in cited.items():
        problem = issue_problem(url, get)
        if problem is not None:
            problems.append(f"{problem}; cited by {len(modules)}: " + ", ".join(sorted(modules)))
    return sorted(problems)


def main(argv: list[str] | None = None, get: Callable[[str], Any] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=TOOLS.parent)
    args = parser.parse_args(argv)
    ledger = yaml.safe_load((args.root / LEDGER).read_text(encoding="utf-8"))
    problems = check(ledger, get or sc.github_api(os.environ.get("GH_TOKEN") or None))
    for problem in problems:
        print(problem)
    if problems:
        print(f"{len(problems)} problem(s) in {LEDGER}", file=sys.stderr)
        return 1
    cited, _ = citations(ledger)
    print(f"{sum(map(len, cited.values()))} waived modules cite {len(cited)} issues, all open")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
