from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from b16_entry_flags import (
    S232_PRECEDENCE_DECLARED_FACT_SOURCES,
    S232_PRECEDENCE_MEMBERSHIP_FLAGS,
    S232_NOTE16_484F_PREDECESSOR_BY_SUCCESSOR,
    WITNESS_LINES,
    entry_flags as _entry_flags,
)
from generate_incidence_tables import PROCLAMATION_11021_CITATION


def entry_flags(*args, **kwargs):
    kwargs.setdefault("entry_date", "2026-08-03")
    return _entry_flags(*args, **kwargs)


def dotted(digits: str) -> str:
    return f"{digits[:4]}.{digits[4:6]}.{digits[6:8]}.{digits[8:]}"


def test_five_witness_lines_reproduce_exact_witness_flags():
    for expected, digits in WITNESS_LINES.items():
        flags = entry_flags(int(digits), dotted(digits), "CN")
        assert {name: flags[name] for name in WITNESS_LINES} == {name: name == expected for name in WITNESS_LINES}


def test_five_witness_lines_emit_complete_new_vector():
    expected = {
        "entry_is_line_a": (True, False, False, False, True),
        "entry_is_line_b": (False, False, True, False, False),
        "entry_is_line_c": (False, True, False, False, False),
        "entry_is_line_d": (True, False, False, False, False),
        "entry_is_line_e": (False, False, False, True, False),
    }
    for line_name, digits in WITNESS_LINES.items():
        flags = entry_flags(int(digits), dotted(digits), "CN")
        vector = (
            flags["entry_is_china_301_list123"], flags["entry_is_china_301_list4a"],
            flags["entry_is_section_232_aluminum"], flags["entry_is_section_201_cspv"],
            flags["entry_is_section_122_exempt"],
        )
        assert vector == expected[line_name]
        assert not flags["entry_is_brazil_301_listed"]
        assert flags["entry_is_forced_labor_301"] == flags["entry_is_forced_labor_301_listed"]
        assert flags["entry_is_brazil_301"] == flags["entry_is_brazil_301_listed"]
        assert not any("claimed" in name for name in flags)
        assert not flags["entry_is_china_301_2024_action"]
        assert not flags["entry_is_china_301_solar"]


def test_aluminum_heading_primary_fans_out_to_witness_line():
    assert entry_flags(7601103000, "7601.10.30.00", "CN")["s232_aluminum_primary"]


def test_steel_heading_primary_fans_out_in_chapter_72():
    flags = entry_flags(7206100000, "7206.10.00.00", "DE")
    assert flags["s232_steel_primary"]
    assert flags["entry_is_section_232_steel"]
    assert flags["entry_is_section_232_covered"]


def test_german_list3_line_no_longer_suppresses_section_122():
    flags = entry_flags(203292000, "0203.29.20.00", "DE")
    assert flags["entry_is_china_301_list123"]
    assert not flags["entry_is_section_122_exempt"]
    assert not flags["entry_is_section_232_covered"]
    # Therefore the generated s122 formula reaches its existing rate/window machinery.


def test_noncovered_chapter_76_line_is_not_primary():
    flags = entry_flags(7610100000, "7610.10.00.00", "DE")
    assert not flags["s232_aluminum_primary"]
    assert not flags["s232_steel_primary"]


def test_eight_digit_membership_uses_rate_line_prefix():
    assert entry_flags(2203000000, "2203.00.00.30", "CN")["china_301_list3"]


def test_unconditional_page_fragments_suppress_new_actions():
    assert not entry_flags(901120000, "0901.12.00.00", "BR")["entry_is_brazil_301"]
    assert not entry_flags(901120000, "0901.12.00.00", "CN")["entry_is_forced_labor_301"]


def test_conditional_fragments_do_not_emit_or_apply_claim_inputs():
    flags = entry_flags(8504320000, "8504.32.00.00", "BR")
    assert flags["entry_is_brazil_301"]
    assert not any(
        "301_aircraft" in name or "301_pharma" in name or "claimed" in name
        for name in flags
    )


def test_note50_52_unconditional_sector_memberships_are_code_derived():
    cases = (
        (7206100000, "7206.10.00.00", "entry_is_section_232_covered"),
        (7601103000, "7601.10.30.00", "entry_is_section_232_covered"),
        (7406100000, "7406.10.00.00", "entry_is_s232_copper_primary_member"),
        (8544421000, "8544.42.10.00", "entry_is_s232_copper_additional_member"),
        (4403220100, "4403.22.01.00", "entry_is_s232_note37_softwood_member"),
        (
            9401614011,
            "9401.61.40.11",
            "entry_is_s232_note37_upholstered_wood_furniture_member",
        ),
        (8701240000, "8701.24.00.00", "entry_is_s232_note38_mhd_vehicle_member"),
        (8702206100, "8702.20.61.00", "entry_is_s232_note38_bus_member"),
    )
    for rate_line, hts_number, membership in cases:
        flags = entry_flags(rate_line, hts_number, "BR")
        assert flags[membership]
        assert "entry_is_note50_52_section_232_precedence_exempt" not in flags


def test_note16_derivative_aluminum_lists_are_effective_dated():
    before = entry_flags(
        3701300000,
        "3701.30.00.00",
        "CA",
        entry_date="2026-06-07",
    )
    after = entry_flags(
        3701300000,
        "3701.30.00.00",
        "CA",
        entry_date="2026-06-08",
    )
    candidate = "entry_is_s232_note16_c_vi_derivative_aluminum_candidate"
    assert not before[candidate]
    assert after[candidate]
    assert not after["entry_is_s232_note16_metal_chapter"]
    assert not after[
        "entry_has_at_least_fifteen_percent_aggregate_applicable_listed_metal_weight"
    ]


def test_note16_c_ii_uses_the_april_legal_effect_correction():
    corrected = entry_flags(
        7612100000,
        "7612.10.00.00",
        "BR",
        entry_date="2026-04-06",
    )
    archived_typo = entry_flags(
        7612101000,
        "7612.10.10.00",
        "BR",
        entry_date="2026-04-06",
    )
    member = "entry_is_s232_note16_c_ii_derivative_aluminum_member"
    assert corrected[member]
    assert corrected["entry_is_s232_note16_metal_chapter"]
    assert not archived_typo[member]


def test_note16_april_source_proof_is_targeted_and_does_not_truncate_c_ii():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "us/policies/usitc/us-tariff-incidence/generated/"
        "note16-232-aluminum-precedence.yaml"
    )
    payload = yaml.safe_load(module_path.read_text())
    module = payload["module"]
    assert (
        PROCLAMATION_11021_CITATION
        in module["source_verification"]["corpus_citation_paths"]
    )
    assert "c(ii) continues beyond that retained page" in module["summary"]

    c_ii_rules = [
        rule
        for rule in payload["rules"]
        if rule["name"].startswith(
            "s232_note16_c_ii_derivative_aluminum_membership"
        )
    ]
    assert sum(len(rule["versions"][0]["values"]) for rule in c_ii_rules) == 17
    official_atoms = [
        atom
        for rule in c_ii_rules
        for atom in rule["metadata"]["proof"]["atoms"]
        if atom["source"]["corpus_citation_path"]
        == PROCLAMATION_11021_CITATION
    ]
    assert len(official_atoms) == 1
    assert official_atoms[0]["source"]["excerpt"] == "7612.10.00"
    assert (
        official_atoms[0]["context"]["evidence_role"]
        == "targeted official confirmation"
    )

    for subdivision in ("c_vi", "c_ix"):
        april_atoms = [
            atom
            for rule in payload["rules"]
            if rule["name"].startswith(f"s232_note16_{subdivision}_")
            for atom in rule["metadata"]["proof"]["atoms"]
            if atom["path"] == "versions[0].values"
        ]
        assert april_atoms
        assert all(
            atom["context"]["release"] == "USITC HTS Revision 5"
            for atom in april_atoms
        )


def test_note16_candidate_in_a_metal_chapter_is_code_qualified():
    flags = entry_flags(
        7615103025,
        "7615.10.30.25",
        "BR",
        entry_date="2026-07-24",
    )
    assert flags["entry_is_s232_note16_c_vi_derivative_aluminum_candidate"]
    assert flags["entry_is_s232_note16_metal_chapter"]


def test_note16_july_statistical_successors_inherit_exact_predecessors():
    assert S232_NOTE16_484F_PREDECESSOR_BY_SUCCESSOR == {
        "8479899510": "8479899599",
        "8479899597": "8479899599",
        "8479909510": "8479909596",
        "8479909591": "8479909596",
        "8708295150": "8708295160",
        "8708295190": "8708295160",
    }
    cases = (
        (
            "8479.89.95.10",
            "entry_is_s232_note16_c_ix_derivative_aluminum_candidate",
        ),
        (
            "8479.89.95.97",
            "entry_is_s232_note16_c_ix_derivative_aluminum_candidate",
        ),
        (
            "8479.90.95.10",
            "entry_is_s232_note16_c_ix_derivative_aluminum_candidate",
        ),
        (
            "8479.90.95.91",
            "entry_is_s232_note16_c_ix_derivative_aluminum_candidate",
        ),
        (
            "8708.29.51.50",
            "entry_is_s232_note16_c_vi_derivative_aluminum_candidate",
        ),
        (
            "8708.29.51.90",
            "entry_is_s232_note16_c_vi_derivative_aluminum_candidate",
        ),
    )
    for hts_number, candidate in cases:
        digits = hts_number.replace(".", "")
        before = entry_flags(
            int(digits), hts_number, "BR", entry_date="2026-06-30"
        )
        after = entry_flags(
            int(digits), hts_number, "BR", entry_date="2026-07-01"
        )
        assert not before[candidate]
        assert after[candidate]


def test_note50_52_flag_does_not_broaden_section_232_covered():
    flags = entry_flags(4403220100, "4403.22.01.00", "BR")
    assert flags["entry_is_s232_note37_softwood_member"]
    assert not flags["entry_is_section_232_covered"]
    assert "entry_is_note50_52_section_232_precedence_exempt" not in flags


def test_candidate_membership_requires_its_precise_declared_eligibility_fact():
    cases = (
        (
            8703240100,
            "8703.24.01.00",
            "entry_is_s232_note33_vehicle_candidate",
            "entry_qualifies_for_note33_vehicle_heading_listed_in_notes_50_52",
        ),
        (
            4009320020,
            "4009.32.00.20",
            "entry_is_s232_note33_auto_part_candidate",
            "entry_is_note33_g_automobile_part",
        ),
        (
            9403409060,
            "9403.40.90.60",
            "entry_is_s232_note37_cabinet_vanity_candidate",
            "entry_is_note37_f_completed_kitchen_cabinet_vanity_or_part",
        ),
        (
            4009420020,
            "4009.42.00.20",
            "entry_is_s232_note38_mhd_part_candidate",
            "entry_is_note38_i_medium_or_heavy_duty_vehicle_part",
        ),
        (
            8471500000,
            "8471.50.00.00",
            "entry_is_s232_note39_semiconductor_candidate",
            "entry_qualifies_for_note39_heading_9903_79_01",
        ),
        (
            2922292700,
            "2922.29.27.00",
            "entry_is_s232_note40_pharmaceutical_candidate",
            "entry_is_note40_patented_pharmaceutical_article",
        ),
    )
    for rate_line, hts_number, candidate, fact in cases:
        candidate_only = entry_flags(rate_line, hts_number, "BR")
        assert candidate_only[candidate]
        assert not candidate_only[fact]

        qualified = entry_flags(rate_line, hts_number, "BR", **{fact: True})
        assert qualified[candidate]
        assert qualified[fact]
        assert not qualified["entry_is_section_232_covered"]


def test_declared_candidate_fact_does_not_turn_a_neighboring_code_into_a_member():
    cases = (
        (
            8703250100,
            "8703.25.01.00",
            "entry_is_s232_note33_vehicle_candidate",
            "entry_qualifies_for_note33_vehicle_heading_listed_in_notes_50_52",
        ),
        (
            4009320021,
            "4009.32.00.21",
            "entry_is_s232_note33_auto_part_candidate",
            "entry_is_note33_g_automobile_part",
        ),
        (
            9403409061,
            "9403.40.90.61",
            "entry_is_s232_note37_cabinet_vanity_candidate",
            "entry_is_note37_f_completed_kitchen_cabinet_vanity_or_part",
        ),
        (
            4009420021,
            "4009.42.00.21",
            "entry_is_s232_note38_mhd_part_candidate",
            "entry_is_note38_i_medium_or_heavy_duty_vehicle_part",
        ),
        (
            8471600000,
            "8471.60.00.00",
            "entry_is_s232_note39_semiconductor_candidate",
            "entry_qualifies_for_note39_heading_9903_79_01",
        ),
        (
            2922292701,
            "2922.29.27.01",
            "entry_is_s232_note40_pharmaceutical_candidate",
            "entry_is_note40_patented_pharmaceutical_article",
        ),
    )
    for rate_line, hts_number, candidate, fact in cases:
        flags = entry_flags(rate_line, hts_number, "BR", **{fact: True})
        assert not flags[candidate]
        assert flags[fact]
        assert "entry_is_note50_52_section_232_precedence_exempt" not in flags


def test_non_code_declared_sector_eligibility_facts_are_explicit_and_sourced():
    cases = (
        "entry_qualifies_for_note33_certified_auto_part_heading_listed_in_notes_50_52",
        "entry_is_note33_auto_part_subject_to_import_adjustment_offset",
        "entry_qualifies_for_note38_certified_mhd_part_heading_listed_in_notes_50_52",
        "entry_is_note38_mhd_part_subject_to_import_adjustment_offset",
    )
    for fact in cases:
        unqualified = entry_flags(3926909990, "3926.90.99.90", "BR")
        assert not unqualified[fact]
        qualified = entry_flags(3926909990, "3926.90.99.90", "BR", **{fact: True})
        assert qualified[fact]
        assert "entry_is_note50_52_section_232_precedence_exempt" not in qualified
        assert "us/statute/hts/chapter-99/page-" in S232_PRECEDENCE_DECLARED_FACT_SOURCES[fact]


def test_python_emits_only_primitive_precedence_inputs_not_the_final_judgment():
    flags = entry_flags(7406100000, "7406.10.00.00", "BR")
    assert set(S232_PRECEDENCE_MEMBERSHIP_FLAGS) <= flags.keys()
    assert set(S232_PRECEDENCE_DECLARED_FACT_SOURCES) <= flags.keys()
    assert "entry_is_note50_52_section_232_precedence_exempt" not in flags


def test_every_declared_sector_fact_has_an_official_note_source():
    assert len(S232_PRECEDENCE_DECLARED_FACT_SOURCES) == 11
    assert all(
        source.startswith("us/statute/hts/chapter-99/page-")
        for source in S232_PRECEDENCE_DECLARED_FACT_SOURCES.values()
    )
