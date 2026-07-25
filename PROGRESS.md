# PR 1004 final-confirmation progress

## State

- Review only; complete.
- Exact live PR 1004 head: `e513d11b73a402334b71178d5236cd6c82a4f830`.
- Exact live PR 1003 companion head: `9de6ebbc9ec4ecb7a4f9c5dbd201cddcbd9b6184`.
- Verdict: `REQUEST-CHANGES`.
- Single source residual: the PR 1003 companion's “any positive SE profit” sentence overclaims the zero-SE-income guard; the case itself is correct.
- The shared dirty checkout remained untouched; no reviewed source or remote state was written.
- PR 1004's pinned deferred-overlap validator and all focused gates pass from a real canonical-basename `rulespec-us` worktree.
- PR 1003's focused gates pass, and its stale progress file is gone.
- Exact-head GitHub CI never settled to green during the review: final polls returned no runs or statuses for either new head, and both PR snapshots reported `mergeable=false`.
- The canonical gate worktrees have been removed. The clean branch-backed audit worktree will be removed immediately after this final ledger commit; committed audit history remains on `codex/confirm-1004-final`.
- The committed verdict is mirrored to the output path with SHA-256 `e86e06d94f5c131bb3ca42f05160c988f1be1bb659213279957862df8cb01839`.

## Done

- Read the GitNexus PR-review and GitHub connector workflow instructions.
- Resolved both live PR heads and bodies through the read-only GitHub connector.
- Read the prior round-4 verdict and progress record.
- Identified the round-over-round ranges:
  - PR 1004: `e25a31417997e27b50ef9d2315d67b9a9036f7b5..e513d11b73a402334b71178d5236cd6c82a4f830`.
  - PR 1003: `50b6ec228dba8279526bd692de85af4659557c78..9de6ebbc9ec4ecb7a4f9c5dbd201cddcbd9b6184`.
- Ran PR 1004's exact pinned validator at the canonical worktree root; it exits 0 and accepts `pipeline_applicable_deduction_limit_start_for_return_category`.
- Ran PR 1004 focused validation (3/3), proof validation (43/43 atoms), and companions (40/40 cases); all pass.
- Ran PR 1003 focused validation (3/3), proof validation (47/47 atoms), and companions (42/42 cases); all pass.
- Confirmed `bulk/fix3-1003/PROGRESS.md` is absent at the PR 1003 head.
- Confirmed both live bodies are single, superseding, internally coherent current-head accounts.
- Confirmed both round-over-round ranges are linear and contain only the stated source/test naming or documentation repairs plus generated ledger/manifest synchronization; no runtime formula or input/output behavior was added.
- Independently confirmed the PR 1003 wording residual against the current domain formula and the passing `seca-floor-below` counterexample.
- Confirmed all six PR 1004 applied-file manifest hashes and all six PR 1003 applied-file hashes; PR 1003's three supersession links also match.
- Ran PR 1004's oracle-pending ratchet: 2,396 declared, zero stale, no problems.
- Polled exact-head workflows and commit statuses repeatedly through `2026-07-25T02:49:20Z`. Both heads returned empty run/status sets, so CI cannot be called green.
- GitNexus reported the throwaway checkout unindexed. Re-indexing was skipped because it would write `.gitnexus`; direct diff, caller/reference, manifest, and executable-gate inspection was used under the no-write review constraint.
- Wrote and committed `scratchpad/confirm-1004-VERDICT.md` at `b06c90f78`.
- Mirrored the committed verdict byte-for-byte to `.git/codex-confirm-1004-progress/confirm-1004-VERDICT.md` and verified matching SHA-256 hashes.
- Removed the clean canonical PR 1004 and PR 1003 gate worktrees and their temporary merge-analysis files.

## Next

- PR 1003 author: narrow “With any positive SE profit” to this fixture's positive imported federal self-employment income.
- Re-run and confirm CI on the resulting exact heads.
- No further review work remains at the reviewed heads.
