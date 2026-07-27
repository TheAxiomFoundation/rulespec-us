# Worker C Progress

## State

Investigation is complete and the final report is in progress. No Tennessee encode
change is justified: exact PolicyEngine-US 1.767.3 gives all 48 target cases a zero
utility allowance, the supplied report used 1.752.2, and `ecps-35254` instead exposes
an oracle-population bridge omission for PolicyEngine's endogenous Tennessee Families
First/TANF income. The pinned corpus does not retain a current FY2026 Tennessee
utility-allowance amount source, so PolicyEngine's amounts must not be copied into
Axiom.

## Done

- Confirmed the `fed-parity/snap-tn` worktree is clean.
- Loaded the GitNexus debugging workflow for source and execution-flow tracing.
- Defined the report-native class as a SNAP benefit `amount_difference` with no SNAP eligibility mismatch.
- Tabulated 337 class cases: AL 37, MA 134, NC 69, SC 49, and TN 48.
- Partitioned all 70 TN residual rows: 48 benefit-only; 16 benefit plus Axiom-only eligibility; 3 benefit plus PolicyEngine-only eligibility; 3 PolicyEngine-only eligibility.
- Confirmed TN class household-size counts: 1:5, 2:8, 3:15, 4:8, 5:6, 6:2, 7:1, 8:2, 9:1.
- Confirmed `ecps-35254`: Axiom 667, PolicyEngine 564.6453450520834, delta +102.35465494791663.
- Identified a provenance mismatch: the supplied reports use PolicyEngine-US 1.752.2, while the requested source comparison targets 1.767.3.
- Located exact PolicyEngine-US 1.767.3 source at local git commit `49d19b239a593dbac8920ac6fd80cfe33372343a`.
- Confirmed the pinned corpus retains FY2024 FNS TN values and an older non-primary TN table, but no FY2026 Tennessee DHS utility chart or FY2026 FNS state table.
- Confirmed 7 CFR 273.9(d)(6)(iii)(A)-(C) delegates utility standards to states, prohibits overlapping standards, and requires annual review and reporting.
- Reproduced all 48 target cases under exact PolicyEngine-US 1.767.3: every case has
  utility type `NONE` and SUA, LUA, individual, and total utility allowance of $0.
- Found Tennessee Families First/TANF income in 8 of the 48 live cases, including
  `ecps-35254`; PolicyEngine 1.767.3 assigns that household $362.03/month of Families
  First and includes it as SNAP unearned income.
- Traced the oracle bridge: `populace_input_mapping.yaml` expects `TANF_BENEFITS` when
  deriving `snap_total_monthly_unearned_income`, but
  `populace_us.py::_PERSON_NON_WAGE_VARIABLES` does not project PolicyEngine's
  `tanf_person`, so Axiom receives zero TANF for the exemplar.
- Confirmed 7 CFR 273.9(b)(2)(i) requires TANF assistance payments to be treated as
  unearned income. PolicyEngine is therefore correct on that rule; this is not a
  PolicyEngine defect and not a Tennessee SNAP encode defect.
- Rejected scoping the retained `1240-01-04-.27` module: its $314/$126/$25 utility
  values are stale by at least FY2024, lack a current effective date, and its three
  state-option hooks would overlap if all applied.
- Rejected a zero-valued placeholder hook because missing authority means unknown,
  not a lawful $0, and such a change would have no mutation-detectable behavior.
- Ran the four relevant existing companion suites with the available local rules
  engine: 18/18 cases passed. The user-specified
  `/Users/maxghenis/TheAxiomFoundation/axiom-rules` path does not exist; the fallback
  `/Users/maxghenis/TheAxiomFoundation/axiom-rules-engine` checkout is not the pinned
  engine ref and has pre-existing local changes, so this is supporting rather than
  release-grade verification.
- Made no encode changes, so no before/after mutation test was required or fabricated.

## Next

1. Complete and commit `WORKER-REPORT.md`.
2. Include the FY2026 source-ingest prerequisite, bridge issue draft, and proposed
   residual dispositions.
3. Record final repository status and hand off the local commits.
