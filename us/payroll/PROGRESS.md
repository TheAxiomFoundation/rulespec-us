# Payroll program closure progress

## State

Assessment, the narrow supported-domain program slice, the golden case, and
the mapping-only oracle entries are complete. Independent reviews found no
arithmetic or forbidden-scope defect; their reporting and comparability
findings have been resolved. This remains a build toward a certificate, not a
certificate claim: corpus-pin drift and computed conformance, exercise,
closure, and execution evidence remain unresolved.

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
- Added eleven companion cases covering wages below, exactly at, and above the
  $184,500 base; exactly at and above the Additional Medicare thresholds; and
  fail-closed section 3101(c) domain boundaries.
- Passed proof validation, all eleven new RuleSpec cases, relevant repository
  structure tests, and pinned composer/engine compilation of the new program.
- Added a $300,000 single-filer golden case with the section 3101(a),
  3101(b)(1), and 3101(b)(2) derivation shown line by line, plus a matching
  Person companion case.
- Added and committed three exact PolicyEngine mappings in the separate
  `axiom-oracles` checkout without running a comparison suite or changing a
  committed report.
- Tightened each mapping's direct-comparison contract to require equality
  between the RuleSpec wage fact and PolicyEngine's corresponding
  `payroll_tax_gross_wages` amount; the Additional Medicare mapping also
  requires zero taxable self-employment income.
- Revalidated the mapping registry after the independent oracle review.
- Updated the assessment after the independent RuleSpec review: the completed
  narrow-profile integration is no longer listed as missing, and the
  always-imported SSA guidance root makes the total adequate-snapshot closure
  universe 143 paths (142 statutory paths plus one guidance path).
- Confirmed the composed artifact retains the legacy uncapped statute output
  internally; downstream evidence must bind the three exact program output
  IDs rather than treating every derived artifact rule as public.

## Next

1. Commit the final report, attempt delivery to the closure-sprint output file,
   and record the sandbox result.
2. Push both branches and open one draft PR per repository if network access
   permits.
3. Defer bridge discovery/execution support, comparison evidence, the
   143-path closure ledger, and public executable evidence to post-freeze work.
