# Encode §152(c) residency and parental-tiebreak rules (EITC frontier)

## Delivery status

- Branch: `closure/w1-eitc-152-residency`
- Base: `origin/main@ecb057ef3`
- Primary module: `us/statutes/26/152/c.yaml`
- Result: all three assigned frontier leaves are encoded; none is deferred.
- Push: blocked by the execution environment's DNS
  (`Could not resolve host: github.com`).
- Draft PR: not opened because the branch could not be published. Requested
  title: `Encode §152(c) residency and parental-tiebreak rules (EITC frontier)`;
  intended reference: `rulespec-us#1135`.

## Per-item result

| Assigned item | Published-classification row | Output | Result | Governing citation and corpus path | Focused cases |
|---:|---:|---|---|---|---:|
| 4 | 6 | `individual_principal_place_of_abode_with_taxpayer_fraction` | Encoded | 26 USC 152(c)(1)(B), with the EITC U.S.-abode overlay in 26 USC 32(c)(3)(C); `us/statute/26/152/c/1`, `us/statute/26/32/c/3` | 8 |
| 8 | 15 | `child_resided_with_both_parents_same_amount_of_time_and_taxpayer_parent_has_highest_adjusted_gross_income` | Encoded | 26 USC 152(c)(4)(B)(ii); `us/statute/26/152/c/4` | 10 shared parental cases |
| 9 | 16 | `child_resided_with_taxpayer_parent_for_longest_period` | Encoded | 26 USC 152(c)(4)(B)(i); `us/statute/26/152/c/4` | 10 shared parental cases |

Every inventory was checked at axiom-corpus pin
`bf97b17baebfdf12601f7c23697524bf5adcdaed`. One retained record exists for
each of the three paths, all with expression/source date 2026-07-13; no
duplicate or more-specific child records were found.

The §152(c) companion now has 24 cases: 6 pre-existing cases and 18 new
cases. The new cases cover 182/365, 183/365, 183/366, and 184/366 abode
boundaries; full-year and invalid day-count normalization; longer, shorter,
and equal parental residence; higher, lower, equal, and negative parental
AGIs; invalid residence counts; and both positive downstream tiebreak paths.

No §61 or §1402 dependency was introduced. Filed parental AGIs are supplied
as facts rather than re-derived through §62 and the §61 income surface.

## Files

- `us/statutes/26/152/c.yaml`
- `us/statutes/26/152/c.test.yaml`
- `us/statutes/26/32.yaml` (new proof import and cascaded §152 hashes only)
- `us/statutes/26/32.test.yaml` (replace the three former derived leaves)
- `.axiom/encoding-manifests/us/statutes/26/152/c.json`
- `.axiom/encoding-manifests/statutes/26/32.json`
- `.axiom/index/provisions_to_rules.json`
- `PROGRESS.md`
- `OUTPUT.md`

No program, SNAP, toolchain, CI, CODEOWNERS, or oracle-pending file changed.

## Validation

Passed:

```text
env PYTHONPATH=/private/tmp/eitc-u1-toolchain.FGxJtx/axiom-encode/src \
  /Users/maxghenis/TheAxiomFoundation/_bulk_drain/.venv/bin/python \
  -m axiom_encode.cli proof-validate us/statutes/26/152/c.yaml
# 18 atoms passed

env PYTHONPATH=/private/tmp/eitc-u1-toolchain.FGxJtx/axiom-encode/src \
  /Users/maxghenis/TheAxiomFoundation/_bulk_drain/.venv/bin/python \
  -m axiom_encode.cli proof-validate us/statutes/26/32.yaml
# 43 atoms passed

env PYTHONPATH=/private/tmp/eitc-u1-toolchain.FGxJtx/axiom-encode/src \
  /Users/maxghenis/TheAxiomFoundation/_bulk_drain/.venv/bin/python \
  -m axiom_encode.cli test \
  --root /private/tmp/w1-rulespec-alias/rulespec-us \
  --axiom-rules-engine-path /private/tmp/axiom-rules-engine-ffd8213-target/release \
  --json /private/tmp/w1-rulespec-alias/rulespec-us/us/statutes/26/152/c.test.yaml
# 24/24 passed

env PYTHONPATH=/private/tmp/eitc-u1-toolchain.FGxJtx/axiom-encode/src \
  /Users/maxghenis/TheAxiomFoundation/_bulk_drain/.venv/bin/python \
  -m axiom_encode.cli validate --skip-reviewers us/statutes/26/152/c.yaml
# passed from a clean detached checkout

/Users/maxghenis/TheAxiomFoundation/_bulk_drain/.venv/bin/python -m pytest -q
# 73 passed; one pre-existing warning for 19 unmanifested modules
```

Known baseline findings, reproduced unchanged on untouched `origin/main`:

- `axiom-encode validate --skip-reviewers us/statutes/26/32.yaml` reports that
  `eitc_qualifying_child` lacks a positive companion assertion.
- The §32 companion command reports four §32(c)(2) resolution errors involving
  `self_employment_earned_income_component` and the wages input. The §152(c)
  changes add no failures to that set.

## Judgment calls

1. The statute supplies the strict “more than one-half” test but not
   day/night, temporary-absence, or birth/death counting mechanics. The
   fraction therefore consumes the administratively counted abode days
   exposed by Form 8862 and validates them against the taxable-year day count.
   Current [IRS Publication 501](https://www.irs.gov/publications/p501) and
   [Form 8862 instructions](https://www.irs.gov/instructions/i8862) say
   temporary absences count and give special born/died-child treatment; this
   PR does not falsely attribute those mechanics to the retained
   §152(c)(1)(B) body.
2. The parental comparison uses scalar facts for the taxpayer parent and the
   other claiming parent. This matches paragraph (B)'s “both parents” scope
   and remains executable inside §32's existing TaxUnit-to-child relation;
   the current companion runner cannot attach a nested child-to-parent
   relation there.
3. Residence comparisons are strict and invalid negative or over-year counts
   fail closed.
4. The equal-residence AGI branch uses strict `>` rather than `>=`. Exact AGI
   equality therefore produces no unique winner instead of allowing both
   parents to satisfy the singular “parent with the highest adjusted gross
   income” rule.
5. Negative AGIs retain ordinary numeric ordering.
6. The separate EITC requirement that the qualifying child's abode be in the
   United States remains in §32 and was not folded into the general §152
   fraction.

No `deferred_outputs` entry was added or removed in §152(c). The unrelated,
pre-existing §32(f), §32(l), and expired §32(n) deferrals remain unchanged.

## Publish commands

When GitHub DNS is available:

```text
git push --set-upstream origin closure/w1-eitc-152-residency
gh pr create --draft --base main \
  --head closure/w1-eitc-152-residency \
  --title "Encode §152(c) residency and parental-tiebreak rules (EITC frontier)" \
  --body "References rulespec-us#1135."
```
