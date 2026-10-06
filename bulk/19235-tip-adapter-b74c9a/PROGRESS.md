# Progress

## State

Rejected after generation transport failure. Two fresh, isolated runs of the
task-specific pinned `axiom-encode` reached the exact corpus leaf and committed
encoding brief, but DNS/transport failed before the model returned any token or
candidate. Apply was blocked before signing, and no generated policy artifact
was installed or retained.

## Done

- Resumed the existing detached worktree at
  `78e6ca4b34fba519f042a0eb9347e57ad8bda003`; its live upstream base remains
  `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- Re-read the committed `ENCODING_BRIEF.md`, prior `OUTPUT.md`, source custody,
  repository instructions, and exact target/source distinction before running
  the encoder.
- Re-verified the clean official corpus worktree at
  `129dae01c6f7a4787bc7678d4a97a478f3934d9f`, including the requested guidance
  record, dynamic-list flags, OLRC §19235 and §19235(1) records, and the
  `2022-08-09` source-credit date.
- Re-verified that the required base has no reusable
  `us/statutes/42/19235` RuleSpec module, so an acceptable adapter must consume
  an explicit external statutory-prerequisite fact.
- Resolved the apparent pin discrepancy in favor of this lane's task-specific
  NSF toolchain: actual `axiom-encode` 0.2.1200 at
  `3869d66d009f52258be35901edbef370e65a399c` and actual Rust engine at
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`.
- Ran two actual `codex:gpt-5.5` `encode --apply` attempts with fresh isolated
  output roots. Run IDs were `a8afeb11` and `ac44a55b`; both returned zero
  tokens and failed while reconnecting to `chatgpt.com`.
- Used the approved `AXIOM_ENCODE_APPLY_SIGNING_KEY` only through those
  unchanged `axiom-encode encode --apply` processes. No inspection command
  referenced its value; post-attempt diagnostics explicitly removed it from
  their child environments. It was not printed, logged, hashed, inspected,
  copied, or rotated.
- Confirmed both apply events reported `applied_files: []`; the target
  RuleSpec, adjacent companion test, signed manifest, policy/apply repair
  output, compiled artifact, and runtime request/result files are absent. Each
  temporary output root retains only its hashed failure repair manifest.
- Confirmed the target worktree's canonical `us/` policy tree and all tracked
  tool/corpus content remain unchanged and Git-clean. The encoder wrote its
  normal ignored run logs only. Accepted worktrees and axiom-corpus PR #631
  remain untouched.
- Wrote the complete run/source/tool/decision record to `OUTPUT.md`.

## Resume condition

After DNS and Codex transport are available, rerun the same task-specific
pinned encoder from a new isolated output and run-log root, using the unchanged
brief and canonical policy root ending in `/us`. Retain output only if signed
apply installs byte-identical generated files and the complete proof,
generated-fixture, and direct-Rust adversarial matrix passes. Otherwise remove
only the exact generated files listed by the apply manifest and keep the
decision rejected.
