"""Tests for tools/waiver_issues.py, offline: GitHub's answers are stubs.

Invariants, each for every input Hypothesis draws:

1. Exactness: `check` reports nothing exactly when every module's current
   record cites an issue GitHub calls open.
2. Coverage: every module that cites an issue that isn't open appears in that
   issue's report, and no module that cites an open issue appears in any.
3. Current record: a module's `pending` record decides, whatever its `active`
   record cites; the `active` record decides only when no `pending` exists.
4. One question each: every cited issue is asked about exactly once, however
   many modules cite it, and no other issue is asked about.
5. Fail closed: no answer passes unless it is a JSON object with state `open`
   and no `pull_request` key.
6. Determinism: the report doesn't depend on the ledger's module order.
7. Totality: `check` returns a list of strings, and never raises, on any
   JSON-shaped ledger.
8. Differential (when axiom-encode is importable): the tool and the encoder's
   ISSUE_RE accept the same URLs.
"""

from __future__ import annotations

import email.message
import http.server
import importlib.util
import re
import sys
import threading
import urllib.error
from pathlib import Path

import pytest
import yaml

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, given, settings, strategies as st  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "waiver-issues.yml"


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


def record(number: int) -> dict:
    return {
        "fingerprint": "sha256:" + "0" * 64,
        "owner": "@PavelMakarchuk",
        "issue": url(number),
        "expires": "2026-12-21",
    }


def ledger_of(entries: dict) -> dict:
    return {"validate_failures": entries}


def stub(states: dict[int, str]):
    """A GitHub that holds these issues and counts the questions it gets."""

    asked: list[str] = []

    def get(path: str) -> dict:
        asked.append(path)
        number = int(path.rsplit("/", 1)[1])
        return {"state": states[number]}

    get.asked = asked
    return get


def http_error(code: int, headers: dict | None = None) -> urllib.error.HTTPError:
    message = email.message.Message()
    for key, value in (headers or {}).items():
        message[key] = value
    return urllib.error.HTTPError("https://api.github.com/x", code, "reason", message, None)


def raising(error: Exception):
    def get(path: str) -> dict:
        raise error

    return get


def test_open_issues_pass():
    ledger = ledger_of({"a.yaml": {"active": record(1)}, "b.yaml": {"pending": record(2)}})
    assert wi.check(ledger, stub({1: "open", 2: "open"})) == []


def test_closed_issue_names_the_issue_and_every_citing_module():
    ledger = ledger_of({"b.yaml": {"active": record(1)}, "a.yaml": {"active": record(1)}, "c.yaml": {"active": record(2)}})
    assert wi.check(ledger, stub({1: "closed", 2: "open"})) == [
        f"{url(1)} is 'closed', not open; cited by 2: a.yaml, b.yaml"
    ]


def test_a_re_point_between_stage_and_consume_passes():
    entry = {"active": record(1), "pending": record(2)}
    assert wi.check(ledger_of({"a.yaml": entry}), stub({1: "closed", 2: "open"})) == []


def test_a_pending_record_that_cites_a_closed_issue_fails():
    entry = {"active": record(1), "pending": record(2)}
    assert wi.check(ledger_of({"a.yaml": entry}), stub({1: "open", 2: "closed"})) == [
        f"{url(2)} is 'closed', not open; cited by 1: a.yaml"
    ]


def test_a_pull_request_is_not_an_issue():
    def get(path: str) -> dict:
        return {"state": "open", "pull_request": {"url": "x"}}

    assert wi.issue_problem(url(1), get) == f"{url(1)} is a pull request, not an issue"


@pytest.mark.parametrize(
    "error, expected",
    [
        (http_error(404), "GitHub answered 404"),
        (http_error(410), "GitHub answered 410"),
        (http_error(500), "GitHub answered 500"),
        (http_error(301), "moved: GitHub redirected the request (301)"),
        (http_error(403, {"x-ratelimit-remaining": "0"}), "rate limit is used up"),
        (http_error(403, {"x-ratelimit-remaining": "9"}), "GitHub answered 403"),
        (urllib.error.URLError("no route"), "no route"),
        (TimeoutError("timed out"), "timed out"),
        (ValueError("not JSON"), "not JSON"),
    ],
)
def test_an_unreadable_issue_fails(error, expected):
    problem = wi.issue_problem(url(1), raising(error))
    assert problem is not None and expected in problem


def test_the_real_fetcher_reports_a_moved_issue():
    """A transferred issue answers 301; the tool must not read wherever it points."""

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(301 if self.path.endswith("/1") else 200)
            self.send_header("Location", "/repos/TheAxiomFoundation/rulespec-us/issues/2")
            self.end_headers()
            if not self.path.endswith("/1"):
                self.wfile.write(b'{"state": "open"}')

        def log_message(self, *args) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        get = sc.github_api(base_url=f"http://127.0.0.1:{server.server_port}")
        assert wi.issue_problem(url(2), get) is None
        assert wi.issue_problem(url(1), get) == f"{url(1)} moved: GitHub redirected the request (301)"
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize(
    "ledger",
    [
        None,
        [],
        {},
        {"validate_failures": None},
        {"validate_failures": []},
    ],
)
def test_a_ledger_without_the_mapping_fails(ledger):
    assert wi.check(ledger, stub({})) == ["known-validation-gaps.yaml has no validate_failures mapping"]


@pytest.mark.parametrize(
    "entry",
    [
        None,
        {},
        {"active": None},
        {"active": {}},
        {"active": record(1), "pending": None},
        {"active": {"issue": 1248}},
        {"active": {"issue": "https://github.com/TheAxiomFoundation/rulespec-us/pull/1"}},
        {"active": {"issue": "https://github.com/someone-else/rulespec-us/issues/1"}},
        {"active": {"issue": "https://github.com/TheAxiomFoundation/../issues/1"}},
        {"active": {"issue": url(1) + "\n"}},
        {"active": {"issue": url(1) + "#comment"}},
    ],
)
def test_a_record_without_an_issue_url_fails_and_asks_nothing(entry):
    get = stub({1: "open"})
    problems = wi.check(ledger_of({"a.yaml": entry}), get)
    assert len(problems) == 1 and problems[0].startswith("a.yaml: ")
    assert get.asked == []


def test_main_exit_codes(tmp_path, capsys):
    (tmp_path / wi.LEDGER).write_text(yaml.safe_dump(ledger_of({"a.yaml": {"active": record(1)}})))
    assert wi.main(["--root", str(tmp_path)], stub({1: "open"})) == 0
    assert "1 waived modules cite 1 issues, all open" in capsys.readouterr().out
    assert wi.main(["--root", str(tmp_path)], stub({1: "closed"})) == 1
    assert "a.yaml" in capsys.readouterr().out


def test_every_module_in_the_real_ledger_cites_a_well_formed_issue():
    text = (REPO_ROOT / wi.LEDGER).read_text(encoding="utf-8")
    ledger = yaml.safe_load(text)
    cited, problems = wi.citations(ledger)
    assert problems == []
    assert sorted(module for modules in cited.values() for module in modules) == sorted(ledger["validate_failures"])
    # An independent reading: every URL the tool cites sits on an issue line.
    assert set(cited) <= set(re.findall(r'^\s+issue: "([^"]+)"$', text, re.M))


def test_workflow_stays_read_only_and_watches_the_ledger():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML reads the bare key `on` as true.
    triggers = workflow[True]
    assert set(triggers) == {"pull_request", "push", "schedule", "workflow_dispatch"}
    for event in ("pull_request", "push"):
        assert {"known-validation-gaps.yaml", "tools/waiver_issues.py", "tools/source_conflicts.py"} <= set(
            triggers[event]["paths"]
        )
    assert workflow["permissions"] == {"contents": "read"}
    jobs = workflow["jobs"]
    assert jobs["verify"]["permissions"] == {"contents": "read", "issues": "read"}
    assert jobs["alarm"]["permissions"] == {"issues": "write"}
    assert "schedule" in jobs["alarm"]["if"] and "pull_request" not in jobs["alarm"]["if"]
    checkout = next(step for step in jobs["verify"]["steps"] if "checkout" in step.get("uses", ""))
    assert checkout["with"]["persist-credentials"] is False


ISSUE_NUMBERS = st.integers(1, 6)
STATES = st.sampled_from(["open", "closed"])
ENTRIES = st.dictionaries(
    st.from_regex(r"[a-z]{1,4}\.yaml", fullmatch=True),
    st.tuples(st.none() | ISSUE_NUMBERS, st.none() | ISSUE_NUMBERS)
    .filter(lambda pair: pair != (None, None))
    .map(lambda pair: {k: record(n) for k, n in zip(("active", "pending"), pair) if n is not None}),
    max_size=8,
)
WORLD = st.dictionaries(ISSUE_NUMBERS, STATES, min_size=6)
JSONISH = st.recursive(
    st.none() | st.booleans() | st.integers(-5, 5) | st.text(max_size=8),
    lambda inner: st.lists(inner, max_size=3) | st.dictionaries(st.text(max_size=8), inner, max_size=3),
    max_leaves=8,
)
FIELDS = st.sampled_from(["validate_failures", "active", "pending", "issue"])


def current_number(entry: dict) -> int:
    return int((entry["pending"] if "pending" in entry else entry["active"])["issue"].rsplit("/", 1)[1])


@PROPERTY
@given(ENTRIES, WORLD)
def test_exact_and_covering(entries, states):
    problems = wi.check(ledger_of(entries), stub(states))
    current = {module: current_number(entry) for module, entry in entries.items()}
    bad = {number for number in current.values() if states[number] != "open"}
    assert (problems == []) == (bad == set())  # Invariant 1
    assert len(problems) == len(bad)
    for module, number in current.items():  # Invariants 2 and 3
        lines = [line for line in problems if line.startswith(f"{url(number)} ")]
        if number in bad:
            assert module in lines[0].split("cited by ", 1)[1].split(": ", 1)[1].split(", ")
        else:
            assert lines == []


@PROPERTY
@given(ENTRIES, WORLD)
def test_one_question_each(entries, states):
    get = stub(states)
    wi.check(ledger_of(entries), get)
    assert sorted(get.asked) == sorted({api_path(current_number(entry)) for entry in entries.values()})


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
@given(st.one_of(JSONISH, st.dictionaries(FIELDS, JSONISH, max_size=4), st.builds(ledger_of, st.dictionaries(st.text(max_size=4), st.dictionaries(FIELDS, JSONISH, max_size=3) | JSONISH, max_size=4))))
def test_check_is_total(ledger):
    problems = wi.check(ledger, lambda path: {"state": "open"})
    assert isinstance(problems, list) and all(isinstance(problem, str) for problem in problems)


@PROPERTY
@given(
    st.one_of(
        st.builds(url, st.integers(1, 10**6)),
        st.from_regex(r"https://github\.com/TheAxiomFoundation/[A-Za-z0-9_.-]{1,8}/issues/[0-9]{1,4}", fullmatch=True),
        st.text(max_size=20),
        st.just(ISSUES + "0"),
        st.just(ISSUES + "01"),
    )
)
def test_tool_and_encoder_accept_the_same_urls(candidate):
    waivers = pytest.importorskip("axiom_encode.validation_waivers")
    assert (wi.ISSUE_RE.fullmatch(candidate) is not None) == (waivers.ISSUE_RE.fullmatch(candidate) is not None)
