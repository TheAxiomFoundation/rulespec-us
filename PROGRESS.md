# Progress

## State

Design complete for eight subsection-granular 7 CFR 273.1
household-composition modules. Implementation will proceed in three coherent
commits: core general/minor formation, special separate/boarder treatment, and
remaining boundary/ineligible-member treatment.

## Done

- Read `CLAUDE.md`.
- Read the full source row for `us/regulation/7/273/1`.
- Read the 7 CFR 273.9, 273.10, and 273.2(j) sibling modules and tests.
- Confirmed the worktree starts at `origin/main` commit `1158ba5b2`.
- Inspected the RuleSpec schema, exact pinned validator, federal composition
  relations, and Colorado household-concept precedents.
- Chose modules at `273/1/a` and `273/1/b/1` through `273/1/b/7`, each with
  strict proof validation and a companion test.
- Defined the live minor surface precisely: no age floor for living alone;
  strict under-22 and under-18 cutoffs; direct parental control separate from
  dependency-based deeming; the State-law-adult exception applies to deeming;
  and foster status defeats (b)(1)(iii) while (b)(4) independently bars
  separate participation.
- Chose source-backed membership/boundary predicates rather than inventing
  pair identifiers or a new candidate relation. Existing
  `member_of_household` relations remain downstream composition inputs.
- Confirmed all 516 remote branches and all open PRs have no 273.1 encoding
  overlap. Issue #28 is related only at the upstream unit boundary; current
  273.9 already consumes 273.10's `snap_total_gross_income`.
- Confirmed the pinned validator rejects merge-anchor key overrides. New tests
  will spell every local factual input in every case.

## Next

- Implement and commit `a` plus precision-focused `b/1` modules and tests.
- Implement and commit `b/2` through `b/4` modules and tests.
- Implement and commit `b/5` through `b/7` modules and tests.
- Regenerate the reverse index; run the pinned validator, proof validator,
  companion tests, and repository tests.
- Recheck coordination immediately before pushing, push, and open PR #1135.
