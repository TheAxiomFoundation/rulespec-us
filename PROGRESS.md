# PR #1177 Blind Adversarial Review Progress

## State

- Review status: complete.
- Verdict: `REQUEST-CHANGES` for two binding conformance defects.
- Review branch: `review/pr-1177-f4cc1b8`.
- Disposable worktree: `.git/review-worktrees/pr-1177-f4cc1b8`.
- GitHub-verified PR head:
  `f4cc1b88d1efd8dcca25058695dc1735c0fbb3de`.
- GitHub-verified head branch: `fed-parity/chunk1-salt-itemized`.
- GitHub-verified base ref/tip:
  `main` at `54004d3c69beda3c2363f9001ca6e37012348bc2`.
- Immutable PR range:
  `54004d3c69beda3c2363f9001ca6e37012348bc2..f4cc1b88d1efd8dcca25058695dc1735c0fbb3de`.
- Required corpus checkout:
  `/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`.
- Binding plan:
  `/Users/maxghenis/TheAxiomFoundation/ops/fed-parity-campaign/SPINE-PLAN.md`.
- Canonical exact-head archive:
  `.git/review-worktrees/pr-1177-canonical/rulespec-us`.
- Exact pinned engine build:
  `/private/tmp/pr1177-engine-ffd82132/target/release/axiom-rules-engine`.
- Final report: `REVIEW.md`.

## Done

- Loaded the GitNexus PR-review workflow.
- Preserved the dirty primary checkout and the author's existing branch
  worktree.
- Confirmed the local author branch and remote-tracking ref both resolve to
  `f4cc1b88d1efd8dcca25058695dc1735c0fbb3de`.
- Created this disposable local review worktree and review-only branch from
  that candidate head. No PR-branch, remote, or GitHub write was made.
- Captured the eight-file candidate diff against local `origin/main`.
- Verified through the read-only GitHub connector that PR #1177 is open,
  non-draft, mergeable, targets `main` at `54004d3c...`, and has exact head
  `f4cc1b88...` on `fed-parity/chunk1-salt-itemized`.
- Confirmed GitHub's eight changed filenames exactly match the local immutable
  range; the head is ten commits ahead and zero behind its merge base.
- Recorded that shell `gh pr view` could not connect to `api.github.com`; the
  read-only GitHub connector supplied the live metadata instead.
- Confirmed the required corpus checkout is clean and detached at exact full
  pin `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Read binding plan §5, §6.1, §6.2, §9 Chunk 1, and its commit discipline.
- Created the required canonical-basename `git archive` root from the exact PR
  head and verified an archive module's SHA-256 against the commit bytes.
- Rebuilt `axiom-rules-engine` offline from exact toolchain pin
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`.
- Ran the pinned companion runner from the canonical archive with that engine:
  2 files, 53 cases, 2 compiled programs, zero failures.
- Ran pinned-encoder validation against the required corpus checkout from the
  canonical archive: both modules report `ci_pass=true`, `all_passed=true`,
  and zero errors.
- Attempted the GitNexus graph workflow in a separate exact-head worktree.
  GitNexus reports the repository unindexed; online `npx` then hung on the
  restricted network, while offline `npx` reported the package was not cached.
- Confirmed all 16 prescribed SALT cases and all 17 prescribed itemized cases
  are present with exact plan inputs and statutory expected values. Independent
  rational recomputation found zero arithmetic mismatches, including
  `40,399.70`, `5,950`, and every section 68 threshold/lesser-of case.
- Confirmed the exact 8/3 direct import lists; no local section 68
  rate/threshold/lesser-of formula; imported section 67(h) consistency;
  negative-component guards; guarded public outputs; and verbatim section 165
  atoms for the positive casualty case.
- Found a binding relation-order test defect. In a separate exact-head archive,
  swapping only the SALT relation arguments from `(TaxUnit, Person)` to
  `(Person, TaxUnit)` still passed the SALT companion 25/25 and the combined
  companion set 53/53. Pinned validation also accepted the mutated SALT module.
  The named positive relation witness is therefore not the mutation test
  required by plan §5 and §10.
- Found a binding proof-atom defect at
  `salt_deduction_pipeline.yaml:250`. Its section 164 excerpt omits the corpus
  row's exact `the term “modified adjusted gross income” means` wording.
  Programmatic exact-Unicode comparison found 12/13 SALT excerpts unique and
  one absent; all 14 itemized excerpts are unique. The pinned structural proof
  validator still reports 24/24 and 23/23 because it does not compare excerpt
  text.
- Audited the ten-module merged closure: 80 declarations are unique, all 13
  import selections and 24 proof imports resolve, entities agree, and the sole
  relation predicate has no collision. Neither `63/c.yaml` nor the Rev. Proc.
  standard-deduction module is present.
- Audited both manifests: applied-file sets are disjoint and exactly the four
  protected pipeline/companion YAML files; hashes match exact-head and
  signature-parent bytes; content commits are ancestors; the signature commit
  changes only the two manifests; and both exceptions are exactly
  `composition`. The local HMAC key is unavailable, but GitHub's exact-head
  generated-guard job succeeded.
- Regenerated the reverse index: it is byte-current at 4,247 provisions, 5,105
  edges, and 4,490 modules. The pending ledger is sorted/unique, has
  `ceiling == count == 2148`, and is the exact field-preserving union of both
  merge parents.
- Confirmed the PR diff is exactly the intended eight files with no workflow,
  toolchain, CODEOWNERS, lockfile, or unrelated change.
- Ran repository layout, reverse-index, and manifest tests: 18 passed with one
  pre-existing unmanifested-module warning.
- Recorded environment-only limitations and fallbacks: the axiom-encode virtual
  environment lacks pytest, so an existing pytest/PyYAML environment ran the
  repository tests; shell GitHub DNS was blocked, so the read-only connector
  verified live metadata; GitNexus analysis parsed the snapshot but sandbox
  policy denied its global registry write at
  `/Users/maxghenis/.gitnexus/registry.json`.
- Wrote and committed the evidence-backed verdict to `REVIEW.md` in commit
  `b90a86cac`.

## Next

- Author after review: add a mutation-killing asymmetric relation-order
  diagnostic, correct the non-verbatim section 164 excerpt, then revalidate and
  regenerate/re-sign every affected manifest after the content commits.
- Reviewer after revision: freeze the new head and rerun the full canonical
  archive, corpus, mutation, closure, manifest, reverse-index, and pending-ledger
  gates.
