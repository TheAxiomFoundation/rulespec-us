# PR #1180 Blind Adversarial Review Progress

## State

- Review status: active.
- Verdict: `REQUEST-CHANGES` unless the confirmed §55(d)(2) defect is
  disproved; remaining review dimensions are still active.
- Live PR head verified through the read-only GitHub connector:
  `5a90ed8aa2cfb62f2ce3f431ffd6e155650b43aa`.
- Expected and verified head branch:
  `fed-parity/atomicA-57-58-59-55`.
- Frozen base:
  `ae64af2740340a40d04ed3c652254f53e62fab61` (`main`).
- Immutable review range:
  `ae64af2740340a40d04ed3c652254f53e62fab61..5a90ed8aa2cfb62f2ce3f431ffd6e155650b43aa`.
- Review branch: `review/pr-1180-5a90ed8`.
- Disposable review worktree:
  `.git/review-worktrees/pr-1180-5a90ed8`.
- Required corpus checkout:
  `/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`.
- Binding plan:
  `/Users/maxghenis/TheAxiomFoundation/ops/fed-parity-campaign/SPINE-PLAN.md`.
- Planned canonical exact-head archive:
  `.git/review-worktrees/pr-1180-canonical/rulespec-us`.
- Final report: `REVIEW.md`.

## Done

- Loaded the GitNexus PR-review workflow.
- Inspected the primary checkout and preserved its unrelated existing changes.
- Confirmed the local author branch and remote-tracking ref both resolve to the
  live GitHub head.
- Confirmed PR #1180 is open, targets `main` at the frozen base, names the
  expected head branch, and reports 13 commits and 16 changed files.
- Attempted the shell GitHub lookup; sandbox network resolution blocked it.
  The read-only GitHub connector supplied live PR metadata instead.
- Created this disposable review-only worktree from the exact candidate head.
  No PR-branch, remote, or GitHub write was made.
- Read the binding plan's house style, AMT consumer contract, Atomic PR A file
  and output list, commit discipline, and definition of done.
- Confirmed the required corpus checkout is clean and detached at exact pin
  `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Frozen the candidate range at 13 commits ahead and zero behind the supplied
  base. Its final tree changes 16 files: four manifests, eight statute/companion
  files, the reverse index, two validation-waiver ledgers, and the oracle
  pending ledger. `git diff --check` passes.
- Created the clean canonical-basename exact-head archive at
  `.git/review-worktrees/pr-1180-canonical/rulespec-us`.
- Verified the archive excludes this review ledger/report and recorded its
  deterministic `git archive` SHA-256 as
  `e4854b7a420e0a565dbb569b3843456af88734fc9c8261d91afc5a29473edb24`.
- Began three independent read-only passes covering §55 legal arithmetic,
  §§57–59 proof/guard/mutation behavior, and mechanical cascade/provenance.
- Reconstructed exact `axiom-encode@3869d66d...` from the local pinned Git
  object and verified the available release engine source tree matches all 110
  tracked files at `axiom-rules-engine@ffd821327...`.
- Reproduced the canonical focused gates: four companions pass 36/36; four
  validations have `ci_pass=true`, `all_passed=true`, and zero errors; proof
  validation passes 114 atoms (81/4/13/16); the focused money-atom gate has
  zero missing obligations.
- Confirmed a blocking §55(d)(2) interaction defect. `amt_separate_addition`
  computes the MFS increment from taxable income plus excluded deductions
  before the newly added senior and §§57–59 amounts, although retained
  §55(d)(2) measures it from AMTI determined without only the increment
  sentence. An independent in-domain MFS + $50,000 §57(a)(5) counterexample
  should produce a $25,000 increment, $715,200 AMTI, and $197,811 base tax;
  the exact-head engine instead produces $0, $690,200, and $190,811.

## Next

- Audit §55 legal corrections and independently recompute companion expected
  values.
- Audit §§57–59 atoms, proof bytes/citations, bounded-domain guards, and
  judgment mutations.
- Reproduce behavior, cascade, ledger, manifest, index, composition, companion,
  and validation gates.
- Write the evidence-backed verdict to `REVIEW.md`.
