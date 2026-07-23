# CSFP eligibility compose progress

## State

The governing age paragraph is present in the pinned corpus. Its atomic
RuleSpec module and the executable federal age-and-income composition are
implemented with companions. Targeted deterministic and proof validation pass;
all 16 targeted cases pass provisionally, and exact-pinned engine verification
plus the full repository battery remain.

## Done

- Confirmed the worktree is clean on `fed-parity/csfp` at `c86b2f62`.
- Located no copy of the named campaign scratchpads in the worktree, repository
  object database, adjacent worktrees, temporary directories, or Codex storage;
  precedent branches and in-tree sources will be used while that evidence gap
  remains explicitly recorded.
- Verified `us/regulation/7/247/9/a` is present at pinned corpus ref
  `dfa47fb05bd1d3abbadf0ff17ce4a04bdd5c8085`, with an exact child anchor to
  official eCFR XML and an inclusive age-60 condition.
- Confirmed paragraph (a) contains no separate certification procedure; the
  pre-September-17-1986 exception is in paragraph (b) and already encoded.
- Implemented `us/regulations/7-cfr/247/9/a.yaml` and its 59/60/61 companion.
- Passed pinned-encoder deterministic validation, two-atom proof validation
  against the pinned local corpus, and all three companion cases.
- Implemented `us/policies/usda/csfp/eligibility_pipeline.yaml`, importing the
  paragraph-(a) age predicate and paragraph-(b) income predicate.
- Bound one monthly-or-annual income amount, annual FPG dollars, household
  size, and the actual State FPG ratio; the direct path fails closed for
  invalid inputs or a State ratio above 1.50 without blocking adjunctive paths.
- Added 13 hand-computed pipeline cases covering ages 59/60/61, annual and
  monthly exact/over income boundaries, two-person household scaling, State
  limit compliance, both adjunctive routes, the legacy exception, and zeros.
- Passed targeted pipeline validation, all 10 proof atoms, and all 13 cases
  against the available engine checkout. The exact pinned-engine rerun remains
  part of the next gate step.
- Regenerated the required provision-to-rules reverse index for the new
  regulation and policy source references.

## Next

- Build/use the exact pinned engine and rerun both companions.
- Run the complete campaign gate battery and fix any in-scope failures.
- Produce the scratchpad summary and done marker, leave signing at dry-run,
  and remove this session ledger from the final tree.
