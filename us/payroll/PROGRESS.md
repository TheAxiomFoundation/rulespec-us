# Payroll program closure progress

## State

Assessment and the narrow supported-domain program slice are complete. The new
integration publishes three cap-aware employee FICA component outputs and
fails closed outside explicit wage-domain boundaries. It is a build toward a
certificate, not a certificate claim: corpus-pin drift and computed
conformance/closure/execution evidence remain unresolved.

## Done

- Read the closure-sprint encoder preamble and repository `CLAUDE.md`.
- Confirmed the task-specific exception permits a new program under
  `programs/us/payroll/`.
- Confirmed SNAP program files, toolchain/CI/CODEOWNERS, comparison suites, and
  committed oracle reports are out of scope.
- Confirmed the existing payroll program and cited section encodings are present
  in the canonical `rulespec-us` checkout.
- Counted the proposed closure universe by exact citation path across every
  statute inventory at both the pinned corpus commit and cached corpus
  `origin/main`.
- Wrote `h1-payroll-assessment.md` before making any program change.
- Confirmed the existing OASDI program imports the section 3121(a)(1)
  wage-base exclusion but does not bind that payment-level output into the
  section 3101(a) person-level tax.
- Added `us/payroll/employee-fica-tax` as a sibling rather than changing the
  narrower existing OASDI program.
- Added a grounded integration module with separate pre-cap OASDI, Person
  Medicare, and TaxUnit Medicare wage contracts.
- Added ten companion cases covering wages below, exactly at, and above the
  $184,500 base; exactly at and above the Additional Medicare thresholds; and
  fail-closed section 3101(c) domain boundaries.
- Passed proof validation, all ten new RuleSpec cases, relevant repository
  structure tests, and pinned composer/engine compilation of the new program.

## Next

1. Add and validate the hand-checkable golden case.
2. Add mapping-only oracle entries in a fresh writable checkout without running
   any comparison suite or regenerating any report.
3. Run permitted checks, request an independent review, update this file, push
   if possible, and open draft PRs if network access returns.
