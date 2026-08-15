# B1.6 B1 build log

- 2026-08-14 — Read the binding campaign sections, D0 report, spike report, spike parser, B1.2 generator, generated module, and companion-test conventions.
- Source pin measured: `0f3ed7ef2efb64383825db65e615959200770e8511c8d4834b16e02892cb9ec8`.
- Discovery: Revision 15's April 2026 metals structure supersedes the Yale loader's legacy note 16(b)/(m) labels. Current steel atoms are in 16(c)(iii), (iv), (vii), (x), and (xi). Note 19(b) names aluminum at heading level only; note 19(j) prints derivative 8/10-digit atoms.
- Discovery: the pinned notes bytes jump from U.S. note 50 to U.S. note 52 and contain neither `9903.03.12` nor the requested note-51 section-338 subdivisions. The 554-row Yale file therefore cannot be emitted with chapter-99 proof atoms from this pinned input.
- G4 pilot (before formal gate): note18 module validation passed. This was a schema probe, not the logged all-module G4 gate.
- G1 pre-gate: log P(pass) = ln(0.98) = -0.020203. Pass means double emit is identical and `--check` byte-compares every emitted file.
- G1: PASS — double emit and 10-file byte comparison succeeded; hashes captured under `.b16-evidence/`.
- G2 pre-gate: log P(pass) = ln(0.97) = -0.030459. Pass means the independent concatenated-page parser exactly equals every emitted membership table in both directions.
- G2: PASS — exact equality for all 23 emitted parameter tables, both directions.
- G3 pre-gate: log P(pass) = ln(0.85) = -0.162519. Pass means every difference in the available 301/201/122 Yale comparisons has a listed partial-value, vintage, or statistical-level disposition and no unknown for list 1, 201, or 122-unconditional.
- G3: PARTIAL — requested zero-unknown lists pass and 309 differences are enumerated (24 partial-value scope, 2 statistical-level, 283 vintage). Metals and section 338 cannot receive a like-for-like legacy-label reconciliation without an explicit old-to-restructured subdivision mapping; section 338 is absent from the pinned source.
- G4 pre-gate: log P(pass) = ln(0.90) = -0.105361. Pass means every emitted module reports `Result: ✓ PASSED` under the pinned validator invocation.
