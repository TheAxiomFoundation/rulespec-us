from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    ROOT / "us/policies/medicaid/magi_household_income_pipeline.yaml"
)
COMPANION_PATH = POLICY_PATH.with_suffix(".test.yaml")
PREFIX = "us:policies/medicaid/magi_household_income_pipeline"
RAW_RELATION = "medicaid_household_candidate_row_for_applicant"
RELATION = "medicaid_household_member_of_applicant"
RUNTIME = "medicaid_magi_household_runtime_inputs_valid"

RUNTIME_GATED_PUBLIC_RULES = {
    "medicaid_current_month_cash_support_included",
    "medicaid_projected_annual_cash_support_included",
    "medicaid_current_month_household_pre_disregard_magi",
    "medicaid_projected_annual_household_pre_disregard_magi",
    "medicaid_current_month_federal_poverty_level_amount",
    "medicaid_projected_annual_federal_poverty_level_amount",
    "medicaid_current_month_five_percentage_point_disregard_amount",
    "medicaid_projected_annual_five_percentage_point_disregard_amount",
    "medicaid_selected_budget_period_household_income_as_fraction_of_fpl",
    "medicaid_household_income_after_five_percentage_point_subtraction_as_fraction_of_fpl",
    "five_percentage_point_disregard_changes_overall_magi_eligibility",
    "medicaid_household_eligibility_comparison_income_as_fraction_of_fpl",
    "medicaid_current_month_household_eligibility_comparison_income",
    "medicaid_projected_annual_household_eligibility_comparison_income",
    "eligible_under_highest_applicable_magi_income_standard",
    "medicaid_adult_group_eligible",
    "medicaid_parent_or_caretaker_relative_eligible",
}


def _policy() -> dict:
    return yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))


def _rules(payload: dict) -> dict[str, dict]:
    return {rule["name"]: rule for rule in payload["rules"]}


def _formula(rules: dict[str, dict], name: str) -> str:
    return rules[name]["versions"][0]["formula"]


def _top_level_boolean_operators(formula: str) -> list[str]:
    depth = 0
    operators: list[str] = []
    for match in re.finditer(r"\(|\)|\b(?:and|or)\b", formula):
        token = match.group()
        if token == "(":
            depth += 1
        elif token == ")":
            depth -= 1
        elif depth == 0:
            operators.append(token)
    assert depth == 0
    return operators


def test_executable_relation_slots_match_sums_and_asymmetric_fixture() -> None:
    payload = _policy()
    rules = _rules(payload)
    raw_relation = rules[RAW_RELATION]
    relation = rules[RELATION]

    assert raw_relation["kind"] == "data_relation"
    assert raw_relation["data_relation"] == {
        "predicate": RAW_RELATION,
        "arity": 2,
    }
    assert relation["kind"] == "derived_relation"
    assert relation["derived_relation"] == {
        "arity": 2,
        "source_relation": f"{PREFIX}#relation.{RAW_RELATION}",
        "current_slot": 1,
        "related_slot": 0,
    }
    assert relation["versions"][0]["formula"] == (
        "household_row_candidate_is_the_applicant or "
        "not household_row_candidate_is_the_applicant"
    )

    expected_sums = {
        "internal_current_month_household_pre_disregard_magi": (
            "household_row_current_month_counted_magi",
            "internal_current_month_cash_support_included",
        ),
        "internal_projected_annual_household_pre_disregard_magi": (
            "household_row_projected_annual_counted_magi",
            "internal_projected_annual_cash_support_included",
        ),
    }
    for rule_name, (counted_income, support) in expected_sums.items():
        compact = "".join(_formula(rules, rule_name).split())
        assert compact == (
            f"sum_where({RELATION},{counted_income},"
            "household_row_internal_medicaid_household_member)"
            f"+{support}"
        )

    policy_text = POLICY_PATH.read_text(encoding="utf-8")
    assert "member_of_individuals_household" not in policy_text

    cases = {
        case["name"]: case
        for case in yaml.safe_load(COMPANION_PATH.read_text(encoding="utf-8"))
    }
    case = cases[
        "member_first_relation_orientation_is_observable_and_public_outputs_are_gated"
    ]
    relation_key = f"{PREFIX}#relation.{RAW_RELATION}"
    current_magi_key = (
        f"{PREFIX}#input.household_row_current_month_magi_based_income"
    )
    self_key = f"{PREFIX}#input.household_row_candidate_is_the_applicant"
    rows = case["input"][relation_key]

    # The runner creates raw [candidate, applicant] tuples in list order.
    # These unequal, asymmetric rows make member filtering observable.
    assert [
        (row[current_magi_key], row[self_key]) for row in rows
    ] == [(1330, True), (9876.54, False)]
    assert case["output"][
        f"{PREFIX}#internal_current_month_household_pre_disregard_magi"
    ] == 1330
    assert case["output"][
        f"{PREFIX}#medicaid_current_month_household_pre_disregard_magi"
    ] == 1330
    assert case["output"][f"{PREFIX}#{RUNTIME}"] == "holds"

    probe = cases[
        "executable_relation_slot_reversal_surfaces_nonzero_opposite_side_value"
    ]
    probe_rows = probe["input"][relation_key]
    assert probe["input"][current_magi_key] == 9876.54
    assert [row[current_magi_key] for row in probe_rows] == [1330]
    assert probe["output"][
        f"{PREFIX}#internal_current_month_household_pre_disregard_magi"
    ] == 1330
    assert probe["output"][
        f"{PREFIX}#internal_current_month_relation_orientation_witness"
    ] == 1330

    derived_relation_key = f"{PREFIX}#relation.{RELATION}"
    for fixture in cases.values():
        assert derived_relation_key not in fixture.get("input", {})


def test_self_row_cannot_trigger_dependent_income_exclusion() -> None:
    rules = _rules(_policy())
    excluded = "".join(
        _formula(
            rules,
            "household_row_magi_excluded_from_this_applicant_household",
        ).split()
    )
    assert (
        "andnothousehold_row_candidate_is_the_applicant"
        "andhousehold_row_applicant_expects_to_claim_candidate_as_tax_dependent"
        in excluded
    )

    row_valid = "".join(
        _formula(rules, "household_row_inputs_valid").split()
    )
    assert (
        "nothousehold_row_candidate_is_the_applicantor("
        "household_row_candidate_age==household_row_applicant_age"
        "andnothousehold_row_applicant_expects_to_claim_candidate_as_tax_dependent"
        in row_valid
    )
    assert (
        "household_row_candidate_is_described_in_paragraph_f_2_i"
        "==household_row_applicant_is_described_in_paragraph_f_2_i"
        in row_valid
    )

    cases = {
        case["name"]: case
        for case in yaml.safe_load(COMPANION_PATH.read_text(encoding="utf-8"))
    }
    case = cases["tax_filer_cannot_claim_self_to_exclude_own_magi"]
    assert case["output"][
        f"{PREFIX}#medicaid_household_relation_rows_valid"
    ] == "not_holds"
    assert case["output"][f"{PREFIX}#{RUNTIME}"] == "not_holds"
    assert case["output"][
        f"{PREFIX}#internal_current_month_household_pre_disregard_magi"
    ] == 2000
    assert case["output"][
        f"{PREFIX}#medicaid_current_month_household_pre_disregard_magi"
    ] == 0


def test_family_size_fpl_mismatch_fails_closed_despite_attestation() -> None:
    rules = _rules(_policy())
    scalar_contract = "".join(
        _formula(rules, "medicaid_scalar_contract_valid").split()
    )
    assert (
        "authoritative_fpl_lookup_family_size==applicable_family_size"
        in scalar_contract
    )
    assert (
        "authoritative_fpl_lookup_annual_guideline_amount"
        "==annual_federal_poverty_level_for_applicable_family_size"
        in scalar_contract
    )

    cases = {
        case["name"]: case
        for case in yaml.safe_load(COMPANION_PATH.read_text(encoding="utf-8"))
    }
    case = cases[
        "family_size_fpl_amount_mismatch_with_true_attestation_fails_closed"
    ]
    inputs = case["input"]
    assert inputs[f"{PREFIX}#input.applicable_family_size"] == 1
    assert (
        inputs[
            f"{PREFIX}#input."
            "annual_federal_poverty_level_for_applicable_family_size"
        ]
        == 21640
    )
    assert (
        inputs[
            f"{PREFIX}#input.authoritative_fpl_lookup_family_size"
        ]
        == 1
    )
    assert (
        inputs[
            f"{PREFIX}#input."
            "authoritative_fpl_lookup_annual_guideline_amount"
        ]
        == 15960
    )
    assert (
        inputs[
            f"{PREFIX}#input."
            "applicable_family_size_fpl_year_region_and_budget_correspondence_attested"
        ]
        is True
    )
    assert case["output"][
        f"{PREFIX}#internal_eligible_under_highest_applicable_magi_income_standard"
    ] == "holds"
    assert case["output"][
        f"{PREFIX}#medicaid_scalar_contract_valid"
    ] == "not_holds"
    assert case["output"][f"{PREFIX}#{RUNTIME}"] == "not_holds"
    assert case["output"][
        f"{PREFIX}#eligible_under_highest_applicable_magi_income_standard"
    ] == "not_holds"


def test_parent_caretaker_fact_has_one_canonical_pipeline_slot() -> None:
    payload = _policy()
    rules = _rules(payload)
    input_names = [item["name"] for item in payload["inputs"]]

    duplicates = sorted(
        name for name, count in Counter(input_names).items() if count > 1
    )
    assert duplicates == []
    assert input_names.count(
        "medicaid_applicant_is_parent_or_caretaker_relative"
    ) == 1
    assert "person_is_parent_or_caretaker_relative" not in input_names

    forbidden_consumer_imports = {
        "us:regulations/42-cfr/435/110#parent_or_caretaker_relative_eligible",
        "us:regulations/42-cfr/435/119#adult_group_eligible",
    }
    assert forbidden_consumer_imports.isdisjoint(payload["imports"])

    canonical_symbol = "medicaid_applicant_is_parent_or_caretaker_relative"
    for name in (
        "medicaid_adult_group_eligible",
        "medicaid_parent_or_caretaker_relative_eligible",
    ):
        formula = _formula(rules, name)
        assert canonical_symbol in formula
        assert "person_is_parent_or_caretaker_relative" not in formula

    companion = COMPANION_PATH.read_text(encoding="utf-8")
    forbidden_keys = {
        "us:regulations/42-cfr/435/110#input."
        "person_is_parent_or_caretaker_relative:",
        "us:regulations/42-cfr/435/119#input."
        "person_is_parent_or_caretaker_relative:",
    }
    assert all(key not in companion for key in forbidden_keys)
    assert (
        f"{PREFIX}#input."
        "medicaid_applicant_is_parent_or_caretaker_relative:"
        in companion
    )


def test_every_public_result_is_structurally_fail_closed() -> None:
    payload = _policy()
    rules = _rules(payload)
    public = {
        rule["name"]: rule
        for rule in payload["rules"]
        if rule.get("kind") == "derived"
        and rule.get("metadata", {}).get("private") is not True
    }

    assert set(public) == RUNTIME_GATED_PUBLIC_RULES | {RUNTIME}
    assert (
        rules["medicaid_household_member_for_applicant"]["metadata"]["private"]
        is True
    )
    assert _formula(
        rules, "medicaid_household_member_for_applicant"
    ).splitlines() == [
        "household_row_inputs_valid",
        "and household_row_internal_medicaid_household_member",
    ]
    assert "household_row_is_valid_applicant_member" in _formula(
        rules, "medicaid_household_relation_has_exactly_one_applicant_row"
    )
    assert _formula(rules, RUNTIME).splitlines() == [
        "medicaid_scalar_contract_valid",
        "and medicaid_household_relation_contract_valid",
        "and medicaid_budget_period_contract_valid",
        "and medicaid_cash_support_contract_valid_for_selected_basis",
        "and paragraph_c_routes_to_paragraph_d_household_income",
    ]

    for name in RUNTIME_GATED_PUBLIC_RULES:
        rule = rules[name]
        formula = _formula(rules, name)

        if rule["dtype"] in {"Money", "Rate"}:
            condition, false_branch = formula.rsplit("else:\n", 1)
            assert condition.startswith(f"if {RUNTIME}")
            assert set(_top_level_boolean_operators(condition)) <= {"and"}
            assert false_branch.strip() == "0"
        else:
            assert rule["dtype"] == "Judgment"
            assert formula.splitlines()[0] == RUNTIME
            assert set(_top_level_boolean_operators(formula)) == {"and"}
