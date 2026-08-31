# Progress

## State

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-in149-20260830-47290`
- Mode: detached HEAD
- Verified base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Scope: NSF Important Notice 149 Items 1–2 supporting-document retention/request and research-security-training certification adapters only; IHE-only RECR/42 U.S.C. §§ 19039–19040 excluded
- Status: source/base/toolchain audit in progress; no generated adapter accepted
- Final report output: `bulk/nsf-in149-retention-training-20260830/OUTPUT.md`

## Done

- Attempted a fresh `git fetch origin main`; sandbox DNS could not resolve `github.com`.
- Verified the existing local `origin/main` and commit object exactly match the required SHA.
- Created this unique detached worktree without modifying any existing branch or axiom-corpus PR #631.
- Loaded the Axiom repository instructions and the `agent-secrets` custody workflow.
- Confirmed the dedicated `agent-secret` keychain exists but its login-keychain unlock-password item is missing; signed apply currently fails closed.
- Started independent audits of the seven authorized guidance records, the pinned encoder, generated-only precedents, and the actual Rust engine.

## Next

1. Record the exact source, dependency, temporal, rule-boundary, proof, and fixture contract.
2. Generate disposable candidates through the pinned `axiom-encode` using only the authorized corpus records.
3. Audit candidates without hand-editing and reject any invented statutory semantics, frozen training vendor, NSF risk conclusion, grace period, or IHE-only duty.
4. Restore signer access through `agent-secret`, then apply only unchanged accepted generation.
5. Run proof, generated fixtures, repository gates, and direct Rust adversaries.
6. Record custody hashes, files, fixtures/states, proof, Rust results, and final accept/reject in the output file.
