# Federal credit compose progress

## State

Defensive correctness-and-completeness audit in progress on
`fed-parity/credits`, based on `origin/main` commit
`c86b2f62511b7ff9d5351c98ca03b87e3cc41042`.

The section 199A pipeline and companion are complete and independently
validated. The audit found that the encoded source's final deduction closes
over an unindexed $157,500 threshold, so the pipeline uses the locally proofed
ACA-style correction pattern and a Revenue Procedure 2025-32 runtime
threshold instead of presenting an incorrect thin identity.

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

## Next

1. Add and commit the corrective saver’s-credit compose and P6 fixtures.
2. Add and commit thin-identity section 22 and section 25A(c) composes with
   P7/P8 fixtures.
3. Regenerate shared index/coverage artifacts and commit them separately.
4. Run the complete validation/signing-dry-run gate battery.
5. Write the required scratchpad summary and completion marker.
