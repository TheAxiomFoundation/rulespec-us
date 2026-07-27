# Federal SNAP residual investigation progress

## State

- Active branch: `fed-parity/snap-fed`.
- Starting commit: `1158ba5b248c3cbbfe1768357f03ca43c8b3618e`.
- Worktree started clean and matches the locally cached `origin/main`.
- A fresh fetch was attempted on 2026-07-27 but the sandbox could not resolve
  `github.com`; all work therefore uses the pinned local checkout and corpus.
- The required residual census is complete. Legal/root-cause validation remains
  in progress; no encode change has been selected yet.

## Done

- Loaded the PolicyEngine and PolicyEngine-US analysis guidance.
- Verified the active branch, worktree cleanliness, remotes, and cached base.
- Tabulated the strict class across all five supplied reports:

  | State | Strict cases | Zero earned | Positive earned |
  | --- | ---: | ---: | ---: |
  | AL | 0 | 0 | 0 |
  | MA | 42 | 29 | 13 |
  | NC | 0 | 0 | 0 |
  | SC | 43 | 36 | 7 |
  | TN | 0 | 0 | 0 |
  | **Total** | **85** | **65** | **20** |

  Strict matching means a one-person household whose sole member is at least
  age 60, with Axiom reporting both zero benefit/ineligible and PolicyEngine
  reporting benefit `23.973597208658855`/eligible.
- Counted the broader exact-$23.97 PE-only residual universe: 154 one- or
  two-person cases (AL 1, MA 91, NC 0, SC 62, TN 0). This is a candidate
  ceiling, not yet a causal clearance estimate.
- Confirmed from the report metadata that earned-income summaries alone cannot
  establish gross-income, net-income, medical-deduction, or categorical-
  eligibility causation.
- Confirmed that the current federal encodes, including at the reports'
  rulespec commit, already contain the elderly/disabled gross-test exemption
  and the one-/two-person minimum-benefit floor. The remaining code seam under
  investigation is the externally supplied medical-deduction entitlement flag.

## Next

1. Read the retained text for 7 CFR 273.9(a)(2), 273.9(d)(3), and
   273.10(e)(2)(ii)(C), then trace the current federal encodes.
2. Reproduce representative cases in PolicyEngine-US 1.767.3 and isolate which
   rule differences drive the mismatches.
3. Make the smallest legally correct encode and companion-test changes, capture
   mutation evidence, and run the required suites.
4. Write and commit `WORKER-REPORT.md`.
