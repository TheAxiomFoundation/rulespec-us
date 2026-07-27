# Payroll program closure progress

## State

Assessment complete. The employee-side federal payroll-tax candidate is not
certifiable yet. The immediate blockers are a real OASDI wage-base integration
gap, corpus-pin drift, and the absence of computed closure/execution evidence.
The checkout remains on `closure/payroll-3101`, based on locally cached
`origin/main` commit `6b0773d3f7fa6719f208154f3e609e292ab7abe7`.

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

## Next

1. Decide whether a narrowly stated, tested single-employer integration can be
   added without implying that the deferred section 3121 wage definition is
   complete; otherwise record an explicit implementation deferral.
2. If confidence supports it, add the sibling program, boundary integration
   tests, and golden case.
3. Add mapping-only oracle entries in a fresh writable checkout without running
   any comparison suite or regenerating any report.
4. Run permitted checks, request an independent review, update this file, push
   if possible, and open draft PRs if network access returns.
