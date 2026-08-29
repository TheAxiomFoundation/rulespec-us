#!/usr/bin/env python3
"""Classify tariff entries against generated B1.6 incidence memberships."""
from __future__ import annotations

import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INCIDENCE_DIR = ROOT / "us/policies/usitc/us-tariff-incidence/generated"
MODULES = (
    "note16-232-steel.yaml", "note18-201-solar.yaml",
    "note19-232-aluminum.yaml", "note20-china-301.yaml",
    "note2aa-122-exemptions.yaml",
    "note50-52-232-sector-precedence.yaml",
)
NOTE16_ALUMINUM_PRECEDENCE_MODULE = "note16-232-aluminum-precedence.yaml"
WITNESS_LINES = {
    "entry_is_line_a": "7202111000", "entry_is_line_b": "7601103000",
    "entry_is_line_c": "9506624040", "entry_is_line_d": "2203000030",
    "entry_is_line_e": "8541420010",
}

# These facts cannot be inferred from an HTS number.  Each name states the
# legal determination entry preparation must supply, and each source points to
# the official Rev. 15 note that makes code incidence alone insufficient.
S232_PRECEDENCE_DECLARED_FACT_SOURCES = {
    "entry_has_at_least_fifteen_percent_aggregate_applicable_listed_metal_weight":
        "us/statute/hts/chapter-99/page-236 (note 16(c))",
    "entry_qualifies_for_note33_vehicle_heading_listed_in_notes_50_52":
        "us/statute/hts/chapter-99/page-519 (note 33(b)-(e))",
    "entry_is_note33_g_automobile_part":
        "us/statute/hts/chapter-99/page-520 and page-521 (note 33(f)-(h))",
    "entry_qualifies_for_note33_certified_auto_part_heading_listed_in_notes_50_52":
        "us/statute/hts/chapter-99/page-525 and page-526 (note 33(p)-(r))",
    "entry_is_note33_auto_part_subject_to_import_adjustment_offset":
        "us/statute/hts/chapter-99/page-553 (note 50(a)(vi)(3))",
    "entry_is_note37_f_completed_kitchen_cabinet_vanity_or_part":
        "us/statute/hts/chapter-99/page-532 (note 37(f)-(g))",
    "entry_is_note38_i_medium_or_heavy_duty_vehicle_part":
        "us/statute/hts/chapter-99/page-535 through page-537 (note 38(h)-(l))",
    "entry_qualifies_for_note38_certified_mhd_part_heading_listed_in_notes_50_52":
        "us/statute/hts/chapter-99/page-536 (note 38(j))",
    "entry_is_note38_mhd_part_subject_to_import_adjustment_offset":
        "us/statute/hts/chapter-99/page-566 (note 52(f)(6))",
    "entry_qualifies_for_note39_heading_9903_79_01":
        "us/statute/hts/chapter-99/page-537 and page-538 (note 39(b)-(d))",
    "entry_is_note40_patented_pharmaceutical_article":
        "us/statute/hts/chapter-99/page-539 and page-540 (note 40(c)(ii), (d)-(h))",
}

# Public RuleSpec input -> local generated-table classification.  The Python
# adapter resolves only these incidence facts; generated RuleSpec derives the
# final Note 50/52 legal precedence Judgment from them and the declared facts
# above.
S232_PRECEDENCE_MEMBERSHIP_FLAGS = {
    "entry_is_s232_note16_c_ii_derivative_aluminum_member":
        "s232_note16_c_ii_derivative_aluminum",
    "entry_is_s232_note16_c_vi_derivative_aluminum_candidate":
        "s232_note16_c_vi_derivative_aluminum_candidate",
    "entry_is_s232_note16_c_ix_derivative_aluminum_candidate":
        "s232_note16_c_ix_derivative_aluminum_candidate",
    "entry_is_s232_note16_metal_chapter": "s232_note16_metal_chapter",
    "entry_is_s232_copper_primary_member": "s232_copper_primary",
    "entry_is_s232_copper_additional_member": "s232_copper_additional",
    "entry_is_s232_note33_vehicle_candidate": "s232_note33_vehicle_candidate",
    "entry_is_s232_note33_auto_part_candidate": "s232_note33_auto_part_candidate",
    "entry_is_s232_note37_softwood_member": "s232_note37_softwood",
    "entry_is_s232_note37_upholstered_wood_furniture_member":
        "s232_note37_upholstered_wood_furniture",
    "entry_is_s232_note37_cabinet_vanity_candidate":
        "s232_note37_cabinet_vanity_candidate",
    "entry_is_s232_note38_mhd_vehicle_member": "s232_note38_mhd_vehicle",
    "entry_is_s232_note38_bus_member": "s232_note38_bus",
    "entry_is_s232_note38_mhd_part_candidate": "s232_note38_mhd_part_candidate",
    "entry_is_s232_note39_semiconductor_candidate":
        "s232_note39_semiconductor_candidate",
    "entry_is_s232_note40_pharmaceutical_candidate":
        "s232_note40_pharmaceutical_candidate",
}

# Section 484(f) statistical changes effective 2026-07-01 split three exact
# 10-digit Note 16 atoms.  The official transfer source is the USITC's
# ``484f_2026-07.pdf`` (pages 61 and 69); each successor below exhausts its
# predecessor's split.  Keeping this mapping at the adapter boundary preserves
# the printed legal table while classifying the current HTS statistical lines.
S232_NOTE16_484F_PREDECESSOR_BY_SUCCESSOR = {
    "8479899510": "8479899599",
    "8479899597": "8479899599",
    "8479909510": "8479909596",
    "8479909591": "8479909596",
    "8708295150": "8708295160",
    "8708295190": "8708295160",
}


def _digits(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 10:
        raise ValueError(f"hts_number must contain exactly 10 digits: {value!r}")
    return digits


@lru_cache(maxsize=1)
def _tables() -> dict[str, set[int]]:
    tables: dict[str, set[int]] = {}
    paths = [INCIDENCE_DIR / filename for filename in MODULES]
    paths += sorted((INCIDENCE_DIR / "note50").glob("page-*.yaml"))
    paths += sorted((INCIDENCE_DIR / "note52").glob("page-*.yaml"))
    for path in paths:
        if path.name.endswith(".test.yaml"):
            continue
        module = yaml.safe_load(path.read_text())
        for rule in module["rules"]:
            if "membership" not in rule["name"]:
                continue
            if rule.get("indexed_by") != "hts_line":
                continue
            tables[rule["name"]] = {
                int(key)
                for version in rule.get("versions", [])
                for key in version.get("values", {})
            }
    return tables


@lru_cache(maxsize=None)
def _note16_aluminum_precedence_tables(entry_day: date) -> dict[str, set[int]]:
    """Select the latest Note-16 aluminum list version active on entry_day."""
    path = INCIDENCE_DIR / NOTE16_ALUMINUM_PRECEDENCE_MODULE
    module = yaml.safe_load(path.read_text())
    tables: dict[str, set[int]] = {}
    for rule in module["rules"]:
        if "membership" not in rule["name"]:
            continue
        active = [
            version
            for version in rule.get("versions", [])
            if date.fromisoformat(version["effective_from"]) <= entry_day
            and (
                not version.get("effective_to")
                or entry_day <= date.fromisoformat(version["effective_to"])
            )
        ]
        if active:
            tables[rule["name"]] = {int(key) for key in active[-1]["values"]}
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


def _note16_member(
    table: str, rate_line: int, hts_digits: str, entry_day: date
) -> bool:
    """Apply a Note-16 table after the official July 2026 statistical splits."""
    tables = _note16_aluminum_precedence_tables(entry_day)
    if table.endswith("_membership_hts10"):
        key = int(hts_digits)
    else:
        key = int(f"{rate_line:010d}"[:8])
    if key in tables.get(table, set()):
        return True
    if entry_day < date(2026, 7, 1):
        return False
    predecessor = S232_NOTE16_484F_PREDECESSOR_BY_SUCCESSOR.get(hts_digits)
    if not predecessor:
        return False
    predecessor_key = (
        int(predecessor)
        if table.endswith("_membership_hts10")
        else int(predecessor[:8])
    )
    return predecessor_key in tables.get(table, set())


def _fragment_member(prefix: str, rate_line: int, hts_digits: str) -> bool:
    """Union all per-page fragments of one legal table family."""
    for table in _tables():
        if not table.startswith(prefix) or not re.search(r"_p\d+$", table):
            continue
        shape = re.sub(r"_p\d+$", "", table)
        if shape.endswith("_membership_hts10"):
            key = int(hts_digits)
        elif shape.endswith("_subheading6_membership"):
            key = int(hts_digits[:6])
        elif shape.endswith("_heading_membership"):
            key = int(hts_digits[:4])
        else:
            key = int(f"{rate_line:010d}"[:8])
        if key in _tables()[table]:
            return True
    return False


def entry_flags(
    rate_line: int,
    hts_number: str,
    country: str,
    *,
    entry_date: str | date,
    entry_has_at_least_fifteen_percent_aggregate_applicable_listed_metal_weight: bool = False,
    entry_qualifies_for_note33_vehicle_heading_listed_in_notes_50_52: bool = False,
    entry_is_note33_g_automobile_part: bool = False,
    entry_qualifies_for_note33_certified_auto_part_heading_listed_in_notes_50_52: bool = False,
    entry_is_note33_auto_part_subject_to_import_adjustment_offset: bool = False,
    entry_is_note37_f_completed_kitchen_cabinet_vanity_or_part: bool = False,
    entry_is_note38_i_medium_or_heavy_duty_vehicle_part: bool = False,
    entry_qualifies_for_note38_certified_mhd_part_heading_listed_in_notes_50_52: bool = False,
    entry_is_note38_mhd_part_subject_to_import_adjustment_offset: bool = False,
    entry_qualifies_for_note39_heading_9903_79_01: bool = False,
    entry_is_note40_patented_pharmaceutical_article: bool = False,
) -> dict[str, bool]:
    if not 0 <= rate_line <= 9_999_999_999:
        raise ValueError("rate_line must be a nonnegative, at-most-10-digit integer")
    hts = _digits(hts_number)
    entry_day = (
        entry_date
        if isinstance(entry_date, date)
        else date.fromisoformat(entry_date)
    )
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
        "s232_copper_primary": ("s232_copper_primary_membership",),
        "s232_copper_additional": ("s232_copper_additional_membership",),
        "s232_note33_vehicle_candidate": ("s232_note33_vehicle_candidate_membership",),
        "s232_note33_auto_part_candidate": (
            "s232_note33_auto_part_candidate_heading_membership",
            "s232_note33_auto_part_candidate_subheading6_membership",
            "s232_note33_auto_part_candidate_membership",
            "s232_note33_auto_part_candidate_membership_hts10",
        ),
        "s232_note37_softwood": ("s232_note37_softwood_membership",),
        "s232_note37_upholstered_wood_furniture": (
            "s232_note37_upholstered_wood_furniture_membership_hts10",
        ),
        "s232_note37_cabinet_vanity_candidate": (
            "s232_note37_cabinet_vanity_candidate_membership_hts10",
        ),
        "s232_note38_mhd_vehicle": (
            "s232_note38_mhd_vehicle_membership",
            "s232_note38_mhd_vehicle_membership_hts10",
        ),
        "s232_note38_bus": ("s232_note38_bus_membership",),
        "s232_note38_mhd_part_candidate": (
            "s232_note38_mhd_part_candidate_membership",
            "s232_note38_mhd_part_candidate_membership_hts10",
        ),
        "s232_note39_semiconductor_candidate": (
            "s232_note39_semiconductor_candidate_subheading6_membership",
        ),
        "s232_note40_pharmaceutical_candidate": (
            "s232_note40_pharmaceutical_candidate_membership_hts10",
        ),
        "s201_cspv": ("s201_cspv_membership", "s201_cspv_membership_hts10"),
        "china_301_list1": ("china_301_list1_membership",),
        "china_301_list2": ("china_301_list2_membership",),
        "china_301_list3": ("china_301_list3_membership",),
        "china_301_list4a": ("china_301_list4a_membership", "china_301_list4a_membership_hts10"),
        "s122_unconditional_exempt": ("s122_aa_ii_membership", "s122_aa_ii_membership_hts10", "s122_aa_iii_membership"),
        "s122_gn6_conditional": ("s122_gn6_conditional_membership",),
    }
    result.update({name: any(_member(table, rate_line, hts) for table in tables) for name, tables in groups.items()})
    note16_aluminum_groups = {
        "s232_note16_c_ii_derivative_aluminum": (
            "s232_note16_c_ii_derivative_aluminum_membership",
            "s232_note16_c_ii_derivative_aluminum_membership_hts10",
        ),
        "s232_note16_c_vi_derivative_aluminum_candidate": (
            "s232_note16_c_vi_derivative_aluminum_candidate_membership",
            "s232_note16_c_vi_derivative_aluminum_candidate_membership_hts10",
        ),
        "s232_note16_c_ix_derivative_aluminum_candidate": (
            "s232_note16_c_ix_derivative_aluminum_candidate_membership",
            "s232_note16_c_ix_derivative_aluminum_candidate_membership_hts10",
        ),
    }
    result.update(
        {
            name: any(
                _note16_member(table, rate_line, hts, entry_day)
                for table in tables
            )
            for name, tables in note16_aluminum_groups.items()
        }
    )
    result["s232_note16_metal_chapter"] = hts[:2] in {"72", "73", "74", "76"}
    result.update(
        {
            public_name: result[local_name]
            for public_name, local_name in S232_PRECEDENCE_MEMBERSHIP_FLAGS.items()
        }
    )
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
    declared_s232_precedence_facts = {
        "entry_has_at_least_fifteen_percent_aggregate_applicable_listed_metal_weight":
            entry_has_at_least_fifteen_percent_aggregate_applicable_listed_metal_weight,
        "entry_qualifies_for_note33_vehicle_heading_listed_in_notes_50_52":
            entry_qualifies_for_note33_vehicle_heading_listed_in_notes_50_52,
        "entry_is_note33_g_automobile_part": entry_is_note33_g_automobile_part,
        "entry_qualifies_for_note33_certified_auto_part_heading_listed_in_notes_50_52":
            entry_qualifies_for_note33_certified_auto_part_heading_listed_in_notes_50_52,
        "entry_is_note33_auto_part_subject_to_import_adjustment_offset":
            entry_is_note33_auto_part_subject_to_import_adjustment_offset,
        "entry_is_note37_f_completed_kitchen_cabinet_vanity_or_part":
            entry_is_note37_f_completed_kitchen_cabinet_vanity_or_part,
        "entry_is_note38_i_medium_or_heavy_duty_vehicle_part":
            entry_is_note38_i_medium_or_heavy_duty_vehicle_part,
        "entry_qualifies_for_note38_certified_mhd_part_heading_listed_in_notes_50_52":
            entry_qualifies_for_note38_certified_mhd_part_heading_listed_in_notes_50_52,
        "entry_is_note38_mhd_part_subject_to_import_adjustment_offset":
            entry_is_note38_mhd_part_subject_to_import_adjustment_offset,
        "entry_qualifies_for_note39_heading_9903_79_01":
            entry_qualifies_for_note39_heading_9903_79_01,
        "entry_is_note40_patented_pharmaceutical_article":
            entry_is_note40_patented_pharmaceutical_article,
    }
    result.update(declared_s232_precedence_facts)
    brazil_unconditional_exempt = any(
        _fragment_member(prefix, rate_line, hts)
        for prefix in (
            "brazil_301_unconditional_exemption_",
            "brazil_301_particular_exemption_",
        )
    )
    forced_common_exempt = any(
        _fragment_member(prefix, rate_line, hts)
        for prefix in (
            "forced_labor_301_common_exemption_",
            "forced_labor_301_particular_exemption_",
        )
    )
    country_code = country.strip().upper()
    eu = {"AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR","HU","IE","IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE"}
    origin_table = ({"GB":"united_kingdom","CH":"switzerland","MY":"malaysia","KH":"cambodia","GT":"guatemala","SV":"el_salvador","AR":"argentina","BD":"bangladesh","TW":"taiwan","ID":"indonesia","EC":"ecuador","JO":"jordan"}.get(country_code) or ("european_union" if country_code in eu else None))
    forced_country_exempt = bool(origin_table) and _fragment_member(
        f"note52_{origin_table}_exemption_", rate_line, hts
    )
    forced_origins = {"AE","AO","AR","AT","AU","BD","BE","BG","BH","BR","BS","CA","CH","CL","CN","CO","CR","CY","CZ","DE","DK","DO","DZ","EC","EE","EG","ES","FI","FR","GB","GR","GT","GY","HK","HN","HR","HU","ID","IE","IL","IN","IQ","IT","JO","JP","KH","KR","KW","KZ","LK","LT","LU","LV","LY","MA","MT","MX","MY","NG","NI","NL","NO","NZ","OM","PE","PH","PK","PL","PT","QA","RO","RU","SA","SE","SG","SI","SK","SV","TH","TR","TT","TW","UY","VE","VN","ZA"}
    result.update({
        "entry_is_brazil_301_listed": country_code == "BR" and not brazil_unconditional_exempt,
        "entry_is_forced_labor_301_listed": country_code in forced_origins and not forced_common_exempt and not forced_country_exempt,
        "entry_is_china_301_2024_action": False,
        "entry_is_china_301_solar": False,
    })
    result["entry_is_brazil_301"] = result["entry_is_brazil_301_listed"]
    result["entry_is_forced_labor_301"] = result["entry_is_forced_labor_301_listed"]
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("rate_line", type=int)
    parser.add_argument("hts_number")
    parser.add_argument("country")
    parser.add_argument("--entry-date", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            entry_flags(
                args.rate_line,
                args.hts_number,
                args.country,
                entry_date=args.entry_date,
            ),
            sort_keys=True,
        )
    )
