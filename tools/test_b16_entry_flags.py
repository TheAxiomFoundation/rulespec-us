from pathlib import Path
import sys

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from b16_entry_flags import WITNESS_LINES, _tables, entry_flags
from generate_incidence_tables import PARTIAL_CODES, partial_rules
from generate_schedule_compositions import (
    COMPONENT_RULES,
    DECLARED_BOOLEAN_INPUTS,
    WITNESS_PATH,
    formula_dependencies,
)

OVERLAY_DIR = Path(__file__).resolve().parents[1] / (
    "us/policies/usitc/us-tariff-duty/overlays/section-301"
)

# The witness composition zeroed the note 50 and note 52 charges for lines a and
# b only.  generate_schedule_compositions rewrites those two hand-written limbs
# into "if entry_is_..._301_listed and origin_is_...", so the generated formula
# only means what the witness meant if the scope flags are false for exactly a
# and b.  This is the contract, not an observation of the current derivation.
WITNESS_OVERLAY_SCOPE = {
    "entry_is_line_a": False,
    "entry_is_line_b": False,
    "entry_is_line_c": True,
    "entry_is_line_d": True,
    "entry_is_line_e": True,
}

NOTE50_UNCONDITIONAL = ("note50_brazil_a_ii_membership", "note50_brazil_a_iii_membership")
NOTE52_UNCONDITIONAL = ("note52_reciprocal_b_membership", "note52_reciprocal_c_membership")

# U.S. note 52(i) is one heading, 9903.05.95.  U.S. note 52(j) is thirteen
# subdivisions, (j)(1) through (j)(13) -- United Kingdom, European Union,
# Switzerland, Malaysia, Cambodia, Guatemala, El Salvador, Argentina,
# Bangladesh, Taiwan, Indonesia, Ecuador, Jordan -- carried by headings
# 9903.05.96, 9903.05.97, 9903.05.98 and 9903.05.99 through 9903.06.21.  An
# earlier revision of the note 52 summary described 52(j) as the "United
# Kingdom and European Union lists", which is two of the thirteen.  These are
# the exact identifiers the per-country overlay modules negate; no module
# defines any of them, so every one is an overlay input.
NOTE_52_I_OVERLAY_GATE = "article_described_in_heading_9903_05_95"
NOTE_52_J_OVERLAY_GATES = (
    "article_described_in_heading_9903_05_96",
    "article_described_in_heading_9903_05_97",
    "article_described_in_heading_9903_05_98",
    "article_described_in_headings_9903_05_99_through_9903_06_01",
    "article_described_in_headings_9903_06_02_through_9903_06_03",
    "article_described_in_headings_9903_06_04_through_9903_06_06",
    "article_described_in_headings_9903_06_07_through_9903_06_09",
    "article_described_in_headings_9903_06_10_through_9903_06_11",
    "article_described_in_headings_9903_06_12_through_9903_06_13",
    "article_described_in_headings_9903_06_14_through_9903_06_15",
    "article_described_in_headings_9903_06_16_through_9903_06_17",
    "article_described_in_headings_9903_06_18_through_9903_06_19",
    "article_described_in_headings_9903_06_20_through_9903_06_21",
)
NOTE_52_UNCONSUMED_OVERLAY_GATES = (NOTE_52_I_OVERLAY_GATE, *NOTE_52_J_OVERLAY_GATES)

# (10-digit table, its 8-digit sibling table, the group flag, the scope flag).
PRINTED_TEN_DIGIT = (
    ("note50_brazil_a_ii_membership_hts10", "note50_brazil_a_ii_membership",
     "note50_brazil_unconditional_exempt", "entry_is_brazil_301_listed"),
    ("note52_reciprocal_b_membership_hts10", "note52_reciprocal_b_membership",
     "note52_reciprocal_unconditional_exempt", "entry_is_forced_labor_301_listed"),
)


def dotted(digits: str) -> str:
    return f"{digits[:4]}.{digits[4:6]}.{digits[6:8]}.{digits[8:]}"


def probe(rate_line_prefix8: int, country: str = "BR") -> dict[str, bool]:
    """Flags for a synthetic 10-digit line under an 8-digit membership key."""
    digits = f"{rate_line_prefix8:08d}00"
    return entry_flags(int(digits), dotted(digits), country)


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
        assert flags["entry_is_brazil_301_listed"] is WITNESS_OVERLAY_SCOPE[line_name]
        assert flags["entry_is_forced_labor_301_listed"] is WITNESS_OVERLAY_SCOPE[line_name]
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


def test_every_table_the_overlay_groups_name_actually_loads():
    """A typo in a group's table tuple degrades silently to "never a member",
    which would pin a scope flag permanently true. Pin the names and require
    each table to be non-empty."""
    expected = (
        "note50_brazil_a_ii_membership", "note50_brazil_a_ii_membership_hts10",
        "note50_brazil_a_iii_membership", "note50_brazil_gn6_conditional_membership",
        "note50_brazil_pharmaceutical_conditional_membership",
        "note52_reciprocal_b_membership", "note52_reciprocal_b_membership_hts10",
        "note52_reciprocal_c_membership", "note52_reciprocal_gn6_conditional_membership",
        "note52_reciprocal_pharmaceutical_conditional_membership",
    )
    assert not [name for name in expected if not _tables().get(name)]


def test_witness_line_a_leaves_scope_through_the_printed_note_lists():
    """7202.11.10 ferrosilicon is printed in note 50(a)(ii) and note 52(b)
    themselves; it is not a section 232 line. Both mechanisms must stay live."""
    flags = entry_flags(7202111000, "7202.11.10.00", "BR")
    assert flags["note50_brazil_unconditional_exempt"]
    assert flags["note52_reciprocal_unconditional_exempt"]
    assert not flags["entry_is_section_232_covered"]
    assert not flags["entry_is_brazil_301_listed"]
    assert not flags["entry_is_forced_labor_301_listed"]


def test_witness_line_b_leaves_scope_through_the_section_232_metals_limb():
    """7601.10.30 unwrought aluminum is on neither note's printed list; it is
    carved out only by note 50(a)(vi)(1) / note 52(f)(1), which this repository
    reaches through the section 232 membership tables."""
    flags = entry_flags(7601103000, "7601.10.30.00", "BR")
    assert not flags["note50_brazil_unconditional_exempt"]
    assert not flags["note52_reciprocal_unconditional_exempt"]
    assert flags["entry_is_section_232_covered"]
    assert not flags["entry_is_brazil_301_listed"]
    assert not flags["entry_is_forced_labor_301_listed"]


def test_note_50_and_note_52_scope_flags_are_independently_sourced():
    """The two notes are distinct instruments, so a line the reciprocal annex
    excludes but the Brazil note does not must flip only the note-52 flag. This
    is what would break if both groups were wired to the same tables."""
    tables = _tables()
    note50 = set().union(*(tables[name] for name in NOTE50_UNCONDITIONAL))
    note52 = set().union(*(tables[name] for name in NOTE52_UNCONDITIONAL))
    assert note50 != note52
    for key in sorted(note52 - note50):
        flags = probe(key)
        if flags["entry_is_section_232_covered"]:
            continue
        assert flags["note52_reciprocal_unconditional_exempt"]
        assert not flags["note50_brazil_unconditional_exempt"]
        assert flags["entry_is_forced_labor_301_listed"] is False
        assert flags["entry_is_brazil_301_listed"] is True
        break
    else:
        pytest.fail("no note-52-only exclusion outside the section 232 tables")


def test_conditional_exclusions_do_not_zero_the_scope_flags():
    """General note 6 civil aircraft (50(a)(iv), 52(d)) and pharmaceutical use
    (50(a)(v), 52(e)) turn on facts no tariff-line panel carries. A line that
    appears only on a conditional list must stay in scope on HTS line alone, so
    that the entry-level condition is decided by an entry-level fact."""
    tables = _tables()
    cases = (
        ("note50_brazil_gn6_conditional_membership", "note50_brazil_gn6_conditional",
         NOTE50_UNCONDITIONAL, "entry_is_brazil_301_listed"),
        ("note50_brazil_pharmaceutical_conditional_membership", "note50_brazil_pharmaceutical_conditional",
         NOTE50_UNCONDITIONAL, "entry_is_brazil_301_listed"),
        ("note52_reciprocal_gn6_conditional_membership", "note52_reciprocal_gn6_conditional",
         NOTE52_UNCONDITIONAL, "entry_is_forced_labor_301_listed"),
        ("note52_reciprocal_pharmaceutical_conditional_membership", "note52_reciprocal_pharmaceutical_conditional",
         NOTE52_UNCONDITIONAL, "entry_is_forced_labor_301_listed"),
    )
    for table, group, unconditional, flag in cases:
        only = tables[table].difference(*(tables[name] for name in unconditional))
        assert only, f"{table} adds nothing beyond the unconditional lists"
        for key in sorted(only):
            flags = probe(key)
            if flags["entry_is_section_232_covered"]:
                continue
            assert flags[group]
            assert flags[flag] is True
            break
        else:
            pytest.fail(f"every {table} line is masked by the section 232 tables")


def test_printed_statistical_lines_are_carved_out_on_all_ten_digits():
    """Every 10-digit line notes 50(a)(ii) and 52(b) actually print must leave
    scope, matched on the full reporting number rather than on its subheading."""
    tables = _tables()
    for hts10_table, _eight, group, scope in PRINTED_TEN_DIGIT:
        assert tables[hts10_table]
        for key in sorted(tables[hts10_table]):
            digits = f"{key:010d}"
            flags = entry_flags(key, dotted(digits), "BR")
            assert flags[group], digits
            assert flags[scope] is False, digits


def test_sibling_statistical_suffixes_are_not_carved_out():
    """The source names one statistical reporting number and not its siblings.

    Where notes 50(a)(ii) and 52(b) print a 10-digit line they never also print
    the enclosing 8-digit subheading, so a different statistical suffix under
    that subheading is a different article and stays in scope. Note 52 shows the
    precision is deliberate: subdivision (b) prints the 10-digit sowing-seed
    lines where the HTSUS breaks sowing out, and subdivision (c) falls back to
    an 8-digit subheading with a prose "for sowing" qualifier where it does not.
    Widening these atoms to their subheading would exempt articles no list
    names, so this test is the guard on that encoding decision.
    """
    tables = _tables()
    for hts10_table, eight_table, group, scope in PRINTED_TEN_DIGIT:
        checked = 0
        for key in sorted(tables[hts10_table]):
            subheading = key // 100
            # If a future revision also prints the 8-digit subheading, siblings
            # legitimately become exempt and this decision must be revisited.
            assert subheading not in tables[eight_table], key
            sibling = next(
                subheading * 100 + suffix
                for suffix in range(100)
                if subheading * 100 + suffix not in tables[hts10_table]
            )
            digits = f"{sibling:010d}"
            flags = entry_flags(sibling, dotted(digits), "BR")
            if flags["entry_is_section_232_covered"]:
                continue
            assert not flags[group], digits
            assert flags[scope] is True, digits
            checked += 1
        assert checked, f"{hts10_table}: every sibling is masked by section 232"


def test_note_50_transaction_fact_residual_is_still_open():
    """The note 50 summary declares an OPEN residual: nothing applies the
    heading 9903.05.02 in-transit window or the heading 9903.05.08 / 9903.05.09
    donation and informational-material exceptions, so entries that qualify are
    over-charged. A disclosure of absence is only honest while it is true.

    Each assertion below fails on exactly the event that would make the prose
    stale -- someone giving Brazil the entry-level rule it lacks, someone adding
    the note 50 in-transit fact, or note 52 losing the counterpart the summary
    contrasts against. None of them restates the prose; they pin the structure
    the prose reports. If one fails, encode the exception AND rewrite
    SUMMARY_NOTES["brazil-50"]; do not delete the assertion.
    """
    assert "brazil_section_301_entry_component_rate" not in COMPONENT_RULES
    assert "forced_labor_section_301_entry_component_rate" in COMPONENT_RULES
    assert [name for name in DECLARED_BOOLEAN_INPUTS if "in_transit" in name] == [
        "entry_loaded_and_in_transit_before_july_24_2026"
    ]


def test_note_52_carve_outs_are_encoded_at_entry_level_and_absent_from_the_total():
    """The note 52 summary classifies its subdivisions per limb: 52(a)'s
    chapter 98 and accompanied-baggage exclusions and the 52(g)/(h) USMCA
    carve-outs ENCODED but consumed only by the entry rate, and 52(i)/(j)
    named in the overlay modules but consumed by nothing at all. An earlier
    revision of that summary called the USMCA carve-outs
    unencoded "(country, article)" rules needing a membership table; they are
    neither, and the composition has expressed them since 2026-07-24.

    Every assertion below is a structural fact about the composition, not a
    restatement of the prose. Each fails on exactly the event that would make
    the corrected text stale -- someone moving the USMCA or chapter 98
    exception onto the panel projection, someone making the total consume the
    entry rate, or someone finally wiring the CAFTA-DR identifier or any of the
    thirteen 52(j) country identifiers into the composition. If one fails,
    rewrite SUMMARY_NOTES["reciprocal-52"] to match the new structure; do not
    delete the assertion.
    """
    witness = yaml.safe_load(WITNESS_PATH.read_text())
    by_name = {rule["name"]: rule for rule in witness["rules"]}
    names = set(by_name)
    entry_rule = "forced_labor_section_301_entry_component_rate"
    panel_rule = "forced_labor_section_301_component_rate"
    assert {entry_rule, panel_rule} <= set(COMPONENT_RULES)
    entry_deps = formula_dependencies(by_name[entry_rule], names)
    panel_deps = formula_dependencies(by_name[panel_rule], names)

    # 52(g)/(h) and the 52(a) chapter 98 exclusion are encoded, and they turn on
    # declared entry facts rather than on any hts_line membership table.
    for exception in (
        "forced_labor_usmca_exception_applies",
        "forced_labor_chapter_98_exclusion_applies",
    ):
        assert exception in names
        assert exception in entry_deps
        assert exception not in panel_deps
    for declared in (
        "entry_is_entered_free_of_duty_under_usmca",
        "entry_is_personal_use_accompanied_baggage",
    ):
        assert declared in DECLARED_BOOLEAN_INPUTS

    # ...and the panel-facing total sums the projection, not the entry rate, so
    # none of those exceptions moves a panel result.
    total_deps = formula_dependencies(by_name["us_tariff_total_ad_valorem_rate"], names)
    assert panel_rule in total_deps
    assert entry_rule not in total_deps

    # 52(i) CAFTA-DR and every one of the thirteen 52(j) country limbs reach no
    # entry at all: their heading identifiers are named only in the overlay
    # modules and are neither composition rules, nor declared entry inputs, nor
    # referenced by any composition formula.
    for gate in NOTE_52_UNCONSUMED_OVERLAY_GATES:
        assert gate not in names
        assert gate not in DECLARED_BOOLEAN_INPUTS
        consumers = sorted(
            name for name, rule in by_name.items()
            if formula_dependencies(rule, {gate})
        )
        assert not consumers, (gate, consumers)


def test_every_note_52_i_and_j_identifier_is_an_unconsumed_overlay_input():
    """Pin the exact 52(i) + 52(j) identifier inventory, module by module.

    test_note_52_carve_outs_... asserts that none of the fourteen reaches the
    composition. That assertion is vacuous for a name that exists nowhere, so a
    typo in the tuple would silently pass and would let the summary understate
    the annex again. This test closes that hole from the other side: every one
    of the fourteen must actually be named by at least one section-301 overlay
    module, none may be DEFINED by any module (they are overlay inputs, not
    derivations), and no module that names one may be imported by the CBP
    composition. 52(j) must stay thirteen limbs, matching (j)(1) through
    (j)(13) in the note.
    """
    assert len(NOTE_52_J_OVERLAY_GATES) == 13
    assert len(set(NOTE_52_UNCONSUMED_OVERLAY_GATES)) == 14

    modules = sorted(
        path for path in OVERLAY_DIR.glob("*.yaml")
        if not path.name.endswith(".test.yaml")
    )
    assert modules, OVERLAY_DIR
    texts = {path: path.read_text() for path in modules}

    witness = yaml.safe_load(WITNESS_PATH.read_text())
    imported = {
        target.split("#", 1)[0].rsplit("/", 1)[-1] for target in witness["imports"]
    }

    naming_modules = set()
    for gate in NOTE_52_UNCONSUMED_OVERLAY_GATES:
        hits = [path for path, text in texts.items() if gate in text]
        assert hits, gate
        for path in hits:
            assert f"- name: {gate}" not in texts[path], (gate, path.name)
            assert path.stem not in imported, (gate, path.name)
        naming_modules.update(hits)

    # SUMMARY_NOTES["reciprocal-52"] says "Twenty per-country overlay modules".
    # If the annex grows or shrinks a module, that sentence is stale too.
    assert len(naming_modules) == 20, sorted(path.name for path in naming_modules)


def test_no_rule_applies_a_note_50_or_note_52_reduced_duty_base():
    """U.S. notes 50(a)(i) and 52(a) both prescribe reduced duty bases for
    entries under 9802.00.40, 9802.00.50, 9802.00.60 and 9802.00.80, and
    neither is applied. The summaries disclose that as an open functional gap,
    so the disclosure must fail the moment it stops being true.

    The contrast is inside the same composition: U.S. note 51(a) prescribes the
    identical bases for section 338 and they ARE encoded, so the absence here
    cannot be defended as a modelling convention. The 9802 fact itself is
    declared and reaches note 52 only as the negation that switches the
    chapter 98 exclusion OFF, which is precisely what leaves an excepted 9802
    entry on a full-customs-value rate.
    """
    witness = yaml.safe_load(WITNESS_PATH.read_text())
    by_name = {rule["name"]: rule for rule in witness["rules"]}
    names = set(by_name)

    # Section 338 has the only reduced-base rule in the composition, and it is
    # consumed by its own entry rate.
    assert {name for name in names if "reduced_duty_base" in name} == {
        "section_338_reduced_duty_base_applies"
    }
    assert "section_338_reduced_duty_base_applies" in formula_dependencies(
        by_name["section_338_entry_component_rate"], names
    )

    # Nothing in either note-50 or note-52 family states a base, a partial
    # value share, or any other 9802 treatment.
    assert not [
        name for name in names
        if name.startswith(("brazil_", "forced_labor_"))
        and ("reduced" in name or "partial" in name or "9802" in name)
    ]
    entry_deps = formula_dependencies(
        by_name["forced_labor_section_301_entry_component_rate"], names
    )
    assert "forced_labor_chapter_98_exclusion_applies" in entry_deps
    assert not [dep for dep in entry_deps if "reduced" in dep or "9802" in dep]

    # The 9802 fact is declared, and the only note-52 rule reading it reads it
    # as a carve-out FROM the chapter 98 exclusion.
    assert "entry_is_9802_excepted_entry" in DECLARED_BOOLEAN_INPUTS
    chapter_98 = by_name["forced_labor_chapter_98_exclusion_applies"]
    assert any(
        "not entry_is_9802_excepted_entry" in version.get("formula", "")
        for version in chapter_98["versions"]
    )
    readers = sorted(
        name for name, rule in by_name.items()
        if formula_dependencies(rule, {"entry_is_9802_excepted_entry"})
    )
    assert [name for name in readers if name.startswith("forced_labor_")] == [
        "forced_labor_chapter_98_exclusion_applies"
    ]

    # Brazil has no entry-level surface at all: one rule, the panel projection.
    assert sorted(name for name in names if name.startswith("brazil_")) == [
        "brazil_section_301_component_rate"
    ]

    # The same generator publishes 9802 partial-value-share rules for two other
    # families and none for these two. If that changes, rewrite both summaries.
    assert [code for code, _ in PARTIAL_CODES] == [
        "9802_00_40", "9802_00_50", "9802_00_60", "9802_00_80"
    ]
    assert partial_rules("301") and partial_rules("122")
    assert partial_rules("brazil-50") == []
    assert partial_rules("reciprocal-52") == []


def test_scope_flags_ignore_country_because_origin_gating_lives_in_the_composition():
    """origin_is_brazil and origin_is_forced_labor_* are applied by the
    composition; repeating origin here would double-gate the charge."""
    for rate_line, hts in ((9506624040, "9506.62.40.40"), (7202111000, "7202.11.10.00")):
        by_country = {
            country: (
                entry_flags(rate_line, hts, country)["entry_is_brazil_301_listed"],
                entry_flags(rate_line, hts, country)["entry_is_forced_labor_301_listed"],
            )
            for country in ("BR", "CN", "DE", "US")
        }
        assert len(set(by_country.values())) == 1, by_country
