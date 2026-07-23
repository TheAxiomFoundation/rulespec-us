# Federal surtax composition progress

## State

Implementation and locally runnable verification are complete on branch
`fed-parity/surtaxes` from `origin/main` at
`c86b2f62511b7ff9d5351c98ca03b87e3cc41042`. Pre-PR provenance remains
credential-blocked: a key holder must generate three signed
manual-composition manifests and rerun `guard-generated`.

## Done

- Read the mandatory repository-regime recon and exact P1–P3 grid contract.
- Read the repository guidance, Ohio composition precedent, and encoded
  sections 1401, 1402(a), 1402(a)(12), 1402(b), 3101(b)(2), and 1411.
- Confirmed the requested worktree and branch are clean and at the stated
  canonical base.
- Surveyed the federal policy tree and selected
  `us/policies/income_tax/*_pipeline.yaml`, matching the repository's state
  income-tax composition convention while keeping policy plumbing out of the
  federal statute tree.
- Verified that the encoded 2026 Social Security contribution and benefit base
  is $184,500 in
  `us/policies/ssa/contribution-and-benefit-base/2026.yaml`.
- Inspected the Wisconsin manual-composition manifest and located the
  repository-pinned `axiom-encode` 0.2.1200 environment. The signing key is not
  present, so manifest generation remains an explicit credential-dependent
  step.
- Surveyed the repository workflow and local gate commands, including pytest,
  RuleSpec validation/execution/proof checks, reverse-index generation, oracle
  pending sync/check, and generated-artifact guards.
- Implemented the additional-Medicare composition with imported wage and
  self-employment legs, section 1401(b)(2)(B) wage coordination, five
  well-posed P1 grid cases, a completed-section-1402(b) replacement for the
  ill-posed gross-profit row, and zero/threshold boundary cases.
- Passed focused RuleSpec validation, proof validation, money-proof checking,
  and all 11 additional-Medicare companion cases with the repository-pinned
  encoder and engine revisions.
- Confirmed the manual-composition signer selects the new P1 module and
  companion, but cannot write the manifest because
  `AXIOM_ENCODE_APPLY_SIGNING_KEY` is unavailable.
- Implemented the per-person ordinary self-employment-tax composition using
  the imported section 1402(a)(12) deduction, section 1402(b) floor and
  wage-coordinated OASDI base, imported section 1401(a) and (b)(1) taxes, and
  the encoded 2026 SSA base. The combined output deliberately excludes the
  section 1401(b)(2) surtax owned by P1.
- Passed focused RuleSpec validation, proof validation, money-proof checking,
  and all 11 self-employment-tax companion cases, including all six P2 grid
  cases and floor/base boundaries.
- Confirmed the signer selects the P2 module and companion for a
  `manual_exception: composition` manifest; signing remains credential-blocked.
- Implemented the thin NIIT composition as an identity over the complete
  encoded section 1411 tax, with completed-return AGI and the statute's
  investment, section 911, and applicability facts documented as runtime
  boundaries.
- Passed focused RuleSpec validation, proof validation, money-proof checking,
  and all nine NIIT companion cases, including every P3 grid case plus zero
  and exact/one-dollar-over threshold cases.
- Confirmed the signer selects the P3 module and companion for a
  `manual_exception: composition` manifest; signing remains credential-blocked.
- Regenerated `.axiom/index/provisions_to_rules.json` for the three new
  composition modules (3,944 provisions, 4,674 edges, 4,436 modules).
- Ran the official oracle-pending sync. It declared all 15 new executable
  outputs, drained one now-classified pre-existing Hawaii output, set the
  ceiling to 1,755, and passed the scoped pending ratchet with zero stale
  declarations under the repository-pinned classifier.
- Repeated the official sync with the workflow's current
  `axiom-encode@origin/main` classifier. It retained all 15 surtax
  declarations, drained 13 additional pre-existing SNAP declarations that are
  now mapped, and produced the committed final ceiling of 1,742. The current
  classifier check passes with 1,742 declared/applied and zero stale.
- Audited the omitted P1 gross-profit GRID row against whole-module import
  semantics. Importing the SE pipeline produces a duplicate/wrong-entity
  `self_employment_income` collision with root section 1401. Documented the
  honest upstream binding fix and the exact eventual value
  `150,000 * .9235 = 138,525; .009 * (138,525 - 100,000) = 346.725`; retained
  the completed-income case only as boundary coverage.
- Passed the full repository suite: 55 tests, with only expected unmanifested
  module and temporary-directory cleanup warnings.
- Passed deterministic RuleSpec validation for all three modules, proof
  validation with 6/15/2 atoms, the money-proof ratchet with zero new missing
  atoms, and all 31 companion cases.
- Passed reverse-index freshness at 3,944 provisions, 4,674 edges, and 4,436
  modules.
- Passed source staleness against local `axiom-corpus` at current
  `origin/main`: all 43 pinned modules match.
- Reproduced the Program Artifact workflow in a canonical `rulespec-us`
  snapshot with the pinned composer and engine: all 32 program specs built and
  compiled. The direct lane path fails only the composer's required
  `rulespec-<prefix>` basename check.
- Confirmed the signer dry run selects exactly three manifests covering the
  six new module/test files. Actual signing fails only because
  `AXIOM_ENCODE_APPLY_SIGNING_KEY` is unavailable; `guard-generated` therefore
  remains red only for those six unsigned files.
- Wrote the requested full build report to
  `/private/tmp/claude-501/-Users-maxghenis-TheAxiomFoundation/53bdb134-6cd3-452d-89aa-000a8b5d77e3/scratchpad/build-surtax-SUMMARY.md`.

## Next

- Have a signing-key holder run `axiom-encode sign-applied-files --repo .
  --base-ref origin/main --head-ref HEAD --manual-exception composition`,
  commit the three generated manifests, and rerun `guard-generated`.
- Resolve the root section 1401 TaxUnit/Person symbol collision in a
  provenance-approved upstream change before adding the exact
  `amt-single-wage-se` gross-profit fixture.
