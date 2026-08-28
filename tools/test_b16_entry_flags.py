from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from b16_entry_flags import (
    S232_PRECEDENCE_DECLARED_FACT_SOURCES,
    S232_PRECEDENCE_MEMBERSHIP_FLAGS,
    WITNESS_LINES,
    entry_flags,
)


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
    assert len(S232_PRECEDENCE_DECLARED_FACT_SOURCES) == 10
    assert all(
        source.startswith("us/statute/hts/chapter-99/page-")
        for source in S232_PRECEDENCE_DECLARED_FACT_SOURCES.values()
    )
