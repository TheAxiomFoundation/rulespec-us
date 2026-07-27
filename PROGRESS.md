# Worker C Progress

## State

Investigation and reporting are complete. No Tennessee encode change is justified:
the actual report pipeline gives all 48 target cases a zero utility allowance under
both PolicyEngine-US 1.752.2 and 1.767.3, and `ecps-35254` instead exposes an
oracle-population bridge omission for PolicyEngine's endogenous Tennessee Families
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
- Confirmed the report used the general `axiom-oracles-compare` loader and
  household IDs, not the specialized SPM-unit SNAP bridge: `ecps-35254` is raw
  household ID 35254 and its four ages match the report.
- Confirmed the pinned corpus retains FY2024 FNS TN values and an older non-primary TN table, but no FY2026 Tennessee DHS utility chart or FY2026 FNS state table.
- Confirmed 7 CFR 273.9(d)(6)(iii)(A)-(C) delegates utility standards to states, prohibits overlapping standards, and requires annual review and reporting.
- Reproduced all 48 target cases through the actual generic comparison pipeline
  under exact PolicyEngine-US 1.752.2 and 1.767.3: every case has utility type
  `NONE` and SUA, LUA, individual, and total utility allowance of $0.
- Reproduced the report's `ecps-35254` PolicyEngine benefit exactly under 1.752.2:
  $564.6453450520834/month. Version 1.767.3 gives the same value through this
  pipeline.
- Neutralized both `tn_ff` and `tanf` in an exact 1.752.2 counterfactual:
  PolicyEngine rises to $673.545369/month, only $6.545369 from Axiom and inside
  the suite's $7 tolerance, so the classified mismatch disappears.
- Found Tennessee Families First/TANF income in 31 of the 48 cases under both
  versions, including `ecps-35254`; PolicyEngine assigns that household
  $362.03/month of Families First and includes it as SNAP unearned income. All 31
  have Axiom benefits above PolicyEngine; the other 17 contain all 5 negative
  deltas.
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
- Finalized `WORKER-REPORT.md` with the complete residual table, exact-version
  utility and counterfactual evidence, provision paths, no-change decision, draft
  bridge issue, corpus-ingest prerequisite, and proposed dispositions.

## Next

1. Ingest a dated, primary FY2026 Tennessee DHS utility chart or FNS SUA table.
2. Resolve the `axiom-oracles` equal-input policy for endogenous TANF and regenerate
   the suite under one declared PolicyEngine-US version.
3. After source ingest, encode mutually exclusive SUA/BUA/telephone selection and
   add source- and mutation-backed companion cases.
