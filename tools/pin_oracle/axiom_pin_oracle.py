"""pytest plugin that tools/pin_runner.py loads into a pinned repository's run.

It records what pytest itself did, under the repository's own ini, conftest
files and addopts: every collected item, every item the configuration
deselected, collection errors and module-level skips, and each phase report
of the pinned items. Items are identified by their position in the
collection (`index`), not by node id: a YAML test runner such as
policyengine-core's gives every case in a file the same node id (`path::`),
because a case's name is set only when it runs. A report belongs to the item
`pytest_runtest_protocol` is running when it arrives. tools/pin_runner.py
classifies the record; nothing here decides whether a pin passed. Items the
register does not pin are dropped after the repository's own selection has
run, so only pinned tests execute.

For a household choice's optimum pin (a YAML case), it also records what the
model did, for the runner to judge:
- `case`: whether the case changes the model, as the YAML runner reads it.
  That means top-level dotted input keys (parameter overrides), and any
  reforms or extensions.
- `choices`: after the case runs, one record per decision variable pinned on
  the case (two entries may pin one case on different variables). Each holds
  the variable as the case's own simulation computes it at the case's period
  (`simulation.calculate(variable, period)`, with an enum read by name), the
  id of the entity instance each value belongs to, the dtype the model
  stored it in, the variable's definition period and the unit and size of
  the period it was read at (core sums, divides or picks a month or year
  when they differ), and the variables the simulation took as inputs
  (`simulation.input_variables`, which counts direct inputs and axes). If
  the simulation can't be read, the record holds the error instead.

Environment (set by the runner):
- AXIOM_PIN_ORACLE_OUT: where to write the JSON record.
- AXIOM_PIN_ORACLE_ROOT: the checkout root; paths are recorded relative to it.
- AXIOM_PIN_ORACLE_PINS: JSON list of [path, name] pairs, name being
  `function` or `Class::function` for a Python test, or a YAML case's `name`.
- AXIOM_PIN_ORACLE_CHOICES (optional): JSON list of [path, name, variable]
  for optimum pins: the decision variables to read after each case runs.

It imports nothing but pytest and the standard library. It parses a period
with the `periods` module of the simulation's own package, so it needs no
import of policyengine-core.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_MESSAGE_LIMIT = 2000
_CASE_LIMIT = 200_000  # characters of a recorded value list


def _parameter_overrides(case_input: object) -> list[str]:
    """The case's parameter overrides: the YAML runner reads a top-level
    dotted input key as one (a reform), and nothing deeper."""

    if not isinstance(case_input, dict):
        return []
    return sorted(str(key) for key in case_input if isinstance(key, str) and "." in key)


def _jsonable(value: object) -> object:
    """A recorded value as JSON data: mapping keys become strings, and any
    other value JSON can't hold becomes its text. Too large or too deep a
    value is None."""

    def convert(node: object) -> object:
        if isinstance(node, dict):
            return {str(key): convert(child) for key, child in node.items()}
        if isinstance(node, list):
            return [convert(child) for child in node]
        if node is None or isinstance(node, (bool, int, float, str)):
            return node
        return str(node)

    try:
        converted = convert(value)
        return converted if len(json.dumps(converted)) <= _CASE_LIMIT else None
    except (RecursionError, ValueError, TypeError):
        return None


def _listed(values: object) -> list:
    """Computed values as a list of plain Python values. A fixed-length string
    variable comes back as bytes, which is decoded as UTF-8 text; bytes that
    aren't UTF-8 raise, so the record holds the error."""

    listed = list(values.tolist() if hasattr(values, "tolist") else values)
    return [value.decode("utf-8") if isinstance(value, bytes) else value for value in listed]


def _period(simulation: object, raw: object) -> object:
    """The period `simulation.calculate` reads for `raw` (the case's period,
    or the simulation's default), parsed by the simulation's own package."""

    for cls in type(simulation).__mro__:
        periods = getattr(sys.modules.get(cls.__module__), "periods", None)
        if callable(getattr(periods, "period", None)):
            return periods.period(raw if raw is not None else simulation.default_calculation_period)
    raise LookupError("the simulation's package has no periods.period")


def _read_choice(item: pytest.Item, variable: str) -> dict:
    """What the case's own simulation computed for one decision variable."""

    try:
        simulation = item.simulation
        period = _period(simulation, item.test.get("period"))
        definition = simulation.tax_benefit_system.get_variable(variable, check_existence=True).definition_period
        values = simulation.calculate(variable, period)
        if hasattr(values, "decode_to_str"):  # an enum's values, by name
            dtype = "enum"
            values = values.decode_to_str()
        else:
            dtype = str(getattr(values, "dtype", "")) or None
        ids = simulation.get_variable_population(variable).ids
        return {
            "variable": variable,
            "computed": _jsonable(_listed(values)),
            "ids": _jsonable([str(each) for each in (ids.tolist() if hasattr(ids, "tolist") else ids)]),
            "dtype": dtype,
            "definition_period": str(definition),
            "period": str(period),
            "period_unit": str(period.unit),
            "period_size": int(period.size),
            "input_variables": sorted(str(name) for name in simulation.input_variables),
        }
    except Exception as exc:  # noqa: BLE001 - recorded; the runner fails the pin
        return {"variable": variable, "error": f"{type(exc).__name__}: {exc}"[:_MESSAGE_LIMIT]}


class _Oracle:
    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        self.root = Path(os.environ["AXIOM_PIN_ORACLE_ROOT"]).resolve()
        self.out = Path(os.environ["AXIOM_PIN_ORACLE_OUT"])
        self.wanted = {(path, name) for path, name in json.loads(os.environ["AXIOM_PIN_ORACLE_PINS"])}
        self.choices: dict[tuple[str, str], set[str]] = {}
        for path, name, variable in json.loads(os.environ.get("AXIOM_PIN_ORACLE_CHOICES") or "[]"):
            self.choices.setdefault((path, name), set()).add(variable)
        self.index: dict[int, int] = {}  # id(item) -> position in the collection
        self.current: int | None = None
        self.record: dict = {
            "pytest": pytest.__version__,
            "rootdir": self._relative(config.rootpath),
            "inifile": self._relative(config.inipath) if config.inipath else None,
            "addopts": list(config.getini("addopts")),
            "xdist": bool(getattr(config.option, "numprocesses", None))
            or getattr(config.option, "dist", "no") not in ("no", None),
            "collected": [],
            "deselected": [],
            "collect_errors": [],
            "collect_skips": [],
            "kept": [],
            "reports": {},
            "exitstatus": None,
        }

    def _relative(self, path: Path) -> str:
        try:
            return Path(path).resolve().relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def key(self, item: pytest.Item) -> tuple[str, str]:
        """(path, name) as the register spells it: `function` or `Class::function`,
        or a YAML case's `name` (policyengine-core's YamlItem carries its case as
        `item.test` and has no name until it runs)."""

        case = getattr(item, "test", None)
        if isinstance(case, dict) and not isinstance(item, pytest.Function):
            name = case.get("name")
            return self._relative(item.path), name if isinstance(name, str) else ""
        names = []
        seen_module = False
        for node in item.listchain():
            if isinstance(node, pytest.Module):
                seen_module = True
                continue
            if not seen_module or node is item or node.name == "()":
                continue
            names.append(node.name)
        names.append(getattr(item, "originalname", None) or item.name)
        return self._relative(item.path), "::".join(names)

    @pytest.hookimpl
    def pytest_itemcollected(self, item: pytest.Item) -> None:
        path, name = self.key(item)
        self.index[id(item)] = len(self.record["collected"])
        collected = {"index": self.index[id(item)], "nodeid": item.nodeid, "path": path, "name": name}
        case = getattr(item, "test", None)
        if isinstance(case, dict) and not isinstance(item, pytest.Function) and (path, name) in self.wanted:
            collected["case"] = {
                "parameters": _parameter_overrides(case.get("input")),
                "reforms": bool(case.get("reforms")),
                "extensions": bool(case.get("extensions")),
            }
        self.record["collected"].append(collected)

    @pytest.hookimpl
    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.failed or report.skipped:
            # A node id's path part is relative to the rootdir, which need not
            # be the checkout root.
            path = report.nodeid.split("::")[0]
            self.record["collect_errors" if report.failed else "collect_skips"].append(
                {
                    "nodeid": report.nodeid,
                    "path": self._relative(self.config.rootpath / path) if path else None,
                    "message": str(report.longrepr)[-_MESSAGE_LIMIT:],
                }
            )

    @pytest.hookimpl
    def pytest_deselected(self, items: list[pytest.Item]) -> None:
        # An item the oracle never saw collected has no index; it can't be a
        # pinned case, and its node id is kept for the log.
        self.record["deselected"].extend(self.index.get(id(item), item.nodeid) for item in items)

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        # The repository's own -k/-m selection and conftest hooks have run;
        # what remains and is pinned runs, and nothing else does.
        items[:] = [item for item in items if self.key(item) in self.wanted]
        self.record["kept"] = [self.index.get(id(item), item.nodeid) for item in items]

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_protocol(self, item: pytest.Item):
        self.current = self.index.get(id(item))
        try:
            yield
        finally:
            self.current = None

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item: pytest.Item):
        yield
        # After the case ran: read each pinned decision variable from its own
        # simulation. A pin that failed is failed anyway; this records what
        # the model computed when it passed.
        variables = self.choices.get(self.key(item))
        if not variables or id(item) not in self.index:
            return
        record = self.record["collected"][self.index[id(item)]]
        record["choices"] = {variable: _read_choice(item, variable) for variable in sorted(variables)}

    @pytest.hookimpl
    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        # Keyed by the running item's index; a report outside any protocol
        # (it should not happen) is kept under its node id, where no case
        # can claim it.
        key = str(self.current) if self.current is not None else f"nodeid:{report.nodeid}"
        phases = self.record["reports"].setdefault(key, {})
        if report.when in phases:
            # Two reports for one node id and phase (a duplicated or renamed
            # item): a later pass must not hide an earlier failure, so the
            # phase becomes an outcome the runner never passes.
            phases[report.when] = {"outcome": "duplicate", "xfail": False, "message": "reported more than once"}
            return
        phases[report.when] = {
            "outcome": report.outcome,
            "xfail": hasattr(report, "wasxfail"),
            "message": (report.longreprtext or "")[-_MESSAGE_LIMIT:],
        }

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, exitstatus: int) -> None:
        self.record["exitstatus"] = int(exitstatus)
        self.out.write_text(json.dumps(self.record, indent=1))


def pytest_configure(config: pytest.Config) -> None:
    if hasattr(config, "workerinput"):
        return  # an xdist worker; the runner refuses distributed runs
    config.pluginmanager.register(_Oracle(config), "axiom-pin-oracle")
