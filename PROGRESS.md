# PR #1008 round-3 re-review

## State

Reviewing exact PR head `efc1d36023d0d820d938f698ed8e431b37962f8d` in this disposable worktree. The substantive age-delegation claim is reproduced, but the explicit no-session-ledger-in-history claim has failed. No GitHub writes or pushes are authorized.

## Done

- Confirmed through the GitHub connector that PR #1008 points to the required head.
- Confirmed the connector-reported net diff contains five files and omits the atomic 7 CFR 247.9(a) files.
- Isolated the review from the dirty shared checkout.
- Audited the exact base-to-head diff and all 15 PR-only commits.
- Confirmed the atomic 247.9(a) YAML, companion, and manifest are absent from both the net diff and the base/head trees.
- Found that PR-only history still contains the session ledger: four commits add/update `PROGRESS.md`, and a fifth deletes it.
- Ran baseline validation successfully.
- Removed only the 247.9(a) condition proof atom and reproduced the exact Person-versus-Household source-scope validation failure, then restored the head file byte-for-byte.

## Next

- Audit every formula and all numeral occurrences.
- Verify State-Plan omission fails closed.
- Run the focused validation, proof, money-proof, companion, and manifest-integrity gates.
- Write the verdict to both requested output paths.
