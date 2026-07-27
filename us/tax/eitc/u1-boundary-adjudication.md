# EITC 2026 boundary adjudication

Date: 2026-07-27

## Decision

Both diagnostic discrepancies are the same boundary condition: the 2026
earned-income amount and maximum credit are separately published in whole
dollars, and section 32(f) requires the credit to be determined under the
Secretary's tables. At the published earned-income amount, Rev. Proc. 2025-32
expressly says the published maximum is allowed.

That makes this a **section 32(f) table/published-dollar boundary effect and a
PolicyEngine boundary defect**, not an Axiom defect. Axiom is right on these
two rows because it switches to the published maximum at the published
earned-income amount. This adjudication does not validate Axiom's continuous
rate calculation away from the two boundaries; the full section 32(f) table
remains deferred.

Primary sources:

- [26 USC 32(a), (b), and (f)](https://uscode.house.gov/view.xhtml?edition=prelim&f=treesort&jumpTo=true&num=0&req=%28title%3A26+section%3A32+edition%3Aprelim%29+OR+%28granuleid%3AUSC-prelim-title26-section32%29):
  subsection (a)(1) supplies the rate calculation, subsection (b)(1) supplies
  the 34 and 45 percent rates, and subsection (f) says the allowed amount
  shall be determined under Secretary-prescribed tables with brackets no
  wider than $50.
- [Rev. Proc. 2025-32 section 4.06(1), PDF pages 14-15](https://www.irs.gov/pub/irs-drop/rp-25-32.pdf):
  the retained text defines the earned-income amount as the amount “at or
  above which” the maximum credit is allowed, then publishes the 2026
  earned-income amounts and maximum credits.

## Dollar arithmetic

| Case | Continuous section 32(a) product | Published boundary | Correct amount | Axiom | PolicyEngine |
|---|---:|---:|---:|---:|---:|
| One child, earned income and AGI $13,020 | $13,020 × 34% = $4,426.80 | Earned-income amount $13,020; maximum $4,427 | **$4,427** | $4,427 | $4,426.7998046875 |
| Three children, earned income and AGI $18,290 | $18,290 × 45% = $8,230.50 | Earned-income amount $18,290; maximum $8,231 | **$8,231** | $8,231 | $8,230.50 |

For the one-child row, the separately published maximum rounds the raw
$4,426.80 product to $4,427. For the three-child row, it rounds the raw
$8,230.50 product to $8,231. More importantly than inferring a rounding rule,
the revenue procedure makes the endpoint controlling: at or above $13,020 or
$18,290, respectively, the published maximum is allowed.

PolicyEngine's cached `upstream/main` at
`61cc1e63323579deaa4a5070185bdfafcd7e838a` (2026-07-24) still implements:

```python
phased_in_amount = earnings * phase_in_rate
return min_(maximum, phased_in_amount)
```

It has the correct whole-dollar maxima ($4,427 and $8,231), but no parameter
for the separately published earned-income amounts. The formula therefore
misses the maximum at exact endpoints where `earned_income_amount × rate` is
slightly below the independently rounded maximum. DNS prevented refreshing
the upstream ref on 2026-07-27, so the issue should be rechecked against live
`main` immediately before filing.

## Comparison disposition

```yaml
cases:
  - c1_earned_income_amount_13020
  - c3_earned_income_amount_18290
classification: upstream_oracle_defect
root_cause: section_32_f_published_table_boundary
expected_source:
  - 26 USC 32(a)(1), (b)(1), (f)
  - Rev. Proc. 2025-32 section 4.06(1), pages 14-15
expected:
  c1_earned_income_amount_13020: 4427
  c3_earned_income_amount_18290: 8231
observed_policyengine:
  c1_earned_income_amount_13020: 4426.7998046875
  c3_earned_income_amount_18290: 8230.5
action: keep exact expected values; do not widen tolerance or suppress rows
upstream_issue: draft_only_not_filed
```

## Draft PolicyEngine-US issue

**Title:** Honor published EITC earned-income thresholds at the maximum

**Body:**

> For tax year 2026, `eitc_phased_in` is below the IRS-published maximum at
> two exact earned-income boundaries:
>
> - one child, $13,020 of EITC earned income: expected $4,427; observed
>   $4,426.7998046875;
> - three or more children, $18,290: expected $8,231; observed $8,230.50.
>
> Rev. Proc. 2025-32 section 4.06(1) defines the “earned income amount” as
> the amount at or above which the maximum EITC is allowed. It publishes
> $13,020 / $4,427 for one child and $18,290 / $8,231 for three or more
> children. IRC §32(f) also directs that the allowed credit be determined
> under Secretary-prescribed tables.
>
> The current formula computes
> `min_(maximum, earnings * phase_in_rate)`. Because the published maximum
> and earned-income amount are independently rounded, the continuous product
> is $0.20 or $0.50 below the published maximum at these exact endpoints.
>
> Please add the published earned-income amount as a child-count parameter
> and return the published maximum when earnings are at or above it (while
> preserving phaseout behavior). Regression tests should cover $1 below, at,
> and $1 above each 2026 endpoint for zero, one, two, and three-or-more
> qualifying children. The exact one- and three-child endpoint assertions
> should be $4,427 and $8,231.
>
> Sources:
> - 26 USC 32(a), (b), and (f):
>   https://uscode.house.gov/view.xhtml?edition=prelim&f=treesort&jumpTo=true&num=0&req=%28title%3A26+section%3A32+edition%3Aprelim%29+OR+%28granuleid%3AUSC-prelim-title26-section32%29
> - Rev. Proc. 2025-32, section 4.06(1), PDF pages 14-15:
>   https://www.irs.gov/pub/irs-drop/rp-25-32.pdf

This issue text is staged only. No issue was filed.
