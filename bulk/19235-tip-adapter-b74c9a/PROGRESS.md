# Progress

## State

In progress: preparing a signed, generated-only RuleSpec implementation adapter for the NSF TIP person-or-entity-of-concern prohibition.

## Done

- Created the unique detached worktree `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19235-tip-adapter-20260830-codex-b74c9a` at the required base `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- Verified the local `origin/main` reference resolves to the required base and the commit object is intact.
- Attempted two fresh `origin/main` fetches; the sandbox had no DNS configuration and could not resolve `github.com`, so the remote-tracking reference did not change.
- Left the canonical checkout, all accepted/candidate worktrees, and axiom-corpus PR #631 untouched.
- Confirmed the canonical `us/` tree has no reusable `us/statutes/42/19235` RuleSpec module at the required base, so any retained adapter must use an explicit external statutory-prerequisite fact.
- Selected `bulk/19235-tip-adapter-b74c9a/OUTPUT.md` as the final report file because repository layout permits audit Markdown under `bulk/`, not at the repository root.

## Next

- Verify official guidance/statute custody, exact dates, and dynamic-list boundaries.
- Run actual `axiom-encode` generation and signed apply through `agent-secret`.
- Accept only unchanged generated output that passes proof, fixture, and direct-Rust adversarial validation; otherwise restore the generated files and signed manifest.
