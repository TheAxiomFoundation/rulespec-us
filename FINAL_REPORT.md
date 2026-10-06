# 42 U.S.C. § 19237 atomic encoding final report

## Outcome

No statutory definition is accepted and no generated RuleSpec output is retained.

| Definition | Decision | Generated RuleSpec bytes | Generated fixtures | Proof atoms | Direct target Rust cases | Retained rule/test/manifest |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| § 19237(3), foreign entity of concern | **Reject** | 0 in both fresh apply-requested attempts | 0 | 0 | 0 | None |
| § 19237(1), covered individual | **Reject** | 0 in its separate fresh apply-requested attempt | 0 | 0 | 0 | None |

The pinned encoder was invoked three times in fresh isolated roots with --apply --no-sync, the official USC corpus, the pinned real Rust engine, the canonical policy root ending in /us, and the unchanged hash-pinned operator contexts. Every run invoked the Codex backend adapter, began a turn, and then failed while attempting the Codex response endpoint:

    stream disconnected before completion: error sending request for url (https://chatgpt.com/backend-api/codex/responses)

All three runs recorded zero input tokens, zero output tokens, zero RuleSpec bytes, apply_requested=true, apply_success=false, applied_files=[], and status=apply_blocked_generation. There was no candidate to validate, no signature or apply manifest to retain, and no generated target against which proof, fixtures, or route-level Rust cases could run.

This is an operational fail-closed rejection. It does not establish that RuleSpec or the Rust runtime is incapable of expressing either definition.

## Worktree and base custody

- Existing detached worktree: /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a
- Detached HEAD before this report update: e06c4c9b777f94909abfd5c5bb5ec55efd7d394e
- Required upstream base: d58cc0ce67ad891fde4c9061c86a2091bfdd524f
- Verified local origin/main: d58cc0ce67ad891fde4c9061c86a2091bfdd524f
- Verified merge-base of detached HEAD and the required base: d58cc0ce67ad891fde4c9061c86a2091bfdd524f
- Canonical policy root supplied to every fresh run: /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us
- The worktree was clean before the fresh runs.
- No accepted branch was checked out or modified.
- No new worktree was created.
- No commit, push, pull request, deployment, publication, or remote mutation was performed.
- The only intended final worktree changes are this report and PROGRESS.md.

The four pre-existing detached documentation commits remain untouched:

- 15582c453d04135df559d424aaaed37a5ccc8edd — chore: initialize 19237 atomic encoding ledger
- 5beca879de6fe65a95af508a4a37d905df2715a4 — docs: record 19237 source and custody audit
- 0a0909ae65ddb7854de28c4c8255fffb1bb8a1a7 — docs: record rejected 19237 encoder run
- e06c4c9b777f94909abfd5c5bb5ec55efd7d394e — docs: finalize rejected 19237 atomic encoding report

## Official source custody

Official corpus checkout:

- Path: /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830
- Clean branch checkout: codex/federal-proposal-security-corpus-2026 at 129dae01c6f7a4787bc7678d4a97a478f3934d9f
- Coverage: complete, 133/133 matched, with no missing, extra, or duplicate citations.

| Artifact | SHA-256 |
| --- | --- |
| Provisions JSONL | 566a513343f88d5a4944c591ef86464dcd27ea8dce8a4dd730f05efec4f69aa4 |
| Inventory JSON | 02a23fd00306ec320c5fc4c1448c356051e47007de2e7bb167203e96c3b8bd12 |
| Coverage JSON | 07aa0d455d923bc6c9a2e34040b583f2365f1dfb41aed7761aae74afb582f03e |
| Official OLRC ZIP | 31929c28f117362ac8788607242795769b05ed7726f07e4ed3b1786f39655ce7 |
| Extracted USLM XML | b72955590abe55bdbd1ce5d13c5293955a82add9c84fad92c1674ec469e86624 |
| Full § 19237 JSONL record body | 315606f96e8ae6a6db4763139f396ec7cf8ec57a5faa951a437a8c4f7e981b31 |
| Paragraph (1) JSONL line | 9e0bc9c9450756cec549336d87df1f1603680b76d83c21f7ff1dbd285151325b |
| Paragraph (1) exact body | 8efb20143a78a9992615e9608fa76e439848cb703f78c14945433e04ca11a022 |
| Paragraph (3) JSONL line | aa3970b6e9c252e1c54a255b8ab13e30d09c99990e2300138ec7c5c2b4d25784 |
| Paragraph (3) exact body | 5c004e80518222e8865a533828c4b60a75459668106499aeacc2acb7413806d4 |

Relevant corpus locations:

- Provisions: data/corpus/provisions/us/statute/2026-08-30-proposal-security-title-42.jsonl
- Section record: line 101
- Paragraph (1) and children: lines 102–104
- Paragraph (3), children (A)–(E), and (D)(i)–(vii): lines 106–118
- Raw USLM: data/corpus/sources/us/statute/2026-08-30-proposal-security-title-42/uslm/usc42.xml
- § 19237 hierarchy: lines 499756–499788
- Source credit: line 499816

The source credit is Pub. L. 117–167, division B, title VI, § 10638, enacted 2022-08-09, 136 Stat. 1669. An accepted encoding therefore requires a literal-false version on 2022-08-08 followed by the operative formula on 2022-08-09.

## Operator-context custody

The already prepared contexts were inspected in place and passed unchanged to the encoder:

| Context | Path | SHA-256 |
| --- | --- | --- |
| Paragraph (3) acceptance | /Users/maxghenis/.Trash/axiom-19237-b07c2bf8-encoding-context/paragraph-3-acceptance.md | 2eeb2aedf0994d097c953198f92343fefda3c282273353c285dfaa71a5384bd7 |
| Paragraph (3) source credit | /Users/maxghenis/.Trash/axiom-19237-b07c2bf8-encoding-context/paragraph-3-source-credit.txt | 3b1135b5003f1e725b7287a4d32b3067a1db651e5b28a2f5bacdb3a7141a8e7e |
| Paragraph (1) acceptance | /Users/maxghenis/.Trash/axiom-19237-b07c2bf8-encoding-context/paragraph-1-acceptance.md | 54c3cd94ca645e10ce222580a475442489133b4ee81255b0d15d40e8b0b5b0e4 |
| Paragraph (1) source credit | /Users/maxghenis/.Trash/axiom-19237-b07c2bf8-encoding-context/paragraph-1-source-credit.txt | 3b1135b5003f1e725b7287a4d32b3067a1db651e5b28a2f5bacdb3a7141a8e7e |

Each fresh run retrieved 14 context files. The paragraph-(3) copied operator files rehashed to the two values above in both fresh workspaces. The paragraph-(1) copied operator files likewise rehashed to their pinned values.

## Pinned tool custody and signing discipline

Encoder:

- Path: /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode
- Clean detached HEAD: 3869d66d009f52258be35901edbef370e65a399c
- Version: 0.2.1200
- Executable: .venv/bin/axiom-encode
- Executable SHA-256: 6d134a9820f10826d3cb56e1a0df755636cad8543051811acc2f0be102af0173

Rust engine:

- Path: /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine
- Clean detached HEAD: ffd8213271947b0189a9dd61a055c1e0e78908a0
- Binary: target/debug/axiom-rules-engine
- Binary SHA-256: ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb

The approved AXIOM_ENCODE_APPLY_SIGNING_KEY environment variable was never referenced on a command line or by any diagnostic command; the only authorized code path that could read it was the unchanged encode --apply flow. Its value was never inspected, printed, logged, hashed, copied, or rotated. No keychain lookup was attempted. Generation failed before signing, so no signature was created. No guard or verification command that would read the key was run.

## Exact fresh encoder invocations

All commands ran from the pinned encoder checkout. Neither --skip-reviewers nor --apply-target-only was used.

First paragraph-(3) attempt:

    .venv/bin/axiom-encode encode us/statute/42/19237/3 \
      --output /private/tmp/axiom-19237-atomic-retry-20260830.TabUHm/output/paragraph-3 \
      --model gpt-5.5 \
      --backend codex \
      --corpus-path /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830 \
      --axiom-rules-engine-path /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine \
      --policy-repo-path /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us \
      --mode repo-augmented \
      --allow-context /Users/maxghenis/.Trash/axiom-19237-b07c2bf8-encoding-context/paragraph-3-acceptance.md \
      --allow-context /Users/maxghenis/.Trash/axiom-19237-b07c2bf8-encoding-context/paragraph-3-source-credit.txt \
      --db /private/tmp/axiom-19237-atomic-retry-20260830.TabUHm/encodings.db \
      --no-sync \
      --apply

Second independently isolated paragraph-(3) attempt:

    .venv/bin/axiom-encode encode us/statute/42/19237/3 \
      --output /private/tmp/axiom-19237-p3-retry2-20260830.wJfxTB/output \
      --model gpt-5.5 \
      --backend codex \
      --corpus-path /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830 \
      --axiom-rules-engine-path /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine \
      --policy-repo-path /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us \
      --mode repo-augmented \
      --allow-context /Users/maxghenis/.Trash/axiom-19237-b07c2bf8-encoding-context/paragraph-3-acceptance.md \
      --allow-context /Users/maxghenis/.Trash/axiom-19237-b07c2bf8-encoding-context/paragraph-3-source-credit.txt \
      --db /private/tmp/axiom-19237-p3-retry2-20260830.wJfxTB/encodings.db \
      --no-sync \
      --apply

Separate paragraph-(1) attempt:

    .venv/bin/axiom-encode encode us/statute/42/19237/1 \
      --output /private/tmp/axiom-19237-p1-signed-20260830.AWLVp6/output \
      --model gpt-5.5 \
      --backend codex \
      --corpus-path /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830 \
      --axiom-rules-engine-path /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine \
      --policy-repo-path /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us \
      --mode repo-augmented \
      --allow-context /Users/maxghenis/.Trash/axiom-19237-b07c2bf8-encoding-context/paragraph-1-acceptance.md \
      --allow-context /Users/maxghenis/.Trash/axiom-19237-b07c2bf8-encoding-context/paragraph-1-source-credit.txt \
      --db /private/tmp/axiom-19237-p1-signed-20260830.AWLVp6/encodings.db \
      --no-sync \
      --apply

## Fresh run results

| Definition / attempt | Run / session | Duration | Source bytes | RuleSpec bytes | Tokens in / out | Status |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Paragraph (3), first | a9e8053c / encode-a9e8053c | 60,911 ms | 1,540 | 0 | 0 / 0 | apply_blocked_generation |
| Paragraph (3), second | d2a70c04 / encode-d2a70c04 | 66,575 ms | 1,540 | 0 | 0 / 0 | apply_blocked_generation |
| Paragraph (1) | aac3cc36 / encode-aac3cc36 | 90,659 ms | 500 | 0 | 0 / 0 | apply_blocked_generation |

For all three:

- Backend/model: codex / gpt-5.5
- Mode: repo-augmented
- Context files retrieved: 14
- Cache-read, cache-creation, and reasoning-output tokens: 0
- Estimated cost: $0
- Standalone validation: false
- Overlay validation: not run
- Apply requested: true
- Apply success: false
- Applied files: none
- Final success: false
- No apply=auto_* repair event occurred because generation never completed.

## Fresh run hashes

The run-row hashes below are SHA-256 over the exact sqlite3 -json output of this projection, run against each isolated database:

    SELECT id,timestamp,citation,file_path,total_duration_ms,agent_type,agent_model,session_id,iteration,parent_run_id,axiom_encode_version,length(source_text) AS source_bytes,length(rulespec_content) AS rulespec_bytes,outcome_json FROM encoding_runs ORDER BY timestamp;

Session hashes use the exact sqlite3 -json output of:

    SELECT id,run_id,started_at,ended_at,model,cwd,event_count,total_tokens,input_tokens,output_tokens,cache_read_tokens,cache_creation_tokens,estimated_cost_usd,axiom_encode_version FROM sessions ORDER BY started_at;

The output-tree custody digest was produced from each run root with:

    find output -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256

### Paragraph (3), run a9e8053c

- Run root: /private/tmp/axiom-19237-atomic-retry-20260830.TabUHm
- Output files: 19
- Run-row JSON SHA-256: 416cb1a6d27e3a3285b4439c69e71f152c1cde0a7ab131162fe2bfe2f1ccf62d
- Session JSON SHA-256: 8eda17b70f863dc344fcd705ba4182de12631c1e5fdc3a7a69b9fc3f913e313a
- Isolated database SHA-256: 4ffe1fcb10832e996187e9381e31d236e7790920a4e5711a13ac960bc277b900
- Output-tree custody digest: 4d68435b4f4d85f42297af20a37717752d1b23947a547db82581ba7146b557d6
- Trace SHA-256: 3720c1ee0c8bdfd104c1f8aac3748c401b6f912879dc606672134e173eacff70
- Context-manifest SHA-256: db15bf0bc63a41f14aa621ceb4209a0d458653ca3110667e21411cc93aa3044e
- Repair-manifest SHA-256: 92c2c94bb8b242626997c40c4601e1f8a866693586916425a706d98a56274659
- Workspace source SHA-256: 0d010ba525a99b0e39266add08db454beb07d3e492844194218e1c77cf93b189
- Workspace source-metadata SHA-256: 0cbe9796d94d4d7cdf72abc171d3ca8807fa48df3ef79be4b52654c8f7095117
- Generated 3.yaml: absent; no hash
- Generated 3.test.yaml: absent; no hash
- Signed apply manifest: absent; no hash

### Paragraph (3), run d2a70c04

- Run root: /private/tmp/axiom-19237-p3-retry2-20260830.wJfxTB
- Output files: 19
- Run-row JSON SHA-256: 32aee5987e5d6da91f53d480b7d398baadfc94f520f5479ec1aec2c349af4f12
- Session JSON SHA-256: 1800359719ed1caa25d4c3c3b3596942978a2f8f55a716c06f611f546390298a
- Isolated database SHA-256: 22891b88c6bec64b3f9ed3bc3fea7de7f4739d11b3f8789ac61af9bdf12b9c1e
- Output-tree custody digest: cd9bc574f878664c7cc2fcad142792655fbd3fc7f9efeb8c18ca12396eae97ed
- Trace SHA-256: e0689709e8bf5d3825e198353f43e7e746452209b0c2a93daf4f95297e3345bf
- Context-manifest SHA-256: db15bf0bc63a41f14aa621ceb4209a0d458653ca3110667e21411cc93aa3044e
- Repair-manifest SHA-256: b4ddd9b0fc35e38c859c386820df1637d7f42ebd3a75b4ace7874ec479204e63
- Workspace source SHA-256: 0d010ba525a99b0e39266add08db454beb07d3e492844194218e1c77cf93b189
- Workspace source-metadata SHA-256: 0cbe9796d94d4d7cdf72abc171d3ca8807fa48df3ef79be4b52654c8f7095117
- Generated 3.yaml: absent; no hash
- Generated 3.test.yaml: absent; no hash
- Signed apply manifest: absent; no hash

### Paragraph (1), run aac3cc36

- Run root: /private/tmp/axiom-19237-p1-signed-20260830.AWLVp6
- Output files: 19
- Run-row JSON SHA-256: f0bcef4db3f7b09154339697b42befbcb93ae92faae0b30e6b77240e633a8644
- Session JSON SHA-256: 3057d11a01954c3982719f77ce0bb119c35dfbf08eb77ac3b0a0fe7f6d0800f5
- Isolated database SHA-256: 8b73d10e5fe59173f415b91334a1e46a4d3134e63b1e373b5e100f2d85deeb01
- Output-tree custody digest: 549c8e41d5a95275fa13b52047d73bed6bb6a85eece7e2d92b76631e64072fa7
- Trace SHA-256: 16b89e1d9fef550e26b5a9378eb4c00e8174022051383bcf9ed9bbcb23e653fb
- Context-manifest SHA-256: 781bb90143f80f3c961c248b97c3d9174d8d822b76517ec394b88511933520d3
- Repair-manifest SHA-256: 500bdfed49f4e25c060c9b375a8c16c46995872796fb13f2414b4f930c543f4e
- Workspace source SHA-256: 49612cc6702c892b8d85c0041f50a68daf93ddeff9633d90925b5cd9f624b9a0
- Workspace source-metadata SHA-256: 376ead3698f0679deb358cbb8424bb1250853d932379b8ec876b4bde62b844b2
- Generated 1.yaml: absent; no hash
- Generated 1.test.yaml: absent; no hash
- Signed apply manifest: absent; no hash

## Prior failed-run continuity

The earlier non-applying paragraph-(3) probe remains a historical precursor only:

- Run/session: b07c2bf8 / encode-b07c2bf8
- Status: standalone_failed
- Apply requested: false
- RuleSpec bytes: 0
- Trace SHA-256: 2ceef221ad8042c3831eee337b823e352239d343316d2bf39ed33c1eda8fe454
- Context-manifest SHA-256: f4a668dd0375cbabf441745d56cd09c1caeb735c6e681a84cde470d079cc9cba
- Repair-manifest SHA-256: dc263df886ca389b904101f172c25c09a17c5a5faf76310a0c38ef93919b1539
- Workspace source SHA-256: 0d010ba525a99b0e39266add08db454beb07d3e492844194218e1c77cf93b189
- Workspace source-metadata SHA-256: 639cd6b83b93f692920be56ba1e2ea02037b8f22b13fc10abcf7df711d3b0ecb
- Canonical run-row export SHA-256: f5b9bb3ba0da5174ceed256c5deb43a0eb9e0ae8c28de9cbec923aa8dd922218
- Session export SHA-256: d38baba475d8aa1468b39259f4c7f8eda9f724893269b43ab570bb4e1ce0e9e7

Its output remains under /Users/maxghenis/.Trash/axiom-19237-b07c2bf8-encoding-output. It was not promoted, copied, repaired, or used as generated content.

## Generated and live file state

All definition artifacts are absent:

| Definition | Canonical rule | Companion test | Signed apply manifest | State |
| --- | --- | --- | --- | --- |
| (3) | us/statutes/42/19237/3.yaml | us/statutes/42/19237/3.test.yaml | us/.axiom/encoding-manifests/statutes/42/19237/3.json | All absent |
| (1) | us/statutes/42/19237/1.yaml | us/statutes/42/19237/1.test.yaml | us/.axiom/encoding-manifests/statutes/42/19237/1.json | All absent |

The legacy-root manifest paths .axiom/encoding-manifests/us/statutes/42/19237/3.json and .axiom/encoding-manifests/us/statutes/42/19237/1.json are also absent.

No generated candidate, test, or manifest was hand-edited, repaired, copied, signed manually, or restored from another run. Because generation created no live artifacts, definition-specific restoration required no deletion. The trace, context, repair, and isolated database records outside the worktree are retained as audit custody, not policy output.

## Required legal structure and proof atoms

### Paragraph (3)

The acceptance contract requires foreign entity AND (A OR B OR C OR D OR E). Every designation, list status, covered-nation status, relationship, Attorney General allegation, same-activities conviction, conviction authority, Commerce determination, Defense consultation, DNI consultation, unauthorized-conduct fact, and detriment fact must remain an external evaluation-time dynamic fact. No current entity, list, nation, alias, or relationship may be frozen.

Required proof source paths:

- us/statute/42/19237/3 for the paragraph chapeau
- us/statute/42/19237/3/A
- us/statute/42/19237/3/B
- us/statute/42/19237/3/C
- us/statute/42/19237/3/D
- us/statute/42/19237/3/D/i
- us/statute/42/19237/3/D/ii
- us/statute/42/19237/3/D/iii
- us/statute/42/19237/3/D/iv
- us/statute/42/19237/3/D/v
- us/statute/42/19237/3/D/vi
- us/statute/42/19237/3/D/vii
- us/statute/42/19237/3/E
- us/statute/42/19237 only for enactment and the 2022-08-08 literal-false sentinel

Observed generated proof atoms: none. Proof validation was not run because 3.yaml does not exist.

### Paragraph (1)

The acceptance contract requires an individual, an externally adjudicated substantive/meaningful contribution to scientific development or execution of the proposed R&D project, and external designation by the same Federal research agency concerned. A title, role, name, free text, hours, or other deterministic proxy cannot decide the qualitative contribution.

Required proof source paths:

- us/statute/42/19237/1 for the paragraph chapeau
- us/statute/42/19237/1/A for substantive/meaningful contribution
- us/statute/42/19237/1/B for same-agency designation
- us/statute/42/19237 only for enactment and the 2022-08-08 literal-false sentinel

Observed generated proof atoms: none. Proof validation was not run because 1.yaml does not exist.

## Fixture counts and distinct states

| Definition | Companion file | Generated cases | holds | not_holds | Expected-error cases | Distinct observed states |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Paragraph (3) | Absent | 0 | 0 | 0 | 0 | None |
| Paragraph (1) | Absent | 0 | 0 | 0 | 0 | None |

The unexecuted paragraph-(3) acceptance matrix requires 20 independent positive leaves: A; B; four C relationship alternatives; twelve D authority alternatives; and two E detriment alternatives. It also requires the foreign-entity conjunction, all-false, C conjunction failures, D chapeau failures, E conjunct failures, dynamic/missing-input probes, and a fully positive 2022-08-08 not_holds case.

The unexecuted paragraph-(1) matrix requires scientific-development and execution positives, both conjuncts, same- and different-agency cases, non-individual, false and missing contribution/designation/linkage facts, and a fully positive 2022-08-08 not_holds case.

The current companion-test harness has no expected-runtime-error field. That limitation must never be worked around by defaulting a missing dynamic fact to false. Any future candidate must use direct raw Rust requests to establish missing-input errors.

## Real Rust commands and results

The selected real Rust runtime was exercised through the pinned encoder on the unchanged accepted OR-definition baseline:

    /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode/.venv/bin/axiom-encode test \
      /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us/statutes/8/1641/b.test.yaml \
      --root /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us \
      --axiom-rules-engine-path /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine \
      --json

Result: exit 0; success=true; test_files=1; cases=4; compiled_programs=1; failures=[].

This confirms the pinned Rust runtime operates. It is not target-definition evidence.

The exact target commands were not invoked because their required generated inputs are absent:

    /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode/.venv/bin/axiom-encode test \
      /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us/statutes/42/19237/3.test.yaml \
      --root /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us \
      --axiom-rules-engine-path /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine \
      --json

    /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode/.venv/bin/axiom-encode proof-validate \
      /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us/statutes/42/19237/3.yaml \
      --json

    AXIOM_RULESPEC_REPO_ROOTS=/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a \
      /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine/target/debug/axiom-rules-engine compile \
      --program /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us/statutes/42/19237/3.yaml \
      --output /private/tmp/axiom-19237-p3-retry2-20260830.wJfxTB/3.compiled.json

    /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine/target/debug/axiom-rules-engine run-compiled \
      --artifact /private/tmp/axiom-19237-p3-retry2-20260830.wJfxTB/3.compiled.json \
      < /private/tmp/axiom-19237-p3-retry2-20260830.wJfxTB/3-request.json

    /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode/.venv/bin/axiom-encode test \
      /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us/statutes/42/19237/1.test.yaml \
      --root /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us \
      --axiom-rules-engine-path /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine \
      --json

    /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode/.venv/bin/axiom-encode proof-validate \
      /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us/statutes/42/19237/1.yaml \
      --json

    AXIOM_RULESPEC_REPO_ROOTS=/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a \
      /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine/target/debug/axiom-rules-engine compile \
      --program /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a/us/statutes/42/19237/1.yaml \
      --output /private/tmp/axiom-19237-p1-signed-20260830.AWLVp6/1.compiled.json

    /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine/target/debug/axiom-rules-engine run-compiled \
      --artifact /private/tmp/axiom-19237-p1-signed-20260830.AWLVp6/1.compiled.json \
      < /private/tmp/axiom-19237-p1-signed-20260830.AWLVp6/1-request.json

The compile, request, and run-compiled files named above do not exist; these command forms were not executed.

Target results:

- Paragraph (3) generated-fixture cases: 0
- Paragraph (3) compiled target programs: 0
- Paragraph (3) direct real-Rust route/adversary/missing/time cases: 0
- Paragraph (1) generated-fixture cases: 0
- Paragraph (1) compiled target programs: 0
- Paragraph (1) direct real-Rust conjunct/agency/missing/time cases: 0

No request JSON or compiled target artifact was created, and no hand-written parallel evaluator was substituted.

## Final accept/reject decisions

### § 19237(3): reject

Two fresh, isolated, apply-requested runs failed before generation. There is no unchanged signed RuleSpec, no companion test, no complete proof, no adversarial fixture matrix, and no target Rust evidence. Nothing is retained.

### § 19237(1): reject

The separate fresh, isolated, apply-requested run also failed before generation. There is no separately faithful unchanged signed RuleSpec, no companion test, no complete proof, no same-agency fixture matrix, and no target Rust evidence. Nothing is retained.

The final policy state remains fail-closed with both definitions absent.
