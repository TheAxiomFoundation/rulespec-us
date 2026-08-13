# B1.3 chapter-72 determinism gate

Verdict: **PASS**

The generator double-emits every selected chapter in memory and refuses to
write/check if the two byte maps differ. An independent emit was also run
between the following two SHA-256 snapshots; every hash stayed identical:

| File | SHA-256 before and after second emit |
|---|---|
| `tools/generate_schedule_compositions.py` | `23a13afcbc80c1f750560af2f42aa32732c8c3f7ef784bf44f5eda0ad44827c5` |
| `us/policies/cbp/us-tariff-schedule/generated/ch72.yaml` | `f696fbfd59d53224d5cbc4ed919f572bc5826df02551c4115092c6bf087b3b1a` |
| `us/policies/cbp/us-tariff-schedule/generated/ch72.test.yaml` | `b2264ff98cbb7a13c48d8981eaceaace1f1996c26b82258ea630d5d740333c4b` |
| `programs/us/us-tariff-schedule/ch72.yaml` | `27064b22bbbc5ac63ad02ee19573d4aa21adca230637e734edce828be0d96a81` |

The final drift check passed:

```text
$ python3 tools/generate_schedule_compositions.py --chapters 72 --check
check OK: 3 files match deterministic outputs
```
