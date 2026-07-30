# PR #1179 Repair Progress

## State

- Defensive correctness and completeness audit in progress on
  `fed-parity/chunk2-taxable-income`.
- Starting point verified at the current local pushed head
  `4ced8fb7065311338ea732cab0a26105e750c40f`.
- Scope is limited to the five blockers in the frozen PR review plus mechanics
  directly affected by their repair.
- Imported injectable relation schemas are now pinned; legal proof and
  companion/domain repairs remain in progress.

## Done

- Read the frozen adversarial review at commit `f58fc22a6`.
- Confirmed the branch, `HEAD`, and
  `origin/fed-parity/chunk2-taxable-income` all resolve to the reviewed head.
- Confirmed the only pre-existing worktree change is untracked
  `WORKER-REPORT.md`; it will be preserved and excluded from repair commits.
- Extended the executable relation-schema registry to the §151 exemption and
  senior `(TaxUnit, Person)` relations and the §170(p) charity
  `(TaxUnit, Payment)` relation.
- Demonstrated that reversing each registered argument vector independently
  fails the schema test, restored each imported module byte-for-byte, and
  reconfirmed the positive test after every restoration.

## Next

- Repair the stale §165 proof/completed-boundary semantics and add the missing
  §63(a) itemizer proof bridge.
- Add the prescribed §151 MAGI-addback diagnostic.
- Reject contradictory individual/nonindividual facts and add a regression.
- Regenerate affected mechanics, run all required gates, and write the
  untracked repair report.
