# PR #1008 round-3 re-review

## State

Reviewing exact PR head `efc1d36023d0d820d938f698ed8e431b37962f8d` in this disposable worktree. No GitHub writes or pushes are authorized.

## Done

- Confirmed through the GitHub connector that PR #1008 points to the required head.
- Confirmed the connector-reported net diff contains five files and omits the atomic 7 CFR 247.9(a) files.
- Isolated the review from the dirty shared checkout.

## Next

- Inspect the exact diff and branch history, including session-ledger and atomic-file claims.
- Reproduce the scope-validation failure after removing the 247.9(a) condition atom.
- Audit every formula and all numeral occurrences.
- Verify State-Plan omission fails closed.
- Run the focused validation, proof, money-proof, companion, and manifest-integrity gates.
- Write the verdict to both requested output paths.
