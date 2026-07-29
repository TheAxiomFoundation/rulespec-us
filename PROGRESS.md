# PR #1174 Repair-Round Re-review Progress

## State

- Review branch: `review/pr-1174-repair-b8ba5db`.
- Disposable worktree:
  `.git/review-worktrees/pr-1174-repair-b8ba5db`.
- Requested PR head:
  `b8ba5dbe7d4c6f07eaada84bbe035821743d7a77`.
- Comparison base:
  `origin/main` at `af6c57d618acff5cb268d345653ea3e4cf64feb6`.
- Repair commits: `5fdcce258` and `b8ba5dbe7`.
- Scope: repair round plus containment only.
- Status: repair/containment verification in progress; verdict not yet
  determined.

## Done

- Read the GitNexus PR-review procedure.
- Confirmed the requested head object exists locally at the full SHA above.
- Preserved the dirty primary checkout and the author's existing branch worktree.
- Confirmed `PROGRESS.md` is absent from the requested head tree.
- Created this isolated local review branch and disposable worktree without
  changing the PR branch, any remote, or GitHub.
- Confirmed `origin/main` is the exact merge base of the requested head.
- Inventoried the repair-only diff: 9 paths, 152 insertions, 123 deletions;
  the changes are limited to the two waiver ledgers, removal of the leaked
  branch `PROGRESS.md`, the 6012 module/companion, and four modern manifests.
- Inventoried the full PR diff: 15 intended statute, companion, index,
  waiver-ledger, and manifest paths; both full and repair diffs pass
  `git diff --check`.
- Reviewed both repair commits and confirmed the claimed hash/binding,
  positive-case, waiver-removal, ledger-removal, and manifest-only edits are
  the only repair-round changes.
- Attempted the GitNexus skill's required index refresh. Parsing completed
  locally, but registration was sandbox-blocked at
  `~/.gitnexus/registry.json`; graph queries therefore could not select this
  unregistered worktree. Preserved the partial index at
  `/private/tmp/pr1174-repair-gitnexus-partial` and continued with direct
  repository impact analysis.
- A policy-blocked `rm -rf` cleanup attempt made no filesystem change; the
  partial index was moved instead.
- Read the exact shared workflow blob at
  `TheAxiomFoundation/.github@b380085c` through the read-only GitHub
  connector. Confirmed pending evidence is loaded from the protected base,
  `require_pending_evidence` compares that evidence to current module bytes,
  and `waiver_module_is_unchanged` emits skip-list entries only for unchanged
  modules.
- Reproduced the workflow's exact `approval_growth` function against
  `origin/main` and the requested head: result `False`; the only state changes
  are removal of `6012.yaml:active` and `63/c.yaml:pending`, with no additions
  or metadata changes.
- Confirmed protected-base §63(c) evidence attests `sha256:53a218...` while
  the repaired module is `sha256:fbc6f30c...`; retaining the pending waiver
  would therefore fail exact-evidence validation.
- Simulated the waiver skip-list against the PR diff. All four changed modules
  (§6012, §63(c), §63(c)(6), and §67(h)) are absent from the head waiver set
  and are selected for validation; the obsolete §63(c) fingerprint record is
  absent.
- Audited every moved input binding across the requested tree. Each of the
  four old `us:statutes/26/63/c#input.*` IDs has zero occurrences; each new
  `us:statutes/26/63/c/6#input.*` ID has 16 occurrences (5 in the §6012
  companion, 6 in the parent §63(c) companion, and 5 in the extracted
  companion).
- Confirmed the new TY2025 joint-return case satisfies every
  26 USC 6012(f)(2) element: joint entitlement, $20,000 combined gross income
  below the $31,500 joint standard deduction, same household, no separate
  return, and neither spouse in the §63(c)(5) branch. Checked current official
  House U.S. Code §§6012 and 63 text; IRS Publication 501 independently
  corroborates the 2025 amount.
- Reconfirmed containment: the full diff contains exactly the 15 intended
  manifest/index/waiver/§6012/§63/§67 paths, the repair diff contains exactly
  9 claimed paths, whitespace checks pass, and the requested tree contains no
  `PROGRESS.md`.
- Independently computed the requested-tree §63(c) digest and confirmed both
  §6012 `standard_deduction` proof imports equal
  `sha256:fbc6f30c840556e4303536a7f2f0bd47bb3612cc2beb30e0bb4ac2f6ac45bbba`.
- Ran the focused manifest suite:
  `tests/test_encoding_manifests.py` plus
  `tests/test_bulk_applied_artifacts.py`; 37 passed with one expected
  unmanifested-backlog warning.
- Verified all eight applied-file hashes in the four modern manifests, the
  presence/shape of all four HMAC-SHA256 signatures, and newest-manifest
  selection: the new modern §6012 and §63(c) manifests both supersede their
  untouched legacy-layout counterparts.
- The local HMAC signing key is not available, so signature values cannot be
  independently recomputed; content-hash, schema, selection, and repository
  manifest tests are green.
- Confirmed exact pinned dependency trees:
  `axiom-encode@3869d66d`, `axiom-rules-engine@ffd821327`, and
  `axiom-corpus@8af592162`.
- Ran one pinned four-module `validate --skip-reviewers --json` invocation in
  the canonical sibling checkout at exact head `b8ba5dbe7`: §63(c),
  §63(c)(6), §67(h), and §6012 each report `ci_pass: true`,
  `all_passed: true`, and `errors: []`.
- Ran the four-file companion batch in that same canonical layout: 4 files,
  17 cases, 4 compiled programs, zero failures.
- An earlier companion attempt from the nested ledger path was noncanonical
  and failed module resolution before executing the requested batch (only
  3 programs/11 cases); the exact-head canonical rerun above is the
  authoritative result.
- Read the existing GitHub Repository Checks run `30404017228` for this head.
  Waiver-change guard, generated guard (including secret-backed manifest
  authentication), module validation, companions, and proof validation all
  passed. Its only failure was full oracle coverage under the then-current
  `axiom-oracles@678dd840`, which lacked exactly the two PR mappings.
- Confirmed current `axiom-encode/main` now pins
  `axiom-oracles@f8ea6027`; that merge contains exact classifications for
  §63(c)(6) and §67(h). Reproduced the shared workflow's full-coverage command
  against the exact head with that current mapping: exit 0, no unmapped or
  untested-comparable outputs. A fresh Repository Checks execution would
  therefore clear the historical transient oracle-pin failure.
- Creating a detached oracle worktree was sandbox-denied at the source
  checkout's git metadata; a read-only local clone under `/private/tmp`
  provided the exact `f8ea6027` tree for the successful rerun.

## Next

- Run pinned validation, companion, and manifest checks.
- Assemble and commit the final evidence report and verdict.
- Write and commit the final evidence report to `WORKER-REPORT.md`.
