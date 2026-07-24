# PR 1002 ACA PTC Fix Progress

## State

- Branch: `fed-parity/aca-ptc`
- Starting head: `cf5ae8bfcb4ba218fdc9cf6bdbc0be9e21aca7ae`
- Base: `origin/main` at `eaad4c3079192e20c06a199e5fd0e1a5a485a80b`
- Phase: verdict read; pinned-corpus resolution and implementation-path decision next.
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

## Next

1. Resolve `26 CFR 1.36B-3(g)` through the real pinned-corpus resolver and
   choose the direct-rounding or fail-closed path from that result.
2. Trace the applicable-percentage pipeline and companion harness.
3. Implement and commit the blocking rounding fix and its 210%-FPL case.
4. Correct the family-size/FPL contract description and add the mismatch NOTE
   case as a documented non-goal.
5. Run the signing dry run and full canonical gate battery.
6. Write the corrected PR-body Gates paragraph and final DONE report with
   exact counts, ledger delta, and local commit SHAs.
