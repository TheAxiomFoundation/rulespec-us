# EITC diagnostic grid: Axiom and PolicyEngine-US

Date: 2026-07-27

## Result

I ran a 21-case synthetic tax-year-2026 grid through the compiled standalone
Axiom program and the local PolicyEngine-US `eitc` variable. No
population-backed suite was run. Nineteen amounts matched exactly. Two cases
at published earned-income-amount boundaries differed by more than the
reference grid's $0.01 tolerance.

This is a **diagnostic run, not provision-rooted comparison evidence**. A
certifying `case-grid` suite did not land for the reasons under “Why this is
not the requested certificate.”

## Same-input contract

- Both engines received the same earned income and adjusted gross income for
  every case.
- Axiom assembled earned income by setting section 32(c)(2) employee
  compensation to the case amount and every other component or exclusion to
  zero. PolicyEngine received the same amount as an explicit TaxUnit
  `eitc_earned_income` override.
- Both engines received adjusted gross income directly. This is the
  evidence-free AGI bridge expressly contemplated by the task.
- Both engines received the same assembled section 32(i)(2) investment-income
  amount directly. This is an additional derived frontier bridge, not evidence
  that either graph assembled the statutory amount.
- PolicyEngine used actual age-10 dependent children and derived its
  `eitc_child_count`. Axiom used explicit section 152(c) child facts and the
  `qualifying_child_of_tax_unit` relation.
- Identification, return-filing, residence, and other eligibility facts were
  explicit. PolicyEngine had `takes_up_eitc` and
  `would_file_if_eligible_for_refundable_credit` set true; required and
  voluntary filing were set false; filing status and every filer/child SSN
  type were explicit.
- For the four childless age cases, both engines received the same age.
  Axiom also had to receive
  `childless_taxpayer_or_spouse_age_eligible_for_eitc` as a manually derived
  Boolean. That extra bridge is the decisive evidence defect.

## Executed cases

| Case | Children | Earned income | AGI | Investment income | Age | Axiom | PolicyEngine | Axiom − PE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `c0_phase_in_5000` | 0 | 5,000 | 5,000 | 0 | 35 | 382.5 | 382.5 | 0 |
| `c1_phase_in_5000` | 1 | 5,000 | 5,000 | 0 | 35 | 1,700 | 1,700 | 0 |
| `c2_phase_in_5000` | 2 | 5,000 | 5,000 | 0 | 35 | 2,000 | 2,000 | 0 |
| `c3_phase_in_5000` | 3 | 5,000 | 5,000 | 0 | 35 | 2,250 | 2,250 | 0 |
| `c4_phase_in_5000` | 4 | 5,000 | 5,000 | 0 | 35 | 2,250 | 2,250 | 0 |
| `c1_earned_income_amount_13020` | 1 | 13,020 | 13,020 | 0 | 35 | 4,427 | 4,426.7998046875 | 0.2001953125 |
| `c1_after_earned_income_amount_13021` | 1 | 13,021 | 13,021 | 0 | 35 | 4,427 | 4,427 | 0 |
| `c3_earned_income_amount_18290` | 3 | 18,290 | 18,290 | 0 | 35 | 8,231 | 8,230.5 | 0.5 |
| `c3_after_earned_income_amount_18292` | 3 | 18,292 | 18,292 | 0 | 35 | 8,231 | 8,231 | 0 |
| `c1_plateau_20000` | 1 | 20,000 | 20,000 | 0 | 35 | 4,427 | 4,427 | 0 |
| `c1_phase_out_start_23890` | 1 | 23,890 | 23,890 | 0 | 35 | 4,427 | 4,427 | 0 |
| `c1_phase_out_28890` | 1 | 28,890 | 28,890 | 0 | 35 | 3,628 | 3,628 | 0 |
| `c1_agi_driven_earned20000_agi28890` | 1 | 20,000 | 28,890 | 0 | 35 | 3,628 | 3,628 | 0 |
| `c3_plateau_20000` | 3 | 20,000 | 20,000 | 0 | 35 | 8,231 | 8,231 | 0 |
| `c3_phase_out_start_23890` | 3 | 23,890 | 23,890 | 0 | 35 | 8,231 | 8,231 | 0 |
| `c0_age_24` | 0 | 5,000 | 5,000 | 0 | 24 | 0 | 0 | 0 |
| `c0_age_25` | 0 | 5,000 | 5,000 | 0 | 25 | 382.5 | 382.5 | 0 |
| `c0_age_64` | 0 | 5,000 | 5,000 | 0 | 64 | 382.5 | 382.5 | 0 |
| `c0_age_65` | 0 | 5,000 | 5,000 | 0 | 65 | 0 | 0 | 0 |
| `c1_investment_12200` | 1 | 20,000 | 20,000 | 12,200 | 35 | 4,427 | 4,427 | 0 |
| `c1_investment_12201` | 1 | 20,000 | 20,000 | 12,201 | 35 | 0 | 0 | 0 |

Axiom returns the published maximum as soon as
`earned_income >= eitc_earned_income_amount`. PolicyEngine instead computes
`min(maximum, earned_income × phase_in_rate)`. Thus at exactly $13,020 with
one child it produces $4,426.7998046875 rather than $4,427; at exactly $18,290
with three children it produces $8,230.50 rather than $8,231. The mismatches
are reported, not hidden by widening tolerance.

## Runtime provenance

The Axiom program was composed with
`axiom-compose@fabe0b3b3fd6e90d3e8f075516f9b668f524f711` and compiled and
executed with the repository-pinned rules engine
`ffd8213271947b0189a9dd61a055c1e0e78908a0`. The compiled artifact SHA-256 was
`37870daf87bb905ef9f1ed89cf5a9a2d3d2836620429bfe637f9508d4744fc30`;
the engine binary SHA-256 was
`674ca6e70afdccb59c3d6847933bc24b4590105e49db54790f2dcd0bdbbe32d7`.
The aligned request contained 1,563 explicit inputs, 30 child relations, and
42 queries in explain mode. One TaxUnit query requested `eitc` and one Person
query requested the encoded childless-age predicate for each case. The request
SHA-256 was
`7bf1884d6932d5c913cc337d41337046da55b33541a9ce12141e09f989c82514`;
the raw-response SHA-256 was
`85aeeab6e7eae80ef165f6f28274f5bdbfd58ffb120b5d2dfc7e8f2c09a8960a`.

The Axiom side can be replayed while the temporary evidence files remain:

```sh
/private/tmp/axiom-rules-engine-ffd8213-target/release/axiom-rules-engine \
  run-compiled \
  --artifact /private/tmp/axiom-eitc-compose.GM3mNk/us-eitc.json \
  < /private/tmp/eitc-21-request.json
```

PolicyEngine ran from the read-only local `policyengine-us` checkout at
`715373c90b0014561977a1b161f2f4c75bb45c33`, editable package version 1.779.4,
with PolicyEngine-Core 3.30.2, NumPy 2.4.1, and Python 3.14.4. The checkout was
97 commits behind its cached upstream reference; its PolicyEngine source was
unchanged, but its lockfile and unrelated untracked files made the checkout
dirty. These facts further limit this run to diagnostic status.

## Why this is not the requested certificate

1. Axiom's Person rule correctly returns not-held/held/held/not-held at ages
   24/25/64/65. The final credit does not consume that rule. It consumes the
   manually supplied TaxUnit-level legal conclusion. The matching age amounts
   therefore do not establish end-to-end provision-rootedness.
2. AGI is not the only bridge. The run also supplies the derived investment
   total and the other legal conclusions enumerated in the assessment.
3. The existing section 32 companion fixture is stale and fails before its two
   amount cases execute, so the established federal grid runner cannot use it
   as engine-reviewed Axiom evidence.
4. The established comparison integration is in the separate
   `axiom-oracles` repository, outside this task's writable checkout. Its
   federal runner reads fixture values rather than executing the standalone
   program. A real suite requires generator and registry work there after the
   RuleSpec graph and fixture are repaired.
5. In the referenced artifact, `population` is `case-grid` and `run_kind` is
   `manual`; `case-grid` is not a valid `run_kind` in the current schema.
   Generated dashboard reports and numeric values remain frozen and untouched.

The synthetic requests and raw responses were kept in `/private/tmp`; no
committed oracle report or numeric artifact was created or modified.
