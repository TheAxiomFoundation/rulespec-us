"""Property-based tests for the late-start import ratchet (tools/late_start_imports.py).

Invariants, for every input:

1. Run-time meaning: a (rule, target) pair is an edge iff some date reaches a
   gap. A reference simulation below follows the engine directly: it flattens
   imports, picks the version a date selects, and looks for a referenced rule
   with no version yet. The tool must agree with it exactly, in both
   directions, and record the first gap date as the edge's version start.
2. Scope: a `#fragment` never changes the result, a name outside the import
   closure is never a reference, and a name the module defines is never one.
3. Edges are a subset of the rule-level reading of "starts late": per-version
   comparison only removes pairs no date can reach.
4. Monotonicity: moving a target's start later never removes an edge, and
   moving a rule version's start earlier, past nothing, never removes one.
5. Determinism: the result does not depend on the order of modules, imports,
   rules or versions.
6. Lexing: words in strings and comments are never references, and the names
   of called functions are never references.
7. Baseline round trip: parse(render(S)) == S and render is canonical.
8. The gate passes iff the edges equal the baseline and, with a protected base,
   the baseline adds no (rule, target) pair unless the change is accepted. An
   unlisted edge, a listed edge that no longer holds and a moved date each fail
   it; the accepted label excuses only an added pair.

Hypothesis is not installed in the shared validate workflow's pytest leg, so
these skip there; the late-start-imports workflow installs it and runs them.
"""

from __future__ import annotations

import importlib.util
import random
import sys
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, assume, given, settings, target, strategies as st  # noqa: E402

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "late_start_imports.py"
_spec = importlib.util.spec_from_file_location("late_start_imports", TOOL_PATH)
lsi = importlib.util.module_from_spec(_spec)
sys.modules["late_start_imports"] = lsi
_spec.loader.exec_module(lsi)

semantic_properties = settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])

TARGETS = ("us:a", "us:b", "us:c", "us:d")
NAMES = ("p", "q", "r", "s")
STARTS = tuple(date(year, 1, 1) for year in (2000, 2010, 2020, 2030))

# A formula is generated from the names it reads, so the reference simulation
# never depends on the lexer it is checking. The sizes keep graphs dense: most
# draws hold an edge, so the properties below are not checked on empty cases.
reads = st.sets(st.sampled_from(NAMES), min_size=1, max_size=3)
versions = st.dictionaries(st.sampled_from(STARTS), reads, min_size=1, max_size=3)
rules = st.dictionaries(st.sampled_from(NAMES), versions, min_size=1, max_size=2)
imports = st.sets(st.sampled_from(TARGETS), min_size=1, max_size=3)
specs = st.fixed_dictionaries({owner: st.tuples(imports, rules) for owner in TARGETS})


def formula(names) -> str:
    return " + ".join(sorted(names)) or "0"


def build(spec) -> dict[str, "lsi.Module"]:
    return {
        target: lsi.Module(
            tuple(sorted(imported)),
            tuple(
                lsi.Rule(
                    name,
                    tuple(lsi.Version(start, formula(read)) for start, read in sorted(dated.items())),
                )
                for name, dated in sorted(defined.items())
            ),
        )
        for target, (imported, defined) in spec.items()
    }


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


def simulated_edges(spec) -> dict[tuple[str, str], date]:
    """Each (rule, target) a date stops on, with the first such date.

    On each date a rule answers from its latest started version (Derived::
    semantics_at), so only names that version reads are reached. The stop is
    a reached name with no version started yet, from another module.
    """
    days = sorted(set(STARTS) | {start + timedelta(days=1) for start in STARTS})
    stops: dict[tuple[str, str], date] = {}
    for origin, (_, defined) in spec.items():
        scope = closure(origin, spec)
        for name, dated in defined.items():
            for day in days:
                started = [start for start in dated if start <= day]
                if not started:
                    continue
                for read in dated[max(started)]:
                    if read in defined:
                        continue
                    owners = [
                        (min(spec[owner][1][read]), f"{owner}#{read}")
                        for owner in sorted(scope)
                        if read in spec[owner][1]
                    ]
                    if owners and min(owners)[0] > day:
                        key = (f"{origin}#{name}", min(owners)[1])
                        stops[key] = min(stops.get(key, day), day)
    return stops


def edges_of(modules):
    return lsi.late_start_edges(lsi.import_references(modules))


@settings(semantic_properties, max_examples=500)
@given(specs)
def test_an_edge_exists_iff_some_date_reaches_a_gap(spec):
    found = {(edge.rule, edge.target): edge.version_start for edge in edges_of(build(spec))}
    target(float(len(found)))
    assert found == simulated_edges(spec)


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
def test_references_stay_inside_the_import_closure_and_outside_the_module(spec):
    modules = build(spec)
    for reference in lsi.import_references(modules):
        origin, _ = reference.rule.split("#")
        owner, name = reference.target.split("#")
        assert owner in lsi.import_closure(origin, modules)
        assert name not in {rule.name for rule in modules[origin].rules}


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
    owner, name = edge.target.split("#")
    # A later start can change which module a shared name resolves to, which
    # is a different target, so hold the name to one definition.
    assume(sum(item.name == name for m in modules.values() for item in m.rules) == 1)
    rule = next(item for item in modules[owner].rules if item.name == name)
    later = lsi.Rule(
        rule.name,
        tuple(replace(version, start=version.start + timedelta(days=365)) for version in rule.versions),
    )
    moved = edges_of(_with_rule(modules, owner, name, later))
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
    earlier = lsi.Rule(
        rule.name,
        tuple(
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
                lsi.Rule(rule.name, tuple(shuffled(rule.versions)))
                for rule in shuffled(modules[target].rules)
            ),
        )
        for target in shuffled(modules)
    }
    assert lsi.import_references(reordered) == lsi.import_references(modules)


words = st.sampled_from(NAMES)
noise = st.one_of(
    words.map(lambda word: f'"{word}"'),
    words.map(lambda word: f"'{word}'"),
    words.map(lambda word: f"# {word}\n"),
    words.map(lambda word: f'"""{word} {word}"""'),
    words.map(lambda word: f"{word}(0)"),
    words.map(lambda word: f"{word}/{word}"),
)


@semantic_properties
@given(st.sets(words), st.lists(noise, max_size=4), st.randoms(use_true_random=False))
def test_strings_comments_calls_and_paths_are_never_references(names, extras, rng):
    parts = [*sorted(names), *extras]
    rng.shuffle(parts)
    # Each part ends its own line, so a comment cannot swallow the next one.
    assert lsi.formula_references("\n".join(parts)) == names


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
