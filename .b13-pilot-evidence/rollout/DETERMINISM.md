# B1.3 all-chapter determinism gate

Verdict: **PASS**

- The table manifest is content-pinned at SHA-256 `0ab7aa9d757661fd488893af038a70ebdd916c555304962b9f93badb0e711f77`.
- Two independent full emits produced identical bytes.
- The final full-set drift check reported `check OK: 300 files match deterministic outputs`.
- `determinism-hashes.sha256` records all 300 outputs plus the generator; its own SHA-256 is `e6e8d3605c54a359fb8758cd322ab487a2c4029229709e79e5991f429099c654`. Every recorded hash was recomputed successfully while rendering this evidence.
- The three chapter-72 pilot files retain their commit-04f920099 hashes: composition `f696fbfd...`, companion `b2264ff...`, and program `27064b22...`.
