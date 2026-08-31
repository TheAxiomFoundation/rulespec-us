# Progress

## State

- Unique locked detached `rulespec-us` worktree initialized at `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-pappg-uei-sam-20260830-codex-01a05519-195736`.
- A fresh `git fetch --no-tags origin main` was attempted on 2026-08-30 but the sandbox could not resolve `github.com`; the existing `origin/main` ref and commit object exactly match the required immutable hash.
- The pre-existing NSF UEI/SAM worktree and axiom-corpus PR #631 remain untouched.
- Official-source and exact-base dependency audits are complete.
- Generation, signed apply, and real-Rust proof work are pending; `agent-secret` currently reports that the existing dedicated keychain lacks its stored unlock password.

## Done

- Read the applicable Axiom and repository instructions.
- Verified that the primary checkout is dirty and diverged and left it unchanged.
- Verified the remote URL, detached HEAD, exact base object, clean materialized checkout, and worktree lock.
- Selected `OUTPUT.md` as the committed final-report file, matching the task-family convention.
- Verified corpus worktree `129dae01c6f7a4787bc7678d4a97a478f3934d9f` and exact citation `us/guidance/nsf/pappg/24-1/chapter-i/uei-and-sam`.
- Verified source-as-of `2026-08-30`, expression/effective date `2024-05-20`, provision id `67fd65f6-4a03-5dd1-9c34-803b4b18d6d8`, official HTML SHA-256 `a8f98d21d424ab919458571a268b50c77f7c42164fecfb4bdbe3a94c64197d29`, and full normalized JSONL SHA-256 `a16f78fee0769493e9ba11d4e7c154b84536158fb6091cef8721b8f8fc482a89`.
- Confirmed the actor/linkage split: proposer/proposing organization duties bind to that entity; every named subrecipient must independently bind its own UEI and Research.gov setup; the named-subrecipient SAM treatment is permission to lack full SAM and never an exemption for the proposer.
- Confirmed that applicant obligations and NSF submission/approval blocking behavior must be distinct outputs.
- Exhaustively confirmed that the exact base contains no 2 CFR Part 25 RuleSpec modules or encoding manifests. Any generated dependency on such a module will be rejected fail-closed.
- Queried the required `agent-secret` interface without exposing values; signed apply cannot proceed unless its existing keychain unlock record is restored.

## Next

- Run actual `axiom-encode` generation with the official corpus, canonical `us/` root, acceptance context, and real Rust engine.
- Retry `agent-secret`; only perform signed apply if the required key can be retrieved through that interface.
- Retain only unchanged generated artifacts that satisfy all requested proof, fixture, and direct Rust cases.
- Commit `OUTPUT.md`, finalize this file, and leave the detached worktree clean without pushing or opening a PR.
