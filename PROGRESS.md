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
  report-path trace are complete. None of the three proposed federal rules is
  missing or causally explains the residuals. The federal encodes are restored
  unchanged after rejecting a composition-breaking candidate patch; final
  reporting and verification remain.

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
- Calculated the 85 strict report row IDs directly on the pinned Populace H5
  with PolicyEngine-US 1.767.3. This is a source-data diagnostic, not yet the
  report-pipeline reproduction: the oracle first reduces the H5 rows to Case
  facts and then rebuilds a PolicyEngine situation. The July 6 reports identify
  PolicyEngine-US 1.752.2, so they are also stale relative to the requested
  version:

  | Current 1.767.3 disposition | AL | MA | NC | SC | TN | Total |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | Eligible only through categorical path | 0 | 12 | 0 | 23 | 0 | 35 |
  | Eligible through both categorical and ordinary income path | 0 | 11 | 0 | 3 | 0 | 14 |
  | Eligible only through ordinary income path | 0 | 1 | 0 | 0 | 0 | 1 |
  | No longer eligible | 0 | 18 | 0 | 17 | 0 | 35 |
  | **Total** | **0** | **42** | **0** | **43** | **0** | **85** |

- Reproduced all 85 strict report rows through the current
  `PopulaceUsCaseLoader` → `PolicyEngineRunner` bridge with the exact cached
  PolicyEngine-US 1.767.3 package:

  | Adapter-path disposition | AL | MA | NC | SC | TN | Total |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | Eligible only through categorical path | 0 | 27 | 0 | 42 | 0 | 69 |
  | Eligible through categorical and ordinary paths | 0 | 14 | 0 | 1 | 0 | 15 |
  | Eligible only through ordinary income path | 0 | 1 | 0 | 0 | 0 | 1 |
  | Ineligible | 0 | 0 | 0 | 0 | 0 | 0 |
  | **Total** | **0** | **42** | **0** | **43** | **0** | **85** |

- All 85 remain PolicyEngine-eligible in the current adapter path. Eighty-four
  retain the report's exact `$23.973597208658855`; MA `ecps-2303` now receives
  `$100.1699930826823`. MA `ecps-3128` is the sole ordinary-only case.
- Confirmed that named MA `ecps-1984` and SC `ecps-28671` are both
  categorical-only in the adapter path. Both pass PolicyEngine's elderly gross
  exemption but fail its net test. The bridge omits source medical-expense
  inputs; categorical eligibility, not the medical deduction, preserves their
  eligibility.
- Ran a medical-expense counterfactual for the sole ordinary-only case
  (`ecps-3128`). Reducing projected health premiums to a nominal amount removes
  its medical deduction, but it still passes both ordinary income tests and
  remains eligible. Medical expenses therefore cause zero eligibility
  residuals in this strict class.
- Confirmed a PolicyEngine-side minimum-allotment defect: 1.767.3 calculates
  `0.08 * $298 = $23.84` without the regulation's nearest-dollar rounding.
  The report adapter further annual-averages a January request, producing
  `$23.973597208658855`. Axiom's encoded `$24` floor is correct.
- Tested a federal categorical wiring change supported by paragraph (a). Its
  new companion initially failed because the existing `273/2/j` regular-
  categorical result was absent from the executable 273.9 graph, then all five
  273.9 cases passed after the import and formula change.
- Rejected that change after downstream mutation testing exposed a material
  regression: importing `273/2/j` made eight new categorical factual inputs
  mandatory for every 273.9 consumer. The California SNAP companion then
  failed 4 of 6 cases on missing PA/SSI inputs. State companion edits are out
  of scope and zero-defaulting legal eligibility facts inside the encode would
  be incorrect, so the federal encode and companion were restored unchanged.
- Confirmed no medical rule should change: the federal calculation already
  subtracts qualifying expenses above $35, while expense classification is
  expressly deferred to an upstream determination. Replacing that
  classification with a household-age check would incorrectly allow expenses
  incurred only by a nonqualifying spouse or dependent. The generic Populace
  projector does not map `snap_total_medical_expenses`, so it defaults that
  factual amount to zero outside the legal encode.
- Classified the federal clearance estimate as zero in every state. A correct
  out-of-scope categorical-input projection would directly explain the 69
  categorical-only cases (MA 27, SC 42), offer an alternate path for 15 more,
  and leave MA `ecps-3128` for a separate projection/gate disposition.

## Next

1. Re-run the unchanged federal companion suites and the representative
   downstream suite after the rollback.
2. Write and commit `WORKER-REPORT.md`, including a zero federal-clearance
   estimate, the out-of-scope projection dispositions, exact law paths, and the
   PolicyEngine issue draft.
