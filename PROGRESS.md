# PR 1003 final confirmation review

## State

- Review complete on PR head `9de6ebbc9ec4ecb7a4f9c5dbd201cddcbd9b6184`.
- Verdict is `REQUEST-CHANGES` for one exact-claim residual: “any positive SE profit” is broader than the guard and fixture prove.
- The subject PR branch and shared dirty checkout remain untouched.

## Done

- Confirmed PR metadata and exact head SHA.
- Created an isolated throwaway worktree without touching the shared dirty checkout or PR branch.
- Recovered prior reviewed head `50b6ec228dba8279526bd692de85af4659557c78`.
- Confirmed PR 1004 head `e513d11b73a402334b71178d5236cd6c82a4f830`: the pinned validator accepts the renamed selector from a canonical-basename root, and the live body is coherent.
- Confirmed PR 1003’s stale `bulk/fix3-1003/PROGRESS.md` is absent and its live body is coherent.
- Checked the round delta: one companion rename/comment edit, deletion of the stale ledger, and three mechanical manifest re-signs.
- Found the single remaining defect: the companion comment universally claims that positive SE profit makes the zero-imported-SE-income guard dominate, while the committed `$433` floor fixture derives imported SE income of zero from positive gross profit.
- From a detached root literally named `rulespec-us`, reproduced the pinned focused gates: validation `3/3`, proof atoms `47/47`, companions `42/42`, Additional Medicare companion `14/14`, and encoding-manifest pytest `3/3`.
- Repeatedly queried current-head CI. GitHub still exposed the prior `3327de193` merge ref and no runs or statuses for `9de6ebbc9`; fresh CI is required after the wording fix creates a new head.
- Wrote and committed `scratchpad/confirm-1003-VERDICT.md`.
- Copied the committed verdict to the requested output path; both copies have SHA-256 `1711a9e3a163dde4416d414320bcabfe0d9bd264ddcff804f0e1b34566e78e9e`.

## Next

- Remove the clean throwaway worktrees and temporary pinned gate snapshots.
