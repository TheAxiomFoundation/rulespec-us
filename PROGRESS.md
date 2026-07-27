# Progress

## State

Paragraphs (a) and (c) are implemented and tested. Implementing and reviewing
the isolated paragraph (d) child module next.

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
- Narrowed the remaining paragraph (a) deferrals to State fiscal-period
  configuration and certification/recertification case-action workflows.
- Added `273/10/c.yaml` and its companion tests for reasonable-certainty
  budgeting, historical income indicators, receipt-month timing, weekly and
  biweekly conversion, lump sums, held wages, pay-cycle normalization, and
  contract, self-employment, and educational-income averaging.
- Removed the satisfied paragraph (c) umbrella deferral from `273/10.yaml`
  while leaving the paragraph (e) rules unchanged.
- Narrowed the remaining paragraph (c) deferrals to the cross-referenced
  change-reporting and self-employment procedures and the State-selected
  statewide averaging method.
- Identified narrow, judgment-heavy matters that must remain deferred: fiscal
  accounting-period construction and recertification workflow; State income
  averaging methods; and cross-referenced medical/SSI/child-support case
  actions.

## Next

- Finish encoding and testing the paragraph (d) child module and remove its
  satisfied umbrella deferral from the parent.
- Run repository validation, update this log, push the branch, and open the
  required draft PR.
