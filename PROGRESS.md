# SNAP earned income deduction closure

## State

Assessment complete. The SNAP earned income deduction is not honestly
certifiable as a provision-closed node tonight. Implementation stopped before
adding a program or oracle artifact. Focused pinned validation is green; final
publication is pending.

## Done

- Read the closure-sprint encoder preamble and repository `CLAUDE.md`.
- Confirmed the worktree is clean on `closure/snap-earned-income-deduction`.
- Verified the existing 7 USC 2014(e)(2) modules and companion tests exist.
- Confirmed that no existing SNAP program specification may be modified.
- Read the required sibling encodings and companion tests.
- Parsed all 689 inventories and 142,879 records at the RuleSpec-pinned corpus
  commit. Final dependency audit expanded the corpus-resolving lower-bound
  closure to 81 unique citation paths: 13 encoded, 3 excludable, and 65
  pending. Required unresolved and open-ended branches prevent an honest
  finite full-closure count.
- Verified 7 CFR 273.9(d)(2), 273.10(e)(1)(i)(B),
  273.12, 273.18(c)(1)(ii)(B), and 273.7(l) from the authoritative corpus
  bodies.
- Traced RuleSpec and PolicyEngine dependencies to observed facts and derived
  quantities.
- Confirmed that `snap_countable_earned_income`,
  `work_supplementation_earned_income`, and the overissuance guard are
  unclosed derived quantities.
- Confirmed that PolicyEngine has neither the work-supplementation adjustment
  nor the overissuance exception required for the requested grid.
- Wrote `s1-snap-eid-assessment.md`, including a conditional worked example.
- Committed the initial assessment checkpoint.
- Validated and proof-validated both existing 7 USC 2014(e)(2) modules with
  the pinned encoder.
- Ran both existing companion suites with the pinned rules engine: all three
  cases passed.
- Ran no population-backed suite.
- Attempted the requested external output copy; the managed workspace denied
  writes outside this worktree, so the committed in-repository assessment is
  the canonical deliverable.

## Next

- Commit this final validation and delivery checkpoint.
- Push and open a draft PR if authentication and network access permit.
- Record the publication result.
