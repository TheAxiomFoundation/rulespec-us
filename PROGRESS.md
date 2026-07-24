# PR 1002 residual fix progress

## State

Implementation in progress. The policy now gates each public percentage and
local contribution/assistance output directly. The imported canonical
contribution is gated through the operative percentage, and the imported
canonical monthly assistance is gated through its monthly premium operands.

## Done

- Read `rereview-1002-VERDICT.md`.
- Confirmed the requested scope: gate every public arithmetic output on the
  existing runtime-input-validity judgment, extend the 210%-FPL off-grid
  companion, run focused validation/proof/companion gates and repository
  pytest, and leave the PR body and `us/statutes` untouched.
- Verified against the pinned engine schema that `metadata.private` does not
  enforce output visibility, so demoting an unrounded helper would not close
  the public leak.
- Traced the dependency graph and avoided a cycle by having
  `aca_ptc_full_year_runtime_inputs_valid` evaluate the unrounded candidate
  internally instead of reading the now-gated public applicable percentage.
- Added fail-closed gates to the public rate, operative rate, canonical bridge
  operands, local monthly contribution, local monthly assistance, and local
  annual assistance. The existing annual-credit gate remains in place.

## Next

- Run deterministic validation on the policy edit and fix any schema or
  dependency issues.
- Add companion expectations for every gated off-grid surface.
- Run the requested gates, record results, and write
  `fix2-1002-DONE.md` with the final commit SHA.
