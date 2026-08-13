#!/usr/bin/env python3
"""Generate the full-schedule HTS rate tables — us-tariff-duty lines/generated.

Deterministic reproducer: reads the corpus-pinned USITC full-schedule
snapshot (retained bytes of corpus version
2026-08-09-usitc-hts-2026-rev15-full-schedule, sha pinned below), builds
the rate spine (indent-hierarchy walk + total rate-text disposition
partition), and emits per-chapter rulespec/v1 indexed-parameter shards
with per-cell proof atoms plus companion tests under
us/policies/usitc/us-tariff-duty/lines/generated/.

Self-gates, all hard failures:
  - snapshot sha pin
  - key-collision freedom (both key spaces)
  - witness identity: generated cells must equal the hand-built witness
    modules' encoded rates (expectations parsed from those YAMLs)
  - pinned line/member censuses
  - double-emit determinism

Usage:
  uv run python tools/generate_hts_rate_tables.py \
      [--corpus <axiom-corpus checkout>] [--check]

--check regenerates into a temp dir and fails if anything differs from
the committed files (CI-friendly drift guard). Hand edits prohibited.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import defaultdict
from pathlib import Path

GENERATOR_VERSION = "b1.2-tables-3"
EFFECTIVE_FROM = "2025-01-01"
CITATION_ROOT = "us/statute/hts"
SNAPSHOT_LABEL = "2026HTSRev15"
SNAPSHOT_SHA256 = "59a76c12e28d7a28975f31a8876bfb08e64927b922fe2b4f88801ff4459181e6"
SNAPSHOT_RELPATH = (
    "data/corpus/sources/us/statute/2026-08-09-usitc-hts-2026-rev15-full-schedule/"
    "usitc-hts/hts_2026_revision_15_json.json"
)
REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "us/policies/usitc/us-tariff-duty/lines/generated"
WITNESS_DIR = REPO_ROOT / "us/policies/usitc/us-tariff-duty/lines"
EXPECTED_LINES = 13_790
EXPECTED_MEMBERS = 19_948
EXPECTED_UNOWNED = ["9802.00.91.00"]

AD_VALOREM_RE = re.compile(r"^(\d+(?:\.\d+)?)%$")
# Currency/quantity markers that make a rate specific or compound.
SPECIFIC_MARK = re.compile(
    r"[¢$]|\bcents?\b|/(?:kg|liter|t\b|barrel|doz)", re.IGNORECASE
)
# Component-valued: percentages applied to named components of the article.
COMPONENT_MARK = re.compile(r"%\s+on\s+the\s+", re.IGNORECASE)


def digits(htsno: str) -> str:
    return htsno.replace(".", "")


def classify(text: str) -> str:
    """Total partition of general/column-2 rate text."""
    t = (text or "").strip()
    if not t:
        return "empty"
    if t == "Free":
        return "free"
    if AD_VALOREM_RE.fullmatch(t):
        return "ad_valorem"
    if COMPONENT_MARK.search(t):
        return "component"
    has_specific = bool(SPECIFIC_MARK.search(t))
    has_pct = "%" in t
    if has_specific and has_pct:
        return "compound"
    if has_specific:
        return "specific"
    return "conditional"


def ad_valorem_fraction(text: str) -> str | None:
    """Percent text -> exact decimal fraction string ("1.4%" -> "0.014")."""
    m = AD_VALOREM_RE.fullmatch((text or "").strip())
    if not m:
        return None
    whole, _, frac = m.group(1).partition(".")
    scaled = (whole + frac).lstrip("0") or "0"
    places = len(frac) + 2
    if len(scaled) <= places:
        return "0." + scaled.zfill(places)
    return scaled[:-places] + "." + scaled[-places:]


def build_spine(records: list[dict]) -> tuple[list[dict], list[str]]:
    """Walk the schedule in document order, assigning each statistical
    line its rate-bearing ancestor-or-self via the indent hierarchy.

    Returns (rated lines, unowned stat lines). Unowned = 10-digit lines
    with no rated ancestor (chapter 98/99 structural rows); they are
    returned explicitly so no line ever drops silently.
    """
    spine: dict[str, dict] = {}
    unowned: list[str] = []
    # Stack of (indent, htsno-with-rate) for ancestor resolution.
    stack: list[tuple[int, str | None]] = []
    for rec in records:
        htsno = rec.get("htsno") or ""
        indent = int(rec.get("indent") or 0)
        rated = bool(
            (rec.get("general") or "").strip() or (rec.get("other") or "").strip()
        )
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if rated and htsno:
            gen, col2 = rec.get("general") or "", rec.get("other") or ""
            spine[htsno] = {
                "htsno": htsno,
                "general_text": gen.strip(),
                "general_disposition": classify(gen),
                "general_rate": ad_valorem_fraction(gen),
                "column2_text": (col2 or "").strip(),
                "column2_disposition": classify(col2),
                "column2_rate": ad_valorem_fraction(col2),
                "special_text": (rec.get("special") or "").strip(),
                "units": rec.get("units") or [],
                "footnotes": [
                    {
                        "columns": f.get("columns"),
                        "value": (f.get("value") or "").strip(),
                        "type": f.get("type"),
                    }
                    for f in (rec.get("footnotes") or [])
                ],
                "stat_members": [],
            }
            if len(digits(htsno)) == 10:
                spine[htsno]["stat_members"].append(htsno)
        elif htsno and len(digits(htsno)) == 10:
            # Unrated statistical line: inherits nearest rated ancestor.
            owner = next((h for _, h in reversed(stack) if h), None)
            if owner:
                spine[owner]["stat_members"].append(htsno)
            else:
                unowned.append(htsno)
        stack.append((indent, htsno if rated and htsno else None))
    return sorted(spine.values(), key=lambda r: digits(r["htsno"])), sorted(unowned)


BODY_FIELD_LABELS = (
    ("Rates of duty (1-General)", "general"),
    ("Rates of duty (1-Special)", "special"),
    ("Rates of duty (2)", "other"),
    ("Additional duties", "additionalDuties"),
    ("Quota quantity", "quotaQuantity"),
)


def row_body_lines(row: dict) -> list[str]:
    lines = [str(row.get("description") or "").strip()]
    units = [str(u).strip() for u in row.get("units") or [] if str(u).strip()]
    if units:
        lines.append("Unit of quantity: " + ", ".join(units))
    for label, field in BODY_FIELD_LABELS:
        value = str(row.get(field) or "").strip()
        if value:
            lines.append(f"{label}: {value}")
    for fn in row.get("footnotes") or []:
        columns = ",".join(str(c) for c in fn.get("columns") or [] if str(c))
        value = str(fn.get("value") or "").strip()
        if value:
            lines.append(f"Footnote [{columns}]: {value}")
    return lines


def q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


class ChapterEmitter:
    def __init__(
        self, chapter: str, lines: list[dict], bodies: dict[str, list[str]], label: str
    ):
        self.ch = chapter
        self.lines = lines
        self.bodies = bodies
        self.label = label

    def _excerpt(self, htsno: str, prefix: str) -> str:
        """The verbatim body line starting with prefix, else the description line."""
        for line in self.bodies[htsno]:
            if line.startswith(prefix):
                return line
        return self.bodies[htsno][0]

    def _atoms(self, entries: list[tuple[str, str]]) -> list[str]:
        out = [
            "    metadata:",
            "      proof:",
            "        atoms:",
        ]
        for htsno, excerpt in entries:
            out.append("          - path: versions[0].values")
            out.append("            kind: parameter")
            out.append("            source:")
            out.append(f"              corpus_citation_path: {CITATION_ROOT}/{htsno}")
            out.append(f"              excerpt: {q(excerpt)}")
        return out

    def _table(
        self,
        name: str,
        dtype: str,
        rows: list[tuple[str, object]],
        atom_entries: list[tuple[str, str]],
        source_note: str,
    ) -> list[str]:
        if not rows:
            # A chapter with no qualifying rows gets no table at all —
            # an empty values map or empty atoms list is a compile error.
            return []
        out = [
            f"  - name: {name}",
            "    kind: parameter",
            f"    dtype: {dtype}",
            "    indexed_by: hts_line",
            f"    source: {source_note}",
        ]
        out.extend(self._atoms(atom_entries))
        out.append("    versions:")
        out.append(f"      - effective_from: '{EFFECTIVE_FROM}'")
        out.append("        values:")
        for key_htsno, rendered in rows:
            out.append(f"          {intkey(key_htsno)}: {rendered}")
        return out

    def module(self) -> str:
        ch = self.ch
        av_free = [
            r for r in self.lines if r["general_disposition"] in ("ad_valorem", "free")
        ]
        col2_av_free = [
            r for r in self.lines if r["column2_disposition"] in ("ad_valorem", "free")
        ]
        source_note = (
            f"USITC HTS {self.label}, chapter {ch} rate columns "
            f"(corpus {CITATION_ROOT}, full-schedule scope)"
        )

        cited = sorted({r["htsno"] for r in self.lines}, key=intkey)
        out = [
            "format: rulespec/v1",
            "module:",
            "  proof_validation:",
            "    required: true",
            "  source_verification:",
            "    corpus_citation_paths:",
            *[f"      - {CITATION_ROOT}/{h}" for h in cited],
            "  deferred_outputs:",
            f"    - output: us:policies/usitc/us-tariff-duty/lines/generated/ch{ch}#ch{ch}_applied_line_duty",
            "      reason: |-",
            "        Applying a line's rate to an entry (including column-2 status,",
            "        special-program claims, and the non-ad-valorem dispositions the",
            "        disposition tables classify) is the composition layer's work;",
            "        these tables publish the statutory columns and their",
            "        classification only. The applied per-entry duty output lands",
            "        with the composition wiring (rulespec-us#1190, B1.3).",
            "      source_values:",
            f"        - us:policies/usitc/us-tariff-duty/lines/generated/ch{ch}#ch{ch}_general_disposition",
            f"        - us:policies/usitc/us-tariff-duty/lines/generated/ch{ch}#ch{ch}_column2_disposition",
            "  summary: |-",
            f"    Generated chapter {ch} base-rate tables from the corpus-pinned USITC",
            f"    snapshot {self.label} (generator {GENERATOR_VERSION}; deterministic; hand",
            "    edits prohibited - regenerate instead). Index keys are the HTS number's",
            "    digits zero-padded to 10 as an integer (7202.11.10.00 -> 7202111000).",
            "    Rate tables cover ad-valorem and Free lines (Free = 0); lines whose",
            "    column text is a specific, compound, component-valued, or conditional",
            "    duty carry no rate cell and are classified in the disposition tables",
            "    (values: ad_valorem, free, specific, compound, component, conditional,",
            "    empty), with the raw column text preserved in the cited provision body.",
            "    The 10-digit statistical-line membership map (member -> rate-bearing",
            "    ancestor) is structural, not statutory, and ships as a generated data",
            "    artifact for the composition layer rather than as a parameter table.",
            "rules:",
        ]

        out.extend(
            self._table(
                f"ch{ch}_general_rate",
                "Rate",
                [
                    (
                        r["htsno"],
                        r["general_rate"] if r["general_rate"] is not None else "0",
                    )
                    for r in av_free
                ],
                [
                    (
                        r["htsno"],
                        self._excerpt(r["htsno"], "Rates of duty (1-General):"),
                    )
                    for r in av_free
                ],
                source_note,
            )
        )
        out.extend(
            self._table(
                f"ch{ch}_column2_rate",
                "Rate",
                [
                    (
                        r["htsno"],
                        r["column2_rate"] if r["column2_rate"] is not None else "0",
                    )
                    for r in col2_av_free
                ],
                [
                    (r["htsno"], self._excerpt(r["htsno"], "Rates of duty (2):"))
                    for r in col2_av_free
                ],
                source_note,
            )
        )
        out.extend(
            self._table(
                f"ch{ch}_general_disposition",
                "Text",
                [(r["htsno"], q(r["general_disposition"])) for r in self.lines],
                [
                    (
                        r["htsno"],
                        self._excerpt(r["htsno"], "Rates of duty (1-General):"),
                    )
                    for r in self.lines
                ],
                source_note,
            )
        )
        out.extend(
            self._table(
                f"ch{ch}_column2_disposition",
                "Text",
                [(r["htsno"], q(r["column2_disposition"])) for r in self.lines],
                [
                    (r["htsno"], self._excerpt(r["htsno"], "Rates of duty (2):"))
                    for r in self.lines
                ],
                source_note,
            )
        )

        out.append("")
        return "\n".join(out)

    def tests(self, samples_per_class: int, witness: set[str]) -> str:
        module_path = f"us:policies/usitc/us-tariff-duty/lines/generated/ch{self.ch}"
        by_class: dict[str, list[dict]] = defaultdict(list)
        for r in self.lines:
            by_class[r["general_disposition"]].append(r)

        picked: list[dict] = []
        seen: set[str] = set()

        def take(r: dict) -> None:
            if r["htsno"] not in seen:
                seen.add(r["htsno"])
                picked.append(r)

        for cls in sorted(by_class):
            for r in by_class[cls]:
                if r["htsno"] in witness:
                    take(r)
            for r in by_class[cls][:samples_per_class]:
                take(r)

        out: list[str] = []
        for r in picked:
            name = f"line {r['htsno']} ({r['general_disposition']})"
            out.append(f"- name: {q(name)}")
            out.append("  period:")
            out.append("    period_kind: custom")
            out.append("    name: day")
            out.append(f"    start: '{EFFECTIVE_FROM}'")
            out.append(f"    end: '{EFFECTIVE_FROM}'")
            out.append("  input:")
            out.append(f"    {module_path}#input.hts_line: {intkey(r['htsno'])}")
            out.append("  output:")
            out.append(
                f"    {module_path}#ch{self.ch}_general_disposition: {q(r['general_disposition'])}"
            )
            out.append(
                f"    {module_path}#ch{self.ch}_column2_disposition: {q(r['column2_disposition'])}"
            )
            if r["general_disposition"] in ("ad_valorem", "free"):
                rate = r["general_rate"] if r["general_rate"] is not None else 0
                out.append(f"    {module_path}#ch{self.ch}_general_rate: {rate}")
            if r["column2_disposition"] in ("ad_valorem", "free"):
                rate = r["column2_rate"] if r["column2_rate"] is not None else 0
                out.append(f"    {module_path}#ch{self.ch}_column2_rate: {rate}")

        out.append("")
        return "\n".join(out)


def intkey(htsno: str) -> int:
    return int(digits(htsno).ljust(10, "0"))


WITNESS_FORMULA_RE = re.compile(
    r"- name: \S*?(general|column_2)_rate_of_duty\n(?:.*\n)*?"
    r"      - effective_from: '[\d-]+'\n        formula: \|-\n          (\S+)"
)
WITNESS_SLUGS = ["7202-11-10-00", "7601-10-30-00", "9506-62-40"]


def witness_gate(spine_lines: list[dict]) -> None:
    by_htsno = {r["htsno"]: r for r in spine_lines}
    failures: list[str] = []
    for slug in WITNESS_SLUGS:
        h = slug.replace("-", ".")
        text = (WITNESS_DIR / f"{slug}.yaml").read_text()
        rec = by_htsno.get(h)
        if rec is None:
            failures.append(f"{h} missing from spine")
            continue
        for column, encoded in WITNESS_FORMULA_RE.findall(text):
            side = "general" if column == "general" else "column2"
            got = rec[f"{side}_rate"]
            if rec[f"{side}_disposition"] == "free":
                got = "0"
            if got is None or float(got) != float(encoded):
                failures.append(f"{h}:{column} generated {got} vs witness {encoded}")
    if failures:
        raise SystemExit(f"witness identity FAILED: {failures}")


def generate(
    out_dir: Path, snapshot_path: Path, chapters: set[str] | None = None
) -> dict[str, str]:
    raw = snapshot_path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != SNAPSHOT_SHA256:
        raise SystemExit(f"snapshot sha mismatch: {sha}")
    rows = json.loads(raw)
    spine_lines, unowned = build_spine(rows)
    if len(spine_lines) != EXPECTED_LINES:
        raise SystemExit(f"line census {len(spine_lines)} != {EXPECTED_LINES}")
    members = [m for r in spine_lines for m in r["stat_members"]]
    if len(members) != EXPECTED_MEMBERS:
        raise SystemExit(f"member census {len(members)} != {EXPECTED_MEMBERS}")
    if unowned != EXPECTED_UNOWNED:
        raise SystemExit(f"unowned stat lines changed: {unowned}")
    keys = [intkey(r["htsno"]) for r in spine_lines]
    if len(set(keys)) != len(keys):
        raise SystemExit("rate-line key collision")
    mkeys = [intkey(m) for m in members]
    if len(set(mkeys)) != len(mkeys):
        raise SystemExit("member key collision")
    witness_gate(spine_lines)

    bodies = {
        str(r["htsno"]): row_body_lines(r) for r in rows if str(r.get("htsno") or "")
    }
    witness = {"7202.11.10.00", "7601.10.30.00", "9506.62.40", "9506.62.40.40"}
    by_chapter: dict[str, list[dict]] = defaultdict(list)
    for r in spine_lines:
        by_chapter[digits(r["htsno"])[:2]].append(r)
    # Chapter 99 exceeds the CI validation budget as one module (its 9902
    # miscellaneous-suspension block alone carries ~1,655 rated lines), so
    # it emits as three sub-shards split at deterministic boundaries:
    # 99a = 9901 + the first 830 9902 lines (intkey order), 99b = the
    # remaining 9902 lines, 99c = 9903 through 9999.
    if "99" in by_chapter:
        ch99 = sorted(by_chapter.pop("99"), key=lambda r: intkey(r["htsno"]))
        pre = [r for r in ch99 if digits(r["htsno"])[:4] <= "9902"]
        post = [r for r in ch99 if digits(r["htsno"])[:4] >= "9903"]
        by_chapter["99a"] = pre[:830]
        by_chapter["99b"] = pre[830:]
        by_chapter["99c"] = post

    out_dir.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    if not chapters:
        selected = sorted(by_chapter)
    else:
        selected = sorted(
            ch for ch in by_chapter if ch in chapters or ch[:2] in chapters
        )
    for ch in selected:
        emitter = ChapterEmitter(ch, by_chapter[ch], bodies, SNAPSHOT_LABEL)
        module_text = emitter.module()
        test_text = emitter.tests(2, witness)
        (out_dir / f"ch{ch}.yaml").write_text(module_text)
        (out_dir / f"ch{ch}.test.yaml").write_text(test_text)
        hashes[f"ch{ch}.yaml"] = hashlib.sha256(module_text.encode()).hexdigest()
        hashes[f"ch{ch}.test.yaml"] = hashlib.sha256(test_text.encode()).hexdigest()
    manifest = {
        "generator": GENERATOR_VERSION,
        "snapshot_sha256": SNAPSHOT_SHA256,
        "snapshot_label": SNAPSHOT_LABEL,
        "effective_from": EFFECTIVE_FROM,
        "files": hashes,
    }
    (out_dir / "GENERATED-MANIFEST.json").write_text(
        json.dumps(manifest, indent=1) + "\n"
    )
    return hashes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--corpus",
        type=Path,
        default=Path(
            os.environ.get(
                "AXIOM_CORPUS_REPO",
                Path.home() / "TheAxiomFoundation/axiom-corpus",
            )
        ),
    )
    ap.add_argument("--check", action="store_true")
    ap.add_argument(
        "--chapters",
        default="",
        help=(
            "Comma-separated two-digit chapter list to emit/check (staged-PR "
            "subsets); empty = the full schedule."
        ),
    )
    args = ap.parse_args()
    snapshot = args.corpus / SNAPSHOT_RELPATH

    chapters = {c.zfill(2) for c in args.chapters.split(",") if c} or None
    with tempfile.TemporaryDirectory(prefix="hts-tables-") as staging:
        first = generate(Path(staging) / "a", snapshot, chapters)
        second = generate(Path(staging) / "b", snapshot, chapters)
        if first != second:
            raise SystemExit("determinism FAILED: double-emit differs")
        if args.check:
            drift = [
                name
                for name, digest in first.items()
                if not (OUTPUT_DIR / name).is_file()
                or hashlib.sha256((OUTPUT_DIR / name).read_bytes()).hexdigest()
                != digest
            ]
            if drift:
                raise SystemExit(f"drift vs committed files: {sorted(drift)[:8]}")
            print(f"check OK: {len(first)} files match committed outputs")
            return 0
        generate(OUTPUT_DIR, snapshot, chapters)
        print(f"wrote {len(first) + 1} files to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
