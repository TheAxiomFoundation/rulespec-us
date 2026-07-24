# PR 1009 Blind Adversarial Review Progress

## State

- Review in progress; statutory values/windows are correct under the pinned
  toolchain, but a blocking filing-status boundary defect is confirmed.
- Live GitHub reports the PR mergeable but 27 commits behind `main`; its
  successful workflows were run against the original base.
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
- Traced a misleading 2027 pass to a stale July 6 local engine binary. Rebuilt
  exact pinned engine `ffd8213271947b0189a9dd61a055c1e0e78908a0`; the pinned
  engine correctly failed all five 2025 and all five 2027 probes, so the declared
  effective window is executable and correct.
- Ran the pinned encoder's filing-status boundary audit: all three derived
  selectors are rejected because they synthesize local `#input.filing_status`
  instead of importing an absolute upstream legal classification. No executable
  upstream filing-status output exists at the frozen PR head.
- Demonstrated the consequence with the exact pinned engine: changing the final
  fixture's status from valid code `4` to invalid code `9` still passed and
  selected the all-other amounts because match lowering uses the last arm as an
  unconditional fallback.
- Reconfirmed live workflow runs are all successful, including generated-guard,
  reverse-index, companion, proofs, oracle coverage, and program artifacts; those
  runs used synthetic merge base `ba8c2a0`, while live `main` is now `d5dcc6b3`
  and GitHub's final mergeability calculation reports `mergeable: true`.

## Next

- Write `scratchpad/review-1009-VERDICT.md` with `REQUEST-CHANGES` first and the
  hand-recomputation/local-gate tables.
- Reconfirm live PR state one final time, finalize/commit this ledger, and remove
  the throwaway review and GitNexus worktrees.
