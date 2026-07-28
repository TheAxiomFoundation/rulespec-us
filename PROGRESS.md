# PROGRESS

## State

Chunk 1 implementation is in progress on
`fed-parity/chunk1-salt-itemized`. Both legal compose modules and companions
are complete, and the reverse-index and pending-coverage union are complete.
Final combined gates, diff audit, and worker report remain. The branch starts
from the requested main/Atomic lineage and now includes the updated
`origin/main` at `af6c57d61` and updated Atomic PR 0 through `b8ba5dbe7`.

- Scope: SALT and itemized-taxable-income-deduction compose modules,
  companions, reverse index, and pending oracle coverage.
- Signing/manifests: reserved for the main lane; this worker will not sign or
  generate the two compose manifests.
- Pushes/GitHub writes: none.

## Done

- Read binding `SPINE-PLAN.md` §§5, 6.1, 6.2, and 9 before implementation.
- Confirmed Atomic PR 0 is not yet contained in `origin/main`, then merged
  `origin/fed-parity/atomic-63c6-67h` as instructed.
- Verified the updated main pin is corpus commit
  `8af592162231e9de748ba6b98792b426ad4fe8b7`, as specified by the task.
- Verified that pinned corpus contains `us/statute/26/165` and descendants, so
  `itemized-casualty-completed` is adopted with §165 proof atoms.
- Added the 2026 SALT compose with the statutory cap, MFS fractions, MAGI
  §§911/931/933 addbacks, floor, and no simulation-only AGI ceiling.
- Added all 16 SALT grid cases plus invalid-status, negative-component,
  every-attestation-false, and typed relation-orientation diagnostics.
- Passed the pinned SALT companion runner (25/25) and standalone
  `validate --skip-reviewers`; audited the merged SALT import surface with no
  duplicate rule or relation names.
- Added the bounded six-component itemized aggregate, importing the SALT
  final, section 67(h) judgment, and section 68 final/reduction without
  duplicating section 68 arithmetic.
- Added all 17 itemized grid cases, including the now-adoptable positive
  casualty case, plus 11 fail-closed and relation-orientation diagnostics.
- Passed the pinned itemized companion runner (28/28) and standalone
  `validate --skip-reviewers` with the pinned corpus artifact; audited the
  full transitive import closure with zero duplicate rule names and one
  uniquely named `(TaxUnit, Person)` relation.
- Recorded that the ambient corpus checkout is stale and lacks section 165;
  validation against the repository-pinned corpus commit has zero findings.
- Regenerated the reverse index to 4,247 provisions, 5,105 edges, and 4,490
  modules. The exact delta from Atomic PR 0 is 20 own-module edges and zero
  removals.
- Added exactly seven new pending-classification IDs. Verified the pending
  ledger is a lossless ID-set union from Atomic PR 0, all 2,139 base entry
  objects are byte-semantically unchanged, and `ceiling == count == unique
  IDs == 2,146`.
- Incorporated the updated Atomic PR 0 tip after its remote-tracking branch
  advanced during this run; retained this committed progress record while
  accepting its section 6012 repair and re-signed prerequisite manifests.

## Next

1. Run the combined pinned companion and validation gates; fix all new
   findings.
2. Audit the merge-base diff and write untracked `WORKER-REPORT.md`.
