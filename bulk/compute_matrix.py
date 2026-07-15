#!/usr/bin/env python3
"""Compute the bulk-encode job matrix from bulk/worklist.yaml.

The worklist is the durable queue. This script is the single source of truth
for turning it into a GitHub Actions matrix and for reading/writing entry
status, so CI and local operators behave identically.

Usage:
  # Emit a GitHub Actions matrix of pending entries (optionally capped/filtered):
  python bulk/compute_matrix.py --status pending [--batch A] [--limit 8]

  # Human-readable listing:
  python bulk/compute_matrix.py --status pending --format table

  # Read one field (used by the runner to look up backend/model per entry):
  python bulk/compute_matrix.py --get us-ny/statute/TAX/673 --field model

The matrix shape preserves the reviewed execution metadata needed by local
jobs, in addition to the citation/backend/model fields used by cloud jobs.
`slug` is the branch-safe citation slug used for `bulk/<slug>` branches and the
PR title.

Status writes are intentionally NOT done here: the workflow updates statuses by
committing to the worklist through a dedicated follow-up (so status changes are
reviewable diffs, never silent CI mutations). `--set-status` exists only for
local operator use and edits the file in place.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

WORKLIST = Path(__file__).resolve().parent / "worklist.yaml"

SELECTABLE_STATUSES = {"pending", "pending-local"}
REPO_ROOT = WORKLIST.parents[1]


def citation_slug(citation: str) -> str:
    """Branch-safe slug for a citation path.

    us-ny/statute/TAX/673 -> us-ny-statute-tax-673
    us-ca/statute/rtc/17053.6 -> us-ca-statute-rtc-17053-6
    """
    slug = citation.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def load() -> dict:
    data = yaml.safe_load(WORKLIST.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict) or "entries" not in data:
        raise SystemExit(f"{WORKLIST} is missing an 'entries' list")
    return data


def entry_backend(data: dict, entry: dict) -> str:
    return entry.get("backend") or data.get("defaults", {}).get("backend", "openai")


def entry_model(data: dict, entry: dict) -> str:
    return entry.get("model") or data.get("defaults", {}).get("model", "gpt-5.5")


def entry_allow_context(entry: dict) -> list[str]:
    """Return reviewed repo-local encoder context paths for one queue entry."""
    citation = entry.get("citation", "unknown citation")
    values = entry.get("allow_context", [])
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value and "\n" not in value for value in values
    ):
        raise ValueError(
            f"{citation}: allow_context must be a list of non-empty path strings"
        )
    root = REPO_ROOT.resolve()
    for value in values:
        path = Path(value)
        resolved = (root / path).resolve()
        if path.is_absolute() or not resolved.is_relative_to(root):
            raise ValueError(f"{citation}: allow_context path escapes the repository")
        if not resolved.is_file():
            raise ValueError(
                f"{citation}: allow_context path is not a repository file: {value}"
            )
    return values


def select(data: dict, status: str, batch: str | None, limit: int | None) -> list[dict]:
    out: list[dict] = []
    for entry in data["entries"]:
        if status != "any" and entry.get("status") != status:
            continue
        if batch and str(entry.get("batch", "")).upper() != batch.upper():
            continue
        dependencies = entry.get("requires_merged_citations", [])
        if not isinstance(dependencies, list) or not all(
            isinstance(value, str) and value for value in dependencies
        ):
            raise ValueError(
                f"{entry.get('citation')}: requires_merged_citations must be "
                "a list of non-empty strings"
            )
        program_scope_sync = entry.get("program_scope_sync")
        if program_scope_sync is not None and not isinstance(program_scope_sync, dict):
            raise ValueError(
                f"{entry.get('citation')}: program_scope_sync must be a mapping"
            )
        if program_scope_sync is not None:
            program_spec = program_scope_sync.get("program_spec")
            scope = program_scope_sync.get("scope")
            additions = program_scope_sync.get("add", [])
            removals = program_scope_sync.get("remove", [])
            if not isinstance(program_spec, str) or not program_spec:
                raise ValueError(
                    f"{entry.get('citation')}: program_scope_sync.program_spec "
                    "must be a non-empty string"
                )
            if scope not in {"federal", "state", "local"}:
                raise ValueError(
                    f"{entry.get('citation')}: program_scope_sync.scope must be "
                    "federal, state, or local"
                )
            for field, values in (("add", additions), ("remove", removals)):
                if not isinstance(values, list) or not all(
                    isinstance(value, str) and value and "\n" not in value
                    for value in values
                ):
                    raise ValueError(
                        f"{entry.get('citation')}: program_scope_sync.{field} "
                        "must be a list of non-empty strings"
                    )
            if not additions and not removals:
                raise ValueError(
                    f"{entry.get('citation')}: program_scope_sync must add or "
                    "remove at least one module"
                )
        out.append(
            {
                "citation": entry["citation"],
                "repo": entry.get("repo", "rulespec-us"),
                "backend": entry_backend(data, entry),
                "model": entry_model(data, entry),
                "acceptance_criteria": entry.get("note", ""),
                "slug": citation_slug(entry["citation"]),
                "allow_context": entry_allow_context(entry),
                "requires_merged_citations": dependencies,
                "program_scope_sync": program_scope_sync,
            }
        )
    if limit is not None:
        out = out[:limit]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--status", default="pending", help="Entry status to select (or 'any').")
    ap.add_argument("--batch", default=None, help="Restrict to a batch label (A, B, ...).")
    ap.add_argument("--limit", type=int, default=None, help="Cap the number of entries.")
    ap.add_argument(
        "--format",
        choices=["matrix", "table", "count"],
        default="matrix",
        help="matrix = GitHub Actions include JSON; table = human listing.",
    )
    ap.add_argument("--get", default=None, help="Look up a single citation's entry.")
    ap.add_argument("--field", default=None, help="With --get, print one field (model/backend/status/slug).")
    ap.add_argument(
        "--set-status",
        nargs=2,
        metavar=("CITATION", "STATUS"),
        default=None,
        help="LOCAL ONLY: set an entry's status in place.",
    )
    args = ap.parse_args()

    if args.status not in SELECTABLE_STATUSES | {"any"}:
        raise SystemExit(
            f"unsupported selectable status: {args.status}; expected one of "
            f"{', '.join(sorted(SELECTABLE_STATUSES | {'any'}))}"
        )

    data = load()

    if args.set_status:
        citation, new_status = args.set_status
        found = False
        for entry in data["entries"]:
            if entry["citation"] == citation:
                entry["status"] = new_status
                found = True
                break
        if not found:
            raise SystemExit(f"citation not found: {citation}")
        WORKLIST.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        print(f"set {citation} -> {new_status}")
        return 0

    if args.get:
        for entry in data["entries"]:
            if entry["citation"] == args.get:
                if args.field == "slug":
                    print(citation_slug(entry["citation"]))
                elif args.field == "model":
                    print(entry_model(data, entry))
                elif args.field == "backend":
                    print(entry_backend(data, entry))
                elif args.field:
                    print(entry.get(args.field, ""))
                else:
                    print(json.dumps(entry))
                return 0
        raise SystemExit(f"citation not found: {args.get}")

    selected = select(data, args.status, args.batch, args.limit)

    if args.format == "count":
        print(len(selected))
    elif args.format == "table":
        for item in selected:
            print(f"{item['slug']:34s} {item['backend']}:{item['model']:10s} {item['citation']}")
        print(f"\n{len(selected)} entr{'y' if len(selected) == 1 else 'ies'} selected (status={args.status}).")
    else:
        print(json.dumps({"include": selected}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
