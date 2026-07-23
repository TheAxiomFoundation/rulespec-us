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

## Next

- Implement and test the additional-Medicare composition.
- Implement and test the self-employment-tax composition.
- Implement and test the NIIT composition.
- Generate approved manifests if credentials permit, regenerate the reverse
  index, run the official oracle sync when locally available, and run all
  local CI-equivalent gates.
- Write the requested external build summary with case arithmetic and exact
  gate results.
