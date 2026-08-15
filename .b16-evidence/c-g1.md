# B1.6-C G1 determinism

Verdict: **PASS**. A full double in-memory emit produced 300 outputs and `python tools/generate_schedule_compositions.py --check` reported `check OK: 300 files match deterministic outputs` on the final bytes.

The generated inventory is 100 compositions, 100 companion tests, and 100 unchanged program specs.
