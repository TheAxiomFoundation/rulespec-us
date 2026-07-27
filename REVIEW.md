VERDICT: APPROVE

# PR #1143 blind adversarial review

No merge-blocking defect was found at GitHub-confirmed head
`6573e95d65e9a64f16bde98b18b24f3f5aff04e0`
(`fed-parity/addmed-se-leg`).

## Scope and isolation

- GitHub metadata was checked at the start and again before this report. The
  head remained the same open, mergeable, five-commit PR targeting `main`.
- The immutable PR range is
  `6b0773d3f7fa6719f208154f3e609e292ab7abe7..6573e95d65e9a64f16bde98b18b24f3f5aff04e0`.
- The range contains exactly the requested four files: pipeline, companion,
  manifest, and reverse index (`242` additions, `160` deletions).
- Review work occurred in disposable local worktrees/clones. No remote or
  GitHub write was made.

## Legal fidelity

Pass.

- A clean local axiom-corpus clone was detached exactly at
  `db12795577c5809009168982cf8a72fb58440620`.
- All 12 source-backed proof excerpts were compared with the retained corpus
  text and matched verbatim. The retained regulation anchor is
  `us/regulation/26/1/1401-1/d/2/i` in
  `data/corpus/anchors/us/regulation/2026-07-24-1401-coordination-repair-title-26-part-1.jsonl`.
- The implementation applies `0.009` to nonnegative self-employment income in
  excess of the coordinated threshold. It maps joint to `$250,000`, married
  filing separately to `$125,000`, and all other documented statuses to
  `$200,000`.
- The reduced threshold is
  `max(0, filing-status threshold - section 3121(a) wages)`, and the SE tax
  base is independently floored at zero.
- The retained statute faithfully says `section 3121(b)(2)`. The only such
  occurrence in the PR's YAML/test pair is the module rationale, which labels
  it “documentary only, never operative proof.” Both operative proof atoms use
  26 CFR 1.1401-1(d)(2)(i), section 3121(a) wages, and section 3101(b)(2).
- The featured amount independently recomputes:
  `150000 * 0.9235 = 138525`;
  `max(0, 200000 - 100000) = 100000`;
  `(138525 - 100000) * 0.009 = 346.725`.

Pinned-encoder `validate --skip-reviewers --json`, directed to that exact
corpus checkout, returned `ci_pass=true`, `all_passed=true`, and `errors=[]`.
Proof validation passed all 17 atoms.

## Wage-leg preservation and blast radius

Pass.

- The complete `federal_additional_medicare_wage_tax` rule node is
  byte-identical at base and head, with SHA-256
  `53614ab7b3447d8e08a13e1c138c90e9588e319116fc86dfc95b0e2dc9c1c4b0`.
- The imported `us/statutes/26/3101/b/2.yaml` blob is also unchanged.
- All eight pre-existing wage-only companion blocks are byte-identical. Across
  all 13 retained case names, every period, complete input, filing-status/wage
  input, and wage-tax expectation is unchanged.
- Precision note: five retained positive-SE forward-contract blocks update
  comments and SE/helper/combined expectations, and one old fail-closed case is
  renamed while retaining the same input and `$450` wage result. Those are
  necessary SE-leg activation changes; no wage assertion was rewritten.
- Direct repository-wide import/reference searches found no program or
  external RuleSpec module consuming a changed pipeline output. The change is
  currently isolated to this module and its bookkeeping.

## Adversarial execution

Pass.

- The repository-pinned engine commit
  `ffd8213271947b0189a9dd61a055c1e0e78908a0` was built locally.
- Exact-head target companion: `19/19` cases passed.
- Target plus direct wage and self-employment companions: `39/39` passed.
- Cases exercise wages exactly at the threshold, wages above the threshold
  with a zero-floored SE threshold, a self-employment loss, joint and separate
  returns, the `$346.725` calculation, and valid-domain additivity.
- In the positive-both-legs case, wage tax `0.009` plus SE tax `8.3115`
  produces combined tax `8.3205`.
- A false international-system attestation deliberately makes the public SE
  and combined outputs fail closed while leaving the independently valid wage
  leg observable. This is the documented invalid-domain contract, not an
  additivity defect.

Required mutations all killed the suite:

| Mutation | Result |
| --- | --- |
| Remove wage reduction | 30 failures across 10 cases |
| Change joint threshold `$250,000 -> $200,000` | 7 failures across 3 cases |
| Remove threshold floor at zero | 19 failures across 8 cases |

The pipeline bytes were restored after each mutation, the target returned to
`19/19`, and the mutation worktree ended clean and detached at the exact PR
head.

## Manifest, index, and history hygiene

Pass.

- The final commit changes only the re-signed manifest. Its parent already
  contains both attested applied-file bytes.
- Recorded and recomputed hashes match:
  - companion:
    `2d89ceef5a13d9e085d1055498a1b24c7ce67c106b6886070b7e59abbafec7b0`
  - pipeline:
    `3c30282d2c6c7a09e0ffb9d14d48afd68daa71ccc142beb44747d2d76ac21128`
- Encoder provenance is the clean pinned commit
  `3869d66d009f52258be35901edbef370e65a399c`, version `0.2.1200`; the
  supersedes linkage matches the prior manifest.
- The canonical reverse-index check passed at `4,233` provisions, `5,069`
  edges, and `4,483` modules. Its PR diff is exactly the new regulation entry
  for this module via `module` and `proof_atom`.
- Manifest/index tests passed `9/9`; repository-layout tests passed `9/9`.
- The PR-only history has no progress, report, ledger, toolchain, dependency,
  workflow, or foreign paths. `PROGRESS.md` and this report exist only in the
  local review branch above the pinned PR head.
- Read-only GitHub checks at the exact head show the generated guard and reverse
  index jobs green. The known corpus-resolution red state pending pin PR #1140
  is not treated as a defect; the required local `db127955...` validation is
  green.

## Non-blocking notes and tooling disclosures

- There is no positive-SE status-4/surviving-spouse fixture, although direct
  inspection confirms status 4 uses the correct `$200,000` branch. All
  executable fixtures are 2026, so effective-date correctness was also checked
  directly rather than mutation-proved.
- GitNexus reported the disposable repository as unindexed. Its analyzer
  parsed the repository but the sandbox denied registration at
  `/Users/maxghenis/.gitnexus/registry.json`; direct exhaustive symbol/import
  searches supplied the blast-radius evidence instead.
- The system Python lacked PyYAML/pytest, and an attempted isolated dependency
  fetch was DNS-blocked. Existing pinned/Homebrew environments completed all
  checks.
- The signing secret was not present locally, so HMAC authenticity was not
  re-derived locally. GitHub's secret-backed generated guard passed at the
  exact head, while local hash, ancestry, provenance, and supersedes checks all
  passed.
- During isolated mutation setup, sandbox policy rejected one hardlink clone,
  direct patching under `/private/tmp`, and an unnecessary cleanup command.
  Safe no-hardlink/scratch-copy fallbacks succeeded; the final mutation and
  execution worktrees are clean.

