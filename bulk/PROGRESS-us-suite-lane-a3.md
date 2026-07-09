# US suite lane A3 — composed DE/MD/ME/MN/CT income-tax liability pipelines

Continues lane A/A2 (OH pilot; AL/ID/KY shipped). Composes the five teed-up
states into `us-XX/policies/income_tax/pilot_liability_pipeline` + per-case suite
vs pinned PolicyEngine-US (penny-exact) and TAXSIM-2024 in axiom-oracles.

Branches (from origin/main): rulespec-us `lane-a3-suite-20260709`,
axiom-oracles `lane-a3-oracles-20260709`. Sibling worktree layout under
`_axiom-worktrees/lane-a-suite-20260708/{rulespec-us,axiom-oracles}` so the oracle
generator's `REPO_ROOT.parent/"rulespec-us"` resolves.

## Pipeline shape (all five)

Multi-bracket generalization of the OH/AL two-tier form — per case supply the
cumulative base tax at the bracket floor, the floor, and the bracket marginal
rate (progress-note "cumulative base + marginal, like OH"):
- `xx_pit_pilot_taxable_income = max(0, AGI - supplied_standard_deduction)`
- `xx_pit_pilot_schedule_tax = supplied_bracket_base + supplied_marginal_rate * max(0, taxable - supplied_bracket_floor)`
- `xx_pit_pilot_income_tax_liability = max(0, schedule_tax - supplied_nonrefundable_credit)`

Inputs: AGI, standard_deduction, bracket_floor, bracket_base, marginal_rate,
nonrefundable_credit (all per-case supplied indexed/current authority).

## Per-state (PE 2026 `_before_refundable_credits`, all penny-exact)

- **DE** §1102 (fixed brackets); credit = §1110 personal credit 110/220.
  single 988.125/2653.125/8559; married 2362.75/6254.5/18134.5.
- **MD** §10-105 STATE only (county tax = separate PE var, excluded); credit 0.
  single 1059/2484/7039.5; married 2168.125/5018.125/14695.75.
- **ME** §5111 (indexed); credit 0. single 565.5/2428.52/9483.72;
  married 1131/4857.05/18966.73. Rate §5111 + std-ded §5124-C landed via the L–N
  batch (composability re-verified post-train; ME note resolved, no #757 ledger).
- **MN** §290.06 subd. 2c (indexed); credit 0 except married-300k, where the
  supplied credit is the negative §290.091 AMT (mn_amt=182.58, binds above the
  regular tax). single 789.125/2560.00/8946.08; married 1575.57/5376.45/18727.88.
- **CT** §12-700 (resident schedule deferred on main → supplied); credit = net
  §12-703 personal credit / §12-700(b) 3% phase-out recapture (negative where
  recapture dominates: -475 / -200 / -950). single 361.25/2317.5/8225;
  married 1494/5300/16450.

## Status

- [x] Phase 1 rulespec-us: 5 pipelines authored, `axiom-encode test` 30/30 cent-
  exact, signed (`--manual-exception composition`), reverse index + pending sync
  (ceiling 531→537, dup key fixed). Commit f4d4b25b. PR: pending.
- [ ] Phase 2 axiom-oracles: generator (`_TAXSIM_STATE`/`_PE_VAR`/`_TOL` DE=8 MD=21
  ME=20 MN=24 CT=7), comparisons+dispositions (TAXSIM-2024 vintage; MD also the
  siitax county-tax scope gap), concept_mappings append-only, us-pe.yaml suite
  rows, test_conformance live_pe_suites +5, scoreboard/affected/vacuous regen.

## Notes

- AL/ID/KY oracle registration merged (or#254) but rulespec pilots unmerged
  (rus#773 BLOCKED); for the phase-2 generator run, AL/ID/KY `.test.yaml` are
  copied UNTRACKED into the rulespec-us worktree (documented UT/VA workaround
  pattern) so `_axiom_liabilities()` completes. UT/VA now on rulespec-us main.
