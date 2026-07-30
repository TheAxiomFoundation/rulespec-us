# PR #1176 round-3 guard probes

## State

Adversarial guard verification is in progress against target
`0e042edd42d29e47e39f5b2f5a3ab7085cffe90b`.

## Done

- Created this isolated local review branch and worktree from the exact target.
- Confirmed the target commit resolves locally.

## Next

- Identify the canonical MCE inputs, outputs, anchor, and existing divergent regressions.
- Run the exact predecessor fixture and three additional integrity probes.
- Mutate the guard off, demonstrate the regressions become wrongly eligible, restore,
  and record an evidence report.
