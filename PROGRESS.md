# PR #1176 round-2 repair progress

## State

Defensive correctness and completeness audit in progress on
`fed-parity/ca-bbce`, starting from
`686d413cfe15410dc160010f7863096c8c20ef48`.
The round-2 blocker is the caller-injectable private derived relation
`calfresh_mce_canonical_member_of_household`.
No push, GitHub write, or signing is in scope.

## Done

- Read the round-2 review first at
  `.git/review-worktrees/pr-1176-repair-686d413/REVIEW.md`.
- Confirmed the requested branch and exact starting head.
- Confirmed the pre-existing untracked `WORKER-REPORT.md`; it will remain
  untouched.
- Selected the GitNexus debugging and impact-analysis workflows. GitNexus
  graph tools are not exposed in this session, so direct source, repository
  search, compiled-artifact, and executable evidence will be used.
- Confirmed the reviewer reproduced a fail-open by directly supplying an
  eligible row under the private derived relation while the federal relation
  contained only an excluded member.

## Next

- Determine whether MCE aggregations can range directly over the fully
  qualified federal relation; prefer eliminating the local surface.
- Add the exact injection regression and retain all round-1 regressions.
- Run companions, pinned validation, proof validation, compose/compile,
  mutation evidence, reverse-index checks, and public-output containment.
- Write untracked `WORKER-REPORT-REPAIR2.md` with final evidence.
