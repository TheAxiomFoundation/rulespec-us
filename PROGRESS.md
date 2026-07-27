# Progress

## State

Paragraphs (a), (c), and (d) are implemented in isolated child modules, their
umbrella deferrals are removed from the parent, and all executable, proof,
companion-test, reverse-index, regression, and scope gates pass. Delivery is
ready except that the protected-artifact manifests cannot be refreshed without
the unavailable signing key.

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
- Rejected contradictory simultaneous weekly and biweekly income-frequency
  configurations instead of silently selecting the weekly branch.
- Removed the satisfied paragraph (c) umbrella deferral from `273/10.yaml`
  while leaving the paragraph (e) rules unchanged.
- Narrowed the remaining paragraph (c) deferrals to the cross-referenced
  change-reporting and self-employment procedures and the State-selected
  statewide averaging method.
- Added `273/10/d.yaml` and companion cases for disallowed and reimbursed
  expenses, billed/due timing, arrearages and nonduplication, fluctuating and
  less-than-monthly averaging, one-time and 24-month medical elections,
  anticipated utility and nonutility expenses, medical-change timing, weekly
  and biweekly conversion, energy-assistance proration, and prospective
  child-support method selection.
- Added paragraph (d)(4) judgments and five branch cases for voluntarily
  reported medical-expense increases, the two exclusive State verification
  timing choices, and decrease/ineligibility action before any required
  verification deadline.
- Required every averaging amount to be explicitly post-disallowance, composed
  conversion directly from paragraph (d)(1), froze one-time medical averaging
  divisors at the election month, and rejected overlapping State utility and
  expense-conversion methods and contradictory weekly/biweekly frequencies.
- Narrowed unresolved paragraph (d) work to execution and notice mechanics for
  the now-encoded medical-change deadlines, the obsolete printed
  dependent-care age-two cap, SSI-linked restored deductions, and optional
  child-support composition or retrospective budgeting that depends on
  sections 273.9 or 273.21.
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
- Confirmed the expanded paragraph (d) child validates, proof-validates 48
  atoms, compiles 31 rules, and passes all 63 companion cases.
- Rebased onto the current `origin/main` after two unrelated upstream
  CI/oracle merges landed; the rebase was conflict-free.
- Reran the final pinned suite after the rebase: all four modules validate,
  proof validation checks 151 atoms, the money-proof gate reports zero missing
  atoms, compilation succeeds at 52/71/33/31 rules, and all 139 companion
  cases pass.
- Confirmed the reverse index is current, forbidden surfaces have an empty
  diff, and the 18 paragraph (e) executable rule objects remain object-for-object
  identical to `origin/main`; the golden $226/$478 case passes.
- Ran the full repository tests: 72 passed and one failed solely because the
  existing parent encoding manifest is stale; new child manifests are also
  required by the stricter generated-artifact guard.
- Confirmed the signing dry run identifies four manifests covering eight
  RuleSpec files. Actual signing cannot run because
  `AXIOM_ENCODE_APPLY_SIGNING_KEY` is unavailable, so `guard-generated`
  reports those same eight files.
- Identified narrow, judgment-heavy matters that must remain deferred: fiscal
  accounting-period construction, retrospective budgeting and
  certification-period assignment; State income averaging methods; and
  cross-referenced medical/SSI/child-support case actions.

## Next

- Push the branch and open the required draft PR, documenting the signing-key
  blocker for the four generated manifests.
- Once an authorized signer is available, generate and commit the manifests,
  then rerun `guard-generated` and the manifest-sync pytest.
