# EITC closure sprint progress

## State

- The launch-eve EITC follow-up is complete on branch
  `closure/eitc-2026`.
- Prior work on this branch completed the assessment, standalone program, and
  21-case diagnostic comparison (19 exact, two boundary discrepancies).
- The checkout is clean and based on the locally cached `origin/main` at
  `f9fb41b99`; it is 25 cached-main commits behind and eight commits ahead.
  DNS again prevented refreshing either remote ref on 2026-07-27. The user
  explicitly required preserving this branch/worktree, so it will not be
  rebased or moved.
- No SNAP program or committed oracle artifact will be modified.
- The current EITC graph is not honestly certifiable: 34 of its 64 scalar
  frontier inputs are derived or legally preclassified quantities, and no
  reviewed 69-citation-path content ledger exists.
- This follow-up will classify those 34 items into in-graph, administratively
  declarable, or must-encode buckets; repair the stale section 32 fixture;
  adjudicate the two diagnostic boundaries; and prepare case-grid suite
  registration without generating or committing a comparison report.

## Done

- Read the closure-sprint encoder preamble and repository instructions.
- Loaded the PolicyEngine and PolicyEngine-US guidance required for the
  household-level EITC comparison.
- Preserved the prior payroll branch and started this work on a fresh branch.
- Traced the final `eitc` formula to 65 module-qualified frontier leaves and
  classified every leaf as observed/preclassified or derived.
- Audited the reached rule sources and classified Rev. Proc. 2025-32 as a
  genuine primary-guidance node, subject to a formal taxonomy/proof caveat.
- Counted the minimum closure universe across every corpus inventory record:
  69 citation paths at both the pinned and cached newer corpus revisions.
- Reproduced the stale section 32 companion failures.
- Wrote the assessment before making any program change.
- Added `programs/us/tax/eitc/fy-2026.yaml` with the single output `eitc`,
  statutory section 32 as its only scope root, and no transformations.
- Composed the new spec with the pinned composer and compiled the result with
  the pinned engine commit. The compiled artifact exposes 61 derived rules.
- Added an Axiom- and PolicyEngine-checked two-child golden case: $28,890 of
  earned income and AGI yields a $1,053 phaseout and a $6,263 credit, with no
  rounding ambiguity.
- Ran a 21-case synthetic, non-population Axiom/PolicyEngine diagnostic grid:
  19 amounts matched and two published earned-income-amount boundaries
  differed. The age rows require an extra unrooted Axiom flag and therefore
  are not end-to-end evidence.
- Kept the established oracle repository and every committed report and
  numeric artifact untouched. A certifying grid did not land because the age
  dataflow and stale section 32 fixture must be repaired first.
- Incorporated independent-review corrections to the conservative frontier
  classification, runtime ancestry counts, closure wording, and golden case.
- Ran the full repository test suite: 73 passed with one existing warning.
- Wrote the final handoff report in the repository. The requested external
  assessment and result paths are not writable in this sandbox.
- Pushed the committed branch to `origin/closure/eitc-2026`.
- GitHub's API hostname remained unreachable and no signed-in browser was
  available, so a draft PR could not be opened from this environment.
- Re-read the closure-sprint preamble, repository instructions, and the
  PolicyEngine, PolicyEngine-US, and model-development guidance for this
  follow-up.
- Confirmed the worktree is clean and already on the required branch.
- Attempted the required pre-edit fetch; it failed because `github.com` could
  not be resolved.
- Repaired both stale section 32 amount cases by mapping the former
  section 32(c)(2) input names to the live six-input surface, supplying zero
  net self-employment earnings, removing obsolete SECA-chain facts, and
  dropping the removed self-employment intermediate assertion. All existing
  EITC amount expectations are unchanged.
- Ran all four `us/statutes/26/32.test.yaml` cases with pinned
  `axiom-encode` 0.2.1200 source and the pinned rules-engine binary at
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`: four passed, zero failures.
- Adjudicated both diagnostic boundaries as section 32(f)
  table/published-dollar effects that expose a PolicyEngine boundary defect.
  Rev. Proc. 2025-32 says the maximum is allowed at or above each published
  earned-income amount; Axiom's $4,427 and $8,231 are therefore right.
- Verified that cached PolicyEngine-US `upstream/main@61cc1e633` still uses
  `min_(maximum, earnings * phase_in_rate)`, drafted a no-tolerance-widening
  comparison disposition and upstream issue, and did not file it.
- Classified all 34 derived frontier leaves with one row each: zero are
  already computed in the final graph, 11 are exact IRS/SSA/military
  administrative boundary facts, and 23 require encoding. Exact form fields,
  operative corpus citation paths, and honest effort estimates are recorded
  in `us/tax/eitc/u1-frontier-classification.md`.
- Cross-checked all 34 rows against the 28 reached derived rules and against
  semantic near-matches in sections 22, 61, 62, 1402, 1411, 151, and 7703.
  None qualifies as an imported producer. In particular, the Person age rule
  remains disconnected from the TaxUnit age conclusion.
- Added all 21 diagnostic case IDs to the section 32 companion with the exact
  2026 period and final `eitc` assertions required by the federal case-grid
  runner. The pinned toolchain now passes all 25 companion cases with zero
  failures.
- Mechanically traced the `us-additional-medicare-grid` registration through
  its manifest, federal generator, fixture validator, tests, report schema,
  disposition merger, and provenance stamper. Recorded transfer-ready
  manifest/config/disposition templates and the exact remaining generated
  artifacts in `us/tax/eitc/u1-case-grid-registration-prep.md`.
- Confirmed that `population: case-grid` is separate from
  `provenance.run_kind: manual`, and schema-validated the two
  `upstream_engine_gap` disposition entries. No comparison report or
  dashboard/conformance artifact was generated.
- Identified the hard registry blocker: the oracle runner requires a clean
  canonical `rulespec-us` checkout at an exact upstream SHA/tree. Those pins
  cannot be filled truthfully until this fixture lands on main.
- An independent audit caught seven stale Rev. Proc. source labels. Corrected
  the live parameter module and the EITC handoff documents from section 3.06
  to the official section 4.06. This was a citation-metadata defect only; no
  parameter or expected amount changed. Refreshed the module's applied-file
  manifest hash, and the pinned 25-case companion remained green.
- The same strict audit rejected two initially overbroad administrative cuts:
  Form 8862 does not report the section 32(k)(2) prior-denial/information
  composite, and dependent/release fields do not report the complete section
  151-entitlement-or-section-152(e) conclusion. Both are now must-encode;
  the final split is 0 already computed, 11 declarable, and 23 must-encode.
- Independent content, requirements, and suite-registration audits are clean
  after the two classification corrections and the source-label repair.
- Reran the full repository suite after the substantive work: 73 passed with
  the single existing warning about 17 unmanifested modules. The pinned
  section 32 companion independently passed 25/25 in both the main run and
  suite audit.
- Wrote the canonical final report to
  `us/tax/eitc/u1-final-report.md`. The required copy to
  `_closure-sprint/out/u1-eitc-frontier.result.md` was attempted and rejected
  by the managed filesystem with `Operation not permitted`.
- Successfully pushed the implementation, audit corrections, and canonical
  final report to `origin/closure/eitc-2026`. No PR was opened.

## Next

1. Have a process with `_closure-sprint/out` write access copy
   `us/tax/eitc/u1-final-report.md` to the requested result path.
2. After the launch freeze and RuleSpec main merge, complete the external
   `axiom-oracles` registration steps in the staged handoff.
