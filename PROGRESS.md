# Progress

## State

- Active: running fresh unsigned preflight generations for A and B before any unchanged signed apply.
- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/42usc19234-a1ab-certifications-20260830-codex-r1/rulespec-us`.
- Base: detached `d58cc0ce67ad891fde4c9061c86a2091bfdd524f` from local `origin/main`.
- Acceptance posture: reject unless unchanged signed generated output has complete parent-plus-child and enactment-date proof, adversarial fixtures, and direct checks in the required Rust engine.
- Blocker: `agent-secret` cannot access the signing service because its stored unlock password is missing; direct keychain fallback is prohibited.

## Done

- Read the applicable global, credential-handling, and `rulespec-us` instructions.
- Attempted a fresh `git fetch --prune origin main`; DNS resolution for `github.com` was unavailable in the shell.
- Verified local `origin/main` is the user-expected `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- Created and verified this unique clean detached worktree without moving an accepted branch.
- Began independent read-only audits of the official USC corpus, encoder/signing workflow, and real Rust runtime.
- Confirmed the normalized A and B leaf records omit the inherited chapeau and enactment-date metadata, so child-only proof is unacceptable.
- Completed source custody: corpus `129dae01c6f7a4787bc7678d4a97a478f3934d9f`; provisions JSONL SHA-256 `566a513343f88d5a4944c591ef86464dcd27ea8dce8a4dd730f05efec4f69aa4`; OLRC ZIP SHA-256 `31929c28f117362ac8788607242795769b05ed7726f07e4ed3b1786f39655ce7`; extracted XML SHA-256 `b72955590abe55bdbd1ce5d13c5293955a82add9c84fad92c1674ec469e86624`.
- Verified encoder `0.2.1200` at `3869d66d009f52258be35901edbef370e65a399c` and required Rust engine `ffd8213271947b0189a9dd61a055c1e0e78908a0` with binary SHA-256 `ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb`.
- Rejected prior runs `5e164202` and `91f8b7e4`: both had child-only proof, opaque recency, and duplicate deadline-date versions; B also collapsed employee/linkage content into one aggregate fact.
- Prepared hashed parent/A primary-source continuations, enactment audit context, and separate A/B encoding briefs outside the repository. RuleSpec and fixtures will remain generator-only.

## Next

- Run fresh A and B preflight generations with explicit inherited chapeau and enactment-date provenance.
- Review generated output without manual alteration; reject and restore clean if any mandatory distinction or proof is absent.
- Restore `agent-secret` access to `agent/axiom-encode-apply-signing-key` without exposing the key.
- If accepted, rerun signed apply, verify unchanged output custody, run generated fixtures and direct Rust adversaries, and record hashes/results.
- Write and commit the final report to `OUTPUT.md`; do not push, open a PR, or deploy.
