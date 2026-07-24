# PR 1002 residual fix progress

## State

Focused gating in progress. The policy gate graph compiles under the pinned
engine, the companion passes, and the on-grid judgment is being normalized to
the deterministic validator's boolean-only syntax.

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
- Ran the first clean pinned gate snapshot. Proof validation passed 38 atoms
  and the companion passed 11 cases. Deterministic validation rejected nested
  scalar `if` expressions inside the `Judgment` formula even though the engine
  executed them, so the on-grid check was rewritten as equivalent boolean
  branches.
- Repository pytest reached 58 passes and one expected stale-manifest failure;
  the authorized signer dry run selected one manifest and the intended two
  files, but the secret helper is locked in this session.

## Next

- Re-run validation, proofs, and the focused companion after the boolean
  rewrite.
- Re-sign the affected two-file manifest if the authorized key becomes
  available; otherwise record the credential blocker and stale-manifest pytest
  result precisely.
- Run the requested gates, record results, and write
  `fix2-1002-DONE.md` with the final commit SHA.
