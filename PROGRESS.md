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
- Verdict: `REQUEST-CHANGES`.

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
- Verified the pinned corpus checkout is clean at `bf97b17baebfdf12601f7c23697524bf5adcdaed`, exactly matching `.axiom/toolchain.toml`; byte-checked the retained page rows and source PDF identity.
- Confirmed `$388` MUA, `$265` BUA, `$27` telephone, the `> $20` LIHEAP threshold, 12-month lookback, one-allowance assignment, BUA exclusions, actual-cost categories, continuation, shared-residence agreement, and non-proration text against the retained SC manual.
- Found that page 165's shared-residence agreement judgment is orphaned: no page-159 entitlement or amount consumes it.
- Added a temporary adversarial disagreement case in a clean exact-head probe. With shared residence true, agreement false, and separately billed heat true, the agreement judgment was `not_holds` but the local and federal allowance remained `$388`; the companion failed as expected. Restored the probe and proved it clean.
- Found an unsupported actual-cost exclusion: page 165 applies `household_utility_costs_included_in_rent_payment` to actual costs even though the retained text applies it only to BUA.
- Found that page 163 does not encode the source's express “During the year” condition on incurred heating/cooling costs.
- Confirmed no PolicyEngine or FNS-table value was used as policy authority for these pages.

## Next

- Review federal utility-hook structural compatibility and current-scope inertness.
- Verify manifests, reverse index, repository hygiene, and behavior neutrality for existing suites.
- Write and commit the final report to `REVIEW.md`.
