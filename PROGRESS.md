# PR #1137 Blind Adversarial Review Progress

## State

- Review branch: `review/pr-1137-995fff`.
- Disposable worktree: `.git/review-worktrees/pr-1137-995fff`.
- Reviewed PR head: `995fff6104a19a89843934e3832cd097c308af1d`.
- Base: `origin/main` at `6b0773d3f7fa6719f208154f3e609e292ab7abe7`.
- Pinned corpus: `bf97b17baebfdf12601f7c23697524bf5adcdaed`.
- Status: complete; verdict is `REQUEST-CHANGES`.

## Done

- Preserved the dirty primary checkout by creating a separate worktree and throwaway branch from the exact target commit.
- Confirmed the target commit exists locally and its merge base with `origin/main` is the PR base.
- Attempted the required `git ls-remote`; sandbox DNS blocked access to `github.com`.
- Independently confirmed through the read-only GitHub connector that open PR #1137 has branch `fed-parity/savers` and full head SHA `995fff6104a19a89843934e3832cd097c308af1d`.
- Confirmed the target commit pins axiom-corpus `bf97b17baebfdf12601f7c23697524bf5adcdaed`.
- Captured the 10-file PR diff. It includes `PROGRESS.md` and `WORKER-REPORT.md`, contrary to the requested PR hygiene invariant.
- Attempted the GitNexus PR-review graph workflow. The repository had no index; local analysis built an index but could not register it because the sandbox denied writes to `/Users/maxghenis/.gitnexus/registry.json`, so graph queries could not target it.
- Verified the corpus checkout is clean and exactly at `bf97b17baebfdf12601f7c23697524bf5adcdaed`.
- Verified the prescribed encoder source checkout is exactly at `3869d66d009f52258be35901edbef370e65a399c`.
- Recorded that the supplied `/Users/maxghenis/axiom-rules` checkout is at `aa1ff025906c7216c053e9b9c4097cc0dfef1811`, not the pinned `ffd8213271947b0189a9dd61a055c1e0e78908a0`.
- The literal test invocation against the review worktree failed module resolution because its leaf directory is not named `rulespec-us`; this was a path-routing artifact, not a module assertion.
- Created a second detached exact-head disposable worktree at `.git/review-worktrees/pr-1137-exec/rulespec-us` solely to preserve canonical repository routing.
- Baseline companion run passed: 2 files, 26 cases.
- Mutated the first tier comparison from `<=` to `<`; the same suite failed eight assertions in the exact 50-percent-limit cases across single, joint, head-of-household, married-filing-separately, and surviving-spouse paths.
- Restored `<=`; the same suite passed 2 files and 26 cases, the pipeline SHA-256 returned to `56fecc5f4ae448cb4422371ab49e7894410d26076ffedeea3847bf8f9fb5f787`, and the exact-head worktree is clean.
- Removed the shared zero-valued section 911 input from the companion anchor; 21 cases failed with an explicit `missing input section_911_excluded_income` error. Restoring the input returned 26/26 and the test SHA-256 to `2621795e923fa8eac2eb147bab5d21a60c766cc6b415f85fcf69c03bd9f4af3a`.
- Proof validation passes both modules: 42 pipeline atoms plus 27 Notice atoms; 0 of 9 monetary obligations lack proof.
- Pinned-encoder CI validation passes the Notice module but rejects the pipeline: `pipeline_savers_credit_50_percent_agi_limit` composes an imported category while overlapping the Notice module's unresolved deferred generic limit.
- The current GitHub `Repository Checks` run is red. Its failed layout step names the two forbidden top-level PR files, then skips RuleSpec validation, so it does not contradict the local pinned-validator failure.
- Verified all 48 corpus-backed proof excerpts verbatim against uniquely resolved rows in pinned corpus `bf97b17ba`; Notice values and 2026 effective periods match pages 3-4, with no executable 2025 or `157500` stale values.
- Verified the two manifest file unions and hashes cover exactly the four changed RuleSpec/test files at ancestor `953106a58`; HMAC authenticity cannot be checked because the signing key is unavailable.
- Verified the oracle ledger grows from 2,293 to 2,313 by exactly the expected 20 IDs, with matching ceilings, no removals, and no foreign additions.
- Verified the reverse index is current at 4,238 provisions, 5,077 edges, and 4,485 modules.
- Verified legal fidelity against pinned statute rows 225, 230, 235, 240, 245, and 1,260: per-person caps, AGI add-backs, inclusive tiers, all primary/spouse eligibility screens, and the explicit section 25B(d)(2) deferral pass.
- Confirmed the pinned validator detects the same deferred-surface defect in all three selected 50%, 20%, and 10% AGI-limit outputs; the CLI reports the first and exits 1.
- Independently passed the 26-case suite on exact PR bytes using an offline build of pinned rules engine `ffd8213271947b0189a9dd61a055c1e0e78908a0`.
- Confirmed remote generated-manifest guard succeeds at the target head, while local HMAC verification remains unavailable without the signing key.
- Wrote the final evidence-backed verdict to `WORKER-REPORT.md`, including both merge-blocking findings, all passing dimensions, and every sandbox/environment limitation.

## Next

- None. The PR must remove the two forbidden root artifacts and resolve all three pinned-validator deferred-surface errors before merge.
