# PR #1179 blocker repair — defensive correctness and completeness audit

## State

- Branch: `fed-parity/chunk2-taxable-income`
- Reviewed/current pushed starting head:
  `4ced8fb7065311338ea732cab0a26105e750c40f`
- Final local repair head:
  `058c638dbd79df019cc89adc823e5bcc02466f1e`
- Result: all five blocking findings are repaired and all required gates pass.
- The branch is eight unsigned local commits ahead of the unchanged
  remote-tracking head.
- This report is intentionally untracked.
- The pre-existing untracked `WORKER-REPORT.md` was preserved.
- No push, GitHub write, signing operation, or oracle-repository write was
  performed.

## Commits

1. `55ac88e1c` — `docs: start PR 1179 repair audit`
2. `9a6c9994b` — `test: pin imported taxable-income relation schemas`
3. `c3e2a54de` — `fix: align taxable-income proofs with current law`
4. `f1c504ed8` — `test: cover senior MAGI exclusion addback`
5. `ef22b46dc` — `fix: reject contradictory individual entity facts`
6. `14a50028c` — `chore: refresh taxable-income proof index`
7. `b47607e59` — `test: keep MAGI fixture merges disjoint`
8. `058c638db` — `docs: record completed PR 1179 repair audit`

All eight commits were created with signing disabled. `git log %G?` reports
`N` for each.

## Blocker repairs

### 1. Current §165(d) wagering-loss proof and boundary

- Replaced the stale pre-OBBBA proof excerpt with the resolver-selected current
  §165(d)(1) sentence proving both:
  - the deductible amount equals 90 percent of wagering losses; and
  - the deduction is capped at wagering gains.
- The replacement excerpt is a byte-verbatim, unique 302-byte substring of
  pinned `us/statute/26/165`.
- Updated the module rationale, summary, and completed
  `wagering_losses_deduction` input description to state that the supplied
  amount is after both the 90-percent-of-losses limitation and the
  wagering-gain ceiling, as well as applicable substantiation rules.
- The compose continues to accept a completed §165 boundary rather than
  inventing raw-loss or raw-gain entitlement mechanics locally.

### 2. §63(a) itemizer proof and §§61/62 bridge

- Sourced `federal_taxable_income` to 26 USC 61, 62, and 63(a)-(b), rather than
  §63(b) alone.
- Added byte-verbatim proof atoms for:
  - §61's gross-income definition;
  - §62's adjusted-gross-income definition;
  - §63(a)'s general
    gross-income-minus-chapter-deductions taxable-income definition.
- Retained the existing §63(b) adjusted-gross-income-minus definition for the
  nonitemizer branch.
- The imported itemized module remains responsible for §63(d)-(e); no duplicate
  local itemized entitlement was introduced.

### 3. §151 MAGI-addback diagnostic

- Added companion-only case `ti-senior-magi-section-931-addback`.
- It uses a real imported §931 exclusion on the plan-fixed single-senior
  threshold facts:

| Fact/result | Value |
|---|---:|
| Adjusted gross income | 75,000 |
| Imported §931 exclusion | 10,000 |
| Senior-deduction MAGI | 85,000 |
| Phaseout threshold | 75,000 |
| Phaseout excess | 10,000 |
| Phaseout reduction at 6% | 600 |
| Senior amount | 5,400 |
| Standard deduction | 18,150 |
| Total taxable-income deductions | 23,550 |
| Federal taxable income | 51,450 |

- The case asserts the imported exclusion, MAGI, rate/threshold, phased senior
  amount, total deductions, and taxable income.
- §931 was used because its output is TaxUnit-level; this avoids combining a
  positive Person-level §911 fact with an inherited empty SALT relation.
- Common zero-addback inputs and the positive §931 variant use disjoint YAML
  anchors. This was required because pinned validation correctly rejects
  merge-key overrides as duplicate keys.
- The adopted first fourteen grid cases are unchanged; this is a RuleSpec-only
  diagnostic.

### 4. Imported relation-schema contracts

`EXPECTED_RELATION_SCHEMAS` now pins every imported injectable relation in the
closure:

| Module/relation | Arity | Arguments |
|---|---:|---|
| SALT `salt_section_911_individual_of_tax_unit` | 2 | `TaxUnit, Person` |
| §151 `exemption_individual_of_tax_unit` | 2 | `TaxUnit, Person` |
| §151 `senior_deduction_individual_of_tax_unit` | 2 | `TaxUnit, Person` |
| §170(p) `charitable_contribution_of_tax_unit` | 2 | `TaxUnit, Payment` |

Required mutation evidence was demonstrated separately for each newly
registered relation:

| Relation | Positive | Two-line swap | Restored |
|---|---|---|---|
| §151 exemption | `1 passed` | `Person, TaxUnit` → `1 failed` with exact declared/expected mismatch | `1 passed` |
| §151 senior | `1 passed` | `Person, TaxUnit` → `1 failed` with exact declared/expected mismatch | `1 passed` |
| §170(p) charity | `1 passed` | `Payment, TaxUnit` → `1 failed` with exact declared/expected mismatch | `1 passed` |

After each inverse patch, scoped `git diff --exit-code` confirmed the imported
module was byte-restored. Neither `us/statutes/26/151.yaml` nor
`us/statutes/26/170/p.yaml` differs from the reviewed head.

### 5. Contradictory individual/nonindividual facts

- Added
  `not estate_or_trust_common_trust_fund_or_partnership` to the verified
  individual-domain formula.
- Added the exact §63 entity-condition proof excerpt.
- Converted the former `ti-entity-zeroes-standard` fixture into
  `ti-contradictory-individual-entity-facts-fail-closed`.
- The regression deliberately combines the inherited
  `taxpayer_is_individual: true` fact with the nonindividual entity flag and
  asserts:
  - imported `standard_deduction_ineligible: holds`;
  - local verified domain `not_holds`;
  - local deduction total `0`;
  - final taxable income `0`.

## Final canonical gate results

The final committed head was archived with `git archive HEAD` to the required
canonical basename:

`/private/tmp/pr1179-repair-gates.3kcOMg/rulespec-us`

Pins:

- `axiom-encode`:
  `3869d66d009f52258be35901edbef370e65a399c`
- corpus:
  `8af592162231e9de748ba6b98792b426ad4fe8b7`
- companion engine:
  `/private/tmp/pr1179-engine-ffd821.GYcBLs/axiom-rules-engine`

| Gate | Result |
|---|---|
| Pinned companion runner | PASS — 1 file, 28 cases, 1 compiled program, zero failures |
| Pinned `validate --skip-reviewers` | PASS — `ci_pass=true`, `all_passed=true`, zero errors |
| Structural `proof-validate` | PASS — 37 atoms, zero issues |
| Strict money-atom proof validation | PASS — zero obligations missing |
| Resolver-selected excerpt byte audit | PASS — 13 source atoms, 13 unique byte matches |
| Relation-schema contract | PASS — 1 passed |
| Reverse-index freshness | PASS — 4,249 provisions / 5,120 edges / 4,491 modules |
| Pending-ledger union | PASS — 2,148 → 2,151; sorted, unique, ceiling=count, zero lost/changed base records |
| `git diff --check` vs reviewed head and `origin/main` | PASS |
| Imported-module restoration | PASS — §151 and §170(p) byte-unchanged |
| Repair diff containment | PASS — exactly five intended tracked paths |

The reverse-index regeneration changed no key or edge count. Its only semantic
delta adds `proof_atom` to the existing taxable-pipeline `via` vectors for
`us/statute/26/61` and `us/statute/26/62`.

## Pending ledger and mapping implications

The repair adds no executable output ID and changes no rule kind, visibility,
dtype, entity, or period. The pending ledger therefore remains the exact
pre-existing three-entry taxable-pipeline addition:

- `federal_taxable_income`
- `federal_taxable_income_deductions`
- `taxable_income_pipeline_verified_domain_applies`

There are no new mapping implications. The existing oracle handoff remains:

| RuleSpec output | Mapping implication |
|---|---|
| public `federal_taxable_income` | `direct_variable` → PE `taxable_income` |
| private `federal_taxable_income_deductions` | `direct_variable` → PE `taxable_income_deductions` |
| private verified-domain judgment | `not_comparable` |

## Diff containment

Repair-only delta
`4ced8fb7065311338ea732cab0a26105e750c40f..058c638dbd79df019cc89adc823e5bcc02466f1e`:

- `.axiom/index/provisions_to_rules.json`
- `PROGRESS.md`
- `tests/test_income_tax_pipeline_relation_schemas.py`
- `us/policies/income_tax/taxable_income_pipeline.test.yaml`
- `us/policies/income_tax/taxable_income_pipeline.yaml`

The full PR delta versus `origin/main` is those five paths plus the inherited
pending ledger and signed composition manifest. There is no workflow,
toolchain, lockfile, imported-relation module, tracked worker report, or
session-ledger change.

## Manifest handoff

The existing signed composition manifest is intentionally byte-untouched,
matching the repository's prior repair-then-re-sign sequence. Both attested
applied-file hashes are now stale by design:

| Applied file | Signed hash | Repaired hash |
|---|---|---|
| companion | `7b875ff22b30f421a993b5cfcbcc762338409e55b095f7a75fb5bf7f73fa67e2` | `68d295be047d7d743890bf40987aedeae0b11256f8d2cca27c65d65d3685abd8` |
| compose | `460e8554e965c4fcf5839d7963faad91b29f7972e2fc40bf3b5d430a6fdaf7c5` | `812f15410e4266a6118b9929399dbe4ae3f654eb77ad0e7bb77b15ee8c50de8f` |

The authorized main lane must re-sign the composition manifest last and rerun
its manifest/guard checks. No signature was forged, removed, or refreshed in
this worker lane.

## Tooling and sandbox disclosures

- GitNexus graph tools were unavailable and the frozen review already recorded
  this exact-head target as unindexed. Direct merged-source, corpus, and
  executable tracing supplied the dependency evidence.
- One nonessential subagent `ps` process-inspection attempt was sandbox-denied
  with `operation not permitted`. It had no effect on any gate or filesystem
  state.
- Pinned validation initially exposed a duplicate merge-key defect in the new
  diagnostic fixture. The fixture anchors were corrected, committed, and the
  final canonical validation is green with zero findings.
- No network access, push, PR edit, issue edit, GitHub write, signing action, or
  remote mutation was attempted.

## Next

1. The authorized main lane reviews this repair.
2. It re-signs the composition manifest last against the repaired applied-file
   bytes.
3. It reruns manifest/guard checks, then pushes and resumes PR review.
