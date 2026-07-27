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
- Final report: `REVIEW.md`.
- Review status: complete.

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
- Ran strict validation for all three modules with the pinned encoder; all passed.
- Parsed all three manifests: each attests exactly its page YAML and companion, their union is exactly the six requested files, all six recomputed hashes match, generated-output hashes match the page YAMLs, import hashes match, and the pinned clean encoder commit is an ancestor/equal toolchain provenance match.
- Local secret-backed HMAC verification was unavailable because the signing key is intentionally absent. Read-only GitHub check logs at the exact head show the protected-base `guard-generated` job received the masked secret and passed all changed RuleSpec manifests.
- Verified the two-commit ancestry is linear (`base -> content/index -> manifests`) and the PR range contains only the six page files, three manifests, and reverse index—no program spec, toolchain, workflow, CODEOWNERS, dependency, report, or ledger paths.
- Regenerated/checked the reverse index: it is current at 4,233 provisions, 5,069 edges, and 4,484 modules; its PR diff is only the expected nine-line page-159 citation mapping.
- Ran the manifest and reverse-index hygiene tests with an available repository-compatible pytest environment: 9 passed. The pinned encoder environment lacks pytest and the system wrapper has a broken interpreter path; this was an environment limitation, not a test failure.
- Reviewed page 163 and 165 against their earlier encode: the PR composes previously disconnected page-164 prerequisites/exclusions, adds verification and precedence, and replaces coarse local MUA/BUA inputs with authoritative outputs. The retained agreement/non-proration judgments remain disconnected; page 165 also adds the unsupported rent bar noted above.
- Verified the page-159 mapping to the federal standard, limited, and individual hooks. Exhaustive boolean analysis found no overlap among its conditional MUA, BUA, and telephone values; the federal sum therefore carries at most one of those three values, and full fixed amounts preserve non-proration.
- Found a separate activation hazard: already-scoped page 369 sets the same federal individual hook to an unconditional stale `$33`. The pinned engine resolves duplicate `sets` relations in import/scope order; normal sorted activation of page 159 leaves page 369 later, so the stale setter would overwrite the new conditional `$27` and stack `$33` onto MUA/BUA or no-utility cases.
- Confirmed the collision with a disposable exact-head wrapper importing page 159 then page 369: with empty inputs, the federal individual hook evaluated to page 369's unconditional `$33`. Deleted the probe files and proved the exact-head checkout clean.
- Treated omission of page 159 from the program spec as deliberate and not a defect. Actual verified utility dollars also correctly remain outside the three standard-allowance hooks and must stay in the separate shelter-cost term when activation is designed.
- Proved current inertness: no program imports page 159, no federal module imports an SC output, no module outside these pages consumes a changed output, and the only active SC program scopes legacy page 163/page 165 without using them in either selected output's dependency closure.
- Composed the SC program at base and head: emitted roots are byte-identical with SHA-256 `a660a49b575dcce18a688309b385fb4bcb158c320a451181f9fa0e6c9273777b`.
- Compiled base and head and traversed the selected `snap_eligible`/`snap_benefit` closure: both closures contain the same 77 items with no additions, removals, or changed semantics. The head adds/changes dormant utility judgments only.
- Wrote the final evidence-backed report to `REVIEW.md`.

## Next

- None; review complete.
