# ACA Premium Tax Credit Compose Progress

## State

- Branch: `fed-parity/aca-ptc`
- Base: `origin/main` at `c86b2f62`
- Phase: implementation, local verification, and the required build summary
  are complete; signing remains an external credential-holder TODO.
- Module home: `us/policies/aca/ptc_pipeline.yaml`, following the federal
  `us/policies/...` executable-RuleSpec convention.

## Done

- Read the mandatory recon report in full, including compose pattern B6, discipline B7, PR gates C11-C12, and the federal-compose checklist.
- Read `GRID-CONTRACT.md` in full and recorded that the companion must preserve all six P4 inputs exactly.
- Read the required section 36B, Rev. Proc. 2025-25, and Ohio compose/template modules in the specified order.
- Confirmed the worktree is clean and on `fed-parity/aca-ptc` at the requested base.
- Identified the core legal/composition boundary: the Rev. Proc. supplies the indexed 2026 initial/final percentages, section 36B(b)(3)(A) supplies linear interpolation, section 36B(c)(1)(A) supplies the inclusive 100%-400% gate, and section 36B(b) supplies monthly assistance mechanics.
- Verified that 2026 coverage uses the 2025 HHS poverty guideline under
  section 36B(d)(3)(B); the needed contiguous-48 values are $15,650 for one
  person, $21,150 for two people, and $32,150 for four people.
- Confirmed that direct import of `36B/b/3/A#applicable_percentage` cannot
  accept the Rev. Proc. endpoints because the upstream module closes over its
  unindexed base tables. The compose instead imports the Rev. Proc. band and
  endpoints and proofedly applies the same statutory linear interpolation.
- Drafted `us/policies/aca/ptc_pipeline.yaml` with six explicit runtime inputs,
  the 100%-400% gate, annual-to-monthly bridges, a 12-month annual result, and
  explicit employer-coverage, QSEHRA, lawfully-present, relational, regulatory
  rounding, and filing-form boundaries.
- Added `us/policies/aca/ptc_pipeline.test.yaml` with all six exact P4 cases
  plus exact 100% FPL, exact 400% FPL, and contribution-above-SLCSP cases.
  Comments show the independent band, rate, contribution, benchmark-excess,
  and enrolled-premium cap arithmetic.
- Passed `axiom-encode` 0.2.1200 validation and proof validation (34 atoms).
- Built `axiom-rules-engine` at the exact pinned commit
  `ffd8213271947b0189a9dd61a055c1e0e78908a0` in a temporary directory and
  passed all 9 companion cases.
- Ran focused layout/manifest/index pytest: 17 passed; the only failure was the
  expected stale reverse index, which is the next generated-artifact step.
- Regenerated `.axiom/index/provisions_to_rules.json`; the 29-line diff adds
  only the new pipeline's four verified source references.
- Ran the official oracle-pending sync and check. The semantic result adds the
  pipeline's 16 executable outputs, drains 14 outputs that are no longer
  pending, and raises the ceiling from 1,741 to 1,743. Preserved the existing
  ledger formatting instead of committing a whole-file serializer rewrite;
  the official check passes with 1,743 applied and zero stale.
- Inspected the Wisconsin manual-composition manifest and ran the pinned
  `sign-applied-files` dry run with `manual_exception: composition`; it
  correctly selected the new pipeline and companion as one manifest group.
- Attempted real signing. It stopped before writing because
  `AXIOM_ENCODE_APPLY_SIGNING_KEY` is not set. No signature or manifest was
  fabricated; `.axiom/encoding-manifests/us/policies/aca/ptc_pipeline.json`
  remains an explicit credential-holder TODO.
- Completed a final section 36B eligibility-boundary review. The module now
  states that fixtures are unmarried or married filing jointly and not
  claimable as dependents, and explicitly defers sections 36B(c)(1)(C)-(D)
  because those filing-status and section 151 facts are absent from the
  aggregate TaxUnit surface. Validation, all 34 proof atoms, and all nine
  companion cases still pass; the reverse index now includes those two cited
  corpus fragments.
- Final full repository pytest passed: 55 tests passed with one warning for
  the existing set of 19 unmanifested modules, including this credential-
  blocked pipeline.
- Final repository-wide money-proof validation passed: 118 missing atoms among
  2,586 monetary obligations, within the ratchet allowance of 151.
- Final reverse-index check passed at 3,947 provisions, 4,672 edges, and 4,434
  modules. Final oracle-pending check passed at 1,743 declared/applied and zero
  stale.
- Final full program-artifact check composed and compiled all 32 programs.
- Final all-companion sweep exercised 4,428 files and 15,562 cases. All nine
  ACA PTC cases passed. Four failures remain in two unchanged
  `us/statutes/26/32.test.yaml` cases because of unresolved section 32(c)(2)
  output/input references; none is in a branch-changed RuleSpec path.
- Final `guard-generated` fails only for the two new ACA files because the
  signing key is unavailable and therefore their manifest cannot be created.

## Next

1. Have a credential holder run the recorded pinned signing command, then
   rerun the manifest/encoder-first gates.
2. Address the pre-existing section 32 companion references and the three
   program allowlist entries that now compile in their own maintenance lane.
