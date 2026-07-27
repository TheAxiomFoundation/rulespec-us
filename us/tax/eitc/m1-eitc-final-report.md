# EITC closure sprint final report

Date: 2026-07-27  
Branch: `closure/eitc-2026`  
Base: cached `origin/main@f9fb41b9933111ce108cc04d5a603cfdb7f1b940`

## Decision

**Do not certify the current EITC graph today.**

The transformation-free program composes and executes the `eitc` node defined
by 26 USC 32. Its reached rules generally trace to genuine legal-source
modules. But the final graph still consumes 34 derived or legally
preclassified inputs that it does not compute. The clearest failure is that
the encoded Person age predicate is disconnected from the final TaxUnit
credit. The existing section 32 companion fixture is also stale, and no
reviewed 69-row closure ledger establishes content coverage.

## Declared frontier

The final `eitc` ancestry consumes 64 distinct module-qualified scalar input
IDs and one structural relation. `D` below means the value requires an
aggregation, comparison, statutory classification, or legal conclusion not
computed by this graph. `O` means a raw or directly recorded fact. The
assessment gives a reason for every classification.

### Derived or legally preclassified inputs: 34

- **26 USC 32 (14):** `adjusted_gross_income`,
  `childless_taxpayer_or_spouse_age_eligible_for_eitc`,
  `childless_taxpayer_principal_place_of_abode_in_united_states_more_than_half_year`,
  `eitc_disallowance_period_applies`, `eitc_relevant_investment_income`,
  `individual_principal_place_of_abode_with_taxpayer_fraction`,
  `prior_deficiency_denial_without_required_eligibility_information`,
  `qualifying_child_marital_status_requires_section_151_entitlement`,
  `satisfies_eitc_separated_spouse_rules`,
  `taxpayer_entitled_to_section_151_deduction_for_child_or_would_be_but_for_section_152_e`,
  `taxpayer_is_dependent_for_section_151_to_another_taxpayer`,
  `taxpayer_is_nonresident_alien_for_any_portion_of_year`,
  `taxpayer_is_qualifying_child_of_another_taxpayer`, and
  `taxpayer_treated_as_resident_by_section_6013_g_or_h_election`.
- **26 USC 152(c) (10):**
  `child_resided_with_both_parents_same_amount_of_time_and_taxpayer_parent_has_highest_adjusted_gross_income`,
  `child_resided_with_taxpayer_parent_for_longest_period`,
  `individual_is_permanently_and_totally_disabled`,
  `individual_is_student`, `individual_is_younger_than_taxpayer`,
  `individual_may_be_claimed_as_qualifying_child_by_two_or_more_taxpayers`,
  `no_parent_of_individual_is_a_claiming_taxpayer`,
  `parents_of_individual_may_claim_individual_but_no_parent_claims`,
  `taxpayer_adjusted_gross_income_higher_than_highest_parent_adjusted_gross_income`,
  and `taxpayer_has_highest_adjusted_gross_income_among_claiming_taxpayers`.
- **26 USC 32(c)(2) (3):**
  `employee_compensation_includible_in_gross_income`,
  `net_earnings_from_self_employment_after_self_employment_tax_deduction`,
  and `nonresident_alien_income_not_connected_with_united_states_business`.
- **26 USC 112 (7):**
  `armed_forces_member_in_missing_status_during_vietnam_conflict_as_result_of_conflict`,
  `civilian_employee_in_missing_status_during_vietnam_conflict_as_result_of_conflict`,
  `hospitalized_resulting_from_combat_zone_wounds_disease_or_injury`,
  `maximum_enlisted_amount_for_commissioned_officer_months`,
  `months_beginning_after_combatant_activities_termination`,
  `served_in_combat_zone_during_month`, and
  `vietnam_combat_zone_hospitalization_month_after_january_1978`.

### Raw or directly recorded scalar facts: 30

- **26 USC 32 (8):** `filing_status`,
  `qualifying_child_name_age_and_tin_included_on_return`,
  `qualifying_child_principal_place_of_abode_is_in_united_states`,
  `spouse_includes_required_social_security_number_on_return`,
  `taxable_year_closed_by_reason_of_taxpayer_death`,
  `taxable_year_is_full_12_months`, `taxpayer_claims_section_911_benefits`,
  and `taxpayer_includes_required_social_security_number_on_return`.
- **26 USC 152(c) (7):** `filing_status`,
  `individual_age_at_close_of_calendar_year`,
  `individual_is_child_of_taxpayer_or_descendant_of_such_child`,
  `individual_is_sibling_stepsibling_or_descendant_of_such_relative`,
  `parents_filing_status`, `return_filed_only_for_claim_of_refund`, and
  `taxpayer_is_parent_of_individual`.
- **26 USC 32(c)(2) (4):** `penal_institution_service_compensation`,
  `pension_or_annuity_amount`,
  `subsidized_state_work_activity_service_compensation`, and
  `taxpayer_elects_to_treat_section_112_excluded_amounts_as_earned_income`.
- **26 USC 112 (7):**
  `active_service_compensation_as_commissioned_officer_excluding_pensions_and_retirement_pay`,
  `active_service_compensation_as_enlisted_member_excluding_pensions_and_retirement_pay`,
  `armed_forces_missing_status_active_service_compensation`,
  `civilian_employee_missing_status_active_service_compensation`,
  `commissioned_officer_in_armed_forces_excluding_commissioned_warrant_officer`,
  `member_below_grade_of_commissioned_officer_in_armed_forces`, and
  `officially_absent_from_post_of_duty_without_authority`.
- **26 USC 7703(a) (4):**
  `legally_separated_under_decree_of_divorce_or_separate_maintenance`,
  `spouse_dies_during_taxable_year`,
  `taxpayer_married_at_close_of_taxable_year`, and
  `taxpayer_married_at_time_of_spouse_death`.

The structural frontier relation is
`us:statutes/26/32#relation.qualifying_child_of_tax_unit`. Even after accepting
AGI as an explicit evidence-free bridge, 33 derived inputs remain.

## Provision roots and closure

The genuine minimum semantic roots are 26 USC 32, 26 USC 152(c), 26 USC
7703(a), 26 USC 112, and Rev. Proc. 2025-32 section 3.06(1)-(2), pages 14-15.
The unused section 151 import reached through the broader section 7703 module
is a loader side effect, not a final-output dependency.

The revenue procedure counts substantively as a provision-equivalent guidance
node: it is official primary IRS guidance with an Internal Revenue Bulletin
citation, corpus pages, and section-level citations for the 2026 values. It is
not an internal policy composition. The caveat is formal but important: its
module lives under `policies/` and lacks required rule-level proof atoms, so a
mechanical statute/regulation-only predicate will reject it. Certification
needs an explicit primary-guidance taxonomy decision and stronger proofs.

I extracted `citation_path` from every inventory record before filtering
roots. The minimum universe is identical at the pinned corpus commit
`bf97b17baebfdf12601f7c23697524bf5adcdaed` and cached `origin/main`:

| Root | Citation paths |
|---|---:|
| 26 USC 32 | 42 |
| 26 USC 152(c) | 5 |
| 26 USC 7703(a) | 3 |
| 26 USC 112 | 17 |
| Rev. Proc. 2025-32 pages 14-15 | 2 |
| **Total** | **69** |

Only **6 of 69** paths mechanically join to either an exact proof-citation key
or an exact RuleSpec file path. That is not an encoded-content count.
The actual number encoded within broader section modules is unknown because no
reviewed 69-row content ledger exists; a closure claim cannot honestly count
the other 63 as encoded.

## Artifacts built

- `PROGRESS.md`: committed state/done/next ledger maintained from the start.
- `us/tax/eitc/m1-eitc-assessment.md`: exhaustive frontier, source judgment,
  closure census, and certification decision.
- `programs/us/tax/eitc/fy-2026.yaml`: one output (`eitc`), one declared root
  (`statutes/26/32`), and no `transformations:` block.
- `us/tax/eitc/m1-eitc-golden-case.md`: two-child exact derivation:
  `$7,316 − (21.06% × $5,000) = $6,263`. Both engines returned $6,263.
- `us/tax/eitc/m1-eitc-diagnostic-grid.md`: 21 aligned, synthetic,
  non-population Axiom/PolicyEngine cases with all bridges disclosed.

No executable or registered `case-grid` suite landed. Calling the Markdown
diagnostic a certifying suite would be misleading: its age cases need the
unrooted TaxUnit age-eligibility flag, the section 32 fixture is stale, and the
established runner lives in the separate read-only `axiom-oracles` checkout
and reads fixture values rather than executing this program.

## Diagnostic comparison

Both engines received identical earned income and AGI. Axiom assembled earned
income from employee compensation with all other section 32(c)(2) components
zero; PolicyEngine received the same `eitc_earned_income` override. Investment
income and every eligibility bridge were explicit.

Nineteen of 21 amounts matched exactly. Two published earned-income-amount
boundaries differed:

- one child at $13,020: Axiom $4,427; PolicyEngine $4,426.7998046875;
- three children at $18,290: Axiom $8,231; PolicyEngine $8,230.50.

Axiom switches to the published maximum at the earned-income amount.
PolicyEngine calculates `min(maximum, earned_income × phase_in_rate)`. Both
differences exceed $0.01 and remain visible. The 24/25/64/65 age rows matched
numerically, but are diagnostic only because the final Axiom credit does not
consume its own Person age predicate.

## Validation

- Pinned composer
  `fabe0b3b3fd6e90d3e8f075516f9b668f524f711` emitted a composition importing
  only `us:statutes/26/32`, with zero transformations.
- Pinned rules engine
  `ffd8213271947b0189a9dd61a055c1e0e78908a0` compiled the program:
  artifact format 2, engine 0.1.0, 61 compiled derived outputs.
- Pinned `axiom-encode` 0.2.1200 ran the existing
  `us/statutes/26/32.test.yaml`: four cases loaded, one program compiled, and
  the two amount cases each reported the stale wage input and removed
  `self_employment_earned_income_component` output. This is a finding, not a
  bypassed check.
- `pytest -q`: **73 passed**, one existing unmanifested-module warning, in
  102.90 seconds.
- The aligned Axiom request executed in explain mode with 1,563 explicit
  inputs, 30 child relations, and 42 queries; no population data was used.
- PolicyEngine used the read-only local source at
  `715373c90b0014561977a1b161f2f4c75bb45c33`, package 1.779.4, core 3.30.2.
- An independent review found and prompted correction of the initial
  frontier-classification and golden-rounding errors.
- The final diff changes no SNAP, committed oracle, toolchain, CI, workflow,
  CODEOWNERS, or other forbidden file.

## Remaining work

1. Connect the Person age rule to the final TaxUnit demographic rule through a
   provision-defined taxpayer/spouse relation and aggregation.
2. Encode section 32(i)(2), 32(d), 32(k), the earned-income components, and the
   other legal frontier composites.
3. Repair and engine-verify the stale section 32 companion fixture without
   changing its committed expected numeric values.
4. Adjudicate all 69 citation paths in a reviewed closure ledger.
5. Formalize primary-guidance provision status and add rule-level proofs to
   the revenue-procedure module.
6. Decide the two exact-threshold model discrepancies rather than widening
   tolerance.
7. After those repairs, add the executable `us-eitc-grid` integration in
   `axiom-oracles`, rerun only the permitted case grid, and regenerate reports
   through the normal runner.

## Delivery status

The requested copy to
`~/TheAxiomFoundation/_closure-sprint/out/m1-eitc-assessment.md` failed with
`Operation not permitted` because that output directory is outside this
task's writable sandbox. The committed assessment above is the canonical
artifact. Push and draft-PR status will be recorded in a final delivery
commit.
