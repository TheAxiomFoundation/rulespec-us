# B1.3 all-chapter validation gate

Verdict: **PASS — 100/100 compositions** in one batched validator process.

Command (run from `~/TheAxiomFoundation/axiom-encode-perf`):

```sh
AXIOM_CORPUS_REPO=$HOME/TheAxiomFoundation/axiom-corpus-b1-full \
UV_CACHE_DIR=/tmp/uv-cache \
uv run axiom-encode validate --skip-reviewers --json <100 sorted composition files>
```

The process exit code was 0 and `/usr/bin/time` measured 1434.19 seconds of total wall time. Every JSON record reports `ci_pass: true`, `all_passed: true`, and no errors.

| Measure | Per-composition validate wall time |
|---|---:|
| Mean | 14.314 s |
| Median | 13.918 s |
| P95 (nearest rank) | 14.875 s |
| Maximum | 35.526 s |

Per-file verdicts are in `validation-table.csv`; per-file wall times are in `validation-timing.csv`; the unmodified machine results are in `validation-results.json`.
