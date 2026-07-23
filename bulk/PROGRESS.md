# Federal surtax composition progress

## State

In progress on branch `fed-parity/surtaxes` from `origin/main` at
`c86b2f62511b7ff9d5351c98ca03b87e3cc41042`.

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

## Next

- Run the official oracle sync/check and all local CI-equivalent gates.
- Write the requested external build summary with case arithmetic and exact
  gate results.
