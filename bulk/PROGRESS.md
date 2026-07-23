# Medicaid MAGI household income compose progress

## State

The executable applicant-scoped relation aggregate, highest-standard-only
5-percentage-point FPL comparison, and guarded section 435.119/435.110
consumer bridges are implemented and green in an initial pinned-engine smoke
companion. Expanding the companion to the complete boundary matrix is next.

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

## Next

- Add the hand-computed 133/138 grid across filer, dependent, non-filer, and
  child-income household variants, plus cash-support and zero/edge cases.
- Run the complete campaign gate battery and fix any failures.
- Produce the scratchpad summary and done marker, leaving manifest signing to
  the main lane after a dry-run selection proof.
