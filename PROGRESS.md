# 7 CFR 273.11 remainder encoding

## State

- Branch: `encode-273-11-remainder`
- Original base: `origin/main` at `1158ba5b2`; current `origin/main` through
  `6b0773d3f` has been merged without modifying its shared tooling changes.
- Claim: `rulespec-us#1135`
- Scope: encode the point-in-time computational remainder of 7 CFR 273.11,
  integrate the existing paragraph (c) treatment with the new canonical
  disqualification outputs, and classify purely procedural paragraphs for
  follow-up.
- Status: implementation, review, and local module validation are complete;
  the branch is ready for its unmerged pull request.
- Source: `us/regulation/7/273/11` in
  `_closure-sprint/data/cfr-273.jsonl` (source as of 2026-07-09).
- Worktree was clean at task start.

## Done

- Read the repository `CLAUDE.md`; it references no additional agent or
  contribution instructions.
- Read the existing `273/11/c.yaml` and companion test.
- Read `273/9.yaml` and `273/10.yaml` for SNAP income and allotment conventions.
- Read the complete cited source text for 7 CFR 273.11(a)-(s).
- Located and smoke-tested the repository's pinned `axiom-encode` 0.2.1200
  toolchain against the existing paragraph (c) proof and companion tests.
- Classified the current section as follows:

  | Paragraph | Treatment in this change |
  | --- | --- |
  | (a) | Encode self-employment averaging, anticipation, farm losses, capital gains, and benefit-level proration envelope. |
  | (b) | Encode actual and simplified allowable-cost methods, including boarder caps; defer the stale foster-care-boarder cross-reference. |
  | (c) | Integrate existing (c)(1)-(2) treatment with canonical (k), (m)-(q), and (s) outputs and preserve the (c)(3) deferral; classify (c)(4) notice/hearing workflow as procedural. |
  | (d) | Encode other-nonhousehold-member income, resource, expense, wage, and household-size treatment. |
  | (e) | Encode DAA-resident certification/size, representative suspension, and deterministic departure balances, including the post-15th State option; classify remaining administrative mechanics separately. |
  | (f) | Encode GLA qualification/application routes, representative suspension, size, and deterministic departure balances; classify remaining administrative mechanics separately. |
  | (g) | Encode battered-shelter separate-household, allotment-limit, income/resource, and shelter-expense rules. |
  | (h) | Encode homeless-household prepared-meal purchase permission. |
  | (i) | Skip as prerelease application-timing and cross-reference procedure. |
  | (j) | Encode the current no-increase rule and optional penalty ceiling; classify plans, restoration, and unrelated-change processing as procedural. |
  | (k) | Encode the current comparable-disqualification state option and mandatory FDPIR branch; classify plans/restoration processing separately. |
  | (l) | Skip because it expressly creates no independent SNAP sanction authority. |
  | (m) | Encode drug-felony member eligibility, state relief, and cutoff. |
  | (n) | Encode the current fleeing-felon/probation-parole status, adverse-action timing gates, and application-deadline safeguard. |
  | (o) | Encode the custodial-parent cooperation state option, point-in-time exceptions, and protection while a good-cause claim is pending; classify notice/evidence/requalification procedure separately. |
  | (p) | Encode the noncustodial-parent cooperation state option and refusal determination; classify notice/privacy/requalification procedure separately. |
  | (q) | Encode the child-support-arrears state option and exceptions; skip claim-collection procedure. |
  | (r) | Encode substantial-winnings disqualification and reentry conditions; skip reporting/action procedure. |
  | (s) | Encode qualifying-conviction, sentence/restriction, and conduct-date conditions. |
- Implemented and committed companion-tested modules for paragraphs (a)-(h),
  (j)-(k), and (m)-(s), including the pre-existing paragraph (c): 17 modules
  and 17 companion test files.
- Refreshed the provision reverse index after the initial implementation.
- Completed an independent subsection-by-subsection review and committed fixes
  for paragraph (c)'s exclusion boundary, battered-shelter eligibility and
  expense typing, mandatory FDPIR reciprocity, pending custodial good cause,
  DAA/GLA certification and departure rules, public-assistance reduction
  limits, self-employment averaging/cost linkage, the paragraph (n)(5)
  deadline safeguard, and the paragraph (s) effective date.
- The pinned `axiom-encode` 0.2.1200 validator, strict proof validator, and
  rules-engine companion tests pass for all 17 modules:
  - 17/17 module validations passed.
  - Strict proof validation passed with 297 atoms and no missing atoms for the
    one monetary obligation.
  - All 151 companion cases passed.
- Verified all four repository repair guards are no-ops for every module:
  test-input assignments, imported test inputs, invalid test inputs, and proof
  import hashes.
- Regenerated the provision reverse index: 4,232 provisions, 5,084 edges, and
  4,499 modules; regeneration produced no diff.
- Ran `tests/test_repository_layout.py` and `tests/test_reverse_index.py`: all
  15 tests passed.
- Refreshed the generated oracle-pending ledger from 2,293 to 2,513 declared
  outputs, covering all 220 newly visible outputs eligible for automatic sync.
  The full ratchet now reports only 27 pre-existing Missouri legacy-manual
  outputs; the same 27 are among 247 failures on `origin/main`, and the sync
  tool intentionally does not add new legacy-manual declarations.
- Verified the complete branch diff has no whitespace errors and changes only
  the expected modules/tests, `PROGRESS.md`, provision index, and oracle-pending
  ledger. No workflow, toolchain, pin, or `CODEOWNERS` file changed.

## Next

- Push `encode-273-11-remainder` and open the unmerged PR titled
  `Encode 7 CFR 273.11 special-circumstances remainder`, referencing #1135.
- Preserve the encoded-versus-procedural classification in the PR body for
  future classification work.
- Do not merge the PR.
