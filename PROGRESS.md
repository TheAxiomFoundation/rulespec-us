# Progress

## State

All eight household-concept modules and companion tests are implemented and
locally validated. Repository-wide validation and generated-index refresh are
next.

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
- Implemented `273/1/a` and `273/1/b/1` with strict source proofs and companion
  tests.
- Covered the live minor boundaries at ages 15, 16, 17, 18, 21, and 22,
  including direct control, financial and other dependency, State-law
  adulthood, foster status, parental co-residence, and spouses.
- Pinned `axiom-encode` validation and proof validation pass for both core
  modules; all 17 core companion cases pass on the available local engine.
- Implemented `273/1/b/2` through `273/1/b/4`, including the elderly/disabled
  separate-household option, the boarder compensation and provider-election
  rules, and the foster-child boundary.
- Pinned validation and proof validation pass for all three special-household
  modules; all 17 companion cases pass on the available local engine.
- Implemented `273/1/b/5` through `273/1/b/7`, with direct imports of the
  paragraph (b)(1) mandatory-combination result for roomers, attendants, and
  institution exceptions.
- Encoded the strict institution meal-share boundary, boarder override, all
  five institution-exception settings, the “unless otherwise stated” gate,
  all paragraph (b)(7) ineligibility paths, and the optional cross-program
  disqualification only when the State option is active.
- Kept institution exceptions limited to removing the institution bar:
  another paragraph (b)(7) bar still excludes the person. Kept excluded
  household members distinct from host-unit nonmembers and left downstream
  income, resource, and size treatment to the applicable later rules.
- Pinned validation and proof validation pass for all three final boundary
  modules; all 38 companion cases pass on the available local engine.

## Next

- Regenerate the reverse index; run the pinned validator, proof validator,
  companion tests, and repository tests.
- Recheck coordination immediately before pushing, push, and open PR #1135.
