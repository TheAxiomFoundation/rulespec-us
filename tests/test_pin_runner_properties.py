"""Property-based tests for tools/pin_runner.py's outcome classifier.

Invariants, for every oracle record:

1. Pass iff a reference predicate holds (Python tests and YAML cases, whose
   node ids repeat, read by collection index): `classify` passes a pin exactly when
   the runner is not distributed by xdist, the pinned file is in the checkout,
   pytest collected at least one case of the pinned function, none was
   deselected, and every case reported setup, call and teardown as `passed`
   with no xfail on the call. The predicate below is written independently of
   `case_outcome` and `worst` (a differential test of the classifier).
2. Fail closed: every pin gets an outcome from OUTCOMES, and a non-passing pin
   always carries a detail.
3. Commit level: `commit_passed` holds exactly when there is at least one
   pin, every pin passed, pytest's process exited 0 and the session's own
   status was 0. The process exit and the session status are separate
   conditions, and each alone fails the commit.
4. `worst` returns `passed` only when every outcome is `passed`, never an
   outcome outside its inputs other than `error`, and `case_outcome` never
   raises on any JSON-shaped record.
5. The cache key ignores pin order and repeats and changes with every
   component.
6. `summarize` prints, from any report, only text that fixed patterns allow:
   every backticked span is an entry id, a commit reference or a pin id, and
   the only free text from the run is a YAML case's name inside its pin id,
   which holds no backtick, @ or angle bracket, no category C or
   default-ignorable character, and no separator but a space. For any JSON
   artifact, any field of any type, `--summarize` exits 0 and prints either a
   valid summary or the malformed-artifact alarm.
7. Provenance: for any answers GitHub's API could give, `commit_provenance`
   never raises, and says a commit is shipped exactly when the canonical name
   is the pinned one, the repository says it is not a fork, and compare says
   `identical` or `behind`. Any exception from the API is a refusal.
8. A household choice's optimum pin (differential): `optimum_shown` accepts an
   oracle record exactly when a reference predicate, written independently,
   holds:
   - the chosen option is not the default (as the float32 numbers a model
     computes with);
   - the record holds a choice for the pin's own variable, which names that
     variable, could be read, and is not among the simulation's inputs (other
     variables' records, which other pins on the case read, never count);
   - the case changes no parameter and applies no reform or extension;
   - the value was read at one of the variable's own periods (any period for
     an eternity variable): a period of the definition's unit and size 1;
   - the model computed at least one value, and every value at the instances
     the pin names (every value when it names none, and none at an instance the
     record lacks) is the chosen option, compared at the stored dtype: enum
     and string values by name, never as numbers; integers exactly; float64
     as float64; and otherwise booleans by type, numbers as float32 and
     options by name.
"""

from __future__ import annotations

import array
import contextlib
import importlib.util
import io
import json
import re
import sys
import unicodedata
import urllib.error
from fractions import Fraction
from pathlib import Path

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, assume, given, settings, strategies as st  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sc = _load("source_conflicts", REPO_ROOT / "tools" / "source_conflicts.py")
runner = _load("pin_runner", REPO_ROOT / "tools" / "pin_runner.py")

SETTINGS = settings(max_examples=500, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
COMMIT = "c" * 40
PATHS = ["tests/test_a.py", "tests/test_b.py"]
YAML_PATH = "policyengine_us/tests/cases.yaml"
NAMES = ["test_x", "test_y", "TestK::test_x"]
YAML_NAMES = ["A case (2024)", "Another case"]
PIN_TARGETS = [(path, name) for path in PATHS for name in NAMES] + [(YAML_PATH, name) for name in YAML_NAMES]

outcome_values = st.sampled_from(["passed", "failed", "skipped", "rerun", None])
phase = st.fixed_dictionaries(
    {"outcome": outcome_values},
    optional={"xfail": st.booleans(), "message": st.text(max_size=5)},
)
PASSING = {when: {"outcome": "passed", "xfail": False} for when in ("setup", "call", "teardown")}
# A third of the records pass outright, so passing pins are common enough for
# the differential to compare both sides.
phase_record = st.one_of(
    st.just(PASSING),
    st.builds(lambda when, report: {**PASSING, when: report}, st.sampled_from(sorted(PASSING)), phase),
    st.dictionaries(st.sampled_from(["setup", "call", "teardown"]), st.one_of(phase, st.just("passed")), max_size=3),
)
json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(max_size=5),
    lambda children: st.lists(children, max_size=3) | st.dictionaries(st.text(max_size=8), children, max_size=3),
    max_leaves=10,
)


@st.composite
def records(draw):
    """(oracle record, pins, missing files)."""

    pins = [
        runner.Pin("us:x", f"entries[0].tests[{index}]", "PolicyEngine/a", COMMIT, path, name)
        for index, (path, name) in enumerate(
            draw(st.lists(st.sampled_from(PIN_TARGETS), min_size=1, max_size=4, unique=True))
        )
    ]
    items, reports = [], {}
    for path in PATHS + [YAML_PATH]:
        for name in YAML_NAMES if path == YAML_PATH else NAMES:
            for case in range(draw(st.integers(0, 2))):
                # A YAML runner gives every case in a file the same node id,
                # so only the collection index tells cases apart.
                nodeid = f"{path}::" if path == YAML_PATH else f"{path}::{name}[{case}]"
                index = len(items)
                items.append({"index": index, "nodeid": nodeid, "path": path, "name": name})
                if draw(st.booleans()) or draw(st.booleans()):
                    reports[str(index)] = draw(phase_record)
    indexes = [item["index"] for item in items]
    record = {
        "collected": items,
        "deselected": draw(st.lists(st.sampled_from(indexes), max_size=2)) if indexes else [],
        "collect_errors": [{"path": path} for path in draw(st.lists(st.sampled_from(PATHS), max_size=1))],
        "collect_skips": [{"path": path} for path in draw(st.lists(st.sampled_from(PATHS), max_size=1))],
        "reports": reports,
        "exitstatus": draw(st.sampled_from([0, 0, 1, 2, 5, None])),
        "xdist": draw(st.booleans()) and draw(st.booleans()),
    }
    missing = draw(st.lists(st.sampled_from(PATHS), max_size=1))
    process_exit = draw(st.sampled_from([0, 0, 0, 1, 2, 4, None]))
    return record, pins, missing, process_exit


def reference_passes(record, pin, missing) -> bool:
    """The specification of `passed`, written without the classifier's helpers."""

    if record["xdist"] or pin.path in missing:
        return False
    items = [item for item in record["collected"] if (item["path"], item["name"]) == (pin.path, pin.name)]
    if not items:
        return False
    # A YAML case is named, not parametrized: its pin must name exactly one.
    if pin.path.endswith((".yaml", ".yml")) and len(items) != 1:
        return False
    for item in items:
        if item["index"] in record["deselected"]:
            return False
        phases = record["reports"].get(str(item["index"])) or {}
        for when in ("setup", "call", "teardown"):
            report = phases.get(when)
            if not isinstance(report, dict) or report.get("outcome") != "passed":
                return False
        if phases["call"].get("xfail"):
            return False
    return True


# 1 and 2. Pass iff the reference predicate; fail closed otherwise.
@SETTINGS
@given(data=records())
def test_classify_passes_exactly_when_the_specification_does(data):
    record, pins, missing, process_exit = data
    results, _ = runner.classify(record, pins, process_exit=process_exit, missing_files=missing)
    assert len(results) == len(pins)
    for result, pin in zip(results, pins, strict=True):
        assert result["id"] == pin.id
        assert result["outcome"] in runner.OUTCOMES
        assert (result["outcome"] == runner.PASSED) == reference_passes(record, pin, missing), (result, pin)
        if result["outcome"] != runner.PASSED:
            assert result.get("detail")


# 3. Commit level.
@SETTINGS
@given(data=records())
def test_commit_level(data):
    record, pins, missing, process_exit = data
    results, issues = runner.classify(record, pins, process_exit=process_exit, missing_files=missing)
    every_pin_passed = all(reference_passes(record, pin, missing) for pin in pins)
    passed = runner.commit_passed({"pins": results, "issues": issues, "pytest_exit": process_exit})
    # Specification: the pins, the process exit and the session status, each
    # required on its own.
    assert passed == (every_pin_passed and process_exit == 0 and record["exitstatus"] == 0 and bool(pins))
    if process_exit not in (0, None):
        assert f"pytest's process exited {process_exit}" in issues
    if process_exit is not None and record["exitstatus"] != 0:
        assert f"pytest's session reported exit status {record['exitstatus']}" in issues


# 4. worst and case_outcome.
@SETTINGS
@given(outcomes=st.lists(st.sampled_from([*runner.CASE_SEVERITY, "unknown"]), max_size=5))
def test_worst(outcomes):
    result = runner.worst(outcomes)
    assert result in set(outcomes) | {"error"}
    assert (result == runner.PASSED) == (bool(outcomes) and all(outcome == runner.PASSED for outcome in outcomes))


@SETTINGS
@given(record=st.one_of(json_values, phase_record))
def test_case_outcome_is_total(record):
    assert runner.case_outcome(record if isinstance(record, dict) or record is None else {"call": record}) in runner.CASE_SEVERITY


# 5. Cache keys.
@SETTINGS
@given(
    names=st.lists(st.sampled_from(NAMES), min_size=1, max_size=4),
    other=st.sampled_from(["repo", "commit", "ids", "version"]),
    order=st.randoms(use_true_random=False),
)
def test_cache_key(names, other, order):
    pins = [runner.Pin("us:x", "l", "PolicyEngine/a", COMMIT, "tests/test_a.py", name) for name in names]
    shuffled = list(pins) + pins[:1]
    order.shuffle(shuffled)
    key = runner.cache_key("PolicyEngine/a", COMMIT, pins, "v1")
    assert key == runner.cache_key("PolicyEngine/a", COMMIT, shuffled, "v1")
    changed = {
        "repo": lambda: runner.cache_key("PolicyEngine/b", COMMIT, pins, "v1"),
        "commit": lambda: runner.cache_key("PolicyEngine/a", "d" * 40, pins, "v1"),
        "ids": lambda: runner.cache_key("PolicyEngine/a", COMMIT, [*pins, runner.Pin("us:x", "l", "PolicyEngine/a", COMMIT, "tests/test_z.py", "test_z")], "v1"),
        "version": lambda: runner.cache_key("PolicyEngine/a", COMMIT, pins, "v2"),
    }[other]()
    assert changed != key


# 6. The alarm summary validates its one free-text field, a YAML case name.
BACKTICKED = re.compile(r"`([^`]*)`")
SAFE_SPANS = (
    re.compile(r"[a-z0-9-]+:[a-z0-9-]+"),
    re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+@[0-9a-f]{12}(:[A-Za-z0-9_./-]+::[A-Za-z_][A-Za-z0-9_]*(::[A-Za-z_][A-Za-z0-9_]*)?)?"),
    re.compile(r"pinned-tests"),
)
YAML_CASE_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+@[0-9a-f]{12}:[A-Za-z0-9_./-]+\.ya?ml::(.+)", re.DOTALL)
DEFAULT_IGNORABLE_IN_NAME = re.compile(
    "[\u034f\u115f-\u1160\u17b4-\u17b5\u180b-\u180d\u180f\u3164\ufe00-\ufe0f\uffa0\U000e0100-\U000e01ef]"
)


def _safe_span(span):
    """A span the alarm may print: a fixed pattern, or a YAML case reference
    whose name has no forbidden delimiter, category C, default-ignorable
    character, non-space separator or surrounding whitespace."""

    if any(pattern.fullmatch(span) for pattern in SAFE_SPANS):
        return True
    match = YAML_CASE_REF.fullmatch(span)
    if match is None:
        return False
    name = match.group(1)
    return name == name.strip() and DEFAULT_IGNORABLE_IN_NAME.search(name) is None and not any(
        char in "`@<>" or (char != " " and unicodedata.category(char)[:1] in ("C", "Z")) for char in name
    )
FIXED_TEXT = re.compile(
    r"- (`[^`]*` entries\[[0-9]+\]\.tests\[[0-9]+\]: (`[^`]*` [a-z ]+|the runner can't execute this pin\.)"
    r"|`[^`]*`: the run of this commit reported an issue\."
    r"|pinned-tests artifact malformed( \([0-9]+ item\(s\)\))?; the `pinned-tests` job's log has the details\."
    r"|pinned-tests artifact missing or unreadable; the `pinned-tests` job's log has the details\."
    r"|The runner reported [0-9]+ issue\(s\) outside any pin; see the `pinned-tests` job's log\."
    r"|\.\.\. and [0-9]+ more; see the report artifact\.)"
    r"|No pinned test failed\."
)
# Any JSON value may sit where a string belongs (round-8 review: `outcome: []`
# made the summarizer raise).
text = st.one_of(
    st.text(max_size=20),
    st.sampled_from(["us:x", "PolicyEngine/a", COMMIT, "tests/test_a.py::test_x", "skipped", "entries[0].tests[1]",
                     "policyengine_us/tests/cases.yaml::A case (2024)", "policyengine_us/tests/cases.yaml::x `@team`",
                     "policyengine_us/tests/cases.yaml::Café", "policyengine_us/tests/cases.yaml::A case!",
                     "policyengine_us/tests/cases.yaml::a\u202eb", "policyengine_us/tests/cases.yaml::a\u00a0b",
                     "policyengine_us/tests/cases.yaml::a\u2028b", "policyengine_us/tests/cases.yaml:: a"]),
    st.builds(lambda name: f"policyengine_us/tests/cases.yaml::{name}", st.text(max_size=12)),
    json_values,
)
pin_dicts = st.fixed_dictionaries({"entry": text, "label": text, "id": text, "outcome": st.one_of(text, st.sampled_from(sorted(runner.OUTCOMES)))})
reports = st.fixed_dictionaries({
    "commits": st.one_of(
        st.lists(st.one_of(
            st.fixed_dictionaries({"repo": text, "commit": text, "issues": st.one_of(st.lists(text, max_size=1), text),
                                   "pins": st.one_of(st.lists(st.one_of(pin_dicts, json_values), max_size=3), text)}),
            json_values,
        ), max_size=3),
        json_values,
    ),
    "unrun": st.one_of(st.lists(st.fixed_dictionaries({"entry": text, "label": text, "reason": text}), max_size=2), json_values),
    "issues": st.one_of(st.lists(text, max_size=2), json_values),
})
# These reports have exactly one defect, so a different malformed field or
# a second forbidden character cannot mask an individually missing guard.
targeted_name_reports = st.builds(
    lambda before, forbidden, after: {
        "commits": [{"repo": "PolicyEngine/a", "commit": COMMIT, "issues": [], "pins": [{
            "entry": "us:x", "label": "entries[0].tests[0]", "outcome": "failed",
            "id": f"{YAML_PATH}::a{before}{forbidden}{after}b",
        }]}],
        "unrun": [], "issues": [],
    },
    st.text(alphabet="abcXYZ 012", max_size=8),
    st.sampled_from(["`", "<", ">", "@"]),
    st.text(alphabet="abcXYZ 012", max_size=8),
)


@SETTINGS
@given(report=st.one_of(reports, json_values, targeted_name_reports))
def test_summarize_prints_only_fixed_text(tmp_path_factory, report):
    path = tmp_path_factory.mktemp("summary") / "report.json"
    path.write_text(json.dumps(report))
    lines = runner.summarize(path)
    assert sum(len(line) + 1 for line in lines) <= 60_000
    for line in lines:
        assert "\n" not in line
        assert FIXED_TEXT.fullmatch(line), line
        for span in BACKTICKED.findall(line):
            assert _safe_span(span), (span, line)


@SETTINGS
@given(report=st.one_of(reports, json_values, targeted_name_reports))
def test_summarize_cli_exits_zero_on_any_artifact(tmp_path_factory, report):
    path = tmp_path_factory.mktemp("cli") / "report.json"
    path.write_text(json.dumps(report))
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        assert runner.main(["--summarize", str(path)]) == 0
    lines = out.getvalue().splitlines()
    assert lines and all(FIXED_TEXT.fullmatch(line) for line in lines), lines


# 7. Provenance.
api_answers = st.one_of(
    json_values,
    st.fixed_dictionaries(
        {},
        optional={
            "full_name": st.sampled_from(["PolicyEngine/a", "policyengine/a", "Other/a", None, 7]),
            "fork": st.sampled_from([False, True, None, 0, "false"]),
            "default_branch": st.sampled_from(["main", "master", "", None, 3]),
            "status": st.sampled_from(["identical", "behind", "ahead", "diverged", None, ["behind"]]),
        },
    ),
)
api_errors = st.sampled_from([
    urllib.error.URLError("offline"), ValueError("bad json"), OSError("reset"),
    urllib.error.HTTPError("u", 404, "x", None, None), urllib.error.HTTPError("u", 301, "x", None, None),
])


@SETTINGS
@given(meta=st.one_of(api_answers, api_errors), compare=st.one_of(api_answers, api_errors))
def test_provenance_is_total_and_exact(meta, compare):
    def get(path):
        answer = meta if path == "/repos/PolicyEngine/a" else compare
        if isinstance(answer, Exception):
            raise answer
        return answer

    record = sc.commit_provenance("PolicyEngine/a", COMMIT, get)
    expected = (
        isinstance(meta, dict)
        and meta.get("full_name") == "PolicyEngine/a"
        and meta.get("fork") is False
        and isinstance(meta.get("default_branch"), str)
        and bool(meta.get("default_branch"))
        and isinstance(compare, dict)
        and compare.get("status") in ("identical", "behind")
    )
    assert record["shipped"] is expected
    assert (record["reason"] is None) is expected


# ---------------------------------------------------------------------------
# 8. A household choice's optimum pin

_REF_NUMBER = re.compile(r"-?(0|[1-9][0-9]*)(\.[0-9]+)?")


def _ref_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return Fraction(repr(value)) if value == value and abs(value) != float("inf") else None
    if isinstance(value, str) and _REF_NUMBER.fullmatch(value):
        return Fraction(value)
    return None


def _ref_float32(number):
    """A float32, through the array module rather than struct."""

    try:
        return array.array("f", [float(number)])[0]
    except OverflowError:
        return None


def _ref_same(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    x, y = _ref_number(a), _ref_number(b)
    if x is not None or y is not None:
        return x is not None and y is not None and (x == y or (_ref_float32(x) is not None and _ref_float32(x) == _ref_float32(y)))
    return isinstance(a, str) and isinstance(b, str) and a.upper().replace("-", "_") == b.upper().replace("-", "_")


def _ref_same_stored(value, option, dtype):
    if dtype in ("enum", "object", "<U5"):
        return isinstance(value, str) and isinstance(option, str) and value.upper().replace("-", "_") == option.upper().replace("-", "_")
    if isinstance(dtype, str) and not isinstance(value, bool) and not isinstance(option, bool):
        x, y = _ref_number(value), _ref_number(option)
        if dtype in ("int16", "int32", "int64", "uint8"):
            return x is not None and y is not None and x == y
        if dtype == "float64":
            return x is not None and y is not None and float(x) == float(y)
    return _ref_same(value, option)


OPTION = st.sampled_from([True, False, "a", "b", "A", "0.5", "0.50", "1", 1, 0.5, "16777216", "16777217", "0.1000000001", "16777219"])
COMPUTED = st.lists(
    st.sampled_from([True, False, 0, 1, 3, 0.5, 0.1, 0.30000001192092896, "a", "A", "B", "16777220", 16777216.0, 16777217]), max_size=3
)
IDS = st.lists(st.sampled_from(["u0", "u1", "u2"]), max_size=3, unique=True)
RECORD = st.one_of(
    st.fixed_dictionaries({"variable": st.sampled_from(["v", "w"]), "error": st.just("KeyError: 'v'")}),
    st.fixed_dictionaries({
        "variable": st.sampled_from(["v", "w"]),
        "computed": COMPUTED,
        "ids": IDS,
        "dtype": st.sampled_from([None, "bool", "float32", "float64", "int64", "uint8", "enum", "object", "<U5"]),
        "definition_period": st.sampled_from(["year", "month", "eternity", None]),
        "period_unit": st.sampled_from(["year", "month"]),
        "period_size": st.sampled_from([1, 1, 2]),
        "input_variables": st.lists(st.sampled_from(["v", "w", "age"]), max_size=2),
    }),
)
ITEMS = st.one_of(
    st.none(),
    st.fixed_dictionaries(
        {
            "case": st.fixed_dictionaries({
                "parameters": st.lists(st.sampled_from(["gov.x.y", "gov.z"]), max_size=1),
                "reforms": st.booleans(),
                "extensions": st.booleans(),
            }),
        },
        optional={"choices": st.dictionaries(st.sampled_from(["v", "w"]), RECORD, max_size=2)},
    ),
)
INSTANCES = st.one_of(st.none(), st.lists(st.sampled_from(["u0", "u1", "u9"]), min_size=1, max_size=2, unique=True).map(tuple))


@SETTINGS
@given(ITEMS, OPTION, OPTION, INSTANCES)
def test_optimum_shown_matches_a_reference(item, chooses, default, instances):
    case = (item or {}).get("case") or {}
    choices = (item or {}).get("choices")
    choice = choices.get("v") if isinstance(choices, dict) else None
    computed = (choice or {}).get("computed") or []
    ids = (choice or {}).get("ids")
    if instances is None:
        selected = computed
    elif isinstance(ids, list) and len(ids) == len(computed) and all(each in ids for each in instances):
        selected = [computed[ids.index(each)] for each in instances]
    else:
        selected = None
    expected = (
        item is not None
        and isinstance(choices, dict)
        and not _ref_same(chooses, default)
        and isinstance(choice, dict)
        and choice.get("variable") == "v"
        and "error" not in choice
        and "v" not in choice.get("input_variables", [])
        and isinstance(choice.get("definition_period"), str)
        and (choice["definition_period"] == "eternity"
             or (choice.get("period_unit") == choice["definition_period"] and choice.get("period_size") == 1))
        and not case.get("parameters")
        and not case.get("reforms")
        and not case.get("extensions")
        and bool(computed)
        and selected is not None
        and all(_ref_same_stored(value, chooses, choice.get("dtype")) for value in selected)
    )
    assert (runner.optimum_shown(item, ("v", chooses, default, instances)) is None) is expected


# Round 5 (P3): random records are almost never accepted, so this property
# builds one that is, checks it is, then changes one field and checks the
# runner and the reference agree on the result.
ACCEPTABLE_OPTIONS = st.sampled_from([True, False, "a", "b", "0.5", "1", "16777219", "16777220"])
FIELD_CHANGES = st.sampled_from([
    None, "input", "override", "reform", "extension", "other value", "no value", "other variable", "missing record",
    "month at year", "two years", "no period", "error", "missing instance", "is the default",
])


@SETTINGS
@given(ACCEPTABLE_OPTIONS, ACCEPTABLE_OPTIONS, st.integers(1, 3), st.sampled_from([None, "bool", "float32", "int64", "enum", "object"]),
       st.booleans(), FIELD_CHANGES)
def test_optimum_shown_accepts_a_built_record_and_one_change_matters(chooses, default, count, dtype, named, change):
    assume(not _ref_same(chooses, default))
    dtype = {bool: "bool"}.get(type(chooses), dtype) if dtype is not None else None
    assume(_ref_same_stored(chooses, chooses, dtype))  # a dtype that holds the option
    ids = [f"u{index}" for index in range(count)]
    choice = {"variable": "v", "computed": [chooses] * count, "ids": ids, "dtype": dtype, "definition_period": "year",
              "period": "2026", "period_unit": "year", "period_size": 1, "input_variables": ["age"]}
    item = {"case": {"parameters": [], "reforms": False, "extensions": False}, "choices": {"v": choice}}
    instances = (ids[0],) if named else None
    assert runner.optimum_shown(item, ("v", chooses, default, instances)) is None
    if change is None:
        return
    if change == "input":
        choice["input_variables"].append("v")
    elif change == "override":
        item["case"]["parameters"] = ["gov.x"]
    elif change == "reform":
        item["case"]["reforms"] = True
    elif change == "extension":
        item["case"]["extensions"] = True
    elif change == "other value":
        other = next(option for option in (False, True, "zz", "0.25", "7") if not _ref_same_stored(option, chooses, dtype))
        choice["computed"][0] = other
    elif change == "no value":
        choice["computed"], choice["ids"] = [], []
    elif change == "other variable":
        choice["variable"] = "w"
    elif change == "missing record":
        item["choices"] = {"w": {**choice, "variable": "w"}}
    elif change == "month at year":
        choice["definition_period"] = "month"
    elif change == "two years":
        choice["period_size"] = 2
    elif change == "no period":
        del choice["period_unit"]
    elif change == "error":
        choice["error"] = "ValueError: x"
    elif change == "missing instance":
        instances = ("nobody",)
    elif change == "is the default":
        default = chooses
    assert runner.optimum_shown(item, ("v", chooses, default, instances)) is not None, change
