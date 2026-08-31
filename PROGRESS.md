# Progress

## State

- Unique locked detached `rulespec-us` worktree initialized at `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-pappg-uei-sam-20260830-codex-01a05519-195736`.
- A fresh `git fetch --no-tags origin main` was attempted on 2026-08-30 but the sandbox could not resolve `github.com`; the existing `origin/main` ref and commit object exactly match the required immutable hash.
- The pre-existing NSF UEI/SAM worktree and axiom-corpus PR #631 remain untouched.
- Source, dependency, generation, signed apply, and real-Rust proof work are pending.

## Done

- Read the applicable Axiom and repository instructions.
- Verified that the primary checkout is dirty and diverged and left it unchanged.
- Verified the remote URL, detached HEAD, exact base object, clean materialized checkout, and worktree lock.
- Selected `OUTPUT.md` as the committed final-report file, matching the task-family convention.

## Next

- Audit the official NSF guidance provision, metadata, source/effective dates, hashes, and actor/linkage facts.
- Confirm whether required 2 CFR Part 25 base modules exist at the exact base; fail closed if they do not.
- Run actual `axiom-encode` with the official corpus, canonical `us/` root, signed apply via `agent-secret`, and the real Rust engine.
- Retain only unchanged generated artifacts that satisfy all requested proof, fixture, and direct Rust cases.
- Commit `OUTPUT.md`, finalize this file, and leave the detached worktree clean without pushing or opening a PR.
