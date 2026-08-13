# B1.3 rollout witness identity gates

Verdict: **PASS** — ch76 90/90 cells; ch95 90/90 cells.

Both independently compiled generated compositions were compared with the independently compiled hand-built witness on the pilot's same 10-country by 8-required-date grid, plus the executable boundary date 2026-02-15. Eleven component/entry-variant outputs, the General Note 3 selected base, each algebraic residual, and the total were Decimal-compared. The four pre-2026-02-15 dates retain matching structural unavailability and raw engine error classes; absence was never coerced to zero.

Chapter 76 uses statistical/rate line 7601.10.30.00 (`7601103000`). Its generated selector preserves heading 9903.90.09's proved 70-percent Russian rate in lieu of ordinary column 2, then adds the separate 200-percent section 232 aluminum component. GB binds both 25-percent UK section 232 implementations across the 2026-07-21 version boundary; CU binds ordinary column 2.

Chapter 95 feeds both compositions the witness statistical line 9506.62.40.40, while only the generated composition receives parent RATE-LINE key `9506624000`, where the General and column-2 rates legally live. Statistical child key `9506624040` is structurally absent and was never queried.

## Chapter 76 by date

| Date | Cells | Outcome | Component mismatches | Max absolute total delta | Verdict |
|---|---:|---|---:|---:|---|
| 2025-02-15 | 10 | matching_pre_effective_unavailable | 0 | 0 | PASS |
| 2025-04-10 | 10 | matching_pre_effective_unavailable | 0 | 0 | PASS |
| 2025-07-01 | 10 | matching_pre_effective_unavailable | 0 | 0 | PASS |
| 2026-01-15 | 10 | matching_pre_effective_unavailable | 0 | 0 | PASS |
| 2026-02-15 | 10 | evaluated | 0 | 0.000 | PASS |
| 2026-02-21 | 10 | evaluated | 0 | 0.000 | PASS |
| 2026-02-25 | 10 | evaluated | 0 | 0.000 | PASS |
| 2026-03-15 | 10 | evaluated | 0 | 0.000 | PASS |
| 2026-08-01 | 10 | evaluated | 0 | 0.000 | PASS |

## Chapter 95 by date

| Date | Cells | Outcome | Component mismatches | Max absolute total delta | Verdict |
|---|---:|---|---:|---:|---|
| 2025-02-15 | 10 | matching_pre_effective_unavailable | 0 | 0 | PASS |
| 2025-04-10 | 10 | matching_pre_effective_unavailable | 0 | 0 | PASS |
| 2025-07-01 | 10 | matching_pre_effective_unavailable | 0 | 0 | PASS |
| 2026-01-15 | 10 | matching_pre_effective_unavailable | 0 | 0 | PASS |
| 2026-02-15 | 10 | evaluated | 0 | 0.000 | PASS |
| 2026-02-21 | 10 | evaluated | 0 | 0.000 | PASS |
| 2026-02-25 | 10 | evaluated | 0 | 0.000 | PASS |
| 2026-03-15 | 10 | evaluated | 0 | 0.000 | PASS |
| 2026-08-01 | 10 | evaluated | 0 | 0.0 | PASS |

## Chapter 76 section 232 binding detail

| Date | Country | Witness component | Generated component | Verdict |
|---|---|---:|---:|---|
| 2026-02-15 | GB | 0.25 | 0.25 | PASS |
| 2026-02-15 | RU | 2 | 2 | PASS |
| 2026-02-21 | GB | 0.25 | 0.25 | PASS |
| 2026-02-21 | RU | 2 | 2 | PASS |
| 2026-02-25 | GB | 0.25 | 0.25 | PASS |
| 2026-02-25 | RU | 2 | 2 | PASS |
| 2026-03-15 | GB | 0.25 | 0.25 | PASS |
| 2026-03-15 | RU | 2 | 2 | PASS |
| 2026-08-01 | GB | 0.25 | 0.25 | PASS |
| 2026-08-01 | RU | 2 | 2 | PASS |

Full 90-row diffs are `identity-ch76.csv` and `identity-ch95.csv`; normalized raw engine results, including pre-effective error classes, are retained in their companion JSON files.
