# Progress — §32(i) investment income disqualification

## State

Ready for review. The full §32(i)(2) disqualified-income aggregate is
explicitly deferred on upstream-law walls. The independently supported
§32(i)(1) threshold rule is verified against its exact corpus path and tested
at the 2026 equality and first-disqualifying boundaries.

The requested external worktree path was not writable in the execution
sandbox. The branch is attached instead beneath the repository at
`.worktrees/w4-eitc-32i-invest`.

## Done

- Read the closure-sprint encoder preamble.
- Read the repository agent notes in `CLAUDE.md`.
- Created the required topic branch and an isolated worktree.
- Read the frontier-classification row for
  `eitc_relevant_investment_income`.
- Resolved the governing provisions by `citation_path` across the pinned
  `axiom-corpus` inventory and read their bodies.
- Confirmed that §1222 capital gain net income is encoded, but the aggregate
  still depends on:
  - category-specific §61 inclusion and exclusion mechanics for interest,
    dividends, rents, and royalties;
  - §469 passive-activity classification, which is absent from the pinned
    corpus and has no RuleSpec module; and
  - the §32(c)(2) overlap exclusion, whose self-employment branch reaches the
    expressly deferred §1402(a) net-earnings output.
- Confirmed that §32(i)(1) disqualifies only when the aggregate strictly
  exceeds the inflation-adjusted threshold; equality remains eligible.
- Inspected the `closure/eitc-2026` program and diagnostic grid without
  modifying the frozen program.
- Added a `deferred_outputs` entry for
  `us:statutes/26/32/i/2#eitc_relevant_investment_income` naming the exact
  §61, §469, and §1402(a) blockers.
- Added `us/statute/26/32/i/1` and `us/statute/26/32/i/2` to the module's
  verified corpus sources and regenerated the reverse citation index.
- Added threshold cases proving that $12,200 remains eligible and $12,201 is
  ineligible for tax year 2026.
- Mechanically refreshed the two pre-existing comprehensive fixtures to the
  current §32(c)(2) input contract and added the missing positive
  qualifying-child Judgment case required by the repository validator.
- Refreshed the section 32 encoding-manifest hashes.
- Passed focused RuleSpec execution: 1 file, 7 cases.
- Passed focused RuleSpec CI validation and proof validation (42 atoms).
- Passed the full repository test suite: 65 tests, with one non-failing
  manifest-sync warning.
- Confirmed the reverse index is current: 4,241 provisions, 5,080 edges, and
  4,486 modules.

## Next

- Push `closure/w4-eitc-32i-invest`.
- Open the required draft pull request referencing `rulespec-us#1135`.
- Human review should preserve the §32(i)(2) deferral until the category-
  specific §61 inclusion/exclusion surface, §469 passive-activity definition,
  and §1402(a) net-earnings output are encoded.
