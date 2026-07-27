# Saver's Credit Revival Progress

## State

- In progress: Notice 2025-67 parameters implemented and validated; pipeline rebuild next.
- Baseline: clean worktree at `6b0773d3f7fa6719f208154f3e609e292ab7abe7` (`origin/main`).
- Constraints: local commits only; no push, GitHub writes, workflow/toolchain edits, or manifest signing.

## Done

- Confirmed the requested worktree, branch, clean status, and base commit.
- Established the required committed progress log.
- Checked for GitNexus graph tooling; it is unavailable in this session, so the audit will use direct repository/corpus inspection and focused validation.
- Recovered both files byte-for-byte from parent `9e6d90dc6ee064727822b2d65941bb95b7754061` of deletion commit `dc7a521fa`.
- Verified recovered SHA-256 values:
  - Pipeline: `9620a6d0efba298addbf7c5a9c77db275bbb2187ddef53d2940641a74e842ea4`.
  - Companion: `2f0ef016c1e78b6df968cda6d75de759b01a3062fbe0d8d758da20d8c7dc9329`.
- Confirmed the branch pins corpus commit `bf97b17baebfdf12601f7c23697524bf5adcdaed`, and the clean corpus checkout is at that exact commit.
- Verified Notice 2025-67 rows 4-5 and section 25B rows 225, 230, 245, 914, and 919 directly in the pinned corpus.
- Added a proof-required Notice 2025-67 parameter module containing all nine tax-year-2026 filing-status/tier limits and a companion value test.
- Passed the module companion test, focused CI validation, proof validation, and zero-missing money-atom validation.

## Next

- Import the nine notice parameters into the saver-credit pipeline and select them by filing status.
- Preserve the recovered fail-closed explicit §§911/931/933 inputs while adding positive add-back coverage.
- Expand the companion across all inclusive tier edges, filing statuses, and separate spouse caps.
