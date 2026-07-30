# Atomic PR A repair progress

## State

- Branch: `fed-parity/atomicA-57-58-59-55`
- Reviewed starting head: `5a90ed8aa2cfb62f2ce3f431ffd6e155650b43aa`
- Review: PR #1180 adversarial review at commit `210731915`
- Mode: defensive correctness and completeness audit
- Constraints: local unsigned commits only; no push and no GitHub writes
- Pre-existing untracked file preserved: `WORKER-REPORT.md`
- All four review blockers and every requested worker-owned gate are complete.
- The only remaining handoff is authorized re-signing of the affected
  provenance manifests by the main lane.

## Done

- Read the complete pinned review before changing the branch.
- Confirmed the worktree starts at the reviewed pushed head.
- Confirmed the starting PR containment is 12 non-manifest files plus four
  manifests.
- Confirmed no GitNexus index is present; repository import/dataflow scans will
  provide fallback impact evidence.
- Reproduced the reviewer fixture before repair with exact pinned tools:
  separate addition `$0`, AMTI `$690,200`, and tentative minimum tax
  `$190,811`, plus `holds` for both invalid-status and nonindividual cases.
- Changed the section 55(d)(2) base to complete pre-increment AMTI, including
  the section 151 exemption and senior adjustments and every adopted signed
  section 57, 58, and 59 amount.
- Restricted the bounded section 55 domain to the imported
  `taxpayer_is_individual` fact and explicit filing statuses `0..4`.
- Retained all three reviewer regressions and extended the neighboring MFS
  case through the final tax outputs.
- Exact pinned section 55 companion passes `17/17`; the repaired reproduction
  returns increment `$25,000`, AMTI `$715,200`, and TMT `$197,811`.
- Explicit-key duplicate audit, safe YAML load, and `git diff --check` pass.
- Replaced the section 57 heading-only proof with the pinned operative body
  and repaired both strict-byte section 55 proof excerpts.
- Narrowed requested-source metadata while retaining cross-section legal
  grounding in proof atoms; the reviewer's explicit-root pinned validator is
  green for section 55 and section 59 with zero findings.
- Kept filing-status `9` as an executable companion regression using the
  repository's TaxUnit table-row form, which is accepted by the pinned
  fixture-policy validator; section 55 remains `17/17`.
- Added exact `TaxUnit, Person` schema contracts for both imported section 151
  relations. The positive contract passes and the reviewer's preserved
  reversed-order mutant is detected even though its runtime companion passes.
- Gated committed canonical archive `95d76e1a3` with the exact pinned encoder,
  engine, corpus, and explicit repository root: companions `39/39`; all four
  validators zero-finding; structural proof `114/114`; strict body evidence
  `49/49`; money obligations zero missing.
- Reproduced live mutations: new section 55 complete-AMTI/status/individual
  mutations fail `10/3/3` assertions; inherited section 57(a)(7), section
  58(c)(2), section 59 completion, and section 59(j) mutations fail
  `5/7/7/8`; the reversed section 151 relation is detected statically.
- Recompiled FY2026 FIIT successfully: artifact format `2`, `150` derived
  outputs, `150` evaluation-order entries, and compatible `generic_bulk`
  fast path with no blockers.
- Reverse index is byte-fresh at `4,272` provisions, `5,132` edges, and `4,493`
  modules. All validation/oracle debt ledgers are byte-identical to the
  reviewed head.
- Reconciled containment: the reviewed starting PR was `12` non-manifest
  files plus four manifests; the repaired branch is necessarily `14` plus
  four because it adds this committed ledger and the required schema contract.
- Full repository pytest is `73 passed, 1 failed, 1 warning`; the sole failure
  is the expected manifest-sync guard for repaired sections 55, 57, and 59.
  The signed manifests remain byte-identical to the reviewed head because
  this worker was expressly forbidden to sign.
- Disclosed environment constraints: the default `python` shim is broken;
  GitNexus has no repository index; an out-of-worktree patch and two recursive
  cleanup attempts were policy-blocked. Existing pinned interpreters and
  exact-target moves supplied complete evidence without changing candidate
  bytes.

## Next

1. Main lane re-signs sections 55, 57, and 59 (including section 55's changed
   companion) with the authorized provenance key.
2. Main lane reruns the manifest-sync test/full pytest, then pushes and
   requests re-review.
