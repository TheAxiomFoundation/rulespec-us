# PR #1176 round-2 repair progress

## State

Complete. The round-2 blocker on `fed-parity/ca-bbce` is repaired and all
requested source-sensitive gates have run. The repair builds on resumed head
`02d6244a8`; no push, GitHub write, or signing was performed.

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
- An initial pinned execution pass covered all 56 ordinary and adversarial
  cases. Standalone validation then exposed a harness mismatch: it rejects
  relation inputs to `kind: derived_relation` even though the pinned runtime
  accepts and unions them. The two adversarial cases now live in a committed
  explicit injection fixture, while the adjacent companion retains the
  validator-compatible control and all round-1 regressions.
- Mutation evidence remains targeted: changing only the eligible-member
  existence comparison from `> 0` to `< 0` produces 13 assertion failures in
  exactly the resource-waiver, net-waiver, and zero-benefit MCE cases.
- The reverse index required no byte change and passes 6/6 tests plus
  generator `--check` at 4,250 provisions, 5,092 edges, and 4,487 modules.
- Re-ran all three changed companions from a canonical-root git archive:
  54/54 assertions passed. The two requested California companions account
  for 47/47 of those assertions.
- Materialized and ran the committed injection fixture over the California
  companion in a disposable canonical archive: 2/2 adversarial cases passed.
  Case 1 is programmatically identical to the reviewer's attacked input and
  expected status; case 2 additionally attempts to spoof both private derived
  scalar judgments.
- Pinned validation passed for the federal state-plan module and both
  California modules with `ci_pass=true`, `all_passed=true`, and no errors.
- Proof validation passed for all three changed modules. The MCE module
  remains proof-required and reports 30 atoms with no issues.
- Compose and compile passed. Relative to the pre-repair artifact, the
  compiled program adds only the two private derived helper IDs; it removes
  nothing and changes no parameter or relation inventory.
- Verified the compiled AST binds the trusted count directly to the fully
  qualified federal relation, binds the integrity guard to that derived
  count, and places the fail-closed guard at the start of both MCE outputs.
  Neither helper compiles as caller input.
- Re-ran exact retired-name probes for IPV and probation. Both fail validation
  because the retired relation is undeclared. The IPV, probation, and eligible
  omission regressions retain their expected outcomes.
- Repository layout/program contracts pass 12/12. `git diff --check` is clean.
- Reverse-index regeneration remains byte-identical; reverse-index tests pass
  6/6 and generator `--check` succeeds.
- Confirmed the only output-inventory change is two source-private derived
  helpers. Existing merged-oracle PR #424 public mappings remain unchanged;
  downstream consumers that inventory every compiled derived ID must honor
  `metadata.private` for these helpers.
- Confirmed the expected no-signing handoff: the manifest-sync test reports
  only the two edited module manifests as stale (1 failed, 2 passed). The main
  lane must refresh/re-sign those modules and their changed companion
  artifacts before push or merge.
- Wrote the required untracked `WORKER-REPORT-REPAIR2.md`. The pre-existing
  untracked `WORKER-REPORT.md` remains untouched.

## Next

- Main lane: refresh and sign the affected manifests/companion artifacts,
  then perform any push or GitHub update.
