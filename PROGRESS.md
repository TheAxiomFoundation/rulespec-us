# PR 1002 residual fix progress

## State

Implementation and focused gates are complete. The only remaining repository
gate failure is manifest synchronization: the authorized signing-key helper is
locked in this session, so the affected ACA manifest could not be re-signed.

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
- Re-ran the final committed implementation in a clean snapshot with encoder
  `3869d66d`, engine `ffd82132`, and corpus `b157a201`: deterministic
  validation passed, proof validation passed 38 atoms, and the focused
  companion passed 1 file / 11 cases.
- Re-ran repository pytest: 58 passed, 1 failed, and 1 warning. The only
  failure is `test_encoded_modules_match_their_manifests`, naming only
  `us/policies/aca/ptc_pipeline.yaml`.
- Confirmed the implementation diff does not touch `us/statutes`, the PR body,
  or any GitHub state.

## Next

1. An authorized lane must unlock the signing helper and re-sign the one ACA
   manifest covering `ptc_pipeline.yaml` and `ptc_pipeline.test.yaml`.
2. Re-run repository pytest; the expected post-signing result is 59 passed and
   1 warning.
3. The main lane rewrites the PR body after this lane's final implementation
   commit.
