"""Budgetary-unit scope contracts for Arizona NA basic categorical eligibility.

FAA5 defines basic categorical eligibility (BCE) on the budgetary unit: it
exists when the unit "does not have a participant meeting certain
disqualification criteria, and all budgetary unit participants receive" a
listed benefit or status, and units that include an SSI participant suspended
for drug and alcohol treatment noncompliance are not in BCE. The module
aggregates per-participant facts over ``member_of_budgetary_unit``
(``arguments: [Person, Household]``), so its unit-level judgments must be
declared on ``Household``.

Companion cases cannot see a wrong declaration here. The harness writes each
relation row against a single query row and orders that pair to match the
output's own declared entity and the compiled direction, so the cases agree
with whichever entity the module declares. The engine resolves aggregation direction from the declared
``arguments`` (axiom-rules-engine #179): a ``Person`` declaration walks from a
participant to its household and evaluates per-participant predicates on the
household id, so data written in the declared ``[Person, Household]`` order
gets vacuous unit judgments.

The static contract checks the declarations. The executable contract compiles
the module with a real engine, requires no relation-orientation warning, and
checks every budgetary unit of one to three participants against the FAA5
text with tuples in declared order. Each unit id also carries decoy
participant facts that flip each of the three aggregate judgments (and BCE
whenever it should hold), so an encoding that read the unit's own facts
instead of its members' fails too.

Until the signed repair tracked in rulespec-us#1440 lands, both contracts are
strict expected failures that cover only ``KnownUnitScopeBug``, which is
raised only while the module still declares a unit judgment on ``Person``
(and, in the executable contract, only while every per-participant judgment is
right). Everything else fails normally: a missing or renamed rule or input, an
engine that cannot be found in CI, a compile or run error, a wrong
per-participant judgment, and any mismatch once the declarations are
repaired. Strict mode makes the repair fail CI until it removes the markers.
"""

from __future__ import annotations

import itertools
import json
import os
import re
import shutil
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

class KnownUnitScopeBug(Exception):
    """The documented rulespec-us#1440 failure: unit judgments on Person."""


KNOWN_UNIT_SCOPE_BUG = pytest.mark.xfail(
    raises=KnownUnitScopeBug,
    strict=True,
    reason=(
        "rulespec-us#1440: the unit judgments are declared on Person; "
        "remove this marker in the signed repair"
    ),
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
# Each listed benefit or status, one input per FAA5 bullet or sub-bullet. The
# first three make up "TANF CA Benefits". A repair that renames or merges any
# of these inputs, or renames a rule above, fails the interface check as an
# ordinary failure, never an expected one; update these tables with it.
TANF_CASH_ASSISTANCE = (
    "participant_receives_tanf_cash_assistance_benefit",
    "participant_is_cash_assistance_eligible_but_no_cash_assistance_benefit_is_paid",
    "participant_has_any_cash_assistance_benefit_recouped_for_overpayment",
)
LISTED = (
    *TANF_CASH_ASSISTANCE,
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


def _formula_identifiers(rules: dict[str, dict]) -> set[str]:
    names: set[str] = set()
    for rule in rules.values():
        for version in rule.get("versions") or []:
            names.update(re.findall(r"[a-z_][a-z0-9_]*", str(version.get("formula"))))
    return names


def _check_interface(rules: dict[str, dict]) -> None:
    """Fail normally (never as the expected failure) on interface drift."""
    relation = rules.get("member_of_budgetary_unit")
    assert relation is not None, "member_of_budgetary_unit relation is missing"
    assert relation["kind"] == "data_relation"
    assert relation["data_relation"]["arity"] == 2
    assert list(relation["data_relation"]["arguments"]) == ["Person", "Household"]
    missing_rules = [
        name for name in (*UNIT_RULES, *PARTICIPANT_RULES) if name not in rules
    ]
    assert not missing_rules, f"renamed or removed rules: {missing_rules}"
    for name in PARTICIPANT_RULES:
        assert rules[name].get("entity") == "Person", name
    identifiers = _formula_identifiers(rules)
    missing_inputs = [name for name in PARTICIPANT_INPUTS if name not in identifiers]
    assert not missing_inputs, f"renamed or merged inputs: {missing_inputs}"


def _raise_if_known_scope_bug(rules: dict[str, dict], detail: str) -> None:
    on_person = [name for name in UNIT_RULES if rules[name].get("entity") == "Person"]
    if on_person:
        raise KnownUnitScopeBug(f"declared on Person: {on_person}; {detail}")


@KNOWN_UNIT_SCOPE_BUG
def test_budgetary_unit_judgments_are_declared_on_the_unit() -> None:
    rules = _rules()
    _check_interface(rules)
    _raise_if_known_scope_bug(rules, "static declaration check")
    for name in UNIT_RULES:
        assert rules[name].get("entity") == "Household", name


def _engine_binary() -> Path | None:
    configured = os.environ.get("AXIOM_RULES_ENGINE_BIN")
    if configured:
        path = Path(configured)
        if not path.is_file():
            pytest.fail(f"AXIOM_RULES_ENGINE_BIN is not a file: {configured}")
        return path
    # The validate workflow builds the pinned engine under
    # AXIOM_DEPENDENCY_ROOT, puts it on PATH and links it beside the
    # checkout; older layouts used _axiom/ inside the checkout. The pinned
    # build is preferred over whatever else is on PATH.
    dependency_root = os.environ.get("AXIOM_DEPENDENCY_ROOT")
    if dependency_root:
        for profile in ("release", "debug"):
            candidate = (
                Path(dependency_root)
                / "axiom-rules-engine"
                / "target"
                / profile
                / "axiom-rules-engine"
            )
            if candidate.is_file():
                return candidate
    on_path = shutil.which("axiom-rules-engine")
    if on_path:
        return Path(on_path)
    for engine_root in (
        ROOT.parent / "axiom-rules-engine",
        ROOT / "_axiom" / "axiom-rules-engine",
    ):
        for profile in ("release", "debug"):
            candidate = engine_root / "target" / profile / "axiom-rules-engine"
            if candidate.is_file():
                return candidate
    if os.environ.get("GITHUB_ACTIONS") == "true":
        pytest.fail("no axiom-rules-engine binary found in CI; the contract must run")
    return None


def _participant_states():
    """Every (disqualified, receives a listed status, drug/alcohol suspended)."""
    return list(itertools.product((False, True), (False, True), (False, True)))


def _units():
    """Every ordered unit of one to three participants.

    A participant who receives a listed status gets exactly one, chosen by a
    cursor that cycles through every listed input across the enumeration.
    """
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


def _expected_participant(member: dict) -> dict[str, bool]:
    listed = member["listed"]
    return {
        PARTICIPANT_RULES[0]: listed is not None
        and listed < len(TANF_CASH_ASSISTANCE),
        PARTICIPANT_RULES[1]: listed is not None,
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


def _member_id(unit_index: int, member_index: int) -> str:
    return f"unit_{unit_index}_participant_{member_index}"


def _request(units: list[list[dict]]) -> dict:
    inputs: list[dict] = []
    relations: list[dict] = []
    queries: list[dict] = []
    unit_outputs = [f"{LEGAL_ID}#{name}" for name in UNIT_RULES]
    participant_outputs = [f"{LEGAL_ID}#{name}" for name in PARTICIPANT_RULES]
    for unit_index, unit in enumerate(units):
        unit_id = f"unit_{unit_index}"
        expected = _expected(unit)
        # Decoy participant facts on the unit id: each flips one aggregate
        # judgment for an encoding that read the unit's facts instead of its
        # members'.
        decoy = {name: False for name in PARTICIPANT_INPUTS}
        decoy[DISQUALIFIED] = expected[UNIT_RULES[0]]
        decoy[DRUG_ALCOHOL_SUSPENDED] = not expected[UNIT_RULES[2]]
        if not expected[UNIT_RULES[1]]:
            decoy[LISTED[unit_index % len(LISTED)]] = True
        for name, value in decoy.items():
            inputs.append(_input(name, "Household", unit_id, value))
        queries.append(
            {"entity_id": unit_id, "period": PERIOD, "outputs": unit_outputs}
        )
        for member_index, member in enumerate(unit):
            member_id = _member_id(unit_index, member_index)
            for name, value in _participant_values(member).items():
                inputs.append(_input(name, "Person", member_id, value))
            relations.append(
                {
                    "name": f"{LEGAL_ID}#relation.member_of_budgetary_unit",
                    "tuple": [member_id, unit_id],
                    "interval": INTERVAL,
                }
            )
            queries.append(
                {
                    "entity_id": member_id,
                    "period": PERIOD,
                    "outputs": participant_outputs,
                }
            )
    return {
        "mode": "explain",
        "dataset": {"inputs": inputs, "relations": relations},
        "queries": queries,
    }


def _outcome(outputs: dict, name: str) -> str:
    return outputs[f"{LEGAL_ID}#{name}"]["outcome"]


@KNOWN_UNIT_SCOPE_BUG
def test_budgetary_unit_judgments_match_faa5_for_every_small_unit(
    tmp_path: Path,
) -> None:
    rules = _rules()
    _check_interface(rules)
    binary = _engine_binary()
    if binary is None:
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
    assert compiled.returncode == 0, (
        f"{binary}: {compiled.stderr or compiled.stdout}"
    )
    compile_log = compiled.stdout + compiled.stderr
    warnings = [code for code in ORIENTATION_WARNINGS if code in compile_log]

    units = _units()
    assert len(units) == 8 + 8**2 + 8**3
    ran = subprocess.run(
        [str(binary), "run-compiled", "--artifact", str(artifact)],
        input=json.dumps(_request(units)),
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert ran.returncode == 0, f"{binary}: {ran.stderr or ran.stdout}"
    results = {
        result["entity_id"]: result["outputs"]
        for result in json.loads(ran.stdout)["results"]
    }

    mismatches: dict[str, int] = {}
    examples = []
    for unit_index, unit in enumerate(units):
        checks = [(f"unit_{unit_index}", _expected(unit))]
        checks += [
            (_member_id(unit_index, member_index), _expected_participant(member))
            for member_index, member in enumerate(unit)
        ]
        for entity_id, expected_by_rule in checks:
            for name, expected in expected_by_rule.items():
                outcome = _outcome(results[entity_id], name)
                if outcome != ("holds" if expected else "not_holds"):
                    mismatches[name] = mismatches.get(name, 0) + 1
                    if len(examples) < 5:
                        examples.append((entity_id, name, unit, outcome))
    detail = (
        f"engine {binary}; orientation warnings: {warnings}; "
        f"mismatches by rule: {mismatches}; examples: {examples}"
    )
    # Per-participant judgments do not depend on the unit declaration, so a
    # mismatch there is never the documented scope bug.
    participant_mismatches = {
        name: count for name, count in mismatches.items() if name in PARTICIPANT_RULES
    }
    if (warnings or mismatches) and not participant_mismatches:
        _raise_if_known_scope_bug(rules, detail)
    assert not warnings and not mismatches, detail
