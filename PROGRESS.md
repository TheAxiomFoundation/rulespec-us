# PR #1180 Blind Adversarial Review Progress

## State

- Review status: complete.
- Verdict: `REQUEST-CHANGES`; multiple independent blocking defects are
  confirmed. Review and report are closed on the immutable range below.
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
- Reproduced the canonical focused gates: four companions pass 36/36; the
  branch CLI reports four validation passes; structural proof validation
  passes 114 atoms (81/4/13/16); the focused money-atom gate has zero missing
  obligations.
- Confirmed a blocking §55(d)(2) interaction defect. `amt_separate_addition`
  computes the MFS increment from taxable income plus excluded deductions
  before the newly added senior and §§57–59 amounts, although retained
  §55(d)(2) measures it from AMTI determined without only the increment
  sentence. An independent in-domain MFS + $50,000 §57(a)(5) counterexample
  should produce a $25,000 increment, $715,200 AMTI, and $197,811 base tax;
  the exact-head engine instead produces $0, $690,200, and $190,811.
- Confirmed two independent §55 fail-closed defects. The verified-domain
  judgment accepts filing status `9`, because it never enumerates statuses
  `0..4`, and it accepts `taxpayer_is_individual=false`, because the new §151
  import closure is not guarded by the binding individual-only boundary.
- Confirmed the §55 companion omits both binding house-style cases: invalid
  filing status and relation-order mutation.
- Confirmed the §151 import adds two relation schemas to the compiled §55
  closure, but the static schema-contract test still covers only the SALT
  relation. In a reviewer archive, reversing
  `exemption_individual_of_tax_unit` and updating its import hashes leaves both
  the static contract (1/1) and the complete §55 companion (14/14) green.
- Confirmed one §57 proof excerpt is not body evidence. The text
  `Specified private activity bonds` occurs only in the PR-B corpus record's
  heading; the release-bound proof evidence is the body and source history.
  A programmatic exact-body audit resolves every citation uniquely and finds
  this sole mismatch among the 25 §§57–59 source excerpts.
- Confirmed explicit-root deterministic validation is not zero-findings:
  §59's source string names both §55(d)(4)(A)(iii) and §59(j), so the exact
  pinned validator rejects it as outside requested subtree
  `us:statutes/26/59`. The CLI's apparent pass is not equivalent: its
  path-discovery helper resolves the canonical archive's `us/` directory,
  rather than the canonical repository root, as `policy_repo_path`.
- Confirmed strict retained-corpus byte checks also find two nonverbatim §55
  excerpts: one drops statutory curly quotation marks and one YAML-folds
  statutory blank-line separators. The pinned structural proof validator does
  not enforce literal excerpt identity.
- Reran exact-engine mutation evidence: §57 a(7), §58 c(2), §59 completion,
  and §59(j) flips each fail their companions (5/7/7/8 assertions), and an
  independent AMTFTC guard inversion fails two assertions.
- Added a separate Form 4972 guard mutation. Replacing the required
  `form_4972_lumpsum_distributions == 0` condition with `!= 0` makes the
  exact-engine §55 companion fail 49 assertions across nine cases, including
  the dedicated nonzero-Form-4972 case.
- Independently recomputed the correction fixtures: §68-reversal AMTI
  `$119,000`; senior-addback AMTI `$122,100`; signed §§57–59-adjustment AMTI
  `$166,950`; and the split-credit case TMT after AMTFTC `$185,618`, regular
  tax after ordinary FTC `$155,000`, AMT `$30,618`, and income tax before
  credits `$190,618`.
- Reproduced base §55 companion 5/5 and head batch 36/36. Shared no-AMT,
  high-income, and MFS expected outputs are unchanged; a reviewer-only probe
  preserves the removed joint phaseout case. A matched post-2017 kiddie probe
  changes only as required by §59(j)'s sunset: exemption `$14,750` to
  `$90,100`, taxable excess `$85,250` to `$26,000`, and resulting AMT to
  `$6,760`.
- Reproduced the fresh FY2026 FIIT composition and exact-engine compile:
  artifact format 2, 150 derived outputs, and fast-path compatibility. Base
  has 137 outputs; head adds 14 intended outputs and removes only the
  inoperative kiddie-limit output.
- Completed the import closure audit: only §55 imports the new §§57–59
  surfaces; all external proof hashes are current and local imports use
  `sha256:local`; there are no repository-wide stragglers.
- Verified the pending-oracle ledger is the exact sorted/unique union:
  2,148 to 2,159, with exactly 11 additions and no removed or modified prior
  row. The §55 waiver and fingerprint entries were removed rather than
  refreshed, and §§57–59 have no live waiver rows.
- Independently reproduced reverse-index parity at 4,272 provisions, 5,132
  edges, and 4,493 modules.
- Verified all four ordinary-provenance manifests name only their module and
  companion, record current file hashes, carry `rulespec-us#1001`, and attest
  bytes already present at signing parent `c36b0b58b`; the signing commit
  changes only the four manifests.
- Confirmed final containment is 12 non-manifest files plus four manifests,
  not the requested 13 plus manifests. The author ledger's earlier count of
  13 included its temporary `PROGRESS.md`, which was removed before signing;
  the relation-schema contract that should cover the new compiled §151
  relation closure was not added.
- Reproduced the repository layout, manifest, reverse-index, and existing
  relation-schema tests. The full repository test suite passes.
- Wrote the complete evidence-backed request-changes verdict to `REVIEW.md`,
  including repair requirements and all sandbox/tooling disclosures.

## Next

- Await a revised PR head, then start a new frozen-head review rather than
  reusing this immutable evidence range.
