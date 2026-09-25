"""Generated tariff-schedule chapters must charge China section 301 once.

tools/generate_schedule_compositions.py emits the chapter compositions under
us/policies/cbp/us-tariff-schedule/generated from the hand-built witness
composition. The witness charges its beer exemplar (HTS 2203.00.00.30) the
List 3 rate through an entry_is_line_d term. Entry preparation
(tools/b16_entry_flags.py) sets that flag and entry_is_china_301_list123 for
the same entry, so a chapter that kept both terms charged 25 percent twice.

These checks run in the repository pytest leg because the chapters' own
companion tests are skipped by validation while their validation waivers are
active.
"""

from __future__ import annotations

import functools
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "us/policies/cbp/us-tariff-schedule/generated"
LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def chapter_modules() -> list[Path]:
    return sorted(
        path
        for path in GENERATED.glob("ch*/ch*.yaml")
        if not path.name.endswith(".test.yaml")
    )


@functools.cache
def module_rules(module: Path) -> list[dict]:
    return yaml.load(module.read_text(), Loader=LOADER)["rules"]


def import_tool(name: str):
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        return __import__(name)
    finally:
        sys.path.remove(str(ROOT / "tools"))


def china_301_formulas(module: Path) -> list[str]:
    rules = [
        rule
        for rule in module_rules(module)
        if rule.get("name") == "china_section_301_component_rate"
    ]
    assert len(rules) == 1, f"{module.name}: expected one China section 301 rule"
    return [version["formula"] for version in rules[0]["versions"]]


def test_all_generated_chapters_are_checked() -> None:
    assert len(chapter_modules()) == 100


def test_china_301_component_has_no_exemplar_term() -> None:
    offenders: list[str] = []
    for module in chapter_modules():
        for formula in china_301_formulas(module):
            exemplar_flags = re.findall(r"\bentry_is_line_[a-e]\b", formula)
            list_1_charges = re.findall(r"\blist_1_additional_ad_valorem_rate\b", formula)
            if exemplar_flags or len(list_1_charges) != 1:
                offenders.append(
                    f"{module.relative_to(ROOT).as_posix()}: exemplar flags "
                    f"{exemplar_flags}, {len(list_1_charges)} List 1-3 charge(s)"
                )
    assert offenders == [], (
        "China section 301 must charge Lists 1-3 exactly once, through "
        "entry_is_china_301_list123; regenerate with "
        "tools/generate_schedule_compositions.py:\n" + "\n".join(offenders)
    )


def test_exemplar_flags_stay_inside_the_generator_allow_list() -> None:
    # The generator runs this check only when chapters are regenerated; run it
    # over the committed bytes too.
    generator = import_tool("generate_schedule_compositions")
    offenders: list[str] = []
    for module in chapter_modules():
        chapter = module.stem.removeprefix("ch")
        try:
            generator.check_retained_entry_flag_references(
                module_rules(module), chapter
            )
        except SystemExit as error:
            offenders.append(str(error))
    assert offenders == [], "\n".join(offenders)


def test_chapter_22_companion_pins_a_single_list_3_charge() -> None:
    module_path = "us:policies/cbp/us-tariff-schedule/generated/ch22/ch22"
    cases = yaml.load(
        (GENERATED / "ch22/ch22.test.yaml").read_text(), Loader=LOADER
    )
    matches = [
        case
        for case in cases
        if case["input"].get(f"{module_path}#input.hts_number") == "2203.00.00.30"
        and case["input"].get(f"{module_path}#input.country_of_origin") == "CN"
        and case["input"].get(f"{module_path}#input.entry_is_line_d") is True
        and case["input"].get(f"{module_path}#input.entry_is_china_301_list123") is True
    ]
    assert len(matches) == 1, "chapter 22 lost its China beer regression case"
    output = matches[0]["output"]
    assert output[f"{module_path}#china_section_301_component_rate"] == 0.25
    assert output[f"{module_path}#schedule_statutory_stack"] == 0.25


def test_entry_preparation_sets_both_flags_for_the_beer_exemplar() -> None:
    flags = import_tool("b16_entry_flags").entry_flags(
        2203000000, "2203.00.00.30", "CN"
    )
    # The chapter 22 case sets this flag pair; its other inputs are explicit
    # falses so the expected stack isolates the China 301 charge.
    assert flags["entry_is_line_d"]
    assert flags["entry_is_china_301_list123"]
