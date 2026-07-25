VERDICT: REQUEST-CHANGES

# PR 1004 final confirmation

Reviewed exact live heads:

- PR 1004: `e513d11b73a402334b71178d5236cd6c82a4f830`
- PR 1003: `9de6ebbc9ec4ecb7a4f9c5dbd201cddcbd9b6184`
- Final GitHub refresh: `2026-07-25T02:49:20Z`

## Single unmet item

PR 1003's renamed fail-closed companion still makes one claim broader than
the case proves. In
`us/policies/income_tax/additional_medicare_tax_pipeline.test.yaml:299`, its
comment says:

> With any positive SE profit the SE leg and combined output fail closed

The current domain is instead:

```text
no_foreign_system_exclusive_se_income
and federal_self_employment_income == 0
```

The passing current-head `seca-floor-below` fixture is a direct counterexample
to the universal wording: positive `gross_self_employment_profit: 433` derives
net earnings of `399.8755`, below the section 1402(b)(2) floor, and therefore
produces zero self-employment income. With a true foreign-system attestation,
the zero-SE-income guard would not fail for that positive profit.

The subject companion itself is otherwise correct. Its `$150,000` profit
derives imported federal SE income of `$138,525`, so that particular case
independently fails the zero-SE-income conjunct and proves the combined-domain
fail-closed result, not the foreign-system attestation in isolation. Narrow
the first sentence to, for example:

> Because this case has positive imported federal self-employment income, the
> SE leg and combined output fail closed ...

## Requested confirmations

### PR 1004 residuals

- **Pinned deferred-overlap validator: PASS.** From a real
  canonical-basename `rulespec-us` worktree, the pinned encoder
  `3869d66d009f52258be35901edbef370e65a399c` (`0.2.1200`) validated
  `qualified_business_income_deduction_pipeline.yaml` with
  `--skip-reviewers`; exit 0, `CI: ✓`, `Result: ✓ PASSED`.
- The obsolete
  `pipeline_qualified_business_income_threshold_amount` selector has zero
  current-head matches. The accepted pipeline-scoped selector is
  `pipeline_applicable_deduction_limit_start_for_return_category`; its policy
  and companion references are internally complete.
- The live PR 1004 body is one current-head account beginning “Single account
  of head e513d11b7 — supersedes all earlier body text.” It contains no
  conflicting historical account.

### PR 1003 residuals

- `bulk/fix3-1003/PROGRESS.md` is absent at the current head.
- The live PR 1003 body is one current-head account beginning “Single account
  of head 9de6ebbc9 — supersedes all earlier body text.” It accurately limits
  the changed companion to the combined fail-closed domain.
- The companion's name and remaining explanation correctly disclaim
  independent attestation coverage, but the universal “any positive SE
  profit” sentence leaves the specifically requested exact-claim residual
  unresolved.

## Focused gates

All commands ran from real canonical-basename `rulespec-us` roots with the
pinned encoder, corpus
`710a326366bd233c40d64ca89b62a07082f13ce3`, and rules engine
`ffd8213271947b0189a9dd61a055c1e0e78908a0`.

| Head | Validation | Proofs | Companions |
|---|---:|---:|---:|
| PR 1004 `e513d11b7` | 3/3 PASS | 43/43 PASS | 40/40 PASS |
| PR 1003 `9de6ebbc9` | 3/3 PASS | 47/47 PASS | 42/42 PASS |

Additional mechanical checks passed: both round ranges pass
`git diff --check`; PR 1004's six applied-file manifest hashes match; PR
1003's six applied-file hashes and three supersession links match; and the PR
1004 oracle-pending ratchet reports 2,396 declared, zero stale, and no
problems.

## Exact-head CI state

GitHub did not settle to green at either new head during this confirmation.
Repeated read-only polls through `2026-07-25T02:49:20Z` returned no
pull-request workflow runs and no commit statuses for either SHA; both PR
snapshots reported `mergeable: false`. The visible workflows for PR 1004's
previous head do not establish CI at `e513d11b7`.

There are therefore no exact-head run or job IDs whose conclusions can be
reported as green. Because the single wording correction above necessarily
creates another head, CI must be run and confirmed on that corrected head.

## Round-over-round delta

- PR 1004's three-commit range
  `e25a31417997e27b50ef9d2315d67b9a9036f7b5..e513d11b73a402334b71178d5236cd6c82a4f830`
  renames the rejected selector and its matching fixture reference, regenerates
  the oracle ledger, and re-signs three manifests. The ledger also adds 14 DC
  and 13 SNAP bookkeeping entries for modules whose blobs are identical at
  both endpoints. No runtime formula, input, or output semantics were added.
- PR 1003's two-commit range
  `50b6ec228dba8279526bd692de85af4659557c78..9de6ebbc9ec4ecb7a4f9c5dbd201cddcbd9b6184`
  deletes the stale progress file, changes only the fail-closed case name and
  comments, and re-signs three manifests. Its executable inputs, expected
  outputs, and formulas are unchanged.

No new executable defect was found in either round delta. The requested change
is limited to the one overbroad companion sentence above.

This was review-only. No reviewed source, PR body, comment, review, branch, or
other remote GitHub state was changed.
