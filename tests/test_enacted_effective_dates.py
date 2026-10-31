"""Lock the version dates that enacted text fixes for the section 6012 path.

A companion case asserts an answer, so it cannot fail when a rule starts too
early and answers a year the law never reached. Reverting the section 63(c)
amounts to 2018 left every companion case green while section 6012 returned
the 2025 threshold for 2018 filers. These tests fail on that reversion.

Each entry names the act that fixes the date. A rule that gains coverage for
another period needs a new version, and this table needs updating with it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

PL_108_311 = ("2005-01-01", None)  # Pub. L. 108-311 s. 207(26), s. 208
PL_99_514 = ("1987-01-01", None)  # Pub. L. 99-514 s. 102(a), s. 151(a)
PL_119_21 = ("2025-01-01", None)  # Pub. L. 119-21 s. 70102(b), (c)
SECTION_6012_F = ("2018-01-01", "2025-12-31")  # 26 USC 6012(f) lead-in

ENACTED_INTERVALS = {
    "us/statutes/26/7703.yaml": {
        "child_principal_abode_fraction_threshold": PL_108_311,
        "household_cost_fraction_threshold": PL_108_311,
        "spouse_absence_period_months": PL_108_311,
        "taxpayer_married_under_general_rule": PL_108_311,
        "living_apart_child_has_required_abode_and_deduction": PL_108_311,
        "taxpayer_not_considered_married_when_living_apart": PL_108_311,
        "taxpayer_considered_married_after_living_apart_rule": PL_108_311,
    },
    "us/statutes/26/63/c/5.yaml": {
        "dependent_basic_standard_deduction_limitation_applies": PL_99_514,
    },
    "us/statutes/26/63/c.yaml": {
        "head_of_household_basic_standard_deduction_after_2017_base_amount": PL_119_21,
        "other_case_basic_standard_deduction_after_2017_base_amount": PL_119_21,
        "head_of_household_basic_standard_deduction_amount": PL_119_21,
        "other_case_basic_standard_deduction_amount": PL_119_21,
        "basic_standard_deduction_before_dependent_limitation": PL_119_21,
        "basic_standard_deduction": PL_119_21,
        "standard_deduction": PL_119_21,
    },
    "us/statutes/26/6012.yaml": {
        "unmarried_individual_exception_to_return_requirement_under_2018_2025_rule": SECTION_6012_F,
        "joint_return_exception_to_return_requirement_under_2018_2025_rule": SECTION_6012_F,
        "individual_income_tax_return_required_under_2018_2025_rule": SECTION_6012_F,
        "tax_exempt_interest_required_to_be_shown_on_return": SECTION_6012_F,
    },
}

CASES = [
    pytest.param(module, rule, interval, id=f"{module}#{rule}")
    for module, rules in ENACTED_INTERVALS.items()
    for rule, interval in rules.items()
]


def _rule(module: str, name: str) -> dict:
    document = yaml.safe_load((REPO_ROOT / module).read_text(encoding="utf-8"))
    matches = [rule for rule in document["rules"] if rule["name"] == name]
    assert len(matches) == 1, f"{module} has {len(matches)} rules named {name}"
    return matches[0]


@pytest.mark.parametrize(("module", "rule", "interval"), CASES)
def test_rule_covers_only_its_enacted_interval(
    module: str, rule: str, interval: tuple[str, str | None]
) -> None:
    versions = _rule(module, rule)["versions"]
    assert len(versions) == 1, f"{rule} gained a version; review its interval"
    assert (versions[0]["effective_from"], versions[0].get("effective_to")) == interval


def test_all_of_7703_shares_the_enacted_start() -> None:
    document = yaml.safe_load(
        (REPO_ROOT / "us/statutes/26/7703.yaml").read_text(encoding="utf-8")
    )
    dated = {rule["name"] for rule in document["rules"] if rule.get("versions")}
    assert dated == set(ENACTED_INTERVALS["us/statutes/26/7703.yaml"])
