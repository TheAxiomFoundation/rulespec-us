# Payroll program closure progress

## State

Assessment in progress. The checkout is clean on `closure/payroll-3101` at the
locally cached `origin/main` commit `6b0773d3f7fa6719f208154f3e609e292ab7abe7`.
Refreshing the remote failed because DNS/network access is unavailable.

## Done

- Read the closure-sprint encoder preamble and repository `CLAUDE.md`.
- Confirmed the task-specific exception permits a new program under
  `programs/us/payroll/`.
- Confirmed SNAP program files, toolchain/CI/CODEOWNERS, comparison suites, and
  committed oracle reports are out of scope.
- Confirmed the existing payroll program and cited section encodings are present
  in the canonical `rulespec-us` checkout.

## Next

1. Audit all four certificate verdict requirements and the corpus universe by
   citation path across every inventory record.
2. Write the assessment before implementing the program.
3. Add the employee payroll-tax program, boundary tests, and golden case only
   where the statutory and repository evidence supports them.
4. Add mapping-only oracle entries if a safe writable `axiom-oracles` checkout
   is available.
5. Run permitted checks, request an independent review, update this file, push
   if possible, and open draft PRs if network access returns.
