# PR #1179 Blind Adversarial Review Progress

## State

- Review status: in progress; `REQUEST-CHANGES` evidence complete.
- Frozen candidate head:
  `4ced8fb7065311338ea732cab0a26105e750c40f`.
- Expected head branch: `fed-parity/chunk2-taxable-income`.
- Local branch and remote-tracking ref agree at the frozen candidate head.
- Frozen local base:
  `origin/main` at `ae64af2740340a40d04ed3c652254f53e62fab61`.
- Immutable local range:
  `ae64af2740340a40d04ed3c652254f53e62fab61..4ced8fb7065311338ea732cab0a26105e750c40f`.
- Review branch: `review/pr-1179-4ced8fb`.
- Disposable review worktree:
  `.git/review-worktrees/pr-1179-4ced8fb`.
- Required corpus checkout:
  `/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`.
- Binding plan:
  `/Users/maxghenis/TheAxiomFoundation/ops/fed-parity-campaign/SPINE-PLAN.md`.
- Canonical exact-head archive:
  `.git/review-worktrees/pr-1179-canonical/rulespec-us`.
- Final report: `REVIEW.md`.

## Done

- Loaded the GitNexus PR-review workflow.
- Inspected the primary checkout before edits; it is detached with unrelated
  existing worktree-link changes, so it will not be used for review commits.
- Preserved the author's existing branch worktree and its untracked
  `WORKER-REPORT.md`.
- Attempted a read-only GitHub PR lookup and `git fetch`; sandbox DNS/network
  restrictions blocked both.
- Confirmed the local author branch and remote-tracking ref both resolve to
  the frozen candidate head and that the expected branch is six commits ahead
  and zero commits behind its local `origin/main` merge base.
- Created this disposable local review worktree and review-only branch from
  the candidate head. No PR-branch, remote, or GitHub write was made.
- Confirmed the required corpus checkout is clean and detached at exact pin
  `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Read binding `SPINE-PLAN.md` §5, §6.3, §9 Chunk 2 and commit discipline,
  plus the tranche definition of done.
- Froze the five-file candidate diff: taxable-income compose, companion,
  manifest, reverse index, and pending ledger only; `git diff --check` passes.
- Created the required canonical-basename exact-head archive at
  `.git/review-worktrees/pr-1179-canonical/rulespec-us`.
- Verified the archive's pipeline SHA-256
  `460e8554e965c4fcf5839d7963faad91b29f7972e2fc40bf3b5d430a6fdaf7c5`
  exactly matches the frozen commit bytes and contains no session ledger or
  review report.
- Confirmed the first 14 companion cases exactly match the plan's case IDs and
  expected taxable-income values. Independent exact-decimal recomputation
  matched all 14, including equal-election, all-component, floor, and senior
  phaseout boundaries.
- Ran the exact pinned companion from the canonical archive with encoder
  `3869d66d...` and engine `ffd821327...`: 1 file, 27 cases, 1 compiled
  program, zero failures.
- Ran pinned validation against the required corpus: `ci_pass=true`,
  `all_passed=true`, and zero errors. Structural proof validation passed 33
  atoms with zero reported issues.
- Programmatically compared every source excerpt in the new compose to the
  exact resolver-selected pinned corpus bytes. Eight of nine occur exactly
  once; the section 165 wagering excerpt occurs zero times. Current section
  165(d) instead requires both a 90-percent loss haircut and the gains ceiling.
- Confirmed the companion omits the prescriptive section 151 MAGI-addback
  diagnostic: every section 911/931/933 fact is false or zero, so none of the
  27 cases proves that an exclusion changes the senior phaseout.
- Audited the 25-module merged closure: 227 rule declarations and four
  relation predicates are unique; all 119 proof imports resolve, all 69
  nonlocal hashes are current, and the merged Chunk 1 hashes are
  `81d04979...` (SALT) and `da533e2f...` (itemized). The closure includes the
  Revenue Procedure standard final and excludes `us/statutes/26/63/c.yaml`.
- Found incomplete relation-schema coverage. The closure has four injectable
  relations, but the executable static contract pins only SALT. In a separate
  exact-head mutation archive, reversing only the section 151 senior relation
  from `(TaxUnit, Person)` to `(Person, TaxUnit)` still passed the static
  contract and the entire taxable-income companion 27/27, including its
  claimed imported-relation orientation witness.
- Found that the itemizer final has no section 63(a) legal proof. The target's
  final is sourced and proved only to section 63(b), even though the same
  output executes the itemizer branch; the imported itemized module proves
  sections 63(d)-(e), not section 63(a)'s general taxable-income definition.
- Found an outside-boundary injection accepted by the companion. The
  `ti-entity-zeroes-standard` case simultaneously asserts
  `taxpayer_is_individual=true` and
  `estate_or_trust_common_trust_fund_or_partnership=true`, yet expects the
  individual verified domain to hold and taxable income to be nonzero.
- Regenerated the reverse index in check mode: byte-current at 4,249
  provisions, 5,120 edges, and 4,491 modules.
- Audited the pending ledger: base and head are sorted and unique with
  `ceiling == count`; the head is the exact field-preserving union, with zero
  losses or changed prior records and exactly the three new taxable-pipeline
  entries (2,148 to 2,151).
- Audited the composition manifest: its exact two applied files and hashes
  match current, content-commit, and pre-signature ancestor bytes; the content
  commit is an ancestor; the signature commit changes only the manifest; the
  exception is exactly `composition`; and no candidate commit follows it.
- Ran focused repository layout, reverse-index, manifest, and relation-schema
  tests: 19 passed with one report-only warning for 19 pre-existing
  unmanifested modules. An independent full repository run passed 74 tests
  with the same warning.
- Confirmed the candidate diff is exactly the intended five files, with no
  workflow, toolchain, lockfile, state, or tracked session-ledger change.
- Attempted the GitNexus graph workflow from a detached exact-head worktree.
  The repository was unindexed; offline `npx` had no cached package, and the
  installed analyzer was blocked from writing its global registry. The direct
  25-module closure audit supplied the dependency and collision evidence.
- Recorded environment-only limitations: live GitHub/fetch access was blocked
  by sandbox networking, and the local manifest HMAC signing key was absent
  and the secret store locked. The signature envelope is shape-valid and all
  non-secret provenance checks pass, but the HMAC itself is not
  cryptographically reverified here.

## Next

- Record the evidence-backed verdict in `REVIEW.md` and finalize the ledger.
