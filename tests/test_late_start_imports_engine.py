"""Known hard shapes for tools/late_start_imports.py against the pinned engine.

Each case is a small tree the static model once read wrongly, or could. The
engine lowers it, and the static bindings must equal the engine's with nothing
refused. These skip unless LATE_START_HARNESS names a compiled harness, which
the engine-differential job builds; run them locally with

  LATE_START_HARNESS=<engine>/target/release/examples/rulespec_import_references \\
      pytest tests/test_late_start_imports_engine.py
"""

from __future__ import annotations

import importlib.util
import os
import sys
from datetime import date
from pathlib import Path

import pytest

HARNESS = os.environ.get("LATE_START_HARNESS")
pytestmark = pytest.mark.skipif(not HARNESS, reason="the engine-differential job builds the harness")

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "late_start_imports.py"
_spec = importlib.util.spec_from_file_location("late_start_imports", TOOL_PATH)
lsi = importlib.util.module_from_spec(_spec)
sys.modules["late_start_imports"] = lsi
_spec.loader.exec_module(lsi)

Y1990 = date(1990, 1, 1)
Y2000 = date(2000, 1, 1)
Y2020 = date(2020, 1, 1)
Y2030 = date(2030, 1, 1)


def derived(name: str, start: date, formula: str, dtype: str = "Integer") -> str:
    """The formula goes in as written, so a case can leave a scalar unquoted."""
    return (
        f"  - name: {name}\n"
        "    kind: derived\n"
        "    entity: Person\n"
        f"    dtype: {dtype}\n"
        "    period: Month\n"
        "    versions:\n"
        f"      - from: '{start}'\n"
        f"        formula: {formula}\n"
    )


def parameter(name: str, start: date, formula: str) -> str:
    return (
        f"  - name: {name}\n"
        "    kind: parameter\n"
        "    versions:\n"
        f"      - from: '{start}'\n"
        f"        formula: {formula}\n"
    )


def sets(name: str, target: str, value: str) -> str:
    return (
        f"  - name: {name}\n"
        "    kind: source_relation\n"
        "    source_relation:\n"
        "      type: sets\n"
        f"      target: {target}\n"
        f"      value: {value}\n"
        f"      basis:\n"
        f"        delegation: {target}\n"
    )


def module(*rules: str, imports: tuple[str, ...] = (), kind: str | None = None) -> str:
    head = f"format: rulespec/v1\nmodule: {{kind: {kind}}}\n" if kind else "format: rulespec/v1\nmodule: {}\n"
    lines = "".join(f"  - us:statutes/1/{name}\n" for name in imports)
    return head + (f"imports:\n{lines}" if imports else "") + "rules:\n" + "".join(rules)


def edge(rule: str, target: str, version_start: date, target_start: date) -> "lsi.Edge":
    return lsi.Edge(f"us:statutes/1/{rule}", f"us:statutes/1/{target}", version_start, target_start)


def compared(tmp_path: Path, texts: dict[str, str]) -> tuple[set, "lsi.EngineRun"]:
    """The static edges of a tree whose bindings the engine has just confirmed."""
    root = tmp_path / "tree"
    paths = [f"us/statutes/1/{name}.yaml" for name in texts]
    for path, text in zip(paths, texts.values()):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text, encoding="utf-8")
    run = lsi.parse_engine_references(lsi.run_harness(Path(HARNESS), root, paths).splitlines())
    assert run.refused == {}
    modules = {
        lsi.canonical_target(path): lsi.parse_module((root / path).read_text(encoding="utf-8"), path)
        for path in paths
    }
    differences = lsi.reference_differences(run, lsi.all_references(modules), modules)
    assert differences.only_engine == set()
    assert differences.only_static == set()
    assert differences.missing_rules == set()
    return lsi.late_start_edges(lsi.import_references(modules)), run


def test_an_unquoted_word_pyyaml_calls_a_boolean_stays_a_reference(tmp_path):
    edges, run = compared(
        tmp_path,
        {
            "target": module(derived("'yes'", Y2020, "'true'", "Boolean")),
            "caller": module(derived("answer", Y2000, "yes", "Boolean"), imports=("target",)),
        },
    )
    assert edges == {edge("caller#answer", "target#yes", Y2000, Y2020)}
    assert {item.name for item in run.bindings} == {"yes"}


def test_a_compositions_own_rules_report_though_they_took_imported_ids(tmp_path):
    edges, run = compared(
        tmp_path,
        {
            "collision": module(parameter("answer", Y1990, "'2'")),
            "target": module(parameter("shared", Y2020, "'(2)'")),
            "caller": module(
                derived("shared", Y1990, "'1'"),
                derived("answer", Y2000, "shared"),
                imports=("collision", "target"),
                kind="composition",
            ),
        },
    )
    assert edges == {edge("caller#answer", "target#shared", Y2000, Y2020)}
    assert ("us:statutes/1/caller#answer", "derived") in run.rules
    assert any(item.rule.endswith("caller#answer") for item in run.bindings)


def test_two_namespaces_in_one_module_record_the_wider_gap(tmp_path):
    edges, _ = compared(
        tmp_path,
        {
            "target": module(
                parameter("p", Y2020, "'1'"), derived("p", Y2030, "'true'", "Boolean")
            ),
            "caller": module(derived("answer", Y2000, "'if p: p else: 0'"), imports=("target",)),
        },
    )
    assert edges == {edge("caller#answer", "target#p", Y2000, Y2030)}


@pytest.mark.parametrize("literal", ["'2'", "'(2)'", "'((2))'", "2", "0x10", "1e3", "true"])
def test_a_literal_in_any_spelling_is_a_parameter(tmp_path, literal):
    edges, _ = compared(
        tmp_path,
        {
            "target": module(parameter("shared", Y2020, literal)),
            "caller": module(
                derived("shared", Y1990, "'1'"),
                derived("answer", Y2000, "shared"),
                imports=("target",),
            ),
        },
    )
    assert edge("caller#answer", "target#shared", Y2000, Y2020) in edges


def test_a_negative_number_is_derived(tmp_path):
    edges, run = compared(
        tmp_path,
        {
            "target": module(parameter("negative", Y2020, "-5")),
            "caller": module(derived("answer", Y2000, "negative"), imports=("target",)),
        },
    )
    assert edges == {edge("caller#answer", "target#negative", Y2000, Y2020)}
    assert {item.namespace for item in run.bindings} == {"derived"}


def test_a_slash_name_binds(tmp_path):
    edges, _ = compared(
        tmp_path,
        {
            "target": module(derived("remote/value", Y2020, "'1'")),
            "caller": module(derived("answer", Y2000, "remote/value"), imports=("target",)),
        },
    )
    assert edges == {edge("caller#answer", "target#remote/value", Y2000, Y2020)}


def test_a_sets_relation_between_parameters_moves_the_start(tmp_path):
    edges, _ = compared(
        tmp_path,
        {
            "rate": module(parameter("rate", Y1990, "'2'")),
            "value": module(parameter("new_rate", Y2020, "'3'")),
            "caller": module(
                sets("assignment", "us:statutes/1/rate#rate", "us:statutes/1/value#new_rate"),
                derived("answer", Y2000, "rate"),
                imports=("rate", "value"),
            ),
        },
    )
    assert edges == {edge("caller#answer", "value#new_rate", Y2000, Y2020)}


def test_a_sets_relation_between_derived_rules_as_the_tree_writes_it(tmp_path):
    edges, _ = compared(
        tmp_path,
        {
            "option": module(derived("state_option", Y1990, "'1'")),
            "state": module(
                derived("state_value", Y2020, "'2'"),
                sets("assignment", "us:statutes/1/option#state_option", "us:statutes/1/state#state_value"),
                derived("answer", Y2000, "state_option"),
                imports=("option",),
            ),
        },
    )
    assert edges == {edge("state#answer", "option#state_option", Y2000, Y2020)}


def test_a_rule_a_relation_sets_reads_what_its_value_reads(tmp_path):
    edges, _ = compared(
        tmp_path,
        {
            "late": module(derived("late", Y2020, "'1'")),
            "value": module(derived("value", Y2000, "late"), imports=("late",)),
            "assignment": module(
                sets("assignment", "us:statutes/1/caller#answer", "us:statutes/1/value#value")
            ),
            "caller": module(
                derived("answer", Y1990, "'1'"), imports=("value", "assignment")
            ),
        },
    )
    assert edge("caller#answer", "late#late", Y2000, Y2020) in edges


def test_a_local_parameter_merges_with_its_imported_name(tmp_path):
    edges, _ = compared(
        tmp_path,
        {
            "target": module(parameter("shared", Y2020, "'2'")),
            "caller": module(
                parameter("shared", Y2030, "'2'"),
                derived("answer", Y2000, "shared"),
                imports=("target",),
            ),
        },
    )
    assert edges == {edge("caller#answer", "target#shared", Y2000, Y2020)}


@pytest.mark.parametrize("call", ["|\n          max # note\n          (1, 2)", "'(max)(1, 2)'"])
def test_a_called_name_is_no_reference_however_it_is_written(tmp_path, call):
    edges, run = compared(
        tmp_path,
        {
            "target": module(derived("max", Y2020, "'1'")),
            "caller": module(derived("answer", Y2000, call), imports=("target",)),
        },
    )
    assert edges == set()
    assert run.bindings == set()


def test_a_branch_no_date_takes_is_still_an_edge(tmp_path):
    # An edge means a version can read the gap. The engine answers at every
    # date here, with `late` marked branch_not_selected.
    edges, _ = compared(
        tmp_path,
        {
            "target": module(derived("late", Y2020, "'1'")),
            "caller": module(
                derived("answer", Y2000, "'if false: late else: 1'"), imports=("target",)
            ),
        },
    )
    assert edges == {edge("caller#answer", "target#late", Y2000, Y2020)}


def test_a_table_starts_at_its_first_values(tmp_path):
    table = (
        "  - name: rate\n"
        "    kind: parameter\n"
        "    indexed_by: bracket\n"
        "    versions:\n"
        "      - from: '1990-01-01'\n"
        "        formula: '1'\n"
        "      - from: '2020-01-01'\n"
        "        values: {0: 2}\n"
    )
    edges, _ = compared(
        tmp_path,
        {
            "target": module(table),
            "caller": module(derived("answer", Y2000, "'rate[0]'"), imports=("target",)),
        },
    )
    assert edges == {edge("caller#answer", "target#rate", Y2000, Y2020)}


def test_a_local_parameter_beside_an_imported_derived_rule_of_its_name(tmp_path):
    edges, run = compared(
        tmp_path,
        {
            "target": module(derived("shared", Y1990, "other + 1"), parameter("other", Y1990, "'1'")),
            "caller": module(
                parameter("shared", Y1990, "'1'"),
                derived("answer", Y2000, "shared"),
                imports=("target",),
            ),
        },
    )
    assert edges == set()
    assert "us:statutes/1/caller#shared" in run.collisions
