# PR #1177 repair re-review progress

## State

- Review status: complete.
- Verdict: `APPROVE`.
- Review worktree: detached from `345c22030642cbd37a9fe46877591a8e1df5af7e`.
- Canonical-basename validation worktree:
  `.git/review-worktrees/pr-1177-repair-canonical/rulespec-us` at the exact
  target commit.
- Prior reviewed head: `f4cc1b88d1efd8dcca25058695dc1735c0fbb3de`.
- Scope is limited to the claimed repair and containment.
- No PR-branch, remote, or GitHub writes are authorized.
- Final report target: `REVIEW.md` in this ledger worktree.

## Done

- Read the GitNexus PR-review workflow.
- Confirmed both named commits exist locally.
- Created this disposable worktree under `.git/review-worktrees/`.
- Recovered the predecessor's exact mutation: move `TaxUnit` from before
  `Person` to after it in the SALT relation's two-item `arguments` vector.
- Proved exact containment for `f4cc1b88d..345c22030`: the linear two-commit
  range changes only the two modules, the added schema test, and the two
  manifests; `git diff --check` passes. Full binary-patch SHA-256:
  `3421c28282f59121be3333f1aaa913b2168c3b115b6e4915c5c748e8f68a303e`.
- Proved the repaired §164 excerpt is byte-identical to its unique retained
  canonical span: 155 UTF-8 bytes, one body occurrence, both SHA-256
  `880b94a90114834681f926ec10a621c4b243c47c40f2145dbd2d08e89268131b`.
- Confirmed the required corpus checkout is detached and clean at
  `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Ran pinned encoder `3869d66d...` from the canonical-basename root with the
  mandated `AXIOM_CORPUS_REPO`: both modules have `ci_pass=true`,
  `all_passed=true`, and empty errors.
- Ran structural proof validation: SALT 24/24 and itemized 23/23, with empty
  issue lists.
- Ran the two companions with the prior pinned release engine artifact:
  53/53 cases, two compiled programs, zero failures.
- Proved both itemized proof imports of the SALT module carry its exact new
  whole-file SHA-256, `81d049791e96d949b63b0b7599f88b4767ab4c68d5e05389d49ead70afb063b8`.
- Confirmed all four manifest applied-file hashes match exact target bytes,
  and the focused schema/manifest pytest set passes 4/4 (one pre-existing
  unmanifested-module warning).
- Inspected `/Users/maxghenis/axiom-rules/src` at
  `c4b62bdb740d4149f0872783964f917e74cffe42`: `DataRelationRef`,
  lowering, `RelationSpec`, `RelationSchema`, and runtime evaluation retain
  only relation name/arity/tuple slots. The sole `arguments` hit under `src/`
  is unrelated CLI prose; the data-relation schema permits that unknown
  property but does not lower it.
- Ran the new contract unmutated: 1 passed. In isolated scratch, applied the
  predecessor's exact two-line `(TaxUnit, Person)` to `(Person, TaxUnit)`
  reversal and reran the same node: 1 failed, reporting declared
  `['Person', 'TaxUnit']` versus expected `['TaxUnit', 'Person']`.
- Proved CI collection: repo-root `pytest --collect-only -q tests/` includes
  the exact new node among 66 tests; the full repository suite passes 66/66
  with one pre-existing warning. The pinned reusable workflow's repository
  test step runs `python -m pytest -q tests`.
- Confirmed sign-last ancestry: `f4cc1b88d -> d5d943632 -> 345c22030`;
  repair commit `d5d943632` changes only two modules plus the test, while
  `345c22030` changes only the two manifests. Every applied-file digest equals
  its byte digest in signing parent `d5d943632`; both `supersedes` records
  exactly identify the prior manifest digest/signature.
- Read-only exact-head CI confirms Repository Checks and
  `validate / generated-guard` succeeded (run `30432777085`); source
  staleness/reverse index also succeeded (run `30432776846`).
- Recorded a noncanonical-root false start: import resolution failed for the
  companion command, and two validators scanned an overly broad parent tree
  until interrupted. Re-running from a checkout literally named
  `rulespec-us` eliminated both environment artifacts.
- Recorded sandbox/tooling limits: GitNexus indexing parsed the disposable
  checkout but could not write `/Users/maxghenis/.gitnexus/registry.json`
  (`EPERM`) and was interrupted after reporting failure; a subprocess
  inspection attempt was sandbox-denied; `uv` could not initialize its home
  cache; raw web cache fetches failed. Read-only GitHub access, direct source
  inspection, Ruby stdlib, and existing Python environments supplied the
  required evidence.
- Wrote the evidence-backed final report to `REVIEW.md`.

## Next

- No reviewer work remains for this repair-only scope.
