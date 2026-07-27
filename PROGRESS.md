# 7 CFR 273.7(f), (g), and (j) encoding

## State

Paragraph (j) is encoded and covered by focused fixtures. Paragraphs (f) and
(g) are the active implementation step. The change remains additive so the
existing composed work-requirement outputs and frozen program verdicts are not
rewired.

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

## Next

- Remove the broad (f) and (g) deferrals while retaining (k), (m), and other
  out-of-slice deferrals.
- Add a narrow (f)(7)(iv) deferral for the ambiguous optional identical
  Title IV-A sanction.
- Encode and test disqualification triggers and periods, individual and
  optional household effects, and reentry.
- Validate, update this log, commit each coherent step, push, and open the
  required draft PR.
