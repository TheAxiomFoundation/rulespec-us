# EITC §152(c) Residency and Parental Tiebreak Progress

## State

- Branch: `closure/w1-eitc-152-residency`, based on `origin/main`.
- Scope: EITC frontier items 4, 8, and 9.
- Status: repository and closure instructions read; statutory and encoding discovery is next.
- Worktree note: the mandated external path was rejected by the filesystem sandbox, so this branch is isolated at `.git/codex-worktrees/w1-eitc-152-residency`.

## Done

- Read `ENCODER-PREAMBLE.md` and the repository `CLAUDE.md`.
- Confirmed the frozen-program, toolchain, CI, CODEOWNERS, and SNAP exclusions.
- Created the requested branch from `origin/main` and attached it to an isolated worktree.

## Next

- Read the assigned frontier-classification rows before implementation.
- Resolve §152(c)(1)(B) and §152(c)(4)(B) by `citation_path` across every inventory record.
- Inspect the `closure/eitc-2026` program/grid and sibling RuleSpec encodings.
- Trace dependencies, encode each item, and add statutory-boundary tests.
