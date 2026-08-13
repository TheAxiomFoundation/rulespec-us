# B1.3 all-chapter rollout gate summary

| Gate | Verdict | Evidence |
|---|---|---|
| Generated inventory | PASS — 100 compositions, 100 tests, 100 programs | `STRUCTURE.md` |
| Witness identity — chapter 76 | PASS — 90/90, zero delta | `IDENTITY.md`, `identity-ch76.csv` |
| Witness identity — chapter 95 | PASS — 90/90, zero delta | `IDENTITY.md`, `identity-ch95.csv` |
| Full pinned validation | PASS — 100/100 in one process | `VALIDATION.md`, `validation-table.csv` |
| Determinism / full `--check` | PASS | `DETERMINISM.md` |
| Repository layout/program tests | PASS — 12/12 | `STRUCTURE.md` |

The batched validation wall time was 1434.19 seconds. Per-composition measurements are in `validation-timing.csv`.

Ledger preparation did not modify `oracle-coverage-pending.yaml`. `ledger-new-legal-ids.txt` contains 11,601 sorted IDs: 11,501 executable composition outputs plus 100 program-output IDs. For coordinator arithmetic, the current ceiling 4,140 plus this full list is 15,741, subject to the coordinator's classification and batching decisions.

Chapter 99a/99b flat column-2 rates are explicit structural omissions, not zeros; see `STRUCTURE.md`. No existing RuleSpec module was changed, and the chapter-72 pilot bytes remain unchanged.
