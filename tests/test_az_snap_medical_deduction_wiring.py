"""Arizona SNAP: the standard medical deduction reaches the benefit chain.

rulespec-us#952. The benefit reads the 7 CFR 273.10 net-income chain, whose
``snap_excess_medical_deduction_for_net_income`` is

    if household_entitled_to_excess_medical_deduction:
        max(0, snap_total_medical_expenses - snap_medical_expense_threshold)
    else: 0

Both operands were free inputs. The Arizona FAA5 NA Medical Expenses and
Deduction module (block 2) computes the deduction Arizona allows: the $145
Standard Medical Deduction, or the actual amount minus the $35 disregard. The
ProgramSpec binds the two operands so the federal step returns Arizona's
amount unchanged:

    household_entitled_to_excess_medical_deduction
        := medical_expense_participant_is_deduction_eligible
    snap_total_medical_expenses
        := medical_deduction + snap_medical_expense_threshold

The identity max(0, d + t - t) = d holds because ``medical_deduction`` is
never negative (every branch of its formula is 0, $145 or max(0, ...)).

The static contract pins the binding and checks it against the module and
regulation texts it relies on, so a renamed rule or a changed federal formula
fails here first. The executable contract composes the program with
axiom-compose, compiles it with axiom-rules-engine, and checks the deduction
at the boundaries of the SMD band. It needs both tools (``axiom_compose``
importable and an engine binary) and skips without them.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "programs/us-az/snap/fy-2026.yaml"
AZ_MODULE = ROOT / "us-az/policies/des/faa5/na-medical-expenses-and-deduction/medical-deduction.yaml"
FEDERAL = ROOT / "us/regulations/7-cfr/273/10.yaml"
AZ_SCOPE = "policies/des/faa5/na-medical-expenses-and-deduction/medical-deduction"
PERIOD = {"period_kind": "month", "start": "2026-01-01", "end": "2026-01-31"}
INTERVAL = {"start": PERIOD["start"], "end": PERIOD["end"]}


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


def test_binding_matches_the_rules_it_relies_on() -> None:
    federal = _rules(FEDERAL)
    step = federal["snap_excess_medical_deduction_for_net_income"]
    assert step["entity"] == "Household" and step["period"] == "Month"
    assert step["versions"][-1]["formula"].split() == (
        "if household_entitled_to_excess_medical_deduction: "
        "max(0, snap_total_medical_expenses - snap_medical_expense_threshold) else: 0"
    ).split()
    assert "snap_medical_expense_threshold" in federal
    # Neither operand may be defined by an encoded module: the spec would
    # then duplicate a derived rule.
    assert "household_entitled_to_excess_medical_deduction" not in federal
    assert "snap_total_medical_expenses" not in federal

    arizona = _rules(AZ_MODULE)
    for name in ("medical_deduction", "medical_expense_participant_is_deduction_eligible"):
        rule = arizona[name]
        assert (rule["kind"], rule["entity"], rule["period"]) == ("derived", "Household", "Month")
    assert arizona["medical_deduction"]["dtype"] == "Money"
    assert arizona["medical_expense_participant_is_deduction_eligible"]["dtype"] == "Judgment"
    # Every branch of the Arizona amount is non-negative, which the identity
    # max(0, d + t - t) = d needs.
    formula = arizona["medical_deduction"]["versions"][-1]["formula"]
    assert "max(0, monthly_combined_out_of_pocket_medical_expenses - medical_expense_disregard)" in formula
    assert "standard_medical_deduction_net_amount" in formula


def _engine_binary() -> Path | None:
    configured = os.environ.get("AXIOM_RULES_ENGINE_BIN")
    if configured:
        return Path(configured)
    dependency_root = os.environ.get("AXIOM_DEPENDENCY_ROOT")
    candidates = []
    if dependency_root:
        candidates += [Path(dependency_root) / "axiom-rules-engine/target" / p / "axiom-rules-engine" for p in ("release", "debug")]
    on_path = shutil.which("axiom-rules-engine")
    if on_path:
        candidates.append(Path(on_path))
    candidates += [ROOT.parent / "axiom-rules-engine/target" / p / "axiom-rules-engine" for p in ("release", "debug")]
    return next((c for c in candidates if c.is_file()), None)


# Combined and verified expense -> expected Arizona deduction (block 2):
# none at or below the $35 disregard; the $145 SMD from $35.01 to $180;
# actual minus $35 above $180 when all expenses are verified.
SMD_BAND = [
    ("0", "0"),
    ("35", "0"),
    ("35.01", "145"),
    ("100", "145"),
    ("180", "145"),
    ("180.01", "145.01"),
    ("300", "265"),
]


def test_composed_program_carries_the_arizona_deduction(tmp_path: Path) -> None:
    compose = pytest.importorskip("axiom_compose")
    binary = _engine_binary()
    if binary is None:
        pytest.skip("no axiom-rules-engine binary (set AXIOM_RULES_ENGINE_BIN)")

    corpus = compose.load_corpus_from_roots([ROOT])
    program = compose.compose(compose.load_spec(SPEC), corpus)
    module = tmp_path / "az-snap.rulespec.yaml"
    module.write_bytes(program.source)
    artifact = tmp_path / "az-snap.compiled.json"
    compiled = subprocess.run(
        [str(binary), "compile", "--program", str(module), "--output", str(artifact)],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=tmp_path,
        env=dict(os.environ, AXIOM_RULESPEC_REPO_ROOTS=str(ROOT)),
    )
    assert compiled.returncode == 0, compiled.stderr or compiled.stdout
    derived = {
        rule["name"]: rule.get("id", rule["name"])
        for rule in json.loads(artifact.read_text())["program"]["derived"]
    }
    output = derived["snap_excess_medical_deduction_for_net_income"]

    def household(index: int, expense: str, elderly: bool) -> list[dict]:
        values = {
            "monthly_combined_out_of_pocket_medical_expenses": {"kind": "decimal", "value": expense},
            "verified_out_of_pocket_medical_expenses": {"kind": "decimal", "value": expense},
            "budgetary_unit_includes_elderly_or_disabled_participant_with_medical_expenses": {"kind": "bool", "value": elderly},
            "medical_expenses_belong_to_and_are_billed_to_elderly_or_disabled_participant": {"kind": "bool", "value": elderly},
            "deceased_participant_would_have_been_eligible_in_month_expense_was_billed": {"kind": "bool", "value": False},
            "remaining_budgetary_unit_participants_are_legally_responsible_for_bill": {"kind": "bool", "value": False},
            "participant_is_eligible_for_and_receiving_ssi": {"kind": "bool", "value": False},
            "ssi_recipient_expenses_incurred_from_later_of_na_application_or_ssi_eligibility_begin_date": {"kind": "bool", "value": False},
        }
        return [
            {
                "name": f"us-az:{AZ_SCOPE}#input.{name}",
                "entity": "Household",
                "entity_id": f"h{index}",
                "interval": INTERVAL,
                "value": value,
            }
            for name, value in values.items()
        ]

    cases = [(expense, True, expected) for expense, expected in SMD_BAND]
    cases.append(("150", False, "0"))
    inputs = [record for i, (e, elderly, _) in enumerate(cases) for record in household(i, e, elderly)]
    request = {
        "mode": "explain",
        "dataset": {"inputs": inputs, "relations": []},
        "queries": [
            {"entity_id": f"h{i}", "period": PERIOD, "outputs": [output]}
            for i in range(len(cases))
        ],
    }
    ran = subprocess.run(
        [str(binary), "run-compiled", "--artifact", str(artifact)],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert ran.returncode == 0, ran.stderr or ran.stdout
    results = {r["entity_id"]: r["outputs"][output] for r in json.loads(ran.stdout)["results"]}
    got = [Decimal(results[f"h{i}"]["value"]["value"]) for i in range(len(cases))]
    assert got == [Decimal(expected) for _, _, expected in cases]
