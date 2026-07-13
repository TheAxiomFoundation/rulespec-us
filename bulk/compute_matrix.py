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

The matrix shape is {"include": [{"citation", "repo", "backend", "model",
"encoder_ref", "slug"}, ...]}. `slug` is the branch-safe citation slug used for
`bulk/<slug>` branches and the PR title.

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

SELECTABLE_STATUSES = {"pending"}
APPROVED_ENCODER_REFS = {"fed5f3df343cd7548809d1c944a17f96c7c52a68"}


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


def entry_encoder_ref(data: dict, entry: dict) -> str:
    encoder_ref = entry.get("encoder_ref") or data.get("defaults", {}).get(
        "encoder_ref", ""
    )
    if encoder_ref and not re.fullmatch(r"[0-9a-f]{40}", str(encoder_ref)):
        raise ValueError(
            f"encoder_ref for {entry.get('citation', '<unknown>')} must be a full "
            "40-character lowercase commit SHA"
        )
    if encoder_ref and str(encoder_ref) not in APPROVED_ENCODER_REFS:
        raise ValueError(
            f"encoder_ref for {entry.get('citation', '<unknown>')} is not in the "
            "reviewed compatibility allowlist"
        )
    return str(encoder_ref)


def select(data: dict, status: str, batch: str | None, limit: int | None) -> list[dict]:
    out: list[dict] = []
    for entry in data["entries"]:
        if status != "any" and entry.get("status") != status:
            continue
        if batch and str(entry.get("batch", "")).upper() != batch.upper():
            continue
        out.append(
            {
                "citation": entry["citation"],
                "repo": entry.get("repo", "rulespec-us"),
                "backend": entry_backend(data, entry),
                "model": entry_model(data, entry),
                "encoder_ref": entry_encoder_ref(data, entry),
                "slug": citation_slug(entry["citation"]),
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
                elif args.field == "encoder_ref":
                    print(entry_encoder_ref(data, entry))
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
