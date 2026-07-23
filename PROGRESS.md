# 2026 indexed-value policy module progress

## State

Corpus and repository-convention audit is in progress on
`fed-parity/revproc`, based on `origin/main`
`c86b2f62511b7ff9d5351c98ca03b87e3cc41042`.

No policy module has been authored yet. The first implementation decision is
gated on presence of each requested source in the corpus pinned by
`.axiom/toolchain.toml`.

## Done

- Confirmed the worktree was clean and correctly based on `origin/main`.
- Read the checked-in Revenue Procedure 2025-32 module, proof-atom,
  companion, and applied-manifest conventions.
- Confirmed existing Revenue Procedure modules cite canonical corpus
  provision paths such as
  `us/guidance/irs/rev-proc-2025-32/page-18`.
- Confirmed the repository uses committed applied-file manifests and a
  generated provision reverse index.
- Located the completed sibling credits lane and recovered its authoritative
  runtime-input inventory: section 199A thresholds and phase-in widths from
  Revenue Procedure 2025-32, and section 25B saver tiers attributed to Notice
  2025-67.
- Confirmed the named `recon-rulespec-worker.log` and
  `build-credits-SUMMARY.md` are not present in this checkout; their relevant
  build facts will be independently verified from the pinned corpus and
  sibling lane history.

## Next

1. Verify exact provision blocks for Revenue Procedure 2025-32 section 4.26
   and search the pinned corpus for Notice 2025-67 section 3.09.
2. Encode only corpus-present sources, with proof atoms and tax-year-2026
   companions.
3. Add manual-composition applied-file manifests and regenerate derived
   indexes without modifying toolchain, workflows, CODEOWNERS, statutes,
   pipelines, or repository ledgers.
4. Run the full validation battery and signing dry-run.
5. Write the requested build summary and done marker, including commit SHAs
   and the exact cross-branch repoint plan.
