# PR #1003 fix 3 progress

## State

- Complete within the authorized scope on branch `fed-parity/surtaxes`.
- The Additional Medicare self-employment leg now fails closed until
  axiom-corpus#514's targeted re-ingest is released and this repository's
  corpus pin is updated.
- The signed apply manifest remains intentionally stale because this task
  authorizes signing dry-run only.
- No pushes, GitHub writes, corpus edits, NIIT changes, ordinary SECA changes,
  or statute changes were made.

## Done

- Confirmed the worktree was clean at start.
- Read `round3-1003-VERDICT.md` from the adjudication branch in full.
- Confirmed finding 1: the pinned `us/statute/26/1401` coordination sentence
  names `3121(b)(2)` instead of the lawful `3101(b)(2)`, so the round-2
  corrected proof excerpts are unsupported at the current pin.
- Located the prior round-2 history and progress/report conventions.
- Added the zero-SE restriction to the Additional Medicare domain Judgment.
- Made the locally authored coordination helper return zero for every
  SE-bearing tax unit and explicitly deferred it pending the corpus repair.
- Made the public SE leg a deferred fail-closed zero while preserving the
  independently valid wage leg.
- Restricted the combined output to the wage-only domain.
- Updated all retained SE-bearing companions to assert the fail-closed
  boundary; wage-only arithmetic remains unchanged.
- Removed both unsupported proof excerpts and the unsupported input-contract
  quotation.
- Pinned focused gates pass: canonical validation, 18/18 proof atoms, and
  14/14 companion cases.
- Full focused surtax gates pass: 3/3 canonical validations, 47/47 proof
  atoms, and 42/42 companion cases.
- Focused monetary proof passes with 2 obligations and 0 missing.
- Repository-wide monetary proof passes with 118 known missing atoms across
  2,850 obligations, within the unchanged allowance of 151.
- The oracle-pending ratchet passes with 2,401 declared and applied entries
  and zero stale entries; no ledger rewrite was needed.
- The reverse index regenerates byte-for-byte unchanged and checks current at
  4,184 provisions, 4,977 edges, and 4,465 modules.
- All 43 pinned source hashes match the current corpus text.
- Program Artifacts compiles all 33/33 definitions at the pinned compose and
  rules-engine revisions.
- Signing dry-run selects the expected three surtax manifests covering six
  files and performs no writes.
- Repository pytest finishes with 58 passed, 1 warning, and exactly one
  expected manifest-sync failure naming only the changed Additional Medicare
  module.
- `guard-generated` fails closed solely because
  `AXIOM_ENCODE_APPLY_SIGNING_KEY` is unavailable.
- Final scope checks confirm no NIIT, ordinary SECA, or `us/statutes` delta,
  no forbidden root progress file, and no repository scratchpad directory.

## Next

1. An authorized keyholder may refresh the selected manifests and rerun
   `guard-generated` plus repository pytest; do not push from this task.
2. After the targeted corpus re-ingest, release, and pin bump land, restore
   the lawful section 1401(b)(2)(B) coordination proof and positive SE cases.
