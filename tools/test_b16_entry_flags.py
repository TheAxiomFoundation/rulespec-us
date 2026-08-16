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


def test_aluminum_heading_primary_fans_out_to_witness_line():
    assert entry_flags(7601103000, "7601.10.30.00", "CN")["s232_aluminum_primary"]


def test_steel_heading_primary_fans_out_in_chapter_72():
    assert entry_flags(7206100000, "7206.10.00.00", "DE")["s232_steel_primary"]


def test_noncovered_chapter_76_line_is_not_primary():
    flags = entry_flags(7610100000, "7610.10.00.00", "DE")
    assert not flags["s232_aluminum_primary"]
    assert not flags["s232_steel_primary"]


def test_eight_digit_membership_uses_rate_line_prefix():
    assert entry_flags(2203000000, "2203.00.00.30", "CN")["china_301_list3"]
