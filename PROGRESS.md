# Federal credit compose progress

## State

Defensive correctness-and-completeness audit complete on
`fed-parity/credits`, based on `origin/main` commit
`c86b2f62511b7ff9d5351c98ca03b87e3cc41042`.

All four requested pipelines and companions are complete and independently
validated. Shared reverse-index and oracle-pending artifacts have been
regenerated with the workflow-current classifier. The only remaining
pre-integration action is intentional: a signing-key holder must generate the
four manual-composition manifests.

## Done

- Confirmed the worktree and branch are clean and correctly scoped.
- Confirmed the deliverables are four proofed RuleSpec policy modules with
  sibling companion fixtures, not ProgramSpecs.
- Read the Ohio pilot compose and the cached federal thin-identity and
  locally-authored-leg precedents.
- Audited all four encoded statute modules and the 2026 inflation parameter
  inventory.
- Recorded the current-law section 199A thresholds ($201,750 all other,
  $201,775 MFS, and $403,500 joint) and current $75,000/$150,000 phase-in
  widths from Revenue Procedure 2025-32.
- Added the proofed `qualified_business_income_deduction_pipeline` and 11
  hand-computed fixtures, including all P5 cases, exact-threshold, active-QBI
  minimum, zero, and net-capital-gain-limit checks.
- Passed that module's `validate --skip-reviewers`, proof validation,
  money-proof ratchet, and pinned-engine companion suite.
- Regenerated and checked `.axiom/index/provisions_to_rules.json`: 3,946
  provisions, 4,674 edges, and 4,437 modules.
- Synchronized `oracle-coverage-pending.yaml` with the current classifier in a
  canonical `rulespec-us` snapshot. It added exactly 16 outputs from these
  composes, drained 14 already-mapped legacy declarations, and passed with
  1,743 declared/applied and zero stale.
- Added the thin `lifetime_learning_credit_pipeline` and 12 hand-computed
  fixtures covering all P8 cases, zero and both phaseout edges, the aggregate
  expense cap, and a binding-tax diagnostic.
- Confirmed the encoded 2026 MAGI ranges are the fixed $80,000-$90,000
  nonjoint and $160,000-$180,000 joint ranges. Grid cases supply $10,000 of
  pre-credit tax and zero preceding credits, so the encoded tax cap does not
  bind.
- Passed that module's `validate --skip-reviewers`, proof validation,
  money-proof ratchet, and pinned-engine companion suite.
- Added the thin `elderly_disabled_credit_pipeline` and 10 hand-computed
  fixtures covering all P7 cases, the executable under-65 disability branch,
  a no-qualified-person zero, and exact AGI-reduction edges.
- Verified that joint returns with one qualified spouse use the $5,000 initial
  amount and that `eld-basic` is $412.50 because its AGI adds a $250 reduction
  omitted from the grid's abbreviated shape.
- Passed that module's `validate --skip-reviewers`, proof validation,
  money-proof ratchet, and pinned-engine companion suite.
- Recorded the official 2026 saver’s-credit tier limits from IRS Notice
  2025-67: joint $48,500/$52,500/$80,500, head of household
  $36,375/$39,375/$60,375, and other returns
  $24,250/$26,250/$40,250.
- Added the proofed `savers_credit_pipeline`, with separate primary/spouse
  eligibility and contribution-cap legs, and 12 hand-computed fixtures
  covering all P6 cases, tier edges, zero contributions, and each eligibility
  screen.
- Passed that module's `validate --skip-reviewers`, proof validation,
  money-proof ratchet, and pinned-engine companion suite.
- Passed the combined final battery: 4/4 deterministic validation, 38 proof
  atoms, zero new missing money atoms, and 45/45 pinned-engine companion
  cases.
- Passed repository pytest: 55 tests, with only the expected unsigned-module
  and temporary-directory cleanup warnings.
- Passed a fresh-snapshot oracle check: 1,743 declared, 1,743 applied, and
  zero stale.
- Passed source staleness: all 43 pinned modules match the current corpus.
- Passed the canonical-basename Program Artifact check: 32/32 programs
  composed and engine-compiled with the pinned composer and rules engine.
- The signer dry run selected exactly four manifests for the eight intended
  pipeline/companion files. No signing was attempted or fabricated.
- Confirmed `guard-generated` now fails only for those same eight unsigned
  files, which is the expected handoff block.

## Next

1. A key holder runs `axiom-encode sign-applied-files` with the
   `composition` manual exception and commits the four generated manifests.
2. Rerun `guard-generated`; it must pass before integration.
