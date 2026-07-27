# Progress

## State

In progress on branch `closure/w3-eitc-32-eligibility` from `origin/main`.
Assigned EITC frontier items: 1, 2, 5, 6, and 7.

## Done

- Read the closure-sprint encoder preamble and root `CLAUDE.md`.
- Created an isolated worktree. The requested sibling-directory path was
  blocked by the filesystem sandbox, so the worktree lives at
  `.git/codex-worktrees/w3-eitc-32-eligibility`.
- Read the five assigned frontier rows, the EITC program/grid context, the
  required sibling encodings, and the governing corpus records resolved by
  exact `citation_path` across every inventory record.
- Encoded the section 32(c)(1)(A)(ii)(II) taxpayer-or-spouse childless-age
  aggregate over the existing Person age predicate.
- Added six aggregate tests covering ages 24, 25, 64, and 65 plus both
  either-spouse branches, and migrated the importing section 24(d) fixtures.
- Encoded the section 32(k)(1) ten-year fraud and two-year
  reckless-or-intentional-disregard windows, including the excluded
  determination year and inclusive last years.
- Encoded the section 32(k)(2) indefinite prior-deficiency gate and its
  current-claim required-information exception.
- Added ten disallowance-window cases and three prior-deficiency cases, and
  migrated all affected section 32 and section 24(d) fixtures.
- Encoded the section 32(c)(3)(B) year-end marital-status gate and exercised
  the unmarried, married-without-entitlement, and married-with-entitlement
  branches.
- Declared the composite section 151 entitlement / but-for-section-152(e)
  output deferred: section 151 exports no per-child entitlement result, while
  the section 152 parent and its subsection (e) adjusted bases are
  entity/schema unsupported.

## Next

- Run final targeted, proof, schema, and repository validation.
- Record final validation in this ledger, push, and open the requested draft
  PR.
