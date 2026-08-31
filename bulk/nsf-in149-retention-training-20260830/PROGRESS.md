# Progress

## State

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-in149-20260830-47290`
- Mode: detached HEAD
- Verified base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Scope: NSF Important Notice 149 Items 1–2 supporting-document retention/request and research-security-training certification adapters only; IHE-only RECR/42 U.S.C. §§ 19039–19040 excluded
- Status: source/base/toolchain and encoding-contract audit complete; no generated adapter accepted
- Final report output: `bulk/nsf-in149-retention-training-20260830/OUTPUT.md`

## Done

- Attempted a fresh `git fetch origin main`; sandbox DNS could not resolve `github.com`.
- Verified the existing local `origin/main` and commit object exactly match the required SHA.
- Created this unique detached worktree without modifying any existing branch or axiom-corpus PR #631.
- Loaded the Axiom repository instructions and the `agent-secrets` custody workflow.
- Confirmed the dedicated `agent-secret` keychain exists but its login-keychain unlock-password item is missing; signed apply currently fails closed.
- Completed independent audits of the seven authorized guidance records, the pinned encoder, generated-only precedents, and the actual Rust engine.
- Verified the guidance JSONL and exact record bodies, including that the FAQ records live below `149-implementation-faq`.
- Verified the required base has no section 19233 or section 19234 RuleSpec module and recorded explicit fail-closed prerequisite boundaries.
- Recorded two target adapters, atomic duties, temporal treatment, proof rules, and the full generated-fixture acceptance matrix in `ENCODING_BRIEF.md`.
- Confirmed the Rust runtime has Date comparisons but no calendar-month subtraction; the brief therefore requires actual dates plus an explicit external twelve-month-window-start date and forbids a 365/366-day substitute.

## Next

1. Materialize exact primary-source continuation files from the authorized corpus records and verify their body hashes.
2. Generate disposable candidates through the pinned `axiom-encode`.
3. Audit candidates without hand-editing and reject any invented statutory semantics, frozen training vendor, NSF risk conclusion, grace period, or IHE-only duty.
4. Restore signer access through `agent-secret`, then apply only unchanged accepted generation.
5. Run proof, generated fixtures, repository gates, and direct Rust adversaries.
6. Record custody hashes, files, fixtures/states, proof, Rust results, and final accept/reject in the output file.
