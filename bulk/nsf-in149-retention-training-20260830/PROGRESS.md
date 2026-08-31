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
- Materialized the ten exact FAQ/statutory primary-source continuation files, matched every continuation body to its normalized corpus body hash, and recorded full custody in `SOURCE_CUSTODY.md`.
- Recorded exact rules-base, encoder, Codex CLI, and Rust-engine custody in `TOOLCHAIN_CUSTODY.md`; no signing secret was accessed.

## Next

1. Complete the two in-flight disposable generations through the pinned `axiom-encode`.
2. Audit candidates without hand-editing and reject any invented statutory semantics, frozen training vendor, NSF risk conclusion, grace period, or IHE-only duty.
3. Restore signer access through `agent-secret`, then apply only unchanged accepted generation.
4. Run proof, generated fixtures, repository gates, and direct Rust adversaries.
5. Record custody hashes, files, fixtures/states, proof, Rust results, and final accept/reject in the output file.
