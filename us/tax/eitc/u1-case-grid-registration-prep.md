# EITC case-grid registration preparation

Date: 2026-07-27

## Prepared state

The RuleSpec side of `us-eitc-grid` is staged. All 21 diagnostic case IDs now
exist in `us/statutes/26/32.test.yaml`, use the exact 2026 tax-year period,
and assert `us:statutes/26/32#eitc`. The repository-pinned rules engine passed
all 25 section 32 companion cases (the four pre-existing cases plus the 21
grid-contract cases).

No comparison report, dashboard JSON, dashboard manifest entry, affected-map
entry, or conformance artifact was generated or changed.

Runnable registration belongs in the separate `axiom-oracles` repository.
That checkout is read-only for this task. More importantly, its federal runner
fail-closes unless the configured `rulespec-us` checkout is clean and its HEAD
and tree exactly match the pinned canonical upstream revision. The repaired
fixture is not yet in canonical `rulespec-us` main, so a truthful manifest
cannot fill `rulespec_upstream_sha` or `rulespec_upstream_tree` yet.

## Committed case contract

| Case ID | Children | Earned income | AGI | Investment income | Age branch | Axiom expected |
|---|---:|---:|---:|---:|---:|---:|
| `c0_phase_in_5000` | 0 | 5,000 | 5,000 | 0 | 35 | 382.5 |
| `c1_phase_in_5000` | 1 | 5,000 | 5,000 | 0 | 35 | 1,700 |
| `c2_phase_in_5000` | 2 | 5,000 | 5,000 | 0 | 35 | 2,000 |
| `c3_phase_in_5000` | 3 | 5,000 | 5,000 | 0 | 35 | 2,250 |
| `c4_phase_in_5000` | 4 | 5,000 | 5,000 | 0 | 35 | 2,250 |
| `c1_earned_income_amount_13020` | 1 | 13,020 | 13,020 | 0 | 35 | 4,427 |
| `c1_after_earned_income_amount_13021` | 1 | 13,021 | 13,021 | 0 | 35 | 4,427 |
| `c3_earned_income_amount_18290` | 3 | 18,290 | 18,290 | 0 | 35 | 8,231 |
| `c3_after_earned_income_amount_18292` | 3 | 18,292 | 18,292 | 0 | 35 | 8,231 |
| `c1_plateau_20000` | 1 | 20,000 | 20,000 | 0 | 35 | 4,427 |
| `c1_phase_out_start_23890` | 1 | 23,890 | 23,890 | 0 | 35 | 4,427 |
| `c1_phase_out_28890` | 1 | 28,890 | 28,890 | 0 | 35 | 3,628 |
| `c1_agi_driven_earned20000_agi28890` | 1 | 20,000 | 28,890 | 0 | 35 | 3,628 |
| `c3_plateau_20000` | 3 | 20,000 | 20,000 | 0 | 35 | 8,231 |
| `c3_phase_out_start_23890` | 3 | 23,890 | 23,890 | 0 | 35 | 8,231 |
| `c0_age_24` | 0 | 5,000 | 5,000 | 0 | 24 | 0 |
| `c0_age_25` | 0 | 5,000 | 5,000 | 0 | 25 | 382.5 |
| `c0_age_64` | 0 | 5,000 | 5,000 | 0 | 64 | 382.5 |
| `c0_age_65` | 0 | 5,000 | 5,000 | 0 | 65 | 0 |
| `c1_investment_12200` | 1 | 20,000 | 20,000 | 12,200 | 35 | 4,427 |
| `c1_investment_12201` | 1 | 20,000 | 20,000 | 12,201 | 35 | 0 |

The age column is an oracle-generator case dimension. The Axiom fixture still
has to supply the unrooted TaxUnit conclusion
`childless_taxpayer_or_spouse_age_eligible_for_eitc`; its Person age rule is
not connected to final `eitc`. Registration must disclose that bridge and
must not describe this suite as end-to-end provision evidence.

## Oracle registry manifest

`axiom-oracles/comparisons/us-additional-medicare-grid.yaml` is auto-discovered;
there is no hand-maintained runner registry or workflow list. The analogous
file to add is `comparisons/us-eitc-grid.yaml`:

```yaml
name: us-eitc-grid
title: Federal Earned Income Tax Credit — Axiom vs PolicyEngine
description: >-
  Compares 21 synthetic tax-year-2026 EITC cases over an explicitly bridged
  RuleSpec frontier. Childless age and other derived frontier facts are not
  end-to-end provision evidence.

runner:
  type: federal-tax-liability-grid
  parameters:
    policy: eitc
    period: "2026"
    concept: us:statutes/26/32#eitc
    python: "3.13"
    policyengine_version: "4.18.9"
    policyengine_us_version: "1.767.3"
    policyengine_core_version: "3.30.3"
    rulespec_remote: https://github.com/TheAxiomFoundation/rulespec-us.git
    rulespec_roots:
      - /private/tmp/oracle-rerun/rulespec-us
    rulespec_upstream_sha: <RULESPEC_MAIN_SHA_CONTAINING_THE_21_CASES>
    rulespec_upstream_tree: <TREE_OF_THAT_EXACT_MAIN_COMMIT>

artifacts:
  report_basename: axiom-policyengine-us-eitc-grid

dashboard:
  filename: axiom-policyengine-us-eitc-grid.json
  suite: us-eitc-grid
```

The PolicyEngine pins above intentionally mirror the reviewed Additional
Medicare federal-grid stack. They are registration pins, not a claim that
those packages are the newest releases. The eventual run must use exactly the
manifest pins or update the manifest, tests, and provenance together.

## Generator and test changes

`scripts/run_comparison.py` already dispatches
`runner.type: federal-tax-liability-grid` to
`scripts/generate_federal_tax_liability.py`; neither `RUNNERS` nor
`.github/workflows/comparisons.yml` needs a new entry. The generator needs:

1. `_EITC_CASES`, with the 21 IDs and neutral dimensions in the table above.
2. `_eitc_situation(case)`, supplying the same earned income, AGI, investment
   income, filing status, ages, child people, SSN types, take-up/filing flags,
   and all other explicit PolicyEngine facts used by the diagnostic.
3. `_validate_eitc_fixture(case, actual)`, fail-closing on the exact RuleSpec
   earned-income component, AGI, investment-income bridge, child relation
   cardinality/facts, and childless age bridge. It must reject a silent
   default or a case outside the reviewed neutral domain.
4. This `PolicyConfig` entry:

```python
"eitc": PolicyConfig(
    key="eitc",
    suite="us-eitc-grid",
    title="Earned Income Tax Credit",
    axiom_module_ref="us:statutes/26/32",
    fixture_path=Path("us/statutes/26/32.test.yaml"),
    axiom_output="us:statutes/26/32#eitc",
    pe_output_variables=("eitc",),
    pe_boundary=(
        "TaxUnit section 32 amount over an explicitly bridged frontier; "
        "childless age cases manually bind the disconnected TaxUnit age "
        "conclusion and are not end-to-end provision evidence"
    ),
    cases=_EITC_CASES,
    pe_situation=_eitc_situation,
    fixture_input_validator=_validate_eitc_fixture,
    pe_diagnostic_variables=("eitc_phased_in", "eitc_maximum"),
),
```

The existing `_axiom_values` loader then enforces all case IDs, the exact
2026 period, the exact Axiom output, unique fixture names, and the custom
same-input validator. It reads reviewed expected fixture values; it does not
execute RuleSpec itself. The pinned RuleSpec companion run is therefore a
separate required gate.

`tests/test_federal_tax_liability_generator.py` must update the exact policy
set/config count, assert all 21 IDs, verify the EITC PolicyEngine binding and
diagnostics, exercise `_eitc_situation` and `_validate_eitc_fixture` including
fail-closed mutations, and assert a 21-row raw report. The shared federal
rulespec SHA/tree constants must be updated coherently if that test continues
to require every federal suite to use one canonical pin.

After the manifest lands, run
`scripts/generate_affected_map.py`; do not hand-edit its output. Its generated
entry should resolve to:

```json
{
  "suite": "us-eitc-grid",
  "name": "us-eitc-grid",
  "report": "axiom-policyengine-us-eitc-grid.json",
  "repos": ["TheAxiomFoundation/rulespec-us"],
  "source": "comparisons/us-eitc-grid.yaml"
}
```

## Boundary dispositions

The two raw differences must remain visible at the $0.01 absolute tolerance.
`classification: upstream_oracle_defect` in the adjudication note is
descriptive, not a valid oracle disposition enum. The staged
`dispositions/us-eitc-grid.yaml` must use `upstream_engine_gap`:

```yaml
schema: axiom_oracles.dispositions.v1
suite: us-eitc-grid
updated: "2026-07-27"
entries:
  - id: eitc-one-child-published-earned-income-boundary
    concept: us:statutes/26/32#eitc
    case_id: c1_earned_income_amount_13020
    kind: amount_difference
    disposition: upstream_engine_gap
    evidence:
      mechanism: >-
        Rev. Proc. 2025-32 section 4.06(1) says the $4,427 one-child
        maximum is allowed at or above the $13,020 earned-income amount.
        PolicyEngine computes the continuous product instead, leaving this
        exact endpoint $0.20 below the published whole-dollar maximum.
      arithmetic:
        - expression: "13020 * 0.34"
          equals: 4426.8
        - expression: "4427 - 4426.8"
          equals: 0.2
      sources:
        - "https://uscode.house.gov/view.xhtml?edition=prelim&f=treesort&jumpTo=true&num=0&req=%28title%3A26+section%3A32+edition%3Aprelim%29+OR+%28granuleid%3AUSC-prelim-title26-section32%29"
        - "https://www.irs.gov/pub/irs-drop/rp-25-32.pdf"
    expires_on_source_change: true
    pinned:
      left: 4427
      right: 4426.7998046875

  - id: eitc-three-child-published-earned-income-boundary
    concept: us:statutes/26/32#eitc
    case_id: c3_earned_income_amount_18290
    kind: amount_difference
    disposition: upstream_engine_gap
    evidence:
      mechanism: >-
        Rev. Proc. 2025-32 section 4.06(1) says the $8,231
        three-or-more-child maximum is allowed at or above the $18,290
        earned-income amount. PolicyEngine computes the continuous product
        instead, leaving this exact endpoint $0.50 below the published
        whole-dollar maximum.
      arithmetic:
        - expression: "18290 * 0.45"
          equals: 8230.5
        - expression: "8231 - 8230.5"
          equals: 0.5
      sources:
        - "https://uscode.house.gov/view.xhtml?edition=prelim&f=treesort&jumpTo=true&num=0&req=%28title%3A26+section%3A32+edition%3Aprelim%29+OR+%28granuleid%3AUSC-prelim-title26-section32%29"
        - "https://www.irs.gov/pub/irs-drop/rp-25-32.pdf"
    expires_on_source_change: true
    pinned:
      left: 8231
      right: 8230.5
```

The schema requires one entry per case when `pinned` is present; selector-wide
mapping pins are invalid. The two-entry template above matches that contract.

## Report and provenance contract

The generator first emits `axiom.comparison_report.v2`; dashboard publication
merges dispositions and stamps `axiom.comparison_report.v2.1`. Required
top-level fields are:

| Field | EITC value/shape |
|---|---|
| `suite` | `us-eitc-grid` |
| `concept` | `us:statutes/26/32#eitc` |
| `population` | `case-grid` |
| `validation_year` | `2026` |
| `engines` | `{left: axiom, right: policyengine}` |
| `engine_bindings.axiom` | fixture, module, and exact output above |
| `engine_bindings.policyengine` | output `eitc`, diagnostic outputs, and bridge boundary |
| `tolerance` | `{absolute: 0.01, relative: 0.0}` |
| `case_count` | `21` |
| result collections | `concepts`, `aggregates`, `summary`, `mismatches`, and `cases` |

Each case contains `case_id`, `concept`, `filing_status`, neutral `inputs`,
expanded `axiom_fixture_inputs`, `axiom`, `policyengine`,
`policyengine_components`, `difference`, and `match`.

`population: case-grid` is not a provenance run kind. Provenance is stamped by
`scripts/run_comparison.py` and must have this shape for a local staged run:

```yaml
schema: axiom_oracles.provenance.v1
generated_at: <UTC_TIMESTAMP_WITH_Z>
generated_by: scripts/run_comparison.py::us-eitc-grid
run_kind: manual
rulespecs:
  - repo: TheAxiomFoundation/rulespec-us
    sha: <SAME_VERIFIED_SHA_AS_THE_MANIFEST>
engine: {}
oracle:
  name: policyengine
  policyengine_package: policyengine==4.18.9
  policyengine_us: 1.767.3
  policyengine_core: 3.30.3
```

Valid `run_kind` values are `weekly`, `pr-triggered`, `affected-rerun`, and
`manual`. A case grid has no dataset block.

## What remains after the launch freeze

1. Merge these RuleSpec fixture changes to canonical `rulespec-us` main.
2. Resolve that exact main commit and tree; put them in the manifest and the
   federal registry tests. Do not use this branch SHA as an “upstream” pin.
3. In `axiom-oracles`, add the manifest, generator cases/situation/validator
   and config, tests, and the validated two-case disposition.
4. Generate and commit the affected map.
5. Run the oracle tests and the pinned 25-case RuleSpec companion gate.
6. Only after the freeze, run
   `scripts/run_comparison.py us-eitc-grid --summary`. The dated raw report
   remains under ignored `reports/`; dashboard publication creates
   `dashboard/public/data/axiom-policyengine-us-eitc-grid.json` and updates
   `dashboard/public/data/manifest.json`, freshness, and overview artifacts.

Keep the current EITC conformance row on `fiit-ecps`. This bridged synthetic
grid is useful arithmetic evidence but is not a replacement certificate.
Repointing conformance would also require a stamped execution attestation (or
a waiver) and regenerated conformance detail, scoreboard, and history files.
