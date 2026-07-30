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
- Built the exact pinned engine commit `ffd821327...` from a fresh archive
  with Cargo offline and ran the exact pinned encoder `3869d66d...` from the
  canonical root. The companion passes 28/28 with one compiled program and
  zero failures.
- Pinned validation against corpus `8af592162...` reports
  `ci_pass=true`, `all_passed=true`, and zero errors.
- Structural proof validation passes all 37 atoms with zero issues. The
  strict money-atom pass reports zero obligations and zero missing atoms.
- Reverse-index check mode is byte-current at 4,249 provisions, 5,120 edges,
  and 4,491 modules.
- Focused repository, manifest, index, and relation-schema gates pass 19/19.
  The sole warning reports the same 19 pre-existing unmanifested modules and
  is explicitly report-only.
- Recomputed the pending ledger from local base `ae64af274...`: base
  ceiling/count 2,148; head ceiling/count 2,151; both sorted and unique; zero
  lost or changed base records; exactly the three taxable-pipeline additions.
  The ledger blob is unchanged from the prior reviewed head.
- Audited the manifest's exact two applied hashes. They match canonical disk,
  content ancestor `b47607e...`, signature parent `f0864dc...`, and head.
  The requested head changes only the manifest, uses the exact pinned encoder,
  carries only the `composition` exception, and supersedes the parent manifest
  hash exactly.
- Confirmed the repair range is ten linear commits with zero merges. Before
  the drop, its path set is exactly the five repair-era paths: compose,
  companion, relation test, reverse index, and `PROGRESS.md`; `f0864dc...`
  deletes only the ledger and `f2bdb8e...` changes only the manifest.
  The net five-file delta is the four substantive repair files plus manifest.
- Confirmed `git diff --check` is clean and the canonical root is byte-equal
  to a fresh `git archive` of the frozen head.
- The manifest HMAC key is absent, so the signature value could not be
  cryptographically recomputed. Its algorithm/key envelope and all non-secret
  content, ancestor, supersession, and repository manifest gates pass.
- Recorded tooling disclosures: the default `pytest` shim points to a missing
  interpreter and system Python lacks PyYAML, so all authoritative Python
  gates were rerun successfully through the pinned encoder virtual
  environment. One parallel run created only generated pytest caches in the
  canonical archive; an explicit recursive cleanup was sandbox-blocked, so
  the known cache files were removed through `apply_patch`/`unlink`, and the
  fresh-archive comparison then passed. Direct `apply_patch` into a mutation
  tree under `/private/tmp` was also sandbox-rejected; the reviewer used an
  in-workspace staging patch and copied it into the isolated tree.

## Next

- Write and commit the evidence-backed verdict to `REVIEW.md`.
