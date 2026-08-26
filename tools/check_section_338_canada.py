#!/usr/bin/env python3
"""Independently check grounded Section 338 Canada generated artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
RULEMAKING_RELATIVE_PATH = Path(
    "data/corpus/provisions/us/rulemaking/"
    "2026-08-09-rulespec-tariff-rulemaking-union.jsonl"
)
RULEMAKING_SHA256 = "b25c5a42c47683b4f9fc0ad548007d10f97dd8ead629e6d1de872494030e05e0"
SUSPENSION_RELATIVE_PATH = Path(
    "data/corpus/provisions/us/rulemaking/2026-08-18-canada-338-suspension.jsonl"
)
SUSPENSION_SHA256 = "ea27a56ab605ff1dbda1a9b4a9e9bfbb38c8064b3510202d98625b19f461abb5"
REV15_RELATIVE_PATH = Path(
    "data/corpus/provisions/us/statute/2026-08-04-usitc-hts-2026-rev15-notes.jsonl"
)
REV15_SHA256 = "0f3ed7ef2efb64383825db65e615959200770e8511c8d4834b16e02892cb9ec8"
ANNEX_PAGE_PREFIX = (
    "us/rulemaking/federal-register/2026-07-23/2026-14991/annex-ii/page-"
)
SUSPENSION_PATH = "us/rulemaking/white-house/2026-08-18/canada-338-suspension/clause-1"
SUSPENSION_EXCERPTS = {
    "Accordingly, the chapeau of Annex II of each of Proclamations 11046, "
    "11047, and 11048, is amended by deleting the effective date “August 19, "
    "2026” and inserting “August 22, 2026” in lieu thereof.",
    "The effective date of the additional ad valorem duties imposed in "
    "Proclamations 11046, 11047, and 11048 shall be 12:01 a.m. eastern time "
    "on August 22, 2026.",
}
TEMPORAL_RULES = {
    "section_338_component_rate": "0",
    "section_338_chapter_98_exclusion_applies": "false",
    "section_338_reduced_duty_base_applies": "false",
    "section_338_entry_component_rate": "0",
}
MEMBERSHIP_START = (
    "1. Heading 9903.03.12 applies to articles classifiable in the following "
    "provisions of the tariff schedule:"
)
MEMBERSHIP_STOP = "(c) As provided in heading 9903.03.15"
HTS8 = re.compile(r"(?<![\d.])(\d{4}\.\d{2}\.\d{2})(?![\d.])")


def checked_records(path: Path, expected_sha256: str) -> tuple[bytes, list[dict]]:
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    assert actual == expected_sha256, (path, expected_sha256, actual)
    return raw, [json.loads(line) for line in raw.splitlines() if line.strip()]


def source_membership(records: dict[str, dict]) -> dict[int, list[str]]:
    result: dict[int, list[str]] = {}
    active = False
    ended = False
    for page in range(1, 8):
        body = records[f"{ANNEX_PAGE_PREFIX}{page}"]["body"]
        start = 0
        if not active:
            marker = body.find(MEMBERSHIP_START)
            if marker < 0:
                continue
            start = marker + len(MEMBERSHIP_START)
            active = True
        stop = body.find(MEMBERSHIP_STOP, start)
        codes = HTS8.findall(body[start : stop if stop >= 0 else len(body)])
        if codes:
            result[page] = codes
        if stop >= 0:
            ended = True
            break
    assert active and ended
    assert {page: len(codes) for page, codes in result.items()} == {1: 12, 2: 51}
    flat = [code for codes in result.values() for code in codes]
    assert len(flat) == len(set(flat)) == 63
    return result


def load_yaml(relative: str) -> object:
    return yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))


def check_incidence(page: int, codes: list[str]) -> None:
    relative = (
        "us/policies/usitc/us-tariff-incidence/generated/note51/alcohol/"
        f"page-{page}.yaml"
    )
    module = load_yaml(relative)
    assert isinstance(module, dict)
    citation = f"{ANNEX_PAGE_PREFIX}{page}"
    source_verification = module["module"]["source_verification"]
    assert source_verification == {"corpus_citation_path": citation}
    assert "corpus_citation_paths" not in source_verification
    rules = module["rules"]
    assert len(rules) == 1
    rule = rules[0]
    name = f"section_338_alcohol_annex_ii_membership_p{page}"
    assert rule["name"] == name
    assert rule["kind"] == "parameter"
    assert rule["dtype"] == "Count"
    assert rule["indexed_by"] == "hts_line"
    version = rule["versions"]
    assert len(version) == 1
    assert version[0]["effective_from"] == "2026-08-19"
    expected_values = {int(code.replace(".", "")): 1 for code in codes}
    assert version[0]["values"] == expected_values
    atoms = rule["metadata"]["proof"]["atoms"]
    assert len(atoms) == len(codes)
    assert [atom["source"]["excerpt"] for atom in atoms] == codes
    assert all(atom["path"] == "versions[0].values" for atom in atoms)
    assert all(atom["kind"] == "parameter" for atom in atoms)
    assert all(atom["source"]["corpus_citation_path"] == citation for atom in atoms)
    assert all(atom["context"] == {"subdivision": "51(b)(1)"} for atom in atoms)

    cases = load_yaml(relative.replace(".yaml", ".test.yaml"))
    assert isinstance(cases, list) and len(cases) == 1
    case = cases[0]
    module_id = relative.removesuffix(".yaml").replace("us/", "us:", 1)
    assert case["period"]["start"] == case["period"]["end"] == "2026-08-22"
    assert case["input"] == {
        f"{module_id}#input.hts_line": int(codes[0].replace(".", ""))
    }
    assert case["output"] == {f"{module_id}#{name}": 1}


def check_component(records: dict[str, dict]) -> None:
    relative = "us/policies/cbp/us-tariff-duty/section-338-canada/component-rate.yaml"
    module = load_yaml(relative)
    assert isinstance(module, dict)
    expected_sources = [
        "us/rulemaking/federal-register/2026-07-23/2026-14991/annex-i/page-1",
        f"{ANNEX_PAGE_PREFIX}1",
        f"{ANNEX_PAGE_PREFIX}2",
        f"{ANNEX_PAGE_PREFIX}6",
        SUSPENSION_PATH,
    ]
    assert module["module"]["source_verification"] == {
        "corpus_citation_paths": expected_sources
    }
    deferred = module["module"]["deferred_outputs"]
    assert len(deferred) == 4
    assert all(
        "signed" in item["reason"] and "Rev-15" in item["reason"] for item in deferred
    )

    rules = {rule["name"]: rule for rule in module["rules"]}
    assert set(rules) == {
        "section_338_alcohol_additional_duty_rate",
        "section_338_alcohol_component_rate",
    }
    scalar = rules["section_338_alcohol_additional_duty_rate"]
    assert scalar["versions"] == [{"effective_from": "2026-08-19", "formula": "0.50"}]
    component = rules["section_338_alcohol_component_rate"]
    assert component["versions"][0] == {
        "effective_from": "2026-08-19",
        "effective_to": "2026-08-21",
        "formula": "0",
    }
    assert component["versions"][1]["effective_from"] == "2026-08-22"
    active_formula = component["versions"][1]["formula"]
    assert "article_product_of_canada" in active_formula
    assert "section_338_alcohol_annex_ii_membership" in active_formula
    assert "not article_is_section_232_carveout_under_note_51_c" in active_formula

    for rule in rules.values():
        for atom in rule["metadata"]["proof"]["atoms"]:
            source = atom["source"]
            assert source["corpus_citation_path"] in expected_sources
            assert source["excerpt"] in records[source["corpus_citation_path"]]["body"]

    cases = load_yaml(relative.replace(".yaml", ".test.yaml"))
    assert isinstance(cases, list) and len(cases) == 6
    module_id = relative.removesuffix(".yaml").replace("us/", "us:", 1)
    input_suffixes = {
        "article_product_of_canada",
        "section_338_alcohol_annex_ii_membership",
        "article_is_section_232_carveout_under_note_51_c",
    }
    expected_inputs = {f"{module_id}#input.{suffix}" for suffix in input_suffixes}
    assert all(set(case["input"]) == expected_inputs for case in cases)
    by_date = [case["period"]["start"] for case in cases]
    assert by_date == [
        "2026-08-19",
        "2026-08-21",
        "2026-08-22",
        "2026-08-22",
        "2026-08-22",
        "2026-08-22",
    ]


def temporal_lower(version: dict) -> str | None:
    return version.get("effective_from", version.get("from"))


def temporal_upper(version: dict) -> str | None:
    return version.get("effective_to", version.get("to"))


def assert_temporal_rules(module: dict, records: dict[str, dict]) -> None:
    rules = {rule["name"]: rule for rule in module["rules"]}
    for name, inert_formula in TEMPORAL_RULES.items():
        rule = rules[name]
        versions = rule["versions"]
        assert len(versions) == 3
        assert (temporal_lower(versions[0]), temporal_upper(versions[0])) == (
            "2026-02-15",
            "2026-08-18",
        )
        assert (temporal_lower(versions[1]), temporal_upper(versions[1])) == (
            "2026-08-19",
            "2026-08-21",
        )
        assert temporal_lower(versions[2]) == "2026-08-22"
        assert temporal_upper(versions[2]) is None
        assert versions[1]["formula"].strip() == inert_formula

        clause_atoms = []
        for atom in rule["metadata"]["proof"]["atoms"]:
            source = atom["source"]
            citation = source["corpus_citation_path"]
            excerpt = source["excerpt"]
            assert excerpt in records[citation]["body"]
            if citation == SUSPENSION_PATH:
                clause_atoms.append(atom)
        assert len(clause_atoms) == 2
        assert {atom["source"]["excerpt"] for atom in clause_atoms} == (
            SUSPENSION_EXCERPTS
        )
        assert {atom["path"] for atom in clause_atoms} == {
            "versions[1].formula",
            "versions[2].formula",
        }


def check_witness_and_generated(records: dict[str, dict]) -> tuple[int, int]:
    witness_relative = "us/policies/cbp/us-tariff-duty/composition.yaml"
    witness = load_yaml(witness_relative)
    assert isinstance(witness, dict)
    verification = witness["module"]["source_verification"]
    assert SUSPENSION_PATH in verification["corpus_citation_paths"]
    assert SUSPENSION_PATH in verification["upstream_source_check"]["checked_paths"]
    assert_temporal_rules(witness, records)

    cases = load_yaml(witness_relative.replace(".yaml", ".test.yaml"))
    assert isinstance(cases, list)
    by_name = {case["name"]: case for case in cases}
    expected_boundary = {
        "line_d_canada_day_before_original_section_338_start_has_forced_labor_only": (
            "2026-08-18",
            0,
            0.10,
        ),
        "line_d_canada_original_section_338_start_is_suspended": (
            "2026-08-19",
            0,
            0.10,
        ),
        "line_d_canada_last_section_338_suspension_day_has_forced_labor_only": (
            "2026-08-21",
            0,
            0.10,
        ),
        "line_d_canada_delayed_section_338_start_stacks_forced_labor": (
            "2026-08-22",
            0.50,
            0.60,
        ),
    }
    witness_id = witness_relative.removesuffix(".yaml").replace("us/", "us:", 1)
    expected_input_suffixes = {
        "customs_value",
        "shipment_value",
        "hts_number",
        "country_of_origin",
        "is_postal_shipment",
        "article_is_potash",
        "cbp_agrees_chapter_98_entry_is_appropriate",
        "entry_is_9802_excepted_entry",
        "entry_is_chapter_98_subchapter_xxiii_entry",
        "entry_is_entered_free_of_duty_under_usmca",
        "entry_is_humanitarian_donation_article",
        "entry_is_informational_material_article",
        "entry_is_personal_use_accompanied_baggage",
        "entry_is_properly_claimed_chapter_98_entry",
        "entry_is_usmca_duty_free_entry",
        "entry_loaded_and_in_transit_before_july_24_2026",
    }
    expected_inputs = {
        f"{witness_id}#input.{suffix}" for suffix in expected_input_suffixes
    }
    for name, (date, component, total) in expected_boundary.items():
        case = by_name[name]
        assert case["period"]["start"] == case["period"]["end"] == date
        assert set(case["input"]) == expected_inputs
        assert case["output"][f"{witness_id}#section_338_component_rate"] == component
        assert (
            case["output"][f"{witness_id}#section_338_entry_component_rate"]
            == component
        )
        assert case["output"][f"{witness_id}#us_tariff_total_ad_valorem_rate"] == total

    generated_paths = sorted(
        path
        for path in (ROOT / "us/policies/cbp/us-tariff-schedule/generated").glob(
            "ch*/ch*.yaml"
        )
        if not path.name.endswith(".test.yaml")
    )
    assert len(generated_paths) == 100
    generated_case_count = 0
    generated_input_suffixes = {
        "entry_is_line_d",
        "country_of_origin",
        "entry_is_personal_use_accompanied_baggage",
        "entry_is_properly_claimed_chapter_98_entry",
        "cbp_agrees_chapter_98_entry_is_appropriate",
        "entry_is_chapter_98_subchapter_xxiii_entry",
        "entry_is_9802_excepted_entry",
    }
    for path in generated_paths:
        module = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert (
            SUSPENSION_PATH
            in module["module"]["source_verification"]["corpus_citation_paths"]
        )
        assert_temporal_rules(module, records)

        module_id = path.relative_to(ROOT).as_posix().removesuffix(".yaml")
        module_id = module_id.replace("us/", "us:", 1)
        generated_cases = yaml.safe_load(
            path.with_name(f"{path.stem}.test.yaml").read_text(encoding="utf-8")
        )
        generated_by_name = {case["name"]: case for case in generated_cases}
        for name, date, component in (
            ("section 338 remains suspended on August 21", "2026-08-21", 0),
            (
                "section 338 starts on delayed August 22 boundary",
                "2026-08-22",
                0.5,
            ),
        ):
            case = generated_by_name[name]
            assert case["period"]["start"] == case["period"]["end"] == date
            assert set(case["input"]) == {
                f"{module_id}#input.{suffix}" for suffix in generated_input_suffixes
            }
            assert (
                case["output"][f"{module_id}#section_338_component_rate"] == component
            )
            assert (
                case["output"][f"{module_id}#section_338_entry_component_rate"]
                == component
            )
            generated_case_count += 1
    return len(generated_paths), generated_case_count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path(
            os.environ.get(
                "AXIOM_CORPUS_REPO",
                Path.home() / "TheAxiomFoundation/axiom-corpus",
            )
        ),
    )
    args = parser.parse_args()
    rulemaking_raw, rulemaking = checked_records(
        args.corpus / RULEMAKING_RELATIVE_PATH, RULEMAKING_SHA256
    )
    _, suspension = checked_records(
        args.corpus / SUSPENSION_RELATIVE_PATH, SUSPENSION_SHA256
    )
    rev15_raw, _ = checked_records(args.corpus / REV15_RELATIVE_PATH, REV15_SHA256)
    records = {record["citation_path"]: record for record in [*rulemaking, *suspension]}

    assert "U.S. note 51" not in rev15_raw.decode("utf-8")
    assert "9903.03.12" not in rev15_raw.decode("utf-8")
    assert "9903.03.13" not in rev15_raw.decode("utf-8")
    assert "9903.03.14" not in rev15_raw.decode("utf-8")
    rulemaking_text = rulemaking_raw.decode("utf-8")
    assert "2026-14992/annex-ii" not in rulemaking_text
    assert "2026-14997/annex-ii" not in rulemaking_text

    membership = source_membership(records)
    for page, codes in membership.items():
        check_incidence(page, codes)
    check_component(records)
    generated_modules, generated_cases = check_witness_and_generated(records)
    print(
        "check OK: 2 pages, 63 incidence atoms, 2 atomic component rules, "
        f"4 witness temporal rules, {generated_modules} generated modules, "
        f"{generated_cases} generated boundary cases"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
