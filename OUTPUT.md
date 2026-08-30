# NSF PAPPG 24-1 Chapter I duplicate-proposal workflow report

## Decision

**REJECT THIS RUN / BLOCKED BEFORE GENERATION.** No RuleSpec module, companion fixture, signed apply manifest, proof result, compiled artifact, or direct-Rust result was created or retained. The canonical policy tree remains byte-for-byte at the required starting base.

Two independent preconditions failed:

1. A fresh `git fetch origin main` could not complete because the sandbox could not resolve `github.com`. The existing remote-tracking ref exactly equals the required commit, but it was last successfully fetched on 2026-08-23, so it is not represented as freshly fetched.
2. Signed apply could not start. The existing `agent-secrets` keychain is present, but `agent-secret` reports that its stored unlock password is missing. The required service is `agent/axiom-encode-apply-signing-key`; the signing value was never read or printed, and no replacement keychain or key was created.

There is also a source-custody acceptance risk that must be resolved before a future run. The current encoder resolves the exact provision body and citation, but its `CorpusSourceUnit` and prompt metadata omit the record's `expression_date: 2024-05-20`. The body contains no date. No arbitrary-context workaround, encoder change, or manual output repair was used. A future run therefore needs either an encoder path that carries this record metadata or explicit authorization to pass a mechanically extracted copy of this same single record as context; coincidental model output is not sufficient date custody.

## Worktree and base

- Detached worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-pappg-24-1-duplicate-review-20260830-codex-195000`
- Required starting commit: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Required starting tree: `20a8f964f20b4a4bfdedc239245c5d1dbafe3f29`
- Local checkpoint commits only:
  - `e866057aa37cb39726a02c8d63a773cfa5dd1581` — initialize `PROGRESS.md`
  - `d3b697487` — record preflight custody and blocker
- Branch state: detached throughout; no branch created or changed.
- The dirty/diverged primary checkout was not used for policy work and was not reset or cleaned.
- The separate axiom-corpus PR #631 worktree/ref and all existing NSF branches/worktrees were not read as legal input or modified.

An initial disposable worktree checkout created during this run was interrupted during index initialization. Its new registration and orphaned partial directory were removed; they are not recoverable. No pre-existing worktree or user-authored data was removed.

## Authorized source and custody hashes

- Corpus worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830`
- Corpus HEAD: `129dae01c6f7a4787bc7678d4a97a478f3934d9f`
- Corpus tree: `acc919b84ab1854c7b227e6578529a0b2dd7a3f4`
- Corpus status during custody check: clean
- Sole authorized citation path: `us/guidance/nsf/pappg/24-1/chapter-i/submission-instructions`
- Record ID: `0a724ccd-9b2b-534c-9bcc-ed391d2511bf`
- Citation label: `PAPPG 24-1 Chapter I: Pre-Submission Information 1`
- Heading: `Chapter I.G.1 Submission Instructions`
- Expression/effective date: `2024-05-20`
- Source as of: `2026-08-30`
- Official source URL: `https://www.nsf.gov/policies/pappg/24-1/ch-1-pre-submission`
- Exact provision-body SHA-256, UTF-8 with no trailing newline: `3e1a117c4a09679284ee79b0fae5b1f619af6e4cb4c6e6415e16e87a88e8804f`
- Raw JSONL record line including newline SHA-256: `0fc72c05862d6b70c64e3e26b36d2f550949c113efa9ca81a6e8fdf3264bb774`
- Normalized compact JSON record plus newline SHA-256: `d47e8abb046267894614c392312db4299a29d4537283c33b110533f3d7fef69d`
- Encoder-normalized `source.txt` bytes SHA-256 (`body.strip()` plus newline): `987275bb6a2723b46698464c61229364955994f549ae733461a794c7865e70fc`
- Raw official HTML SHA-256: `a8f98d21d424ab919458571a268b50c77f7c42164fecfb4bdbe3a94c64197d29`
- Provisions JSONL SHA-256: `a16f78fee0769493e9ba11d4e7c154b84536158fb6091cef8721b8f8fc482a89`
- Inventory JSON SHA-256: `5b5433685a24e613c69375c376cc4dabb1efa5faa48e036a410d0948931f82c7`
- Corpus manifest SHA-256: `86846900f5b137e1e5392f2cc464fd569114a3484258abe7ec00ba7af982538e`

The source body contains a duplicate/substantially-similar proposal paragraph and a separate AOR-certification paragraph. Because generation did not occur, nothing conflates them. A future artifact must keep the AOR text outside this workflow unless it is independently encoded.

## Toolchain custody

### axiom-encode

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode`
- HEAD: `3869d66d009f52258be35901edbef370e65a399c`
- Tree: `d2ce31c8073b4bc0b4b169b9273f394650094230`
- `uv.lock` SHA-256: `ff0ea7983fe344be90ab54b388b0c4c441a1ac69ecf73937440d12802d92d5fc`
- Status during custody check: clean

### axiom-rules-engine

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine`
- HEAD: `ffd8213271947b0189a9dd61a055c1e0e78908a0`
- Tree: `86e78cc74fffe774fe0ba010c0a951ca1dfcc000`
- `Cargo.lock` SHA-256: `56f01fb4b5118a479328fbffd55b93635ed11038de60bcdd206b88aad84d16cb`
- Existing real-Rust debug binary SHA-256: `ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb`
- Status during custody check: clean

## Files and generated artifacts

Retained task ledgers:

- `PROGRESS.md`
- `OUTPUT.md`

Generated policy files retained: **none**.

Expected-but-not-created files:

- `us/policies/nsf/pappg/24-1/chapter-i/submission-instructions.yaml`
- Adjacent `.test.yaml` companion
- Signed apply manifest under `us/.axiom/encoding-manifests/policies/nsf/pappg/24-1/chapter-i/`

## Fixtures, proof, and real Rust

- Encoder run ID/hash: **none; generation did not start**.
- Requested machine result `review_required`: **not encoded or evaluated**.
- Required fixture states (one proposal/multiple designations; concurrent separate proposals with possible overlap; no overlap; no concurrency; external duplicate determination; missing facts; pre-effective time): **not generated or run**.
- Proof validation: **not run; no module exists**.
- Signed-manifest verification and generated-file guard: **not run; no manifest exists**.
- Real-Rust compile artifact/hash: **none; no module exists**.
- Direct-Rust adversaries: **not run; no compiled artifact exists**.

No automated legal conclusion, rejection rule, semantic-similarity computation, or AOR-certification rule was introduced.

## Required continuation conditions

1. Restore access to the existing agent-secrets unlock record so the following succeeds without exposing the value: `agent-secret get agent/axiom-encode-apply-signing-key`.
2. Provide a network-capable fresh fetch or explicitly waive the fresh-fetch requirement while retaining the exact required base.
3. Resolve the dropped effective-date metadata through the encoder itself, or explicitly authorize a mechanically extracted, hash-pinned copy of only the same corpus record as `--allow-context` for generation.

Until all three conditions are satisfied, acceptance would violate the requested source, signature, and custody requirements.

No push, PR, deployment, or change to corpus, encoder, or engine repositories occurred.
