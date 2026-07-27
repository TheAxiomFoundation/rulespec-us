# Progress: 7 CFR 273.24(g)

## State

Authoritative-text and repository-convention review is complete. The
paragraph (g) implementation shape is settled; no RuleSpec implementation
changes have been made yet.

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

## Next

- Add the paragraph (g) allocation, covered-person, application, time-limit,
  allocation-charge, and nondiscrimination rules.
- Extend the companion tests across the covered-individual branches and the
  8 percent cap boundary.
- Update only directly affected import metadata/tests if validation shows that
  the changed federal output requires it.
