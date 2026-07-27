# Federal SNAP residual investigation progress

## State

- Active branch: `fed-parity/snap-fed`.
- Starting commit: `1158ba5b248c3cbbfe1768357f03ca43c8b3618e`.
- Worktree started clean. On 2026-07-27, the locally cached
  `origin/main` advanced to `6b0773d3fdc61d4926790509b89d70a9aa970736`;
  the two progress commits were rebased onto that commit before encode edits.
- A fresh fetch was attempted on 2026-07-27 but the sandbox could not resolve
  `github.com`; all work therefore uses the pinned local checkout and corpus.
- The required census, retained-text audit, and exact PolicyEngine-US 1.767.3
  trace are complete. Federal encode changes and companion mutation tests are
  next.

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
- Rechecked the retained 7 CFR Part 273 XML after the toolchain pin advanced
  from `f7fe8471c415908b26cfac1e199e92d1580c8ff3` to
  `bf97b17baebfdf12601f7c23697524bf5adcdaed`; the pinned Part 273 source has
  the same SHA-256 (`92d5f3baba66e0f7f8ba2a2887a2a664166fcc0deb275b1b143a7ca23a4114a6`).
- Verified the controlling retained text:
  - `us/regulation/7/273/9`, paragraph (a), requires only the net test for an
    elderly/disabled household and exempts a categorically eligible household
    from both tests.
  - `us/regulation/7/273/9/d/3` allows medical expenses over $35 incurred by an
    elderly/disabled member, subject to the listed expense limitations.
  - `us/regulation/7/273/10`, paragraph (e)(2)(ii)(C), sets the non-initial
    one-/two-person minimum at 8 percent of the one-person maximum, rounded to
    the nearest whole dollar.
- Reproduced the 85 strict report rows against the pinned Populace rows with
  PolicyEngine-US 1.767.3. The July 6 reports identify PolicyEngine-US 1.752.2,
  so they are stale relative to the requested version:

  | Current 1.767.3 disposition | AL | MA | NC | SC | TN | Total |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | Eligible only through categorical path | 0 | 12 | 0 | 23 | 0 | 35 |
  | Eligible through both categorical and ordinary income path | 0 | 11 | 0 | 3 | 0 | 14 |
  | Eligible only through ordinary income path | 0 | 1 | 0 | 0 | 0 | 1 |
  | No longer eligible | 0 | 18 | 0 | 17 | 0 | 35 |
  | **Total** | **0** | **42** | **0** | **43** | **0** | **85** |

- Confirmed that the named MA case `ecps-1984` is categorical-only under
  1.767.3. The named SC case `ecps-28671` is both categorically eligible and
  net-income eligible.
- Confirmed a PolicyEngine-side minimum-allotment defect: 1.767.3 calculates
  `0.08 * $298 = $23.84` without the regulation's nearest-dollar rounding.
  The report adapter further annual-averages a January request, producing
  `$23.973597208658855`. Axiom's encoded `$24` floor is correct.
- Selected one federal correction supported by paragraph (a): include regular
  categorical eligibility in the federal income-eligibility result. No medical
  rule was changed: the federal calculation already subtracts qualifying
  expenses above $35, while expense classification is expressly deferred to an
  upstream determination. Replacing that classification with a household-age
  check would incorrectly allow expenses incurred only by a nonqualifying
  spouse or dependent.
- Added the categorical bypass to `273/9.yaml` by importing the existing
  `273/2/j` regular-categorical result. The companion case sets both ordinary
  income tests to fail and proves that regular categorical eligibility still
  satisfies the composed income gate.
- Captured before-fix mutation evidence: the new companion failed twice because
  `snap_regular_categorically_eligible` was not an executable output and its
  PA/SSI factual input did not resolve in the compiled 273.9 graph.
- Ran the required companion commands after the change:
  - `273/9.test.yaml`: 5 cases passed.
  - `273/10.test.yaml`: 5 cases passed.

## Next

1. Finish the Case-to-PolicyEngine 1.767.3 rerun and distinguish direct-H5
   results from report-pipeline results.
2. Review the composed input projection to determine how many categorical
   cases this federal graph correction can clear without a separate oracle
   mapping change.
3. Write and commit `WORKER-REPORT.md`, including the stale-case dispositions,
   conservative clearance estimate, exact law paths, and PolicyEngine issue
   draft.
