# Progress

## State

- Detached rulespec-us worktree created at `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- Worktree path: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-pappg-uei-sam-20260830-codex-193603`.
- `git fetch origin main` was attempted but blocked by sandbox DNS; the local `origin/main` object was verified to equal the required immutable base hash.
- Official corpus provision and Axiom toolchain prerequisites are being audited before generation.

## Done

- Preserved the dirty/diverged primary checkout without modification.
- Created and locked a unique detached worktree under `_axiom-worktrees`.
- Verified a clean worktree, detached HEAD, and exact expected base.
- Located the official NSF provision at `us/guidance/nsf/pappg/24-1/chapter-i/uei-and-sam`.
- Confirmed that origin/main contains no 2 CFR Part 25 RuleSpec base modules; generated imports to such targets will be rejected fail-closed.

## Next

- Finalize the source, actor/linkage, effective-date, and legal-versus-system behavior matrix.
- Run actual `axiom-encode` generation and signed apply using the official corpus and canonical `us/` root.
- Retain only unchanged generated outputs that pass proof/fixture validation and direct Rust cases.
- Write the final report to `OUTPUT.md` and leave the detached worktree clean.
