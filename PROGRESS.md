# EITC closure sprint progress

## State

- The launch-eve EITC follow-up is in progress on branch
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
  already computed in the final graph, 13 are exact IRS/SSA/military
  administrative boundary facts, and 21 require encoding. Exact form fields,
  operative corpus citation paths, and honest effort estimates are recorded
  in `us/tax/eitc/u1-frontier-classification.md`.
- Cross-checked all 34 rows against the 28 reached derived rules and against
  semantic near-matches in sections 22, 61, 62, 1402, 1411, 151, and 7703.
  None qualifies as an imported producer. In particular, the Person age rule
  remains disconnected from the TaxUnit age conclusion.

## Next

1. Mirror the `us-additional-medicare-grid` registration contract and stage
   the EITC case-grid suite without generating a committed report.
2. Run scoped and repository checks, write the requested output report,
   update this ledger, commit each coherent step, and push if DNS permits.
