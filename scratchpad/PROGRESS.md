# PR #1003 fix 3 progress

## State

- In progress on branch `fed-parity/surtaxes` from
  `3327de19395465dee736061b2d4c33108416d261`.
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

## Next

1. Remove unsupported coordination excerpts and explicitly defer the
   self-employment leg.
2. Restrict the combined Additional Medicare output to tax units with zero
   self-employment income.
3. Convert the self-employment companion cases to fail-closed assertions while
   preserving the lawful post-repair arithmetic as comments.
4. Run focused validation, proof, companion, repository pytest, generated
   artifact checks, and signing dry-run.
5. Write `scratchpad/fix3-1003-DONE.md` with the final SHA, case table, and
   complete gate results.
