VERDICT: REQUEST-CHANGES

# PR #1137 round-2 blind review

Reviewed PR head `262119256b47f68b5b5583f0efd76bd6ade7c5f1` against base
`6b0773d3f7fa6719f208154f3e609e292ab7abe7`, using pinned encoder
`3869d66d009f52258be35901edbef370e65a399c`, rules engine
`ffd8213271947b0189a9dd61a055c1e0e78908a0`, and corpus
`bf97b17baebfdf12601f7c23697524bf5adcdaed`.

## Finding

### [HIGH — merge-blocking] The oracle-pending ledger was not synchronized with the three round-2 output renames

The pipeline now exports:

- `pipeline_tier_50_applicable_ceiling_for_return_category` at
  [savers_credit_pipeline.yaml:110](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/us/policies/income_tax/savers_credit_pipeline.yaml:110)
- `pipeline_tier_20_applicable_ceiling_for_return_category` at
  [savers_credit_pipeline.yaml:149](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/us/policies/income_tax/savers_credit_pipeline.yaml:149)
- `pipeline_tier_10_applicable_ceiling_for_return_category` at
  [savers_credit_pipeline.yaml:188](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/us/policies/income_tax/savers_credit_pipeline.yaml:188)

But the committed ledger still declares the removed names
`pipeline_savers_credit_{10,20,50}_percent_agi_limit` at
[oracle-coverage-pending.yaml:3998](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/oracle-coverage-pending.yaml:3998),
[line 4001](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/oracle-coverage-pending.yaml:4001),
and
[line 4004](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/oracle-coverage-pending.yaml:4004).

Full pinned oracle coverage exits 1. It reports all three old declarations as
stale—`output not found (removed or renamed)`—and all three live
`pipeline_tier_*` outputs as unmapped. The live outputs are discovered and
tested (`tested: true`, with 3, 3, and 5 assertions), so this is ledger drift,
not a discovery failure.

Exact-head GitHub Repository Checks independently reproduces the same failure
in [run 30289991267, job 90057289118](https://github.com/TheAxiomFoundation/rulespec-us/actions/runs/30289991267/job/90057289118).
That job passes generated-manifest guard, both RuleSpec YAML validations, all
26 companion cases, and all 69 proof atoms before failing only at full oracle
coverage on these three stale/three unmapped IDs.

Required fix: replace the three removed ledger IDs with the three live
`pipeline_tier_{10,20,50}_applicable_ceiling_for_return_category` IDs, retain
the structurally correct 2,313 ceiling/entry count, and rerun full oracle
coverage at the new head.

## Round-1 fix verification

### Report-file history cleanup — PASS

The PR has three linear commits:

1. `c45bbf60153424dd3b7f9e5c4eae522e6e747fb5`
2. `1b0a2f02e205a86667a9f14977dbdcd4e317f8a7`
3. `262119256b47f68b5b5583f0efd76bd6ade7c5f1`

The union and final diff contain exactly the expected eight paths (1,555
insertions, 1 deletion). `git log --name-status`, full PR patch scanning, and
`git ls-tree` over every PR-only commit found no `PROGRESS.md`,
`WORKER-REPORT.md`, or report content. `git diff --check` passes.

### Deferred-overlap rename — PASS in the RuleSpec validator

The three selected ceilings use the new purpose-specific `pipeline_tier_*`
names, distinct from the notice module's generic deferred surfaces. Pinned
`axiom-encode validate ... --skip-reviewers` passes both modules, including
the deferred-overlap gate. The follow-on ledger synchronization is the sole
defect reported above.

## Other review dimensions

### 26 USC 25B legal fidelity — PASS

- Separate primary and spouse `min(max(0, contribution), $2,000 cap)` legs are
  encoded at
  [savers_credit_pipeline.yaml:447](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/us/policies/income_tax/savers_credit_pipeline.yaml:447)
  and
  [line 477](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/us/policies/income_tax/savers_credit_pipeline.yaml:477),
  then separately gated and added at
  [line 532](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/us/policies/income_tax/savers_credit_pipeline.yaml:532).
- §§911/931/933 exclusions are required, no-default inputs and are
  unconditionally added to AGI at
  [lines 104–108](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/us/policies/income_tax/savers_credit_pipeline.yaml:104).
- Tier comparisons use inclusive `<=` at
  [lines 351–363](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/us/policies/income_tax/savers_credit_pipeline.yaml:351),
  matching §25B(b)'s “not over” grammar.
- Primary and spouse age-18, §152(f)(2) student, and dependent screens are
  encoded at
  [lines 365–445](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/us/policies/income_tax/savers_credit_pipeline.yaml:365).
- §25B(d)(2) is not silent: testing-period distributions, rollovers,
  exceptions, and spouse attribution are explicitly deferred at
  [lines 63–68](/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/review-worktrees/pr-1137-round2-exec/us/policies/income_tax/savers_credit_pipeline.yaml:63);
  the inputs are documented as completed per-person net §25B(d) amounts.

### Notice 2025-67 and stale-value traps — PASS

Pinned corpus page 3 byte-checks joint limits
`48,500 / 52,500 / 80,500`; page 4 byte-checks head-of-household limits
`36,375 / 39,375 / 60,375` and all-other limits
`24,250 / 26,250 / 40,250`. All nine module formulas and selectors use those
values for `2026-01-01` through `2026-12-31`.

The nine 2025 predecessor values occur only inside verbatim proof excerpts
stating “increased from ... to ...”; none enters executable formulas. No
`157,500`/`157500` trap occurs. No PolicyEngine value is used; PolicyEngine
appears only in the test comment documenting the known inclusive-boundary
divergence.

### Companions and mutation — PASS

The exact requested command, rerun from a canonical exact-head disposable
worktree, passes both companion files: 25 pipeline cases plus 1 notice case.
Coverage includes both sides of all three tiers for single, joint, and
head-of-household returns, plus married-filing-separately, surviving spouse,
§911 add-back, per-spouse cap, age, student, and dependent cases.

Changing only the tier-50 operator at pipeline line 352 from `<=` to `<`
killed the mutation with eight failed assertions across five exact-boundary
cases:

- single: 2
- joint: 2
- head of household: 2
- married filing separately: 1
- surviving spouse: 1

The file was restored byte-for-byte to SHA-256
`87a3bf8d1d656597d3818c4cd7eb75f685ed5e7e418e58662c81d6a2f6e10372`;
both suites then passed again. Every detached execution worktree is clean.

An independently archived exact `ffd821...` engine build also passed the same
2-file/26-case suite. Repository Python guards passed 65 tests with one
pre-existing manifest-census warning.

### Proof atoms — PASS

Pinned proof validation passes:

- pipeline: 42 atoms, zero issues
- notice module: 27 atoms, zero issues

An independent exact-string walk checked 48 source atoms / 25 unique
`(citation_path, excerpt)` pairs against the exact `bf97b17...` corpus and
found zero failures. All cited §25B(a), (b), (c), (e) and Notice pages 3–4
rows resolve.

### Remaining hygiene — PASS, except the finding above

- Both manifests cover exactly the four content/test files introduced at
  ancestor `c45bbf601...`; all four SHA-256 values match both that ancestor
  and head. The recorded encoder is the pinned `3869d66...`.
- Exact-head CI's signed generated-manifest guard passes.
- The ledger is structurally +20: base `2293/2293/2293`
  ceiling/entries/unique to head `2313/2313/2313`, with zero removals,
  changed pre-existing entries, duplicates, or foreign-module additions.
  Its three stale in-module IDs are the semantic defect above.
- `tests/generate_reverse_index.py --check` passes:
  4,238 provisions, 5,077 edges, 4,485 modules; semantic diff is six expected
  added provisions, with no removals or changed existing entries.
- No `.axiom/toolchain.toml`, workflow, or `CODEOWNERS` change exists.

## Environment disclosures

- The required shell `git ls-remote origin refs/heads/fed-parity/savers
  refs/pull/1137/head` was attempted twice and failed because the sandbox
  could not resolve `github.com`. Read-only GitHub PR metadata was checked at
  the beginning and end of the review and independently confirmed the
  unchanged exact head `262119256b47...`; the exact-head CI evidence above
  provides a second remote confirmation.
- `/Users/maxghenis/axiom-rules` is a dirty checkout at `aa1ff025...`, not
  the toolchain pin. The literal requested companion command nevertheless
  passes; a separate exact `ffd821...` build and exact-head CI were used for
  pinned validation.
- A first disposable worktree whose basename was not `rulespec-us` caused
  the encoder to derive malformed durable IDs. Rerunning in the canonical
  `.../rulespec-us` worktree resolved that harness-only failure.
- Local HMAC verification could not run without
  `AXIOM_ENCODE_APPLY_SIGNING_KEY`; exact-head CI's generated-manifest guard
  passes with the repository secret.
- GitNexus indexing was blocked from writing
  `~/.gitnexus/registry.json`; its transient untracked caches were removed.
  Raw PR diff analysis, pinned validation, and reverse-index regeneration
  supplied the dependency evidence instead.
