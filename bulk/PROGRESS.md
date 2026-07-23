# Medicaid MAGI household income compose progress

## State

The executable compose and complete hand-computed companion are implemented.
Focused gates pass, and the reverse index is regenerated and current. The
remaining full pytest rerun and fresh-snapshot oracle/program-artifact/signing
checks are next.

## Done

- Confirmed the worktree is clean on `fed-parity/medicaid` at `c86b2f62`.
- Read the campaign scratchpad sources, the merged-lane compose precedent, the
  Medicaid regulation modules, the current eCFR text, CMS FAQ Q6, PolicyEngine
  mechanics, and the oracle harness boundary.
- Confirmed that the disregard is an overall-eligibility backstop: it applies
  only when raw income exceeds the highest applicable MAGI standard and the
  5-point subtraction cures that excess.
- Confirmed the compose belongs at
  `us/policies/medicaid/magi_household_income_pipeline.yaml`, with a sibling
  companion and no root ProgramSpec.
- Confirmed `42 CFR 435.552` is outside the dependency graph and will not be
  imported or edited.
- Implemented
  `us/policies/medicaid/magi_household_income_pipeline.yaml`, including the
  paragraph-(d)/(f) member sum, raw and final FPL ratios, exact highest-band
  disregard gate, runtime-boundary check, and guarded adult and
  parent/caretaker consumers.
- Proved on the pinned engine that relation rows are independently evaluated,
  nonmembers are filtered, and the existing 435.119 and 435.110 rules consume
  the compose's private bridges.
- Added an initial hand-computed companion covering a positive
  counted-income-plus-cash member contribution and the inclusive exact-138%
  adult boundary. Focused validate, proof-validate (28 atoms), and pinned
  engine tests (2/2) pass.
- Expanded the companion to all six cent-level boundary points around 133%
  and 138% across four applicant-specific assembly variants: tax filer,
  claimed-dependent child with excluded income, non-filer with spouse and a
  filtered roommate, and filer parent with required-filer child income.
- Added the complete cash-support gate matrix, zero-income/no-floor behavior,
  both sides of the lower-parent-band highest-standard guard, and invalid
  family-size/FPL runtime cases. All 33 companion cases pass on the pinned
  engine; proof validation checks 28 atoms and the money-proof ratchet reports
  zero missing monetary proofs.
- Regenerated `.axiom/index/provisions_to_rules.json`; its fresh `--check`
  reports 3,944 provisions, 4,672 edges, and 4,434 modules. The first repo
  pytest pass had 54 passing tests and only the expected pre-regeneration
  stale-index failure.

## Next

- Rerun repository pytest against the regenerated index.
- Run oracle-pending sync/fresh check, canonical-basename program artifacts,
  and signing selection dry-run.
- Produce the scratchpad summary and done marker, leaving manifest signing to
  the main lane after a dry-run selection proof.
