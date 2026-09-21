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
    "note50-brazil-exemptions.yaml", "note52-reciprocal-exemptions.yaml",
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
    """Match exact 10, rate-line 8, HTS prefix 6, or heading prefix 4.

    The exact-10 branch is load-bearing and deliberate, not an oversight to be
    relaxed into an 8-digit prefix match.  These notes print a code at the width
    they mean: where a list names a 10-digit statistical reporting number it
    names that article and not its siblings under the same subheading, and in
    every such case in notes 50(a)(ii) and 52(b) the enclosing 8-digit
    subheading is NOT separately printed.  U.S. note 52 demonstrates the intent
    internally -- subdivision (b) lists the 10-digit sowing-seed lines
    (1204.00.0010, 1205.10.0010, 1205.90.0010, 1206.00.0031, 0712.90.8550)
    where the HTSUS breaks sowing out as a statistical suffix, while
    subdivision (c) falls back to an 8-digit subheading plus the prose
    qualifier ("Castor oil seeds, for sowing ... subheading 1207.30.00")
    exactly where it does not.  Widening would exempt articles no list names:
    all honey rather than certified-organic honey under 0409.00.00, oil-stock
    and food-grade seed rather than planting seed, alnico and ceramic magnets
    rather than sintered neodymium-iron-boron under 8505.11.00.  It would also
    silently rewrite five already-validated families, including the section 232
    derivative tables that feed entry_is_section_232_covered and the section 201
    table whose only atom is the witness line 8541.42.0010.
    test_sibling_statistical_suffixes_are_not_carved_out enforces this.
    """
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
        # U.S. note 50(a) and U.S. note 52 have the same four-limb shape: two
        # unconditional exclusion lists readable off the printed HTS line, then a
        # general note 6 civil-aircraft list and a pharmaceutical-use list whose
        # operative condition is not a panel fact.  The conditional groups are
        # published so an entry preparer can see them; they are deliberately not
        # part of any scope derivation below.
        "note50_brazil_unconditional_exempt": (
            "note50_brazil_a_ii_membership", "note50_brazil_a_ii_membership_hts10",
            "note50_brazil_a_iii_membership",
        ),
        "note50_brazil_gn6_conditional": ("note50_brazil_gn6_conditional_membership",),
        "note50_brazil_pharmaceutical_conditional": ("note50_brazil_pharmaceutical_conditional_membership",),
        "note52_reciprocal_unconditional_exempt": (
            "note52_reciprocal_b_membership", "note52_reciprocal_b_membership_hts10",
            "note52_reciprocal_c_membership",
        ),
        "note52_reciprocal_gn6_conditional": ("note52_reciprocal_gn6_conditional_membership",),
        "note52_reciprocal_pharmaceutical_conditional": ("note52_reciprocal_pharmaceutical_conditional_membership",),
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
    # Scope of the two overlay charges, on panel-observable facts alone.
    #
    # Both notes are written as exclusion lists against a charging heading, so
    # the generated formulas read "...301_listed and origin_is_X: rate".  The
    # flag therefore has to mean "this HTS line is NOT carved out", which is the
    # complement of the exclusions this repository can actually evaluate:
    #
    #   in scope  <=>  not (unconditional exclusion list  or  section 232 metals)
    #
    # Netted in: note 50(a)(ii) and (a)(iii) / note 52(b) and (c), which turn on
    # the printed HTS line; and the aluminum and steel part of note 50(a)(vi)(1)
    # / note 52(f)(1), reached through the section 232 membership tables that
    # already exist.  That reproduces the witness composition exactly -- it
    # zeroed both charges for lines a (7202.11.10, printed in both notes' own
    # lists) and b (7601.10.30, aluminum) and for no other witness line.
    #
    # Deliberately NOT netted in: the general note 6 civil-aircraft lists
    # (50(a)(iv), 52(d)) and the pharmaceutical-use lists (50(a)(v), 52(e)),
    # because their conditions are entry facts, not line facts -- zeroing a
    # charge for every line that could be an aircraft part would over-exempt.
    # Also not netted in, for want of any membership table: the copper, vehicle,
    # vehicle-part, wood, medium- and heavy-duty vehicle, semiconductor, and
    # patented-pharmaceutical limbs of 50(a)(vi) / 52(f).  Entries covered by
    # those chapter-99 headings are scored in scope here and are a known
    # overstatement, not a claim of coverage.  The precise defect is
    # consumption, not absence: those sector headings are published as
    # chapter-99 rate cells (us/policies/usitc/us-tariff-duty/lines/generated/
    # ch99c.yaml carries 9903.94.01, 9903.76.01, 9903.74.01 and 9903.79.01),
    # and 52(f) additionally has an overlay module for heading 9903.05.90
    # defining forced_labor_metals_heading_applies.  The CBP composition
    # imports neither, and neither is hts_line-keyed, so there is nothing here
    # for this classifier to read.
    #
    # ``country`` is intentionally unused: origin gating (origin_is_brazil,
    # origin_is_forced_labor_*) is applied by the composition, and duplicating it
    # here would double-gate the charge.
    #
    # Naming: entry_is_forced_labor_301_listed carries a frozen misnomer.  It
    # gates U.S. note 52, the reciprocal country annex; the phrase "forced labor"
    # appears nowhere in that note.  The identifier is kept because the
    # composition contract binds to it.
    result.update({
        "entry_is_brazil_301_listed": not (
            result["note50_brazil_unconditional_exempt"] or result["entry_is_section_232_covered"]
        ),
        "entry_is_forced_labor_301_listed": not (
            result["note52_reciprocal_unconditional_exempt"] or result["entry_is_section_232_covered"]
        ),
        # Still not entry-preparable: no membership table exists for the 2024
        # China 301 action or its solar lines.  Declared false, not derived.
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
