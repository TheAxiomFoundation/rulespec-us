# 42 U.S.C. § 19237 atomic encoding final report

## Outcome

No statutory definition is accepted and no generated RuleSpec output is retained.

| Definition | Decision | Generated fixtures | Proof | Direct target Rust checks | Retained rule/test/manifest |
| --- | --- | ---: | --- | ---: | --- |
| § 19237(3), foreign entity of concern | **Reject** | 0 | Not run; no rule exists | 0 | None |
| § 19237(1), covered individual | **Reject / not attempted** | 0 | Not run; no rule exists | 0 | None |

Paragraph (3) could not enter the required signed-apply workflow because the dedicated `agent-secret` keychain cannot retrieve its unlock password. A separate non-applying connectivity probe then failed before generation with zero tokens and no candidate. Paragraph (1) was not attempted after both prerequisites failed for the priority definition. This prevents any claim of proof completeness, adversarial fixture coverage, or route-level Rust success.

## Worktree and base custody

- Detached worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19237-atomic-20260830-codex-1959-a`
- Required base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Detached worktree starting object: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Recorded `origin/main`: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Detachment verified: `HEAD` had no symbolic branch.
- Initial worktree diff: zero tracked changes, zero deleted files, and zero untracked files.
- Accepted branches: not checked out or modified. The canonical checkout's divergent local `main` was not used.
- Fetch truth: `git fetch origin main --prune` was attempted on 2026-08-30 and failed with `Could not resolve host: github.com`. The existing remote-tracking ref exactly matched the user-specified object, but this report does not claim that the fetch succeeded or that the ref was freshly refreshed during this run.
- Local detached commits made under the opening standing order before this report checkpoint:
  - `15582c453d04135df559d424aaaed37a5ccc8edd` — `chore: initialize 19237 atomic encoding ledger`
  - `5beca879de6fe65a95af508a4a37d905df2715a4` — `docs: record 19237 source and custody audit`
  - `0a0909ae65ddb7854de28c4c8255fffb1bb8a1a7` — `docs: record rejected 19237 encoder run`
- No push, pull request, merge, production action, or accepted-branch commit was performed.

## Official source custody

Corpus checkout:

- Path: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830`
- Clean HEAD: `129dae01c6f7a4787bc7678d4a97a478f3934d9f`
- Provisions: `data/corpus/provisions/us/statute/2026-08-30-proposal-security-title-42.jsonl`
  - Section record: line 101
  - Paragraph (1) and children: lines 102–104
  - Paragraph (3), children (A)–(E), and (D)(i)–(vii): lines 106–118
- Raw USLM: `data/corpus/sources/us/statute/2026-08-30-proposal-security-title-42/uslm/usc42.xml`
  - § 19237 hierarchy: lines 499756–499788
  - Source credit: line 499816
- Retained official OLRC ZIP: `data/corpus/sources/us/statute/2026-08-30-proposal-security-title-42/olrc/xml_usc42@119-102.zip`
- Inventory: `data/corpus/inventory/us/statute/2026-08-30-proposal-security-title-42.json`
- Coverage: `data/corpus/coverage/us/statute/2026-08-30-proposal-security-title-42.json`
- Coverage state: complete, 133/133 matched, with no missing, extra, or duplicate citations.

SHA-256 custody:

| Artifact | SHA-256 |
| --- | --- |
| Provisions JSONL | `566a513343f88d5a4944c591ef86464dcd27ea8dce8a4dd730f05efec4f69aa4` |
| Inventory JSON | `02a23fd00306ec320c5fc4c1448c356051e47007de2e7bb167203e96c3b8bd12` |
| Coverage JSON | `07aa0d455d923bc6c9a2e34040b583f2365f1dfb41aed7761aae74afb582f03e` |
| Official OLRC ZIP | `31929c28f117362ac8788607242795769b05ed7726f07e4ed3b1786f39655ce7` |
| Extracted/archive-member USLM XML | `b72955590abe55bdbd1ce5d13c5293955a82add9c84fad92c1674ec469e86624` |
| Full § 19237 JSONL record body | `315606f96e8ae6a6db4763139f396ec7cf8ec57a5faa951a437a8c4f7e981b31` |
| Paragraph (1) JSONL line | `9e0bc9c9450756cec549336d87df1f1603680b76d83c21f7ff1dbd285151325b` |
| Paragraph (1) exact body | `8efb20143a78a9992615e9608fa76e439848cb703f78c14945433e04ca11a022` |
| Paragraph (3) JSONL line | `aa3970b6e9c252e1c54a255b8ab13e30d09c99990e2300138ec7c5c2b4d25784` |
| Paragraph (3) exact body | `5c004e80518222e8865a533828c4b60a75459668106499aeacc2acb7413806d4` |

The source credit is Pub. L. 117–167, division B, title VI, § 10638, enacted 2022-08-09, 136 Stat. 1669. The corpus has no separate effective-date field or note for this section. Any accepted encoding therefore needed a literal-false version on 2022-08-08 and the operative formula on 2022-08-09.

## Audited legal structure

Paragraph (3) must be `foreign entity AND (A OR B OR C OR D OR E)`.

- (A): external Secretary of State foreign-terrorist-organization designation specifically under 8 U.S.C. § 1189(a).
- (B): external inclusion on the OFAC-maintained SDN list.
- (C): external covered-nation status under 10 U.S.C. § 4872, not § 19237(2), AND one of four same-government relationships: ownership, control, jurisdiction, or direction.
- (D): external Attorney General allegation AND conviction for the same activities AND one of twelve exact authority alternatives represented by child paths `/3/D/i` through `/3/D/vii`.
- (E): external Secretary of Commerce determination, Defense consultation, DNI consultation, unauthorized-conduct predicate, and national-security OR foreign-policy detriment.

The exact paragraph/chapeau path is `us/statute/42/19237/3`; exact children are `/3/A`, `/3/B`, `/3/C`, `/3/D`, `/3/D/i` through `/3/D/vii`, and `/3/E`. Every designation, list, covered-nation, relationship, allegation, conviction, determination, consultation, conduct, and detriment fact must remain dynamic. A name or alias cannot establish any route.

Paragraph (1) must require all of the individual chapeau, a caller-reviewed substantive/meaningful contribution predicate for the proposed R&D project, and designation by the same Federal research agency concerned. Its exact paths are `us/statute/42/19237/1`, `/1/A`, and `/1/B`. The qualitative contribution cannot be decided from free text, role, title, name, or a deterministic proxy.

## Encoder, signing, and run custody

Selected encoder:

- Path: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode`
- Clean detached HEAD and committed version source: `3869d66d009f52258be35901edbef370e65a399c`
- Version: `0.2.1200`
- Executable: `.venv/bin/axiom-encode`
- Executable SHA-256: `6d134a9820f10826d3cb56e1a0df755636cad8543051811acc2f0be102af0173`
- Provenance preflight: `dirty_tracked=false`; `commit` and `version_commit` both equal the selected HEAD.

Signed apply never started. The required command `agent-secret get agent/axiom-encode-apply-signing-key` failed before exposing a value with `missing unlock password. Run: agent-secret init`; `AXIOM_ENCODE_APPLY_SIGNING_KEY` was unset. The dedicated keychain file exists, but its login-keychain unlock-password record is missing. No alternate key source was queried and no signing value was invented, printed, or bypassed.

One non-applying connectivity probe used the actual encoder with:

- Citation: `us/statute/42/19237/3`
- Backend/model: `codex` / `gpt-5.5`
- Mode: `repo-augmented`
- Official corpus, selected Rust engine, and this detached policy repo passed explicitly.
- `--no-sync` was used; `--apply`, `--apply-target-only`, and `--skip-reviewers` were not used.
- Operator context required all 20 positive paragraph-(3) OR leaves, dynamic predicates, exact provenance, missing-fact adversaries, a nonforeign adversary, and the pre-enactment false version.

Run result:

- Run ID: `b07c2bf8`
- Session ID: `encode-b07c2bf8`
- Encoder-recorded duration: 53,658 ms
- Retrieved context files: 14
- Model tokens: 0 input, 0 output, 0 cache-read, 0 reasoning-output
- Status: `standalone_failed`
- Apply state: `apply_requested=false`, `applied_files=[]`
- Failure: the Codex response stream disconnected after DNS/send retries to the ChatGPT Codex response endpoint.
- Candidate bytes recorded in the run database: 0
- Candidate `3.yaml`: absent
- Generated `3.test.yaml`: absent

Failed-run custody hashes recorded before cleanup:

| Artifact | SHA-256 |
| --- | --- |
| Trace JSON | `2ceef221ad8042c3831eee337b823e352239d343316d2bf39ed33c1eda8fe454` |
| Context manifest JSON | `f4a668dd0375cbabf441745d56cd09c1caeb735c6e681a84cde470d079cc9cba` |
| Repair manifest JSON | `dc263df886ca389b904101f172c25c09a17c5a5faf76310a0c38ef93919b1539` |
| Workspace source text | `0d010ba525a99b0e39266add08db454beb07d3e492844194218e1c77cf93b189` |
| Workspace source metadata | `639cd6b83b93f692920be56ba1e2ea02037b8f22b13fc10abcf7df711d3b0ecb` |
| Paragraph (3) acceptance context | `2eeb2aedf0994d097c953198f92343fefda3c282273353c285dfaa71a5384bd7` |
| Paragraph (1) acceptance context | `54c3cd94ca645e10ce222580a475442489133b4ee81255b0d15d40e8b0b5b0e4` |
| Source-credit continuation | `3b1135b5003f1e725b7287a4d32b3067a1db651e5b28a2f5bacdb3a7141a8e7e` |
| Canonical run-row JSON export | `f5b9bb3ba0da5174ceed256c5deb43a0eb9e0ae8c28de9cbec923aa8dd922218` |
| Session JSON export | `d38baba475d8aa1468b39259f4c7f8eda9f724893269b43ab570bb4e1ce0e9e7` |
| Local encoding database at audit time | `1ff2fba787dce7f3b489f583d8225f1128a7585dd2cb179b2a4d29007875fead` |

The local run database is `/Users/maxghenis/TheAxiomFoundation/axiom-encode/encodings.db`. The failed output and operator-context directories were moved out of the worktree to the Trash after hashing; no generated candidate was among them. The durable database run/session rows remain as the encoder audit record.

## Generated/applied file state

All expected definition artifacts are absent:

| Definition | Canonical rule | Companion test | Current apply manifest | State |
| --- | --- | --- | --- | --- |
| (3) | `us/statutes/42/19237/3.yaml` | `us/statutes/42/19237/3.test.yaml` | `us/.axiom/encoding-manifests/statutes/42/19237/3.json` | All absent |
| (1) | `us/statutes/42/19237/1.yaml` | `us/statutes/42/19237/1.test.yaml` | `us/.axiom/encoding-manifests/statutes/42/19237/1.json` | All absent |

The legacy-root manifest equivalents under `.axiom/encoding-manifests/us/statutes/42/19237/` are also absent. No generated file was copied, edited, repaired, signed manually, or committed.

## Fixture, proof, and Rust results

Paragraph (3):

- Generated fixture count: 0.
- Fixture states: none.
- Required positive matrix had 20 independently exposed leaves: A; B; four C relationships; twelve D authority alternatives; and two E detriment alternatives.
- Required adversaries included all-false, nonforeign, both C conjunction failures, missing Attorney General allegation, missing same-activities conviction, no D authority, each E determination/consultation/conduct/detriment failure, omitted dynamic facts, and 2022-08-08.
- Proof validation: not run because no `3.yaml` exists.
- Companion test execution: not run because no `3.test.yaml` exists.
- Compiled target artifact: none.
- Direct Rust route/adversary checks: 0; no target program existed to compile.

Paragraph (1):

- Generated fixture count: 0.
- Fixture states: none.
- Proof validation: not run because no `1.yaml` exists.
- Companion test execution: not run because no `1.test.yaml` exists.
- Direct Rust conjunct/missing-fact/pre-effective checks: 0; no target program existed to compile.

Selected real Rust runtime:

- Path: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine`
- Clean detached HEAD: `ffd8213271947b0189a9dd61a055c1e0e78908a0`
- Binary: `target/debug/axiom-rules-engine`
- Binary SHA-256: `ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb`
- Runtime baseline only: the existing accepted OR-definition companion `us/statutes/8/1641/b.test.yaml` ran through the selected real engine with 1 file, 4/4 cases, 1 compiled program, and zero failures. This confirms the selected runtime operates; it is not a substitute for any missing § 19237 target check.

## Final retention and next action

The worktree was restored to committed evidence only. No § 19237 rule, test, manifest, compiled artifact, request, response, or fixture is retained or claimed as accepted.

A future run must first restore the existing `agent-secrets/keychain-password` login-keychain record so the exact signing service can be read through `agent-secret`, and restore working Codex backend DNS/connectivity. It must then execute a fresh `axiom-encode encode ... --apply --no-sync` run. The failed dry run cannot be promoted or copied. Only unchanged signed output that passes the full generated fixture matrix, exact proof audit, source staleness, signature guard, and direct Rust checks may be retained.
