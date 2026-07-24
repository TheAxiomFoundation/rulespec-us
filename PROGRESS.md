# PR #1003 residual fix — round 2

## State

In progress on branch `fed-parity/surtaxes` at rereviewed head
`d486f0997c62e1d3f1fbc382b0675b853bbcc144`. The worktree was clean at
start. No pushes, GitHub writes, PR-body edits, or `us/statutes` edits are in
scope.

## Done

- Read `scratchpad/rereview-1003-VERDICT.md`.
- Confirmed the three adjudicated residuals:
  - ordinary SECA public tax outputs need the same required section 1401(c)
    attestation guard used by the Additional Medicare wrapper;
  - the pinned `us/statute/26/1401` record text is authoritative for the
    section 1401(b)(2)(B) wage-coordination wording despite the separately
    tracked broken `source_url` metadata;
  - both finite-decimal straddle cases must assert the imported operative
    section 1402(b)(2) floor branch directly.
- Read the repository instructions and confirmed the initial Git state.

## Next

1. Add and prove the ordinary SECA fail-closed foreign-coverage boundary.
2. Align the wage-input contract and proof excerpt to the actual pinned
   section 1401(b)(2)(B) text, then run the deterministic authoring checks.
3. Rework both floor straddle companions to exercise the imported operative
   floor outputs.
4. Refresh required generated artifacts, run focused gates and full repository
   pytest, and write `scratchpad/fix2-1003-DONE.md`.
