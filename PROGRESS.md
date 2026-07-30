# PR #1179 Repair Re-review Progress

## State

- Review status: in progress.
- Frozen repair head:
  `f2bdb8e15182fe8e312b34b36217d5623a411161`.
- Prior reviewed head:
  `4ced8fb7065311338ea732cab0a26105e750c40f`.
- Review scope: the five claimed repairs and containment only.
- Review branch: `review/pr-1179-repair-f2bdb8e`.
- Disposable review worktree:
  `.git/review-worktrees/pr-1179-repair-f2bdb8e`.
- Canonical exact-head archive planned at:
  `.git/review-worktrees/pr-1179-repair-f2bdb8e-canonical/rulespec-us`.
- Required corpus checkout:
  `/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`.
- Final report: `REVIEW.md`.

## Done

- Read the GitNexus PR-review skill and limited its workflow to the
  user-prescribed repair and containment scope.
- Read the predecessor's `REVIEW.md` and captured its five exact blockers.
- Confirmed the requested head resolves locally to the full frozen commit.
- Inspected the primary checkout without modifying its unrelated dirty state.
- Created this review-only local branch and disposable worktree from the
  frozen repair head. No PR branch, remote, or GitHub write was made.
- Confirmed the prior reviewed head is an ancestor of the repair head with
  exactly ten intervening commits.
- Froze the final delta to the compose, companion, relation-schema test,
  reverse index, and composition manifest; `git diff --check` is clean.
- Audited the intervening commit path set: the same four non-manifest repair
  files plus `PROGRESS.md`; the progress ledger is deleted before the final
  manifest-only signature commit.
- Confirmed the required corpus checkout is clean and detached at exact pin
  `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Created the canonical-basename exact-head archive at the planned path. It
  contains neither `PROGRESS.md` nor `REVIEW.md`; the compose blob is
  `507fa3179ab04da5d2562af6fb97d4fb60b86e85` with SHA-256
  `812f15410e4266a6118b9929399dbe4ae3f654eb77ad0e7bb77b15ee8c50de8f`.
- Confirmed the current section 165(d) proof excerpt is a 302-byte exact
  substring occurring once in the resolver-selected pinned provision and
  states both the 90-percent loss limit and wagering-gains ceiling.
- Confirmed the compose's rationale, itemizer branch, and completed input
  contract all define the wagering amount as after both current-law limits,
  rather than merely updating the excerpt.
- Confirmed the final is sourced to sections 61, 62, and 63(a)-(b), with
  byte-exact definition atoms for the gross-income, adjusted-gross-income,
  itemizer, and nonitemizer bridge. All 13 compose source excerpts occur
  exactly once in their resolver-selected pinned provision bodies.
- Independently recomputed the section 931 diagnostic: `75,000 + 10,000 =
  85,000` MAGI; `6,000 - 0.06 * 10,000 = 5,400` senior deduction;
  `18,150 + 5,400 = 23,550` deductions; and `75,000 - 23,550 = 51,450`
  taxable income. Every asserted intermediate and final matches.
- Confirmed the static registry pins the section 151 exemption and senior
  relations as `(TaxUnit, Person)` and the section 170(p) relation as
  `(TaxUnit, Payment)`.
- Re-ran three isolated exact two-line argument-order mutations. Reversing
  exemption, senior, or charity independently yields return code 1 and one
  targeted schema-test failure; the pristine baseline passes.
- Ran the byte-exact predecessor companion blob `727d57e5...` over the
  repaired compose blob `507fa317...`. Its sole failing case is
  `ti-entity-zeroes-standard`: the repaired domain returns `not_holds` and
  taxable income returns zero instead of the predecessor's expected
  `holds`/`100000`.
- Confirmed the repaired contradictory regression has the exact same period
  and 85-key resolved input map as the predecessor fixture, including both
  `taxpayer_is_individual=true` and the nonindividual entity fact `true`.

## Next

- Run the companion, pinned validation, proof, ledger, manifest, and
  containment gates.
- Write and commit the evidence-backed verdict to `REVIEW.md`.
