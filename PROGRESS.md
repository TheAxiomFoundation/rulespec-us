# PR #1003 Additional Medicare CI Fix Progress

## State

- Defensive correctness and completeness audit is complete on branch
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
- Added explicit deferred records for the old exemption and taxable-income
  helpers, each blocked by the upstream deferred section 1401(c) output.
- Removed the executable section 1401(c) condition/amount path and its three
  TaxUnit inputs; added an expressly ordinary-case imported-income alias.
- Preserved `federal_additional_medicare_wage_tax`,
  `federal_additional_medicare_self_employment_tax`, and
  `federal_additional_medicare_tax` verbatim.
- Retained all 12 companions and all six GRID-CONTRACT public results,
  including the `346.725` row; retained the Person-level section 1402(b)
  agreement input.
- Ratcheted `oracle-coverage-pending.yaml` from 1,753 to exactly 1,751 entries.
- Confirmed both pinned deferred-overlap detectors now report zero issues and
  pinned proof validation passes with 14 atoms checked.
- Built the exact pinned rules engine commit
  `ffd8213271947b0189a9dd61a055c1e0e78908a0` and used the exact pinned corpus
  commit `dfa47fb05bd1d3abbadf0ff17ce4a04bdd5c8085` in canonical temporary
  checkouts.
- Ran the shared-workflow-equivalent `validate --skip-reviewers` invocation:
  Additional Medicare, NIIT, ordinary SE tax, and PR #1002 PTC each reported
  `CI: ✓` and `Result: ✓ PASSED`.
- Ran a no-skip diagnostic on Additional Medicare: its deterministic CI tier
  reported `CI: ✓`; all four external reviewer CLIs exited before any turns or
  tokens, so that non-CI reviewer layer is unavailable locally.
- Proof validation passed for all four files (14, 2, 15, and 34 atoms).
- Companion tests passed for all three PR #1003 files (32/32), Additional
  Medicare alone (12/12), and PTC (9/9).
- Reverse-index check passed: 3,944 provisions, 4,674 edges, 4,436 modules.
- Oracle-coverage pending check passed with 1,751 applied declarations and zero
  stale entries.

## Next

- Main lane re-signs the changed Additional Medicare pipeline/test manifest.
- Main lane pushes the local commits and re-runs PR #1003 CI.
