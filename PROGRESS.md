# PR 1003 final confirmation review

## State

- Review-only worktree pinned to PR head `9de6ebbc9ec4ecb7a4f9c5dbd201cddcbd9b6184`.
- Scope is limited to the named last-round residuals, focused gates, settled CI, and round-over-round delta.
- One exact-claim residual remains in the renamed Additional Medicare companion comment: “any positive SE profit” is broader than the guard and fixture prove.

## Done

- Confirmed PR metadata and exact head SHA.
- Created an isolated throwaway worktree without touching the shared dirty checkout or PR branch.
- Recovered prior reviewed head `50b6ec228dba8279526bd692de85af4659557c78`.
- Confirmed PR 1004 head `e513d11b73a402334b71178d5236cd6c82a4f830`: the pinned validator accepts the renamed selector from a canonical-basename root, and the live body is coherent.
- Confirmed PR 1003’s stale `bulk/fix3-1003/PROGRESS.md` is absent and its live body is coherent.
- Checked the round delta: one companion rename/comment edit, deletion of the stale ledger, and three mechanical manifest re-signs.
- Found the single remaining defect: the companion comment universally claims that positive SE profit makes the zero-imported-SE-income guard dominate, while the committed `$433` floor fixture derives imported SE income of zero from positive gross profit.
- From a detached root literally named `rulespec-us`, reproduced the pinned focused gates: validation `3/3`, proof atoms `47/47`, companions `42/42`, Additional Medicare companion `14/14`, and encoding-manifest pytest `3/3`.

## Next

- Confirm settled CI and inspect only the round-over-round delta.
- Write `scratchpad/confirm-1003-VERDICT.md`.
