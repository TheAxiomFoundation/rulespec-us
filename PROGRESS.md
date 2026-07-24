# PR #1003 residual fix — round 2

## State

In progress on branch `fed-parity/surtaxes`. The ordinary SECA section 1401(c)
guard is implemented and locally proved; wage-coordination provenance and
operative floor coverage remain. No pushes, GitHub writes, PR-body edits, or
`us/statutes` edits are in scope.

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

## Next

1. Align the wage-input contract and proof excerpt to the actual pinned
   section 1401(b)(2)(B) text, then run the deterministic authoring checks.
2. Rework both floor straddle companions to exercise the imported operative
   floor outputs.
3. Refresh the downstream SE import hash and required generated artifacts, run
   focused gates and full repository
   pytest, and write `scratchpad/fix2-1003-DONE.md`.
