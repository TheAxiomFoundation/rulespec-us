# Saver's Credit Compose Revival — Defensive Correctness and Completeness Audit

## Outcome

The saver’s-credit composition is revived on `fed-parity/savers`, grounded to
the pinned Notice 2025-67 corpus text, and committed locally. The implementation:

- imports nine official tax-year-2026 AGI limits instead of accepting
  caller-supplied thresholds;
- computes section 25B AGI with explicit sections 911, 931, and 933 add-backs,
  with no silent defaults;
- applies the $2,000 contribution cap separately to each eligible spouse;
- uses inclusive statutory tier ceilings;
- has a 25-case companion suite plus mutation evidence; and
- passes focused compile, proof, citation, repository-layout, and reverse-index
  gates.

No push, GitHub write, manifest signing, workflow edit, or toolchain edit was
performed.

## Baseline and corpus pin

- Worktree: `/Users/maxghenis/TheAxiomFoundation/wt-savers`
- Branch: `fed-parity/savers`
- Starting `origin/main`: `6b0773d3f7fa6719f208154f3e609e292ab7abe7`
- Pinned corpus in `.axiom/toolchain.toml`:
  `bf97b17baebfdf12601f7c23697524bf5adcdaed`
- `/Users/maxghenis/TheAxiomFoundation/axiom-corpus` was clean and at that
  exact commit; `main` equaled `origin/main`. No fetch was necessary.

## Recovery provenance

The deletion commit and its sole parent were resolved directly in
`/Users/maxghenis/TheAxiomFoundation/wt-fed-credits`:

- Deletion commit:
  `dc7a521fafaa051e3016c8e9756bc52744173ae7`
  (`chore: split saver credit pipeline from PR 1004`)
- Recovered-from parent:
  `9e6d90dc6ee064727822b2d65941bb95b7754061`
- Original unchanged creation commit:
  `56dbbf64c65989c77ca046e97399dd0d568a7406`

Byte-for-byte recovery evidence:

| Recovered path | Git blob in parent | Lines | Bytes | SHA-256 |
|---|---|---:|---:|---|
| `us/policies/income_tax/savers_credit_pipeline.yaml` | `c89ca6ad4207ff3191da206a96bb6a34a690e34f` | 385 | 15,143 | `9620a6d0efba298addbf7c5a9c77db275bbb2187ddef53d2940641a74e842ea4` |
| `us/policies/income_tax/savers_credit_pipeline.test.yaml` | `e5632985921ab1225f3b707b8723677854f96e1f` | 252 | 17,299 | `2f0ef016c1e78b6df968cda6d75de759b01a3062fbe0d8d758da20d8c7dc9329` |

Both recovered worktree files compared byte-equal to
`git show dc7a521fa^:<path>` before rebuilding. The deletion commit’s raw diff
changes both blobs from mode `100644` to zero.

Current post-rebuild SHA-256 values:

- Notice module:
  `40436ffee4b5f13b030a892ddcdee4873adfb0c92e990fdffa37cb981e66a366`
- Pipeline:
  `56fecc5f4ae448cb4422371ab49e7894410d26076ffedeea3847bf8f9fb5f787`
- Pipeline companion:
  `2621795e923fa8eac2eb147bab5d21a60c766cc6b415f85fcf69c03bd9f4af3a`

## Pinned-corpus findings

### Notice 2025-67

The authoritative provision file is:

`/Users/maxghenis/TheAxiomFoundation/axiom-corpus/data/corpus/provisions/us/guidance/2026-07-23-irs-notice-2025-67.jsonl`

| Return category | 50% tier: AGI not over | 20% tier: AGI not over | 10% tier: AGI not over | Corpus evidence |
|---|---:|---:|---:|---|
| Married filing jointly | $48,500 | $52,500 | $80,500 | row 4, `us/guidance/irs/notice-2025-67/page-3` |
| Head of household | $36,375 | $39,375 | $60,375 | sentence begins in row 4/page 3; amounts are in row 5, `.../page-4` |
| All other taxpayers | $24,250 | $26,250 | $40,250 | row 5, `us/guidance/irs/notice-2025-67/page-4` |

The retained official PDF is:

`data/corpus/sources/us/guidance/2026-07-23-irs-notice-2025-67/official-documents/irs-notice-2025-67.pdf`

Its verified SHA-256 is
`1eea8f141b0cddd182f9f09b3bc8ffad683d27ceb806dfc6da126811dc0a1f8d`.

### 26 USC 25B

The authoritative statute provision file is:

`/Users/maxghenis/TheAxiomFoundation/axiom-corpus/data/corpus/provisions/us/statute/2026-07-13-recovery-r2026-07-15-self-contained-r2026-07-17-dedup.jsonl`

- Row 225, `us/statute/26/25B/a`: the credit applies to contributions “of the
  eligible individual” that “do not exceed $2,000.” The cap is therefore
  applied to each eligible spouse, not once to a joint tax unit.
- Row 230 and granular row 914, `.../b` and `.../b/1`: tiers use “not over”
  and “over … but not over.” Each upper boundary is inclusive.
- Granular row 919, `.../b/2`: head-of-household limits use 75% of the joint
  amounts and all-other limits use 50%, after inflation adjustment.
- Row 235, `.../c`: age, student, and dependent eligibility rules.
- Row 245, `.../e`: AGI is determined without regard to sections 911, 931,
  and 933.

Starting from ordinary adjusted gross income, the encoded section 25B amount
is therefore:

`AGI25B = AGI + section_911_excluded_income + section_931_excluded_income + section_933_excluded_income`

The retained statute XML SHA-256 is
`07c45fbb7f655a7b66d727af135c23f7820b3c51b1572b256d68d0c754d8410d`.

## Defensive encoding decisions

### Notice parameter module

`us/policies/irs/notice-2025-67/savers-credit.yaml` follows the current
official-parameter pattern:

- `proof_validation.required: true`;
- page-3/page-4 Notice citations plus section 25B(b);
- `official_parameter_source` upstream review;
- `source_verification.values` for all nine values;
- one bounded-2026 `Money` parameter per published amount;
- amount and effective-period proof atoms; and
- deferred filing-status-selected surfaces with all source values enumerated.

Its same-stem companion asserts all nine published amounts. The pipeline pins
the module’s final SHA-256 in every cross-module import proof.

### Section 25B AGI

The preserved parent unexpectedly already contained all three statutory
add-backs, despite the historical review description saying they were
missing. The recovery hash proves that fact. The rebuild preserves the
correct formula and makes the boundary explicitly fail-closed:

- all three exclusions are required `Money` inputs;
- none has a YAML/default fallback; and
- tests supply zero only as an explicit assertion that the exclusion is zero.

The positive section 911 test starts at ordinary AGI $24,250 and adds $1,
producing section 25B AGI $24,251 and moving from the 50% tier to the 20% tier.

### Filing-status selection and inclusive tiers

The pipeline imports all nine Notice parameters and selects:

- code `1`: joint;
- code `3`: head of household; and
- codes `0`, `2`, and `4`: all other (single, married filing separately, and
  surviving spouse).

An enumerated-status Judgment guards the public credit. The tier comparisons
remain `<=`, matching the statutory “not over” language.

### Per-individual cap

Primary and spouse contributions are separately normalized and capped:

`min(max(0, person_contribution), $2,000)`

Each leg is then gated by that person’s eligibility and the two legs are
summed. A joint case with $5,000 supplied for each spouse produces two
separate $2,000 amounts and a $2,000 credit at the 50% rate.

The pipeline still accepts completed per-person section 25B(d) net
contributions. Distribution attribution and category assembly remain
explicitly deferred; missing distributions are not treated as zero. The
published credit remains before section 26’s aggregate nonrefundable-credit
limitation.

## Companion and mutation evidence

The pipeline companion has 25 hand-computed cases:

- 18 exact-boundary/one-dollar-over cases: all three tier ceilings for single,
  joint, and head-of-household returns;
- married-filing-separately and surviving-spouse all-other-category cases;
- one positive section 911 add-back case;
- one both-spouses-over-cap case; and
- age, student, and dependent screens.

Mutation proof:

1. The first comparison was temporarily changed from `<=` to `<`.
2. The companion produced 8 assertion failures across 25 cases:
   single, joint, head-of-household, MFS, and surviving-spouse exact
   50%-ceiling cases.
3. For single/joint/HoH, both rate and credit assertions changed from
   50%/$1,000 to 20%/$400; MFS and surviving-spouse credit assertions also
   changed from $1,000 to $400.
4. The `<=` comparison was restored.
5. All 25 cases passed again, and the source compared cleanly to committed
   state.

## Validation evidence

| Gate | Result |
|---|---|
| Notice companion through the requested pinned encoder/engine invocation | PASS — 1 file, 1 case |
| Pipeline companion through the requested pinned encoder/engine invocation | PASS — 1 file, 25 cases |
| Focused `axiom_encode.cli validate --skip-reviewers` | PASS — Notice module and pipeline |
| `proof-validate --require-money-atoms` | PASS — 27 Notice atoms + 42 pipeline atoms; 0 of 9 money obligations missing |
| Pinned-corpus path/excerpt resolution | PASS — 6 unique paths, 48 source proof atoms, every excerpt verbatim in its cited row |
| Reverse-index generation and `--check` | PASS — 4,238 provisions, 5,077 edges, 4,485 modules |
| `tests/test_repository_layout.py` + `tests/test_reverse_index.py` | PASS — 15 tests; final post-hardening rerun in 398.97s |
| `git diff --check` | PASS |

The exact pipeline companion invocation was:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Users/maxghenis/TheAxiomFoundation/_worktrees/axiom-encode-782-pinned/src \
/Users/maxghenis/axiom-encode/.venv/bin/python -m axiom_encode.cli test \
  --root /Users/maxghenis/TheAxiomFoundation/wt-savers \
  --axiom-rules-engine-path /Users/maxghenis/axiom-rules \
  us/policies/income_tax/savers_credit_pipeline.test.yaml
```

Because this worktree is named `wt-savers` rather than canonical
`rulespec-us`, standalone compile validation cannot resolve same-repository
absolute imports without repository-root routing. Focused validation used a
temporary `/private/tmp/.../rulespec-us` symlink through
`AXIOM_RULESPEC_REPO_ROOTS`; this is the same source tree and both modules
passed. The required companion command itself accepted
`--root /Users/maxghenis/TheAxiomFoundation/wt-savers` and passed directly
with `/Users/maxghenis/axiom-rules`.

The literal reverse-index command was attempted as requested:

`uv run --with pyyaml python tests/generate_reverse_index.py`

It first could not write the sandboxed home cache. With a writable temporary
cache, `uv` then could not reach PyPI because network access is unavailable.
The generator and `--check` were therefore run successfully with the
already-installed axiom-encode Python/PyYAML environment. Focused pytest used
the already-installed axiom-corpus environment. No dependency, toolchain, or
workflow file was changed.

## Oracle disposition

Do not change Axiom to match either known PolicyEngine defect:

1. **Inclusive boundaries:** PolicyEngine #9151 treats a tier ceiling
   exclusively. Section 25B(b) says “not over,” so an exact ceiling belongs to
   the higher-rate band. Classify exact-ceiling mismatches as an expected
   oracle divergence pending the PE fix.
2. **Joint cap:** the PE side applies one $2,000 cap to a joint unit. Section
   25B(a) applies the cap to contributions of each eligible individual.
   Classify the two-eligible-spouse mismatch as the PE single-cap defect.
3. **Comparison surface:** this pipeline is before section 26. If an oracle
   comparison is added, compare against a before-section-26 potential surface,
   not PE’s final liability-capped credit.
4. **Add-back domain:** never coerce an unavailable section 911/931/933
   exclusion to zero. A missing oracle fact is an unsupported-domain result,
   while an explicit zero is a valid fact.

### Confirmed oracle-pending sync set

The read-only pending checker, run without a program filter, identifies all 20
new rule outputs as unmapped: these nine Notice parameters plus the eleven
pipeline outputs in the immediately following list. All 20 belong in the main
lane’s requested sync:

```text
us:policies/irs/notice-2025-67/savers-credit#savers_credit_10_percent_agi_limit_all_other
us:policies/irs/notice-2025-67/savers-credit#savers_credit_10_percent_agi_limit_head_of_household
us:policies/irs/notice-2025-67/savers-credit#savers_credit_10_percent_agi_limit_joint
us:policies/irs/notice-2025-67/savers-credit#savers_credit_20_percent_agi_limit_all_other
us:policies/irs/notice-2025-67/savers-credit#savers_credit_20_percent_agi_limit_head_of_household
us:policies/irs/notice-2025-67/savers-credit#savers_credit_20_percent_agi_limit_joint
us:policies/irs/notice-2025-67/savers-credit#savers_credit_50_percent_agi_limit_all_other
us:policies/irs/notice-2025-67/savers-credit#savers_credit_50_percent_agi_limit_head_of_household
us:policies/irs/notice-2025-67/savers-credit#savers_credit_50_percent_agi_limit_joint
```

No pending file was edited in this lane.

### Remaining eleven oracle-pending pipeline outputs

These eleven pipeline IDs complete both the 20-ID pending sync set and the
executable-output inventory added relative to `origin/main`:

```text
us:policies/income_tax/savers_credit_pipeline#pipeline_savers_credit_modified_adjusted_gross_income
us:policies/income_tax/savers_credit_pipeline#pipeline_savers_credit_50_percent_agi_limit
us:policies/income_tax/savers_credit_pipeline#pipeline_savers_credit_20_percent_agi_limit
us:policies/income_tax/savers_credit_pipeline#pipeline_savers_credit_10_percent_agi_limit
us:policies/income_tax/savers_credit_pipeline#pipeline_savers_credit_filing_status_is_enumerated
us:policies/income_tax/savers_credit_pipeline#pipeline_savers_credit_applicable_percentage
us:policies/income_tax/savers_credit_pipeline#primary_savers_credit_eligible
us:policies/income_tax/savers_credit_pipeline#spouse_savers_credit_eligible
us:policies/income_tax/savers_credit_pipeline#primary_savers_credit_contributions_taken_into_account
us:policies/income_tax/savers_credit_pipeline#spouse_savers_credit_contributions_taken_into_account
us:policies/income_tax/savers_credit_pipeline#federal_savers_credit
```

## Local commit ledger

- `6fbf665d6` — `chore: start saver credit revival progress log`
- `bdbb8b7f8` — `chore: recover preserved savers credit pipeline`
- `1f1077fb6` — `feat: encode 2026 savers credit notice parameters`
- `ffd4bbe6f` — `feat: compose grounded 2026 savers credit`
- `b63179b58` — `test: record savers credit boundary mutation proof`
- `a4f4e606b` — `chore: index savers credit corpus citations`
- `7d3a944ff` — `fix: keep notice proof excerpt within cited page`

The final report/progress commit follows this ledger. All commits are local;
nothing was pushed.
