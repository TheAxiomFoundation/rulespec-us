# Progress: 7 CFR 273.24(g)

## State

Paragraph (g) is encoded with person-level application and time-limit effects,
the State fiscal-year allocation cap, allocation charging, and
nondiscrimination. The module passes the pinned encoder validation pipeline,
proof validation, and all 17 companion cases. Repository-wide checks and
direct-downstream import-hash maintenance remain.

## Done

- Confirmed the assigned slice is 7 CFR 273.24(g), ABAWD State discretionary
  exemptions.
- Confirmed the frozen `programs/` tree and other protected files will not be
  edited.
- Confirmed the branch is `closure/enc-273-24g`, based on `origin/main`.
- Read the `2026-07-09` corpus text for 7 CFR 273.24(g).
- Read the required sibling modules and companion tests for sections 273.9,
  273.10, 273.2(j), and 273.11(c).
- Confirmed paragraph (g) requires:
  - a covered-individual predicate and a person-level State exemption choice;
  - an 8 percent fiscal-year average-monthly allocation cap based on FNS's
    adjusted covered-individual estimate;
  - separate treatment for exemptions provided to an otherwise-exempt person;
  - nondiscriminatory State administration.
- Confirmed paragraph (g) gives no executable formula for FNS's estimate and
  no rounding rule, so the final adjusted estimate will remain an input and
  the allocation output will be decimal-valued.
- Confirmed paragraph (h) carryover/adjustment mechanics and paragraph (i)
  reporting are outside this slice.
- Removed the paragraph (g) deferred output while preserving the unrelated
  paragraph (j) deferral.
- Added the 8 percent parameter, the defined State caseload measure, the
  decimal-valued FNS-adjusted State allocation, and the fiscal-year cap
  compliance judgment.
- Added the covered-individual predicate, State-assignment application
  predicate, and the separate allocation-charge predicate for an exemption
  provided to someone otherwise exempt that month.
- Composed allocation charging from the legally effective exemption predicate,
  so an attempted assignment to a non-covered person neither applies nor
  consumes the State allocation.
- Composed an applied discretionary exemption into the existing ABAWD
  time-limit-inapplicable and time-limit-eligible results.
- Added the paragraph (g)(4) State nondiscrimination judgment.
- Added companion coverage for both covered-individual entry branches, every
  exclusion, assigned and unassigned covered recipients, the resulting
  time-limit effect, the otherwise-exempt allocation exception, the exact
  8 percent boundary, and nondiscrimination.
- Passed:
  - pinned `axiom-encode` proof validation (25 atoms);
  - pinned `axiom-encode` companion execution (17 cases);
  - pinned encoder CI validation with this worktree supplied explicitly as
    the policy root.
- Identified a pinned CLI routing defect: because this worktree is not named
  `rulespec-*`, the ordinary `validate` entry point resolves absolute legal
  test inputs against a stale sibling checkout. The same pinned validation
  pipeline passes when supplied this worktree as its policy root.

## Next

- Update the directly affected 7 CFR 273.11(c) proof import hash and rerun its
  companion tests.
- Run repository-wide pytest and reverse-index checks.
- Refresh and sign the encoder apply manifest, then run the generated-file
  guard.
- Push the branch and open the required draft PR.
