VERDICT: APPROVE

# PR #1177 repair re-review

Risk: LOW for the scoped repair. Both prior blockers are repaired with direct
negative/byte-level evidence, and the repair range is exactly contained.

## Evidence digest

### 1. Section 164 excerpt is byte-verbatim

- Audited immutable target `345c22030642cbd37a9fe46877591a8e1df5af7e`
  against the clean detached corpus checkout at
  `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Parsed the target YAML, selected the unique `us/statute/26/164` definition
  atom, and byte-searched the unique retained §164 row (JSONL line 36).
- The repaired excerpt is 151 Unicode characters / 155 UTF-8 bytes and occurs
  exactly once in the retained body, at byte offset 8864.
- Excerpt and retained span are byte-equal and share SHA-256
  `880b94a90114834681f926ec10a621c4b243c47c40f2145dbd2d08e89268131b`.
  This includes the `the term “modified adjusted gross income”` wrapper and
  the UTF-8 curly quotes.

### 2. Relation-order contract kills the exact prior mutation

- Direct source inspection of `/Users/maxghenis/axiom-rules/src` at
  `c4b62bdb740d4149f0872783964f917e74cffe42` confirms that
  `DataRelationRef`, lowering, `RelationSpec`, `RelationSchema`, and evaluation
  retain only relation name, `arity`, and tuple slots. `arguments` is absent
  from the lowered/runtime model; the YAML schema merely permits it as an
  unknown property.
- Recovered and applied the predecessor's exact two-line scratch mutation:

  ```diff
        arguments:
  -        - TaxUnit
           - Person
  +        - TaxUnit
  ```

- The new test passes unmutated (`1 passed`) and fails under only that swap
  (`1 failed`), reporting declared `['Person', 'TaxUnit']` versus expected
  `['TaxUnit', 'Person']`.
- Repo-root collection includes
  `tests/test_income_tax_pipeline_relation_schemas.py::test_income_tax_pipeline_relation_schemas_are_exact`
  among 66 tests. The full repository suite passes `66 passed` with one
  pre-existing unmanifested-module warning.
- The pinned reusable CI workflow runs `python -m pytest -q tests`; exact-head
  Repository Checks run `30432777085` completed that repository-test step
  successfully.

### 3. Dependent hashes, validation, companions, and manifests are current

- SALT whole-file SHA-256 is
  `81d049791e96d949b63b0b7599f88b4767ab4c68d5e05389d49ead70afb063b8`.
  Both itemized proof imports of SALT carry exactly that hash.
- From a canonical-basename exact-head worktree, pinned encoder
  `3869d66d009f52258be35901edbef370e65a399c` with
  `AXIOM_CORPUS_REPO=/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`
  reports `ci_pass=true`, `all_passed=true`, and `errors=[]` for both modules.
- Structural proof validation passes SALT 24/24 and itemized 23/23 with empty
  issue lists.
- The two companions pass 53/53, with two compiled programs and zero failures.
- Focused schema/manifest tests pass 4/4. All four manifest `applied_files`
  hashes equal the exact target bytes.
- The commit chain is linear:
  `f4cc1b88d -> d5d943632 -> 345c22030`. Repair commit `d5d943632`
  changes only the two modules and new test; signing commit `345c22030`
  changes only the two manifests. Every recorded applied-file hash equals the
  corresponding byte hash in signing parent `d5d943632`.
- Both manifest `supersedes` objects exactly identify the prior manifest
  digest/signature. Exact-head `validate / generated-guard` succeeded in
  Repository Checks run `30432777085`, supplying the HMAC-backed guard without
  exposing the local signing secret.

### 4. Repair containment is exact

`git diff --name-status f4cc1b88d..345c22030` contains exactly five paths:

- the SALT module;
- the itemized module;
- `tests/test_income_tax_pipeline_relation_schemas.py`;
- the SALT manifest;
- the itemized manifest.

There are no other paths, reverse ancestry is empty, and `git diff --check`
passes. The full-index binary repair-patch SHA-256 is
`3421c28282f59121be3333f1aaa913b2168c3b115b6e4915c5c748e8f68a303e`.

## Environment and sandbox disclosures

- No PR branch, remote, or GitHub write was made. GitHub access was read-only.
- GitNexus reported the repository unindexed. A contained analyzer attempt
  parsed the disposable checkout but the sandbox denied its global registry
  write to `/Users/maxghenis/.gitnexus/registry.json` (`EPERM`); it was
  interrupted after reporting that failure. Direct exact-diff and source
  analysis supplied the scoped blast-radius evidence.
- A subprocess-list probe was sandbox-denied, and `uv` could not initialize
  its home cache. Raw web cache fetches also missed, while the default pytest
  launcher referenced a removed interpreter. Existing pinned Python
  environments, Ruby stdlib, and the read-only GitHub connector supplied
  successful fallbacks.
- An initial run from a checkout whose basename was not `rulespec-us` produced
  import-resolution failures and overly broad validation scans. Those scans
  were interrupted; all authoritative results above were rerun successfully
  from the exact-head canonical-basename worktree.
- The exact-head `program-artifacts` workflow was still in progress when
  read-only CI state was sampled. It is outside this repair-only re-review;
  Repository Checks/generated-guard and source-staleness/reverse-index had
  completed successfully.

## Recommendation

Approve the repair head `345c22030642cbd37a9fe46877591a8e1df5af7e`.
