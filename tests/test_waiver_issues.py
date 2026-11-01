"""Example tests for tools/waiver_issues.py, offline: GitHub's answers are stubs.

These need no Hypothesis, so they run in the required Repository Checks pytest
leg. tests/test_waiver_issues_properties.py holds the property tests, which run
in .github/workflows/waiver-issues.yml.
"""

from __future__ import annotations

import email.message
import http.client
import http.server
import importlib.util
import re
import sys
import threading
import urllib.error
from pathlib import Path

import pytest
import yaml

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
ISSUES = "https://github.com/TheAxiomFoundation/rulespec-us/issues/"
OLD = "sha256:" + "a" * 64
NEW = "sha256:" + "b" * 64


def url(number: int) -> str:
    return f"{ISSUES}{number}"


def record(number: int, fingerprint: str = OLD) -> dict:
    return {
        "fingerprint": fingerprint,
        "owner": "@PavelMakarchuk",
        "issue": url(number),
        "expires": "2026-12-21",
    }


def ledger_of(entries: dict) -> dict:
    return {"validate_failures": entries}


def stub(states: dict[int, str]):
    """A GitHub that holds these issues and records the questions it gets."""

    asked: list[str] = []

    def get(path: str) -> dict:
        asked.append(path)
        return {"state": states[int(path.rsplit("/", 1)[1])]}

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
    get = stub({1: "closed", 2: "open"})
    assert wi.check(ledger_of({"a.yaml": entry}), get) == []
    assert get.asked == ["/repos/TheAxiomFoundation/rulespec-us/issues/2"]


def test_a_re_point_to_a_closed_issue_fails():
    entry = {"active": record(1), "pending": record(2)}
    assert wi.check(ledger_of({"a.yaml": entry}), stub({1: "open", 2: "closed"})) == [
        f"{url(2)} is 'closed', not open; cited by 1: a.yaml"
    ]


def test_a_pending_record_on_a_new_fingerprint_leaves_the_active_record_live():
    entry = {"active": record(1, OLD), "pending": record(2, NEW)}
    assert wi.check(ledger_of({"a.yaml": entry}), stub({1: "closed", 2: "open"})) == [
        f"{url(1)} is 'closed', not open; cited by 1: a.yaml"
    ]


def test_a_pending_record_on_a_new_fingerprint_must_also_cite_an_open_issue():
    entry = {"active": record(1, OLD), "pending": record(2, NEW)}
    assert wi.check(ledger_of({"a.yaml": entry}), stub({1: "open", 2: "closed"})) == [
        f"{url(2)} is 'closed', not open; cited by 1: a.yaml"
    ]


def test_records_without_a_fingerprint_do_not_count_as_sharing_one():
    active, pending = record(1), record(2)
    del active["fingerprint"], pending["fingerprint"]
    get = stub({1: "open", 2: "open"})
    assert wi.check(ledger_of({"a.yaml": {"active": active, "pending": pending}}), get) == []
    assert len(get.asked) == 2


def test_a_module_citing_one_issue_twice_counts_once():
    entry = {"active": record(1, OLD), "pending": record(1, NEW)}
    assert wi.check(ledger_of({"a.yaml": entry}), stub({1: "closed"})) == [
        f"{url(1)} is 'closed', not open; cited by 1: a.yaml"
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
        (http.client.IncompleteRead(b"{"), "IncompleteRead"),
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
def test_a_record_without_an_issue_url_fails(entry):
    problems = wi.check(ledger_of({"a.yaml": entry}), stub({1: "open"}))
    assert len(problems) == 1 and problems[0].startswith("a.yaml: ")


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
    assert set().union(*cited.values()) == set(ledger["validate_failures"])
    # An independent reading: every URL the tool cites sits on an issue line.
    assert set(cited) <= set(re.findall(r'^\s+issue: "([^"]+)"$', text, re.M))


def test_workflow_stays_read_only_and_watches_the_ledger():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML reads the bare key `on` as true.
    triggers = workflow[True]
    assert set(triggers) == {"pull_request", "push", "schedule", "workflow_dispatch"}
    for event in ("pull_request", "push"):
        assert {
            "known-validation-gaps.yaml",
            "tools/waiver_issues.py",
            "tools/source_conflicts.py",
            "tests/test_waiver_issues*.py",
        } <= set(triggers[event]["paths"])
    assert workflow["permissions"] == {"contents": "read"}
    jobs = workflow["jobs"]
    assert jobs["verify"]["permissions"] == {"contents": "read", "issues": "read"}
    assert jobs["alarm"]["permissions"] == {"issues": "write"}
    assert "schedule" in jobs["alarm"]["if"] and "pull_request" not in jobs["alarm"]["if"]
    checkout = next(step for step in jobs["verify"]["steps"] if "checkout" in step.get("uses", ""))
    assert checkout["with"]["persist-credentials"] is False


def test_workflow_runs_the_property_tests_with_hypothesis_installed():
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["verify"]["steps"]
    runs = [step.get("run", "") for step in steps]
    assert any("hypothesis==" in run and "pytest==" in run for run in runs)
    assert any("tests/test_waiver_issues.py" in run and "tests/test_waiver_issues_properties.py" in run for run in runs)


def test_one_alarm_at_a_time_finds_the_last_alarm_without_the_search_index():
    alarm = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["alarm"]
    assert alarm["concurrency"] == {"group": "waiver-issues-alarm", "cancel-in-progress": False}
    script = alarm["steps"][0]["run"]
    assert "gh issue list" in script and "--search" not in script
    assert 'select(.title == \\"$title\\")' in script


@pytest.mark.parametrize(
    "candidate",
    [
        url(1),
        url(1248),
        "https://github.com/TheAxiomFoundation/rulespec-us-ca/issues/7",
        "https://github.com/TheAxiomFoundation/a.b_c-d/issues/12",
        "https://github.com/TheAxiomFoundation/../issues/1",
        ISSUES + "0",
        ISSUES + "01",
        url(1) + "/",
        url(1) + "#x",
        url(1) + "\n",
        "http://github.com/TheAxiomFoundation/rulespec-us/issues/1",
        "https://github.com/TheAxiomFoundation/rulespec-us/pull/1",
        "https://github.com/someone-else/rulespec-us/issues/1",
        "",
    ],
)
def test_tool_and_encoder_accept_the_same_urls(candidate):
    """Differential, where axiom-encode is importable: the required pytest leg."""

    waivers = pytest.importorskip("axiom_encode.validation_waivers")
    assert (wi.ISSUE_RE.fullmatch(candidate) is not None) == (waivers.ISSUE_RE.fullmatch(candidate) is not None)
