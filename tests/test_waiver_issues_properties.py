"""Property-based tests for tools/waiver_issues.py, offline.

Invariants, each for every input Hypothesis draws:

1. Exact report: `check` returns one line for each closed issue a governing
   record cites, and that line names exactly the modules whose governing
   records cite it. So it reports nothing exactly when every governing record
   cites an open issue, and a module that cites only open issues appears in no
   line.
2. Governing records: a `pending` record replaces an `active` record with the
   same fingerprint. With different fingerprints both govern. A lone record
   governs.
3. One question each: every issue a governing record cites is asked about
   exactly once, however many modules cite it, and no other issue is asked
   about.
4. Fail closed: no answer passes unless it is a JSON object with state `open`
   and no `pull_request` key.
5. Determinism: the report doesn't depend on the ledger's module order.
6. Totality: `check` returns a list of strings, and never raises, on any
   JSON-shaped ledger.
"""

from __future__ import annotations

import importlib.util
import sys
from collections import defaultdict
from pathlib import Path

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, given, settings, strategies as st  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sc = _load("source_conflicts", TOOLS / "source_conflicts.py")
wi = _load("waiver_issues", TOOLS / "waiver_issues.py")
PROPERTY = settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
ISSUES = "https://github.com/TheAxiomFoundation/rulespec-us/issues/"


def url(number: int) -> str:
    return f"{ISSUES}{number}"


def api_path(number: int) -> str:
    return f"/repos/TheAxiomFoundation/rulespec-us/issues/{number}"


def record(number: int, fingerprint: str) -> dict:
    return {"fingerprint": fingerprint, "owner": "@PavelMakarchuk", "issue": url(number), "expires": "2026-12-21"}


def ledger_of(entries: dict) -> dict:
    return {"validate_failures": entries}


def stub(states: dict[int, str]):
    asked: list[str] = []

    def get(path: str) -> dict:
        asked.append(path)
        return {"state": states[int(path.rsplit("/", 1)[1])]}

    get.asked = asked
    return get


def number_of(entry_record: dict) -> int:
    return int(entry_record["issue"].rsplit("/", 1)[1])


def governing_numbers(entry: dict) -> set[int]:
    """Invariant 2, stated apart from the tool's own code."""

    active, pending = entry.get("active"), entry.get("pending")
    if active and pending and active["fingerprint"] == pending["fingerprint"]:
        return {number_of(pending)}
    return {number_of(item) for item in (active, pending) if item}


def expected_report(entries: dict, states: dict[int, str]) -> list[str]:
    citing: dict[int, set[str]] = defaultdict(set)
    for module, entry in entries.items():
        for number in governing_numbers(entry):
            citing[number].add(module)
    return sorted(
        f"{url(number)} is 'closed', not open; cited by {len(modules)}: " + ", ".join(sorted(modules))
        for number, modules in citing.items()
        if states[number] != "open"
    )


ISSUE_NUMBERS = st.integers(1, 6)
RECORDS = st.builds(record, ISSUE_NUMBERS, st.sampled_from(["sha256:" + digit * 64 for digit in "ab"]))
ENTRIES = st.dictionaries(
    st.from_regex(r"[a-z]{1,4}\.yaml", fullmatch=True),
    st.fixed_dictionaries({}, optional={"active": RECORDS, "pending": RECORDS}).filter(bool),
    max_size=8,
)
WORLD = st.dictionaries(ISSUE_NUMBERS, st.sampled_from(["open", "closed"]), min_size=6)
JSONISH = st.recursive(
    st.none() | st.booleans() | st.integers(-5, 5) | st.text(max_size=8),
    lambda inner: st.lists(inner, max_size=3) | st.dictionaries(st.text(max_size=8), inner, max_size=3),
    max_leaves=8,
)
FIELDS = st.sampled_from(["validate_failures", "active", "pending", "issue", "fingerprint"])


@PROPERTY
@given(ENTRIES, WORLD)
def test_the_report_is_exact(entries, states):
    problems = wi.check(ledger_of(entries), stub(states))
    assert problems == expected_report(entries, states)
    every_open = all(states[number] == "open" for entry in entries.values() for number in governing_numbers(entry))
    assert (problems == []) == every_open


@PROPERTY
@given(ENTRIES, WORLD)
def test_one_question_each(entries, states):
    get = stub(states)
    wi.check(ledger_of(entries), get)
    wanted = {api_path(number) for entry in entries.values() for number in governing_numbers(entry)}
    assert sorted(get.asked) == sorted(wanted)


@PROPERTY
@given(JSONISH)
def test_only_an_open_issue_passes(answer):
    passes = wi.issue_problem(url(1), lambda path: answer) is None
    assert passes == (isinstance(answer, dict) and answer.get("state") == "open" and "pull_request" not in answer)


@PROPERTY
@given(st.fixed_dictionaries({"state": JSONISH}, optional={"pull_request": JSONISH}))
def test_only_the_state_open_passes_on_an_object(answer):
    passes = wi.issue_problem(url(1), lambda path: answer) is None
    assert passes == (answer["state"] == "open" and "pull_request" not in answer)


@PROPERTY
@given(ENTRIES, WORLD, st.randoms(use_true_random=False))
def test_order_does_not_change_the_report(entries, states, rng):
    shuffled = list(entries.items())
    rng.shuffle(shuffled)
    assert wi.check(ledger_of(dict(shuffled)), stub(states)) == wi.check(ledger_of(entries), stub(states))


@PROPERTY
@given(
    st.one_of(
        JSONISH,
        st.dictionaries(FIELDS, JSONISH, max_size=4),
        st.builds(
            ledger_of,
            st.dictionaries(st.text(max_size=4), st.dictionaries(FIELDS, JSONISH, max_size=3) | JSONISH, max_size=4),
        ),
    )
)
def test_check_is_total(ledger):
    problems = wi.check(ledger, lambda path: {"state": "open"})
    assert isinstance(problems, list) and all(isinstance(problem, str) for problem in problems)
