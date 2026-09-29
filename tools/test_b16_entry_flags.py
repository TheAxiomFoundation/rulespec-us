from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from b16_entry_flags import WITNESS_LINES, entry_flags


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
        assert not flags["entry_is_forced_labor_301_listed"]
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
