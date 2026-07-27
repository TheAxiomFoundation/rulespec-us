# 7 CFR 273.7(f), (g), and (j) encoding

## State

Paragraphs (f), (g), and (j) are encoded, independently reviewed, and ready
for draft PR review. Core validation and all 33 frozen-program artifact checks
pass. The only repository-suite finding is the expected stale signed
encoding-manifest hash for the edited module; the signed manifest was not
hand-edited.

## Done

- Read `ENCODER-PREAMBLE.md`.
- Read the repository `CLAUDE.md`.
- Confirmed the worktree is clean on `closure/enc-273-7-work`.
- Confirmed the designated final-report path is
  `_closure-sprint/out/enc-273-7-work.result.md`.
- Read all required sibling modules and companion tests.
- Read the controlling 2026-07-09 corpus text for 7 CFR 273.7(f), (g), (i),
  and (j); paragraph (i) is incorporated because (f) and (j) expressly use its
  good-cause definition.
- Surveyed repository analogues for occurrence-based sanctions, reentry,
  voluntary quit, reduced work effort, and good cause.
- Chose standalone outputs rather than changing the existing
  `snap_member_general_work_requirement_compliant` or
  `snap_member_general_work_requirement_eligible` formulas.
- Chose to treat post-reduction earnings equal to Federal minimum wage times
  30 hours as exempt, following the explicit cross-reference from
  7 CFR 273.7(j)(3)(iii) to the “at least equal” rule in (b)(1)(vii).
- Identified a narrow source ambiguity in (f)(7)(iv): the corpus renders its
  comparable-disqualification cross-reference as `273.11(1)`. The optional
  identical Title IV-A sanction will be deferred rather than assigned a
  guessed target.
- Removed the broad paragraph (j) deferral.
- Encoded the State lookback-window limits, qualifying-job thresholds,
  voluntary quit and reduced-work-effort determinations, incorporated general
  good cause, quit-specific good cause, and the paragraph (j)(4) exceptions.
- Added focused paragraph (j) fixtures covering boundary dates and earnings,
  strike dismissal, comparable replacement work, exclusions, reduced effort,
  minor variations, and good cause.
- Parsed both YAML files and passed all nine repository-layout tests.
- Removed the broad paragraph (f) and (g) deferrals.
- Added a narrow paragraph (f)(7)(iv) deferral for the corpus's ambiguous
  `§ 273.11(1)` cross-reference and the optional State election.
- Encoded direct SNAP noncompliance, Title IV-A/unemployment-compensation
  noncompliance, and paragraph (j) as shared sanction triggers.
- Encoded first-, second-, and third-or-later occurrence schedules, including
  the “later of” minimum-period/compliance rule and optional permanent
  third-or-later sanctions.
- Encoded optional whole-household sanctions, their 180-day cap, household
  reestablishment conditions, and the remaining-period rule when the
  disqualified member joins another household as head.
- Encoded completed-period reentry, exemption-based reentry during a sanction,
  and final-month application treatment.
- Expanded fixture inputs explicitly after the pinned validator correctly
  rejected overridden YAML merge keys.
- Passed pinned `axiom-encode validate --skip-reviewers`,
  `axiom-encode proof-validate`, and all 37 companion cases with the pinned
  rules engine.
- Tightened paragraph (j) after self-review so the 30-to-60-day validity gate
  applies only to pre-application changes, while changes on or after
  application remain reviewable independently.
- Confined paragraph (j)(5)'s final-month application rule to
  disqualifications caused by voluntary quit or reduced work effort.
- Distinguished the initial household sanction duration from the remaining
  duration carried into a newly joined household, with the 180-day cap
  applied to both.
- Re-ran pinned validation, proof validation, and all 39 companion cases
  successfully after those corrections.
- Independent legal-fidelity and RuleSpec reviews identified and confirmed
  additional edge cases before push.
- Corrected sanction-only exemption logic to use the Federal minimum wage
  while preserving the pre-existing composed exemption output unchanged.
- Gated new sanctions for the pending-SSI work-requirement waiver.
- Limited generic non-quit failures to general paragraph (i)(2)/(4) good
  cause, and extended E&T-opening good cause until the State both identifies
  an opening and informs the participant.
- Required a currently active sanction and current paragraph (b)(1) exemption
  for exemption-based reentry; broadened the application fact so paragraph
  (j)(5)'s final-month application can cover post-sanction participation.
- Replaced household ceiling-as-duration calculations with gated maximums,
  State-selected duration validation, and actual selected durations.
- Encoded the clear optional paragraph (f)(7)(iv) trigger and narrowed its
  deferral to downstream effects blocked by the malformed cross-reference.
- Encoded paragraph (j)(3)(vii)'s last-certification-period full-sanction
  timing.
- Passed pinned validation, proof validation, and all 46 companion cases
  after the independent-review fixes.
- The independent re-review found two final gaps and confirmed their fixes:
  exemption-based reentry now requires both becoming exempt during an active
  sanction and remaining currently exempt, while completed-period reentry
  derives its application condition from reapplication or the paragraph
  (j)(5) final-month exception.
- Added invalid over-cap household selections and invalid first-occurrence
  permanent selection boundaries.
- Added a narrow paragraph (f)(7)(ii) deferral for the unresolved interaction
  between the paragraph (a)(6) pending-SSI waiver and the otherwise mandatory
  external Title IV-A/unemployment-compensation sanction.
- Both independent reviewers report no remaining concrete blocker.
- Pinned validation, proof validation, and all 50 companion cases pass after
  the final re-review fixes.
- Passed the reverse-index check with 4,232 provisions, 5,068 edges, and 4,483
  modules.
- Passed the exact-CI-pinned frozen-program artifact check for all 33 program
  specs without editing any program composition.
- Ran the full repository suite: 72 tests passed and one failed solely because
  the signed encoding manifest still records the pre-change `273/7.yaml` hash.

## Next

- Push the branch and open the required draft PR.
