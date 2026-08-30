# 45 CFR part 604 anti-lobbying encoding progress

## State

- Detached worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-45-cfr-604-anti-lobbying-20260830-agent`
- Pinned base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Mode: unsigned feasibility only. The exact `agent-secret` helper succeeds outside this Codex sandbox but fails inside it with `missing unlock password`; no generated file may be applied or recommended for acceptance from this run.
- Retention rule: keep no unsigned generated RuleSpec, test, or manifest in this worktree.

## Done

- Verified the worktree is detached, clean, and based on the required pinned SHA.
- Preserved all existing proposal-security branches and worktrees unchanged.
- Confirmed Appendix B is image-only in the official adapter output and excluded it from semantic encoding.

## Next

- Run the official encoder without `--apply` against the official eCFR corpus artifacts for § 604.100, § 604.110, and Appendix A.
- Reject candidates that expand scope, backdate the operative gate, conflate certification with conditional SF-LLL disclosure, reverse flow-down actors, invent Appendix B semantics, or require an absent 31 U.S.C. § 1352 RuleSpec base.
- For any promising unchanged candidate, run proof validation, adversarial fixtures, and direct tests with the specified real Rust rules engine.
- Delete all unsigned candidates after recording hashes, run identifiers, checks, and rejection reasons.
