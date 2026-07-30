# PR #1176 round-3 guard probes

## State

Adversarial guard verification is in progress against target
`0e042edd42d29e47e39f5b2f5a3ab7085cffe90b`. The exact predecessor
direct-relation injection and all three explicit-identity completeness probes
now pass their fail-closed expectations.

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
- Added a reproducible explicit-identity raw-engine harness and three review
  fixtures under `review-artifacts/`.
- Rows supplied to both the anchor and local relation with identical member
  identities produced count `2`, integrity `holds`, per-member IPV exclusion
  `holds`, household exclusion `holds`, and MCE `not_holds`.
- A one-for-one supplied membership swap (excluded source member versus
  distinct eligible local member) produced source count `1`, integrity
  `not_holds`, household exclusion `holds`, and MCE `not_holds`; the guard
  catches the attempted exchange because the source projection remains in
  the union.
- An eligible plus IPV-barred pair fed only to the anchor produced count `2`,
  integrity `holds`, per-member IPV exclusion `holds`, household exclusion
  `holds`, and MCE `not_holds`; the derived local scan sees the anchor rows.

## Next

- Mutate the guard off, demonstrate the regressions become wrongly eligible, restore,
  and record an evidence report.
