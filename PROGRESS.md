# EITC closure sprint progress

## State

- Assessment, standalone program, diagnostic comparison, and final report are
  complete on branch `closure/eitc-2026`.
- The checkout is clean and based on the locally cached `origin/main` at
  `f9fb41b99`; DNS prevented refreshing the remote on 2026-07-27.
- No SNAP program or committed oracle artifact will be modified.
- The current EITC graph is not honestly certifiable: 34 of its 64 scalar
  frontier inputs are derived or legally preclassified quantities, and no
  reviewed 69-citation-path content ledger exists.

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
- Added an Axiom- and PolicyEngine-checked two-child golden case: $28,890 of
  earned income and AGI yields a $1,053 phaseout and a $6,263 credit, with no
  rounding ambiguity.
- Ran a 21-case synthetic, non-population Axiom/PolicyEngine diagnostic grid:
  19 amounts matched and two published earned-income-amount boundaries
  differed. The age rows require an extra unrooted Axiom flag and therefore
  are not end-to-end evidence.
- Kept the established oracle repository and every committed report and
  numeric artifact untouched. A certifying grid did not land because the age
  dataflow and stale section 32 fixture must be repaired first.
- Incorporated independent-review corrections to the conservative frontier
  classification, runtime ancestry counts, closure wording, and golden case.
- Ran the full repository test suite: 73 passed with one existing warning.
- Wrote the final handoff report in the repository. The requested external
  assessment and result paths are not writable in this sandbox.
- Pushed the committed branch to `origin/closure/eitc-2026`.
- GitHub's API hostname remained unreachable and no signed-in browser was
  available, so a draft PR could not be opened from this environment.

## Next

- Open a draft PR from the pushed branch when GitHub API access is available,
  then review the assessment and program without treating either as a
  certificate.
