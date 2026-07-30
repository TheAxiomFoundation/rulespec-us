# PR #1180 Repair Re-review Progress

## State

- Review status: in progress.
- Frozen candidate head:
  `7e69fbb5ed19b58d262989cf455c4b9469119a1f`.
- Prior reviewed head:
  `5a90ed8aa2cfb62f2ce3f431ffd6e155650b43aa`.
- Review branch: `review/pr-1180-rereview-7e69fbb`.
- Disposable review worktree:
  `.git/review-worktrees/pr-1180-rereview-7e69fbb`.
- Pinned corpus:
  `/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`.
- Scope: the four claimed blocker repairs and containment only.
- Canonical exact-candidate archive:
  `.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us`.
- Canonical `git archive` SHA-256:
  `1e49c0ef36a56375f9121562bb791d6bef26791c0609682954b984d6cd4bccf4`.
- Final report: `REVIEW.md`.

## Done

- Loaded the GitNexus PR-review workflow.
- Preserved unrelated changes in the primary checkout.
- Confirmed the requested head resolves locally and created this isolated
  review-only worktree at that exact commit.
- Confirmed no PR-branch, remote, or GitHub write is authorized or planned.
- Froze the repair range at seven commits from prior reviewed head
  `5a90ed8aa` through candidate `7e69fbb5e`; `git diff --check` passes.
- Created a clean canonical-basename archive directly from candidate commit
  `7e69fbb5e`; it excludes this review ledger and report.
- Confirmed the net repair diff is exactly nine paths: the four affected
  manifests, the §151 static relation-schema contract, §55 module/companion,
  §57 module, and §59 module. No index or debt-ledger path changed, and the
  candidate tree does not track `PROGRESS.md`.
- Confirmed the intermediate repair ledger is added, maintained, and dropped
  within the seven-commit repair range; the final signing commit changes only
  the four manifests.
- Verified ordinary manifest provenance for §§55, 57, 58, and 59. Each
  manifest has `backend: manual`, `manual_exception: rulespec-us#1001`,
  encoder commit `3869d66d...`, exactly module plus companion, current SHA-256
  bytes, and byte-identical applied blobs already present in signing parent
  `740eaa9c2`. All four supersedes links match the prior manifest hash and
  signature.
- Reproduced the focused repository containment gates: manifest sync, relation
  schemas, reverse index, and layout are `19 passed` (one expected warning for
  the repository's 19 pre-existing unmanifested modules).
- Verified the exact engine source tree has `110/110` tracked blobs matching
  pinned commit `ffd821327...`; the deterministic release binary used here has
  SHA-256 `674ca6e7...`.
- Read pinned §55(d)(2) and §55(d)(4): the MFS addition uses AMTI determined
  without only the addition sentence, capped at the MFS exemption, and the
  post-2017 rule substitutes 50 percent for 25 percent.
- Confirmed the repair's preliminary-AMTI expression contains taxable income,
  excluded deductions, both adopted §151 amounts, §57, both §58 amounts, and
  all three signed §59 adjustments before computing the MFS addition.
- Independently recomputed the repaired counterexample:
  `$624,100 + $16,100 + $50,000 = $690,200`; addition
  `min($70,100, 50% × $50,000) = $25,000`; AMTI `$715,200`; and TMT
  `$31,785 + $166,026 = $197,811`, exactly `$7,000` above the defective
  predecessor result.
- Independently recomputed the neighboring MFS case: preliminary AMTI
  `$666,100`, addition `$12,950`, final AMTI `$679,050`, TMT `$187,689`,
  and AMT `$27,689` after `$160,000` regular tax.
- Reproduced the exact-pinned four-companion batch at `39/39`; §55 alone is
  `17/17`, so both retained MFS expectations execute at the lawful values.
- Confirmed the repaired domain requires an individual and an exact filing
  status in `0..4`. The committed status-9 and nonindividual cases fail closed
  with zero guarded money outputs. Additional exact-engine probes for statuses
  `-1`, `5`, `8`, `9`, and `10`, plus nonindividual units under every valid
  status `0..4`, all fail closed (`10/10`).

## Next

- Verify proof excerpts, correctly rooted pinned validation, and schema
  mutation kills.
- Reproduce companions, compilation/validation gates, and the mutation battery.
- Write and commit the final evidence-backed verdict to `REVIEW.md`.
