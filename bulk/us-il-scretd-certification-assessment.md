# Illinois SCRETD certification assessment

- Assessment date: 2026-07-27
- Program: `us-il/scretd`, tax year 2026
- Output: `il_scretd_deferral_amount`

## Executive verdict

The program is genuinely provision-rooted, but it is not certifiable today.

| Question | Result | Evidence |
| --- | --- | --- |
| Provision-rooted? | **Yes** | The only declared output is defined in `us-il/statutes/320/30/3.yaml` with source `Sec. 3, application paragraph and clause (1)` and proof atoms bound to `us-il/statute/320/30/3`. |
| Conformant? | **No** | The signed root does not consume the § 2 household-income judgment. A five-case boundary grid is 4/5 against PolicyEngine before repair. The full surfaces are also not one-to-one comparable. |
| Exercised? | **No** | The current modules have 10 companion cases, only 4 of them at the § 3 root. There is no committed case-grid receipt or complete provision-derived obligation census. |
| Closed? | **No** | The eight-section act census is conservatively 0 fully encoded / 5 excludable / 3 pending, and the outgoing citation frontier is not in the corpus. |
| Executable? | **No** | The current program composes and compiles diagnostically, but there is no published compiled artifact × released-engine execution receipt. The dashboard marks the surface non-executable. |

This is not a finding that the output was synthesized. It is the opposite:
the output node is real, while one of the provision-defined eligibility
judgments that should reach it is disconnected.

## 1. Premise: clean provision root

`programs/us-il/scretd/fy-2026.yaml` declares exactly one output:

```text
il_scretd_deferral_amount
```

The program has no `transformations:` block. Its scope names only:

```text
us-il/statutes/320/30/2
us-il/statutes/320/30/3
```

Repository-wide resolution found one definition of the output:
`us-il/statutes/320/30/3.yaml`, rule
`il_scretd_deferral_amount`. The rule's source is
`Sec. 3, application paragraph and clause (1)`, and its proof atoms cite
`us-il/statute/320/30/3`. No `policies/` module defines or wraps this output.

**Premise verdict: yes, genuinely provision-rooted.**

## 2. Material graph defect

Section 2 defines:

- `maximum_household_income`, including $77,000 for tax year 2026;
- `household_income_no_greater_than_maximum`; and
- `qualified_taxpayer`, which requires age, three-year occupancy, and the
  household-income judgment.

Its existing companion cases correctly show that $77,001 in 2026 makes both
the income judgment and `qualified_taxpayer` fail.

Section 3 imports only `#qualifying_property`. Its
`application_requirements_satisfied` formula repeats the age and occupancy
requirements, including the assessment-freeze shortcuts, but never consumes
`household_income_no_greater_than_maximum` or `qualified_taxpayer`.
Consequently, the composed program contains the income rules without a path
from them to `il_scretd_deferral_amount`.

The smallest textually defensible repair is:

1. import
   `us-il:statutes/320/30/2#household_income_no_greater_than_maximum`;
2. add its proof-import atom, using the current § 2 file hash
   `sha256:934679228fbfd0921adacdb259e9c4711ecc08211e21276ad0b603aefa0d9550`;
3. add `and household_income_no_greater_than_maximum` as an unconditional
   application conjunct, outside both assessment-freeze `or` expressions; and
4. give all § 3 companion cases explicit household-income facts.

Using `qualified_taxpayer or freeze` would be wrong: § 3 lets the freeze
exemption substitute for application items (a) age and (c) occupancy, not for
the § 2(a)(iii) income qualification.

There is still a legal-review point. Section 2 defines the capitalized
“Qualified Taxpayer,” while § 3's operative text says “A taxpayer” and does
not explicitly invoke that capitalized term. Program administration,
PolicyEngine, and the task's stated boundary all treat the income ceiling as
mandatory, but the Act-level link should be approved during signed
regeneration.

The repair was tested only in isolated temporary checkouts. It was not
committed because `us-il/.axiom/encoding-manifests/statutes/320/30/3.json`
cryptographically binds the current module and companion-test hashes. A
manual semantic edit would fail `guard-generated`. The repair must be produced
or applied through an authorized, signed `axiom-encode ... --apply` workflow;
`repair-proof-import-hashes` must not be used to launder a semantic change.

## 3. Closure

### Declared root and inventory universe

The closure root should be the full act, `320 ILCS 30`, not merely the two
files named by the program spec. The corpus-wide scan examined every
`.items[]` record in all 728 inventory files (143,788 records) by
`citation_path`; it did not filter inventory filenames.

There are two inventory ingests for this act: the original ingest and a
self-contained recovery ingest. Their citation/body pairs are identical.
After deduplication, the provision universe is **8 sections**, §§ 1–8.
Each ingest also has a chapter container and an act container, producing
10 inventory rows per ingest; those two structural containers are not
provisions and are outside the eight-section denominator.

The signed ingest manifest reports:

```text
complete: true
matched_count: 10
missing_count: 0
provision_count: 10
```

Its command is explicitly scoped with:

```text
--only-chapter 320 --only-act 30
```

Therefore `complete: true` certifies the ingest against its declared
act-specific scope only. It does not certify all of chapter 320 or any
outgoing dependency.

### Conservative provision ledger

| Provision | Status | Reason |
| --- | --- | --- |
| 320 ILCS 30/1 | Excludable | Short title; `no_household_computation`. |
| 320 ILCS 30/2 | Pending | The module is partial and explicitly defers real-estate taxes, equity interest, and household income; its income judgment is disconnected from the root. |
| 320 ILCS 30/3 | Pending | The root is present, but the operative graph is incomplete and much of the section is represented only by bare parameters or post-determination text. |
| 320 ILCS 30/4 | Pending | Mostly lien-recording procedure, but the filing fee becomes deferred taxes and may affect later 80%-equity capacity. Its boundary semantics must be resolved before exclusion. |
| 320 ILCS 30/5 | Excludable | Billing and payment timing after the household determination; `procedural_no_point_in_time_effect`. |
| 320 ILCS 30/6 | Excludable | Voluntary repayment after determination; `procedural_no_point_in_time_effect`. |
| 320 ILCS 30/7 | Excludable | Intergovernmental treasury remittance; `no_household_computation`. |
| 320 ILCS 30/8 | Excludable | Savings clause; `no_household_computation`. |

**Current census: 0 fully encoded / 5 excludable / 3 pending / 8 total.**

The files for §§ 2 and 3 mean “2 touched / 6 absent,” but file presence is not
closure. Calling those two sections fully encoded would hide their explicit
deferrals and the disconnected eligibility edge. If § 4 is documented as a
boundary-only procedural rule, the act could close at 2 encoded / 6 excluded /
0 pending after §§ 2 and 3 are completed. If its filing-fee effect must be
modeled, the likely final shape is 3 encoded / 5 excluded / 0 pending.

### Outgoing citation frontier

No record among the 143,788 corpus inventory records matches these required
citation paths:

- `us-il/statute/320/25/3.05`
- `us-il/statute/320/25/3.05a`
- `us-il/statute/320/25/3.07`
- `us-il/statute/35/200/15-172`
- `us-il/statute/210/45/1-113`

They supply the cross-referenced household-income chain, the low-income senior
assessment-freeze exemption, and the licensed-facility definition. The broader
Property Tax Code dependency for tax liability and valuation has not yet been
resolved to an exact citation frontier.

### What `closed` needs

`closed` requires:

1. a signed eight-provision ledger with no pending provisions;
2. signed regeneration completing §§ 2 and 3;
3. a documented decision for § 4;
4. corpus ingestion and encoding of every computation-bearing outgoing
   citation, or a typed boundary fact with precise semantics for each crossing;
   and
5. an exact Property Tax Code citation frontier for tax liability and
   valuation.

The target is **8/8 accounted for and 0 pending**, plus zero unresolved
outgoing crossings. The scoped `complete: true` ingest is necessary evidence,
not sufficient closure evidence.

## 4. Conformance and the non-population case grid

### Surface mismatch

PolicyEngine's `il_scretd_deferral_amount`:

1. requires `il_scretd_eligible`;
2. defines that as any tax-unit member meeting its annual age threshold plus
   tax-unit income eligibility;
3. computes income as summed `irs_gross_income`;
4. returns `min(real_estate_taxes, max_annual_deferral)` when eligible; and
5. returns zero otherwise.

For 2026 its relevant boundaries are age 65, income $77,000, and cap $7,500.

The RuleSpec root additionally models the application deadline and form,
qualifying property, three-year occupancy/freeze shortcut, requested partial
amount, appraisal, agreement, joint-owner approval, insurance, fund
availability, and remaining 80%-equity capacity. PolicyEngine does not model
those gates. PolicyEngine also uses IRS gross income, which is not the
cross-referenced Illinois statutory household-income concept.

Accordingly, `axiom-oracles` already classifies the mapping as
`mapping_type: not_comparable` and the program surface as
`known_not_comparable`. That classification should not be changed to a
full-surface comparable mapping merely because a bounded overlap grid passes.

### Five-case grid contract

Use a one-person Illinois tax unit with wage-only income so that, for these
cases only, the declared statutory household-income input equals
PolicyEngine's IRS gross-income input. Hold every RuleSpec-only application,
property, and agreement fact true; set the revolving fund and equity to
$100,000 and prior deferrals plus interest to zero.

| Case | Age | Income | Taxes and request | Current RuleSpec | PolicyEngine | Boundary |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Age below | 64 | $76,999 | $7,501 | $0 | $0 | age below |
| Below boundaries | 65 | $76,999 | $7,499 | $7,499 | $7,499 | age at; income below; cap below |
| Exact boundaries | 65 | $77,000 | $7,500 | $7,500 | $7,500 | income at; cap at |
| Income above | 65 | $77,001 | $7,501 | **$7,500** | **$0** | income above; cap above |
| Cap above | 70 | $50,000 | $7,501 | $7,500 | $7,500 | cap above |

**Current diagnostic result: 4/5.** The single failure is the disconnected
income qualification, not numerical noise.

In an isolated pinned-toolchain diagnostic, adding these five cases to the
existing four § 3 cases without the income edge produced 8/9 passing root
cases; only “income above” failed, with application `holds` instead of
`not_holds` and $7,500 instead of $0. The proposed income-edge repair then
passed all 15 § 2 + § 3 cases in the temporary checkout. These are diagnostic
results, not committed receipts.

The PolicyEngine values were probed only on enumerated synthetic households.
The local simulation used PolicyEngine-US 1.779.4 after verifying that the
four SCRETD variable files and relevant parameters match the intended
PolicyEngine-US 1.767.3 source at commit
`49d19b239a593dbac8920ac6fd80cfe33372343a`. A committed suite must still run
the exact declared 1.767.3 pin.

**No population-backed suite was run.**

### Harness mechanics

The current example lives on `axiom-oracles` main:

- `comparisons/us-additional-medicare-grid.yaml`
- `scripts/run_comparison.py::_run_federal_tax_liability_grid`
- `scripts/generate_federal_tax_liability.py`
- `tests/test_federal_tax_liability_generator.py`
- `dashboard/public/data/axiom-policyengine-us-additional-medicare-grid.json`

The report uses top-level `population: case-grid` and `case_count: 5`.
Its provenance `run_kind` is `manual`; `case-grid` is not a valid provenance
run-kind value.

After the signed RuleSpec repair, a clean SCRETD extension needs:

1. the five exact 2026 companion fixtures above;
2. a dedicated or generalized US case-grid runner rather than silently placing
   a state loan in the federal-tax runner;
3. an SCRETD policy configuration, PolicyEngine situation builder, fixture
   validator, age/income/cap diagnostics, and non-vacuity tests;
4. `comparisons/us-il-scretd-grid.yaml` pinned to PolicyEngine 4.18.9,
   PolicyEngine-US 1.767.3, core 3.30.3, and a fresh RuleSpec SHA/tree;
5. a typed bounded-domain claim that leaves the existing full-surface
   `not_comparable` classification intact;
6. a committed report, affected-map entry, freshness data, scoreboard, and
   dashboard overview; and
7. correct affected-map routing to `rulespec-us`, not a fabricated
   `rulespec-us-il` repository inferred from the legal-ID prefix.

The expected repaired overlap vector is:

```text
[0, 7499, 7500, 0, 7500]
```

### What `conformant` needs

For the bounded PolicyEngine overlap, `conformant` needs a live committed
five-case report with 5/5 agreement, all five cases in scope, zero unexplained
mismatches, exact package/source pins, and a committed RuleSpec SHA/tree.

That is not enough for full-output conformance. A full claim additionally
needs a commensurate reference for the application, property, request, fund,
agreement, and equity constraints that PolicyEngine omits, or an explicitly
accepted certification design that combines a typed partial bridge with
independent reference evidence for those constraints.

## 5. Exercise

The current signed modules contain:

- 6 companion cases for § 2;
- 4 companion cases for § 3; and
- 10 total cases.

The § 3 cases exercise a cap-above result, a late application, the
assessment-freeze shortcut, and the remaining-equity cap. They do not exercise
the income judgment through the root, age below without the freeze shortcut,
income at/above the limit, or the cap below/at its boundary.

The five-case contract would raise the concrete count to:

- 9 § 3 root cases;
- 6 § 2 cases; and
- 15 total companion cases.

Even 15 cases do not by themselves establish `exercised`. The verdict also
needs a reviewed provision-derived obligation census covering:

- all eight application gates and both freeze-substitution branches;
- all three agreement gates;
- each of the five minimum operands: request, payable taxes/assessments, fund,
  annual cap, and equity capacity;
- both zero and positive branches of remaining equity capacity;
- the homestead and qualifying-property branches;
- the income definition and below/at/above limit;
- the age-by-June-1 boundary, which PolicyEngine's annual integer age cannot
  represent exactly; and
- material interactions, including low equity with a binding annual cap and
  assessment-freeze qualification with an independently satisfied income
  ceiling.

The final exercise-case count cannot be stated honestly until that obligation
census and a case-to-obligation set cover are committed. The concrete current
size is 10; the known boundary-grid floor is 15.

## 6. Golden household

### Declared facts

For tax year 2026:

- one Illinois taxpayer, age 70 by June 1;
- wage-only statutory household income of $50,000;
- qualifying owner-occupied property, held and occupied for at least three
  years;
- timely prescribed-form application filed with the correct collector;
- separate assessed valuation;
- requested partial deferral: $9,000;
- real-estate taxes payable: $10,000;
- revolving-fund availability: $20,000;
- tax-deferral and recovery agreement entered;
- all joint-owner approvals and insurance evidence satisfied;
- taxpayer equity interest: $100,000; and
- prior deferred taxes plus interest: $1,000.

No assessment-freeze shortcut or appraisal fallback is needed.

### Statutory derivation

1. Age qualification: `70 >= 65` by June 1, so age holds.
2. Income qualification: `$50,000 <= $77,000`, so the 2026 income judgment
   holds.
3. Three-year occupancy and qualifying-property conditions hold.
4. Application and agreement conditions hold.
5. Gross 80%-equity ceiling:
   `0.80 * $100,000 = $80,000`.
6. Remaining equity capacity:
   `$80,000 - $1,000 = $79,000`.
7. Annual 2026 per-taxpayer cap: `$7,500`.
8. Deferral:

```text
min(
  $9,000 requested,
  $10,000 payable taxes,
  $20,000 available fund,
  $7,500 annual cap,
  $79,000 remaining equity capacity
) = $7,500
```

PolicyEngine independently reaches $7,500 on this bounded household:
age and income are eligible, then
`min($10,000 real_estate_taxes, $7,500 cap) = $7,500`.

The current RuleSpec also returns $7,500 for these positive facts, but that
agreement is not probative of the missing income edge: changing only income
from $50,000 to $77,001 leaves the current RuleSpec result positive while
PolicyEngine returns zero.

## 7. Executability

The current signed program was composed and compiled diagnostically with:

- pinned axiom-encode
  `3869d66d009f52258be35901edbef370e65a399c`;
- pinned axiom-rules-engine
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`; and
- the repository's two existing companion files.

Results:

```text
composition: 15 rules
companion files: 2
companion cases: 10
compiled programs: 2
failures: 0
```

This proves local compilability, not the `executable` verdict. There is no
published compiled SCRETD artifact and no receipt showing a publicly released
engine binary executing that artifact and reproducing the certified grid and
golden values. The current dashboard row says:

```text
surface_status: coverageOnly
surface_oracle: false
surface_executable: false
```

`executable` needs, after the signed semantic repair:

1. a published compiled artifact bound to the final RuleSpec source SHA/tree;
2. a released engine binary with an immutable digest;
3. execution of that exact artifact by that exact binary;
4. reproduction of `[0, 7499, 7500, 0, 7500]` and the $7,500 golden result;
5. a durable receipt binding source, artifact, engine, inputs, and outputs; and
6. dashboard evidence derived from that receipt.

## 8. Work completed and intentionally not completed

Completed:

- verified the clean provision root before doing other work;
- scanned 728 corpus inventory files and 143,788 records by citation path;
- produced the eight-provision closure ledger and outgoing frontier;
- traced both executable graphs;
- designed and probed the five-case non-population boundary grid;
- identified and isolated the income-edge repair;
- validated the current signed files with the pinned engine/encoder;
- validated the repair shape and proposed cases in temporary checkouts;
- produced the hand-checkable golden household; and
- maintained `PROGRESS.md`.

Intentionally not completed:

- no protected RuleSpec or companion fixture was hand-edited;
- no signed manifest was forged or bypassed;
- no full-surface comparable bridge was fabricated;
- no population-backed oracle suite was run;
- no case-grid report was committed before its source-side blocker was fixed;
  and
- no executable or certification verdict was claimed without the required
  artifact and receipts.

## 9. Evidence and vintages

- Program spec: `programs/us-il/scretd/fy-2026.yaml`
- Statute modules:
  `us-il/statutes/320/30/2.yaml` and
  `us-il/statutes/320/30/3.yaml`
- Current § 3 hashes:
  `931a9af9c902eaa2da249aa9993e18f48c8f4bb47563bcbbeffee78ccc2c6120`
  (module) and
  `46e046d2700ff98e581001eb3c9cf515a61956ebf1d359f203fbda6eeefda143`
  (test)
- Signed apply manifest:
  `us-il/.axiom/encoding-manifests/statutes/320/30/3.json`
- Signed corpus manifest:
  `axiom-corpus/.axiom/ingest-manifests/us-il/statute/2026-06-26-ilcs-320-30-us-il-chapter-320-act-30.json`
- RuleSpec toolchain pins: axiom-encode
  `3869d66d009f52258be35901edbef370e65a399c`, engine
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`, and corpus
  `bf97b17baebfdf12601f7c23697524bf5adcdaed`
- Intended oracle pins: PolicyEngine 4.18.9, PolicyEngine-US 1.767.3, and
  PolicyEngine Core 3.30.3

## 10. Recommended order of work

1. Obtain human legal approval for the § 2 income-to-§ 3 application edge.
2. Regenerate/apply § 3 and its nine companion cases through the authorized
   signed encoder workflow.
3. Resolve/ingest the outgoing citation frontier and finish the eight-section
   closure ledger.
4. Add the bounded five-case SCRETD oracle suite, preserving the full-surface
   `not_comparable` classification.
5. Finish the provision-derived exercise census and cases.
6. Publish the compiled artifact and released-engine execution receipt.

Until all four computed verdicts are green, the honest launch result is:
**provision-rooted, but not certified**.
