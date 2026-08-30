# Progress

## State

- Active: source custody and encoder workflow preparation.
- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-pappg-24-1-duplicate-review-20260830-codex-195000`.
- Detached starting base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- The local `origin/main` ref equals the required base. A fresh `git fetch origin main` was attempted on 2026-08-30 but failed because sandbox DNS could not resolve `github.com`; no claim of a successful fresh fetch will be made.
- Source authority is limited to corpus citation `us/guidance/nsf/pappg/24-1/chapter-i/submission-instructions` in the authorized federal-proposal-security corpus worktree. The separate NSF/PAPPG corpus worktree and PR #631 are out of scope.
- Standing-order interpretation: checkpoint commits are local detached commits only. Nothing will be pushed, proposed as a PR, or deployed.
- Final report target: `OUTPUT.md` in this detached worktree.

## Done

- Read the Axiom project, encoder, corpus, and rulespec-us instructions.
- Loaded the `agent-secrets` signing workflow; secret values will not be printed.
- Confirmed the primary rulespec-us checkout is dirty/diverged and left it untouched except for the requested remote fetch attempt and worktree registration.
- Removed one incomplete disposable worktree checkout created during this run after Git interrupted its index initialization; no pre-existing worktree or branch was changed.
- Created and verified the clean detached worktree above at the exact required commit.
- Located the single authorized corpus provision and confirmed its citation label, official NSF URL, source-as-of date, and `2024-05-20` expression date.

## Next

- Record source, toolchain, and custody hashes.
- Discover the exact signing credential name through `agent-secret` without exposing its value.
- Run one signed `axiom-encode encode --apply` against the authorized corpus, canonical `us/` policy root, detached rulespec worktree, and specified Rust engine.
- Inspect the generated artifacts without altering them; verify signature, custody, proof, companion fixtures, and repository guards.
- Compile and run independent direct-Rust adversaries for all required states, including missing facts and pre-effective time.
- Accept only unchanged signed encoder output that passes every requirement; otherwise remove generated policy artifacts and report rejection.
