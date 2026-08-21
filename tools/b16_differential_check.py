#!/usr/bin/env python3
"""Structurally independent differential for the B1.6 incidence tables.

The extractor shares only the sha-pinned notes JSONL and the declarative legal
coordinates below with the production generator.  It deliberately does not
import that generator, use its prose boundaries, or use a regular expression
to recognize HTS numbers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from b16_entry_flags import entry_flags

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "us/policies/usitc/us-tariff-incidence/generated"
NOTES_SHA256 = "0f3ed7ef2efb64383825db65e615959200770e8511c8d4834b16e02892cb9ec8"
RATE_SHA256 = "59a76c12e28d7a28975f31a8876bfb08e64927b922fe2b4f88801ff4459181e6"
RATE_RELPATH = Path(
    "sources/us/statute/2026-08-09-usitc-hts-2026-rev15-full-schedule/"
    "usitc-hts/hts_2026_revision_15_json.json"
)

EU_CODES = {"AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"}
COUNTRY_NAME_CODES = {
    "Algeria":"DZ", "Angola":"AO", "Argentina":"AR", "Australia":"AU", "the Bahamas":"BS", "Bahrain":"BH", "Bangladesh":"BD", "Brazil":"BR", "Cambodia":"KH", "Canada":"CA", "Chile":"CL", "China":"CN", "Colombia":"CO", "Costa Rica":"CR", "Dominican Republic":"DO", "Ecuador":"EC", "Egypt":"EG", "El Salvador":"SV", "Guatemala":"GT", "Guyana":"GY", "Honduras":"HN", "Hong Kong, China":"HK", "India":"IN", "Indonesia":"ID", "Iraq":"IQ", "Israel":"IL", "Japan":"JP", "Jordan":"JO", "Kazakhstan":"KZ", "Kuwait":"KW", "Libya":"LY", "Malaysia":"MY", "Mexico":"MX", "Morocco":"MA", "New Zealand":"NZ", "Nicaragua":"NI", "Nigeria":"NG", "Norway":"NO", "Oman":"OM", "Pakistan":"PK", "Peru":"PE", "the Philippines":"PH", "Qatar":"QA", "Russia":"RU", "Saudi Arabia":"SA", "Singapore":"SG", "South Africa":"ZA", "South Korea":"KR", "Sri Lanka":"LK", "Switzerland":"CH", "Taiwan":"TW", "Thailand":"TH", "Trinidad and Tobago":"TT", "Türkiye":"TR", "the United Arab Emirates":"AE", "the United Kingdom":"GB", "Uruguay":"UY", "Venezuela":"VE", "Vietnam":"VN",
}


@dataclass(frozen=True)
class LegalTable:
    table: str
    note: int
    path: tuple[str, ...]
    include_prefix: str = ""
    # These associations are independently obtained from the charging
    # heading's description in the RATE snapshot and checked below.
    rate_heading: str = ""
    widths: tuple[int, ...] = (8, 10)


# Law coordinates, not parser instructions or excerpts from the notes text.
LEGAL_TABLES = (
    LegalTable("china_301_list1_membership", 20, ("b",), rate_heading="9903.88.01"),
    LegalTable("china_301_list2_membership", 20, ("d",), rate_heading="9903.88.02"),
    LegalTable("china_301_list3_membership", 20, ("f",), rate_heading="9903.88.03"),
    LegalTable("china_301_list4a_membership", 20, ("s",), rate_heading="9903.88.15"),
    LegalTable("s201_cspv_membership", 18, ("c", "i")),
    LegalTable("s122_aa_i_ch98_membership", 2, ("aa", "i"), "9818"),
    LegalTable("s122_aa_ii_membership", 2, ("aa", "ii"), rate_heading="9903.03.03"),
    LegalTable("s122_aa_iii_membership", 2, ("aa", "iii"), rate_heading="9903.03.04"),
    LegalTable("s122_gn6_conditional_membership", 2, ("aa", "iv"), rate_heading="9903.03.05"),
    LegalTable("s232_steel_primary_membership", 16, ("c", "iii"), "7", widths=(4, 6, 8)),
    LegalTable("s232_steel_derivative_legacy_membership", 16, ("c", "iv")),
    LegalTable("s232_steel_derivative_april_membership", 16, ("c", "vii")),
    LegalTable("s232_steel_derivative_equipment_membership", 16, ("c", "x")),
    LegalTable("s232_steel_derivative_mobile_membership", 16, ("c", "xi")),
    LegalTable("s232_aluminum_primary_membership", 19, ("b",), "76", widths=(4, 8)),
    LegalTable("s232_aluminum_derivative_membership", 19, ("j",)),
    LegalTable("brazil_301_unconditional_exemption_membership", 50, ("a", "ii")),
    LegalTable("brazil_301_particular_exemption_membership", 50, ("a", "iii")),
    LegalTable("brazil_301_aircraft_conditional_membership", 50, ("a", "iv")),
    LegalTable("brazil_301_pharma_conditional_membership", 50, ("a", "v")),
    LegalTable("forced_labor_301_common_exemption_membership", 52, ("b",)),
    LegalTable("forced_labor_301_particular_exemption_membership", 52, ("c",)),
    LegalTable("forced_labor_301_aircraft_conditional_membership", 52, ("d",)),
    LegalTable("forced_labor_301_pharma_conditional_membership", 52, ("e",)),
)


@dataclass(frozen=True)
class Page:
    number: int
    citation: str
    body: str
    stream_start: int


@dataclass(frozen=True)
class Marker:
    label: str
    start: int
    end: int


def is_ascii_letter(c: str) -> bool:
    return "a" <= c <= "z" or "A" <= c <= "Z"


def is_ascii_digit(c: str) -> bool:
    return "0" <= c <= "9"


def marker_at(text: str, pos: int) -> Marker | None:
    """Read one parenthesized letter/romanette/number by character walking."""
    if pos >= len(text) or text[pos] != "(":
        return None
    j = pos + 1
    while j < len(text) and (is_ascii_letter(text[j]) or is_ascii_digit(text[j])):
        j += 1
    if j == pos + 1 or j >= len(text) or text[j] != ")":
        return None
    # Case is structural: note subdivisions use lowercase markers while deeper
    # subparagraphs may independently use (A), (B), and roman capitals.
    return Marker(text[pos + 1 : j], pos, j + 1)


def syntactic_markers(text: str, lo: int, hi: int) -> list[Marker]:
    """Find markers that introduce provisions, rejecting inline citations."""
    found: list[Marker] = []
    i = lo
    while i < hi:
        marker = marker_at(text, i)
        if marker is None:
            i += 1
            continue
        j = marker.end
        while j < hi and text[j].isspace():
            j += 1
        # Operative subdivisions in this snapshot begin with a capitalized
        # clause, a compiler note, or an immediately nested marker.  Inline
        # citations normally continue with lowercase prose or punctuation.
        nested_clause = False
        if j < hi and text[j] == "(":
            nested = marker_at(text, j)
            if nested:
                k = nested.end
                while k < hi and text[k].isspace():
                    k += 1
                nested_clause = k < hi and (text[k].isupper() or text[k] in "[“")
        if j < hi and (text[j].isupper() or text[j] in "[“" or nested_clause):
            found.append(marker)
        i = marker.end
    return found


def note_starts(text: str) -> list[tuple[int, int]]:
    """Recognize structural ``N. (a)`` note openings without prose matching."""
    starts: list[tuple[int, int]] = []
    i = 0
    while i < len(text):
        if not is_ascii_digit(text[i]) or (i and is_ascii_digit(text[i - 1])):
            i += 1
            continue
        j = i
        while j < len(text) and is_ascii_digit(text[j]):
            j += 1
        number = int(text[i:j])
        if j >= len(text) or text[j] != ".":
            i = j
            continue
        k = j + 1
        while k < len(text) and text[k].isspace():
            k += 1
        marker = marker_at(text, k)
        if marker and marker.label == "a":
            starts.append((number, i))
        i = j + 1
    return starts


ROMANETTES = ("i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xiii", "xiv", "xv")


def next_label(label: str, depth: int) -> str | None:
    if depth:
        try:
            return ROMANETTES[ROMANETTES.index(label) + 1]
        except (ValueError, IndexError):
            return None
    # HTS note subdivisions use a, ..., z, aa, bb, ... rather than spreadsheet
    # lettering; that sequence is itself part of the document structure.
    if len(label) == 1 and label < "z":
        return chr(ord(label) + 1)
    if len(label) == 1:
        return "aa"
    if len(set(label)) == 1 and label[0] < "z":
        return chr(ord(label[0]) + 1) * len(label)
    return None


def subdivision(text: str, note_lo: int, note_hi: int, path: tuple[str, ...]) -> tuple[int, int]:
    lo, hi = note_lo, note_hi
    for depth, wanted in enumerate(path):
        candidates = syntactic_markers(text, lo, hi)
        match = next((m for m in candidates if m.label == wanted), None)
        if match is None:
            raise ValueError(f"subdivision marker absent at depth {depth + 1}: {path}")
        # Advance in the ordered alphabet for this nesting level.  This keeps a
        # nested (i) inside top-level (c), while (d) closes (c), across pages.
        successor = next_label(wanted, depth)
        peer = next((m for m in candidates if m.start > match.start and m.label == successor), None)
        next_peer = peer.start if peer else hi
        lo, hi = match.end, next_peer
    return lo, hi


def scan_hts(text: str, lo: int, hi: int, allow_terminal_period: bool = False) -> set[str]:
    """Scan printed 4/6/8/10-digit HTS tokens by character transitions."""
    out: set[str] = set()
    i = lo
    while i < hi:
        if not is_ascii_digit(text[i]) or (i and (is_ascii_digit(text[i - 1]) or text[i - 1] == ".")):
            i += 1
            continue
        start = i
        groups: list[str] = [text[i:i + 4]]
        if len(groups[0]) != 4 or not all(is_ascii_digit(c) for c in groups[0]):
            i = start + 1
            continue
        i += 4
        for _ in range(2):
            if i >= hi or text[i] != ".":
                break
            i += 1
            group = text[i:i + 2]
            if len(group) != 2 or not all(is_ascii_digit(c) for c in group):
                break
            groups.append(group)
            i += 2
        if len(groups) == 3:
            group = text[i:i + 2]
            if len(group) == 2 and all(is_ascii_digit(c) for c in group):
                groups.append(group)
                i += 2
        if groups and (
            i >= hi
            or (
                not is_ascii_digit(text[i])
                and (text[i] != "." or allow_terminal_period)
            )
        ):
            out.add("".join(groups))
        i = max(i, start + 1)
    return out


def skip_leading_annotations(text: str, lo: int, hi: int) -> int:
    """Move past bracketed compiler metadata that separates preamble/list."""
    bracket = text.find("[", lo, hi)
    if bracket < 0:
        return lo
    close = text.find("]", bracket + 1, hi)
    if close < 0:
        raise ValueError("unterminated bracketed annotation")
    # Recognize the annotation's structural label, not any operative sentence.
    label = text[bracket + 1 : bracket + 9].lower()
    return close + 1 if label == "compiler" else lo


def load_pages(path: Path) -> tuple[str, list[Page]]:
    if hashlib.sha256(path.read_bytes()).hexdigest() != NOTES_SHA256:
        raise ValueError("notes snapshot sha mismatch")
    records = []
    for raw in path.read_text().splitlines():
        item = json.loads(raw)
        if item.get("kind") == "page" and item.get("parent_citation_path") == "us/statute/hts/chapter-99":
            records.append(item)
    records.sort(key=lambda item: int(item["metadata"]["page_number"]))
    chunks: list[str] = []
    pages: list[Page] = []
    offset = 0
    for item in records:
        body = item.get("body") or ""
        pages.append(Page(int(item["metadata"]["page_number"]), item["citation_path"], body, offset))
        chunks.append(body)
        offset += len(body) + 1
    return "\n".join(chunks), pages


def page_receipts(pages: list[Page], lo: int, hi: int) -> list[str]:
    return [p.citation for p in pages if p.stream_start < hi and p.stream_start + len(p.body) >= lo]


def load_rate_descriptions(corpus: Path) -> dict[str, str]:
    # The notes path is .../data/corpus/provisions/...; RATE is another pinned
    # corpus artifact, used only to validate table-to-subdivision association.
    corpus_dir = next((p for p in corpus.parents if p.name == "corpus"), None)
    if corpus_dir is None:
        raise ValueError("cannot locate data/corpus ancestor for RATE snapshot")
    rate_path = corpus_dir / RATE_RELPATH
    if hashlib.sha256(rate_path.read_bytes()).hexdigest() != RATE_SHA256:
        raise ValueError("RATE snapshot sha mismatch")
    return {row.get("htsno"): row.get("description", "") for row in json.loads(rate_path.read_text())}


def verify_rate_associations(descriptions: dict[str, str]) -> None:
    for spec in LEGAL_TABLES:
        if not spec.rate_heading:
            continue
        desc = descriptions.get(spec.rate_heading, "")
        path_text = "".join(f"({part})" for part in spec.path)
        if path_text not in desc or f"note {spec.note}" not in desc:
            raise ValueError(f"RATE heading {spec.rate_heading} does not name note {spec.note}{path_text}")


def note52_countries_from_rate(descriptions: dict[str, str]) -> set[str]:
    """Independently expand the note-52 charging headings to ISO alpha-2."""
    countries: set[str] = set()
    for number in range(20, 85):
        description = descriptions.get(f"9903.05.{number:02d}", "")
        if "U.S. note 52" not in description:
            raise ValueError(f"note 52 charging heading absent: 9903.05.{number:02d}")
        if "member state of the European Union" in description:
            countries.update(EU_CODES)
            continue
        matches = [code for name, code in COUNTRY_NAME_CODES.items() if f"product of {name}" in description]
        if len(matches) != 1:
            raise ValueError(f"cannot independently resolve note 52 country at 9903.05.{number:02d}")
        countries.add(matches[0])
    if len(countries) != 86:
        raise ValueError(f"note 52 country set expected 86, got {len(countries)}")
    return countries


def generated_note52_formula_countries() -> set[str]:
    """Observe the action union at the entry-flag boundary on a nonexempt line."""
    return {
        code
        for code in set(COUNTRY_NAME_CODES.values()) | EU_CODES
        if entry_flags(99_999_999_99, "9999.99.99.99", code)[
            "entry_is_forced_labor_301"
        ]
    }


def generated_tables() -> dict[str, set[str]]:
    tables: dict[str, set[str]] = {}
    for path in OUT.rglob("*.yaml"):
        if path.name.endswith(".test.yaml"):
            continue
        for rule in yaml.safe_load(path.read_text()).get("rules", []):
            if rule.get("kind") == "parameter" and "membership" in rule["name"]:
                tables[rule["name"]] = {str(key) for key in rule["versions"][0]["values"]}
    return tables


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        stream, pages = load_pages(args.corpus)
        descriptions = load_rate_descriptions(args.corpus)
        verify_rate_associations(descriptions)
        expected_countries = note52_countries_from_rate(descriptions)
        generated_countries = generated_note52_formula_countries()
        if generated_countries != expected_countries:
            raise ValueError(
                "note 52 formula country mismatch: "
                f"missing={sorted(expected_countries-generated_countries)}, "
                f"extra={sorted(generated_countries-expected_countries)}"
            )
        starts = note_starts(stream)
        note_ranges: dict[int, tuple[int, int]] = {}
        for index, (number, start) in enumerate(starts):
            note_ranges[number] = (start, starts[index + 1][1] if index + 1 < len(starts) else len(stream))
        generated = generated_tables()
        report: dict[str, dict] = {}
        report["origin_is_note52_covered"] = {
            "expected": len(expected_countries),
            "generated": len(generated_countries),
            "only_expected": [],
            "only_generated": [],
        }
        brazil_generated = {
            code
            for code in set(COUNTRY_NAME_CODES.values()) | EU_CODES
            if entry_flags(99_999_999_99, "9999.99.99.99", code)[
                "entry_is_brazil_301"
            ]
        }
        report["entry_is_brazil_301_country_coverage"] = {
            "expected": 1,
            "generated": len(brazil_generated),
            "only_expected": sorted({"BR"} - brazil_generated),
            "only_generated": sorted(brazil_generated - {"BR"}),
        }
        if brazil_generated != {"BR"}:
            failed = True
        failed = False
        for spec in LEGAL_TABLES:
            if spec.note not in note_ranges:
                raise ValueError(f"note {spec.note} absent")
            lo, hi = subdivision(stream, *note_ranges[spec.note], spec.path)
            lo = skip_leading_annotations(stream, lo, hi)
            codes = {code for code in scan_hts(stream, lo, hi, 4 in spec.widths) if not code.startswith("99")}
            codes = {code for code in codes if len(code) in spec.widths}
            if spec.include_prefix:
                codes = {code for code in codes if code.startswith(spec.include_prefix)}
            for width in spec.widths:
                base = spec.table.removesuffix("_membership")
                suffix = {4: "_heading_membership", 6: "_subheading6_membership", 8: "_membership", 10: "_membership_hts10"}[width]
                table = base + suffix
                expected = {str(int(code)) for code in codes if len(code) == width}
                if spec.note in {50, 52}:
                    fragments = {
                        name: values
                        for name, values in generated.items()
                        if re.fullmatch(re.escape(table) + r"_p\d+", name)
                    }
                    got = set().union(*fragments.values()) if fragments else set()
                    for fragment, fragment_got in sorted(fragments.items()):
                        page_number = int(fragment.rsplit("_p", 1)[1])
                        page = next(item for item in pages if item.number == page_number)
                        page_lo = max(lo, page.stream_start)
                        page_hi = min(hi, page.stream_start + len(page.body))
                        fragment_codes = scan_hts(
                            stream, page_lo, page_hi, 4 in spec.widths
                        )
                        fragment_expected = {
                            str(int(code))
                            for code in fragment_codes
                            if not code.startswith("99") and len(code) == width
                        }
                        if spec.include_prefix:
                            fragment_expected = {
                                code for code in fragment_expected
                                if code.zfill(width).startswith(spec.include_prefix)
                            }
                        report[fragment] = {
                            "expected": len(fragment_expected),
                            "generated": len(fragment_got),
                            "only_expected": sorted(fragment_expected - fragment_got),
                            "only_generated": sorted(fragment_got - fragment_expected),
                        }
                        if fragment_expected != fragment_got:
                            failed = True
                            print(f"FINDING {fragment}: page {page.citation}", file=sys.stderr)
                else:
                    got = generated.get(table, set())
                if not expected and not got:
                    continue
                union_name = table + ("_union" if spec.note in {50, 52} else "")
                report[union_name] = {
                    "expected": len(expected),
                    "generated": len(got),
                    "only_expected": sorted(expected - got),
                    "only_generated": sorted(got - expected),
                }
                if expected != got:
                    failed = True
                    print(f"FINDING {union_name}: pages {', '.join(page_receipts(pages, lo, hi))}", file=sys.stderr)
        text = json.dumps(report, indent=2) + "\n"
        args.output.write_text(text) if args.output else sys.stdout.write(text)
        return int(failed)
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(f"differential error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
