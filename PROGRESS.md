# PR #1176 round-3 re-review progress

## State

- Review complete at exact requested head
  `0e042edd42d29e47e39f5b2f5a3ab7085cffe90b`.
- Verdict: `APPROVE`.
- PR branch `fed-parity/ca-bbce` is read-only for this review.
- Review-only commits and artifacts live on local branch
  `review/pr-1176-round3-audit-019fb12a` under `.git/review-worktrees/`.
- Final output file: `WORKER-REPORT.md` in this ledger worktree.
- Canonical exact-head archive:
  `/private/tmp/pr1176-round3-suite.8k45tj/rulespec-us`.
- Exact pinned engine build:
  `/private/tmp/pr1176-engine-ffd.YywOin/axiom-rules-engine`.

## Done

- Read the GitNexus PR-review workflow.
- Resolved the exact local PR head and isolated review bookkeeping from the PR
  surface.
- Established the requested pinned corpus path:
  `/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`.
- Confirmed ancestry `e111d8b8d` -> `01ec7fb5e` (ledger drop) ->
  `0e042edd4` (four-manifest re-sign).
- Ran the canonical companion gate: 54/54 cases, three test files and three
  compiled programs, zero failures.
- Materialized the engine-only attack fixture under a canonical companion
  basename and ran it: 2/2 cases, zero failures.
- Validated the federal state-plan, California MCE, and California benefit
  modules: all report `ci_pass=true`, `all_passed=true`, and zero errors.
- Proof-validated the same modules: 41 atoms checked, zero issues.
- Ran manifest, repository-layout, reverse-index, and manifest-provenance
  contracts: 26 passed; the single warning is the unchanged 19-module
  unmanifested backlog.
- Independently audited the static surface: exactly two new rule IDs since
  pre-round-3 `686d413c`, both private; no removals; both fail-closed MCE
  outputs consume the guard. The 14-path merge-base diff is contained to the
  intended CA, ProgramSpec, federal state-plan, four manifests, reverse index,
  and repair report; `git diff --check` is clean and PR head tracks no
  `PROGRESS.md`.
- Verified all four manifests have composition attestations, exact
  supersession hashes, and seven applied-file hashes matching both ancestor
  `01ec7fb5e` and head. ProgramSpec citation is exactly
  `programs/us-ca/snap/fy-2026`.
- Verified the 17 merged axiom-oracles PR #424 mapping rows are byte-identical
  on oracle main and contain neither helper.
- Completed the independent federal blast audit:
  - Arizona base/overlay companions pass 6/6 and their complete canonical
    request/response transcripts are byte-identical.
  - New York base/overlay companions pass 12/12 with byte-identical complete
    transcripts.
  - Raw compiled artifacts differ only by the new private helper plus its
    evaluation-order entry; removing those inert entries yields
    byte-identical artifacts.
  - Federal exact-head companion passes 7/7 and validation has zero findings.
- Completed all guard probes at the exact target:
  - Direct eligible-row injection and attempted derived-scalar spoof both
    produce `(count=1, integrity=not_holds, exclusion=holds,
    MCE=not_holds)` via the cardinality guard.
  - Equal-count rows on both surfaces produce
    `(2, holds, holds, not_holds)` because the same-row IPV scan catches the
    barred member.
  - A distinct eligible member exchanged one-for-one for the barred anchor
    member produces `(1, not_holds, holds, not_holds)` because the source
    projection remains in the local union and the cardinality guard catches
    the attempted swap.
  - Inconsistent eligible+IPV rows fed only to the anchor produce
    `(2, holds, holds, not_holds)` because both rows project into the local
    per-member exclusion scan.
- Mutated only the integrity helper to `formula: true`. With lawful
  expectations retained, the two divergent cases fail 0/2 with six targeted
  assertions and both unsafe tuples become `(1, holds, not_holds, holds)`;
  those unsafe expectations pass wrongly 2/2. Restoration returns the module
  to target SHA-256 `ba01095a...`, empty target diff, and lawful 2/2 green.
- Attempted the required GitNexus index. The sandbox denied its write to
  `/Users/maxghenis/.gitnexus/registry.json`; direct source, git, and compiled
  artifact checks are being used instead.
- Recorded one additional sandbox denial: `apply_patch` rejected a disposable
  `/private/tmp` fixture edit. The identical edit succeeded in the writable
  review ledger area, and no test was skipped.
- Reconfirmed through the read-only GitHub connector that open PR #1176 still
  points to the exact reviewed head and 14-file surface.
- Wrote the complete evidence and sandbox-disclosure report to
  `WORKER-REPORT.md`.

## Next

- No review work remains. Preserve the local ledger commits and report the
  verdict; do not write to the PR branch, a remote, or GitHub.
