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

## Next

1. Remove saver-dependent generated artifacts during regeneration.
2. Implement the remaining QBID Rev. Proc. threshold import and fixed 2026
   minimum.
3. Add the section 22 fail-closed boundaries and the section 25A(g)(5)
   double-benefit contract.
4. Regenerate required derived artifacts, run the complete validation battery
   and signing dry-run, and prepare the corrected PR body and completion report.
