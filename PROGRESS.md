# PR 1004 fix-wave progress

## State

- Working locally on `fed-parity/credits`; no pushes or GitHub writes.
- The starting checkout was clean at reviewed head `e9b57e02`.
- A refresh of `origin/main` and `origin/fed-parity/revproc` was attempted, but
  this environment could not resolve `github.com`. Cached remote-tracking refs
  are available; cached `origin/main` is 18 commits ahead of the PR merge base.
- Scope is QBID, the elderly/disabled credit, and the Lifetime Learning Credit.
  No `us/statutes` edits are permitted.
- The saver pipeline is split out; its two source files remain byte-for-byte
  available in the review scratchpad for the follow-up branch.
- The retained implementation is complete and validates without PR #1009
  present. The requested no-hardcode threshold fallback remains an explicitly
  attested runtime boundary until that dependency lands.

## Done

- Read `review-1004-VERDICT.md` in full and mapped all nine findings to the
  adjudicated fix program.
- Confirmed that the saver pipeline and its companion test are tracked on this
  branch and that the worktree had no pre-existing changes.
- Preserved `savers_credit_pipeline.yaml` and its companion test with SHA-256
  hashes `9620a6d0...ea4` and `2f0ef016...329`, then removed both from this
  branch with `git rm`.
- Guarded the final QBID output against corporations and added the active-QBI
  minimum counterexample; the targeted companion and proof checks pass.
- Replaced the imported `{1,4}` QBID width selector with a local five-status
  rule and added the surviving-spouse band-top counterexample; targeted proof
  validation and all 13 QBID cases pass.
- Added the required only-qualified-business aggregation attestation and a
  false-attestation counterexample. The QBID module passes static validation,
  23 proof atoms, and all 14 companion cases.
- Confirmed that directly importing the PR #1009 Rev. Proc. module breaks
  standalone validation, then applied the instructed fallback: retained the
  runtime threshold, added an official-return-category attestation, validated
  that category against all five filing statuses without hard-coding threshold
  dollars, guarded the final result, and added the wrong-category joint case.
- Removed the caller-supplied COLA and encoded the unadjusted statutory
  $1,000/$400 bases for 2026 with the pre-2027 proof boundary.
- Guarded the section 22 output on an empty section 104(a)(4) payment relation
  and added the Foreign Service/Social Security counterexample. Static
  validation, all 3 proof atoms, and all 11 companion cases pass.
- Added the required section 22 at-retirement permanence attestation and a
  false-attestation disability case. Static validation, all 5 proof atoms, and
  all 12 companion cases pass.
- Added the section 25A(g)(5) net-expense attestation to both LLC boundaries
  and a false-attestation double-benefit case. Static validation, all 6 proof
  atoms, and all 13 companion cases pass.
- Removed the saver manifest, regenerated the source reverse index, and
  reconciled the oracle pending ledger (7 saver outputs removed, 5 new QBID
  helpers added; 2,314 declarations applied with no stale entries).
- Ran the pinned complete battery: 3/3 static validations, 38/38 proof atoms,
  and 40/40 companion cases pass. Reverse-index, oracle-ledger,
  `git diff --check`, saver-byte, and no-`us/statutes` checks pass.
- Ran repository pytest: 66 passed and only the expected signed-manifest sync
  test failed for the three changed retained modules.
- Ran the requested signing dry-run: it selected exactly 3 manifests covering
  6 files and wrote nothing.
- Completed two independent read-only reviews plus a focused fallback
  re-review; no actionable policy, schema, test, or scope findings remain.

## Next

1. Have an authorized signer re-sign the QBID, elderly/disabled, and LLC
   pipeline/test pairs before merge.
2. Replace the temporary QBID threshold amount/category boundary with the
   encoded PR #1009 import after that module lands.
3. Restore the preserved saver files only on a follow-up branch after its
   Notice 2025-67 provenance and section 911-addback blockers are resolved.
