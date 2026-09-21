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

# One date, repository-wide, deliberately NOT a per-production field.
#
# The pinned artifact is the Rev-15 CODIFIED schedule.  It can establish what a
# list contains as codified on 2026-08-03; it cannot establish what that list
# contained on the day the underlying proclamation took effect.  That is why the
# five pre-existing families carry this same date while encoding instruments
# from 2018 (China 301 List 1, section 232 steel, section 201 CSPV), and why the
# emitted summary says so in terms.
#
# Nothing in this lane reads the value: b16_entry_flags._tables() unions
# ``values`` across every version without consulting ``effective_from``,
# b16_differential_check.generated_tables() takes ``versions[0]`` the same way,
# and the Oracles comparison window ends 2026-08-01, before this date is even
# reached.  The legally operative start dates for the note 50 and note 52
# charges -- 2026-07-22 (FR 2026-14542) and 2026-07-24 (FR 2026-15181) -- are
# already carried, with their own proof atoms, by the version boundaries of
# brazil_section_301_component_rate and forced_labor_section_301_component_rate
# in the composition, which is where a charge's temporal scope belongs.  Dating
# these membership tables 2026-07-22 would add no behaviour anywhere and would
# assert a historical fact about the lists' contents that this artifact cannot
# prove.  Both reasons point the same way, so the single codified date stands.
CODIFIED_EFFECTIVE_FROM = "2026-08-03"

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
    # U.S. note 50(a): exclusions from the heading 9903.05.01 Brazil additional
    # duty.  (a)(ii) and (a)(iii) are unconditional on the printed HTS line;
    # (a)(iv) general note 6 civil aircraft and (a)(v) pharmaceutical-use both
    # add a fact no tariff-line panel carries, so they stay a separate class.
    # (a)(vi) -- metals, vehicles, wood, MHDV, semiconductors, patented
    # pharmaceuticals -- names only chapter-99 SECTOR headings (9903.82,
    # 9903.94, 9903.76, 9903.74, 9903.79, 9903.04), which extract() drops by
    # design, so it has no production: it would emit nothing at all.
    # (a)(i) is not an hts_line-keyed list either.  It carries the charge, the
    # accompanied-baggage exclusion, the chapter 98 exclusion with its
    # 9802.00.40/.50/.60/.80 exception, and the four reduced duty bases the
    # note prescribes for those excepted 9802 entries.  Each turns on an entry
    # fact rather than a line fact, so none of them could have a production
    # here -- but unlike note 52, whose chapter 98 and baggage exclusions the
    # composition does apply at entry level, none of them is applied to the
    # Brazil duty anywhere.  The emitted summary says so in terms.
    Production("brazil-50", "note50_brazil_a_ii_membership", "50(a)(ii)", "(ii) As provided in heading 9903.05.03", "(iii) As provided in heading 9903.05.04"),
    Production("brazil-50", "note50_brazil_a_iii_membership", "50(a)(iii)", "(iii) As provided in heading 9903.05.04", "(iv) As provided in heading 9903.05.05", after_compiler=False),
    Production("brazil-50", "note50_brazil_gn6_conditional_membership", "50(a)(iv)", "(iv) As provided in heading 9903.05.05", "(v) As provided in heading 9903.05.06", "conditional"),
    Production("brazil-50", "note50_brazil_pharmaceutical_conditional_membership", "50(a)(v)", "(v) As provided in heading 9903.05.06", "(vi) As provided in heading 9903.05.07", "conditional"),
    # U.S. note 52: exclusions from the reciprocal charging headings
    # 9903.05.20-9903.05.84.  Same four shapes, same zero-atom metals limb at
    # (f).  (f) yields nothing because it names chapter-99 SECTOR headings --
    # 9903.82.02 and 9903.82.04-9903.82.26, then 9903.94, 9903.76, 9903.74,
    # 9903.79 and 9903.04 -- in place of HTS lines; the 9903.05.20-9903.05.84
    # charging headings it excepts from are incidental to that.  52(a) country
    # selection and subdivisions (g) through (k) are not hts_line-keyed
    # memberships, so no production can emit them -- which is a statement about
    # this generator, not about the repository.  52(a)'s country tiers reach
    # the panel total; its chapter 98 and baggage exclusions and the 52(g)/(h)
    # USMCA carve-outs are encoded at the entry level only; and 52(a)'s four
    # 9802 reduced duty bases, 52(i), all thirteen limbs of 52(j) and both
    # branches of the 52(k) ad valorem equivalent are applied nowhere.  The
    # emitted summary states which is which.
    Production("reciprocal-52", "note52_reciprocal_b_membership", "52(b)", "(b) As provided in heading 9903.05.86", "(c) As provided in heading 9903.05.87", after_compiler=False),
    Production("reciprocal-52", "note52_reciprocal_c_membership", "52(c)", "(c) As provided in heading 9903.05.87", "(d) As provided in heading 9903.05.88", after_compiler=False),
    Production("reciprocal-52", "note52_reciprocal_gn6_conditional_membership", "52(d)", "(d) As provided in heading 9903.05.88", "(e) As provided in heading 9903.05.89", "conditional", after_compiler=False),
    Production("reciprocal-52", "note52_reciprocal_pharmaceutical_conditional_membership", "52(e)", "(e) As provided in heading 9903.05.89", "(f) As provided in heading 9903.05.90", "conditional", after_compiler=False),
)

FILES = {
    "301": "note20-china-301", "201": "note18-201-solar",
    "122": "note2aa-122-exemptions", "232-steel": "note16-232-steel",
    "232-aluminum": "note19-232-aluminum",
    "brazil-50": "note50-brazil-exemptions",
    "reciprocal-52": "note52-reciprocal-exemptions",
}

# Appended verbatim to the shared module summary for the named action only.  The
# five pre-existing actions are absent, so their emitted bytes are unchanged.
# Each string must be a single line: render() writes the summary as one physical
# line inside a ``|-`` block scalar.
SUMMARY_NOTES = {
    "brazil-50": (
        " U.S. note 50(a) states EXCLUSIONS from the heading 9903.05.01 additional duty on articles the product"
        " of Brazil: membership in a table below means the listed article is carved out of that duty, not that it"
        " bears it. Subdivision (a)(ii) (\"articles the product of Brazil that are classifiable in the following"
        " subheadings of the HTSUS\") and subdivision (a)(iii) (\"the following particular articles the product of"
        " Brazil\") are published as unconditional membership tables keyed on the printed HTS line."
        " Subdivision (a)(iv) (civil aircraft and parts \"that otherwise meet the criteria of general note 6 of the"
        " HTSUS\") and subdivision (a)(v) (articles \"for use in pharmaceutical applications\") each additionally"
        " require a fact that no tariff-line panel carries, so they are published as separate conditional tables and"
        " must not be netted out of an entry's scope on the HTS line alone. Subdivision (a)(vi) cites only chapter-99"
        " sector headings (9903.82, 9903.94, 9903.76, 9903.74, 9903.79, 9903.04) and so yields no HTS atoms and no table"
        " here; of its eight limbs only the aluminum and steel part of limb (1) reaches this lane, through the"
        " separate section 232 membership tables. The other limbs - copper, passenger vehicles and their parts,"
        " wood products, medium- and heavy-duty vehicles and their parts, semiconductor articles, and patented"
        " pharmaceutical articles - are unconsumed here rather than absent from the repository: sector headings those"
        " limbs name are published as chapter-99 rate cells, the generated chapter-99 table"
        " us/policies/usitc/us-tariff-duty/lines/generated/ch99c.yaml carrying 9903.94.01, 9903.76.01, 9903.74.01"
        " and 9903.79.01 each with its own duty columns. What is missing is consumption: outside the section"
        " 232 route for aluminum and steel, no rule in the Brazil scope and no rule in the composition reads any of"
        " those headings, so they carve nothing out of the heading 9903.05.01 duty and entries covered by those"
        " limbs are scored in scope here - a known overstatement, declared, not a claim of coverage."
        " Country of origin is applied by the composition, which"
        " gates the charge on origin_is_brazil. The heading 9903.05.02 in-transit window and the heading 9903.05.08"
        " donation and 9903.05.09 informational-material exceptions are applied nowhere to the heading 9903.05.01"
        " duty: each of those three headings prints the applicable-subheading rate without that additional duty,"
        " yet no rule relieves a Brazil entry of it. The scope of that statement is the Brazil duty, not the"
        " repository. Two of the three underlying transaction facts do exist and are consumed elsewhere: the"
        " composition declares entry_is_humanitarian_donation_article and entry_is_informational_material_article and"
        " reads them in its IEEPA fentanyl exception rules and in forced_labor_section_301_entry_component_rate. What"
        " is missing is any Brazil rule that reads them - zero Brazil rules do. The third fact is absent outright:"
        " nothing states the heading 9903.05.02 July 22 window, and the composition's only declared in-transit input,"
        " entry_loaded_and_in_transit_before_july_24_2026, carries note 52's July 24 window instead. The generated"
        " Brazil component is \"if entry_is_brazil_301_listed and origin_is_brazil:"
        " brazil_section_301_additional_duty_rate else: 0\", and there is no brazil_section_301_entry_component_rate"
        " to hold any exception at all. Entries that qualify"
        " are therefore over-charged the full additional duty; this is an open residual of this lane, not a"
        " delegation. Note 52 is encoded the other way: its analogous heading 9903.05.85 in-transit and heading"
        " 9903.05.91 donation and 9903.05.92 informational-material exceptions are applied by"
        " forced_labor_section_301_entry_component_rate, the entry-level rule for that family - which"
        " us_tariff_total_ad_valorem_rate does not consume either, so the difference is that note 52's exceptions are"
        " expressed somewhere and note 50's are expressed nowhere. Note 50 has no counterpart rule. The heading"
        " 9903.05.01 overlay module does name article_described_in_headings_9903_05_02_through_9903_05_09, negated"
        " inside its Asset-level heading_applies rule; no module defines that identifier, so it is an overlay input,"
        " and the composition imports that module only for brazil_section_301_additional_duty_rate. It consumes"
        " neither heading_applies nor the identifier and declares neither as an entry input, so nothing there reaches"
        " an entry."
        " A second Brazil gap runs the same way and is stated here for the first time. Subdivision (a)(i) is not"
        " only the charging sentence: it excepts \"products for personal use included in accompanied baggage of"
        " persons arriving in the United States\", it provides that the duty \"shall not apply to goods for which"
        " entry is properly claimed under a provision of chapter 98 of the tariff schedule ... and whenever CBP"
        " agrees that entry under such a provision is appropriate, except for goods entered under heading 9802.00.80"
        " or subheadings 9802.00.40, 9802.00.50 or 9802.00.60\", and for those excepted 9802 entries it does not"
        " restore the full charge but prescribes a reduced duty base - \"For goods entered under subheadings"
        " 9802.00.40, 9802.00.50 and 9802.00.60, the additional duty applies to the value of repairs, alterations or"
        " processing performed, as described in the applicable subheading\", and \"For goods entered under heading"
        " 9802.00.80, the additional duty applies to the value of the article assembled abroad, less the cost or"
        " value of such products of the United States\". None of that reaches an entry here. The facts it would need"
        " are already declared - entry_is_personal_use_accompanied_baggage, entry_is_properly_claimed_chapter_98_entry,"
        " cbp_agrees_chapter_98_entry_is_appropriate and entry_is_9802_excepted_entry are all declared boolean inputs"
        " of the composition, and note 52 derives forced_labor_chapter_98_exclusion_applies from three of them - but"
        " no Brazil rule consumes any of them, because the Brazil family has no entry-level rule at all. A qualifying"
        " accompanied-baggage or chapter 98 entry is therefore charged the full heading 9903.05.01 duty, and a 9802"
        " entry is charged on full customs value rather than on the repair, processing or assembled-abroad base the"
        " note prescribes. Note 50 must not be called entry-complete. The reduced bases are not Brazil's alone:"
        " U.S. note 52(a) states the identical two sentences and no rule applies those either, whereas the section"
        " 338 alcohol family, whose U.S. note 51(a) states the same bases, does carry"
        " section_338_reduced_duty_base_applies - with proof atoms quoting both sentences - and exposes it on"
        " section_338_entry_component_rate instead of misstating those entries at full customs value. Notes 50 and"
        " 52 have no counterpart to that rule. This generator emits the parallel contrast itself: it publishes"
        " 9802.00.40, 9802.00.50, 9802.00.60 and 9802.00.80 partial-value-share rules for the China 301 and section"
        " 122 families and none for this one."
        " Atoms are held at the precision the source prints them: an atom printed as an 8-digit subheading is"
        " matched on the entry's 8-digit rate line, and an atom printed as a 10-digit statistical reporting number"
        " is matched on all ten digits, in the separate _membership_hts10 table. Subdivision (a)(ii) prints exactly"
        " five 10-digit lines - 0409.00.0005, 4407.99.0295, 8422.40.9181, 8505.11.0070 and 8537.10.9170 - inline"
        " among its 8-digit subheadings, and for none of the five does the list also print the enclosing 8-digit"
        " subheading, so the other statistical suffixes under those subheadings are deliberately NOT carved out"
        " here: the note named one reporting number and not its siblings, and reading it as naming the whole"
        " subheading would exclude articles it never listed. Running the other way, items (3), (4) and (5) of"
        " subdivision (a)(iii)'s enumerated particular articles are limited to goods \"for religious purposes only\""
        " - subheadings 1404.90.90, 1905.90.10 and 1905.90.90 - and an HTS-line key cannot carry that qualifier, so"
        " those three lines are carved out here for every entry on the line. That follows the treatment this"
        " repository already gives the identically worded U.S. note 2(aa)(iii) list; it is an over-exclusion on"
        " three lines, declared here rather than silently netted."
    ),
    "reciprocal-52": (
        " U.S. note 52 is the country-indexed reciprocal annex: its charging headings are 9903.05.20 through"
        " 9903.05.84, and subdivisions (b) through (f) state EXCLUSIONS from those duties, so membership in a table"
        " below means the listed article is carved out. Subdivision (b) (\"articles that are classifiable in the"
        " following provisions of the HTSUS\") and subdivision (c) (\"the following particular articles\") are"
        " published as unconditional membership tables keyed on the printed HTS line;"
        " subdivision (d) (civil aircraft and parts meeting general note 6) and subdivision"
        " (e) (articles \"for use in pharmaceutical applications\") require facts outside any tariff-line panel and are"
        " published as separate conditional tables that must not be netted out on the HTS line alone. Subdivision (f)"
        " yields no HTS atoms and no table here because it names chapter-99 sector headings in place of HTS lines -"
        " 9903.82.02 and 9903.82.04 through 9903.82.26 for metals and their derivatives, then the 9903.94 vehicle and"
        " vehicle-part headings, 9903.76 wood, 9903.74 medium- and heavy-duty vehicles, 9903.79 semiconductors and"
        " 9903.04 patented pharmaceuticals - and it is those sector headings, not the 9903.05.20 through 9903.05.84"
        " charging headings the limb excepts from, that the extractor drops. Of its eight limbs only the aluminum and"
        " steel part of limb (1) reaches this lane, through the separate section 232 membership tables. The rest are"
        " unconsumed rather than absent: heading 9903.05.90 has its own overlay module,"
        " us/policies/usitc/us-tariff-duty/overlays/section-301/forced-labor-metals-9903-05-90.yaml, defining an"
        " Asset-level forced_labor_metals_heading_applies over article-level facts, and sector headings those limbs"
        " name are published as chapter-99 rate cells, the generated chapter-99 table"
        " us/policies/usitc/us-tariff-duty/lines/generated/ch99c.yaml carrying 9903.94.01, 9903.76.01, 9903.74.01"
        " and 9903.79.01 each with its own duty columns; the hand-built CBP composition imports neither,"
        " so neither carves anything out of a charge in this lane and entries covered by those limbs are scored in"
        " scope here. Naming: the consuming composition identifiers are forced_labor_section_301_component_rate"
        " and entry_is_forced_labor_301_listed. That label is a misnomer - the phrase \"forced labor\" does not appear"
        " in U.S. note 52 - but it is retained unchanged because the composition contract binds to it; the tables in"
        " this module are named for the note instead. The remaining subdivisions are not all outside this repository,"
        " and what an hts_line-keyed table cannot express is not the same as what is unencoded. Country selection"
        " under 52(a) is encoded and reaches the panel total: the composition's"
        " origin_is_forced_labor_ten_percent_country and origin_is_forced_labor_twelve_and_one_half_percent_country"
        " gates, and its origin_is_eu, origin_is_taiwan, origin_is_japan, origin_is_korea and origin_is_switzerland"
        " gates, classify an entry's origin into the tiers the per-country headings 9903.05.20 through 9903.05.84"
        " state, and for those last five countries the"
        " paired headings' ceiling - charge only the shortfall where the column 1 rate is below the tier rate, and"
        " nothing where it is at or above it - is applied on the panel-facing rate as well. 52(a)'s chapter 98 and"
        " accompanied-baggage exclusions and the 52(g) and 52(h) USMCA carve-outs are encoded too, but only at the"
        " entry level: forced_labor_chapter_98_exclusion_applies, the declared"
        " entry_is_personal_use_accompanied_baggage, and forced_labor_usmca_exception_applies - the last derived from"
        " Canada or Mexico origin together with a declared entry_is_entered_free_of_duty_under_usmca - are consumed by"
        " forced_labor_section_301_entry_component_rate, while us_tariff_total_ad_valorem_rate sums the panel"
        " projection forced_labor_section_301_component_rate instead, so none of the three moves a panel result."
        " 52(a) is not fully applied even at that level. Its chapter 98 exclusion is expressly subject to an"
        " exception - \"except for goods entered under subheadings 9802.00.40, 9802.00.50 or 9802.00.60 or heading"
        " 9802.00.80\" - and forced_labor_chapter_98_exclusion_applies does carry it, as"
        " \"and not entry_is_9802_excepted_entry\". But the note does not then restore the full charge on those"
        " entries: it prescribes a reduced base, \"the additional duties apply to the value of repairs, alterations"
        " or processing performed, as described in the applicable subheading\" for 9802.00.40, 9802.00.50 and"
        " 9802.00.60, and \"the value of the article assembled abroad, less the cost or value of such products of"
        " the United States\" for 9802.00.80. No rule in this repository states either base for note 52. An excepted"
        " 9802 entry therefore falls straight through to forced_labor_section_301_component_rate, an ad valorem rate"
        " on full customs value, which overstates the duty the note imposes. That this is a gap and not a modelling"
        " choice is settled inside the same composition: U.S. note 51(a) prescribes the identical bases for the"
        " section 338 alcohol family, and there they are encoded - section_338_reduced_duty_base_applies, with proof"
        " atoms quoting both sentences, exposed by section_338_entry_component_rate rather than converted into a"
        " full-customs-value rate. Notes 50 and 52 have no counterpart rule."
        " One piece of that composition's wording is deliberately not carried into this module: it calls"
        " forced_labor_section_301_entry_component_rate \"the separate legally complete\""
        " CustomsEntry rate for the family, and that rule's own source line begins \"Legally complete forced labor"
        " section 301 component\". The wording is pre-existing and it is false - that rule applies neither 52(a)'s"
        " 9802 reduced bases, nor 52(i), nor any of the thirteen limbs of 52(j), nor the 52(k) ad valorem"
        " equivalent. Nothing in this module repeats or adopts it."
        " 52(g) and 52(h) never needed a membership table: the note excepts \"any products of Canada entered free of"
        " duty under the United States-Mexico-Canada Agreement\" and states the identical Mexico clause, naming no"
        " article at all. Two further limbs reach no entry at all, and the defect is consumption, not silence:"
        " identifiers for both exist and nothing reads them. 52(i) is the CAFTA-DR carve-out: it excludes \"a"
        " textile or apparel good as defined in"
        " subdivision (d)(v) of general note 29 of the HTSUS which is the product of Costa Rica, the Dominican"
        " Republic, El Salvador, Guatemala, Honduras or Nicaragua\" and is \"entered free of duty under the"
        " Dominican Republic-Central America-United States Free Trade Agreement, including any treatment set forth"
        " in subchapter XXII of chapter 98 of the HTSUS\". 52(j) is the country annex, and it is thirteen"
        " subdivisions, (j)(1) through (j)(13), not two: the United Kingdom, the European Union, Switzerland,"
        " Malaysia, Cambodia, Guatemala, El Salvador, Argentina, Bangladesh, Taiwan, Indonesia, Ecuador and Jordan,"
        " carried by headings 9903.05.96, 9903.05.97, 9903.05.98 and 9903.05.99 through 9903.06.21, each naming"
        " HTSUS provisions country by country. Twenty per-country overlay modules already reference those two limbs,"
        " through fourteen distinct identifiers - article_described_in_heading_9903_05_95 for 52(i), and for 52(j)"
        " article_described_in_heading_9903_05_96, _97 and _98 together with the ten range identifiers"
        " article_described_in_headings_9903_05_99_through_9903_06_01 through"
        " article_described_in_headings_9903_06_20_through_9903_06_21 - each negated inside that module's"
        " Asset-level heading-applies rule. No module defines any of the fourteen, so each is an overlay input"
        " rather than a derivation. The composition imports none of those modules, consumes none of the fourteen"
        " identifiers and declares none of them as an entry input: the same unconsumed-identifier pattern note 50"
        " declares for Brazil. The identifiers are therefore present while the legal tests behind them are not"
        " implemented in this composition: not the general note 29(d)(v) textile and apparel definition or the"
        " CAFTA-DR duty-free claim that 52(i) turns on, and not the thirteen per-country article lists that 52(j)"
        " turns on. 52(k) is split"
        " the same way. Its tier ceiling arithmetic is on the panel path, but the ad valorem equivalent it"
        " prescribes is derived nowhere, in either of its two branches: not for a good \"of a member state of the"
        " European Union, Japan, South Korea, Switzerland or Taiwan subject to a specific or compound rate of duty"
        " under column 1-General\", whose equivalent \"shall be determined by dividing the amount of duty payable"
        " under column 1-General by the customs value of the good\", and not for the separate branch, \"For any good"
        " of South Korea for which a specific or compound rate of duty under column 1-Special is properly claimed,"
        " the ad valorem equivalent rate of duty shall be determined in the same manner.\" The ceiling comparison"
        " runs against mfn_ad_valorem_rate, so on a line whose column 1 rate is specific or compound there is no"
        " equivalent rate for that comparison to use."
        " Atoms are held at the precision the source prints them: an atom printed as an 8-digit subheading is"
        " matched on the entry's 8-digit rate line, and an atom printed as a 10-digit statistical reporting number"
        " is matched on all ten digits, in the separate _membership_hts10 table. Subdivision (b) prints seven"
        " 10-digit lines - 0712.90.8550, 1204.00.0010, 1205.10.0010, 1205.90.0010, 1206.00.0031, 4407.99.0295 and"
        " 8505.11.0070 - and in no case also prints the enclosing 8-digit subheading, so the other statistical"
        " suffixes under those subheadings are deliberately NOT carved out here. Note 52 shows on its own face that"
        " the precision is deliberate: where the HTSUS already breaks out a sowing-seed statistical line,"
        " subdivision (b) lists that 10-digit line, and where it does not, subdivision (c) instead lists the 8-digit"
        " subheading and puts the qualifier in the article description, as in \"(3) Castor oil seeds, for sowing"
        " (classifiable in subheading 1207.30.00)\". Running the other way, seven of subdivision (c)'s enumerated"
        " particular articles carry such a qualifier - items (3) through (7) are limited to seeds \"for sowing\""
        " (subheadings 1207.30.00, 1207.40.00, 1207.50.00, 1207.60.00 and 1207.99.03) and items (8) and (9) to goods"
        " \"for religious purposes only\" (subheadings 1905.90.10 and 1905.90.90) - and an HTS-line key cannot carry"
        " it, so those seven lines are carved out here for every entry on the line. That is an over-exclusion on"
        " seven lines, declared here rather than silently netted."
    ),
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
    out += ["    versions:",f"      - effective_from: '{CODIFIED_EFFECTIVE_FROM}'","        values:"]
    out += [f"          {key(a['code'])}: 1" for a in atoms]
    return out

def partial_rules(action: str) -> list[str]:
    if action not in {"301","122"}: return []
    prefix="china_301" if action=="301" else "s122"
    page="us/statute/hts/chapter-99/page-260" if action=="301" else "us/statute/hts/chapter-99/page-221"
    out=[]
    for code,inp in PARTIAL_CODES:
        out += [f"  - name: {prefix}_{code}_partial_value_share","    kind: derived","    entity: Import","    dtype: Rate","    period: Day",f"    source: USITC HTS chapter 99 partial-value treatment for {code.replace('_','.')}","    metadata:","      proof:","        atoms:","          - path: versions[0].formula","            kind: formula","            source:",f"              corpus_citation_path: {page}",f"              excerpt: {q(code.replace('_','.'))}","    versions:",f"      - effective_from: '{CODIFIED_EFFECTIVE_FROM}'","        formula: |-",f"          {inp}"]
    return out

PARTIAL_CODES=[("9802_00_40","foreign_repair_value_share"),("9802_00_50","foreign_repair_value_share"),("9802_00_60","foreign_processing_value_share"),("9802_00_80","foreign_assembly_value_share")]

def render(action: str, productions: list[tuple[Production,list[dict]]]) -> tuple[str,str]:
    cited=sorted({a['page'] for _,atoms in productions for a in atoms},key=lambda x:int(x.rsplit('-',1)[1]))
    if action == "301": cited = sorted(set(cited)|{"us/statute/hts/chapter-99/page-260"},key=lambda x:int(x.rsplit('-',1)[1]))
    if action == "122": cited = sorted(set(cited)|{"us/statute/hts/chapter-99/page-221"},key=lambda x:int(x.rsplit('-',1)[1]))
    slug=FILES[action]; summary=f"Generated by {VERSION} deterministically from the corpus-pinned USITC Rev-15 chapter-99 notes; hand edits prohibited. This is the codified state effective {CODIFIED_EFFECTIVE_FROM} and therefore post-dates the analysis window; it is not a historical-vintage panel.{SUMMARY_NOTES.get(action,'')}"
    out=["format: rulespec/v1","module:","  proof_validation:","    required: true","  source_verification:","    corpus_citation_paths:"]+[f"      - {c}" for c in cited]+["  summary: |-",f"    {summary}","rules:"]
    tests=[]; module=f"us:policies/usitc/us-tariff-incidence/generated/{slug}"
    for p,atoms in productions:
        for width in (4,6,8,10):
            group=[a for a in atoms if len(a['code'].replace('.',''))==width]
            if not group: continue
            name=table_name(p, width)
            out += table_lines(p,group)
            present=group[0]
            tests += [f"- name: {q(name+' membership-present')}","  period:","    period_kind: custom","    name: day",f"    start: '{CODIFIED_EFFECTIVE_FROM}'",f"    end: '{CODIFIED_EFFECTIVE_FROM}'","  input:",f"    {module}#input.hts_line: {key(present['code'])}","  output:",f"    {module}#{name}: 1"]
    out += partial_rules(action)
    if action in {"301","122"}:
        pprefix="china_301" if action=="301" else "s122"
        for code,inp in PARTIAL_CODES:
            rule=f"{pprefix}_{code}_partial_value_share"
            tests += [f"- name: {q(rule+' passthrough')}","  period:","    period_kind: custom","    name: day",f"    start: '{CODIFIED_EFFECTIVE_FROM}'",f"    end: '{CODIFIED_EFFECTIVE_FROM}'","  input:",f"    {module}#input.{inp}: 0.25","  output:",f"    {module}#{rule}: 0.25"]
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
