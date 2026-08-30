# 2 CFR 25.110 atomic exceptions progress

## State

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-25-110-exc-20260830-codex-1948`
- Base: detached `d58cc0ce67ad891fde4c9061c86a2091bfdd524f` (the required expected `origin/main` commit)
- Fetch: attempted on 2026-08-30, but sandbox DNS blocked `github.com`; the locally tracked `origin/main` matched the required hash exactly.
- Scope: separate generated-only attempts for 2 CFR 25.110(a)(2)(ii) and (iv), with (i) attempted only if all agency judgments remain external facts.
- Excluded: accepted paragraph (iii), OMB class exceptions, generic-identifier reporting, pushes, pull requests, and production actions.
- Output report: `FINAL_REPORT.md` in this worktree.

## Done

- Read the applicable Axiom project, encoder, corpus, and rules repository instructions.
- Loaded the approved `agent-secret` workflow for signed apply without exposing credentials.
- Verified the official corpus worktree and real encoder/runtime locations supplied by the user.
- Created a unique clean detached worktree at the required immutable base.

## Next

- Inspect the exact corpus provision, encoder command surface, signed-run custody conventions, and the accepted paragraph (iii) artifacts without modifying them.
- Run each eligible paragraph through an independent `axiom-encode` session.
- Retain only unchanged signed generated output that passes proof, adversarial fixtures, and direct Rust execution; restore rejected attempts cleanly.
