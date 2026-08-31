# 2 CFR 25.110 remaining atomic exceptions progress

## State

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-2cfr25-110-remaining-20260830-codex-001`
- Detached base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Scope: remaining atomic 2 CFR 25.110(a)(2) exceptions, excluding accepted paragraph (iii).
- Status: source/workflow custody audited; paragraph-specific generation briefs are next.
- Output report: `bulk/2-cfr-25-110-remaining/FINAL_REPORT.md`.

## Done

- Attempted `git fetch origin main`; the sandbox could not resolve `github.com`.
- Verified the local `origin/main` is the required `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- Created this unique detached worktree at that exact commit.
- Loaded the approved `agent-secret` workflow without exposing credentials.
- Confirmed `.axiom/repository-structure.yaml` allows task Markdown only under `bulk/` and relocated this ledger accordingly.
- Verified the clean official corpus checkout at `129dae01c6f7a4787bc7678d4a97a478f3934d9f` and the exact `us/regulation/2/25/110` row.
- Recorded source custody: provisions JSONL `dc4a3cf6e561f7c4923d4669ad4da126212b06aa9d13c88784d5a85c2d763fb9`, raw eCFR XML `6afb0be190a4b937ee1cffd49ffdff1289554225fb5c6acb26ba560cf8ffc52d`, and encoder-resolved section body `444167ba073d496b99d3700ab9a32919b58bb9931eaff1ff2012a61d4b4ca1fd`.
- Verified clean detached toolchains: `axiom-encode` `3869d66d009f52258be35901edbef370e65a399c` (version `0.2.1200`) and Rust engine `ffd8213271947b0189a9dd61a055c1e0e78908a0`.
- Audited accepted paragraph (iii) read-only and confirmed its generated module/test/manifest paths will not be copied, modified, or merged into these attempts.
- Fixed the cross-cutting acceptance model: qualification is separate from an actual Federal-agency grant; UEI and SAM scopes remain separate; applicant/recipient/subrecipient and award/subaward facts remain transaction-specific.
- Confirmed paragraph (i) is attemptable only with `agency_determines_must_protect` and the national-security, foreign-policy, or personal-safety route supplied as external facts.
- Confirmed the requested `2024-10-01` effective gate is a task-specific fail-closed narrowing; the local eCFR XML cites the final rule but does not itself state that date.
- Checked the signing handle `agent/axiom-encode-apply-signing-key` / `axiom-foundation`; `agent-secret` is currently blocked because the existing dedicated keychain's login-keychain unlock record is missing. No bypass was attempted.

## Next

- Create and hash three paragraph-specific generation briefs outside the rules repository.
- Run paragraph (a)(2)(ii) independently, validate proof/fixtures with the real Rust engine, and retain or reject unchanged signed output.
- Run paragraph (a)(2)(iv) independently and apply the same acceptance gates.
- Run paragraph (a)(2)(i) independently with all protected-interest judgment facts external.
- Retry signed apply only through `agent-secret`; reject and restore any candidate that cannot be signed unchanged.
- Write and commit the final report with hashes, files, fixtures, proof, Rust results, and paragraph decisions.
