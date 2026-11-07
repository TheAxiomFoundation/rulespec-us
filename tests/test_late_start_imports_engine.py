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


def parameter(name: str, start: date, formula: str, *more: tuple[date, date | None, str]) -> str:
    """`more` adds versions as (from, to, formula); the first version has no end
    unless it comes first in `more` instead."""
    versions = [(start, None, formula), *more] if start else list(more)
    return (
        f"  - name: {name}\n"
        "    kind: parameter\n"
        "    versions:\n"
        + "".join(
            f"      - from: '{begin}'\n"
            + (f"        to: '{end}'\n" if end else "")
            + f"        formula: {text}\n"
            for begin, end, text in versions
        )
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


def data_relation(name: str) -> str:
    return (
        f"  - name: {name}\n"
        "    kind: data_relation\n"
        "    data_relation:\n"
        f"      predicate: {name}\n"
        "      arity: 2\n"
    )


def derived_relation(name: str, source: str, predicate: str, *fields: str) -> str:
    """`fields` adds lines to the derived_relation mapping, such as an entity."""
    return (
        f"  - name: {name}\n"
        "    kind: derived_relation\n"
        "    derived_relation:\n"
        "      arity: 2\n"
        f"      source_relation: {source}\n"
        "      current_slot: 1\n"
        "      related_slot: 0\n"
        + "".join(f"      {line}\n" for line in fields)
        + "    versions:\n"
        "      - effective_from: '2000-01-01'\n"
        f"        formula: {predicate}\n"
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
    assert differences.extra_rules == set()
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
    assert ("us:statutes/1/caller#answer", "derived") in {(rule, space) for rule, space, _ in run.rules}
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
    # The line names the value the formula meets, though this module holds it.
    assert edges == {edge("state#answer", "state#state_value", Y2000, Y2020)}


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


# Round 3 shapes. Each stops the pinned engine on a date inside the edge.


def test_an_end_dated_local_parameter_beside_a_late_import(tmp_path):
    edges, _ = compared(
        tmp_path,
        {
            "target": module(parameter("shared", Y2020, "'2'")),
            "caller": module(
                parameter("shared", None, "", (Y1990, date(1999, 12, 31), "'1'")),
                derived("answer", Y2000, "shared"),
                imports=("target",),
            ),
        },
    )
    assert edges == {edge("caller#answer", "target#shared", Y2000, Y2020)}


def test_a_gap_between_two_versions_of_an_import(tmp_path):
    edges, run = compared(
        tmp_path,
        {
            "target": module(
                parameter("t", None, "", (Y1990, date(1995, 12, 31), "'1'"), (Y2020, None, "'2'"))
            ),
            "caller": module(derived("answer", Y2000, "t"), imports=("target",)),
        },
    )
    assert edges == {edge("caller#answer", "target#t", Y2000, Y2020)}
    assert {item.coverage for item in run.bindings} == {
        ((Y1990, date(1995, 12, 31)), (Y2020, lsi.OPEN))
    }


def test_an_import_that_ends_first(tmp_path):
    edges, _ = compared(
        tmp_path,
        {
            "target": module(parameter("t", None, "", (Y1990, date(2025, 12, 31), "'1'"))),
            "caller": module(derived("answer", Y2000, "t"), imports=("target",)),
        },
    )
    assert edges == {edge("caller#answer", "target#t", date(2026, 1, 1), lsi.OPEN)}


def test_a_rule_version_reads_only_on_the_dates_it_is_picked(tmp_path):
    caller = derived("answer", Y2000, "late").replace(
        "        formula: late\n",
        "        formula: late\n      - from: '2010-01-01'\n        to: '2014-12-31'\n        formula: '1'\n",
    )
    edges, run = compared(
        tmp_path,
        {
            "target": module(parameter("late", date(2016, 1, 1), "'1'")),
            "caller": module(caller, imports=("target",)),
        },
    )
    assert edges == {
        edge("caller#answer", "target#late", Y2000, date(2016, 1, 1)),
        edge("caller#answer", "target#late", date(2015, 1, 1), date(2016, 1, 1)),
    }


def test_a_derived_relation_reads_what_its_predicate_reads(tmp_path):
    relation = (
        "  - name: candidate_row\n"
        "    kind: data_relation\n"
        "    data_relation:\n"
        "      predicate: candidate_row\n"
        "      arity: 2\n"
        "  - name: member_of_applicant\n"
        "    kind: derived_relation\n"
        "    derived_relation:\n"
        "      arity: 2\n"
        "      source_relation: us:statutes/1/caller#relation.candidate_row\n"
        "      current_slot: 1\n"
        "      related_slot: 0\n"
        "    versions:\n"
        "      - effective_from: '2000-01-01'\n"
        "        formula: candidate_ok\n"
    )
    edges, run = compared(
        tmp_path,
        {
            "late": module(derived("candidate_ok", Y2020, "true", "Judgment")),
            "caller": module(
                relation, derived("answer", Y2000, "len(member_of_applicant)"), imports=("late",)
            ),
        },
    )
    assert edges == {edge("caller#answer", "late#candidate_ok", Y2000, Y2020)}
    assert {item.name for item in run.bindings} == {"candidate_ok"}


@pytest.mark.parametrize("name", ["TRUE", "NULL"])
def test_a_string_field_keeps_an_unquoted_name_as_written(tmp_path, name):
    # Round 4 finding 7: the scratch copy once wrote `NULL` back as `null`.
    edges, _ = compared(
        tmp_path,
        {
            "target": module(derived(name, Y2020, "'true'", "Boolean")),
            # Quoted: a formula reads a value, where an unquoted TRUE is `true`.
            "caller": module(derived("answer", Y2000, f"'{name}'", "Boolean"), imports=("target",)),
        },
    )
    assert edges == {edge("caller#answer", f"target#{name}", Y2000, Y2020)}


def test_a_sets_relation_copies_the_first_entry_of_its_value(tmp_path):
    edges, _ = compared(
        tmp_path,
        {
            "rate": module(parameter("rate", Y1990, "'2'")),
            "first": module(parameter("new_rate", Y2020, "'3'")),
            "second": module(parameter("new_rate", Y1990, "'3'")),
            "caller": module(
                sets("assignment", "us:statutes/1/rate#rate", "us:statutes/1/second#new_rate"),
                derived("answer", Y2000, "rate + 0"),
                imports=("rate", "first", "second"),
            ),
        },
    )
    assert edges == {edge("caller#answer", "first#new_rate", Y2000, Y2020)}


def test_a_sets_relation_replaces_only_the_parameter_of_its_name(tmp_path):
    edges, _ = compared(
        tmp_path,
        {
            "t": module(parameter("t", Y1990, "'2'"), derived("t", Y2020, "true", "Judgment")),
            "v": module(parameter("v", Y1990, "'3'"), derived("v", Y1990, "true", "Judgment")),
            "caller": module(
                sets("assignment", "us:statutes/1/t#t", "us:statutes/1/v#v"),
                derived("answer", Y2000, "'if t: 1 else: 2'"),
                imports=("t", "v"),
            ),
        },
    )
    # The judgment read of the derived `t` still meets 2020; the scalar side
    # now carries `v`'s versions.
    assert edges == {edge("caller#answer", "t#t", Y2000, Y2020)}


def test_a_relation_rule_gives_a_name_its_id(tmp_path):
    edges, _ = compared(
        tmp_path,
        {
            "rate": module(parameter("rate", Y1990, "'2'")),
            "value": module(parameter("new_rate", Y2020, "'3'")),
            "relation": module(
                sets("rate", "us:statutes/1/relation#rate", "us:statutes/1/value#new_rate"),
                imports=("rate", "value"),
            ),
            "caller": module(derived("answer", Y2000, "rate + 0"), imports=("relation",)),
        },
    )
    assert edges == {edge("caller#answer", "value#new_rate", Y2000, Y2020)}



# Round 4 shapes. Each binding below is one the pinned engine lowers; the
# review ran each tree at a date inside its edge, where it stops.

LATE_CANDIDATE = module(derived("candidate_ok", Y2020, "true", "Judgment"))
CANDIDATE_EDGE = edge("caller#answer", "late#candidate_ok", Y2000, Y2020)


@pytest.mark.parametrize(("source", "predicate"), [("filtered", "true"), ("candidate_row", "filtered")])
def test_a_relation_reads_what_the_relations_it_builds_on_read(tmp_path, source, predicate):
    # Finding 1: related_entity_ids evaluates a relation's source, and a
    # relation its predicate tests, before the predicate itself.
    edges, run = compared(
        tmp_path,
        {
            "late": LATE_CANDIDATE,
            "caller": module(
                data_relation("candidate_row"),
                derived_relation("filtered", "us:statutes/1/caller#relation.candidate_row", "candidate_ok"),
                derived_relation("outer", source, predicate),
                derived("answer", Y2000, "len(outer)"),
                imports=("late",),
            ),
        },
    )
    assert edges == {CANDIDATE_EDGE}
    assert {item.name for item in run.bindings} == {"candidate_ok"}


def test_a_member_alias_reads_its_relation_in_rules_of_its_entity(tmp_path):
    # Finding 3.
    edges, run = compared(
        tmp_path,
        {
            "late": LATE_CANDIDATE,
            "caller": module(
                data_relation("candidate_row"),
                derived_relation(
                    "filtered", "candidate_row", "candidate_ok", "entity: Person", "member_relation: member"
                ),
                derived("answer", Y2000, "len(member)"),
                imports=("late",),
            ),
        },
    )
    assert edges == {CANDIDATE_EDGE}
    assert {item.name for item in run.bindings} == {"candidate_ok"}


def test_a_module_reads_its_own_relation_of_a_name_another_module_shares(tmp_path):
    # Finding 4.
    edges, run = compared(
        tmp_path,
        {
            "late": module(
                derived("candidate_ok", Y2020, "true", "Judgment"),
                data_relation("rows"),
                derived_relation("members", "rows", "candidate_ok"),
            ),
            "caller": module(
                data_relation("rows"),
                derived_relation("members", "rows", "true"),
                derived("answer", Y2000, "len(members)"),
                imports=("late",),
            ),
        },
    )
    assert edges == set()
    assert run.bindings == set()


@pytest.mark.parametrize(
    ("formula", "late"),
    [
        ("'count_where(members, flag)'", True),
        ("'len(members)'", False),
        ("'count_where(members, local_flag)'", False),
    ],
)
def test_an_aggregation_takes_the_one_relation_of_a_name_only_for_an_imported_rule(tmp_path, formula, late):
    edges, _ = compared(
        tmp_path,
        {
            "late": module(
                derived("candidate_ok", Y2020, "true", "Judgment"),
                derived("flag", Y1990, "true", "Judgment"),
                data_relation("rows"),
                derived_relation("members", "rows", "candidate_ok"),
            ),
            "caller": module(
                derived("local_flag", Y1990, "true", "Judgment"),
                derived("answer", Y2000, formula),
                imports=("late",),
            ),
        },
    )
    assert edges == ({CANDIDATE_EDGE} if late else set())


@pytest.mark.parametrize("named", [False, True])
def test_a_compositions_own_relation_carries_its_alias_only_while_a_rule_names_it(tmp_path, named):
    # rewrite_relation_references drops the composition's own `filtered`, which
    # shares its name with an imported relation, unless a rule names it.
    rules = [
        data_relation("candidate_row"),
        derived_relation(
            "filtered", "candidate_row", "candidate_ok", "entity: Person", "member_relation: member"
        ),
        derived("answer", Y2000, "len(member)"),
    ]
    if named:
        rules.append(derived("count", Y2000, "len(filtered)"))
    edges, _ = compared(
        tmp_path,
        {
            "late": module(derived("candidate_ok", Y2020, "true", "Judgment"), data_relation("filtered")),
            "caller": module(*rules, imports=("late",), kind="composition"),
        },
    )
    both = {CANDIDATE_EDGE, edge("caller#count", "late#candidate_ok", Y2000, Y2020)}
    assert edges == (both if named else set())


def test_an_indexed_period_bound_reads_the_table_of_that_name(tmp_path):
    # Finding 5.
    table = (
        "  - name: period_start\n"
        "    kind: parameter\n"
        "    indexed_by: bracket\n"
        "    versions:\n"
        "      - from: '2020-01-01'\n"
        "        values: {0: 3}\n"
    )
    edges, _ = compared(
        tmp_path,
        {
            "target": module(table),
            "caller": module(derived("answer", Y2000, "'period_start[0]'"), imports=("target",)),
        },
    )
    assert edges == {edge("caller#answer", "target#period_start", Y2000, Y2020)}


@pytest.mark.parametrize(
    ("name", "formula"),
    [
        ("late", "'len(member_of_applicant.late)'"),
        ("period_start", "'days_between(period_start, period_end)'"),
    ],
)
def test_a_dropped_field_and_a_scalar_period_bound_read_no_rule(tmp_path, name, formula):
    # Finding 6.
    edges, run = compared(
        tmp_path,
        {
            "target": module(derived(name, Y2020, "'1'")),
            "caller": module(derived("answer", Y2000, formula), imports=("target",)),
        },
    )
    assert edges == set()
    assert run.bindings == set()


def test_a_scalar_read_meets_the_parameter_until_it_goes(tmp_path):
    # Finding 2: the base reads the 1990 parameter, not the 2020 derived rule
    # of its name, so its edge appears only when the head deletes the parameter.
    caller = module(derived("answer", Y2000, "'shared + 0'"), imports=("target",))
    base, run = compared(
        tmp_path / "base",
        {"target": module(parameter("shared", Y1990, "'7'"), derived("shared", Y2020, "'1'")), "caller": caller},
    )
    assert base == set()
    assert {item.namespace for item in run.bindings} == {"parameter"}
    head, _ = compared(tmp_path / "head", {"target": module(derived("shared", Y2020, "'1'")), "caller": caller})
    assert head == {edge("caller#answer", "target#shared", Y2000, Y2020)}
