# PR 1009 Blind Adversarial Review Progress

## State

- Review in progress; a blocking effective-window defect has been reproduced.
- Frozen PR head: `3e31892d3b64cf63368927b57de1946e63bae196` (`origin/fed-parity/revproc`).
- PR base reported by GitHub: `ba8c2a0158dd9d87cf304bded9c11fc8479d3e5e` (`main`).
- Review scope is PR #1009 alone; PR #1004 is not being reviewed.
- `git fetch origin` was attempted first and failed because the sandbox could not resolve `github.com`; live metadata is being read through the GitHub connector.

## Done

- Read the full `gitnexus-pr-review` skill.
- Read the full tier-1 blind-review protocol and substituted PR #1009.
- Confirmed live PR metadata, title, body, head SHA, base SHA, and five changed filenames.
- Created `/private/tmp/review-1009` from `origin/fed-parity/revproc`.
- Audited the aggregate PR diff: five expected files only, with no workflow,
  `CODEOWNERS`, toolchain, or unrelated policy changes.
- Verified the six published table values and three phase-in widths against the
  pinned Rev. Proc. pages and 26 USC 199A.
- Confirmed the shared oracle ledger changes semantically add exactly 12 QBI
  outputs and remove zero entries; manifest file hashes match both companions.
- Ran `validate --skip-reviewers`, `proof-validate` (40 atoms), the five-case
  companion, and repository pytest (67 passed); all succeeded.
- Confirmed the no-key generated guard fails closed locally and the recorded CI
  generated-guard job succeeded with its signing secret.
- Built a GitNexus index at the frozen PR head. YAML rules are represented only
  as file nodes, with no executable process/caller edges; repository search also
  finds no consumer of this new module in PR #1009.
- Re-ran the companion in an analysis-only worktree with every test period moved
  to 2027: all five cases still passed despite `effective_to: 2026-12-31`.
  Moving the periods to 2025 correctly produced five missing-parameter failures,
  proving the runtime honors the lower bound but not the upper bound.

## Next

- Finish the independent legal/boundary audit and hand-recomputation table.
- Reconfirm live PR head, current-main divergence, and CI status.
- Write `scratchpad/review-1009-VERDICT.md` with `REQUEST-CHANGES` first,
  finalize/commit this ledger, and remove both throwaway worktrees.
