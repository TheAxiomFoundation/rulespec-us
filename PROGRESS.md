# PR #1003 Additional Medicare CI Fix Progress

## State

- Defensive correctness and completeness audit is in the implementation phase
  on branch
  `fed-parity/surtaxes`.
- Scope remains limited to deferring the generic Additional Medicare
  international-agreement surfaces that overlap the upstream deferred
  `self_employment_tax_after_international_agreement_exemption`, then exposing
  an explicitly ordinary/no-agreement imported branch to the existing public
  outputs.
- No pushes, manifest re-signing, workflow edits, or toolchain edits are
  authorized.
- Read-only PR metadata confirms PR #1003 is open at head
  `8218c7baff9330cf1eb707bb7d2df87bfb4abcfc`.
- The local `gh` credential is invalid, so the supplied Actions job/error is
  the CI-log source of record; read-only PR context was retrieved through the
  GitHub connector.
- The pinned shared workflow at
  `TheAxiomFoundation/.github@799195b2ca85c8106fcee001ead074fa99e2feef`
  actually invokes `axiom-encode validate "${selected[@]}"
  --skip-reviewers`. A no-skip local diagnostic invokes four external Claude
  reviewers, all unavailable in this environment; deterministic CI parity
  therefore uses the workflow's `--skip-reviewers` command.

## Done

- Read the `gh-fix-ci` workflow instructions.
- Confirmed the current worktree, branch, remote, and clean starting state.
- Confirmed the requested fix is already explicitly approved and constrained:
  defer the generic surface, preserve public output names and six grid results,
  and do not push or re-sign manifests.
- Located the exact workflow, encoder, engine, proof, companion, and
  reverse-index commands.
- Confirmed the pinned encoder source is commit
  `3869d66d009f52258be35901edbef370e65a399c`.
- Audited the direct dependency chain and found two imported-deferred overlap
  violations: the CI-named exemption amount and the downstream generic taxable
  self-employment-income helper.
- Confirmed the NIIT, ordinary SE-tax, and PR #1002 PTC pipelines have zero
  sibling instances under both deferred-overlap detectors. The local
  `origin/fed-parity/aca-ptc` ref exactly matches PR #1002 head
  `6c1cb66e9752cefe421e8a49a3c01346ba0968a7`.
- Identified the fixture boundary: remove only the three TaxUnit section
  1401(c) facts and deleted-helper assertions; retain the Person-level section
  1402(b) agreement fact and all 12 cases.

## Next

- Add explicit deferred records for the two old generic helper surfaces,
  blocked by the upstream deferred section 1401(c) output.
- Remove the executable agreement condition, exemption amount, generic taxable
  amount, and their three TaxUnit inputs.
- Add an ordinary-case imported-income alias, preserve the three public output
  names, retain all 12 fixtures, and ratchet the oracle-pending ledger.
- Run CI-mode validation on all three PR #1003 pipelines and the PR #1002 PTC
  pipeline, plus proof validation, companions, reverse-index, and grid-result
  invariance checks.
- Record exact commands/results, final commit SHA, and any tooling limitations
  in the required DONE marker.
