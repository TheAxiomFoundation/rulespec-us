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
- Confirmed path 1 is unavailable in the pinned engine. Formula relation
  arguments must be bare identifiers, imports have no symbol-alias syntax,
  and the program contains two canonical `member_of_household` producers.
  The CA-local predicates therefore cannot bind a bare aggregation directly
  to the fully qualified state-plan relation.
- Recovered the exact reviewer fixture (`a652857f...`) and result
  (`9a4d9cc9...`). Its only semantic addition is a two-row direct canonical
  relation (`{}` plus a fully eligible second member) beside one excluded
  federal member; the placeholder preserves the federal member's row index.
- Selected path 2: expose a private source-side count computed inside the
  federal state-plan module, compare it with the CA projection length in a
  private integrity judgment, and make the two household MCE outputs fail
  closed when the counts diverge. Under the pinned engine's monotone union,
  every new injected member tuple strictly enlarges the projection.

## Next

- Implement the source-side count, integrity judgment, and exact injection
  regression while retaining all round-1 regressions.
- Run companions, pinned validation, proof validation, compose/compile,
  mutation evidence, reverse-index checks, and public-output containment.
- Write untracked `WORKER-REPORT-REPAIR2.md` with final evidence.
