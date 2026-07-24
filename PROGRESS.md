# PR #1003 residual fix — round 2

## State

In progress on branch `fed-parity/surtaxes`. All three adjudicated residuals
are implemented and pass the pinned focused gate battery. Downstream hashes
and generated metadata are reconciled through the oracle ledger. The signed
apply manifests cannot be refreshed in this session because
`AXIOM_ENCODE_APPLY_SIGNING_KEY` is absent; the remaining non-signing gates,
repository pytest, and final scratchpad report are in progress. No pushes,
GitHub writes, PR-body edits, or `us/statutes` edits are in scope.

## Done

- Read `scratchpad/rereview-1003-VERDICT.md`.
- Confirmed the three adjudicated residuals:
  - ordinary SECA public tax outputs need the same required section 1401(c)
    attestation guard used by the Additional Medicare wrapper;
  - the pinned `us/statute/26/1401` record text is authoritative for the
    section 1401(b)(2)(B) wage-coordination wording despite the separately
    tracked broken `source_url` metadata;
  - both finite-decimal straddle cases must assert the imported operative
    section 1402(b)(2) floor branch directly.
- Read the repository instructions and confirmed the initial Git state.
- Added required TaxUnit input `no_foreign_system_exclusive_se_income` and
  source-backed Judgment `self_employment_tax_pipeline_domain_is_valid`.
- Gated the existing OASDI, hospital-insurance, and combined ordinary SECA tax
  outputs behind that Judgment without renaming any existing surface.
- Added `seca-foreign-system-boundary-fails-closed`, which preserves observable
  pre-relief SE income of `$46,175` but returns zero for all three public taxes.
- Pinned proof validation passes all 21 SECA atoms; all 14 current SECA
  companion cases pass.
- Aligned both local section 1401(b)(2)(B) proof excerpts and the `wages`
  input contract to the full coordination language: wages as defined in
  section 3121(a), taken into account in determining the tax imposed by
  section 3101(b)(2).
- Documented exactly that the record's broken `source_url` metadata is tracked
  as `axiom-corpus#514` and does not invalidate the record text's hash-chained
  provenance.
- Pinned Additional Medicare proof validation passes all 17 atoms and all 14
  companions pass, so the adjudicated deferred fail-closed fallback is not
  triggered.
- Removed the non-operative exact-$400 helper, its standalone input/case, and
  its now-unused explicit threshold import.
- Reworked `seca-floor-below` and `seca-floor-above` as Person cases that assert
  the imported section 1402(b)(2) `$400` threshold, the nonresident-exclusion
  control Judgment, and operative `self_employment_income` / OASDI-base outputs
  directly at `399.8755` and `400.799`.
- Documented in both cases that exact `N = 400` requires gross input
  `800000 / 1847`, which has no finite decimal expansion.
- Canonical SECA validation and all 19 proof atoms pass; all 13 revised SECA
  companions pass.
- Refreshed the Additional Medicare proof-import pin to the finalized SECA
  module hash
  `sha256:3668c1e3e86ff0625cab484bc1a1623ac233a0c401bdef71fd2a2832a51af72b`.
- Reconciled `oracle-coverage-pending.yaml` as an exact one-for-one swap from
  the retired floor-helper Judgment to
  `self_employment_tax_pipeline_domain_is_valid`; the ceiling remains `2327`,
  and pinned `oracle-coverage-pending check` reports no problems or stale
  entries.
- Re-ran the full focused battery from a canonical-basename checkout at the
  current committed head: 3/3 canonical validations, 46/46 proof atoms
  (10 NIIT, 19 SECA, 17 Additional Medicare), and 42/42 companions
  (15 NIIT, 13 SECA, 14 Additional Medicare).
- Confirmed that the deterministic authoring checks accept the adjudicated
  section 1401(b)(2)(B) wording, so no deferred fail-closed fallback is needed.
- Pinned signing dry-run identifies the expected three surtax manifests
  covering six files. The actual signing key is absent from this session, so
  no manifest was rewritten or falsely attested.

## Next

1. Run the remaining non-signing repository gates and full pytest.
2. Write `scratchpad/fix2-1003-DONE.md` with the exact signing boundary and
   gate results.
