VERDICT: REQUEST-CHANGES — The fail-closed companion still overclaims that “any positive SE profit” makes the zero-imported-SE-income guard dominate.

# PR 1003 final confirmation review

## Reviewed state

- PR 1003 head: `9de6ebbc9ec4ecb7a4f9c5dbd201cddcbd9b6184`
- PR 1003 base: `836e74b578a35fdfb30bf828e89510cd894e8300`
- Prior reviewed head: `50b6ec228dba8279526bd692de85af4659557c78`
- PR 1004 residual-check head: `e513d11b73a402334b71178d5236cd6c82a4f830`

## Single unmet item

The renamed case `amt-se-domain-fails-closed-attestation-not-independent`
correctly stops claiming that it independently proves the section 1401(c)
attestation. Its new comment nevertheless says:

> With any positive SE profit the SE leg and combined output fail closed

That universal statement is broader than the implementation and fixture prove.
The domain guard is
`no_foreign_system_exclusive_se_income and federal_self_employment_income == 0`,
not `gross_self_employment_profit == 0`. The committed `seca-floor-below`
fixture supplies positive gross self-employment profit of `433`, derives net
earnings of `399.8755`, and proves imported self-employment income is `0`
because the section 1402(b)(2) floor applies. With a true attestation, that
positive-profit case remains in-domain.

The renamed fixture proves only that its own positive imported federal
self-employment income (`138525`) makes the combined domain fail closed. Scope
the comment accordingly, for example: “In this fixture, positive imported
federal self-employment income makes the wage-only-domain guard dominate.”

## Requested confirmations

- PR 1004: resolved. From a disposable root literally named `rulespec-us`, the
  pinned encoder at `3869d66d009f52258be35901edbef370e65a399c`
  accepted the renamed pipeline-scoped QBID selector (`CI: ✓`,
  `Result: ✓ PASSED`). The live body is one coherent replacement account at
  `e513d11b7`.
- PR 1003: `bulk/fix3-1003/PROGRESS.md` is absent. The live body is one
  coherent replacement account at `9de6ebbc9`. The renamed companion accurately
  disclaims independent attestation coverage, subject only to the overbroad
  sentence above.
- Focused gates: from a detached canonical-basename `rulespec-us` root, using
  encoder `3869d66d…`, engine `ffd821327…`, and corpus `710a3263…`,
  validation passed `3/3`, proof validation passed `47/47` atoms, companions
  passed `42/42`, the changed Additional Medicare companion passed `14/14`,
  and encoding-manifest pytest passed `3/3`.
- Current-head CI had not settled at the final read. GitHub reported live head
  `9de6ebbc9`, but `refs/pull/1003/merge` still represented previously tested
  head `3327de193`; no workflow runs or commit statuses existed for
  `9de6ebbc9`. The last settled `3327de193` run was green in Repository Checks,
  program-artifacts, and Source staleness and reverse index. Because the single
  wording fix above necessarily creates a new head, require fresh green CI
  there.

## Round-over-round delta

`50b6ec228..9de6ebbc9` contains two commits and five files:

- `5da440336` deletes the stale `bulk/fix3-1003/PROGRESS.md` and renames/rewords
  one Additional Medicare companion without changing its inputs or outputs.
- `9de6ebbc9` mechanically re-signs the three surtax manifests; NIIT and SECA
  content hashes remain unchanged, and the Additional Medicare manifest
  changes only for the companion hash plus ordinary signature/supersession
  metadata.

`git diff --check`, manifest JSON parsing, applied-file hashes, supersession
links, and focused manifest tests pass. The inaccurate universal wording above
is the only new issue in the round delta.
