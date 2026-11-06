"""Tests for tools/pin_runner.py and the workflow job that runs it.

Three kinds:

- the outcome classifier and pin selection, on synthetic oracle records;
- the source-conflicts workflow's isolation of the `pinned-tests` job, read
  statically from the workflow file;
- the whole runner on fixture repositories (`git init` in a temporary
  directory, a tiny pyproject.toml), one per way a pin can fail closed. These
  need git, uv and the package index, so they run where
  AXIOM_PIN_RUNNER_TESTS_REQUIRED=1 (the pinned-tests job sets it, and there
  a missing tool fails them) and skip elsewhere, such as the Repository Checks
  leg, which should not depend on the package index.

Property-based tests of the classifier live in test_pin_runner_properties.py.
"""

from __future__ import annotations

import copy
import dataclasses
import email.message
import http.server
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
import threading
import urllib.error
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "source-conflicts.yml"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sc = _load("source_conflicts", REPO_ROOT / "tools" / "source_conflicts.py")
runner = _load("pin_runner", REPO_ROOT / "tools" / "pin_runner.py")

COMMIT = "c" * 40
UV = shutil.which("uv")
GIT = shutil.which("git")
REQUIRED = os.environ.get("AXIOM_PIN_RUNNER_TESTS_REQUIRED") == "1"
needs_git = pytest.mark.skipif(not GIT, reason="building fixture repositories needs git")
needs_tools = pytest.mark.skipif(
    not REQUIRED,
    reason="fixture-repository tests need git, uv and the package index; the pinned-tests job runs them "
    "(AXIOM_PIN_RUNNER_TESTS_REQUIRED=1)",
)


def pin(name="test_ok", path="tests/test_main.py", repo="PolicyEngine/fixture", commit=COMMIT):
    return runner.Pin("us:fixture", "entries[0].tests[0]", repo, commit, path, name)


def phases(setup="passed", call="passed", teardown="passed", xfail=False):
    record = {}
    for when, outcome in (("setup", setup), ("call", call), ("teardown", teardown)):
        if outcome is not None:
            record[when] = {"outcome": outcome, "xfail": xfail and when == "call", "message": ""}
    return record


def oracle(items=(), *, reports=None, deselected=(), errors=(), skips=(), exitstatus=0, xdist=False):
    """A synthetic oracle record; items are (nodeid, path, name), indexed in
    order. `reports` and `deselected` name items by node id here, for
    readability; the record keys them by index, as the oracle does."""

    index = {}
    for position, (nodeid, _, _) in enumerate(items):
        index.setdefault(nodeid, position)
    return {
        "collected": [
            {"index": position, "nodeid": nodeid, "path": path, "name": name}
            for position, (nodeid, path, name) in enumerate(items)
        ],
        "deselected": [index[nodeid] for nodeid in deselected],
        "collect_errors": [{"nodeid": path, "path": path, "message": "boom"} for path in errors],
        "collect_skips": [{"nodeid": path, "path": path, "message": "skip"} for path in skips],
        "reports": {str(index[nodeid]): record for nodeid, record in (reports or {}).items()},
        "exitstatus": exitstatus,
        "xdist": xdist,
    }


# ---------------------------------------------------------------------------
# Classification


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        (None, "not run"),
        ({}, "not run"),
        (phases(), "passed"),
        (phases(setup="failed", call=None, teardown="passed"), "error"),
        (phases(setup="skipped", call=None, teardown="passed"), "skipped"),
        ({"setup": {"outcome": "skipped", "xfail": True}, "teardown": {"outcome": "passed"}}, "xfail"),
        (phases(call=None), "not run"),
        (phases(call="failed"), "failed"),
        (phases(call="skipped"), "skipped"),
        (phases(call="skipped", xfail=True), "xfail"),
        (phases(xfail=True), "xpass"),
        (phases(teardown=None), "error"),
        (phases(teardown="failed"), "error"),
        (phases(teardown="skipped"), "error"),
        ({"setup": {"outcome": "passed"}, "call": {"outcome": "rerun"}, "teardown": {"outcome": "passed"}}, "error"),
        ({"setup": "passed", "call": {"outcome": "passed"}, "teardown": {"outcome": "passed"}}, "error"),
        ({"call": {"outcome": "passed"}, "teardown": {"outcome": "passed"}}, "not run"),
    ],
)
def test_case_outcome(record, expected):
    assert runner.case_outcome(record) == expected


def test_worst():
    assert runner.worst(["passed", "passed"]) == "passed"
    assert runner.worst(["passed", "skipped", "xfail"]) == "xfail"
    assert runner.worst(["not run", "passed"]) == "not run"
    assert runner.worst(["failed", "error"]) == "error"
    assert runner.worst([]) == "error"
    assert runner.worst(["passed", "something new"]) == "error"  # an unknown outcome never passes
    assert runner.worst(["something new"]) == "error"


def test_classify_passes_only_every_case_passing():
    one, two = "tests/test_main.py::test_p[1]", "tests/test_main.py::test_p[2]"
    items = [(one, "tests/test_main.py", "test_p"), (two, "tests/test_main.py", "test_p")]
    results, issues = runner.classify(oracle(items, reports={one: phases(), two: phases()}), [pin("test_p")], process_exit=0)
    assert (results[0]["outcome"], len(results[0]["cases"]), issues) == ("passed", 2, [])
    results, issues = runner.classify(oracle(items, reports={one: phases(), two: phases(call="skipped")}, exitstatus=0), [pin("test_p")], process_exit=0)
    assert results[0]["outcome"] == "skipped" and "1 of 2 case(s) did not pass, first " + two in results[0]["detail"]
    results, _ = runner.classify(oracle(items, reports={one: phases()}), [pin("test_p")], process_exit=0)
    assert results[0]["outcome"] == "not run"  # a collected case that never reported


def test_a_yaml_pin_names_exactly_one_case():
    # #1843 review: two passing cases with one name used to pass the pin.
    path = "policyengine_us/tests/a.yaml"
    items = [("policyengine_us/tests/a.yaml::", path, "Twice"), ("policyengine_us/tests/a.yaml::", path, "Twice")]
    record = oracle(items, reports={})
    record["reports"] = {"0": phases(), "1": phases()}
    yaml_pin = runner.Pin("us:fixture", "entries[0].tests[0]", "PolicyEngine/policyengine-us", COMMIT, path, "Twice")
    results, _ = runner.classify(record, [yaml_pin], process_exit=0)
    assert results[0]["outcome"] == "ambiguous" and results[0]["cases"] == []
    record["reports"]["1"] = phases(call="failed")
    assert runner.classify(record, [yaml_pin], process_exit=0)[0][0]["outcome"] == "ambiguous"
    # A Python test's parametrized cases are still one pin, all of which must pass.
    one, two = "tests/test_main.py::test_p[1]", "tests/test_main.py::test_p[2]"
    py = [(one, "tests/test_main.py", "test_p"), (two, "tests/test_main.py", "test_p")]
    assert runner.classify(oracle(py, reports={one: phases(), two: phases()}), [pin("test_p")], process_exit=0)[0][0]["outcome"] == "passed"


def test_two_pins_that_join_to_one_id_never_share_a_cached_pass(tmp_path):
    # #1843 review: (tests/a.yaml, "b.yaml::c") and (tests/a.yaml::b.yaml, "c")
    # both display as tests/a.yaml::b.yaml::c. A path with `::` can't run at
    # all now, and the cache matches on the (path, name) pair, never the id.
    first = runner.Pin("us:x", "entries[0].tests[0]", "PolicyEngine/a", COMMIT, "tests/a.yaml", "b.yaml::c")
    second = runner.Pin("us:x", "entries[0].tests[1]", "PolicyEngine/a", COMMIT, "tests/a.yaml::b.yaml", "c")
    assert first.id == second.id and first.key != second.key
    assert runner.cache_key("PolicyEngine/a", COMMIT, [first], "v") != runner.cache_key("PolicyEngine/a", COMMIT, [second], "v")
    groups, unrun = runner.collect_pins(register(
        {"repo": "PolicyEngine/policyengine-us", "commit": COMMIT, "path": "tests/a.yaml::b.yaml", "name": "c", "pins": ["reading"]},
    ))
    assert groups == {} and "has `::` in its path" in unrun[0]["reason"]
    # A stored pass of the first, forged under the second's key, is not reused for the second.
    cache = tmp_path / "cache"
    cache.mkdir()
    key = runner.cache_key("PolicyEngine/a", COMMIT, [second], "v")
    passed_case = [{"nodeid": "tests/a.yaml::", "index": 0, "outcome": "passed"}]
    stored = {
        "key": key, "repo": "PolicyEngine/a", "commit": COMMIT, "issues": [], "pytest_exit": 0,
        "pins": [{**runner._failed(first, "passed", ""), "cases": passed_case}],
    }
    stored["pins"][0].pop("detail")
    (cache / f"{key}.json").write_text(json.dumps(stored))
    settings_ = runner.Settings(uv="uv", git="git", work=tmp_path, cache_dir=cache)
    assert runner._cached(settings_, key, "PolicyEngine/a", COMMIT, [second]) is None
    # The same record does serve the pin it belongs to.
    stored["key"] = runner.cache_key("PolicyEngine/a", COMMIT, [first], "v")
    (cache / f"{stored['key']}.json").write_text(json.dumps(stored))
    assert runner._cached(settings_, stored["key"], "PolicyEngine/a", COMMIT, [first]) is not None


def test_classify_matches_by_path_and_name_not_node_id():
    # The node id is relative to the rootdir, which need not be the checkout root.
    item = ("sub/tests/test_main.py::TestK::test_m", "tests/test_main.py", "TestK::test_m")
    results, _ = runner.classify(oracle([item], reports={item[0]: phases()}), [pin("TestK::test_m")], process_exit=0)
    assert results[0]["outcome"] == "passed"
    results, _ = runner.classify(oracle([item], reports={item[0]: phases()}), [pin("test_m")], process_exit=0)
    assert results[0]["outcome"] == "missing"
    # The same function name in another file is another test.
    other = ("tests/test_other.py::TestK::test_m", "tests/test_other.py", "TestK::test_m")
    results, _ = runner.classify(oracle([other], reports={other[0]: phases()}), [pin("TestK::test_m")], process_exit=0)
    assert results[0]["outcome"] == "missing"


@pytest.mark.parametrize(
    ("record", "missing_files", "expected"),
    [
        (oracle(), ["tests/test_main.py"], "missing file"),
        (oracle(errors=["tests/test_main.py"]), [], "collection error"),
        (oracle(skips=["tests/test_main.py"]), [], "not collected"),
        (oracle(skips=["tests/test_other.py"]), [], "missing"),
        (oracle(), [], "missing"),
        (oracle([("n", "tests/test_main.py", "test_ok")], deselected=["n"], reports={}), [], "deselected"),
        (oracle([("n", "tests/test_main.py", "test_ok")], reports={"n": phases()}, xdist=True), [], "error"),
    ],
)
def test_classify_fails_closed(record, missing_files, expected):
    results, _ = runner.classify(record, [pin()], process_exit=1, missing_files=missing_files)
    assert results[0]["outcome"] == expected
    assert results[0]["detail"]


def test_classify_commit_issues():
    # The process exit and the session's own status are checked independently
    # (round-8 review: a sessionfinish hook set exit 1 after the plugin wrote).
    item = ("n", "tests/test_main.py", "test_ok")
    passing = oracle([item], reports={"n": phases()})
    assert runner.classify(passing, [pin()], process_exit=0)[1] == []
    assert runner.classify(passing, [pin()], process_exit=1)[1] == ["pytest's process exited 1"]
    assert runner.classify(passing, [pin()], process_exit=None)[1] == ["pytest did not run"]
    _, issues = runner.classify(oracle([item], reports={"n": phases()}, exitstatus=1), [pin()], process_exit=0)
    assert issues == ["pytest's session reported exit status 1"]
    _, issues = runner.classify(oracle([item], reports={"n": phases()}, exitstatus=None), [pin()], process_exit=0)
    assert issues == ["pytest's session reported exit status None"]
    _, issues = runner.classify(oracle([item], reports={"n": phases()}, xdist=True), [pin()], process_exit=0)
    assert any("pytest-xdist" in issue for issue in issues)
    results, issues = runner.classify(oracle([item], reports={"n": phases(call="failed")}, exitstatus=1), [pin()], process_exit=1)
    assert results[0]["outcome"] == "failed" and len(issues) == 2


def test_a_duplicate_report_never_passes():
    # The oracle turns a second report for one node id and phase into
    # `duplicate`, so a later pass cannot hide an earlier failure.
    item = ("n", "tests/test_main.py", "test_ok")
    record = phases()
    record["call"] = {"outcome": "duplicate", "xfail": False}
    results, _ = runner.classify(oracle([item], reports={"n": record}), [pin()], process_exit=0)
    assert results[0]["outcome"] == "error"


def test_commit_passed():
    case = {"nodeid": "n", "outcome": "passed"}
    good = {"pins": [{"outcome": "passed", "cases": [case]}], "issues": [], "pytest_exit": 0}
    assert runner.commit_passed(good)
    assert not runner.commit_passed({**good, "issues": ["x"]})
    assert not runner.commit_passed({**good, "pins": []})
    assert not runner.commit_passed({**good, "pins": "x"})
    # Each condition alone fails it: the process exit, then the pins.
    for exit_code in (1, 2, None, "0"):
        assert not runner.commit_passed({**good, "pytest_exit": exit_code})
    assert not runner.commit_passed({k: v for k, v in good.items() if k != "pytest_exit"})
    assert not runner.commit_passed({**good, "pins": [{"outcome": "passed", "cases": [case]}, {"outcome": "xfail", "cases": [case]}]})
    assert not runner.commit_passed({**good, "pins": [{"outcome": "passed", "cases": []}]})
    assert not runner.commit_passed({**good, "pins": [{"outcome": "passed", "cases": [{"outcome": "skipped"}]}]})


# ---------------------------------------------------------------------------
# Which pins run, Python, install specs, cache keys


def register(*tests):
    return {"version": 1, "entries": [{"jurisdiction": "us", "id": "fixture", "tests": list(tests)}]}


def test_collect_pins_groups_runnable_pins_and_refuses_the_rest():
    good = {"repo": "PolicyEngine/a", "commit": COMMIT, "path": "tests/test_a.py", "name": "test_x", "pins": ["reading"]}
    groups, unrun = runner.collect_pins(register(
        good,
        {**good, "name": "TestK::test_y"},
        {**good, "repo": "policyengine/b"},  # GitHub's spelling is required, so a case variant is refused
        {**good, "repo": "SomeoneElse/c"},
        {**good, "path": "tests/cases.yaml", "name": "a case"},
        {"path": "tests/test_local.py", "name": "test_z", "pins": ["reading"]},
        {**good, "commit": "abc"},
        {**good, "path": "tests/helpers.py"},
        "junk",
        # A YAML case runs where YAML_RUNNERS names its repository's runner.
        {**good, "repo": "PolicyEngine/policyengine-us", "path": "policyengine_us/tests/a.yaml", "name": "A case (2024)"},
        {**good, "repo": "PolicyEngine/policyengine-us", "path": "policyengine_us/tests/a.yaml", "name": "two\nlines"},
    ))
    assert sorted(groups) == [("PolicyEngine/a", COMMIT), ("PolicyEngine/policyengine-us", COMMIT)]
    assert [p.name for p in groups[("PolicyEngine/a", COMMIT)]] == ["test_x", "TestK::test_y"]
    (yaml_pin,) = groups[("PolicyEngine/policyengine-us", COMMIT)]
    assert (yaml_pin.kind, yaml_pin.name) == ("yaml", "A case (2024)")
    assert all(p.kind == "python" for p in groups[("PolicyEngine/a", COMMIT)])
    reasons = [item["reason"] for item in unrun]
    assert len(reasons) == 8
    assert "has a malformed name" in reasons[7]
    assert reasons[0].startswith("the runner won't execute pins in policyengine/b")
    assert reasons[1].startswith("the runner won't execute pins in SomeoneElse/c")
    assert "is a YAML test case in PolicyEngine/a, which has no YAML test runner here" in reasons[2]
    assert "this repository" in reasons[3]
    assert "malformed commit" in reasons[4]
    assert "not in a test_*.py file" in reasons[5]
    assert "not a mapping" in reasons[6]
    assert all(item["entry"] == "us:fixture" for item in unrun)


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        (None, "3.14"),
        (">=3.10,<3.15", "3.14"),
        ("<3.13", "3.12"),
        ("==3.11.*", "3.11"),
        ("~=3.10", "3.14"),
        (">=3.10.4,<3.11", "3.10"),
        ("!=3.14.*", "3.13"),
    ],
)
def test_pick_python(spec, expected):
    assert runner.pick_python(spec) == expected


@pytest.mark.parametrize("spec", [">=3.15", "<3.9", "not a specifier"])
def test_pick_python_fails_closed(spec):
    with pytest.raises(runner.StepError) as caught:
        runner.pick_python(spec)
    assert caught.value.outcome == "install failed"


def test_install_spec_table(monkeypatch):
    assert runner.install_spec("PolicyEngine/a") == ("-e", ".[dev]")
    monkeypatch.setitem(runner.INSTALL_SPECS, "PolicyEngine/policyengine-us", ("-e", ".[test]"))
    assert runner.install_spec("PolicyEngine/policyengine-us") == ("-e", ".[test]")
    assert runner.install_spec("PolicyEngine/a") == ("-e", ".[dev]")


def test_allowed_owners():
    # Exact owners only. The owner in the URL proves nothing by itself (a fork
    # network serves every object through the parent), so commit_provenance
    # runs before any fetch too.
    assert runner.allowed_repo("TheAxiomFoundation/rulespec-us")
    assert runner.allowed_repo("PolicyEngine/microcosm-dynamics")
    for repo in ("PolicyEngineX/fork", "someone/TheAxiomFoundation", "policyengine/microcosm-dynamics",
                 "POLICYENGINE/x", "PolicyEngine/..", "PolicyEngine/.", "PolicyEngine/"):
        assert not runner.allowed_repo(repo), repo


def test_cache_key():
    a, b = pin("test_a"), pin("test_b")
    key = runner.cache_key("PolicyEngine/a", COMMIT, [a, b], "v1")
    assert key == runner.cache_key("PolicyEngine/a", COMMIT, [b, a, a], "v1")
    assert len({
        key,
        runner.cache_key("PolicyEngine/b", COMMIT, [a, b], "v1"),
        runner.cache_key("PolicyEngine/a", "d" * 40, [a, b], "v1"),
        runner.cache_key("PolicyEngine/a", COMMIT, [a], "v1"),
        runner.cache_key("PolicyEngine/a", COMMIT, [a, b], "v2"),
    }) == 5


# ---------------------------------------------------------------------------
# Household choices: an optimum pin must show the model choosing

PE_US = "PolicyEngine/policyengine-us"
EXPECT = ("tax_unit_itemizes", True, False, None)
OPTIMUM = {"repo": PE_US, "commit": COMMIT, "path": "policyengine_us/tests/a.yaml", "name": "Itemizes",
           "pins": ["optimum"], "variable": "tax_unit_itemizes", "chooses": True}


def choice_entry(*tests, default=False):
    return {"jurisdiction": "us", "id": "choice", "default": {"value": default, "basis": "statute"}, "tests": list(tests)}


def choices(*tests, default=False):
    return {"version": 1, "entries": [choice_entry(*tests, default=default)]}


def test_collect_pins_reads_household_choices():
    default_pin = {**OPTIMUM, "name": "Takes the default", "pins": ["default"]}
    no_option = {key: value for key, value in OPTIMUM.items() if key != "chooses"}
    groups, unrun = runner.collect_pins(register(), choices(
        OPTIMUM,
        default_pin,
        {**OPTIMUM, "path": "tests/test_a.py", "name": "test_a"},
        {**OPTIMUM, "name": "No variable", "variable": "not a name"},
        {**OPTIMUM, "name": "The default", "chooses": False},
        {**no_option, "name": "No option"},
        {**OPTIMUM, "name": "One unit", "instances": ["unit_0"]},
        {**OPTIMUM, "name": "Bad instances", "instances": ["unit_0", "unit_0"]},
        {**OPTIMUM, "name": "Empty instances", "instances": []},
    ))
    assert [(p.label, p.name, p.expect) for p in groups[(PE_US, COMMIT)]] == [
        ("choices.entries[0].tests[0]", "Itemizes", EXPECT),
        ("choices.entries[0].tests[1]", "Takes the default", None),
        ("choices.entries[0].tests[6]", "One unit", ("tax_unit_itemizes", True, False, ("unit_0",))),
    ]
    assert [item["label"] for item in unrun] == [f"choices.entries[0].tests[{index}]" for index in (2, 3, 4, 5, 7, 8)]
    reasons = [item["reason"] for item in unrun]
    assert "optimum pin on a Python test" in reasons[0]
    assert "without a decision variable" in reasons[1]
    assert "chosen option is the default" in reasons[2]
    assert "without a chosen option and a default" in reasons[3]
    assert all("malformed instances" in reason for reason in reasons[4:])
    # A register pin is never read as an optimum, whatever its pins say.
    groups, unrun = runner.collect_pins(register({**OPTIMUM, "pins": ["optimum"], "chooses": False}))
    assert [p.expect for p in groups[(PE_US, COMMIT)]] == [None] and unrun == []


AS_SHIPPED = {"parameters": [], "reforms": False, "extensions": False}


def record(*computed, variable="tax_unit_itemizes", inputs=("age", "employment_income"), ids=None, dtype="bool", **extra):
    """One decision variable's record, as the oracle writes it."""

    ids = list(ids) if ids is not None else [f"unit_{index}" for index in range(len(computed))]
    return {"variable": variable, "computed": list(computed), "ids": ids, "dtype": dtype, "definition_period": "year",
            "period": "2026", "period_unit": "year", "period_size": 1, "input_variables": list(inputs), **extra}


def chose(*computed, inputs=("age", "employment_income"), **case):
    """An oracle record of a case whose simulation computed these values."""

    return {"case": {**AS_SHIPPED, **case}, "choices": {"tax_unit_itemizes": record(*computed, inputs=inputs)}}


@pytest.mark.parametrize(
    ("item", "reason"),
    [
        (chose(True), None),
        (chose(True, True), None),  # every tax unit chose it
        (chose(True, inputs=["tax_unit_itemizes", "age"]), "sets tax_unit_itemizes as an input (directly or through axes)"),
        (chose(True, False), "computed tax_unit_itemizes = False"),
        (chose(1), "computed tax_unit_itemizes = 1"),  # 1 is not true
        (chose(), "computed no value of tax_unit_itemizes"),
        # #1844 reviews: a case that changes the model doesn't show it choosing as shipped.
        (chose(True, parameters=["gov.simulation.branch_to_determine_itemization"]),
         "changes the model (gov.simulation.branch_to_determine_itemization)"),
        (chose(True, reforms=True), "changes the model (a reform or extension)"),
        (chose(True, extensions=True), "changes the model (a reform or extension)"),
        ({"case": AS_SHIPPED, "choices": {"tax_unit_itemizes": {"variable": "tax_unit_itemizes", "error": "KeyError: 'x'"}}},
         "could not be read: KeyError"),
        # An error means the record can't be trusted, whatever else it holds.
        ({"case": AS_SHIPPED, "choices": {"tax_unit_itemizes": record(True, error="ValueError: partly read")}},
         "could not be read: ValueError"),
        ({"case": AS_SHIPPED}, "did not expose the case or the model's choices"),
        ({"choices": chose(True)["choices"]}, "did not expose the case or the model's choices"),
        (None, "did not expose the case or the model's choices"),
        # #1844 review round 3 (P1): a pin is judged only on its own variable's
        # record. Another entry's pin on the same case reads another variable.
        ({"case": AS_SHIPPED, "choices": {"zz_always_true": record(True, variable="zz_always_true")}},
         "did not read tax_unit_itemizes from the case"),
        ({"case": AS_SHIPPED, "choices": {"tax_unit_itemizes": record(True, variable="zz_always_true")}},
         "did not read tax_unit_itemizes from the case"),
        ({"case": AS_SHIPPED, "choices": {"tax_unit_itemizes": record(False),
                                          "zz_always_true": record(True, variable="zz_always_true")}},
         "computed tax_unit_itemizes = False"),
    ],
)
def test_optimum_shown(item, reason):
    found = runner.optimum_shown(item, EXPECT)
    assert (found is None) if reason is None else (found is not None and reason in found), found


@pytest.mark.parametrize(
    ("periods", "reason"),
    [
        ({}, None),
        ({"definition_period": "eternity", "period": "2026", "period_unit": "year", "period_size": 1}, None),
        ({"definition_period": "eternity", "period": "2026-01", "period_unit": "month", "period_size": 1}, None),
        ({"definition_period": "month", "period": "2026-01", "period_unit": "month", "period_size": 1}, None),
        # #1844 review round 4 (P1): core sums a monthly variable over a year (or
        # picks its last month), and divides a yearly one into months, so the
        # value isn't one choice: a sum of defaults can look like an optimum.
        ({"definition_period": "month"}, "defined by month, over 2026"),
        ({"definition_period": "year", "period": "2026-01", "period_unit": "month"}, "defined by year, over 2026-01"),
        ({"period": "year:2026:2", "period_size": 2}, "defined by year, over year:2026:2"),
        ({"definition_period": None}, "did not record the period"),
        ({"period_unit": 3}, "did not record the period"),
        ({"period_size": "1"}, "did not record the period"),
    ],
)
def test_an_optimum_pin_reads_one_of_the_variables_own_periods(periods, reason):
    choice = {**record(True), **periods}
    found = runner.optimum_shown({"case": AS_SHIPPED, "choices": {"tax_unit_itemizes": choice}}, EXPECT)
    assert (found is None) if reason is None else (found is not None and reason in found), found


@pytest.mark.parametrize(
    ("instances", "ids", "reason"),
    [
        (None, None, "computed tax_unit_itemizes = False, not"),  # every instance must choose
        (("unit_0",), None, None),
        (("unit_0", "unit_1"), None, "computed tax_unit_itemizes = False for unit_1"),
        (("unit_9",), None, "has no instance 'unit_9'"),
        (("unit_0",), [], "did not record which instance"),
        (("unit_0",), ["unit_0"], "did not record which instance"),  # fewer ids than values
    ],
)
def test_an_optimum_pin_may_name_the_instances_that_choose(instances, ids, reason):
    # #1844 review round 3 (P2): in a case with several tax units or people,
    # a pin can name the instances whose choice it shows.
    choice = record(True, False)
    if ids is not None:
        choice["ids"] = ids
    found = runner.optimum_shown({"case": AS_SHIPPED, "choices": {"tax_unit_itemizes": choice}},
                                 ("tax_unit_itemizes", True, False, instances))
    assert (found is None) if reason is None else (found is not None and reason in found), found


@pytest.mark.parametrize(
    ("computed", "chooses", "default", "dtype", "vacuous"),
    [
        # #1844 review round 2 (P1): a float32 model is read as the float32
        # number it stores.
        ([0.30000001192092896], "0.3", "0.5", "float32", False),
        ([0.5], "0.5005", "0.5", "float32", True),  # the model computed the default
        ([0.5], "0.500000001", "0.5", "float32", True),  # the same float32 number as the default
        ([16777216.0], "16777217", "16777216", "float32", True),
        (["SEPARATE"], "separate", "joint", "enum", False),  # an enum by its name
        # Round 3 (P3): an integer compares exactly, and a float64 as a float64.
        ([16777220], "16777219", "0", "int64", True),
        ([16777219], "16777219", "0", "int32", False),
        ([0.1], "0.1", "0.5", "float64", False),
        ([0.1], "0.1000000001", "0.5", "float64", True),
        # A record without a dtype compares as float32, as same_option does.
        ([16777220], "16777219", "0", None, False),
    ],
)
def test_numbers_and_enums_compare_as_the_model_stores_them(computed, chooses, default, dtype, vacuous):
    item = {"case": AS_SHIPPED, "choices": {"v": record(*computed, variable="v", inputs=(), dtype=dtype)}}
    assert (runner.optimum_shown(item, ("v", chooses, default, None)) is not None) is vacuous


@pytest.mark.parametrize(
    ("value", "option", "dtype", "same"),
    [
        (True, True, "bool", True), (1, True, "bool", False), (True, 1, "int64", False),
        (3, "3", "int64", True), (3, "3.0", "int64", True), (3, "3.5", "int64", False), (3, "x", "int64", False),
        (0.1, "0.1", "float64", True), (0.1, "0.1000000001", "float64", False),
        (0.1, "0.1000000001", "float32", True), ("SEPARATE", "separate", "enum", True),
        # Round 4 (P1): an enum or string value is a name, however numeric.
        ("16777220", "16777219", "enum", False), ("16777220", "16777220", "enum", True), ("0", 0, "enum", False),
        ("16777220", "16777219", "object", False), ("a", "A", "object", True), ("12", "12.0", "<U2", False),
        # An unsigned integer compares exactly too.
        (3, "3", "uint8", True), (3, "3.5", "uint8", False), (16777220, "16777219", "uint32", False),
    ],
)
def test_same_stored(value, option, dtype, same):
    assert runner.same_stored(value, option, dtype) is same


def test_an_optimum_that_is_the_default_shows_nothing():
    item = {"case": AS_SHIPPED, "choices": {"share": record(0.5, variable="share", inputs=(), dtype="float32")}}
    assert "is the default" in runner.optimum_shown(item, ("share", "0.5", "0.50", None))
    assert runner.optimum_shown(item, ("share", "0.5", "1", None)) is None


@pytest.mark.parametrize(
    ("a", "b", "same"),
    [
        (True, True, True), (True, 1, False), (False, 0, False), ("a", "a", True), ("a", "b", False),
        ("0.5", 0.5, True), ("0.5", "0.50", True), (1, 1.0, True), ("1", "1.5", False), ("inf", float("inf"), False),
        ("true", True, False), (None, None, False),
        # #1844 review (P2): an enum option matches the model's name for it.
        ("separate", "SEPARATE", True), ("head-of-household", "HEAD_OF_HOUSEHOLD", True), ("separate", "JOINT", False),
        # The float32 numbers a model computes with.
        ("0.3", 0.30000001192092896, True), ("16777217", "16777216", True), ("0.5005", "0.5", False),
    ],
)
def test_same_option(a, b, same):
    assert runner.same_option(a, b) is same


def test_classify_marks_a_vacuous_optimum():
    item = ("policyengine_us/tests/a.yaml::", "policyengine_us/tests/a.yaml", "Itemizes")
    good = oracle([item], reports={item[0]: phases()})
    good["collected"][0].update(chose(True))
    optimum = runner.Pin("us:choice", "choices.entries[0].tests[0]", PE_US, COMMIT, item[1], item[2], EXPECT)
    results, issues = runner.classify(good, [optimum], process_exit=0)
    assert results[0]["outcome"] == "passed" and issues == []
    forced = copy.deepcopy(good)
    forced["collected"][0]["choices"]["tax_unit_itemizes"]["input_variables"].append("tax_unit_itemizes")
    results, _ = runner.classify(forced, [optimum], process_exit=0)
    assert results[0]["outcome"] == "vacuous" and "as an input" in results[0]["detail"]
    assert not runner.commit_passed({"pins": results, "issues": [], "pytest_exit": 0})
    # A failing case fails, whatever it computed.
    failing = oracle([item], reports={item[0]: phases(call="failed")})
    failing["collected"][0].update(chose(True))
    assert runner.classify(failing, [optimum], process_exit=0)[0][0]["outcome"] == "failed"
    # Only an optimum pin is checked: without the expectation the record passes.
    plain = dataclasses.replace(optimum, expect=None)
    assert runner.classify(forced, [plain], process_exit=0)[0][0]["outcome"] == "passed"
    # Two pins on one case, on two variables, are judged on their own records.
    both = copy.deepcopy(good)
    both["collected"][0]["choices"]["other"] = record(False, variable="other")
    other = dataclasses.replace(optimum, label="choices.entries[1].tests[0]", expect=("other", True, False, None))
    results, _ = runner.classify(both, [optimum, other], process_exit=0)
    assert [result["outcome"] for result in results] == ["passed", "vacuous"]


oracle_module = _load("axiom_pin_oracle", REPO_ROOT / "tools" / "pin_oracle" / "axiom_pin_oracle.py")


def test_the_oracle_records_values_as_bounded_json():
    # #1844 review round 3 (P3): what the oracle records is JSON, and too
    # large or too deep a value is None, which the runner reads as no value.
    jsonable = oracle_module._jsonable
    assert jsonable([True, 0.5, "a", None]) == [True, 0.5, "a", None]
    assert jsonable({1: [b"x"]}) == {"1": ["b'x'"]}
    assert jsonable(list(range(oracle_module._CASE_LIMIT))) is None
    assert jsonable("x" * (oracle_module._CASE_LIMIT - 2)) == "x" * (oracle_module._CASE_LIMIT - 2)
    assert jsonable("x" * (oracle_module._CASE_LIMIT - 1)) is None
    deep: list = []
    for _ in range(5000):
        deep = [deep]
    assert jsonable(deep) is None
    assert jsonable(float("nan")) is not None  # JSON-encodable as NaN; the runner's comparisons refuse it
    item = {"case": AS_SHIPPED, "choices": {"v": {**record(True, variable="v"), "computed": None}}}
    assert "computed no value of v" in runner.optimum_shown(item, ("v", True, False, None))


def test_the_oracle_decodes_fixed_length_strings():
    # #1844 review round 5 (P2): core returns a str variable with max_length
    # as bytes; the oracle records the text, so `|S20` values compare by name.
    class Array(list):
        def tolist(self):
            return list(self)

    assert oracle_module._listed(Array([b"16777220", b"SEPARATE"])) == ["16777220", "SEPARATE"]
    assert oracle_module._listed([True, 0.5, "a"]) == [True, 0.5, "a"]
    with pytest.raises(UnicodeDecodeError):
        oracle_module._listed(Array([b"\xff"]))
    item = {"case": AS_SHIPPED, "choices": {"v": record("16777220", variable="v", inputs=(), dtype="|S20")}}
    assert runner.optimum_shown(item, ("v", "16777220", "0", None)) is None
    assert "computed v = '16777220'" in runner.optimum_shown(item, ("v", "16777219", "0", None))


def test_cache_key_covers_an_optimum_pins_expectation():
    plain = pin("Itemizes", path="tests/a.yaml")
    keys = {
        runner.cache_key(PE_US, COMMIT, [plain], "v1"),
        runner.cache_key(PE_US, COMMIT, [dataclasses.replace(plain, expect=EXPECT)], "v1"),
        runner.cache_key(PE_US, COMMIT, [dataclasses.replace(plain, expect=("tax_unit_itemizes", False, True, None))], "v1"),
        runner.cache_key(PE_US, COMMIT, [dataclasses.replace(plain, expect=("tax_unit_itemizes", True, False, ("u",)))], "v1"),
    }
    assert len(keys) == 4


def test_summarize_prints_household_choice_pins(tmp_path):
    report = {
        "commits": [{"repo": PE_US, "commit": COMMIT, "issues": [], "pins": [
            {"entry": "us:choice", "label": "choices.entries[0].tests[0]", "id": "policyengine_us/tests/a.yaml::Itemizes",
             "outcome": "vacuous"}]}],
        "unrun": [{"entry": "us:choice", "label": "choices.entries[0].tests[1]", "reason": "x"}],
        "issues": ["x"],
    }
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    assert runner.summarize(path) == [
        f"- `us:choice` choices.entries[0].tests[0]: `{PE_US}@cccccccccccc:policyengine_us/tests/a.yaml::Itemizes` vacuous",
        "- `us:choice` choices.entries[0].tests[1]: the runner can't execute this pin.",
    ]


def test_cli_reads_the_household_choices_file(tmp_path):
    tools = ["--uv", sys.executable, "--git", sys.executable]
    report_path = tmp_path / "report.json"
    root = tmp_path / "root"
    root.mkdir()
    (root / "known-source-conflicts.yaml").write_text(yaml.safe_dump(register()))
    # No household-choices file beside the register: nothing more to run.
    assert runner.main(["--root", str(root), "--report", str(report_path), *tools]) == 0
    # The file beside the register is read; its unrunnable pins are issues.
    (root / "household-choices.yaml").write_text(yaml.safe_dump(choices({**OPTIMUM, "path": "tests/test_a.py", "name": "test_a"})))
    assert runner.main(["--root", str(root), "--report", str(report_path), *tools]) == 1
    assert json.loads(report_path.read_text())["unrun"][0]["label"] == "choices.entries[0].tests[0]"
    # A file named explicitly must exist.
    assert runner.main(["--root", str(root), "--choices", str(tmp_path / "absent.yaml"), "--report", str(report_path), *tools]) == 1
    assert json.loads(report_path.read_text())["issues"][0].startswith("runner error:")


def test_the_cache_holds_and_returns_only_passing_commits(tmp_path):
    # Both sides check: _store writes only passing commits, and _cached
    # re-checks a record against the repository, commit and ids it is read
    # for, so neither a failure, a stale record nor a corrupt one passes.
    settings_ = runner.Settings(uv="uv", git="git", work=tmp_path, cache_dir=tmp_path / "cache")
    pins = [pin("test_a"), pin("test_b")]
    repo = "PolicyEngine/fixture"
    key = runner.cache_key(repo, COMMIT, pins, "v1")
    case = [{"nodeid": "n", "outcome": "passed"}]

    def result(*outcomes, issues=(), exit_code=0, cases=case, **extra):
        return {
            "repo": repo, "commit": COMMIT, "issues": list(issues), "logs": {"pytest": "x"}, "pytest_exit": exit_code,
            "pins": [{"entry": "us:old", "label": "entries[9].tests[9]", "id": p.id, "path": p.path, "name": p.name,
                      "outcome": o, "cases": cases}
                     for p, o in zip(pins, outcomes, strict=True)],
            **extra,
        }

    for failing in (
        result("passed", "skipped"),
        result("passed", "passed", issues=["pytest's process exited 1"]),
        result("passed", "passed", exit_code=1),  # round-8 review: a nonzero exit is never cached
        result("passed", "passed", exit_code=None),
        result("passed", "passed", cases=[]),
    ):
        runner._store(settings_, key, failing)
        assert not (tmp_path / "cache").exists() or not any((tmp_path / "cache").iterdir())
    runner._store(settings_, key, result("passed", "passed"))
    stored = json.loads((tmp_path / "cache" / f"{key}.json").read_text())
    assert stored["key"] == key and stored["logs"] == {}
    hit = runner._cached(settings_, key, repo, COMMIT, pins)
    assert hit["cached"] is True
    assert [(p["entry"], p["label"]) for p in hit["pins"]] == [("us:fixture", "entries[0].tests[0]")] * 2
    # A planted record that did not pass, belongs to another key, repository
    # or commit, covers other ids, repeats an id, or has no passing case is
    # ignored (round-8 review: a forged repository and commit were accepted).
    path = tmp_path / "cache" / f"{key}.json"
    two = result("passed", "passed")
    for planted in (
        {**result("passed", "failed"), "key": key},
        {**two, "key": "another"},
        {**two, "key": key, "repo": "OutsideOwner/forged"},
        {**two, "key": key, "commit": "d" * 40},
        {**result("passed", "passed", issues=["x"]), "key": key},
        {**result("passed", "passed", exit_code=1), "key": key},
        {**result("passed", "passed", cases=[]), "key": key},
        {**two, "key": key, "pins": two["pins"][:1]},
        {**two, "key": key, "pins": two["pins"] + two["pins"][:1]},
        [],
    ):
        path.write_text(json.dumps(planted))
        assert runner._cached(settings_, key, repo, COMMIT, pins) is None, planted
    path.write_text("{not json")
    assert runner._cached(settings_, key, repo, COMMIT, pins) is None
    assert runner._cached(runner.Settings(uv="uv", git="git", work=tmp_path), key, repo, COMMIT, pins) is None


def test_runner_version_covers_the_runner_and_the_oracle():
    assert {path.name for path in runner.RUNNER_FILES} == {"pin_runner.py", "axiom_pin_oracle.py"}
    assert all(path.is_file() for path in runner.RUNNER_FILES)
    assert re.fullmatch(r"[0-9a-f]{64}", runner.runner_version())


# ---------------------------------------------------------------------------
# The alarm summary reads the report as data


def test_summarize_prints_only_validated_fields(tmp_path):
    report = {
        "commits": [
            {
                "repo": "PolicyEngine/a",
                "commit": COMMIT,
                "issues": [],
                "pins": [
                    {"entry": "us:x", "label": "entries[0].tests[0]", "id": "tests/test_a.py::test_x", "outcome": "passed"},
                    {"entry": "us:x", "label": "entries[0].tests[1]", "id": "tests/test_a.py::TestK::test_y", "outcome": "skipped"},
                    {"entry": "us:x", "label": "entries[0].tests[2]", "id": "tests/test_a.py::test_z`@team", "outcome": "failed"},
                    {"entry": "us:x", "label": "entries[0].tests[3]", "id": "tests/test_a.py::test_w", "outcome": "pwned <script>"},
                ],
            },
            {"repo": "x/y`; rm -rf", "commit": COMMIT, "pins": []},
        ],
        "unrun": [{"entry": "us:x", "label": "entries[0].tests[4]", "reason": "@everyone look"}],
        "issues": ["x"],
    }
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    lines = runner.summarize(path)
    assert lines == [
        "- `us:x` entries[0].tests[1]: `PolicyEngine/a@cccccccccccc:tests/test_a.py::TestK::test_y` skipped",
        "- `us:x` entries[0].tests[4]: the runner can't execute this pin.",
        "- pinned-tests artifact malformed (3 item(s)); the `pinned-tests` job's log has the details.",
    ]
    assert not any("@team" in line or "pwned" in line or "rm -rf" in line or "@everyone" in line for line in lines)


@pytest.mark.parametrize(
    "report",
    [
        # Round-8 review: `outcome: []` made `--summarize` raise TypeError and
        # abort the alarm step.
        {"commits": [{"repo": "PolicyEngine/a", "commit": COMMIT, "pins": [
            {"entry": "us:x", "label": "entries[0].tests[0]", "id": "tests/test_a.py::test_x", "outcome": []}]}]},
        {"commits": [{"repo": "PolicyEngine/a", "commit": COMMIT, "pins": [
            {"entry": "us:x", "label": "entries[0].tests[0]", "id": "tests/test_a.py::test_x", "outcome": {"a": 1}}]}]},
        {"commits": [{"repo": ["PolicyEngine/a"], "commit": COMMIT, "pins": []}]},
        {"commits": [{"repo": "PolicyEngine/a", "commit": COMMIT, "pins": {"a": 1}, "issues": []}]},
        {"commits": {"a": 1}},
        {"commits": [7, None, "x"]},
        {"unrun": "x"},
        {"unrun": [{"entry": {"a": 1}, "label": []}]},
        {"issues": 7},
    ],
)
def test_a_malformed_artifact_raises_the_alarm(tmp_path, report, capsys):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    lines = runner.summarize(path)
    assert any(line.startswith("- pinned-tests artifact malformed") for line in lines), lines
    assert runner.main(["--summarize", str(path)]) == 0
    assert "pinned-tests artifact malformed" in capsys.readouterr().out


def test_one_malformed_pin_does_not_hide_the_others(tmp_path):
    # Every field is type-checked where it is read, so the malformed pin is
    # counted and the failing pin beside it still reaches the alarm.
    path = tmp_path / "report.json"
    path.write_text(json.dumps({"commits": [{"repo": "PolicyEngine/a", "commit": COMMIT, "issues": [], "pins": [
        {"entry": "us:x", "label": "entries[0].tests[0]", "id": "tests/test_a.py::test_x", "outcome": []},
        {"entry": "us:x", "label": "entries[0].tests[1]", "id": "tests/test_a.py::test_y", "outcome": "skipped"},
    ]}], "unrun": [], "issues": []}))
    assert runner.summarize(path) == [
        "- `us:x` entries[0].tests[1]: `PolicyEngine/a@cccccccccccc:tests/test_a.py::test_y` skipped",
        "- pinned-tests artifact malformed (1 item(s)); the `pinned-tests` job's log has the details.",
    ]


@pytest.mark.parametrize(
    ("report", "missing"),
    [
        # Round-9 review: `{}` and a commit without `pins` printed "No pinned
        # test failed". The runner always writes these lists, so each one
        # missing is a malformed artifact.
        ({}, 3),
        ({"commits": [], "unrun": []}, 1),
        ({"commits": [], "issues": []}, 1),
        ({"unrun": [], "issues": []}, 1),
        ({"commits": [{"repo": "PolicyEngine/a", "commit": COMMIT, "issues": []}], "unrun": [], "issues": []}, 1),
        ({"commits": [{"repo": "PolicyEngine/a", "commit": COMMIT, "pins": []}], "unrun": [], "issues": []}, 1),
        ({"commits": [{"repo": "PolicyEngine/a", "commit": COMMIT}], "unrun": [], "issues": []}, 2),
    ],
)
def test_an_incomplete_artifact_raises_the_alarm(tmp_path, report, missing, capsys):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    assert runner.summarize(path) == [
        f"- pinned-tests artifact malformed ({missing} item(s)); the `pinned-tests` job's log has the details."
    ]
    assert runner.main(["--summarize", str(path)]) == 0
    assert "No pinned test failed" not in capsys.readouterr().out


def test_summarize_never_raises(tmp_path, monkeypatch, capsys):
    # Even a bug in the summarizer yields the alarm line, and exit 0.
    path = tmp_path / "report.json"
    path.write_text(json.dumps({"commits": []}))
    monkeypatch.setattr(runner, "_summary_lines", lambda report: 1 / 0)
    assert runner.summarize(path) == [runner.MALFORMED_ARTIFACT]
    monkeypatch.setattr(runner, "summarize", lambda path: 1 / 0)
    assert runner.main(["--summarize", str(path)]) == 0
    assert capsys.readouterr().out == runner.MALFORMED_ARTIFACT + "\n"


def test_summarize_prints_yaml_case_ids_but_nothing_that_formats(tmp_path):
    # A YAML case name is free text. It is printed inside a code span when it
    # holds no backtick, @, angle bracket, category C, default-ignorable, or
    # separator character but a space; anything else is malformed. #1843 round-2 review
    # (P3): "Café" and "A case!" were malformed though the rule allows them.
    printable = ("A farm loss (2024), $3,000", "Café", "A case!", "Ein Fall für 2024 [ü]", "(2024) a case", "a :: b")
    unsafe = ("x `@team`", "<img src=x>", "@everyone", "two\nlines", "tab\there", "\u202ereversed", "zero\u200dwidth",
              "line\u2028separator", "no\u00a0break", "private\ue000use", "surrogate\ud800", "unassigned\u0378",
              " leading", "trailing ", "")
    pins = [
        {"entry": "us-md:x", "label": f"entries[0].tests[{index}]", "id": f"policyengine_us/tests/a.yaml::{name}", "outcome": "failed"}
        for index, name in enumerate(printable + unsafe)
    ]
    pins.append({"entry": "us-md:x", "label": "entries[0].tests[99]", "id": "policyengine_us/tests/a.py::Café", "outcome": "failed"})
    path = tmp_path / "report.json"
    path.write_text(json.dumps({"commits": [{"repo": "PolicyEngine/policyengine-us", "commit": COMMIT, "issues": [], "pins": pins}],
                                "unrun": [], "issues": []}))
    assert runner.summarize(path) == [
        f"- `us-md:x` entries[0].tests[{index}]: `PolicyEngine/policyengine-us@cccccccccccc:policyengine_us/tests/a.yaml::{name}` failed"
        for index, name in enumerate(printable)
    ] + [f"- pinned-tests artifact malformed ({len(unsafe) + 1} item(s)); the `pinned-tests` job's log has the details."]


def _yaml_summary_report(names, *, path="tests/a.yaml", repo="PolicyEngine/a"):
    return {
        "commits": [{"repo": repo, "commit": COMMIT, "issues": [], "pins": [
            {"entry": "us:x", "label": f"entries[0].tests[{index}]", "id": f"{path}::{name}", "outcome": "failed"}
            for index, name in enumerate(names)
        ]}],
        "unrun": [], "issues": [],
    }


@pytest.mark.parametrize("forbidden", ["`", "<", ">", "@"])
def test_summarize_refuses_each_unsafe_case_name(tmp_path, forbidden):
    # A second unsafe character must not mask removal of this one's guard.
    path = tmp_path / "report.json"
    path.write_text(json.dumps(_yaml_summary_report(["ab", f"a{forbidden}b"])))
    assert runner.summarize(path) == [
        "- `us:x` entries[0].tests[0]: `PolicyEngine/a@cccccccccccc:tests/a.yaml::ab` failed",
        "- pinned-tests artifact malformed (1 item(s)); the `pinned-tests` job's log has the details.",
    ]


@pytest.mark.parametrize("name", [
    "\u034f", "\u115f", "\u1160", "\u115f\u1160", "\u17b4", "\u17b5", "\u180b", "\u180d", "\u180f",
    "\u3164", "\ufe00", "\ufe0f", "\uffa0", "\U000e0100", "\U000e01ef",
])
def test_summarize_refuses_default_ignorable_case_names(tmp_path, name):
    # Every hard-coded range is tested at both boundaries, independently of
    # category C: all these characters are letters or combining marks.
    path = tmp_path / "report.json"
    path.write_text(json.dumps(_yaml_summary_report([name])))
    assert runner.summarize(path) == [
        "- pinned-tests artifact malformed (1 item(s)); the `pinned-tests` job's log has the details."
    ]


@pytest.mark.parametrize(("name", "displayed"), [
    ("a" * 200, "a" * 200),
    ("a" * 201, "a" * 200 + "…"),
    ("a" * 199 + " z", "a" * 199 + "…"),
    ("a" * 300_000, "a" * 200 + "…"),
])
def test_summarize_shortens_long_yaml_case_names(tmp_path, name, displayed):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(_yaml_summary_report([name])))
    assert runner.summarize(path) == [
        f"- `us:x` entries[0].tests[0]: `PolicyEngine/a@cccccccccccc:tests/a.yaml::{displayed}` failed"
    ]


def test_summarize_validates_the_whole_name_before_shortening(tmp_path):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(_yaml_summary_report(["a" * 300_000 + "`"])))
    assert runner.summarize(path) == [
        "- pinned-tests artifact malformed (1 item(s)); the `pinned-tests` job's log has the details."
    ]


def test_summarize_bounds_the_whole_output(tmp_path, capsys):
    path = tmp_path / "report.json"
    # Long names are shortened individually; large, valid paths still make
    # the character budget bind before the existing 100-line limit.
    report = _yaml_summary_report(["a" * 10_000] * 99, path="tests/" + "b" * 1000 + ".yaml")
    path.write_text(json.dumps(report))
    lines = runner.summarize(path)
    assert 1 < len(lines) < 100
    assert lines[-1] == f"- ... and {99 - len(lines) + 1} more; see the report artifact."
    assert all("::" + "a" * 200 + "…` failed" in line for line in lines[:-1])
    assert sum(len(line) + 1 for line in lines) <= 60_000
    assert runner.main(["--summarize", str(path)]) == 0
    assert len(capsys.readouterr().out) <= 60_000
    # The full prefix can consume the budget: even a repository name alone
    # must not force an oversized line into the result.
    path.write_text(json.dumps(_yaml_summary_report(["ab"], repo="PolicyEngine/" + "a" * 60_000)))
    assert runner.summarize(path) == ["- ... and 1 more; see the report artifact."]


def test_summarize_counts_utf16_units(tmp_path):
    # #1867 build report: a character outside the basic plane is two UTF-16
    # units, which GitHub counts; 99 names of 200 such characters made 57,608
    # characters but 77,408 units.
    path = tmp_path / "report.json"
    path.write_text(json.dumps(_yaml_summary_report(["\U0001F600" * 200] * 99, path="tests/" + "b" * 300 + ".yaml")))
    lines = runner.summarize(path)
    rendered = "\n".join(lines) + "\n"
    assert lines[-1].startswith("- ... and ")
    assert len(rendered.encode("utf-16-le")) // 2 <= 60_000


@pytest.mark.parametrize("extra", [0, 1])
def test_summarize_character_budget_boundary(tmp_path, extra):
    path = tmp_path / "report.json"
    # Exactly 60,000 rendered characters, including the CLI's final newline,
    # fit. One more is replaced by the bounded artifact pointer.
    prefix = "- `us:x` entries[0].tests[0]: `PolicyEngine/"
    suffix = "@cccccccccccc:tests/a.yaml::ab` failed\n"
    repo_name = "a" * (60_000 - len(prefix) - len(suffix) + extra)
    path.write_text(json.dumps(_yaml_summary_report(["ab"], repo="PolicyEngine/" + repo_name)))
    lines = runner.summarize(path)
    if extra:
        assert lines == ["- ... and 1 more; see the report artifact."]
    else:
        assert "\n".join(lines) + "\n" == prefix + repo_name + suffix


@pytest.mark.parametrize("extra", [0, 1])
def test_summarize_character_budget_counts_every_line_break(tmp_path, extra):
    path = tmp_path / "report.json"
    # Each detail line is 30,000 characters including its newline. A second
    # line one character longer must overflow; omitting accumulated newlines
    # from the budget would admit 60,001 rendered characters here.
    prefix = "- `us:x` entries[0].tests[0]: `PolicyEngine/"
    suffix = "@cccccccccccc:tests/a.yaml::ab` failed\n"
    repo_name = "a" * (30_000 - len(prefix) - len(suffix))
    report = _yaml_summary_report(["ab", "ab" + "c" * extra], repo="PolicyEngine/" + repo_name)
    path.write_text(json.dumps(report))
    lines = runner.summarize(path)
    if extra:
        assert lines[-1] == "- ... and 1 more; see the report artifact."
    else:
        assert len(lines) == 2
        assert len("\n".join(lines) + "\n") == 60_000
    assert len("\n".join(lines) + "\n") <= 60_000


def test_summarize_reserves_room_for_the_overflow_line(tmp_path):
    path = tmp_path / "report.json"
    # A line can fit by itself yet leave no room for the overflow pointer;
    # it must be removed as well when another line would exceed the budget.
    first = "- `us:x` entries[0].tests[0]: `PolicyEngine/"
    suffix = "@cccccccccccc:tests/a.yaml::ab` failed\n"
    repo_name = "a" * (60_000 - len(first) - len(suffix))
    path.write_text(json.dumps(_yaml_summary_report(["ab", "cd"], repo="PolicyEngine/" + repo_name)))
    assert runner.summarize(path) == ["- ... and 2 more; see the report artifact."]


def test_summarize_without_a_report(tmp_path):
    assert runner.summarize(tmp_path / "absent.json") == [runner.MISSING_ARTIFACT]
    (tmp_path / "list.json").write_text("[]")
    assert runner.summarize(tmp_path / "list.json") == [runner.MALFORMED_ARTIFACT]
    # Whether a 100,000-deep list parses depends on the Python build (3.13
    # raises RecursionError, 3.14 on CI parses it); either way it is an alarm.
    (tmp_path / "deep.json").write_text("[" * 100000 + "]" * 100000)
    assert runner.summarize(tmp_path / "deep.json") in ([runner.MISSING_ARTIFACT], [runner.MALFORMED_ARTIFACT])
    (tmp_path / "clean.json").write_text(json.dumps({"commits": [], "unrun": [], "issues": []}))
    assert runner.summarize(tmp_path / "clean.json") == ["No pinned test failed."]
    (tmp_path / "error.json").write_text(json.dumps({"commits": [], "unrun": [], "issues": ["runner error: x"]}))
    assert "1 issue(s) outside any pin" in runner.summarize(tmp_path / "error.json")[0]


def test_summarize_cli(tmp_path, capsys):
    (tmp_path / "clean.json").write_text(json.dumps({"commits": [], "unrun": [], "issues": []}))
    assert runner.main(["--summarize", str(tmp_path / "clean.json")]) == 0
    assert capsys.readouterr().out == "No pinned test failed.\n"


# ---------------------------------------------------------------------------
# Provenance: GitHub must say the commit is shipped code of the pinned repository


def http_error(code, remaining=None):
    headers = email.message.Message()
    if remaining is not None:
        headers["x-ratelimit-remaining"] = remaining
    return urllib.error.HTTPError("https://api.github.com/x", code, "reason", headers, None)


def api(answers):
    def get(path):
        answer = answers[path]
        if isinstance(answer, Exception):
            raise answer
        return answer
    return get


REPO_PATH = "/repos/PolicyEngine/a"
COMPARE_PATH = f"/repos/PolicyEngine/a/compare/main...{COMMIT}"
META = {"full_name": "PolicyEngine/a", "fork": False, "default_branch": "main"}


@pytest.mark.parametrize(
    ("answers", "shipped", "reason"),
    [
        ({REPO_PATH: META, COMPARE_PATH: {"status": "behind"}}, True, None),
        ({REPO_PATH: META, COMPARE_PATH: {"status": "identical"}}, True, None),
        ({REPO_PATH: META, COMPARE_PATH: {"status": "ahead"}}, False, "not reachable from PolicyEngine/a's default branch"),
        ({REPO_PATH: META, COMPARE_PATH: {"status": "diverged"}}, False, "compare says 'diverged'"),
        ({REPO_PATH: META, COMPARE_PATH: {}}, False, "compare says None"),
        ({REPO_PATH: META, COMPARE_PATH: []}, False, "not a JSON object"),
        # Found by test_provenance_is_total_and_exact: a list status raised TypeError.
        ({REPO_PATH: META, COMPARE_PATH: {"status": ["behind"]}}, False, "compare says ['behind']"),
        ({REPO_PATH: META, COMPARE_PATH: {"status": {"behind": 1}}}, False, "not reachable"),
        ({REPO_PATH: {**META, "full_name": "PolicyEngine/renamed"}}, False, "GitHub names this repository 'PolicyEngine/renamed'"),
        ({REPO_PATH: {**META, "full_name": "policyengine/a"}}, False, "GitHub names this repository"),
        ({REPO_PATH: {**META, "fork": True}}, False, "is a fork"),
        ({REPO_PATH: {k: v for k, v in META.items() if k != "fork"}}, False, "is a fork"),
        ({REPO_PATH: {**META, "default_branch": ""}}, False, "names no default branch"),
        ({REPO_PATH: ["x"]}, False, "not a JSON object"),
        ({REPO_PATH: http_error(404)}, False, "GitHub answered 404"),
        ({REPO_PATH: http_error(301)}, False, "renamed or moved"),
        ({REPO_PATH: http_error(403, "0")}, False, "rate limit is used up"),
        ({REPO_PATH: http_error(429, "0")}, False, "rate limit is used up"),
        ({REPO_PATH: http_error(403, "10")}, False, "GitHub answered 403"),
        ({REPO_PATH: META, COMPARE_PATH: http_error(404)}, False, "GitHub answered 404"),
        ({REPO_PATH: urllib.error.URLError("offline")}, False, "could not be read"),
        ({REPO_PATH: ValueError("not json")}, False, "could not be read"),
    ],
)
def test_commit_provenance(answers, shipped, reason):
    record = sc.commit_provenance("PolicyEngine/a", COMMIT, api(answers))
    assert record["shipped"] is shipped
    if reason is None:
        assert record["reason"] is None
    else:
        assert reason in record["reason"], record


@pytest.mark.parametrize("repo, commit", [("PolicyEngine/..", COMMIT), ("PolicyEngine/a", "abc"), ("x", COMMIT)])
def test_commit_provenance_refuses_malformed_input_without_asking(repo, commit):
    def never(path):
        raise AssertionError(path)
    assert sc.commit_provenance(repo, commit, never)["shipped"] is False


class _Handler(http.server.BaseHTTPRequestHandler):
    routes: dict = {}

    def do_GET(self):  # noqa: N802 - http.server's name
        code, headers, body = self.routes[self.path]
        self.send_response(code)
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def test_github_api_never_follows_a_redirect():
    # A renamed repository answers 301; following it would read another
    # repository. The real client refuses, and so does commit_provenance.
    _Handler.routes = {
        "/repos/PolicyEngine/old": (301, {"Location": "/repos/OutsideOwner/new"}, b""),
        "/repos/OutsideOwner/new": (200, {"Content-Type": "application/json"}, json.dumps(META).encode()),
        "/repos/PolicyEngine/a": (200, {"Content-Type": "application/json"}, json.dumps(META).encode()),
        f"/repos/PolicyEngine/a/compare/main...{COMMIT}": (200, {}, b'{"status": "behind"}'),
        "/repos/PolicyEngine/limited": (403, {"x-ratelimit-remaining": "0"}, b"{}"),
    }
    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        get = sc.github_api(base_url=f"http://127.0.0.1:{server.server_port}")
        assert sc.commit_provenance("PolicyEngine/a", COMMIT, get)["shipped"] is True
        moved = sc.commit_provenance("PolicyEngine/old", COMMIT, get)
        assert moved["shipped"] is False and "renamed or moved" in moved["reason"]
        limited = sc.commit_provenance("PolicyEngine/limited", COMMIT, get)
        assert limited["shipped"] is False and "rate limit" in limited["reason"]
    finally:
        server.shutdown()
        server.server_close()


# ---------------------------------------------------------------------------
# The workflow isolates the job that runs other repositories' code


def workflow():
    return yaml.safe_load(WORKFLOW.read_text())


def steps_text(job) -> str:
    return yaml.safe_dump(job, sort_keys=True)


def test_pinned_tests_job_holds_no_secrets():
    job = workflow()["jobs"]["pinned-tests"]
    assert job["permissions"] == {"contents": "read"}  # no id-token, no write
    text = steps_text(job)
    for forbidden in ("secrets.", "github.token", "GITHUB_TOKEN", "GH_TOKEN", "R2_", "ACTIONS_ID_TOKEN", "vars."):
        assert forbidden not in text, forbidden
    assert "env" not in job
    for step in job["steps"]:
        if str(step.get("uses", "")).startswith("actions/checkout@"):
            assert step["with"]["persist-credentials"] is False, step


def test_pin_provenance_job_holds_only_the_read_token_and_runs_no_pinned_code():
    # The pinned-tests job asks GitHub unauthenticated, and shared runners use
    # up the 60-request limit. This job asks with the run's read-only token
    # instead; it runs no pinned code, so no other repository's code sees it.
    jobs = workflow()["jobs"]
    job = jobs["pin-provenance"]
    assert job["permissions"] == {"contents": "read"}
    assert "env" not in job and "outputs" not in job
    text = steps_text(job)
    for forbidden in ("secrets.", "R2_", "ACTIONS_ID_TOKEN", "vars.", "uv", "pytest"):
        assert forbidden not in text, forbidden
    with_token = [step for step in job["steps"] if "github.token" in steps_text(step)]
    assert len(with_token) == 1 and with_token[0]["env"] == {"GH_TOKEN": "${{ github.token }}"}
    runs = [step["run"] for step in job["steps"] if "tools/pin_runner.py" in step.get("run", "")]
    assert len(runs) == 1 and "--record-provenance" in runs[0] and "--report" not in runs[0]
    for step in job["steps"]:
        if str(step.get("uses", "")).startswith("actions/checkout@"):
            assert step["with"]["persist-credentials"] is False, step
    uploads = [step for step in job["steps"] if str(step.get("uses", "")).startswith("actions/upload-artifact@")]
    assert len(uploads) == 1 and uploads[0]["with"]["name"] == "pin-provenance"
    assert uploads[0]["with"]["if-no-files-found"] == "error"
    # pinned-tests waits for the record and reads it.
    pinned = jobs["pinned-tests"]
    assert pinned["needs"] == "pin-provenance"
    downloads = [step for step in pinned["steps"] if str(step.get("uses", "")).startswith("actions/download-artifact@")]
    assert len(downloads) == 1 and downloads[0]["with"]["name"] == "pin-provenance"
    (run,) = [step["run"] for step in pinned["steps"] if "tools/pin_runner.py" in step.get("run", "")]
    assert "--provenance" in run


def test_the_alarm_fires_when_pin_provenance_fails():
    # A failed pin-provenance skips pinned-tests (it needs the record), and a
    # skipped pinned-tests is not a success, so main and scheduled runs still
    # raise the alarm: always() keeps the alarm job from being skipped too.
    jobs = workflow()["jobs"]
    assert jobs["pinned-tests"]["needs"] == "pin-provenance"
    alarm = jobs["alarm"]
    assert "pinned-tests" in alarm["needs"]
    condition = alarm["if"]
    assert condition.startswith("${{ always() &&")
    assert "needs.pinned-tests.result != 'success'" in condition
    assert "== 'failure'" not in condition


def test_pinned_tests_job_passes_its_result_only_as_a_json_artifact():
    jobs = workflow()["jobs"]
    job = jobs["pinned-tests"]
    assert "outputs" not in job
    text = steps_text(job)
    for channel in ("GITHUB_OUTPUT", "GITHUB_ENV", "GITHUB_PATH", "GITHUB_STEP_SUMMARY"):
        assert channel not in text, channel
    uploads = [step for step in job["steps"] if str(step.get("uses", "")).startswith("actions/upload-artifact@")]
    assert len(uploads) == 1
    assert uploads[0]["with"]["name"] == "pinned-tests"
    assert uploads[0]["with"]["path"].endswith("/pinned-tests.json")
    assert "needs.pinned-tests.outputs" not in WORKFLOW.read_text()
    runs = " ".join(step.get("run", "") for step in job["steps"])
    assert "tools/pin_runner.py" in runs and "--report" in runs
    tests = [step for step in job["steps"] if "tests/test_pin_runner.py" in step.get("run", "")]
    assert tests and tests[0]["env"]["AXIOM_PIN_RUNNER_TESTS_REQUIRED"] == "1"


def test_only_the_isolated_job_runs_other_repositories_code():
    # A runner command runs pinned code unless it only records provenance or
    # summarizes a report.
    jobs = workflow()["jobs"]
    for name, job in jobs.items():
        commands = [step.get("run", "") for step in job.get("steps", []) if "tools/pin_runner.py" in step.get("run", "")]
        runs_pins = any("--record-provenance" not in command and "--summarize" not in command for command in commands)
        assert runs_pins == (name == "pinned-tests"), name


def test_the_report_is_read_as_data():
    jobs = workflow()["jobs"]
    readers = [
        name for name, job in jobs.items()
        if any(
            str(step.get("uses", "")).startswith("actions/download-artifact@") and step["with"]["name"] == "pinned-tests"
            for step in job.get("steps", [])
        )
    ]
    assert readers == ["alarm"]
    for name in readers:
        for step in jobs[name]["steps"]:
            assert "${{" not in step.get("run", ""), (name, step.get("name"))
        runs = " ".join(step.get("run", "") for step in jobs[name]["steps"])
        assert re.search(r"pin_runner\.py\s*\\?\s*--summarize", runs)
    assert set(jobs["alarm"]["needs"]) == {"verify", "pinned-tests"}


def test_workflow_permissions_default_to_read():
    assert workflow()["permissions"] == {"contents": "read"}


def test_only_pull_requests_reuse_cached_results():
    # Pushes to main and the daily run execute every pin and save fresh results.
    steps = workflow()["jobs"]["pinned-tests"]["steps"]
    restores = [step for step in steps if str(step.get("uses", "")).startswith("actions/cache/restore@")]
    assert len(restores) == 1 and restores[0]["if"] == "github.event_name == 'pull_request'"
    assert any(str(step.get("uses", "")).startswith("actions/cache/save@") for step in steps)


def test_pinned_tests_runs_on_every_change_it_depends_on():
    # Round-8 hub condition: the job runs on every PR touching the runner,
    # the register or the workflow (and on pushes to main touching them).
    on = workflow()[True]  # PyYAML reads the `on:` key as True
    for event in ("pull_request", "push"):
        paths = on[event]["paths"]
        for needed in ("known-source-conflicts.yaml", "household-choices.yaml", "tools/source_conflicts.py",
                       "tools/household_choices.py", "tools/pin_runner.py", "tools/pin_oracle/**",
                       ".github/workflows/source-conflicts.yml"):
            assert needed in paths, (event, needed)
    for needed in ("tests/test_pin_runner.py", "tests/test_pin_runner_properties.py", "tests/test_household_choices.py",
                   "tests/test_household_choices_properties.py"):
        assert needed in on["pull_request"]["paths"]
    # A pass is cached against both files the pins come from.
    key = next(step for step in workflow()["jobs"]["pinned-tests"]["steps"]
               if str(step.get("uses", "")).startswith("actions/cache/save@"))["with"]["key"]
    assert "rulespec-us/household-choices.yaml" in key
    assert "schedule" in on


# ---------------------------------------------------------------------------
# The whole runner on fixture repositories

PYPROJECT = textwrap.dedent(
    """\
    [project]
    name = "fixture"
    version = "0"
    requires-python = ">=3.10"

    [project.optional-dependencies]
    dev = [{dev}]

    [build-system]
    requires = ["setuptools>=68"]
    build-backend = "setuptools.build_meta"

    [tool.setuptools]
    py-modules = []
    {extra}
    """
)

MAIN_TESTS = textwrap.dedent(
    """\
    import os

    import pytest


    def test_ok():
        assert True


    def test_no_secrets():
        assert "AXIOM_FIXTURE_SECRET" not in os.environ
        assert "GITHUB_TOKEN" not in os.environ
        assert os.environ["HOME"] != __REAL_HOME__


    class TestK:
        def test_m(self):
            pass


    @pytest.mark.parametrize("x", [1, 2])
    def test_p(x):
        assert x


    @pytest.mark.parametrize("x", [1, 2])
    def test_p_half(x):
        assert x == 1


    @pytest.mark.skip(reason="planted")
    def test_skipped():
        pass


    @pytest.mark.xfail(reason="planted")
    def test_xfailed():
        assert False


    @pytest.mark.xfail(reason="planted")
    def test_xpassed():
        pass


    @pytest.mark.xfail(reason="planted", strict=True)
    def test_strict_xpass():
        pass


    def test_fails():
        assert False


    def test_setup_error(broken):
        pass


    def test_conftest_skipped():
        pass


    def test_body_skip():
        pytest.skip("not today")
    """
)

CONFTEST = textwrap.dedent(
    """\
    import pytest


    @pytest.fixture
    def broken():
        raise RuntimeError("fixture error")


    def pytest_collection_modifyitems(items):
        for item in items:
            if item.name == "test_conftest_skipped":
                item.add_marker(pytest.mark.skip(reason="conftest says no"))
    """
)

# Round 6's shape: an alias of pytest.skip called at import skips the module.
PARTIAL_SKIP = textwrap.dedent(
    """\
    import pytest
    from functools import partial

    skip_if_missing = partial(pytest.skip, "optional data absent", allow_module_level=True)
    skip_if_missing()


    def test_x():
        pass
    """
)


# A stand-in for policyengine-core's YAML test runner, with the same shape:
# it calls pytest.main itself, with a plugin that collects YAML files into
# items whose name is "" until they run (so every case shares the node id
# `path::`), and it is started as `python -m <module> test <files>`.
FIXTURE_CORE = textwrap.dedent(
    """\
    import sys

    import pytest
    import yaml


    class Values(list):
        # A numpy array, as core returns one: values and their dtype.
        def __init__(self, values, dtype=None):
            super().__init__(values)
            self.dtype = dtype

        def tolist(self):
            return list(self)


    class EnumValues(Values):
        # An enum's values, as core's EnumArray holds them: indices, read by
        # name through decode_to_str().
        def __init__(self, names):
            super().__init__(range(len(names)), "int16")
            self.names = names

        def decode_to_str(self):
            return Values(self.names)


    class Population:
        def __init__(self, ids):
            self.ids = ids


    class Period(str):
        # core's Period, as far as the oracle reads it: a year or a month.
        @property
        def unit(self):
            return "month" if len(self.split("-")) == 2 else "year"

        @property
        def size(self):
            return 1


    class periods:
        # The simulation's own package's periods module, as core has one.
        @staticmethod
        def period(raw):
            return Period(str(raw))


    class Definition:
        def __init__(self, definition_period):
            self.definition_period = definition_period


    class TaxBenefitSystem:
        def __init__(self, definitions):
            self.definitions = definitions

        def get_variable(self, name, check_existence=False):
            return Definition(self.definitions.get(name, "year"))


    class Simulation:
        # policyengine-core's simulation, as the oracle reads it: inputs
        # (direct, or named by axes) and calculate(). Values come from the
        # case's `computed`.

        def __init__(self, test):
            case_input = test.get("input") or {}
            axes = [axis["name"] for group in case_input.get("axes") or [] for axis in group]
            self.input_variables = [key for key in case_input if "." not in key and key != "axes"] + axes
            self.computed = test.get("computed") or {}
            self.ids = test.get("ids") or {}
            self.default_calculation_period = "2024"
            self.tax_benefit_system = TaxBenefitSystem(test.get("definition_periods") or {})

        def calculate(self, variable, period):
            values = self.computed[variable]
            if values and all(isinstance(value, str) for value in values):
                return EnumValues(values)
            if all(isinstance(value, bool) for value in values):
                return Values(values, "bool")
            return Values(values, "float32" if any(isinstance(value, float) for value in values) else "int64")

        def get_variable_population(self, variable):
            return Population(self.ids.get(variable) or [f"u{index}" for index in range(len(self.computed[variable]))])


    class YamlFile(pytest.File):
        def collect(self):
            for test in yaml.safe_load(self.path.read_text()):
                yield YamlItem.from_parent(self, name="", test=test)


    class YamlItem(pytest.Item):
        def __init__(self, *, test, **kwargs):
            super().__init__(**kwargs)
            self.test = test

        def runtest(self):
            self.name = self.test.get("name", "")
            self.simulation = Simulation(self.test)
            output = self.test.get("output")
            if output == "skip":
                pytest.skip("planted")
            if isinstance(output, dict):  # a case that states variables, as a policy test does
                output = output.get("status")
            assert output == "ok", f"expected ok, got {output!r}"

        def reportinfo(self):
            return self.path, 0, self.test.get("name", "")


    class Plugin:
        def pytest_collect_file(self, parent, file_path):
            if file_path.suffix in (".yaml", ".yml"):
                return YamlFile.from_parent(parent, path=file_path)


    def main():
        args = sys.argv[1:]
        assert args[0] == "test", args
        paths = [arg for arg in args[1:] if arg.endswith((".yaml", ".yml"))]
        return pytest.main(["--capture", "no", "--maxfail", "0", "--tb", "short", *paths], plugins=[Plugin()])


    if __name__ == "__main__":
        sys.exit(main())
    """
)
FIXTURE_CORE_PYPROJECT = textwrap.dedent(
    """\
    [project]
    name = "fixture-yaml"
    version = "0"
    requires-python = ">=3.10"

    [project.optional-dependencies]
    dev = ["pytest==9.1.1", "pyyaml==6.0.3"]

    [build-system]
    requires = ["setuptools>=68"]
    build-backend = "setuptools.build_meta"

    [tool.setuptools]
    packages = ["fixture_core"]
    """
)
YAML_CASES = textwrap.dedent(
    """\
    - name: A case that passes (2024)
      output: ok
    - name: A case that fails
      output: bad
    - name: A skipped case
      output: skip
    - name: Twice
      output: ok
    - name: Twice
      output: bad
    - name: Both pass
      output: ok
    - name: Both pass
      output: ok
    """
)


CHOICE_CASES = textwrap.dedent(
    """\
    - name: Chooses to itemize
      input: {income: 1}
      computed: {itemizes: [true]}
      output: {status: ok}
    - name: Told to itemize
      input: {income: 1, itemizes: true}
      computed: {itemizes: [true]}
      output: {status: ok}
    - name: Forced through axes
      input: {income: 1, axes: [[{name: itemizes, count: 1, min: 1, max: 1}]]}
      computed: {itemizes: [true]}
      output: {status: ok}
    - name: Does not itemize
      input: {income: 1}
      computed: {itemizes: [false]}
      output: {status: ok}
    - name: Computes nothing for the choice
      input: {income: 1}
      output: {status: ok}
    - name: Chooses under a parameter override
      input: {gov.itemizing.compare_tax: false, income: 1}
      computed: {itemizes: [true]}
      output: {status: ok}
    - name: Chooses under a reform
      reforms: [some.reform]
      input: {income: 1}
      computed: {itemizes: [true]}
      output: {status: ok}
    - name: Chooses under an extension
      extensions: [some.extension]
      input: {income: 1}
      computed: {itemizes: [true]}
      output: {status: ok}
    - name: Files separately
      input: {income: 1}
      computed: {filing_status: [SEPARATE]}
      output: {status: ok}
    - name: Two entries pin this case
      input: {income: 1}
      computed: {itemizes: [false], always_true: [true]}
      output: {status: ok}
    - name: Only the first unit itemizes
      input: {income: 1}
      computed: {itemizes: [true, false]}
      ids: {itemizes: [first, second]}
      output: {status: ok}
    - name: A monthly choice read over a year
      period: 2024
      input: {income: 1}
      computed: {itemizes: [true]}
      definition_periods: {itemizes: month}
      output: {status: ok}
    - name: A monthly choice read over a month
      period: 2024-01
      input: {income: 1}
      computed: {itemizes: [true]}
      definition_periods: {itemizes: month}
      output: {status: ok}
    """
)


def _git(cwd: Path, *args: str) -> str:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(cwd),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_AUTHOR_NAME": "Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@invalid",
        "GIT_COMMITTER_NAME": "Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@invalid",
    }
    return subprocess.run([GIT, *args], cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout.strip()


def fixture_repo(base: Path, repo: str, files: dict[str, str], *, dev='"pytest==9.1.1"', extra="") -> str:
    """A git repository at base/<owner>/<name>; returns its one commit."""

    root = base / repo
    root.mkdir(parents=True)
    files = {"pyproject.toml": PYPROJECT.format(dev=dev, extra=extra), **files}
    for relative, text in files.items():
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text(text)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "fixture")
    return _git(root, "rev-parse", "HEAD")


class FakeGitHub:
    """GitHub's REST answers for fixture repositories, computed with git.

    A fixture repository is canonical and not a fork unless `meta` overrides
    that, its default branch is `main`, and compare main...<commit> is
    `identical` or `behind` exactly when git says the commit is reachable
    from main (`ahead` or `diverged` otherwise; an unknown commit is 404).
    Like GitHub, the fixture's URL still serves any object it holds."""

    def __init__(self, base: Path, meta=None, fail=None):
        self.base, self.meta, self.fail, self.calls = base, meta or {}, fail or {}, []

    def _git(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([GIT, "-C", str(root), *args], capture_output=True, text=True)

    def __call__(self, path: str):
        self.calls.append(path)
        if path in self.fail:
            raise self.fail[path]
        parts = path.strip("/").split("/")
        repo = "/".join(parts[1:3])
        root = self.base / repo
        if parts[0] != "repos" or not root.is_dir():
            raise http_error(404)
        if len(parts) == 3:
            return {"full_name": repo, "fork": False, "default_branch": "main", **self.meta.get(repo, {})}
        branch, _, commit = "/".join(parts[4:]).partition("...")
        if self._git(root, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            raise http_error(404)
        if self._git(root, "rev-parse", branch).stdout.strip() == commit:
            return {"status": "identical"}
        if self._git(root, "merge-base", "--is-ancestor", commit, branch).returncode == 0:
            return {"status": "behind"}
        if self._git(root, "merge-base", "--is-ancestor", branch, commit).returncode == 0:
            return {"status": "ahead"}
        return {"status": "diverged"}


def settings(tmp_path: Path, base: Path, **overrides) -> object:
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    overrides.setdefault("api", FakeGitHub(base))
    return runner.Settings(
        uv=UV or "uv", git=GIT, work=work, repo_url=f"file://{base}/{{repo}}", uv_dirs=runner.uv_dirs(UV) if UV else {},
        **overrides,
    )


def pinned(repo: str, commit: str, ids: list[str]) -> list[dict]:
    return [
        {"repo": repo, "commit": commit, "path": test_id.split("::", 1)[0], "name": test_id.split("::", 1)[1], "pins": ["reading"]}
        for test_id in ids
    ]


def outcomes(report) -> dict[str, str]:
    return {pin["id"]: pin["outcome"] for result in report["commits"] for pin in result["pins"]}


@pytest.fixture(scope="module")
def fixtures(tmp_path_factory):
    base = tmp_path_factory.mktemp("repos")
    commits = {
        "main": fixture_repo(base, "PolicyEngine/fixture-main", {
            "tests/conftest.py": CONFTEST,
            "tests/test_main.py": MAIN_TESTS.replace("__REAL_HOME__", repr(os.environ.get("HOME", ""))),
            "tests/test_partial_skip.py": PARTIAL_SKIP,
        }),
        "addopts": fixture_repo(
            base,
            "PolicyEngine/fixture-addopts",
            {"tests/test_sel.py": "import pytest\n\n\n@pytest.mark.slow\ndef test_slow():\n    pass\n\n\ndef test_fast():\n    pass\n"},
            extra='\n[tool.pytest.ini_options]\naddopts = "-m \'not slow\'"\nmarkers = ["slow: slow tests"]\n',
        ),
        "broken": fixture_repo(base, "TheAxiomFoundation/fixture-broken", {
            "tests/test_broken.py": "def test_x(:\n    pass\n",
            "tests/test_fine.py": "def test_y():\n    pass\n",
        }),
        "install": fixture_repo(
            base, "PolicyEngine/fixture-install", {"tests/test_a.py": "def test_a():\n    pass\n"},
            dev='"pytest==9.1.1", "axiom-no-such-package-for-pin-runner-tests==1.0"',
        ),
        "nopytest": fixture_repo(
            base, "PolicyEngine/fixture-nopytest", {"tests/test_a.py": "def test_a():\n    pass\n"}, dev="",
        ),
        # The round-8 reviewer's probes: a hook that changes the exit after
        # the oracle wrote, a failure after the oracle wrote, and a duplicated
        # item whose first run fails and second passes.
        "exit1": fixture_repo(base, "PolicyEngine/fixture-exit1", {
            "tests/test_a.py": "def test_a():\n    pass\n",
            "conftest.py": (
                "import pytest\n\n\n@pytest.hookimpl(hookwrapper=True)\n"
                "def pytest_sessionfinish(session, exitstatus):\n    yield\n    session.exitstatus = 1\n"
            ),
        }),
        "unconfigure": fixture_repo(base, "PolicyEngine/fixture-unconfigure", {
            "tests/test_a.py": "def test_a():\n    pass\n",
            "conftest.py": "def pytest_unconfigure(config):\n    raise RuntimeError('after the oracle wrote')\n",
        }),
        "duplicate": fixture_repo(base, "PolicyEngine/fixture-duplicate", {
            "tests/test_a.py": "calls = 0\n\n\ndef test_a():\n    global calls\n    calls += 1\n    assert calls == 2\n",
            "conftest.py": "def pytest_collection_modifyitems(items):\n    items[:] = [items[0], items[0]]\n",
        }),
        "yaml": fixture_repo(base, "PolicyEngine/fixture-yaml", {
            "pyproject.toml": FIXTURE_CORE_PYPROJECT,
            "fixture_core/__init__.py": "",
            "fixture_core/cli.py": FIXTURE_CORE,
            "tests/policy/cases.yaml": YAML_CASES,
            "tests/policy/passing.yaml": "- name: Only passing\n  output: ok\n",
            "tests/policy/choices.yaml": CHOICE_CASES,
            "tests/test_py.py": "def test_ok():\n    pass\n",
        }),
        "slow": fixture_repo(base, "PolicyEngine/fixture-slow", {
            "tests/test_slow.py": "import time\n\n\ndef test_sleep():\n    time.sleep(600)\n",
        }),
    }
    return base, commits


MAIN_EXPECTED = {
    "tests/test_main.py::test_ok": "passed",
    "tests/test_main.py::test_no_secrets": "passed",
    "tests/test_main.py::TestK::test_m": "passed",
    "tests/test_main.py::test_p": "passed",
    "tests/test_main.py::test_p_half": "failed",
    "tests/test_main.py::test_skipped": "skipped",
    "tests/test_main.py::test_xfailed": "xfail",
    "tests/test_main.py::test_xpassed": "xpass",
    "tests/test_main.py::test_strict_xpass": "failed",
    "tests/test_main.py::test_fails": "failed",
    "tests/test_main.py::test_setup_error": "error",
    "tests/test_main.py::test_conftest_skipped": "skipped",
    "tests/test_main.py::test_body_skip": "skipped",
    "tests/test_main.py::test_absent": "missing",
    "tests/test_partial_skip.py::test_x": "not collected",
    "tests/test_nofile.py::test_x": "missing file",
}


@needs_tools
def test_every_way_a_pin_fails_closed(tmp_path, fixtures, monkeypatch):
    base, commits = fixtures
    monkeypatch.setenv("AXIOM_FIXTURE_SECRET", "s3cret")
    monkeypatch.setenv("GITHUB_TOKEN", "s3cret")
    payload = register(*pinned("PolicyEngine/fixture-main", commits["main"], list(MAIN_EXPECTED)))
    report = runner.run_register(payload, settings(tmp_path, base))
    assert outcomes(report) == MAIN_EXPECTED
    (result,) = report["commits"]
    env = result["environment"]
    assert env["install"] == ["-e", ".[dev]"] and env["python_request"] == "3.14" and env["requires_python"] == ">=3.10"
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", env["exclude_newer"])
    assert env["pytest"] == "9.1.1" and env["inifile"] == "pyproject.toml"
    assert report["runner"]["uv"].startswith("uv ")
    by_id = {pin["id"]: pin for pin in result["pins"]}
    assert [case["outcome"] for case in by_id["tests/test_main.py::test_p"]["cases"]] == ["passed", "passed"]
    # test_p_half's first case passed; the pin did not. Twelve failing pins,
    # plus the process exit and the session status, each reported on its own.
    assert report["summary"] == {"pins": 16, "passed": 4, "cases_passed": 6, "issues": 14}
    assert result["pytest_exit"] == 1
    assert result["issues"] == ["pytest's process exited 1", "pytest's session reported exit status 1"]


@needs_tools
def test_repository_deselection_fails_the_pin(tmp_path, fixtures):
    base, commits = fixtures
    payload = register(*pinned("PolicyEngine/fixture-addopts", commits["addopts"], ["tests/test_sel.py::test_slow", "tests/test_sel.py::test_fast"]))
    report = runner.run_register(payload, settings(tmp_path, base))
    assert outcomes(report) == {"tests/test_sel.py::test_slow": "deselected", "tests/test_sel.py::test_fast": "passed"}
    assert report["commits"][0]["environment"]["addopts"] == ["-m", "not slow"]


@needs_tools
def test_a_collection_error_fails_every_pin_of_the_commit(tmp_path, fixtures):
    # pytest stops before running anything when a file fails to collect.
    base, commits = fixtures
    payload = register(*pinned("TheAxiomFoundation/fixture-broken", commits["broken"], ["tests/test_broken.py::test_x", "tests/test_fine.py::test_y"]))
    report = runner.run_register(payload, settings(tmp_path, base))
    assert outcomes(report) == {"tests/test_broken.py::test_x": "collection error", "tests/test_fine.py::test_y": "not run"}


@needs_tools
def test_an_install_failure_fails_every_pin(tmp_path, fixtures):
    base, commits = fixtures
    payload = register(*pinned("PolicyEngine/fixture-install", commits["install"], ["tests/test_a.py::test_a"]))
    report = runner.run_register(payload, settings(tmp_path, base))
    assert outcomes(report) == {"tests/test_a.py::test_a": "install failed"}
    assert report["commits"][0]["logs"]["install"]


@needs_tools
def test_a_nonzero_pytest_exit_fails_and_is_never_cached(tmp_path, fixtures):
    # Round-8 review: a sessionfinish hookwrapper set exit 1 after the oracle
    # wrote exit 0, and the runner reported and cached a pass.
    base, commits = fixtures
    cache = tmp_path / "cache"
    for name, repo in (("exit1", "PolicyEngine/fixture-exit1"), ("unconfigure", "PolicyEngine/fixture-unconfigure")):
        payload = register(*pinned(repo, commits[name], ["tests/test_a.py::test_a"]))
        report = runner.run_register(payload, settings(tmp_path, base, cache_dir=cache))
        (result,) = report["commits"]
        assert result["pins"][0]["outcome"] == "passed"  # the oracle's own view
        assert result["pytest_exit"] not in (0, None)
        assert any(issue.startswith("pytest's process exited") for issue in result["issues"]), result["issues"]
        assert report["issues"] and not runner.commit_passed(result)
    assert not cache.exists() or not any(cache.iterdir())


@needs_tools
def test_a_duplicated_item_cannot_hide_its_failure(tmp_path, fixtures):
    base, commits = fixtures
    payload = register(*pinned("PolicyEngine/fixture-duplicate", commits["duplicate"], ["tests/test_a.py::test_a"]))
    report = runner.run_register(payload, settings(tmp_path, base))
    assert outcomes(report) == {"tests/test_a.py::test_a": "error"}


@needs_git
def test_an_outside_fork_commit_is_never_fetched(tmp_path):
    # Round-8 review: GitHub serves every object of a fork network through
    # the parent's URL, so an unmerged commit from an outside fork passed the
    # owner check and was fetched. Provenance is now asked first.
    base = tmp_path / "repos"
    marker = tmp_path / "fork-code-ran"
    fixture_repo(base, "PolicyEngine/fixture-fork", {"tests/test_a.py": "def test_a():\n    pass\n"})
    root = base / "PolicyEngine" / "fixture-fork"
    (root / "tests" / "test_a.py").write_text(
        f"from pathlib import Path\n\nPath({str(marker)!r}).write_text('ran')\n\n\ndef test_a():\n    pass\n"
    )
    _git(root, "checkout", "-q", "-b", "outside")
    _git(root, "commit", "-qam", "an outside contributor's change")
    fork = _git(root, "rev-parse", "HEAD")
    _git(root, "update-ref", "refs/pull/1/head", fork)  # where GitHub keeps a fork PR's head
    _git(root, "checkout", "-q", "main")
    _git(root, "branch", "-D", "outside")
    # The parent's URL does serve the commit, as GitHub's does.
    probe = tmp_path / "probe"
    probe.mkdir()
    _git(probe, "init", "-q")
    _git(probe, "fetch", "-q", "--depth", "1", f"file://{root}", fork)
    shutil.rmtree(probe)

    fake = FakeGitHub(base)
    payload = register(*pinned("PolicyEngine/fixture-fork", fork, ["tests/test_a.py::test_a"]))
    report = runner.run_register(payload, settings(tmp_path, base, api=fake))
    assert outcomes(report) == {"tests/test_a.py::test_a": "untrusted commit"}
    assert "compare says 'ahead'" in report["issues"][0]
    assert report["commits"][0]["provenance"]["shipped"] is False
    assert not marker.exists()
    assert not any((tmp_path / "work").iterdir())  # nothing fetched, installed or run
    assert fake.calls == ["/repos/PolicyEngine/fixture-fork", f"/repos/PolicyEngine/fixture-fork/compare/main...{fork}"]


@needs_git
@pytest.mark.parametrize(
    ("meta", "fail", "commit", "reason"),
    [
        ({"full_name": "PolicyEngine/renamed"}, None, None, "GitHub names this repository 'PolicyEngine/renamed'"),
        ({"fork": True}, None, None, "is a fork"),
        ({}, None, "e" * 40, "GitHub answered 404"),
        ({}, "rate", None, "rate limit is used up"),
        ({}, "moved", None, "renamed or moved"),
    ],
)
def test_provenance_refusals_happen_before_any_fetch(tmp_path, meta, fail, commit, reason):
    base = tmp_path / "repos"
    head = fixture_repo(base, "PolicyEngine/fixture-meta", {"tests/test_a.py": "def test_a():\n    pass\n"})
    repo_path = "/repos/PolicyEngine/fixture-meta"
    failures = {"rate": {repo_path: http_error(403, "0")}, "moved": {repo_path: http_error(301)}}.get(fail)
    fake = FakeGitHub(base, meta={"PolicyEngine/fixture-meta": meta}, fail=failures)
    payload = register(*pinned("PolicyEngine/fixture-meta", commit or head, ["tests/test_a.py::test_a"]))
    report = runner.run_register(payload, settings(tmp_path, base, api=fake))
    assert outcomes(report) == {"tests/test_a.py::test_a": "untrusted commit"}
    assert reason in report["issues"][0], report["issues"]
    assert not any((tmp_path / "work").iterdir())


def test_an_unexpected_api_failure_refuses(tmp_path):
    # commit_provenance turns HTTP, URL, OS and decoding errors into refusals;
    # anything else the API client raises is caught by the runner and refuses
    # too, before any fetch.
    def broken(path):
        raise RuntimeError("an API client bug")

    work = tmp_path / "work"
    work.mkdir()
    settings_ = runner.Settings(uv="uv", git="git", work=work, api=broken)
    report = runner.run_register(register(*pinned("PolicyEngine/a", COMMIT, ["tests/test_a.py::test_a"])), settings_)
    assert outcomes(report) == {"tests/test_a.py::test_a": "untrusted commit"}
    assert "runner error: an API client bug" in report["issues"][0]
    assert not any(work.iterdir())


def test_recorded_provenance_is_used_without_asking(tmp_path):
    def unreachable(path):
        raise AssertionError(f"asked GitHub for {path}")

    work = tmp_path / "work"
    work.mkdir()
    recorded = {("PolicyEngine/a", COMMIT): {"repo": "PolicyEngine/a", "commit": COMMIT, "shipped": False, "reason": "recorded: a fork"}}
    settings_ = runner.Settings(uv="uv", git="git", work=work, api=unreachable, provenance=recorded)
    report = runner.run_register(register(*pinned("PolicyEngine/a", COMMIT, ["tests/test_a.py::test_a"])), settings_)
    assert outcomes(report) == {"tests/test_a.py::test_a": "untrusted commit"}
    assert "recorded: a fork" in report["issues"][0]
    assert not any(work.iterdir())


def _seed_passing_cache(settings_, payload):
    """A valid cached pass for every commit the payload pins, as _store
    would write it after a passing run."""

    groups, _ = runner.collect_pins(payload)
    for (repo, commit), pins in groups.items():
        key = runner.cache_key(repo, commit, pins, runner.runner_version())
        runner._store(settings_, key, {
            "repo": repo, "commit": commit, "issues": [], "logs": {}, "pytest_exit": 0,
            "pins": [{"entry": p.entry, "label": p.label, "id": p.id, "path": p.path, "name": p.name,
                      "outcome": "passed", "cases": [{"nodeid": p.id, "outcome": "passed"}]} for p in pins],
        })


def _unreachable(path):
    raise AssertionError(f"asked GitHub for {path}")


@pytest.mark.parametrize("shipped", [False, True])
def test_a_recorded_answer_decides_before_the_cache_and_asks_nothing(tmp_path, shipped):
    # #1843 fix review (P2): a recorded refusal refuses even with a valid
    # cached pass for that commit, and a recorded success serves the cached
    # pass without asking GitHub, whose unauthenticated limit runs out.
    work = tmp_path / "work"
    work.mkdir()
    cache = tmp_path / "cache"
    payload = register(*pinned("PolicyEngine/a", COMMIT, ["tests/test_a.py::test_a"]))
    record = {"repo": "PolicyEngine/a", "commit": COMMIT, "shipped": shipped, "reason": None if shipped else "recorded: a fork"}
    settings_ = runner.Settings(uv="uv", git="git", work=work, cache_dir=cache, api=_unreachable,
                                provenance={("PolicyEngine/a", COMMIT): record})
    _seed_passing_cache(settings_, payload)
    report = runner.run_register(payload, settings_)
    if shipped:
        assert outcomes(report) == {"tests/test_a.py::test_a": "passed"}
        assert report["commits"][0]["cached"] is True and report["commits"][0]["provenance"] == record
    else:
        assert outcomes(report) == {"tests/test_a.py::test_a": "untrusted commit"}
        assert report["commits"][0]["cached"] is False and "recorded: a fork" in report["issues"][0]
    assert not any(work.iterdir())  # nothing was fetched


@pytest.mark.parametrize(
    "recorded",
    [
        ("PolicyEngine/a", "d" * 40),  # the same repository, another commit
        ("PolicyEngine/b", COMMIT),  # another repository, the same commit
        ("PolicyEngine/A", COMMIT),  # the repository name in another case
        ("policyengine/a", COMMIT),  # the owner in another case
    ],
)
def test_a_record_serves_only_its_exact_repository_and_commit(tmp_path, recorded):
    # #1843 fix review (P2): a record for anything but the exact (repository,
    # commit) is not used, so the run asks GitHub, which here refuses.
    calls = []

    def refusing(path):
        calls.append(path)
        return {"full_name": "PolicyEngine/a", "fork": True, "default_branch": "main"}

    work = tmp_path / "work"
    work.mkdir()
    cache = tmp_path / "cache"
    payload = register(*pinned("PolicyEngine/a", COMMIT, ["tests/test_a.py::test_a"]))
    record = {"repo": recorded[0], "commit": recorded[1], "shipped": True, "reason": None}
    settings_ = runner.Settings(uv="uv", git="git", work=work, cache_dir=cache, api=refusing, provenance={recorded: record})
    _seed_passing_cache(settings_, payload)
    report = runner.run_register(payload, settings_)
    assert outcomes(report) == {"tests/test_a.py::test_a": "untrusted commit"}
    assert "is a fork" in report["issues"][0] and calls == ["/repos/PolicyEngine/a"]
    assert report["commits"][0]["cached"] is False and not any(work.iterdir())


def test_a_commit_the_record_lacks_is_asked_of_github(tmp_path):
    base = tmp_path / "repos"
    head = fixture_repo(base, "PolicyEngine/fixture-meta", {"tests/test_a.py": "def test_a():\n    pass\n"})
    fake = FakeGitHub(base, meta={"PolicyEngine/fixture-meta": {"fork": True}})
    other = {("PolicyEngine/b", COMMIT): {"repo": "PolicyEngine/b", "commit": COMMIT, "shipped": True, "reason": None}}
    payload = register(*pinned("PolicyEngine/fixture-meta", head, ["tests/test_a.py::test_a"]))
    report = runner.run_register(payload, settings(tmp_path, base, api=fake, provenance=other))
    assert "is a fork" in report["issues"][0] and fake.calls


def test_record_provenance_asks_with_the_token_and_runs_nothing(tmp_path, monkeypatch, capsys):
    base = tmp_path / "repos"
    head = fixture_repo(base, "PolicyEngine/fixture-meta", {"tests/test_a.py": "def test_a():\n    pass\n"})
    tokens = []

    def github_api(token=None, base_url=None):
        tokens.append(token)
        return FakeGitHub(base)

    monkeypatch.setattr(sc, "github_api", github_api)
    monkeypatch.setenv("GH_TOKEN", "read-only")
    register_path = tmp_path / "register.yaml"
    register_path.write_text(yaml.safe_dump(register(*pinned("PolicyEngine/fixture-meta", head, ["tests/test_a.py::test_a"]))))
    out = tmp_path / "out" / "provenance.json"
    assert runner.main(["--register", str(register_path), "--record-provenance", str(out)]) == 0
    assert tokens == ["read-only"]
    record = json.loads(out.read_text())
    assert record["provenance_version"] == runner.PROVENANCE_VERSION
    assert [(item["repo"], item["commit"], item["shipped"]) for item in record["records"]] == [("PolicyEngine/fixture-meta", head, True)]
    assert runner.load_provenance(out)[("PolicyEngine/fixture-meta", head)]["shipped"] is True
    assert "1 pinned commit(s); 0 not shipped" in capsys.readouterr().out
    assert not (tmp_path / "work").exists()
    # Without a register there is no record, and the command fails.
    assert runner.main(["--register", str(tmp_path / "absent.yaml"), "--record-provenance", str(tmp_path / "none.json")]) == 1
    assert not (tmp_path / "none.json").exists()


def test_record_provenance_covers_the_household_choices(tmp_path, monkeypatch):
    # The pinned-tests job holds no token, so a household choice's pin that
    # the record missed would be asked of GitHub unauthenticated.
    base = tmp_path / "repos"
    head = fixture_repo(base, "PolicyEngine/fixture-meta", {"tests/test_a.py": "def test_a():\n    pass\n"})
    other = fixture_repo(base, "PolicyEngine/fixture-choice", {"tests/test_b.py": "def test_b():\n    pass\n"})
    third = fixture_repo(base, "PolicyEngine/fixture-named", {"tests/test_c.py": "def test_c():\n    pass\n"})
    assert len({head, other, third}) == 3
    monkeypatch.setattr(sc, "github_api", lambda token=None, base_url=None: FakeGitHub(base))
    for repo in ("PolicyEngine/fixture-meta", "PolicyEngine/fixture-choice", "PolicyEngine/fixture-named"):
        monkeypatch.setitem(runner.YAML_RUNNERS, repo, ("fixture_core.cli", ()))
    root = tmp_path / "root"
    root.mkdir()
    (root / "known-source-conflicts.yaml").write_text(yaml.safe_dump(register(*pinned("PolicyEngine/fixture-meta", head, ["tests/test_a.py::test_a"]))))
    choice = {**OPTIMUM, "repo": "PolicyEngine/fixture-choice", "commit": other, "path": "tests/b.yaml", "name": "Itemizes"}
    out = tmp_path / "provenance.json"

    def recorded():
        return sorted((item["repo"], item["commit"]) for item in json.loads(out.read_text())["records"])

    assert runner.main(["--root", str(root), "--record-provenance", str(out)]) == 0
    assert recorded() == [("PolicyEngine/fixture-meta", head)]
    # The file beside the register is read, as a run reads it.
    (root / "household-choices.yaml").write_text(yaml.safe_dump(choices(choice)))
    assert runner.main(["--root", str(root), "--record-provenance", str(out)]) == 0
    assert recorded() == [("PolicyEngine/fixture-choice", other), ("PolicyEngine/fixture-meta", head)]
    # So is one named explicitly, in place of the file beside the register.
    # Its pin is a third commit, which only reading that file can record.
    named = tmp_path / "named.yaml"
    named.write_text(yaml.safe_dump(choices({**choice, "repo": "PolicyEngine/fixture-named", "commit": third})))
    assert runner.main(["--root", str(root), "--choices", str(named), "--record-provenance", str(out)]) == 0
    assert recorded() == [("PolicyEngine/fixture-meta", head), ("PolicyEngine/fixture-named", third)]
    # A named file that doesn't exist fails, with no record.
    assert runner.main(["--root", str(root), "--choices", str(tmp_path / "absent.yaml"), "--record-provenance", str(tmp_path / "none.json")]) == 1
    assert not (tmp_path / "none.json").exists()


def test_a_dangling_household_choices_link_fails_in_both_modes(tmp_path, monkeypatch):
    # A household-choices.yaml that links to nothing is not an absent file.
    # Read as absent, its pins would be neither recorded nor run, and both
    # modes would pass.
    monkeypatch.setattr(sc, "github_api", lambda token=None, base_url=None: FakeGitHub(tmp_path / "repos"))
    root = tmp_path / "root"
    root.mkdir()
    (root / "known-source-conflicts.yaml").write_text(yaml.safe_dump(register()))
    out = tmp_path / "provenance.json"
    report_path = tmp_path / "report.json"
    record = ["--root", str(root), "--record-provenance", str(out)]
    run = ["--root", str(root), "--report", str(report_path), "--uv", sys.executable, "--git", sys.executable]
    (root / "household-choices.yaml").symlink_to(tmp_path / "gone.yaml")
    assert runner.main(record) == 1
    assert not out.exists()
    assert runner.main(run) == 1
    assert json.loads(report_path.read_text())["issues"][0].startswith("runner error:")
    # With no file at all there are no household choices, and both pass.
    (root / "household-choices.yaml").unlink()
    assert runner.main(record) == 0
    assert json.loads(out.read_text())["records"] == []
    assert runner.main(run) == 0


@pytest.mark.parametrize("selection", ["root", "register", "choices"])
def test_a_run_finds_every_pin_it_selects_in_the_record(tmp_path, monkeypatch, selection):
    # Given the same selection, --record-provenance and a run read the same
    # files, so the run never asks GitHub (unauthenticated) about a pin.
    base = tmp_path / "repos"
    head = fixture_repo(base, "PolicyEngine/fixture-meta", {"tests/test_a.py": "def test_a():\n    pass\n"})
    other = fixture_repo(base, "PolicyEngine/fixture-choice", {"tests/test_b.py": "def test_b():\n    pass\n"})
    monkeypatch.setitem(runner.YAML_RUNNERS, "PolicyEngine/fixture-choice", ("fixture_core.cli", ()))
    folder = tmp_path / ("root" if selection == "root" else "elsewhere")
    folder.mkdir()
    register_path = folder / ("known-source-conflicts.yaml" if selection == "root" else "register.yaml")
    register_path.write_text(yaml.safe_dump(register(*pinned("PolicyEngine/fixture-meta", head, ["tests/test_a.py::test_a"]))))
    choices_path = tmp_path / "named.yaml" if selection == "choices" else folder / "household-choices.yaml"
    choice = {**OPTIMUM, "repo": "PolicyEngine/fixture-choice", "commit": other, "path": "tests/b.yaml", "name": "Itemizes"}
    choices_path.write_text(yaml.safe_dump(choices(choice)))
    args = {
        "root": ["--root", str(folder)],
        "register": ["--register", str(register_path)],
        "choices": ["--register", str(register_path), "--choices", str(choices_path)],
    }[selection]
    out = tmp_path / "provenance.json"
    monkeypatch.setattr(sc, "github_api", lambda token=None, base_url=None: FakeGitHub(base))
    assert runner.main([*args, "--record-provenance", str(out)]) == 0

    def refuse(path):
        raise AssertionError(f"the run asked GitHub for {path}")

    seen = []

    def run_register(payload, settings, choices=None):
        seen.append((payload, settings, choices))
        raise RuntimeError("stop before running anything")

    monkeypatch.setattr(sc, "github_api", lambda token=None, base_url=None: refuse)
    monkeypatch.setattr(runner, "run_register", run_register)
    tools = ["--uv", sys.executable, "--git", sys.executable]
    assert runner.main([*args, "--provenance", str(out), "--report", str(tmp_path / "report.json"), *tools]) == 1
    ((payload, settings, chosen),) = seen
    groups, _ = runner.collect_pins(payload, chosen)
    assert set(groups) == {("PolicyEngine/fixture-meta", head), ("PolicyEngine/fixture-choice", other)}
    assert set(settings.provenance) == set(groups)
    assert all(settings.provenance[key]["shipped"] is True for key in groups)


def pin_runner_selection(run: str) -> dict[str, str]:
    """The options that choose a pin_runner.py command's files, in a step's script."""

    words = shlex.split(run.replace("\\\n", " "))
    (start,) = [index for index, word in enumerate(words) if word.endswith("tools/pin_runner.py")]
    chosen: dict[str, str] = {}
    rest = words[start + 1:]
    for index, word in enumerate(rest):
        flag, equals, value = word.partition("=")
        if flag in ("--root", "--register", "--choices"):
            chosen[flag] = value if equals else rest[index + 1]
    return chosen


def test_pin_provenance_and_pinned_tests_select_the_same_files():
    # The record holds the commits of the files pin-provenance selected. If
    # pinned-tests selected others, their commits would be asked of GitHub
    # without a token, where the rate limit runs out.
    jobs = workflow()["jobs"]
    (record,) = [step["run"] for step in jobs["pin-provenance"]["steps"] if "tools/pin_runner.py" in step.get("run", "")]
    (run,) = [step["run"] for step in jobs["pinned-tests"]["steps"] if "tools/pin_runner.py" in step.get("run", "")]
    assert pin_runner_selection(record) == pin_runner_selection(run)
    assert pin_runner_selection(run)["--root"] == "rulespec-us"
    # The parser sees through line continuations and either spelling.
    assert pin_runner_selection("python a/tools/pin_runner.py --root r \\\n  --choices=c --report x") == {"--root": "r", "--choices": "c"}


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        "[]",
        '{"provenance_version": 2, "records": []}',
        '{"provenance_version": 1}',
        '{"provenance_version": 1, "records": [{"repo": "a/b", "commit": "c"}]}',
        '{"provenance_version": 1, "records": [{"repo": "a/b", "commit": "c", "shipped": "yes"}]}',
        '{"provenance_version": 1, "records": [{"repo": 1, "commit": 2, "shipped": false}]}',
        '{"provenance_version": 1, "records": [{"repo": 1, "commit": "' + "c" * 40 + '", "shipped": false}]}',
        '{"provenance_version": 1, "records": [{"repo": "a/b", "commit": 2, "shipped": false}]}',
        '{"provenance_version": 1, "records": ["a/b"]}',
    ],
)
def test_a_malformed_provenance_record_fails_the_run_closed(tmp_path, content):
    path = tmp_path / "provenance.json"
    path.write_text(content)
    with pytest.raises(ValueError):
        runner.load_provenance(path)
    register_path = tmp_path / "register.yaml"
    register_path.write_text(yaml.safe_dump(register(*pinned("PolicyEngine/a", COMMIT, ["tests/test_a.py::test_a"]))))
    report_path = tmp_path / "report.json"
    argv = ["--register", str(register_path), "--report", str(report_path), "--provenance", str(path), "--uv", "uv", "--git", "git"]
    assert runner.main(argv) == 1
    assert json.loads(report_path.read_text())["issues"][0].startswith("runner error:")


@needs_tools
def test_an_install_without_pytest_fails_every_pin(tmp_path, fixtures):
    base, commits = fixtures
    payload = register(*pinned("PolicyEngine/fixture-nopytest", commits["nopytest"], ["tests/test_a.py::test_a"]))
    report = runner.run_register(payload, settings(tmp_path, base))
    assert outcomes(report) == {"tests/test_a.py::test_a": "install failed"}
    assert report["issues"][0].endswith("the install (-e .[dev]) does not provide pytest")


YAML_EXPECTED = {
    "tests/policy/cases.yaml::A case that passes (2024)": "passed",
    "tests/policy/cases.yaml::A case that fails": "failed",
    "tests/policy/cases.yaml::A skipped case": "skipped",
    # #1843 review: a YAML pin names exactly one case. Two cases sharing the
    # name are ambiguous, whether one fails or both pass.
    "tests/policy/cases.yaml::Twice": "ambiguous",
    "tests/policy/cases.yaml::Both pass": "ambiguous",
    "tests/policy/cases.yaml::No such case": "missing",
    "tests/policy/missing.yaml::Anything": "missing file",
    # A Python pin at the same commit runs under pytest, separately.
    "tests/test_py.py::test_ok": "passed",
}


@needs_tools
def test_yaml_cases_run_through_the_repositorys_own_yaml_runner(tmp_path, fixtures, monkeypatch):
    base, commits = fixtures
    monkeypatch.setitem(runner.YAML_RUNNERS, "PolicyEngine/fixture-yaml", ("fixture_core.cli", ()))
    payload = register(*pinned("PolicyEngine/fixture-yaml", commits["yaml"], list(YAML_EXPECTED)))
    report = runner.run_register(payload, settings(tmp_path, base))
    assert outcomes(report) == YAML_EXPECTED
    (result,) = report["commits"]
    # Each kind ran once, with its own exit: pytest passed, the YAML run failed.
    assert result["runs"]["python"]["exit"] == 0
    assert result["runs"]["yaml"]["exit"] == 1
    assert result["runs"]["yaml"]["files"] == ["tests/policy/cases.yaml"]
    assert result["pytest_exit"] == 1
    assert "the YAML test runner's process exited 1" in result["issues"]
    by_id = {pin["id"]: pin for pin in result["pins"]}
    assert "2 cases in tests/policy/cases.yaml are named 'Both pass'" in by_id["tests/policy/cases.yaml::Both pass"]["detail"]


@needs_tools
def test_a_passing_yaml_commit_passes_and_is_cached(tmp_path, fixtures, monkeypatch):
    base, commits = fixtures
    monkeypatch.setitem(runner.YAML_RUNNERS, "PolicyEngine/fixture-yaml", ("fixture_core.cli", ()))
    payload = register(*pinned("PolicyEngine/fixture-yaml", commits["yaml"], [
        "tests/policy/passing.yaml::Only passing", "tests/policy/cases.yaml::A case that passes (2024)",
    ]))
    cache = tmp_path / "cache"
    first = runner.run_register(payload, settings(tmp_path, base, cache_dir=cache))
    assert outcomes(first) == {"tests/policy/passing.yaml::Only passing": "passed",
                               "tests/policy/cases.yaml::A case that passes (2024)": "passed"}
    assert first["issues"] == [] and first["commits"][0]["pytest_exit"] == 0
    second = runner.run_register(payload, settings(tmp_path, base, cache_dir=cache))
    assert second["commits"][0]["cached"] is True


@needs_tools
def test_an_install_without_the_yaml_runner_fails_closed(tmp_path, fixtures, monkeypatch):
    base, commits = fixtures
    monkeypatch.setitem(runner.YAML_RUNNERS, "PolicyEngine/fixture-yaml", ("no_such_core.cli", ()))
    payload = register(*pinned("PolicyEngine/fixture-yaml", commits["yaml"], ["tests/policy/passing.yaml::Only passing"]))
    report = runner.run_register(payload, settings(tmp_path, base))
    assert outcomes(report) == {"tests/policy/passing.yaml::Only passing": "install failed"}
    assert "does not provide no_such_core" in report["issues"][0]


@needs_tools
def test_a_timeout_fails_the_pin(tmp_path, fixtures):
    base, commits = fixtures
    payload = register(*pinned("PolicyEngine/fixture-slow", commits["slow"], ["tests/test_slow.py::test_sleep"]))
    report = runner.run_register(payload, settings(tmp_path, base, timeout=20))
    assert outcomes(report) == {"tests/test_slow.py::test_sleep": "timed out"}
    assert report["commits"][0]["seconds"]["total"] < 40


@needs_tools
def test_an_unfetchable_commit_fails_the_pin(tmp_path, fixtures):
    # Provenance would refuse an unknown commit first; this API vouches for
    # it, so the fetch itself must fail closed.
    base, _ = fixtures

    def vouches(path):
        repo = "/".join(path.strip("/").split("/")[1:3])
        return {"status": "behind"} if "/compare/" in path else {"full_name": repo, "fork": False, "default_branch": "main"}

    payload = register(*pinned("PolicyEngine/fixture-main", "e" * 40, ["tests/test_main.py::test_ok"]))
    report = runner.run_register(payload, settings(tmp_path, base, api=vouches))
    assert outcomes(report) == {"tests/test_main.py::test_ok": "fetch failed"}


@needs_tools
def test_a_repository_off_the_allowlist_never_runs(tmp_path, fixtures):
    base, commits = fixtures
    # The commit exists under an allowed owner; a copy elsewhere must not be fetched.
    shutil.copytree(base / "PolicyEngine" / "fixture-main", base / "SomeoneElse" / "fixture-main")
    payload = register(*pinned("SomeoneElse/fixture-main", commits["main"], ["tests/test_main.py::test_ok"]))
    report = runner.run_register(payload, settings(tmp_path, base))
    assert report["commits"] == []
    assert report["issues"] == [
        "us:fixture entries[0].tests[0] tests/test_main.py::test_ok: the runner won't execute pins in "
        "SomeoneElse/fixture-main (allowed owners: TheAxiomFoundation, PolicyEngine)."
    ]
    assert not any((tmp_path / "work").iterdir())


@needs_tools
def test_passing_results_are_cached_by_runner_version(tmp_path, fixtures, monkeypatch):
    base, commits = fixtures
    payload = register(*pinned("PolicyEngine/fixture-main", commits["main"], ["tests/test_main.py::test_ok"]))
    cache = tmp_path / "cache"
    first = runner.run_register(payload, settings(tmp_path, base, cache_dir=cache))
    second = runner.run_register(payload, settings(tmp_path, base, cache_dir=cache))
    assert [r["cached"] for r in first["commits"] + second["commits"]] == [False, True]
    assert outcomes(second) == {"tests/test_main.py::test_ok": "passed"}
    monkeypatch.setattr(runner, "runner_version", lambda: "another runner")
    third = runner.run_register(payload, settings(tmp_path, base, cache_dir=cache))
    assert third["commits"][0]["cached"] is False
    # Failures are never cached.
    failing = register(*pinned("PolicyEngine/fixture-main", commits["main"], ["tests/test_main.py::test_skipped"]))
    for _ in range(2):
        assert runner.run_register(failing, settings(tmp_path, base, cache_dir=cache))["commits"][0]["cached"] is False


@needs_tools
def test_cli_writes_the_report_and_fails_on_any_issue(tmp_path, fixtures, capsys, monkeypatch):
    base, commits = fixtures
    monkeypatch.setattr(sc, "github_api", lambda token=None, base_url=None: FakeGitHub(base))
    payload = register(*pinned("PolicyEngine/fixture-main", commits["main"], ["tests/test_main.py::test_ok", "tests/test_main.py::test_skipped"]))
    register_path = tmp_path / "register.yaml"
    register_path.write_text(yaml.safe_dump(payload))
    report_path = tmp_path / "out" / "report.json"
    code = runner.main(["--register", str(register_path), "--report", str(report_path), "--repo-url", f"file://{base}/{{repo}}"])
    assert code == 1
    report = json.loads(report_path.read_text())
    assert outcomes(report) == {"tests/test_main.py::test_ok": "passed", "tests/test_main.py::test_skipped": "skipped"}
    captured = capsys.readouterr()
    assert "1 of 2 pin(s) passed" in captured.out
    assert "tests/test_main.py::test_skipped: skipped" in captured.err
    assert runner.summarize(report_path) == [
        f"- `us:fixture` entries[0].tests[1]: `PolicyEngine/fixture-main@{commits['main'][:12]}:tests/test_main.py::test_skipped` skipped"
    ]


def test_cli_fails_closed_without_a_register(tmp_path):
    report_path = tmp_path / "report.json"
    assert runner.main(["--register", str(tmp_path / "absent.yaml"), "--report", str(report_path)]) == 1
    report = json.loads(report_path.read_text())
    assert report["issues"][0].startswith("runner error:")


@needs_tools
def test_an_optimum_pin_passes_only_when_its_case_shows_the_model_choosing(tmp_path, fixtures, monkeypatch):
    # The oracle records whether each pinned case changes the model, and what
    # its simulation computed for the decision variable and took as inputs;
    # the runner then requires the model's own choice, of an option other
    # than the default.
    base, commits = fixtures
    monkeypatch.setitem(runner.YAML_RUNNERS, "PolicyEngine/fixture-yaml", ("fixture_core.cli", ()))
    names = ("Chooses to itemize", "Told to itemize", "Forced through axes", "Does not itemize",
             "Computes nothing for the choice", "Chooses under a parameter override", "Chooses under a reform",
             "Chooses under an extension")
    tests = [
        {"repo": "PolicyEngine/fixture-yaml", "commit": commits["yaml"], "path": "tests/policy/choices.yaml", "name": name,
         "pins": ["optimum"], "variable": "itemizes", "chooses": True}
        for name in names
    ]
    report = runner.run_register(register(), settings(tmp_path, base), choices(*tests))
    assert outcomes(report) == {f"tests/policy/choices.yaml::{name}": "vacuous" for name in names[1:]} | {
        "tests/policy/choices.yaml::Chooses to itemize": "passed",
    }
    details = {pin["id"].split("::")[1]: pin.get("detail", "") for pin in report["commits"][0]["pins"]}
    assert "sets itemizes as an input" in details["Told to itemize"]
    assert "sets itemizes as an input" in details["Forced through axes"]
    assert "computed itemizes = False" in details["Does not itemize"]
    assert "could not be read: KeyError" in details["Computes nothing for the choice"]
    assert "changes the model (gov.itemizing.compare_tax)" in details["Chooses under a parameter override"]
    assert "changes the model (a reform or extension)" in details["Chooses under a reform"]
    assert "changes the model (a reform or extension)" in details["Chooses under an extension"]
    # The YAML run itself passed: vacuity is the runner's finding, not pytest's.
    assert report["commits"][0]["pytest_exit"] == 0
    # A pass is cached for its expectation only.
    cache = tmp_path / "cache"
    first = runner.run_register(register(), settings(tmp_path, base, cache_dir=cache), choices(tests[0]))
    second = runner.run_register(register(), settings(tmp_path, base, cache_dir=cache), choices(tests[0]))
    other = runner.run_register(register(), settings(tmp_path, base, cache_dir=cache), choices(tests[0], default="no"))
    assert [r["commits"][0]["cached"] for r in (first, second, other)] == [False, True, False]
    assert outcomes(other) == {"tests/policy/choices.yaml::Chooses to itemize": "passed"}
    # An enum is read by name, not by the index it is stored as.
    separately = {**tests[0], "name": "Files separately", "variable": "filing_status", "chooses": "separate"}
    enum = runner.run_register(register(), settings(tmp_path, base), choices(separately, default="joint"))
    assert outcomes(enum) == {"tests/policy/choices.yaml::Files separately": "passed"}
    # #1844 review round 3: two entries pin one case on two variables, and each
    # is judged on its own; a pin may name the instances that choose.
    shared = {**tests[0], "name": "Two entries pin this case"}
    always = {**shared, "variable": "always_true"}
    first = {**tests[0], "name": "Only the first unit itemizes", "instances": ["first"]}
    every = {**tests[0], "name": "Only the first unit itemizes"}
    payload = {"version": 1, "entries": [choice_entry(shared, first), {**choice_entry(always, every), "id": "other"}]}
    report = runner.run_register(register(), settings(tmp_path, base), payload)
    by_label = {pin["label"]: (pin["outcome"], pin.get("detail", "")) for pin in report["commits"][0]["pins"]}
    assert by_label["choices.entries[0].tests[0]"][0] == "vacuous"
    assert "computed itemizes = False" in by_label["choices.entries[0].tests[0]"][1]
    assert by_label["choices.entries[1].tests[0]"] == ("passed", "")
    assert by_label["choices.entries[0].tests[1]"] == ("passed", "")
    assert by_label["choices.entries[1].tests[1]"][0] == "vacuous"
    assert "computed itemizes = False for" not in by_label["choices.entries[1].tests[1]"][1]
    # Round 4 (P1): a monthly variable read over a year isn't one choice.
    yearly = {**tests[0], "name": "A monthly choice read over a year"}
    monthly = {**tests[0], "name": "A monthly choice read over a month"}
    report = runner.run_register(register(), settings(tmp_path, base), choices(yearly, monthly))
    by_label = {pin["label"]: (pin["outcome"], pin.get("detail", "")) for pin in report["commits"][0]["pins"]}
    assert by_label["choices.entries[0].tests[0]"][0] == "vacuous"
    assert "defined by month, over 2024" in by_label["choices.entries[0].tests[0]"][1]
    assert by_label["choices.entries[0].tests[1]"] == ("passed", "")
