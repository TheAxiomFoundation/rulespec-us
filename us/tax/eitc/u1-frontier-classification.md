# EITC derived-frontier classification

Date: 2026-07-27

## Decision

The 34 derived or legally preclassified scalar leaves identified by the m1
assessment divide as follows:

| Bucket | Count |
|---|---:|
| (a) Already computed in-graph | 0 |
| (b) Declarable frontier fact | 13 |
| (c) Must-encode | 21 |
| **Total** | **34** |

This applies the administrative-cut rule strictly. A value is in bucket (b)
only when the administering agency receives the same conclusion in a named
return field or authoritative SSA/military record. A form that merely supplies
inputs from which the agency calculates the conclusion is not enough. The IRS
has not yet published a final tax-year-2026 Form 1040 package, so the return
citations below use the current final 2025 forms to identify the existing
administrative interface. The 2026 Form W-2 is final.

Corpus sizes use the distinct retained citation paths at the repository's
pinned axiom-corpus commit
`bf97b17baebfdf12601f7c23697524bf5adcdaed`. “Absent” means the cross-referenced
provision has no retained path at that pin. Effort estimates cover a reviewed
RuleSpec module and focused companion tests; they exclude new engine relation
features or administrative-data ingestion unless the row says otherwise.

## One-row-per-item classification

| # | Frontier item | Bucket | Controlling evidence, corpus size, and effort |
|---:|---|:---:|---|
| 1 | `adjusted_gross_income` | (b) | [Form 1040][f1040] lines 11a and 11b expressly report “adjusted gross income.” Section 62's rule exists locally but is not imported into section 32. |
| 2 | `childless_taxpayer_or_spouse_age_eligible_for_eitc` | (c) | 26 USC 32(c)(1)(A)(ii)(II); **1 path**, `us/statute/26/32/c/1`. About **0.5 day** to aggregate the existing Person age predicate across taxpayer/spouse roles and wire boundary tests. [Form 8862][f8862] lines 10a-10b report ages, not the thresholded conclusion. |
| 3 | `childless_taxpayer_principal_place_of_abode_in_united_states_more_than_half_year` | (b) | [Form 1040][f1040] page 1 has the exact unnumbered “main home ... in the U.S. for more than half” checkbox; [Form 8862][f8862] lines 9a-9b record the taxpayer/spouse U.S.-home days and state the administrative cutoff. |
| 4 | `eitc_disallowance_period_applies` | (c) | 26 USC 32(k)(1); **1 path**, `us/statute/26/32/k/1`. About **2-4 hours** to compute the two- and ten-year windows from prior final-determination year/type facts. Form 8862's instructions describe the bans, but no filed line reports the active-period conclusion. |
| 5 | `eitc_relevant_investment_income` | (c) | 26 USC 32(i)(2); **1 path**, `us/statute/26/32/i/2`. About **1-2 days** to assemble and net every statutory disqualified-income category and test the zero/netting boundaries. No return line reports this EITC-specific aggregate. |
| 6 | `individual_principal_place_of_abode_with_taxpayer_fraction` | (c) | 26 USC 32(c)(3) through 152(c)(1)(B); **2 paths**, `us/statute/26/32/c/3` and `us/statute/26/152/c/1`. About **0.5-1 day** for day counting, birth/death and temporary-absence treatment, normalization, and tests. Form 8862 line 7 supplies days and Form 1040 Dependents row (5) supplies only the greater-than-half result, not this fraction. |
| 7 | `prior_deficiency_denial_without_required_eligibility_information` | (b) | [Form 8862][f8862] header records that a non-math/clerical prior reduction or disallowance occurred; line 2's EIC box and Part II lines 3-11 are the Secretary-required eligibility information. IRS account status plus presence/completion of this filed form directly supplies the procedural boundary fact. |
| 8 | `qualifying_child_marital_status_requires_section_151_entitlement` | (c) | 26 USC 32(c)(3)(B); **1 path**, `us/statute/26/32/c/3`. About **2-4 hours** to add the child's year-end marital-status fact, derive the exception gate, and test it. No claimant-return line reports this precise gate. |
| 9 | `satisfies_eitc_separated_spouse_rules` | (b) | [Form 1040][f1040] page 1 has the exact unnumbered checkbox after Dependents for MFS/HOH filers who lived apart for the last six months, or have a state-law written separation/decree and no shared household at year end. Those are the section 32(d)(2) administrative branches. |
| 10 | `taxpayer_entitled_to_section_151_deduction_for_child_or_would_be_but_for_section_152_e` | (b) | [Form 1040][f1040] Dependents rows (1)-(4) record the claimed dependent; [Form 8862][f8862] line 16 directly asks whether the person is the filer's dependent; [Form 8332][f8332] Parts I-II record the current/future section 152(e) release. |
| 11 | `taxpayer_is_dependent_for_section_151_to_another_taxpayer` | (b) | [Form 1040][f1040] line 12a says “Someone can claim You as a dependent”; [Form 8862][f8862] lines 11a-11b repeat the taxpayer/spouse conclusion. |
| 12 | `taxpayer_is_nonresident_alien_for_any_portion_of_year` | (b) | [Form 1040][f1040] line 12c records dual-status-alien status; [Form 1040-NR][f1040nr] is the full-year nonresident return; [Schedule OI][f1040nro] items B, E, and H record tax residence, immigration status, and U.S.-presence days. IRS observes the filed residence classification and period from this return package. |
| 13 | `taxpayer_is_qualifying_child_of_another_taxpayer` | (b) | [Form 8862][f8862] line 4 asks exactly whether the taxpayer or spouse could be claimed as another taxpayer's qualifying child. |
| 14 | `taxpayer_treated_as_resident_by_section_6013_g_or_h_election` | (b) | [Form 1040][f1040] Filing Status has the exact unnumbered checkbox for treating a nonresident or dual-status spouse as a U.S. resident for the entire year and requires the election statement when applicable. |
| 15 | `child_resided_with_both_parents_same_amount_of_time_and_taxpayer_parent_has_highest_adjusted_gross_income` | (c) | 26 USC 152(c)(4)(B)(ii); **1 path**, `us/statute/26/152/c/4`. About **1-3 days**, and possibly relation-engine support, for cross-parent residence equality plus a tie-aware AGI maximum. |
| 16 | `child_resided_with_taxpayer_parent_for_longest_period` | (c) | 26 USC 152(c)(4)(B)(i); **1 path**, `us/statute/26/152/c/4`. About **1-3 days**, and possibly relation-engine support, for cross-parent residence-duration comparison and tests. |
| 17 | `individual_is_permanently_and_totally_disabled` | (b) | [Form 1040][f1040] Dependents row (6) has a “Permanently and totally disabled” checkbox; [Schedule EIC][f1040sei] line 4b asks the same conclusion. The section 22 producer is a near-match but is not imported. |
| 18 | `individual_is_student` | (b) | [Form 1040][f1040] Dependents row (6) has a “Full-time student” checkbox; [Schedule EIC][f1040sei] line 4a also records the under-24 student branch. |
| 19 | `individual_is_younger_than_taxpayer` | (c) | 26 USC 152(c)(3)(A); **1 path**, `us/statute/26/152/c/3`. About **0.5 day** once both ages and taxpayer roles are available, including equal-age boundary tests. |
| 20 | `individual_may_be_claimed_as_qualifying_child_by_two_or_more_taxpayers` | (c) | 26 USC 152(c)(4)(A); **1 path**, `us/statute/26/152/c/4`. About **1-3 days** for cross-taxpayer candidate relations, qualifying-child evaluation, counting, and tests. |
| 21 | `no_parent_of_individual_is_a_claiming_taxpayer` | (c) | 26 USC 152(c)(4)(A)(ii); **1 path**, `us/statute/26/152/c/4`. About **0.5-1 day** after parent/claim relations exist, to aggregate filed-claim facts and test empty/multiple-parent cases. |
| 22 | `parents_of_individual_may_claim_individual_but_no_parent_claims` | (c) | 26 USC 152(c)(4)(C); **1 path**, `us/statute/26/152/c/4`. About **1-3 days** to combine parent eligibility across tax units with actual claim choices. |
| 23 | `taxpayer_adjusted_gross_income_higher_than_highest_parent_adjusted_gross_income` | (c) | 26 USC 152(c)(4)(C); **1 path**, `us/statute/26/152/c/4`. About **1-3 days**, and possibly relation-engine support, for parent-role traversal, AGI maximum, strict comparison, and ties. |
| 24 | `taxpayer_has_highest_adjusted_gross_income_among_claiming_taxpayers` | (c) | 26 USC 152(c)(4)(A)(ii); **1 path**, `us/statute/26/152/c/4`. About **1-3 days**, and possibly relation-engine support, for claimant traversal and tie-aware AGI ranking. |
| 25 | `employee_compensation_includible_in_gross_income` | (c) | 26 USC 32(c)(2)(A)(i) and the section 61 gross-income surface; **18 paths**: `us/statute/26/32/c/2` plus all 17 paths at `us/statute/26/61`, `/61/a`, `/61/a/1` through `/14`, and `/61/b`. About **2-4 days** to assemble wages, tips, statutory-employee income, and other includible compensation with the gross-income inclusions/exclusions and focused tests. Form 1040 line 1z is not the complete EIC aggregate: the EIC instructions separately add statutory-employee Schedule C income. |
| 26 | `net_earnings_from_self_employment_after_self_employment_tax_deduction` | (c) | 26 USC 32(c)(2)(A)(ii), 1402(a), and 164(f); **22 paths**: `us/statute/26/32/c/2`, all 18 paths at `us/statute/26/1402/a` through `/17`, and all 3 paths at `us/statute/26/164/f` through `/2`. About **5-10 days** because section 1402(a) is deferred and its 17 special-rule paragraphs, unresolved cross-references, optional methods, and entity issues dominate the work. |
| 27 | `nonresident_alien_income_not_connected_with_united_states_business` | (c) | 26 USC 32(c)(2)(B)(iii) and 871(a); **1 retained path**, `us/statute/26/32/c/2`; section 871(a) is **absent** at the pin. About **2-4 days after sourcing section 871(a)** to classify and aggregate only the employee compensation subject to that subsection. [Schedule NEC][f1040nrn] has broader income categories and separate rate-column totals, not one line for this section 32 subset. |
| 28 | `armed_forces_member_in_missing_status_during_vietnam_conflict_as_result_of_conflict` | (b) | DD Form 1300, Report of Casualty, blocks 4a-4g record hostile type, missing/MIA status, date, place, circumstances, and duty. [DoDI 1300.18][dodi130018] makes DCIPS the system of record; [SSA POMS RS 01702.370][ssa1300] says SSA accepts DD Form 1300 showing MIA status. |
| 29 | `civilian_employee_in_missing_status_during_vietnam_conflict_as_result_of_conflict` | (c) | 26 USC 112(d)(2)-(3) and 5 USC 5561(4)-(5); **2 retained paths**, `us/statute/26/112/d/2` and `/d/3`; the Title 5 paths are **absent**. About **1.5-2.5 days** after sourcing the civilian missing-status definitions, conflict dates, and causation facts. |
| 30 | `hospitalized_resulting_from_combat_zone_wounds_disease_or_injury` | (c) | 26 USC 112(a)(2), (b)(2), and (c)(2)-(3); **4 paths**, `us/statute/26/112/a/2`, `/b/2`, `/c/2`, and `/c/3`. About **1-2 days** to model the service/medical event, causal link, hospital interval, and tests. No exact field was found that records the statutory causal conclusion. |
| 31 | `maximum_enlisted_amount_for_commissioned_officer_months` | (c) | 26 USC 112(c)(5)(A)-(B), with Title 37 pay cross-references; **1 retained path**, `us/statute/26/112/c/5`; the required Title 37 paths are **absent**. About **1-2 days after sourcing** the applicable highest enlisted basic pay plus hostile-fire/imminent-danger pay components. |
| 32 | `months_beginning_after_combatant_activities_termination` | (c) | 26 USC 112(a)(2), (b)(2), and (c)(3); **3 paths**, `us/statute/26/112/a/2`, `/b/2`, and `/c/3`. About **0.5-1 day after sourcing the controlling termination designations** for month arithmetic and boundaries. |
| 33 | `served_in_combat_zone_during_month` | (b) | [Navy CPPA Handbook][cppa-handbook] Appendix A-2, “Request to Start/Stop HFP/CZTE,” paragraph 1 records personnel and the effective date; the [Navy HF/IDP SOP][navy-sop] records Effective/Start Date, Stop Date, `CZ-DEDTN`, and Country Code (CZTE) in NSIPS/MMPA. These are the service pay system's month-level CZTE records. |
| 34 | `vietnam_combat_zone_hospitalization_month_after_january_1978` | (c) | Final sentences of 26 USC 112(a) and (b); **2 paths**, `us/statute/26/112/a` and `/b`. Less than **0.5 day** after hospitalization dates are available, to implement the January 1978 boundary and tests. |

## Why bucket (a) is empty

The final `eitc` ancestry reaches 28 derived nodes, but none computes one of
these 34 leaves under an alias. The important near-misses are:

- `us:statutes/26/32#eitc_childless_age_eligible` computes one Person's age
  predicate, but the final TaxUnit rule consumes the uncomputed
  taxpayer-or-spouse aggregate.
- `us:statutes/26/22#permanently_totally_disabled` and
  `us:statutes/26/62#adjusted_gross_income` exist but section 32 does not
  import them; section 62 also still bridges a deferred deductions aggregate.
- Section 1402(a)(12) and section 164(f) have partial self-employment
  deductions, but section 32(c)(2) imports neither, and section 1402(a)'s final
  net-earnings output is explicitly deferred.
- The imported `us:statutes/26/7703#taxpayer_married_under_general_rule`
  computes section 7703(a) marital status, not section 32(d)'s
  separated-spouse test. Section 7703(b) and section 151 loader side effects
  are not final-output dependencies.
- Section 1411 net investment income is not section 32(i)(2) disqualified
  income, section 61 gross income is not the section 32(c)(2) employee
  compensation component, and neither is imported.

[f1040]: https://www.irs.gov/pub/irs-pdf/f1040.pdf
[f1040nr]: https://www.irs.gov/pub/irs-pdf/f1040nr.pdf
[f1040nro]: https://www.irs.gov/pub/irs-pdf/f1040nro.pdf
[f1040nrn]: https://www.irs.gov/pub/irs-pdf/f1040nrn.pdf
[f1040sei]: https://www.irs.gov/pub/irs-pdf/f1040sei.pdf
[f8862]: https://www.irs.gov/pub/irs-pdf/f8862.pdf
[f8332]: https://www.irs.gov/pub/irs-pdf/f8332.pdf
[dodi130018]: https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/130018p.pdf
[ssa1300]: https://secure.ssa.gov/apps10/poms.nsf/lnx/0301702370
[cppa-handbook]: https://www.mynavyhr.navy.mil/Portals/55/Support/PayPers/CPCResources/CPPA_HANDBOOK_12JUN2025.pdf
[navy-sop]: https://www.mynavyhr.navy.mil/Portals/55/Support/PayPers/CPCResources/SOP/Hostile_Fire-Imminent_Danger_Pay_SOP_Rev_APR_2025.pdf
