VERDICT: REQUEST-CHANGES

# Blind adversarial review — rulespec-us PR #1180

PR #1180 is not safe to merge. The core §55 correction understates AMT for an
in-domain married-filing-separately taxpayer whenever a newly added AMTI item
crosses the §55(d)(2) threshold. The candidate also accepts invalid filing
statuses and nonindividual tax units, has a non-body §57 proof excerpt, fails
correctly rooted pinned validation for §59, and leaves the newly imported §151
relation schemas outside the static contract.

## Frozen review target

- Live PR: open, base `main`, 13 commits.
- Base: `ae64af2740340a40d04ed3c652254f53e62fab61`.
- Exact head: `5a90ed8aa2cfb62f2ce3f431ffd6e155650b43aa`.
- Exact head branch:
  `fed-parity/atomicA-57-58-59-55`.
- Corpus: clean detached
  `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Canonical archive:
  `/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-canonical/rulespec-us`.
- Canonical `git archive` SHA-256:
  `e4854b7a420e0a565dbb569b3843456af88734fc9c8261d91afc5a29473edb24`.
- Pinned encoder:
  `3869d66d009f52258be35901edbef370e65a399c`
  (`0.2.1200`).
- Pinned rules engine:
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`.

No PR-branch, remote, or GitHub write was made.

## Blocking findings

### 1. §55(d)(2) MFS AMTI is computed from an incomplete base

[`amt_separate_addition`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-canonical/rulespec-us/us/statutes/26/55.yaml:303>)
uses only `taxable_income + amt_excluded_deductions`. The newly added senior
deduction and §§57–59 amounts are added later by
[`amt_income`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-canonical/rulespec-us/us/statutes/26/55.yaml:419>).

The retained §55(d)(2) record instead measures the increment from alternative
minimum taxable income “determined without regard to this sentence.” In other
words, only the MFS increment itself is removed from the preliminary AMTI; the
other AMTI adjustments remain. See the pinned
[§55(d)(2) corpus record](</Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216/data/corpus/provisions/us/statute/2026-07-13-recovery-r2026-07-15-self-contained-r2026-07-17-dedup.jsonl:1084>).

An added in-domain counterexample uses MFS, taxable income `$624,100`,
standard deduction `$16,100`, and a `$50,000` §57(a)(5) preference:

```text
pre-increment AMTI = 624,100 + 16,100 + 50,000 = 690,200
§55(d)(2) increment = 50% × (690,200 − 640,200) = 25,000
final AMTI = 715,200
TMT = 26% × 122,250 + 28% × (715,200 − 122,250) = 197,811
```

The exact-head engine instead returns increment `$0`, AMTI `$690,200`, and TMT
`$190,811`, understating tax by `$7,000`. The failing reviewer fixture is
[preserved in the review ledger](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-section55-mutation/rulespec-us/us/statutes/26/55.test.yaml:582>).

Required repair: compute a preliminary AMTI containing every applicable
§§56–59 and §151 item except the MFS increment, derive the increment from that
preliminary amount, and retain a companion case with a nonzero adjustment that
crosses the MFS threshold.

### 2. The §55 verified domain does not enforce its adopted domain

The domain formula at
[`55.yaml:200`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-canonical/rulespec-us/us/statutes/26/55.yaml:200>)
checks amounts and completion attestations but never:

- restricts `filing_status` to the exact five values `0..4`; or
- requires the tax unit to be an individual.

Two otherwise valid reviewer cases demonstrate the leak:

- [filing status `9`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-section55-mutation/rulespec-us/us/statutes/26/55.test.yaml:623>)
  expected `not_holds`, but the engine returns `holds`;
- [`taxpayer_is_individual=false`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-section55-mutation/rulespec-us/us/statutes/26/55.test.yaml:640>)
  expected `not_holds`, but the engine returns `holds`.

This violates SPINE-PLAN §5 fail-closed house style and §6.4's individual-only,
five-status boundary. The canonical §55 companion contains neither required
case. Add both guards and both regression cases.

### 3. The proof and deterministic-validation contract is not green

There are two independent failures.

First, the §57 proof atom at
[`57.yaml:74`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-canonical/rulespec-us/us/statutes/26/57.yaml:74>)
uses `Specified private activity bonds` as evidence for
`us/statute/26/57/a/5/C`. In the pinned PR-B
[corpus record](</Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216/data/corpus/provisions/us/statute/2026-07-27-usc-amt-ftc-sections-title-26.jsonl:25>),
that string occurs only in `heading`; it is absent from `body`. Release-bound
proof evidence consists of body plus source history, not headings.
A programmatic unique-citation, exact-UTF-8 body audit found `24/25` exact
§§57–59 excerpts, with this as the sole miss. The current proof validator
rejects it; pinned `0.2.1200` reports `4/4` only because that older structural
validator does not bind excerpt text to corpus evidence.

Second, exact-pinned deterministic validation with
`ValidatorPipeline(policy_repo_path=<canonical-root>, ...)` fails §59:

```text
`section_59_j_kiddie_exemption_limit_applies` source
`26 USC 55(d)(4)(A)(iii) and 59(j)` is outside requested source
`us:statutes/26/59`.
```

The triggering source is
[`59.yaml:221`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-canonical/rulespec-us/us/statutes/26/59.yaml:221>).
The result is `all_passed=false`, `ci_pass=false`; §§57 and 58 pass the same
explicit-root invocation.

The branch CLI's apparent four-file pass is not equivalent evidence. For the
archive path, its root-discovery helper resolves `<canonical-root>/us` as the
policy repository rather than `<canonical-root>`, bypassing this requested
source-subtree check. Repair the §59 source declaration and require the
explicit canonical-root invocation to return zero findings.

### 4. The compiled relation closure is not statically protected

The new §151 imports bring two schemas into the compiled §55 closure:
[`exemption_individual_of_tax_unit`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-canonical/rulespec-us/us/statutes/26/151.yaml:37>)
and
[`senior_deduction_individual_of_tax_unit`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-canonical/rulespec-us/us/statutes/26/151.yaml:46>).
The static schema contract still lists only the SALT relation at
[`test_income_tax_pipeline_relation_schemas.py:17`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-canonical/rulespec-us/tests/test_income_tax_pipeline_relation_schemas.py:17>).

In a reviewer archive, reversing the §151 exemption relation arguments and
updating the resulting import hashes leaves both checks green:

- static schema test: `1/1`;
- full §55 companion: `14/14`.

That is the exact runtime-inert mutation the static contract is meant to catch.
Add both §151 relation vectors to the contract and retain the relation-order
mutation evidence.

This also explains the mechanical containment mismatch. The final PR changes
12 non-manifest files plus four manifests, not the requested 13 files plus
manifests. The author's intermediate count of 13 included its temporary
`PROGRESS.md`, which was removed before signing; the required schema-contract
file remained unchanged.

### 5. Two new §55 excerpts also fail a strict byte audit

This is independent of the explicit §§57–59 miss:

- [`amt_income`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-canonical/rulespec-us/us/statutes/26/55.yaml:334>)
  drops the retained corpus's curly quotation marks around “alternative
  minimum taxable income”;
- [`alternative_minimum_tax`](</Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1180-canonical/rulespec-us/us/statutes/26/55.yaml:892>)
  YAML-folds the retained §55(a) blank-line separators into spaces.

The exact-body result is `22/24`. Structural proof validation still reports
`81/81`, so these need literal evidence repair rather than reliance on the
older gate.

## Lawful corrections and expected-value audit

Apart from the MFS interaction defect, the requested §55 corrections are wired
as intended:

- senior deduction and guarded §§57–59 amounts enter AMTI;
- itemizers subtract the §68 reduction;
- exactly one completed §26(b) regular-tax total is consumed;
- ordinary FTC appears only on the regular-tax comparison side;
- AMTFTC appears only on tentative minimum tax;
- the post-2017 §59(j) branch is removed;
- Form 4972 is no longer subtracted and instead must be zero;
- a nonzero §911(a) exclusion fails closed pending the §911(f) worksheet.

Independent statutory arithmetic reproduced these targeted expectations:

| Correction | Comparable old result | Corrected result | Statutory reason |
|---|---:|---:|---|
| §68 reversal for itemizer | AMTI `$122,000` | `$119,000` | §56(b)(1)(E): §68 does not apply |
| §151 senior addback | AMTI `$116,100` | `$122,100` | all §151 deductions restored in AMTI |
| Signed §§57–59 items | AMTI `$116,100` | `$166,950` | `+50,000 +1,000 −500 +400 −125 +75` |
| FTC sides | AMT `$35,618` under reused-credit formula | `$30,618` | §55(b)(1)(A) AMTFTC vs. §55(a)/(c) ordinary FTC |
| Post-2017 kiddie probe | exemption `$14,750`; taxable excess `$85,250` | exemption `$90,100`; taxable excess `$26,000`; AMT `$6,760` | §55(d)(4) sunsets §59(j) after 2017 |
| Nonzero Form 4972 / §911 | formerly evaluated | all §55 money outputs zero | bounded domain excludes both broader worksheets |

The split-credit recomputation is:

```text
base TMT = 195,618
TMT after AMTFTC = 195,618 − 10,000 = 185,618
regular side after ordinary FTC = 160,000 − 5,000 = 155,000
AMT = 30,618
income tax before credits = 160,000 + 30,618 = 190,618
```

Base/head preservation is otherwise sound:

- base §55 companion: `5/5`;
- head companions: `36/36`;
- shared no-AMT, high-income, and MFS expected outputs are unchanged;
- a reviewer-only joint partial-phaseout probe preserves AMTI `$1,052,200`,
  phaseout `$26,100`, exemption `$114,100`, and taxable excess `$938,100`;
- the changed kiddie outputs above are tied solely to the statutory sunset.

## §§57–59 and mutation audit

- Public output lists exactly match SPINE-PLAN §9 step 5.
- §59(j) is effective after 2017 and all eight §59 cases prove `not_holds`.
- The adopted §59 fixture proves the three signed adjustments are zero; the
  diagnostic fixture separately reproduces `400`, `-125`, and `75`.
- §58 exposes signed completed values and both public Money outputs are guarded
  by the combined bounded-domain judgment.
- Exact-engine companions for §§57–59 pass `22/22`.
- False-attestation coverage is §57 `5/5`, §58 `4/4`, and §59 `5/5`.
- Author mutations were reproduced with the exact engine:
  §57(a)(7) produces 5 failures, §58(c)(2) 7, §59 completion 7, and §59(j)
  `false -> true` fails all 8 cases.
- An independent AMTFTC-guard inversion produces 2 failures.
- A separate review mutation changing the Form 4972 zero guard to `!= 0`
  produces 49 failures across 9 §55 cases.

The judgment/guard mutations are therefore live; the defects above are missing
domain/schema/proof cases, not vacuous execution.

## Cascade, provenance, and mechanical evidence

The following checks pass:

- repository-wide import audit: only §55 imports the new §§57–59 outputs;
  every external proof hash is current and every local import is
  `sha256:local`; no stragglers;
- module SHA-256 values:
  §55 `c2be416c...0cc97`, §57 `5e92f5fa...15844`,
  §58 `b93ffa4f...ea8e`, §59 `97fe6fb6...d129`;
- fresh FY2026 FIIT composition: artifact format 2, 150 derived outputs,
  fast-path compatible; base has 137 outputs, head adds 14 intended outputs
  and removes only `amt_kiddie_tax_exemption_limit`;
- pending ledger: exact sorted/unique union, `2148 -> 2159`, exactly 11
  additions, no prior row removed or changed, `ceiling == count`;
- waiver/fingerprint handling: §55 entries removed, not refreshed; §§57–59
  have no live entries;
- reverse index: 4,272 provisions, 5,132 edges, 4,493 modules;
- four manifests: exactly module plus companion, current SHA-256 bytes,
  `backend: manual`, `manual_exception: rulespec-us#1001`, encoder
  `3869d66d...`; every applied blob already exists in signing parent
  `c36b0b58b`, and the signing commit changes only the manifests;
- no workflow, toolchain, dependency, Cargo, or `tools/` change;
- `git diff --check`, full repository pytest, layout/manifest/index tests, and
  the existing schema test pass.

These green gates do not exercise the MFS/new-adjustment interaction, invalid
status, nonindividual domain, body-bound proof evidence, or imported §151
relation order.

## Environment and sandbox disclosures

- Shell `gh pr view` could not resolve GitHub; the read-only GitHub connector
  supplied live PR metadata.
- GitNexus reported this repository is not indexed. Its offline npm fallback
  was uncached and could not write its normal npm log location. I did not
  create a tracked `.gitnexus/` index; the full repository import scan is the
  fallback impact evidence.
- `uv` could not initialize its read-only user cache; all substantive runs
  used the already-installed exact-pinned environment.
- Sandbox policy denied `ps` and one subreviewer's initial `/private/tmp`
  patch. The patch was recreated under `.git/review-worktrees/`; no evidence
  was lost.
- One direct four-file `ValidatorPipeline` attempt stalled in executor
  shutdown and was interrupted. The exact §59 invocation was rerun
  independently to completion with the exact pinned encoder and engine and
  produced the deterministic finding quoted above.
- Test runs created only disposable untracked `__pycache__`/`.pytest_cache`
  data in the shared canonical archive after it had been proven byte-exact.
  No tracked candidate byte changed.

## Required before re-review

1. Correct §55(d)(2) to use complete pre-increment AMTI and add the failing
   MFS/nonzero-adjustment fixture.
2. Enforce individual-only and filing-status `0..4` in §55 and add both
   fail-closed companion cases.
3. Replace the §57 heading-only excerpt with body evidence; repair the two
   strict §55 excerpts.
4. Make explicit canonical-root pinned validation pass §59 with zero findings.
5. Add the two imported §151 relation vectors to the static schema contract
   and retain a reversing-order mutation.
6. Regenerate affected hashes, manifests, reverse index, and ledgers; then
   rerun the complete 36-case companion batch, explicit-root four-file
   validation, proof-byte audit, mutations, and 150-output FIIT composition.
