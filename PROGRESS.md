# Progress

## State

- Task: retry fail-closed atomic encodings in 42 U.S.C. § 19237.
- Existing worktree: /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a
- Mode: detached HEAD at e06c4c9b777f94909abfd5c5bb5ec55efd7d394e; accepted branches untouched.
- Required/live base: d58cc0ce67ad891fde4c9061c86a2091bfdd524f.
- Canonical policy root used for every fresh run: the existing worktree path ending in /us.
- Official corpus: clean branch checkout codex/federal-proposal-security-corpus-2026 at 129dae01c6f7a4787bc7678d4a97a478f3934d9f with complete 133/133 coverage.
- Pinned encoder: clean detached checkout at 3869d66d009f52258be35901edbef370e65a399c; executable SHA-256 6d134a9820f10826d3cb56e1a0df755636cad8543051811acc2f0be102af0173.
- Pinned real Rust engine: clean detached checkout at ffd8213271947b0189a9dd61a055c1e0e78908a0; binary SHA-256 ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb.
- Final disposition: reject both definitions; no RuleSpec, companion test, signed manifest, compiled target, or direct target request is retained.
- Only FINAL_REPORT.md and this ledger are intentionally changed.

## Fresh apply-requested attempts

All fresh attempts used the unchanged pinned encoder with --apply --no-sync, backend/model codex/gpt-5.5, repo-augmented mode, the official corpus, the pinned Rust engine, the canonical /us policy root, an isolated database/output root, and the unchanged prepared operator contexts.

| Definition / attempt | Run / session | Root | Duration | Tokens | RuleSpec bytes | Result |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Paragraph (3), first | a9e8053c / encode-a9e8053c | /private/tmp/axiom-19237-atomic-retry-20260830.TabUHm | 60,911 ms | 0 | 0 | apply_blocked_generation |
| Paragraph (3), second | d2a70c04 / encode-d2a70c04 | /private/tmp/axiom-19237-p3-retry2-20260830.wJfxTB | 66,575 ms | 0 | 0 | apply_blocked_generation |
| Paragraph (1) | aac3cc36 / encode-aac3cc36 | /private/tmp/axiom-19237-p1-signed-20260830.AWLVp6 | 90,659 ms | 0 | 0 | apply_blocked_generation |

Each run failed with the Codex response stream disconnecting before completion. Every run recorded apply_requested=true, apply_success=false, applied_files=[], final_success=false, zero input/output/cache/reasoning tokens, and no generated candidate. No apply auto-repair or manual repair occurred.

The approved AXIOM_ENCODE_APPLY_SIGNING_KEY was not inspected, printed, logged, hashed, copied, rotated, placed on a command line, or retrieved from a keychain. Generation failed before signing, and no guard that would read the key was run.

## Acceptance findings

- Paragraph (3) still requires foreign entity AND (A OR B OR C OR D OR E).
- Every designation, list, nation, government relationship, Attorney General allegation, same-activities conviction, authority, Commerce determination, Defense/DNI consultation, unauthorized-conduct fact, and detriment fact must remain external and dynamic.
- Paragraph (3) requires 20 positive OR leaves, the foreign-entity conjunction, all missing/conjunction adversaries, and the 2022-08-08 false sentinel before the operative 2022-08-09 version.
- Paragraph (3) proof must include the /3 chapeau; /3/A, /3/B, /3/C, /3/D, /3/D/i through /3/D/vii, and /3/E; the section root may support only enactment and the false sentinel.
- Paragraph (1) still requires individual status, caller-adjudicated substantive/meaningful scientific-development or execution contribution, and designation by the same Federal research agency.
- Paragraph (1) proof must include /1, /1/A, and /1/B; the section root may support only enactment and the false sentinel.
- Missing dynamic facts must remain Rust missing-input errors, never false defaults.
- No generated proof atoms or fixtures exist for either definition, so fixture counts and distinct states are zero.
- No target RuleSpec exists, so proof validation, target compilation, and all route-level direct Rust cases correctly remain unrun/zero.

## Runtime evidence

The selected real Rust engine was re-exercised through the pinned encoder on the existing accepted OR-definition companion us/statutes/8/1641/b.test.yaml.

Result: exit 0; success=true; one test file; 4/4 cases; one compiled program; zero failures.

This confirms the selected runtime operates but supplies no § 19237 target evidence.

## Custody

- Paragraph (3) operator context SHA-256: 2eeb2aedf0994d097c953198f92343fefda3c282273353c285dfaa71a5384bd7.
- Paragraph (1) operator context SHA-256: 54c3cd94ca645e10ce222580a475442489133b4ee81255b0d15d40e8b0b5b0e4.
- Source-credit continuation SHA-256: 3b1135b5003f1e725b7287a4d32b3067a1db651e5b28a2f5bacdb3a7141a8e7e.
- Run a9e8053c trace/context/repair/database SHA-256: 3720c1ee0c8bdfd104c1f8aac3748c401b6f912879dc606672134e173eacff70 / db15bf0bc63a41f14aa621ceb4209a0d458653ca3110667e21411cc93aa3044e / 92c2c94bb8b242626997c40c4601e1f8a866693586916425a706d98a56274659 / 4ffe1fcb10832e996187e9381e31d236e7790920a4e5711a13ac960bc277b900.
- Run d2a70c04 trace/context/repair/database SHA-256: e0689709e8bf5d3825e198353f43e7e746452209b0c2a93daf4f95297e3345bf / db15bf0bc63a41f14aa621ceb4209a0d458653ca3110667e21411cc93aa3044e / b4ddd9b0fc35e38c859c386820df1637d7f42ebd3a75b4ace7874ec479204e63 / 22891b88c6bec64b3f9ed3bc3fea7de7f4739d11b3f8789ac61af9bdf12b9c1e.
- Run aac3cc36 trace/context/repair/database SHA-256: 16b89e1d9fef550e26b5a9378eb4c00e8174022051383bcf9ed9bbcb23e653fb / 781bb90143f80f3c961c248b97c3d9174d8d822b76517ec394b88511933520d3 / 500bdfed49f4e25c060c9b375a8c16c46995872796fb13f2414b4f930c543f4e / 8b73d10e5fe59173f415b91334a1e46a4d3134e63b1e373b5e100f2d85deeb01.
- FINAL_REPORT.md SHA-256: a9af20db84bcfb2d32834ac404974c12d573fb933d1bdde3e84a0760a659abe4.

## Next

- Restore working Codex response-stream connectivity before any future retry.
- Use a new isolated root/database for every future definition attempt.
- Never promote or copy these failed runs.
- Retain only a newly generated, unchanged signed output that independently passes exact proof, generated fixtures, manifest/file hash reconciliation, and the full direct real-Rust matrix.
