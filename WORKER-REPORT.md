VERDICT: REQUEST-CHANGES

# Blind adversarial review — rulespec-us PR #1137

Reviewed PR head `995fff6104a19a89843934e3832cd097c308af1d` against
`origin/main` at `6b0773d3f7fa6719f208154f3e609e292ab7abe7`.
The review ledger and this report exist only on throwaway branch
`review/pr-1137-995fff`, after the reviewed commit.

## Request-change findings

### [HIGH, merge-blocking] Forbidden review artifacts are committed in the PR

The PR-only comparison has 10 files and includes:

```text
A PROGRESS.md
A WORKER-REPORT.md
```

This directly violates the required invariant that neither file appear in
`git diff --name-only origin/main..995fff6104a1`. It is also an observed CI
failure, not merely a style concern: GitHub Actions run `30287674016`, job
`90049528491`, failed `Reject disallowed repository layout` with:

```text
Repository layout does not match .axiom/repository-structure.yaml.
- PROGRESS.md: top-level file is not allowed
- WORKER-REPORT.md: top-level file is not allowed
```

The failure then skipped RuleSpec validation in that job. Remove both files
from the PR head and rerun the full repository checks.

### [HIGH, merge-blocking] The pinned encoder rejects all three selected AGI-limit outputs

Using the encoder pinned by the PR,
`3869d66d009f52258be35901edbef370e65a399c`, this command exits 1:

```sh
python -m axiom_encode.cli validate --skip-reviewers \
  us/policies/income_tax/savers_credit_pipeline.yaml
```

The CLI reports that
`pipeline_savers_credit_50_percent_agi_limit` composes the imported
`savers_credit_50_percent_agi_limit_all_other` while the overlapping deferred
`savers_credit_50_percent_agi_limit` remains unresolved. Direct invocation of
the same pinned CI check enumerates the corresponding defects for the 50%,
20%, and 10% selected limits.

Exact declarations:

- Pipeline selected outputs:
  `us/policies/income_tax/savers_credit_pipeline.yaml:110`,
  `:149`, and `:188`.
- Imported category values:
  `us/policies/income_tax/savers_credit_pipeline.yaml:123-137`,
  `:162-176`, and `:201-215`.
- Overlapping Notice deferred surfaces:
  `us/policies/irs/notice-2025-67/savers-credit.yaml:44-66`.

The current remote layout failure masks this next validation failure. Make the
selected outputs concrete/non-conflicting under the pinned authoring contract,
or otherwise resolve the deferred generic surfaces, then revalidate and
re-sign the affected manifests.

## Passed review dimensions

### Legal fidelity

- **Per-eligible-individual cap:** pinned statute row 225,
  `us/statute/26/25B/a`, limits contributions “of the eligible individual.”
  The pipeline independently caps primary and spouse at lines 447-505 and sums
  the eligible legs at lines 532-547. The joint fixture at test lines 303-318
  proves `50% × ($2,000 + $2,000) = $2,000`.
- **Section 25B(e) AGI:** pinned statute row 245,
  `us/statute/26/25B/e`, is implemented at pipeline lines 86-108 as AGI plus
  sections 911, 931, and 933 exclusions. Lines 557-580 declare all four values
  as required inputs with no defaults. Removing the explicit section 911 zero
  caused 21 `missing input section_911_excluded_income` failures; restoration
  returned the suite to green.
- **Inclusive tiers:** pinned statute row 230,
  `us/statute/26/25B/b`, uses “not over.” Pipeline lines 351-363 use `<=` for
  all three ceilings.
- **Eligibility:** pinned statute row 235,
  `us/statute/26/25B/c`, is encoded for both primary and spouse at pipeline
  lines 365-445: age 18, not a section 152(f)(2) student, and not claimable as
  another taxpayer's dependent. Pinned row 1260,
  `us/statute/26/152/f/2`, supplies the full-time/five-calendar-month student
  definition; the pipeline requires the completed statutory classification
  rather than a generic student flag.
- **Testing-period distributions:** not silent. Pipeline lines 50-68 explicitly
  defer per-person section 25B(d) category, testing-period-distribution,
  rollover/exception, and spouse-attribution composition. Inputs at lines
  596-622 require completed per-person net section 25B(d) amounts.

### Notice 2025-67 and stale-value audit

The nine encoded values at
`us/policies/irs/notice-2025-67/savers-credit.yaml:23-31` byte-match the
retained official text:

| Return category | 50% | 20% | 10% |
|---|---:|---:|---:|
| Joint | $48,500 | $52,500 | $80,500 |
| Head of household | $36,375 | $39,375 | $60,375 |
| All other | $24,250 | $26,250 | $40,250 |

Evidence resolves uniquely in pinned corpus `bf97b17baebfdf12601f7c23697524bf5adcdaed`:

- Notice page 3:
  `data/corpus/provisions/us/guidance/2026-07-23-irs-notice-2025-67.jsonl:4`.
- Notice page 4: the same file at row 5.
- The retained PDF SHA-256 is
  `1eea8f141b0cddd182f9f09b3bc8ffad683d27ceb806dfc6da126811dc0a1f8d`.

All nine versions apply only from `2026-01-01` through `2026-12-31`.
Selectors correctly map `1` to joint, `3` to head of household, and `0/2/4`
to all other. Structured executable/test scanning found no 2025 limits and no
`157500`; prior-year amounts occur only inside official “increased from …
to …” proof excerpts. The Notice module/test contain no PolicyEngine
provenance.

### Tests, mutation, and fail-closed behavior

On an exact-head detached worktree whose leaf is canonically named
`rulespec-us`, the requested command passed:

```text
RuleSpec companion tests passed: 2 file(s), 26 case(s)
```

Coverage includes both sides of all three tiers for single, joint, and head of
household; MFS and surviving-spouse selectors; a section 911 add-back; separate
spouse caps; and age/student/dependent screens.

Real mutation evidence:

1. Changed the first tier operator from `<=` to `<`.
2. The same 26-case run failed eight assertions across the single, joint,
   head-of-household, MFS, and surviving-spouse exact-50%-ceiling paths.
3. Restored `<=`.
4. The suite returned to 26/26 and the pipeline SHA-256 returned to
   `56fecc5f4ae448cb4422371ab49e7894410d26076ffedeea3847bf8f9fb5f787`;
   the exact-head worktree is clean.

A supplemental offline build of the exactly pinned rules engine
`ffd8213271947b0189a9dd61a055c1e0e78908a0` also passed all 26 cases on exact
PR bytes.

### Proofs

- `proof-validate --require-money-atoms` passes.
- Pipeline: 42 atoms.
- Notice: 27 atoms.
- Money obligations: 0 missing of 9.
- All 48 source-backed excerpts exist verbatim in exactly one cited pinned
  corpus row; the remaining 21 pipeline atoms are imports.

### Manifests, ledger, index, and forbidden infrastructure changes

- The two manifest `applied_files` unions equal exactly the four changed
  RuleSpec/test YAMLs.
- All four attested hashes match the PR head and ancestor `953106a58`; that
  commit passes `git merge-base --is-ancestor 953106a58 995fff6104a1`.
- The hashes are:
  - pipeline test:
    `2621795e923fa8eac2eb147bab5d21a60c766cc6b415f85fcf69c03bd9f4af3a`
  - pipeline:
    `56fecc5f4ae448cb4422371ab49e7894410d26076ffedeea3847bf8f9fb5f787`
  - Notice test:
    `45786d0c6888bd5e7675b866ab893b8bcebdde9fa99a54319ebb7db796cccac9`
  - Notice module:
    `40436ffee4b5f13b030a892ddcdee4873adfb0c92e990fdffa37cb981e66a366`
- Both manifests have HMAC-SHA256 signatures with key ID
  `axiom-encode-apply-v1`; the remote generated guard passes at the target
  head.
- `oracle-coverage-pending.yaml` moves from 2,293 entries/ceiling 2,293 to
  2,313/2,313. The delta is exactly the expected 20 IDs (11 pipeline, 9
  Notice), with no removals or foreign additions.
- Reverse-index check passes: 4,238 provisions, 5,077 edges, 4,485 modules.
- No `.axiom/toolchain.toml`, workflow, or CODEOWNERS change appears in the
  PR-only diff. `git diff --check` passes.

## Environment and sandbox disclosures

- The required direct `git ls-remote` attempt failed because sandbox DNS could
  not resolve `github.com`. The read-only GitHub connector independently
  returned PR branch `fed-parity/savers` at exact full head
  `995fff6104a19a89843934e3832cd097c308af1d`; the local remote-tracking ref
  matches it.
- Running the test command from the review worktree whose path ends in
  `pr-1137-995fff` failed canonical import resolution because the encoder
  derived IDs from the noncanonical leaf. The exact detached worktree ending
  in `rulespec-us` passed as reported above.
- `/Users/maxghenis/axiom-rules` is at `aa1ff025…`, not the pinned engine
  commit. Creating an external Git worktree at the pin was denied by the
  filesystem sandbox; an archive-built pinned engine supplied the independent
  passing run.
- Local HMAC verification could not run because
  `AXIOM_ENCODE_APPLY_SIGNING_KEY` is unavailable. Hash/ancestor checks passed,
  and the remote generated guard succeeded.
- GitNexus built a local index but could not register it because the sandbox
  denied writing `/Users/maxghenis/.gitnexus/registry.json`; graph queries
  were therefore unavailable. Direct diff, corpus, validator, and execution
  evidence supplied the review.

## Required resolution

Remove the two forbidden root artifacts, resolve all three pinned-validator
deferred-surface errors, regenerate/re-sign affected artifacts, and rerun the
full repository checks before merge.
