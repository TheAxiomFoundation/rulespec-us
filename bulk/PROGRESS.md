# Medicaid MAGI household income compose progress

## State

Designing the applicant-scoped relation aggregate and highest-standard-only
5-percentage-point FPL comparison after completing source and convention
research.

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

## Next

- Prove the imported relation/`sum_where` syntax against the pinned engine.
- Implement the executable compose and its declared runtime boundaries.
- Add the hand-computed 133/138 grid across filer, dependent, non-filer, and
  child-income household variants, plus cash-support and zero/edge cases.
- Run the complete campaign gate battery and fix any failures.
- Produce the scratchpad summary and done marker, leaving manifest signing to
  the main lane after a dry-run selection proof.
