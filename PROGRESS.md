# ACA Premium Tax Credit Compose Progress

## State

- Branch: `fed-parity/aca-ptc`
- Base: `origin/main` at `c86b2f62`
- Phase: compose module and nine-case companion pass pinned validation,
  proof validation, and exact-pinned-engine execution; generated artifacts and
  full gates next.
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

## Next

1. Run the official oracle-pending classification sync and inspect whether the
   ledger changes.
2. Attempt the approved manual-composition signing path without fabricating
   credentials; record an explicit TODO if the HMAC key remains unavailable.
3. Run the full local gate battery and record every result in the required
   summary.
