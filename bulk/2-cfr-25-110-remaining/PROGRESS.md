# 2 CFR 25.110 remaining atomic exceptions progress

## State

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-2cfr25-110-remaining-20260830-codex-001`
- Detached base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Scope: remaining atomic 2 CFR 25.110(a)(2) exceptions, excluding accepted paragraph (iii).
- Status: initialized; workflow, source, prior-attempt, and validation audits are in progress.
- Output report: `bulk/2-cfr-25-110-remaining/FINAL_REPORT.md`.

## Done

- Attempted `git fetch origin main`; the sandbox could not resolve `github.com`.
- Verified the local `origin/main` is the required `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- Created this unique detached worktree at that exact commit.
- Loaded the approved `agent-secret` workflow without exposing credentials.
- Confirmed `.axiom/repository-structure.yaml` allows task Markdown only under `bulk/` and relocated this ledger accordingly.

## Next

- Finish the canonical generated-output workflow and source custody audit.
- Run paragraph (a)(2)(ii) independently, validate proof/fixtures with the real Rust engine, and retain or reject unchanged signed output.
- Run paragraph (a)(2)(iv) independently and apply the same acceptance gates.
- Attempt paragraph (a)(2)(i) only if the generator can keep the protected-interest judgment wholly external.
- Write and commit the final report with hashes, files, fixtures, proof, Rust results, and paragraph decisions.
