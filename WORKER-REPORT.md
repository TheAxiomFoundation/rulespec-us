# Chunk 2 taxable-income RuleSpec worker report

## State

- Branch: `fed-parity/chunk2-taxable-income`
- Base: `origin/main` at `ae64af274`
- Head: `196dbd0140ab9bc8261594e3ce2a6671551e1dea`
- Claim: `rulespec-us#1001` claim 7, `us-pe:taxable_income`
- Result: worker-authorized RuleSpec implementation and gates are complete.
- This file is intentionally untracked.
- No push, GitHub write, signing operation, or oracle-repository write was performed.
- The signed manifest is intentionally absent; the main lane must sign and create
  `.axiom/encoding-manifests/us/policies/income_tax/taxable_income_pipeline.json`
  last.

## Commits

1. `792fde7a6` — `chore: start chunk 2 progress log`
2. `3fdd0caff` — `Add federal taxable-income pipeline`
3. `04d7b90f1` — `Regenerate taxable-income coverage metadata`
4. `196dbd014` — `Record completed Chunk 2 worker gates`

## Done

- Added `us/policies/income_tax/taxable_income_pipeline.yaml`.
- Added `us/policies/income_tax/taxable_income_pipeline.test.yaml` with all 14
  binding section 6.3 cases and 13 companion-only diagnostics.
- Added exactly three local executable rules:
  - private `taxable_income_pipeline_verified_domain_applies`;
  - private `federal_taxable_income_deductions`;
  - public `federal_taxable_income`.
- Introduced no local `data_relation` or `derived_relation`.
- Regenerated `.axiom/index/provisions_to_rules.json`.
- Extended `oracle-coverage-pending.yaml` as a sorted, lossless union from 2,148
  to 2,151 entries.
- Maintained the committed non-root progress file at
  `work-in-progress/chunk2/PROGRESS.md`; no root `PROGRESS.md` exists.

## Next

1. Main lane reviews the compose and companion.
2. Main lane signs the applied pipeline files with the composition exception and
   creates the manifest last; no attested content should change afterward.
3. The paired oracle PR adds `us-taxable-income-grid`, the generator config and
   tests, the bridge contract below, any measured dispositions, and adoption
   artifacts pinned to this RuleSpec head/tree.
4. After any main-lane content change, rerun all archive gates and sign against
   the new ancestor rather than amending beneath a signature.

## Intended tracked diff

Relative to `origin/main`, the branch changes exactly:

- `.axiom/index/provisions_to_rules.json`
- `oracle-coverage-pending.yaml`
- `us/policies/income_tax/taxable_income_pipeline.test.yaml`
- `us/policies/income_tax/taxable_income_pipeline.yaml`
- `work-in-progress/chunk2/PROGRESS.md`

There is no `.github` change, root progress file, manifest, importer refresh,
bytecode artifact, or unrelated tracked file.

## Exact imports and hashes

The compose uses the ten imports prescribed by SPINE-PLAN section 6.3:

| Import | SHA-256 proof hash |
|---|---|
| `us:policies/income_tax/itemized_taxable_income_deductions_pipeline#federal_itemized_taxable_income_deductions` | `da533e2f7e0cfd79c11e35c502860c7c5b09b7b197ab78e6266ecbced9bde56a` |
| `us:policies/irs/rev-proc-2025-32/standard-deduction#standard_deduction` | `094cdd5d0f026ec381bf708a4d821d956b4cbfcade4d9270410baf5c9658f04b` |
| `us:statutes/26/63/c/6#standard_deduction_ineligible` | `ee32cfd0ed49ed31983fd36e7a8fd74b3c0a2f7adc4ce6151d95c0956de8d2b3` |
| `us:statutes/26/151#section_151_exemption_deduction` | `28fb0e7c50d48ad764ff1ddee8b654a18006fc3dde026034b4dfb6efb90a0fb2` |
| `us:statutes/26/151#senior_deduction` | `28fb0e7c50d48ad764ff1ddee8b654a18006fc3dde026034b4dfb6efb90a0fb2` |
| `us:policies/income_tax/qualified_business_income_deduction_pipeline#federal_qualified_business_income_deduction` | `0289ec52ae86438182d2ae9be281d2711c5e093c1b7cc086678f42e4c69f47c2` |
| `us:statutes/26/170/p#nonitemizer_charitable_deduction` | `e460a0d2e5275870e1b47b657a9755bf7d2f4028cfe3fae538be03dc7d77d791` |
| `us:statutes/26/224#qualified_tips_deduction` | `098fe7fa0062c6dbf4433bbd68b322821e56975e8ce36d85d0e0da9eec2c4fcd` |
| `us:statutes/26/225#qualified_overtime_deduction` | `43ed6c47485c241b89493f356ace95ef927094bad1fe5d35d7d059b295d04f9a` |
| `us:statutes/26/163/h/4/C/ii/I#qualified_passenger_vehicle_loan_interest_deduction_after_modified_adjusted_gross_income_limit` | `a27298953ad96cf724c580854b0a8d038a15fcf1c2787cb07098c82343820088` |

No stale import hash was found and no importer/companion refresh cascade was
needed. The standard-deduction closure contains the Revenue Procedure module and
`63/c/6.yaml`, not the colliding `63/c.yaml` module.

## Design and fail-closed boundary

The guarded deduction total is:

```text
itemizer:
  itemized + QBI + wagering + tips + overtime + senior + auto-loan interest

nonitemizer:
  section-63(c)(6)-eligible standard + QBI + nonitemizer charity
  + tips + overtime + senior + auto-loan interest

taxable income:
  max(0, AGI - section 151 exemption deduction - selected deductions)
```

The verified domain requires status `0..4`, an individual taxpayer, the imported
itemized and QBI boundaries, complete 2026 temporal facts, a section 170(p) fact
consistent with `resolved_itemization_election`, nonnegative completed amounts,
and every imported component-domain attestation. It treats the election as a
resolved legal/return fact and does not encode PolicyEngine's optimization
heuristic.

The raw Revenue Procedure amount is set to zero in the selected nonitemizer total
when any imported section 63(c)(6) disqualifier holds. Companion diagnostics
cover MFS/either-spouse-itemizes, nonresident alien, qualifying section 443 short
return, and estate/trust/common-trust-fund/partnership. Each starts from raw
standard deduction 16,100, applies zero, and produces taxable income 100,000 on
100,000 AGI with all other deductions zero.

## Section 6.3 case walkthroughs

Dollar values are annual 2026 amounts. `Std` is the raw Revenue Procedure amount;
`Itemized` is the imported section 68 final. The selected `Total` is the local
guarded deduction total.

| Case | Status / election | AGI | Std | Itemized | Other selected components | Total | Taxable income |
|---|---|---:|---:|---:|---|---:|---:|
| `ti-single-standard` | single / standard | 100,000 | 16,100 | 0 | none | 16,100 | 83,900 |
| `ti-joint-standard` | joint / standard | 200,000 | 32,200 | 0 | none | 32,200 | 167,800 |
| `ti-hoh-standard` | HOH / standard | 100,000 | 24,150 | 0 | none | 24,150 | 75,850 |
| `ti-mfs-standard` | separate / standard | 100,000 | 16,100 | 0 | none | 16,100 | 83,900 |
| `ti-surviving-standard` | surviving / standard | 200,000 | 32,200 | 0 | none | 32,200 | 167,800 |
| `ti-single-itemized` | single / itemized | 100,000 | 16,100 | 25,000 | none | 25,000 | 75,000 |
| `ti-choice-equal` | single / standard | 100,000 | 16,100 | 16,100 | resolved election keeps standard | 16,100 | 83,900 |
| `ti-nonitemizer-all-components` | single age 65 / standard | 75,000 | 18,150 | 0 | QBI 10,000; charity 500; tips 5,000; overtime 2,000; senior 6,000; auto 1,000 | 42,650 | 32,350 |
| `ti-itemizer-all-components` | single age 65 / itemized | 75,000 | 18,150 | 30,000 | QBI 10,000; wagering 5,000; tips 5,000; overtime 2,000; senior 6,000; auto 1,000 | 59,000 | 16,000 |
| `ti-personal-exemption-zero` | single / standard | 50,000 | 16,100 | 0 | four exemption relation rows × zero exemption amount | 16,100 | 33,900 |
| `ti-floor-zero` | single / standard | 10,000 | 16,100 | 0 | none; final zero floor binds | 16,100 | 0 |
| `ti-senior-single-threshold` | single age 65 / standard | 75,000 | 18,150 | 0 | senior 6,000 | 24,150 | 50,850 |
| `ti-senior-single-plus-one` | single age 65 / standard | 75,001 | 18,150 | 0 | senior 5,999.94 | 24,149.94 | 50,851.06 |
| `ti-senior-joint-threshold` | joint, both age 65 / standard | 150,000 | 35,500 | 0 | senior 12,000 | 47,500 | 102,500 |

### Exact completed worksheet and bridge values

The bridge vector is ordered as
`[itemized, QBI, nonitemizer charity, tips, overtime, auto interest, exemptions]`.
The senior value is diagnostic only and is not bridged into PolicyEngine.

| Case | Election | Section 68 completed scalar | Section 199A completed scalar | Bridge vector | Senior diagnostic |
|---|---|---:|---:|---|---:|
| `ti-single-standard` | false | 100,000 | 83,900 | `[0, 0, 0, 0, 0, 0, 0]` | 0 |
| `ti-joint-standard` | false | 200,000 | 167,800 | `[0, 0, 0, 0, 0, 0, 0]` | 0 |
| `ti-hoh-standard` | false | 100,000 | 75,850 | `[0, 0, 0, 0, 0, 0, 0]` | 0 |
| `ti-mfs-standard` | false | 100,000 | 83,900 | `[0, 0, 0, 0, 0, 0, 0]` | 0 |
| `ti-surviving-standard` | false | 200,000 | 167,800 | `[0, 0, 0, 0, 0, 0, 0]` | 0 |
| `ti-single-itemized` | true | 75,000 | 75,000 | `[25,000, 0, 0, 0, 0, 0, 0]` | 0 |
| `ti-choice-equal` | false | 83,900 | 83,900 | `[16,100, 0, 0, 0, 0, 0, 0]` | 0 |
| `ti-nonitemizer-all-components` | false | 75,000 | 75,000 | `[0, 10,000, 500, 5,000, 2,000, 1,000, 0]` | 6,000 |
| `ti-itemizer-all-components` | true | 16,000 | 75,000 | `[30,000, 10,000, 0, 5,000, 2,000, 1,000, 0]` | 6,000 |
| `ti-personal-exemption-zero` | false | 50,000 | 33,900 | `[0, 0, 0, 0, 0, 0, 0]` | 0 |
| `ti-floor-zero` | false | 10,000 | 0 | `[0, 0, 0, 0, 0, 0, 0]` | 0 |
| `ti-senior-single-threshold` | false | 75,000 | 50,850 | `[0, 0, 0, 0, 0, 0, 0]` | 6,000 |
| `ti-senior-single-plus-one` | false | 75,001 | 50,851.06 | `[0, 0, 0, 0, 0, 0, 0]` | 5,999.94 |
| `ti-senior-joint-threshold` | false | 150,000 | 102,500 | `[0, 0, 0, 0, 0, 0, 0]` | 12,000 |

The two all-component cases deliberately preserve the binding completed section
199A boundary at 75,000. An algebraically reconstructed downstream scalar would
activate section 199A's 20% taxable-income ceiling and would not produce the
prescribed 10,000 QBI deduction. The compose does not invent or recompute that
upstream worksheet value.

## Companion-only diagnostics

The additional 13 cases cover:

- invalid status via the same TaxUnit-table mutation pattern as Chunk 1;
- nonindividual taxpayer;
- isolated imported itemized-domain failure;
- isolated QBI aggregation-attestation failure;
- resolved-election / section 170(p) mismatch;
- negative completed wagering deduction;
- false vehicle-interest temporary-window fact;
- every imported component attestation false together;
- all four section 63(c)(6) standard-deduction disqualifiers;
- an imported relation-orientation witness combining one senior Person row and
  two charitable Payment rows.

Every out-of-domain diagnostic returns `not_holds`, zero local deductions, and
zero final taxable income. There is only one new public amount, so the public
fail-closed surface is fully covered.

## Import-closure and relation audit

A recursive audit of the exact merged target found:

```text
merged_modules=25
imported_modules=24
unique_rules=227
imported_rules=224
duplicate_names=0
local_relations=0
```

The four existing imported relations are:

- `salt_section_911_individual_of_tax_unit`: `(TaxUnit, Person)`
- `exemption_individual_of_tax_unit`: `(TaxUnit, Person)`
- `senior_deduction_individual_of_tax_unit`: `(TaxUnit, Person)`
- `charitable_contribution_of_tax_unit`: `(TaxUnit, Payment)`

Because the taxable-income module adds no relation, no
`EXPECTED_RELATION_SCHEMAS` entry and no derived-relation injection invariant are
needed. The caller-injected-row union gotcha is therefore inapplicable locally.

The required two-line-swap kill was demonstrated against the existing static
contract:

1. Temporarily changed the SALT arguments from `(TaxUnit, Person)` to
   `(Person, TaxUnit)`.
2. The contract exited 1 with an assertion showing declared
   `['Person', 'TaxUnit']` versus expected `['TaxUnit', 'Person']`.
3. Restored the two lines.
4. The contract passed and `git diff --exit-code` confirmed no residual change.

## Oracle PR handoff

### New-output mapping proposals

Only `federal_taxable_income` is public. The other two entries are included
because the coverage classifier enumerates private derived rules too.

| Legal ID | Visibility | Proposed `mapping_type` | PE-US 1.767.3 variable | Notes |
|---|---|---|---|---|
| `us:policies/income_tax/taxable_income_pipeline#federal_taxable_income` | public | `direct_variable` | `taxable_income` | Exact TaxUnit/year/USD final; PE formula is `max(0, adjusted_gross_income - exemptions - taxable_income_deductions)`. |
| `us:policies/income_tax/taxable_income_pipeline#federal_taxable_income_deductions` | private | `direct_variable` | `taxable_income_deductions` | Exact selected TaxUnit/year/USD deduction total within the adopted domain. |
| `us:policies/income_tax/taxable_income_pipeline#taxable_income_pipeline_verified_domain_applies` | private | `not_comparable` | none | Legal/runtime boundary judgment with no one-to-one PE variable. |

Suggested direct-variable metadata for the two amount mappings is
`country: us`, `program: tax`, `entity: tax_unit`, `period: year`, `unit: USD`,
and `comparison: money`.

### Exact taxable config bridge

```text
federal_itemized_taxable_income_deductions
  -> itemized_taxable_income_deductions
federal_qualified_business_income_deduction
  -> qualified_business_income_deduction
nonitemizer_charitable_deduction
  -> charitable_deduction_for_non_itemizers
qualified_tips_deduction
  -> tip_income_deduction
qualified_overtime_deduction
  -> overtime_income_deduction
qualified_passenger_vehicle_loan_interest_deduction_after_modified_adjusted_gross_income_limit
  -> auto_loan_interest_deduction
section_151_exemption_deduction
  -> exemptions
resolved_itemization_election
  -> tax_unit_itemizes
```

Compared output:

```text
federal_taxable_income -> taxable_income
```

Do not bridge `senior_deduction`; record and reconcile PE's independently
derived `additional_senior_deduction` diagnostic. Also record raw
`standard_deduction` and the selected branch diagnostics.

### PE-US 1.767.3 verification

The cached package metadata at
`/Users/maxghenis/.cache/uv/archive-v0/-QudTS5FEzSKZ0Anf7ddx` reports version
`1.767.3`. The following exact classes were found there:

- `taxable_income`
- `taxable_income_deductions`
- `itemized_taxable_income_deductions`
- `qualified_business_income_deduction`
- `charitable_deduction_for_non_itemizers`
- `tip_income_deduction`
- `overtime_income_deduction`
- `auto_loan_interest_deduction`
- `exemptions`
- `tax_unit_itemizes`
- `additional_senior_deduction`
- `standard_deduction`

## Gate results

Final gates ran against canonical-basename archive
`/private/tmp/chunk2-head-archive.xhz2nw/rulespec-us`, created with
`git archive HEAD` at head `196dbd0140ab9bc8261594e3ce2a6671551e1dea`.

| Gate | Result |
|---|---|
| Pinned `axiom_encode.cli test` on the companion | PASS, 27/27 cases |
| Pinned `axiom_encode.cli validate --skip-reviewers` with corpus pin `8af59216` | PASS, CI green, zero findings |
| Reverse-index generator `--check` | PASS, 4,249 provisions / 5,120 edges / 4,491 modules |
| Reverse-index base-preservation audit | PASS, 15 added edges, 2 new provision keys, all additions point only to the taxable-income module, zero lost/changed base edge |
| Pending-ledger exact-union audit | PASS, base 2,148 / head 2,151 / ceiling 2,151 / sorted unique / zero changed or lost base entry |
| Changed-file PolicyEngine coverage classifier | PASS, three outputs; all `pending_classification` and companion-tested; zero unmapped |
| Exact merged-surface audit | PASS, 25 modules / 227 unique rules / zero duplicates / no `63/c.yaml` / no local relation |
| Static relation-schema contract | PASS after restoration; deliberate two-line swap failed as required |
| `git diff --check origin/main...HEAD` | PASS |
| Intended-file-only audit | PASS, exactly five tracked paths listed above |
| Worktree cleanliness before report | PASS |

The full-repository `oracle-coverage-pending check` was also inspected, but the
locally installed oracle registry reports unrelated pre-existing unmapped state
outside this change. It was not used to rewrite the ledger. The binding
changed-file classifier and the exact base-preserving ledger ratchet both pass
for all three Chunk 2 outputs.

## Environment and authorization disclosures

- No sandbox denial occurred.
- One initial test invocation used the suggested but nonexistent
  `/Users/maxghenis/TheAxiomFoundation/axiom-rules` path; it was immediately
  rerun successfully against the actual local engine checkout
  `/Users/maxghenis/TheAxiomFoundation/axiom-rules-engine`.
- No network action was required.
- No push, PR edit, issue edit, GitHub write, signature, or manifest generation
  was attempted.
