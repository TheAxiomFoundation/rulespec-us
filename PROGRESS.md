# PR 1002 ACA PTC Fix Progress

## State

- Branch: `fed-parity/aca-ptc`
- Starting head: `cf5ae8bfcb4ba218fdc9cf6bdbc0be9e21aca7ae`
- Base: `origin/main` at `eaad4c3079192e20c06a199e5fd0e1a5a485a80b`
- Phase: fail-closed rounding fix complete and locally focused-gated; family-size contract correction next.
- Signing: reserved for the main lane; this lane will only run the required dry run.

## Done

- Confirmed the worktree was clean at the reviewed head.
- Read `review-1002-VERDICT.md` in full.
- Recorded the adjudicated requirements:
  mandatory applicable-percentage rounding must either be encoded from a
  resolver-confirmed corpus provision or fail closed if that provision is
  absent; the family-size description must treat the poverty line as a trusted
  upstream fact; signing must remain blocked; all gates and reporting numbers
  must be recomputed.
- Read the GitNexus debugging workflow. The repository is known from the
  verdict to be unindexed, so source-level tracing will be used unless status
  now shows an index.
- Invoked the pinned encoder at commit
  `3869d66d009f52258be35901edbef370e65a399c` and version `0.2.1200` through
  its real `resolve_corpus_source_unit` for `26 CFR 1.36B-3(g)` against
  `/Users/maxghenis/TheAxiomFoundation/axiom-corpus`.
- The resolver returned `ABSENT` after trying
  `us/regulation/26/1/36B-3/g`, `us/regulation/26/1/36B-3`,
  `us/regulation/26/1`, and `us/regulation/26`. Per the adjudicated verdict,
  this lane must implement the fail-closed guard/deferred-output path and must
  not encode the rounding operation as though the regulation were ingested.
- Added a private 0.01-percentage-point grid increment solely for the
  fail-closed computability guard; the general rounded-rate output remains
  explicitly deferred to the absent regulation.
- Extended `aca_ptc_full_year_runtime_inputs_valid` to admit only raw
  interpolations already on that grid. All nine existing fixtures now assert
  that the guard holds.
- Added the 210%-FPL counterexample. It records raw rate `0.06968`, recomputes
  the legally rounded chain (`0.0697`, contribution `$2,290.6905`, credit
  `$5,209.3095`), and proves this corpus-bounded implementation returns
  `not_holds` and a zero final credit rather than the wrong raw-rate credit.
- Pinned focused gates pass after the rounding edit: deterministic validation,
  proof validation (37 atoms), and the ACA companion (10 cases).

## Next

1. Correct the family-size/FPL contract description and add the mismatch NOTE
   case as a documented non-goal.
2. Sync the added private guard parameter into the oracle-pending ledger and
   regenerate the reverse index if required.
3. Run the signing dry run and full canonical gate battery.
4. Write the corrected PR-body Gates paragraph and final DONE report with
   exact counts, ledger delta, and local commit SHAs.
