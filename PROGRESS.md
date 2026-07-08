# US TANF coverage — wave-1 scout progress

Branch `us-tanf-scout-wave1` (from origin/main). Goal: prove the reproducible
recipe for covering per-state TANF rows in the us-pe universe, so wave-2 fans out.

## Done and protected (pushed)
- **Recipe**: `docs/us-tanf-coverage-recipe.md` — full corpus→encode→compose→
  oracle→register pipeline, source-type playbook, per-state cost, failure modes,
  wave-2 worklist template, premise corrections, required-secrets gate.
- **Alabama proven end to end** (axiom-oracles branch `us-tanf-scout-wave1`,
  `al-tanf-ecps` suite): **1444/1444 = 100.0%** vs pinned PE `al_tanf` on the full
  Alabama Enhanced-CPS population; registered in `conformance/us-pe.yaml`
  (us-pe covered 27→28, unexplained 0). `programs/us-al/tanf/fy-2026.yaml`
  mirrored here.
- **Harness validated**: reproduced covered `co-tanf-ecps` = 1042/1045 = 99.71%.

## Blockers found (why only AL was provable in-session)
- `AXIOM_ENCODE_APPLY_SIGNING_KEY` / `AXIOM_CORPUS_INGEST_PRIVATE_KEY` **absent** →
  no fresh encode or ingest (CI rejects unsigned). Blocks GA/DE/ME/HI (partial
  leaves, need encode) and any needs-ingest state.
- AL was fast only because a prior sweep had already encoded its complete benefit
  leaf (Appendix N §2). FL has benefit leaves but page-based, no clean outputs →
  heavy compose. IN belongs to another lane.

## Next (wave-2, once signing key provisioned)
Simplest-PE-module-first: encode+compose GA, DE, ME, HI; then MS, ND, NC, SD;
then TX/MT/IL. Skip IN. Non-simulated states → `in_scope: false`.

## Discipline
Rebase on origin/main before merge; append-only mapping blocks; re-run suite
after rebase; foreground CI; never admin-merge.
