# 2026 indexed-value policy-module progress

## State

Corpus presence and repository-convention audit is complete on
`fed-parity/revproc`, based on `origin/main`
`c86b2f62511b7ff9d5351c98ca03b87e3cc41042`.

Revenue Procedure 2025-32 section 4.26 is present at the pinned corpus ref, so
the qualified-business-income module and companion are now implemented.
Notice 2025-67 is absent from that corpus, so the saver's-credit half is
stopped pending ingest and no Notice-derived executable values will be added.

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
- Verified the exact corpus pin
  `dfa47fb05bd1d3abbadf0ff17ce4a04bdd5c8085`.
- Verified Revenue Procedure 2025-32 section 4.26 at canonical
  `us/guidance/irs/rev-proc-2025-32/page-21` and `page-22`.
- Verified all six published table values: thresholds of $403,500 joint,
  $201,775 married filing separately, and $201,750 all other; phase-in range
  endpoints of $553,500, $276,775, and $276,750, respectively. The resulting
  widths are $150,000 joint and $75,000 otherwise.
- Verified Notice 2025-67 is absent by path and full-text searches of the
  pinned source, inventory, coverage, provision, and ingest-manifest trees.
  The required ingest target is Notice 2025-67, 2025-49 I.R.B. 761; the
  official document has no numbered section 3.09.
- Added
  `us/policies/irs/rev-proc-2025-32/qualified-business-income.yaml`
  with all six published table cells, three explicit phase-in widths, and
  filing-status selectors for the threshold, range endpoint, and width.
- Added a five-case companion covering all five filing-status codes and
  asserting every published value and width over the 2026 effective window.
- Passed pinned-encoder deterministic validation and proof validation:
  40 atoms checked, with zero missing across nine monetary obligations.
- Passed all five companion cases with the RuleSpec engine.
- Regenerated and checked `.axiom/index/provisions_to_rules.json`; the new
  module is indexed under Revenue Procedure pages 21 and 22 and
  `us/statute/26/199A`.

## Next

1. Run the full validation battery and manual-composition signing dry-run.
2. Write the requested build summary and done marker, including commit SHAs,
   the Notice ingest-needed finding, and the exact cross-branch repoint plan.
