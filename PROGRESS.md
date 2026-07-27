# EITC §152(c) Residency and Parental Tiebreak Progress

## State

- Branch: `closure/w1-eitc-152-residency`, based on `origin/main`.
- Scope: EITC frontier items 4, 8, and 9.
- Status: statutory and dependency discovery complete; implementation design is in progress.
- Worktree note: the mandated external path was rejected by the filesystem sandbox, so this branch is isolated at `.git/codex-worktrees/w1-eitc-152-residency`.
- Corpus pin inspected: `bf97b17baebfdf12601f7c23697524bf5adcdaed`.

## Done

- Read `ENCODER-PREAMBLE.md` and the repository `CLAUDE.md`.
- Confirmed the frozen-program, toolchain, CI, CODEOWNERS, and SNAP exclusions.
- Created the requested branch from `origin/main` and attached it to an isolated worktree.
- Read the assigned frontier rows before implementation and inspected the
  `closure/eitc-2026` program/grid for context.
- Read the required sibling RuleSpec modules and companion tests.
- Resolved every retained inventory record for the governing paths:
  `us/statute/26/32/c/3`, `us/statute/26/152/c/1`, and
  `us/statute/26/152/c/4`.
- Confirmed that § 152(c)(1)(B) requires strictly more than one-half of the
  taxable year; § 32(c)(3)(C) separately requires the EITC abode to be in the
  United States; and § 152(c)(4)(B) selects the parent with the longest
  residence period, then the higher-AGI parent only when residence time is
  equal.
- Confirmed there is no § 1402 dependency. Comparing supplied parental AGI
  facts avoids deriving AGI through the § 61 wall.
- Traced the three current leaf inputs through `us/statutes/26/152/c.yaml`,
  its companion tests, and the importing § 32 module/tests. No other modules
  reference the three names.
- Identified non-statutory day-count details: the retained statutory bodies do
  not themselves define temporary-absence or birth/death normalization, while
  current IRS Publication 501 and Form 8862 instructions do.

## Next

- Finalize the narrowest RuleSpec input surface without relying on unsupported
  nested relation traversal.
- Encode the abode fraction and its strict half-year boundaries, including
  ordinary/leap-year, temporary-absence, and birth/death cases.
- Encode both § 152(c)(4)(B) parental comparisons with strict residence and
  AGI tie behavior.
- Update every affected companion fixture, run focused and broader
  validation, then push and open the requested draft PR if network permits.
