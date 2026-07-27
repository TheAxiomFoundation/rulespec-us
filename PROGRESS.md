# Saver's Credit Revival Progress

## State

- In progress: implementation and mutation proof complete; reverse-index/repository gates next.
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
- Replaced caller-supplied thresholds with nine notice imports and explicit joint/head-of-household/all-other selectors.
- Preserved explicit, no-default §§911/931/933 add-back inputs and added a positive §911 threshold-crossing case.
- Preserved separate primary/spouse $2,000 caps and added a both-spouses-over-cap case.
- Expanded the pipeline companion to 25 cases, including every exact and one-dollar-over tier edge for single, joint, and head-of-household filers; MFS and surviving-spouse category checks; and eligibility screens.
- Passed the 25-case companion, focused CI validation (using a temporary canonical checkout alias for this `wt-savers` worktree name), proof validation, and zero-missing money-atom validation.
- Mutation proof: changing the first comparison from `<=` to `<` produced 8 assertion failures across the exact 50-percent-limit cases (single, joint, head of household, MFS, and surviving spouse); restoring `<=` returned all 25 cases to green.

## Next

- Regenerate/check the corpus-provision reverse index and run focused repository tests.
- Inventory new output legal IDs, write `WORKER-REPORT.md`, and finalize the committed progress state.
