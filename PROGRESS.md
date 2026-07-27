# EITC closure sprint progress

## State

- Assessment and standalone program complete on branch `closure/eitc-2026`.
- The checkout is clean and based on the locally cached `origin/main` at
  `f9fb41b99`; DNS prevented refreshing the remote on 2026-07-27.
- No SNAP program or committed oracle artifact will be modified.
- The current EITC graph is not honestly certifiable: 23 of its 64 scalar
  frontier occurrences are derived legal quantities, and no reviewed
  69-citation-path content ledger exists.

## Done

- Read the closure-sprint encoder preamble and repository instructions.
- Loaded the PolicyEngine and PolicyEngine-US guidance required for the
  household-level EITC comparison.
- Preserved the prior payroll branch and started this work on a fresh branch.
- Traced the final `eitc` formula to 65 module-qualified frontier leaves and
  classified every leaf as observed/preclassified or derived.
- Audited the reached rule sources and classified Rev. Proc. 2025-32 as a
  genuine primary-guidance node, subject to a formal taxonomy/proof caveat.
- Counted the minimum closure universe across every corpus inventory record:
  69 citation paths at both the pinned and cached newer corpus revisions.
- Reproduced the stale section 32 companion failures.
- Wrote the assessment before making any program change.
- Added `programs/us/tax/eitc/fy-2026.yaml` with the single output `eitc`,
  statutory section 32 as its only scope root, and no transformations.
- Composed the new spec with the pinned composer and compiled the result with
  the pinned engine commit. The compiled artifact exposes 61 derived rules.
- Added and engine-checked a hand-worked one-child golden case: $28,890 of
  earned income and AGI yields a $799 phaseout and a $3,628 credit.

## Next

- Document and, if it can be done honestly within the permitted repositories,
  run a non-population diagnostic grid without changing oracle reports or
  hiding the non-AGI bridges.
- Validate, independently review, and write the final handoff report.
