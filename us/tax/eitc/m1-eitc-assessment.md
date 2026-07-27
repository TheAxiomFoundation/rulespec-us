# EITC certification assessment

Date: 2026-07-27

## Bottom line

**No: the current 26 USC 32 output is not honestly certifiable today.**
The output itself is defined by section 32, and its reached executable rules
are generally grounded in section 32, section 152(c), section 7703(a), section
112, or the official 2026 IRS revenue procedure. But its final dataflow has
**65 module-qualified frontier leaves**: 64 scalar inputs and one structural
relation. Under the conservative classification used below, **34 are derived
or legally preclassified quantities** that still need encoding or an explicit
evidence-free bridge. Only 30 are raw or directly recorded facts.

The decisive example is childless age eligibility. Section 32's module
defines `eitc_childless_age_eligible` from a person's `age`, but the final
`eitc_demographic_eligible` rule does not consume it. It consumes the supplied
legal conclusion
`childless_taxpayer_or_spouse_age_eligible_for_eitc`. Changing `age` therefore
cannot exercise the final credit's age boundary. Computing that flag in a
program transformation would violate the task's no-transformations rule;
computing it in an oracle adapter would produce a useful diagnostic, but not
end-to-end provision evidence.

Two further blockers reinforce the answer:

- the existing section 32 companion suite is stale: its two amount cases name
  a removed wage input and removed
  `self_employment_earned_income_component` output, so both fail before
  checking the credit; and
- a citation-path closure claim has a 69-path minimum universe, but only six
  paths mechanically join to exact proof-index or file-path evidence. That is
  not a content-level encoded count, which remains unknown without a reviewed
  69-row ledger.

## Exhaustive declared frontier

`O` means a raw or directly recorded fact available from a return,
administrative record, vital record, service record, or direct factual report.
`D` means an aggregation, comparison, statutory classification, or legal
conclusion that the current subgraph does not compute and that must be encoded
for a general certificate. For example, residence dates are facts, but a
more-than-half-year test is derived; enrollment is a fact, but “student” under
section 152(f)(2) is a statutory classification.

There are **64 distinct module-qualified scalar input IDs** below. The section
32 TaxUnit `filing_status` and section 152(c) Person `filing_status` share an
unqualified spelling, but remain separate legal/entity inputs in the compiled
runtime contract.

### 26 USC 32: 22 scalar inputs plus one relation

| Class | Input | Why |
|---|---|---|
| D | `adjusted_gross_income` | Section 62 assembled total; section 32 does not import its computation. |
| D | `childless_taxpayer_or_spouse_age_eligible_for_eitc` | Aggregates the age predicate across the taxpayer/spouse; the encoded Person predicate is disconnected from the final credit. |
| D | `childless_taxpayer_principal_place_of_abode_in_united_states_more_than_half_year` | Applies the statutory more-than-half-year threshold to residence facts. |
| D | `eitc_disallowance_period_applies` | Section 32(k)(1) multi-year fraud or reckless-disregard consequence. |
| D | `eitc_relevant_investment_income` | Section 32(i)(2) assembled disqualified-income total; only its threshold test is encoded. |
| O | `filing_status` | Filed-return status. |
| D | `individual_principal_place_of_abode_with_taxpayer_fraction` | Assembles residence dates or durations into a fraction. |
| D | `prior_deficiency_denial_without_required_eligibility_information` | Section 32(k)(2) procedural and legal conclusion. |
| D | `qualifying_child_marital_status_requires_section_151_entitlement` | Section 32(c)(3)(B) exception gate, not merely marital status. |
| O | `qualifying_child_name_age_and_tin_included_on_return` | Return-field presence. |
| O | `qualifying_child_principal_place_of_abode_is_in_united_states` | Residence fact. |
| D | `satisfies_eitc_separated_spouse_rules` | Multi-condition section 32(d) legal test. |
| O | `spouse_includes_required_social_security_number_on_return` | Return and SSN fact. |
| O | `taxable_year_closed_by_reason_of_taxpayer_death` | Tax-period/vital-record fact. |
| O | `taxable_year_is_full_12_months` | Tax-period fact. |
| O | `taxpayer_claims_section_911_benefits` | Return election/claim fact. |
| D | `taxpayer_entitled_to_section_151_deduction_for_child_or_would_be_but_for_section_152_e` | Sections 151 and 152(e) entitlement conclusion. |
| O | `taxpayer_includes_required_social_security_number_on_return` | Return and SSN fact. |
| D | `taxpayer_is_dependent_for_section_151_to_another_taxpayer` | Sections 151/152 legal conclusion. |
| D | `taxpayer_is_nonresident_alien_for_any_portion_of_year` | Tax-law residence classification over the taxable year. |
| D | `taxpayer_is_qualifying_child_of_another_taxpayer` | Requires applying section 152(c) for another taxpayer. |
| D | `taxpayer_treated_as_resident_by_section_6013_g_or_h_election` | Legal consequence of a section 6013(g) or (h) election, not merely election-field presence. |
| O | `relation.qualifying_child_of_tax_unit` | Structural filing-unit membership relation; it has no formula or rule-level source. |

### 26 USC 152(c): 17 scalar inputs

| Class | Input | Why |
|---|---|---|
| D | `child_resided_with_both_parents_same_amount_of_time_and_taxpayer_parent_has_highest_adjusted_gross_income` | Residence comparison plus an AGI ranking. |
| D | `child_resided_with_taxpayer_parent_for_longest_period` | Cross-parent residence-duration comparison. |
| O | `filing_status` | Candidate child's filed-return status. |
| O | `individual_age_at_close_of_calendar_year` | Age fact. |
| O | `individual_is_child_of_taxpayer_or_descendant_of_such_child` | Family relationship fact. |
| D | `individual_is_permanently_and_totally_disabled` | Statutory classification defined outside section 152(c), not a raw diagnosis. |
| O | `individual_is_sibling_stepsibling_or_descendant_of_such_relative` | Family relationship fact. |
| D | `individual_is_student` | Section 152(f)(2) classification assembled from enrollment facts. |
| D | `individual_is_younger_than_taxpayer` | Comparison of two ages rather than either observed age. |
| D | `individual_may_be_claimed_as_qualifying_child_by_two_or_more_taxpayers` | Requires applying the qualifying-child test across taxpayers. |
| D | `no_parent_of_individual_is_a_claiming_taxpayer` | Cross-parent aggregation of filed-claim facts. |
| O | `parents_filing_status` | Parents' filed-return status. |
| D | `parents_of_individual_may_claim_individual_but_no_parent_claims` | Parent eligibility plus claim-choice composite. |
| O | `return_filed_only_for_claim_of_refund` | Return-purpose fact. |
| D | `taxpayer_adjusted_gross_income_higher_than_highest_parent_adjusted_gross_income` | AGI assembly and cross-taxpayer comparison. |
| D | `taxpayer_has_highest_adjusted_gross_income_among_claiming_taxpayers` | AGI assembly and claimant ranking. |
| O | `taxpayer_is_parent_of_individual` | Family relationship fact. |

### 26 USC 32(c)(2): seven scalar inputs

| Class | Input | Why |
|---|---|---|
| D | `employee_compensation_includible_in_gross_income` | Tax-law assembled includible compensation, broader than raw wages. |
| D | `net_earnings_from_self_employment_after_self_employment_tax_deduction` | Requires sections 1402 and 164(f). |
| D | `nonresident_alien_income_not_connected_with_united_states_business` | Tax-law classification and aggregation. |
| O | `penal_institution_service_compensation` | Compensation/source fact. |
| O | `pension_or_annuity_amount` | Reported payment amount. |
| O | `subsidized_state_work_activity_service_compensation` | Preclassified state-program compensation amount from the administering record. |
| O | `taxpayer_elects_to_treat_section_112_excluded_amounts_as_earned_income` | Return election fact. |

### 26 USC 112: 14 scalar inputs

| Class | Input | Why |
|---|---|---|
| O | `active_service_compensation_as_commissioned_officer_excluding_pensions_and_retirement_pay` | Military pay-record amount. |
| O | `active_service_compensation_as_enlisted_member_excluding_pensions_and_retirement_pay` | Military pay-record amount. |
| D | `armed_forces_member_in_missing_status_during_vietnam_conflict_as_result_of_conflict` | Combines status, statutory conflict dates, and causation. |
| O | `armed_forces_missing_status_active_service_compensation` | Military pay-record amount. |
| D | `civilian_employee_in_missing_status_during_vietnam_conflict_as_result_of_conflict` | Combines status, statutory conflict dates, and causation. |
| O | `civilian_employee_missing_status_active_service_compensation` | Government pay-record amount. |
| O | `commissioned_officer_in_armed_forces_excluding_commissioned_warrant_officer` | Rank/status fact. |
| D | `hospitalized_resulting_from_combat_zone_wounds_disease_or_injury` | Causal and statutory classification assembled from service and medical facts. |
| D | `maximum_enlisted_amount_for_commissioned_officer_months` | Section 112(c)(5)/Title 37 pay-component sum. |
| O | `member_below_grade_of_commissioned_officer_in_armed_forces` | Rank/status fact. |
| D | `months_beginning_after_combatant_activities_termination` | Date arithmetic from a legally designated termination date. |
| O | `officially_absent_from_post_of_duty_without_authority` | Official service-status fact. |
| D | `served_in_combat_zone_during_month` | Applies the section 112(c) combat-zone designation and month boundary to service-location facts. |
| D | `vietnam_combat_zone_hospitalization_month_after_january_1978` | Statutory date-boundary comparison. |

### 26 USC 7703(a): four scalar inputs

| Class | Input | Why |
|---|---|---|
| O | `legally_separated_under_decree_of_divorce_or_separate_maintenance` | Decree/status fact. |
| O | `spouse_dies_during_taxable_year` | Vital-record/date fact. |
| O | `taxpayer_married_at_close_of_taxable_year` | Marital-status fact. |
| O | `taxpayer_married_at_time_of_spouse_death` | Marital-status/vital-record fact. |

The conservative count is therefore **34 derived or legally preclassified
scalar inputs + 30 raw or directly recorded scalar inputs + one structural
relation = 65 module-qualified leaves**. Even if AGI is accepted as the task's
explicit bridged dimension bearing no evidence, 33 other derived inputs
remain. Some administrative systems may store a derived status directly, but
that does not make its legal derivation part of this provision graph.

## Dependency and provision-rootedness judgment

The compiled final-output ancestry contains 39 executable RuleSpec nodes: 28
derived rules, 10 parameters, and the structural relation. In the authored
RuleSpec kinds the split is 27 derived rules, 11 parameters, and the relation:
the formula-valued `abode_fraction_threshold` parameter lowers to a compiled
derived node. Its genuine source roots are:

1. **26 USC 32** for the credit, rates, eligibility, earned-income definition,
   and inflation-adjustment delegation;
2. **26 USC 152(c)** for the reached qualifying-child relationship, age,
   joint-return, and tiebreaker rules;
3. **26 USC 7703(a)** for the reached general marital-status rule;
4. **26 USC 112** for the optional combat-pay inclusion in earned income; and
5. **Rev. Proc. 2025-32 section 3.06(1)-(2), pages 14-15** for tax-year-2026
   dollar amounts.

Section 7703's file also imports section 151 for unused section 7703(b) rules.
That is a module-loader side effect, not an ancestor of `eitc`; adding section
151 to the current output-dependency root set on that basis would overstate
the legal graph. Conversely, actually encoding the section 151/152(e), section
164(f)/1402, and other derived frontier leaves would expand the genuine roots
well beyond this minimum.

### Does the revenue procedure count as a provision?

**Substantively, yes—with an explicit taxonomy caveat.** The file is under
`policies/`, but it is not an internal composition. It transcribes official
primary-source IRS guidance; its module verification points to corpus
provisions `us/guidance/irs/rev-proc-2025-32/page-14` and `page-15`; and each
reached parameter cites Rev. Proc. 2025-32 section 3.06(1) or (2). Section
32(j) supplies the statutory inflation-adjustment rule, while the revenue
procedure publishes the operative 2026 values. The corpus classifies the
source as IRS primary guidance, subtype `revenue_procedure`, with an Internal
Revenue Bulletin citation.

That is a real legal-source node and should be declared as a guidance root,
not hidden as a policy composition. However, the module lacks
`proof_validation.required` and rule-level proof atoms. A mechanical predicate
that accepts only `statutes/` and `regulations/` namespaces—or requires
rule-level proofs—will reject it. Certification therefore needs an explicit
decision that citation-bearing primary guidance is provision-equivalent, plus
stronger proof metadata or a more accurate module taxonomy. It must not imply
that arbitrary `policies/` modules qualify.

## Closure universe by citation path

I enumerated `.items[].citation_path` from **every** US corpus inventory record
before filtering the declared roots. No inventory filename selected the
universe.

The result is identical at the repository's toolchain pin
`bf97b17baebfdf12601f7c23697524bf5adcdaed` and cached corpus `origin/main`
`db12795577c5809009168982cf8a72fb58440620`:

| Declared root | Citation paths |
|---|---:|
| 26 USC 32 | 42 |
| 26 USC 152(c) | 5 |
| 26 USC 7703(a) | 3 |
| 26 USC 112 | 17 |
| Rev. Proc. 2025-32 pages 14-15 | 2 |
| **Minimum closure universe** | **69** |

The pin scan covered 689 inventory JSON files and 142,879 records. The cached
`origin/main` scan covered 691 files and 142,902 records. Both produced 69
unique and 69 raw matching paths; the newer corpus records concern a section
1401 repair and do not change EITC.

Exact committed encoding evidence does **not** support saying “69 encoded”:

| Mechanical evidence join | Exact paths evidenced |
|---|---:|
| Proof-citation index keys ∩ 69 paths | 4 |
| RuleSpec file paths ∩ 69 paths | 4 |
| Union of either exact join | **6 / 69** |

The proof-index hits are the roots for sections 32 and 112 plus both revenue
procedure pages. The file-path hits are section 32, section 32(c)(2), section
152(c), and section 112. Their union is six paths. Broad modules plainly
contain rules derived from additional child provisions, but the closure
prototype correctly warns that a section-named file or section-level proof
does not establish content coverage for every descendant. No committed,
reviewed 69-row ledger supplies the honest content-level encoded count.

Section 32's declared deferrals for subsection (f) tables, subsection (l)
cross-program treatment, and expired subsection (n) are not an exhaustive
output-gap inventory. The final amount still bridges unencoded section 32(d),
32(i)(2), and 32(k) legal conclusions, and its age aggregation is disconnected.
Each of the 69 rows still needs an `encoded`, `excluded-with-reason`, or
`pending` adjudication before a closure verdict.

## Reproduction and evidence

- `us/statutes/26/32.yaml`: imports and declared deferrals at lines 1-34;
  child rules at 41-263; amount rules at 265-507; age and eligibility at
  509-706.
- `us/statutes/26/152/c.yaml`: reached qualifying-child rules at lines 78-251.
- `us/statutes/26/32/c/2.yaml`: earned-income rules at lines 12-99.
- `us/statutes/26/112.yaml`: reached combat-pay rule at lines 33-116.
- `us/statutes/26/7703.yaml`: reached marital-status rule at lines 74-103.
- `us/policies/irs/rev-proc-2025-32/earned-income-credit.yaml`: source
  verification at lines 3-11 and parameters at lines 45-130.
- `.axiom/index/provisions_to_rules.json`: exact proof-citation evidence.

The formula ancestry was independently derived from the RuleSpec formulas and
from a compiled section 32 artifact. The existing companion failure was
reproduced with:

```sh
axiom-encode test --root . --json us/statutes/26/32.test.yaml
```

Both amount cases report the removed
`wages_salaries_tips_and_other_employee_compensation_includible_in_gross_income`
input and `self_employment_earned_income_component` output as unknown.

## Certification decision and useful next work

Do not certify this EITC graph today. A transformation-free standalone program
can still expose the provision-defined `eitc` output over the declared
frontier, and a bridged synthetic grid can still diagnose its arithmetic.
Neither artifact cures the 34 derived or legally preclassified inputs or
creates childless-age evidence.

The shortest honest repair path is:

1. connect the existing Person age predicate to the TaxUnit demographic rule;
2. encode section 32(i)(2), section 32(d), and section 32(k) conclusions;
3. replace qualifying-child and earned-income legal composites with reached
   rules, declaring any remaining record facts precisely;
4. repair the stale section 32 companion suite;
5. adjudicate the 69-row closure ledger; and
6. strengthen and formally classify the revenue-procedure parameter module.
