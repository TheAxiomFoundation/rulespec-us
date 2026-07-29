# PR #1176 repair progress

## State

Defensive correctness and completeness audit in progress on
`fed-parity/ca-bbce` from `8d1f31d50cfa094db9206172ee56c6fb68665e7c`.
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

## Next

- Inventory every MCE aggregation or waiver that scans household members.
- Compare every excerpt in both changed modules against the pinned corpus
  programmatically.
- Repair blocker 1 with one canonical federal household-membership relation.
- Add divergent-relation IPV, probation/parole, and eligible-member tests.
- Run all requested companions, validation, composition/compile, mutation,
  reverse-index, output-surface, and intended-path gates.
- Write `WORKER-REPORT-REPAIR.md` with exact evidence and final head.
