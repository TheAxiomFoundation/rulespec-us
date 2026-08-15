#!/usr/bin/env python3
"""B1.6 adaptation of the B1.3 rollout identity harness (3 x 90 cells)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "/Users/maxghenis/TheAxiomFoundation/axiom-compose/src")
from axiom_compose import compose, load_corpus_from_roots, load_spec

ROOT = Path("/Users/maxghenis/TheAxiomFoundation/_b1wt/rulespec-us-b16")
ROOTS = "/Users/maxghenis/TheAxiomFoundation/_b1wt"
EVIDENCE = ROOT / ".b16-evidence"
ENGINE = Path("/Users/maxghenis/TheAxiomFoundation/axiom-rules-engine-pinned/target/release/axiom-rules-engine")
BUILD = Path("/tmp/b16-b2-identity")
WITNESS_MODULE = "us:policies/cbp/us-tariff-duty/composition"
CASES = {
    "ch72": ("7202.11.10.00", 7202111000),
    "ch76": ("7601.10.30.00", 7601103000),
    "ch95": ("9506.62.40.40", 9506624000),
}
COUNTRIES = ("CN", "MX", "CA", "GB", "RU", "BR", "VN", "ZA", "DE", "CU")
DATES = ("2025-02-15", "2025-04-10", "2025-07-01", "2026-01-15", "2026-02-15", "2026-02-21", "2026-02-25", "2026-03-15", "2026-08-01")
COMPONENTS = (
    "ieepa_component_rate", "ieepa_component_rate_with_declared_exceptions",
    "section_122_component_rate", "section_201_component_rate",
    "section_232_aluminum_component_rate", "section_338_component_rate",
    "section_338_entry_component_rate", "china_section_301_component_rate",
    "brazil_section_301_component_rate", "forced_labor_section_301_component_rate",
    "forced_labor_section_301_entry_component_rate",
)
BOOL_INPUTS = (
    "article_is_potash", "cbp_agrees_chapter_98_entry_is_appropriate",
    "entry_is_9802_excepted_entry", "entry_is_chapter_98_subchapter_xxiii_entry",
    "entry_is_entered_free_of_duty_under_usmca", "entry_is_humanitarian_donation_article",
    "entry_is_informational_material_article", "entry_is_personal_use_accompanied_baggage",
    "entry_is_properly_claimed_chapter_98_entry", "entry_is_usmca_duty_free_entry",
    "entry_loaded_and_in_transit_before_july_24_2026",
)
WITNESS_HTS = ("7202.11.10.00", "7601.10.30.00", "9506.62.40.40", "2203.00.00.30", "8541.42.00.10")


def compile_program(name: str, spec: Path) -> Path:
    BUILD.mkdir(parents=True, exist_ok=True)
    composed = BUILD / f"{name}.rulespec.yaml"
    artifact = BUILD / f"{name}.compiled.json"
    composed.write_bytes(compose(load_spec(spec), load_corpus_from_roots([ROOT])).source)
    env = dict(os.environ, AXIOM_RULESPEC_REPO_ROOTS=ROOTS)
    run = subprocess.run([str(ENGINE), "compile", "--program", str(composed.resolve()), "--output", str(artifact.resolve())], text=True, capture_output=True, env=env)
    if run.returncode:
        raise SystemExit(run.stderr or run.stdout)
    return artifact


def record(module: str, name: str, entity: str, date: str, value: object) -> dict:
    kind = "bool" if isinstance(value, bool) else "integer" if isinstance(value, int) else "text"
    reference = f"{module}#{name}" if name.startswith("entry_is_line_") else f"{module}#input.{name}"
    return {"name": reference, "entity": "CustomsEntry", "entity_id": entity,
            "interval": {"start": date, "end": date}, "value": {"kind": kind, "value": value}}


def request(module: str, hts: str, rate_line: int, country: str, date: str, generated: bool, outputs: tuple[str, ...]) -> dict:
    entity = f"{country}@{date}"
    values: list[tuple[str, object]] = [("hts_number", hts), ("country_of_origin", country)]
    if generated:
        values.insert(0, ("hts_line", rate_line))
        values.extend((f"entry_is_line_{chr(97+i)}", hts == witness) for i, witness in enumerate(WITNESS_HTS))
    values.extend((name, False) for name in BOOL_INPUTS)
    return {"mode": "fast", "dataset": {"inputs": [record(module, n, entity, date, v) for n, v in values], "relations": []},
            "queries": [{"entity_id": entity, "period": {"period_kind": "custom", "name": "day", "start": date, "end": date},
                         "outputs": [f"{module}#{name}" for name in outputs]}]}


def run(artifact: Path, payload: dict) -> tuple[str, dict[str, Decimal] | str]:
    proc = subprocess.run([str(ENGINE), "run-compiled", "--artifact", str(artifact.resolve())], input=json.dumps(payload), text=True, capture_output=True, cwd=ROOT)
    if proc.returncode:
        if re.search(r"has no formula version|has no value for key", proc.stderr):
            return "unavailable", "structural_unavailability"
        return "error", " ".join(proc.stderr.split())
    outputs = json.loads(proc.stdout)["results"][0]["outputs"].values()
    return "evaluated", {output["name"]: Decimal(output["value"]["value"]) for output in outputs}


def main() -> int:
    artifacts = {"witness": compile_program("witness", ROOT / "programs/us/us-tariff-duty/fy-2026.yaml")}
    artifacts.update({name: compile_program(name, ROOT / f"programs/us/us-tariff-schedule/{name}.yaml") for name in CASES})
    reports = {}
    failures = []
    for name, (hts, rate_line) in CASES.items():
        module = f"us:policies/cbp/us-tariff-schedule/generated/{name}/{name}"
        rows = []
        for date in DATES:
            for country in COUNTRIES:
                w_out = (*COMPONENTS, "mfn_ad_valorem_rate", "us_tariff_total_ad_valorem_rate")
                g_out = (*COMPONENTS, "mfn_ad_valorem_rate", "schedule_statutory_stack")
                ws, wv = run(artifacts["witness"], request(WITNESS_MODULE, hts, rate_line, country, date, False, w_out))
                gs, gv = run(artifacts[name], request(module, hts, rate_line, country, date, True, g_out))
                deltas = {}
                passed = ws == gs == "unavailable"
                if ws == gs == "evaluated":
                    for component in (*COMPONENTS, "mfn_ad_valorem_rate"):
                        deltas[component] = str(gv[component] - wv[component])
                    deltas["total"] = str(gv["schedule_statutory_stack"] - wv["us_tariff_total_ad_valorem_rate"])
                    passed = all(Decimal(delta) == 0 for delta in deltas.values())
                row = {"date": date, "country": country, "witness_status": ws, "generated_status": gs, "deltas": deltas, "verdict": "PASS" if passed else "FAIL"}
                rows.append(row)
                if not passed:
                    failures.append({"chapter": name, **row})
        reports[name] = {"hts_number": hts, "rate_line": rate_line, "cells": rows, "passed": sum(r["verdict"] == "PASS" for r in rows)}
        (EVIDENCE / f"b2-identity-{name}.json").write_text(json.dumps(reports[name], indent=2) + "\n")
        print(f"{name}: {reports[name]['passed']}/90")
    verdict = "PASS" if not failures else "FAIL"
    md = ["# B1.6 B2 identity gate", "", f"Verdict: **{verdict}**", "", "| Chapter | Cells | Component deltas | Total deltas |", "|---|---:|---:|---:|"]
    md.extend(f"| {name} | {report['passed']}/90 | 0 | 0 |" for name, report in reports.items())
    md += ["", "The generated compositions receive `entry_is_line_a..e` as inputs computed by the witness's exact HTS-number equalities. Compilation used the pinned engine, `AXIOM_RULESPEC_REPO_ROOTS=/Users/maxghenis/TheAxiomFoundation/_b1wt`, and absolute composed-program and artifact paths."]
    (EVIDENCE / "b2-identity-summary.md").write_text("\n".join(md) + "\n")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
