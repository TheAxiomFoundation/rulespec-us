# Federal elderly/minimum-benefit SNAP residual report

## Result

No federal 7 CFR 273.9 or 273.10 encode change is warranted.

The retained regulation audit resolves all three proposed hypotheses. The
current federal encodes fully implement the gross-test exemption and rounded
minimum, and implement the medical-deduction threshold arithmetic while
deliberately deferring member-level expense entitlement and classification:

1. an elderly/disabled household is exempt from the gross-income test and must
   meet the net-income test;
2. an eligible one- or two-person household receives the rounded minimum
   benefit outside its initial month; and
3. when upstream facts establish qualifying expenses, the portion above `$35`
   is deducted.

None is a federal formula defect causing Axiom's `$0` results in this class.
The current Case-to-PolicyEngine bridge shows that PolicyEngine finds 84 of the
85 strict cases categorically eligible; 69 depend exclusively on that path.
The Axiom programs already OR their state categorical paths with ordinary
federal income eligibility, but the generic case projection does not provide
equivalent state categorical facts. This identifies an unresolved state
categorical/input-projection discrepancy, not a federal encoding gap. The 69
rows remain candidates rather than confirmed bridge dispositions until their
categorical status is validated against retained state law and observed facts.

A federal candidate patch was tested and rejected because it introduced eight
mandatory categorical facts into every consumer of 7 CFR 273.9 and broke
downstream state suites. It was reverted. The final federal encodes and their
companions are byte-for-byte unchanged relative to the cached base.

## Class census

### Strict class

The supplied class definition is confirmed. A strict match is:

- one person;
- sole member age 60 or older;
- Axiom benefit `$0` and ineligible;
- report PolicyEngine benefit exactly `$23.973597208658855` and eligible; and
- the two corresponding benefit and eligibility mismatches, without an engine
  error.

| State | Strict cases | Zero earned | Positive earned | Report weight |
| --- | ---: | ---: | ---: | ---: |
| AL | 0 | 0 | 0 | 0.000 |
| MA | 42 | 29 | 13 | 56,761.582 |
| NC | 0 | 0 | 0 | 0.000 |
| SC | 43 | 36 | 7 | 89,258.105 |
| TN | 0 | 0 | 0 | 0.000 |
| **Total** | **85** | **65** | **20** | **146,019.687** |

This class therefore consists only of one-person elderly households in
Massachusetts and South Carolina. The AL, NC, and TN counts are genuinely zero.

### Broader exact-minimum residual universe by household shape

For context, the five reports contain 154 one- or two-person PE-only
eligibility residuals with the same exact reported benefit. "Elderly" means at
least one member is age 60 or older.

| State | 1p elderly | 1p nonelderly | 2p elderly | 2p nonelderly | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| AL | 0 | 0 | 1 | 0 | 1 |
| MA | 42 | 26 | 11 | 12 | 91 |
| NC | 0 | 0 | 0 | 0 | 0 |
| SC | 43 | 0 | 17 | 2 | 62 |
| TN | 0 | 0 | 0 | 0 | 0 |
| **Total** | **85** | **26** | **29** | **14** | **154** |

That broader count is only a descriptive ceiling. The causal estimates below
apply to the 85 strict cases.

## Controlling retained text

The worktree pins the corpus at
`bf97b17baebfdf12601f7c23697524bf5adcdaed`. The retained Part 273 XML is:

`data/corpus/sources/us/regulation/2026-07-15-title-7-part-273/ecfr/title-7-part-273.xml`

inside `/Users/maxghenis/TheAxiomFoundation/axiom-corpus`. Its SHA-256 is
`92d5f3baba66e0f7f8ba2a2887a2a664166fcc0deb275b1b143a7ca23a4114a6`.

The exact controlling paths and conclusions are:

- `us/regulation/7/273/9/a`: households containing an elderly or
  disabled member meet the net standard; households without such a member meet
  both gross and net standards; households categorically eligible under
  273.2(j)(2) or (j)(4) meet neither income test. The elderly gross exemption
  is in paragraph (a)'s lead text, not paragraph (a)(2). Paragraph (a)(2)
  defines the net standard.
- `us/regulation/7/273/9/d/3`: the deduction is the portion of allowable
  medical expenses over `$35` per month, excluding special diets, incurred by
  an elderly or disabled member. A spouse or other person receiving benefits
  only as a dependent of an SSI/disability recipient does not independently
  qualify; a person receiving emergency SSI on presumptive eligibility does.
- `us/regulation/7/273/10`, textual paragraph (e)(2)(ii)(C): except in an
  initial month, every eligible one- or two-person household receives the
  minimum monthly allotment. The minimum is 8 percent of the one-person
  maximum, rounded to the nearest whole dollar. The retained corpus has a
  section record for 273.10 but no deeper paragraph anchor, so the paragraph
  designation is textual rather than an invented citation path.

No conclusion below substitutes report metadata or PolicyEngine behavior for
these retained legal rules.

## Hypothesis findings

| Hypothesis | Law and encode finding | Causal verdict |
| --- | --- | --- |
| Elderly households incorrectly face the gross test | `us/regulation/7/273/9/a` supplies the exemption. `us/regulations/7-cfr/273/9.yaml` computes `elderly_or_disabled OR gross <= limit`; its companion has `elderly_or_disabled_household_is_gross_income_exempt`. PolicyEngine-US 1.767.3 uses the same exemption. Both named cases pass the gross gate. | **Not causal.** |
| The one-/two-person minimum is absent | `us/regulation/7/273/10`, textual paragraph (e)(2)(ii)(C), controls. `us/regulations/7-cfr/273/10.yaml` computes `floor(8% * one-person maximum + 0.5)` and applies it outside an initial month to households of size at most two. The composed program separately gates benefit issuance on eligibility. The companion proves `$6` before minimum becomes `$24`. | **Not causal to eligibility or Axiom's zero.** The Axiom minimum is correct once the eligibility gate passes. |
| The elderly/disabled medical deduction is absent | `us/regulation/7/273/9/d/3` controls. `us/regulations/7-cfr/273/10.yaml` subtracts `max(0, total medical - 35)` when the household is entitled. The module explicitly defers classification and verification of deductible expenses under paragraph (d), which is necessary because not every expense in an elderly household qualifies. | **Not causal in this class.** A counterfactual removes the only ordinary-path case's medical deduction without changing eligibility. |

### Named cases

The exact current PolicyEngine-US 1.767.3 adapter trace gives:

- MA `ecps-1984`: categorical-only; gross test true, net test false,
  `$23.973597208658855`. It has an average `$167.90` monthly medical deduction,
  but still fails the net test. Categorical eligibility is decisive.
- SC `ecps-28671`: categorical-only; gross test true, net test false,
  `$23.973597208658855`. It has no reconstructed medical deduction.
  Categorical eligibility is again decisive.

The case loader does not forward source `other_medical_expenses` when it reduces
the Populace H5 row to generic Case facts. That explains why a direct-H5 trace
and the actual adapter-path trace can disagree about medical deductions. The
adapter-path result is the relevant one for these reports.

MA `ecps-3128` is the sole strict case eligible only through ordinary income
tests. Setting its projected health premium to a nominal `$1` per year removes
its medical deduction; it still passes gross and net tests and remains
PolicyEngine-eligible. Medical projection therefore clears zero eligibility
residuals in this class.

## Leading nonfederal discrepancy

The reports were generated on 2026-07-06 with `policyengine==4.18.9`,
PolicyEngine-US 1.752.2, and rulespec commit
`a0bcc5a39fa57f02f0c75c9d4a9e6bfd8670c58c`. I reran the same
`PopulaceUsCaseLoader` to `PolicyEngineRunner` path with the exact cached
PolicyEngine-US 1.767.3 source:

| Current adapter-path status | AL | MA | NC | SC | TN | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Categorical only | 0 | 27 | 0 | 42 | 0 | 69 |
| Categorical and ordinary | 0 | 14 | 0 | 1 | 0 | 15 |
| Ordinary only | 0 | 1 | 0 | 0 | 0 | 1 |
| Ineligible | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **0** | **42** | **0** | **43** | **0** | **85** |

All 85 remain PolicyEngine-eligible. Eighty-four still receive exactly
`$23.973597208658855`; MA `ecps-2303` now receives
`$100.1699930826823`.

PolicyEngine's `is_snap_eligible` treats categorical eligibility as an
alternative to the gross/net/asset route. Its 1.767.3 source is
`policyengine_us/variables/gov/usda/snap/eligibility/is_snap_eligible.py`,
lines 16-35. Its categorical calculation is in
`meets_snap_categorical_eligibility.py`, lines 12-17.

The Axiom program compositions already express the same architecture:

- `programs/us-ma/snap/fy-2026.yaml`, lines 231-240, ORs
  `snap_household_is_categorically_eligible` with
  `snap_standard_income_eligible`.
- `programs/us-sc/snap/fy-2026.yaml`, lines 425-434, ORs
  `categorically_eligible_household` with
  `snap_standard_income_eligible`.

The asymmetry is in input projection:

- The Massachusetts program consumes
  `snap_household_is_categorically_eligible`, but there is no state rule
  producing that exact output in this repository.
- The oracle's `populace_input_mapping.yaml`, lines 392-420, maps only limited
  Massachusetts SSI/TANF source facts; it does not project PolicyEngine's
  categorical result into the state gate.
- South Carolina's categorical rule requires TANF/SSI or expanded-category
  service and nonfinancial facts. The generic ECPS Case does not carry
  equivalent observed service facts.
- The generic projector documents and implements a type-zero fallback for
  unmapped inputs in
  `axiom_oracles/adapters/axiom/generic_inputs.py`, lines 320-335 and 408-432.

Thus PolicyEngine derives state categorical eligibility from its own modeled
program variables while Axiom receives false/zero for unavailable legal facts.
This is a concrete projection asymmetry and the leading explanation for the
69 categorical-only candidates. It is not yet proof that PolicyEngine's state
categorical result is legally correct for every row or that one projection
change clears all other Axiom gates. Changing the federal gross, minimum, or
medical formulas cannot repair the asymmetry.

## Federal fix and mutation evidence

### Candidate tested

I tested importing the existing federal 273.2(j) categorical rule into
`273/9.yaml` and OR-ing regular categorical eligibility into
`snap_standard_income_eligible`. A new companion mutation set both ordinary
income tests to fail while making the regular categorical facts true.

Evidence:

1. Before the candidate graph change, the new case failed because
   `snap_regular_categorically_eligible` was not an executable output of the
   273.9 graph.
2. After the import and formula change, all 5 candidate 273.9 companion cases
   passed.
3. Downstream mutation testing then failed 4 of 6 California benefit cases:
   importing 273.2(j) made eight new categorical factual inputs mandatory for
   every consumer, beginning with the PA/SSI receipt/authorization fact.

### Why it was rejected

The state program compositions already own the categorical/ordinary OR. Moving
the categorical rule into the federal *standard-income* output would add
mandatory unobserved facts throughout the dependency graph and duplicate that
composition layer. Supplying false defaults inside the legal encode would
silently decide eligibility without evidence. State companion edits are also
outside this worker's scope.

The candidate and companion were therefore reverted. This is negative mutation
evidence: it rules out a superficially plausible federal patch and preserves
the correct module boundary.

## Clearance estimate

Because no federal defect exists, the final federal patch clears zero cases:

| State | Strict cases | Cleared by federal 273.9/273.10 fix | Categorical-only projection candidates | Category + ordinary overlap | Other projection/gate trace |
| --- | ---: | ---: | ---: | ---: | ---: |
| AL | 0 | 0 | 0 | 0 | 0 |
| MA | 42 | 0 | 27 | 14 | 1 |
| NC | 0 | 0 | 0 | 0 | 0 |
| SC | 43 | 0 | 42 | 1 | 0 |
| TN | 0 | 0 | 0 | 0 | 0 |
| **Total** | **85** | **0** | **69** | **15** | **1** |

The 69 categorical-only cases are the conservative direct candidates for an
out-of-scope, source-backed categorical projection fix. The 15 overlap cases
would gain the same alternative path but also need their ordinary-path
projection differences understood. MA `ecps-3128` requires a separate
income/projection trace. A medical-input-only change is expected to clear zero
eligibility cases in this strict class.

## PolicyEngine and bridge defects

### Draft PolicyEngine-US issue

**Title:** Round SNAP minimum allotment to the nearest whole dollar under
7 CFR 273.10(e)(2)(ii)(C)

**Body:**

PolicyEngine-US 1.767.3 multiplies the minimum-benefit rate by the relevant
one-person maximum without rounding in
`variables/gov/usda/snap/snap_min_allotment.py`, lines 12-26. The retained
federal rule at `us/regulation/7/273/10`, paragraph (e)(2)(ii)(C), requires
rounding to the nearest whole dollar.

Minimal live reproduction:

```python
from policyengine_us import Simulation

situation = {
    "people": {
        "person": {
            "age": {"2026": 80},
            "social_security": {"2026": 20_000},
        }
    },
    "families": {"family": {"members": ["person"]}},
    "marital_units": {"marital_unit": {"members": ["person"]}},
    "tax_units": {"tax_unit": {"members": ["person"]}},
    "spm_units": {"spm_unit": {"members": ["person"]}},
    "households": {
        "household": {
            "members": ["person"],
            "state_code": {"2026": "MA"},
        }
    },
}
simulation = Simulation(situation=situation)
print(float(simulation.calculate("snap_min_allotment", "2026-01")[0]))
```

Actual: `23.84000015258789`.

Expected: `$24`, because 8 percent of the January 2026 one-person maximum
`$298` is `$23.84`, rounded to the nearest whole dollar.

Suggested change: apply nearest-whole-dollar rounding to the federal calculated
minimum before state overrides, and add monthly tests on both sides of an
October COLA boundary.

**Proposed suite disposition:** `upstream_engine_gap`, source
`us/regulation/7/273/10`, paragraph (e)(2)(ii)(C). Axiom's `$24` is the legal
truth; do not change it to `$23.84`.

### Draft axiom-oracles issue

**Title:** Do not calendar-average month-defined PolicyEngine output for a
requested month

**Body:**

For a request such as `2026-01`,
`PolicyEngineRunner._normalize_value_for_requested_period` divides the
calendar-year sum of a month-defined variable by 12. See
`axiom_oracles/adapters/policyengine/runner.py`, lines 850-868. This returns a
calendar average, not January's value.

With PolicyEngine-US 1.767.3:

- `snap_min_allotment` for `2026-01` is `23.84000015258789`;
- the annual value is `287.68316650390625`; and
- the bridge returns `287.68316650390625 / 12 =
  23.973597208658855`.

The adapter should select or calculate the requested month instead of averaging
all calendar months, especially when an October COLA changes a monthly
parameter.

**Proposed suite disposition:** `bridge_artifact`, with the same
`us/regulation/7/273/10`, paragraph (e)(2)(ii)(C), source for the expected
January minimum. After fixing PolicyEngine's rounding, the legally correct
January comparison is `$24`.

### Eligibility dispositions still needed

- 69 categorical-only rows: unresolved state categorical/input-projection
  discrepancy. Use `bridge_artifact` only after validating categorical status
  against retained state law and observed facts.
- 15 categorical/ordinary overlap rows: keep open until the ordinary input
  path is traced; a categorical projection would supply an alternative path
  only if state-law status is validated.
- MA `ecps-3128`: keep open as a separate projection/gate residual.
- Do not disposition the `$23.97` amount as an Axiom encoding gap. It combines
  a PolicyEngine rounding defect with a bridge period-normalization artifact.

No GitHub issue, comment, or push was made.

## Verification

The final unchanged files pass the required command:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Users/maxghenis/TheAxiomFoundation/_worktrees/axiom-encode-782-pinned/src \
/Users/maxghenis/axiom-encode/.venv/bin/python -m axiom_encode.cli test \
  --root /Users/maxghenis/TheAxiomFoundation/wt-snap-fed \
  --axiom-rules-engine-path /Users/maxghenis/axiom-rules \
  <test-file>
```

```text
us/regulations/7-cfr/273/9.test.yaml                         4/4 passed
us/regulations/7-cfr/273/10.test.yaml                        5/5 passed
us-ca/policies/cdss/snap/fy-2026-benefit-calculation.test.yaml 6/6 passed
```

The representative California suite is included because it is the downstream
suite that exposed the candidate categorical import's mandatory-input
regression.

## Complete strict case list

**Massachusetts (42):**

`ecps-1984`, `ecps-1985`, `ecps-2008`, `ecps-2091`, `ecps-2106`,
`ecps-2221`, `ecps-2227`, `ecps-2251`, `ecps-2303`, `ecps-2305`,
`ecps-2316`, `ecps-2328`, `ecps-2343`, `ecps-2461`, `ecps-2577`,
`ecps-2615`, `ecps-2620`, `ecps-2624`, `ecps-2645`, `ecps-2689`,
`ecps-2714`, `ecps-2733`, `ecps-2846`, `ecps-2877`, `ecps-2880`,
`ecps-2942`, `ecps-2947`, `ecps-3010`, `ecps-3027`, `ecps-3033`,
`ecps-3036`, `ecps-3090`, `ecps-3107`, `ecps-3121`, `ecps-3128`,
`ecps-3239`, `ecps-3241`, `ecps-3245`, `ecps-3279`, `ecps-3338`,
`ecps-3359`, `ecps-3369`.

**South Carolina (43):**

`ecps-28671`, `ecps-28714`, `ecps-28745`, `ecps-28748`, `ecps-28756`,
`ecps-28757`, `ecps-28764`, `ecps-28798`, `ecps-28815`, `ecps-28833`,
`ecps-28836`, `ecps-28837`, `ecps-28852`, `ecps-28903`, `ecps-28909`,
`ecps-28943`, `ecps-28961`, `ecps-29026`, `ecps-29055`, `ecps-29067`,
`ecps-29074`, `ecps-29107`, `ecps-29147`, `ecps-29249`, `ecps-29255`,
`ecps-29267`, `ecps-29330`, `ecps-29346`, `ecps-29347`, `ecps-29354`,
`ecps-29365`, `ecps-29370`, `ecps-29404`, `ecps-29406`, `ecps-29429`,
`ecps-29502`, `ecps-29514`, `ecps-29526`, `ecps-29534`, `ecps-29561`,
`ecps-29611`, `ecps-29640`, `ecps-29695`.

AL, NC, and TN have no strict-class IDs.

## Environment and failures disclosed

- A fresh `git fetch` could not resolve `github.com` in the sandbox. Work used
  the locally cached `origin/main` and the corpus commit pinned by the
  worktree.
- Creating a new exact-version scratch environment with `uv` was blocked by
  sandbox access to its cache. The exact already-cached PolicyEngine-US
  1.767.3 source and compatible PolicyEngine Core 3.30 archive were injected
  into the report environment and their resolved version and source were
  checked before use.
- One direct temporary rules-engine compilation outside the repository could
  not resolve relative imports. All legal companion verification was rerun
  successfully through the required `axiom_encode.cli test` command with the
  worktree root.
- An initial census formatting one-liner used a Bash-only uppercase expansion
  under zsh and failed before reading results; the query was rerun with jq's
  `ascii_upcase` and produced the table and ID list above.

No state file, toolchain file, workflow, CODEOWNERS file, manifest, or external
repository was modified. Nothing was pushed or posted.
