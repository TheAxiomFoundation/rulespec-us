# Progress — § 152(c)(4) claimant tiebreakers

## State

- Branch: `closure/w2-eitc-152-tiebreak`
- Base: `origin/main` at `ecb057ef3`
- Scope: the six named EITC frontier items assigned as 10–15 (global
  classification rows 19–24), governed by 26 U.S.C. § 152(c)(3)–(4)
- Worktree: isolated under
  `.git/codex-worktrees/rulespec-us-w2-eitc-152-tiebreak` because the sandbox
  denied creation at the requested sibling path. The `rulespec-us-*`
  basename is required for canonical module IDs in the pinned validator.
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
- Identified downstream integration work: replace the former conclusion
  inputs in both companions, preserve section 32's statutory disregard of
  the section 152(c)(1)(D) support test, refresh import proof hashes and
  authoritative manifests, and regenerate the provision index.
- Encoded all six assigned outputs in `us/statutes/26/152/c.yaml`.
- Added a complete other-taxpayer relation with row-local qualifying-child,
  parent, actual-claim, and copied-AGI facts. Strict maxima are implemented by
  rejecting any equal-or-higher competing row.
- Added a private support-omitted claimant surface so section 32 can apply its
  paragraph-(1)(D) disregard without changing generic section 152 results.
- Added 20 companion cases covering the assigned statutory boundaries,
  disabled-child and strict-age edges, eligible nonclaimants, ineligible
  claimants and parents, AGI ties, fail-closed relation completeness, and
  existing section 152(c) behavior.
- Confirmed the section 152(c) companion passes all 20 cases in the pinned
  runtime; module validation and proof validation pass.
- Integrated the tiebreaker into section 32 through private, support-omitted
  eligibility rules, matching section 32(c)(3)(A)'s express disregard of
  section 152(c)(1)(D).
- Repaired section 32's stale earned-income companion inputs, replaced the
  former direct tiebreaker conclusions with statutory inputs, and added a
  support-disregard integration case. All five section 32 cases pass in the
  pinned runtime; module validation and proof validation pass.

## Next

- Refresh authoritative manifests and the provision index.
- Run focused and repository-wide validation, update this file, commit each
  coherent step, push, and open the draft PR.
