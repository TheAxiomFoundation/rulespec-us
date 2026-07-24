# PR #1003 fix 3 progress

## State

- In progress on branch `fed-parity/surtaxes`.
- Scope is limited to the Additional Medicare tax pipeline and its companion
  cases at the current corpus pin.
- The self-employment leg must fail closed until axiom-corpus#514's targeted
  re-ingest is released and this repository's corpus pin is updated.
- No pushes, GitHub writes, corpus edits, NIIT changes, or ordinary SECA
  changes are in scope.

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

## Next

1. Regenerate/check the reverse index and verify the oracle ledger remains
   current.
2. Run repository pytest and remaining repository/focused gates.
3. Run signing dry-run only and record the expected manifest handoff.
4. Verify the final diff excludes NIIT, ordinary SECA, and statute files.
5. Write the task scratchpad's `fix3-1003-DONE.md` with the final SHA, case
   table, and complete gate results.
