# Federal benefit eligibility compose progress

## State

- Branch: `fed-parity/benefit-elig`
- Starting commit: `c86b2f62511b7ff9d5351c98ca03b87e3cc41042`
- Phase: implementation and validation complete; scratchpad reports and final
  progress-ledger cleanup next.
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
- Added the WIC person-level eligibility compose and a 22-case companion:
  - all five encoded category facts crossed with income below, at, and above the 185-percent Federal maximum;
  - a no-category negative control;
  - a documented SNAP adjunctive-eligibility override;
  - the encoded pregnant-applicant/unborn-child income-guideline exception;
  - a mismatched-pregnancy negative proving that the unborn-child exception
    cannot passport another WIC category;
  - residency, certification, and nutritional-risk blockers.
- Declared the WIC category classification, State guidelines below the Federal
  maximum, and competent-professional nutritional-risk determination as
  explicit boundaries.
- Declared current-rate/unemployment and instream-migrant income procedures as
  completed upstream projections rather than silently inferring them.
- Passed targeted WIC schema/CI validation, proof validation (13 atoms), and
  all 22 companion cases.
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
- Resolved all three actionable findings from two independent read-only review
  passes.
- Regenerated `.axiom/index/provisions_to_rules.json`; the check mode confirms
  3,944 provisions, 4,670 edges, and 4,435 modules are current.
- Passed the final targeted battery for both modules: schema/CI validation,
  45 proof atoms, and all 51 hand-computed companion cases.
- Passed the repository test suite: 63 tests passed. The expected
  unmanifested-module warning remains because the campaign permits signing
  dry-run only.
- Ran all 15,604 repository companion cases. The only four failures are the
  unchanged baseline reference failures in `us/statutes/26/32.test.yaml`; the
  two new companions pass.
- Passed the repository-wide money-proof ratchet: 118 missing legacy atoms
  across 2,586 monetary obligations, below the allowed backlog of 151.
- Passed the pinned Program Artifact build: all 32 ProgramSpecs compose and
  compile. The builder also reports three pre-existing allowlisted specs that
  now compile; no allowlist was edited.
- Passed source-staleness against the local current corpus: all 43 pinned
  modules match.
- Ran `sign-applied-files` in dry-run mode only. It would create two manifests
  covering the four new RuleSpec/companion files; it wrote nothing.
- Confirmed the generated-file guard fails only because those four files lack
  the manifests intentionally withheld by the signing-dry-run constraint.
- Confirmed all 15 new executable outputs are companion-tested but remain
  unmapped in oracle coverage. The pending-ledger check reports those 15
  required declarations plus one pre-existing stale Hawaii entry. The
  campaign's no-ledger-edit order prevents resolving this lane in-tree.
- Confirmed the unrelated failing §32 companion and its module are unchanged
  from `origin/main`.

## Next

1. Write `build-benefit-elig-SUMMARY.md` and `build-benefit-elig-DONE.md` with
   case tables, boundaries, gates, commit SHAs, and oracle-suite notes.
2. Remove this temporary progress ledger so the final repository diff obeys
   the no-repo-ledger requirement.
3. Verify the final tree is clean and contains only the four RuleSpec files
   plus the generated reverse-index update.
