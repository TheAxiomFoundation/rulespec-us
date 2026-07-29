# PR #1176 repair-round re-review progress

## State

Re-review is complete on the isolated review branch pinned to exact live PR
head `686d413cfe15410dc160010f7863096c8c20ef48`. Final verdict:
**REQUEST-CHANGES**.

The retired relation is correctly rejected, but the replacement private
derived relation remains caller-populable. The pinned engine unions
caller-supplied rows with derived rows, so an injected eligible member can
still confer MCE when the federal membership relation contains only an
excluded member.

The finding-first final report is committed at `REVIEW.md`. No PR-branch,
remote, corpus, author-worktree, or GitHub writes were made.

## Done

- Read the GitNexus PR-review skill and established the review checklist.
- Confirmed the primary checkout and source branch worktree contain unrelated
  user state and left both untouched.
- Queried PR #1176 read-only, resolved its exact head/branch/base, and created
  this disposable worktree under `.git/review-worktrees/`.
- Verified both predecessor reproducer SHA-256 values exactly. Replaying each
  byte-for-byte against the repaired module exits nonzero with 24 errors
  rejecting the retired relation as undeclared.
- Ran both repaired companions from an exact-head canonical-basename archive:
  47/47 cases and 2/2 compiled programs passed.
- Ran pinned `validate --skip-reviewers`: both modules passed with
  `ci_pass=true`, `all_passed=true`, and zero findings.
- Ran proof validation: 29/29 MCE atoms and 9/9 benefit atoms passed.
- Reproduced mutation sensitivity (`eligible-member > 0` to `< 0`): 13
  assertion failures across exactly three MCE-dependent benefit cases.
  Restored source SHA-256 `e3f0cba2...` and reran 47/47 green.
- Composed with pinned `axiom-compose` and compiled with pinned engine:
  328 derived outputs, 100 parameters, and three relations.
- Passed the repository layout and ProgramSpec contract tests, 12/12.
- Programmatically rechecked every excerpt against every matching retained row
  in the clean corpus pin `8af59216`: 38/38 atoms, 59/59 strict UTF-8
  atom-row comparisons, zero mismatches. `Broad- Based` matches exactly.
- Audited all three re-signed manifests. All five applied-file hashes match
  bytes already present at parent `79ad71497`; supersession chains match; the
  ProgramSpec citation is exactly `programs/us-ca/snap/fy-2026`.
- Verified the disposable encoder chain
  `3869d66d -> 0114ccb3 -> 7121774c` and the merged encode#1322 routing
  regression (`programs/us-sc/snap/fy-2026`), which passed 1/1.
- Constructed an independent canonical-projection injection probe. The harness
  accepts direct rows for
  `#relation.calfresh_mce_canonical_member_of_household`; adding an eligible
  row changed the only-excluded-member result from `not_holds` to `holds`.
  Engine source confirms direct rows and derived rows are unioned.
- Confirmed the review worktree is clean after moving mutation and injection
  evidence to explicit paths under `/private/tmp`.
- Confirmed merged axiom-oracles #424 adds exactly 17 rule-output rows and
  references neither the retired nor canonical relation name.
- Compared compiled original PR head `8d1f31d50` with repaired target:
  zero derived/parameter ID additions or removals; exactly two derived
  definitions changed; the sole relation replacement is the old CA input for
  the new derived relation.
- Confirmed the live GitHub diff and local `origin/main...target` diff contain
  the same 11 intended paths and no foreign/toolchain/workflow changes.
- Performed the final live head-drift check: PR #1176 remained open,
  mergeable, non-draft, and exactly at `686d413cf`.
- Wrote and committed the final report to `REVIEW.md`.

## Next

- Author: make derived/private relations invalid dataset inputs, or replace
  the alias with a relation whose population cannot diverge from the federal
  state-plan relation.
- Add a regression proving direct input under
  `#relation.calfresh_mce_canonical_member_of_household` is rejected.
- Re-sign affected manifests after that executable repair, then request
  another exact-head review.
