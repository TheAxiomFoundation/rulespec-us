# Worker C Progress

## State

Residual inventory is complete. Engine and authority tracing shows that the pinned corpus does not retain a current Tennessee FY2026 utility-allowance amount source, so PolicyEngine values cannot be copied into Axiom. Investigation is continuing to determine whether a source-independent structural fix is supported.

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

## Next

1. Reproduce Tennessee deduction internals under exact PolicyEngine-US 1.767.3 and compare them with the supplied 1.752.2 report.
2. Determine whether the non-stacking and shelter-composition rules permit a source-independent Tennessee-owned fix.
3. Encode only a retained-authority-supported change; otherwise document the FY2026 source ingest prerequisite and make no numeric change.
4. Run proportional verification and complete `WORKER-REPORT.md`, including dispositions and any justified PolicyEngine issue draft.
