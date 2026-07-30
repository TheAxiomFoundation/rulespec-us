# Atomic PR A progress

## State

- Branch: `fed-parity/atomicA-57-58-59-55`
- Base: `origin/main` at `ae64af2740340a40d04ed3c652254f53e62fab61`
- Status: in progress
- Provenance lane: ordinary; no signing, pushing, or GitHub writes in this worktree
- Corpus stop condition: cleared against pinned commit `8af592162231e9de748ba6b98792b426ad4fe8b7`

## Done

- Created the requested worktree and branch from the pinned `origin/main` base.
- Recorded the binding scope, stop condition, and delivery constraints.
- Read SPINE-PLAN §5, §6.4, §9 step 5, and the completion/report contract.
- Verified the pinned corpus worktree is detached, clean, and exactly at `8af59216`.
- Verified every required §§57–59 proof atom resolves exactly once, including
  §57(a)(5), §58(a)/(b)/(c), §59(a)/(e)/(g)/(h)/(j), and §55(d)(4) for the
  post-2017 inapplicability of §59(j).
- Audited the import graph: no baseline module imports §§55 or 57–59; the only
  non-module consumer is the unpinned FY2026 federal income-tax program scope.
- Confirmed the changed §55 pending waiver/fingerprint must be removed if its
  corrected module validates cleanly, following the §6012 precedent.
- Encoded bounded §59 completed-return surfaces with a guarded AMTFTC, signed
  subsection (e)/(g)/(h) adjustments, and the post-2017 `not_holds` §59(j)
  applicability judgment.
- Passed the §59 companion (8 cases), proof validation (16 atoms), and focused
  deterministic validate; flip/restore mutations made both the completion
  judgment and kiddie judgment fail their named expectations.
- Encoded §57(a)(5) as a guarded completed-return preference, with explicit
  zero attestations for every other operative 2026 §57 preference.
- Passed the exact-pinned §57 companion (8 cases), proof validation (4 atoms),
  money-atom gate, and focused deterministic validate; negating the §57(a)(7)
  attestation produced five expected assertion failures before restoration.
- Corrected the initial §58 boundary after re-reading SPINE-PLAN §6.4: both
  downstream loss adjustments are signed completed after-insolvency aliases,
  and the module infers no allocation or ordering for the single subsection
  (c)(1) insolvency amount.
- Passed the corrected exact-pinned §58 companion (6 cases), proof validation
  (13 atoms), money-atom gate, and focused deterministic validate; negating
  the subsection (c)(2) attestation produced seven expected assertion failures
  before restoration.
- Corrected §55 to restore the §151 senior deduction and bounded §§57–59
  adjustments to AMTI, subtract the §68 reduction for itemizers, and use one
  §26(b) regular-tax total with ordinary FTC and AMTFTC confined to their
  respective sides.
- Removed the post-2017 kiddie branch and erroneous Form 4972 subtraction while
  making zero §911(f) exclusion and zero Form 4972 amounts explicit fail-closed
  domain conditions.
- Passed the exact-pinned §55 companion (14 cases), proof validation (81 atoms),
  money-atom gate, and focused deterministic validate. Negating the §56 domain
  attestation produced 48 expected assertion failures before restoration.
- Removed §55's stale pending validation waiver and matching fingerprint row
  after the corrected module passed focused pinned validation; both ledgers
  still parse and contain no live §55 entry.
- Added the exact zero-loss pending-oracle union for all 11 new public
  §§57–59 outputs. The ledger is lexicographically sorted and unique, with
  `ceiling == count == 2159` and no pre-existing entry removed.

## Next

1. Regenerate and verify the reverse index.
2. Run every companion, pinned validate, program compile, containment, and
   flip/restore mutation gate.
3. Write the final `WORKER-REPORT.md` without tracking it.
