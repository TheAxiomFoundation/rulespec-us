# NSF Important Notice 149 adapter outcome

## Disposition

No adapter was accepted. The two fresh signed-apply generations failed before
model output because the pinned Codex subprocess could not resolve or reach its
responses endpoint. The encoder correctly blocked apply before validation or
signing. No generated RuleSpec, companion test, signed manifest, proof result,
or Rust fixture result exists.

| Module | Disposition | Reason |
|---|---|---|
| Supporting-document retention/request adapter | **REJECT** | Run `28d303f4` produced zero tokens and zero RuleSpec bytes; `apply_blocked_generation` |
| Research-security-training certification adapter | **REJECT** | Run `d369ad07` produced zero tokens and zero RuleSpec bytes; `apply_blocked_generation` |

This is a fail-closed disposition, not a source-fidelity rejection of emitted
YAML: neither run emitted a candidate to audit. Hand-authored output, trace
injection, synthetic fixtures, manual attestation, and generated-output repair
were not used.

## Worktree and base custody

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-in149-20260830-47290`
- Mode: detached HEAD
- HEAD before this uncommitted report update: `d5e56a153ec75869573c7b5fa8af80c678e60d30`
- Required and verified merge base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Ahead/behind required base: 5/0
- HEAD tree: `61941d495b33213b0b13c541bd3442fec8b8da26`
- Required-base tree: `20a8f964f20b4a4bfdedc239245c5d1dbafe3f29`
- Initial and post-run policy worktree: clean; no target module, test, or
  manifest was installed
- Existing five post-base commits contain custody/progress Markdown only
- No commit, push, PR operation, deploy, or synchronization was performed
- Rules PR #1324 and corpus PR #631 were not touched

Prepared-document SHA-256 values before this report update were:

| File | SHA-256 |
|---|---|
| `ENCODING_BRIEF.md` | `4777a253f6f660b1844f18cdbd54558c956b26bec783e19a3af3f3cbdca07146` |
| `GENERATION_CUSTODY.md` | `ab14c191927e88fa4ac37b5aa84032adc6a66e42b8d5c4ecaf454b46fbea10a3` |
| `PROGRESS.md` | `aee68d52c8277f0c62544479a160a05a9d45ebc80621f6ec9dd7303d20d24308` |
| `SOURCE_CUSTODY.md` | `3e4f2c4ec39f2ff895feb0c8d447cb1f9afde4f8c26453c410865c8f9570b3a3` |
| `TOOLCHAIN_CUSTODY.md` | `9f5bbbb006ffd43890c424738551e005b9342ee562d9603ab1d3a7c221b9fae5` |

Their sorted aggregate ledger SHA-256 was
`e33d45459989e294c2af78be7942252ec3e1c0d2d6b48b3ba089ddf9a6699f97`.

Post-resumption hashes for the five non-self-referential custody documents are:

| File | SHA-256 |
|---|---|
| `ENCODING_BRIEF.md` | `4777a253f6f660b1844f18cdbd54558c956b26bec783e19a3af3f3cbdca07146` |
| `GENERATION_CUSTODY.md` | `715f5257e0842b060efd9008bfc4437916833418be79801b640ad0e67268a42a` |
| `PROGRESS.md` | `e9e8879e20f231c4d1c2cc9206473c1b0be0d58e32ea20b3ef6bf72d0d678d1a` |
| `SOURCE_CUSTODY.md` | `3e4f2c4ec39f2ff895feb0c8d447cb1f9afde4f8c26453c410865c8f9570b3a3` |
| `TOOLCHAIN_CUSTODY.md` | `ef72c62115e8310d5bf1822569ee1aa858120f0c1c04343338e0f407681fdc56` |

Their sorted aggregate ledger SHA-256 is
`ed73cf3215814da6e248c57bbbd58195c1dedb9a094f4a86d815068ed7036aba`.
The final `OUTPUT.md` hash is reported out of band to avoid self-reference.

## Official sources and credits

Corpus checkout:
`/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830`
at clean HEAD `129dae01c6f7a4787bc7678d4a97a478f3934d9f`.

- U.S. National Science Foundation, *Important Notice No. 149: Updates to NSF
  Research Security Policies*,
  `https://www.nsf.gov/notices/important/important-notice-no-149-updates-nsf-research-security/in149`
- U.S. National Science Foundation, *Important Notice No. 149 Implementation
  FAQ*,
  `https://www.nsf.gov/research-security/important-notice-no-149-implementation-faq`
- Expression date for the selected records: `2025-11-24`
- Source snapshot as of: `2026-08-30`
- Important Notice HTML SHA-256:
  `b80a6a59dbb102e3371b4eab6e90971562e91e551220c892533b2efb3da9cb8d`
- FAQ HTML SHA-256:
  `a80e70b6640477ae3f95cc9a54b394a03aac087d1d17e7ff6fb50c774f5fdf41`
- Normalized guidance provisions SHA-256:
  `a16f78fee0769493e9ba11d4e7c154b84536158fb6091cef8721b8f8fc482a89`
- Guidance inventory SHA-256:
  `5b5433685a24e613c69375c376cc4dabb1efa5faa48e036a410d0948931f82c7`

Authorized body hashes:

| Corpus record | Body SHA-256 |
|---|---|
| `us/guidance/nsf/important-notice/149-research-security/1` | `edfddabaf767db5be1e5544ad0a8f0fc4e0964eab782ef16a374365b2a0ed21e` |
| `us/guidance/nsf/important-notice/149-research-security/2` | `ed64c82ae4f30dc11074ef55790fd8cb2d1bfbb2a362fe61bb76eae4d931c156` |
| `us/guidance/nsf/important-notice/149-implementation-faq/question-1` | `93b97ac429d5e727abd459529d162a4b119a5a971485f328cdc920e27035140a` |
| `us/guidance/nsf/important-notice/149-implementation-faq/question-5` | `846a41f7b6f5f371cc57011e0b22252f8ee96626fdac29a86b823a61a5d2669c` |
| `us/guidance/nsf/important-notice/149-implementation-faq/question-6` | `7421c38e894258b087d2a0c468a488acf3dea9b6ed8a411ae38f0cead6267fd0` |
| `us/guidance/nsf/important-notice/149-implementation-faq/question-7` | `5b495b022f84ecd1a1e58e9ae4fefa880a64d97defb0bb14e8172cd3743e259d` |
| `us/guidance/nsf/important-notice/149-implementation-faq/question-8` | `fcb3cf23c893c1237dece111578692f4d66750d7e5a00a6be767dfbb0978f777` |

The source audit supports `2025-12-02` as the live date and `2025-12-01` as
false for both modules. It supports no grace period. Item 1 has separate
retention, actual-request production, and requested-document review conditions.
Item 2 has separate individual and AOR same-proposal certifications within an
inclusive twelve-calendar-month window. Named training resources are acceptable
routes, not frozen vendors. NSF risk-assessment discretion and IHE-only RECR/
42 U.S.C. sections 19039-19040 remain excluded. Because no section 19233 or
19234 RuleSpec base exists, an eventual adapter must expose the relevant
external prerequisite and fail closed rather than duplicate the statutes.

## Toolchain custody

- Encoder checkout: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode`
- Encoder HEAD: `3869d66d009f52258be35901edbef370e65a399c`
- Encoder version: `0.2.1200`
- Encoder executable SHA-256:
  `6d134a9820f10826d3cb56e1a0df755636cad8543051811acc2f0be102af0173`
- Rust checkout: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine`
- Rust HEAD: `ffd8213271947b0189a9dd61a055c1e0e78908a0`
- Rust binary SHA-256:
  `ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb`

The inherited apply-signing value was never printed, logged, hashed, rotated,
retrieved, or placed on a command line. Both A3 runs failed before the encoder
read it for manifest signing, so no signature or signing proof exists.

## Prior-run custody

| Attempt | State | Files | Aggregate file-ledger SHA-256 |
|---|---|---:|---|
| Item 1 A1, run `a80c2aa7` | Zero-output transport failure | 16 | `b71f2f8c249aceeadf75232e4350b4e247a1e72901107814ab8eda302e04d033` |
| Item 2 A1, run `9fa1c0ca` | Zero-output transport failure | 17 | `0b56a9371907cd1269c6ec45fd6854c491dec00238ef1c5cfb33d4892e7bbe34` |
| Item 1 A2 | Interrupted after context staging; no run ID | 13 | `8596891d503cf85ef38b087041e11b654f6ed2aae19181db490c4be091d413fd` |
| Item 2 A2, run `21131959` | Zero-output transport failure | 17 | `a0249ffcce025447352ac4396a84a9ada6d6314168f4cbf2fe1a77d607c46257` |

The A2 Item 1 root is preserved as incomplete context custody. A2 Item 2 has
trace `9b5b1601caddef2a2bfed59c396fe2cb1bf615c76fc170e1323c64d78b5f89c7`,
repair manifest `28c86d0ee092934498363169b15db911fb1088c7f6d0bf172ff9e982414a5af4`,
and database `d139bf3275ba295bf914b77c24f0ad31d8f23cbc6eb05962f08c2a423bb4357f`.

## Fresh-run hashes and outcomes

| Field | Supporting documents A3 | Training certifications A3 |
|---|---|---|
| Root | `/Users/maxghenis/tmp/axiom-nsf-in149-item1-run-47290-a3` | `/Users/maxghenis/tmp/axiom-nsf-in149-item2-run-47290-a3` |
| Run/session | `28d303f4` / `encode-28d303f4` | `d369ad07` / `encode-d369ad07` |
| Duration | 61,956 ms | 42,419 ms |
| File count | 15 | 17 |
| Aggregate ledger | `85383a7e1d8bf2edc913fc3742432a2dd6527c96abea500bdaad3ea2fdbedac2` | `d6cb1c0ed83f22f306c80143890e460303e4e98951c29bdc3f14c9d93be5cbf0` |
| Combined source | `8f0defb6c30e263780323ad1f7bf90e326351b9186126178921475946ee6932f` | `7211f22db14a5077d32fb3b9308b9128d6e61ebbf66464db96d2b03298ba5d0b` |
| Source metadata | `cd3f7765afce6287b44d369d400c2a4375457a95b6bb8f9ecb1ce896c666b144` | `60ed072378c25386a9de72bb981fcb4ca2b0ababc16b8b47350bdd5cd340d1f8` |
| Context manifest | `88f420297f63b3d5c6b9a591a72adb17c1771b35b95a1cf578037dc2edae72fb` | `828d56932a09e574f9c11a493710f1d1c37b29462c0c35bf6de8bd206190de1e` |
| Context-tree ledger | `0a33b1e9672a7ec6646c9a1be433f12b0cc1463104586f057b7a8001dac053e7` | `e069b1e005f758f0161dda23a7826b55b24995d406c5910ab3929315b19d0be5` |
| Trace | `4f4a189554f34412c6d4a72df8ad7e3cdcc8f8fb362989e0b0de7a236bd93d88` | `d4d5a0148bb31cfc7472e7aa8c5b37379581dd98d9c9c23355e2f6eee69a896f` |
| Repair manifest | `ca59443e99a08b0c27cb58ea7df3e8a4adc58b2b6e052e8d6b54daef2f19fc81` | `2cb2af423cc044845256d292a1fd57e2401f2371af21ea9ec055a05599737840` |
| Database | `c226c4a19133fbca2a6a08740e8d79e75ea03dc25f1ca6d12681a0abe5c904cf` | `3b8bffcc9f2da2c88ada40f9b293f947df441f9fc251e710e56e1999be0f4d12` |
| Output hash | absent | absent |
| DB outcome | `apply_blocked_generation` | `apply_blocked_generation` |

Both traces contain 14 events and terminate in `turn.failed` after DNS lookup
errors, WebSocket fallback, and five HTTPS reconnect attempts. Both databases
record zero RuleSpec bytes, `apply_requested=true`, `apply_success=false`,
`applied_files=[]`, and `final_success=false`; both databases pass SQLite
integrity checking. All 9 Item 1 and 11 Item 2 copied context files byte-match
their recorded source paths.

The repository context selector copied the unrelated 26 U.S.C. section 3304
IHE definition and test into both disposable workspaces. No model output was
produced, so they were never imported or applied. Any future candidate using
that context for an IHE/RECR duty remains an automatic rejection.

## Fixtures, proof, and real Rust

| Required surface | Supporting documents | Training certifications |
|---|---:|---:|
| Generated companion files | 0 | 0 |
| Generated fixture cases | 0 | 0 |
| Executable fixture states | 0 | 0 |
| Proof trees validated | 0 | 0 |
| Modules compiled by pinned Rust | 0 | 0 |
| Direct Rust cases executed | 0 | 0 |
| Signed manifests verified | 0 | 0 |

Accordingly, none of the requested proposer/recipient, document-type,
actual/no-request, same-person, individual/AOR, twelve-month boundary,
same-proposal, missing-prerequisite, `2025-12-01`/`2025-12-02`, or IHE-exclusion
states was executed. They are **not passed**; they remain ungenerated and
unverified. Running proof or Rust against a nonexistent candidate would not be
evidence, so those commands were not invoked.

## Legitimate continuation

The pinned encoder has no supported replay, offline resume, or apply-existing
generated-output command. Failed Codex homes are ephemeral and retain no usable
session rollout. `sign-applied-files` records a manual attestation and is not a
substitute for generated provenance. The only faithful continuation is a fresh
normal `axiom-encode encode ... --apply` run in a new root after outbound Codex
transport is restored, followed by unchanged-output hash equality, signed-guard
verification, proof validation, generated fixtures, and direct pinned-Rust
execution.

An exact-name and targeted manifest/trace recovery sweep across the preserved
worktrees, Axiom run assets, and `/Users/maxghenis/tmp` found no additional
adapter YAML, companion test, signed manifest, or completed trace outside the
known A1-A3 evidence. The repair JSON files are diagnostics, not generated or
signed RuleSpec candidates.
