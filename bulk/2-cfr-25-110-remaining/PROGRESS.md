# 2 CFR 25.110 atomic exceptions progress

## State

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-25-110-exc-20260830-codex-1948`
- Base: detached `d58cc0ce67ad891fde4c9061c86a2091bfdd524f` (the required expected `origin/main` commit)
- Fetch: attempted on 2026-08-30, but sandbox DNS blocked `github.com`; the locally tracked `origin/main` matched the required hash exactly.
- Toolchain: official corpus `129dae01c6f7a4787bc7678d4a97a478f3934d9f`, encoder `3869d66d009f52258be35901edbef370e65a399c` (0.2.1200), and Rust engine `ffd8213271947b0189a9dd61a055c1e0e78908a0`.
- Scope: separate generated-only attempts for 2 CFR 25.110(a)(2)(ii) and (iv), with (i) attempted only if all agency judgments remain external facts.
- Excluded: accepted paragraph (iii), OMB class exceptions, generic-identifier reporting, pushes, pull requests, and production actions.
- Output report: `bulk/2-cfr-25-110-remaining/FINAL_REPORT.md` in this worktree.
- Blockers: `agent-secret` cannot unlock its existing dedicated keychain because the login-keychain unlock record is missing; the first Codex generation stream also disconnected before producing output.

## Done

- Read the applicable Axiom project, encoder, corpus, rules-repository, and repository-structure instructions.
- Loaded the approved `agent-secret` workflow and identified service `agent/axiom-encode-apply-signing-key`, account `axiom-foundation`, without exposing credentials.
- Verified the official § 25.110 provision, exact actor/transaction/scope distinctions, source hashes, prior rejected runs, and untouched accepted paragraph (iii) custody.
- Created a unique clean detached worktree at the required immutable base.
- Created three paragraph-only generation briefs outside the rules repository and recorded their hashes.
- Attempted paragraph (ii) independently as run `58a75d26`; Codex disconnected before generation, leaving only an isolated repair manifest and trace and no worktree changes.
- Relocated this ledger under the repository-approved `bulk/` root after verifying `.axiom/repository-structure.yaml`.

## Next

- Retry paragraph (ii) in a fresh output root, then independently run paragraphs (iv) and conditionally (i).
- If `agent-secret` access is restored, rerun any acceptable paragraph through signed `axiom-encode encode --apply` against the canonical `us/` root.
- Retain only byte-identical generated/applied output that passes proof, adversarial fixtures, signed guard, and direct Rust execution; restore rejected target paths narrowly.
- Write and commit the final evidence report under `bulk/2-cfr-25-110-remaining/FINAL_REPORT.md`.
