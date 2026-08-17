#!/usr/bin/env python3
"""Classify tariff entries against generated B1.6 incidence memberships."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INCIDENCE_DIR = ROOT / "us/policies/usitc/us-tariff-incidence/generated"
MODULES = (
    "note16-232-steel.yaml", "note18-201-solar.yaml",
    "note19-232-aluminum.yaml", "note20-china-301.yaml",
    "note2aa-122-exemptions.yaml",
)
WITNESS_LINES = {
    "entry_is_line_a": "7202111000", "entry_is_line_b": "7601103000",
    "entry_is_line_c": "9506624040", "entry_is_line_d": "2203000030",
    "entry_is_line_e": "8541420010",
}


def _digits(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 10:
        raise ValueError(f"hts_number must contain exactly 10 digits: {value!r}")
    return digits


@lru_cache(maxsize=1)
def _tables() -> dict[str, set[int]]:
    tables: dict[str, set[int]] = {}
    for filename in MODULES:
        module = yaml.safe_load((INCIDENCE_DIR / filename).read_text())
        for rule in module["rules"]:
            if "membership" not in rule["name"]:
                continue
            tables[rule["name"]] = {
                int(key)
                for version in rule.get("versions", [])
                for key in version.get("values", {})
            }
    return tables


def _member(table: str, rate_line: int, hts_digits: str) -> bool:
    """Match exact 10, rate-line 8, HTS prefix 6, or heading prefix 4."""
    if table.endswith("_membership_hts10"):
        key = int(hts_digits)
    elif table.endswith("_subheading6_membership"):
        key = int(hts_digits[:6])
    elif table.endswith("_heading_membership"):
        key = int(hts_digits[:4])
    else:
        key = int(f"{rate_line:010d}"[:8])
    return key in _tables().get(table, set())


def entry_flags(rate_line: int, hts_number: str, country: str) -> dict[str, bool]:
    if not 0 <= rate_line <= 9_999_999_999:
        raise ValueError("rate_line must be a nonnegative, at-most-10-digit integer")
    hts = _digits(hts_number)
    if not country.strip():
        raise ValueError("country must be nonempty")
    result = {name: hts == digits for name, digits in WITNESS_LINES.items()}
    groups = {
        "s232_steel_primary": (
            "s232_steel_primary_heading_membership",
            "s232_steel_primary_subheading6_membership",
            "s232_steel_primary_membership",
        ),
        "s232_steel_derivative_legacy": ("s232_steel_derivative_legacy_membership", "s232_steel_derivative_legacy_membership_hts10"),
        "s232_steel_derivative_april": ("s232_steel_derivative_april_membership", "s232_steel_derivative_april_membership_hts10"),
        "s232_steel_derivative_equipment": ("s232_steel_derivative_equipment_membership", "s232_steel_derivative_equipment_membership_hts10"),
        "s232_steel_derivative_mobile": ("s232_steel_derivative_mobile_membership",),
        "s232_aluminum_primary": ("s232_aluminum_primary_heading_membership", "s232_aluminum_primary_membership"),
        "s232_aluminum_derivative": ("s232_aluminum_derivative_membership", "s232_aluminum_derivative_membership_hts10"),
        "s201_cspv": ("s201_cspv_membership", "s201_cspv_membership_hts10"),
        "china_301_list1": ("china_301_list1_membership",),
        "china_301_list2": ("china_301_list2_membership",),
        "china_301_list3": ("china_301_list3_membership",),
        "china_301_list4a": ("china_301_list4a_membership", "china_301_list4a_membership_hts10"),
        "s122_unconditional_exempt": ("s122_aa_ii_membership", "s122_aa_ii_membership_hts10", "s122_aa_iii_membership"),
        "s122_gn6_conditional": ("s122_gn6_conditional_membership",),
    }
    result.update({name: any(_member(table, rate_line, hts) for table in tables) for name, tables in groups.items()})
    result.update({
        "entry_is_china_301_list123": any(result[f"china_301_list{i}"] for i in (1, 2, 3)),
        "entry_is_china_301_list4a": result["china_301_list4a"],
        "entry_is_section_232_aluminum": result["s232_aluminum_primary"] or result["s232_aluminum_derivative"],
        "entry_is_section_232_steel": any(result[name] for name in (
            "s232_steel_primary", "s232_steel_derivative_legacy",
            "s232_steel_derivative_april", "s232_steel_derivative_equipment",
            "s232_steel_derivative_mobile",
        )),
        "entry_is_section_201_cspv": result["s201_cspv"],
        "entry_is_section_122_exempt": result["s122_unconditional_exempt"],
    })
    result["entry_is_section_232_covered"] = (
        result["entry_is_section_232_aluminum"] or result["entry_is_section_232_steel"]
    )
    # Follow-up incidence tables are not yet entry-preparable; declared booleans default false.
    result.update({
        "entry_is_brazil_301_listed": False,
        "entry_is_forced_labor_301_listed": False,
        "entry_is_china_301_2024_action": False,
        "entry_is_china_301_solar": False,
    })
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("rate_line", type=int); parser.add_argument("hts_number"); parser.add_argument("country")
    args = parser.parse_args()
    print(json.dumps(entry_flags(args.rate_line, args.hts_number, args.country), sort_keys=True))
