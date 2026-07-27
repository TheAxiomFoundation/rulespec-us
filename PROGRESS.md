# Progress — § 152(c)(4) claimant tiebreakers

## State

- Branch: `closure/w2-eitc-152-tiebreak`
- Base: `origin/main` at `ecb057ef3`
- Scope: the six named EITC frontier items assigned as 10–15 (global
  classification rows 19–24), governed by 26 U.S.C. § 152(c)(3)–(4)
- Worktree: isolated under `.git/codex-worktrees/w2-eitc-152-tiebreak`
  because the sandbox denied creation at the requested sibling path
- Corpus provisions: `us/statute/26/152/c/3` and
  `us/statute/26/152/c/4`, expression date `2026-07-13`

## Done

- Read `ENCODER-PREAMBLE.md`.
- Read repository `CLAUDE.md`.
- Created the required branch from `origin/main` without disturbing the
  repository's dirty detached checkout.
- Read every assigned classification row before implementation and treated
  the user's six explicit fact names as controlling over shifted global row
  numbers.
- Resolved the governing provisions by exact `citation_path` across every
  statute inventory record and read their retained text and official USLM
  source.
- Read the mandatory sibling modules and companions, the existing
  section 152(c) fragment, the section 32 consumer, and the
  `closure/eitc-2026` context branch.
- Confirmed that reported adjusted gross income is the classification's
  declarable Form 1040 boundary fact. No assigned output requires computing
  AGI through sections 62/61 or invoking section 1402, so no item is
  deferred.
- Confirmed the pinned engine supports complete candidate relations,
  `count_where`, and filtered derived relations; it has no maximum
  aggregator, so strict maxima will be encoded as the absence of an equal-
  or-higher competing row.
- Identified downstream integration work: replace the six former conclusion
  inputs in both companions, refresh section 32's five import proof hashes,
  refresh authoritative manifests, and regenerate the provision index.

## Next

- Encode the six outputs from primitive age, claimant, parent, actual-claim,
  relation-completeness, and reported-AGI facts.
- Add companion boundaries for equal ages, one/two claimants, empty and
  multiple-parent sets, declining parents, parent-AGI equality, and tied
  claimant AGIs.
- Repair the section 32 fixtures, refresh derived artifacts, validate the
  exact pinned toolchain, commit each coherent step, push, and open the draft
  PR.
