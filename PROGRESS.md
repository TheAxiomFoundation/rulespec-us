# CSFP eligibility compose progress

## State

The governing age paragraph is present in the pinned corpus. Its atomic
RuleSpec module and the executable federal age-and-income composition are
implemented with companions. Targeted deterministic and proof validation pass;
all 16 targeted cases pass the exact pinned engine, and the full repository
battery is complete. Only owner-controlled signing and oracle-ledger admission
remain intentionally unresolved under the lane's no-sign/no-ledger orders.

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
- Passed exact-pinned deterministic validation for both new modules, two age
  proof atoms plus ten pipeline proof atoms, and all 16 targeted companion
  cases. The clean engine build is pinned at
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`.
- Regenerated the required provision-to-rules reverse index for the new
  regulation and policy source references; check mode reports 3,947
  provisions, 4,671 edges, and 4,435 modules.
- Passed 55 repository tests, the repository monetary-proof ratchet (118 gaps
  within the allowance of 151), source staleness (43/43 pinned modules match),
  and the exact-pinned program-artifact build (32/32).
- Ran all 4,429 companions (15,569 cases) on the pinned engine. The only four
  failures are unchanged baseline references in `us/statutes/26/32.test.yaml`;
  neither new CSFP companion failed.
- Passed `git diff --check`. Signing dry-run selected two manifests covering
  the four new RuleSpec/module-companion files and wrote nothing.
- Confirmed the expected unsigned admission boundary: `guard-generated`
  reports exactly those four files without manifests.
- Confirmed the expected oracle-ledger boundary without syncing it: seven new
  CSFP/247.9(a) outputs are undeclared and the existing ledger has fourteen
  stale entries (21 findings total). The oracle suite design binds
  `csfp_eligible` to PolicyEngine's eligibility boolean, not its CSFP amount.

## Next

- Commit this completed gate record.
- Remove this session ledger from the final tree as required.
- Write the uncommitted scratchpad summary and done marker against final HEAD.
