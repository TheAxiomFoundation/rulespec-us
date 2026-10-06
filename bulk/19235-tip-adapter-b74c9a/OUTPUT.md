# NSF TIP implementation adapter report

## Decision

**REJECT — generation transport failed before candidate creation or signed
apply.** Two fresh runs of the task-specific pinned `axiom-encode` resolved the
exact official guidance record and copied the unchanged encoding brief into the
evaluation workspace. Both runs then failed at DNS/transport before the model
returned a token. Their apply events report `applied_files: []` and
`apply_blocked_generation`.

No RuleSpec, companion test, apply manifest, signature, proof artifact, oracle
fixture, compiled artifact, direct-Rust request, or runtime result was created
or retained in the policy repository. The target paths were absent before the
runs and remain absent. This is the required fail-closed outcome: there is no
unsigned or manually authored substitute to accept.

The approved signing environment was consumed only through the two unchanged
`axiom-encode encode --apply` processes. Generation failed before signing. No
inspection command referenced its value, and post-attempt validation and
reporting commands explicitly removed it from their child environments. The
value was never printed, logged, hashed, inspected, copied, or rotated.

## Base, worktree, and mutation custody

- Canonical repository: `/Users/maxghenis/TheAxiomFoundation/rulespec-us`
- Task worktree:
  `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19235-tip-adapter-20260830-codex-b74c9a`
- Worktree mode: detached HEAD
- Resumed HEAD: `78e6ca4b34fba519f042a0eb9347e57ad8bda003`
- Required live upstream base and local `origin/main`:
  `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Base tree: `20a8f964f20b4a4bfdedc239245c5d1dbafe3f29`
- Canonical policy root used by both runs:
  `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19235-tip-adapter-20260830-codex-b74c9a/us`
- Requested corpus leaf:
  `us/guidance/nsf/research-security/tip-person-entity-of-concern/implementation`
- Generated module target, distinct from corpus provenance:
  `us:policies/nsf/research-security/tip-person-entity-of-concern/implementation`

The only task files changed from the resumed committed state are this configured
report and `PROGRESS.md`. `ENCODING_BRIEF.md` remains byte-for-byte unchanged at
SHA-256 `44c268c49e21c8094b00237e1bcba6d54beb7e87d2e6d02ad3514ca95f9620a3`.
No file under `us/` changed. No branch, commit, fetch, push, PR, merge, deploy,
publication, or production action occurred. Accepted worktrees and axiom-corpus
PR #631 were not modified.

Expected apply paths, all absent before and after both runs:

- `us/policies/nsf/research-security/tip-person-entity-of-concern/implementation.yaml`
- `us/policies/nsf/research-security/tip-person-entity-of-concern/implementation.test.yaml`
- `us/.axiom/encoding-manifests/policies/nsf/research-security/tip-person-entity-of-concern/implementation.json`

Because no generated policy file was installed, restoration required no file
deletion or checkout operation. The two temporary output roots contain only
failed-run custody material and no candidate YAML.

## Official guidance custody

Corpus worktree:
`/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830`

- Corpus HEAD/tree:
  `129dae01c6f7a4787bc7678d4a97a478f3934d9f` /
  `acc919b84ab1854c7b227e6578529a0b2dd7a3f4`
- Corpus Git state after the runs: clean
- Guidance URL:
  `https://www.nsf.gov/research-security/person-or-entity-concern-prohibition`
- Target record ID: `39bcc301-2820-5a7d-89b3-8ec3ad77285b`
- Record expression/source-as-of date: `2026-08-30`
- Page publication date recorded in the retained HTML: `2025-07-03`
- Page last-updated date recorded in the retained HTML: `2026-06-18`
- Exact provision-body SHA-256:
  `de23799bdc7629f8691faccec0a7b45a0873b10ea7bf409212032699a12ed738`
- Raw JSONL record plus newline SHA-256:
  `b241d967c0541957fe6ea601ac50a43cc81f3dc8776c34f98761e490cb857c20`
- Encoder-normalized source text SHA-256 (`body.strip()` plus newline):
  `13ab51e73528799565246c6ecefe790346afe858da23c805e254f6fbb9c57091`
- Retained raw NSF HTML SHA-256:
  `161ff22863b12f79cdc783b7bd8a265909b98899a0e79bacbb6ceff4e8d56275`
- Guidance provisions JSONL SHA-256:
  `a16f78fee0769493e9ba11d4e7c154b84536158fb6091cef8721b8f8fc482a89`
- Guidance inventory SHA-256:
  `5b5433685a24e613c69375c376cc4dabb1efa5faa48e036a410d0948931f82c7`
- Guidance coverage SHA-256:
  `f31dbf081095cdbcf3230ebd810587ab11ecb7914f1babb96300aa4ad00b32a3`
- Source manifest SHA-256:
  `86846900f5b137e1e5392f2cc464fd569114a3484258abe7ec00ba7af982538e`
- Ingest report SHA-256:
  `99eb18197aeb10a8aa4885e41863b4745fed7cdc5cd6d23201e9e47fbd6d8b20`
- Coverage result: complete, 25 source records matched to 25 provisions, with
  no missing, extra, or duplicate citations

The retained record explicitly sets `dynamic_external_lists: true` and
`prohibited_entity_names_must_not_be_encoded: true`.

For exact link custody only, the retained NSF HTML points to these external
list notices. Their contents and membership results were not imported,
enumerated, or frozen:

- §1260H notice dated `2026-06-10`:
  `https://www.federalregister.gov/documents/2026/06/10/2026-11571/notice-of-availability-of-designation-of-chinese-military-companies`
- §1260H prior notice dated `2025-01-07`:
  `https://www.federalregister.gov/documents/2025/01/07/2025-00070/notice-of-availability-of-designation-of-chinese-military-companies`
- §1260H prior notice dated `2024-04-02`:
  `https://www.federalregister.gov/documents/2024/04/02/2024-06895/notice-of-availability-of-designation-of-chinese-military-companies`
- §1260H prior notice dated `2021-06-28`:
  `https://www.federalregister.gov/documents/2021/06/28/2021-13753/notice-of-designation-of-chinese-military-companies-under-the-william-m-mac-thornberry-ndaa-for-fy21`
- §1237(b) final notice dated `2021-06-28`:
  `https://www.federalregister.gov/documents/2021/06/28/2021-13755/notice-of-the-removal-of-the-designation-as-communist-chinese-military-companies-under-the-strom`

Those notice dates, the NSF publication/update dates, and the corpus snapshot
date are not the adapter's legal effective date.

## Higher-authority and effective-date custody

- 42 U.S.C. §19235 record ID:
  `b6c4799b-d99b-5528-81e0-99b157d02b2b`
- 42 U.S.C. §19235(1) record ID:
  `525f0145-8151-5ac1-9c84-db3a64a75c13`
- Statute view URL:
  `https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title42-section19235&num=0&edition=prelim`
- Official OLRC archive URL:
  `https://uscode.house.gov/download/releasepoints/us/pl/119/102/xml_usc42@119-102.zip`
- OLRC release: `Online@119-102`
- Statute expression/source-as-of date: `2026-07-12`
- OLRC Title 42 archive SHA-256:
  `31929c28f117362ac8788607242795769b05ed7726f07e4ed3b1786f39655ce7`
- Archived `usc42.xml` SHA-256:
  `b72955590abe55bdbd1ce5d13c5293955a82add9c84fad92c1674ec469e86624`
- Statute provisions JSONL SHA-256:
  `566a513343f88d5a4944c591ef86464dcd27ea8dce8a4dd730f05efec4f69aa4`
- Statute inventory SHA-256:
  `02a23fd00306ec320c5fc4c1448c356051e47007de2e7bb167203e96c3b8bd12`
- Statute coverage SHA-256:
  `07aa0d455d923bc6c9a2e34040b583f2365f1dfb41aed7761aae74afb582f03e`
- Coverage result: complete, 133 source records matched to 133 provisions

The official USLM `sourceCredit` for §19235 records Pub. L. 117-167,
division B, title VI, §10636, `2022-08-09`, 136 Stat. 1669. Therefore the
required operative date is `2022-08-09`, with an explicit all-positive false
sentinel on `2022-08-08`. Paragraph (1) is the NSF TIP Directorate branch. The
required upstream-source check remains `us/statute/42/19235` plus
`us/statute/42/19235/1`.

The required-base tree contains no reusable `us/statutes/42/19235` RuleSpec
module. An acceptable narrow adapter must therefore consume an explicit
external statutory-prerequisite fact and must not reproduce §19235 as a
parallel local statute implementation.

## Tool custody

This resumed lane uses its recorded task-specific NSF toolchain. The newer
general workflow validation pin is not the apply tool for this lane and rejects
the explicitly authorized direct signing environment.

Actual `axiom-encode`:

- Worktree:
  `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode`
- Version: `0.2.1200`
- HEAD/tree:
  `3869d66d009f52258be35901edbef370e65a399c` /
  `d2ce31c8073b4bc0b4b169b9273f394650094230`
- `uv.lock` SHA-256:
  `ff0ea7983fe344be90ab54b388b0c4c441a1ac69ecf73937440d12802d92d5fc`
- Executable:
  `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode/.venv/bin/axiom-encode`
- Executable SHA-256:
  `6d134a9820f10826d3cb56e1a0df755636cad8543051811acc2f0be102af0173`
- Git state after both attempts: clean

Actual Rust runtime:

- Worktree:
  `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine`
- HEAD/tree:
  `ffd8213271947b0189a9dd61a055c1e0e78908a0` /
  `86e78cc74fffe774fe0ba010c0a951ca1dfcc000`
- `Cargo.lock` SHA-256:
  `56f01fb4b5118a479328fbffd55b93635ed11038de60bcdd206b88aad84d16cb`
- Executable:
  `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine/target/debug/axiom-rules-engine`
- Executable SHA-256:
  `ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb`
- Git state after both attempts: clean

## Encoder runs and hashes

Both runs used `backend=codex`, `model=gpt-5.5`,
`mode=repo-augmented`, the exact requested guidance leaf, `--source-id` for the
canonical policy target, the unchanged brief as the sole allowed extra context,
the task-specific corpus and Rust paths, the canonical policy root ending in
`/us`, `--no-sync`, and `--apply`.

| Field | Attempt 1 | Attempt 2 |
| --- | --- | --- |
| UTC completion | `2026-08-31T00:36:45Z` | `2026-08-31T00:42:43Z` |
| Fresh output root | `/private/tmp/axiom-19235-tip-adapter-b74c9a.4s0bMo` | `/private/tmp/axiom-19235-tip-adapter-b74c9a-retry2.S6mCrx` |
| Run/session | `a8afeb11` / `encode-a8afeb11` | `ac44a55b` / `encode-ac44a55b` |
| Duration | `63,071 ms` | `78,207 ms` |
| Tokens in/out | `0 / 0` | `0 / 0` |
| Retrieved context files | `1` | `1` |
| Generation prompt SHA-256 | `435fbf6bd9f34b03d8cfc741743a4a5d28e3652463a8eb3cc6d1cf4808a42892` | same |
| Context manifest SHA-256 | `eaa1b1460eb06e7f308c0d07b58580c38b9cf83def8769841f1e9637c33473fa` | same |
| Workspace source metadata SHA-256 | `57e5ad77b80d954d238d00f9f443c37e33fa6e1c332a6cc0b6a32997a130ccdd` | same |
| Workspace source text SHA-256 | `13ab51e73528799565246c6ecefe790346afe858da23c805e254f6fbb9c57091` | same |
| Copied brief SHA-256 | `44c268c49e21c8094b00237e1bcba6d54beb7e87d2e6d02ad3514ca95f9620a3` | same |
| Trace SHA-256 | `99e4aa4c176c36218c96dace390a60cb4df901f8140f8a3b37f9a572a1df1e1a` | `51dd0a21a84eb581c428558933a3c7c62f6fe0b07d5a204bcc497c822f61bcac` |
| Run-log SHA-256 | `36b0aa497e96ec254bb993213732e404587ff859b06aecd3c113925b9fa3e621` | `273e65868be12465f12cc7b958a023a5e3074f91fcc46f2b242e40867b37495d` |
| Failure repair-manifest SHA-256 | `32e203cebf08e3190371ce6b91fcede293dc77f2b567330f80e419f929b369af` | `dbca93a93a7ef68db0f9ca65950a20f30cce3ab344b3f31ae6dca3a2a8f83997` |
| Isolated encoding DB SHA-256 | not configured under attempt-1 root | `db9ecaf9c3ab479edb5c5212af21cb4013aa1a86499bd0166024ef7cfca5e910` |
| Generated main/test SHA-256 | none / none | none / none |
| Signed apply-manifest SHA-256/signature | none / none | none / none |
| Applied files | `[]` | `[]` |

Attempt 1 run log:
`/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode/.axiom/run-logs/a8afeb11.jsonl`

Attempt 2 run log:
`/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode/.axiom/run-logs/ac44a55b.jsonl`

The attempt-2 trace records repeated DNS failures (`failed to lookup address
information`) on WebSocket transport, then the same send failure on the HTTPS
fallback. The two independently hashed TIP attempts establish a transport
failure, not a TIP-specific validation result.

The encoder's mechanical `generate` event uses `status: passed` while its
`reason` records the transport error. The governing retained facts are zero
tokens, absent output, `standalone_validation_success: false`, and the
subsequent failed apply event with `reason_code: apply_blocked_generation`.

## Dynamic-list interface required for any future candidate

No executable input identifiers were generated. The required interface remains
the authorized contract, not an implemented claim:

`external statutory prerequisite AND TIP scope AND covered matter AND
(receive OR participate) AND ((person AND §1237(b) membership) OR
(entity AND §1260H membership))`.

- Person and entity identity facts must remain distinct.
- §1237(b) person membership and §1260H entity membership must remain distinct
  caller-supplied, time-indexed facts.
- Receive and participate must remain distinct facts joined by OR.
- Grant, award, program, support, or other activity coverage must remain
  distinct from TIP Directorate scope.
- The applicable §19235 statutory prerequisite must be an explicit external
  fact because there is no reusable statute module at the required base.
- Provider/list version, retrieval success, currentness, and historical
  interval coverage, if represented, must also be caller-supplied facts.
- Historical membership must cover the queried interval. Omitted or
  non-covering membership data must produce a real missing-input error; it may
  not default to listed or unlisted.
- No current or historical membership result, organization/person name,
  jurisdictional inference, or list snapshot may be frozen into RuleSpec.

## Proof, fixtures, and real Rust results

Generated companion fixture count: **0**. Proof/oracle fixture count: **0**.
Direct-Rust adversary request count: **0**. Compiled artifact count: **0**.

| Required adversarial dimension | Generated fixture | Direct Rust |
| --- | --- | --- |
| §1237(b) person route, listed/unlisted/missing | not emitted | not run |
| §1260H entity route, listed/unlisted/missing | not emitted | not run |
| Person/entity distinction and both wrong-type routes | not emitted | not run |
| Receive and participate branches | not emitted | not run |
| TIP and non-TIP scope | not emitted | not run |
| Covered and non-covered matter kind | not emitted | not run |
| Historical interval-covering membership facts | not emitted | not run |
| Historical missing/non-covering membership facts | not emitted | not run |
| External statutory prerequisite true/false/missing | not emitted | not run |
| All-positive pre-effective `2022-08-08` sentinel | not emitted | not run |

Strict proof validation was not run because no module exists. Therefore there
are zero proof atoms and no claim that the operative formula, both list OR
branches, action OR branches, TIP scope, external prerequisite, upstream source
check, or effective period passed proof validation.

The generated-fixture command was not run because the adjacent test file does
not exist. Its planned command form was:

```text
<pinned-axiom-encode> test <live-implementation.test.yaml> \
  --root <task-worktree>/us \
  --axiom-rules-engine-path <pinned-engine> --json
```

The pinned real Rust runtime was verified by commit and executable hash, but
target compile was not run because the generated module does not exist. The
planned command forms were:

```text
AXIOM_RULESPEC_REPO_ROOTS=<task-worktree>/us \
  <pinned-engine>/target/debug/axiom-rules-engine compile \
  --program <live-implementation.yaml> \
  --output <fresh-output>/direct-rust/implementation.compiled.json

<pinned-engine>/target/debug/axiom-rules-engine run-compiled \
  --artifact <fresh-output>/direct-rust/implementation.compiled.json \
  < <one-adversarial-request.json>
```

No mock evaluator, hand-coded policy formula, parallel statute implementation,
manual fixture, or substitute runtime was used.

Result for every planned fixture, proof, compile, and `run-compiled` command:
**NOT RUN — no generated candidate or companion test exists.**

## Final acceptance status

**Reject and retain no policy artifact.** The keychain issue from the prior
report is no longer the blocker and was not used as a reason to stop. The
current blocker is independently evidenced DNS/transport failure before model
generation. A future retry must use the same exact source leaf, unchanged brief,
task-specific encoder and Rust pins, canonical `/us` policy root, and a new
isolated output/run-log root. Acceptance remains conditional on unchanged
signed generated/live bytes, complete proof, all generated adversarial
fixtures, and matching direct-Rust behavior including missing-input and
pre-effective cases.
