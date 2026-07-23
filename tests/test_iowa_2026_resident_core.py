from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "us-ia"
    / "policies"
    / "income_tax"
    / "2026_full_year_resident_core.yaml"
)


def _module() -> dict:
    return yaml.safe_load(MODULE_PATH.read_text(encoding="utf-8"))


def test_iowa_tax_unit_money_helpers_are_not_public_outputs() -> None:
    payload = _module()
    tax_unit_money_rules = [
        rule
        for rule in payload["rules"]
        if rule.get("entity") == "TaxUnit" and rule.get("dtype") == "Money"
    ]

    assert tax_unit_money_rules
    assert all(
        rule.get("metadata", {}).get("private") is True
        for rule in tax_unit_money_rules
    )

    profile = next(
        rule
        for rule in payload["rules"]
        if rule["name"] == "ia_2026_resident_input_profile_valid"
    )
    assert profile.get("metadata", {}).get("private") is not True
    public_derived_rules = {
        rule["name"]
        for rule in payload["rules"]
        if rule.get("kind") == "derived"
        and rule.get("metadata", {}).get("private") is not True
    }
    assert public_derived_rules == {"ia_2026_resident_input_profile_valid"}
    profile_formula = profile["versions"][0]["formula"]
    assert all(
        f"filing_status == {status}" in profile_formula for status in (0, 1, 3, 4)
    )
    assert "filing_status == 2" not in profile_formula


def test_iowa_deferred_credit_branches_accept_no_caller_legal_results() -> None:
    payload = _module()
    rendered = MODULE_PATH.read_text(encoding="utf-8")
    prohibited_inputs = {
        "ia_2026_unsupported_profile_money_hold",
        "ia_2026_person_tuition_eligibility_hold",
        "ia_2026_person_tuition_qualifying_expenses_hold",
        "ia_2026_person_early_childhood_eligibility_hold",
        "ia_2026_person_early_childhood_qualifying_expenses_hold",
    }

    assert "inputs" not in payload
    assert all(name not in rendered for name in prohibited_inputs)

    rules = {rule["name"]: rule for rule in payload["rules"]}
    assert (
        rules["ia_2026_person_tuition_credit_eligible"]["versions"][0]["formula"]
        == "false"
    )
    assert (
        rules["ia_2026_person_early_childhood_credit_eligible"]["versions"][0][
            "formula"
        ]
        == "false"
    )
    assert (
        rules["ia_2026_person_tuition_credit"]["versions"][0]["formula"]
        == "min(0, 0)"
    )
    assert (
        rules["ia_2026_person_early_childhood_credit"]["versions"][0]["formula"]
        == "min(0, 0)"
    )


def test_iowa_blindness_is_derived_from_raw_measurements() -> None:
    rendered = MODULE_PATH.read_text(encoding="utf-8")

    assert "ia_2026_taxpayer_is_blind" not in rendered
    assert "ia_2026_spouse_is_blind" not in rendered
    assert (
        "ia_2026_taxpayer_better_eye_corrected_central_visual_acuity_numerator"
        in rendered
    )
    assert (
        "ia_2026_taxpayer_better_eye_corrected_central_visual_acuity_denominator"
        in rendered
    )
    assert "ia_2026_taxpayer_widest_visual_field_diameter_degrees" in rendered
