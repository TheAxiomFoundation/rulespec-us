# Worker B progress

## State

The case inventory, retained-law review, and engine-source trace are complete.
Axiom is correct for this class; PolicyEngine incorrectly excludes the earnings
of a school-age minor living alone. The current task is to preserve the exact
1.767.3 reproduction and prepare the report and proposed dispositions.

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
  a live 1.767.3 reproduction confirms the same mechanism.
- Confirmed from retained 7 CFR 273.1(a)(1) and (b)(1)(ii)-(iii) that a minor
  living alone may form a one-person SNAP household; no Axiom rule or ECPS
  adapter imposes a minor-head prohibition.
- Confirmed from retained 7 CFR 273.9(a), (b)(1)(i), and (c)(7) that the
  household must count these wages. The under-18 student exclusion requires
  co-residence with a parent or a household member exercising parental
  control, which a one-person household cannot satisfy.
- Traced PolicyEngine US 1.767.3 to `snap_excluded_child_earner`: it checks only
  age and K-12 status and omits the parent/parental-control condition. A live
  one-person simulation therefore zeroes $217,027.52 of annual wages, reports
  zero gross SNAP income, and awards SNAP.
- Determined that there is no case-relevant encode or adapter change to make in
  this worktree. The broader deferred 7 CFR 273.9(b)/(c) composition work is
  outside this class and belongs to the shared federal owner.
- Added and executed `tools/reproduce_policyengine_snap_teen.py` against the
  exact cached PolicyEngine US 1.767.3 wheel with PolicyEngine Core 3.26.0 and
  SPM Calculator 0.2.0 for 2026-01. Both AL age 17 and NC age 15 reproduce
  zero counted income, eligibility, and a $298 monthly benefit; the
  school-status and age-18 controls count income and return zero benefit.

## Next

- Run the existing federal companion tests as regression evidence.
- Write `WORKER-REPORT.md` with the case table, exact retained-law citations,
  root cause, issue draft, and proposed suite dispositions.
- Record final validation and commit the completed report.
