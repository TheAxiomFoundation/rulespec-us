# Progress

## State

- Active Axiom-native encoding of the NSF Important Notice 149 and implementation FAQ MFTRP certification adapter.
- Unique worktree is detached and clean at the required base object `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- A live `git fetch origin main` was attempted on 2026-08-30, but the sandbox could not resolve `github.com`; the local `origin/main` ref exactly matches the required object. Fetch will be retried before final acceptance.
- No existing branch, accepted candidate, or axiom-corpus PR #631 worktree has been modified.
- Official-source custody, atomic-boundary, encoder, and Rust workflow inspection is complete.
- No RuleSpec artifact has been generated or accepted yet.
- Signed apply is blocked before secret lookup because `agent-secret` cannot find the existing keychain's stored unlock-password record. No secret value was read and no alternate credential path was used.

## Done

- Read the global and repository Axiom instructions and the `agent-secrets` signing workflow.
- Created and verified a unique detached `rulespec-us` worktree at the requested base.
- Audited only IN-149 items 3 and 4 and FAQ questions 3, 5, 6, 7, and 8 in the supplied official corpus worktree.
- Confirmed the selected records require separate current-membership, senior/key individual, AOR organizational, and annual PI/co-PI rules.
- Confirmed proposal certifications are project-linked, annual certification requires an active NSF award made on or after 2024-05-20, and the selected records do not establish a precise earlier proposal-certification effective date.
- Confirmed no canonical `us/statutes/42/19232` module exists at the required base, so the adapter must expose the incorporated statutory responsibilities as external prerequisites rather than import them.
- Recorded the source-faithful runtime, temporal, proof, and adversary contract in `bulk/ENCODING_BRIEF.md` and prepared exactly six official-text continuation inputs for item 4 and FAQ questions 3, 5, 6, 7, and 8.

## Next

- Restore access to `agent/axiom-encode-apply-signing-key` through `agent-secret`; do not bypass the helper or begin a paid generation/apply run while signed retention is impossible.
- Use the pinned `axiom-encode` with the canonical `us/` root and `agent-secret`-supplied signing material to generate and signed-apply the standard artifact bundle without manual repair.
- Run strict proof validation, all requested generated fixtures, and direct adversaries through the real Rust `axiom-rules-engine`.
- Retain only unchanged signed output with complete evidence; otherwise restore the worktree to a clean accepted state.
- Write exact hashes, files, fixture states, proof results, Rust outcomes, and atomic accept/reject findings to `bulk/FINAL_REPORT.md`.
