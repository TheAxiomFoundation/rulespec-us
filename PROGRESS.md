# Progress

## State

Paragraphs (a), (c), and (d) are implemented in isolated child modules, their
umbrella deferrals are removed from the parent, and the complete pinned
RuleSpec suite passes. Running repository and protected-artifact gates next.

## Done

- Read the encoder preamble and repository instructions.
- Confirmed the worktree is clean and scoped to the assigned branch.
- Confirmed the verified paragraph (e) sequence and frozen `programs/` tree are
  out of scope.
- Read every required sibling module and companion test.
- Extracted the authoritative 2026-07-09 text for every assigned paragraph.
- Reviewed federal and state analogs for initial-month proration, prospective
  income, and expense timing.
- Confirmed that child modules avoid rebinding existing paragraph (e) and
  state-plan composition inputs.
- Added and passed a regression case proving the protected household still has
  net income of $226 and a monthly allotment of $478.
- Added `273/10/a.yaml` and its companion tests for application-month
  eligibility, the federal initial-month definition, both proration elections,
  release-date treatment, rounding down, and the post-proration $10 issuance
  threshold.
- Removed the satisfied paragraph (a) umbrella deferral from `273/10.yaml`
  without changing any paragraph (e) rule, formula, or ordering.
- Added direct paragraph (a)(2)-(4) rules and tests for prospective
  recertification, late and timely recertification initial-month treatment,
  reuse of an application across anticipated eligibility changes, and
  month-specific allotment variation.
- Narrowed the remaining paragraph (a) deferrals to State fiscal-period
  configuration, retrospective recertification budgeting, the
  cross-referenced agency-error remedy, and certification-period assignment.
- Added `273/10/c.yaml` and its companion tests for reasonable-certainty
  budgeting, historical income indicators, receipt-month timing, weekly and
  biweekly conversion, lump sums, held wages, pay-cycle normalization, and
  contract, self-employment, and educational-income averaging.
- Removed the satisfied paragraph (c) umbrella deferral from `273/10.yaml`
  while leaving the paragraph (e) rules unchanged.
- Narrowed the remaining paragraph (c) deferrals to the cross-referenced
  change-reporting and self-employment procedures and the State-selected
  statewide averaging method.
- Added `273/10/d.yaml` and 57 companion cases for disallowed and reimbursed
  expenses, billed/due timing, arrearages and nonduplication, fluctuating and
  less-than-monthly averaging, one-time and 24-month medical elections,
  anticipated utility and nonutility expenses, medical-change timing, weekly
  and biweekly conversion, energy-assistance proration, and prospective
  child-support method selection.
- Required every averaging amount to be explicitly post-disallowance, composed
  conversion directly from paragraph (d)(1), froze one-time medical averaging
  divisors at the election month, and rejected overlapping State utility and
  expense-conversion methods.
- Narrowed unresolved paragraph (d) work to cross-section medical-change
  processing, the obsolete printed dependent-care age-two cap, SSI-linked
  restored deductions, and optional child-support composition or retrospective
  budgeting that depends on sections 273.9 or 273.21.
- Confirmed the paragraph (d) child compiles as 25 rules, proof-validates 42
  atoms, and passes all 57 companion cases with the pinned encoder and engine.
- Removed the satisfied paragraph (d) umbrella deferral from `273/10.yaml`
  without changing any paragraph (e) rule, formula, or ordering.
- Added non-executable parent provenance records that point paragraphs (a),
  (c), and (d) to representative outputs in their child modules without
  introducing a circular import.
- Confirmed the integrated parent validates, proof-validates 24 atoms, compiles
  52 executable/imported rules, and passes all six companion cases, including
  the protected $226 net-income and $478 allotment benchmark.
- Regenerated and checked the reverse citation index; the paragraph (a), (c),
  and (d) modules now appear as module- and proof-level dependents of the
  section 273.10 corpus provision.
- Ran the pinned encoder against the parent and all three child modules before
  the final scope tightening: validation passed; proof validation passed for
  134 atoms; the money-proof gate found zero missing atoms; all modules
  compiled as of 2026-07-09; and all 122 then-existing companion cases passed.
- Confirmed the expanded paragraph (a) child validates, proof-validates 28
  atoms, compiles 71 rules, and passes all 15 companion cases.
- Identified narrow, judgment-heavy matters that must remain deferred: fiscal
  accounting-period construction, retrospective budgeting and
  certification-period assignment; State income averaging methods; and
  cross-referenced medical/SSI/child-support case actions.

## Next

- Run repository-level regression and protected-artifact gates.
- Update this log with final gate results, push the branch, and open the required
  draft PR.
