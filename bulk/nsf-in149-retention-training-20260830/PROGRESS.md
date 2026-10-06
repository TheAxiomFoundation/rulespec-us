# Progress

## State

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-in149-20260830-47290`
- Mode: detached HEAD
- Verified base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Scope: NSF Important Notice 149 Items 1–2 supporting-document retention/request and research-security-training certification adapters only; IHE-only RECR/42 U.S.C. §§ 19039–19040 excluded
- Status: all completed encoder attempts failed before model output; Item 1 A2 was interrupted after context staging; fresh signed-apply A3 attempts failed at transport before signing; no generated adapter accepted
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
- Ran one isolated, unsigned, non-applying encoder attempt for each target. Both exhausted transport reconnects before model output; neither emitted a RuleSpec or test.
- Recorded the failed run IDs, database outcomes, context behavior, and artifact hashes in `GENERATION_CUSTODY.md`.
- Recovered the incomplete A2 state: Item 2 finished as a second zero-output
  transport failure, while Item 1 stopped after context staging with no run,
  trace, database, output, or live process.
- Ran fresh signed-apply A3 attempts with the inherited signing environment.
  Both failed before model output with `apply_blocked_generation`; the signing
  step was never reached and the key was never inspected.
- Confirmed the pinned encoder has no supported replay, offline resume, or
  apply-existing-generated-output route. Manual attestation and trace injection
  would break the required generated-output custody and were not used.
- Confirmed the canonical `us/` tree still contains no target module, test, or
  signed manifest. No generated fixtures, proof run, or direct Rust case exists.
- Recorded the final reject/block disposition in `OUTPUT.md`.

## Next

1. Restore outbound Codex transport for the pinned encoder without changing its
   provenance or model path.
2. Start fresh roots rather than overwriting or resuming A1-A3 evidence.
3. Audit any candidate without hand-editing and reject invented statutory
   semantics, a frozen training vendor, an NSF risk conclusion, a grace period,
   or an IHE-only duty.
4. Accept only an unchanged signed apply, then run proof, generated fixtures,
   repository gates, and direct Rust adversaries.
