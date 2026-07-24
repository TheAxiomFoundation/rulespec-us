# PR 1002 residual fix progress

## State

Companion update in progress. The policy gate graph compiles under the pinned
engine, and the 210%-FPL fixture now exercises every fail-closed public
percentage and Money surface.

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
- Verified the policy edit with the pinned engine: the pre-update companion
  compiled all 11 cases and reported only the expected stale raw-rate
  assertion (`0.06968` expected, `0` returned).
- Expanded the off-grid fixture to require zero from both applicable
  percentages, both monthly premium bridge operands, canonical and local
  contribution, canonical and local monthly assistance, local annual
  assistance, and the final credit.

## Next

- Run the focused companion and commit the fixture checkpoint.
- Re-sign the affected two-file manifest locally.
- Run the requested gates, record results, and write
  `fix2-1002-DONE.md` with the final commit SHA.
