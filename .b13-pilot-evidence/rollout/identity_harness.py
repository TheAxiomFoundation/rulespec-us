#!/usr/bin/env python3
"""Pinned-engine identity gates for B1.3 witness chapters 76 and 95.

Runs one engine process at a time.  The four dates before the witness's
executable boundary are evaluated cell/output-by-cell/output and must have the
same numeric-or-unavailable status (raw engine error classes are retained).
Supported dates are batched by artifact/date and Decimal-compared across the
full statutory component vector, selected base, and total.
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

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).resolve().parent
ENGINE = Path(
    "/Users/maxghenis/TheAxiomFoundation/axiom-rules-engine-pinned/target/release/axiom-rules-engine"
)
ARTIFACT_DIR = Path("/tmp/b13-rollout-identity")
WITNESS_ARTIFACT = ARTIFACT_DIR / "witness.compiled.json"
WITNESS_MODULE = "us:policies/cbp/us-tariff-duty/composition"
WITNESS_EFFECTIVE_FROM = "2026-02-15"

CASES = {
    "ch76": {
        "chapter": "76",
        "hts_number": "7601.10.30.00",
        "rate_line": 7601103000,
        "artifact": ARTIFACT_DIR / "ch76.compiled.json",
        "module": "us:policies/cbp/us-tariff-schedule/generated/ch76/ch76",
    },
    "ch95": {
        "chapter": "95",
        "hts_number": "9506.62.40.40",
        "rate_line": 9506624000,
        "artifact": ARTIFACT_DIR / "ch95.compiled.json",
        "module": "us:policies/cbp/us-tariff-schedule/generated/ch95/ch95",
    },
}

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
DATES = REQUIRED_DATES[:4] + (WITNESS_EFFECTIVE_FROM,) + REQUIRED_DATES[4:]
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


def inputs_for(
    module: str, case: dict, country: str, date: str, generated: bool
) -> list[dict]:
    entity = f"{country}@{date}"
    values: list[tuple[str, object]] = [
        ("hts_number", case["hts_number"]),
        ("country_of_origin", country),
    ]
    if generated:
        values.insert(0, ("hts_line", case["rate_line"]))
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
    if re.search(
        r"parameter `[^`]+` has no value for key `-?\d+` at \d{4}-\d{2}-\d{2}",
        stderr,
    ):
        return "missing_parameter_value"
    return "unexpected_error:" + " ".join(stderr.strip().split())


def evaluate_pre_output(
    artifact: Path,
    module: str,
    case: dict,
    country: str,
    date: str,
    generated: bool,
    output: str,
) -> dict:
    entity = f"{country}@{date}"
    request = {
        "mode": "explain",
        "dataset": {
            "inputs": inputs_for(module, case, country, date, generated),
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
    case: dict,
    date: str,
    generated: bool,
    total: str,
) -> dict[str, dict]:
    inputs: list[dict] = []
    queries: list[dict] = []
    outputs = [
        f"{module}#{name}" for name in (*COMPONENTS, "mfn_ad_valorem_rate", total)
    ]
    for country in COUNTRIES:
        entity = f"{country}@{date}"
        inputs.extend(inputs_for(module, case, country, date, generated))
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


def assert_case_contract(case_name: str, case: dict) -> None:
    witness = yaml.safe_load(
        (ROOT / "us/policies/cbp/us-tariff-duty/composition.yaml").read_text()
    )
    generated_path = (
        ROOT
        / f"us/policies/cbp/us-tariff-schedule/generated/{case_name}/{case_name}.yaml"
    )
    generated = yaml.safe_load(generated_path.read_text())
    witness_rules = {rule["name"]: rule for rule in witness["rules"]}
    generated_rules = {rule["name"]: rule for rule in generated["rules"]}
    for name in (*COMPONENTS, "mfn_ad_valorem_rate"):
        first_version = generated_rules[name]["versions"][0]
        first = first_version.get("effective_from", first_version.get("from"))
        if first != WITNESS_EFFECTIVE_FROM:
            raise SystemExit(f"generated {case_name} {name} starts at {first}")
    witness_total_start = witness_rules["us_tariff_total_ad_valorem_rate"]["versions"][
        0
    ]["effective_from"]
    generated_total_first = generated_rules["schedule_statutory_stack"]["versions"][0]
    generated_total_start = generated_total_first.get(
        "effective_from", generated_total_first.get("from")
    )
    if (
        witness_total_start != WITNESS_EFFECTIVE_FROM
        or generated_total_start != WITNESS_EFFECTIVE_FROM
    ):
        raise SystemExit(f"{case_name} total effective boundaries differ")

    table = yaml.safe_load(
        (
            ROOT
            / f"us/policies/usitc/us-tariff-duty/lines/generated/{case_name}.yaml"
        ).read_text()
    )
    table_rules = {rule["name"]: rule for rule in table["rules"]}
    for suffix in ("general_rate", "column2_rate"):
        values = table_rules[f"{case_name}_{suffix}"]["versions"][0]["values"]
        if case["rate_line"] not in values:
            raise SystemExit(f"{case_name} rate-line key absent from {suffix}")
    if case_name == "ch95" and 9506624040 in table_rules["ch95_general_rate"][
        "versions"
    ][0]["values"]:
        raise SystemExit("ch95 statistical child was incorrectly used as a rate-line key")
    if case_name == "ch76":
        formula = generated_rules["mfn_ad_valorem_rate"]["versions"][0]["formula"]
        if "russia_heading_9903_90_09_rate_of_duty" not in formula:
            raise SystemExit("ch76 omits the Russian heading 9903.90.09 in-lieu branch")


def decimal_sum(values: dict[str, str], names: tuple[str, ...]) -> Decimal:
    return sum((Decimal(values[name]) for name in names), Decimal(0))


def run_case(case_name: str, case: dict) -> tuple[list[dict], list[dict]]:
    assert_case_contract(case_name, case)
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
            case,
            date,
            False,
            "us_tariff_total_ad_valorem_rate",
        )
        supported_generated[date] = evaluate_supported(
            case["artifact"],
            case["module"],
            case,
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
                        case,
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
                    case,
                    country,
                    date,
                    False,
                    "us_tariff_total_ad_valorem_rate",
                )
                generated_outputs = {
                    name: evaluate_pre_output(
                        case["artifact"],
                        case["module"],
                        case,
                        country,
                        date,
                        True,
                        name,
                    )
                    for name in COMPONENTS
                }
                generated_outputs["total"] = evaluate_pre_output(
                    case["artifact"],
                    case["module"],
                    case,
                    country,
                    date,
                    True,
                    "schedule_statutory_stack",
                )
                witness_result = {"status": "pre_effective", "outputs": witness_outputs}
                generated_result = {
                    "status": "pre_effective",
                    "outputs": generated_outputs,
                }
                mismatches: list[str] = []
                for name in (*COMPONENTS, "total"):
                    left = witness_outputs[name]
                    right = generated_outputs[name]
                    if left["status"] != right["status"]:
                        mismatches.append(name)
                    elif left["status"] == "evaluated" and Decimal(
                        left["value"]
                    ) != Decimal(right["value"]):
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
                    "status": (
                        "matching_pre_effective_unavailable"
                        if pass_cell
                        else "error_mismatch"
                    ),
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
                witness_result = supported_witness[date][country]
                generated_result = supported_generated[date][country]
                witness_values = witness_result["values"]
                generated_values = generated_result["values"]
                mismatches = [
                    name
                    for name in COMPONENTS
                    if Decimal(witness_values[name]) != Decimal(generated_values[name])
                ]
                witness_base = Decimal(witness_values["mfn_ad_valorem_rate"])
                generated_base = Decimal(generated_values["mfn_ad_valorem_rate"])
                witness_total = Decimal(
                    witness_values["us_tariff_total_ad_valorem_rate"]
                )
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
                    "witness": witness_result,
                    "generated": generated_result,
                    "comparison": row,
                }
            )

    required_cells = {(country, date) for country in COUNTRIES for date in REQUIRED_DATES}
    observed_cells = {(row["country"], row["date"]) for row in rows}
    if not required_cells <= observed_cells:
        raise SystemExit(f"{case_name} required grid incomplete")
    failures = [row for row in rows if row["verdict"] != "PASS"]

    csv_buffer = io.StringIO()
    writer = csv.DictWriter(
        csv_buffer, fieldnames=list(rows[0]), lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    (EVIDENCE / f"identity-{case_name}.csv").write_text(csv_buffer.getvalue())
    (EVIDENCE / f"identity-{case_name}-results.json").write_text(
        json.dumps(
            {
                "engine": str(ENGINE),
                "chapter": case["chapter"],
                "hts_number": case["hts_number"],
                "rate_line": case["rate_line"],
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
    if failures:
        print(json.dumps(failures[:10], indent=2))
    return rows, failures


def date_summary(rows: list[dict]) -> str:
    rendered: list[str] = []
    for date in DATES:
        subset = [row for row in rows if row["date"] == date]
        statuses = sorted({row["status"] for row in subset})
        max_delta = max(
            (abs(Decimal(row["total_delta"])) for row in subset if row["total_delta"]),
            default=Decimal(0),
        )
        rendered.append(
            f"| {date} | {len(subset)} | {', '.join(statuses)} | "
            f"{sum(bool(row['component_mismatches']) for row in subset)} | "
            f"{max_delta} | "
            f"{'PASS' if all(row['verdict'] == 'PASS' for row in subset) else 'FAIL'} |"
        )
    return "\n".join(rendered)


def main() -> int:
    missing = [
        path
        for path in [WITNESS_ARTIFACT, *(case["artifact"] for case in CASES.values())]
        if not path.is_file()
    ]
    if missing:
        raise SystemExit(f"compile artifacts before running identity gate: {missing}")

    case_rows: dict[str, list[dict]] = {}
    all_failures: list[dict] = []
    for case_name, case in CASES.items():
        rows, failures = run_case(case_name, case)
        case_rows[case_name] = rows
        all_failures.extend({"case": case_name, **failure} for failure in failures)
        print(
            f"{case_name} identity {'PASS' if not failures else 'FAIL'}: "
            f"{len(rows) - len(failures)}/{len(rows)} cells"
        )

    section232_detail: list[str] = []
    raw_ch76 = json.loads((EVIDENCE / "identity-ch76-results.json").read_text())
    for cell in raw_ch76["cells"]:
        if cell["comparison"]["status"] != "evaluated" or cell["country"] not in {
            "GB",
            "RU",
        }:
            continue
        witness_value = cell["witness"]["values"][
            "section_232_aluminum_component_rate"
        ]
        generated_value = cell["generated"]["values"][
            "section_232_aluminum_component_rate"
        ]
        expected = Decimal("2.00") if cell["country"] == "RU" else Decimal("0.25")
        if Decimal(witness_value) != expected or Decimal(generated_value) != expected:
            all_failures.append(
                {
                    "case": "ch76",
                    "date": cell["date"],
                    "country": cell["country"],
                    "section_232_binding_failure": True,
                }
            )
        section232_detail.append(
            f"| {cell['date']} | {cell['country']} | {witness_value} | "
            f"{generated_value} | {'PASS' if Decimal(witness_value) == Decimal(generated_value) == expected else 'FAIL'} |"
        )

    report = f"""# B1.3 rollout witness identity gates

Verdict: **{'PASS' if not all_failures else 'FAIL'}** — ch76 {sum(row['verdict'] == 'PASS' for row in case_rows['ch76'])}/90 cells; ch95 {sum(row['verdict'] == 'PASS' for row in case_rows['ch95'])}/90 cells.

Both independently compiled generated compositions were compared with the independently compiled hand-built witness on the pilot's same 10-country by 8-required-date grid, plus the executable boundary date 2026-02-15. Eleven component/entry-variant outputs, the General Note 3 selected base, each algebraic residual, and the total were Decimal-compared. The four pre-2026-02-15 dates retain matching structural unavailability and raw engine error classes; absence was never coerced to zero.

Chapter 76 uses statistical/rate line 7601.10.30.00 (`7601103000`). Its generated selector preserves heading 9903.90.09's proved 70-percent Russian rate in lieu of ordinary column 2, then adds the separate 200-percent section 232 aluminum component. GB binds both 25-percent UK section 232 implementations across the 2026-07-21 version boundary; CU binds ordinary column 2.

Chapter 95 feeds both compositions the witness statistical line 9506.62.40.40, while only the generated composition receives parent RATE-LINE key `9506624000`, where the General and column-2 rates legally live. Statistical child key `9506624040` is structurally absent and was never queried.

## Chapter 76 by date

| Date | Cells | Outcome | Component mismatches | Max absolute total delta | Verdict |
|---|---:|---|---:|---:|---|
{date_summary(case_rows['ch76'])}

## Chapter 95 by date

| Date | Cells | Outcome | Component mismatches | Max absolute total delta | Verdict |
|---|---:|---|---:|---:|---|
{date_summary(case_rows['ch95'])}

## Chapter 76 section 232 binding detail

| Date | Country | Witness component | Generated component | Verdict |
|---|---|---:|---:|---|
{chr(10).join(section232_detail)}

Full 90-row diffs are `identity-ch76.csv` and `identity-ch95.csv`; normalized raw engine results, including pre-effective error classes, are retained in their companion JSON files.
"""
    (EVIDENCE / "IDENTITY.md").write_text(report)
    return 1 if all_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
