# Progress

## State

- Transport-blocked before RuleSpec generation after three reviewed Codex
  gpt-5.5 encode --apply invocations with unchanged encode arguments.
- Detached lane HEAD remains
  5bd899c572dc473254579898309994d0cc6396c3 on the required and
  user-confirmed live base d58cc0ce67ad891fde4c9061c86a2091bfdd524f.
- The approved AXIOM_ENCODE_APPLY_SIGNING_KEY environment variable was present
  for the encoder processes. Its value was never inspected, printed, logged,
  hashed, or rotated, and it was not used for another command or operation.
- The prior keychain and fresh-fetch blockers are superseded: no keychain
  lookup was attempted, and the user explicitly confirmed the live base.
- Each model trace ended with a ChatGPT response-stream disconnection after the
  built-in reconnect loop. A direct diagnostic then failed to resolve
  chatgpt.com.
- All three runs returned zero RuleSpec bytes,
  standalone_validation_success=false, applied_files=[], and
  apply_blocked_generation.
- No main RuleSpec, companion test, signed manifest, index change, proof,
  fixture, oracle, or Rust result was generated or retained.
- Executable retention decision: all six atomic outputs rejected.
- Existing accepted work, other worktrees, branches, and axiom-corpus PR #631
  remain untouched.

## Done

- Re-read and reconciled the committed PROGRESS, FINAL_REPORT,
  ENCODING_BRIEF, exact continuations, repository instructions, and toolchain
  procedures.
- Reverified the clean detached lane, exact merge base, canonical /us policy
  root, and absence of a reusable us:statutes/42/19232 module.
- Preserved the unchanged item 3 positional source and exactly six audited
  continuation files for item 4 and FAQ questions 3, 5, 6, 7, and 8.
- Reconfirmed the four separate concepts: actual current-participation
  ineligibility; same-project senior/key individual certification;
  same-project AOR organizational certification; and annual PI/co-PI duty for
  at least one linked active NSF award made on or after 2024-05-20.
- Reconfirmed the strict greater-than 2024-05-20 award ineligibility edge,
  inclusive annual-duty edge, proposal-only project limitation, and
  fail-closed proposal-certification gate through 2025-12-01.
- Used three fresh output roots, isolated databases, --no-sync, the pinned
  axiom-encode 0.2.1200, the pinned corpus, the canonical /us root, and the
  pinned real Rust engine path.
- Verified all three context manifests contain only the unchanged brief and
  six continuations and record exactly the seven authorized corpus paths.
- Preserved run IDs 545f312a, 199fc3bb, and 2c12f1cb with prompt, context,
  trace, repair, database, and run-log hashes in bulk/FINAL_REPORT.md.
- Relocated the first two encoder-created untracked run logs into their
  matching isolated roots without changing their hashes; the third log was
  isolated from process start.
- Confirmed the pinned encoder has no supported signed-apply resume, offline
  replay, or cached-response recovery path and did not switch backend, model,
  or signing method.
- Updated the configured final report with source, date, scope, custody,
  per-rule rejection, fixture/proof/Rust non-results, and exact unblock
  evidence.

## Next

- Restore DNS/transport access from the pinned Codex backend to
  chatgpt.com/backend-api/codex/responses.
- Rerun the exact sanitized command in bulk/FINAL_REPORT.md with a new isolated
  output root and AXIOM_ENCODE_RUN_LOG_DIR inside that root.
- Do not change the source set, encoding brief, Codex gpt-5.5 backend, toolchain
  pins, /us policy root, or approved environment signing path.
- If generation succeeds, require generated/applied byte equality, no
  auto-repair or auto-deferral markers, signed-manifest and guard-generated
  success, strict proof, all generated fixtures, and the full direct pinned
  Rust adversary matrix before retaining any atomic output.
- If any atomic output fails those gates, restore its complete generated bundle
  rather than manually editing generated artifacts.
- No commit, push, PR, deploy, or publish action is authorized.
