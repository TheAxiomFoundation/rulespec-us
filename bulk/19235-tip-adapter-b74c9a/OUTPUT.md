# NSF TIP implementation adapter report

## Decision

**REJECT — pre-generation custody gate blocked.** No RuleSpec, companion
fixture, apply manifest, repair artifact, compiled artifact, or runtime result
was created or retained. The required existing signing key could not be read
through `agent-secret`, so a signed encoder-first apply was impossible. No
alternate key, retroactive signature, manual RuleSpec, or parallel evaluator
was used.

The worktree retains only this report, `PROGRESS.md`, and the authorized
`ENCODING_BRIEF.md`; all are audit documentation under the repository-permitted
`bulk/` tree.

## Base and worktree

- Canonical repository: `/Users/maxghenis/TheAxiomFoundation/rulespec-us`
- Detached worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19235-tip-adapter-20260830-codex-b74c9a`
- Required/base commit: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Existing local `origin/main`: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Fresh-fetch status: two `git fetch origin main` attempts failed before any
  ref change because the sandbox had no DNS configuration and could not
  resolve `github.com`.
- Canonical content root for a future apply: `<worktree>/us`
- Accepted/candidate worktrees and axiom-corpus PR #631: untouched
- Push, PR, merge, publication, and deployment: none

## Source custody

Requested logical corpus citation:

`us/guidance/nsf/research-security/tip-person-entity-of-concern/implementation`

Future canonical RuleSpec source ID:

`us:policies/nsf/research-security/tip-person-entity-of-concern/implementation`

- Corpus HEAD: `129dae01c6f7a4787bc7678d4a97a478f3934d9f`
- Corpus tree: `acc919b84ab1854c7b227e6578529a0b2dd7a3f4`
- Target provision ID: `39bcc301-2820-5a7d-89b3-8ec3ad77285b`
- Exact provision-body SHA-256: `de23799bdc7629f8691faccec0a7b45a0873b10ea7bf409212032699a12ed738`
- Raw provision record plus newline SHA-256: `b241d967c0541957fe6ea601ac50a43cc81f3dc8776c34f98761e490cb857c20`
- Encoder-normalized source text SHA-256 (`body.strip()` plus newline): `13ab51e73528799565246c6ecefe790346afe858da23c805e254f6fbb9c57091`
- Raw NSF HTML SHA-256: `161ff22863b12f79cdc783b7bd8a265909b98899a0e79bacbb6ceff4e8d56275`
- Guidance provisions JSONL SHA-256: `a16f78fee0769493e9ba11d4e7c154b84536158fb6091cef8721b8f8fc482a89`
- Guidance inventory SHA-256: `5b5433685a24e613c69375c376cc4dabb1efa5faa48e036a410d0948931f82c7`
- Guidance coverage SHA-256: `f31dbf081095cdbcf3230ebd810587ab11ecb7914f1babb96300aa4ad00b32a3`
- Corpus manifest SHA-256: `86846900f5b137e1e5392f2cc464fd569114a3484258abe7ec00ba7af982538e`
- Ingest report SHA-256: `99eb18197aeb10a8aa4885e41863b4745fed7cdc5cd6d23201e9e47fbd6d8b20`

The corpus metadata explicitly records `dynamic_external_lists: true` and
`prohibited_entity_names_must_not_be_encoded: true`.

Higher-authority custody:

- 42 U.S.C. 19235 provision ID: `b6c4799b-d99b-5528-81e0-99b157d02b2b`
- 42 U.S.C. 19235(1) provision ID: `525f0145-8151-5ac1-9c84-db3a64a75c13`
- OLRC Title 42 archive SHA-256: `31929c28f117362ac8788607242795769b05ed7726f07e4ed3b1786f39655ce7`
- Archived `usc42.xml` SHA-256: `b72955590abe55bdbd1ce5d13c5293955a82add9c84fad92c1674ec469e86624`
- Statute provisions JSONL SHA-256: `566a513343f88d5a4944c591ef86464dcd27ea8dce8a4dd730f05efec4f69aa4`
- Statute inventory SHA-256: `02a23fd00306ec320c5fc4c1448c356051e47007de2e7bb167203e96c3b8bd12`
- Statute coverage SHA-256: `07aa0d455d923bc6c9a2e34040b583f2365f1dfb41aed7761aae74afb582f03e`
- Effective date: `2022-08-09`, from the official USLM source credit for
  Pub. L. 117-167, div. B, title VI, section 10636, Aug. 9, 2022,
  136 Stat. 1669.

The NSF page publication/update, guidance snapshot, statute snapshot, and linked
2021/2024/2025/2026 list-version dates are not the prohibition's effective date.

## Tool custody

- `axiom-encode` version: `0.2.1200`
- `axiom-encode` HEAD/tree: `3869d66d009f52258be35901edbef370e65a399c` / `d2ce31c8073b4bc0b4b169b9273f394650094230`
- `axiom-encode` `uv.lock` SHA-256: `ff0ea7983fe344be90ab54b388b0c4c441a1ac69ecf73937440d12802d92d5fc`
- `axiom-rules-engine` HEAD/tree: `ffd8213271947b0189a9dd61a055c1e0e78908a0` / `86e78cc74fffe774fe0ba010c0a951ca1dfcc000`
- Engine `Cargo.lock` SHA-256: `56f01fb4b5118a479328fbffd55b93635ed11038de60bcdd206b88aad84d16cb`
- Existing real debug binary SHA-256: `ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb`

Both tool worktrees were clean when pinned.

## Run and signed custody

No encoder run started because signing was preflighted first.

- Run ID: none
- Generation-prompt SHA-256: none
- Generated-output SHA-256: none
- Trace SHA-256: none
- Context-manifest SHA-256: none
- Signed apply-manifest SHA-256/signature: none
- Applied-file SHA-256 values: none
- Repair manifest: none

`agent-secret search axiom` returned `missing unlock password`; the prescribed
`agent-secret init` then reported that the existing keychain's stored unlock
password is missing. The required service is
`agent/axiom-encode-apply-signing-key`. The key was never printed or exposed.

## Files, fixtures, proof, and runtime

Retained audit files:

- `bulk/19235-tip-adapter-b74c9a/PROGRESS.md`
- `bulk/19235-tip-adapter-b74c9a/ENCODING_BRIEF.md`
- `bulk/19235-tip-adapter-b74c9a/OUTPUT.md`

Generated/applied files: none. Therefore:

- Companion fixtures and requested adversarial states: planned in the brief,
  but not generated or executed.
- Strict proof validation: not run; there is no candidate to validate.
- Generated/live byte comparison and signed-manifest guard: not run.
- Real Rust compile and `run-compiled`: not run.
- Missing dynamic data, historical lookup, and pre-effective runtime states:
  not claimed as passing.

## Required dynamic-registry design

Any acceptable generated adapter must consume caller-supplied, time-indexed
facts and preserve:

`external statutory prerequisite AND TIP covered activity AND (receive OR participate) AND ((person AND section 1237(b) membership) OR (entity AND section 1260H membership))`.

Section 1237(b)/1260H membership, provider/list version, retrieval success,
currentness, and historical as-of coverage remain external dataset facts. No
company or list contents may appear in RuleSpec. Missing interval-covering
membership data must produce a real engine missing-input failure, not silently
mean listed or unlisted. A separate fail-closed/review Judgment may consume
explicit unavailable/stale facts, but it may not become a static registry.

## Resume condition

Resume only after the existing command below succeeds without printing its
value:

`agent-secret get agent/axiom-encode-apply-signing-key`

Then run encoder-first signed apply with `ENCODING_BRIEF.md` as the authorized
same-record/effective-date context, retain the output only if candidate/live
bytes and signed hashes are unchanged, and execute the full generated plus
direct-Rust adversarial matrix. Otherwise restore the generated RuleSpec,
fixture, and signed manifest and keep this decision as reject.
