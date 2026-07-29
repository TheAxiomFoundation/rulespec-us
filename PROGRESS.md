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
  every non-source member ID strictly enlarges the projection; duplicate
  tuples are deduplicated and cannot change either aggregation.
- Added the private federal
  `snap_state_plan_member_of_household_count`, computed directly as
  `len(member_of_household)` inside the state-plan module, with companion
  coverage. Caller dataset inputs cannot override a derived scalar's
  executable formula in the pinned engine.
- Added the private California integrity judgment comparing the canonical
  projection length with the trusted federal count. Integrity failure makes
  the household-exclusion output `holds` and MCE status `not_holds`.
- Added the reviewer's exact canonical-relation injection shape as a
  fail-closed companion regression, plus a stronger case proving caller data
  cannot spoof either derived integrity output.
- Pinned focused companions pass 56/56 across the federal state-plan, MCE,
  and benefit modules. The two requested CA companions pass 49/49, including
  all round-1 omission cases and both new injection cases.
- Mutation evidence remains targeted: changing only the eligible-member
  existence comparison from `> 0` to `< 0` produces 13 assertion failures in
  exactly the resource-waiver, net-waiver, and zero-benefit MCE cases.
- The reverse index required no byte change and passes 6/6 tests plus
  generator `--check` at 4,250 provisions, 5,092 edges, and 4,487 modules.

## Next

- Finish pinned validation, proof validation, compose/compile, retired-name
  rejection, repository contracts, and public-output containment.
- Write untracked `WORKER-REPORT-REPAIR2.md` with final evidence.
