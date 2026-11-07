"""Tests for tools/late_start_imports.py, the late-start import ratchet.

These run in the repository's pytest leg without an engine build, which is a
required check, so `test_committed_baseline_matches_this_checkout` enforces the
ratchet on every pull request. They cover YAML and formula reading, version
dates, import scope, `sets` relations, edge detection, the baseline file format,
and the gate with its base bound on small git repositories. On a pull request
the base bound itself runs in the late-start-imports workflow, and the engine
comparisons in its engine-differential job; property-based tests of the same
logic live in test_late_start_imports_properties.py.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL_PATH = REPO_ROOT / "tools" / "late_start_imports.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("late_start_imports", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["late_start_imports"] = module
    spec.loader.exec_module(module)
    return module


lsi = _load_tool()

Y2018 = date(2018, 1, 1)
Y2026 = date(2026, 1, 1)
OPEN = lsi.OPEN
BOTH = lsi.BOTH
DERIVED_ONLY = lsi.DERIVED_ONLY


def _rule(name: str, *versions: tuple[date, str]) -> "lsi.Rule":
    return lsi.Rule(name, tuple(lsi.Version(start, formula) for start, formula in versions))


def _parameter(name: str, start: date, table: bool = False) -> "lsi.Rule":
    return lsi.Rule(name, (lsi.Version(start),), lsi.PARAMETER, table)


def _edge(rule="us:a#r", target="us:b#t", start=Y2018, resumes=Y2026):
    return lsi.Edge(rule, target, start, resumes)


def _ended(start: date, end: date, formula: str = "") -> "lsi.Version":
    return lsi.Version(start, formula, end)


def _edges(modules):
    return lsi.late_start_edges(lsi.import_references(modules))


LATE_TARGET = lsi.Module(rules=(_rule("later_amount", (Y2026, "100")), _rule("other", (Y2018, "7"))))


EVERY_NAME_DERIVED = lsi.Scope(
    derived=frozenset({"a", "b", "c", "a/b", "wages", "imported", "period_start", "period_end"})
)


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("a + b", {"a", "b"}),
        ("max(a, b)", {"a", "b"}),
        ("max (a)", {"a"}),
        ("max()", set()),
        ("sum(members.wages)", {"wages"}),
        ('if "a" == b: 1 else: 2', {"b"}),
        ("'a' + b", {"b"}),
        ('"it\\"s a" + b', {"b"}),
        ("'\\q' + b", {"b"}),
        ("1 # a\n+ b", {"b"}),
        ('"""a\nb""" 1 + c', {"c"}),
        ("a/b + c", {"a/b", "c"}),
        ("a / b", {"a", "b"}),
        ("max # note\n(a)", {"a"}),
        ("(max)(a)", {"a"}),
        ("((max))(a, b)", {"a", "b"}),
        ("(a) + (b)", {"a", "b"}),
        ("1_000 + a", {"a"}),
        ("1.5 + a", {"a"}),
        ("if a and not b: true else: False", {"a", "b"}),
        ("if a: b elif c: 1 else: 2", {"a", "b", "c"}),
        ("match a:\n  1 => b\n  _ => c", {"a", "b", "c"}),
        ("match a:\n  b => 1\n  'x' => 2", {"a", "b"}),
        ("if exactly_one(a, b): 1 else: 0", {"a", "b"}),
        ("-a", {"a"}),
        ("\u3000a\u3000", {"a"}),
        # A scalar reads the period, whatever rules carry those names.
        ("period_start + period_end", set()),
        ("days_between(period_start, period_end)", set()),
        ("if period_start: 1 else: 2", {"period_start"}),
        # `len` drops the field it carries.
        ("len(members.wages)", set()),
        ("len(members, a)", set()),
    ],
)
def test_lower_formula_binds_what_formula_rs_binds(formula, expected):
    lowered = lsi.lower_formula(formula, EVERY_NAME_DERIVED)
    assert lowered.reads == {(lsi.DERIVED, name) for name in expected}


@pytest.mark.parametrize(
    "formula",
    [
        "",
        '"""a\nb""" + c',
        '"""a',
        "a/b(c)",
        "2018-01-01",
        "2018_a",
        "a b",
        "a < b < c",
        "x = 1",
        "f(1,)",
        "max(1)(2)",
        "a.b",
        "a.from",
        "a and b",
        "not a",
        "unknown(a)",
        "ceil(a, b)",
        "days_between(a)",
        "mean_over_periods(a)",
        "count_where(members)",
        "count_where(members, a + b)",
        "sum(members)",
        "len(a + b)",
        "match a:\n  _ => 1\n  2 => 3",
        "match a:",
        "if a: 1",
        "a[0]",
        "9223372036854775808",
        "'open",
        "'trailing\\",
        "a ! b",
    ],
)
def test_lower_formula_refuses_what_formula_rs_refuses(formula):
    with pytest.raises(lsi.FormulaError):
        lsi.lower_formula(formula, EVERY_NAME_DERIVED)


@pytest.mark.parametrize(
    ("formula", "judgment", "reads", "aggregations", "members"),
    [
        # A name binds a parameter in a scalar position and only a derived
        # rule in a judgment position, where a parameter lowers to an input.
        ("shared", False, {("parameter", "shared")}, set(), set()),
        ("shared", True, {("derived", "shared")}, set(), set()),
        ("rate", True, set(), set(), set()),
        ("if rate > 1: shared else: 0", False, {("parameter", "rate"), ("parameter", "shared")}, set(), set()),
        ("rate[size]", False, {("parameter", "rate"), ("derived", "size")}, set(), set()),
        ("period_start[0]", False, {("parameter", "period_start")}, set(), set()),
        ("len(members)", False, set(), {lsi.Aggregation("members")}, set()),
        ("len((members))", False, set(), {lsi.Aggregation("members")}, set()),
        (
            "count_where(members, size)",
            False,
            {("derived", "size")},
            {lsi.Aggregation("members", frozenset({"size"}))},
            set(),
        ),
        ("count_where(members, flag)", False, set(), {lsi.Aggregation("members")}, set()),
        (
            "sum_where(members, size, flag)",
            False,
            {("derived", "size")},
            {lsi.Aggregation("members", frozenset({"size"}))},
            set(),
        ),
        ("sum(members.rate)", False, set(), {lsi.Aggregation("members")}, set()),
        ("candidate_row and size", True, {("derived", "size")}, set(), set()),
    ],
)
def test_lower_formula_reads_by_position(formula, judgment, reads, aggregations, members):
    scope = lsi.Scope(
        scalars=frozenset({"shared", "rate", "period_start"}),
        derived=frozenset({"shared", "size"}),
    )
    lowered = lsi.lower_formula(formula, scope, judgment)
    assert lowered == lsi.Lowered(frozenset(reads), frozenset(aggregations), frozenset(members))


def test_a_relation_predicate_tests_membership_of_a_relation_it_names():
    scope = lsi.Scope(
        derived=frozenset({"candidate_ok"}), relation_predicates=frozenset({"members"})
    )
    lowered = lsi.lower_formula("candidate_ok and not members", scope, judgment=True)
    assert lowered == lsi.Lowered(
        frozenset({("derived", "candidate_ok")}), frozenset(), frozenset({"members"})
    )
    # A predicate has no parameters, so an index has no table to read.
    with pytest.raises(lsi.FormulaError, match="not a parameter table"):
        lsi.lower_formula("rate[0] > 1", scope, judgment=True)


@pytest.mark.parametrize(
    ("formula", "reads", "relations"),
    [
        ("a + b", {"a": BOTH, "b": BOTH}, {"a", "b"}),
        ("max(a)", {"a": BOTH}, {"a"}),
        ("len(members)", {}, {"members"}),
        ("len((members))", {}, {"members"}),
        ("count_where(members, eligible)", {"eligible": DERIVED_ONLY}, {"members"}),
        (
            "sum_where(members, wages, eligible)",
            {"wages": DERIVED_ONLY, "eligible": DERIVED_ONLY},
            {"members"},
        ),
        ("count_where(members, a + b)", {"a": BOTH, "b": BOTH}, {"members", "a", "b"}),
        ("sum(members.wages)", {"wages": DERIVED_ONLY}, {"members"}),
        ("period_start", {"period_start": DERIVED_ONLY}, set()),
        ("a/b(c) + 2018_d", {"c": BOTH, "d": BOTH}, {"c", "d"}),
    ],
)
def test_the_token_reader_reads_at_least_what_any_lowering_could(formula, reads, relations):
    # The fallback for a formula the engine refuses to lower.
    assert lsi.token_reads(formula) == (reads, frozenset(relations))


@pytest.mark.parametrize(
    ("formula", "literal"),
    [
        ("5", True),
        ("0.5", True),
        ("1_000", True),
        ('"text"', True),
        ("'text'", True),
        ("true", True),
        ("False", True),
        ("(2)", True),
        ("((2))", True),
        ("( # note\n 2 )", True),
        ('"""note"""\n5', True),
        ("a", False),
        ("-5", False),
        ("(-5)", False),
        ("1 + 2", False),
        ("(1) + (2)", False),
        ("(1", False),
        ("()", False),
        ("", False),
        ("2018-01-01", False),
        ("9223372036854775807", True),
        ("9223372036854775808", False),
        ("1.", False),
    ],
)
def test_is_literal_follows_what_the_parser_leaves(formula, literal):
    assert lsi.is_literal(formula) is literal


def test_a_long_run_of_whitespace_does_not_stall_the_lexer():
    started = time.perf_counter()
    assert not lsi.is_literal("1" + " " * 100_000 + "+ imported")
    lowered = lsi.lower_formula("1" + " " * 100_000 + "+ imported", EVERY_NAME_DERIVED)
    assert lowered.reads == {(lsi.DERIVED, "imported")}
    assert time.perf_counter() - started < 5


def test_a_formula_nested_past_the_port_is_refused_not_crashed():
    with pytest.raises(lsi.FormulaError, match="nests deeper"):
        lsi.lower_formula("(" * 5_000 + "a" + ")" * 5_000, EVERY_NAME_DERIVED)


@pytest.mark.parametrize(
    ("scalar", "expected"),
    [
        ("yes", "yes"),
        ("No", "No"),
        ("on", "on"),
        ("2018-01-01", "2018-01-01"),
        ("12:30:00", "12:30:00"),
        ("1_000", "1_000"),
        ("007", "007"),
        ("-007", "-007"),
        ("0x", "0x"),
        ('"5"', "5"),
        ("'true'", "true"),
        ("", None),
        ("~", None),
        ("null", None),
        ("NULL", None),
        ("true", True),
        ("TRUE", True),
        ("False", False),
        ("5", 5),
        ("+5", 5),
        ("-5", -5),
        ("0", 0),
        ("0x10", 16),
        ("-0x10", -16),
        ("0o17", 15),
        ("0b11", 3),
        ("1.5", 1.5),
        (".5", 0.5),
        ("1.", 1.0),
        ("1e3", 1000.0),
    ],
)
def test_scalars_load_the_way_serde_yaml_reads_them(scalar, expected):
    loaded = lsi.scalar_value(yaml.load(f"key: {scalar}\n", Loader=lsi.EngineLoader)["key"])
    assert loaded == expected and type(loaded) is type(expected)


def test_a_string_field_keeps_an_unquoted_scalar_as_written():
    # serde_yaml hands a `String` field the scalar's text, so the pinned engine
    # names this rule `TRUE`, and stops on it before 2026 (round 3 witness).
    target = lsi.parse_module(
        "rules:\n"
        "  - name: TRUE\n"
        "    kind: derived\n"
        "    versions: [{from: 2026-01-01, formula: x + 1}]\n"
    )
    importer = lsi.parse_module(
        "imports:\n"
        "  - us:b\n"
        "rules:\n"
        "  - name: r\n"
        "    kind: derived\n"
        "    versions: [{from: 2018-01-01, formula: TRUE + 1}]\n"
    )
    assert target.names == ("TRUE",)
    assert _edges({"us:b": target, "us:a": importer}) == {_edge(target="us:b#TRUE")}


@pytest.mark.parametrize(
    "text",
    [
        "rules: [{name: r, kind: derived, versions: [{from: 2018-01-01, formula: !!float 1}]}]\n",
        "rules: !custom []\n",
        "base: &b {from: 2018-01-01}\n"
        "rules: [{name: r, kind: derived, versions: [{!!merge <<: *b, formula: a}]}]\n",
    ],
    ids=["float-tag", "local-tag", "merge-tag"],
)
def test_a_written_out_tag_is_refused_rather_than_guessed(text):
    # PyYAML applies `!!merge`, and serde_yaml ignores it.
    with pytest.raises(yaml.constructor.ConstructorError, match="not modeled"):
        lsi.parse_module(text)


def test_a_plain_merge_key_stays_an_ordinary_key():
    module = lsi.parse_module(
        "base: &b {from: 2018-01-01}\n"
        "rules:\n"
        "  - name: r\n"
        "    kind: derived\n"
        "    versions:\n"
        "      - <<: *b\n"
        "        formula: a\n"
    )
    assert module.rules == ()


def test_parse_module_reads_both_date_spellings():
    module = lsi.parse_module(
        """
imports:
  - us:b#t
rules:
  - name: long_form
    kind: derived
    versions:
      - effective_from: 2018-01-01
        formula: a
  - name: alias_form
    kind: parameter
    versions:
      - from: '2019-01-01'
        to: 2019-12-31
        formula: 1
  - name: top_level
    kind: derived
    from: 2020-01-01
    formula: b
"""
    )
    assert module.imports == ("us:b#t",)
    assert [(rule.name, rule.start) for rule in module.rules] == [
        ("long_form", date(2018, 1, 1)),
        ("alias_form", date(2019, 1, 1)),
        ("top_level", date(2020, 1, 1)),
    ]
    assert module.rules[0].versions[0].formula == "a"
    assert module.rules[1].versions[0].formula == "1"
    assert module.rules[1].versions[0].end == date(2019, 12, 31)
    assert module.rules[2].versions[0].formula == "b"
    assert module.rules[0].versions[0].end == OPEN


@pytest.mark.parametrize("end", ["", "~", "null", "effective_to: ~"])
def test_a_null_end_is_no_end(end):
    field = end if end.startswith("effective_to") else f"to: {end}"
    module = lsi.parse_module(
        f"rules:\n  - name: r\n    kind: derived\n    versions:\n"
        f"      - from: 2018-01-01\n        {field}\n        formula: a\n"
    )
    assert module.rules[0].versions[0].end == OPEN


def test_parse_module_keeps_only_kinds_the_engine_versions():
    module = lsi.parse_module(
        """
rules:
  - {name: a, kind: data_relation}
  - {name: b, kind: source_relation}
  - {name: c, kind: derived_relation, versions: [{effective_from: 2018-01-01, formula: d}]}
  - {name: e, kind: derived, versions: [{effective_from: 2018-01-01, formula: d}]}
"""
    )
    assert [rule.name for rule in module.rules] == ["e"]
    assert module.names == ("a", "b", "c", "e")
    # `c` states no derived_relation, so the engine refuses it.
    assert module.relations == (lsi.Relation("a"), lsi.Relation("c", True, "", "d", refused=True))
    assert module.derived_kinds == ("e",)


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (
            "derived_relation: {arity: 2, source_relation: ' rows ', entity: Person,"
            " member_relation: member}\n    versions: [{from: 2018-01-01, formula: ' ok '}]",
            lsi.Relation("r", True, "rows", "ok", "Person", "member"),
        ),
        (
            "derived_relation: {arity: 2, source: rows}\n    formula: ok",
            lsi.Relation("r", True, "rows", "ok"),
        ),
        (
            "derived_relation: {arity: 2, source: rows}\n    from: 2018-01-01\n    formula: ok",
            lsi.Relation("r", True, "rows", "ok"),
        ),
        (
            "derived_relation: {arity: 2, source_relation: rows, source: other}\n    formula: ok",
            lsi.Relation("r", True, "", "ok", refused=True),
        ),
        (
            "derived_relation: {source_relation: rows}\n    formula: ok",
            lsi.Relation("r", True, "rows", "ok", refused=True),
        ),
        (
            "derived_relation: {arity: 2, source_relation: null}\n    formula: ok",
            lsi.Relation("r", True, "", "ok", refused=True),
        ),
        (
            "derived_relation: {arity: 2, source_relation: rows}\n"
            "    versions: [{from: 2018-01-01, formula: a}, {from: 2020-01-01, formula: b}]",
            lsi.Relation("r", True, "rows", "a b", refused=True),
        ),
        (
            "derived_relation: {arity: 2, source_relation: rows}\n"
            "    versions: [{from: 2018-01-01, formula: '  '}]",
            lsi.Relation("r", True, "rows", "", refused=True),
        ),
        (
            "derived_relation: {arity: 2, source_relation: rows, entity: 5, member_relation: TRUE}\n"
            "    formula: ok",
            lsi.Relation("r", True, "rows", "ok", "5", "true"),
        ),
    ],
)
def test_parse_relation_reads_what_to_derived_relation_spec_reads(body, expected):
    module = lsi.parse_module(f"rules:\n  - name: r\n    kind: derived_relation\n    {body}\n")
    assert module.relations == (expected,)


def test_parse_module_handles_null_imports_and_table_parameters():
    module = lsi.parse_module(
        """
imports:
rules:
  - name: table
    kind: parameter
    indexed_by: size
    versions:
      - effective_from: '2018-01-01'
        values: {1: 10, 2: 20}
"""
    )
    assert module.imports == ()
    assert module.rules == (_parameter("table", Y2018, table=True),)


@pytest.mark.parametrize(
    ("rule", "namespace", "table", "start"),
    [
        ("{kind: parameter, from: 2018-01-01, formula: 5}", "parameter", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: '0.5'}", "parameter", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: 'true'}", "parameter", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: true}", "parameter", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: '\"text\"'}", "parameter", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: '# note\n\n5\n'}", "parameter", False, Y2018),
        ("{kind: derived, from: 2018-01-01, formula: 5}", "parameter", False, Y2018),
        ("{kind: parameter, entity: Person, from: 2018-01-01, formula: 5}", "derived", False, Y2018),
        ("{kind: parameter, entity: '', from: 2018-01-01, formula: 5}", "parameter", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: a + 1}", "derived", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: -5}", "derived", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: '-5'}", "derived", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: 2018-01-01}", "derived", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: '(2)'}", "parameter", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: '((2))'}", "parameter", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: yes}", "derived", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: TRUE}", "parameter", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: 0x10}", "parameter", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: 1e3}", "parameter", False, Y2018),
        ("{kind: parameter, from: 2018-01-01, formula: '1e3'}", "derived", False, Y2018),
        ("{kind: parameter, entity: 0, from: 2018-01-01, formula: 5}", "derived", False, Y2018),
        ("{kind: parameter, entity: false, from: 2018-01-01, formula: 5}", "derived", False, Y2018),
        ("{kind: parameter, entity: ~, from: 2018-01-01, formula: 5}", "parameter", False, Y2018),
        (
            "{kind: parameter, versions: [{from: 2018-01-01, formula: 1},"
            " {from: 2026-01-01, formula: a}]}",
            "derived",
            False,
            Y2018,
        ),
        ("{kind: derived, versions: [{from: 2018-01-01, values: {0: 1}}]}", "parameter", True, Y2018),
        (
            "{kind: parameter, versions: [{from: 2018-01-01, formula: a},"
            " {from: 2026-01-01, values: {0: 1}}]}",
            "parameter",
            True,
            Y2026,
        ),
        (
            "{kind: parameter, entity: Person, versions: [{from: 2018-01-01, values: {0: 1}}]}",
            "parameter",
            True,
            Y2018,
        ),
        (
            "{kind: parameter, versions: [{from: 2018-01-01, values: {}, formula: 2},"
            " {from: 2026-01-01, formula: 1}]}",
            "parameter",
            False,
            Y2018,
        ),
    ],
)
def test_the_namespace_follows_the_engine_and_not_the_kind(rule, namespace, table, start):
    parsed = lsi.parse_module(f"rules:\n  - {{name: r, {rule[1:]}\n")
    assert [(item.namespace, item.table, item.start) for item in parsed.rules] == [
        (namespace, table, start)
    ]


def test_an_unquoted_word_pyyaml_calls_a_boolean_stays_a_reference():
    # The pinned engine stops with: derived `yes` has no formula version.
    parsed = lsi.parse_module(
        "rules: [{name: r, kind: derived, versions: [{from: 2018-01-01, formula: yes}]}]\n"
    )
    assert parsed.rules == (_rule("r", (Y2018, "yes")),)


def test_a_table_keeps_no_formula_from_a_version_the_engine_drops():
    parsed = lsi.parse_module(
        "rules:\n"
        "  - name: rate\n"
        "    kind: parameter\n"
        "    versions:\n"
        "      - {from: 2018-01-01, formula: other_rule}\n"
        "      - {from: 2026-01-01, values: {0: 1}}\n"
    )
    assert parsed.rules == (_parameter("rate", Y2026, table=True),)


@pytest.mark.parametrize("text", ["- a\n", "just text\n", ""])
def test_parse_module_rejects_a_non_mapping(text):
    with pytest.raises(ValueError, match="not a RuleSpec mapping"):
        lsi.parse_module(text, "us/a.yaml")


@pytest.mark.parametrize(
    "raw", ["soon", "'2018-1-1'", "'2018-01-01T00:00:00'", "20180101", "'+2018-01-01'"]
)
def test_parse_module_rejects_a_date_it_cannot_read(raw):
    # chrono reads more spellings than YYYY-MM-DD; the check refuses them
    # rather than guess.
    with pytest.raises(ValueError, match="rule r.*not a YYYY-MM-DD date"):
        lsi.parse_module(
            f"rules: [{{name: r, kind: derived, versions: [{{from: {raw}, formula: 1}}]}}]\n",
            "us/a.yaml",
        )


@pytest.mark.parametrize("formula", ['"abc', "'abc", '1 """', '"""a""', 'a + """b'])
def test_a_formula_that_leaves_a_string_open_is_refused(formula):
    # The engine lexes every rule's formula as one source, so an open string
    # runs into the next rule (round 3 witness).
    text = yaml.safe_dump(
        {"rules": [{"name": "r", "kind": "derived", "from": "2018-01-01", "formula": formula}]}
    )
    with pytest.raises(ValueError, match="leaves a string open"):
        lsi.parse_module(text, "us/a.yaml")


@pytest.mark.parametrize("formula", ['"""a"""', '"a" + b', "'it\\'s' + b", '"""\n"""\n1'])
def test_a_formula_that_closes_its_strings_is_read(formula):
    text = yaml.safe_dump(
        {"rules": [{"name": "r", "kind": "derived", "from": "2018-01-01", "formula": formula}]}
    )
    assert lsi.parse_module(text, "us/a.yaml").rules[0].versions[0].formula == formula


@pytest.mark.parametrize(
    ("rule", "module"),
    [
        ({"name": "a'b", "kind": "derived", "from": "2018-01-01", "formula": "1"}, {}),
        ({"name": "r", "kind": "derived", "entity": 'Per"son', "from": "2018-01-01"}, {}),
        ({"name": "r", "kind": "derived", "from": "2018-01-01", "formula": "a"}, {"title": "a\nb"}),
    ],
    ids=["quote-in-name", "quote-in-entity", "line-break-in-title"],
)
def test_text_the_engine_writes_raw_may_not_break_its_line(rule, module):
    text = yaml.safe_dump({"module": module, "rules": [rule]})
    with pytest.raises(ValueError, match="quote or a line break|holds a line break"):
        lsi.parse_module(text, "us/a.yaml")


def test_import_closure_is_transitive_drops_fragments_and_survives_cycles():
    modules = {
        "us:a": lsi.Module(imports=("us:b#t",)),
        "us:b": lsi.Module(imports=("us:c",)),
        "us:c": lsi.Module(imports=("us:a", "us:missing")),
    }
    assert lsi.import_closure("us:a", modules) == {"us:b", "us:c"}


def test_flattened_merges_imports_first_and_each_module_once():
    modules = {
        "us:a": lsi.Module(imports=("us:b", "us:c#t")),
        "us:b": lsi.Module(imports=("us:d",)),
        "us:c": lsi.Module(imports=("us:d", "us:a")),
        "us:d": lsi.Module(),
    }
    assert lsi.flattened("us:a", modules) == ["us:d", "us:b", "us:c", "us:a"]


def test_the_6012_shape_is_an_edge():
    modules = {
        "us:statutes/26/7703": lsi.Module(rules=(_rule("considered_married", (Y2026, "1")),)),
        "us:statutes/26/6012": lsi.Module(
            imports=("us:statutes/26/7703#considered_married",),
            rules=(_rule("return_required", (Y2018, "considered_married")),),
        ),
    }
    assert _edges(modules) == {
        lsi.Edge(
            "us:statutes/26/6012#return_required",
            "us:statutes/26/7703#considered_married",
            Y2018,
            Y2026,
        )
    }


@pytest.mark.parametrize(
    "specifier",
    ["us:b#later_amount", "us:b", "us:b#other"],
    ids=["named-fragment", "no-fragment", "fragment-names-another-rule"],
)
def test_a_fragment_does_not_narrow_what_a_formula_sees(specifier):
    # The sweep this tool replaced read only `#fragment` imports, so it missed
    # the last two. All three stop at run time on the pinned engine.
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(imports=(specifier,), rules=(_rule("r", (Y2018, "later_amount")),)),
    }
    assert _edges(modules) == {_edge(target="us:b#later_amount")}


def test_a_name_reached_through_a_transitive_import_is_an_edge():
    modules = {
        "us:c": LATE_TARGET,
        "us:b": lsi.Module(imports=("us:c",)),
        "us:a": lsi.Module(imports=("us:b",), rules=(_rule("r", (Y2018, "later_amount")),)),
    }
    assert _edges(modules) == {_edge(target="us:c#later_amount")}


def test_a_later_version_that_starts_with_its_target_is_not_an_edge():
    # This is how to encode the change. The rule-level reading of "starts
    # late" would flag it, and no date reaches a gap.
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(_rule("r", (Y2018, "1"), (Y2026, "later_amount")),),
        ),
    }
    assert _edges(modules) == set()


def test_runs_of_one_pair_merge_across_versions():
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(
                _rule(
                    "r",
                    (date(2010, 1, 1), "1"),
                    (Y2018, "later_amount"),
                    (date(2020, 1, 1), "later_amount + 1"),
                    (Y2026, "later_amount + 2"),
                ),
            ),
        ),
    }
    assert _edges(modules) == {_edge(target="us:b#later_amount")}


def test_starting_on_the_same_day_is_not_an_edge():
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(imports=("us:b",), rules=(_rule("r", (Y2026, "later_amount")),)),
    }
    assert _edges(modules) == set()


def test_a_local_name_is_not_an_import_edge():
    # The encoder's temporal-dependency-coverage validator owns these. A local
    # definition also wins over an imported rule of the same name.
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(
                _rule("r", (Y2018, "later_amount + own")),
                _rule("later_amount", (Y2018, "1")),
                _rule("own", (Y2026, "1")),
            ),
        ),
    }
    assert _edges(modules) == set()


def test_a_name_outside_the_import_closure_is_not_a_reference():
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(rules=(_rule("r", (Y2018, "later_amount")),)),
    }
    assert lsi.import_references(modules) == set()


def test_parameters_two_imports_define_merge_into_the_earliest():
    modules = {
        "us:b": lsi.Module(rules=(_parameter("shared", Y2026),)),
        "us:c": lsi.Module(rules=(_parameter("shared", date(2010, 1, 1)),)),
        "us:a": lsi.Module(imports=("us:b", "us:c"), rules=(_rule("r", (Y2018, "shared")),)),
    }
    assert lsi.import_references(modules) == {
        lsi.Reference(
            "us:a#r",
            Y2018,
            "us:c#shared",
            date(2010, 1, 1),
            lsi.PARAMETER,
            coverage=((date(2010, 1, 1), OPEN), (Y2026, OPEN)),
            window=((Y2018, OPEN),),
        )
    }
    assert _edges(modules) == set()


def test_an_imported_parameter_wins_over_a_local_derived_rule_of_its_name():
    # formula.rs lower_to_scalar checks parameters first, so the local rule
    # does not hide this. The engine stops: parameter `shared` has no value.
    modules = {
        "us:b": lsi.Module(rules=(_parameter("shared", Y2026),)),
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(_rule("shared", (date(2010, 1, 1), "1")), _rule("r", (Y2018, "shared"))),
        ),
    }
    assert _edges(modules) == {_edge(target="us:b#shared")}


def test_an_imported_parameter_wins_over_an_imported_derived_rule_of_its_name():
    modules = {
        "us:b": lsi.Module(rules=(_parameter("shared", Y2026),)),
        "us:c": lsi.Module(rules=(_rule("shared", (date(2010, 1, 1), "1")),)),
        "us:a": lsi.Module(imports=("us:b", "us:c"), rules=(_rule("r", (Y2018, "shared")),)),
    }
    assert _edges(modules) == {_edge(target="us:b#shared")}


def test_position_decides_which_definition_of_a_name_a_formula_reads():
    # lower_to_scalar binds the parameter, and lower_to_judgment only the
    # derived rule.
    def edges(formula):
        return _edges(
            {
                "us:b": lsi.Module(rules=(_parameter("shared", date(2010, 1, 1)),)),
                "us:c": lsi.Module(rules=(_rule("shared", (Y2026, "1")),)),
                "us:a": lsi.Module(
                    imports=("us:b", "us:c"), rules=(_rule("r", (Y2018, formula)),)
                ),
            }
        )

    assert edges("shared") == set()
    assert edges("if shared > 0: 1 else: 0") == set()
    assert edges("if shared: 1 else: 0") == {_edge(target="us:c#shared")}
    assert lsi.parse_module(
        "rules: [{name: r, kind: derived, dtype: Judgment, entity: Person,"
        " versions: [{from: 2018-01-01, formula: shared}]}]\n"
    ).rules[0].judgment


def test_a_judgment_rule_reads_the_derived_definition_of_a_name():
    modules = {
        "us:b": lsi.Module(rules=(_parameter("shared", date(2010, 1, 1)),)),
        "us:c": lsi.Module(rules=(_rule("shared", (Y2026, "1")),)),
        "us:a": lsi.Module(
            imports=("us:b", "us:c"),
            rules=(lsi.Rule("r", (lsi.Version(Y2018, "shared"),), dtype="Judgment"),),
        ),
    }
    assert _edges(modules) == {_edge(target="us:c#shared")}


def test_a_name_that_moves_to_its_late_derived_definition_widens_the_gap():
    # Round 4: deleting the parameter sends `shared + 0` to the derived rule,
    # which starts in 2020, and the engine then stops in 2010. The base bound
    # sees the new stop dates because the base read only the parameter.
    base = {
        "us:b": lsi.Module(rules=(_parameter("shared", date(1990, 1, 1)),)),
        "us:c": lsi.Module(rules=(_rule("shared", (date(2020, 1, 1), "1")),)),
        "us:a": lsi.Module(
            imports=("us:b", "us:c"),
            rules=(_rule("answer", (date(2000, 1, 1), "shared + 0")),),
        ),
    }
    head = {**base, "us:b": lsi.Module()}
    before = lsi.stop_dates(lsi.import_references(base))
    after = lsi.stop_dates(lsi.import_references(head))
    assert before == {}
    assert lsi.widened(after, before) == {
        ("us:a#answer", "shared"): ((date(2000, 1, 1), date(2019, 12, 31)),)
    }


def test_a_local_parameter_feeds_a_merged_name_and_is_no_import_edge():
    modules = {
        "us:b": lsi.Module(rules=(_parameter("shared", Y2026),)),
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(_parameter("shared", Y2018), _rule("r", (Y2018, "shared"))),
        ),
    }
    assert _edges(modules) == set()


def test_a_local_parameter_does_not_hide_a_regression_in_its_imported_half():
    # The engine merges them, so version 2000 meets 2020 and stops.
    start = date(2000, 1, 1)

    def modules(imported):
        return {
            "us:b": lsi.Module(rules=(_parameter("shared", imported),)),
            "us:a": lsi.Module(
                imports=("us:b",),
                rules=(_parameter("shared", date(2030, 1, 1)), _rule("r", (start, "shared"))),
            ),
        }

    assert _edges(modules(date(1990, 1, 1))) == set()
    assert _edges(modules(date(2020, 1, 1))) == {
        lsi.Edge("us:a#r", "us:b#shared", start, date(2020, 1, 1))
    }


def test_an_end_dated_local_parameter_does_not_hide_a_late_import():
    # Round 3: the merged name holds both, and neither applies from 2000 to
    # 2019. The pinned engine stops in 2010: parameter `shared` has no value.
    start = date(2000, 1, 1)
    modules = {
        "us:b": lsi.Module(rules=(_parameter("shared", date(2020, 1, 1)),)),
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(
                lsi.Rule("shared", (_ended(date(1990, 1, 1), date(1999, 12, 31), "1"),), lsi.PARAMETER),
                _rule("answer", (start, "shared")),
            ),
        ),
    }
    assert _edges(modules) == {lsi.Edge("us:a#answer", "us:b#shared", start, date(2020, 1, 1))}


def test_a_gap_between_two_versions_of_an_import_is_an_edge():
    target = lsi.Rule(
        "t", (_ended(date(1990, 1, 1), date(1995, 12, 31)), lsi.Version(date(2020, 1, 1))), lsi.PARAMETER
    )
    modules = {
        "us:b": lsi.Module(rules=(target,)),
        "us:a": lsi.Module(imports=("us:b",), rules=(_rule("r", (date(2000, 1, 1), "t")),)),
    }
    assert _edges(modules) == {_edge(start=date(2000, 1, 1), resumes=date(2020, 1, 1))}


def test_an_import_that_ends_first_never_resumes():
    target = lsi.Rule("t", (_ended(date(1990, 1, 1), date(2025, 12, 31)),), lsi.PARAMETER)
    modules = {
        "us:b": lsi.Module(rules=(target,)),
        "us:a": lsi.Module(imports=("us:b",), rules=(_rule("r", (date(2000, 1, 1), "t")),)),
    }
    edge = _edge(start=Y2026, resumes=OPEN)
    assert _edges(modules) == {edge}
    assert edge.render() == "us:a#r\tus:b#t\t2026-01-01\tnever"
    assert lsi.parse_baseline(edge.render() + "\n") == {edge}


def test_a_rule_version_that_ends_with_its_import_reads_no_gap():
    target = lsi.Rule("t", (_ended(date(1990, 1, 1), date(2025, 12, 31)),), lsi.PARAMETER)
    modules = {
        "us:b": lsi.Module(rules=(target,)),
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(lsi.Rule("r", (_ended(date(2000, 1, 1), date(2025, 12, 31), "t"),)),),
        ),
    }
    assert _edges(modules) == set()


def test_a_rule_version_reads_only_on_the_dates_the_engine_picks_it():
    # The 2010 version ends, so the engine picks the 2000 version again in 2015.
    reader = lsi.Rule(
        "r", (lsi.Version(date(2000, 1, 1), "late"), _ended(date(2010, 1, 1), date(2014, 12, 31), "1"))
    )
    modules = {
        "us:b": lsi.Module(rules=(_parameter("late", date(2016, 1, 1)),)),
        "us:a": lsi.Module(imports=("us:b",), rules=(reader,)),
    }
    target = "us:b#late"
    assert _edges(modules) == {
        _edge(target=target, start=date(2000, 1, 1), resumes=date(2016, 1, 1)),
        _edge(target=target, start=date(2015, 1, 1), resumes=date(2016, 1, 1)),
    }


def test_versions_apply_until_a_later_start_or_their_own_end():
    first = lsi.Version(date(2000, 1, 1))
    ended = _ended(date(2010, 1, 1), date(2014, 12, 31))
    shadowed = _ended(date(2003, 1, 1), date(2004, 12, 31))
    assert lsi.windows([first, ended, shadowed]) == {
        first: (
            (date(2000, 1, 1), date(2002, 12, 31)),
            (date(2005, 1, 1), date(2009, 12, 31)),
            (date(2015, 1, 1), OPEN),
        ),
        shadowed: ((date(2003, 1, 1), date(2004, 12, 31)),),
        ended: ((date(2010, 1, 1), date(2014, 12, 31)),),
    }
    lonely = _ended(date(2000, 1, 1), date(2000, 12, 31))
    assert lsi.windows([lonely]) == {lonely: ((date(2000, 1, 1), date(2000, 12, 31)),)}


@pytest.mark.parametrize(
    ("intervals", "removed", "left"),
    [
        ([(2000, None)], [(2010, None)], [(2000, 2009)]),
        ([(2000, None)], [(1990, 1995), (2020, None)], [(2000, 2019)]),
        ([(2000, None)], [(1990, 2025)], [(2026, None)]),
        ([(2000, 2004)], [(1990, None)], []),
        ([(2000, 2004), (2008, None)], [(2003, 2008), (2010, None)], [(2000, 2002), (2009, 2009)]),
        ([(2000, 2009)], [], [(2000, 2009)]),
        ([], [(2000, None)], []),
        ([(2000, 2001), (2002, 2003)], [(2005, None)], [(2000, 2003)]),
    ],
)
def test_subtract_leaves_the_dates_no_interval_holds(intervals, removed, left):
    def days(runs):
        return tuple(
            (date(start, 1, 1), OPEN if end is None else date(end, 12, 31)) for start, end in runs
        )

    assert lsi.subtract(days(intervals), days(removed)) == days(left)


def test_a_version_reads_what_the_predicates_of_its_relations_read():
    # Round 3: the engine evaluates the predicate on the query date, and stops
    # in 2010 with: derived `candidate_ok` has no formula version.
    modules = {
        "us:b": lsi.Module(rules=(_rule("candidate_ok", (date(2020, 1, 1), "x > 1")),)),
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(_rule("answer", (date(2000, 1, 1), "len(member_of_applicant)")),),
            relations=(
                lsi.Relation("candidate_row"),
                lsi.Relation("member_of_applicant", True, "candidate_row", "candidate_ok"),
            ),
        ),
    }
    assert _edges(modules) == {
        lsi.Edge("us:a#answer", "us:b#candidate_ok", date(2000, 1, 1), date(2020, 1, 1))
    }
    reads = lsi.import_references(modules)
    assert {(item.read_name, item.namespace) for item in reads} == {("candidate_ok", lsi.DERIVED)}


def _judgment(name, start, formula):
    return lsi.Rule(name, (lsi.Version(start, formula),), dtype="Judgment")


def _ported_edges(modules):
    """The edges, once the port has lowered every formula: none of them came
    from the token reader's fallback."""
    model = lsi.static_model(modules)
    assert model.fallbacks == set()
    return lsi.late_start_edges(item for item in model.references if item.crosses)


LATE_CANDIDATE = lsi.Module(rules=(_judgment("candidate_ok", date(2020, 1, 1), "x > 1"),))
CANDIDATE_EDGE = lsi.Edge("us:a#answer", "us:b#candidate_ok", date(2000, 1, 1), date(2020, 1, 1))


def _filtered(name="filtered", source="candidate_row", predicate="candidate_ok", **fields):
    return lsi.Relation(name, True, source, predicate, **fields)


def _answer(formula, entity=""):
    return lsi.Rule("answer", (lsi.Version(date(2000, 1, 1), formula),), entity=entity)


def _reader(*rules, relations=(), imports=("us:b",), composition=False):
    return lsi.Module(
        imports=imports, rules=rules, relations=relations, composition=composition
    )


def test_a_version_reads_down_a_chain_of_derived_relations():
    # Round 4 finding 1: related_entity_ids evaluates `outer`'s source,
    # `filtered`, before its own predicate, so the engine stops on
    # `candidate_ok` in 2010 although `outer` reads nothing itself.
    modules = {
        "us:b": LATE_CANDIDATE,
        "us:a": _reader(
            _answer("len(outer)"),
            relations=(
                lsi.Relation("candidate_row"),
                _filtered(),
                _filtered("outer", "filtered", "true"),
            ),
        ),
    }
    assert _ported_edges(modules) == {CANDIDATE_EDGE}


def test_a_predicate_reads_through_the_relations_it_tests_and_counts():
    for predicate in ("inner", "len(inner) > 0", "not inner or x > 1"):
        modules = {
            "us:b": LATE_CANDIDATE,
            "us:a": _reader(
                _answer("len(outer)"),
                relations=(
                    lsi.Relation("candidate_row"),
                    _filtered("inner"),
                    _filtered("outer", "candidate_row", predicate),
                ),
            ),
        }
        assert _ported_edges(modules) == {CANDIDATE_EDGE}, predicate


def test_a_member_alias_reads_its_filtered_relation_in_rules_of_its_entity():
    # Round 4 finding 3.
    relations = (
        lsi.Relation("candidate_row"),
        _filtered(entity="Person", member="member"),
    )

    def edges(entity):
        return _ported_edges(
            {"us:b": LATE_CANDIDATE, "us:a": _reader(_answer("len(member)", entity), relations=relations)}
        )

    assert edges("Person") == {CANDIDATE_EDGE}
    assert edges("Household") == set()
    assert edges("") == set()


def test_a_module_reads_its_own_relation_of_a_name_another_module_shares():
    # Round 4 finding 4: the imported `members` filters on a late rule, and the
    # root's own `members` on nothing.
    imported = replace(LATE_CANDIDATE, relations=(lsi.Relation("rows"), _filtered("members", "rows")))
    modules = {
        "us:b": imported,
        "us:a": _reader(_answer("len(members)"), relations=(_filtered("members", "rows", "true"),)),
    }
    assert _ported_edges(modules) == set()


def test_an_aggregation_takes_the_one_relation_of_a_name_only_for_an_imported_rule():
    # rewrite_relation_references falls back to the short name only when the
    # aggregation reads a derived rule another module declares.
    imported = lsi.Module(
        rules=(
            _judgment("candidate_ok", date(2020, 1, 1), "x > 1"),
            _judgment("flag", date(1990, 1, 1), "y > 1"),
        ),
        relations=(lsi.Relation("rows"), _filtered("members", "rows")),
    )

    def edges(formula):
        local = _judgment("local_flag", date(1990, 1, 1), "z > 1")
        return _ported_edges({"us:b": imported, "us:a": _reader(_answer(formula), local)})

    assert edges("count_where(members, flag)") == {CANDIDATE_EDGE}
    assert edges("len(members)") == set()
    assert edges("count_where(members, local_flag)") == set()
    assert edges("count_where(members, input_flag)") == set()


def test_a_composition_root_reads_its_own_relations_by_their_bare_names():
    modules = {
        "us:b": LATE_CANDIDATE,
        "us:a": _reader(
            _answer("len(filtered)"),
            relations=(lsi.Relation("candidate_row"), _filtered()),
            composition=True,
        ),
    }
    assert _ported_edges(modules) == {CANDIDATE_EDGE}


def test_a_dropped_relation_carries_no_member_alias():
    # A composition root's own `filtered` shares its name with an imported
    # relation, so rewrite_relation_references drops it unless a rule names it,
    # and rewrite_filtered_entity_member_aliases never sees its alias.
    imported = replace(LATE_CANDIDATE, relations=(lsi.Relation("filtered"),))
    relations = (lsi.Relation("candidate_row"), _filtered(entity="Person", member="member"))
    alone = {
        "us:b": imported,
        "us:a": _reader(_answer("len(member)", "Person"), relations=relations, composition=True),
    }
    assert _ported_edges(alone) == set()
    named = {
        "us:b": imported,
        "us:a": _reader(
            _answer("len(member)", "Person"),
            lsi.Rule("count", (lsi.Version(date(2000, 1, 1), "len(filtered)"),)),
            relations=relations,
            composition=True,
        ),
    }
    assert _ported_edges(named) == {
        CANDIDATE_EDGE,
        replace(CANDIDATE_EDGE, rule="us:a#count"),
    }


def test_an_indexed_period_bound_reads_the_table_of_that_name():
    # Round 4 finding 5: only a bare scalar `period_start` reads the period.
    modules = {
        "us:b": lsi.Module(rules=(_parameter("period_start", date(2020, 1, 1), table=True),)),
        "us:a": _reader(_answer("period_start[0]")),
    }
    assert _ported_edges(modules) == {replace(CANDIDATE_EDGE, target="us:b#period_start")}


@pytest.mark.parametrize(
    "formula", ["len(member_of_applicant.late)", "days_between(period_start, period_end)"]
)
def test_a_dropped_field_and_a_scalar_period_bound_read_no_rule(formula):
    # Round 4 finding 6: both answer in 2010 on the pinned engine.
    modules = {
        "us:b": lsi.Module(
            rules=(
                _rule("late", (date(2020, 1, 1), "1 + 1")),
                _rule("period_start", (date(2020, 1, 1), "1 + 1")),
            )
        ),
        "us:a": _reader(_answer(formula)),
    }
    assert _ported_edges(modules) == set()


def test_a_formula_the_port_refuses_falls_back_to_reading_every_name_both_ways():
    modules = {
        "us:b": lsi.Module(rules=(_parameter("late", Y2026),)),
        "us:a": _reader(_answer("late late")),
    }
    model = lsi.static_model(modules)
    assert model.fallbacks == {"us:a"}
    assert lsi.late_start_edges(item for item in model.references if item.crosses) == {
        lsi.Edge("us:a#answer", "us:b#late", date(2000, 1, 1), Y2026)
    }
    lowered = lsi.static_model({**modules, "us:a": _reader(_answer("late + 0"))})
    assert lowered.fallbacks == set()


def test_a_refused_predicate_falls_back_to_the_token_reader():
    modules = {
        "us:b": LATE_CANDIDATE,
        "us:a": _reader(
            _answer("len(filtered)"),
            relations=(lsi.Relation("candidate_row"), _filtered(predicate="candidate_ok candidate_ok")),
        ),
    }
    model = lsi.static_model(modules)
    assert model.fallbacks == {"us:a"}
    assert lsi.late_start_edges(item for item in model.references if item.crosses) == {
        CANDIDATE_EDGE
    }


def test_scratch_yaml_keeps_the_text_of_a_null_name(tmp_path):
    # Round 4 finding 7: `name: NULL` came back as `null`, a different rule.
    root = tmp_path / "tree"
    (root / "us").mkdir(parents=True)
    (root / "us" / "a.yaml").write_text(
        "rules:\n"
        "  - name: NULL\n"
        "    kind: derived\n"
        "    entity: ~\n"
        "    versions: [{from: 2018-01-01, formula: TRUE + 1}]\n",
        encoding="utf-8",
    )
    scratch = lsi.write_scratch_root(root, ["us/a.yaml"], tmp_path / "scratch")
    text = (scratch / "us" / "a.yaml").read_text(encoding="utf-8")
    assert lsi.parse_module(text) == lsi.parse_module(
        (root / "us" / "a.yaml").read_text(encoding="utf-8")
    )
    rule = yaml.load(text, Loader=lsi.EngineLoader)["rules"][0]
    assert rule["name"] == "NULL" and lsi.scalar_value(rule["entity"]) is None


def test_an_edge_on_a_merged_name_records_the_start_a_formula_meets():
    start = date(2000, 1, 1)
    modules = {
        "us:b": lsi.Module(rules=(_parameter("shared", Y2026),)),
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(_parameter("shared", Y2018), _rule("r", (start, "shared"))),
        ),
    }
    assert _edges(modules) == {lsi.Edge("us:a#r", "us:b#shared", start, Y2018)}


def test_a_table_removes_the_scalar_parameters_of_its_name():
    # `program.parameters.retain` drops the scalar's earlier versions.
    modules = {
        "us:b": lsi.Module(rules=(_parameter("rate", Y2026, table=True),)),
        "us:c": lsi.Module(rules=(_parameter("rate", date(2010, 1, 1)),)),
        "us:a": lsi.Module(imports=("us:b", "us:c"), rules=(_rule("r", (Y2018, "rate[0]")),)),
    }
    assert _edges(modules) == {_edge(target="us:b#rate")}


def test_a_table_starts_at_its_first_values_not_its_first_date():
    table = lsi.parse_module(
        "rules:\n"
        "  - name: rate\n"
        "    kind: parameter\n"
        "    indexed_by: size\n"
        "    versions:\n"
        "      - {from: 1990-01-01, formula: '1'}\n"
        "      - {from: 2026-01-01, values: {0: 2}}\n"
    )
    modules = {
        "us:b": table,
        "us:a": lsi.Module(imports=("us:b",), rules=(_rule("r", (Y2018, "rate[0]")),)),
    }
    assert _edges(modules) == {_edge(target="us:b#rate")}


def test_a_parameter_never_reads_a_name():
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(lsi.Rule("r", (lsi.Version(Y2018, "later_amount"),), lsi.PARAMETER),),
        ),
    }
    assert lsi.all_references(modules) == set()


def test_all_references_keep_local_bindings_for_the_differential():
    modules = {
        "us:a": lsi.Module(
            rules=(_rule("r", (Y2018, "own + input_name")), _parameter("own", Y2026)),
        ),
    }
    assert lsi.all_references(modules) == {
        lsi.Reference(
            "us:a#r",
            Y2018,
            "us:a#own",
            Y2026,
            lsi.PARAMETER,
            coverage=((Y2026, OPEN),),
            window=((Y2018, OPEN),),
            crosses=False,
        )
    }
    assert lsi.import_references(modules) == set()


def test_two_namespaces_tied_at_one_version_record_the_wider_gap():
    # The order must not decide the line, whatever the hash seed does.
    start = date(2000, 1, 1)
    narrow = lsi.Reference("us:a#r", start, "us:b#p", date(2020, 1, 1), lsi.PARAMETER)
    wide = lsi.Reference("us:a#r", start, "us:b#p", date(2030, 1, 1), lsi.DERIVED)
    expected = {lsi.Edge("us:a#r", "us:b#p", start, date(2030, 1, 1))}
    assert lsi.late_start_edges([narrow, wide]) == expected
    assert lsi.late_start_edges([wide, narrow]) == expected


def test_runs_that_do_not_touch_are_separate_edges():
    first = lsi.Reference(
        "us:a#r",
        date(2000, 1, 1),
        "us:b#p",
        date(2005, 1, 1),
        coverage=((date(2005, 1, 1), date(2011, 12, 31)), (date(2020, 1, 1), OPEN)),
        window=((date(2000, 1, 1), date(2009, 12, 31)),),
    )
    later = replace(first, version_start=date(2010, 1, 1), window=((date(2010, 1, 1), OPEN),))
    expected = {
        lsi.Edge("us:a#r", "us:b#p", date(2000, 1, 1), date(2005, 1, 1)),
        lsi.Edge("us:a#r", "us:b#p", date(2012, 1, 1), date(2020, 1, 1)),
    }
    assert lsi.late_start_edges([first, later]) == expected
    assert lsi.late_start_edges([later, first]) == expected


def test_parse_module_reads_a_sets_relation_on_a_rule_of_any_kind():
    module = lsi.parse_module(
        "rules:\n"
        "  - name: assignment\n"
        "    kind: source_relation\n"
        "    source_relation: {type: sets, target: 'us:b#rate', value: ' us:c#value '}\n"
        "  - name: r\n"
        "    kind: derived\n"
        "    from: 2018-01-01\n"
        "    formula: rate\n"
        "    source_relation: {type: sets, target: 'us:b#other', value: 'us:c#value'}\n"
    )
    assert module.sets == (("us:b#rate", "us:c#value"), ("us:b#other", "us:c#value"))


@pytest.mark.parametrize(
    "relation",
    [
        "{type: restates, target: 'us:b#rate', value: 'us:c#value'}",
        "{type: sets, target: 'us:b', value: 'us:c#value'}",
        "{type: sets, target: 'us:b#rate', value: 'us:c'}",
        "{type: sets, target: 'us:b#rate', value: 'us:b#rate'}",
        "{type: sets, target: 'us:b#rate'}",
    ],
)
def test_a_sets_relation_the_engine_skips_is_no_relation(relation):
    module = lsi.parse_module(
        f"rules: [{{name: s, kind: source_relation, source_relation: {relation}}}]\n"
    )
    assert module.sets == ()


RATE = lsi.Module(rules=(_parameter("rate", date(1990, 1, 1)),))
VALUE = lsi.Module(rules=(_parameter("value", Y2026),))


def test_a_sets_relation_gives_the_target_the_values_start():
    # The pinned engine stops with: parameter `rate` has no value.
    modules = {
        "us:b": RATE,
        "us:c": VALUE,
        "us:a": lsi.Module(
            imports=("us:b", "us:c"),
            rules=(_rule("r", (Y2018, "rate")),),
            sets=(("us:b#rate", "us:c#value"),),
        ),
    }
    assert _edges(modules) == {_edge(target="us:c#value")}
    assert lsi.all_references(modules) == {
        lsi.Reference(
            "us:a#r",
            Y2018,
            "us:c#value",
            Y2026,
            lsi.PARAMETER,
            "rate",
            coverage=((Y2026, OPEN),),
            window=((Y2018, OPEN),),
        )
    }


def test_a_sets_relation_acts_only_in_a_root_that_flattens_it():
    modules = {
        "us:b": RATE,
        "us:c": VALUE,
        "us:s": lsi.Module(imports=("us:b", "us:c"), sets=(("us:b#rate", "us:c#value"),)),
        "us:a": lsi.Module(imports=("us:b",), rules=(_rule("r", (Y2018, "rate")),)),
    }
    assert _edges(modules) == set()


def test_a_local_value_still_crosses_on_the_imported_name_it_replaces():
    # The line names the value, whose versions the formula meets.
    modules = {
        "us:b": RATE,
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(_parameter("value", Y2026), _rule("r", (Y2018, "rate"))),
            sets=(("us:b#rate", "us:a#value"),),
        ),
    }
    assert _edges(modules) == {_edge(target="us:a#value")}
    assert {item.read_name for item in lsi.import_references(modules)} == {"rate"}


def test_a_sets_relation_copies_only_the_first_entry_of_its_value():
    # find_set_binding takes the first entry; the merge comes later. Round 3:
    # the engine stops in 2010 on `rate`.
    modules = {
        "us:b": RATE,
        "us:c": VALUE,
        "us:d": lsi.Module(rules=(_parameter("value", date(1980, 1, 1)),)),
        "us:a": lsi.Module(
            imports=("us:b", "us:c", "us:d"),
            rules=(_rule("r", (Y2018, "rate")),),
            sets=(("us:b#rate", "us:d#value"),),
        ),
    }
    assert _edges(modules) == {_edge(target="us:c#value")}


def test_a_sets_relation_replaces_the_parameter_and_not_a_derived_rule_of_its_name():
    modules = {
        "us:b": RATE,
        "us:e": lsi.Module(rules=(_rule("rate", (date(1990, 1, 1), "x + 1")),)),
        "us:c": VALUE,
        "us:a": lsi.Module(
            imports=("us:b", "us:e", "us:c"),
            rules=(_rule("r", (Y2018, "rate")),),
            sets=(("us:e#rate", "us:c#value"),),
        ),
    }
    assert _edges(modules) == {_edge(target="us:c#value")}
    # The derived rule keeps its own versions, which a judgment position reads.
    judged = {
        **modules,
        "us:a": replace(modules["us:a"], rules=(_rule("r", (Y2018, "if rate: 1 else: 0")),)),
    }
    assert {(item.target, item.coverage) for item in lsi.import_references(judged)} == {
        ("us:e#rate", ((date(1990, 1, 1), OPEN),))
    }


def test_an_id_comes_from_the_last_rule_of_a_name_of_any_kind():
    # apply_rule_ids gives `rate` the id of us:x, which versions nothing, so the
    # target does not resolve while the value does, and the engine refuses the
    # root.
    modules = {
        "us:b": RATE,
        "us:c": VALUE,
        "us:x": lsi.Module(names=("rate",)),
        "us:a": lsi.Module(
            imports=("us:b", "us:c", "us:x"),
            rules=(_rule("r", (Y2018, "rate")),),
            sets=(("us:b#rate", "us:c#value"),),
        ),
    }
    assert lsi.program("us:a", lsi.flattened("us:a", modules), modules) is None
    assert lsi.all_references(modules) == set()


def test_a_composition_root_gives_its_own_rules_no_id():
    modules = {
        "us:c": VALUE,
        "us:a": lsi.Module(
            imports=("us:c",),
            rules=(_parameter("rate", date(1990, 1, 1)), _rule("r", (Y2018, "rate"))),
            sets=(("us:a#rate", "us:c#value"),),
            composition=True,
        ),
    }
    assert lsi.program("us:a", lsi.flattened("us:a", modules), modules) is None
    plain = {**modules, "us:a": replace(modules["us:a"], composition=False)}
    assert _edges(plain) == {_edge(target="us:c#value")}


def test_a_sets_relation_between_kinds_is_refused():
    modules = {
        "us:b": RATE,
        "us:c": lsi.Module(rules=(_rule("value", (Y2026, "x + 1")),)),
        "us:a": lsi.Module(
            imports=("us:b", "us:c"),
            rules=(_rule("r", (Y2018, "rate")),),
            sets=(("us:b#rate", "us:c#value"),),
        ),
    }
    assert lsi.program("us:a", lsi.flattened("us:a", modules), modules) is None


def test_a_sets_relation_finds_only_the_definition_that_kept_the_id():
    # apply_rule_ids leaves the last definition's id on a merged name, so the
    # engine finds no `us:b#rate` here and the relation changes nothing.
    modules = {
        "us:b": RATE,
        "us:d": lsi.Module(rules=(_parameter("rate", date(1980, 1, 1)),)),
        "us:c": VALUE,
        "us:a": lsi.Module(
            imports=("us:b", "us:d", "us:c"),
            rules=(_rule("r", (Y2018, "rate")),),
            sets=(("us:b#rate", "us:c#value"),),
        ),
    }
    assert _edges(modules) == set()


def test_sets_relations_chain_in_merge_order():
    modules = {
        "us:b": RATE,
        "us:c": lsi.Module(rules=(_parameter("middle", date(2000, 1, 1)),)),
        "us:d": VALUE,
        "us:e": lsi.Module(sets=(("us:c#middle", "us:d#value"),)),
        "us:f": lsi.Module(sets=(("us:b#rate", "us:c#middle"),)),
        "us:a": lsi.Module(
            imports=("us:b", "us:c", "us:d", "us:e", "us:f"),
            rules=(_rule("r", (Y2018, "rate")),),
        ),
    }
    assert _edges(modules) == {_edge(target="us:d#value")}
    reversed_order = {
        **modules,
        "us:a": lsi.Module(
            imports=("us:b", "us:c", "us:d", "us:f", "us:e"),
            rules=(_rule("r", (Y2018, "rate")),),
        ),
    }
    assert _edges(reversed_order) == set()


def test_a_rule_a_relation_sets_reads_what_its_value_reads():
    modules = {
        "us:b": LATE_TARGET,
        "us:c": lsi.Module(rules=(_rule("value", (Y2018, "later_amount")),)),
        "us:s": lsi.Module(sets=(("us:a#r", "us:c#value"),)),
        "us:a": lsi.Module(
            imports=("us:b", "us:c", "us:s"),
            rules=(_rule("r", (date(1990, 1, 1), "1")),),
        ),
    }
    assert _edges(modules) == {_edge(target="us:b#later_amount")}


def test_a_word_in_a_comment_or_string_is_not_a_reference():
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(_rule("r", (Y2018, '1 # later_amount\n + "later_amount"')),),
        ),
    }
    assert _edges(modules) == set()


def test_module_path_inverts_canonical_target():
    assert lsi.module_path("us:statutes/26/6012#x") == "us/statutes/26/6012.yaml"
    assert lsi.module_path("us-la:statutes/47:32#x") == "us-la/statutes/47:32.yaml"


def test_baseline_rejects_malformed_lines():
    line = "us:a#r\tus:b#t\t2018-01-01\t2026-01-01"
    assert lsi.parse_baseline(f"# comment\n\n{line}\n") == {_edge()}
    for bad, message in (
        ("us:a#r\tus:b#t\t2018-01-01", "must be"),
        ("us:a\tus:b#t\t2018-01-01\t2026-01-01", "two rule ids"),
        ("us:a#r\tus:b#t\t2026-01-01\t2026-01-01", "resumes before it starts"),
        ("us:a#r\tus:b#t\t2027-01-01\t2026-01-01", "resumes before it starts"),
        ("us:a#r\tus:b#t\tnever\t2026-01-01", "not a YYYY-MM-DD date"),
        ("us:a#r\tus:b#t\t2018-1-01\t2026-01-01", "not a YYYY-MM-DD date"),
        (f"{line}\n{line}", "duplicates"),
    ):
        with pytest.raises(ValueError, match=message):
            lsi.parse_baseline(bad + "\n")


def test_baseline_rejects_a_date_that_is_not_one():
    with pytest.raises(ValueError):
        lsi.parse_baseline("us:a#r\tus:b#t\tsoon\t2026-01-01\n")


def test_gate_accepts_a_matching_baseline():
    assert lsi.compare({_edge()}, {_edge()}).ok


def test_gate_fails_on_an_unlisted_edge():
    verdict = lsi.compare({_edge()}, set())
    assert not verdict.ok and verdict.new == {_edge()} and not verdict.stale


def test_gate_fails_on_a_listed_edge_that_no_longer_holds():
    verdict = lsi.compare(set(), {_edge()})
    assert not verdict.ok and verdict.stale == {_edge()} and not verdict.new


def test_gate_fails_when_a_listed_edges_dates_move():
    wider = _edge(start=date(2010, 1, 1))
    verdict = lsi.compare({wider}, {_edge()})
    assert verdict.new == {wider} and verdict.stale == {_edge()}


def test_gate_fails_on_a_widened_stop_date_even_when_the_list_matches():
    wider = {("us:a#r", "t"): ((Y2018, date(2025, 12, 31)),)}
    verdict = lsi.compare({_edge()}, {_edge()}, wider)
    assert not verdict.ok and verdict.widened == wider and not verdict.new


def _stops(*runs):
    return tuple((date(start, 1, 1), OPEN if end is None else date(end, 12, 31)) for start, end in runs)


def test_widened_is_every_stop_date_the_base_lacks():
    base = {("us:a#r", "t"): _stops((2018, 2025))}
    assert lsi.widened(base, base) == {}
    assert lsi.widened({("us:a#r", "t"): _stops((2020, 2025))}, base) == {}
    assert lsi.widened({("us:a#r", "t"): _stops((2016, 2027))}, base) == {
        ("us:a#r", "t"): _stops((2016, 2017), (2026, 2027))
    }
    assert lsi.widened({("us:a#s", "t"): _stops((2018, 2025))}, base) == {
        ("us:a#s", "t"): _stops((2018, 2025))
    }
    assert lsi.widened({}, base) == {}


def test_stop_dates_key_on_the_name_a_formula_reads():
    replaced = lsi.Reference(
        "us:a#r", Y2018, "us:c#value", Y2026, lsi.PARAMETER, "rate", coverage=((Y2026, OPEN),)
    )
    plain = lsi.Reference("us:a#r", Y2018, "us:b#rate", Y2026, coverage=((Y2026, OPEN),))
    assert lsi.stop_dates([replaced]) == lsi.stop_dates([plain]) == {
        ("us:a#r", "rate"): ((Y2018, date(2025, 12, 31)),)
    }


def test_moving_which_module_supplies_a_name_narrows_without_a_label():
    # Round 3: keyed by target, this repair read as an added pair.
    def modules(*suppliers):
        return {
            "us:b": lsi.Module(rules=(_parameter("x", Y2026),)),
            "us:c": lsi.Module(rules=(_parameter("x", date(2020, 1, 1)),)),
            "us:a": lsi.Module(imports=suppliers, rules=(_rule("r", (Y2018, "x")),)),
        }

    base = lsi.import_references(modules("us:b"))
    head = lsi.import_references(modules("us:b", "us:c"))
    assert {edge.target for edge in lsi.late_start_edges(base)} == {"us:b#x"}
    assert {edge.target for edge in lsi.late_start_edges(head)} == {"us:c#x"}
    assert lsi.widened(lsi.stop_dates(head), lsi.stop_dates(base)) == {}
    assert lsi.widened(lsi.stop_dates(base), lsi.stop_dates(head)) == {
        ("us:a#r", "x"): ((date(2020, 1, 1), date(2025, 12, 31)),)
    }


def test_a_second_gap_on_a_listed_pair_widens_its_stop_dates():
    # The list could carry both lines after a regeneration; the bound still
    # sees the new dates.
    def modules(target):
        return {
            "us:b": lsi.Module(rules=(target,)),
            "us:a": lsi.Module(imports=("us:b",), rules=(_rule("r", (Y2018, "t")),)),
        }

    base = modules(lsi.Rule("t", (lsi.Version(date(2020, 1, 1)),), lsi.PARAMETER))
    head = modules(
        lsi.Rule(
            "t",
            (_ended(date(2020, 1, 1), date(2022, 12, 31)), lsi.Version(date(2024, 1, 1))),
            lsi.PARAMETER,
        )
    )
    head_references = lsi.import_references(head)
    assert len(lsi.late_start_edges(head_references)) == 2
    assert lsi.widened(
        lsi.stop_dates(head_references), lsi.stop_dates(lsi.import_references(base))
    ) == {("us:a#r", "t"): ((date(2023, 1, 1), date(2023, 12, 31)),)}


def test_summarize_counts_rules_and_modules():
    summary = lsi.summarize({_edge(), _edge(rule="us:a#s"), _edge(rule="us-co:c#r", target="us:d#t")})
    assert summary.startswith(
        "3 late-start import edge(s): 3 rules, 2 importing modules, 2 target modules"
    )
    assert lsi.summarize(set()).startswith("0 late-start import edge(s)")


def _tracked_files() -> set[str]:
    listing = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"], check=True, capture_output=True
    ).stdout.decode("utf-8")
    return {path for path in listing.split("\0") if path}


def test_committed_baseline_is_canonical_and_names_tracked_modules():
    text = (REPO_ROOT / lsi.BASELINE_RELATIVE_PATH).read_text(encoding="utf-8")
    entries = lsi.parse_baseline(text)
    assert lsi.render_baseline(entries) == text, "regenerate with late_start_imports.py baseline"
    tracked = _tracked_files()
    named = {lsi.module_path(id_) for entry in entries for id_ in (entry.rule, entry.target)}
    assert not sorted(named - tracked)[:10], "baseline names modules that are not tracked"


def test_committed_baseline_matches_this_checkout():
    edges = lsi.late_start_edges(lsi.import_references(lsi.load_modules(REPO_ROOT)))
    baseline = lsi.parse_baseline(
        (REPO_ROOT / lsi.BASELINE_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    verdict = lsi.compare(edges, baseline)
    assert verdict.ok, (
        f"new edges: {sorted(map(lsi.Edge.render, verdict.new))[:10]}\n"
        f"lines that no longer hold: {sorted(map(lsi.Edge.render, verdict.stale))[:10]}\n"
        "See tools/README.md, Late-start imports."
    )


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


MODULE_TEMPLATE = """\
format: rulespec/v1
imports:
  - us:statutes/1/target
module: {{}}
rules:
  - name: answer
    kind: derived
    versions:
      - effective_from: '{start}'
        formula: later_amount
"""
TARGET = """\
format: rulespec/v1
module: {}
rules:
  - name: later_amount
    kind: parameter
    versions:
      - effective_from: '2026-01-01'
        formula: '100'
"""


def _write(root: Path, relative: str, text: str) -> None:
    (root / relative).parent.mkdir(parents=True, exist_ok=True)
    (root / relative).write_text(text, encoding="utf-8")


@pytest.fixture
def repository(tmp_path):
    """A checkout whose base commit carries an empty baseline and no edge."""
    root = tmp_path / "rulespec-us"
    _write(root, "us/statutes/1/target.yaml", TARGET)
    _write(root, "us/statutes/1/importer.yaml", MODULE_TEMPLATE.format(start="2026-01-01"))
    _write(root, lsi.BASELINE_RELATIVE_PATH.as_posix(), lsi.render_baseline(set()))
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
    return root, _git(root, "rev-parse", "HEAD")


def _check(root: Path, base: str | None, allow_added: bool = False) -> int:
    return lsi.check(root, root / lsi.BASELINE_RELATIVE_PATH, base, allow_added)


def test_check_passes_on_a_checkout_that_matches_its_base(repository):
    root, base = repository
    assert _check(root, base) == 0


def test_check_fails_when_a_change_adds_an_edge(repository, capsys):
    root, base = repository
    _write(root, "us/statutes/1/importer.yaml", MODULE_TEMPLATE.format(start="2018-01-01"))
    _git(root, "add", "-A")
    assert _check(root, base) == 1
    output = capsys.readouterr().out
    assert "1 edge(s) are not in known-late-start-imports.txt" in output
    assert (
        "us:statutes/1/importer#answer reads us:statutes/1/target#later_amount "
        "from 2018-01-01, and that target has none until 2026-01-01"
    ) in output


def test_regenerating_does_not_pass_the_base_bound_without_the_label(repository, capsys):
    root, base = repository
    _write(root, "us/statutes/1/importer.yaml", MODULE_TEMPLATE.format(start="2018-01-01"))
    _git(root, "add", "-A")
    _regenerate(root)
    assert _check(root, base) == 1
    output = capsys.readouterr().out
    assert lsi.ACCEPT_LABEL in output
    assert "us:statutes/1/importer#answer reads later_amount on [2018-01-01..2025-12-31]" in output
    assert _check(root, base, allow_added=True) == 0
    assert "label accepts them" in capsys.readouterr().out
    assert _check(root, None) == 0


def _regenerate(root: Path) -> None:
    edges = lsi.late_start_edges(lsi.import_references(lsi.load_modules(root)))
    _write(root, lsi.BASELINE_RELATIVE_PATH.as_posix(), lsi.render_baseline(edges))


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def test_the_base_bound_reads_the_base_modules_and_not_its_list(repository):
    # Round 3: a base with no list at that path left the pull request unbound.
    root, _ = repository
    (root / lsi.BASELINE_RELATIVE_PATH).unlink()
    without = _commit(root, "no baseline")
    _write(root, "us/statutes/1/importer.yaml", MODULE_TEMPLATE.format(start="2018-01-01"))
    _regenerate(root)
    assert _check(root, without) == 1
    assert _check(root, without, allow_added=True) == 0


def test_the_base_bound_ignores_uncommitted_changes_at_the_base(repository):
    root, base = repository
    _write(root, "us/statutes/1/importer.yaml", MODULE_TEMPLATE.format(start="2018-01-01"))
    _regenerate(root)
    assert lsi.load_modules_at(root, base) != lsi.load_modules(root)
    assert _check(root, base) == 1


def test_a_repair_that_moves_the_supplier_needs_no_label(repository):
    root, _ = repository
    _write(root, "us/statutes/1/importer.yaml", MODULE_TEMPLATE.format(start="2018-01-01"))
    _regenerate(root)
    base = _commit(root, "an edge the base carries")
    _write(root, "us/statutes/1/earlier.yaml", TARGET.replace("2026-01-01", "2020-01-01"))
    _write(
        root,
        "us/statutes/1/importer.yaml",
        MODULE_TEMPLATE.format(start="2018-01-01").replace(
            "  - us:statutes/1/target\n", "  - us:statutes/1/target\n  - us:statutes/1/earlier\n"
        ),
    )
    _git(root, "add", "-A")
    _regenerate(root)
    baseline = (root / lsi.BASELINE_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "us:statutes/1/earlier#later_amount\t2018-01-01\t2020-01-01" in baseline
    assert _check(root, base) == 0


def test_a_base_ref_that_is_not_a_commit_stops_the_check(repository):
    root, _ = repository
    with pytest.raises(SystemExit, match="not a commit"):
        _check(root, "no-such-ref")


def test_check_fails_when_a_repair_leaves_its_line_behind(repository, capsys):
    root, base = repository
    edge = lsi.Edge(
        "us:statutes/1/importer#answer", "us:statutes/1/target#later_amount", Y2018, Y2026
    )
    _write(root, lsi.BASELINE_RELATIVE_PATH.as_posix(), lsi.render_baseline({edge}))
    assert _check(root, None) == 1
    assert "1 listed edge(s) no longer hold" in capsys.readouterr().out


def test_the_cli_regenerates_the_committed_baseline_format(repository, capsys):
    root, _ = repository
    assert lsi.main(["baseline", "--root", str(root)]) == 0
    assert capsys.readouterr().out == lsi.render_baseline(set())


def test_harness_uses_the_engine_compile_entry_points():
    source = lsi.HARNESS_SOURCE
    assert "CanonicalRuleSpecRoots::new" in source
    assert "CompiledProgramArtifact::from_rulespec_file" in source
    assert "CompiledProgramArtifact::from_composed_rulespec_file" in source
    assert "ModuleKindOnAtomicSurface" in source


def test_harness_finds_a_modules_rules_by_name_and_not_by_id():
    assert "declared_names" in lsi.HARNESS_SOURCE
    assert "rule.id" not in lsi.HARNESS_SOURCE


def _result(module: str, *references: dict, collisions=(), rules=()) -> str:
    return json.dumps(
        {
            "module": module,
            "ok": True,
            "rules": list(rules),
            "references": list(references),
            "collisions": list(collisions),
        }
    )


def _read(rule="us:a#r", name="t", namespace="derived", start="2026-01-01") -> dict:
    return {
        "rule": rule,
        "version_start": "2018-01-01",
        "version_end": None,
        "name": name,
        "namespace": namespace,
        "coverage": None if start is None else [[start, None]],
    }


def _binding(rule="us:a#r", name="t", namespace="derived", start=Y2026) -> "lsi.Binding":
    coverage = () if start is None else ((start, OPEN),)
    return lsi.Binding(rule, Y2018, name, namespace, start, OPEN, coverage)


def test_parse_engine_references_reads_every_result():
    lines = [
        _result("us/a.yaml", _read(), _read(name="i", namespace="input", start=None)),
        json.dumps({"module": "us/b.yaml", "ok": False, "error": "refused"}),
        _result(
            "us/c.yaml",
            collisions=["hidden"],
            rules=[
                {
                    "name": "hidden",
                    "namespace": "parameter",
                    "versions": [["2018-01-01", "2019-12-31"], ["2020-01-01", None]],
                }
            ],
        ),
        "",
    ]
    run = lsi.parse_engine_references(lines)
    assert run.results == {"us:a", "us:b", "us:c"}
    assert run.compiled == {"us:a", "us:c"}
    assert run.refused == {"us:b": "refused"}
    assert run.bindings == {_binding()}
    assert run.inputs == {_binding(name="i", namespace="input", start=None)}
    assert run.collisions == {"us:c#hidden"}
    assert run.rules == {
        ("us:c#hidden", "parameter", ((Y2018, date(2019, 12, 31)), (date(2020, 1, 1), OPEN)))
    }


def test_parse_engine_references_reads_an_ended_version_and_its_coverage():
    item = {
        **_read(),
        "version_end": "2019-12-31",
        "coverage": [["2026-01-01", None], ["2010-01-01", "2012-12-31"]],
    }
    run = lsi.parse_engine_references([_result("us/a.yaml", item)])
    assert run.bindings == {
        lsi.Binding(
            "us:a#r",
            Y2018,
            "t",
            "derived",
            date(2010, 1, 1),
            date(2019, 12, 31),
            ((date(2010, 1, 1), date(2012, 12, 31)), (Y2026, OPEN)),
        )
    }


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ('{"root_error": "not canonical"}', "refused the checkout"),
        ('{"module": "us/a.yaml"}', "malformed result"),
        ('{"ok": true}', "malformed result"),
    ],
)
def test_parse_engine_references_refuses_what_it_cannot_read(line, message):
    with pytest.raises(SystemExit, match=message):
        lsi.parse_engine_references([line])


def test_parse_engine_references_refuses_a_second_result_for_a_module():
    with pytest.raises(SystemExit, match="second result"):
        lsi.parse_engine_references([_result("us/a.yaml"), _result("us/a.yaml")])


def _run(
    *compiled, bindings=(), inputs=(), collisions=(), results=None, rules=()
) -> "lsi.EngineRun":
    return lsi.EngineRun(
        set(results if results is not None else compiled),
        set(compiled),
        {},
        set(bindings),
        set(inputs),
        set(collisions),
        set(rules),
    )


def _static(rule="us:a#r", target="us:b#t", namespace="derived") -> "lsi.Reference":
    return lsi.Reference(rule, Y2018, target, Y2026, namespace, coverage=((Y2026, OPEN),))


MODULES = {
    "us:a": lsi.Module(rules=tuple(_rule(name, (Y2018, "t")) for name in "rsu")),
    "us:b": lsi.Module(),
}


def test_reference_differences_compare_only_modules_the_engine_compiled():
    run = _run("us:a", bindings={_binding(), _binding(rule="us:a#s")})
    differences = lsi.reference_differences(
        run,
        {_static(), _static(rule="us:a#u"), _static(rule="us:refused#r")},
        MODULES,
    )
    assert differences.only_engine == {_binding(rule="us:a#s")}
    assert differences.only_static == {_binding(rule="us:a#u")}


def test_reference_differences_key_on_name_namespace_and_every_date():
    for different in (
        _static(target="us:b#other"),
        _static(namespace="parameter"),
        replace(_static(), target_start=Y2018, coverage=((Y2018, OPEN),)),
        replace(_static(), version_end=date(2020, 12, 31)),
        replace(_static(), coverage=((Y2026, date(2027, 12, 31)),)),
        replace(_static(), coverage=((date(2010, 1, 1), date(2011, 12, 31)), (Y2026, OPEN))),
    ):
        differences = lsi.reference_differences(
            _run("us:a", bindings={_binding()}), {different}, MODULES
        )
        assert differences.only_engine and differences.only_static


def test_reference_differences_ignore_which_module_defined_the_name():
    # The engine's ids cannot answer that when names collide.
    differences = lsi.reference_differences(
        _run("us:a", bindings={_binding()}), {_static(target="us:a#t")}, MODULES
    )
    assert not differences.only_engine and not differences.only_static


def test_reference_differences_read_the_name_a_sets_relation_replaced():
    static = lsi.Reference(
        "us:a#r", Y2018, "us:c#value", Y2026, lsi.DERIVED, "t", coverage=((Y2026, OPEN),)
    )
    differences = lsi.reference_differences(_run("us:a", bindings={_binding()}), {static}, MODULES)
    assert not differences.only_engine and not differences.only_static


def test_the_other_side_of_a_collision_is_a_difference():
    # Round 4: the model binds each name where the lowering does, so a read of
    # the other namespace is a misread, not a choice.
    run = _run("us:a", bindings={_binding()}, collisions={"us:a#t"})
    differences = lsi.reference_differences(
        run, {_static(), _static(namespace="parameter")}, MODULES
    )
    assert differences.only_static == {_binding(namespace="parameter")}


def test_a_collision_excuses_no_read_the_engine_never_made():
    # Round 2: a composition's own rules fell out of the report, and a colliding
    # name then excused the binding left behind.
    run = _run("us:a", collisions={"us:a#t"})
    differences = lsi.reference_differences(run, {_static()}, MODULES)
    assert differences.only_static == {_binding()}


def test_a_collision_excuses_no_input_read():
    run = _run(
        "us:a", inputs={_binding(namespace="input", start=None)}, collisions={"us:a#t"}
    )
    differences = lsi.reference_differences(run, {_static()}, MODULES)
    assert differences.only_static == {_binding()}


def test_a_parameter_read_the_engine_lowered_to_an_input_is_a_difference():
    run = _run("us:a", inputs={_binding(namespace="input", start=None)})
    differences = lsi.reference_differences(run, {_static(namespace="parameter")}, MODULES)
    assert differences.only_static == {_binding(namespace="parameter")}


def test_a_derived_read_the_engine_lowered_to_an_input_is_a_difference():
    run = _run("us:a", inputs={_binding(namespace="input", start=None)})
    differences = lsi.reference_differences(run, {_static()}, MODULES)
    assert differences.only_static == {_binding()}


def test_an_imported_derived_rule_beside_a_local_parameter_says_nothing_about_this_module():
    run = _run(
        "us:a",
        bindings={_binding(rule="us:a#shared", name="t")},
        collisions={"us:a#shared"},
    )
    modules = {"us:a": lsi.Module(rules=(_parameter("shared", Y2018),))}
    assert lsi.reference_differences(run, set(), modules).only_engine == set()


def test_a_declared_rule_with_a_colliding_name_still_counts():
    run = _run(
        "us:a",
        bindings={_binding(rule="us:a#shared", name="t")},
        collisions={"us:a#shared"},
    )
    modules = {"us:a": lsi.Module(rules=(_rule("shared", (Y2018, "t")),))}
    assert lsi.reference_differences(run, set(), modules).only_engine == {
        _binding(rule="us:a#shared", name="t")
    }


def test_a_declared_rule_the_program_does_not_hold_that_way_is_a_difference():
    modules = {"us:a": lsi.Module(rules=(_rule("r", (Y2018, "1")), _parameter("q", Y2018)))}
    versions = ((Y2018, OPEN),)
    r, q = ("us:a#r", "derived", versions), ("us:a#q", "parameter", versions)

    def differences(*held):
        return lsi.reference_differences(_run("us:a", rules=held), set(), modules)

    assert differences(r, q).missing_rules == set()
    assert differences(r, q).extra_rules == set()
    assert differences(r).missing_rules == {q}
    moved = differences(("us:a#r", "parameter", versions), q)
    assert moved.missing_rules == {r}
    assert moved.extra_rules == {("us:a#r", "parameter", versions)}
    redated = differences(("us:a#r", "derived", ((Y2026, OPEN),)), q)
    assert redated.missing_rules == {r}
    # Round 3: an imported definition of a declared name in the other
    # namespace is a difference too, so a misread rule cannot hide behind it.
    both = differences(r, q, ("us:a#q", "derived", ((Y2026, OPEN),)))
    assert both.extra_rules == {("us:a#q", "derived", ((Y2026, OPEN),))}


def test_declared_rules_hold_every_version_of_a_merged_name():
    modules = {
        "us:b": lsi.Module(rules=(_parameter("q", Y2026),)),
        "us:a": lsi.Module(imports=("us:b",), rules=(_parameter("q", Y2018),)),
    }
    assert lsi.declared_rules(modules, ["us:a"]) == {
        ("us:a#q", "parameter", ((Y2018, OPEN), (Y2026, OPEN)))
    }


TRACKED = [f"us/statutes/{index}.yaml" for index in range(200)]
TARGETS = {lsi.canonical_target(path) for path in TRACKED}


def test_coverage_passes_on_a_full_run():
    assert lsi.coverage_failures(_run(*TARGETS), TRACKED, {_edge("us:statutes/0#r")}) == []


def test_coverage_allows_a_refused_module_with_no_edge():
    run = _run(*sorted(TARGETS)[1:], results=TARGETS)
    assert lsi.coverage_failures(run, TRACKED, set()) == []


def test_coverage_fails_a_run_with_no_results():
    failures = lsi.coverage_failures(_run(), TRACKED, set())
    assert any("no result for 200 module(s)" in failure for failure in failures)
    assert any("below the 99% floor" in failure for failure in failures)


def test_coverage_fails_when_the_engine_refuses_most_of_the_tree():
    run = _run(*sorted(TARGETS)[:100], results=TARGETS)
    failures = lsi.coverage_failures(run, TRACKED, set())
    assert any("compiled 100 of 200" in failure for failure in failures)


def test_coverage_fails_when_a_module_has_no_result():
    run = _run(*sorted(TARGETS)[1:])
    assert any("no result for 1 module(s)" in item for item in lsi.coverage_failures(run, TRACKED, set()))


def test_coverage_fails_on_a_result_for_an_untracked_module():
    run = _run(*TARGETS, "us:statutes/untracked")
    assert any("untracked" in item for item in lsi.coverage_failures(run, TRACKED, set()))


def test_coverage_fails_on_an_edge_in_a_refused_module():
    refused = sorted(TARGETS)[0]
    run = _run(*(TARGETS - {refused}), results=TARGETS)
    failures = lsi.coverage_failures(run, TRACKED, {_edge(f"{refused}#r")})
    assert any("1 edge(s) in modules the engine refused" in failure for failure in failures)


def test_coverage_fails_when_the_port_refused_a_formula_the_engine_lowered():
    first, second = sorted(TARGETS)[:2]
    compiled = _run(*TARGETS)
    failures = lsi.coverage_failures(compiled, TRACKED, set(), {first})
    assert failures == [f"the port refused a formula in 1 module(s) the engine compiled: {[first]}"]
    # The engine refused `second` too, so the token reader stood in for both.
    refused = _run(*(TARGETS - {second}), results=TARGETS)
    assert lsi.coverage_failures(refused, TRACKED, set(), {second}) == []


def test_the_differential_refuses_a_run_that_compiled_nothing(tmp_path, monkeypatch, capsys):
    """A green exit needs coverage, not only agreement on an empty set."""
    root = tmp_path / "rulespec-us"
    _write(root, "us/statutes/1/target.yaml", TARGET)
    _write(root, "us/statutes/1/importer.yaml", MODULE_TEMPLATE.format(start="2018-01-01"))
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    engine = tmp_path / "engine"
    engine.mkdir()
    (engine / "Cargo.toml").write_text("", encoding="utf-8")
    refused = json.dumps({"module": "us/statutes/1/importer.yaml", "ok": False, "error": "drift"})

    real_run = subprocess.run

    def fake_run(command, **kwargs):
        if command[0] == "git":
            return real_run(command, **kwargs)
        if command[0] == "cargo":
            return subprocess.CompletedProcess(command, 0)
        return subprocess.CompletedProcess(command, 0, stdout=refused + "\n", stderr="")

    monkeypatch.setattr(lsi.subprocess, "run", fake_run)
    assert lsi.differential(engine, root, tmp_path / "out.jsonl") == 1
    output = capsys.readouterr().out
    assert "This run does not cover the tree" in output
    assert "equal the engine" not in output


def test_the_differential_fails_on_a_rule_the_program_does_not_hold(
    tmp_path, monkeypatch, capsys
):
    root = tmp_path / "rulespec-us"
    _write(root, "us/statutes/1/target.yaml", TARGET)
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    engine = tmp_path / "engine"
    engine.mkdir()
    (engine / "Cargo.toml").write_text("", encoding="utf-8")
    real_run = subprocess.run

    def fake_run(command, **kwargs):
        if command[0] == "git":
            return real_run(command, **kwargs)
        if command[0] == "cargo":
            return subprocess.CompletedProcess(command, 0)
        stdout = _result("us/statutes/1/target.yaml") + "\n"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(lsi.subprocess, "run", fake_run)
    assert lsi.differential(engine, root, tmp_path / "out.jsonl") == 1
    assert "us:statutes/1/target#later_amount as a parameter" in capsys.readouterr().out


def test_scratch_copy_keeps_every_scalar_the_engine_would_read(tmp_path):
    text = (
        "rules:\n"
        "  - name: 'yes'\n"
        "    kind: derived\n"
        "    versions:\n"
        "      - {from: 2018-01-01, to: '2019-01-01', formula: yes}\n"
        "      - {from: 2020-01-01, formula: 1e3}\n"
        "      - {from: 2021-01-01, formula: '1e3'}\n"
        "      - {from: 2022-01-01, formula: -5}\n"
        "      - {from: 2023-01-01, formula: true}\n"
    )
    _write(tmp_path, "us/a.yaml", text)
    root = lsi.write_scratch_root(tmp_path, ["us/a.yaml"], tmp_path / "scratch")
    written = (root / "us/a.yaml").read_text(encoding="utf-8")
    assert yaml.load(written, Loader=lsi.EngineLoader)["rules"] == (
        yaml.load(text, Loader=lsi.EngineLoader)["rules"]
    )
    assert '"1e3"' in written and '"yes"' in written


def test_scratch_copy_keeps_executable_content_and_drops_citations(tmp_path):
    source = {
        "format": "rulespec/v1",
        "imports": None,
        "module": {
            "kind": "composition",
            "source_verification": {"corpus_citation_paths": ["us/statute/1"]},
        },
        "rules": [
            {
                "name": "r",
                "kind": "derived",
                "metadata": {"proof": {"atoms": []}},
                "versions": [{"effective_from": "2018-01-01", "formula": "a"}],
            }
        ],
    }
    atomic = {"format": "rulespec/v1", "module": {"summary": "text"}, "rules": []}
    _write(tmp_path, "us/a.yaml", yaml.safe_dump(source))
    _write(tmp_path, "us/b.yaml", yaml.safe_dump(atomic))
    root = lsi.write_scratch_root(tmp_path, ["us/a.yaml", "us/b.yaml"], tmp_path / "scratch")
    assert root.name == "rulespec-us"
    written = yaml.safe_load((root / "us/a.yaml").read_text(encoding="utf-8"))
    assert written["module"] == {"kind": "composition"}
    assert written["imports"] == []
    assert written["rules"] == [
        {
            "name": "r",
            "kind": "derived",
            "versions": [{"effective_from": "2018-01-01", "formula": "a"}],
        }
    ]
    assert yaml.safe_load((root / "us/b.yaml").read_text(encoding="utf-8"))["module"] == {}
    assert lsi.parse_module((tmp_path / "us/a.yaml").read_text(), "a") == lsi.parse_module(
        (root / "us/a.yaml").read_text(), "a"
    )
