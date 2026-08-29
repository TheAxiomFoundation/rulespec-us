#!/usr/bin/env python3
"""Generate grounded chapter-99 action-incidence membership tables.

The grammar below is data: each production is an action, exact subdivision
anchor, exact peer stop anchor, and membership class.  The single parser carries
subdivision state across physical pages and preserves atoms at their printed
4-, 6-, 8-, and 10-digit widths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

VERSION = "b1.6-incidence-3"
SHA256 = "0f3ed7ef2efb64383825db65e615959200770e8511c8d4834b16e02892cb9ec8"
RELPATH = "data/corpus/provisions/us/statute/2026-08-04-usitc-hts-2026-rev15-notes.jsonl"
REV10_SHA256 = "87774d2023f02954b1723bdf0b20b890d148fba4474c5422acc77d98dadefba3"
REV10_RELPATH = (
    "data/corpus/provisions/us/statute/"
    "2026-08-01-usitc-hts-2026-rev10-notes.jsonl"
)
REV5_SHA256 = "ee8889aa9fe24c5330b103dada5eb270037c1038149eea614c85421d92011214"
REV5_RELPATH = (
    "data/corpus/provisions/us/statute/"
    "2026-08-01-usitc-hts-2026-rev5-notes.jsonl"
)
PROCLAMATION_11021_SHA256 = (
    "92a7aa2ca28779965dafc471e4f7d288527eb87a62c4e8c7903efcf85a9460cf"
)
PROCLAMATION_11021_BODY_SHA256 = (
    "8bb8ff988becea34d3e4331b35350f023e68750419a62c724b36311870218d57"
)
PROCLAMATION_11021_RELPATH = (
    "data/corpus/provisions/us/rulemaking/"
    "2026-08-29-tariff-232-proclamation-11021-annex-iv-page-43.jsonl"
)
PROCLAMATION_11021_CITATION = (
    "us/rulemaking/federal-register/2026-04-09/2026-06960/annex-iv/page-43"
)
REV6_SHA256 = "77b1a7ea0f038d436ae002545e6a057e04869da3e41d29e04bcc7e88631ae27f"
REV6_RELPATH = (
    "data/corpus/provisions/us/statute/"
    "2026-08-01-usitc-hts-2026-rev6-notes.jsonl"
)
REV12_SHA256 = "c42ed5322255c3c3db900b4cf5f751200a12f986fdb0be433fae67c48ddbefac"
REV12_RELPATH = (
    "data/corpus/provisions/us/statute/"
    "2026-08-01-usitc-hts-2026-rev12-notes.jsonl"
)
NOTE16_ALUMINUM_VINTAGES = (
    (
        "2026-04-06",
        REV5_RELPATH,
        REV5_SHA256,
        "USITC HTS Revision 5",
    ),
    ("2026-06-08", REV10_RELPATH, REV10_SHA256, "USITC HTS Revision 10"),
)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "us/policies/usitc/us-tariff-incidence/generated"
HTS = re.compile(
    r"(?<![\d.])(\d{4}\.\d{2}\.\d{2}(?:\d{2})?)(?!\d|\.\d)"
)
PRINTED_WIDTH_HTS = re.compile(
    r"(?<![\d.])(\d{4}(?:\.\d{2}(?:\.\d{2}(?:\d{2})?)?)?)(?!\d|\.\d)"
)

@dataclass(frozen=True)
class Production:
    action: str
    table: str
    subdivision: str
    start: str
    stop: str
    membership_class: str = "membership"
    after_compiler: bool = True
    include_prefixes: tuple[str,...] = ()
    widths: tuple[int, ...] = (8, 10)
    effective_from: str = "2026-08-03"
    source_label: str = "USITC HTS Revision 15"

# Exact anchors intentionally include operative heading language, not bare labels.
GRAMMAR = (
    Production("301", "china_301_list1_membership", "20(b)", "(b) Heading 9903.88.01 applies", "(c) For the purposes of heading 9903.88.02"),
    Production("301", "china_301_list2_membership", "20(d)", "(d) Heading 9903.88.02 applies", "(e) For the purposes of heading 9903.88.03"),
    Production("301", "china_301_list3_membership", "20(f)", "(f) Heading 9903.88.03 applies", "(g) For the purposes of heading 9903.88.04"),
    Production("301", "china_301_list4a_membership", "20(s)", "(s) Heading 9903.88.15 applies", "(t) For the purposes of heading 9903.88.16"),
    Production("201", "s201_cspv_membership", "18(c)(i)", "(c) (i) For the purposes of subheadings 9903.45.21", "(ii) Subheadings 9903.45.21", after_compiler=False),
    Production("122", "s122_aa_i_ch98_membership", "2(aa)(i)", "(aa) [Compiler’s note: Subdivisions (aa)(i)", "(ii) As provided in heading 9903.03.03", after_compiler=False, include_prefixes=("9818.",)),
    Production("122", "s122_aa_ii_membership", "2(aa)(ii)", "(ii) As provided in heading 9903.03.03", "(iii) As provided in heading 9903.03.04"),
    Production("122", "s122_aa_iii_membership", "2(aa)(iii)", "(iii) As provided in heading 9903.03.04", "(iv) As provided in heading 9903.03.05", after_compiler=False),
    Production("122", "s122_gn6_conditional_membership", "2(aa)(iv)", "(iv) As provided in heading 9903.03.05", "(v) As provided in heading 9903.03.06", "conditional"),
    Production("232-steel", "s232_steel_primary_membership", "16(c)(iii)", "(iii) Articles of steel:", "(iv) Derivative steel articles:", after_compiler=False, include_prefixes=("72", "73"), widths=(4, 6, 8)),
    Production("232-steel", "s232_steel_derivative_legacy_membership", "16(c)(iv)", "(iv) Derivative steel articles:", "(v) Articles of copper:", after_compiler=False),
    Production("232-steel", "s232_steel_derivative_april_membership", "16(c)(vii)", "(vii) Derivative steel articles:", "(viii) Articles of copper:", after_compiler=True),
    Production("232-steel", "s232_steel_derivative_equipment_membership", "16(c)(x)", "(x) Derivative steel articles:", "(xi) Derivative steel articles:", after_compiler=False),
    Production("232-steel", "s232_steel_derivative_mobile_membership", "16(c)(xi)", "(xi) Derivative steel articles:", "(d) Headings 9903.82.04", after_compiler=False),
    Production("232-aluminum", "s232_aluminum_primary_membership", "19(b)", "(b) The rates of duty set forth in heading 9903.85.01", "(c) The Secretary of Commerce", after_compiler=False, include_prefixes=("76",), widths=(4, 8)),
    Production("232-aluminum", "s232_aluminum_derivative_membership", "19(j)", "(j) The rates of duty set forth in heading 9903.85.07", "(k) The rates of duty in heading 9903.85.08", after_compiler=False),
    # Proclamation 11021 moved the operative aluminum-derivative program into
    # note 16(c).  These three lists are the primitive incidence surface for
    # the later notes 50/52 sector-precedence exclusions.  Revision 10 is the
    # first snapshot needed by those exclusions and is independently checked
    # below to be byte-for-byte equal at the extracted-atom level to Rev. 15.
    Production(
        "232-note16-aluminum-precedence",
        "s232_note16_c_ii_derivative_aluminum_membership",
        "16(c)(ii)",
        "(ii) Derivative aluminum articles:",
        "(iii) Articles of steel:",
        after_compiler=False,
        effective_from="2026-06-08",
        source_label="USITC HTS Revision 10, unchanged through Revision 15",
    ),
    Production(
        "232-note16-aluminum-precedence",
        "s232_note16_c_vi_derivative_aluminum_candidate_membership",
        "16(c)(vi)",
        "(vi) Derivative aluminum articles:",
        "(vii) Derivative steel articles",
        after_compiler=False,
        effective_from="2026-06-08",
        source_label="USITC HTS Revision 10, unchanged through Revision 15",
    ),
    Production(
        "232-note16-aluminum-precedence",
        "s232_note16_c_ix_derivative_aluminum_candidate_membership",
        "16(c)(ix)",
        "(ix) Derivative aluminum articles:",
        "(x) Derivative steel articles:",
        after_compiler=False,
        effective_from="2026-06-08",
        source_label="USITC HTS Revision 10, unchanged through Revision 15",
    ),
    # Notes 50(a)(vi) and 52(f) exclude the sector programs named below from
    # their additional duties.  Some program notes define an unconditional
    # HTS list; others print only a candidate list and require a product/use
    # determination.  Candidate tables are deliberately named as such so
    # entry preparation cannot confuse code incidence with legal eligibility.
    Production("232-note50-52", "s232_copper_primary_membership", "16(c)(v)", "(v) Articles of copper:", "(vi) Derivative aluminum articles:", after_compiler=False),
    Production("232-note50-52", "s232_copper_additional_membership", "16(c)(viii)", "(viii) Articles of copper:", "(ix) Derivative aluminum articles:", after_compiler=False),
    Production("232-note50-52", "s232_note33_vehicle_candidate_membership", "33(b)", "(b) The rates of duty set forth in headings 9903.94.01", "(c) Heading 9903.94.02 applies", after_compiler=False),
    Production("232-note50-52", "s232_note33_auto_part_candidate_membership", "33(g)", "(g) Subject to a manufacturer's import adjustment offset amount", "(h) Heading 9903.94.06 applies", after_compiler=False, include_prefixes=("40", "70", "73", "83", "84", "85", "87", "90", "94"), widths=(4, 6, 8, 10)),
    Production("232-note50-52", "s232_note37_softwood_membership", "37(b)", "(b) The rates of duty set forth in heading 9903.76.01", "(c) Heading 9903.76.02 provides", after_compiler=False),
    Production("232-note50-52", "s232_note37_upholstered_wood_furniture_membership", "37(d)", "(d) The rates of duty set forth in headings 9903.76.02", "(e) Except for as provided by heading 9903.76.04", after_compiler=False, widths=(10,)),
    Production("232-note50-52", "s232_note37_cabinet_vanity_candidate_membership", "37(f)", "(f) Except for as provided by heading 9903.76.04", "(g) Heading 9903.76.04 applies", after_compiler=False, widths=(10,)),
    Production("232-note50-52", "s232_note38_mhd_vehicle_membership", "38(b)", "(b) The rate of duty set forth in heading 9903.74.01", "(c) Heading 9903.74.02 applies", after_compiler=False),
    Production("232-note50-52", "s232_note38_bus_membership", "38(c)", "(c) Heading 9903.74.02 applies", "(d) Heading 9903.74.03", after_compiler=False),
    Production("232-note50-52", "s232_note38_mhd_part_candidate_membership", "38(i)", "(i) Subject to a manufacturer’s import adjustment offset amount", "(j) Heading 9903.74.09 applies", after_compiler=False, include_prefixes=("40", "70", "73", "83", "84", "85", "87", "90", "94")),
    Production("232-note50-52", "s232_note39_semiconductor_candidate_membership", "39(b)", "(b) For the purposes of this note, “semiconductor articles” refers", "To be included within the definition of semiconductor articles", after_compiler=False, widths=(6,)),
    Production("232-note50-52", "s232_note40_pharmaceutical_candidate_membership", "40(c)", "(c) The headings provided in subdivision (a) of this note", "For the purposes of this note:", after_compiler=True, widths=(10,)),
    Production("brazil-301", "brazil_301_unconditional_exemption_membership", "50(a)(ii)", "(ii) As provided in heading 9903.05.03", "(iii) As provided in heading 9903.05.04"),
    Production("brazil-301", "brazil_301_particular_exemption_membership", "50(a)(iii)", "(iii) As provided in heading 9903.05.04", "(iv) As provided in heading 9903.05.05", after_compiler=False),
    Production("brazil-301", "brazil_301_aircraft_conditional_membership", "50(a)(iv)", "(iv) As provided in heading 9903.05.05", "(v) As provided in heading 9903.05.06", "conditional"),
    Production("brazil-301", "brazil_301_pharma_conditional_membership", "50(a)(v)", "(v) As provided in heading 9903.05.06", "(vi) As provided in heading 9903.05.07", "conditional"),
    Production("forced-labor-301", "forced_labor_301_common_exemption_membership", "52(b)", "(b) As provided in heading 9903.05.86", "(c) As provided in heading 9903.05.87", after_compiler=False),
    Production("forced-labor-301", "forced_labor_301_particular_exemption_membership", "52(c)", "(c) As provided in heading 9903.05.87", "(d) As provided in heading 9903.05.88", after_compiler=False),
    Production("forced-labor-301", "forced_labor_301_aircraft_conditional_membership", "52(d)", "(d) As provided in heading 9903.05.88", "(e) As provided in heading 9903.05.89", "conditional", after_compiler=False),
    Production("forced-labor-301", "forced_labor_301_pharma_conditional_membership", "52(e)", "(e) As provided in heading 9903.05.89", "(f) As provided in heading 9903.05.90", "conditional", after_compiler=False),
)

# Note 52(j) prints one or more consecutive headings for each origin group.
# Keeping a table per origin/condition avoids flattening country-specific or
# preference-conditional relief into a code-only boolean.
COUNTRY_PRODUCTIONS = (
    ("united_kingdom", False, "9903.05.96", "9903.05.97"),
    ("european_union", False, "9903.05.97", "9903.05.98"),
    ("switzerland", False, "9903.05.98", "9903.05.99"),
    ("malaysia", False, "9903.05.99", "9903.06.02"),
    ("cambodia", False, "9903.06.02", "9903.06.04"),
    ("guatemala", False, "9903.06.04", "9903.06.06"),
    ("el_salvador", False, "9903.06.07", "9903.06.09"),
    ("argentina", False, "9903.06.10", "9903.06.12"),
    ("bangladesh", False, "9903.06.12", "9903.06.14"),
    ("taiwan", False, "9903.06.14", "9903.06.16"),
    ("indonesia", False, "9903.06.16", "9903.06.18"),
    ("ecuador", False, "9903.06.18", "9903.06.20"),
    ("jordan", False, "9903.06.20", "(k)"),
)

FILES = {
    "301": "note20-china-301", "201": "note18-201-solar",
    "122": "note2aa-122-exemptions", "232-steel": "note16-232-steel",
    "232-aluminum": "note19-232-aluminum",
    "232-note16-aluminum-precedence": "note16-232-aluminum-precedence",
    "232-note50-52": "note50-52-232-sector-precedence",
    "brazil-301": "note50-brazil-301",
    "forced-labor-301": "note52-forced-labor-301",
}

PAGE_ACTION_DIRS = {
    "brazil-301": "note50",
    "forced-labor-301": "note52",
}

def country_pairs(all_pages: list[dict]) -> list[tuple[Production,list[dict]]]:
    pairs=[]
    for origin, conditional, first, stop in COUNTRY_PRODUCTIONS:
        start_marker = re.compile(r"\((?:[ivx]+|\d+)\) As provided in heading " + re.escape(first))
        start = None
        for page in all_pages:
            m=start_marker.search(page.get("body") or "")
            if m: start=m.group(0); break
        if start is None: raise ValueError(f"missing country start heading {first}")
        if stop == "(k)": stop_anchor="Rates of Duty Unit of Quantity"
        elif stop == "(j)": stop_anchor="(j)"
        else:
            stop_anchor=None
            rx=re.compile(r"\((?:[ivx]+|\d+)\) As provided in heading " + re.escape(stop))
            for page in all_pages:
                m=rx.search(page.get("body") or "")
                if m: stop_anchor=m.group(0); break
            if stop_anchor is None: raise ValueError(f"missing country stop heading {stop}")
        p=Production("forced-labor-301",f"note52_{origin}_{'fta_conditional_' if conditional else ''}exemption_membership",f"52({'i' if conditional else 'j'})",start,stop_anchor,"conditional" if conditional else "membership",after_compiler=False)
        pairs.append((p,extract(all_pages,p)))
    return pairs

def pages(path: Path) -> list[dict]:
    out=[]
    for n, raw in enumerate(path.read_text().splitlines(), 1):
        d=json.loads(raw)
        if d.get("kind")=="page" and d.get("parent_citation_path")=="us/statute/hts/chapter-99": out.append(d)
    return sorted(out, key=lambda d:int(d["metadata"]["page_number"]))


def proclamation_11021_page(path: Path) -> dict:
    """Load the targeted April-effect, proviso, and c(ii)-code witness."""
    records = [json.loads(raw) for raw in path.read_text().splitlines() if raw]
    if len(records) != 1:
        raise ValueError(
            "Proclamation 11021 Annex IV page-43 artifact must contain one record"
        )
    page = records[0]
    if page.get("kind") != "page":
        raise ValueError("Proclamation 11021 Annex IV record is not a page")
    if page.get("citation_path") != PROCLAMATION_11021_CITATION:
        raise ValueError("Proclamation 11021 Annex IV citation path changed")
    if page.get("metadata", {}).get("effective_date") != "2026-04-06":
        raise ValueError("Proclamation 11021 Annex IV effective date changed")
    if (
        hashlib.sha256((page.get("body") or "").encode()).hexdigest()
        != PROCLAMATION_11021_BODY_SHA256
    ):
        raise ValueError("Proclamation 11021 Annex IV page body changed")
    body = page["body"]
    required_excerpts = (
        "on or after 12:01 a.m. eastern time on April 6, 2026",
        (
            "only apply where the weight of the applicable metal is at least 15 "
            "percent of the weight of the imported article"
        ),
        "(ii) Derivative aluminum articles:",
        "7612.10.00",
    )
    for excerpt in required_excerpts:
        if excerpt not in body:
            raise ValueError(
                "Proclamation 11021 Annex IV page missing required excerpt: "
                f"{excerpt}"
            )
    if "7612.10.10" in body:
        raise ValueError(
            "Proclamation 11021 Annex IV page contains superseded HTS 7612.10.10"
        )
    selection_scope = page.get("metadata", {}).get("selection_scope", "")
    if "page-43 portion of subdivision (c)(ii)" not in selection_scope:
        raise ValueError("Proclamation page scope no longer marks c(ii) as partial")
    return page

def segments(all_pages: list[dict], p: Production):
    active=False
    for page in all_pages:
        body=page.get("body") or ""; off=0
        if not active:
            off=body.find(p.start)
            if off < 0: continue
            active=True
            if p.after_compiler:
                marker=body.find("[Compiler", off)
                if marker >= 0:
                    close=body.find("]", marker)
                    if close < 0: raise ValueError(f"unterminated compiler note: {page['citation_path']}")
                    off=close+1
        end=body.find(p.stop, off)
        yield page, off, end if end >= 0 else len(body)
        if end >= 0: return
    if not active: raise ValueError(f"missing start anchor for {p.subdivision}: {p.start}")
    raise ValueError(f"missing stop anchor for {p.subdivision}: {p.stop}")

def extract(all_pages: list[dict], p: Production) -> list[dict]:
    found=[]
    for page, lo, hi in segments(all_pages,p):
        tokenizer = PRINTED_WIDTH_HTS if any(width < 8 for width in p.widths) else HTS
        for m in tokenizer.finditer(page["body"],lo,hi):
            code=m.group(1)
            if code.startswith("99"): continue
            if len(code.replace(".", "")) not in p.widths: continue
            if p.include_prefixes and not code.startswith(p.include_prefixes): continue
            found.append({"code":code,"page":page["citation_path"],"excerpt":code,"subdivision":p.subdivision})
    # A duplicated printed atom is legal-text ambiguity, not something to hide.
    seen={}
    for atom in found:
        if atom["code"] in seen: raise ValueError(f"duplicate {p.table} atom {atom['code']}")
        seen[atom["code"]]=atom
    return sorted(found,key=lambda a:(len(a["code"].replace('.','')),int(a["code"].replace('.',''))))


def q(s): return json.dumps(s,ensure_ascii=False)
def key(code): return int(code.replace(".",""))

def table_suffix(width: int) -> str:
    return {4: "_heading_membership", 6: "_subheading6_membership", 8: "_membership", 10: "_membership_hts10"}[width]


def table_name(p: Production, width: int) -> str:
    base = p.table.removesuffix("_membership")
    return base + table_suffix(width)


def table_lines(p: Production, atoms: list[dict], page_number: int | None = None) -> list[str]:
    width = len(atoms[0]["code"].replace(".", ""))
    name=table_name(p, width)
    if page_number is not None:
        name += f"_p{page_number}"
    out=[f"  - name: {name}","    kind: parameter","    dtype: Count","    indexed_by: hts_line",f"    source: {p.source_label} U.S. note {p.subdivision}","    metadata:","      proof:","        atoms:"]
    for a in atoms:
        out += ["          - path: versions[0].values","            kind: parameter","            source:",f"              corpus_citation_path: {a['page']}",f"              excerpt: {q(a['excerpt'])}","            context:",f"              subdivision: {q(a['subdivision'])}"]
    out += ["    versions:",f"      - effective_from: '{p.effective_from}'","        values:"]
    out += [f"          {key(a['code'])}: 1" for a in atoms]
    return out


def versioned_table_lines(
    production: Production,
    width: int,
    vintages: list[tuple[str, str, list[dict]]],
) -> list[str]:
    """Render one table whose legal list changes across pinned HTS releases."""
    name = table_name(production, width)
    source_labels: list[str] = []
    for _effective_from, release, atoms in vintages:
        for atom in atoms:
            labels = [
                atom.get("release", release),
                *[
                    confirmation["release"]
                    for confirmation in atom.get("confirmations", [])
                ],
            ]
            for label in labels:
                if label not in source_labels:
                    source_labels.append(label)
    out = [
        f"  - name: {name}",
        "    kind: parameter",
        "    dtype: Count",
        "    indexed_by: hts_line",
        f"    source: {' and '.join(source_labels)} U.S. note "
        f"{production.subdivision}",
        "    metadata:",
        "      proof:",
        "        atoms:",
    ]
    for version_index, (effective_from, release, atoms) in enumerate(vintages):
        for atom in atoms:
            out += [
                f"          - path: versions[{version_index}].values",
                "            kind: parameter",
                "            source:",
                f"              corpus_citation_path: {atom['page']}",
                f"              excerpt: {q(atom['excerpt'])}",
                "            context:",
                f"              subdivision: {q(atom['subdivision'])}",
                f"              release: {q(atom.get('release', release))}",
                f"              effective_from: {q(effective_from)}",
            ]
            for confirmation in atom.get("confirmations", []):
                out += [
                    f"          - path: versions[{version_index}].values",
                    "            kind: parameter",
                    "            source:",
                    (
                        "              corpus_citation_path: "
                        f"{confirmation['page']}"
                    ),
                    f"              excerpt: {q(confirmation['excerpt'])}",
                    "            context:",
                    f"              subdivision: {q(atom['subdivision'])}",
                    f"              release: {q(confirmation['release'])}",
                    f"              effective_from: {q(effective_from)}",
                    "              evidence_role: targeted official confirmation",
                ]
    out.append("    versions:")
    for index, (effective_from, _release, atoms) in enumerate(vintages):
        out.append(f"      - effective_from: '{effective_from}'")
        if index + 1 < len(vintages):
            effective_to = (
                date.fromisoformat(vintages[index + 1][0]) - timedelta(days=1)
            ).isoformat()
            out.append(f"        effective_to: '{effective_to}'")
        out += [
            "        values:",
            *[f"          {key(atom['code'])}: 1" for atom in atoms],
        ]
    return out


def render_note16_aluminum_precedence(
    vintage_pairs: list[
        tuple[str, str, list[tuple[Production, list[dict]]]]
    ],
) -> tuple[str, str]:
    """Render the effective-dated Note-16 aluminum precedence module."""
    action = "232-note16-aluminum-precedence"
    slug = FILES[action]
    cited_set = {
        atom["page"]
        for _date, _release, pairs in vintage_pairs
        for _production, atoms in pairs
        for atom in atoms
    }
    cited_set.update(
        confirmation["page"]
        for _date, _release, pairs in vintage_pairs
        for _production, atoms in pairs
        for atom in atoms
        for confirmation in atom.get("confirmations", [])
    )
    cited = sorted(cited_set, key=lambda path: int(path.rsplit("-", 1)[1]))
    summary = (
        f"Generated by {VERSION} deterministically from corpus-pinned USITC "
        "Revision 6 for the complete April-6 subdivision (ii) list, Revision 5 "
        "for the April-6 subdivision (vi)/(ix) lists, and Revision 10 for the "
        "June-8 lists. The official Proclamation 11021 Annex IV page-43 witness "
        "directly confirms the April-6 effective date, the note 16(c) aggregate "
        "15-percent listed-metal-weight proviso, and corrected HTS 7612.10.00; "
        "c(ii) continues beyond that retained page. Revision-10 atoms are "
        "checked unchanged in the Revision-12 campaign vintage and Revision 15; "
        "hand edits prohibited. Code incidence is unconditional for subdivision "
        "(ii). Subdivisions (vi) and (ix) remain candidates outside chapters 72, "
        "73, 74, and 76 because of the Proclamation's proviso."
    )
    out = [
        "format: rulespec/v1",
        "module:",
        "  proof_validation:",
        "    required: true",
        "  source_verification:",
        "    corpus_citation_paths:",
        *[f"      - {citation}" for citation in cited],
        "  summary: |-",
        f"    {summary}",
        "rules:",
    ]
    tests: list[str] = []
    module = f"us:policies/usitc/us-tariff-incidence/generated/{slug}"
    productions = [production for production, _atoms in vintage_pairs[-1][2]]
    for production in productions:
        for width in (8, 10):
            versions: list[tuple[str, str, list[dict]]] = []
            for effective_from, release, pairs in vintage_pairs:
                atoms = next(
                    atoms
                    for candidate, atoms in pairs
                    if candidate.table == production.table
                )
                versions.append(
                    (
                        effective_from,
                        release,
                        [
                            atom
                            for atom in atoms
                            if len(atom["code"].replace(".", "")) == width
                        ],
                    )
                )
            if not any(atoms for _date, _release, atoms in versions):
                continue
            out += versioned_table_lines(production, width, versions)
            present = versions[-1][2][0]
            name = table_name(production, width)
            tests += [
                f"- name: {q(name + ' current-vintage membership-present')}",
                "  period:",
                "    period_kind: custom",
                "    name: day",
                "    start: '2026-07-24'",
                "    end: '2026-07-24'",
                "  input:",
                f"    {module}#input.hts_line: {key(present['code'])}",
                "  output:",
                f"    {module}#{name}: 1",
            ]
    return "\n".join(out) + "\n", "\n".join(tests) + "\n"


def page_render(
    action: str, page: str, productions: list[tuple[Production, list[dict]]]
) -> tuple[str, str]:
    """Render one singular-source module containing only one printed page."""
    page_number = int(page.rsplit("-", 1)[1])
    directory = PAGE_ACTION_DIRS[action]
    module = (
        "us:policies/usitc/us-tariff-incidence/generated/"
        f"{directory}/page-{page_number}"
    )
    summary = (
        f"Generated by {VERSION} deterministically from USITC Rev-15 page "
        f"{page_number}; hand edits prohibited. Conditional fragments are "
        "encoded but composition wiring is deferred by the active hard-cut "
        "waiver set."
    )
    out = [
        "format: rulespec/v1",
        "module:",
        "  proof_validation:",
        "    required: true",
        "  source_verification:",
        f"    corpus_citation_path: {page}",
    ]
    conditional_outputs: list[str] = []
    for production, atoms in productions:
        if production.membership_class != "conditional":
            continue
        for width in (4, 6, 8, 10):
            if any(len(atom["code"].replace(".", "")) == width for atom in atoms):
                conditional_outputs.append(
                    f"{module}#{table_name(production, width)}_p{page_number}"
                )
    if conditional_outputs:
        out += ["  deferred_outputs:"]
        for output in conditional_outputs:
            out += [
                f"    - output: {output}",
                "      reason: |-",
                "        Composition regeneration is blocked by the active hard-cut",
                "        waiver set; conditional wiring is deferred to .github#106.",
            ]
    out += ["  summary: |-", f"    {summary}", "rules:"]
    tests: list[str] = []
    for production, atoms in productions:
        for width in (4, 6, 8, 10):
            group = [
                atom for atom in atoms
                if len(atom["code"].replace(".", "")) == width
            ]
            if not group:
                continue
            name = f"{table_name(production, width)}_p{page_number}"
            out += table_lines(production, group, page_number)
            present = group[0]
            tests += [
                f"- name: {q(name + ' membership-present')}",
                "  period:",
                "    period_kind: custom",
                "    name: day",
                "    start: '2026-08-03'",
                "    end: '2026-08-03'",
                "  input:",
                f"    {module}#input.hts_line: {key(present['code'])}",
                "  output:",
                f"    {module}#{name}: 1",
            ]
    return "\n".join(out) + "\n", "\n".join(tests) + "\n"

def partial_rules(action: str) -> list[str]:
    if action not in {"301","122"}: return []
    prefix="china_301" if action=="301" else "s122"
    page="us/statute/hts/chapter-99/page-260" if action=="301" else "us/statute/hts/chapter-99/page-221"
    out=[]
    for code,inp in PARTIAL_CODES:
        out += [f"  - name: {prefix}_{code}_partial_value_share","    kind: derived","    entity: Import","    dtype: Rate","    period: Day",f"    source: USITC HTS chapter 99 partial-value treatment for {code.replace('_','.')}","    metadata:","      proof:","        atoms:","          - path: versions[0].formula","            kind: formula","            source:",f"              corpus_citation_path: {page}",f"              excerpt: {q(code.replace('_','.'))}","    versions:","      - effective_from: '2026-08-03'","        formula: |-",f"          {inp}"]
    return out

PARTIAL_CODES=[("9802_00_40","foreign_repair_value_share"),("9802_00_50","foreign_repair_value_share"),("9802_00_60","foreign_processing_value_share"),("9802_00_80","foreign_assembly_value_share")]

def render(action: str, productions: list[tuple[Production,list[dict]]]) -> tuple[str,str]:
    cited=sorted({a['page'] for _,atoms in productions for a in atoms},key=lambda x:int(x.rsplit('-',1)[1]))
    if action == "301": cited = sorted(set(cited)|{"us/statute/hts/chapter-99/page-260"},key=lambda x:int(x.rsplit('-',1)[1]))
    if action == "122": cited = sorted(set(cited)|{"us/statute/hts/chapter-99/page-221"},key=lambda x:int(x.rsplit('-',1)[1]))
    slug=FILES[action]
    if action == "232-note16-aluminum-precedence":
        summary = (
            f"Generated by {VERSION} deterministically from the corpus-pinned "
            "USITC Revision-15 chapter-99 notes after an exact extracted-atom "
            "equality check against Revision 10; hand edits prohibited. These "
            "note 16(c)(ii), (vi), and (ix) lists are unchanged from the "
            "2026-06-08 snapshot through 2026-08-03. Code incidence is "
            "unconditional for subdivision (ii); subdivisions (vi) and (ix) "
            "remain candidates because note 16(c) requires at least 15-percent "
            "aggregate listed-metal weight outside chapters 72, 73, 74, and 76."
        )
    else:
        summary = (
            f"Generated by {VERSION} deterministically from the corpus-pinned "
            "USITC Rev-15 chapter-99 notes; hand edits prohibited. This is the "
            "codified state effective 2026-08-03 and therefore post-dates the "
            "analysis window; it is not a historical-vintage panel."
        )
    out=["format: rulespec/v1","module:","  proof_validation:","    required: true","  source_verification:","    corpus_citation_paths:"]+[f"      - {c}" for c in cited]
    out += ["  summary: |-",f"    {summary}","rules:"]
    tests=[]; module=f"us:policies/usitc/us-tariff-incidence/generated/{slug}"
    for p,atoms in productions:
        for width in (4,6,8,10):
            group=[a for a in atoms if len(a['code'].replace('.',''))==width]
            if not group: continue
            name=table_name(p, width)
            out += table_lines(p,group)
            present=group[0]
            tests += [f"- name: {q(name+' membership-present')}","  period:","    period_kind: custom","    name: day","    start: '2026-08-03'","    end: '2026-08-03'","  input:",f"    {module}#input.hts_line: {key(present['code'])}","  output:",f"    {module}#{name}: 1"]
    out += partial_rules(action)
    if action in {"301","122"}:
        pprefix="china_301" if action=="301" else "s122"
        for code,inp in PARTIAL_CODES:
            rule=f"{pprefix}_{code}_partial_value_share"
            tests += [f"- name: {q(rule+' passthrough')}","  period:","    period_kind: custom","    name: day","    start: '2026-08-03'","    end: '2026-08-03'","  input:",f"    {module}#input.{inp}: 0.25","  output:",f"    {module}#{rule}: 0.25"]
    return "\n".join(out)+"\n", "\n".join(tests)+"\n"

def generate(
    dest: Path,
    source: Path,
    selected: set[str] | None,
    selected_pages: set[int] | None = None,
) -> dict[str,str]:
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SHA256: raise SystemExit("notes snapshot sha mismatch")
    all_pages=pages(source); hashes={}; dest.mkdir(parents=True,exist_ok=True)
    for action,slug in FILES.items():
        if selected and action not in selected: continue
        if action == "232-note16-aluminum-precedence":
            vintage_pairs = []
            corpus = source.parents[5]
            proclamation_source = corpus / PROCLAMATION_11021_RELPATH
            if (
                hashlib.sha256(proclamation_source.read_bytes()).hexdigest()
                != PROCLAMATION_11021_SHA256
            ):
                raise SystemExit(
                    "Proclamation 11021 Annex IV page-43 snapshot sha mismatch"
                )
            proclamation_page = proclamation_11021_page(proclamation_source)
            revision6_source = corpus / REV6_RELPATH
            if (
                hashlib.sha256(revision6_source.read_bytes()).hexdigest()
                != REV6_SHA256
            ):
                raise SystemExit("USITC HTS Revision 6 notes snapshot sha mismatch")
            revision6_pages = pages(revision6_source)
            for effective_from, relpath, expected_sha, release in NOTE16_ALUMINUM_VINTAGES:
                vintage_source = corpus / relpath
                if hashlib.sha256(vintage_source.read_bytes()).hexdigest() != expected_sha:
                    raise SystemExit(f"{release} notes snapshot sha mismatch")
                vintage_pages = pages(vintage_source)
                pairs = []
                for production in GRAMMAR:
                    if production.action != action:
                        continue
                    atom_release = release
                    if (
                        effective_from == "2026-04-06"
                        and production.subdivision == "16(c)(ii)"
                    ):
                        atoms = extract(revision6_pages, production)
                        atom_release = "USITC HTS Revision 6"
                    else:
                        atoms = extract(vintage_pages, production)
                    annotated_atoms = []
                    for atom in atoms:
                        annotated = {**atom, "release": atom_release}
                        if (
                            effective_from == "2026-04-06"
                            and production.subdivision == "16(c)(ii)"
                            and atom["code"] == "7612.10.00"
                        ):
                            annotated["confirmations"] = [
                                {
                                    "page": proclamation_page["citation_path"],
                                    "excerpt": "7612.10.00",
                                    "release": (
                                        "Official Proclamation 11021 Annex IV "
                                        "page 43"
                                    ),
                                }
                            ]
                        annotated_atoms.append(annotated)
                    if (
                        effective_from == "2026-04-06"
                        and production.subdivision == "16(c)(ii)"
                        and not any(
                            atom.get("confirmations")
                            for atom in annotated_atoms
                        )
                    ):
                        raise SystemExit(
                            "Revision 6 c(ii) lacks officially confirmed HTS "
                            "7612.10.00"
                        )
                    pairs.append(
                        (
                            production,
                            annotated_atoms,
                        )
                    )
                vintage_pairs.append((effective_from, release, pairs))
            module, test = render_note16_aluminum_precedence(vintage_pairs)
            for name, text in [(slug + ".yaml", module), (slug + ".test.yaml", test)]:
                (dest / name).write_text(text)
                hashes[name] = hashlib.sha256(text.encode()).hexdigest()
            continue
        pairs=[]
        for p in GRAMMAR:
            if p.action==action:
                pairs.append((p,extract(all_pages,p)))
        if action == "forced-labor-301": pairs.extend(country_pairs(all_pages))
        if action in PAGE_ACTION_DIRS:
            by_page: dict[str, list[tuple[Production, list[dict]]]] = {}
            for production, atoms in pairs:
                page_atoms: dict[str, list[dict]] = {}
                for atom in atoms:
                    page_atoms.setdefault(atom["page"], []).append(atom)
                for page, fragment in page_atoms.items():
                    by_page.setdefault(page, []).append((production, fragment))
            for page, page_pairs in sorted(
                by_page.items(), key=lambda item: int(item[0].rsplit("-", 1)[1])
            ):
                page_number = int(page.rsplit("-", 1)[1])
                if selected_pages and page_number not in selected_pages:
                    continue
                module, test = page_render(action, page, page_pairs)
                directory = PAGE_ACTION_DIRS[action]
                for leaf, text in [
                    (f"page-{page_number}.yaml", module),
                    (f"page-{page_number}.test.yaml", test),
                ]:
                    name = f"{directory}/{leaf}"
                    target = dest / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(text)
                    hashes[name] = hashlib.sha256(text.encode()).hexdigest()
        else:
            module,test=render(action,pairs)
            for name,text in [(slug+".yaml",module),(slug+".test.yaml",test)]:
                (dest/name).write_text(text); hashes[name]=hashlib.sha256(text.encode()).hexdigest()
    return hashes


def verify_note16_aluminum_precedence_history(
    corpus: Path, rev15_source: Path
) -> None:
    """Prove the new precedence lists existed before notes 50/52 took effect."""
    rev10_source = corpus / REV10_RELPATH
    rev12_source = corpus / REV12_RELPATH
    rev6_source = corpus / REV6_RELPATH
    proclamation_source = corpus / PROCLAMATION_11021_RELPATH
    if hashlib.sha256(rev10_source.read_bytes()).hexdigest() != REV10_SHA256:
        raise SystemExit("Revision-10 notes snapshot sha mismatch")
    if hashlib.sha256(rev12_source.read_bytes()).hexdigest() != REV12_SHA256:
        raise SystemExit("Revision-12 notes snapshot sha mismatch")
    if hashlib.sha256(rev6_source.read_bytes()).hexdigest() != REV6_SHA256:
        raise SystemExit("Revision-6 notes snapshot sha mismatch")
    if (
        hashlib.sha256(proclamation_source.read_bytes()).hexdigest()
        != PROCLAMATION_11021_SHA256
    ):
        raise SystemExit(
            "Proclamation 11021 Annex IV page-43 snapshot sha mismatch"
        )
    proclamation_page = proclamation_11021_page(proclamation_source)
    proclamation_body = proclamation_page["body"]
    rev10_pages = pages(rev10_source)
    rev12_pages = pages(rev12_source)
    rev6_pages = pages(rev6_source)
    rev15_pages = pages(rev15_source)
    threshold = (
        "only apply where the weight of the applicable metal is at least 15 "
        "percent of the weight of the imported article"
    )
    for label, snapshot_pages in (
        ("Revision 10", rev10_pages),
        ("Revision 12", rev12_pages),
        ("Revision 15", rev15_pages),
    ):
        stream = "\n".join(page.get("body") or "" for page in snapshot_pages)
        if threshold not in stream:
            raise SystemExit(f"note 16(c) metal-weight threshold absent in {label}")
    if threshold not in proclamation_body:
        raise SystemExit(
            "note 16(c) metal-weight threshold absent in Proclamation 11021"
        )
    for production in GRAMMAR:
        if production.action != "232-note16-aluminum-precedence":
            continue
        rev10_codes = [atom["code"] for atom in extract(rev10_pages, production)]
        rev12_codes = [atom["code"] for atom in extract(rev12_pages, production)]
        rev15_codes = [atom["code"] for atom in extract(rev15_pages, production)]
        if not rev10_codes == rev12_codes == rev15_codes:
            raise SystemExit(
                f"{production.subdivision} changed between Revision 10, 12, and 15"
            )
        if production.subdivision == "16(c)(ii)":
            rev6_codes = [
                atom["code"] for atom in extract(rev6_pages, production)
            ]
            if rev6_codes != rev10_codes:
                raise SystemExit(
                    "Revision-6 c(ii) differs from the later pinned snapshots"
                )
            if "7612.10.00" not in rev6_codes or "7612.10.10" in rev6_codes:
                raise SystemExit(
                    "Revision-6 c(ii) does not carry the official 7612.10.00 "
                    "correction"
                )

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--corpus",type=Path,default=Path(os.environ.get("AXIOM_CORPUS_REPO",Path.home()/"TheAxiomFoundation/axiom-corpus-b1-full"))); ap.add_argument("--check",action="store_true"); ap.add_argument("--actions",default=""); ap.add_argument("--pages", default="")
    a=ap.parse_args(); selected={x for x in a.actions.split(',') if x} or None; selected_pages={int(x) for x in a.pages.split(',') if x} or None; source=a.corpus/RELPATH
    verify_note16_aluminum_precedence_history(a.corpus, source)
    with tempfile.TemporaryDirectory(prefix="b16-incidence-") as td:
        first=generate(Path(td)/"a",source,selected,selected_pages); second=generate(Path(td)/"b",source,selected,selected_pages)
        if first!=second: raise SystemExit("determinism FAILED")
        if a.check:
            drift=[n for n,h in first.items() if not (OUT/n).exists() or hashlib.sha256((OUT/n).read_bytes()).hexdigest()!=h]
            if drift: raise SystemExit(f"drift: {drift}")
            print(f"check OK: {len(first)} files")
        else:
            generate(OUT,source,selected,selected_pages); print(f"wrote {len(first)} files")
    return 0
if __name__=="__main__": raise SystemExit(main())
