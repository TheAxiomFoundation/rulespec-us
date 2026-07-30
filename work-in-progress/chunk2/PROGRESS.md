# Chunk 2 taxable-income pipeline progress

## State

All worker-authorized implementation and gates are complete. The compose and
27-case companion are committed, the reverse index and pending ledger are
regenerated, and the final canonical archive passes the pinned test, validation,
index, and changed-file coverage checks. Signing and manifest creation remain
reserved for the main lane.

## Done

- Verified that `origin/main` contains merged Chunk 1 and Atomic PR 0.
- Created the requested worktree and branch because neither existed locally.
- Confirmed the exact taxable-income import set, public output, cases, and commit order.
- Audited the 24-module imported closure: 224 pre-existing executable rules are unique;
  the only relations are the four existing SALT, section 151, and section 170(p)
  relations.
- Added the guarded taxable-income domain, branch deduction total, and
  `federal_taxable_income` final with current non-local import hashes.
- Added all 14 binding section 6.3 grid cases plus 13 companion-only diagnostics,
  including invalid status, all-attestations-false, election mismatch, negative
  wagering loss, all four section 63(c)(6) disqualifiers, and relation orientation.
- Passed 27/27 companion cases and pinned corpus validation with zero findings.
- Repeated both gates from `/private/tmp/chunk2-archive.LMS76C/rulespec-us`, a
  canonical-basename `git archive` of the committed compose step: 27/27 and pass.
- Regenerated the reverse index to 4,249 provisions, 5,120 edges, and 4,491
  modules; its diff adds only the taxable-income module and removes no edge.
- Extended the pending ledger from 2,148 to 2,151 entries as an exact sorted
  union with no changed or lost baseline entry.
- Ran the pinned changed-file coverage classifier: all three new outputs are
  `pending_classification` and companion-tested; none is unmapped.
- Proved the merged surface has 25 modules and 227 unique rules (24 imported
  modules and 224 imported rules), no duplicate name, no `63/c.yaml`, and no
  local relation.
- Demonstrated the static relation contract kill: swapping the existing SALT
  relation's two argument lines failed with declared `(Person, TaxUnit)` versus
  expected `(TaxUnit, Person)`; restoration passed and left no diff.
- Verified the final and deduction-total PolicyEngine candidates directly in
  the cached PolicyEngine-US 1.767.3 package (`taxable_income` and
  `taxable_income_deductions`).
- Audited the branch diff: exactly the two pipeline files, reverse index,
  pending ledger, and this non-root progress file; no root `PROGRESS.md`,
  `.github` change, stale importer, manifest, or unrelated file.

## Next

- Commit this final progress state.
- Write `WORKER-REPORT.md` untracked with the final head SHA, gate evidence,
  case walkthroughs, bridge values, and exact oracle mapping handoff.
- Main lane: review, sign the applied pipeline files, create the manifest last,
  and pair the RuleSpec head with the taxable-income oracle PR.
