# Worker B progress

## State

The case inventory is complete. The current task is to finish the retained-law
and engine-source trace, reproduce the PolicyEngine result on version 1.767.3,
and prepare the case dispositions.

## Done

- Confirmed the assigned worktree and clean starting branch.
- Loaded the GitNexus debugging and exploration workflows.
- Inventoried all five ECPS reports. The corrected class contains 12
  one-person minor households with PolicyEngine-only eligibility:
  Alabama 4, Massachusetts 1, North Carolina 3, South Carolina 2, and
  Tennessee 2.
- Confirmed that 11 cases have $217,027.52 in 2026 earned income and one
  Alabama case has $21,866.20; every case has both eligibility and benefit
  mismatches.
- Traced the repeated $217,027.52 to a $198,505 base-data point mass multiplied
  by the common 2026 uprating factor 1.09331. In the pinned Populace artifact,
  all 990 persons at $198,505 are synthetic PUF clones (194 are minors and 66
  are minors in one-person households), so this is a synthetic-clone artifact,
  not a raw ECPS top-code.
- Confirmed the dashboard reports were generated with PolicyEngine US 1.752.2;
  the assigned 1.767.3 behavior still requires a live reproduction.

## Next

- Read the retained text of 7 CFR 273.1 and 273.9.
- Trace the relevant Axiom and PolicyEngine implementations.
- Build a minimal PolicyEngine reproduction and decide the legally correct
  disposition.
