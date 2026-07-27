# Employee FICA tax golden case

This fixture is a hand-checkable tax-year-2026 case for the three outputs of
`us/payroll/employee-fica-tax`. It is statutory arithmetic, not a value copied
from PolicyEngine.

## Facts and supported profile

- One employee, one employer, and one tax unit.
- Filing status: single (`filing_status = 0`).
- OASDI wages before only the section 3121(a)(1) contribution-base exclusion:
  **$300,000**. This is a completed frontier fact after all other applicable
  section 3121 exclusions; it is not W-2 box 3.
- Person Medicare wages and tips (W-2 box 5): **$300,000**.
- TaxUnit Medicare wages and tips, equal to the one Person's box 5 amount:
  **$300,000**.
- No wages are exempt under section 3101(c), employer continuity needs no
  adjustment, and taxable self-employment income is zero.

These facts satisfy the supported-domain contract stated in
`us/policies/payroll/employee_fica_tax_pipeline.yaml`.

## Statutory derivation

### 1. Employee OASDI wage tax — 26 USC 3101(a) and 3121(a)(1)

The official 2026 contribution-and-benefit base is **$184,500**.

```text
OASDI taxable wages = min($300,000, $184,500)
                    = $184,500

employee_oasdi_wage_tax = $184,500 × 6.2%
                        = $184,500 × 0.062
                        = $11,439
```

### 2. Employee hospital-insurance wage tax — 26 USC 3101(b)(1)

The 1.45 percent tax has no contribution-and-benefit-base cap.

```text
employee_hospital_insurance_wage_tax = $300,000 × 1.45%
                                     = $300,000 × 0.0145
                                     = $4,350
```

### 3. Employee Additional Medicare wage tax — 26 USC 3101(b)(2)

For a single filer, the statutory threshold is **$200,000**.

```text
excess Medicare wages = max($0, $300,000 - $200,000)
                      = $100,000

employee_additional_medicare_wage_tax = $100,000 × 0.9%
                                      = $100,000 × 0.009
                                      = $900
```

## Expected program outputs

| Output | Entity | Expected value |
|---|---|---:|
| `employee_oasdi_wage_tax` | Person | $11,439 |
| `employee_hospital_insurance_wage_tax` | Person | $4,350 |
| `employee_additional_medicare_wage_tax` | TaxUnit | $900 |

For this one-person fixture only, the three components sum to **$16,689**.
That sum is a reader check, not a published program output: the program keeps
the Person and TaxUnit components separate rather than silently aggregating
across entities.

The companion cases
`person-wages-at-golden-300k` and
`single-wages-well-above-additional-medicare-threshold` execute the same
component arithmetic in
`us/policies/payroll/employee_fica_tax_pipeline.test.yaml`.
