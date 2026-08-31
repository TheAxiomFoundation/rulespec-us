# NSF IN-149 MFTRP certification adapter final report

## Result

**Executable result: rejected; no RuleSpec output retained.**

The source and toolchain preflight, atomic encoding contract, and exact official
continuation inputs are complete and committed. Generation was deliberately not
started because the required signing key could not be obtained through
`agent-secret`. A fresh remote fetch also could not be completed because the
sandbox could not resolve `github.com`. The locally cached `origin/main` object
matches the user-specified base exactly, but this report does not misstate it as
freshly fetched.

Under the requirement to retain only unchanged signed output with complete
proof, generated fixtures, and direct-Rust adversaries, all executable atomic
rules are rejected from retention. No unsigned, manually authored, manually
repaired, or simulated policy artifact was substituted.

## Rulespec base and worktree custody

- Repository: `/Users/maxghenis/TheAxiomFoundation/rulespec-us`
- Remote: `https://github.com/TheAxiomFoundation/rulespec-us.git`
- Required base commit and cached `origin/main`:
  `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Required base tree: `20a8f964f20b4a4bfdedc239245c5d1dbafe3f29`
- Last successful local fetch recorded by the remote-ref reflog:
  `2026-08-23 01:38:32 +0200`
- Fresh-fetch attempts in this run: two; both failed with
  `Could not resolve host: github.com`.
- Unique worktree:
  `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-in149-mftrp-cert-adapter-20260830-codex-b7e4c1`
- Worktree mode: detached HEAD; no branch was created, checked out, or modified.
- Preparation commit 1:
  `d4133c5f85f3d965bbc5fb510a19a7cc94438e4f`
- Preparation commit 2:
  `a23e0a063dced7cbef24908e510a3c3312249c91`
- Preparation commit 2 tree:
  `2586fd062731cda0f26a93780111c9ef508a8461`
- Existing branches, other worktrees, and axiom-corpus PR #631: unchanged.

## Official source custody

- Corpus worktree:
  `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830`
- Corpus commit: `129dae01c6f7a4787bc7678d4a97a478f3934d9f`
- Corpus tree: `acc919b84ab1854c7b227e6578529a0b2dd7a3f4`
- Source-introduction commit:
  `e0564d63595bd4fdb043ee77134c94b3dc218ca8`
- Provision bundle SHA-256:
  `a16f78fee0769493e9ba11d4e7c154b84536158fb6091cef8721b8f8fc482a89`
- Inventory SHA-256:
  `5b5433685a24e613c69375c376cc4dabb1efa5faa48e036a410d0948931f82c7`
- Coverage SHA-256:
  `f31dbf081095cdbcf3230ebd810587ab11ecb7914f1babb96300aa4ad00b32a3`
- Ingest manifest SHA-256:
  `86846900f5b137e1e5392f2cc464fd569114a3484258abe7ec00ba7af982538e`
- IN-149 HTML SHA-256:
  `b80a6a59dbb102e3371b4eab6e90971562e91e551220c892533b2efb3da9cb8d`
- FAQ HTML SHA-256:
  `a80e70b6640477ae3f95cc9a54b394a03aac087d1d17e7ff6fb50c774f5fdf41`

The seven authorized records all have `expression_date: 2025-11-24` and
`source_as_of: 2026-08-30`. The expression date was not treated as an operative
effective date.

| Corpus citation path | Record ID | Exact body SHA-256 |
| --- | --- | --- |
| `us/guidance/nsf/important-notice/149-research-security/3` | `fbc95392-8ffc-5043-8978-ff07f6610c79` | `d5c4c85696d21c370097a702a1c880a0fe5224c4ee8160ddb0eca7ad3b279077` |
| `us/guidance/nsf/important-notice/149-research-security/4` | `9ea581fa-b25f-59cd-93f3-0bbf767e9cf4` | `32e6de5335f45b71a7b36dec754fa47be438c21b4fdaca984ce3119915fe3216` |
| `us/guidance/nsf/important-notice/149-implementation-faq/question-3` | `737e78d3-50fe-5270-bae3-612a3c273d61` | `85300dd55c066db21e991954e184de8bb397122b553f25cc7399c05d0a6c1d38` |
| `us/guidance/nsf/important-notice/149-implementation-faq/question-5` | `6a6ae4e4-c72c-594c-98ed-82502f381595` | `846a41f7b6f5f371cc57011e0b22252f8ee96626fdac29a86b823a61a5d2669c` |
| `us/guidance/nsf/important-notice/149-implementation-faq/question-6` | `7eb10f8c-8296-5c2a-8f80-e6fbc5b48ac9` | `7421c38e894258b087d2a0c468a488acf3dea9b6ed8a411ae38f0cead6267fd0` |
| `us/guidance/nsf/important-notice/149-implementation-faq/question-7` | `b8e7df20-be8e-5d01-a8a7-440b1def2cd2` | `5b495b022f84ecd1a1e58e9ae4fefa880a64d97defb0bb14e8172cd3743e259d` |
| `us/guidance/nsf/important-notice/149-implementation-faq/question-8` | `41e58f51-90cc-5b72-8fb9-e8de0f878789` | `fcb3cf23c893c1237dece111578692f4d66750d7e5a00a6be767dfbb0978f777` |

The body hashes are SHA-256 over the exact UTF-8 JSON string contents without
an added terminal newline.

## Prepared run inputs

- Encoding brief SHA-256:
  `fd27bc45a5140c0d549c228ce252badece89148f57d24623e1c52c30dc74d1ab`
- Item 4 continuation SHA-256:
  `c468b6ced83edac19f44e6c3868a758276baf2f273c68741884016ce79dc8ccf`
- FAQ question 3 continuation SHA-256:
  `6db55c4fa789759bf6af4f5ab3d51dc09721a43e1616d5ca8275e37c889c6a9f`
- FAQ question 5 continuation SHA-256:
  `23f39e71f68a8b1c19887df55db41f70f62fd76afe8a24ebc6fdf9128e8c973c`
- FAQ question 6 continuation SHA-256:
  `20de14f72e53f623750b89a5474021b649a4599fbbeace28d5daed531cc67b82`
- FAQ question 7 continuation SHA-256:
  `2bdb553f32cdcac8ffa013f88c1332a7aed39bb1eaf84eb7bc1ce5d1abf9071b`
- FAQ question 8 continuation SHA-256:
  `713a0bd9622e9c4d4753ac3cc7a3fdb11600142053b72dcd5a01af9fde1bcac3`

All six continuation bodies were byte-for-byte compared with their selected
corpus record bodies after removing the load-bearing continuation header and
citation line; all six matched. Item 3 remains the positional primary source.

## Axiom toolchain custody

### `axiom-encode`

- Worktree:
  `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode`
- Commit: `3869d66d009f52258be35901edbef370e65a399c`
- Tree: `d2ce31c8073b4bc0b4b169b9273f394650094230`
- Version: `0.2.1200`
- `uv.lock` SHA-256:
  `ff0ea7983fe344be90ab54b388b0c4c441a1ac69ecf73937440d12802d92d5fc`
- `.venv/bin/axiom-encode` SHA-256:
  `6d134a9820f10826d3cb56e1a0df755636cad8543051811acc2f0be102af0173`
- Git state: clean and detached.

### `axiom-rules-engine`

- Worktree:
  `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine`
- Commit: `ffd8213271947b0189a9dd61a055c1e0e78908a0`
- Tree: `86e78cc74fffe774fe0ba010c0a951ca1dfcc000`
- `Cargo.lock` SHA-256:
  `56f01fb4b5118a479328fbffd55b93635ed11038de60bcdd206b88aad84d16cb`
- Existing debug binary SHA-256:
  `ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb`
- Git state: clean and detached.

## Signing and run custody

- Required environment variable: `AXIOM_ENCODE_APPLY_SIGNING_KEY`
- Environment state: unset.
- Required helper: `agent-secret` only.
- Metadata lookup result from `agent-secret search axiom`:
  `agent-secret: missing unlock password. Run: agent-secret init`
- Exact suppressed-value lookup attempted:
  `agent-secret get agent/axiom-encode-apply-signing-key axiom-foundation >/dev/null`
- Exact lookup result: the same missing-unlock-password error.
- Secret values read or printed: none.
- Alternate credential path used: none.
- Encode invocation: not started.
- Encode run ID: none.
- Generation prompt SHA-256: none.
- Trace SHA-256: none.
- Context-manifest SHA-256: none.
- Generated main/test SHA-256: none.
- Apply manifest and signature: none.
- Apply-time auto-repair markers: none, because apply did not start.

Starting a paid generation run while signed retention was impossible would not
advance the requested outcome. Running without `--apply`, using a substitute
signer, hand-authoring YAML, or invoking manual `sign-applied-files` would have
violated the requested custody chain.

## Files and retention decision

Committed preparation/report files:

- `bulk/PROGRESS.md`
- `bulk/ENCODING_BRIEF.md`
- `bulk/FINAL_REPORT.md`
- `bulk/nsf-in149-mftrp-context/01-item-4.txt`
- `bulk/nsf-in149-mftrp-context/02-faq-question-3.txt`
- `bulk/nsf-in149-mftrp-context/03-faq-question-5.txt`
- `bulk/nsf-in149-mftrp-context/04-faq-question-6.txt`
- `bulk/nsf-in149-mftrp-context/05-faq-question-7.txt`
- `bulk/nsf-in149-mftrp-context/06-faq-question-8.txt`

Executable files retained: **none**.

- No `us/policies/nsf/important-notice/149-research-security/mftrp-certification-adapter.yaml`.
- No adjacent companion test.
- No signed encoding manifest.
- No reverse-index mutation.
- No temporary candidate copied into the repository.
- No branch, push, PR, production action, or axiom-corpus mutation.

## Atomic rule acceptance

The source-faithful semantic contract is recorded in `bulk/ENCODING_BRIEF.md`,
but executable acceptance requires unchanged signed generation, strict proof,
fixtures, and direct Rust. Every executable result is therefore rejected, not
silently deferred as accepted.

| Atomic rule | Required distinction | Executable decision |
| --- | --- | --- |
| Current-party proposal senior/key ineligibility | Actual current MFTRP membership; individual; senior/key; NSF proposal; same-project role link | **REJECT — no signed generated rule** |
| Current-party award senior/key ineligibility | Same actual membership gates; NSF award; same-award role link; award date strictly `> 2024-05-20` | **REJECT — no signed generated rule** |
| Senior/key individual proposal certification | Individual certification; senior/key; same proposed project; correct proposal documents; external §19232 prerequisite; no inference of actual status | **REJECT — no signed generated rule** |
| AOR organizational proposal certification | AOR; Cover Sheet; complete roster; all made aware; all complied; same project; separate §19232 prerequisites | **REJECT — no signed generated rule** |
| Annual PI/co-PI certification duty | PI/co-PI only; at least one linked active NSF award; award date `>= 2024-05-20`; not all senior/key personnel | **REJECT — no signed generated rule** |
| Annual Research.gov status certification | Person-level annual cycle; Research.gov; participation/non-participation status submission; separate from actual status | **REJECT — no signed generated rule** |
| Proposal-certification timing gate | Explicit false through `2025-12-01`; true beginning `2025-12-02`; no guessed lapse start | **REJECT — no signed generated parameter** |
| Award-date cutoff | Actual Date input compared to a generated Date-valued parameter table; strict and inclusive edges kept distinct | **REJECT — no signed generated parameter** |
| External statutory responsibilities | No nonexistent §19232 import; separate fail-closed applicant prerequisite inputs; no agency-duty collapse | **REJECT — no signed generated gates** |

## Fixtures, proof, and Rust outcomes

Generated companion fixture count: **0**. Direct Rust adversary request count:
**0**. This is a custody rejection, not a report of fabricated passing tests.

The following requested state matrix was specified but not emitted or executed:

- actual current MFTRP membership `true`, `false`, and missing;
- individual versus AOR actor;
- senior/key versus PI/co-PI versus neither role;
- same proposed project versus another proposal/project;
- same award role linkage versus another award;
- active versus inactive and NSF versus non-NSF award;
- actual award date `2024-05-19`, `2024-05-20`, and `2024-05-21`;
- Biographical Sketch, Current and Pending Support, Cover Sheet, Research.gov,
  wrong channel, and missing channel;
- current versus noncurrent annual cycle;
- complete versus incomplete AOR roster, awareness, and compliance gates;
- each external §19232 prerequisite true, false, and missing;
- proposal periods `2025-10-09`, `2025-10-10`, `2025-12-01`, and
  `2025-12-02`;
- actual membership facts contradictory to certification assertions;
- every required gate missing one at a time.

Proof outcome: **not run; no generated module exists to validate**.

Companion-test outcome: **not run; no generated companion exists**.

Direct Rust outcome: **not run; no signed generated artifact exists to compile
or execute**. The real Rust binary was inspected and hashed; it was not replaced
with a hand-written evaluator or mock.

## Exact unblock conditions and next run

Both hard prerequisites must be restored before generation:

1. Restore the dedicated `agent-secret` keychain unlock record so the exact
   Axiom signing service can be injected into a single `encode --apply` process
   without printing or broadly exporting it.
2. Restore GitHub DNS/network access, rerun `git fetch origin main`, and verify
   the freshly fetched `origin/main` is still exactly
   `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`. If it differs, stop instead of
   rebasing or guessing because the required base is explicit.

After those conditions hold, use the committed brief and six exact continuation
files with the pinned encoder, canonical `us/` policy root, and pinned real Rust
engine. Retain output only if generation/apply is unchanged, the signed manifest
passes `guard-generated`, strict proof passes, every generated fixture passes,
all direct Rust adversaries produce the expected holds/not-holds or fail-closed
missing-input outcomes, and the generated/applied SHA-256 values are identical.
