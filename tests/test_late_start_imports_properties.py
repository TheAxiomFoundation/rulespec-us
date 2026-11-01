"""Property-based tests for the late-start import ratchet (tools/late_start_imports.py).

Invariants, for every input:

1. Run-time meaning: each (rule, target) a date stops on is an edge, with the
   first such date as its version start, and any other edge is a name the tool
   reads in both namespaces. A reference simulation below binds names the way
   lower_to_scalar does, by position, which the tool cannot: every generated
   formula reads in a scalar position, so a parameter wins. It flattens imports,
   sorts each rule into a namespace, picks the version a date selects, and
   looks for what that version binds with no version yet. Generated formulas
   take every branch, so "stops" and "can read the gap" agree here; the tool
   makes no claim about a branch a date never takes. The specs hold only what
   the engine loads: no import cycle, and one derived rule per name per program.
2. Scope: a `#fragment` never changes the result, a name outside the import
   closure is never a reference, and a binding that nothing imported feeds is
   never one.
3. Edges are a subset of the rule-level reading of "starts late": per-version
   comparison only removes pairs no date can reach.
4. Monotonicity: moving a target's start later never removes an edge, and
   moving a rule version's start earlier, past nothing, never removes one.
5. Determinism: the result does not depend on the order of modules, imports,
   rules or versions, and reduction to edges does not depend on the order of
   references.
6. Lexing: words in strings and comments are never references, and the names
   of called functions are never references, however they are parenthesized.
7. Baseline round trip: parse(render(S)) == S and render is canonical.
8. The gate passes iff the edges equal the baseline and, with a protected base,
   the baseline adds no (rule, target) pair unless the change is accepted. An
   unlisted edge, a listed edge that no longer holds and a moved date each fail
   it; the accepted label excuses only an added pair.

Hypothesis is not installed in the shared validate workflow's pytest leg, so
these skip there; the late-start-imports workflow installs it and runs them.

`test_the_pinned_engine_binds_what_the_tool_reads` needs no simulation: the
engine-differential job points LATE_START_HARNESS at the compiled harness, and
the engine lowers these same generated programs. The simulation states what a
run does with those bindings; the engine vouches for the bindings themselves.
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

TARGETS = ("us:statutes/a", "us:statutes/b", "us:statutes/c", "us:statutes/d")
NAMES = ("p", "q", "r", "s")
STARTS = tuple(date(year, 1, 1) for year in (2000, 2010, 2020, 2030))

# A formula is generated from the names it reads, so the reference simulation
# never depends on the lexer it is checking. The sizes keep graphs dense: about
# a third of draws hold an edge, so the properties below see real cases. A rule
# never reads its own name, which the engine refuses.
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
READING = ("derived", "computed")
LITERAL = ("scalar", "flagless")
TABLE = ("valued", "stale")
DERIVED_SHAPES = (*READING, "constant")
reads = st.sets(st.sampled_from(NAMES), min_size=1, max_size=3)
dated_reads = st.dictionaries(st.sampled_from(STARTS), reads, min_size=1, max_size=3)
dated_values = st.sets(st.sampled_from(STARTS), min_size=1, max_size=2)
reading_rule = st.tuples(st.sampled_from(READING), dated_reads)
value_rule = st.tuples(st.sampled_from(("constant", *LITERAL, *TABLE)), dated_values)
rule_shapes = st.one_of(reading_rule, reading_rule, value_rule)
rules = st.dictionaries(st.sampled_from(NAMES), rule_shapes, min_size=1, max_size=2)


def imports_for(index: int):
    """Only later modules, so no graph holds a cycle, which the engine refuses."""
    later = TARGETS[index + 1 :]
    return st.sets(st.sampled_from(later), min_size=1, max_size=3) if later else st.just(set())


def loadable(spec):
    """What the engine refuses goes: a second derived rule of a name in one
    flattened program becomes a scalar, and so does a reading rule left in a
    derived cycle, which `reads_from` finds."""
    spec = {owner: (imported, dict(defined)) for owner, (imported, defined) in spec.items()}
    for root in TARGETS:
        kept: dict[str, str] = {}
        for owner in sorted(closure(root, spec) | {root}):
            for name, (shape, body) in spec[owner][1].items():
                if shape in DERIVED_SHAPES and kept.setdefault(name, owner) != owner:
                    spec[owner][1][name] = ("scalar", set(body))
        while cycle := derived_cycle(root, spec):
            owner, name = cycle
            spec[owner][1][name] = ("scalar", set(spec[owner][1][name][1]))
    return spec


def derived_cycle(root, spec) -> tuple[str, str] | None:
    """A (module, name) on a derived dependency cycle in this root's program."""
    scope = closure(root, spec) | {root}
    # In a scalar position a parameter wins, so only a derived binding follows.
    follows = {}
    for owner in sorted(scope):
        for name, (shape, body) in spec[owner][1].items():
            if shape in READING:
                follows[name] = (owner, {read for reads in body.values() for read in reads})

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
    {owner: st.tuples(imports_for(index), rules) for index, owner in enumerate(TARGETS)}
).map(loadable)


def formula(names, own) -> str:
    return " + ".join(sorted(set(names) - {own})) or "1 + 1"


def rule_yaml(name, shape, body) -> dict:
    kind = "derived" if shape in ("derived", "flagless") else "parameter"
    rule = {"name": name, "kind": kind}
    if shape in ("derived", "constant"):
        rule.update(entity="Person", dtype="Integer", period="Month")
    if shape in READING:
        rule["versions"] = [
            {"from": start.isoformat(), "formula": formula(read, name)}
            for start, read in sorted(body.items())
        ]
    elif shape in ("constant", *LITERAL):
        rule["versions"] = [{"from": start.isoformat(), "formula": "1"} for start in sorted(body)]
    else:
        rule["indexed_by"] = "size"
        rule["versions"] = [
            {"from": start.isoformat(), "values": {0: 1}} for start in sorted(body)
        ]
        if shape == "stale":
            rule["versions"].insert(0, {"from": "1990-01-01", "formula": "p + q"})
    return rule


def module_text(imported, defined) -> str:
    return yaml.safe_dump(
        {
            "format": "rulespec/v1",
            "module": {},
            "imports": sorted(imported),
            "rules": [rule_yaml(name, *defined[name]) for name in sorted(defined)],
        }
    )


def build(spec) -> dict[str, "lsi.Module"]:
    """Through the YAML parser, so these properties cover the sorting into namespaces."""
    return {target: lsi.parse_module(module_text(*body)) for target, body in spec.items()}


def closure(target, spec) -> set[str]:
    """The engine's flattening: each imported module and everything it imports."""
    seen: set[str] = set()

    def visit(current):
        for imported in spec[current][0]:
            if imported not in seen:
                seen.add(imported)
                visit(imported)

    visit(target)
    seen.discard(target)
    return seen


def definitions(name, scope, spec) -> list[tuple[str, str, object]]:
    return [
        (owner, *spec[owner][1][name]) for owner in sorted(scope) if name in spec[owner][1]
    ]


def scalar_group(name, scope, spec, tables_only=False) -> list[tuple[str, date]]:
    """What lower_to_scalar binds a name to: a parameter if any exists, so a table
    or else the merged scalars, and only then a derived rule. Each entry is
    (module, version start), for the versions that survive lowering."""
    found = definitions(name, scope, spec)
    tables = [(owner, body) for owner, shape, body in found if shape in TABLE]
    literals = [(owner, body) for owner, shape, body in found if shape in LITERAL]
    derived = [(owner, body) for owner, shape, body in found if shape in DERIVED_SHAPES]
    chosen = tables or literals or ([] if tables_only else derived)
    return [(owner, start) for owner, body in chosen for start in body]


def in_both_namespaces(name, scope, spec) -> bool:
    shapes = {shape for _, shape, _ in definitions(name, scope, spec)}
    return bool(shapes & {*TABLE, *LITERAL}) and bool(shapes & set(DERIVED_SHAPES))


def simulated_edges(spec) -> dict[tuple[str, str], date]:
    """Each (rule, target) a date stops on, with the first such date.

    On each date a rule answers from its latest started version (Derived::
    semantics_at), so only names that version reads are reached. The stop is a
    reached name bound to nothing started yet, when an imported module feeds it.
    """
    days = sorted(set(STARTS) | {start + timedelta(days=1) for start in STARTS})
    stops: dict[tuple[str, str], date] = {}
    for origin, (_, defined) in spec.items():
        scope = closure(origin, spec) | {origin}
        for name, (shape, dated) in defined.items():
            if shape not in READING:
                continue
            for day in days:
                started = [start for start in dated if start <= day]
                if not started:
                    continue
                for read in dated[max(started)]:
                    if read == name:
                        continue
                    group = scalar_group(read, scope, spec)
                    imported = [(start, owner) for owner, start in group if owner != origin]
                    if imported and min(start for _, start in group) > day:
                        key = (f"{origin}#{name}", f"{min(imported)[1]}#{read}")
                        stops[key] = min(stops.get(key, day), day)
    return stops


def edges_of(modules):
    return lsi.late_start_edges(lsi.import_references(modules))


def test_the_generators_reach_tables_and_collisions_and_stay_loadable():
    """The hard shapes must occur often enough to test, and no program the engine
    refuses may."""

    def shapes(spec):
        return {shape for _, defined in spec.values() for shape, _ in defined.values()}

    def collides(spec):
        return any(
            in_both_namespaces(name, closure(owner, spec) | {owner}, spec)
            for owner in spec
            for name in NAMES
        )

    for reached in (
        lambda spec: "stale" in shapes(spec) and bool(simulated_edges(spec)),
        collides,
        lambda spec: any(spec[owner][0] for owner in TARGETS[:-1]),
    ):
        spec = find(specs, reached, settings=settings(deadline=None, database=None))
        for owner, (imported, _) in spec.items():
            assert all(TARGETS.index(item) > TARGETS.index(owner) for item in imported)
        for root in TARGETS:
            scope = closure(root, spec) | {root}
            for name in NAMES:
                derived = [
                    owner
                    for owner, shape, _ in definitions(name, scope, spec)
                    if shape in DERIVED_SHAPES
                ]
                assert len(derived) <= 1


@settings(semantic_properties, max_examples=500)
@given(specs)
def test_each_stop_is_an_edge_and_each_other_edge_is_a_name_read_both_ways(spec):
    found = {(edge.rule, edge.target): edge.version_start for edge in edges_of(build(spec))}
    stops = simulated_edges(spec)
    target(float(len(found)))
    assert stops.items() <= found.items()
    for rule, reached in found.keys() - stops.keys():
        origin = rule.split("#")[0]
        name = reached.split("#")[1]
        assert in_both_namespaces(name, closure(origin, spec) | {origin}, spec)


@pytest.mark.skipif(not HARNESS, reason="the engine-differential job builds the harness")
@settings(semantic_properties, max_examples=150)
@given(specs)
def test_the_pinned_engine_binds_what_the_tool_reads(spec):
    with tempfile.TemporaryDirectory(prefix="late-start-generated-") as scratch:
        root = Path(scratch) / "tree"
        paths = []
        for module, body in spec.items():
            relative = lsi.module_path(f"{module}#x")
            paths.append(relative)
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(module_text(*body), encoding="utf-8")
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


@semantic_properties
@given(specs, st.sampled_from(NAMES))
def test_a_fragment_never_changes_the_result(spec, fragment):
    modules = build(spec)
    fragmented = {
        target: replace(
            module, imports=tuple(f"{specifier}#{fragment}" for specifier in module.imports)
        )
        for target, module in modules.items()
    }
    assert lsi.import_references(fragmented) == lsi.import_references(modules)


@semantic_properties
@given(specs)
def test_a_crossing_reference_names_a_definition_inside_the_import_closure(spec):
    modules = build(spec)
    for reference in lsi.import_references(modules):
        origin, _ = reference.rule.split("#")
        owner, name = reference.target.split("#")
        assert owner in lsi.import_closure(origin, modules)
        assert owner != origin
        assert any(rule.name == name for rule in modules[owner].rules)


@semantic_properties
@given(specs)
def test_edges_are_a_subset_of_the_rule_level_reading(spec):
    modules = build(spec)
    starts = {
        f"{origin}#{rule.name}": rule.start
        for origin, module in modules.items()
        for rule in module.rules
    }
    rule_level = {
        (item.rule, item.target)
        for item in lsi.import_references(modules)
        if starts[item.rule] < item.target_start
    }
    assert {(edge.rule, edge.target) for edge in edges_of(modules)} <= rule_level


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
        for owner, (_, defined) in spec.items()
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


def _with_rule(modules, origin, name, rule):
    module = modules[origin]
    return {
        **modules,
        origin: replace(
            module,
            rules=tuple(rule if item.name == name else item for item in module.rules),
        ),
    }


@semantic_properties
@given(specs, st.data())
def test_moving_a_target_later_never_removes_an_edge(spec, data):
    modules = build(spec)
    edges = edges_of(modules)
    assume(edges)
    edge = data.draw(st.sampled_from(sorted(edges)))
    _, name = edge.target.split("#")

    # Every definition moves, so a shared name still resolves to the same target.
    def later(rule):
        return replace(
            rule,
            versions=tuple(
                replace(version, start=version.start + timedelta(days=365))
                for version in rule.versions
            ),
        )

    moved = edges_of(
        {
            owner: replace(
                module,
                rules=tuple(later(rule) if rule.name == name else rule for rule in module.rules),
            )
            for owner, module in modules.items()
        }
    )
    assert (edge.rule, edge.target) in {(item.rule, item.target) for item in moved}


@semantic_properties
@given(specs, st.data())
def test_moving_a_late_version_earlier_never_removes_its_edge(spec, data):
    modules = build(spec)
    edges = edges_of(modules)
    assume(edges)
    edge = data.draw(st.sampled_from(sorted(edges)))
    origin, name = edge.rule.split("#")
    rule = next(item for item in modules[origin].rules if item.name == name)
    earlier = replace(
        rule,
        versions=tuple(
            replace(version, start=version.start - timedelta(days=365))
            if version.start == edge.version_start
            else version
            for version in rule.versions
        ),
    )
    moved = edges_of(_with_rule(modules, origin, name, earlier))
    assert (edge.rule, edge.target) in {(item.rule, item.target) for item in moved}


@semantic_properties
@given(specs, st.randoms(use_true_random=False))
def test_the_result_does_not_depend_on_declaration_order(spec, rng: random.Random):
    def shuffled(items):
        items = list(items)
        rng.shuffle(items)
        return items

    modules = build(spec)
    reordered = {
        target: lsi.Module(
            tuple(shuffled(modules[target].imports)),
            tuple(
                replace(rule, versions=tuple(shuffled(rule.versions)))
                for rule in shuffled(modules[target].rules)
            ),
        )
        for target in shuffled(modules)
    }
    assert lsi.import_references(reordered) == lsi.import_references(modules)
    references = sorted(lsi.import_references(modules))
    assert lsi.late_start_edges(shuffled(references)) == lsi.late_start_edges(references)


words = st.sampled_from(NAMES)
noise = st.one_of(
    words.map(lambda word: f'"{word}"'),
    words.map(lambda word: f"'{word}'"),
    words.map(lambda word: f"# {word}\n"),
    words.map(lambda word: f'"""{word} {word}"""'),
    words.map(lambda word: f"{word}(0)"),
    words.map(lambda word: f"{word} # note\n(0)"),
    words.map(lambda word: f"({word})(0)"),
    words.map(lambda word: f"(({word}))\n(0)"),
)


@semantic_properties
@given(st.sets(words), st.lists(noise, max_size=4), st.randoms(use_true_random=False))
def test_strings_comments_and_calls_are_never_references(names, extras, rng):
    parts = [*sorted(names), *extras]
    rng.shuffle(parts)
    # An operator on each line, so that a name is never a callee by accident and
    # a comment cannot swallow the next part.
    assert lsi.formula_references("\n+ ".join(parts)) == names


@semantic_properties
@given(st.integers(min_value=0, max_value=5), st.sampled_from(["5", "0.5", '"a"', "true"]))
def test_parentheses_never_change_what_is_a_literal(depth, literal):
    assert lsi.is_literal("(" * depth + literal + ")" * depth)
    assert not lsi.is_literal("(" * depth + "-" + literal + ")" * depth)


dates = st.dates(min_value=date(1, 1, 1), max_value=date(2100, 1, 1))
ids = st.builds(
    lambda jurisdiction, path, name: f"{jurisdiction}:statutes/{path}#{name}",
    st.sampled_from(["us", "us-co", "us-la"]),
    st.text(alphabet="abc012/-.:", min_size=1, max_size=10),
    st.text(alphabet="abc_012", min_size=1, max_size=10),
)
late_pairs = st.tuples(dates, dates).filter(lambda pair: pair[0] != pair[1]).map(sorted)
edge_values = st.builds(
    lambda rule, target, pair: lsi.Edge(rule, target, pair[0], pair[1]), ids, ids, late_pairs
)
edge_sets = st.sets(edge_values, max_size=30)


def _keys(entries):
    return {(entry.rule, entry.target) for entry in entries}


@semantic_properties
@given(edge_sets)
def test_baseline_round_trip(entries):
    text = lsi.render_baseline(entries)
    assert lsi.parse_baseline(text) == entries
    assert lsi.render_baseline(lsi.parse_baseline(text)) == text
    body = [line for line in text.splitlines() if not line.startswith("#")]
    assert body == sorted(body)


@semantic_properties
@given(edge_sets, edge_sets, st.one_of(st.none(), edge_sets), st.booleans())
def test_gate_passes_iff_equal_and_shrinking(edges, baseline, base, allow_added):
    verdict = lsi.compare(edges, baseline, base, allow_added)
    expected = edges == baseline and (
        base is None or allow_added or _keys(baseline) <= _keys(base)
    )
    assert verdict.ok == expected


@semantic_properties
@given(edge_sets, edge_values, st.booleans())
def test_an_unlisted_edge_always_fails_even_when_accepted(baseline, extra, allow_added):
    assume(extra not in baseline)
    verdict = lsi.compare(baseline | {extra}, baseline, baseline, allow_added)
    assert not verdict.ok and verdict.new == {extra}


@semantic_properties
@given(edge_sets.filter(bool), st.data(), st.booleans())
def test_a_listed_edge_that_no_longer_holds_always_fails_even_when_accepted(baseline, data, allow_added):
    gone = data.draw(st.sampled_from(sorted(baseline)))
    verdict = lsi.compare(baseline - {gone}, baseline, baseline, allow_added)
    assert not verdict.ok and verdict.stale == {gone}


@semantic_properties
@given(edge_sets, edge_values)
def test_a_regenerated_new_pair_fails_until_accepted(base, extra):
    assume((extra.rule, extra.target) not in _keys(base))
    grown = base | {extra}
    verdict = lsi.compare(grown, grown, base)
    assert not verdict.ok and verdict.added == {extra}
    assert lsi.compare(grown, grown, base, allow_added=True).ok


@semantic_properties
@given(edge_sets.filter(bool), st.data())
def test_a_listed_pair_may_change_dates_when_regenerated(base, data):
    entry = data.draw(st.sampled_from(sorted(base)))
    current = (base - {entry}) | {replace(entry, target_start=entry.target_start + timedelta(days=1))}
    assert lsi.compare(current, current, base).ok
