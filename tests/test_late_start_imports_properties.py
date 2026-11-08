"""Property-based tests for the late-start import ratchet (tools/late_start_imports.py).

Invariants:

1. Run-time meaning. For every generated program without a `sets` relation, the
   dates on which each rule stops on each name it reads equal the tool's stop
   dates, names defined in both namespaces included. A reference simulation
   below finds those dates without the tool's formula port or interval code:
   it binds names the way lower_to_scalar does, by position (every generated
   formula reads in a scalar position, so a parameter wins), flattens imports,
   sorts each rule into a namespace, and on each stretch of dates where nothing
   changes picks the version the engine picks and looks for a name it reads
   with no version then. Generated formulas take every branch, so "stops" and
   "can read the gap" agree here; the tool makes no claim about a branch a date
   never takes.
2. Edges render stop dates: each edge starts on a stop date of its rule for a
   name its target supplies, and each (rule, name) with stop dates has an edge
   whose target supplies that name.
3. Scope: a `#fragment` never changes the result, and a crossing reference
   names a definition in the import closure, or in its own module only when a
   `sets` relation put it in place of an imported definition.
4. Monotonicity: taking dates from a name's versions never removes another
   rule's stop date, and starting a rule's earliest version earlier never
   removes one of that rule's own.
5. Determinism: the result does not depend on the order of modules, rules or
   versions, nor on the order of imports where no `sets` relation acts (there,
   merge order decides, as it does in the engine). Reduction to edges does not
   depend on the order of references.
6. Lexing and parsing: words in strings, comments and docstrings are never
   references, and the name of a called function is never one, however it is
   parenthesized, even where a derived rule carries that name. The token
   pattern and the ported lexer agree on whether a formula leaves a quote open.
7. Interval algebra: `merged`, `subtract`, `windows` and `widened` agree with a
   day-by-day count on every input.
8. Baseline round trip: parse(render(S)) == S and render is canonical.
9. The gate passes iff the edges equal the baseline and no (rule, name) stops
   on a date the protected base does not. An unlisted edge and a listed edge
   that no longer holds each fail it whatever the label says.

The generated programs hold only what the engine loads: no import cycle, one
derived rule per name per program, no derived cycle, and `sets` relations only
where every root that flattens them resolves both sides to entries of one kind
whose metadata agree. They carry end dates, tables, collisions between
namespaces and `sets` relations.

Hypothesis is not installed in the shared validate workflow's pytest leg, so
these skip there; the late-start-imports workflow installs it and runs them.

`test_the_pinned_engine_binds_what_the_tool_reads` needs no simulation: the
engine-differential job points LATE_START_HARNESS at the compiled harness, and
the engine lowers the same generated programs, `sets` relations and end dates
included, and must bind every name with the versions the tool says.
"""

from __future__ import annotations

import importlib.util
import os
import random
import sys
import tempfile
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, assume, find, given, settings, target, strategies as st  # noqa: E402

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "late_start_imports.py"
_spec = importlib.util.spec_from_file_location("late_start_imports", TOOL_PATH)
lsi = importlib.util.module_from_spec(_spec)
sys.modules["late_start_imports"] = lsi
_spec.loader.exec_module(lsi)

semantic_properties = settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])

HARNESS = os.environ.get("LATE_START_HARNESS")
OPEN = lsi.OPEN

TARGETS = ("us:statutes/a", "us:statutes/b", "us:statutes/c", "us:statutes/d")
NAMES = ("p", "q", "r", "s")
STARTS = tuple(date(year, 1, 1) for year in (2000, 2010, 2020, 2030))


def end_of(start: date) -> date:
    """An ended version runs four years: before the next start, as the engine
    requires of an explicit end."""
    return date(start.year + 4, 1, 1) - timedelta(days=1)


# A formula is generated from the names it reads, so the reference simulation
# never depends on the lexer it is checking. The sizes keep graphs dense: most
# draws hold an edge, so the properties below see real cases. A rule never
# reads its own name, which the engine refuses.
#
# Every rule below names a shape, which fixes what the YAML says. `kind` differs
# from the namespace on purpose, because the engine ignores it here:
#   derived   kind derived, an entity, reads names: derived namespace
#   computed  kind parameter, no entity, reads names: derived namespace
#   constant  kind parameter, an entity, a literal: derived namespace
#   scalar    kind parameter, no entity, a literal: parameter namespace
#   flagless  kind derived, no entity, a literal: parameter namespace
#   valued    a parameter table
#   stale     a table whose first date holds only a formula, which the engine drops
#
# A module is (imports, rules, ended, relations): `ended` holds the (name, start)
# of each version that ends after four years, and `relations` each `sets`
# relation as (target module, target name, value module, value name).
READING = ("derived", "computed")
LITERAL = ("scalar", "flagless")
TABLE = ("valued", "stale")
DERIVED_SHAPES = (*READING, "constant")
VALUE_SHAPES = ("constant", *LITERAL, *TABLE)
reads = st.sets(st.sampled_from(NAMES), min_size=1, max_size=3)
dated_reads = st.dictionaries(st.sampled_from(STARTS), reads, min_size=1, max_size=3)
dated_values = st.sets(st.sampled_from(STARTS), min_size=1, max_size=2)
reading_rule = st.tuples(st.sampled_from(READING), dated_reads)
value_rule = st.tuples(st.sampled_from(VALUE_SHAPES), dated_values)
rule_shapes = st.one_of(reading_rule, reading_rule, value_rule)
rules = st.dictionaries(st.sampled_from(NAMES), rule_shapes, min_size=1, max_size=2)
ended = st.frozensets(st.tuples(st.sampled_from(NAMES), st.sampled_from(STARTS)), max_size=3)


def imports_for(index: int):
    """Only later modules, so no graph holds a cycle, which the engine refuses."""
    later = TARGETS[index + 1 :]
    return st.sets(st.sampled_from(later), min_size=1, max_size=3) if later else st.just(set())


def relations_for(index: int):
    here = st.sampled_from(TARGETS[index:])
    return st.lists(
        st.tuples(here, st.sampled_from(NAMES), here, st.sampled_from(NAMES)), max_size=2
    ).map(tuple)


def loadable(spec):
    """What the engine refuses goes: a second derived rule of a name in one
    flattened program becomes a scalar, and so does a reading rule left in a
    derived cycle, which `derived_cycle` finds. Each `sets` relation first aims
    at names its modules define (see `aimed`). It stays only when its value
    reads nothing, both sides sit in the module or its closure, and every root
    that flattens it resolves both sides to entries of one kind whose metadata
    agree."""
    spec = {
        owner: (imported, dict(defined), stopped, relations)
        for owner, (imported, defined, stopped, relations) in spec.items()
    }
    for root in TARGETS:
        kept: dict[str, str] = {}
        for owner in sorted(closure(root, spec) | {root}):
            for name, (shape, body) in spec[owner][1].items():
                if shape in DERIVED_SHAPES and kept.setdefault(name, owner) != owner:
                    spec[owner][1][name] = ("scalar", set(body))
        while cycle := derived_cycle(root, spec):
            owner, name = cycle
            spec[owner][1][name] = ("scalar", set(spec[owner][1][name][1]))
    for owner, (imported, defined, stopped, relations) in list(spec.items()):
        scope = closure(owner, spec) | {owner}
        spec[owner] = (
            imported,
            defined,
            stopped,
            tuple(
                relation
                for relation in (aimed(item, spec) for item in relations)
                if relation[0] in scope
                and relation[2] in scope
                and relation[1] in spec[relation[0]][1]
                and spec[relation[2]][1].get(relation[3], ("", ()))[0] in VALUE_SHAPES
                and relation[:2] != relation[2:]
            ),
        )
    while True:
        modules = build(spec)
        refused = [
            root
            for root in TARGETS
            if lsi.program(root, lsi.flattened(root, modules), modules) is None
        ]
        if not refused:
            return spec
        owner = max(
            (owner for owner in closure(refused[0], spec) | {refused[0]} if spec[owner][3]),
            key=TARGETS.index,
        )
        imported, defined, stopped, relations = spec[owner]
        spec[owner] = (imported, defined, stopped, relations[:-1])


# What apply_source_relation_sets compares between a target and its value, by
# the shape that decides it in rule_yaml: the namespace, then an entity, dtype
# and period for a derived rule, or `indexed_by` for a parameter.
METADATA = {
    **dict.fromkeys(("derived", "constant"), ("derived", "Person", "Integer", "Month")),
    "computed": ("derived", "", "", ""),
    **dict.fromkeys(LITERAL, ("parameter", "")),
    **dict.fromkeys(TABLE, ("parameter", "size")),
}


def aimed(relation, spec):
    """A drawn relation aimed at names its modules define: the target at one of
    its module's rules, and the value at a rule that reads nothing, preferring
    one whose metadata match the target's. Names drawn blind would leave almost
    every relation pointing at nothing, or at entries the engine refuses to
    copy between. lsi.program stays the arbiter: `loadable` drops whatever it
    refuses."""
    target_module, target_name, value_module, value_name = relation
    defined = sorted(spec[target_module][1])
    if target_name not in defined:
        target_name = defined[NAMES.index(target_name) % len(defined)]
    values = sorted(
        name for name, (shape, _) in spec[value_module][1].items() if shape in VALUE_SHAPES
    )
    wanted = METADATA[spec[target_module][1][target_name][0]]
    values = [
        name for name in values if METADATA[spec[value_module][1][name][0]] == wanted
    ] or values
    if values and value_name not in values:
        value_name = values[NAMES.index(value_name) % len(values)]
    return (target_module, target_name, value_module, value_name)


def derived_cycle(root, spec) -> tuple[str, str] | None:
    """A (module, name) on a derived dependency cycle in this root's program."""
    scope = closure(root, spec) | {root}
    # In a scalar position a parameter wins, so only a derived binding follows.
    follows = {}
    for owner in sorted(scope):
        for name, (shape, body) in spec[owner][1].items():
            if shape in READING:
                follows[name] = (owner, {read for reads in body.values() for read in reads} - {name})

    def reaches(start, name, seen):
        if name not in follows or name in seen:
            return False
        seen.add(name)
        return any(
            read == start or reaches(start, read, seen)
            for read in follows[name][1]
            if not scalar_group(read, scope, spec, tables_only=True)
        )

    for name in sorted(follows):
        if reaches(name, name, set()):
            return follows[name][0], name
    return None


specs = st.fixed_dictionaries(
    {
        owner: st.tuples(imports_for(index), rules, ended, relations_for(index))
        for index, owner in enumerate(TARGETS)
    }
).map(loadable)


def without_relations(spec):
    return {owner: (*body[:3], ()) for owner, body in spec.items()}


plain_specs = specs.map(without_relations)


def formula(names, own) -> str:
    return " + ".join(sorted(set(names) - {own})) or "1 + 1"


def dated(start: date, name: str, stopped) -> dict:
    version = {"from": start.isoformat()}
    if (name, start) in stopped:
        version["to"] = end_of(start).isoformat()
    return version


def rule_yaml(name, shape, body, stopped) -> dict:
    kind = "derived" if shape in ("derived", "flagless") else "parameter"
    rule = {"name": name, "kind": kind}
    if shape in ("derived", "constant"):
        rule.update(entity="Person", dtype="Integer", period="Month")
    if shape in READING:
        rule["versions"] = [
            {**dated(start, name, stopped), "formula": formula(read, name)}
            for start, read in sorted(body.items())
        ]
    elif shape in ("constant", *LITERAL):
        rule["versions"] = [
            {**dated(start, name, stopped), "formula": "1"} for start in sorted(body)
        ]
    else:
        rule["indexed_by"] = "size"
        rule["versions"] = [
            {**dated(start, name, stopped), "values": {0: 1}} for start in sorted(body)
        ]
        if shape == "stale":
            rule["versions"].insert(0, {"from": "1990-01-01", "formula": "p + q"})
    return rule


def relation_yaml(index, number, relation) -> dict:
    target, value = f"{relation[0]}#{relation[1]}", f"{relation[2]}#{relation[3]}"
    return {
        "name": f"assignment_{index}_{number}",
        "kind": "source_relation",
        "source_relation": {
            "type": "sets",
            "target": target,
            "value": value,
            "basis": {"delegation": target},
        },
    }


def module_text(owner, imported, defined, stopped, relations) -> str:
    index = TARGETS.index(owner)
    return yaml.safe_dump(
        {
            "format": "rulespec/v1",
            "module": {},
            "imports": sorted(imported),
            "rules": [
                *(relation_yaml(index, number, item) for number, item in enumerate(relations)),
                *(rule_yaml(name, *defined[name], stopped) for name in sorted(defined)),
            ],
        }
    )


def build(spec) -> dict[str, "lsi.Module"]:
    """Through the YAML parser, so these properties cover the sorting into namespaces."""
    return {owner: lsi.parse_module(module_text(owner, *body)) for owner, body in spec.items()}


def closure(owner, spec) -> set[str]:
    """The engine's flattening: each imported module and everything it imports."""
    seen: set[str] = set()

    def visit(current):
        for imported in spec[current][0]:
            if imported not in seen:
                seen.add(imported)
                visit(imported)

    visit(owner)
    seen.discard(owner)
    return seen


def definitions(name, scope, spec) -> list[tuple[str, str, object]]:
    return [
        (owner, *spec[owner][1][name]) for owner in sorted(scope) if name in spec[owner][1]
    ]


def spans(owner, name, starts, spec) -> list[tuple[date, date]]:
    stopped = spec[owner][2]
    return [(start, end_of(start) if (name, start) in stopped else OPEN) for start in starts]


def scalar_group(name, scope, spec, tables_only=False) -> list[tuple[str, date, date]]:
    """What lower_to_scalar binds a name to: a parameter if any exists, so a table
    or else the merged scalars, and only then a derived rule. Each entry is
    (module, from, to), for the versions that survive lowering."""
    found = definitions(name, scope, spec)
    tables = [(owner, body) for owner, shape, body in found if shape in TABLE]
    literals = [(owner, body) for owner, shape, body in found if shape in LITERAL]
    derived = [(owner, body) for owner, shape, body in found if shape in DERIVED_SHAPES]
    chosen = tables or literals or ([] if tables_only else derived)
    return [
        (owner, start, end) for owner, body in chosen for start, end in spans(owner, name, body, spec)
    ]


def in_both_namespaces(name, scope, spec) -> bool:
    shapes = {shape for _, shape, _ in definitions(name, scope, spec)}
    return bool(shapes & {*TABLE, *LITERAL}) and bool(shapes & set(DERIVED_SHAPES))


# Nothing changes inside these stretches: each starts on a version's start or
# on the day after a version ends.
CUTS = sorted({*STARTS, *(end_of(start) + timedelta(days=1) for start in STARTS)})
STRETCHES = [
    (cut, CUTS[index + 1] - timedelta(days=1) if index + 1 < len(CUTS) else OPEN)
    for index, cut in enumerate(CUTS)
]


def applies(start: date, end: date, day: date) -> bool:
    return start <= day <= end


def simulated_stops(spec) -> dict[tuple[str, str], tuple[tuple[date, date], ...]]:
    """Per (rule, name), the dates a run stops on a name an import feeds.

    On each date a rule answers from the version the engine picks: of those that
    apply, the latest started (Derived::semantics_at). The stop is a name that
    version reads, bound to nothing that applies then, when an imported module
    feeds the name.
    """
    stops: dict[tuple[str, str], list[tuple[date, date]]] = {}
    for origin, (_, defined, _, _) in spec.items():
        scope = closure(origin, spec) | {origin}
        for name, (shape, body) in defined.items():
            if shape not in READING:
                continue
            versions = [
                (start, end, body[start]) for start, end in spans(origin, name, body, spec)
            ]
            for first, last in STRETCHES:
                picked = [item for item in versions if applies(item[0], item[1], first)]
                if not picked:
                    continue
                for read in max(picked)[2]:
                    if read == name:
                        continue
                    group = scalar_group(read, scope, spec)
                    if not any(owner != origin for owner, _, _ in group):
                        continue
                    if not any(applies(start, end, first) for _, start, end in group):
                        stops.setdefault((f"{origin}#{name}", read), []).append((first, last))
    return {key: lsi.merged(runs) for key, runs in stops.items()}


def edges_of(modules):
    return lsi.late_start_edges(lsi.import_references(modules))


def stops_of(modules):
    return lsi.stop_dates(lsi.import_references(modules))


def _shapes(spec):
    return {shape for _, defined, _, _ in spec.values() for shape, _ in defined.values()}


def _collides(spec):
    return any(
        in_both_namespaces(name, closure(owner, spec) | {owner}, spec)
        for owner in spec
        for name in NAMES
    )


def _reach(condition):
    """A seeded search, so a generator that stops reaching a shape fails every
    run instead of now and then."""
    return find(
        specs,
        condition,
        settings=settings(deadline=None, database=None, max_examples=3000),
        random=random.Random(0),
    )


@pytest.mark.parametrize(
    "reached",
    [
        lambda spec: "stale" in _shapes(spec) and bool(simulated_stops(without_relations(spec))),
        _collides,
        lambda spec: any(spec[owner][0] for owner in TARGETS[:-1]),
        lambda spec: any(edge.resumes == OPEN for edge in edges_of(build(spec))),
        lambda spec: any(
            run[0] not in STARTS for runs in stops_of(build(spec)).values() for run in runs
        ),
        lambda spec: any(body[3] for body in spec.values())
        and stops_of(build(spec)) != stops_of(build(without_relations(spec))),
    ],
    ids=["stale-table", "collision", "imports", "never-resumes", "interior-gap", "sets"],
)
def test_the_generators_reach_each_hard_shape_and_stay_loadable(reached):
    spec = _reach(reached)
    for owner, (imported, _, _, _) in spec.items():
        assert all(TARGETS.index(item) > TARGETS.index(owner) for item in imported)
    modules = build(spec)
    for root in TARGETS:
        assert lsi.program(root, lsi.flattened(root, modules), modules) is not None
        scope = closure(root, spec) | {root}
        for name in NAMES:
            derived = [
                owner
                for owner, shape, _ in definitions(name, scope, spec)
                if shape in DERIVED_SHAPES
            ]
            assert len(derived) <= 1
        assert derived_cycle(root, spec) is None


@settings(semantic_properties, max_examples=500)
@given(plain_specs)
def test_each_stop_date_is_the_tools(spec):
    found = stops_of(build(spec))
    target(float(len(found)))
    assert found == simulated_stops(spec)


@semantic_properties
@given(specs)
def test_edges_render_the_stop_dates(spec):
    references = lsi.import_references(build(spec))
    stops = lsi.stop_dates(references)
    names: dict[tuple[str, str], set[str]] = {}
    for item in references:
        names.setdefault((item.rule, item.target), set()).add(item.read_name)
    edges = lsi.late_start_edges(references)
    for edge in edges:
        assert any(
            lsi.subtract([(edge.start, edge.start)], stops.get((edge.rule, name), ())) == ()
            for name in names[(edge.rule, edge.target)]
        )
    carried = {(edge.rule, name) for edge in edges for name in names[(edge.rule, edge.target)]}
    assert set(stops) <= carried


@pytest.mark.skipif(not HARNESS, reason="the engine-differential job builds the harness")
@settings(semantic_properties, max_examples=150)
@given(specs)
def test_the_pinned_engine_binds_what_the_tool_reads(spec):
    with tempfile.TemporaryDirectory(prefix="late-start-generated-") as scratch:
        root = Path(scratch) / "tree"
        paths = []
        for owner, body in spec.items():
            relative = lsi.module_path(f"{owner}#x")
            paths.append(relative)
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(module_text(owner, *body), encoding="utf-8")
        run = lsi.parse_engine_references(
            lsi.run_harness(Path(HARNESS), root, paths).splitlines()
        )
    assert run.refused == {}
    target(float(len(run.bindings)))
    modules = build(spec)
    differences = lsi.reference_differences(run, lsi.all_references(modules), modules)
    assert differences.only_engine == set()
    assert differences.only_static == set()
    assert differences.missing_rules == set()
    assert differences.extra_rules == set()


@semantic_properties
@given(specs, st.sampled_from(NAMES))
def test_a_fragment_never_changes_the_result(spec, fragment):
    modules = build(spec)
    fragmented = {
        owner: replace(
            module, imports=tuple(f"{specifier}#{fragment}" for specifier in module.imports)
        )
        for owner, module in modules.items()
    }
    assert lsi.import_references(fragmented) == lsi.import_references(modules)


@semantic_properties
@given(specs)
def test_a_crossing_reference_names_a_definition_inside_the_import_closure(spec):
    modules = build(spec)
    for reference in lsi.import_references(modules):
        origin, _ = reference.rule.split("#")
        owner, name = reference.target.split("#")
        assert owner in lsi.import_closure(origin, modules) | {origin}
        assert any(rule.name == name for rule in modules[owner].rules)
        if owner == origin:
            assert reference.name not in ("", name)


@semantic_properties
@given(specs)
def test_import_references_are_the_crossing_part_of_all_references(spec):
    modules = build(spec)
    crossing = lsi.import_references(modules)
    everything = lsi.all_references(modules)
    assert crossing <= everything
    assert all(
        item.rule.split("#")[0] == item.target.split("#")[0] for item in everything - crossing
    )


@semantic_properties
@given(specs)
def test_a_table_never_reads_and_never_starts_before_its_values(spec):
    modules = build(spec)
    tables = {
        (owner, name): body
        for owner, (_, defined, _, _) in spec.items()
        for name, (shape, body) in defined.items()
        if shape in TABLE
    }
    for (owner, name), body in tables.items():
        rule = next(item for item in modules[owner].rules if item.name == name)
        assert rule.table and rule.namespace == lsi.PARAMETER
        assert rule.start == min(body)
        assert not any(version.formula for version in rule.versions)
    assert not any(
        item.rule in {f"{owner}#{name}" for owner, name in tables}
        for item in lsi.all_references(modules)
    )


def _restricted(stops, keep):
    return {key: runs for key, runs in stops.items() if keep(key)}


@semantic_properties
@given(specs, st.sampled_from(NAMES))
def test_taking_dates_from_a_name_never_removes_another_rules_stop(spec, name):
    modules = build(spec)

    def later(rule):
        return replace(
            rule,
            versions=tuple(
                replace(version, start=version.start + timedelta(days=365))
                for version in rule.versions
            ),
        )

    moved = {
        owner: replace(
            module,
            rules=tuple(later(rule) if rule.name == name else rule for rule in module.rules),
        )
        for owner, module in modules.items()
    }

    def other(key):
        return key[0].split("#", 1)[1] != name

    before = _restricted(stops_of(modules), other)
    assert lsi.widened(before, stops_of(moved)) == {}


@semantic_properties
@given(specs, st.data())
def test_starting_a_rule_earlier_never_removes_its_own_stop(spec, data):
    modules = build(spec)
    stops = stops_of(modules)
    assume(stops)
    rule_id = data.draw(st.sampled_from(sorted({rule for rule, _ in stops})))
    origin, name = rule_id.split("#")
    rule = next(item for item in modules[origin].rules if item.name == name)
    first = min(rule.versions)
    earlier = replace(
        rule,
        versions=tuple(
            replace(version, start=version.start - timedelta(days=365))
            if version == first
            else version
            for version in rule.versions
        ),
    )
    module = modules[origin]
    moved = {
        **modules,
        origin: replace(
            module, rules=tuple(earlier if item.name == name else item for item in module.rules)
        ),
    }
    own = _restricted(stops, lambda key: key[0] == rule_id)
    assert lsi.widened(own, stops_of(moved)) == {}


@semantic_properties
@given(specs, st.randoms(use_true_random=False))
def test_the_result_does_not_depend_on_declaration_order(spec, rng: random.Random):
    def shuffled(items):
        items = list(items)
        rng.shuffle(items)
        return items

    modules = build(spec)
    merge_order_matters = any(module.sets for module in modules.values())
    reordered = {
        owner: replace(
            modules[owner],
            imports=tuple(
                modules[owner].imports if merge_order_matters else shuffled(modules[owner].imports)
            ),
            rules=tuple(
                replace(rule, versions=tuple(shuffled(rule.versions)))
                for rule in shuffled(modules[owner].rules)
            ),
        )
        for owner in shuffled(modules)
    }
    assert lsi.import_references(reordered) == lsi.import_references(modules)
    references = sorted(lsi.import_references(modules))
    assert lsi.late_start_edges(shuffled(references)) == lsi.late_start_edges(references)


words = st.sampled_from(NAMES)
CALLEES = ("max", "min", "floor", "ceil")
callees = st.sampled_from(CALLEES)
noise = st.one_of(
    words.map(lambda word: f'"{word}"'),
    words.map(lambda word: f"'{word}'"),
    words.map(lambda word: f"0 # {word}\n"),
    words.map(lambda word: f'"""{word} {word}""" 0'),
    callees.map(lambda callee: f"{callee}(0)"),
    callees.map(lambda callee: f"{callee} # note\n(0)"),
    callees.map(lambda callee: f"({callee})(0)"),
    callees.map(lambda callee: f"(({callee}))\n(0)"),
)
# Every word and every callee names a derived rule, so a read that a string, a
# comment or a call produced would show.
NOISY_SCOPE = lsi.Scope(derived=frozenset({*NAMES, *CALLEES}))


@semantic_properties
@given(st.sets(words), st.lists(noise, max_size=4), st.randoms(use_true_random=False))
def test_strings_comments_and_calls_are_never_references(names, extras, rng):
    parts = [*sorted(names), *extras]
    assume(parts)
    rng.shuffle(parts)
    # An operator on each line, so that a comment cannot swallow the next part.
    formula_text = "\n+ ".join(parts)
    assert lsi.closes_its_strings(formula_text)
    lowered = lsi.lower_formula(formula_text, NOISY_SCOPE)
    assert lowered.reads == {(lsi.DERIVED, name) for name in names}


@semantic_properties
@given(st.text(alphabet=st.sampled_from(['"', "'", "\\", "#", "\n", " ", "a", "1", "+", "é"]), max_size=14))
def test_the_token_pattern_and_the_lexer_agree_on_a_string_left_open(formula_text):
    # Two readers of one lexer: TOKEN, behind open_string and the token reader,
    # and lex, the port of Lexer::tokenise. lex stops at its first error, so
    # each direction holds where it can see the string.
    try:
        lsi.lex(formula_text)
    except lsi.FormulaError as caught:
        error = str(caught)
    else:
        error = None
    left = lsi.open_string(formula_text)
    if error is None:
        assert left != "string"
    if error == "unterminated string":
        assert left == "string"
    if left == "string":
        assert error is not None


@semantic_properties
@given(st.integers(min_value=0, max_value=5), st.sampled_from(["5", "0.5", '"a"', "true"]))
def test_parentheses_never_change_what_is_a_literal(depth, literal):
    assert lsi.is_literal("(" * depth + literal + ")" * depth)
    assert not lsi.is_literal("(" * depth + "-" + literal + ")" * depth)


# Intervals over a short horizon, counted day by day. OPEN stands past it.
ORIGIN = date(2000, 1, 1)
HORIZON = 40
offsets = st.integers(min_value=0, max_value=HORIZON - 1)


def _interval(pair):
    start, length = pair
    return (
        ORIGIN + timedelta(days=start),
        OPEN if length is None else ORIGIN + timedelta(days=start + length),
    )


intervals = st.tuples(offsets, st.one_of(st.none(), st.integers(0, 12))).map(_interval)
interval_lists = st.lists(intervals, max_size=5)


def _days(runs) -> set[date]:
    last = ORIGIN + timedelta(days=HORIZON + 15)
    return {
        start + timedelta(days=offset)
        for start, end in runs
        for offset in range((min(end, last) - start).days + 1)
    }


def _canonical(runs) -> bool:
    return all(
        start <= end and (index == 0 or runs[index - 1][1] + timedelta(days=1) < start)
        for index, (start, end) in enumerate(runs)
    )


@semantic_properties
@given(interval_lists)
def test_merged_runs_hold_the_same_days_sorted_and_apart(runs):
    result = lsi.merged(runs)
    assert _days(result) == _days(runs) and _canonical(result)


@semantic_properties
@given(interval_lists, interval_lists)
def test_subtract_leaves_exactly_the_days_the_second_lacks(left, right):
    result = lsi.subtract(left, right)
    assert _days(result) == _days(left) - _days(right) and _canonical(result)


@semantic_properties
@given(st.dictionaries(offsets, st.one_of(st.none(), st.integers(0, 12)), min_size=1, max_size=4))
def test_windows_give_each_day_to_the_latest_started_version_that_applies(starts):
    versions = [
        lsi.Version(*(lambda span: (span[0], "", span[1]))(_interval(item)))
        for item in starts.items()
    ]
    picked = lsi.windows(versions)
    for day in sorted(_days([(version.start, version.end) for version in versions])):
        applying = [version for version in versions if version.start <= day <= version.end]
        owner = max(applying, key=lambda version: version.start)
        assert day in _days(picked[owner])
        assert not any(day in _days(runs) for version, runs in picked.items() if version != owner)


stop_maps = st.dictionaries(
    st.sampled_from([("us:a#r", "t"), ("us:a#r", "u"), ("us:a#s", "t")]),
    interval_lists.map(lsi.merged).filter(bool),
    max_size=3,
)


@semantic_properties
@given(stop_maps, stop_maps)
def test_widened_is_empty_iff_every_stop_date_is_the_bases(head, base):
    found = lsi.widened(head, base)
    assert (found == {}) == all(
        _days(runs) <= _days(base.get(key, ())) for key, runs in head.items()
    )
    for key, runs in found.items():
        assert _days(runs) == _days(head[key]) - _days(base.get(key, ()))


@semantic_properties
@given(stop_maps, stop_maps, stop_maps)
def test_widened_composes(head, middle, base):
    if lsi.widened(head, middle) == {} and lsi.widened(middle, base) == {}:
        assert lsi.widened(head, base) == {}
    assert lsi.widened(head, head) == {}


dates = st.dates(min_value=date(1, 1, 1), max_value=date(2100, 1, 1))
ids = st.builds(
    lambda jurisdiction, path, name: f"{jurisdiction}:statutes/{path}#{name}",
    st.sampled_from(["us", "us-co", "us-la"]),
    st.text(alphabet="abc012/-.:", min_size=1, max_size=10),
    st.text(alphabet="abc_012", min_size=1, max_size=10),
)
gap_dates = st.one_of(
    st.tuples(dates, dates).filter(lambda pair: pair[0] != pair[1]).map(sorted),
    dates.map(lambda start: [start, OPEN]),
)
edge_values = st.builds(
    lambda rule, target, pair: lsi.Edge(rule, target, pair[0], pair[1]), ids, ids, gap_dates
)
edge_sets = st.sets(edge_values, max_size=30)


@semantic_properties
@given(edge_sets)
def test_baseline_round_trip(entries):
    text = lsi.render_baseline(entries)
    assert lsi.parse_baseline(text) == entries
    assert lsi.render_baseline(lsi.parse_baseline(text)) == text
    body = [line for line in text.splitlines() if not line.startswith("#")]
    assert body == sorted(body)


@semantic_properties
@given(edge_sets, edge_sets, stop_maps)
def test_gate_passes_iff_equal_and_nothing_widened(edges, baseline, wider):
    verdict = lsi.compare(edges, baseline, wider)
    assert verdict.ok == (edges == baseline and not wider)
    assert verdict.new == edges - baseline and verdict.stale == baseline - edges


@semantic_properties
@given(edge_sets, edge_values)
def test_an_unlisted_edge_always_fails(baseline, extra):
    assume(extra not in baseline)
    verdict = lsi.compare(baseline | {extra}, baseline)
    assert not verdict.ok and verdict.new == {extra}


@semantic_properties
@given(edge_sets.filter(bool), st.data())
def test_a_listed_edge_that_no_longer_holds_always_fails(baseline, data):
    gone = data.draw(st.sampled_from(sorted(baseline)))
    verdict = lsi.compare(baseline - {gone}, baseline)
    assert not verdict.ok and verdict.stale == {gone}
