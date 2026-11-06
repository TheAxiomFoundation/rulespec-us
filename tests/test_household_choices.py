"""Tests for tools/household_choices.py and the committed household-choices file.

These run in the Repository Checks pytest leg, offline. The committed
household-choices.yaml must pass `check` exactly. The rest pin each rule on
small fixture repositories: the schema, the domain and default rules, the
modeling-state rules, the links (axiom.input, source_conflict, coupling), the
id namespace shared with the source-conflict register, hygiene and money,
`verify` against a fake network, the worklist, and `aggregate`. Property-based
and differential tests live in test_household_choices_properties.py.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest
import yaml

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
REPO = "TheAxiomFoundation/rulespec-us"
PE = "PolicyEngine/policyengine-us"
COMMIT = "a" * 40
SLOT = "parents_of_individual_may_claim_individual_but_no_parent_claims"


# ---------------------------------------------------------------------------
# The committed file


def test_committed_file_passes_check() -> None:
    payload = sc.load_register(REPO_ROOT / hc.CHOICES_FILENAME)
    assert hc.check_choices(payload, sc.RepoContext(root=REPO_ROOT, repo=REPO)) == []


def test_committed_file_cli_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert hc.main(["check", "--root", str(REPO_ROOT)]) == 0
    assert "0 issue(s)" in capsys.readouterr().out


def test_committed_file_carries_the_cross_tax_unit_case() -> None:
    # Eng hub ruling 5: a choice spanning tax units (who claims a qualifying
    # child, IRC 152(c)(4)) is the schema case for actor, per and scope.
    payload = sc.load_register(REPO_ROOT / hc.CHOICES_FILENAME)
    entry = next(item for item in payload["entries"] if item["id"] == "qualifying-child-claim-by-non-parent")
    assert entry["actor"] == "eligible-claimants" and entry["domain"]["per"] == "person"
    assert entry["objective"]["scope"] == "household"


# ---------------------------------------------------------------------------
# Fixtures


MODULE = {
    "format": "rulespec/v1",
    "module": {"summary": "x"},
    "imports": ["us:statutes/26/443/a/1#imported_fact"],
    "rules": [
        {
            "name": "tiebreaker",
            "kind": "derived",
            "versions": [{"effective_from": "1990-01-01", "formula": f"not {SLOT} and imported_fact or other_input"}],
        }
    ],
}


def make_repo(tmp_path: Path, *, register: dict | None = None) -> sc.RepoContext:
    (tmp_path / "us" / "statutes" / "26" / "152").mkdir(parents=True, exist_ok=True)
    (tmp_path / "us-mt" / "statutes").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "us" / "statutes" / "26" / "152" / "c.yaml").write_text(yaml.safe_dump(MODULE, sort_keys=False))
    if register is not None:
        (tmp_path / sc.REGISTER_FILENAME).write_text(yaml.safe_dump(register, sort_keys=False))
    return sc.RepoContext(root=tmp_path, repo=REPO)


def entry(**overrides):
    base = {
        "id": "itemized-deduction-election",
        "jurisdiction": "us",
        "program": "income-tax",
        "question": "Does the taxpayer elect to itemize deductions?",
        "actor": "taxpayer",
        "texts": [{"corpus_citation_path": "us/statute/26/63/e/1", "excerpt": "Unless an individual makes an election"}],
        "domain": {"kind": "boolean", "per": "tax-unit"},
        "default": {"value": False, "basis": "statute", "note": "No election, no itemized deduction."},
        "objective": {"measure": "net-income", "scope": "household"},
        "optimization": {"structure": "two-way"},
        "implementations": [
            {
                "repo": PE,
                "commit": COMMIT,
                "path": "policyengine_us/variables/tax_unit_itemizes.py",
                "variable": "tax_unit_itemizes",
                "models": "optimized",
                "objective": {"measure": "federal-income-tax", "scope": "tax-unit"},
                "cites_entry": False,
            }
        ],
        "tests": [
            {
                "repo": PE,
                "commit": COMMIT,
                "path": "policyengine_us/tests/policy/itemizes.yaml",
                "name": "A case that itemizes",
                "pins": ["optimum"],
                "variable": "tax_unit_itemizes",
                "chooses": True,
            }
        ],
    }
    base.update(overrides)
    return base


def child_entry(**overrides):
    base = {
        "id": "qualifying-child-claim-by-non-parent",
        "jurisdiction": "us",
        "program": "income-tax",
        "question": "Does no parent claim the child?",
        "actor": "eligible-claimants",
        "texts": [{"corpus_citation_path": "us/statute/26/152/c/4", "excerpt": "no parent so claims the individual"}],
        "domain": {"kind": "boolean", "per": "person"},
        "default": {"value": False, "basis": "statute"},
        "objective": {"measure": "net-income", "scope": "household"},
        "optimization": {"structure": "two-way"},
        "axiom": {"input": f"us:statutes/26/152/c#input.{SLOT}"},
    }
    base.update(overrides)
    return base


def payload(*entries, statutory=None):
    value = {"version": 1, "entries": list(entries)}
    if statutory is not None:
        value["statutory_not_choice"] = statutory
    return value


def check(ctx, *entries, statutory=None):
    return hc.check_choices(payload(*entries, statutory=statutory), ctx)


def has(issues, fragment):
    return any(fragment in issue for issue in issues)


# ---------------------------------------------------------------------------
# Top level and identity


def test_valid_entries_have_no_issues(tmp_path):
    ctx = make_repo(tmp_path)
    assert check(ctx, entry(), child_entry()) == []


def test_top_level_shape(tmp_path):
    ctx = make_repo(tmp_path)
    assert hc.check_choices([], ctx) == [f"{hc.CHOICES_FILENAME} must be a mapping with `version` and `entries`."]
    issues = hc.check_choices({"version": 2, "entries": {}, "extra": 1}, ctx)
    assert has(issues, "unknown top-level key `extra`")
    assert has(issues, "version must be 1")
    assert has(issues, "entries must be a list")


def test_required_fields_and_identity(tmp_path):
    ctx = make_repo(tmp_path)
    issues = check(ctx, {"id": "Bad_Id"})
    for key in ("jurisdiction", "program", "question", "actor", "domain", "default", "objective"):
        assert has(issues, f".{key} is required"), key
    assert has(issues, "id must match")
    issues = check(ctx, entry(jurisdiction="us-zz", program="Income Tax", actor="spouse"))
    assert has(issues, "jurisdiction must be a jurisdiction directory")
    assert has(issues, "program must be kebab-case")
    assert has(issues, "actor must be one of")


def test_duplicate_global_ids(tmp_path):
    issues = check(make_repo(tmp_path), entry(), entry())
    assert has(issues, "`us:itemized-deduction-election` duplicates entries[0]")


def test_an_entry_cites_the_provision_that_grants_the_choice(tmp_path):
    issues = check(make_repo(tmp_path), entry(texts=[]))
    assert has(issues, "must cite the provision that grants the choice")


def test_texts_and_pending_texts_are_checked_as_the_register_checks_them(tmp_path):
    ctx = make_repo(tmp_path)
    issues = check(ctx, entry(texts=[{"corpus_citation_path": "not a path", "excerpt": ""}]))
    assert has(issues, "is not a canonical corpus citation path")
    assert has(issues, "excerpt must be a non-blank string")
    pending = [{"citation": "Form 2", "kind": "letter", "url": "http://x", "excerpt": "e", "snapshot": {}}]
    issues = check(ctx, entry(pending_texts=pending))
    assert has(issues, "pending_texts[0].kind must be one of")
    assert has(issues, "pending_texts[0].url must be an https URL")
    assert has(issues, "pending_texts[0].snapshot.repo is required")


def test_unknown_keys_rejected_at_every_level(tmp_path):
    ctx = make_repo(tmp_path)
    value = entry(extra=1)
    value["domain"]["extra"] = 1
    value["default"]["extra"] = 1
    value["objective"]["extra"] = 1
    value["optimization"]["extra"] = 1
    value["implementations"][0]["follows"] = "reading"
    value["tests"][0]["extra"] = 1
    issues = check(ctx, value)
    for where in ("", ".domain", ".default", ".objective", ".optimization", ".implementations[0]", ".tests[0]"):
        assert any(f"{where} has unknown key" in issue for issue in issues), where


# ---------------------------------------------------------------------------
# Domain and default


@pytest.mark.parametrize(
    ("domain", "fragment"),
    [
        ({"kind": "set", "per": "person"}, "kind must be one of"),
        ({"kind": "boolean", "per": "dependent"}, "per must be one of"),
        ({"kind": "enum", "per": "person", "options": ["a"]}, "at least two options"),
        ({"kind": "enum", "per": "person", "options": ["a", "a"]}, "repeats an option"),
        ({"kind": "enum", "per": "person", "options": ["A", "b"]}, "kebab-case"),
        ({"kind": "boolean", "per": "person", "options": ["a", "b"]}, "options is only for an enum"),
        ({"kind": "share", "per": "person", "bounds": ["0", "2"]}, "lie within 0 and 1"),
        ({"kind": "share", "per": "person", "bounds": ["1", "0"]}, "low bound below the high bound"),
        ({"kind": "share", "per": "person", "bounds": [0, 1]}, "two non-negative decimal strings"),
        ({"kind": "amount", "per": "person", "bounds": ["0", "100"]}, "currency must be an ISO 4217 code"),
        ({"kind": "boolean", "per": "person", "bounds": ["0", "1"]}, "bounds is only for a share or an amount"),
        ({"kind": "boolean", "per": "person", "currency": "USD"}, "currency is only for an amount"),
    ],
)
def test_domain_rules(tmp_path, domain, fragment):
    issues = check(make_repo(tmp_path), entry(domain=domain, optimization={"structure": "search"}, implementations=[], tests=[]))
    assert has(issues, fragment), issues


@pytest.mark.parametrize(
    ("domain", "value", "ok"),
    [
        ({"kind": "boolean", "per": "person"}, True, True),
        ({"kind": "boolean", "per": "person"}, "true", False),
        ({"kind": "enum", "per": "person", "options": ["joint", "separate"]}, "joint", True),
        ({"kind": "enum", "per": "person", "options": ["joint", "separate"]}, "single", False),
        ({"kind": "share", "per": "person", "bounds": ["0", "1"]}, "0.5", True),
        ({"kind": "share", "per": "person", "bounds": ["0", "1"]}, 0.5, False),  # quoted decimal strings only
        ({"kind": "share", "per": "person", "bounds": ["0", "1"]}, "1.5", False),
        ({"kind": "amount", "per": "person", "bounds": ["0", "5000"], "currency": "USD"}, "5000", True),
    ],
)
def test_default_value_lies_in_the_domain(tmp_path, domain, value, ok):
    value_entry = entry(
        domain=domain, default={"value": value, "basis": "convention", "note": "n"},
        optimization={"structure": "search"}, implementations=[], tests=[],
    )
    issues = check(make_repo(tmp_path), value_entry)
    assert has(issues, "default.value is not one of the domain's options") != ok, issues


def test_default_basis(tmp_path):
    ctx = make_repo(tmp_path)
    assert has(check(ctx, entry(default={"value": False, "basis": "custom"})), "default.basis must be one of")
    assert has(check(ctx, entry(default={"value": False, "basis": "convention"})), "default.note is required for a convention")
    assert has(check(ctx, entry(default={"value": False})), "default.basis must be one of")
    assert has(check(ctx, entry(default={"basis": "statute"})), "default.value is required")
    # A statutory default cites a statute; a regulation's, a regulation.
    form = [{"corpus_citation_path": "us/form/irs/1040/instructions", "excerpt": "e"}]
    assert has(check(ctx, entry(texts=form)), "must cite a text of kind statute")
    assert has(check(ctx, entry(default={"value": False, "basis": "regulation"})), "must cite a text of kind regulation")
    assert not has(
        check(ctx, entry(texts=form, default={"value": False, "basis": "agency"})), "must cite a text of kind"
    )
    pending = [{"citation": "ARM 42.15.524", "kind": "regulation", "url": "https://x.example",
                "excerpt": "e", "snapshot": {"repo": PE, "commit": COMMIT, "path": "s.html", "sha256": "b" * 64}}]
    assert not has(
        check(ctx, entry(pending_texts=pending, default={"value": False, "basis": "regulation"})), "must cite a text of kind"
    )


# ---------------------------------------------------------------------------
# Objective, scope, multi-year


def test_objective_shape(tmp_path):
    ctx = make_repo(tmp_path)
    issues = check(ctx, entry(objective={"measure": "federal-income-tax", "scope": "family"}))
    assert has(issues, "objective.measure must be one of net-income, total-tax")
    assert has(issues, "objective.scope must be one of")
    assert check(ctx, entry(objective={"measure": "total-tax", "scope": "tax-unit"})) == []


@pytest.mark.parametrize(
    ("actor", "per", "ok"),
    [
        ("taxpayer", "tax-unit", True),
        ("spouses-jointly", "person", True),
        ("eligible-claimants", "person", False),  # who claims a child: spans tax units
        ("household", "household", False),
        ("taxpayer", "spm-unit", False),
        ("provider-household", "person", False),
    ],
)
def test_a_choice_spanning_tax_units_takes_the_household_as_its_scope(tmp_path, actor, per, ok):
    value = child_entry(actor=actor, domain={"kind": "boolean", "per": per},
                        objective={"measure": "net-income", "scope": "tax-unit"})
    assert has(check(make_repo(tmp_path), value), "objective.scope must be household") != ok


def test_multi_year_is_a_flag(tmp_path):
    ctx = make_repo(tmp_path)
    assert check(ctx, entry(multi_year=True)) == []
    assert has(check(ctx, entry(multi_year=False)), "multi_year must be true when present")


# ---------------------------------------------------------------------------
# Optimization and modeling states


@pytest.mark.parametrize(
    ("domain", "structure", "fragment"),
    [
        ({"kind": "enum", "per": "person", "options": ["a", "b", "c"]}, "two-way", "two-way needs a boolean or a two-option enum"),
        ({"kind": "share", "per": "person", "bounds": ["0", "1"]}, "finite", "finite needs a boolean or an enum"),
        ({"kind": "boolean", "per": "person"}, "piecewise-linear", "piecewise-linear needs a share or an amount"),
        ({"kind": "boolean", "per": "person"}, "gradient", "structure must be one of"),
    ],
)
def test_structure_fits_the_domain(tmp_path, domain, structure, fragment):
    value = entry(domain=domain, optimization={"structure": structure},
                  default={"value": "a" if domain["kind"] == "enum" else ("0" if domain["kind"] == "share" else False),
                           "basis": "convention", "note": "n"})
    assert has(check(make_repo(tmp_path), value), fragment)


def test_modeling_states(tmp_path):
    ctx = make_repo(tmp_path)
    impl = entry()["implementations"][0]
    cases = [
        ({**impl, "models": "best"}, "models must be one of"),
        ({key: value for key, value in impl.items() if key != "objective"}, "objective is required when models is optimized"),
        ({**impl, "objective": {"measure": "utility", "scope": "household"}}, "objective.measure must be one of"),
        ({**impl, "models": "convention"}, "objective is only for an implementation that optimizes"),
        ({**impl, "cites_entry": "no"}, "cites_entry must be true or false"),
        ({**impl, "path": "/abs.py"}, "path must be a relative path"),
        ({key: value for key, value in impl.items() if key not in ("repo", "commit")}, "repo is required"),
    ]
    for implementation, fragment in cases:
        assert has(check(ctx, entry(implementations=[implementation])), fragment), fragment
    # An optimizing implementation needs the entry's optimization; an exact
    # optimum needs an exact structure; a candidate set must be described.
    unoptimized = {key: value for key, value in entry().items() if key != "optimization"}
    assert has(check(ctx, unoptimized), "so the entry needs optimization.structure")
    assert has(check(ctx, entry(optimization={"structure": "search"})), "structure is search, which finds no exact optimum")
    candidate = {**impl, "models": "candidate-min"}
    assert has(check(ctx, entry(implementations=[candidate])), "needs optimization.candidates")
    assert check(ctx, entry(implementations=[candidate], optimization={"structure": "two-way", "candidates": "both"})) == []


def test_the_state_agency_decides(tmp_path):
    # Eng hub ruling 4: a state-agency entry is never optimized by the household.
    ctx = make_repo(tmp_path)
    value = entry(actor="state-agency")
    issues = check(ctx, value)
    assert has(issues, "optimization must be absent: the State agency decides")
    assert has(issues, "models must be one of convention, input, absent: the State agency decides")
    agency = {k: v for k, v in entry(actor="state-agency").items() if k not in ("optimization", "tests")}
    agency["implementations"] = [{**entry()["implementations"][0], "models": "absent"}]
    del agency["implementations"][0]["objective"]
    assert check(ctx, agency) == []


# ---------------------------------------------------------------------------
# Pins


def test_every_modeling_implementation_is_pinned(tmp_path):
    ctx = make_repo(tmp_path)
    assert has(check(ctx, entry(tests=[])), "tests must be a non-empty list")
    no_tests = {k: v for k, v in entry().items() if k != "tests"}
    assert has(
        check(ctx, no_tests),
        "models optimized, so a test in PolicyEngine/policyengine-us at the same commit must pin optimum on tax_unit_itemizes",
    )
    convention = {**entry()["implementations"][0], "models": "convention"}
    del convention["objective"]
    issues = check(ctx, entry(implementations=[convention]))
    assert has(issues, "models convention, so a test in PolicyEngine/policyengine-us at the same commit must pin default")
    default_pin = {"repo": PE, "commit": COMMIT, "path": "policyengine_us/tests/policy/itemizes.yaml",
                   "name": "Takes the default", "pins": ["default"]}
    assert check(ctx, entry(implementations=[convention], tests=[default_pin])) == []
    # A pin in another repository does not pin this one.
    elsewhere = {**entry()["tests"][0], "repo": "PolicyEngine/policyengine-uk"}
    assert has(check(ctx, entry(tests=[elsewhere])), "must pin optimum")
    # An implementation that does not model the choice needs no pin.
    absent = {k: v for k, v in convention.items()} | {"models": "absent"}
    assert check(ctx, {k: v for k, v in entry(implementations=[absent]).items() if k != "tests"}) == []
    # #1844 review round 3 (P2, P3): the pin is at the implementation's own
    # commit, and an optimum pin reads that implementation's decision variable.
    other_commit = {**entry()["tests"][0], "commit": "b" * 40}
    assert has(check(ctx, entry(tests=[other_commit])), "at the same commit must pin optimum on tax_unit_itemizes")
    other_variable = {**entry()["tests"][0], "variable": "is_tax_unit_head"}
    assert has(check(ctx, entry(tests=[other_variable])), "at the same commit must pin optimum on tax_unit_itemizes")
    default_elsewhere = {**default_pin, "commit": "b" * 40}
    assert has(check(ctx, entry(implementations=[convention], tests=[default_elsewhere])), "must pin default")
    # Two optimizing implementations need a pin each.
    second = {**entry()["implementations"][0], "path": "policyengine_us/variables/state_itemizes.py", "variable": "state_itemizes"}
    issues = check(ctx, entry(implementations=[entry()["implementations"][0], second]))
    assert [issue for issue in issues if "must pin optimum" in issue] == [
        "Entry `itemized-deduction-election` (entries[0]).implementations[1] models optimized, so a test in "
        "PolicyEngine/policyengine-us at the same commit must pin optimum on state_itemizes."
    ]
    state_pin = {**entry()["tests"][0], "name": "A state case", "variable": "state_itemizes"}
    assert check(ctx, entry(implementations=[entry()["implementations"][0], second], tests=[entry()["tests"][0], state_pin])) == []


@pytest.mark.parametrize(
    ("change", "fragment"),
    [
        ({"variable": None}, "variable is required when models is optimized"),
        ({"variable": "not a name"}, "implementations[0].variable must name the model variable"),
        ({"variable": 3}, "implementations[0].variable must name the model variable"),
    ],
)
def test_an_optimizing_implementation_names_its_variable(tmp_path, change, fragment):
    impl = {**entry()["implementations"][0], **change}
    if change.get("variable") is None:
        del impl["variable"]
    issues = check(make_repo(tmp_path), entry(implementations=[impl]))
    assert has(issues, fragment), issues
    # Without a variable, the coverage message doesn't print None.
    assert not any("on None" in issue for issue in issues)


@pytest.mark.parametrize(
    ("change", "fragment"),
    [
        ({"instances": ["first"]}, None),
        ({"instances": ["first", "second"]}, None),
        ({"instances": []}, "instances must be a non-empty list"),
        ({"instances": "first"}, "instances must be a non-empty list"),
        ({"instances": [""]}, "instances must be a non-empty list"),
        ({"instances": ["a\nb"]}, "instances must be a non-empty list"),
        ({"instances": [3]}, "instances must be a non-empty list"),
        ({"instances": ["first", "first"]}, "instances repeats an instance"),
    ],
)
def test_an_optimum_pin_may_name_its_instances(tmp_path, change, fragment):
    issues = check(make_repo(tmp_path), entry(tests=[{**entry()["tests"][0], **change}]))
    assert (issues == []) if fragment is None else has(issues, fragment), issues


def test_instances_are_only_for_an_optimum_pin(tmp_path):
    convention = {**entry()["implementations"][0], "models": "convention"}
    del convention["objective"]
    default_pin = {"repo": PE, "commit": COMMIT, "path": "policyengine_us/tests/policy/itemizes.yaml",
                   "name": "Takes the default", "pins": ["default"], "instances": ["first"]}
    assert has(check(make_repo(tmp_path), entry(implementations=[convention], tests=[default_pin])),
               "instances is only for an optimum pin")


@pytest.mark.parametrize(
    ("change", "fragment"),
    [
        ({"pins": []}, "pins must be a non-empty list of default or optimum"),
        ({"pins": ["reading"]}, "pins may name only default and optimum"),
        ({"pins": ["optimum", "optimum"]}, "pins repeats a pin"),
        ({"pins": ["default", "optimum"]}, "pins both default and optimum"),
        ({"variable": "not a name"}, "variable must name the model variable"),
        ({"chooses": "yes"}, "chooses is not one of the domain's options"),
        ({"chooses": False}, "chooses is the default, so the pin is vacuous"),
        ({"path": "policyengine_us/tests/test_itemizes.py", "name": "test_itemizes"}, "must be another repository's YAML test case"),
    ],
)
def test_optimum_pin_rules(tmp_path, change, fragment):
    pin = {**entry()["tests"][0], **change}
    assert has(check(make_repo(tmp_path), entry(tests=[pin])), fragment)


def test_an_optimum_pin_names_its_option(tmp_path):
    pin = {key: value for key, value in entry()["tests"][0].items() if key != "chooses"}
    assert has(check(make_repo(tmp_path), entry(tests=[pin])), "chooses is required with optimum")


def test_variable_and_chooses_belong_to_an_optimum_pin(tmp_path):
    convention = {**entry()["implementations"][0], "models": "input"}
    del convention["objective"]
    pin = {**entry()["tests"][0], "pins": ["default"]}
    issues = check(make_repo(tmp_path), entry(implementations=[convention], tests=[pin]))
    assert has(issues, "tests[0].variable is only for an optimum pin")
    assert has(issues, "tests[0].chooses is only for an optimum pin")


def test_test_locations_are_checked_as_the_register_checks_them(tmp_path):
    ctx = make_repo(tmp_path)
    pin = {**entry()["tests"][0], "path": "policyengine_us/policy/itemizes.yaml"}
    assert has(check(ctx, entry(tests=[pin])), "is not under a tests directory")
    local = {"path": "tests/test_missing.py", "name": "test_x", "pins": ["default"]}
    convention = {**entry()["implementations"][0], "models": "input"}
    del convention["objective"]
    assert has(check(ctx, entry(implementations=[convention], tests=[local])), "does not exist in this repository")
    repeated = entry()["tests"][0]
    assert has(check(ctx, entry(tests=[repeated, copy.deepcopy(repeated)])), "repeats policyengine_us/tests/policy/itemizes.yaml")


# ---------------------------------------------------------------------------
# Links: axiom.input, source_conflict, coupling


@pytest.mark.parametrize(
    ("value", "fragment"),
    [
        (f"us/statutes/26/152/c#input.{SLOT}", "must be <jurisdiction>:<module path>#input.<slot>"),
        (f"us:statutes/26/152/d#input.{SLOT}", "which is not a RuleSpec module in this repository"),
        (f"us-mt:statutes/26/152/c#input.{SLOT}", "which is not a RuleSpec module in this repository"),
        ("us:statutes/26/152/c#input.tiebreaker", "is a rule of us/statutes/26/152/c.yaml, not an input"),
        ("us:statutes/26/152/c#input.imported_fact", "is imported by us/statutes/26/152/c.yaml"),
        ("us:statutes/26/152/c#input.never_read", "no formula in us/statutes/26/152/c.yaml reads `never_read`"),
        (f"us:statutes/26/152/c#input.{SLOT[:-1]}", "reads"),  # a prefix of a slot is not that slot
    ],
)
def test_axiom_input_names_a_slot_a_formula_reads(tmp_path, value, fragment):
    issues = check(make_repo(tmp_path), child_entry(axiom={"input": value}))
    assert has(issues, fragment), issues


def test_axiom_needs_an_input_or_consumers(tmp_path):
    assert has(check(make_repo(tmp_path), child_entry(axiom={})), "axiom needs input, consumers or both")


def write_module(ctx, relative, slot, *, inputs=None):
    """A module at `relative` whose formula reads `slot`, optionally declaring inputs."""

    path = ctx.root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    module = {"format": "rulespec/v1", "module": {"summary": "x"},
              "rules": [{"name": "uses_it", "kind": "derived", "versions": [{"effective_from": "2020-01-01", "formula": f"{slot} or 0"}]}]}
    if inputs is not None:
        module["inputs"] = inputs
    path.write_text(yaml.safe_dump(module, sort_keys=False))


def consumers_entry(*consumers):
    return entry(axiom={"consumers": list(consumers)})


@pytest.mark.parametrize(
    ("declared", "fragment"),
    [
        (None, None),  # undeclared: the formula screen alone
        ([{"name": "itemizes", "entity": "TaxUnit", "dtype": "Boolean"}], None),
        ([{"name": "itemizes", "entity": "TaxUnit", "dtype": "Judgment"}], None),
        ([{"name": "other", "entity": "Person", "dtype": "Money"}], None),  # declares other inputs only
        # #1844 review round 3 (P3): a declared slot must fit the domain.
        ([{"name": "itemizes", "entity": "Household", "dtype": "Boolean"}], "declares `itemizes` on Household, not the domain's tax-unit"),
        ([{"name": "itemizes", "entity": "Asset", "dtype": "Boolean"}], "declares `itemizes` on Asset"),
        ([{"name": "itemizes", "entity": "TaxUnit", "dtype": "Money"}], "declares `itemizes` as Money, which can't hold a boolean choice"),
    ],
)
def test_a_declared_input_must_fit_the_domain(tmp_path, declared, fragment):
    ctx = make_repo(tmp_path)
    write_module(ctx, "us/statutes/26/55.yaml", "itemizes", inputs=declared)
    issues = check(ctx, consumers_entry({"input": "us:statutes/26/55#input.itemizes", "polarity": "same"}))
    assert (issues == []) if fragment is None else has(issues, fragment), issues


@pytest.mark.parametrize(
    ("consumers", "fragment"),
    [
        ([{"input": "us:statutes/26/55#input.itemizes", "polarity": "same"},
          {"input": "us:statutes/26/170/p#input.does_not_itemize", "polarity": "inverse"}], None),
        ([], "axiom.consumers must be a non-empty list"),
        ([{"input": "us:statutes/26/55#input.itemizes"}], "polarity must be same or inverse"),
        ([{"input": "us:statutes/26/55#input.itemizes", "polarity": "opposite"}], "polarity must be same or inverse"),
        ([{"input": "us:statutes/26/55#input.itemizes", "polarity": "same", "note": "x"}], "unknown key"),
        ([{"input": "us:statutes/26/99#input.itemizes", "polarity": "same"}], "is not a RuleSpec module in this repository"),
        ([{"input": "us:statutes/26/55#input.nothing", "polarity": "same"}], "no formula in us/statutes/26/55.yaml reads `nothing`"),
        ([{"input": "us:statutes/26/55#input.itemizes", "polarity": "same"},
          {"input": "us:statutes/26/55#input.itemizes", "polarity": "inverse"}], "repeats a consumer"),
    ],
)
def test_axiom_consumers(tmp_path, consumers, fragment):
    ctx = make_repo(tmp_path)
    write_module(ctx, "us/statutes/26/55.yaml", "itemizes")
    write_module(ctx, "us/statutes/26/170/p.yaml", "does_not_itemize")
    issues = check(ctx, entry(axiom={"consumers": consumers}))
    assert (issues == []) if fragment is None else has(issues, fragment), issues


def test_declared_input_screens_are_total_on_malformed_shapes(tmp_path):
    # #1844 review round 4 (P2): an unhashable domain kind or declared entity
    # crashed the declared-input screen. A deterministic sweep: every malformed
    # domain field, and every malformed declaration, through a declared
    # granting slot and a declared consumer.
    ctx = make_repo(tmp_path)
    shapes = ([], {}, None, 3, "", "x", True)
    declared = [{"name": "itemizes", "entity": "TaxUnit", "dtype": "Boolean"}]
    write_module(ctx, "us/statutes/26/55.yaml", "itemizes", inputs=declared)
    axiom = {"input": "us:statutes/26/55#input.itemizes", "consumers": [{"input": "us:statutes/26/55#input.itemizes", "polarity": "same"}]}
    for field in ("kind", "per"):
        for shape in shapes:
            value = entry(domain={"kind": "boolean", "per": "tax-unit", field: shape}, axiom=axiom)
            issues = check(ctx, value)
            assert isinstance(issues, list) and all(isinstance(issue, str) for issue in issues), (field, shape)
            assert issues, (field, shape)  # the malformed domain itself is reported
    for key in ("entity", "dtype"):
        for shape in shapes:
            write_module(ctx, "us/statutes/26/55.yaml", "itemizes", inputs=[{**declared[0], key: shape}])
            issues = check(ctx, entry(axiom={"consumers": axiom["consumers"]}))
            assert isinstance(issues, list) and all(isinstance(issue, str) for issue in issues), (key, shape)
            assert has(issues, f"declares `itemizes` {'on' if key == 'entity' else 'as'} {shape}"), (key, shape, issues)


def test_the_granting_slot_is_screened_against_its_declaration_too(tmp_path):
    ctx = make_repo(tmp_path)
    write_module(ctx, "us/statutes/26/63/e.yaml", "itemizes", inputs=[{"name": "itemizes", "entity": "Person", "dtype": "Boolean"}])
    issues = check(ctx, entry(axiom={"input": "us:statutes/26/63/e#input.itemizes"}))
    assert has(issues, "declares `itemizes` on Person, not the domain's tax-unit"), issues


@pytest.mark.parametrize("polarity", ["same", "inverse"])
def test_consumers_are_only_for_a_boolean_choice(tmp_path, polarity):
    # Eng hub condition 3: no mapping between other kinds of slot values is
    # defined, so a non-boolean choice lists no consumers, whatever the polarity.
    ctx = make_repo(tmp_path)
    write_module(ctx, "us/statutes/26/55.yaml", "share_input")
    share = entry(domain={"kind": "share", "per": "tax-unit", "bounds": ["0", "1"]}, default={"value": "0", "basis": "convention", "note": "n"},
                  axiom={"consumers": [{"input": "us:statutes/26/55#input.share_input", "polarity": polarity}]})
    assert has(check(ctx, share), "axiom.consumers is only for a boolean choice")
    enum = entry(domain={"kind": "enum", "per": "tax-unit", "options": ["a", "b"]}, default={"value": "a", "basis": "convention", "note": "n"},
                 axiom={"consumers": [{"input": "us:statutes/26/55#input.share_input", "polarity": polarity}]})
    assert has(check(ctx, enum), "axiom.consumers is only for a boolean choice")


def test_a_consumer_is_not_the_input_but_may_share_its_module(tmp_path):
    ctx = make_repo(tmp_path)
    slot = f"us:statutes/26/152/c#input.{SLOT}"
    same = child_entry(axiom={"input": slot, "consumers": [{"input": slot, "polarity": "same"}]})
    assert has(check(ctx, same), "is axiom.input itself")
    # Another slot of the granting module is a consumer like any other.
    other = child_entry(axiom={"input": slot, "consumers": [{"input": "us:statutes/26/152/c#input.other_input", "polarity": "inverse"}]})
    assert check(ctx, other) == []


def test_source_conflict_names_a_register_entry(tmp_path):
    register = {"version": 1, "entries": [{"id": "some-conflict", "jurisdiction": "us"}]}
    ctx = make_repo(tmp_path, register=register)
    assert not has(check(ctx, entry(source_conflict="us:some-conflict")), "source_conflict")
    assert has(check(ctx, entry(source_conflict="us:no-such-conflict")), "source_conflict must be the global id of an entry")


def test_coupled_choices_list_each_other(tmp_path):
    ctx = make_repo(tmp_path)
    a = entry(domain={"kind": "boolean", "per": "tax-unit", "coupled_with": ["us:qualifying-child-claim-by-non-parent"]})
    b = child_entry()
    assert has(check(ctx, a, b), "does not list `us:itemized-deduction-election` in domain.coupled_with")
    b["domain"]["coupled_with"] = ["us:itemized-deduction-election"]
    assert check(ctx, a, b) == []
    assert has(check(ctx, entry(domain={"kind": "boolean", "per": "tax-unit", "coupled_with": ["us:itemized-deduction-election"]})),
               "must be the global id of another entry")
    assert has(check(ctx, entry(domain={"kind": "boolean", "per": "tax-unit", "coupled_with": []})), "non-empty list of global ids")


# ---------------------------------------------------------------------------
# One id namespace with the register


def test_a_global_id_is_never_in_both_files(tmp_path):
    # Eng hub ruling 2: one shared function, called by both checks, so a
    # register entry added later can't take a choice's id either.
    register = {"version": 1, "entries": [{"id": "itemized-deduction-election", "jurisdiction": "us"}]}
    ctx = make_repo(tmp_path, register=register)
    fragment = "`us:itemized-deduction-election` is both known-source-conflicts.yaml entries[0] and household-choices.yaml entries[0]"
    assert has(check(ctx, entry()), fragment)
    (tmp_path / hc.CHOICES_FILENAME).write_text(yaml.safe_dump(payload(entry())))
    assert has(sc.check_register(register, ctx, scan_modules=False), fragment)
    # The same local id in another jurisdiction is another global id.
    register["entries"][0]["jurisdiction"] = "us-mt"
    (tmp_path / sc.REGISTER_FILENAME).write_text(yaml.safe_dump(register))
    assert not has(check(ctx, entry()), "is both")


def test_an_unreadable_other_file_fails_both_checks(tmp_path):
    ctx = make_repo(tmp_path)
    (tmp_path / sc.REGISTER_FILENAME).write_text("entries: [&a {}]\n")
    issues = check(ctx, entry())
    assert has(issues, "cannot read known-source-conflicts.yaml to check that no global id is in both files")
    (tmp_path / sc.REGISTER_FILENAME).unlink()
    (tmp_path / hc.CHOICES_FILENAME).symlink_to(tmp_path / "elsewhere.yaml")
    issues = sc.check_register({"version": 1, "entries": []}, ctx, scan_modules=False)
    assert has(issues, "cannot read household-choices.yaml to check that no global id is in both files")


def test_files_read_beside_the_payload_never_raise(tmp_path):
    # #1844 review round 7 (P3): a value YAML cannot construct (a date such
    # as 2026-02-30) in a referenced module or the other root file raised
    # ValueError, and so did a local test file that couldn't be read.
    ctx = make_repo(tmp_path)
    module = tmp_path / "us" / "statutes" / "26" / "152" / "c.yaml"
    module.write_text(module.read_text().replace("'1990-01-01'", "2026-02-30"))
    assert hc._module_rules(module) is None and hc._declared_inputs(module) == {}
    issues = check(ctx, child_entry())
    assert has(issues, "us/statutes/26/152/c.yaml is not readable YAML"), issues
    ctx = make_repo(tmp_path)
    (tmp_path / sc.REGISTER_FILENAME).write_text("version: 1\nentries: []\nextra: 2026-02-30\n")
    assert has(check(ctx, entry()), "cannot read known-source-conflicts.yaml to check that no global id is in both files")
    (tmp_path / sc.REGISTER_FILENAME).unlink()
    (tmp_path / hc.CHOICES_FILENAME).write_text("version: 1\nentries: []\nextra: 2026-02-30\n")
    issues = sc.check_register({"version": 1, "entries": []}, ctx, scan_modules=False)
    assert has(issues, "cannot read household-choices.yaml to check that no global id is in both files")
    (tmp_path / hc.CHOICES_FILENAME).unlink()


def test_a_local_default_pin_whose_file_cannot_be_read_is_an_issue(tmp_path):
    ctx = make_repo(tmp_path)
    local = {"path": "tests/default.test.yaml", "name": "Local default", "pins": ["default"]}
    value = entry(tests=[entry()["tests"][0], local])
    test_file = tmp_path / "tests" / "default.test.yaml"
    test_file.write_text("- name: Local default\n  period: 2026\n")
    assert check(ctx, value) == []
    for text in ("- name: Local default\n  period: 2026-02-30\n", "[" * 600 + "]" * 600):
        test_file.write_text(text)
        assert has(check(ctx, value), "Local default is not a test case in tests/default.test.yaml")
    if os.geteuid() != 0:  # root reads a chmod-0 file
        test_file.chmod(0)
        try:
            assert has(check(ctx, value), "tests/default.test.yaml cannot be read")
        finally:
            test_file.chmod(0o644)


# ---------------------------------------------------------------------------
# statutory_not_choice, hygiene, money


def test_statutory_not_choice(tmp_path):
    ctx = make_repo(tmp_path)
    good = {"jurisdiction": "us-mt", "citation": "MCA 2021 15-30-2131(1)(c)(vi)(D)", "note": "Split equally by statute."}
    assert check(ctx, entry(), statutory=[good]) == []
    issues = check(ctx, entry(), statutory=[good, dict(good), {"jurisdiction": "us-zz", "citation": "", "extra": 1}])
    assert has(issues, "statutory_not_choice[1] repeats MCA 2021 15-30-2131(1)(c)(vi)(D) for us-mt")
    assert has(issues, "statutory_not_choice[2] has unknown key `extra`")
    assert has(issues, "statutory_not_choice[2].jurisdiction must be a jurisdiction directory")
    assert has(issues, "statutory_not_choice[2].citation must be a non-blank string")
    assert has(issues, "statutory_not_choice[2].note must be a non-blank string")
    assert has(check(ctx, entry(), statutory=[]), "statutory_not_choice must be a non-empty list")


@pytest.mark.parametrize("text", ["see d1741", "from local_26f3b41d", "at /Users/x/file", "mail a@b.org"])
def test_hygiene(tmp_path, text):
    issues = check(make_repo(tmp_path), entry(question=f"Does it? ({text})"))
    assert has(issues, "; household-choices.yaml is public.")


@pytest.mark.parametrize("question", ["Is it worth $1,200?", "Is it worth 200 dollars?", "Is it worth USD 200?"])
def test_prose_states_no_money(tmp_path, question):
    issues = check(make_repo(tmp_path), entry(question=question))
    assert has(issues, "describe the effect without an amount")


def test_excerpts_may_quote_money(tmp_path):
    texts = [{"corpus_citation_path": "us/statute/26/63/e/1", "excerpt": "a deduction of $1,200"}]
    assert check(make_repo(tmp_path), entry(texts=texts)) == []


def test_anchors_are_refused(tmp_path):
    path = tmp_path / hc.CHOICES_FILENAME
    path.write_text("version: 1\nentries: [&a {id: x}, *a]\n")
    with pytest.raises(sc.RegisterError):
        sc.load_register(path)


def _field_paths(value, prefix=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield (*prefix, key)
            yield from _field_paths(child, (*prefix, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield (*prefix, index)
            yield from _field_paths(child, (*prefix, index))


def test_check_is_total_on_every_field(tmp_path):
    # As for the register: replace every field of well-formed entries, at
    # every depth, with each malformed shape; check returns strings and never raises.
    ctx = make_repo(tmp_path, register={"version": 1, "entries": [{"id": "c", "jurisdiction": "us"}]})
    for base in (entry(source_conflict="us:c", multi_year=True), child_entry(domain={"kind": "share", "per": "person", "bounds": ["0", "1"], "coupled_with": ["us:x"]})):
        for path in list(_field_paths(base)):
            for new in ([], {}, None, 7, -1.5, True, "", "x", [[]], {"a": []}):
                value = copy.deepcopy(base)
                target = value
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = new
                issues = hc.check_choices(payload(value, copy.deepcopy(value), statutory=[{"note": new}]), ctx)
                assert isinstance(issues, list) and all(isinstance(issue, str) for issue in issues), (path, new)


def test_check_cli(tmp_path, capsys):
    make_repo(tmp_path)
    assert hc.main(["check", "--root", str(tmp_path)]) == 1
    assert "must be a regular file" in capsys.readouterr().err
    (tmp_path / hc.CHOICES_FILENAME).write_text(yaml.safe_dump(payload(entry(actor="robot"))))
    assert hc.main(["check", "--root", str(tmp_path)]) == 1
    captured = capsys.readouterr()
    assert "actor must be one of" in captured.err and "1 entry, 1 issue(s)" in captured.out


# ---------------------------------------------------------------------------
# The worklist


def test_worklist():
    assert hc.worklist(child_entry()) == ["no implementation recorded"]
    itemize = entry()
    assert hc.worklist(itemize) == [
        "PolicyEngine/policyengine-us optimizes federal-income-tax over the tax-unit, narrower than net-income over the household",
        "no Axiom input slot in the module that grants it yet",
    ]
    # #1844 review round 3 (P2): the consumers a caller must set consistently.
    consumers = [{"input": "us:statutes/26/55#input.itemizes", "polarity": "same"},
                 {"input": "us:statutes/26/170/p#input.does_not_itemize", "polarity": "inverse"}]
    assert hc.worklist(entry(axiom={"consumers": consumers}))[-1] == (
        "no Axiom input slot in the module that grants it yet; other slots take it as an input, so a caller sets "
        "them consistently (this lists them; it doesn't check that their encodings agree): "
        "us:statutes/26/55#input.itemizes (same), us:statutes/26/170/p#input.does_not_itemize (inverse)"
    )
    assert not any("Axiom" in line for line in hc.worklist(entry(axiom={"input": "x", "consumers": consumers})))
    impl = itemize["implementations"][0]
    broad = {**impl, "objective": {"measure": "net-income", "scope": "household"}}
    assert hc.worklist(entry(implementations=[broad], axiom={"input": "x"})) == []
    convention = {**impl, "models": "convention"}
    absent = {**impl, "models": "absent"}
    candidate = {**broad, "models": "candidate-min"}
    lines = hc.worklist(entry(implementations=[convention, absent, candidate], multi_year=True, axiom={"input": "x"}))
    assert lines == [
        "PolicyEngine/policyengine-us uses convention where a two-way comparison finds the exact optimum",
        "PolicyEngine/policyengine-us does not model this choice",
        "PolicyEngine/policyengine-us uses candidate-min where a two-way comparison finds the exact optimum",
        "binds later years or carries amounts forward; optimized one year at a time",
    ]
    # With no cheap exact structure, a convention is not a gap.
    assert hc.worklist(entry(implementations=[convention], optimization={"structure": "search"}, axiom={"input": "x"})) == []


@pytest.mark.parametrize(
    ("wanted", "actual", "ok"),
    [
        (("net-income", "household"), ("net-income", "household"), True),
        (("net-income", "household"), ("total-tax", "household"), False),
        (("total-tax", "household"), ("net-income", "household"), True),
        (("total-tax", "tax-unit"), ("total-tax", "tax-unit"), True),
        (("total-tax", "household"), ("total-tax", "tax-unit"), False),
        (("net-income", "tax-unit"), ("federal-income-tax", "tax-unit"), False),
    ],
)
def test_meets_standard(wanted, actual, ok):
    as_objective = lambda pair: {"measure": pair[0], "scope": pair[1]}  # noqa: E731
    assert hc.meets_standard(as_objective(wanted), as_objective(actual)) is ok


# ---------------------------------------------------------------------------
# verify (network, faked)


class FakeNet:
    def __init__(self, files):
        self.files = files

    def __call__(self, repo, commit, path):
        try:
            return self.files[(repo, commit, path)]
        except KeyError:
            raise OSError(f"404 {repo}@{commit}:{path}") from None


def substring(source_text, excerpt):
    return excerpt in source_text


def verified_inputs(source=b"class tax_unit_itemizes(Variable):\n    pass\n"):
    value = entry(proposed=[{"repo": PE, "pr": f"https://github.com/{PE}/pull/1", "path": "x.py", "models": "candidate-min"}])
    files = {
        (PE, COMMIT, value["implementations"][0]["path"]): source,
        (PE, COMMIT, value["tests"][0]["path"]): b"- name: A case that itemizes\n  output: {}\n",
    }
    corpus = {"us/statute/26/63/e/1": "... Unless an individual makes an election under this subsection ..."}
    return payload(value), FakeNet(files), corpus


def test_verify_passes_and_reports_the_worklist():
    choices, net, corpus = verified_inputs()
    issues, report = hc.verify_choices(choices, fetch=net, matches=substring, resolve=corpus.get, on_default_branch=lambda r, c: True)
    assert issues == []
    assert report[0] == "verified: 1 texts, 0 pending texts, 1 implementations, 1 tests"
    assert any(line.startswith("uncited: us:itemized-deduction-election") for line in report)
    assert any(line.startswith("proposed: ") and "would model it as candidate-min" in line for line in report)
    assert "worklist: us:itemized-deduction-election: no Axiom input slot in the module that grants it yet" in report


@pytest.mark.parametrize(
    ("source", "issue"),
    [
        (b"class tax_unit_itemizes(Variable):\n    pass\n", None),
        (b"import x\n\nclass tax_unit_itemizes(x.Variable):\n    value_type = bool\n", None),
        # #1844 review round 4 (P2): class-shaped text that defines nothing.
        (b'DOC = """\nclass tax_unit_itemizes(Variable):\n    pass\n"""\n', "does not define `class tax_unit_itemizes` in module scope"),
        (b"# class tax_unit_itemizes(Variable):\nx = 1\n", "does not define `class tax_unit_itemizes` in module scope"),
        (b"def f():\n    class tax_unit_itemizes(Variable):\n        pass\n", "does not define `class tax_unit_itemizes` in module scope"),
        (b"class Outer:\n    class tax_unit_itemizes(Variable):\n        pass\n", "does not define `class tax_unit_itemizes` in module scope"),
        (b"class tax_unit_itemizes_other(Variable):\n    pass\n", "does not define `class tax_unit_itemizes` in module scope"),
        # Round 6 (P2): an if, try or with opens no scope, so a class inside
        # one at module level is a module-level class, as core loads it.
        (b"if True:\n    class tax_unit_itemizes(Variable):\n        pass\n", None),
        (b"try:\n    import x\nexcept ImportError:\n    class tax_unit_itemizes(Variable):\n        pass\n", None),
        (b"with open('x') as f:\n    class tax_unit_itemizes(Variable):\n        pass\n", None),
        (b"class tax_unit_itemizes(Variable:\n", "does not parse as Python"),
    ],
)
def test_verify_parses_the_class_definition(source, issue):
    choices, net, corpus = verified_inputs(source=source)
    issues, _ = hc.verify_choices(choices, fetch=net, matches=substring, resolve=corpus.get, on_default_branch=lambda r, c: True)
    assert (issues == []) if issue is None else (len(issues) == 1 and issue in issues[0]), issues


def test_verify_checks_the_implementation_defines_its_variable():
    # #1844 review round 3 (P2): the implementation file defines the variable
    # its optimum pin reads.
    choices, net, corpus = verified_inputs(source=b"class is_tax_unit_head(Variable):\n    pass\n")
    issues, _ = hc.verify_choices(choices, fetch=net, matches=substring, resolve=corpus.get, on_default_branch=lambda r, c: True)
    assert issues == [
        "us:itemized-deduction-election (entries[0]).implementations[0]: policyengine_us/variables/tax_unit_itemizes.py "
        "does not define `class tax_unit_itemizes` in module scope."
    ]
    # A parameter file can't be checked that way: the report says so.
    choices, net, corpus = verified_inputs()
    implementation = choices["entries"][0]["implementations"][0]
    implementation["path"] = "policyengine_us/parameters/itemizes.yaml"
    net.files[(PE, COMMIT, implementation["path"])] = b"values: {}\n"
    issues, report = hc.verify_choices(choices, fetch=net, matches=substring, resolve=corpus.get, on_default_branch=lambda r, c: True)
    assert issues == []
    assert any(line.startswith("unchecked: ") and "not a Python file" in line for line in report)


def test_verify_findings():
    choices, net, corpus = verified_inputs(source=b"# Household choice us:itemized-deduction-election\n")
    issues, report = hc.verify_choices(choices, fetch=net, matches=substring, resolve=None, on_default_branch=lambda r, c: False)
    assert any("not verified; no pinned corpus release was given" in issue for issue in issues)
    assert any("cites_entry is false but the file carries `# Household choice us:itemized-deduction-election`" in issue for issue in issues)
    assert sum("is not on PolicyEngine/policyengine-us's default branch" in issue for issue in issues) == 2
    choices["entries"][0]["tests"][0]["name"] = "No such case"
    issues, _ = hc.verify_choices(choices, fetch=net, matches=substring, resolve=corpus.get)
    assert any("No such case is not a test case in" in issue for issue in issues)
    issues, report = hc.verify_choices(choices, fetch=FakeNet({}), matches=substring, resolve=corpus.get)
    assert report[1] == sc.UNCHECKED_REACHABILITY
    assert sum("cannot read" in issue for issue in issues) == 2


@pytest.mark.parametrize(
    ("source", "found"),
    [
        ("# Household choice us:a\n", True),
        ("x = 1  #  Household choice us:a", True),
        ("# Household choice us:a-b\n", False),
        ("# Household choice us:a:b\n", False),
        ("# Source conflict us:a\n", False),
        ("us:a\n", False),
    ],
)
def test_cites_is_the_marker_with_a_whole_id(source, found):
    assert hc.cites(source, "us:a") is found


@pytest.mark.parametrize(
    ("source", "found"),
    [
        ("# Source conflict us:a\n", True),
        ("see us:a.", True),
        ("# Household choice us:a-b\n", False),
        ("# Source conflict us-mt:a\n", False),
        ("# Source conflict us:a:b\n", False),
    ],
)
def test_the_registers_cite_is_a_whole_id(source, found):
    # A household choice's marker never reads as a cite of a register entry
    # whose id it extends: ids are compared whole, in both tools.
    assert sc.cites_global_id(source, "us:a") is found


# ---------------------------------------------------------------------------
# aggregate


def test_aggregate_view_round_trips_and_is_deterministic():
    files = {
        "TheAxiomFoundation/rulespec-us": payload(entry(), child_entry(), statutory=[{"jurisdiction": "us-mt", "citation": "c", "note": "n"}]),
        "TheAxiomFoundation/rulespec-uk": payload(entry(id="marriage-allowance-transfer", jurisdiction="uk")),
    }
    view, issues = hc.aggregate(files)
    assert issues == []
    assert [row["global_id"] for row in view["entries"]] == [
        "uk:marriage-allowance-transfer", "us:itemized-deduction-election", "us:qualifying-child-claim-by-non-parent",
    ]
    assert hc.files_from_view(view) == {repo: files[repo] for repo in sorted(files)}
    reversed_files = dict(reversed(list(files.items())))
    assert hc.render_json(hc.aggregate(reversed_files)[0]) == hc.render_json(view)
    assert hc.render_markdown(hc.aggregate(reversed_files)[0]) == hc.render_markdown(view)


def test_aggregate_collisions_and_jurisdictions():
    files = {
        "TheAxiomFoundation/rulespec-us": payload(entry()),
        "TheAxiomFoundation/rulespec-us-ca": payload(entry(), entry(id="other", jurisdiction="uk")),
    }
    view, issues = hc.aggregate(files)
    assert "us:itemized-deduction-election is in both TheAxiomFoundation/rulespec-us and TheAxiomFoundation/rulespec-us-ca." in issues
    assert "TheAxiomFoundation/rulespec-us-ca: uk:other has a jurisdiction outside that repository." in issues
    assert len(view["entries"]) == 2


def test_markdown_escapes_cells():
    view, _ = hc.aggregate({"TheAxiomFoundation/rulespec-us": payload(entry(actor="a|b\nc"))})
    row = hc.render_markdown(view).splitlines()[6]
    assert "a\\|b c" in row and row.count(" | ") == 5


def test_the_view_holds_copies_of_every_row():
    # #1844 review round 7 (P3): removing the copy from the
    # statutory_not_choice rows passed every test.
    files = {"TheAxiomFoundation/rulespec-us-mt": {
        "version": 1, "entries": [entry(jurisdiction="us-mt")],
        "statutory_not_choice": [{"jurisdiction": "us-mt", "citation": "MCA 2021 15-30-2131", "note": "Split equally."}],
    }}
    before = copy.deepcopy(files)
    view, _ = hc.aggregate(files)
    view["entries"][0]["entry"]["question"] = "changed"
    view["statutory_not_choice"][0]["item"]["note"] = "changed"
    view["repositories"][0]["version"] = "changed"
    assert files == before


def test_aggregate_cli_reports_an_unreadable_local_file(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("version: 1\nentries: []\nextra: 2026-02-30\n")
    assert hc.main(["aggregate", "--file", f"TheAxiomFoundation/rulespec-uk={bad}", "--json", str(tmp_path / "v.json")]) == 1
    assert "TheAxiomFoundation/rulespec-uk: " in capsys.readouterr().err


def test_aggregate_cli_writes_the_same_bytes_twice(tmp_path, capsys):
    source = tmp_path / "choices.yaml"
    source.write_text(yaml.safe_dump(payload(entry(), child_entry())))
    outputs = []
    for run in range(2):
        out = tmp_path / f"view-{run}.json"
        assert hc.main(["aggregate", "--file", f"TheAxiomFoundation/rulespec-us={source}", "--json", str(out)]) == 0
        outputs.append(out.read_bytes())
    assert outputs[0] == outputs[1]
    assert json.loads(outputs[0])["entries"][0]["worklist"]


# ---------------------------------------------------------------------------
# #1844 review: guards no test caught


def test_agency_defaults_may_rest_on_practice_or_rulemaking(tmp_path):
    for kind in ("agency-practice", "rulemaking"):
        pending = [{"citation": "Agency letter", "kind": kind, "url": "https://x.example", "excerpt": "e",
                    "snapshot": {"repo": PE, "commit": COMMIT, "path": "s.html", "sha256": "b" * 64}}]
        value = entry(texts=[], pending_texts=pending, default={"value": False, "basis": "agency"})
        assert not has(check(make_repo(tmp_path), value), "must cite a text of kind"), kind


def test_a_state_agency_entry_proposes_and_pins_no_optimum(tmp_path):
    agency = {k: v for k, v in entry(actor="state-agency").items() if k not in ("optimization", "implementations")}
    agency["proposed"] = [{"repo": PE, "pr": f"https://github.com/{PE}/pull/1", "path": "x.py", "models": "optimized"}]
    issues = check(make_repo(tmp_path), agency)
    assert has(issues, "proposed[0].models must be one of convention, input, absent: the State agency decides")
    assert has(issues, "tests[0] pins optimum, but the State agency decides")


def test_an_unreadable_sibling_file_is_an_issue_not_a_crash(tmp_path):
    ctx = make_repo(tmp_path, register={"version": 1, "entries": []})
    register = tmp_path / sc.REGISTER_FILENAME
    register.chmod(0)
    try:
        try:
            register.read_bytes()
            pytest.skip("this user can read a mode-000 file (root?)")
        except PermissionError:
            pass
        issues = check(ctx, entry())
        assert has(issues, "cannot read known-source-conflicts.yaml to check source_conflict links")
        assert has(issues, "cannot read known-source-conflicts.yaml to check that no global id is in both files")
    finally:
        register.chmod(0o644)


def test_an_unparseable_or_too_deep_module_is_an_issue(tmp_path):
    ctx = make_repo(tmp_path)
    module = tmp_path / "us" / "statutes" / "26" / "152" / "c.yaml"
    for text in ("rules: [", "rules: " + "[" * 20000 + "]" * 20000):
        module.write_text(text)
        assert has(check(ctx, child_entry()), "us/statutes/26/152/c.yaml is not readable YAML")


def test_coupled_with_repeats_an_entry(tmp_path):
    a = entry(domain={"kind": "boolean", "per": "tax-unit",
                      "coupled_with": ["us:qualifying-child-claim-by-non-parent", "us:qualifying-child-claim-by-non-parent"]})
    b = child_entry(domain={"kind": "boolean", "per": "person", "coupled_with": ["us:itemized-deduction-election"]})
    assert has(check(make_repo(tmp_path), a, b), "domain.coupled_with repeats an entry")


@pytest.mark.parametrize(
    "path",
    [("full_optimization",), ("default", "note"), ("optimization", "candidates"), ("years", "note"),
     ("implementations", 0, "basis")],
)
def test_every_prose_field_states_no_money(tmp_path, path):
    value = entry(full_optimization="x", years={"from": 2020, "type": "program", "note": "x"})
    value["optimization"]["candidates"] = "x"
    value["implementations"][0]["basis"] = "x"
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = "It saves $5 a year."
    label = ".".join(str(part) for part in path).replace(".0.", "[0].")
    assert has(check(make_repo(tmp_path), value), f"{label} states $5"), label


def test_statutory_notes_state_no_money(tmp_path):
    item = {"jurisdiction": "us-mt", "citation": "MCA", "note": "Split equally, $5 each."}
    assert has(check(make_repo(tmp_path), entry(), statutory=[item]), "statutory_not_choice[0].note states $5")


@pytest.mark.parametrize(
    ("change", "fragment"),
    [
        ({"repo": "not a repo"}, "proposed[0].repo must be owner/name"),
        ({"pr": "PolicyEngine/policyengine-us#1"}, "proposed[0].pr must be a github.com pull request URL"),
        ({"pr": "https://github.com/PolicyEngine/policyengine-uk/pull/1"}, "is a pull request in PolicyEngine/policyengine-uk"),
        ({"path": "/abs.py"}, "proposed[0].path must be a relative path"),
        ({"models": "best"}, "proposed[0].models must be one of"),
        ({"follows": "reading"}, "proposed[0] has unknown key `follows`"),
    ],
)
def test_proposed_changes(tmp_path, change, fragment):
    proposal = {"repo": PE, "pr": f"https://github.com/{PE}/pull/1", "path": "x.py", "models": "candidate-min", **change}
    assert has(check(make_repo(tmp_path), entry(proposed=[proposal])), fragment)
    assert has(check(make_repo(tmp_path), entry(proposed=[])), "proposed must be a non-empty list")


def test_malformed_statutory_identities_are_issues_not_crashes(tmp_path):
    # #1844 review round 2 (P2): an unhashable jurisdiction or citation crashed
    # the duplicate check.
    ctx = make_repo(tmp_path)
    for field in ("jurisdiction", "citation", "note"):
        for shape in ([], {}, None, 3, "", [[]], {"a": []}):
            item = {"jurisdiction": "us-mt", "citation": "MCA", "note": "n", field: shape}
            issues = check(ctx, entry(), statutory=[item, copy.deepcopy(item)])
            assert isinstance(issues, list) and all(isinstance(issue, str) for issue in issues), (field, shape)


def test_aggregate_keeps_an_empty_file():
    files = {"TheAxiomFoundation/rulespec-us": {"version": 1, "entries": []}}
    view, issues = hc.aggregate(files)
    assert issues == [] and view["repositories"] == [{"repository": "TheAxiomFoundation/rulespec-us", "version": 1}]
    assert hc.files_from_view(view) == files


def test_float32_twins_are_one_option(tmp_path):
    # A pin can't tell 16777217 from 16777216: a model stores both as one float32.
    value = entry(domain={"kind": "amount", "per": "tax-unit", "bounds": ["0", "20000000"], "currency": "USD"},
                  default={"value": "16777216", "basis": "convention", "note": "n"})
    value["tests"][0]["chooses"] = "16777217"
    assert has(check(make_repo(tmp_path), value), "chooses is the default, so the pin is vacuous")
