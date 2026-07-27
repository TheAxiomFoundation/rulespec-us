# PR #1139 blind adversarial review

## State

- Review worktree: `.git/review-worktrees/pr-1139-bec5142`
- Review branch: `review/pr-1139-bec5142`
- Pinned PR head: `bec5142d32a84bc6a8bb51ed5d96682f6b00cbf7`
- Remote verification: `git ls-remote` is blocked because the sandbox cannot resolve `github.com`; local branch and remote-tracking ref both match the pinned head. The read-only GitHub connector independently reports identical two-commit comparisons for remote branch `fed-parity/snap-sc` and exact SHA `bec5142d32a84bc6a8bb51ed5d96682f6b00cbf7`.
- PR merge base: `6b0773d3f7fa6719f208154f3e609e292ab7abe7` (`origin/main` and GitHub connector).
- PR-only commits: `d5394fc03` (encode) and `bec5142d3` (sign manifests).
- PR-only files: ten expected files (six page YAML/test files, three manifests, one reverse index).
- Exact-head execution checkout: `.git/review-worktrees/pr-1139-bec5142-exec/rulespec-us` (detached at the pinned head; canonical basename required by the rules engine).
- Verdict: pending.

## Done

- Confirmed the pinned object exists locally and is a commit.
- Confirmed local `fed-parity/snap-sc` and `origin/fed-parity/snap-sc` refs both resolve to the pinned head.
- Created this disposable worktree directly from the pinned object without touching the dirty primary worktree.
- Confirmed through the read-only GitHub connector that PR #1139 is the SC SNAP utility-page PR, that the branch and exact SHA have the same two-commit comparison, and that the connector's ten-file list exactly matches the local diff.
- Established the immutable PR range `6b0773d3f7fa6719f208154f3e609e292ab7abe7..bec5142d32a84bc6a8bb51ed5d96682f6b00cbf7`.
- Attempted the PR-review skill's GitNexus path: graph tools are unavailable, and the no-install CLI status probe hung until interrupted; review will use direct dependency/index inspection and record this tooling limitation.
- Ran the mandated companion command at the exact head: all three files and all 25 cases passed.
- Mutation-tested `mandatory_utility_allowance_amount` from 388 to 389: the suite failed with 10 mismatches, including the parameter, local allowance, and federal hook.
- Mutation-tested the BUA assignment guard by flipping `not household_entitled_to_mandatory_utility_allowance`: the suite failed with 11 mismatches across all three companion files, including BUA loss and simultaneous MUA/BUA.
- Restored both mutations with patches, reran all companions (25/25 pass), and proved the detached execution worktree is clean and byte-identical to the pinned head for both mutated files.

## Next

- Byte-check page values, conditions, and exclusions against the pinned corpus.
- Review federal utility-hook structural compatibility and current-scope inertness.
- Verify manifests, reverse index, repository hygiene, and behavior neutrality for existing suites.
- Write and commit the final report to `REVIEW.md`.
