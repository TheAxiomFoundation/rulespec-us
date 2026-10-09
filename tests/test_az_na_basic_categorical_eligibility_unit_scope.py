"""Budgetary-unit scope contracts for Arizona NA basic categorical eligibility.

FAA5 defines basic categorical eligibility (BCE) on the budgetary unit: it
exists when the unit "does not have a participant meeting certain
disqualification criteria, and all budgetary unit participants receive" a
listed benefit or status, and units that include an SSI participant suspended
for drug and alcohol treatment noncompliance are not in BCE. The module
aggregates per-participant facts over ``member_of_budgetary_unit``
(``arguments: [Person, Household]``), so its unit-level judgments must be
declared on ``Household``.

The companion harness types every input ``Entity`` and writes relation rows as
``[related_i, case]``, so under the legacy aggregation direction it passes
whether these judgments are declared on ``Person`` or ``Household``. Engines
that resolve direction from declared ``arguments`` (axiom-rules-engine #179)
make a ``Person`` declaration walk from a participant to its household and
evaluate per-participant predicates on the household id. The static contract
below fails on that declaration under any engine. The executable contract
compiles the module with a real engine and checks every unit of one to three
participants against the FAA5 text, with decoy participant facts on the
household id that a correct encoding never reads.
"""

from __future__ import annotations

import itertools
import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
MODULE_REL = (
    "us-az/policies/des/faa5/na-categorical-eligibility/"
    "basic-categorical-eligibility.yaml"
)
MODULE = ROOT / MODULE_REL
LEGAL_ID = (
    "us-az:policies/des/faa5/na-categorical-eligibility/"
    "basic-categorical-eligibility"
)

UNIT_RULES = (
    "no_budgetary_unit_participant_meets_bce_disqualification_criterion",
    "all_budgetary_unit_participants_receive_listed_bce_benefit_or_status",
    "budgetary_unit_includes_ssi_participant_suspended_for_drug_alcohol_treatment_noncompliance",
    "na_basic_categorical_eligibility",
)
PARTICIPANT_RULES = (
    "participant_receives_tanf_cash_assistance_benefit_for_bce",
    "participant_receives_bce_qualifying_benefit_or_status",
)

DISQUALIFIED = "participant_meets_categorical_eligibility_disqualification_criterion"
DRUG_ALCOHOL_SUSPENDED = (
    "participant_ssi_suspended_for_failure_to_comply_with_drug_and_alcohol_"
    "treatment_requirement"
)
# Each listed benefit or status, one input per FAA5 bullet or sub-bullet.
LISTED = (
    "participant_receives_tanf_cash_assistance_benefit",
    "participant_is_cash_assistance_eligible_but_no_cash_assistance_benefit_is_paid",
    "participant_has_any_cash_assistance_benefit_recouped_for_overpayment",
    "participant_receives_tanf_services",
    "participant_receives_grant_diversion",
    "participant_receives_kinship_foster_care",
    "participant_receives_tribal_tanf",
    "participant_receives_refugee_cash_assistance",
    "participant_receives_bia_general_assistance",
    "participant_receives_ssi",
    "participant_ssi_benefits_are_in_no_pay_status",
    "participant_ssi_benefits_are_in_suspend_status",
)
PARTICIPANT_INPUTS = (DISQUALIFIED, DRUG_ALCOHOL_SUSPENDED, *LISTED)
PERIOD = {"period_kind": "month", "start": "2026-06-01", "end": "2026-06-30"}
INTERVAL = {"start": PERIOD["start"], "end": PERIOD["end"]}
ORIENTATION_WARNINGS = (
    "relation_orientation_mismatch",
    "unknown_relation_argument_entity",
)


def _rules() -> dict[str, dict]:
    payload = yaml.safe_load(MODULE.read_text())
    return {rule["name"]: rule for rule in payload.get("rules") or []}


def test_budgetary_unit_judgments_are_declared_on_the_unit() -> None:
    rules = _rules()
    relation = rules["member_of_budgetary_unit"]
    assert relation["kind"] == "data_relation"
    assert relation["data_relation"]["arity"] == 2
    assert list(relation["data_relation"]["arguments"]) == ["Person", "Household"]
    for name in UNIT_RULES:
        assert rules[name].get("entity") == "Household", name
    for name in PARTICIPANT_RULES:
        assert rules[name].get("entity") == "Person", name


def _engine_binary() -> Path | None:
    configured = os.environ.get("AXIOM_RULES_ENGINE_BIN")
    if configured:
        return Path(configured)
    engine_root = ROOT / "_axiom" / "axiom-rules-engine" / "target"
    for profile in ("release", "debug"):
        candidate = engine_root / profile / "axiom-rules-engine"
        if candidate.is_file():
            return candidate
    return None


def _participant_states():
    """Every combination of the three facts FAA5 BCE turns on.

    ``listed`` is the index of the one listed benefit or status the
    participant receives, or None; cycling the index across participants
    exercises every listed input.
    """
    return list(itertools.product((False, True), (False, True), (False, True)))


def _units():
    states = _participant_states()
    listed_cursor = itertools.cycle(range(len(LISTED)))
    units = []
    for size in (1, 2, 3):
        for members in itertools.product(states, repeat=size):
            units.append(
                [
                    {
                        "disqualified": disqualified,
                        "listed": next(listed_cursor) if receives_listed else None,
                        "drug_alcohol_suspended": suspended,
                    }
                    for disqualified, receives_listed, suspended in members
                ]
            )
    return units


def _expected(unit: list[dict]) -> dict[str, bool]:
    no_disqualified = not any(member["disqualified"] for member in unit)
    all_listed = all(member["listed"] is not None for member in unit)
    includes_suspended = any(member["drug_alcohol_suspended"] for member in unit)
    return {
        UNIT_RULES[0]: no_disqualified,
        UNIT_RULES[1]: all_listed,
        UNIT_RULES[2]: includes_suspended,
        UNIT_RULES[3]: no_disqualified and all_listed and not includes_suspended,
    }


def _input(name: str, entity: str, entity_id: str, value: bool) -> dict:
    return {
        "name": f"{LEGAL_ID}#input.{name}",
        "entity": entity,
        "entity_id": entity_id,
        "interval": INTERVAL,
        "value": {"kind": "bool", "value": value},
    }


def _participant_values(member: dict) -> dict[str, bool]:
    values = {name: False for name in PARTICIPANT_INPUTS}
    values[DISQUALIFIED] = member["disqualified"]
    values[DRUG_ALCOHOL_SUSPENDED] = member["drug_alcohol_suspended"]
    if member["listed"] is not None:
        values[LISTED[member["listed"]]] = True
    return values


def _request(units: list[list[dict]]) -> dict:
    inputs: list[dict] = []
    relations: list[dict] = []
    outputs = [f"{LEGAL_ID}#{name}" for name in UNIT_RULES]
    for unit_index, unit in enumerate(units):
        unit_id = f"unit_{unit_index}"
        expected = _expected(unit)
        # Decoy participant facts on the unit id itself, chosen to flip every
        # unit-level judgment if an encoding read them instead of members'.
        decoy = {name: False for name in PARTICIPANT_INPUTS}
        decoy[DISQUALIFIED] = expected[UNIT_RULES[0]]
        decoy[DRUG_ALCOHOL_SUSPENDED] = not expected[UNIT_RULES[2]]
        if not expected[UNIT_RULES[1]]:
            decoy[LISTED[unit_index % len(LISTED)]] = True
        for name, value in decoy.items():
            inputs.append(_input(name, "Household", unit_id, value))
        for member_index, member in enumerate(unit):
            member_id = f"{unit_id}_participant_{member_index}"
            for name, value in _participant_values(member).items():
                inputs.append(_input(name, "Person", member_id, value))
            relations.append(
                {
                    "name": f"{LEGAL_ID}#relation.member_of_budgetary_unit",
                    "tuple": [member_id, unit_id],
                    "interval": INTERVAL,
                }
            )
    return {
        "mode": "explain",
        "dataset": {"inputs": inputs, "relations": relations},
        "queries": [
            {"entity_id": f"unit_{index}", "period": PERIOD, "outputs": outputs}
            for index in range(len(units))
        ],
    }


def test_budgetary_unit_judgments_match_faa5_for_every_small_unit(
    tmp_path: Path,
) -> None:
    binary = _engine_binary()
    if binary is None or not binary.is_file():
        pytest.skip("no axiom-rules-engine binary (set AXIOM_RULES_ENGINE_BIN)")
    artifact = tmp_path / "basic-categorical-eligibility.json"
    compiled = subprocess.run(
        [
            str(binary),
            "compile",
            "--program",
            str(MODULE),
            "--rulespec-root",
            str(ROOT),
            "--output",
            str(artifact),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert compiled.returncode == 0, compiled.stderr or compiled.stdout
    compile_log = compiled.stdout + compiled.stderr
    for code in ORIENTATION_WARNINGS:
        assert code not in compile_log, compile_log

    units = _units()
    assert len(units) == 8 + 8**2 + 8**3
    ran = subprocess.run(
        [str(binary), "run-compiled", "--artifact", str(artifact)],
        input=json.dumps(_request(units)),
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert ran.returncode == 0, ran.stderr or ran.stdout
    results = {
        result["entity_id"]: result for result in json.loads(ran.stdout)["results"]
    }

    mismatches = []
    for unit_index, unit in enumerate(units):
        outputs = results[f"unit_{unit_index}"]["outputs"]
        for name, expected in _expected(unit).items():
            outcome = outputs[f"{LEGAL_ID}#{name}"]["outcome"]
            if outcome != ("holds" if expected else "not_holds"):
                mismatches.append((unit_index, name, unit, outcome))
    assert not mismatches, mismatches[:5]
