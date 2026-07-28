# PROGRESS

## State

Chunk 1 implementation is in progress on
`fed-parity/chunk1-salt-itemized`. The SALT compose and companion are complete;
the itemized compose and companion are being implemented. The branch starts
from local `origin/main` at `c13cdf7dd` and includes Atomic PR 0 by
fast-forward merge through `3f933cd93`.

- Scope: SALT and itemized-taxable-income-deduction compose modules,
  companions, reverse index, and pending oracle coverage.
- Signing/manifests: reserved for the main lane; this worker will not sign or
  generate the two compose manifests.
- Pushes/GitHub writes: none.

## Done

- Read binding `SPINE-PLAN.md` §§5, 6.1, 6.2, and 9 before implementation.
- Confirmed Atomic PR 0 is not yet contained in `origin/main`, then merged
  `origin/fed-parity/atomic-63c6-67h` as instructed.
- Verified the current main pin is the newer corpus commit
  `10142cb0f07403c2de4599c76bec01e96640fda9`.
- Verified that pinned corpus contains `us/statute/26/165` and descendants, so
  `itemized-casualty-completed` is adopted with §165 proof atoms.
- Added the 2026 SALT compose with the statutory cap, MFS fractions, MAGI
  §§911/931/933 addbacks, floor, and no simulation-only AGI ceiling.
- Added all 16 SALT grid cases plus invalid-status, negative-component,
  every-attestation-false, and typed relation-orientation diagnostics.
- Passed the pinned SALT companion runner (25/25) and standalone
  `validate --skip-reviewers`; audited the merged SALT import surface with no
  duplicate rule or relation names.

## Next

1. Finish the itemized compose and companion, importing §67(h) and §68.
2. Run the combined pinned companion and validation gates; fix all new
   findings.
3. Regenerate the reverse index and splice only this chunk's seven pending
   mappings.
4. Audit the merge-base diff and write untracked `WORKER-REPORT.md`.
