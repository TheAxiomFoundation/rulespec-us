# WORKER REPORT — Spine Chunk 1: SALT + itemized pipelines

## Result

- Status: complete.
- Branch: `fed-parity/chunk1-salt-itemized`.
- Final tracked HEAD: `1c86ac88cf3eccdcd3feeb098575ca0b44a337cd`.
- Updated prerequisite base: `origin/fed-parity/atomic-63c6-67h` at
  `b8ba5dbe7d4c6f07eaada84bbe035821743d7a77`; this includes `origin/main`
  at `af6c57d618acff5cb268d345653ea3e4cf64feb6`.
- Corpus pin: `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- No push, GitHub write, or signing was performed. No compose manifest was
  generated. This report is intentionally untracked.

Tracked chunk-only diff from the updated Atomic tip:

1. `.axiom/index/provisions_to_rules.json`
2. `PROGRESS.md`
3. `oracle-coverage-pending.yaml`
4. `us/policies/income_tax/salt_deduction_pipeline.yaml`
5. `us/policies/income_tax/salt_deduction_pipeline.test.yaml`
6. `us/policies/income_tax/itemized_taxable_income_deductions_pipeline.yaml`
7. `us/policies/income_tax/itemized_taxable_income_deductions_pipeline.test.yaml`

There are no chunk changes to `.github`, `CODEOWNERS`,
`.axiom/toolchain.toml`, or `.axiom/encoding-manifests`. Changes to those
paths visible against `origin/main` are inherited unchanged from the required
Atomic prerequisite.

## Gate results

- Pinned companion runner: PASS, 2 files and 53 cases
  (`25` SALT + `28` itemized).
- Pinned `validate --skip-reviewers --json`: PASS for both modules,
  `ci_pass=true`, `all_passed=true`, and `errors=[]`.
- Final validation used the task-pinned corpus commit extracted locally and
  supplied through `AXIOM_CORPUS_ARTIFACT_ROOT`; `us/statute/26/165`,
  `/165/c`, and the repaired `/63` all resolve there.
- Reverse-index check: PASS — 4,247 provisions, 5,105 edges, 4,490 modules.
  Delta from updated Atomic: 20 own-module edges, zero removals (14 itemized,
  6 SALT).
- Pending-ledger union: PASS — updated Atomic has 2,139 entries; current has
  exactly those IDs plus the seven IDs below. No base ID was lost, no base
  entry object changed, IDs are sorted and unique, and
  `ceiling == count == 2,146`.
- Import-surface audit: PASS — 63 rules across the ten-module transitive
  closure, 63 unique names, and one uniquely named relation with declared
  arguments `(TaxUnit, Person)`. Neither `us/statutes/26/63/c.yaml` nor the
  Revenue Procedure standard-deduction final is imported.
- Exact-import audit: PASS — all eight SALT and three itemized imports match
  SPINE-PLAN §§6.1–6.2. The itemized module imports §68's final and aliases
  its final/reduction; it contains no local `2/37`, threshold, lesser-of, or
  reduction computation.
- Scope audit: PASS — the diff from updated Atomic contains exactly the seven
  tracked files listed above; no workflow, toolchain, CODEOWNERS, manifest,
  or foreign-ledger change is present.
- Signing audit: all chunk commits and the merge commit are unsigned.

The exact final runtime command was:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Users/maxghenis/TheAxiomFoundation/_worktrees/axiom-encode-782-pinned/src \
/Users/maxghenis/axiom-encode/.venv/bin/python -m axiom_encode.cli test \
  --root . \
  --axiom-rules-engine-path /Users/maxghenis/axiom-rules \
  us/policies/income_tax/salt_deduction_pipeline.test.yaml \
  us/policies/income_tax/itemized_taxable_income_deductions_pipeline.test.yaml
```

The validator used the same pinned `PYTHONPATH`, both module paths, and
`AXIOM_CORPUS_ARTIFACT_ROOT` pointing to an extraction of corpus commit
`8af592162231e9de748ba6b98792b426ad4fe8b7`.

## Required divergence-case walkthroughs

### `salt-low-agi-engine-cap`

Inputs are single status, AGI `$5,000`, completed personal SALT `$10,000`,
and zero §§911/931/933 exclusions. Statutory MAGI is `$5,000`, below the
`$505,000` threshold, so the statutory cap remains `$40,400` and:

```text
min($10,000, $40,400) = $10,000
```

RuleSpec therefore returns `$10,000`. PolicyEngine's pinned
`limit_itemized_deductions_to_taxable_income` simulation flag applies an
extra AGI-based ceiling and predicts `$5,000`. That engine-only ceiling is
deliberately absent from the legal formula.

### `salt-magi-911-addback`

The explicit `(TaxUnit, Person)` relation carries two unequal §911 rows,
`$4,000` and `$6,000`. Their guarded TaxUnit bridge is `$10,000`.

```text
statutory MAGI = $500,000 AGI + $10,000 §911 = $510,000
excess = $510,000 - $505,000 = $5,000
phaseout = 30% * $5,000 = $1,500
cap = $40,400 - $1,500 = $38,900
min($50,000 taxes, $38,900 cap) = $38,900
```

RuleSpec returns `$38,900`. The pinned PolicyEngine cap phases on AGI without
the statutory §911 addback and predicts `$40,400`. The unequal two-row
fixture is also the relation-orientation mutation witness.

### `salt-personal-property-tax-probe`

The only nonzero tax is a completed `$4,000` annual ad valorem personal
property tax under §164(a)(2), with AGI `$100,000`. It is below the unphased
`$40,400` cap, so RuleSpec returns `$4,000`. PolicyEngine's pinned SALT source
list omits this statutory category and predicts `$0`.

## Exact axiom-oracles mapping list

PolicyEngine-US was independently verified from the cached extracted wheel at
`/Users/maxghenis/.cache/uv/archive-v0/-QudTS5FEzSKZ0Anf7ddx`;
`policyengine_us-1.767.3.dist-info/METADATA` reports version `1.767.3`.
Every named candidate below exists as `TaxUnit`, `float`, `YEAR`, `USD`.
`section_68_reduction` does not exist.

The registry's actual mapping types are `direct_variable`,
`derived_expression`, `many_to_one`, `one_to_many`, `parameter_value`, and
`not_comparable`; it has no `bridge` or `reconcile-only` type.

| RuleSpec legal ID | Proposed mapping_type | Candidate PE variable | Priority / reason |
|---|---|---|---|
| `us:policies/income_tax/salt_deduction_pipeline#salt_deduction_pipeline_verified_domain_applies` | `not_comparable` | none | P4; PE has no fail-closed legal-domain judgment. |
| `us:policies/income_tax/salt_deduction_pipeline#federal_section_911_exclusion_for_salt_magi` | `not_comparable` | `foreign_earned_income_exclusion` | P4; nearest bridge value exists, but PE exposes an input surface rather than this guarded relation aggregate. |
| `us:policies/income_tax/salt_deduction_pipeline#federal_salt_deduction` | `direct_variable` | `salt_deduction` | P1; same TaxUnit annual money output, with divergences measured rather than hidden. |
| `us:policies/income_tax/itemized_taxable_income_deductions_pipeline#itemized_taxable_income_deductions_verified_domain_applies` | `not_comparable` | none | P4; PE has no matching fail-closed judgment. |
| `us:policies/income_tax/itemized_taxable_income_deductions_pipeline#itemized_deductions_otherwise_allowable_after_other_limitations` | `direct_variable` | `total_itemized_taxable_income_deductions` | P1; PE's 2026 parameter list is the same six completed components. |
| `us:policies/income_tax/itemized_taxable_income_deductions_pipeline#federal_section_68_reduction` | `not_comparable` | `itemized_taxable_income_deductions_reduction` | P4; diagnostic/reconciliation candidate uses PE's AGI-minus-exemptions proxy and truncated rate, not the statutory completed base. |
| `us:policies/income_tax/itemized_taxable_income_deductions_pipeline#federal_itemized_taxable_income_deductions` | `direct_variable` | `itemized_taxable_income_deductions` | P1; same TaxUnit annual money final. |

Verified PolicyEngine source files:

- `policyengine_us/variables/gov/irs/income/taxable_income/deductions/itemizing/salt_deduction.py`
- `policyengine_us/variables/gov/irs/income/taxable_income/adjusted_gross_income/above_the_line_deductions/foreign_earned_income.py`
- `policyengine_us/variables/gov/irs/income/taxable_income/deductions/itemizing/total_itemized_taxable_income_deductions.py`
- `policyengine_us/variables/gov/irs/income/taxable_income/deductions/itemizing/itemized_taxable_income_deductions_reduction.py`
- `policyengine_us/variables/gov/irs/income/taxable_income/deductions/itemizing/itemized_taxable_income_deductions.py`

## Environment and sandbox disclosures

- The ambient `/Users/maxghenis/TheAxiomFoundation/axiom-corpus` checkout is
  stale at `2794b5448e81525f0ee351cdac2a49d32327aade` and lacks §165. Running
  itemized validation against that unrelated checkout produces only a
  `Source verification source missing: us/statute/26/165` artifact. Validation
  against the repository's actual `8af592…` pin is fully green.
- A supplemental `pytest` invocation was unavailable: the pinned
  axiom-encode venv has no `pytest`, and `/Users/maxghenis/bin/pytest` points
  to a missing `/opt/homebrew/bin/python3`. This was not a required gate.
- A nonessential `ps` diagnostic was denied by the sandbox. It did not affect
  any build, test, validation, index, ledger, or Git result.
- The available local axiom-oracles checkout is behind current mapping
  coverage and its full-repository pending check reports pre-existing
  unrelated debt. The classifier nevertheless reports all seven IDs above in
  `pending.applied` and reports zero problem lines for either new module.
