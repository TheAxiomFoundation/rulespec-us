# Atomic PR A repair progress

## State

- Branch: `fed-parity/atomicA-57-58-59-55`
- Reviewed starting head: `5a90ed8aa2cfb62f2ce3f431ffd6e155650b43aa`
- Review: PR #1180 adversarial review at commit `210731915`
- Mode: defensive correctness and completeness audit
- Constraints: local unsigned commits only; no push and no GitHub writes
- Pre-existing untracked file preserved: `WORKER-REPORT.md`
- All four review blockers are repaired; relation-schema containment is now
  statically protected in addition to the exact pinned runtime gates.

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

## Next

1. Reconcile derived artifacts and containment.
2. Run every requested gate from a committed canonical
   basename archive root.
