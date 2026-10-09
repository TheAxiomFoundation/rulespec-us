"""Florida SNAP: Appendix A-1 limits follow the SNAP household size.

The FL SNAP ProgramSpec composes Florida's ESS Appendix A-1 with the federal
FY 2026 SNAP tables. A-1 keys every table on the free input
`assistance_group_size`, and the federal chain keys on `household_size`.
Before rulespec-us#1183 nothing bound the two, so the A-1 key defaulted to 1
and every A-1 limit read the one-person row: a three-person household saw a
$2,610 "200% gross income limit" instead of $4,442.

Invariants checked, exhaustively over household sizes 1-100:

1. Binding: the spec binds `assistance_group_size := household_size` (Count,
   Household) and `assistance_group_has_elderly_or_disabled_member` to the
   federal elderly-or-disabled determination, and every in-scope Florida state
   module that reads those names gets them from the spec.
2. Differential: A-1's 130% gross and 100% net limits equal the federal
   FY 2026 48-states/DC limits, and A-1's 200% gross limit is twice the federal
   100% net limit, at every size including the per-member extension rows.
3. Monotonicity: every A-1 and federal limit is non-decreasing in size.

The table semantics below mirror the modules' formulas, and each formula's
text is pinned so a change to the encoded shape fails here first rather than
leaving this oracle silently out of date.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "programs/us-fl/snap/fy-2026.yaml"
APPENDIX = (
    ROOT
    / "us-fl/policies/dcf/ess-program-policy-manual"
    / "appendix-a-1-food-assistance-income-eligibility-standards-and-deductions/page-1.yaml"
)
FEDERAL = ROOT / "us/policies/usda/snap/fy-2026-cola/income-eligibility-standards.yaml"
SIZES = range(1, 101)
BOUND_NAMES = {
    "assistance_group_size": "household_size",
    "assistance_group_has_elderly_or_disabled_member": "snap_household_has_elderly_or_disabled_member",
}


@cache
def rules(path: Path) -> dict[str, dict]:
    return {rule["name"]: rule for rule in yaml.safe_load(path.read_text())["rules"]}


def only_version(rule: dict) -> dict:
    (version,) = rule["versions"]
    return version


def appendix_limit(stem: str):
    """A-1 `<stem>(n)`: the listed row, or row 10 plus the per-member add."""
    module = rules(APPENDIX)
    formula = " ".join(only_version(module[stem])["formula"].split())
    assert formula == (
        "if assistance_group_size <= maximum_listed_assistance_group_size: "
        f"{stem}_table[assistance_group_size] else: "
        f"{stem}_table[maximum_listed_assistance_group_size] + "
        "((assistance_group_size - maximum_listed_assistance_group_size) * "
        f"{stem}_each_additional_member_add)"
    ), f"{stem} changed shape; update this oracle"
    table = only_version(module[f"{stem}_table"])["values"]
    add = int(only_version(module[f"{stem}_each_additional_member_add"])["formula"])
    listed = int(only_version(module["maximum_listed_assistance_group_size"])["formula"])
    assert sorted(table) == list(range(1, listed + 1))
    return lambda n: table[n] if n <= listed else table[listed] + (n - listed) * add


def federal_limit(stem: str):
    """Federal `<stem>(n)`: row min(n, 8), plus the per-member add above 8."""
    module = rules(FEDERAL)
    formula = " ".join(only_version(module[stem])["formula"].split())
    assert formula == (
        f"{stem}_table[max(min(household_size, 8), 1)] + "
        f"(max(household_size - 8, 0) * {stem}_additional_member)"
    ), f"{stem} changed shape; update this oracle"
    table = only_version(module[f"{stem}_table"])["values"]
    add = int(only_version(module[f"{stem}_additional_member"])["formula"])
    assert sorted(table) == list(range(1, 9))
    return lambda n: table[min(n, 8)] + max(n - 8, 0) * add


def spec_transformations() -> dict[str, dict]:
    spec = yaml.safe_load(SPEC.read_text())
    return {item["name"]: item for item in spec.get("transformations") or []}


def test_spec_binds_appendix_keys_to_the_snap_household() -> None:
    transformations = spec_transformations()
    size = transformations["assistance_group_size"]
    assert size["pattern"] == "derived_formula"
    assert size["formula"] == "household_size"
    assert size["dtype"] == "Count"  # the engine needs an integer table key
    assert size["entity"] == "Household"
    elderly = transformations["assistance_group_has_elderly_or_disabled_member"]
    assert elderly["pattern"] == "all_of"
    assert elderly["conditions"] == [BOUND_NAMES["assistance_group_has_elderly_or_disabled_member"]]
    assert elderly["entity"] == "Household"


def test_every_in_scope_state_module_reading_a_bound_name_is_covered() -> None:
    spec = yaml.safe_load(SPEC.read_text())
    transformations = spec_transformations()
    readers = 0
    for relative in spec["scope"]["state"]:
        module = rules(ROOT / "us-fl" / f"{relative}.yaml")
        text = yaml.safe_dump(list(module.values()))
        for name in BOUND_NAMES:
            if name in text and name not in module:
                readers += 1
                assert name in transformations, f"{relative} reads unbound {name}"
    assert readers, "no in-scope state module reads the bound names; drop the binding"


def test_appendix_limits_match_the_federal_tables_at_every_size() -> None:
    fl_200 = appendix_limit("monthly_200_percent_gross_income_limit")
    fl_130 = appendix_limit("monthly_130_percent_gross_income_limit")
    fl_100 = appendix_limit("monthly_100_percent_net_income_limit")
    fed_130 = federal_limit("snap_gross_income_limit_130_percent_fpl_48_states_dc")
    fed_100 = federal_limit("snap_net_income_limit_100_percent_fpl_48_states_dc")
    for n in SIZES:
        assert fl_130(n) == fed_130(n), n
        assert fl_100(n) == fed_100(n), n
        assert fl_200(n) == 2 * fed_100(n), n
    # The reported case: a household of three.
    assert (fl_200(3), fl_130(3), fl_100(3)) == (4442, 2888, 2221)


def test_limits_are_non_decreasing_in_household_size() -> None:
    limits = [
        appendix_limit("monthly_200_percent_gross_income_limit"),
        appendix_limit("monthly_130_percent_gross_income_limit"),
        appendix_limit("monthly_100_percent_net_income_limit"),
        appendix_limit("maximum_food_assistance_benefit"),
        federal_limit("snap_gross_income_limit_130_percent_fpl_48_states_dc"),
        federal_limit("snap_net_income_limit_100_percent_fpl_48_states_dc"),
    ]
    for limit in limits:
        values = [limit(n) for n in SIZES]
        assert values == sorted(values)
