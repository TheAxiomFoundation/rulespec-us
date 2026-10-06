# PR #1180 repair report — Atomic PR A (§§55, 57, 58, 59)

## Outcome

This was performed as a defensive correctness and completeness audit.

- Branch: `fed-parity/atomicA-57-58-59-55`
- Reviewed starting head: `5a90ed8aa2cfb62f2ce3f431ffd6e155650b43aa`
- Frozen base: `ae64af2740340a40d04ed3c652254f53e62fab61`
- Review read first: `REVIEW.md` at review commit `210731915`
- Final local head: `76451e916d6676a9c955265b5844e018dd8ed8e3`
- Pushes/GitHub writes: none
- Signing: none; all five repair commits are unsigned
- Pre-existing untracked `WORKER-REPORT.md`: preserved unchanged

The four substantive blockers are repaired. Every worker-owned gate is green.
The only remaining handoff is re-signing the affected provenance manifests by
the authorized main lane, as required by the no-signing instruction.

## Commits

1. `e851b3067` — `chore: start PR 1180 repair ledger`
2. `32b2dae55` — `fix: compute MFS increment from complete AMTI`
3. `da1c5062d` — `fix: bind AMT proof evidence to pinned sources`
4. `95d76e1a3` — `test: lock section 151 relation directions`
5. `76451e916` — `chore: record PR 1180 repair gates`

## Blocker 1 — §55(d)(2) MFS increment

`amt_separate_addition` now uses complete preliminary AMTI, excluding only the
MFS increment itself:

```text
pre-increment AMTI =
    taxable income
  + represented §56 excluded deductions
  + §151 exemption deduction
  + §151 senior deduction
  + §57(a)(5) preference
  + signed §58(a) adjustment
  + signed §58(b) adjustment
  + signed §59(e) adjustment
  + signed §59(g) adjustment
  + signed §59(h) adjustment

MFS increment =
  min(
    MFS exemption amount,
    50% × max(0, pre-increment AMTI − complete-phaseout threshold)
  )
```

The reviewer's exact companion case is retained with the lawful downstream
values.

### Exact before/after reproduction

Inputs: MFS, taxable income `$624,100`, standard-deduction addback `$16,100`,
§57(a)(5) preference `$50,000`, ordinary computation, and zero regular tax.

Before:

```text
buggy increment base       = 624,100 + 16,100 = 640,200
MFS increment              = 50% × max(0, 640,200 − 640,200) = 0
AMTI after later §57 item  = 640,200 + 50,000 = 690,200
exemption phaseout         = 95,100
exemption                  = 0
lower-rate tax             = 26% × 122,250 = 31,785
higher-rate tax            = 28% × (690,200 − 122,250) = 159,026
TMT / AMT / income tax     = 190,811
```

After:

```text
pre-increment AMTI         = 624,100 + 16,100 + 50,000 = 690,200
MFS increment              = min(70,100, 50% × (690,200 − 640,200))
                           = 25,000
final AMTI                 = 690,200 + 25,000 = 715,200
exemption phaseout         = 107,600
exemption                  = 0
lower-rate tax             = 26% × 122,250 = 31,785
higher-rate tax            = 28% × (715,200 − 122,250) = 166,026
TMT / AMT / income tax     = 197,811
```

The repaired tax is exactly `$7,000` higher:

```text
197,811 − 190,811 = 7,000 = 28% × 25,000
```

The neighboring pre-existing MFS case was recomputed through the final tax
outputs and remains:

```text
pre-increment AMTI = 650,000 + 16,100 = 666,100
increment          = 50% × (666,100 − 640,200) = 12,950
final AMTI         = 679,050
phaseout           = 89,525
TMT                = 187,689
regular tax        = 160,000
AMT                = 27,689
income tax         = 187,689
```

The exact pinned §55 companion passes all `17/17` cases.

## Blocker 2 — fail-closed §55 domain

`section_55_verified_domain_is_satisfied` now requires:

- the imported/transitive §151 `taxpayer_is_individual` fact; and
- an explicit equality disjunction containing exactly filing statuses `0`,
  `1`, `2`, `3`, and `4`.

The companion retains both reviewer regressions:

- filing status `9` is exercised as a TaxUnit table row and returns
  `not_holds`; all requested §55 money outputs return zero;
- `taxpayer_is_individual=false` returns `not_holds`; all requested §55 money
  outputs return zero.

The table-row form is the repository's established form for intentional
out-of-range tax-status diagnostics. It exercises status `9` in the engine
while satisfying the pinned validator's scalar-fixture policy.

Live mutations confirm both guards matter:

- adding status `9` to the accepted disjunction fails 3 assertions;
- making the individual condition tautological fails 3 assertions.

## Blocker 3 — proof evidence and correctly rooted validation

Repairs:

- replaced §57's heading-only text with the substantive pinned-body definition
  of a specified private activity bond;
- restored the exact curly quotation marks in the §55 AMTI definition;
- used a literal §55(a) excerpt preserving the retained blank-line separators;
- strengthened the §55(d)(2) atom with the operative
  “determined without regard to this sentence” text;
- changed the §59(j) rule's requested source to `26 USC 59(j)`, while retaining
  the separate §55(d)(4) sunset proof atom;
- narrowed §55 requested-source labels to the §55 subtree while retaining
  cross-section legal grounding in their proof atoms;
- regenerated §57 and §59 module hashes and all affected §55 import hashes.

Current module SHA-256 values:

```text
§55  3b7a78143c80aac06860b129fc859a200e339fa49d185ce1c0f76e126a5be4aa
§57  61497fe678e465dc6f52b8a2e8b97c905932d85d0d989aa2bb836eeeee5e8dfa
§58  b93ffa4fce240ee5d8511502d07e8cee8fc14cd5764683efc820e9e42157ea8e
§59  d1e8f213150c74ed437fb6786aff5465f65a65efc1b021137a5a1ea8102012d1
```

The reviewer's explicit canonical-root `ValidatorPipeline` invocation now
returns `all_passed=true`, `ci_pass=true`, and zero issues/errors for all four
sections. The unmodified default-oracle single-§59 constructor also passes
with zero findings.

Proof gates:

```text
structural atoms:  §55 81/81, §57 4/4, §58 13/13, §59 16/16 = 114/114
strict body bytes: §55 24/24, §57 3/3, §58 11/11, §59 11/11 = 49/49
money obligations: 0 missing
```

The strict audit used the review-cited pinned release tree under
`data/corpus/provisions`.

## Blocker 4 — relation schemas and containment

`tests/test_income_tax_pipeline_relation_schemas.py` now locks both imported
§151 relation schemas:

```text
exemption_individual_of_tax_unit:
  arity 2; arguments [TaxUnit, Person]

senior_deduction_individual_of_tax_unit:
  arity 2; arguments [TaxUnit, Person]
```

The positive contract passes. Pointing the final contract at the reviewer's
preserved `Person, TaxUnit` mutant raises the intended assertion. The preserved
specimen remains runtime-inert—the reviewer companion passes—so the static
contract covers a real gap rather than duplicating runtime coverage.

Containment is reconciled:

- reviewed starting PR: exactly 12 non-manifest files plus 4 manifests;
- repaired final branch versus frozen base: exactly 14 non-manifest files plus
  4 manifests;
- repair-only delta versus reviewed head: exactly 6 non-manifest files and no
  manifest edits:

```text
PROGRESS.md
tests/test_income_tax_pipeline_relation_schemas.py
us/statutes/26/55.test.yaml
us/statutes/26/55.yaml
us/statutes/26/57.yaml
us/statutes/26/59.yaml
```

The two additional final non-manifest paths are the required committed
`PROGRESS.md` and the missing schema-contract test. There are no deletions,
renames, workflow/toolchain/dependency changes, or unrelated files.

## Gate results

Pinned inputs:

- corpus: `8af592162231e9de748ba6b98792b426ad4fe8b7`
- encoder: `3869d66d009f52258be35901edbef370e65a399c`
  (`0.2.1200`)
- rules engine: `ffd8213271947b0189a9dd61a055c1e0e78908a0`
- composer: `fabe0b3b3fd6e90d3e8f075516f9b668f524f711`

Final-head canonical-basename archive:

```text
/private/tmp/pr1180-repair-final-head.AqKHwq/rulespec-us
git-archive SHA-256:
e968612128e5055008d27030995751ebba9ec214eeaa166ec8f617f4d8556fdc
```

Final-head smoke:

- companions: `39/39` across 4 modules (`17 + 8 + 6 + 8`);
- explicit-root validation: all 4 sections, zero findings;
- structural proof: `114/114`.

The exhaustive functional archive was commit `95d76e1a3`; every functional
file is byte-identical in final head `76451e916`, whose only subsequent change
was this committed progress ledger. Exhaustive results:

- strict body proof evidence: `49/49`;
- proof-money gate: zero missing;
- duplicate-key/merge audit: zero duplicates;
- schema contract: `1/1`;
- `git diff --check`: pass;
- 13,758 committed archive files: zero missing and zero byte mismatches.

Mutation evidence:

```text
remove §57(a)(5) from MFS increment base   -> 10 failures
accept filing status 9                     ->  3 failures
remove individual-only guard               ->  3 failures
negate §57(a)(7) attestation               ->  5 failures
negate §58(c)(2) attestation               ->  7 failures
negate §59 completion attestation          ->  7 failures
§59(j) false -> true                       ->  8 failures
reverse §151 relation order                -> static contract failure
```

FY2026 FIIT recompose/recompile:

```text
compile exit                  0
artifact format               2
derived outputs               150
evaluation-order entries      150
fast-path strategy            generic_bulk
fast-path compatible          true
fast-path blockers            []
compiled artifact SHA-256     5624cd625ab2fe3b418f50374bb8e313c0635f7d3825bba71adce9f6b5139ba8
```

Index and ledgers:

- reverse index fresh: 4,272 provisions / 5,132 edges / 4,493 modules;
- `oracle-coverage-pending.yaml` byte-identical to reviewed head;
- `known-validation-gaps.yaml`,
  `.axiom/pending-validation-fingerprints.json`, `known-dangling.yaml`, and
  `known-missing-money-atoms.yaml` also byte-identical to reviewed head.

Full repository pytest on the functionally identical exhaustive archive:

```text
73 passed, 1 failed, 1 warning
```

The sole failure is
`tests/test_encoding_manifests.py::test_encoded_modules_match_their_manifests`.
There are no unrelated failures. The warning reports the repository's existing
19 unmanifested modules.

## Required main-lane manifest handoff

The four signed manifests remain byte-identical to reviewed head `5a90ed8aa`.
Editing their hashes while retaining the old HMAC would create a false
attestation, and signing was explicitly forbidden.

The authorized main lane must re-sign sections 55, 57, and 59:

```text
§55 module
old c2be416c67a65faa3c1239c559890c4bcef7ab079417239f9b8fe06deaa0cc97
new 3b7a78143c80aac06860b129fc859a200e339fa49d185ce1c0f76e126a5be4aa

§55 companion
old 6025bce2793f8bacd31dab1d78a48f3c71979e3b09395d2ff9d0b0c4fa41421b
new d2a285381b4ddb57f6472af20d420076a31d4b94b36c6d3f92ff4105efcf4198

§57 module
old 5e92f5faae26d4974f073fedbdeb82853744670762c98da21632028ec7115844
new 61497fe678e465dc6f52b8a2e8b97c905932d85d0d989aa2bb836eeeee5e8dfa

§59 module
old 97fe6fb67b7d97a95cec9ce73b7eee124e152fb7c734e3b1bb2d3afcf606d129
new d1e8f213150c74ed437fb6786aff5465f65a65efc1b021137a5a1ea8102012d1
```

Section 58 and the §57/§59 companions are unchanged and already match their
manifests. After authorized re-signing, rerun the manifest-sync test and full
pytest before pushing.

## Environment and sandbox disclosures

- The default `/Users/maxghenis/bin/python` shim points to a missing
  `/opt/homebrew/bin/python3`. Gates used the existing exact-pinned Python 3.14
  environment and repository test environment instead.
- GitNexus reported no index for this repository. Repository-wide import,
  hash, and dataflow scans supplied the fallback impact evidence.
- `apply_patch` rejected an attempted disposable mutation outside the project
  root. Equivalent mutation copies were created inside the worktree, patched,
  tested, and moved intact to `/private/tmp`; candidate bytes were untouched.
- Recursive cleanup commands were policy-blocked in two gate sessions.
  Exact-target moves/removal were used instead; no evidence or candidate data
  was lost.
- One strict-proof diagnostic initially selected the corpus checkout's legacy
  top-level `provisions/`; the binding rerun used the review's exact
  `data/corpus/provisions` rooting and passed.
- Canonical archives contain no `.git`, so provenance and containment checks
  used the worktree's Git object database.
- Parallel pytest created only disposable `.pytest_cache`/`__pycache__` paths
  in the temporary archive. All committed archive files remained byte-exact.

## Next

1. Authorized main lane re-signs §55, §57, and §59 manifests.
2. Rerun manifest-sync/full pytest; expect all tests green.
3. Push the branch and request re-review.
