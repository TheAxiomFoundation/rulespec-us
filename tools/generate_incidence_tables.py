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
from pathlib import Path

VERSION = "b1.6-incidence-1"
SHA256 = "0f3ed7ef2efb64383825db65e615959200770e8511c8d4834b16e02892cb9ec8"
RELPATH = "data/corpus/provisions/us/statute/2026-08-04-usitc-hts-2026-rev15-notes.jsonl"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "us/policies/usitc/us-tariff-incidence/generated"
HTS = re.compile(r"(?<![\d.])(\d{4}\.\d{2}\.\d{2}(?:\d{2})?)(?![\d.])")
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
)

FILES = {
    "301": "note20-china-301", "201": "note18-201-solar",
    "122": "note2aa-122-exemptions", "232-steel": "note16-232-steel",
    "232-aluminum": "note19-232-aluminum",
}

def pages(path: Path) -> list[dict]:
    out=[]
    for n, raw in enumerate(path.read_text().splitlines(), 1):
        d=json.loads(raw)
        if d.get("kind")=="page" and d.get("parent_citation_path")=="us/statute/hts/chapter-99": out.append(d)
    return sorted(out, key=lambda d:int(d["metadata"]["page_number"]))

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


def table_lines(p: Production, atoms: list[dict]) -> list[str]:
    width = len(atoms[0]["code"].replace(".", ""))
    name=table_name(p, width)
    out=[f"  - name: {name}","    kind: parameter","    dtype: Count","    indexed_by: hts_line",f"    source: USITC HTS Revision 15 U.S. note {p.subdivision}","    metadata:","      proof:","        atoms:"]
    for a in atoms:
        out += ["          - path: versions[0].values","            kind: parameter","            source:",f"              corpus_citation_path: {a['page']}",f"              excerpt: {q(a['excerpt'])}","            context:",f"              subdivision: {q(a['subdivision'])}"]
    out += ["    versions:","      - effective_from: '2026-08-03'","        values:"]
    out += [f"          {key(a['code'])}: 1" for a in atoms]
    return out

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
    slug=FILES[action]; summary=f"Generated by {VERSION} deterministically from the corpus-pinned USITC Rev-15 chapter-99 notes; hand edits prohibited. This is the codified state effective 2026-08-03 and therefore post-dates the analysis window; it is not a historical-vintage panel."
    out=["format: rulespec/v1","module:","  proof_validation:","    required: true","  source_verification:","    corpus_citation_paths:"]+[f"      - {c}" for c in cited]+["  summary: |-",f"    {summary}","rules:"]
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

def generate(dest: Path, source: Path, selected: set[str]|None) -> dict[str,str]:
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SHA256: raise SystemExit("notes snapshot sha mismatch")
    all_pages=pages(source); hashes={}; dest.mkdir(parents=True,exist_ok=True)
    for action,slug in FILES.items():
        if selected and action not in selected: continue
        pairs=[]
        for p in GRAMMAR:
            if p.action==action:
                pairs.append((p,extract(all_pages,p)))
        module,test=render(action,pairs)
        for name,text in [(slug+".yaml",module),(slug+".test.yaml",test)]:
            (dest/name).write_text(text); hashes[name]=hashlib.sha256(text.encode()).hexdigest()
    return hashes

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--corpus",type=Path,default=Path(os.environ.get("AXIOM_CORPUS_REPO",Path.home()/"TheAxiomFoundation/axiom-corpus-b1-full"))); ap.add_argument("--check",action="store_true"); ap.add_argument("--actions",default="")
    a=ap.parse_args(); selected={x for x in a.actions.split(',') if x} or None; source=a.corpus/RELPATH
    with tempfile.TemporaryDirectory(prefix="b16-incidence-") as td:
        first=generate(Path(td)/"a",source,selected); second=generate(Path(td)/"b",source,selected)
        if first!=second: raise SystemExit("determinism FAILED")
        if a.check:
            drift=[n for n,h in first.items() if not (OUT/n).exists() or hashlib.sha256((OUT/n).read_bytes()).hexdigest()!=h]
            if drift: raise SystemExit(f"drift: {drift}")
            print(f"check OK: {len(first)} files")
        else:
            generate(OUT,source,selected); print(f"wrote {len(first)} files")
    return 0
if __name__=="__main__": raise SystemExit(main())
