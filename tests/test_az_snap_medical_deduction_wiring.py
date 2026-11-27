"""Arizona SNAP: the standard medical deduction reaches the benefit chain.

rulespec-us#952. The benefit reads the 7 CFR 273.10 net-income chain, whose
``snap_excess_medical_deduction_for_net_income`` is

    if household_entitled_to_excess_medical_deduction:
        max(0, snap_total_medical_expenses - snap_medical_expense_threshold)
    else: 0

Both operands were free inputs. The Arizona FAA5 NA Medical Expenses and
Deduction module (block 2) computes the deduction Arizona allows: the $145
Standard Medical Deduction, or the actual amount minus the $35 disregard. The
ProgramSpec binds three slots:

    household_entitled_to_excess_medical_deduction
        := medical_expense_participant_is_deduction_eligible
    snap_total_medical_expenses
        := medical_deduction + snap_medical_expense_threshold
    budgetary_unit_includes_elderly_or_disabled_participant_with_medical_expenses
        := snap_household_has_elderly_or_disabled_member

The second binding relies on max(0, d + t - t) = d, which holds because
``medical_deduction`` is never negative. It also means
``snap_total_medical_expenses`` holds a deduction plus the threshold, not a
total; the reader guard below fails if any other in-scope rule reads it.

The static contracts pin the bindings, check them against the module and
regulation rules they rely on, and guard the bound slots' readers. The
executable contracts compose the program with axiom-compose, compile it with
axiom-rules-engine and run it. They need both tools and skip without them,
unless ``AXIOM_REQUIRE_WIRING_EXECUTABLE=1`` (set by the program-artifacts
workflow, which installs both), in which case a missing tool fails.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "programs/us-az/snap/fy-2026.yaml"
AZ_SCOPE = "policies/des/faa5/na-medical-expenses-and-deduction/medical-deduction"
AZ_ID = f"us-az:{AZ_SCOPE}"
AZ_MODULE = ROOT / "us-az" / f"{AZ_SCOPE}.yaml"
FEDERAL_ID = "us:regulations/7-cfr/273/10"
FEDERAL = ROOT / "us/regulations/7-cfr/273/10.yaml"
MEMBER_RELATION = "us:statutes/7/2012/j#relation.member_of_household"
PERIOD = {"period_kind": "month", "start": "2026-01-01", "end": "2026-01-31"}
INTERVAL = {"start": PERIOD["start"], "end": PERIOD["end"]}
REQUIRE_EXECUTABLE = os.environ.get("AXIOM_REQUIRE_WIRING_EXECUTABLE") == "1"

# Slot -> the only modules whose rules may read it once the spec binds it.
BOUND_SLOT_READERS = {
    "snap_total_medical_expenses": {FEDERAL_ID},
    "household_entitled_to_excess_medical_deduction": {FEDERAL_ID},
    "budgetary_unit_includes_elderly_or_disabled_participant_with_medical_expenses": {AZ_ID},
}


def _transformations() -> dict[str, dict]:
    spec = yaml.safe_load(SPEC.read_text())
    return {item["name"]: item for item in spec.get("transformations") or []}


def _rules(path: Path) -> dict[str, dict]:
    payload = yaml.safe_load(path.read_text())
    return {rule["name"]: rule for rule in payload.get("rules") or []}


def test_spec_binds_the_federal_medical_operands_to_the_arizona_deduction() -> None:
    spec = yaml.safe_load(SPEC.read_text())
    assert AZ_SCOPE in spec["scope"]["state"]
    assert "regulations/7-cfr/273/10" in spec["scope"]["federal"]
    assert "statutes/7/2012/j" in spec["scope"]["federal"]

    bound = _transformations()
    entitled = bound["household_entitled_to_excess_medical_deduction"]
    assert entitled["pattern"] == "all_of"
    assert entitled["conditions"] == ["medical_expense_participant_is_deduction_eligible"]
    assert (entitled["entity"], entitled["dtype"], entitled["period"]) == (
        "Household",
        "Judgment",
        "Month",
    )

    total = bound["snap_total_medical_expenses"]
    assert total["pattern"] == "derived_formula"
    assert total["formula"].split() == [
        "medical_deduction",
        "+",
        "snap_medical_expense_threshold",
    ]
    assert (total["entity"], total["dtype"], total["period"], total["unit"]) == (
        "Household",
        "Money",
        "Month",
        "USD",
    )

    member = bound[
        "budgetary_unit_includes_elderly_or_disabled_participant_with_medical_expenses"
    ]
    assert member["pattern"] == "all_of"
    assert member["conditions"] == ["snap_household_has_elderly_or_disabled_member"]
    assert (member["entity"], member["dtype"], member["period"]) == (
        "Household",
        "Judgment",
        "Month",
    )


def test_bindings_match_the_rules_they_rely_on() -> None:
    federal = _rules(FEDERAL)
    step = federal["snap_excess_medical_deduction_for_net_income"]
    assert step["entity"] == "Household" and step["period"] == "Month"
    assert step["versions"][-1]["formula"].split() == (
        "if household_entitled_to_excess_medical_deduction: "
        "max(0, snap_total_medical_expenses - snap_medical_expense_threshold) else: 0"
    ).split()
    assert "snap_medical_expense_threshold" in federal

    household_flag = _rules(ROOT / "us/statutes/7/2012/j.yaml")[
        "snap_household_has_elderly_or_disabled_member"
    ]
    assert (household_flag["entity"], household_flag["period"]) == ("Household", "Month")

    arizona = _rules(AZ_MODULE)
    for name in ("medical_deduction", "medical_expense_participant_is_deduction_eligible"):
        rule = arizona[name]
        assert (rule["kind"], rule["entity"], rule["period"]) == ("derived", "Household", "Month")
    assert arizona["medical_deduction"]["dtype"] == "Money"
    eligible = " ".join(
        arizona["medical_expense_participant_is_deduction_eligible"]["versions"][-1]["formula"].split()
    )
    # The elderly-or-disabled binding keeps "with medical expenses" because the
    # same conjunct still requires the expenses to belong to that participant
    # and to exceed the $35 disregard; the deceased and SSI routes are
    # separate disjuncts on their own inputs.
    assert "monthly_combined_out_of_pocket_medical_expenses > medical_expense_disregard" in eligible
    assert (
        "budgetary_unit_includes_elderly_or_disabled_participant_with_medical_expenses "
        "and medical_expenses_belong_to_and_are_billed_to_elderly_or_disabled_participant"
    ) in eligible
    assert "deceased_participant_would_have_been_eligible_in_month_expense_was_billed" in eligible
    assert "participant_is_eligible_for_and_receiving_ssi" in eligible
    # Every branch of the Arizona amount is non-negative, which the identity
    # max(0, d + t - t) = d needs.
    formula = arizona["medical_deduction"]["versions"][-1]["formula"]
    assert "max(0, monthly_combined_out_of_pocket_medical_expenses - medical_expense_disregard)" in formula
    assert "standard_medical_deduction_net_amount" in formula


def _module_path(module_id: str) -> Path:
    jurisdiction, path = module_id.split("#", 1)[0].split(":", 1)
    return ROOT / jurisdiction / f"{path}.yaml"


def _in_scope_modules() -> dict[str, Path]:
    """Every module the spec scopes, plus everything those modules import."""
    spec = yaml.safe_load(SPEC.read_text())
    state = spec["program"].split("/", 1)[0]
    pending = [f"us:{p}" for p in spec["scope"].get("federal") or []]
    pending += [f"{state}:{p}" for p in spec["scope"].get("state") or []]
    seen: dict[str, Path] = {}
    while pending:
        module_id = pending.pop().split("#", 1)[0]
        if module_id in seen:
            continue
        path = _module_path(module_id)
        assert path.is_file(), module_id
        seen[module_id] = path
        payload = yaml.safe_load(path.read_text()) or {}
        pending += [str(item) for item in payload.get("imports") or []]
    return seen


def test_only_the_intended_rules_read_the_bound_slots() -> None:
    readers: dict[str, set[str]] = {slot: set() for slot in BOUND_SLOT_READERS}
    for module_id, path in _in_scope_modules().items():
        for rule in (yaml.safe_load(path.read_text()) or {}).get("rules") or []:
            text = json.dumps(rule.get("versions") or [])
            for slot in BOUND_SLOT_READERS:
                if rule.get("name") != slot and re.search(rf"\b{slot}\b", text):
                    readers[slot].add(module_id)
    assert readers == BOUND_SLOT_READERS


def _engine_binary() -> Path | None:
    configured = os.environ.get("AXIOM_RULES_ENGINE_BIN")
    if configured:
        return Path(configured)
    dependency_root = os.environ.get("AXIOM_DEPENDENCY_ROOT")
    candidates = []
    if dependency_root:
        candidates += [
            Path(dependency_root) / "axiom-rules-engine/target" / p / "axiom-rules-engine"
            for p in ("release", "debug")
        ]
    on_path = shutil.which("axiom-rules-engine")
    if on_path:
        candidates.append(Path(on_path))
    candidates += [
        ROOT.parent / "axiom-rules-engine/target" / p / "axiom-rules-engine"
        for p in ("release", "debug")
    ]
    return next((c for c in candidates if c.is_file()), None)


def _missing(reason: str) -> None:
    if REQUIRE_EXECUTABLE:
        pytest.fail(f"{reason}; AXIOM_REQUIRE_WIRING_EXECUTABLE=1 requires the executable contracts")
    pytest.skip(reason)


@pytest.fixture(scope="module")
def compiled(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path, str]:
    try:
        import axiom_compose as compose
    except ImportError:
        _missing("axiom_compose is not importable")
    binary = _engine_binary()
    if binary is None:
        _missing("no axiom-rules-engine binary (set AXIOM_RULES_ENGINE_BIN)")
    tmp_path = tmp_path_factory.mktemp("az-snap")
    corpus = compose.load_corpus_from_roots([ROOT])
    program = compose.compose(compose.load_spec(SPEC), corpus)
    module = tmp_path / "az-snap.rulespec.yaml"
    module.write_bytes(program.source)
    artifact = tmp_path / "az-snap.compiled.json"
    result = subprocess.run(
        [str(binary), "compile", "--program", str(module), "--output", str(artifact)],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=tmp_path,
        env=dict(os.environ, AXIOM_RULESPEC_REPO_ROOTS=str(ROOT)),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    output = next(
        rule.get("id", rule["name"])
        for rule in json.loads(artifact.read_text())["program"]["derived"]
        if rule["name"] == "snap_excess_medical_deduction_for_net_income"
    )
    return binary, artifact, output


def _record(name: str, entity: str, entity_id: str, value: dict) -> dict:
    return {"name": name, "entity": entity, "entity_id": entity_id, "interval": INTERVAL, "value": value}


def _run(compiled, cases: list[dict], extra_inputs: list[dict] = ()) -> subprocess.CompletedProcess:
    binary, artifact, output = compiled
    inputs: list[dict] = list(extra_inputs)
    relations: list[dict] = []
    for index, case in enumerate(cases):
        household, member = f"h{index}", f"h{index}-m0"
        relations.append({"name": MEMBER_RELATION, "tuple": [member, household], "interval": INTERVAL})
        inputs.append(
            _record(
                "us:statutes/7/2012/j#input.snap_member_is_elderly_or_disabled",
                "Person",
                member,
                {"kind": "bool", "value": case["member_flag"]},
            )
        )
        values = {
            "monthly_combined_out_of_pocket_medical_expenses": {"kind": "decimal", "value": case["expense"]},
            "verified_out_of_pocket_medical_expenses": {"kind": "decimal", "value": case.get("verified", case["expense"])},
            "medical_expenses_belong_to_and_are_billed_to_elderly_or_disabled_participant": {"kind": "bool", "value": case["billed_to_member"]},
            "deceased_participant_would_have_been_eligible_in_month_expense_was_billed": {"kind": "bool", "value": False},
            "remaining_budgetary_unit_participants_are_legally_responsible_for_bill": {"kind": "bool", "value": False},
            "participant_is_eligible_for_and_receiving_ssi": {"kind": "bool", "value": False},
            "ssi_recipient_expenses_incurred_from_later_of_na_application_or_ssi_eligibility_begin_date": {"kind": "bool", "value": False},
        }
        for name, value in values.items():
            inputs.append(_record(f"{AZ_ID}#input.{name}", "Household", household, value))
    request = {
        "mode": "explain",
        "dataset": {"inputs": inputs, "relations": relations},
        "queries": [
            {"entity_id": f"h{i}", "period": PERIOD, "outputs": [output]} for i in range(len(cases))
        ],
    }
    return subprocess.run(
        [str(binary), "run-compiled", "--artifact", str(artifact)],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        timeout=600,
    )


def _deductions(compiled, cases: list[dict]) -> list[Decimal]:
    ran = _run(compiled, cases)
    assert ran.returncode == 0, ran.stderr or ran.stdout
    output = compiled[2]
    results = {r["entity_id"]: r["outputs"][output] for r in json.loads(ran.stdout)["results"]}
    return [Decimal(results[f"h{i}"]["value"]["value"]) for i in range(len(cases))]


# Combined (and verified) expense of an elderly member -> expected Arizona
# deduction (block 2): none at or below the $35 disregard; the $145 SMD from
# $35.01 to $180; actual minus $35 above $180 when all expenses are verified.
SMD_BAND = [
    ("0", "0"),
    ("35", "0"),
    ("35.01", "145"),
    ("100", "145"),
    ("180", "145"),
    ("180.01", "145.01"),
    ("300", "265"),
]


def test_smd_band_through_the_composed_program(compiled) -> None:
    cases = [dict(expense=e, member_flag=True, billed_to_member=True) for e, _ in SMD_BAND]
    assert _deductions(compiled, cases) == [Decimal(expected) for _, expected in SMD_BAND]


def test_elderly_or_disabled_fact_comes_from_the_member_flag(compiled) -> None:
    cases = [
        # Federal member flag only (the Arizona household fact is derived).
        dict(expense="150", member_flag=True, billed_to_member=True),
        # No member flagged: no Arizona deduction.
        dict(expense="150", member_flag=False, billed_to_member=True),
        # Flagged member, but the expenses are not that member's.
        dict(expense="150", member_flag=True, billed_to_member=False),
    ]
    assert _deductions(compiled, cases) == [Decimal("145"), Decimal("0"), Decimal("0")]


@pytest.mark.parametrize(
    "name, value",
    [
        (
            f"{AZ_ID}#input.budgetary_unit_includes_elderly_or_disabled_participant_with_medical_expenses",
            {"kind": "bool", "value": True},
        ),
        (f"{FEDERAL_ID}#input.snap_total_medical_expenses", {"kind": "decimal", "value": "150"}),
        (f"{FEDERAL_ID}#input.household_entitled_to_excess_medical_deduction", {"kind": "bool", "value": True}),
    ],
)
def test_bound_slots_are_no_longer_inputs(compiled, name: str, value: dict) -> None:
    # A caller that still sends a bound slot is rejected instead of silently
    # overriding the binding (the Arizona-fact-only case cannot be expressed).
    case = dict(expense="150", member_flag=True, billed_to_member=True)
    ran = _run(compiled, [case], [_record(name, "Household", "h0", value)])
    assert ran.returncode != 0
    assert "must use an absolute legal RuleSpec reference" in ran.stderr + ran.stdout


def test_partial_verification_above_180_pins_todays_module_behavior(compiled) -> None:
    # Known module defect, rulespec-us#2390: above $180 with only part of the
    # expenses verified, `medical_deduction` returns 0. Block 2 allows the
    # higher deduction, so the $145 SMD (>= $35.01 verified) is expected after
    # the re-encode. This pin then changes from 0 to 145 as an intended change.
    case = dict(expense="300", verified="100", member_flag=True, billed_to_member=True)
    assert _deductions(compiled, [case]) == [Decimal("0")]
