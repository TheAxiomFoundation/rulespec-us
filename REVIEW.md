VERDICT: APPROVE

# PR #1180 repair re-review

No blocking repair or containment finding remains at candidate
`7e69fbb5ed19b58d262989cf455c4b9469119a1f`. This review was limited to the
four previously reported blockers, their executable protection, and the
repair-only delta from prior reviewed head
`5a90ed8aa2cfb62f2ce3f431ffd6e155650b43aa`.

## Frozen inputs

- Candidate: `7e69fbb5ed19b58d262989cf455c4b9469119a1f`.
- Prior reviewed head: `5a90ed8aa2cfb62f2ce3f431ffd6e155650b43aa`.
- Pinned corpus: `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Pinned encoder: `0.2.1200` at
  `3869d66d009f52258be35901edbef370e65a399c`.
- Pinned rules engine:
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`; all `110/110` tracked source
  blobs match, and the release binary used for execution has SHA-256
  `674ca6e70afdccb59c3d6847933bc24b4590105e49db54790f2dcd0bdbbe32d7`.
- Canonical candidate archive:
  `/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us`.
- Canonical `git archive` SHA-256:
  `1e49c0ef36a56375f9121562bb791d6bef26791c0609682954b984d6cd4bccf4`.

## Repair verification

### 1. Section 55(d)(2) now uses complete preliminary AMTI

The pinned [§55(d)(2) record](</Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216/data/corpus/provisions/us/statute/2026-07-13-recovery-r2026-07-15-self-contained-r2026-07-17-dedup.jsonl:1084>)
measures the MFS addition from AMTI determined without only the addition
sentence. The pinned [§55(d)(4) record](</Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216/data/corpus/provisions/us/statute/2026-07-13-recovery-r2026-07-15-self-contained-r2026-07-17-dedup.jsonl:1086>)
substitutes 50 percent for 25 percent after 2017.

The repaired
[`amt_separate_addition`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us/us/statutes/26/55.yaml:317>)
base contains taxable income, excluded deductions, both adopted §151 amounts,
the §57 preference, both §58 adjustments, and all three signed §59
adjustments—the same pre-addition terms used by
[`amt_income`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us/us/statutes/26/55.yaml:442>).

Independent arithmetic and the exact-pinned companion agree:

- Repaired counterexample: preliminary AMTI
  `$624,100 + $16,100 + $50,000 = $690,200`; addition
  `min($70,100, 50% × ($690,200 − $640,200)) = $25,000`; final AMTI
  `$715,200`; TMT
  `26% × $122,250 + 28% × $592,950 = $197,811`. This is the lawful `$7,000`
  correction to the predecessor's `$190,811`.
- Neighboring MFS case: preliminary AMTI `$666,100`; addition `$12,950`;
  final AMTI `$679,050`; TMT `$187,689`; and AMT `$27,689` after `$160,000`
  regular tax.

Section 55 passes `17/17`; the retained
[counterexample](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us/us/statutes/26/55.test.yaml:468>)
and [neighboring case](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us/us/statutes/26/55.test.yaml:371>)
assert those exact outputs.

### 2. The adopted domain fails closed

The repaired
[`section_55_verified_domain_is_satisfied`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us/us/statutes/26/55.yaml:199>)
requires `taxpayer_is_individual` and explicitly enumerates only filing
statuses `0..4`.

- The committed [status-9 regression](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us/us/statutes/26/55.test.yaml:509>)
  and [nonindividual regression](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us/us/statutes/26/55.test.yaml:546>)
  both return `not_holds` and zero guarded money outputs.
- Additional exact-engine probes for statuses `-1`, `5`, `8`, `9`, and `10`
  all fail closed.
- Nonindividual units under every otherwise-valid status `0..4` also fail
  closed. The added probe batch is `10/10`.

Mutating the formula to accept status 9 or to make the individual check
tautological produces `3` failing assertions in the corresponding regression
in each case.

### 3. Proof evidence and correct-root validation are green

A programmatic strict-byte audit scanned 703 pinned JSONL files containing
143,779 records. All 25 cited paths resolve uniquely, and every proof excerpt
is an exact UTF-8 substring of corpus body/source-history evidence:

| Module | Strict matches |
| --- | ---: |
| §55 | 24/24 |
| §57 | 3/3 |
| §58 | 11/11 |
| §59 | 11/11 |
| **Total** | **49/49** |

The repaired [§57(a)(5)(C) excerpt](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us/us/statutes/26/57.yaml:67>)
is substantive operative corpus-body text, not the former heading-only string.

Pinned `ValidatorPipeline` was invoked with
`policy_repo_path=<canonical-rulespec-us-root>`—not `<root>/us`—the exact
corpus and engine pins, `enable_oracles=False`, `max_workers=1`,
`require_policy_proofs=True`, `enforce_repository_layout=True`, and reviewers
skipped:

| Module | Compile findings | CI findings | `all_passed` | `ci_pass` |
| --- | ---: | ---: | --- | --- |
| §55 | 0 | 0 | true | true |
| §57 | 0 | 0 | true | true |
| §58 | 0 | 0 | true | true |
| §59 | 0 | 0 | true | true |

The narrowed [§59(j) source declaration](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us/us/statutes/26/59.yaml:221>)
therefore has zero findings under the same correct rooting that exposed the
prior blocker. Structural proof validation is also `114/114` atoms
(`81/4/13/16`), with zero focused money-atom misses.

### 4. Both imported relation directions are statically protected

The §151 declarations are both arity two and
[`[TaxUnit, Person]`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us/us/statutes/26/151.yaml:37>).
The repaired [static contract](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-rereview-canonical/rulespec-us/tests/test_income_tax_pipeline_relation_schemas.py:17>)
locks both exact vectors and passes.

Each relation was independently reversed to `[Person, TaxUnit]` by changing
only its two argument lines:

- reversing `exemption_individual_of_tax_unit`: static test `1 failed`;
- reversing `senior_deduction_individual_of_tax_unit`: static test `1 failed`.

The assertion identifies the reversed relation in each mutant. Both mutated
archives still pass the §55 runtime companion `17/17`, confirming that the new
static contract supplies precisely the previously missing runtime-inert kill.

## Gates, mutations, and containment

- Exact-pinned companions: `39/39` across §§55, 57, 58, and 59.
- Correct-root four-module validation: zero findings, as tabulated above.
- FY2026 FIIT composition/compile: artifact format 2, 150 derived outputs, 150
  evaluation-order entries, and compatible `generic_bulk` fast path with no
  blockers.
- Behavioral mutation battery, all nonzero as required:

  | Mutation | Failed assertions |
  | --- | ---: |
  | omit §57 from preliminary MFS AMTI | 10 |
  | accept filing status 9 | 3 |
  | remove individual-only boundary | 3 |
  | invert §57(a)(7) guard | 5 |
  | invert §58(c)(2) guard | 7 |
  | invert §59 completion guard | 7 |
  | change §59(j) `false` to `true` | 8 |

- Repair range: seven commits. The net diff from the prior reviewed head is
  exactly nine paths: §55 module/companion, §57 module, §59 module, the schema
  contract, and four manifests. The intermediate repair `PROGRESS.md` is
  added, maintained, and dropped within the range; it is absent from the
  candidate tree. No index or validation/oracle ledger path changed.
- `git diff --check` passes. Focused manifest, schema, reverse-index, and
  repository-layout tests are `19 passed` with one expected warning for 19
  pre-existing unmanifested modules.
- Signing commit `7e69fbb5e` changes only the four manifests. Each manifest
  records exactly its module and companion, current SHA-256 bytes,
  `backend: manual`, `manual_exception: rulespec-us#1001`, and encoder commit
  `3869d66d...`. Every applied blob already exists byte-for-byte in signing
  parent `740eaa9c2`; all four supersedes links match the prior manifest hash
  and signature.

## Environment and sandbox disclosures

- GitNexus CLI is present, but `gitnexus status` reports the repository is not
  indexed. No candidate-local index was created; the frozen Git diff, direct
  import scan, exact-engine execution, and FIIT compile provide the scoped
  containment evidence.
- The sandbox rejected an initial mutation patch under `/private/tmp`.
  Mutation archives were moved to the authorized
  `.git/review-worktrees/` area and all requested kills were reproduced.
- An offline dependency setup lacked cached packages and one available Python
  environment lacked `pytest`; existing pinned environments completed every
  substantive gate.
- Test execution created only disposable `.pytest_cache`/`__pycache__`
  directories in the canonical archive. Excluding those caches, it remains
  byte-identical to the frozen `git archive`; no tracked candidate byte
  changed.
- No PR-branch, remote, or GitHub write was made.

## Recommendation

Approve. The four prior blockers are repaired, their exact failure modes are
now executable, the repair range is mechanically contained, and no new
blocking legal-correctness defect was found within the requested scope.
