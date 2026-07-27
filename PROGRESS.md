# New Jersey WFNJ Maximum-Benefit Evidence Progress

## State

Evidence assembly is complete with an honest **4-of-5** verdict:
`provision_rooted`, `conformant`, `exercised`, and candidate-scoped `closed`
hold; `executable` does not. The evidence and hand-checkable golden case are
in `us-nj/wfnj/v1-maximum-benefit-evidence.md`.

The branch is `x2-nj-wfnj-max` in its required isolated worktree, based on the
locally available
`origin/main@ecb057ef35ab47fb055213b42459c42ae63485ef`. Fetch and push attempts
could not resolve `github.com`. The companion oracle branch is
`x2-nj-wfnj-max-grid`; its configured local origin rejected a sandboxed push.
Neither branch is published, so no Draft PR could be opened.

The orchestrator result target
`/Users/maxghenis/TheAxiomFoundation/_closure-sprint/out/x2-nj-wfnj-max.result.md`
is outside this workspace's write grant. The final-channel report is intended
for the orchestrator's output capture; the committed evidence file is the
durable in-repository report.

## Done

- Read the employee-Medicare five-criteria evidence package and PR #1149,
  the r1 rank-4 candidate row and pointers, the closure-sprint constraints,
  root `CLAUDE.md`, and the certified-node schema.
- Created the required worktree and committed this progress log before
  implementation.
- Resolved the corpus frontier at
  `axiom-corpus@db12795577c5809009168982cf8a72fb58440620` by scanning all 691
  inventory files and 142,902 items: one raw occurrence, one unique path, no
  descendants, encoded 1 / excluded 0 / pending 0.
- Verified the exact official Schedule II table
  `[214, 425, 559, 644, 728, 814, 894, 961]`, cap of eight, and `$66` for each
  additional person, including the July 10, 2023 administrative-change
  notice and newer official manual.
- Added ten one-input RuleSpec companion cases for assistance-unit sizes 1
  through 10 at implementation pin
  `5b51301a2d29b099f9fa167d403a1a2eb0921fef`, tree
  `06fef82924e2b29c0b5e8afd79341ae3baabfa2c`.
- Ran the repository-pinned
  `axiom-encode@3869d66d009f52258be35901edbef370e65a399c` and
  `axiom-rules-engine@ffd8213271947b0189a9dd61a055c1e0e78908a0` toolchain
  against an extracted pinned tree: 1 file, 14 cases, all passed.
- Ran repository layout tests after adding the final evidence path:
  `9 passed`.
- Read PolicyEngine's named `nj_wfnj_payment_levels` body at
  `PolicyEngine/policyengine-us@61cc1e63323579deaa4a5070185bdfafcd7e838a`
  and confirmed it performs cap, table lookup, multiplication, and addition
  rather than forwarding a parameter.
- Built and registered the non-population
  `us-nj-wfnj-payment-level-grid` at local companion
  `axiom-oracles@e9fc5ca0f623a97b2fceae561bbf24aefe77dd85`, tree
  `73928393e147a50ce1fa1ecfca9b4e76cb086c9d`.
- Ran the registered grid on PolicyEngine 4.18.9 / PE-US 1.767.3 / core
  3.30.3: 10 matches, 0 mismatches, 0 errors. Receipt SHA-256:
  `5b67928d7b973958af134278e22d23a3a8fe5c5ff947fd56f06e3e1411ccde78`.
- Ran final focused oracle registry/runner tests: `43 passed`; Ruff check and
  new-file format checks passed.
- Built exact released engine v0.1.1 source, compiled a deterministic local
  one-output slice, and ran the size-10 golden request: `$1,093` USD with the
  correct N.J.A.C. trace.
- Proved `executable` false: the repository section module has four derived
  outputs, composition does not prune them, the one-output slice is temporary
  and unpublished, and no NJ WFNJ program artifact exists in the 222 locally
  fetched artifact tags.
- Preserved the launch freeze: no population suite, `certified-nodes.yaml`,
  program/SNAP snapshot, toolchain, CI, CODEOWNERS, or coverage-manifest edit.
- Completed independent fact, scope, schema, forbidden-path, YAML-fence,
  hash, receipt, and golden-run review.

## Next

- Split the Schedule II node into committed one-output source, or add a
  separately reviewed future composition-pruning capability. This sprint does
  not authorize the required refactor/toolchain expansion.
- Land an authorized one-output program source, publish its
  provenance-stamped artifact, and run that artifact through released engine
  v0.1.1 from a fresh stranger path.
- Publish the RuleSpec and companion oracle branches when GitHub access and a
  writable oracle remote are available; then open a Draft PR referencing
  rulespec-us#1135.
- Only after the stranger-path blocker closes may a human change
  `criteria.executable.holds` or consider an attestation. Do not add the node
  to `certified-nodes.yaml` from this evidence package.
