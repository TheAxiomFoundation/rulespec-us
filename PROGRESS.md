# PR #1177 repair re-review progress

## State

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
- Recorded a noncanonical-root false start: import resolution failed for the
  companion command, and two validators scanned an overly broad parent tree
  until interrupted. Re-running from a checkout literally named
  `rulespec-us` eliminated both environment artifacts.

## Next

- Inspect engine runtime use of relation `arity` versus `arguments`.
- Run the unmutated and mutated relation-schema test and confirm CI discovery.
- Finish signature/supersedes and signing-ancestry checks.
- Commit the evidence-backed verdict to `REVIEW.md`.
