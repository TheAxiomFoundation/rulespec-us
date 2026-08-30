# Progress

## State

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-in149-retention-training-20260830-codex-193722b`
- Mode: detached HEAD
- Verified base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Scope: NSF Important Notice 149 Items 1–2 supporting-document and research-security-training certification adapters only; IHE-only RECR/42 U.S.C. §§ 19039–19040 excluded
- Status: source/base audit complete; disposable generation is next, but signed apply remains blocked
- Final report output: `OUTPUT.md`

## Done

- Attempted a fresh `git fetch origin main`; sandbox DNS could not resolve `github.com`.
- Verified the existing local `origin/main` and commit object exactly match the user-supplied expected SHA.
- Created this uniquely named detached worktree without modifying any branch, accepted worktree, or axiom-corpus PR #631.
- Loaded the Axiom repository instructions and the `agent-secrets` custody workflow.
- Verified the supplied corpus worktree is clean and contains the authorized Item 1, Item 2, and FAQ records, plus the official § 19233 and § 19234 records.
- Confirmed the signing key must be obtained through `agent-secret`; `agent-secret search axiom` currently fails because the dedicated keychain has no unlock password configured.
- Verified the required `rulespec-us` base contains no § 19233 module, no § 19234 module, and no existing NSF policy tree. Any candidate must therefore use explicit external statutory-prerequisite gates and fail closed when they are absent.
- Verified the authorized guidance records use `149-research-security/{1,2}` and `149-implementation-faq/question-{1,5,6,7,8}`; no substantive grace period applies to these scoped items.
- Confirmed Item 1 retention is an organization duty for both proposers and recipients, production requires an actual NSF request, and review of requested documents is a separate conditioned judgment.
- Confirmed Item 2 requires separate same-proposal certifications by each senior/key person and by the AOR for all senior/key personnel, with qualifying training completed within the preceding 12 months; IHE-only RECR certification is excluded.

## Next

1. Generate a disposable two-item adapter candidate with the pinned `axiom-encode`, authorized corpus context, canonical `us/` root, and pinned Rust engine.
2. Audit generated RuleSpec/proof/fixtures without hand-editing and reject any invented statutory semantics, frozen training vendor, risk conclusion, grace period, or IHE-only duty.
3. Resolve the `agent-secret` signing-key blocker before any live `axiom-encode --apply` operation.
4. Apply only the unchanged candidate, then run the generated companion fixtures and required direct-Rust adversarial matrix.
5. Retain generated RuleSpec only if every gate passes; otherwise reject and leave only ledger/report files.
6. Record custody hashes, commands, files, fixtures, proof, Rust results, and final accept/reject in `OUTPUT.md`.
