# PR 1002 ACA PTC Fix Progress

## State

- Branch: `fed-parity/aca-ptc`
- Starting head: `cf5ae8bfcb4ba218fdc9cf6bdbc0be9e21aca7ae`
- Base: `origin/main` at `eaad4c3079192e20c06a199e5fd0e1a5a485a80b`
- Phase: implementation and canonical gate battery complete; reports and
  standard campaign closeout next.
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
- Reworded the family-size and poverty-line contract: the poverty line is a
  trusted upstream fact for the household's family size and jurisdiction, and
  this table-free module checks positivity but does not validate correspondence.
- Added the deliberately mismatched family-size-4/size-1-poverty-line NOTE
  case. It documents the non-goal by asserting the current trusted-input
  behavior (`runtime_inputs_valid: holds`, credit `$3,600`) without endorsing
  the mismatch as a valid legal fact.
- Focused validation and proof validation still pass, and the ACA companion now
  passes all 11 cases.
- Regenerated the reverse index with the repository tool and confirmed it is
  byte-for-byte current at 4,171 provisions, 4,947 edges, and 4,454 modules.
- Ran `oracle-coverage-pending sync` from the required
  `ae-main-sync@212f6671fe7a` snapshot in a real canonical-basename
  `rulespec-us` checkout. The exact current oracle surface adds the private ACA
  guard parameter and drains 27 now-mapped declarations, producing 2,304
  pending declarations.
- Recreated the canonical snapshot at `ec5149f12bcc`, then confirmed validation
  passes, proof validation checks all 37 atoms, and the ACA companion passes all
  11 cases.
- The repository money-atom gate passes across 4,455 files and 52 roots: 118 of
  2,846 obligations remain missing, within the ratcheted allowance of 151.
- The pending-ledger rerun is unchanged and its check passes at 2,304 applied
  declarations with zero stale entries.
- The signing dry run selects exactly one manifest group covering
  `ptc_pipeline.yaml` and `ptc_pipeline.test.yaml`; actual signing remains the
  main lane's job.
- Repository pytest reports 58 passed, one warning, and one expected failure:
  the ACA module's intentionally stale signed-manifest hash.
- The full companion sweep covers 16,525 cases. Its four failures are the same
  unrelated 26 U.S.C. 32 failures reproduced at the PR base, where the sweep
  covers 16,514 cases.
- Program artifacts pass at 33/33 with the pinned composer and engine.
- The existing six-case ACA PolicyEngine comparison remains 6/6. It does not
  include the new 210%-FPL case; a direct pinned probe shows PolicyEngine uses
  the unrounded rate and returns approximately `$5,209.9668`, so it diverges
  from the deliberate fail-closed zero until the regulation is ingested.
- Exact pending-ledger delta from base to this head is 2,300 to 2,304:
  17 ACA additions, 13 now-mapped SNAP removals, net `+4`.

## Next

1. Commit this completed gate record.
2. Remove this session ledger in the standard campaign closeout because root
   `PROGRESS.md` is not an admitted repository artifact.
3. Recheck the final committed head, then write and commit the corrected
   PR-body Gates paragraph and final DONE report with exact local SHAs.
