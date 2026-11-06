"""Run every pinned test at its pinned commit and ask pytest what happened.

A register entry's `tests` pin readings to tests in other repositories at
fixed commits, and a household choice's `tests` pin a consumer's default or
optimum (household-choices.yaml, beside the register;
tools/household_choices.py). `source_conflicts.py check` only screens a pin's
syntax: the file is a test_*.py file and defines the named function. Whether pytest
collects and passes that test depends on import-time code, conftest files,
plugins and ini settings, which no static check can decide. This runner asks
pytest.

For each (repository, commit) the register or the household choices pin, it:

0. asks GitHub, before fetching anything, whether the commit is shipped code
   of that repository (`source_conflicts.commit_provenance`), or reads the
   answer `--record-provenance` recorded (below): the canonical
   name must be exactly the pinned one, the repository must not be a fork,
   and the commit must be reachable from its default branch. GitHub serves
   every object of a fork network through the parent's URL, so the owner in
   the URL proves nothing by itself;
1. fetches the commit (`git fetch --depth 1`) into a fresh checkout;
2. picks a Python: the newest of PYTHONS that the project's `requires-python`
   allows (the newest of PYTHONS when it has none);
3. makes a fresh virtual environment and installs the repository's own test
   install (INSTALL_SPECS, default `-e ".[dev]"`) with
   `uv pip install --exclude-newer <the commit's committer date>`, so
   registry packages resolve as they did when the commit was made (Git and
   direct-URL requirements follow the repository's own declarations);
4. runs pytest from the checkout root on the pinned Python test files, under
   the repository's own ini, conftest files and addopts, with
   `-p no:cacheprovider`, a scratch `--basetemp` and the oracle plugin
   (tools/pin_oracle), which records what pytest collected, deselected and
   reported, and keeps only the pinned tests. Pinned YAML cases run in a
   second process, through the repository's own YAML test runner
   (YAML_RUNNERS; PolicyEngine-US's is policyengine-core), with the oracle
   loaded through PYTEST_ADDOPTS. Each process's exit is checked on its own;
5. classifies each pin from its run's record (`classify`).

Only the outcome `passed` passes: every collected case of the pinned function
passed its setup, call and teardown, none was deselected, skipped, xfailed or
xpassed, and pytest's process exited 0, checked independently of the
plugin's own record. A household choice's `optimum` pin must also be
non-vacuous (`optimum_shown`), or it is `vacuous`. It must be a YAML case that
runs the model as shipped, with no parameter override, reform or extension,
and whose own simulation computed the chosen option (`chooses`) for the pin's
own decision variable, at every entity instance the pin names (or at every
one), without taking that variable as an input. The case need not assert the
variable. The chosen option must differ from the entry's default, even as a
float32 number. Anything else is an
issue: an unshipped or unprovable commit, a fetch, venv or install failure, a
collection error, a missing or deselected test, a module-level skip,
`skipped`, `xfail`, `xpass`, `failed` or `error`, a per-commit timeout
(DEFAULT_TIMEOUT), and any exception in the runner itself.
Pins this runner cannot execute fail too: a pin in a repository outside
ALLOWED_OWNERS (matched exactly), a pin in this repository (no pinned
commit), and a YAML test case in a repository with no YAML_RUNNERS entry.

The claim, also stated in tools/README.md: the source-conflicts workflow's
`pinned-tests` job passing means each pinned test was collected and passed at
its pinned commit, in the repository's own install resolved as of that
commit's date, under its own pytest configuration.

The job that runs this executes code from other repositories, so it holds no
secrets and passes its result on only as the JSON report (`--report`). It
asks GitHub unauthenticated, and on shared runners GitHub's unauthenticated
limit (60 requests an hour) runs out. So provenance is recorded first, by
`--record-provenance`, in a job that runs no pinned code and holds the
workflow's read-only token (GH_TOKEN); the run reads it with `--provenance`
before any pinned code runs, and asks GitHub only for a commit it lacks.

Results that passed are cached (`--cache-dir`) under a key of the repository,
the commit, the sorted pinned ids and the runner version (a hash of this file
and the oracle plugin), so a runner change re-runs everything. Failures are
never cached, a cached record is re-checked against the commit it is read
for, and provenance is asked of GitHub again (or read from this run's
record) before any cached result is used. The workflow restores the cache only for pull requests, so pushes to
main and the daily run execute every pin.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time
import unicodedata
from collections.abc import Callable, Iterable, Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

import tomllib

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import source_conflicts as sc  # noqa: E402 - beside this file

ORACLE_DIR = TOOLS / "pin_oracle"
ORACLE_MODULE = "axiom_pin_oracle"
RUNNER_FILES = (Path(__file__).resolve(), ORACLE_DIR / f"{ORACLE_MODULE}.py")
REPORT_VERSION = 1
CHOICES_LABEL = "choices."  # prefix of a household choice's pin label

# The runner executes code only from these GitHub owners.
ALLOWED_OWNERS = ("TheAxiomFoundation", "PolicyEngine")
# `uv pip install` arguments, run from the checkout root. A repository without
# a `dev` extra that holds its test dependencies gets an entry here.
DEFAULT_INSTALL = ("-e", ".[dev]")
INSTALL_SPECS: dict[str, tuple[str, ...]] = {}
# A YAML test case runs only through its repository's own YAML test runner:
# `python -m <module> test <files> <args>` from the checkout root, with the
# oracle loaded through PYTEST_ADDOPTS (policyengine-core calls pytest.main
# itself, with its own plugin collecting the YAML files). A YAML pin in a
# repository with no entry here can't run.
YAML_RUNNERS: dict[str, tuple[str, tuple[str, ...]]] = {
    "PolicyEngine/policyengine-us": ("policyengine_core.scripts.policyengine_command", ("-c", "policyengine_us")),
}
YAML_SUFFIXES = (".yaml", ".yml")
# Newest first: the first that `requires-python` allows is used.
PYTHONS = ("3.14", "3.13", "3.12", "3.11", "3.10", "3.9")
DEFAULT_TIMEOUT = 15 * 60  # seconds per commit: fetch, environment, install and pytest
REPO_URL = "https://github.com/{repo}.git"
THREAD_CAPS = {"OMP_NUM_THREADS": "4", "OPENBLAS_NUM_THREADS": "4", "MKL_NUM_THREADS": "4"}
_LOG_TAIL = 4000

PASSED = "passed"
# Every outcome a pin can have; `summarize` prints nothing else.
OUTCOMES = frozenset({
    PASSED, "failed", "error", "skipped", "xfail", "xpass", "not run", "deselected", "missing", "missing file",
    "not collected", "collection error", "untrusted commit", "fetch failed", "install failed", "timed out",
    "runner error", "ambiguous", "vacuous",
})
# Worst first: a pin's outcome is the worst of its cases.
CASE_SEVERITY = ("error", "failed", "xpass", "xfail", "skipped", "not run", PASSED)


@dataclasses.dataclass(frozen=True)
class Pin:
    entry: str  # global id, <jurisdiction>:<id>
    label: str  # entries[i].tests[j]
    repo: str
    commit: str
    path: str
    name: str  # function, or Class::function; or a YAML case's name
    # A household choice's optimum pin: (decision variable, the option the
    # model must compute, the entry's default, which it must differ from, and
    # the entity instances that must compute it, or None for every one).
    expect: tuple[str, Any, Any, tuple[str, ...] | None] | None = None

    @property
    def id(self) -> str:
        """For display only: a test's identity is `key`, the (path, name) pair."""

        return f"{self.path}::{self.name}"

    @property
    def key(self) -> tuple[str, str]:
        return (self.path, self.name)

    @property
    def kind(self) -> str:
        return "yaml" if self.path.endswith(YAML_SUFFIXES) else "python"


class StepError(Exception):
    """A step that failed; `outcome` is what every pin of the commit gets."""

    def __init__(self, outcome: str, detail: str) -> None:
        super().__init__(detail)
        self.outcome = outcome
        self.detail = detail


# ---------------------------------------------------------------------------
# Which pins run


def allowed_repo(repo: str) -> bool:
    """The owner is exactly one of ALLOWED_OWNERS. GitHub's canonical spelling
    is required later (commit_provenance), so a case variant is refused."""

    owner, _, name = repo.partition("/")
    return owner in ALLOWED_OWNERS and name not in {"", ".", ".."}


def install_spec(repo: str) -> tuple[str, ...]:
    return INSTALL_SPECS.get(repo, DEFAULT_INSTALL)


def _unrunnable(item: Any) -> str | None:
    """Why the runner will not execute this pin, or None."""

    if not isinstance(item, Mapping):
        return "is not a mapping; run `source_conflicts.py check`"
    repo, commit, path, name = (item.get(key) for key in ("repo", "commit", "path", "name"))
    if repo is None:
        return (
            "is a test in this repository, which has no pinned commit; the runner executes only "
            "Python tests in other repositories"
        )
    if not (isinstance(repo, str) and sc.REPO_RE.fullmatch(repo)):
        return "has a malformed repo; run `source_conflicts.py check`"
    if not (isinstance(commit, str) and sc.COMMIT_RE.fullmatch(commit)):
        return "has a malformed commit; run `source_conflicts.py check`"
    if not (isinstance(path, str) and sc._relative_path(path)):
        return "has a malformed path; run `source_conflicts.py check`"
    if "::" in path:
        return "has `::` in its path, which would make its id ambiguous; run `source_conflicts.py check`"
    if path.endswith(YAML_SUFFIXES):
        if repo not in YAML_RUNNERS:
            return f"is a YAML test case in {repo}, which has no YAML test runner here (YAML_RUNNERS)"
        if not (isinstance(name, str) and name.strip() and "\n" not in name and "\r" not in name):
            return "has a malformed name; run `source_conflicts.py check`"
        if not allowed_repo(repo):
            return f"the runner won't execute pins in {repo} (allowed owners: {', '.join(ALLOWED_OWNERS)})"
        return None
    if not path.endswith(".py"):
        return "is neither a Python test nor a YAML test case"
    if not (isinstance(name, str) and sc.TEST_NAME_RE.fullmatch(name)):
        return "has a malformed name; run `source_conflicts.py check`"
    if not sc.python_test_file(path):
        return "is not in a test_*.py file"
    if not allowed_repo(repo):
        return f"the runner won't execute pins in {repo} (allowed owners: {', '.join(ALLOWED_OWNERS)})"
    return None


def _option(value: Any) -> bool:
    return isinstance(value, bool) or (isinstance(value, str) and bool(value.strip()))


def _optimum_expectation(
    item: Mapping[str, Any], entry: Mapping[str, Any]
) -> tuple[tuple[str, Any, Any, tuple[str, ...] | None] | None, str | None]:
    """(expectation, None) for a well-formed optimum pin, else (None, why not)."""

    if not str(item.get("path")).endswith(YAML_SUFFIXES):
        return None, (
            "is an optimum pin on a Python test; the runner reads the decision variable only from a YAML case's "
            "simulation"
        )
    variable, chooses = item.get("variable"), item.get("chooses")
    default = entry.get("default").get("value") if isinstance(entry.get("default"), Mapping) else None
    if not (isinstance(variable, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", variable)):
        return None, "is an optimum pin without a decision variable; run `household_choices.py check`"
    if not (_option(chooses) and _option(default)):
        return None, "is an optimum pin without a chosen option and a default; run `household_choices.py check`"
    if same_option(chooses, default):
        return None, "is an optimum pin whose chosen option is the default, so it shows nothing; run `household_choices.py check`"
    instances = item.get("instances")
    if instances is not None and not (
        isinstance(instances, list)
        and instances
        and all(isinstance(each, str) and each.strip() and "\n" not in each for each in instances)
        and len(set(instances)) == len(instances)
    ):
        return None, "is an optimum pin with malformed instances; run `household_choices.py check`"
    return (variable, chooses, default, tuple(instances) if instances is not None else None), None


def collect_pins(payload: Any, choices: Any = None) -> tuple[dict[tuple[str, str], list[Pin]], list[dict[str, str]]]:
    """Runnable pins grouped by (repo, commit), and the pins that can't run:
    the register's, then the household choices' (labels `choices.entries[...]`)."""

    groups: dict[tuple[str, str], list[Pin]] = {}
    unrun: list[dict[str, str]] = []
    for prefix, source in (("", payload), (CHOICES_LABEL, choices)):
        entries = source.get("entries") if isinstance(source, Mapping) else None
        for index, entry in enumerate(entries if isinstance(entries, list) else []):
            if not isinstance(entry, Mapping):
                continue  # `check` reports it; it has no pins to run
            gid = f"{entry.get('jurisdiction')}:{entry.get('id')}"
            tests = entry.get("tests")
            for t_index, item in enumerate(tests if isinstance(tests, list) else []):
                label = f"{prefix}entries[{index}].tests[{t_index}]"
                reason = _unrunnable(item)
                expect = None
                if reason is None and prefix and isinstance(item.get("pins"), list) and "optimum" in item["pins"]:
                    expect, reason = _optimum_expectation(item, entry)
                if reason is not None:
                    where = item.get("path") if isinstance(item, Mapping) else None
                    name = item.get("name") if isinstance(item, Mapping) else None
                    unrun.append({"entry": gid, "label": label, "pin": f"{where}::{name}", "reason": reason})
                    continue
                pin = Pin(gid, label, item["repo"], item["commit"], item["path"], item["name"], expect)
                groups.setdefault((pin.repo, pin.commit), []).append(pin)
    return groups, unrun


# ---------------------------------------------------------------------------
# Classification (pure; tests/test_pin_runner.py covers every branch)


def case_outcome(phases: Mapping[str, Any] | None) -> str:
    """One collected case's outcome from its setup, call and teardown reports."""

    if not phases:
        return "not run"
    for report in phases.values():
        if not isinstance(report, Mapping) or report.get("outcome") not in ("passed", "failed", "skipped"):
            return "error"
    setup, call, teardown = (phases.get(when) for when in ("setup", "call", "teardown"))
    if setup is None:
        return "not run"
    if setup["outcome"] == "failed":
        return "error"
    if setup["outcome"] == "skipped":
        return "xfail" if setup.get("xfail") else "skipped"
    if call is None:
        return "not run"
    if call["outcome"] == "failed":
        return "failed"  # a strict xpass is reported as failed
    if call["outcome"] == "skipped":
        return "xfail" if call.get("xfail") else "skipped"
    if call.get("xfail"):
        return "xpass"
    if teardown is None or teardown["outcome"] != "passed":
        return "error"
    return PASSED


def worst(outcomes: Iterable[str]) -> str:
    """The worst case outcome; no cases, or one outside CASE_SEVERITY, is an error."""

    outcomes = list(outcomes)
    if not outcomes or any(outcome not in CASE_SEVERITY for outcome in outcomes):
        return "error"
    return min(outcomes, key=CASE_SEVERITY.index)


_NUMBER_RE = re.compile(r"-?(0|[1-9][0-9]*)(\.[0-9]+)?")


def _number(value: Any) -> Decimal | None:
    """A YAML number, or a decimal string, as a Decimal; None otherwise."""

    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(repr(value)) if math.isfinite(value) else None
    if isinstance(value, str) and _NUMBER_RE.fullmatch(value):
        return Decimal(value)
    return None


def option_name(value: str) -> str:
    """An enum option's name as a model writes it: the file's kebab-case
    `head-of-household` is PolicyEngine's `HEAD_OF_HOUSEHOLD`."""

    return value.upper().replace("-", "_")


def _float32(value: Decimal) -> float | None:
    """The value as a float32, as a model stores it; None if it can't be one."""

    try:
        return struct.unpack("f", struct.pack("f", float(value)))[0]
    except (OverflowError, struct.error, ValueError):
        return None


def same_option(a: Any, b: Any) -> bool:
    """One option of a choice: booleans by value and type (1 is not true);
    numbers and decimal strings as the float32 numbers a model computes with
    ("0.5" is 0.5 is "0.50", and 16777217 is 16777216); other strings by
    option name (`separate` is `SEPARATE`)."""

    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    x, y = _number(a), _number(b)
    if x is not None or y is not None:
        if x is None or y is None:
            return False
        if x == y:
            return True
        fx, fy = _float32(x), _float32(y)
        return fx is not None and fx == fy
    return isinstance(a, str) and isinstance(b, str) and option_name(a) == option_name(b)


# The dtypes of values that are names, never numbers: an enum (read by
# name), a numpy string, or Python objects (core's str variables).
_NAME_DTYPES = ("enum", "object", "str")


def same_stored(value: Any, option: Any, dtype: Any) -> bool:
    """Is a computed value the option, compared as the model stored it? An
    enum or a string by name, however numeric it looks ("16777219" is not
    "16777220"); an integer exactly; a float64 as a float64; and anything else
    (a boolean, a float32, or a value whose dtype is unknown) as
    `same_option` compares it."""

    if isinstance(dtype, str) and (dtype in _NAME_DTYPES or dtype.startswith(("<U", ">U", "|U", "<S", "|S"))):
        return isinstance(value, str) and isinstance(option, str) and option_name(value) == option_name(option)
    if isinstance(dtype, str) and not isinstance(value, bool) and not isinstance(option, bool):
        x, y = _number(value), _number(option)
        if dtype.startswith(("int", "uint")):
            return x is not None and y is not None and x == y
        if dtype == "float64":
            return x is not None and y is not None and float(x) == float(y)
    return same_option(value, option)


def optimum_shown(item: Any, expect: tuple[str, Any, Any, tuple[str, ...] | None]) -> str | None:
    """None when a pinned YAML case shows the model choosing the optimum,
    else why the pin is vacuous. The oracle's record of the case says:
    - `case`: whether it changes the model (parameter overrides, a reform or
      an extension);
    - `choices`: for each decision variable pinned on the case, what its own
      simulation computed, for which entity instances, in which dtype, and
      which variables it took as inputs, including through axes.
    The pin is judged on the record for its own variable only. The model must
    compute the chosen option for every instance the pin names (every instance
    when it names none), at one of the variable's own periods (a monthly
    variable read over a year is a sum, not a choice), without the variable
    as an input, in a case that runs it as shipped, and the option must not be
    the default. This shows the
    model choosing the non-default option, not which rule chose it: a
    convention that agrees in this case passes too, and so does a choice
    forced through an input upstream of the variable."""

    variable, chooses, default, instances = expect
    if same_option(chooses, default):
        return f"the chosen option {chooses!r} is the default (or the same number), so the case shows nothing"
    case = item.get("case") if isinstance(item, Mapping) else None
    choices = item.get("choices") if isinstance(item, Mapping) else None
    if not isinstance(case, Mapping) or not isinstance(choices, Mapping):
        return "the YAML runner did not expose the case or the model's choices"
    choice = choices.get(variable)
    if not isinstance(choice, Mapping) or choice.get("variable") != variable:
        return f"the YAML runner did not read {variable} from the case"
    if choice.get("error") is not None or not isinstance(choice.get("input_variables"), list):
        return f"the model's {variable} could not be read: {choice.get('error')}"
    if variable in choice["input_variables"]:
        return f"the case sets {variable} as an input (directly or through axes), so the model did not choose it"
    definition, unit, size = (choice.get(key) for key in ("definition_period", "period_unit", "period_size"))
    if not (isinstance(definition, str) and isinstance(unit, str) and isinstance(size, int)):
        return f"the YAML runner did not record the period it read {variable} at"
    if definition != "eternity" and (unit != definition or size != 1):
        return (
            f"the case reads {variable}, which is defined by {definition}, over {choice.get('period')}; core sums, "
            f"divides or picks a period to get that value, so it isn't one choice: pin a case for one {definition}"
        )
    overrides = case.get("parameters") if isinstance(case.get("parameters"), list) else []
    if overrides or case.get("reforms") or case.get("extensions"):
        changed = ", ".join(str(key) for key in overrides) or "a reform or extension"
        return f"the case changes the model ({changed}), so it does not show the model choosing as shipped"
    computed = choice.get("computed")
    if not (isinstance(computed, list) and computed):
        return f"the model computed no value of {variable}"
    ids = choice.get("ids")
    if instances is None:
        values = [(None, value) for value in computed]
    else:
        if not (isinstance(ids, list) and len(ids) == len(computed)):
            return f"the YAML runner did not record which instance computed each value of {variable}"
        position = {str(each): index for index, each in enumerate(ids)}
        missing = [each for each in instances if each not in position]
        if missing:
            return f"the case has no instance {missing[0]!r} of {variable}'s entity"
        values = [(each, computed[position[each]]) for each in instances]
    for instance, value in values:
        if not same_stored(value, chooses, choice.get("dtype")):
            where = f" for {instance}" if instance is not None else ""
            return f"the model computed {variable} = {value!r}{where}, not the chosen option {chooses!r}"
    return None


def _for_path(records: Any, path: str) -> list[Mapping[str, Any]]:
    return [record for record in records or [] if isinstance(record, Mapping) and record.get("path") == path]


def classify(
    oracle: Mapping[str, Any],
    pins: Iterable[Pin],
    *,
    process_exit: int | None,
    missing_files: Iterable[str] = (),
    runner: str = "pytest",
) -> tuple[list[dict[str, Any]], list[str]]:
    """(one result per pin, commit-level issues) from the oracle's record and
    the test process's exit code (None when it did not run). The two are
    checked independently: a repository hook can change the session's exit
    status after the plugin has written its record. Cases are matched by
    (path, name) and read by their collection index, never by node id, which
    a YAML runner repeats for every case in a file."""

    missing_files = set(missing_files)
    commit_issues: list[str] = []
    if oracle.get("xdist"):
        commit_issues.append("pytest-xdist distributes this run (the repository's addopts); the runner needs one process")
    collected = [item for item in oracle.get("collected") or [] if isinstance(item, Mapping)]
    deselected = set(oracle.get("deselected") or [])
    reports = oracle.get("reports") or {}
    results = []
    for pin in pins:
        result: dict[str, Any] = {
            "entry": pin.entry, "label": pin.label, "id": pin.id, "path": pin.path, "name": pin.name, "cases": [],
        }
        items = [item for item in collected if item.get("path") == pin.path and item.get("name") == pin.name]
        if pin.path in missing_files:
            result.update(outcome="missing file", detail=f"{pin.path} is not in the checkout")
        elif oracle.get("xdist"):
            result.update(outcome="error", detail=commit_issues[0])
        elif not items:
            errors = _for_path(oracle.get("collect_errors"), pin.path)
            skips = _for_path(oracle.get("collect_skips"), pin.path)
            if errors:
                result.update(outcome="collection error", detail=f"pytest could not collect {pin.path}")
            elif skips:
                result.update(outcome="not collected", detail=f"pytest skipped {pin.path} at collection")
            else:
                result.update(outcome="missing", detail=f"{pin.id} is not in pytest's collection")
        elif pin.kind == "yaml" and len(items) > 1:
            # A YAML case is named, not parametrized: a pin names exactly one.
            result.update(
                outcome="ambiguous",
                detail=f"{len(items)} cases in {pin.path} are named {pin.name!r}; a YAML pin names exactly one case",
            )
        elif any(item.get("index") in deselected for item in items):
            result.update(outcome="deselected", detail="the repository's own configuration deselects it")
        else:
            cases = [
                {"nodeid": item.get("nodeid"), "index": item.get("index"),
                 "outcome": case_outcome(reports.get(str(item.get("index"))))}
                for item in items
            ]
            result["cases"] = cases
            outcome = worst(case["outcome"] for case in cases)
            result["outcome"] = outcome
            if outcome != PASSED:
                bad = [case["nodeid"] for case in cases if case["outcome"] != PASSED]
                result["detail"] = f"{len(bad)} of {len(cases)} case(s) did not pass, first {bad[0]}"
            elif pin.expect is not None:
                # A household choice's optimum: every case of the pin must show
                # the model choosing an option other than the default.
                reason = next(filter(None, (optimum_shown(item, pin.expect) for item in items)), None)
                if reason is not None:
                    result.update(outcome="vacuous", detail=reason)
        results.append(result)
    if process_exit is None:
        commit_issues.append(f"{runner} did not run")
    else:
        if process_exit != 0:
            commit_issues.append(f"{runner}'s process exited {process_exit}")
        if oracle.get("exitstatus") != 0:
            commit_issues.append(f"{runner}'s session reported exit status {oracle.get('exitstatus')}")
    return results, commit_issues


# ---------------------------------------------------------------------------
# Running one commit


def runner_version() -> str:
    digest = hashlib.sha256()
    for path in RUNNER_FILES:
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def cache_key(repo: str, commit: str, pins: Iterable[Pin], version: str) -> str:
    pins = list(pins)
    # Each test as its (path, name) pair, never the joined display id, which
    # two different pairs could share.
    tests = sorted({pin.key for pin in pins})
    # An optimum pin's pass depends on what it expects, so a changed
    # expectation never reuses a pass.
    expect = sorted({json.dumps([pin.path, pin.name, *pin.expect]) for pin in pins if pin.expect is not None})
    blob = json.dumps({"repo": repo, "commit": commit, "tests": tests, "expect": expect, "runner": version}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def pick_python(requires_python: str | None, candidates: Iterable[str] = PYTHONS) -> str:
    """The newest candidate minor version that `requires-python` allows."""

    from packaging.specifiers import (  # a dependency of pytest
        InvalidSpecifier,
        SpecifierSet,
    )

    candidates = list(candidates)
    if requires_python is None:
        return candidates[0]
    try:
        allowed = SpecifierSet(requires_python)
    except InvalidSpecifier as exc:
        raise StepError("install failed", f"requires-python {requires_python!r} is not a valid specifier: {exc}") from None
    for version in candidates:
        if any(allowed.contains(f"{version}.{patch}") for patch in range(40)):
            return version
    raise StepError("install failed", f"none of Python {', '.join(candidates)} satisfies requires-python {requires_python!r}")


def requires_python(tree: Path) -> str | None:
    pyproject = tree / "pyproject.toml"
    if not pyproject.is_file():
        return None
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise StepError("install failed", f"pyproject.toml is not readable TOML: {exc}") from None
    project = data.get("project")
    value = project.get("requires-python") if isinstance(project, dict) else None
    if value is not None and not isinstance(value, str):
        raise StepError("install failed", "pyproject.toml's requires-python is not a string")
    return value


@dataclasses.dataclass
class Settings:
    uv: str
    git: str
    work: Path
    timeout: float = DEFAULT_TIMEOUT
    repo_url: str = REPO_URL
    cache_dir: Path | None = None
    # uv's own cache and managed interpreters, shared across commits (they
    # hold downloads, not results).
    uv_dirs: Mapping[str, str] = dataclasses.field(default_factory=dict)
    # GET a GitHub REST path; unauthenticated by default (the job holds no token).
    api: Callable[[str], Any] = dataclasses.field(default_factory=sc.github_api)
    # Provenance recorded by --record-provenance, by (repository, commit);
    # used instead of asking `api` (load_provenance).
    provenance: Mapping[tuple[str, str], Mapping[str, Any]] = dataclasses.field(default_factory=dict)


def _tail(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-_LOG_TAIL:]
    except OSError:
        return ""


def _kill_group(pid: int) -> None:
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(pid, signal.SIGKILL)


def _run(argv: list[str], *, step: str, cwd: Path, env: Mapping[str, str], deadline: float, logs: Path) -> tuple[int, str]:
    """Run one step in its own process group; (exit code, output tail).
    Raises StepError("timed out") when the commit's deadline passes."""

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise StepError("timed out", f"the per-commit timeout ran out before {step}")
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / f"{step}.log"
    with log.open("wb") as handle:
        process = subprocess.Popen(
            argv, cwd=cwd, env=dict(env), stdin=subprocess.DEVNULL, stdout=handle, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            code = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            _kill_group(process.pid)
            process.wait()
            raise StepError("timed out", f"the per-commit timeout ran out during {step}") from None
        finally:
            _kill_group(process.pid)  # anything the step left running in its group
    return code, _tail(log)


def _base_env(work: Path) -> dict[str, str]:
    """A fixed, minimal environment for every step: nothing inherited but
    PATH, so no token or credential reaches code from another repository. HOME
    is a scratch directory, so no user git, uv or netrc configuration applies."""

    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(work / "home"),
        "TMPDIR": str(work / "tmp"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "UV_NO_CONFIG": "1",
        **THREAD_CAPS,
    }


def _refused(repo: str, commit: str, pins: list[Pin], provenance: Mapping[str, Any]) -> dict[str, Any]:
    detail = f"untrusted commit: {provenance.get('reason')}"
    return {
        "repo": repo, "commit": commit, "cached": False, "provenance": dict(provenance), "environment": {},
        "seconds": {}, "issues": [detail], "pins": [_failed(pin, "untrusted commit", detail) for pin in pins],
        "logs": {}, "pytest_exit": None,
    }


def _ask_provenance(repo: str, commit: str, api: Callable[[str], Any]) -> dict[str, Any]:
    try:
        return sc.commit_provenance(repo, commit, api)
    except Exception as exc:  # noqa: BLE001 - an unanswerable question refuses
        return {"repo": repo, "commit": commit, "shipped": False, "reason": f"runner error: {exc}"}


PROVENANCE_VERSION = 1


def record_provenance(payload: Any, api: Callable[[str], Any], choices: Any = None) -> dict[str, Any]:
    """The provenance of every (repository, commit) the register and the
    household choices pin, asked of GitHub through `api`. Runs no pinned code."""

    groups, _ = collect_pins(payload, choices)
    return {
        "provenance_version": PROVENANCE_VERSION,
        "records": [_ask_provenance(repo, commit, api) for repo, commit in sorted(groups)],
    }


def load_provenance(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    """Provenance recorded by record_provenance, by (repository, commit). A
    file that isn't one raises ValueError, so the run fails closed."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("provenance_version") != PROVENANCE_VERSION or not isinstance(data.get("records"), list):
        raise ValueError(f"{path} is not a provenance record of version {PROVENANCE_VERSION}")
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for record in data["records"]:
        if not (
            isinstance(record, dict) and isinstance(record.get("repo"), str)
            and isinstance(record.get("commit"), str) and isinstance(record.get("shipped"), bool)
        ):
            raise ValueError(f"{path} holds a malformed provenance record: {record!r}")
        records[(record["repo"], record["commit"])] = record
    return records


def run_commit(repo: str, commit: str, pins: list[Pin], settings: Settings, *, key: str | None = None) -> dict[str, Any]:
    """Check provenance, then reuse a cached pass (`key`) or fetch, install and
    run one commit's pins. Never raises."""

    recorded = settings.provenance.get((repo, commit))
    if recorded is not None:
        provenance = dict(recorded)
    else:
        provenance = _ask_provenance(repo, commit, settings.api)
    if not provenance.get("shipped"):
        return _refused(repo, commit, pins, provenance)
    if key is not None:
        hit = _cached(settings, key, repo, commit, pins)
        if hit is not None:
            hit["provenance"] = provenance
            return hit

    started = time.monotonic()
    deadline = started + settings.timeout
    work = Path(tempfile.mkdtemp(prefix=f"{repo.replace('/', '-')}-{commit[:12]}-", dir=settings.work))
    tree, logs = work / "checkout", work / "logs"
    (work / "home").mkdir()
    (work / "tmp").mkdir()
    base = _base_env(work)
    spec = install_spec(repo)
    result: dict[str, Any] = {
        "repo": repo,
        "commit": commit,
        "cached": False,
        "provenance": provenance,
        "pytest_exit": None,
        "environment": {"install": list(spec)},
        "seconds": {},
        "issues": [],
        "pins": [],
        "logs": {},
    }
    env_record = result["environment"]

    def timed(step: str, argv: list[str], *, cwd: Path, env: Mapping[str, str]) -> tuple[int, str]:
        began = time.monotonic()
        try:
            return _run(argv, step=step, cwd=cwd, env=env, deadline=deadline, logs=logs)
        finally:
            result["seconds"][step] = round(time.monotonic() - began, 2)

    try:
        git = [settings.git, "-c", "credential.helper=", "-c", "core.hooksPath=" + os.devnull,
               "-c", "protocol.file.allow=always", "-c", "advice.detachedHead=false", "-C", str(tree)]
        tree.mkdir()
        url = settings.repo_url.format(repo=provenance["full_name"])
        for step, argv in (
            ("git-init", [*git, "init", "-q"]),
            ("fetch", [*git, "fetch", "-q", "--depth", "1", "--no-tags", url, commit]),
            ("checkout", [*git, "checkout", "-q", commit]),
        ):
            code, tail = timed(step, argv, cwd=tree, env=base)
            if code != 0:
                result["logs"][step] = tail
                raise StepError("fetch failed", f"git {step} exited {code}")
        code, out = timed("commit-date", [*git, "show", "-s", "--format=%H %ct", commit], cwd=tree, env=base)
        head, _, stamp = out.strip().partition(" ")
        if code != 0 or head != commit or not stamp.isdigit():
            raise StepError("fetch failed", f"could not read commit {commit} after fetching it")
        exclude_newer = dt.datetime.fromtimestamp(int(stamp), dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        env_record["exclude_newer"] = exclude_newer

        env_record["requires_python"] = requires_python(tree)
        env_record["python_request"] = pick_python(env_record["requires_python"])
        venv = work / "venv"
        uv_env = {**base, **settings.uv_dirs}
        code, tail = timed("venv", [settings.uv, "venv", "--quiet", "--python", env_record["python_request"], str(venv)], cwd=work, env=uv_env)
        if code != 0:
            result["logs"]["venv"] = tail
            raise StepError("install failed", f"uv venv --python {env_record['python_request']} exited {code}")
        python = venv / "bin" / "python"
        code, tail = timed(
            "install",
            [settings.uv, "pip", "install", "--quiet", "--python", str(python), "--exclude-newer", exclude_newer, *spec],
            cwd=tree,
            env=uv_env,
        )
        if code != 0:
            result["logs"]["install"] = tail
            raise StepError("install failed", f"uv pip install {' '.join(spec)} exited {code}")
        code, out = timed(
            "python-version",
            [str(python), "-c", "import platform, pytest; print(platform.python_version(), pytest.__version__)"],
            cwd=work,
            env=base,
        )
        if code != 0:
            result["logs"]["python-version"] = out
            raise StepError("install failed", f"the install ({' '.join(spec)}) does not provide pytest")
        env_record["python"] = out.split()[0]

        if any(pin.kind == "yaml" for pin in pins):
            package = YAML_RUNNERS[repo][0].split(".")[0]
            code, out = timed(
                "yaml-runner-check",
                [str(python), "-c", "import importlib.util, sys; sys.exit(importlib.util.find_spec(sys.argv[1]) is None)", package],
                cwd=work,
                env=base,
            )
            if code != 0:
                result["logs"]["yaml-runner-check"] = out
                raise StepError("install failed", f"the install ({' '.join(spec)}) does not provide {package}")

        missing = sorted({pin.path for pin in pins if not (tree / pin.path).is_file()})
        runs: dict[str, Any] = {}
        by_pin: dict[tuple[str, str], dict[str, Any]] = {}
        exits: list[int | None] = []
        # Python tests run under pytest; YAML cases under their repository's
        # own YAML runner. Each run has its own oracle record and process exit,
        # and each exit is checked on its own.
        for kind in ("python", "yaml"):
            kind_pins = [pin for pin in pins if pin.kind == kind]
            if not kind_pins:
                continue
            files = sorted({pin.path for pin in kind_pins} - set(missing))
            label = "pytest" if kind == "python" else "the YAML test runner"
            oracle_out = work / f"oracle-{kind}.json"
            oracle: Mapping[str, Any] = {"collected": [], "exitstatus": None}
            code = None
            if files:
                run_env = {
                    **base,
                    "PATH": f"{venv / 'bin'}{os.pathsep}{base['PATH']}",
                    "VIRTUAL_ENV": str(venv),
                    "PYTHONPATH": str(ORACLE_DIR),
                    "AXIOM_PIN_ORACLE_OUT": str(oracle_out),
                    "AXIOM_PIN_ORACLE_ROOT": str(tree),
                    "AXIOM_PIN_ORACLE_PINS": json.dumps(sorted([pin.path, pin.name] for pin in kind_pins)),
                }
                if kind == "python":
                    step = "pytest"
                    argv = [str(python), "-m", "pytest", "-p", "no:cacheprovider", f"--basetemp={work / 'basetemp-python'}",
                            "-p", ORACLE_MODULE, *files]
                else:
                    step = "yaml-tests"
                    module, extra = YAML_RUNNERS[repo]
                    run_env["PYTEST_ADDOPTS"] = f"-p {ORACLE_MODULE} -p no:cacheprovider --basetemp={work / 'basetemp-yaml'}"
                    run_env["AXIOM_PIN_ORACLE_CHOICES"] = json.dumps(
                        sorted({(pin.path, pin.name, pin.expect[0]) for pin in kind_pins if pin.expect is not None})
                    )
                    argv = [str(python), "-m", module, "test", *files, *extra]
                code, tail = timed(step, argv, cwd=tree, env=run_env)
                result["logs"][step] = tail
                try:
                    oracle = json.loads(oracle_out.read_text(encoding="utf-8"))
                    if not isinstance(oracle, dict):
                        raise ValueError("not a JSON object")
                except (OSError, ValueError) as exc:
                    raise StepError("error", f"{label} exited {code} without the oracle's record ({exc})") from None
            exits.append(code)
            runs[kind] = {"exit": code, "files": files, **{key: oracle.get(key) for key in ("pytest", "inifile", "addopts")}}
            kind_results, kind_issues = classify(oracle, kind_pins, process_exit=code, missing_files=missing, runner=label)
            for pin, kind_result in zip(kind_pins, kind_results, strict=True):
                by_pin[(pin.label, pin.id)] = kind_result
            result["issues"].extend(kind_issues)
        result["pins"] = [by_pin[(pin.label, pin.id)] for pin in pins]
        result["runs"] = runs
        # 0 only when every run exited 0; otherwise the first other exit (None
        # when a run did not happen).
        result["pytest_exit"] = 0 if exits and all(code == 0 for code in exits) else next((code for code in exits if code != 0), None)
        first = runs.get("python") or runs.get("yaml") or {}
        for key in ("pytest", "inifile", "addopts"):
            env_record[key] = first.get(key)
    except StepError as exc:
        result["issues"].append(exc.detail)
        result["pins"] = [_failed(pin, exc.outcome, exc.detail) for pin in pins]
    except Exception as exc:  # noqa: BLE001 - a runner bug fails the pins, never passes them
        detail = f"runner error: {type(exc).__name__}: {exc}"
        result["issues"].append(detail)
        result["pins"] = [_failed(pin, "runner error", detail) for pin in pins]
    result["seconds"]["total"] = round(time.monotonic() - started, 2)
    return result


def _failed(pin: Pin, outcome: str, detail: str) -> dict[str, Any]:
    return {
        "entry": pin.entry, "label": pin.label, "id": pin.id, "path": pin.path, "name": pin.name, "cases": [],
        "outcome": outcome, "detail": detail,
    }


def _case_list_passed(cases: Any) -> bool:
    return (
        isinstance(cases, list)
        and bool(cases)
        and all(isinstance(case, Mapping) and case.get("outcome") == PASSED for case in cases)
    )


def commit_passed(result: Mapping[str, Any]) -> bool:
    """Two independent conditions: pytest's process exited 0, and every pin
    passed with at least one passing case. No issue may be recorded either."""

    pins = result.get("pins")
    return (
        isinstance(pins, list)
        and bool(pins)
        and not result.get("issues")
        and result.get("pytest_exit") == 0
        and all(isinstance(pin, Mapping) and pin.get("outcome") == PASSED and _case_list_passed(pin.get("cases")) for pin in pins)
    )


def _cached(settings: Settings, key: str, repo: str, commit: str, pins: list[Pin]) -> dict[str, Any] | None:
    """A cached pass for exactly this repository, commit and set of ids, or
    None. This catches corruption and stale records; it cannot authenticate
    a deliberately forged one, so the workflow restores the cache only for
    pull requests (see tools/README.md)."""

    if settings.cache_dir is None:
        return None
    path = settings.cache_dir / f"{key}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not (
        isinstance(data, dict)
        and data.get("key") == key
        and data.get("repo") == repo
        and data.get("commit") == commit
        and commit_passed(data)
    ):
        return None
    by_key = {
        (result.get("path"), result.get("name")): result for result in data["pins"] if isinstance(result, Mapping)
    }
    if set(by_key) != {pin.key for pin in pins} or len(data["pins"]) != len(by_key):
        return None
    # A result belongs to a test, not to the entries that pin it today.
    data["pins"] = [{**by_key[pin.key], "entry": pin.entry, "label": pin.label} for pin in pins]
    data["cached"] = True
    return data


def _store(settings: Settings, key: str, result: dict[str, Any]) -> None:
    if settings.cache_dir is None or not commit_passed(result):
        return
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    payload = {**result, "key": key, "logs": {}}
    temporary = settings.cache_dir / f".{key}.tmp"
    temporary.write_text(json.dumps(payload, indent=1, sort_keys=True))
    temporary.replace(settings.cache_dir / f"{key}.json")


# ---------------------------------------------------------------------------
# The whole register


def _version(argv: list[str]) -> str | None:
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=60, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def uv_dirs(uv: str) -> dict[str, str]:
    """uv's cache and interpreter directories as the caller's environment has them."""

    dirs = {}
    for variable, argv in (("UV_CACHE_DIR", [uv, "cache", "dir"]), ("UV_PYTHON_INSTALL_DIR", [uv, "python", "dir"])):
        value = _version(argv)
        if value:
            dirs[variable] = value
    return dirs


def run_register(payload: Any, settings: Settings, choices: Any = None) -> dict[str, Any]:
    version = runner_version()
    groups, unrun = collect_pins(payload, choices)
    report: dict[str, Any] = {
        "report_version": REPORT_VERSION,
        "runner": {
            "version": version,
            "uv": _version([settings.uv, "--version"]),
            "git": _version([settings.git, "--version"]),
            "host_python": sys.version.split()[0],
            "timeout_seconds": settings.timeout,
            "allowed_owners": list(ALLOWED_OWNERS),
            "started_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "commits": [],
        "unrun": unrun,
        "issues": [],
    }
    for pin in unrun:
        report["issues"].append(f"{pin['entry']} {pin['label']} {pin['pin']}: {pin['reason']}.")
    for (repo, commit), pins in sorted(groups.items()):
        key = cache_key(repo, commit, pins, version)
        result = run_commit(repo, commit, pins, settings, key=key)
        if not result.get("cached"):
            result["ran_at"] = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            _store(settings, key, result)
        report["commits"].append(result)
        where = f"{repo}@{commit[:12]}"
        for issue in result["issues"]:
            report["issues"].append(f"{where}: {issue}")
        for pin in result["pins"]:
            if pin["outcome"] != PASSED:
                detail = f" ({pin['detail']})" if pin.get("detail") else ""
                report["issues"].append(f"{pin['entry']} {pin['label']} {where}:{pin['id']}: {pin['outcome']}{detail}.")
    pins = [pin for result in report["commits"] for pin in result["pins"]]
    report["summary"] = {
        "pins": len(pins) + len(unrun),
        "passed": sum(pin["outcome"] == PASSED for pin in pins),
        "cases_passed": sum(case["outcome"] == PASSED for pin in pins for case in pin["cases"]),
        "issues": len(report["issues"]),
    }
    return report


def render(report: Mapping[str, Any]) -> str:
    lines = []
    for result in report["commits"]:
        env = result.get("environment", {})
        provenance = result.get("provenance") or {}
        if not provenance.get("shipped"):
            lines.append(
                f"{result['repo']}@{result['commit'][:12]}: refused before fetching, "
                f"{len(result['pins'])} pin(s) not run: {provenance.get('reason')}"
            )
            continue
        cases = sum(case["outcome"] == PASSED for pin in result["pins"] for case in pin["cases"])
        lines.append(
            f"{result['repo']}@{result['commit'][:12]}: {sum(p['outcome'] == PASSED for p in result['pins'])} of "
            f"{len(result['pins'])} pin(s) passed, {cases} case(s); Python {env.get('python') or env.get('python_request')}, "
            f"resolved as of {env.get('exclude_newer')}, install {' '.join(env.get('install') or [])}; "
            f"pytest exit {result.get('pytest_exit')}; {result['seconds'].get('total')}s"
            f"{' (cached)' if result.get('cached') else ''}"
        )
    summary = report["summary"]
    lines.append(
        f"pinned tests: {summary['passed']} of {summary['pins']} pin(s) passed, {summary['cases_passed']} case(s), "
        f"{summary['issues']} issue(s)."
    )
    return "\n".join(lines)


# A Python pin id (`path.py::test` or `path.py::Class::test`), or a YAML
# case's (`path.yaml::Case name (2024)`). The alarm prints an id inside an
# inline code span, so a YAML case name, which is free text, is printed only
# when it holds no backtick (which would end the span), no @ or angle
# bracket, no category C character (control, format, private-use, surrogate
# or unassigned), no separator other than a space, and no default-ignorable
# character. Any other letter or punctuation is fine: "Café", "A case!".
_SAFE_PYTHON_ID_RE = re.compile(r"[A-Za-z0-9_./-]+::[A-Za-z_][A-Za-z0-9_]*(::[A-Za-z_][A-Za-z0-9_]*)?")
_SAFE_YAML_PATH_RE = re.compile(r"[A-Za-z0-9_./-]+\.ya?ml")
_UNSAFE_IN_NAME = frozenset("`@<>")
# Default_Ignorable_Code_Point ranges outside category C, from Unicode's
# DerivedCoreProperties. Category C is refused separately below.
_DEFAULT_IGNORABLE_RANGES = (
    (0x034F, 0x034F),
    (0x115F, 0x1160),
    (0x17B4, 0x17B5),
    (0x180B, 0x180D),
    (0x180F, 0x180F),
    (0x3164, 0x3164),
    (0xFE00, 0xFE0F),
    (0xFFA0, 0xFFA0),
    (0xE0100, 0xE01EF),
)


def _safe_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if _SAFE_PYTHON_ID_RE.fullmatch(value):
        return True
    path, separator, name = value.partition("::")
    return (
        bool(separator)
        and _SAFE_YAML_PATH_RE.fullmatch(path) is not None
        and name != ""
        and name == name.strip()
        and all(
            char == " " or (
                char not in _UNSAFE_IN_NAME
                and unicodedata.category(char)[0] not in "CZ"
                and not any(start <= ord(char) <= end for start, end in _DEFAULT_IGNORABLE_RANGES)
            )
            for char in name
        )
    )


_SAFE_ENTRY_RE = re.compile(r"[a-z0-9-]+:[a-z0-9-]+")
_SAFE_LABEL_RE = re.compile(r"(?:choices\.)?entries\[[0-9]+\]\.tests\[[0-9]+\]")
_SUMMARY_LIMIT = 100
# GitHub counts an issue body in UTF-16 code units (65,536 at most); the
# summary keeps room for the workflow's own text.
_SUMMARY_UTF16_LIMIT = 60_000


def _utf16_units(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2
_CASE_NAME_LIMIT = 200


MISSING_ARTIFACT = "- pinned-tests artifact missing or unreadable; the `pinned-tests` job's log has the details."
MALFORMED_ARTIFACT = "- pinned-tests artifact malformed; the `pinned-tests` job's log has the details."


def _safe(value: Any, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _summary_lines(report: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    malformed = 0
    # The runner always writes these lists (an empty list, not a missing
    # key), so a missing or mistyped one is a malformed artifact.
    for key in ("commits", "unrun", "issues"):
        if not isinstance(report.get(key), list):
            malformed += 1
    for result in _items(report.get("commits")):
        if not (isinstance(result, Mapping) and _safe(result.get("repo"), sc.REPO_RE) and _safe(result.get("commit"), sc.COMMIT_RE)):
            malformed += 1
            continue
        where = f"{result['repo']}@{result['commit'][:12]}"
        malformed += sum(1 for key in ("pins", "issues") if not isinstance(result.get(key), list))
        if result.get("issues"):
            lines.append(f"- `{where}`: the run of this commit reported an issue.")
        for pin in _items(result.get("pins")):
            outcome = pin.get("outcome") if isinstance(pin, Mapping) else None
            if not (
                isinstance(pin, Mapping)
                and _safe(pin.get("entry"), _SAFE_ENTRY_RE)
                and _safe(pin.get("label"), _SAFE_LABEL_RE)
                and _safe_id(pin.get("id"))
                and isinstance(outcome, str)
                and outcome in OUTCOMES
            ):
                malformed += 1
            elif outcome != PASSED:
                identifier = pin["id"]
                path, _, name = identifier.partition("::")
                if _SAFE_YAML_PATH_RE.fullmatch(path) and len(name) > _CASE_NAME_LIMIT:
                    identifier = f"{path}::{name[:_CASE_NAME_LIMIT].rstrip()}…"
                lines.append(f"- `{pin['entry']}` {pin['label']}: `{where}:{identifier}` {outcome}")
    for pin in _items(report.get("unrun")):
        if isinstance(pin, Mapping) and _safe(pin.get("entry"), _SAFE_ENTRY_RE) and _safe(pin.get("label"), _SAFE_LABEL_RE):
            lines.append(f"- `{pin['entry']}` {pin['label']}: the runner can't execute this pin.")
        else:
            malformed += 1
    if malformed:
        lines.append(MALFORMED_ARTIFACT.replace("malformed;", f"malformed ({malformed} item(s));"))
    if not lines:
        issues = report.get("issues")
        if isinstance(issues, list) and issues:
            lines.append(f"- The runner reported {len(issues)} issue(s) outside any pin; see the `pinned-tests` job's log.")
        else:
            lines.append("No pinned test failed.")
    kept: list[str] = []
    characters = 0
    for line in lines:
        # Count the newline main() prints after every line as well. All
        # fields, including an unusually long repository or path, fit only
        # if the complete rendered summary stays within the budget.
        if len(kept) >= _SUMMARY_LIMIT or characters + _utf16_units(line) + 1 > _SUMMARY_UTF16_LIMIT:
            while True:
                overflow = f"- ... and {len(lines) - len(kept)} more; see the report artifact."
                if characters + _utf16_units(overflow) + 1 <= _SUMMARY_UTF16_LIMIT:
                    return [*kept, overflow]
                characters -= _utf16_units(kept.pop()) + 1
        kept.append(line)
        characters += _utf16_units(line) + 1
    return kept


def summarize(path: Path) -> list[str]:
    """Markdown lines naming the pins that did not pass, for the alarm issue.

    The report comes from a job that ran other repositories' code, so it is
    data: every field's type and pattern is checked before use. Free text
    from the run is printed in one place: a YAML case name under _safe_id's
    rule, shortened after 200 characters. Other printed fields match fixed
    patterns (ids, commits, the outcome vocabulary). A missing or malformed
    artifact is itself an alarm line; this never raises."""

    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        return [MISSING_ARTIFACT]
    if not isinstance(report, Mapping):
        return [MALFORMED_ARTIFACT]
    try:
        return _summary_lines(report)
    except Exception:  # noqa: BLE001 - a malformed artifact must raise the alarm, never crash it
        return [MALFORMED_ARTIFACT]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=TOOLS.parent, help="rulespec repository holding the register")
    parser.add_argument("--register", type=Path, help="register file (default: <root>/known-source-conflicts.yaml)")
    parser.add_argument(
        "--choices", type=Path,
        help="household-choices file (default: household-choices.yaml beside the register, when it exists)",
    )
    parser.add_argument("--report", type=Path, help="write the JSON report here (required for a run)")
    parser.add_argument("--summarize", type=Path, metavar="REPORT", help="print the failing pins of a report as Markdown, and exit")
    parser.add_argument("--cache-dir", type=Path, help="reuse and record passing results here")
    parser.add_argument("--work-dir", type=Path, help="scratch directory (default: a new temporary directory)")
    parser.add_argument("--keep-work", action="store_true", help="keep checkouts, environments and logs")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds per commit")
    parser.add_argument("--repo-url", default=REPO_URL, help="clone URL template with {repo}")
    parser.add_argument("--uv", default=shutil.which("uv"), help="uv executable")
    parser.add_argument("--github-api", default=sc.GITHUB_API, help="GitHub REST API base URL (asked for provenance; unauthenticated in a run)")
    parser.add_argument("--git", default=shutil.which("git"), help="git executable")
    parser.add_argument(
        "--record-provenance", type=Path, metavar="FILE",
        help="ask GitHub (with GH_TOKEN, when set) for the provenance of every pinned commit, write it here, and exit; runs no pinned code",
    )
    parser.add_argument(
        "--provenance", type=Path, metavar="FILE",
        help="read provenance that --record-provenance wrote; a commit the record lacks is asked of GitHub unauthenticated",
    )
    args = parser.parse_args(argv)
    register_path = args.register or args.root / sc.REGISTER_FILENAME
    choices_path = args.choices or register_path.parent / sc.CHOICES_FILENAME

    def load_choices() -> Any:
        if args.choices is None and not choices_path.exists() and not choices_path.is_symlink():
            return None
        return sc.load_register(choices_path)

    if args.record_provenance is not None:
        try:
            payload = sc.load_register(register_path)
            api = sc.github_api(os.environ.get("GH_TOKEN") or None, base_url=args.github_api)
            record = record_provenance(payload, api, load_choices())
        except Exception as exc:  # noqa: BLE001 - no record, so the run that needs it fails closed
            print(f"pin-runner: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        args.record_provenance.parent.mkdir(parents=True, exist_ok=True)
        args.record_provenance.write_text(json.dumps(record, indent=1) + "\n")
        refused = sum(1 for item in record["records"] if not item.get("shipped"))
        print(f"Recorded the provenance of {len(record['records'])} pinned commit(s); {refused} not shipped or unknown.")
        return 0
    if args.summarize is not None:
        try:
            lines = summarize(args.summarize)
        except Exception:  # noqa: BLE001 - the alarm step must always get its text
            lines = [MALFORMED_ARTIFACT]
        print("\n".join(lines))
        return 0
    if args.report is None:
        parser.error("--report is required for a run")

    work = args.work_dir or Path(tempfile.mkdtemp(prefix="pin-runs-"))
    work.mkdir(parents=True, exist_ok=True)
    try:
        try:
            if not args.uv or not args.git:
                raise RuntimeError("uv and git must be on PATH (or given with --uv and --git)")
            payload = sc.load_register(register_path)
            choices = load_choices()
            settings = Settings(
                uv=args.uv, git=args.git, work=work, timeout=args.timeout, repo_url=args.repo_url,
                cache_dir=args.cache_dir, uv_dirs=uv_dirs(args.uv), api=sc.github_api(base_url=args.github_api),
                provenance=load_provenance(args.provenance) if args.provenance is not None else {},
            )
            report = run_register(payload, settings, choices)
        except Exception as exc:  # noqa: BLE001 - fail closed, with a report
            report = {
                "report_version": REPORT_VERSION, "runner": {}, "commits": [], "unrun": [],
                "issues": [f"runner error: {type(exc).__name__}: {exc}"],
                "summary": {"pins": 0, "passed": 0, "cases_passed": 0, "issues": 1},
            }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=1) + "\n")
        print(render(report))
        for issue in report["issues"]:
            print(f"- {issue}", file=sys.stderr)
        return 1 if report["issues"] else 0
    finally:
        if not args.keep_work and args.work_dir is None:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
