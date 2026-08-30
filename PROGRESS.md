# Progress

## State

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-31usc1352-base-20260830-codex-233523`
- Mode: detached HEAD
- Verified base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Target: narrow generated 31 U.S.C. § 1352 anti-lobbying base module
- Status: source scope mapped; first generated candidate pending; no RuleSpec has been applied
- Final report output: `FINAL_REPORT.md`

## Done

- Read the global, rulespec-us, axiom-corpus, axiom-encode, and agent-secret instructions relevant to this task.
- Attempted `git fetch origin main`; the sandbox could not resolve `github.com`.
- Verified the existing local `origin/main` object is exactly the user-supplied expected SHA.
- Created this uniquely named detached worktree without touching the accepted proposal-security worktree or the earlier anti-lobbying worktree.
- Located the specified official USC corpus checkout, encoder checkout, and real Rust engine checkout.
- Confirmed live RuleSpec may only be installed by signed `axiom-encode encode --apply` and may not be hand-edited.
- Confirmed the dedicated `agent-secret` keychain currently cannot unlock because its stored unlock password is missing.
- Mapped all 73 normalized § 1352 records in `data/corpus/provisions/us/statute/2026-08-30-proposal-security-title-31.jsonl` and verified the official OLRC archive/member provenance.
- Verified the normalized records expose only the `2026-07-12` snapshot boundary; the raw source notes contain older legal-history dates but are not normalized provision context.
- Confirmed subsection (a)'s appropriated-fund prohibition has no transaction-amount threshold.
- Confirmed subsection (d)(2)(B)'s reporting exemption makes the non-loan contract/grant/cooperative-agreement/subcontract/subgrant filing boundary strictly greater than `$100,000`; Federal loans instead use subsection (d)(2)(C)'s separate threshold.
- Confirmed subsection (b)(2) separates the no-prohibited-payment certification from disclosure of an LDA registrant who made lobbying contacts, while subsection (b)(5) assigns downstream filers separately.

## Next

1. Create and hash a task-specific encoder context that preserves the audited rejection gates.
2. Run scoped encoder attempts with explicit corpus, policy-repo, and Rust-engine paths.
3. Reject any candidate with wrong scope/date, missing filing or supported flow-down, collapsed certification/disclosure, or non-fail-closed missing facts.
4. Resolve the signing-key access blocker through `agent-secret` before any apply.
5. Apply only an unchanged signed generated candidate, then run proof, fixture, and direct Rust checks.
6. Write exact hashes, commands, results, and per-atom accept/reject findings to `FINAL_REPORT.md`.
