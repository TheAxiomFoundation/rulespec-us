# PR 1004 final-confirmation progress

## State

- Review only; in progress.
- Exact live PR 1004 head: `e513d11b73a402334b71178d5236cd6c82a4f830`.
- Exact live PR 1003 companion head: `9de6ebbc9ec4ecb7a4f9c5dbd201cddcbd9b6184`.
- Candidate is isolated in a branch-backed throwaway worktree.
- The shared dirty checkout is untouched; no reviewed source or remote state will be written.
- PR 1004's pinned deferred-overlap validator and all focused gates pass from a real canonical-basename `rulespec-us` worktree.
- PR 1003's focused gates pass, and its stale progress file is gone.
- A precision concern remains under independent confirmation: the PR 1003 companion says “any positive SE profit” makes the wage-only guard dominate, while a current-head floor fixture has positive gross profit but zero imported federal SE income.
- Exact-head GitHub CI is not yet green or settled: the connector returns no runs or statuses for either new head, and both PR snapshots report `mergeable=false`.

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
- Polled exact-head workflows and commit statuses repeatedly. Both heads currently return empty run/status sets, so CI cannot yet be called green.

## Next

- Resolve the narrow PR 1003 companion-claim adjudication.
- Re-poll exact-head CI/head state once more.
- Write and commit `scratchpad/confirm-1004-VERDICT.md`, mirror it to the output path, then remove the throwaway worktree.
