#!/usr/bin/env python3
"""Pinned-engine identity gate for the B1.3 chapter-72 pilot.

Runs one engine process at a time.  The four dates before the witness's
executable boundary are evaluated cell/output-by-cell/output and must have the
same numeric-or-unavailable status (raw engine error classes are retained).
Supported dates are batched by artifact/date and Decimal-compared across the
full statutory component vector and total.
"""

from __future__ import annotations

import csv
import io
import json
import re
import subprocess
from decimal import Decimal
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path(__file__).resolve().parent
ENGINE = Path(
    "/Users/maxghenis/TheAxiomFoundation/axiom-rules-engine-pinned/target/release/axiom-rules-engine"
)
WITNESS_ARTIFACT = EVIDENCE / "witness.compiled.json"
GENERATED_ARTIFACT = EVIDENCE / "ch72.compiled.json"
WITNESS_MODULE = "us:policies/cbp/us-tariff-duty/composition"
GENERATED_MODULE = "us:policies/cbp/us-tariff-schedule/generated/ch72"

COUNTRIES = ("CN", "MX", "CA", "GB", "RU", "BR", "VN", "ZA", "DE", "CU")
REQUIRED_DATES = (
    "2025-02-15",
    "2025-04-10",
    "2025-07-01",
    "2026-01-15",
    "2026-02-21",
    "2026-02-25",
    "2026-03-15",
    "2026-08-01",
)
# Extra witness-supported boundary exercises live IEEPA/fentanyl routing; every
# required supported date falls after IEEPA termination.
DATES = REQUIRED_DATES[:4] + ("2026-02-15",) + REQUIRED_DATES[4:]
PRE_VERSION_DATES = set(REQUIRED_DATES[:4])

COMPONENTS = (
    "ieepa_component_rate",
    "ieepa_component_rate_with_declared_exceptions",
    "section_122_component_rate",
    "section_201_component_rate",
    "section_232_aluminum_component_rate",
    "section_338_component_rate",
    "section_338_entry_component_rate",
    "china_section_301_component_rate",
    "brazil_section_301_component_rate",
    "forced_labor_section_301_component_rate",
    "forced_labor_section_301_entry_component_rate",
)
PANEL_COMPONENTS = (
    "ieepa_component_rate",
    "section_201_component_rate",
    "section_122_component_rate",
    "section_232_aluminum_component_rate",
    "section_338_component_rate",
    "china_section_301_component_rate",
    "brazil_section_301_component_rate",
    "forced_labor_section_301_component_rate",
)
DECLARED_BOOLEAN_INPUTS = (
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
)


def input_record(module: str, name: str, entity: str, date: str, value: object) -> dict:
    if isinstance(value, bool):
        kind = "bool"
    elif isinstance(value, int):
        kind = "integer"
    else:
        kind = "text"
    return {
        "name": f"{module}#input.{name}",
        "entity": "CustomsEntry",
        "entity_id": entity,
        "interval": {"start": date, "end": date},
        "value": {"kind": kind, "value": value},
    }


def inputs_for(module: str, country: str, date: str, generated: bool) -> list[dict]:
    entity = f"{country}@{date}"
    values: list[tuple[str, object]] = [
        ("hts_number", "7202.11.10.00"),
        ("country_of_origin", country),
    ]
    if generated:
        values.insert(0, ("hts_line", 7202111000))
    values.extend((name, False) for name in DECLARED_BOOLEAN_INPUTS)
    return [input_record(module, name, entity, date, value) for name, value in values]


def query(entity: str, date: str, outputs: list[str]) -> dict:
    return {
        "entity_id": entity,
        "period": {
            "period_kind": "custom",
            "name": "day",
            "start": date,
            "end": date,
        },
        "outputs": outputs,
    }


def invoke(artifact: Path, request: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(ENGINE), "run-compiled", "--artifact", str(artifact)],
        input=json.dumps(request, separators=(",", ":")),
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )


def normalized_error(stderr: str) -> str:
    if re.search(r"has no formula version at \d{4}-\d{2}-\d{2}", stderr):
        return "missing_formula_version"
    if re.search(r"parameter `[^`]+` has no value for key `-?\d+` at \d{4}-\d{2}-\d{2}", stderr):
        return "missing_parameter_value"
    return "unexpected_error:" + " ".join(stderr.strip().split())


def evaluate_pre_output(
    artifact: Path,
    module: str,
    country: str,
    date: str,
    generated: bool,
    output: str,
) -> dict:
    entity = f"{country}@{date}"
    request = {
        "mode": "explain",
        "dataset": {
            "inputs": inputs_for(module, country, date, generated),
            "relations": [],
        },
        "queries": [query(entity, date, [f"{module}#{output}"])],
    }
    process = invoke(artifact, request)
    if process.returncode != 0:
        error_class = normalized_error(process.stderr)
        unavailable = error_class in {"missing_formula_version", "missing_parameter_value"}
        return {
            "status": "unavailable" if unavailable else "unexpected_error",
            "error_class": error_class,
            "stderr": process.stderr.strip(),
        }
    response = json.loads(process.stdout)
    result = next(iter(response["results"][0]["outputs"].values()))
    if result["kind"] != "scalar":
        raise SystemExit(f"unexpected pre-effective non-scalar output: {result}")
    return {
        "status": "evaluated",
        "value": result["value"]["value"],
        "mode": response["metadata"]["actual_mode"],
    }


def evaluate_supported(
    artifact: Path,
    module: str,
    date: str,
    generated: bool,
    total: str,
) -> dict[str, dict]:
    inputs: list[dict] = []
    queries: list[dict] = []
    outputs = [
        f"{module}#{name}"
        for name in (*COMPONENTS, "mfn_ad_valorem_rate", total)
    ]
    for country in COUNTRIES:
        entity = f"{country}@{date}"
        inputs.extend(inputs_for(module, country, date, generated))
        queries.append(query(entity, date, outputs))
    request = {
        "mode": "fast",
        "dataset": {"inputs": inputs, "relations": []},
        "queries": queries,
    }
    process = invoke(artifact, request)
    if process.returncode != 0:
        raise SystemExit(
            f"{artifact.name} evaluation failed for {date}: {process.stderr.strip()}"
        )
    response = json.loads(process.stdout)
    if response["metadata"]["actual_mode"] != "fast":
        raise SystemExit(f"{artifact.name} unexpectedly fell back: {response['metadata']}")
    normalized: dict[str, dict] = {}
    for result in response["results"]:
        country = result["entity_id"].split("@", 1)[0]
        values: dict[str, str] = {}
        for output in result["outputs"].values():
            if output["kind"] != "scalar":
                raise SystemExit(f"unexpected non-scalar output: {output}")
            values[output["name"]] = output["value"]["value"]
        normalized[country] = {
            "status": "evaluated",
            "mode": response["metadata"]["actual_mode"],
            "values": values,
        }
    return normalized


def assert_version_contract() -> None:
    witness = yaml.safe_load(
        (ROOT / "us/policies/cbp/us-tariff-duty/composition.yaml").read_text()
    )
    generated = yaml.safe_load(
        (
            ROOT
            / "us/policies/cbp/us-tariff-schedule/generated/ch72.yaml"
        ).read_text()
    )
    witness_rules = {rule["name"]: rule for rule in witness["rules"]}
    generated_rules = {rule["name"]: rule for rule in generated["rules"]}
    for name in (*COMPONENTS, "mfn_ad_valorem_rate"):
        first_version = generated_rules[name]["versions"][0]
        first = first_version.get("effective_from", first_version.get("from"))
        if first != WITNESS_EFFECTIVE_FROM:
            raise SystemExit(f"generated {name} starts at {first}, not witness boundary")
    witness_total_start = witness_rules["us_tariff_total_ad_valorem_rate"]["versions"][0][
        "effective_from"
    ]
    generated_total_start = generated_rules["schedule_statutory_stack"]["versions"][0][
        "effective_from"
    ]
    if witness_total_start != WITNESS_EFFECTIVE_FROM or generated_total_start != WITNESS_EFFECTIVE_FROM:
        raise SystemExit("total effective boundaries differ")


WITNESS_EFFECTIVE_FROM = "2026-02-15"


def decimal_sum(values: dict[str, str], names: tuple[str, ...]) -> Decimal:
    return sum((Decimal(values[name]) for name in names), Decimal(0))


def main() -> int:
    assert_version_contract()
    raw: list[dict] = []
    rows: list[dict] = []

    supported_witness: dict[str, dict[str, dict]] = {}
    supported_generated: dict[str, dict[str, dict]] = {}
    for date in DATES:
        if date in PRE_VERSION_DATES:
            continue
        supported_witness[date] = evaluate_supported(
            WITNESS_ARTIFACT,
            WITNESS_MODULE,
            date,
            False,
            "us_tariff_total_ad_valorem_rate",
        )
        supported_generated[date] = evaluate_supported(
            GENERATED_ARTIFACT,
            GENERATED_MODULE,
            date,
            True,
            "schedule_statutory_stack",
        )

    for date in DATES:
        for country in COUNTRIES:
            if date in PRE_VERSION_DATES:
                witness_outputs = {
                    name: evaluate_pre_output(
                        WITNESS_ARTIFACT,
                        WITNESS_MODULE,
                        country,
                        date,
                        False,
                        name,
                    )
                    for name in COMPONENTS
                }
                witness_outputs["total"] = evaluate_pre_output(
                    WITNESS_ARTIFACT,
                    WITNESS_MODULE,
                    country,
                    date,
                    False,
                    "us_tariff_total_ad_valorem_rate",
                )
                generated_outputs = {
                    name: evaluate_pre_output(
                        GENERATED_ARTIFACT,
                        GENERATED_MODULE,
                        country,
                        date,
                        True,
                        name,
                    )
                    for name in COMPONENTS
                }
                generated_outputs["total"] = evaluate_pre_output(
                    GENERATED_ARTIFACT,
                    GENERATED_MODULE,
                    country,
                    date,
                    True,
                    "schedule_statutory_stack",
                )
                witness = {"status": "pre_effective", "outputs": witness_outputs}
                generated = {"status": "pre_effective", "outputs": generated_outputs}
                mismatches: list[str] = []
                for name in (*COMPONENTS, "total"):
                    left = witness_outputs[name]
                    right = generated_outputs[name]
                    if left["status"] != right["status"]:
                        mismatches.append(name)
                    elif left["status"] == "evaluated" and Decimal(left["value"]) != Decimal(right["value"]):
                        mismatches.append(name)
                    elif left["status"] == "unexpected_error":
                        mismatches.append(name)
                totals_unavailable = (
                    witness_outputs["total"]["status"]
                    == generated_outputs["total"]["status"]
                    == "unavailable"
                )
                pass_cell = not mismatches and totals_unavailable
                row = {
                    "date": date,
                    "country": country,
                    "status": "matching_pre_effective_unavailable" if pass_cell else "error_mismatch",
                    "component_mismatches": ";".join(mismatches),
                    "witness_base": "",
                    "generated_base": "",
                    "witness_total": "",
                    "generated_total": "",
                    "total_delta": "",
                    "witness_residual": "",
                    "generated_residual": "",
                    "verdict": "PASS" if pass_cell else "FAIL",
                }
            else:
                witness = supported_witness[date][country]
                generated = supported_generated[date][country]
                witness_values = witness["values"]
                generated_values = generated["values"]
                mismatches = [
                    name
                    for name in COMPONENTS
                    if Decimal(witness_values[name]) != Decimal(generated_values[name])
                ]
                witness_base = Decimal(witness_values["mfn_ad_valorem_rate"])
                generated_base = Decimal(generated_values["mfn_ad_valorem_rate"])
                witness_total = Decimal(witness_values["us_tariff_total_ad_valorem_rate"])
                generated_total = Decimal(generated_values["schedule_statutory_stack"])
                total_delta = generated_total - witness_total
                witness_residual = witness_total - witness_base - decimal_sum(
                    witness_values, PANEL_COMPONENTS
                )
                generated_residual = generated_total - generated_base - decimal_sum(
                    generated_values, PANEL_COMPONENTS
                )
                pass_cell = (
                    not mismatches
                    and witness_base == generated_base
                    and total_delta == 0
                    and witness_residual == 0
                    and generated_residual == 0
                )
                row = {
                    "date": date,
                    "country": country,
                    "status": "evaluated",
                    "component_mismatches": ";".join(mismatches),
                    "witness_base": str(witness_base),
                    "generated_base": str(generated_base),
                    "witness_total": str(witness_total),
                    "generated_total": str(generated_total),
                    "total_delta": str(total_delta),
                    "witness_residual": str(witness_residual),
                    "generated_residual": str(generated_residual),
                    "verdict": "PASS" if pass_cell else "FAIL",
                }
            rows.append(row)
            raw.append(
                {
                    "date": date,
                    "country": country,
                    "witness": witness,
                    "generated": generated,
                    "comparison": row,
                }
            )

    required_cells = {
        (country, date) for country in COUNTRIES for date in REQUIRED_DATES
    }
    observed_cells = {(row["country"], row["date"]) for row in rows}
    if not required_cells <= observed_cells:
        raise SystemExit(f"required grid incomplete: {sorted(required_cells - observed_cells)}")
    failures = [row for row in rows if row["verdict"] != "PASS"]

    (EVIDENCE / "identity-results.json").write_text(
        json.dumps(
            {
                "engine": str(ENGINE),
                "countries": COUNTRIES,
                "required_dates": REQUIRED_DATES,
                "extra_dates": [date for date in DATES if date not in REQUIRED_DATES],
                "component_outputs": COMPONENTS,
                "cells": raw,
            },
            indent=2,
        )
        + "\n"
    )
    fieldnames = list(rows[0])
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    (EVIDENCE / "identity-diff.csv").write_text(csv_buffer.getvalue())

    date_rows: list[str] = []
    for date in DATES:
        subset = [row for row in rows if row["date"] == date]
        statuses = sorted({row["status"] for row in subset})
        max_delta = max(
            (abs(Decimal(row["total_delta"])) for row in subset if row["total_delta"]),
            default=Decimal(0),
        )
        date_rows.append(
            f"| {date} | {len(subset)} | {', '.join(statuses)} | "
            f"{sum(bool(row['component_mismatches']) for row in subset)} | {max_delta} | "
            f"{'PASS' if all(row['verdict'] == 'PASS' for row in subset) else 'FAIL'} |"
        )
    column2_rows = [
        row
        for row in rows
        if row["country"] in {"RU", "CU"} and row["status"] == "evaluated"
    ]
    column2_detail = "\n".join(
        f"| {row['date']} | {row['country']} | {row['witness_base']} | "
        f"{row['generated_base']} | {row['witness_total']} | "
        f"{row['generated_total']} | {row['verdict']} |"
        for row in column2_rows
    )
    report = f"""# B1.3 chapter-72 witness identity gate

Verdict: **{'PASS' if not failures else 'FAIL'}** — {len(rows) - len(failures)}/{len(rows)} cells matched ({len(required_cells)} required cells plus {len(rows) - len(required_cells)} extra boundary cells).

The pinned engine evaluated both independently compiled compositions. Eleven component/entry-variant outputs, the General Note 3 selected base, each stack's algebraic residual, and the total were Decimal-compared on supported dates. For the four requested dates before the witness's 2026-02-15 executable boundary, every component was probed separately: numeric results matched where a single open-ended rule lowered as timeless, unavailable results matched where versioned rules or parameters had no value, and both totals were unavailable. The raw evidence retains each underlying engine error class. Absence was not coerced to zero.

| Date | Cells | Outcome | Component mismatches | Max absolute total delta | Verdict |
|---|---:|---|---:|---:|---|
{chr(10).join(date_rows)}

## Column-2 identity detail

RU and CU exercise the General Note 3 column-2 branch. The raw public `schedule_base_general_rate` remains the required General-table lookup; the statutory stack's internal selected base matches the witness.

| Date | Country | Witness selected base | Generated selected base | Witness total | Generated total | Verdict |
|---|---|---:|---:|---:|---:|---|
{column2_detail}

Full 90-row diff: `identity-diff.csv`. Raw normalized engine results: `identity-results.json`.
"""
    (EVIDENCE / "IDENTITY.md").write_text(report)

    print(
        f"identity {'PASS' if not failures else 'FAIL'}: "
        f"{len(rows) - len(failures)}/{len(rows)} cells; "
        f"required={len(required_cells)}, extra={len(rows) - len(required_cells)}"
    )
    if failures:
        print(json.dumps(failures[:10], indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
