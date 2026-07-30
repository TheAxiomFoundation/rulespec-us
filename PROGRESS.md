# PR #1176 round-3 guard probes

## State

Adversarial guard verification is in progress against target
`0e042edd42d29e47e39f5b2f5a3ab7085cffe90b`. The exact predecessor
direct-relation injection now passes its fail-closed expectations.

## Done

- Created this isolated local review branch and worktree from the exact target.
- Confirmed the target commit resolves locally.
- Created a canonical-basename archive at
  `/private/tmp/pr1176-guard-a91/rulespec-us` and verified the MCE module bytes
  match the target object (`ba01095a...`).
- Materialized the committed injection fixture under the canonical companion
  filename and ran it with the workflow-pinned engine. Both cases passed:
  federal count `1`, integrity `not_holds`, household exclusion `holds`, and
  MCE status `not_holds`.

## Next

- Run three additional integrity probes with explicit relation-member IDs.
- Mutate the guard off, demonstrate the regressions become wrongly eligible, restore,
  and record an evidence report.
