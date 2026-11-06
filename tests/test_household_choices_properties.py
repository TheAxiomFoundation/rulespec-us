"""Property-based and differential tests for tools/household_choices.py.

Invariants, each for every input Hypothesis draws:

1. `aggregate` is deterministic: the JSON and Markdown views are
   byte-identical across runs and whatever order the files are given in.
2. `aggregate` round-trips and carries every entry exactly once: with no id
   collisions, the view has one row per entry, in repository then file order,
   `files_from_view` rebuilds the files it read, and aggregating the rebuilt
   files gives the same view.
3. One id namespace: `id_collision_issues` reports exactly the global ids in
   both the register and the household-choices file, one issue each, and the
   same issues whichever file is passed in memory (both checks call it).
4. Vacuity: an optimum pin whose `chooses` is in the domain is reported as
   vacuous exactly when it is the default's option.
5. Differential: the check's notion of one option (`same_value`) agrees with
   the runner's (`pin_runner.same_option`) on every value a domain can hold
   (booleans, kebab-case options and decimal strings). They differ only off
   the domain: the runner also matches a YAML number to a decimal string and
   an enum option to the model's upper-case name, which test_pin_runner.py
   covers.
6. Scope: an objective scoped to the tax unit is accepted exactly when
   neither the actor nor the entity spans tax units.
7. Worklist: an optimizing implementation is listed as narrower exactly when
   `meets_standard` fails, and net income over the household always meets it.
8. Totality: `check_choices` returns a list of strings, and never raises, on
   any JSON-shaped payload.
"""

from __future__ import annotations

import array
import copy
import importlib.util
import itertools
import re
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, given, settings, strategies as st  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sc = _load("source_conflicts", TOOLS / "source_conflicts.py")
hc = _load("household_choices", TOOLS / "household_choices.py")
runner = _load("pin_runner", TOOLS / "pin_runner.py")
PROPERTY = settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])

# Kebab-case words; none reads as a decision-queue id, which hygiene refuses.
KEBAB = st.from_regex(r"[a-z][a-z0-9]{0,6}(-[a-z0-9]{1,4}){0,2}", fullmatch=True).filter(
    lambda word: not any(pattern.search(word) for pattern, _ in sc.HYGIENE_PATTERNS)
)
DECIMAL = st.from_regex(r"(0|[1-9][0-9]{0,3})(\.[0-9]{1,3})?", fullmatch=True)
# Every quoted lower-case word in household_choices.py: the field names
# `check` reads, among others. #1844 review round 2 (P2): six-character random
# keys never reached `jurisdiction` or `citation`.
FIELD_NAMES = sorted(set(re.findall(r'"([a-z][a-z_]{1,30})"', (TOOLS / "household_choices.py").read_text())))
JSONISH = st.recursive(
    st.none() | st.booleans() | st.integers(-5, 5) | st.floats(allow_nan=False, allow_infinity=False) | st.text(max_size=8),
    lambda children: st.lists(children, max_size=3)
    | st.dictionaries(st.sampled_from(FIELD_NAMES) | st.text(max_size=6), children, max_size=3),
    max_leaves=12,
)

COUNTRIES = {"TheAxiomFoundation/rulespec-us": "us", "TheAxiomFoundation/rulespec-uk": "uk", "TheAxiomFoundation/rulespec-ca": "ca"}


@st.composite
def choice_files(draw):
    """Files for up to three repositories, every global id unique, each
    entry's jurisdiction in its repository, the rest of each entry arbitrary."""

    files = {}
    used = set()
    for repo, country in COUNTRIES.items():
        if not draw(st.booleans()):
            continue
        entries = []
        for _ in range(draw(st.integers(0, 3))):
            jurisdiction = draw(st.sampled_from([country, f"{country}-x", f"{country}-yz"]))
            entry_id = draw(KEBAB)
            if f"{jurisdiction}:{entry_id}" in used:
                continue
            used.add(f"{jurisdiction}:{entry_id}")
            extra = draw(st.dictionaries(st.sampled_from(["question", "actor", "domain", "default", "implementations",
                                                          "multi_year", "axiom", "objective"]), JSONISH, max_size=4))
            entries.append({"id": entry_id, "jurisdiction": jurisdiction, **extra})
        payload = {"version": 1, "entries": entries}
        statutory = draw(st.lists(st.fixed_dictionaries({"jurisdiction": st.just(country), "citation": KEBAB, "note": st.text(max_size=8)}), max_size=2))
        if statutory:
            payload["statutory_not_choice"] = statutory
        files[repo] = payload
    return files


@PROPERTY
@given(choice_files(), st.randoms(use_true_random=False))
def test_aggregate_is_deterministic_in_any_order(files, rng):
    view, _ = hc.aggregate(files)
    order = list(files.items())
    rng.shuffle(order)
    again, _ = hc.aggregate(dict(order))
    assert hc.render_json(again) == hc.render_json(view) == hc.render_json(hc.aggregate(files)[0])
    assert hc.render_markdown(again) == hc.render_markdown(view)


@PROPERTY
@given(choice_files())
def test_aggregate_round_trips_and_carries_every_entry_once(files):
    view, issues = hc.aggregate(files)
    assert issues == []
    expected = [
        f"{entry['jurisdiction']}:{entry['id']}" for repo in sorted(files) for entry in files[repo]["entries"]
    ]
    assert [row["global_id"] for row in view["entries"]] == expected
    # #1844 review round 2 (P2): empty files round-trip too.
    rebuilt = hc.files_from_view(view)
    assert rebuilt == {repo: files[repo] for repo in sorted(files)}
    assert hc.aggregate(rebuilt)[0] == view
    # The view holds copies: changing any row never changes the files.
    before = copy.deepcopy(files)
    for row in view["entries"]:
        row["entry"]["id"] = "changed"
    for row in view["statutory_not_choice"]:
        row["item"]["note"] = "changed"
    for row in view["repositories"]:
        row["version"] = "changed"
    assert files == before


@st.composite
def two_files(draw):
    pairs = st.tuples(st.sampled_from(["us", "us-mt", "us-co"]), st.sampled_from(["a", "b", "c", "d-e"]))
    register = draw(st.lists(pairs, max_size=5))
    choices = draw(st.lists(pairs, max_size=5))
    as_payload = lambda items: {"version": 1, "entries": [{"jurisdiction": j, "id": i} for j, i in items]}  # noqa: E731
    return as_payload(register), as_payload(choices)


@PROPERTY
@given(two_files())
def test_id_collisions_are_exactly_the_shared_ids_from_either_side(files):
    conflicts, choices = files
    shared = {f"{e['jurisdiction']}:{e['id']}" for e in conflicts["entries"]} & {
        f"{e['jurisdiction']}:{e['id']}" for e in choices["entries"]
    }
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / sc.REGISTER_FILENAME).write_text(yaml.safe_dump(conflicts))
        (root / sc.CHOICES_FILENAME).write_text(yaml.safe_dump(choices))
        from_register = sc.id_collision_issues(root, conflicts=conflicts)
        from_choices = sc.id_collision_issues(root, choices=choices)
        from_disk = sc.id_collision_issues(root)
    assert from_register == from_choices == from_disk
    assert len(from_register) == len(shared)
    assert {issue.split("`")[1] for issue in from_register} == shared


DOMAINS = st.one_of(
    st.just({"kind": "boolean", "per": "tax-unit"}),
    st.lists(KEBAB, min_size=2, max_size=4, unique=True).map(lambda options: {"kind": "enum", "per": "person", "options": options}),
    st.just({"kind": "share", "per": "person", "bounds": ["0", "1"]}),
)


def domain_values(domain):
    if domain["kind"] == "boolean":
        return st.booleans()
    if domain["kind"] == "enum":
        return st.sampled_from(domain["options"])
    return st.sampled_from(["0", "0.5", "0.50", "0.500000001", "1", "1.0", "0.25"])


@st.composite
def optimum_cases(draw):
    domain = draw(DOMAINS)
    return domain, draw(domain_values(domain)), draw(domain_values(domain))


def _repo(directory: str) -> sc.RepoContext:
    root = Path(directory)
    (root / "us" / "statutes").mkdir(parents=True, exist_ok=True)
    return sc.RepoContext(root=root, repo="TheAxiomFoundation/rulespec-us")


def base_entry(domain, default, chooses):
    return {
        "id": "a-choice",
        "jurisdiction": "us",
        "program": "income-tax",
        "question": "Which option?",
        "actor": "taxpayer",
        "texts": [{"corpus_citation_path": "us/statute/26/1/a", "excerpt": "x"}],
        "domain": domain,
        "default": {"value": default, "basis": "convention", "note": "n"},
        "objective": {"measure": "net-income", "scope": "household"},
        "optimization": {"structure": "search", "candidates": "c"},
        "implementations": [{"repo": "PolicyEngine/policyengine-us", "commit": "a" * 40, "path": "x.py", "variable": "v",
                             "models": "candidate-min", "objective": {"measure": "net-income", "scope": "household"},
                             "cites_entry": False}],
        "tests": [{"repo": "PolicyEngine/policyengine-us", "commit": "a" * 40, "path": "tests/x.yaml", "name": "A case",
                   "pins": ["optimum"], "variable": "v", "chooses": chooses}],
    }


def _same_reference(a, b) -> bool:
    """One option, written independently of the tool: booleans only equal
    booleans; two decimal strings are the same number; anything else is the
    same string."""

    if type(a) is bool or type(b) is bool:
        return type(a) is type(b) and a is b
    number = re.compile(r"(0|[1-9][0-9]*)(\.[0-9]+)?")
    if isinstance(a, str) and isinstance(b, str) and number.fullmatch(a) and number.fullmatch(b):
        # The same number, or the same float32 a model would compute with.
        return Fraction(a) == Fraction(b) or array.array("f", [float(a)])[0] == array.array("f", [float(b)])[0]
    return isinstance(a, str) and isinstance(b, str) and a == b


@PROPERTY
@given(optimum_cases())
def test_an_optimum_pin_is_vacuous_exactly_when_it_is_the_default(case):
    domain, default, chooses = case
    with tempfile.TemporaryDirectory() as directory:
        issues = hc.check_choices({"version": 1, "entries": [base_entry(domain, default, chooses)]}, _repo(directory))
    vacuous = any("so the pin is vacuous" in issue for issue in issues)
    assert vacuous == _same_reference(chooses, default)
    assert [issue for issue in issues if "vacuous" not in issue] == []


DOMAIN_VALUES = st.one_of(
    st.booleans(), KEBAB, DECIMAL, st.sampled_from(["16777216", "16777217", "0.5", "0.500000001", "0.3"])
)


@PROPERTY
@given(DOMAIN_VALUES, DOMAIN_VALUES)
def test_check_and_runner_agree_on_what_one_option_is(a, b):
    assert hc.same_value(a, b) == runner.same_option(a, b)


@PROPERTY
@given(st.sampled_from(hc.ACTORS), st.sampled_from(hc.ENTITIES))
def test_tax_unit_scope_is_accepted_exactly_when_nothing_spans_tax_units(actor, per):
    value = base_entry({"kind": "boolean", "per": per}, False, True)
    value["actor"] = actor
    value["objective"] = {"measure": "total-tax", "scope": "tax-unit"}
    if actor in hc.AGENCY_ACTORS:
        del value["optimization"], value["implementations"], value["tests"]
    with tempfile.TemporaryDirectory() as directory:
        issues = hc.check_choices({"version": 1, "entries": [value]}, _repo(directory))
    refused = any("objective.scope must be household" in issue for issue in issues)
    # Written out here, not read from the tool: who and what can move more than one tax unit.
    spanning_actors = {"eligible-claimants", "household", "provider-household"}
    spanning_entities = {"family", "spm-unit", "household", "benefit-unit"}
    assert refused == (actor in spanning_actors or per in spanning_entities)
    assert [issue for issue in issues if "objective.scope" not in issue] == []


OBJECTIVES = st.fixed_dictionaries({"measure": st.sampled_from(hc.IMPLEMENTATION_MEASURES), "scope": st.sampled_from(hc.SCOPES)})
ENTRY_OBJECTIVES = st.fixed_dictionaries({"measure": st.sampled_from(hc.MEASURES), "scope": st.sampled_from(hc.SCOPES)})


@PROPERTY
@given(ENTRY_OBJECTIVES, OBJECTIVES, st.sampled_from(hc.OPTIMIZING))
def test_the_worklist_lists_a_narrower_objective_exactly_when_it_is_narrower(wanted, actual, models):
    value = base_entry({"kind": "boolean", "per": "tax-unit"}, False, True)
    value["objective"] = wanted
    value["implementations"][0].update(models=models, objective=actual)
    narrower = any("narrower than" in line for line in hc.worklist(value))
    assert narrower == (not hc.meets_standard(wanted, actual))
    assert hc.meets_standard(wanted, {"measure": "net-income", "scope": "household"})


@PROPERTY
@given(JSONISH)
def test_check_is_total(payload):
    with tempfile.TemporaryDirectory() as directory:
        ctx = _repo(directory)
        statutory = {"version": 1, "entries": [], "statutory_not_choice": payload}
        repeated = {"version": 1, "entries": [], "statutory_not_choice": [payload, copy.deepcopy(payload)]}
        for candidate in (payload, {"version": 1, "entries": [payload]}, statutory, repeated):
            issues = hc.check_choices(candidate, ctx)
            assert isinstance(issues, list) and all(isinstance(issue, str) for issue in issues)


def test_every_entry_field_shape_combination_is_total():
    # A deterministic sweep, so a crash on a rarely drawn field fails every run.
    shapes = ([], {}, None, 3, "", "x", True)
    with tempfile.TemporaryDirectory() as directory:
        ctx = _repo(directory)
        for key, shape in itertools.product(sorted(hc.ENTRY_KEYS), shapes):
            value = base_entry({"kind": "boolean", "per": "tax-unit"}, False, True)
            value[key] = shape
            issues = hc.check_choices({"version": 1, "entries": [value, copy.deepcopy(value)]}, ctx)
            assert isinstance(issues, list) and all(isinstance(issue, str) for issue in issues), (key, shape)
