# PR #1176 repair progress

## State

Defensive correctness and completeness audit complete on
`fed-parity/ca-bbce`. The implementation was verified at
`bfadb955942721ce4bb31ea784a9d4beaede3f90`, descended from
`8d1f31d50cfa094db9206172ee56c6fb68665e7c`.
No push, GitHub write, signing, or ProgramSpec manifest repair is in scope.

## Done

- Read the blind-review report at
  `.git/review-worktrees/pr-1176-8d1f31d/REVIEW.md`.
- Confirmed the target branch and starting head.
- Confirmed the pre-existing untracked `WORKER-REPORT.md`; it will remain
  untouched.
- Selected the GitNexus debugging workflow, then confirmed that GitNexus graph
  tools are unavailable in this session; direct source and compiled-flow
  inspection will be used instead.
- Replayed both SHA-verified reviewer reproducers from an exact-head,
  canonical-basename archive. Each passes with the observed fail-open
  expectations; each produces exactly the two targeted failures with
  fail-closed expectations.
- Programmatically compared all 37 excerpts in both modules against every
  matching pinned-corpus row: 36 were byte-verbatim and the sole mismatch was
  the ACIN `Broad- Based` text.
- Corrected the ACIN excerpt to the retained row's exact `Broad- Based` bytes.
- Traced every MCE member scan. Only the household-bar and eligible-member
  aggregations scan members; all benefit-side waivers delegate to MCE status.
- Removed the PR-new California membership relation and ranged both MCE
  aggregations over the imported federal state-plan `member_of_household`.
- Migrated the isolated companion to the canonical relation and merged the
  California-only bar facts into the benefit companion's existing federal
  rows, preserving the E/D rows' true elderly/disabled facts.
- Added canonical equivalents of the reviewer's divergent IPV,
  probation/parole, and eligible-member omission cases. A direct attempt to
  retain the now-undeclared California relation as adversarial input was
  rejected by the pinned runner, proving that divergence is no longer a
  representable dataset state.
- Smoke-ran both companions from a canonical archive: 47/47 cases passed.
- The first full program compile exposed that a bare imported relation name
  with a local predicate remained an unqualified implicit relation. Replaced
  that alias with a private, tautological derived relation whose executable
  source is the fully qualified federal state-plan relation; both MCE
  aggregations now range over this complete canonical projection.
- Verified the corrected projection in a canonical-basename archive: the
  compiled program contains neither the unqualified alias nor the retired CA
  input relation, both companions pass 47/47 cases, both modules validate with
  zero findings, and proof validation passes 29/29 and 9/9 atoms.
- Rebuilt a fresh canonical-basename archive from the verified implementation
  commit and passed the full final gate set: 47/47 companion cases, both module
  validators with zero findings, 38/38 proof atoms, 12/12 repository contract
  tests, and program composition/compilation with 328 derived outputs, 100
  parameters, two canonical input relations, and one private derived relation.
- Re-verified mutation sensitivity by changing the eligible-member comparator
  from `> 0` to `< 0`: the benefit companion produced 13 assertion failures
  confined to the three intended MCE-dependent cases; the untouched companion
  then passed 12/12.
- Confirmed all 38 excerpts in both modules are byte-verbatim against every
  matching pinned-corpus row.
- Confirmed the reverse index is current at 4,250 provisions, 5,092 edges, and
  4,487 modules; no regeneration was needed.
- Confirmed the repair adds or removes no public derived/parameter output and
  needs no axiom-oracles mapping change. It retires one caller-populated CA
  relation and replaces it with a private canonical projection.
- Wrote the final evidence and handoff report to
  `WORKER-REPORT-REPAIR.md`.

## Next

- Main lane: refresh and re-sign the affected encoding/ProgramSpec manifests
  for blocker 2, then run its signing/fingerprint gates.
- Main lane: retain the already-merged 17 oracle mappings unchanged; this
  repair requires neither a new mapping nor a retired mapping row.
