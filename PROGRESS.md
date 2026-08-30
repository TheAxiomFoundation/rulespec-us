# Progress

## State

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-31usc1352-base-20260830-codex-233523`
- Mode: detached HEAD
- Verified base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Target: narrow generated 31 U.S.C. § 1352 anti-lobbying base module
- Status: source and toolchain audit in progress; no RuleSpec has been applied
- Final report output: `FINAL_REPORT.md`

## Done

- Read the global, rulespec-us, axiom-corpus, axiom-encode, and agent-secret instructions relevant to this task.
- Attempted `git fetch origin main`; the sandbox could not resolve `github.com`.
- Verified the existing local `origin/main` object is exactly the user-supplied expected SHA.
- Created this uniquely named detached worktree without touching the accepted proposal-security worktree or the earlier anti-lobbying worktree.
- Located the specified official USC corpus checkout, encoder checkout, and real Rust engine checkout.
- Confirmed live RuleSpec may only be installed by signed `axiom-encode encode --apply` and may not be hand-edited.
- Confirmed the dedicated `agent-secret` keychain currently cannot unlock because its stored unlock password is missing.

## Next

1. Map exact § 1352 subsection records and source hashes from the supplied corpus checkout.
2. Resolve the signing-key access blocker through `agent-secret` before any apply.
3. Run scoped encoder attempts with explicit corpus, policy-repo, and Rust-engine paths.
4. Reject any candidate with wrong scope/date, missing filing or supported flow-down, collapsed certification/disclosure, or non-fail-closed missing facts.
5. Apply only an unchanged signed generated candidate, then run proof, fixture, and direct Rust checks.
6. Write exact hashes, commands, results, and per-atom accept/reject findings to `FINAL_REPORT.md`.
