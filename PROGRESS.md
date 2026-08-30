# Progress

## State

- Detached rulespec-us worktree created at `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- Worktree path: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-pappg-uei-sam-20260830-codex-193603`.
- `git fetch origin main` was attempted but blocked by sandbox DNS; the local `origin/main` object was verified to equal the required immutable base hash.
- Source and base dependency audits are complete; the first real generation attempt failed upstream before producing a candidate, and a retry is next.
- Signed apply is currently blocked because `agent-secret search axiom` reports a missing unlock password for the existing agent-secrets keychain.

## Done

- Preserved the dirty/diverged primary checkout without modification.
- Created and locked a unique detached worktree under `_axiom-worktrees`.
- Verified a clean worktree, detached HEAD, and exact expected base.
- Located the official NSF provision at `us/guidance/nsf/pappg/24-1/chapter-i/uei-and-sam`.
- Confirmed that origin/main contains no 2 CFR Part 25 RuleSpec base modules; generated imports to such targets will be rejected fail-closed.
- Verified PAPPG effective date `2024-05-20`, source-as-of date `2026-08-30`, normalized body SHA-256 `c64a40f7048f038cc5e9a281c4d67d252923ed3c12992a32c5700a9e48b6bcb6`, and official snapshot SHA-256 `a8f98d21d424ab919458571a268b50c77f7c42164fecfb4bdbe3a94c64197d29`.
- Chose one self-contained generated target, `us:policies/nsf/pappg/24-1/uei-and-sam`, because the PAPPG provision directly states the requested NSF-specific duties and behavior.
- Fixed the actor matrix: lead/proposing organization and each named subrecipient require distinct own-entity evidence; unnamed or merely potential subrecipients are out of this adapter's named-subrecipient scope; the named-subrecipient SAM treatment cannot exempt the lead.
- Fixed the output separation: applicant-side UEI/SAM/Research.gov duties remain distinct from NSF system submission and approval gates.
- Ran actual `axiom-encode` with Codex GPT-5.5, the official corpus, real Rust engine path, canonical `us/` root, isolated DB/log paths, and acceptance context. Run `82a574a0` failed with `stream disconnected before completion` at the Codex responses endpoint, with zero tokens and no generated RuleSpec candidate.

## Next

- Retry actual `axiom-encode` generation using the same pinned inputs and non-proof acceptance brief.
- Restore `agent-secret` access, then rerun as a signed apply without altering generated RuleSpec or fixtures.
- Retain only unchanged generated outputs that pass proof/fixture validation and direct Rust cases.
- Write the final report to `OUTPUT.md` and leave the detached worktree clean.
