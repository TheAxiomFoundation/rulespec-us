"""Section 232 aluminum/steel routing and the chapter-99 heading-overlap check.

The generated chapter compositions are checked here, not only when they are
regenerated: CI skips companion tests for modules with an active validation
waiver, and every generated chapter has one.

Invariants (every membership vector, origin and date the modules define):
* for every entry b16 entry preparation produces from a chapter-table key,
  HTS10 membership key or witness line, no chapter-99 heading, rate
  parameter or mutually exclusive group (section 232 metals from April 6,
  2026) is charged twice, except the named KNOWN_DOUBLE_CHARGES entry that
  rulespec-us#1398 removes;
* from 2026-04-06 a section 232 aluminum member is charged by the aluminum
  component alone, so aluminum and steel never both charge one entry and
  adding steel membership never changes the section 232 total;
* from 2026-04-06 a British steel-only member pays 25 percent, a Russian
  aluminum member exactly 200 percent, and any other steel-only member 50;
* before 2026-04-06 the steel component is unchanged (50 percent for any
  steel member).
The domain is finite, so the invariants are enumerated exhaustively.
"""

from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import generate_schedule_compositions as generator  # noqa: E402
import schedule_heading_overlap as overlap  # noqa: E402
from b16_entry_flags import entry_flags  # noqa: E402

GENERATED = ROOT / "us/policies/cbp/us-tariff-schedule/generated"
PROCLAMATION = "2026-04-06"
CONSOLIDATION = "2026-07-21"
ALUMINUM = "section_232_aluminum_component_rate"
STEEL = "section_232_steel_component_rate"


def load_module(chapter: str) -> dict:
    return yaml.load((GENERATED / f"ch{chapter}" / f"ch{chapter}.yaml").read_bytes(), Loader=overlap._LOADER)


def table_keys(chapter: str) -> set[int]:
    _, keys = overlap.committed_inputs([chapter])
    return keys[chapter]


def check(modules: dict[str, dict]) -> overlap.Report:
    return overlap.check_chapters(
        modules,
        {chapter: table_keys(chapter) for chapter in modules},
        **overlap.generator_inputs(),
    )


@pytest.fixture(scope="module")
def committed_report() -> overlap.Report:
    modules, keys = overlap.committed_inputs()
    return overlap.check_chapters(modules, keys, **overlap.generator_inputs())


GROUP = "group:section-232-metals"


def test_every_committed_chapter_charges_each_heading_at_most_once(committed_report):
    assert committed_report.chapters == 100
    # Every chapter-table key, plus HTS10 membership keys and witness lines.
    assert committed_report.entries >= 13790
    unexpected, stale = generator.split_known_double_charges(committed_report, {f"{n:02d}" for n in range(100)} | {"99a", "99b", "99c"})
    assert unexpected == [], "\n".join(map(str, unexpected[:10]))
    assert stale == []


def test_known_double_charge_is_the_1398_beer_exemplar(committed_report):
    assert {(item.chapter, item.hts_number, item.heading, item.origin) for item in committed_report.collisions} == {
        ("22", "2203.00.00.30", "9903.88.03", "CN")
    }


def _steel_versions(module: dict) -> list[dict]:
    return next(rule for rule in module["rules"] if rule["name"] == STEEL)["versions"]


def test_check_catches_the_double_charged_steel_formula():
    """Main's single-version steel formula: every origin class, from April 6."""
    module = load_module("76")
    steel = next(rule for rule in module["rules"] if rule["name"] == STEEL)
    steel["versions"] = [{
        "from": generator.WITNESS_EFFECTIVE_FROM,
        "formula": "if entry_is_section_232_steel: ch76_s232_steel_heading_rate\nelse: 0",
    }]
    collisions = check({"76": module}).collisions
    assert {item.hts_number for item in collisions} == {"7614.10.10.00"}
    assert {item.heading for item in collisions} == {"9903.82.02", GROUP}
    assert min(item.day.isoformat() for item in collisions) == PROCLAMATION
    # The UK (9903.82.04 + 9903.82.02) and Russian (9903.85.67 + 9903.82.02)
    # forms charge different headings of the one exclusive group.
    assert {"GB", "RU"} <= {item.origin for item in collisions if item.heading == GROUP}
    assert min(item.day.isoformat() for item in collisions if item.heading == "9903.82.02") == CONSOLIDATION


def test_check_catches_a_double_charge_in_the_proclamation_window():
    module = load_module("76")
    _steel_versions(module)[1]["formula"] = (
        "if entry_is_section_232_steel:\n"
        "  (if origin_is_uk: ch76_s232_steel_uk_proclamation_rate\n"
        "   else: ch76_s232_steel_proclamation_rate)\n"
        "else: 0"
    )
    collisions = check({"76": module}).collisions
    assert {item.hts_number for item in collisions} == {"7614.10.10.00"}
    assert {item.heading for item in collisions} == {GROUP}
    assert all(PROCLAMATION <= item.day.isoformat() < CONSOLIDATION for item in collisions)


def test_check_catches_a_russian_double_charge_after_consolidation():
    """9903.85.67/.68 plus 9903.82.14 on one article violates note 16(a)."""
    module = load_module("76")
    _steel_versions(module)[2]["formula"] = (
        "if entry_is_section_232_aluminum and not origin_is_russia: 0\n"
        "elif entry_is_section_232_steel:\n"
        "  (if origin_is_russia: ch76_s232_steel_russia_heading_rate\n"
        "   else: 0)\n"
        "else: 0"
    )
    collisions = check({"76": module}).collisions
    assert {(item.hts_number, item.origin, item.heading) for item in collisions} == {
        ("7614.10.10.00", "RU", GROUP)
    }


def test_check_catches_two_terms_on_one_rate_parameter():
    """The China 301 List 1-3 rate charged by two terms is a double count."""
    module = load_module("72")
    china = next(rule for rule in module["rules"] if rule["name"] == "china_section_301_component_rate")
    version = china["versions"][0]
    version["formula"] = (
        "(if entry_is_china_301_list123 and origin_is_china: list_1_additional_ad_valorem_rate else: 0)\n"
        "+ (if entry_is_section_232_covered and origin_is_china: list_1_additional_ad_valorem_rate else: 0)"
    )
    collisions = check({"72": module}).collisions
    assert collisions
    assert {item.origin for item in collisions} == {"CN"}


def test_check_evaluates_the_base_summand():
    """A second term on the base's heading 9903.90.09 (the Russian rate in
    lieu of column 2) is a double charge; the base is not exempt."""
    module = load_module("76")
    rule = next(rule for rule in module["rules"] if rule["name"] == "section_122_component_rate")
    rule["versions"][-1]["formula"] = (
        "if entry_is_line_b and origin_is_russia: ch76_russia_heading_9903_90_09_rate_of_duty\nelse: 0"
    )
    collisions = check({"76": module}).collisions
    assert {(item.hts_number, item.origin, item.heading) for item in collisions} == {
        ("7601.10.30.00", "RU", "9903.90.09")
    }
    assert {summand for item in collisions for summand, _ in item.charges} == {
        "mfn_ad_valorem_rate", "section_122_component_rate",
    }


def test_known_double_charge_excuses_only_the_listed_charges(committed_report):
    known = next(item for item in committed_report.collisions if item.hts_number == "2203.00.00.30")
    extra = overlap.Collision(
        known.chapter, known.hts_number, known.rate_line, known.day, known.origin, known.heading,
        [*known.charges, ("forced_labor_section_301_component_rate", "list_1_additional_ad_valorem_rate")],
    )
    other_origin = overlap.Collision(
        known.chapter, known.hts_number, known.rate_line, known.day, "HK", known.heading, list(known.charges),
    )
    report = overlap.Report(collisions=[known, extra, other_origin])
    unexpected, stale = generator.split_known_double_charges(report, {"22"})
    assert unexpected == [extra, other_origin]
    assert stale == []
    unexpected, stale = generator.split_known_double_charges(overlap.Report(), {"22"})
    assert stale == [("22", "2203.00.00.30", "9903.88.03")]


def test_check_fails_closed_on_an_unmodelled_input():
    module = load_module("72")
    steel = next(rule for rule in module["rules"] if rule["name"] == STEEL)
    steel["versions"][-1]["formula"] = "if entry_is_unmodelled_flag: 0\nelse: 0"
    with pytest.raises(overlap.CheckError, match="unmodelled input"):
        check({"72": module})


def test_check_fails_closed_on_unsupported_syntax():
    with pytest.raises(overlap.CheckError):
        overlap.parse_formula("max(a, b)")


def test_a_missing_table_cell_keeps_its_reads():
    """The unavailable path must record hts_line, or its cached outcome would
    be reused for entries whose cell exists (review finding, 2026-09-25)."""
    scope = overlap.Scope("01", load_module("01"), ROOT)
    _, keys = overlap.committed_inputs(["01"])
    rates = next(
        rule for rule in overlap.load_yaml(generator.TABLE_DIR / "ch01.yaml")["rules"]
        if rule["name"] == "ch01_general_rate"
    )["versions"][0]["values"]
    missing = min(key for key in keys["01"] if key not in rates)
    inputs = {
        **{name: overlap._as_decimal(value) for name, value in generator.heading_check_fixed_inputs().items()},
        **{name: False for name in generator.HEADING_CHECK_ENTRY_INPUTS},
        "hts_line": missing, "hts_number": overlap.dotted(missing), "country_of_origin": "AT",
    }
    reads: set[str] = set()
    with pytest.raises(overlap.TableKeyMissing):
        overlap.Context(scope, date(2026, 2, 15), inputs).rule("ieepa_component_rate", reads)
    assert "hts_line" in reads


def test_entries_after_a_missing_cell_are_still_checked():
    """A collision on a present cell is found even when an entry with the
    same flags and a missing cell is evaluated first."""
    module = load_module("01")
    rule = next(rule for rule in module["rules"] if rule["name"] == "section_201_component_rate")
    rule["versions"][0]["formula"] = (
        "if origin_is_eu and mfn_ad_valorem_rate < "
        "reciprocal_eu_below_floor_column_1_general_duty_rate_threshold: reciprocal_eu_floor_duty_rate\n"
        "else: 0"
    )
    collisions = check({"01": module}).collisions
    assert collisions
    assert {item.day.isoformat() for item in collisions} == {"2026-02-15"}
    assert "0102.31.00.00" in {item.hts_number for item in collisions}


def _evaluate(scope: overlap.Scope, day: str, inputs: dict) -> dict[str, Decimal]:
    context = overlap.Context(scope, overlap._as_date(day), inputs)
    return {name: context.rule(name, set())[0] for name in (ALUMINUM, STEEL)}


@pytest.mark.parametrize("chapter", ["72", "76", "99a"])
def test_section_232_invariants_hold_exhaustively(chapter):
    scope = overlap.Scope(chapter, load_module(chapter), ROOT)
    fixed = {name: overlap._as_decimal(value) for name, value in generator.heading_check_fixed_inputs().items()}
    fixed.update({name: False for name in generator.RETAINED_ENTRY_FLAGS})
    days = scope.boundaries([ALUMINUM, STEEL])
    origins = sorted(scope.country_literals() | {overlap.UNLISTED_ORIGIN})
    checked = 0
    for day in days:
        for origin in origins:
            totals = {}
            for aluminum in (False, True):
                for steel in (False, True):
                    inputs = {
                        **fixed,
                        **{name: False for name in generator.GENERATED_MEMBERSHIP_INPUTS},
                        "entry_is_section_232_aluminum": aluminum,
                        "entry_is_section_232_steel": steel,
                        "entry_is_section_232_covered": aluminum or steel,
                        "country_of_origin": origin,
                    }
                    values = _evaluate(scope, day.isoformat(), inputs)
                    totals[(aluminum, steel)] = values[ALUMINUM] + values[STEEL]
                    checked += 1
                    if not steel:
                        assert values[STEEL] == 0
                    if day.isoformat() >= PROCLAMATION:
                        assert values[ALUMINUM] == 0 or values[STEEL] == 0, (day, origin, aluminum, steel)
                        if aluminum:
                            assert values[STEEL] == 0, (day, origin)
                        if steel and not aluminum:
                            expected = Decimal("0.25") if origin == "GB" else Decimal("0.50")
                            assert values[STEEL] == expected, (day, origin)
                        if aluminum and origin == "RU":
                            assert totals[(aluminum, steel)] == Decimal("2.00"), (day, origin)
                        if origin == "GB":
                            assert totals[(aluminum, steel)] in {0, Decimal("0.25")}, (day, origin)
                    elif steel:
                        assert values[STEEL] == Decimal("0.50"), (day, origin)
            if day.isoformat() >= PROCLAMATION:
                # Adding steel membership never changes an aluminum member's charge.
                assert totals[(True, True)] == totals[(True, False)], (day, origin)
    assert checked == len(days) * len(origins) * 4


def _companion_value(value):
    if value == "holds":
        return True
    if value == "not_holds":
        return False
    return overlap._as_decimal(value)


@pytest.mark.parametrize("chapter", sorted(generator.EXPECTED_CHAPTERS))
def test_evaluator_agrees_with_engine_validated_companion_cases(chapter):
    """Differential: every expected output the artifact engine verified in the
    committed companion file is reproduced by the Python evaluator."""
    scope = overlap.Scope(chapter, load_module(chapter), ROOT)
    prefix = f"us:policies/cbp/us-tariff-schedule/generated/ch{chapter}/ch{chapter}#"
    cases = yaml.load((GENERATED / f"ch{chapter}" / f"ch{chapter}.test.yaml").read_bytes(), Loader=overlap._LOADER)
    compared = 0
    for case in cases:
        inputs = {
            key.removeprefix(prefix + "input."): (value if key.endswith(".hts_line") else overlap._as_decimal(value))
            for key, value in case["input"].items()
        }
        context = overlap.Context(scope, overlap._as_date(case["period"]["start"]), inputs)
        for key, expected in case["output"].items():
            actual, _ = context.rule(key.removeprefix(prefix), set())
            assert actual == _companion_value(expected), (case["name"], key, actual, expected)
            compared += 1
    assert compared > 50


def test_pinned_entry_vectors_match_entry_preparation():
    for chapter, (rate_line, hts_number, members, _) in generator.SECTION_232_ENTRY_CASES.items():
        flags = entry_flags(rate_line, hts_number, "CN")
        truthy = {name for name in generator.GENERATED_MEMBERSHIP_INPUTS if flags[name]}
        assert truthy == set(members), (chapter, hts_number)
        assert not any(flags[name] for name in generator.RETAINED_ENTRY_FLAGS)


def test_only_7614_10_10_is_both_an_aluminum_and_a_steel_member():
    """The one entry the routing change reaches through entry preparation."""
    _, keys = overlap.committed_inputs()
    both = []
    for chapter, entries in overlap.chapter_entries(keys).items():
        for rate_line, hts_number in entries:
            flags = entry_flags(rate_line, hts_number, "CN")
            if flags["entry_is_section_232_aluminum"] and flags["entry_is_section_232_steel"]:
                both.append(hts_number)
    assert both == ["7614.10.10.00"]


def test_generated_steel_rule_cites_the_consolidated_and_proclamation_sources():
    module = load_module("72")
    steel = next(rule for rule in module["rules"] if rule["name"] == STEEL)
    cited = {atom["source"]["corpus_citation_path"] for atom in steel["metadata"]["proof"]["atoms"]}
    assert {
        "us/statute/hts/9903.82.02",
        "us/statute/hts/9903.82.04",
        "us/statute/hts/9903.82.14",
        "us/statute/hts/chapter-99/page-236",
        "us/statute/hts/chapter-99/page-250",
        "us/rulemaking/federal-register/2026-04-09/2026-06960",
    } <= cited
    assert [version.get("effective_from") for version in steel["versions"]] == [
        generator.WITNESS_EFFECTIVE_FROM, PROCLAMATION, CONSOLIDATION,
    ]
    paths = module["module"]["source_verification"]["corpus_citation_paths"]
    assert paths == sorted(paths)
    assert cited <= set(paths)
