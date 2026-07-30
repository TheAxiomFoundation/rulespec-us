#!/usr/bin/env python3
"""Run explicit-identity relation probes against a compiled RuleSpec artifact."""

from __future__ import annotations

import argparse
import calendar
import json
import subprocess
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml


def scalar(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"kind": "bool", "value": value}
    if isinstance(value, int):
        return {"kind": "integer", "value": value}
    if isinstance(value, float):
        return {"kind": "decimal", "value": str(value)}
    if isinstance(value, date):
        return {"kind": "date", "value": value.isoformat()}
    if isinstance(value, str):
        return {"kind": "text", "value": value}
    raise TypeError(f"unsupported scalar {value!r}")


def month_period(raw: str) -> dict[str, str]:
    year, month = (int(part) for part in raw.split("-", 1))
    return {
        "period_kind": "month",
        "start": f"{year:04d}-{month:02d}-01",
        "end": f"{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}",
    }


def normalized_output(raw: dict[str, Any]) -> Any:
    if raw.get("kind") == "judgment":
        return raw.get("outcome")
    value = raw.get("value") or {}
    kind = value.get("kind")
    if kind == "integer":
        return int(value["value"])
    if kind == "decimal":
        return str(Decimal(str(value["value"])))
    return value.get("value")


def run_case(
    case: dict[str, Any],
    *,
    engine: Path,
    artifact: Path,
) -> dict[str, Any]:
    period = month_period(str(case["period"]))
    interval = {"start": period["start"], "end": period["end"]}
    inputs: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []

    for name, value in case["input"].items():
        if isinstance(value, list) and "#relation." in str(name):
            for index, source_row in enumerate(value):
                row = dict(source_row)
                entity_id = str(row.pop("_entity_id", f"related_{index}"))
                relations.append(
                    {
                        "name": str(name),
                        "tuple": [entity_id, "case"],
                        "interval": interval,
                    }
                )
                for input_name, input_value in row.items():
                    inputs.append(
                        {
                            "name": str(input_name),
                            "entity": "Entity",
                            "entity_id": entity_id,
                            "interval": interval,
                            "value": scalar(input_value),
                        }
                    )
            continue
        inputs.append(
            {
                "name": str(name),
                "entity": "Entity",
                "entity_id": "case",
                "interval": interval,
                "value": scalar(value),
            }
        )

    expected_queries: list[tuple[str, dict[str, Any]]] = [
        ("case", dict(case.get("output") or {}))
    ]
    expected_queries.extend(
        (str(entity_id), dict(outputs))
        for entity_id, outputs in (case.get("member_output") or {}).items()
    )
    request = {
        "mode": "explain",
        "dataset": {"inputs": inputs, "relations": relations},
        "queries": [
            {
                "entity_id": entity_id,
                "period": period,
                "outputs": list(expected),
            }
            for entity_id, expected in expected_queries
        ],
    }
    completed = subprocess.run(
        [str(engine), "run-compiled", "--artifact", str(artifact)],
        input=json.dumps(request),
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode:
        return {
            "name": case["name"],
            "success": False,
            "engine_error": completed.stderr.strip() or completed.stdout.strip(),
        }

    results = json.loads(completed.stdout)["results"]
    actual_by_entity: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for (entity_id, expected), result in zip(expected_queries, results, strict=True):
        actual = {
            output_id: normalized_output(result["outputs"][output_id])
            for output_id in expected
        }
        actual_by_entity[entity_id] = actual
        for output_id, expected_value in expected.items():
            actual_value = actual[output_id]
            if isinstance(expected_value, (int, float)) and not isinstance(
                expected_value, bool
            ):
                matches = Decimal(str(actual_value)) == Decimal(str(expected_value))
            else:
                matches = actual_value == expected_value
            if not matches:
                failures.append(
                    f"{entity_id} {output_id}: expected {expected_value!r}, "
                    f"got {actual_value!r}"
                )
    return {
        "name": case["name"],
        "success": not failures,
        "actual": actual_by_entity,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()

    fixture = yaml.safe_load(args.fixtures.read_text())
    results = [
        run_case(case, engine=args.engine, artifact=args.artifact)
        for case in fixture["cases"]
    ]
    payload = {"success": all(result["success"] for result in results), "cases": results}
    print(json.dumps(payload, indent=2))
    return 0 if payload["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
