# EITC §152(c) Residency and Parental Tiebreak Progress

## State

- Branch: `closure/w1-eitc-152-residency`, based on `origin/main`.
- Scope: EITC frontier items 4, 8, and 9.
- Status: all three assigned outputs are encoded; clean-checkout validation is in progress.
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
- Encoded `individual_principal_place_of_abode_with_taxpayer_fraction` from a
  validated administrative abode-day count and taxable-year day count. Invalid
  negative, over-year, or zero-denominator inputs fail closed.
- Replaced the former fraction leaf in the § 152(c) and § 32 fixtures and added
  eight focused cases covering ordinary-year and leap-year half boundaries,
  full-year normalization, and invalid counts.
- Added the new § 152(c) proof import to § 32, cascaded § 152 module hashes,
  refreshed authoritative manifests, and regenerated the provision index.
- Validation at this checkpoint:
  - § 152(c) companion: 24/24 passed.
  - § 152(c) proof validation: 18 atoms passed.
  - § 32 proof validation: 43 atoms passed.
  - Manifest and reverse-index tests: 9 passed.
  - The untouched baseline and this branch both expose the same pre-existing
    § 32 companion resolution failures for § 32(c)(2).
- Encoded both § 152(c)(4)(B) outputs as pairwise comparisons of the two
  claiming parents' supplied residence-day counts. Invalid day counts fail
  closed; the longest-period comparison is strict.
- Encoded the equal-residence branch using supplied filed parental AGIs and a
  strict greater-than comparison. Negative AGIs retain numeric ordering and
  an exact AGI tie produces no unique winner.
- Added ten focused parental cases, including both positive downstream
  tiebreak paths, unequal residence despite higher AGI, equal/lower/tied AGI,
  negative AGIs, and invalid residence counts.
- Kept the parent facts scalar because the current companion runner cannot
  attach a child-to-parent relation inside § 32's tax-unit-to-child relation;
  the scalar pair is also faithful to paragraph (B)'s “both parents” scope.
- A clean-checkout `validate --skip-reviewers` run flagged the fraction proof
  excerpt because its “taxpayer” and “taxable year” wording triggered the
  validator's TaxUnit heuristic. Kept the citation exact at
  `us/statute/26/152/c/1` while omitting the misleading inline excerpt; the
  module summary retains the full statutory text.
- Confirmed on untouched `origin/main` that § 32's separate missing-positive-
  coverage warning for `eitc_qualifying_child` predates this branch.

## Next

- Rerun the clean-checkout module validator after the proof-scope repair and
  run the relevant repository regression checks.
- Write the final report, push, and open the requested draft PR if network
  access permits.
