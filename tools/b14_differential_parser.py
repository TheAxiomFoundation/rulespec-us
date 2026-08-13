#!/usr/bin/env python3
"""Independent B1.4 differential parser for the pinned USITC HTS snapshot.

This program intentionally does not import or read the first-path generator,
its manifest, or any intermediate artifact.  Its only substantive inputs are
the retained USITC JSON bytes and the published generated module YAML files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = Path("/Users/maxghenis/TheAxiomFoundation/axiom-corpus-b1-full")
SNAPSHOT_RELATIVE = Path(
    "data/corpus/sources/us/statute/"
    "2026-08-09-usitc-hts-2026-rev15-full-schedule/"
    "usitc-hts/hts_2026_revision_15_json.json"
)
SNAPSHOT_SHA256 = "59a76c12e28d7a28975f31a8876bfb08e64927b922fe2b4f88801ff4459181e6"
MODULE_DIR = ROOT / "us/policies/usitc/us-tariff-duty/lines/generated"

PLAIN_PERCENT = re.compile(r"(?P<number>[0-9]+(?:\.[0-9]+)?)%\Z")
NAMED_COMPONENT_PERCENT = re.compile(r"%\s+on\s+the\s+", re.IGNORECASE)
QUANTITY_RATE = re.compile(
    r"(?:[¢$]|\bcents?\b|/(?:kg|liter|t\b|barrel|doz))", re.IGNORECASE
)
TABLE_SUFFIXES = {
    "general_rate",
    "column2_rate",
    "general_disposition",
    "column2_disposition",
}


def disposition(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "empty"
    if text == "Free":
        return "free"
    if PLAIN_PERCENT.fullmatch(text):
        return "ad_valorem"
    if NAMED_COMPONENT_PERCENT.search(text):
        return "component"
    quantity = bool(QUANTITY_RATE.search(text))
    if quantity and "%" in text:
        return "compound"
    if quantity:
        return "specific"
    return "conditional"


def percent_fraction(value: object) -> Decimal | None:
    match = PLAIN_PERCENT.fullmatch(str(value or "").strip())
    if not match:
        return None
    return Decimal(match.group("number")) / Decimal(100)


def numeric_key(hts_number: str) -> int:
    compact = "".join(char for char in hts_number if char.isdigit())
    if not compact or len(compact) > 10:
        raise ValueError(f"invalid HTS number {hts_number!r}")
    return int(compact.ljust(10, "0"))


def source_excerpt(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "htsno": row.get("htsno"),
        "indent": row.get("indent"),
        "description": row.get("description"),
        "general": row.get("general"),
        "other": row.get("other"),
    }


def parse_snapshot(raw: bytes) -> tuple[dict[int, dict[str, Any]], list[str]]:
    document = json.loads(raw)
    if not isinstance(document, list):
        raise SystemExit("snapshot root is not a row list")

    rated: dict[int, dict[str, Any]] = {}
    collisions: list[str] = []
    # Track the active rated provision at each indentation level separately
    # from rated-line selection.  This independently checks that an unrated
    # ten-digit statistical row is a child, rather than a rate-bearing line.
    active: list[tuple[int, int | None]] = []
    for row in document:
        hts = str(row.get("htsno") or "").strip()
        level = int(row.get("indent") or 0)
        while active and active[-1][0] >= level:
            active.pop()

        general_text = str(row.get("general") or "").strip()
        column2_text = str(row.get("other") or "").strip()
        is_rated = bool(hts and (general_text or column2_text))
        owner: int | None = None
        if is_rated:
            owner = numeric_key(hts)
            general_class = disposition(general_text)
            column2_class = disposition(column2_text)
            cells: dict[str, object] = {
                "general_disposition": general_class,
                "column2_disposition": column2_class,
            }
            if general_class in {"ad_valorem", "free"}:
                cells["general_rate"] = (
                    Decimal(0)
                    if general_class == "free"
                    else percent_fraction(general_text)
                )
            if column2_class in {"ad_valorem", "free"}:
                cells["column2_rate"] = (
                    Decimal(0)
                    if column2_class == "free"
                    else percent_fraction(column2_text)
                )
            record = {"htsno": hts, "cells": cells, "source": source_excerpt(row)}
            if owner in rated:
                collisions.append(f"{owner}: {rated[owner]['htsno']} and {hts}")
            rated[owner] = record
        elif hts and len("".join(c for c in hts if c.isdigit())) == 10:
            # Resolve the nearest rated ancestor as a structural cross-check;
            # importantly, do not emit this statistical child as a rated line.
            _nearest_rated_ancestor = next(
                (candidate for _, candidate in reversed(active) if candidate is not None),
                None,
            )
        active.append((level, owner))
    return rated, collisions


def scalar_equal(expected: object, actual: object) -> bool:
    if isinstance(expected, str) or isinstance(actual, str):
        return type(expected) is type(actual) and expected == actual
    try:
        return Decimal(str(expected)) == Decimal(str(actual))
    except Exception:
        return expected == actual


def first(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    return items[0] if items else None


def compare_module(
    path: Path, rated: dict[int, dict[str, Any]]
) -> tuple[dict[str, Any], set[int]]:
    module = yaml.safe_load(path.read_text())
    tables: list[dict[str, Any]] = []
    module_keys: set[int] = set()
    for rule in module.get("rules", []):
        name = str(rule.get("name") or "")
        suffix = next((s for s in TABLE_SUFFIXES if name.endswith("_" + s)), None)
        versions = rule.get("versions") or []
        if suffix is None or not versions or "values" not in versions[0]:
            continue
        published = versions[0]["values"] or {}
        missing: list[dict[str, Any]] = []
        mismatched: list[dict[str, Any]] = []
        matches = 0
        for raw_key, expected in published.items():
            key = int(raw_key)
            module_keys.add(key)
            derived = rated.get(key)
            if derived is None or suffix not in derived["cells"]:
                missing.append(
                    {"key": key, "published": expected, "derived": None, "source": None}
                )
                continue
            actual = derived["cells"][suffix]
            if scalar_equal(expected, actual):
                matches += 1
            else:
                mismatched.append(
                    {
                        "key": key,
                        "published": expected,
                        "derived": str(actual) if isinstance(actual, Decimal) else actual,
                        "source": derived["source"],
                    }
                )
        tables.append(
            {
                "name": name,
                "published_cells": len(published),
                "match_cells": matches,
                "missing_derived_count": len(missing),
                "mismatched_count": len(mismatched),
                "first_missing_derived": first(missing),
                "first_mismatch": first(mismatched),
            }
        )
    return {
        "module": path.name.removesuffix(".yaml"),
        "published_cells": sum(t["published_cells"] for t in tables),
        "match_cells": sum(t["match_cells"] for t in tables),
        "missing_derived_count": sum(t["missing_derived_count"] for t in tables),
        "mismatched_count": sum(t["mismatched_count"] for t in tables),
        "tables": tables,
    }, module_keys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--chapters",
        default="",
        help="comma-separated chapter/module selectors (for example 72,76,95)",
    )
    args = parser.parse_args()

    snapshot_path = args.corpus / SNAPSHOT_RELATIVE
    raw = snapshot_path.read_bytes()
    snapshot_sha = hashlib.sha256(raw).hexdigest()
    if snapshot_sha != SNAPSHOT_SHA256:
        raise SystemExit(f"snapshot sha256 mismatch: {snapshot_sha}")
    rated, collisions = parse_snapshot(raw)

    selectors = {item.strip().lower() for item in args.chapters.split(",") if item.strip()}
    module_paths = sorted(
        path
        for path in MODULE_DIR.glob("ch*.yaml")
        if not path.name.endswith(".test.yaml")
        and (
            not selectors
            or path.stem.lower().removeprefix("ch") in selectors
            or path.stem.lower().removeprefix("ch")[:2] in selectors
        )
    )
    chapter_reports: list[dict[str, Any]] = []
    published_rated_keys: set[int] = set()
    for path in module_paths:
        chapter_report, module_keys = compare_module(path, rated)
        chapter_reports.append(chapter_report)
        published_rated_keys.update(module_keys)

    if selectors:
        selected_prefixes = {s[:2].zfill(2) for s in selectors}
        derived_scope = {
            key for key, record in rated.items()
            if "".join(c for c in record["htsno"] if c.isdigit())[:2] in selected_prefixes
        }
    else:
        derived_scope = set(rated)
    extra_derived_keys = sorted(derived_scope - published_rated_keys)
    missing_derived_total = sum(c["missing_derived_count"] for c in chapter_reports)
    mismatched_total = sum(c["mismatched_count"] for c in chapter_reports)
    exact = not collisions and not extra_derived_keys and not missing_derived_total and not mismatched_total
    report = {
        "verdict": "PASS" if exact else "FAIL",
        "scope": sorted(selectors) if selectors else "all",
        "snapshot": str(snapshot_path),
        "snapshot_sha256": snapshot_sha,
        "module_count": len(module_paths),
        "rated_line_count": len(derived_scope),
        "published_rated_line_count": len(published_rated_keys),
        "published_cell_count": sum(c["published_cells"] for c in chapter_reports),
        "match_cell_count": sum(c["match_cells"] for c in chapter_reports),
        "missing_derived_count": missing_derived_total,
        "extra_derived_count": len(extra_derived_keys),
        "mismatched_count": mismatched_total,
        "key_collision_count": len(collisions),
        "first_key_collision": collisions[0] if collisions else None,
        "first_extra_derived": (
            {
                "key": extra_derived_keys[0],
                "source": rated[extra_derived_keys[0]]["source"],
            }
            if extra_derived_keys else None
        ),
        "chapters": chapter_reports,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(
        f"{report['verdict']}: {report['match_cell_count']}/{report['published_cell_count']} "
        f"cells; {len(published_rated_keys)}/{len(derived_scope)} rated lines; "
        f"{len(module_paths)} modules"
    )
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
