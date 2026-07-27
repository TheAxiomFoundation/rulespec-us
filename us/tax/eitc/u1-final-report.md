# EITC launch follow-up final report

Date: 2026-07-27  
Branch: `closure/eitc-2026`

## Outcome

The no-regret launch path is complete:

- all 34 derived frontier items have a strict, one-row classification;
- the two stale section 32 amount fixtures are repaired;
- both diagnostic residuals are adjudicated to the dollar;
- the RuleSpec half of a 21-case oracle suite is staged and engine-tested;
- the external registry/report contract is transfer-ready; and
- no comparison report, PR, or upstream issue was created.

All task commits were pushed to
`origin/closure/eitc-2026`; no PR was opened.

Canonical deliverables:

- `us/tax/eitc/u1-frontier-classification.md`
- `us/tax/eitc/u1-boundary-adjudication.md`
- `us/tax/eitc/u1-case-grid-registration-prep.md`
- `us/tax/eitc/u1-final-report.md`

The required copy to
`/Users/maxghenis/TheAxiomFoundation/_closure-sprint/out/u1-eitc-frontier.result.md`
was attempted after this report was assembled, but the managed filesystem
returned `Operation not permitted`. This committed file is the canonical
output; a process with access to `_closure-sprint/out` must copy it to the
requested external path.

## Frontier classification

| Bucket | Count |
|---|---:|
| (a) Already computed in-graph | 0 |
| (b) Declarable frontier fact | 11 |
| (c) Must-encode | 23 |
| **Total** | **34** |

No semantic alias is imported and reached for any of the 34 items. Important
near-misses include the disconnected Person age predicate, unimported sections
22 and 62 producers, partial/deferred self-employment rules, and section 7703
marital rules that do not compute the section 32(d) separated-spouse test.

### All 34 bucket assignments

| # | Frontier item | Bucket |
|---:|---|:---:|
| 1 | `adjusted_gross_income` | (b) |
| 2 | `childless_taxpayer_or_spouse_age_eligible_for_eitc` | (c) |
| 3 | `childless_taxpayer_principal_place_of_abode_in_united_states_more_than_half_year` | (b) |
| 4 | `eitc_disallowance_period_applies` | (c) |
| 5 | `eitc_relevant_investment_income` | (c) |
| 6 | `individual_principal_place_of_abode_with_taxpayer_fraction` | (c) |
| 7 | `prior_deficiency_denial_without_required_eligibility_information` | (c) |
| 8 | `qualifying_child_marital_status_requires_section_151_entitlement` | (c) |
| 9 | `satisfies_eitc_separated_spouse_rules` | (b) |
| 10 | `taxpayer_entitled_to_section_151_deduction_for_child_or_would_be_but_for_section_152_e` | (c) |
| 11 | `taxpayer_is_dependent_for_section_151_to_another_taxpayer` | (b) |
| 12 | `taxpayer_is_nonresident_alien_for_any_portion_of_year` | (b) |
| 13 | `taxpayer_is_qualifying_child_of_another_taxpayer` | (b) |
| 14 | `taxpayer_treated_as_resident_by_section_6013_g_or_h_election` | (b) |
| 15 | `child_resided_with_both_parents_same_amount_of_time_and_taxpayer_parent_has_highest_adjusted_gross_income` | (c) |
| 16 | `child_resided_with_taxpayer_parent_for_longest_period` | (c) |
| 17 | `individual_is_permanently_and_totally_disabled` | (b) |
| 18 | `individual_is_student` | (b) |
| 19 | `individual_is_younger_than_taxpayer` | (c) |
| 20 | `individual_may_be_claimed_as_qualifying_child_by_two_or_more_taxpayers` | (c) |
| 21 | `no_parent_of_individual_is_a_claiming_taxpayer` | (c) |
| 22 | `parents_of_individual_may_claim_individual_but_no_parent_claims` | (c) |
| 23 | `taxpayer_adjusted_gross_income_higher_than_highest_parent_adjusted_gross_income` | (c) |
| 24 | `taxpayer_has_highest_adjusted_gross_income_among_claiming_taxpayers` | (c) |
| 25 | `employee_compensation_includible_in_gross_income` | (c) |
| 26 | `net_earnings_from_self_employment_after_self_employment_tax_deduction` | (c) |
| 27 | `nonresident_alien_income_not_connected_with_united_states_business` | (c) |
| 28 | `armed_forces_member_in_missing_status_during_vietnam_conflict_as_result_of_conflict` | (b) |
| 29 | `civilian_employee_in_missing_status_during_vietnam_conflict_as_result_of_conflict` | (c) |
| 30 | `hospitalized_resulting_from_combat_zone_wounds_disease_or_injury` | (c) |
| 31 | `maximum_enlisted_amount_for_commissioned_officer_months` | (c) |
| 32 | `months_beginning_after_combatant_activities_termination` | (c) |
| 33 | `served_in_combat_zone_during_month` | (b) |
| 34 | `vietnam_combat_zone_hospitalization_month_after_january_1978` | (c) |

The 11 bucket-(b) rows have exact Form 1040, Form 1040-NR, Schedule OI,
Schedule EIC, Form 8862, DD Form 1300, or Navy CZTE record fields in the
classification ledger. The strict audit rejected two tempting shortcuts:
Form 8862 does not directly report the section 32(k)(2) prior-denial/compliance
composite, and dependent/release fields do not directly report the complete
section 151-entitlement-or-section-152(e) conclusion.

### Full must-encode list

| Frontier item | Provision and pinned corpus size | Effort |
|---|---|---|
| `childless_taxpayer_or_spouse_age_eligible_for_eitc` | §32(c)(1)(A)(ii)(II); 1 path, `26/32/c/1` | ~0.5 day to aggregate the existing Person predicate across taxpayer/spouse roles and test boundaries. |
| `eitc_disallowance_period_applies` | §32(k)(1); 1 path, `26/32/k/1` | 2-4 hours for two-/ten-year windows from prior final-determination facts. |
| `eitc_relevant_investment_income` | §32(i)(2); 1 path, `26/32/i/2` | 1-2 days to assemble and net the statutory categories. |
| `individual_principal_place_of_abode_with_taxpayer_fraction` | §32(c)(3), §152(c)(1)(B); 2 paths, `26/32/c/3`, `26/152/c/1` | 0.5-1 day for day counts, exceptions, normalization, and tests. |
| `prior_deficiency_denial_without_required_eligibility_information` | §32(k)(2); 1 path, `26/32/k/2` | 0.5-1 day for prior deficiency plus current information-compliance logic. |
| `qualifying_child_marital_status_requires_section_151_entitlement` | §32(c)(3)(B); 1 path, `26/32/c/3` | 2-4 hours for the year-end marital gate and tests. |
| `taxpayer_entitled_to_section_151_deduction_for_child_or_would_be_but_for_section_152_e` | §32(c)(3)(B), §151(c), §152(e); 9 scoped paths | 2-4 days for dependency entitlement, parent release rules, relations, and tests. |
| `child_resided_with_both_parents_same_amount_of_time_and_taxpayer_parent_has_highest_adjusted_gross_income` | §152(c)(4)(B)(ii); 1 path, `26/152/c/4` | 1-3 days, possibly relation-engine work, for residence equality and tie-aware AGI maximum. |
| `child_resided_with_taxpayer_parent_for_longest_period` | §152(c)(4)(B)(i); 1 path, `26/152/c/4` | 1-3 days, possibly relation-engine work, for cross-parent duration comparison. |
| `individual_is_younger_than_taxpayer` | §152(c)(3)(A); 1 path, `26/152/c/3` | ~0.5 day once both ages and roles are available. |
| `individual_may_be_claimed_as_qualifying_child_by_two_or_more_taxpayers` | §152(c)(4)(A); 1 path, `26/152/c/4` | 1-3 days for cross-taxpayer candidates, qualification, and counting. |
| `no_parent_of_individual_is_a_claiming_taxpayer` | §152(c)(4)(A)(ii); 1 path, `26/152/c/4` | 0.5-1 day after parent/claim relations exist. |
| `parents_of_individual_may_claim_individual_but_no_parent_claims` | §152(c)(4)(C); 1 path, `26/152/c/4` | 1-3 days to combine parent eligibility and claim choices. |
| `taxpayer_adjusted_gross_income_higher_than_highest_parent_adjusted_gross_income` | §152(c)(4)(C); 1 path, `26/152/c/4` | 1-3 days, possibly relation-engine work, for strict comparison and ties. |
| `taxpayer_has_highest_adjusted_gross_income_among_claiming_taxpayers` | §152(c)(4)(A)(ii); 1 path, `26/152/c/4` | 1-3 days, possibly relation-engine work, for claimant traversal/ranking. |
| `employee_compensation_includible_in_gross_income` | §32(c)(2)(A)(i) plus §61; 18 paths | 2-4 days for wages, tips, statutory-employee income, and inclusion/exclusion rules. |
| `net_earnings_from_self_employment_after_self_employment_tax_deduction` | §32(c)(2)(A)(ii), §1402(a), §164(f); 22 paths | 5-10 days; deferred §1402(a)'s special rules and cross-references dominate. |
| `nonresident_alien_income_not_connected_with_united_states_business` | §32(c)(2)(B)(iii), §871(a); 1 retained path plus absent §871(a) | 2-4 days after sourcing §871(a) for the covered employee-compensation aggregate. |
| `civilian_employee_in_missing_status_during_vietnam_conflict_as_result_of_conflict` | §112(d)(2)-(3), 5 USC 5561(4)-(5); 2 retained paths plus absent Title 5 dependency | 1.5-2.5 days after sourcing definitions/dates/causation facts. |
| `hospitalized_resulting_from_combat_zone_wounds_disease_or_injury` | §112(a)(2), (b)(2), (c)(2)-(3); 4 paths | 1-2 days for the service/medical event, causation, interval, and tests. |
| `maximum_enlisted_amount_for_commissioned_officer_months` | §112(c)(5) plus Title 37 pay rules; 1 retained path plus absent Title 37 dependencies | 1-2 days after sourcing pay components. |
| `months_beginning_after_combatant_activities_termination` | §112(a)(2), (b)(2), (c)(3); 3 paths | 0.5-1 day after sourcing controlling termination designations. |
| `vietnam_combat_zone_hospitalization_month_after_january_1978` | final sentences of §112(a), (b); 2 paths | Less than 0.5 day after hospitalization dates are available. |

## Companion fixture

The original failure was reproduced before editing: two amount cases each
failed on the removed section 32(c)(2) wage input and removed
`self_employment_earned_income_component` output.

The repair mapped the five legacy component names to the live names, supplied
the live net-self-employment input as zero, removed obsolete section
1402/164/1401 chain inputs, and removed only the nonexistent intermediate
assertion. Every existing final amount expectation stayed unchanged.

Result on the repository-pinned `axiom-encode` 0.2.1200 source
(`3869d66d009f52258be35901edbef370e65a399c`) and rules engine
`ffd8213271947b0189a9dd61a055c1e0e78908a0`:

- immediately after the mechanical repair: **4/4 passed**;
- after staging the 21 grid-contract cases: **25/25 passed**, one compiled
  program, zero failures.

## Boundary adjudications

Both residuals are section 32(f) table/published-dollar boundary effects that
expose a PolicyEngine amount defect. Rev. Proc. 2025-32 section 4.06(1) says
the maximum is allowed “at or above” the separately published earned-income
amount.

| Case | Statutory rate product | Published endpoint | Correct | Axiom | PolicyEngine |
|---|---:|---:|---:|---:|---:|
| One child at $13,020 | $13,020 × 34% = **$4,426.80** | $13,020 / **$4,427** maximum | **$4,427** | $4,427 | $4,426.7998046875 |
| Three children at $18,290 | $18,290 × 45% = **$8,230.50** | $18,290 / **$8,231** maximum | **$8,231** | $8,231 | $8,230.50 |

Axiom is numerically right on both rows because it switches to the published
maximum at the published threshold. PolicyEngine's cached upstream formula
uses `min_(maximum, earnings * phase_in_rate)` and therefore misses the
independently rounded maximum by $0.20 and $0.50 at the exact endpoints.
Do not widen tolerance.

The audit also found and corrected a separate Axiom metadata defect: seven
parameter `source` labels said Rev. Proc. section 3.06 instead of the official
section 4.06. The corresponding applied-file manifest hash was refreshed; no
value changed. The full section 32(f) table remains deferred, so this is not a
broader validation of Axiom's continuous calculation.

`u1-boundary-adjudication.md` contains a schema-ready comparison disposition
and complete draft PolicyEngine issue. The valid oracle disposition is
`upstream_engine_gap`; no issue was filed.

## Suite registration

Staged here:

- all 21 exact case IDs and expected EITC values in the section 32 companion;
- a transfer-ready `comparisons/us-eitc-grid.yaml` manifest template;
- the required `_EITC_CASES`, PolicyEngine situation, strict fixture
  validator, `PolicyConfig`, and test contract;
- the raw v2 / dispositioned v2.1 report shapes;
- two schema-validated, source-pinned `upstream_engine_gap` disposition
  entries; and
- the exact provenance contract:
  `population: case-grid`, `run_kind: manual`, no dataset block, canonical
  rulespec SHA, and pinned PolicyEngine package versions.

Still required in the separate `axiom-oracles` repository:

1. merge this fixture to canonical `rulespec-us` main and resolve its exact
   commit/tree;
2. fill `rulespec_upstream_sha` and `rulespec_upstream_tree` with that main
   revision (never this feature-branch SHA);
3. add the manifest, generator situation/validator/config, tests, and two
   dispositions;
4. generate `comparisons/affected_map.json`;
5. run the pinned PolicyEngine 1.767.3 stack and confirm the two live pins;
6. after the launch freeze, generate/publish the 21-case report and dashboard
   manifest/freshness/overview artifacts.

The current EITC conformance row must remain on `fiit-ecps`: the childless-age
bridge and other frontier facts prevent this synthetic grid from serving as a
replacement provision certificate.

## Validation

```text
env PYTHONPATH=/private/tmp/eitc-u1-toolchain.FGxJtx/axiom-encode/src \
  /Users/maxghenis/TheAxiomFoundation/_bulk_drain/.venv/bin/python \
  -m axiom_encode.cli test --root . \
  --axiom-rules-engine-path \
  /private/tmp/axiom-rules-engine-ffd8213-target/release \
  --json us/statutes/26/32.test.yaml

success=true; cases=25; compiled_programs=1; failures=[]
```

```text
/Users/maxghenis/TheAxiomFoundation/_bulk_drain/.venv/bin/python -m pytest -q

73 passed, 1 existing unmanifested-module warning
```

Additional mechanical checks confirmed 34 unique classification rows matching
the m1 inventory, counts of 0/11/23, 21 unique grid IDs with the exact EITC
output, valid YAML templates, a valid current disposition schema, no stale
section 3.06 labels, and no generated comparison/dashboard/conformance files.
