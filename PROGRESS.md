# Progress — § 152(c)(4) claimant tiebreakers

## State

- Branch: `closure/w2-eitc-152-tiebreak`
- Base: `origin/main` at `ecb057ef3`
- Scope: EITC frontier items 10–15 for 26 U.S.C. § 152(c)(4)
- Worktree: isolated under `.git/codex-worktrees/w2-eitc-152-tiebreak`
  because the sandbox denied creation at the requested sibling path

## Done

- Read `ENCODER-PREAMBLE.md`.
- Read repository `CLAUDE.md`.
- Created the required branch from `origin/main` without disturbing the
  repository's dirty detached checkout.

## Next

- Read classification rows 10–15 before implementation.
- Resolve § 152(c)(4) by `citation_path` across the corpus inventory.
- Inspect `closure/eitc-2026`, sibling statute encodings, and validation tools.
- Encode only assigned tiebreakers, add statutory-boundary tests, validate,
  update this file, commit each coherent step, push, and open the draft PR.
