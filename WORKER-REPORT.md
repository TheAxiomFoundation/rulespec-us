# Worker B report: SNAP lone-minor high-earner eligibility

## Conclusion

**Axiom is right for this class. PolicyEngine US has an income-counting
defect.**

A minor may be a one-person SNAP household when genuinely living alone.
However, that minor's wages are not covered by the child-earner exclusion:
7 CFR 273.9(c)(7) also requires the child to live with a parent or under the
parental control of another household member. PolicyEngine US 1.767.3 omits
that residence/control condition, imputes K-12 attendance to ages 5 through
17, zeros all of the lone minor's wages, and then awards SNAP.

There is no minor-headed-household bar in the Axiom result. The generic ECPS
adapter projects the source singleton as a one-person Axiom household and
supplies all wages. Axiom then correctly fails the federal income gate. No
case-relevant RuleSpec or adapter change is warranted.

## 1. Corrected class inventory

The two cases named in the assignment are not exhaustive.

The strict assigned class is:

- one-person household;
- sole member under age 18;
- annual earned income exactly $217,027.52;
- Axiom `snap_eligible = false` and `snap_benefit = 0`;
- PolicyEngine `snap_eligible = true` and positive benefit.

It contains **11 cases**. A mechanism-complete filter using any positive
earned income contains **12**: AL `ecps-37651` has $21,866.20 and exhibits the
same defect. The extra case establishes that the behavior does not depend on
the repeated $217,027.52 value.

| State | Strict count | One-person household shapes | Same-mechanism count |
|---|---:|---|---:|
| AL | 3 | age 16 × 1; age 17 × 2 (one disabled) | 4 (adds age-16 `ecps-37651`) |
| MA | 1 | age 15 × 1; pregnant | 1 |
| NC | 3 | age 15 × 2; age 17 × 1 | 3 |
| SC | 2 | age 16 × 2 | 2 |
| TN | 2 | age 7 × 1; age 15 × 1 | 2 |
| **Total** | **11** | all one-person households | **12** |

All 12 have both an `amount_difference` for
`us:statutes/7/2014/u#snap_benefit` and an `eligibility_right_only` mismatch
for `us:statutes/7/2014/o#snap_eligible`.

| State / JSON pointer | Case | Sole member | Annual earnings | Axiom eligible / benefit | PE eligible / benefit |
|---|---|---:|---:|---|---|
| AL `/cases/0` | `ecps-36459` | 17, disabled | $217,027.52 | false / $0 | true / $296.8949788411458 |
| AL `/cases/4` | `ecps-36559` | 17 | $217,027.52 | false / $0 | true / $299.66998291015625 |
| AL `/cases/50` | `ecps-37623` | 16 | $217,027.52 | false / $0 | true / $150.64496866861978 |
| AL `/cases/53` | `ecps-37651` | 16 | $21,866.20 | false / $0 | true / $299.66998291015625 |
| MA `/cases/36` | `ecps-2194` | 15, pregnant | $217,027.52 | false / $0 | true / $299.66998291015625 |
| NC `/cases/0` | `ecps-27147` | 15 | $217,027.52 | false / $0 | true / $150.64496866861978 |
| NC `/cases/29` | `ecps-27597` | 17 | $217,027.52 | false / $0 | true / $198.19500732421875 |
| NC `/cases/56` | `ecps-27962` | 15 | $217,027.52 | false / $0 | true / $150.64496866861978 |
| SC `/cases/68` | `ecps-29280` | 16 | $217,027.52 | false / $0 | true / $299.66998291015625 |
| SC `/cases/114` | `ecps-29677` | 16 | $217,027.52 | false / $0 | true / $299.66998291015625 |
| TN `/cases/10` | `ecps-35407` | 15 | $217,027.52 | false / $0 | true / $299.66998291015625 |
| TN `/cases/20` | `ecps-35601` | 7 | $217,027.52 | false / $0 | true / $299.66998291015625 |

The evidence reports are:

```text
/Users/maxghenis/TheAxiomFoundation/axiom-oracles/dashboard/public/data/
  axiom-policyengine-{al,ma,nc,sc,tn}-snap-ecps.json
```

All five reports retain all mismatches:
`dashboard_truncation.shown_mismatches` equals
`dashboard_truncation.total_mismatches`. Their `cases[]` arrays contain only
mismatching households, so population prevalence was checked against the
pinned HDF rather than inferred from `cases[]`.

The reports retain the compatibility population label `enhanced-cps`, while
each affected case's `metadata.dataset` identifies the actual
`populace://policyengine/populace-us/populace_us_2024.h5` artifact. The
population pin metadata records `built_with = 1.729.0`.

### Report-version caveat

The five reports were generated on July 6, 2026 with
`policyengine_us = 1.752.2`, not the assigned 1.767.3. The live reproduction
in section 5 independently confirms the same defective branch on exactly
1.767.3. The suites should be regenerated on 1.767.3 before final disposition
files are merged.

## 2. Repeated-income prevalence and source

The report value $217,027.52 is the cent-rounded value produced from source
$198,505 after 2026 uprating. The live calculated value is $217,027.515625,
an observed multiplier of approximately `1.093310070905015`; the ratio using
the cent-rounded metadata value is `1.0933100929447621`.

Pinned population artifact:

```text
/Users/maxghenis/.cache/huggingface/hub/
  datasets--policyengine--populace-us/snapshots/
  d8f5cff65f36205a613cb144fd97db3087bbd82a/populace_us_2024.h5
SHA-256:
  16be6338f9d0b3c339883dae59949e995663b64cf145de6728b3dd0f916c5d5f
```

| Scope | Households | Persons | Exact-$198,505 persons | Exact-value households | Exact-value minors | Exact-value minor singletons |
|---|---:|---:|---:|---:|---:|---:|
| AL | 1,444 | 2,998 | 18 | 17 | 9 | 3 |
| MA | 1,632 | 3,507 | 23 | 23 | 4 | 1 |
| NC | 1,854 | 3,964 | 30 | 29 | 12 | 3 |
| SC | 1,283 | 2,690 | 12 | 11 | 6 | 2 |
| TN | 1,427 | 3,032 | 18 | 18 | 6 | 2 |
| **Five states** | **7,640** | **16,191** | **101** | **98** | **37** | **11** |
| **Nationwide** | **75,112** | **160,858** | **990** | **945** | **194** | **66** |

The point is 0.6154% of nationwide persons and occurs in 1.2581% of
nationwide households. In the five report states the corresponding rates are
0.6238% and 1.2827%. The 11 strict residuals carry a combined survey weight of
559.9380915004003.

The proposed ECPS top-code explanation is **not supported**:

- all 990 persons at exactly $198,505 have
  `person_is_puf_clone = true`, `_half = "synthetic_puf"`, and tax-unit role
  `HEAD`;
- 477 have raw CPS `WSAL_VAL = 0`, and the 990 records contain 168 distinct
  raw wage values from $0 through $120,000;
- 10,667 persons have `employment_income` above $198,505, with a maximum of
  $179,365,000, so $198,505 is not an `employment_income` cap;
- AL `ecps-37651` is a non-clone `cps_keep` record whose source and raw wage
  are both $20,000, yet it follows the same PolicyEngine branch.

The repeated value is therefore a **synthetic-PUF clone mass point**, not a
raw ECPS top-code. The available artifact does not establish whether the
original PUF record was itself disclosure-edited; it does establish that the
cross-household repetition here is produced by cloning.

## 3. Controlling retained law

The worktree pins `axiom-corpus` at
`f7fe8471c415908b26cfac1e199e92d1580c8ff3`. Every rule conclusion below was
checked in:

```text
data/corpus/provisions/us/regulation/
  2026-07-15-title-7-part-273.jsonl
```

using section records `us/regulation/7/273/1` and
`us/regulation/7/273/9`. The retained records' official source links are
[§ 273.1](https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.1)
and
[§ 273.9](https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9).

### Household composition: 7 CFR 273.1

- [§ 273.1(a)(1)](https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.1(a)(1))
  expressly includes an individual living alone. It imposes no minimum age.
- The mandatory combinations in
  [§ 273.1(b)(1)(ii)-(iii)](https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.1(b)(1))
  apply when an under-22 person lives with a parent or stepparent, or when an
  under-18 child lives with and is under the parental control of a nonparent
  household member. Neither condition can apply to a genuine one-person
  household.
- [§ 273.1(d)(1)](https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.1(d)(1))
  treats head designation as administrative. Its final sentence directs the
  state either to designate a head or let the household do so when the
  household does not consist of adult parents and children or adults
  exercising parental control. It is not a minor-head eligibility bar.

Thus a genuine minor living alone can form a SNAP household.

### Income: 7 CFR 273.9

- [§ 273.9(a)](https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(a))
  requires a nonelderly, nondisabled, noncategorically eligible household to
  pass both gross and net income standards.
- [§ 273.9(b)](https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(b))
  includes income from every source except the enumerated paragraph (c)
  exclusions; paragraph (b)(1)(i) specifically includes all employee wages
  and salaries.
- The decisive
  [§ 273.9(c)(7)](https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(c)(7))
  exclusion has three conjunctive requirements: the member is under 18, is an
  elementary or secondary student, **and lives with a parent or under the
  parental control of another household member**. A lone minor fails the
  final condition, so the wages count.

For FY 2026, the encoded one-person gross limit is $1,696 per month. The
$217,027.52 cases have $18,085.6267 per month. Even the lower-income AL case
has $1,822.1833 per month. Eleven nonelderly/nondisabled cases fail the gross
standard. AL `ecps-36459` is marked disabled and therefore need only meet the
net standard, which its counted wages also exceed. The source facts show no
SSI, TANF/public-assistance, or other applicable categorical exception for
these 12 cases.

**Legal result:** the household exists, its wages count, and it is ineligible.

## 4. Axiom and adapter trace

Axiom has no federal `us/regulations/7-cfr/273/1.yaml`, and no state program
wrapper applies a minor-head prohibition. Alabama's retained state rule is
affirmative: `us-al/policies/dhr/poe/chapter-01-household-concept/103.yaml`
states that a responsible household member need not be an adult and a minor
may represent the household. North Carolina's retained
`fns-210-household-composition/page-1.yaml` summary likewise says that an FNS
unit can be a person living alone, although that module is marked
`entity_not_supported` and contributes no operational rule.

The relevant calculation path is:

1. The external generic adapter's
   `axiom_oracles/data/populace_input_mapping.yaml` derives
   `household_size` from the number of people and maps the sum of
   `YEARLY_EARNED_INCOME`, divided monthly, to
   `snap_gross_monthly_earned_income`. It does not inspect age or zero a
   minor's wages.
2. `us/regulations/7-cfr/273/10.yaml` lines 203-221 calculates total gross
   income as earned income plus unearned income minus supplied exclusions.
   Axiom does not operationally evaluate the paragraph (c)(7) predicates:
   the generic unresolved-input fallback supplies zero income exclusions,
   which is legally correct for this living-alone fact pattern.
3. `us/regulations/7-cfr/273/9.yaml` lines 37-65 applies the gross and net
   tests.
4. The AL and NC program files declare `snap_eligible` as an auto-gated
   output. Composition produces
   `snap_eligible = snap_eligible_core and snap_income_eligible`.

That path explains the reports without any age-based household rejection:
the adapter supplies the wages and Axiom's income gate returns false.

### Repository disposition

- **RuleSpec change in this worktree:** none.
- **ECPS adapter change in `axiom-oracles`:** none. Its treatment is correct
  for a one-person minor household.
- **Shared federal 273.9/273.10 change for this class:** none.

The federal `273/9.yaml` module explicitly defers the detailed paragraph
(b)/(c) income-composition layer. That broader gap could matter for the
opposite fact pattern—a student under 18 who *does* live with a parent or
controlling member—but it does not cause these lone-minor results. If Worker A
later closes that shared gap, the exclusion must require all of age, school
status, and the parent/parental-control relationship; it must include lone
minor and co-resident-child controls. Worker B did not edit the shared federal
files.

## 5. PolicyEngine US 1.767.3 trace and live reproduction

The exact 1.767.3 wheel is cached at:

```text
/Users/maxghenis/.cache/uv/archive-v0/-QudTS5FEzSKZ0Anf7ddx
```

Its relevant files byte-match local PolicyEngine source commit
`49d19b239a593dbac8920ac6fd80cfe33372343a`. The live environment used
`policyengine-core==3.26.0` and `spm-calculator==0.2.0`.

### SNAP unit formation

PolicyEngine does not independently construct a regulatory SNAP unit here:

- `policyengine_us/entities.py` lines 20-36 gives an SPM unit only generic
  members, without parent/child roles;
- `spm_unit_size.py` is the number of members;
- `snap_unit_size.py` lines 14-23 starts with SPM-unit size and removes only
  student-, immigration-, and work-requirement-ineligible members.

The supplied one-person SPM unit therefore remains a one-person SNAP unit.
That outcome is correct for these facts.

### Income-counting defect

- `is_in_k12_school.py` lines 10-17 by default imputes school attendance for
  ages 5 through 17 unless explicitly overridden.
- `snap_excluded_child_earner.py` lines 14-19 returns only
  `is_in_k12_school & (age <= 17)`. It omits co-resident parent and parental
  control.
- `snap_countable_earner.py` lines 15-24 consequently returns false.
- `snap_earned_income_person.py` and `snap_earned_income.py` remove all wages.
- `snap_gross_income.py` then returns zero, and `is_snap_eligible.py` passes
  the gross and net tests.

The model accepts explicit `is_household_head = true`, but the exclusion
ignores it. `is_tax_unit_dependent` is also not a valid substitute:
PolicyEngine infers the lone minor as a dependent because its tax-unit-head
inference admits only adults.

The committed reproduction is
`tools/reproduce_policyengine_snap_teen.py`. It uses 2026-01 and the exact
report income:

```sh
PE_US_PATH=/Users/maxghenis/.cache/uv/archive-v0/-QudTS5FEzSKZ0Anf7ddx
PE_CORE_PATH=$(readlink /Users/maxghenis/.cache/uv/wheels-v6/pypi/policyengine-core/3.26.0-py3-none-any)
SPM_CALC_PATH=$(readlink /Users/maxghenis/.cache/uv/wheels-v6/pypi/spm-calculator/0.2.0-py3-none-any)
PYTHONPATH="$PE_US_PATH:$PE_CORE_PATH:$SPM_CALC_PATH" \
  /Users/maxghenis/m6-sol-lanes/remarr-r2-runtime/bin/python \
  tools/reproduce_policyengine_snap_teen.py
```

Key output for both AL age 17 and NC age 15:

```text
policyengine-us=1.767.3
policyengine-core=3.26.0
spm-calculator=0.2.0
employment_income_annual=217027.515625
is_in_k12_school=True
is_household_head=True
spm_unit_size=1
snap_unit_size=1
snap_excluded_child_earner=True
snap_countable_earner=False
snap_earned_income=0.0
snap_gross_income=0.0
meets_snap_gross_income_test=True
meets_snap_net_income_test=True
is_snap_eligible=True
snap=298.0
```

Changing only `is_in_k12_school` to false is the causal control:

```text
snap_excluded_child_earner=False
snap_countable_earner=True
snap_earned_income=18085.626953125
snap_gross_income=18085.626953125
meets_snap_gross_income_test=False
meets_snap_net_income_test=False
is_snap_eligible=False
snap=0.0
```

The age-18 control follows the same countable-income path.

## 6. Draft PolicyEngine issue

No issue was filed because this lane prohibits GitHub writes.

### Title

SNAP child-earned-income exclusion incorrectly applies to minor household
heads living alone

### Body

Environment: `policyengine-us==1.767.3`,
`policyengine-core==3.26.0`, 2026-01 simulation.

A one-person SPM/household unit headed by a 15- or 17-year-old with annual
employment income of $217,027.52 receives SNAP. PolicyEngine imputes K-12
attendance from age, marks the sole household head as
`snap_excluded_child_earner`, removes all wages from SNAP gross income, and
returns eligibility plus a $298 monthly benefit:

```python
from policyengine_us import Simulation

sim = Simulation(
    situation={
        "people": {
            "teen": {
                "age": {"2026": 17},
                "employment_income": {"2026": 217_027.52},
                "is_household_head": True,
            }
        },
        "families": {"family": {"members": ["teen"]}},
        "marital_units": {"marital_unit": {"members": ["teen"]}},
        "spm_units": {"spm_unit": {"members": ["teen"]}},
        "tax_units": {"tax_unit": {"members": ["teen"]}},
        "households": {
            "household": {
                "members": ["teen"],
                "state_code": {"2026": "AL"},
            }
        },
    }
)

for variable in (
    "snap_excluded_child_earner",
    "snap_earned_income",
    "snap_gross_income",
    "is_snap_eligible",
    "snap",
):
    print(variable, sim.calculate(variable, "2026-01")[0])
```

```text
is_household_head=True
snap_unit_size=1
snap_excluded_child_earner=True
snap_earned_income=0
snap_gross_income=0
is_snap_eligible=True
snap=298
```

Setting only `is_in_k12_school=False` causes the same wages to be counted,
both income tests to fail, and SNAP to become zero. This demonstrates the
causal branch.

7 CFR 273.1(a)(1) permits an individual living alone to be a household.
7 CFR 273.9(b)(1)(i) counts wages. Section 273.9(c)(7) excludes a student's
earnings only when the under-18 student also lives with a parent or under the
parental control of another household member. A one-person household cannot
satisfy that final condition.

The defect is in `snap_excluded_child_earner`: its predicate uses only age and
school attendance and cannot represent/check the residence or parental-control
condition. It ignores explicit `is_household_head=True`.

Suggested resolution:

1. Add a relationship/parental-control-aware predicate and require it in
   `snap_excluded_child_earner`.
2. A guard for an explicit household head would fix this minimal case but is
   only a partial proxy; do not use `is_tax_unit_dependent` alone.
3. Add regression cases for:
   - lone age-15 and age-17 household heads with wages: wages count and SNAP
     is zero;
   - an under-18 student living with a qualifying parent/controlling member:
     the child-income exclusion remains;
   - age 18 and age 17 with school status false as controls.

Minimal reproduction:
`tools/reproduce_policyengine_snap_teen.py`.

## 7. Proposed suite dispositions

These are copy-ready schema-valid grouped entries for the current reports.
Split each YAML document into the named
`axiom-oracles/dispositions/<suite>.yaml` file. They intentionally contain no
`linked_issue` because no issue was filed. After filing, add the issue URL as
`linked_issue` and `evidence.upstream_url`. Regenerate the five suites on
PolicyEngine US 1.767.3 before merging these files; remove any case selector
whose mismatch no longer exists.

```yaml
schema: axiom_oracles.dispositions.v1
suite: al-snap-ecps
updated: '2026-07-27'
entries:
  - id: pe-lone-minor-child-earnings-benefit
    concept: us:statutes/7/2014/u#snap_benefit
    case_selector:
      case_ids:
        - ecps-36459
        - ecps-36559
        - ecps-37623
        - ecps-37651
    kind: amount_difference
    disposition: upstream_engine_gap
    evidence: &pe_lone_minor_evidence
      mechanism: >-
        PolicyEngine excludes all earnings of an imputed K-12 member age 17
        or younger without requiring the co-resident-parent or parental-control
        condition in 7 CFR 273.9(c)(7). The sole minor is a valid household
        under 273.1(a)(1), but wages count under 273.9(b)(1)(i), so Axiom
        correctly fails the income gate and returns zero benefit.
      sources:
        - dashboard/public/data/axiom-policyengine-al-snap-ecps.json
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.1(a)(1)
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(b)(1)(i)
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(c)(7)
    expires_on_source_change: true
  - id: pe-lone-minor-child-earnings-eligibility
    concept: us:statutes/7/2014/o#snap_eligible
    case_selector:
      case_ids:
        - ecps-36459
        - ecps-36559
        - ecps-37623
        - ecps-37651
    kind: eligibility_right_only
    disposition: upstream_engine_gap
    evidence: *pe_lone_minor_evidence
    expires_on_source_change: true
---
schema: axiom_oracles.dispositions.v1
suite: ma-snap-ecps
updated: '2026-07-27'
entries:
  - id: pe-lone-minor-child-earnings-benefit
    concept: us:statutes/7/2014/u#snap_benefit
    case_selector:
      case_ids:
        - ecps-2194
    kind: amount_difference
    disposition: upstream_engine_gap
    evidence: &pe_lone_minor_evidence
      mechanism: >-
        PolicyEngine excludes all earnings of an imputed K-12 member age 17
        or younger without requiring the co-resident-parent or parental-control
        condition in 7 CFR 273.9(c)(7). The sole minor is a valid household
        under 273.1(a)(1), but wages count under 273.9(b)(1)(i), so Axiom
        correctly fails the income gate and returns zero benefit.
      sources:
        - dashboard/public/data/axiom-policyengine-ma-snap-ecps.json
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.1(a)(1)
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(b)(1)(i)
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(c)(7)
    expires_on_source_change: true
  - id: pe-lone-minor-child-earnings-eligibility
    concept: us:statutes/7/2014/o#snap_eligible
    case_selector:
      case_ids:
        - ecps-2194
    kind: eligibility_right_only
    disposition: upstream_engine_gap
    evidence: *pe_lone_minor_evidence
    expires_on_source_change: true
---
schema: axiom_oracles.dispositions.v1
suite: nc-snap-ecps
updated: '2026-07-27'
entries:
  - id: pe-lone-minor-child-earnings-benefit
    concept: us:statutes/7/2014/u#snap_benefit
    case_selector:
      case_ids:
        - ecps-27147
        - ecps-27597
        - ecps-27962
    kind: amount_difference
    disposition: upstream_engine_gap
    evidence: &pe_lone_minor_evidence
      mechanism: >-
        PolicyEngine excludes all earnings of an imputed K-12 member age 17
        or younger without requiring the co-resident-parent or parental-control
        condition in 7 CFR 273.9(c)(7). The sole minor is a valid household
        under 273.1(a)(1), but wages count under 273.9(b)(1)(i), so Axiom
        correctly fails the income gate and returns zero benefit.
      sources:
        - dashboard/public/data/axiom-policyengine-nc-snap-ecps.json
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.1(a)(1)
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(b)(1)(i)
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(c)(7)
    expires_on_source_change: true
  - id: pe-lone-minor-child-earnings-eligibility
    concept: us:statutes/7/2014/o#snap_eligible
    case_selector:
      case_ids:
        - ecps-27147
        - ecps-27597
        - ecps-27962
    kind: eligibility_right_only
    disposition: upstream_engine_gap
    evidence: *pe_lone_minor_evidence
    expires_on_source_change: true
---
schema: axiom_oracles.dispositions.v1
suite: sc-snap-ecps
updated: '2026-07-27'
entries:
  - id: pe-lone-minor-child-earnings-benefit
    concept: us:statutes/7/2014/u#snap_benefit
    case_selector:
      case_ids:
        - ecps-29280
        - ecps-29677
    kind: amount_difference
    disposition: upstream_engine_gap
    evidence: &pe_lone_minor_evidence
      mechanism: >-
        PolicyEngine excludes all earnings of an imputed K-12 member age 17
        or younger without requiring the co-resident-parent or parental-control
        condition in 7 CFR 273.9(c)(7). The sole minor is a valid household
        under 273.1(a)(1), but wages count under 273.9(b)(1)(i), so Axiom
        correctly fails the income gate and returns zero benefit.
      sources:
        - dashboard/public/data/axiom-policyengine-sc-snap-ecps.json
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.1(a)(1)
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(b)(1)(i)
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(c)(7)
    expires_on_source_change: true
  - id: pe-lone-minor-child-earnings-eligibility
    concept: us:statutes/7/2014/o#snap_eligible
    case_selector:
      case_ids:
        - ecps-29280
        - ecps-29677
    kind: eligibility_right_only
    disposition: upstream_engine_gap
    evidence: *pe_lone_minor_evidence
    expires_on_source_change: true
---
schema: axiom_oracles.dispositions.v1
suite: tn-snap-ecps
updated: '2026-07-27'
entries:
  - id: pe-lone-minor-child-earnings-benefit
    concept: us:statutes/7/2014/u#snap_benefit
    case_selector:
      case_ids:
        - ecps-35407
        - ecps-35601
    kind: amount_difference
    disposition: upstream_engine_gap
    evidence: &pe_lone_minor_evidence
      mechanism: >-
        PolicyEngine excludes all earnings of an imputed K-12 member age 17
        or younger without requiring the co-resident-parent or parental-control
        condition in 7 CFR 273.9(c)(7). The sole minor is a valid household
        under 273.1(a)(1), but wages count under 273.9(b)(1)(i), so Axiom
        correctly fails the income gate and returns zero benefit.
      sources:
        - dashboard/public/data/axiom-policyengine-tn-snap-ecps.json
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.1(a)(1)
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(b)(1)(i)
        - https://www.ecfr.gov/current/title-7/chapter-II/subchapter-C/part-273#p-273.9(c)(7)
    expires_on_source_change: true
  - id: pe-lone-minor-child-earnings-eligibility
    concept: us:statutes/7/2014/o#snap_eligible
    case_selector:
      case_ids:
        - ecps-35407
        - ecps-35601
    kind: eligibility_right_only
    disposition: upstream_engine_gap
    evidence: *pe_lone_minor_evidence
    expires_on_source_change: true
```

## 8. Validation and limitations

Successful checks:

- exact PolicyEngine US 1.767.3 live reproduction for AL age 17, NC age 15,
  school-status control, and age-18 control;
- `us/regulations/7-cfr/273/9.test.yaml`: 4 companion cases passed;
- `us/regulations/7-cfr/273/10.test.yaml`: 5 companion cases passed;
- report inventory was checked across all five untruncated dashboard reports;
- retained law was read from the pinned corpus ref, not from recollection or
  an unpinned web copy;
- all five proposed disposition documents passed
  `validate_dispositions` against the `axiom-oracles` repository.

Environment/tool limitations encountered:

- The prescribed engine path
  `/Users/maxghenis/TheAxiomFoundation/axiom-rules` does not exist, so the
  first companion-test attempt failed before running cases. The successful
  rerun used the matching pinned engine at
  `/Users/maxghenis/TheAxiomFoundation/_worktrees/axiom-rules-engine-782-pinned`
  (commit `e19f1b7573c74512f20a6b71a0c55dbbf333d41b`).
- A parallel first rerun caused a temporary RuleSpec alias-symlink collision
  for the 273.9 suite; its sequential rerun passed all four cases.
- `/Users/maxghenis/axiom-encode/.venv` does not contain PolicyEngine. A
  scratch UV environment was blocked by sandbox permissions on a cached
  package's internal `.git`; the exact cached 1.767.3 wheel and pinned cached
  dependencies were therefore executed read-only via `PYTHONPATH`.
- GitNexus reported this worktree was not indexed and no GitNexus MCP tools
  were available. The local CLI could query an indexed PolicyEngine source
  checkout; because that graph was not pinned to 1.767.3, the final trace
  verified the exact cached 1.767.3 files directly.

No encode file changed, so no companion test or mutation fixture was added.
No toolchain, workflow, CODEOWNERS, manifest, external adapter, disposition,
or GitHub state was modified.

## 9. Local commits

- `d378f0777` — `docs: start SNAP teen investigation log`
- `a954681ed` — `docs: record SNAP teen case inventory`
- `d5f5d0d87` — `docs: record SNAP teen legal conclusion`
- `92becd9bb` — `test: add PolicyEngine SNAP lone-minor repro`
- `8207feb60` — `test: align SNAP teen repro to 2026 period`
