# Worker C: Tennessee SNAP deduction/utility residual report

## Outcome

No Tennessee RuleSpec encode was changed.

The proposed utility-allowance root cause is falsified for these comparison cases
under both the report's PolicyEngine-US 1.752.2 and the requested 1.767.3:

- all 48 Tennessee benefit-only residual households have utility allowance type
  `NONE`;
- SUA, LUA/BUA, telephone/IUA, and total utility allowance are all $0 for all 48;
- only 7 of the 48 have a positive housing cost, and only 3 have a positive excess
  shelter deduction under 1.752.2 (4 under 1.767.3).

`ecps-35254` instead exposes a cross-program population-bridge asymmetry.
PolicyEngine endogenously computes Tennessee Families First (`tn_ff`) and counts it
as TANF unearned income in SNAP. The Axiom input mapping asks for a
`TANF_BENEFITS` fact, but the Populace loader never emits `tanf_person`, so Axiom
receives $0 of TANF. That is an oracle bridge artifact, not a Tennessee SNAP rule
defect. Retained 7 CFR 273.9(b)(2)(i) supports PolicyEngine's treatment of TANF as
unearned income. The same asymmetry is present in 31 of the 48 target cases; all 31
have Axiom benefits above PolicyEngine. The other 17 cases remain unexplained here.

There is a separate, real Tennessee utility source gap: the current program has no
active state utility amount, while PolicyEngine 1.767.3 carries FY2026 values.
However, the pinned corpus does **not** retain a current Tennessee FY2026 utility
chart or FY2026 FNS state table. It therefore cannot support copying PolicyEngine's
numbers into Axiom. Current source ingest is a prerequisite.

No PolicyEngine issue is justified by this evidence. A draft `axiom-oracles` bridge
issue and proposed residual dispositions appear below. No GitHub write was made.

## Scope and provenance

The five supplied reports are:

```text
/Users/maxghenis/TheAxiomFoundation/axiom-oracles/dashboard/public/data/
  axiom-policyengine-{al,ma,nc,sc,tn}-snap-ecps.json
```

The target report class is defined from the materialized mismatch records as:

1. a `snap_benefit` `amount_difference`; and
2. no `snap_eligible` mismatch in the same case.

Because `snap_benefit` is auto-gated on eligibility, a nonzero benefit mismatch
without an eligibility mismatch establishes that both engines agree on eligibility.
The class does not require both benefit amounts to be positive: 2 Massachusetts and
5 North Carolina cases have a zero benefit on one side despite agreeing on
eligibility.

Important provenance correction: the reports were generated on 2026-07-06 with:

| Component | Report provenance |
|---|---:|
| PolicyEngine-US | **1.752.2** |
| PolicyEngine package | 4.18.9 |
| Axiom rules engine | `e19f1b7573c74512f20a6b71a0c55dbbf333d41b` |
| RuleSpec-US | `a0bcc5a39fa57f02f0c75c9d4a9e6bfd8670c58c` |

The assignment requests inspection of PolicyEngine-US 1.767.3. Results from that
version are therefore a current source/behavior audit, not a bit-for-bit
reproduction of the supplied report. The Tennessee SNAP files have not changed
since the report RuleSpec SHA; the only `us-tn/**` changes between that SHA and this
branch are unrelated income-tax additions.

The report-producing configuration at `axiom-oracles` commit
`c51c7e055d8f0ca18ac2be3ace8166e38132e167` used the general
`axiom-oracles-compare` pipeline, not the specialized SPM-unit SNAP bridge.
Accordingly, `ecps-35254` means raw household ID 35254. Its county and ages in the
certified H5 are `47157` and `[13, 10, 2, 30]`, exactly matching the report. The
general loader rebuilds a synthetic one-SPM-unit case and supplies aggregate
housing cost but no utility-expense facts. The certified H5 has SHA-256
`16be6338f9d0b3c339883dae59949e995663b64cf145de6728b3dd0f916c5d5f`.

All legal claims below use the corpus ref pinned in `.axiom/toolchain.toml`:

```text
f7fe8471c415908b26cfac1e199e92d1580c8ff3
```

## Residual inventory

### All 70 materialized Tennessee residual cases

| Residual combination | Cases | Case IDs |
|---|---:|---|
| Benefit amount only (target class) | 48 | Detailed below |
| Benefit + Axiom-only eligibility | 16 | 35306, 35309, 35344, 35453, 35491, 35539, 35635, 35965, 35997, 36095, 36256, 36265, 36298, 36349, 36374, 74728 |
| Benefit + PolicyEngine-only eligibility | 3 | 35407, 35601, 36308 |
| PolicyEngine-only eligibility only | 3 | 35744, 35845, 35971 |
| **Total** | **70** | |

The report is complete with respect to its 89 Tennessee mismatch records; it
materializes only cases having at least one mismatch.

### Same class across all five states

Every state has the structural class. “Household shape” here is reported first as
household size; the detailed Tennessee table then preserves each exact age and
earned-income vector.

| State | Class cases | Household-size distribution | Axiom > PE | Axiom < PE | Both benefits > $0 |
|---|---:|---|---:|---:|---:|
| AL | 37 | 1:5, 2:5, 3:7, 4:4, 5:5, 6:9, 7:1, 8:1 | 23 | 14 | 37 |
| MA | 134 | 1:66, 2:32, 3:21, 4:10, 5:3, 6:1, 9:1 | 32 | 102 | 132 |
| NC | 69 | 1:11, 2:5, 3:10, 4:11, 5:21, 6:8, 7:1, 8:1, 9:1 | 36 | 33 | 64 |
| SC | 49 | 1:8, 2:11, 3:12, 4:7, 5:6, 6:4, 7:1 | 47 | 2 | 49 |
| TN | 48 | 1:5, 2:8, 3:15, 4:8, 5:6, 6:2, 7:1, 8:2, 9:1 | 43 | 5 | 48 |
| **Total** | **337** | | **181** | **156** | **330** |

The same mismatch shape across states does not establish a shared cause. The
Tennessee live component trace below rules out utility allowances for its 48 cases.

Tennessee report deltas range from -$11.35 to +$628.55 per month. The median is
+$100.81. (`difference = Axiom - PolicyEngine`.)

### All 48 Tennessee target cases

The benefit columns are monthly dollars from the supplied 1.752.2 report. Earned
income is the report's annual per-person vector. Values are rounded to cents only
for display.

| Case | Size | Ages | Annual earned income by person | Axiom | PE 1.752.2 | Delta |
|---|---:|---|---|---:|---:|---:|
| ecps-35254 | 4 | 13,10,2,30 | 0,0,0,19679.58 | 667 | 564.65 | 102.35 |
| ecps-35266 | 4 | 35,14,10,8 | 16399.65,0,0,0 | 732 | 607.55 | 124.45 |
| ecps-35294 | 5 | 27,36,11,3,1 | 0,47012.33,0,0,0 | 303 | 310.18 | -7.18 |
| ecps-35304 | 3 | 36,10,7 | 0,0,0 | 785 | 410.27 | 374.73 |
| ecps-35320 | 2 | 58,11 | 16399.65,0 | 280 | 208.33 | 71.67 |
| ecps-35324 | 3 | 51,67,13 | 0,0,0 | 457 | 387.77 | 69.23 |
| ecps-35347 | 3 | 31,15,8 | 14553.05,0,0 | 497 | 386.57 | 110.43 |
| ecps-35438 | 3 | 43,45,11 | 28852.45,0,0 | 270 | 259.67 | 10.33 |
| ecps-35480 | 1 | 22 | 0 | 298 | 206.67 | 91.33 |
| ecps-35493 | 6 | 35,31,6,5,4,1 | 44155.26,0,0,0,0,0 | 627 | 636.29 | -9.29 |
| ecps-35504 | 3 | 37,17,10 | 0,0,0 | 785 | 408.77 | 376.23 |
| ecps-35590 | 2 | 33,7 | 6468.02,0 | 479 | 379.93 | 99.07 |
| ecps-35596 | 2 | 49,12 | 9839.79,0 | 411 | 312.66 | 98.34 |
| ecps-35643 | 2 | 37,15 | 7131.98,0 | 466 | 366.73 | 99.27 |
| ecps-35647 | 3 | 31,28,3 | 0,0,0 | 785 | 460.60 | 324.40 |
| ecps-35661 | 3 | 40,12,9 | 0,0,0 | 785 | 736.37 | 48.63 |
| ecps-35696 | 5 | 44,41,15,8,6 | 13119.72,0,0,0,0 | 1170 | 965.60 | 204.40 |
| ecps-35704 | 2 | 30,4 | 5314.48,0 | 497 | 162.73 | 334.27 |
| ecps-35708 | 4 | 31,30,3,0 | 0,0,0,0 | 994 | 935.45 | 58.55 |
| ecps-35789 | 3 | 24,0,63 | 6559.86,0,0 | 716 | 605.27 | 110.73 |
| ecps-35827 | 4 | 49,12,11,9 | 0,0,0,0 | 994 | 365.45 | 628.55 |
| ecps-35835 | 3 | 43,36,10 | 0,0,0 | 785 | 455.87 | 329.13 |
| ecps-35902 | 8 | 34,34,15,12,6,5,4,1 | 44295.14,0,0,0,0,0,0,0 | 992 | 1003.35 | -11.35 |
| ecps-35911 | 6 | 54,15,15,0,10,9 | 0,0,0,0,0,0 | 1421 | 1368.59 | 52.41 |
| ecps-35930 | 4 | 42,45,17,15 | 15208.62,0,0,0 | 756 | 362.45 | 393.55 |
| ecps-35974 | 3 | 44,18,15 | 19345.32,0,0 | 460 | 409.67 | 50.33 |
| ecps-36024 | 1 | 17 | 0 | 298 | 289.54 | 8.46 |
| ecps-36061 | 5 | 46,45,24,17,11 | 0,0,9970.99,0,0 | 1061 | 747.88 | 313.12 |
| ecps-36069 | 2 | 31,8 | 16399.65,0 | 280 | 208.33 | 71.67 |
| ecps-36071 | 3 | 65,65,16 | 0,0,0 | 527 | 416.27 | 110.73 |
| ecps-36087 | 4 | 28,34,5,2 | 0,0,0,0 | 994 | 406.85 | 587.15 |
| ecps-36102 | 3 | 43,19,16 | 0,0,0 | 785 | 736.37 | 48.63 |
| ecps-36129 | 4 | 45,54,17,16 | 19023.60,0,0,0 | 680 | 561.65 | 118.35 |
| ecps-36137 | 5 | 39,17,17,15,6 | 33892.61,0,0,0,0 | 583 | 590.68 | -7.68 |
| ecps-36188 | 3 | 36,9,4 | 12026.41,0,0 | 607 | 496.00 | 111.00 |
| ecps-36206 | 3 | 47,20,18 | 1115.18,0,0 | 785 | 493.90 | 291.10 |
| ecps-36219 | 1 | 64 | 0 | 298 | 243.87 | 54.13 |
| ecps-36247 | 4 | 25,5,3,2 | 8164.29,0,0,0 | 939 | 772.25 | 166.75 |
| ecps-36253 | 1 | 34 | 0 | 298 | 182.67 | 115.33 |
| ecps-36258 | 5 | 30,29,8,5,2 | 0,0,0,0,0 | 1183 | 1143.80 | 39.20 |
| ecps-36303 | 9 | 58,11,9,12,46,27,6,29,10 | 82,0,0,0,0,24052.82,0,0,0 | 1527 | 1466.17 | 60.83 |
| ecps-36323 | 8 | 35,18,14,13,12,11,8,39 | 34755.36,0,0,0,0,0,0,27379.06 | 636 | 646.65 | -10.65 |
| ecps-36346 | 2 | 45,4 | 7344.60,0 | 546 | 414.88 | 131.12 |
| ecps-36378 | 7 | 38,39,17,16,14,14,11 | 33766.88,0,0,0,0,0,0 | 985 | 750.53 | 234.47 |
| ecps-36395 | 2 | 48,43 | 0,0 | 546 | 268.03 | 277.97 |
| ecps-36403 | 3 | 17,45,43 | 0,10961.88,0 | 624 | 513.47 | 110.53 |
| ecps-36407 | 5 | 53,48,18,14,12 | 0,0,0,0,0 | 1183 | 1127.08 | 55.92 |
| ecps-36436 | 1 | 21 | 0 | 298 | 289.54 | 8.46 |

Reproducible inventory query:

```bash
for st in al ma nc sc tn; do
  f=/Users/maxghenis/TheAxiomFoundation/axiom-oracles/dashboard/public/data/axiom-policyengine-${st}-snap-ecps.json
  jq -r --arg state "$st" '
    .cases[]
    | ([.mismatches[]
        | select(.concept=="us:statutes/7/2014/u#snap_benefit"
                 and .kind=="amount_difference")][0]) as $b
    | select($b != null)
    | select(all(.mismatches[];
        .concept != "us:statutes/7/2014/o#snap_eligible"))
    | [
        $state, .case_id, .metadata.scope.geoid,
        .metadata.household_weight,
        .metadata.household_summary.household_size,
        (.metadata.household_summary.ages|tojson),
        (.metadata.household_summary.yearly_earned_income_per_person|tojson),
        .metadata.household_summary.yearly_earned_income_total,
        $b.left, $b.right, $b.difference
      ]
    | @tsv
  ' "$f"
done
```

## Utility parameter and wiring audit

### Amount comparison

| Source/runtime | HCSUA/SUA by size 1–10+ | LUA/BUA | Telephone/IUA | Current authority status |
|---|---|---:|---:|---|
| Axiom FY2026 active program | No TN state amount; federal option defaults to $0 | $0 | $0 | Missing state amounts |
| Unscoped `us-tn/regulations/1240-01/04/27/block-1.yaml` | 314, 326, 338, 350, 360, 372, 384, 396, 408, 419 | 126 | 25 | Retained non-primary table; no current effective interval |
| Retained FNS FY2024 table | 430, 445, 462, 480, 495, 511, 526, 542, 560, 574 | 164 | 35 | Primary, but only 2023-10-01 through 2024-09-30 |
| PolicyEngine-US 1.752.2 and 1.767.3 at 2026-01 | 451, 466, 485, 503, 519, 536, 551, 568, 587, 602 | 162 | 36 | Oracle parameter, not corpus authority |
| Retained FY2026 authority | **Absent** | **Absent** | **Absent** | Ingest prerequisite |

The exact PolicyEngine-US package sources inspected were:

```text
/Users/maxghenis/.cache/uv/wheels-v6/pypi/policyengine-us/1.752.2-py3-none-any
/Users/maxghenis/.cache/uv/wheels-v6/pypi/policyengine-us/1.767.3-py3-none-any
```

Their resolved archive sources are:

```text
/Users/maxghenis/.cache/uv/archive-v0/P9Ky5D9haWGhyYZ6g2W8t/policyengine_us
/Users/maxghenis/.cache/uv/archive-v0/-QudTS5FEzSKZ0Anf7ddx/policyengine_us
```

The cached 1.767.3 source corresponds to PolicyEngine-US git commit
`49d19b239a593dbac8920ac6fd80cfe33372343a`.
The five relevant parameter files are byte-identical between these versions.
PolicyEngine selects one allowance type in priority order: SUA for a
heating/cooling expense, LUA for at least two other utilities where active, IUA
for one utility, otherwise `NONE`. It does not stack these components for the
traced households. Tennessee has `always_standard = false` and an active LUA.

### Axiom FY2026 wiring

`programs/us-tn/snap/fy-2026.yaml` does not scope
`us-tn/regulations/1240-01/04/27/block-1.yaml`. Its
`snap_total_allowable_shelter_expenses` composition currently includes only
`household_shelter_costs_incurred`; it does not include the federal utility hook.
Consequently, the stale state utility table is inactive, and the federal state
options remain at their $0 defaults.

That is a real coverage gap for future utility-bearing Tennessee cases, but it
cannot explain the 48 traced cases because PolicyEngine itself assigns every one of
them $0 of utility allowance.

Scoping the old regulation is unsafe. It exports SUA, BUA, and telephone amounts
unconditionally from `0001-01-01`, while the federal module currently sums all three
state-option hooks. That would permit overlapping utility standards and would also
activate stale income, allotment, deduction, and shelter tables from the same
module.

### Exact target-case batches

| Component condition | PE-US 1.752.2 | PE-US 1.767.3 |
|---|---:|---:|
| Utility type `NONE` | 48 | 48 |
| Positive SUA, LUA, IUA, or total utility allowance | 0 | 0 |
| Positive housing cost | 7 | 7 |
| Positive excess-shelter deduction | 3 | 4 |
| Positive TN Families First/TANF | 31 | 31 |

The 31 Families First cases are identical under both versions:

```text
35254, 35266, 35304, 35320, 35324, 35347, 35590, 35596, 35643, 35647,
35661, 35696, 35708, 35789, 35835, 35911, 35974, 36024, 36061, 36069,
36071, 36102, 36129, 36188, 36247, 36258, 36303, 36346, 36403, 36407,
36436
```

The 7 housing-cost cases are:

```text
35294, 35480, 35696, 36087, 36247, 36258, 36346
```

Under 1.752.2, only `35480`, `35696`, and `36346` have a positive
excess-shelter deduction. Version 1.767.3 additionally gives `36258` a positive
deduction. None has a utility allowance.

## Retained authority

### Federal utility rules

The pinned corpus's exact provision anchors are in:

```text
data/corpus/anchors/us/regulation/2026-05-10-snap-7-cfr-273.jsonl
```

- `us/regulation/7/273/9/d/6/iii/A` permits state standard utility allowances,
  allows state variation including household size, defines individual, HCSUA, and
  LUA standards, requires the LUA to include at least two utilities, and prohibits
  two standards that include the same expense.
- `us/regulation/7/273/9/d/6/iii/B` requires annual review, whole-dollar cost
  adjustments, annual reporting of amounts to FNS, and FNS approval when a
  methodology changes.
- `us/regulation/7/273/9/d/6/iii/C` requires FNS methodology approval at least every
  five years using recent, reliable, low-income residential utility data.

These provisions establish the state delegation and non-stacking structure. They do
not establish Tennessee dollar amounts.

### Tennessee manual

The pinned primary Tennessee source is:

```text
data/corpus/provisions/us-tn/manual/
  2026-05-27-tn-snap-policies-r2026-07-15-self-contained.jsonl
```

- `us-tn/manual/dhs/snap/24-18/page-5` makes the SUA available for households that
  directly incur separate heating or cooling costs and limits the telephone
  allowance to households not entitled to another utility allowance.
- `us-tn/manual/dhs/snap/24-18/page-6` describes the costs included in the SUA and
  conditions that allow or bar its use.
- `us-tn/manual/dhs/snap/24-18/page-7` makes the BUA available for at least two
  non-heating/cooling utilities and refers the reader to a “Utility Allowance
  Chart.”
- `us-tn/manual/dhs/snap/24-18/page-17` lists “Standard Utility Allowance {SUA},”
  “Family Assistance Standards Desk Guide,” and “Utility Allowance Chart” as
  supporting documents.

Those supporting documents and their current amounts are not retained at the pinned
corpus ref.

### Retained amount sources

The strongest retained primary amount source is the FNS FY2024 technical table:

```text
us/guidance/usda/fns/snap-qc-fy2024-technical-documentation/page-184
```

It is explicitly effective only from 2023-10-01 through 2024-09-30. Its Tennessee
amounts are HCSUA $430–$574 by household size, LUA $164, and telephone $35. It proves
the $314/$126/$25 table is obsolete for current use but does not support FY2026.

The older source:

```text
us-tn/regulation/1240-01/04/27/block-1
```

contains $314–$419, $126, and $25. Corpus metadata marks it
`primary_source: false` and explains that Cornell LII is being used as a
normalization source pending a full official Title 1240 ingest. The retained text
does not establish a safe current or historical effective interval.

### Source conclusion

A current primary Tennessee DHS allowance chart or the authoritative FNS FY2026 SUA
table must be ingested before any FY2026 amount is encoded. PolicyEngine's values
are useful comparison evidence, not legal authority.

## Root cause for `ecps-35254`

### Live component trace

| Item | Supplied report / exact PE runs |
|---|---:|
| Report Axiom benefit | $667.00/month |
| Report PE 1.752.2 benefit | $564.645345/month |
| PE 1.767.3 benefit through the same pipeline | $564.645345/month |
| Report delta | +$102.354655/month |
| PE earned income | $1,639.9650/month |
| PE TN Families First (`tn_ff`) | $362.0347/month |
| PE TANF | $362.0347/month |
| PE unearned income | $362.0347/month |
| PE gross income | $2,002.00/month |
| Housing cost | $0 |
| SUA / LUA / IUA / total utility | $0 / $0 / $0 / $0 |
| Excess-shelter deduction | $0 |

The exact 1.752.2 run reproduces the report's PolicyEngine value bit-for-bit.
Version 1.767.3 produces the same component values in this pipeline. The ordinary
SNAP contribution is 30% of net income, and 30% of the omitted $362.03 Families
First amount is about $108.61. The recorded $102.35 gap is therefore directionally
and materially explained by the TANF asymmetry; utility is exactly $0.

### TANF counterfactual

An exact 1.752.2 counterfactual over the same reconstructed comparison case
overrode both `tn_ff` and aggregate `tanf` to zero:

| PE result | SNAP benefit |
|---|---:|
| Report-pipeline baseline | $564.645345/month |
| `tn_ff = tanf = $0` | $673.545369/month |
| Axiom report value | $667.00/month |
| Remaining PE-minus-Axiom difference | $6.545369/month |

The counterfactual raises PolicyEngine's benefit by $108.90 and leaves only $6.55,
inside this report's $7 amount tolerance. The classified mismatch therefore
disappears when the asymmetric TANF amount is neutralized.

The general runner normalizes PolicyEngine's calendar-year result to a monthly
average, spanning the October federal-fiscal-year transition. A direct January
2026 evaluation gives `$558.699951` at baseline and `$667.599976` with TANF
neutralized, only $0.60 above Axiom. This explains the remaining exact-value
difference without implicating a utility rule.

### Minimal exact report repro

This read-only repro uses the report stack installed in `axiom-oracles`
(PolicyEngine 4.18.9 and PolicyEngine-US 1.752.2) and reconstructs the effective
comparison case without reloading the full population:

```bash
cd /Users/maxghenis/TheAxiomFoundation/axiom-oracles
PYTHONPATH=. .venv/bin/python - <<'PY'
from axiom_oracles.adapters.policyengine.runner import PolicyEngineRunner
from axiom_oracles.core.case import Case, Concepts, Entity

ages = [13, 10, 2, 30]
earned = [0, 0, 0, 19_679.58]
people = tuple(
    Entity(
        entity_id=str(i),
        kind="person",
        facts={
            Concepts.PERSON_AGE: age,
            Concepts.YEARLY_EARNED_INCOME: income,
            Concepts.HOUSEHOLD_RELATION: (
                "HeadOfHousehold" if i == 0
                else "Child" if age < 18
                else "Other"
            ),
        },
    )
    for i, (age, income) in enumerate(zip(ages, earned, strict=True))
)
case = Case(
    case_id="ecps-35254",
    period="2026-01",
    facts={Concepts.RENT_PAID: 0},
    entities=people,
    metadata={"scope": {"type": "census_county", "geoid": "47157"}},
)
variables = [
    "snap_normal_allotment",
    "snap_utility_allowance",
    "snap_standard_utility_allowance",
    "snap_limited_utility_allowance",
    "snap_individual_utility_allowance",
    "tanf",
    "snap_unearned_income",
    "snap_earned_income",
    "heating_cooling_expense",
    "count_distinct_utility_expenses",
]
result = PolicyEngineRunner().run_case(case, variables)
print(result.values)
print(result.errors)
PY
```

It returns SNAP `$564.6453450520834`, TANF and SNAP unearned income of about
`$4,344.42/year`, and zero for heating/cooling expense, distinct utility count,
SUA, LUA, IUA, and total utility allowance, with no errors.

### Execution/data flow

```text
PolicyEngine side
Populace household
  -> endogenous tn_ff
  -> aggregate tanf
  -> snap_unearned_income
  -> gross/net SNAP income
  -> lower SNAP allotment

Axiom side
Populace loader
  -> _PERSON_NON_WAGE_VARIABLES omits tanf_person
  -> no TANF_BENEFITS fact
  -> mapping aggregates missing TANF as $0
  -> lower gross/net SNAP income
  -> higher SNAP allotment
```

Relevant report-era bridge files at
`axiom-oracles@c51c7e055d8f0ca18ac2be3ace8166e38132e167`:

- `axiom_oracles/core/case.py` defines `Concepts.TANF_BENEFITS`.
- `axiom_oracles/data/ecps_input_mapping.yaml` derives
  `snap_total_monthly_unearned_income` from facts including `TANF_BENEFITS`.
- `axiom_oracles/populations/enhanced_cps.py::_PERSON_NON_WAGE_VARIABLES`
  lists the PolicyEngine person variables projected as non-wage facts but omits
  `Concepts.TANF_BENEFITS`.
- `axiom_oracles/adapters/policyengine/runner.py` reconstructs the right-hand
  synthetic household, supplies earnings and housing cost, and lets PolicyEngine
  compute benefit programs such as Families First endogenously.
- `programs/us-tn/snap/fy-2026.yaml` correctly includes
  `snap_total_monthly_unearned_income` in its SNAP income composition.

The current equivalents are
`axiom_oracles/data/populace_input_mapping.yaml` and
`axiom_oracles/populations/populace_us.py`; they retain the same TANF omission.

The certified H5's raw `public_assistance` values are zero for all four members of
household 35254. PolicyEngine's $362.03 is an **endogenous modeled benefit**, not an
observed population input. Therefore, blindly mapping raw `public_assistance` would
not repair parity.

### Controlling law

Pinned provision `us/regulation/7/273/9/b/2/i` expressly treats federally aided
public-assistance payments such as TANF as unearned income unless a specific
exclusion applies. No such exclusion was identified for this ordinary Families
First cash payment.

Pinned provision `us/regulation/7/273/10`, paragraph (e)(1)(i)(A), requires total
monthly unearned income to enter gross income. Paragraph (e)(2)(ii)(A) reduces the
maximum allotment by 30% of net monthly income. These are retained in:

```text
data/corpus/provisions/us/regulation/2026-07-15-title-7-part-273.jsonl
```

PolicyEngine is correct to count the Families First payment. Changing Tennessee
SNAP law to omit it would be wrong.

## Encode decision

### No change now

The smallest correct action is no behavior change pending source ingest.

1. **Do not add a zero-valued Tennessee hook.** Missing authority means “unknown,”
   not a lawful $0. A behaviorally inert placeholder also cannot supply meaningful
   before/after mutation evidence.
2. **Do not scope the old regulation.** Its values are stale, undated for current
   use, and would activate three overlapping hooks plus other obsolete tables.
3. **Do not invent historical dates.** FY2024 evidence establishes obsolescence but
   does not establish when the old amounts began or ended.
4. **Do not copy PolicyEngine's FY2026 amounts.** The assignment expressly requires
   retained authority, and none is present.
5. **Do not change SNAP income rules to match the oracle bridge omission.** Retained
   federal law requires TANF to be counted.

Because no encode changed, no companion test changed and no mutation test was
fabricated.

### Implementation after source ingest

Once a current, dated primary amount source is retained, a Tennessee implementation
should:

1. encode HCSUA, BUA/LUA, and telephone amounts with source-supported effective
   dates;
2. select exactly one applied allowance in priority order rather than summing
   overlapping standards;
3. add the selected allowance to the shelter-cost composition;
4. keep the existing manual eligibility predicates;
5. prove in companion tests that:
   - SUA wins when SUA and BUA facts overlap;
   - BUA applies only without SUA;
   - telephone applies only without SUA or BUA;
   - no qualifying facts produce $0;
   - shelter total equals base shelter plus exactly one allowance;
   - household-size boundaries match the source; and
6. capture mutation failures for the utility term, priority gates, and each sourced
   amount.

## Proposed dispositions

### `ecps-35254`

Proposed suite disposition: `bridge_artifact`.

> PolicyEngine endogenously computes about $362.0348/month of Tennessee Families
> First and counts it as SNAP unearned income. The Axiom mapping requests a
> `TANF_BENEFITS` fact, but the Populace loader emits no equivalent modeled TANF
> fact. Under retained 7 CFR 273.9(b)(2)(i) and 273.10(e), TANF must enter SNAP
> gross/net income and reduce the allotment. Retain the Tennessee SNAP encoding and
> treat the mismatch as expected until both engines receive consistently sourced
> TANF inputs. In the exact report stack, neutralizing `tn_ff` and `tanf` moves
> PolicyEngine to $673.545369, within the suite's $7 tolerance of Axiom's $667.

Suggested disposition evidence links:

```text
us/regulation/7/273/9/b/2/i
us/regulation/7/273/10 (e)(1)(i)(A), (e)(2)(ii)(A)
```

### Other target cases

The exact 1.752.2 and 1.767.3 traces identify Families First in 30 additional
cases:

```text
35266, 35304, 35320, 35324, 35347, 35590, 35596, 35643, 35647, 35661,
35696, 35708, 35789, 35835, 35911, 35974, 36024, 36061, 36069, 36071,
36102, 36129, 36188, 36247, 36258, 36303, 36346, 36403, 36407, 36436
```

They are bridge-artifact candidates, but this report does not blanket-disposition
them without an individual counterfactual. All 31 Families First cases have
positive Axiom-minus-PolicyEngine deltas, ranging from $8.46 to $374.73/month. The
remaining 17 cases have neither utility allowances nor Families First; they contain
12 positive and all 5 negative deltas and remain unexplained by this investigation.
None should be labeled a utility defect.

Recommended next disposition sequence:

1. fix or explicitly neutralize the TANF cross-program bridge;
2. rerun the suite with the declared PolicyEngine-US version;
3. disposition only residuals that survive that equal-input rerun; and
4. separately add current Tennessee utility coverage after authority ingest, then
   add utility-bearing targeted cases because the current ECPS target class contains
   none.

## Draft `axiom-oracles` issue

**Title:** Populace SNAP comparisons omit endogenous TANF benefits from Axiom facts

**Problem**

For Tennessee household `ecps-35254`, PolicyEngine computes Tennessee Families
First and includes it through `tanf` in SNAP unearned income. The generic Axiom
input mapping expects `TANF_BENEFITS`, but `PopulaceUsCaseLoader` does not project
`tanf_person`; the corresponding Axiom input is therefore zero. This causes the
comparison to give the two engines different cross-program inputs.

The raw H5 `public_assistance` field is also zero, so adding a raw-field mapping is
not equivalent to PolicyEngine's endogenous benefit.

**Evidence**

- Household 35254, PE 1.752.2 and 1.767.3: `tn_ff = tanf =
  snap_unearned_income =
  ~$362.0348/month`.
- SUA, LUA, IUA, total utility, housing cost, and excess shelter deduction are $0.
- The exact 1.752.2 zero-TANF counterfactual moves SNAP from $564.645345 to
  $673.545369, within the configured $7 tolerance of Axiom's $667.
- `populace_input_mapping.yaml` requests `TANF_BENEFITS`.
- `_PERSON_NON_WAGE_VARIABLES` omits TANF.
- Retained 7 CFR 273.9(b)(2)(i) requires TANF to be counted as unearned income.

**Expected behavior**

Comparison inputs should follow a declared equal-input policy for cross-program
benefits. Choose one and record its provenance:

1. compose an independently grounded Axiom Tennessee Families First module;
2. explicitly bridge the PolicyEngine-computed `tanf_person`/state component to
   Axiom and label it oracle-derived; or
3. neutralize endogenous TANF consistently on both sides for isolated SNAP tests.

Do not silently map raw `public_assistance`, and do not alter SNAP law to omit TANF.

**Acceptance criteria**

- The chosen cross-program policy is explicit in suite provenance.
- A focused household test proves equal TANF inputs reach both engines.
- A no-TANF test remains unchanged.
- Tennessee SNAP ECPS is regenerated under one declared PolicyEngine-US version.
- `ecps-35254` is removed from unexplained residuals or has a source-linked expected
  disposition.

## Draft corpus ingest prerequisite

**Title:** Ingest current Tennessee SNAP SUA/BUA/telephone allowance amounts

Retain a primary, dated source for FY2026 Tennessee utility amounts, preferably:

1. the current Tennessee DHS “Standard Utility Allowance,” “Family Assistance
   Standards Desk Guide,” or “Utility Allowance Chart” referenced by Policy 24.18;
   or
2. the authoritative FNS FY2026 state SUA table.

The ingest must preserve effective dates, household-size rows, HCSUA/SUA, LUA/BUA,
telephone/IUA amounts, and state methodology/options. The retained FY2024 FNS table
is insufficient for 2026.

## Verification

No encode changed. The following existing companion suites passed with the
available local fallback rules engine:

| Test file | Cases | Result |
|---|---:|---|
| `us-tn/regulations/1240-01/04/27/block-1.test.yaml` | 4 | Pass |
| `us-tn/policies/dhs/snap/24-18/page-5.test.yaml` | 6 | Pass |
| `us-tn/policies/dhs/snap/24-18/page-6.test.yaml` | 4 | Pass |
| `us-tn/policies/dhs/snap/24-18/page-7.test.yaml` | 4 | Pass |
| **Total** | **18** | **Pass** |

Command form:

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Users/maxghenis/TheAxiomFoundation/_worktrees/axiom-encode-782-pinned/src \
/Users/maxghenis/axiom-encode/.venv/bin/python -m axiom_encode.cli test \
  --root /Users/maxghenis/TheAxiomFoundation/wt-snap-tn \
  --axiom-rules-engine-path /Users/maxghenis/TheAxiomFoundation/axiom-rules-engine \
  <test-file>
```

Passing tests establish fidelity to their retained source modules; in particular,
the old regulation test does not make its amounts legally current.

## Tool and environment limitations

- The user-specified test engine path
  `/Users/maxghenis/TheAxiomFoundation/axiom-rules` does not exist and produced a
  `FileNotFoundError`. The fallback
  `/Users/maxghenis/TheAxiomFoundation/axiom-rules-engine` is at
  `aa1ff025906c7216c053e9b9c4097cc0dfef1811`, not the pinned engine ref, and has
  pre-existing local changes. The 18 passing cases are therefore supporting, not
  release-grade pinned verification.
- The worktree was not registered in GitNexus. A temporary analysis was attempted,
  but registration failed because the sandbox denied writing
  `/Users/maxghenis/.gitnexus/registry.json`. The worktree graph therefore remained
  unavailable; direct source tracing and the globally indexed PolicyEngine graph
  were used instead.
- A scratch `uv` install of exact PolicyEngine-US 1.767.3 could not write to the
  host uv cache under the sandbox. The already cached exact 1.767.3 wheel/source was
  used.
- The 1.767.3 behavior audit used the same PolicyEngine 4.18.9 wrapper as the
  report. That wrapper warns that its bundle manifest pins PE-US 1.752.2, while
  also confirming that calculations proceed with installed PE-US 1.767.3. Both
  versions produced the same reported target-case results.
- One redundant full-population single-household rerun was manually interrupted
  after more than 90 seconds during dependency expansion. The completed exact
  1.752.2 and 1.767.3 48-household batches supply the reported component results.

No push, GitHub write, manifest signing, workflow edit, toolchain edit, or
CODEOWNERS edit was performed.

## Local commits before this report

| Commit | Purpose |
|---|---|
| `0891e249b` | Start and commit `PROGRESS.md` |
| `ca0dadf5a` | Record residual and authority evidence |
| `36468b4cf` | Record root-cause and no-change decision |
| `069da9aa1` | Correct the pipeline identity and exact-version batch evidence |
| `4bfaf0284` | Record the exact TANF counterfactual |

The commit containing this report and the final `PROGRESS.md` state is reported in
the final handoff message.
