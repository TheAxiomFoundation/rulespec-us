# Federal benefit eligibility compose progress

## State

- Branch: `fed-parity/benefit-elig`
- Starting commit: `c86b2f62511b7ff9d5351c98ca03b87e3cc41042`
- Phase: both eligibility composes and reverse source index complete; repository-wide gates next.
- Network fetch was unavailable because `github.com` could not be resolved. The cached `origin/main` and `HEAD` both resolve to the stated starting commit.

## Done

- Confirmed the checkout was clean and on the requested branch before edits.
- Read `tier2-scoping-REPORT.md` sections 1 (WIC) and 4 (Head Start).
- Read `recon-rulespec-worker.log`, including the federal compose, bridge-toolchain, validation, and signing discipline.
- Read the encoded WIC and Head Start regulatory modules and companions:
  - `us/regulations/7-cfr/246/7/c.yaml`
  - `us/regulations/7-cfr/246/7/d.yaml`
  - `us/regulations/7-cfr/246/7/e.yaml`
  - `us/regulations/45-cfr/1302/12.yaml`
  - `us/regulations/45-cfr/1302/12/b.yaml`
- Confirmed the required modeling boundaries:
  - WIC nutritional risk remains an explicit runtime determination; it is never silently assumed.
  - Head Start and Early Head Start outputs express regulatory eligibility, not selection, enrollment, take-up, or imputed service value.
  - Federal poverty-guideline dollar amounts remain caller-supplied runtime inputs.
- Added the WIC person-level eligibility compose and a 21-case companion:
  - all five encoded category facts crossed with income below, at, and above the 185-percent Federal maximum;
  - a no-category negative control;
  - a documented SNAP adjunctive-eligibility override;
  - the encoded pregnant-applicant/unborn-child income-guideline exception;
  - residency, certification, and nutritional-risk blockers.
- Declared the WIC category classification, State guidelines below the Federal
  maximum, and competent-professional nutritional-risk determination as
  explicit boundaries.
- Declared current-rate/unemployment and instream-migrant income procedures as
  completed upstream projections rather than silently inferring them.
- Passed targeted WIC schema/CI validation, proof validation (12 atoms), and
  all 21 companion cases.
- Added the Head Start/Early Head Start person-level eligibility compose and a
  29-case companion:
  - ordinary income below, at, and above 100 percent of the poverty line;
  - public-assistance, potential-assistance, homelessness, and foster-care
    paragraph-(c) routes;
  - the strict-below-130-percent/35-percent additional allowance and its two
    program-policy gates;
  - the child-only 10-percent exception;
  - Early Head Start, preschool, transition, school-date, school-attendance,
    pregnancy, Tribal, and Migrant or Seasonal branches.
- Added explicit composition bridges so the paragraph-(c) failure fact is
  derived rather than caller-asserted and the shared paragraph-(b) age fact is
  contextualized for Tribal versus Migrant or Seasonal programs.
- Route-specific age rechecks prevent a dual Tribal/Migrant program context
  from satisfying one route with the other route's age fact; two explicit
  cross-contamination regressions cover both directions.
- Declared actual selection, enrollment, funded slots, take-up, service value,
  verification compliance, small-community criteria, continuity, records, and
  staff-policy administration outside the scalar eligibility outputs.
- Passed targeted Head Start schema/CI validation, proof validation (32
  atoms), and all 29 companion cases.
- Resolved both actionable findings from the independent read-only review.
- Regenerated `.axiom/index/provisions_to_rules.json`; the check mode confirms
  3,944 provisions, 4,670 edges, and 4,435 modules are current.

## Next

1. Run the full repository validation battery and signing dry-run.
2. Resolve any independent-review findings.
3. Write `build-benefit-elig-SUMMARY.md` and `build-benefit-elig-DONE.md` with case tables, boundaries, gates, commit SHAs, and oracle-suite notes.
