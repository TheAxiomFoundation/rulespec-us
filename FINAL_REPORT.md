# 42 U.S.C. § 19232(e) encoding report

## Disposition

**REJECT.** No RuleSpec was generated, signed, applied, or retained. The required generated-only workflow was blocked before candidate creation by three consecutive Codex transport failures, and signed apply was independently blocked because the approved `agent-secret` keychain could not unlock. No hand-authored or previously rejected RuleSpec was substituted.

## Worktree and base

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-42-19232-e-nonretroactivity-20260830-codex-03`
- Mode: detached HEAD
- Required base object: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Local `origin/main`: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Fresh-fetch result: failed twice because `github.com` could not be resolved. The worktree was created directly from the verified local remote-tracking object, but the fresh-fetch requirement was not satisfied and is part of the rejection.
- Pre-report detached HEAD: `e36f15d2c519d7d02fd3362a63b97eb191422c46`
- Documentation-only commits before this final report: `64ccea231410c20752bb389c1f6b8ada4d2941dd`, `0b5e730a8250800482895c57e2e28d012cd8bb5a`, `0eb2a7392647e98e9a971cc1314c1ec0115216ce`, and `e36f15d2c519d7d02fd3362a63b97eb191422c46`. These implement the standing order to commit progress after each coherent step; no RuleSpec content was committed.
- Accepted sibling worktree inspected read-only: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-19232-f-training-retry-20260830` at `94160652eb3d4a148d3c632677da8c42818853fa`
- Prior § 19232(e) attempts were inspected only as rejection evidence and were not edited or reused.

## Official source and temporal basis

- Corpus worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830`
- Corpus commit: `129dae01c6f7a4787bc7678d4a97a478f3934d9f`
- Provision file: `data/corpus/provisions/us/statute/2026-08-30-proposal-security-title-42.jsonl`
- Full JSONL SHA-256: `566a513343f88d5a4944c591ef86464dcd27ea8dce8a4dd730f05efec4f69aa4`
- Coverage SHA-256: `07aa0d455d923bc6c9a2e34040b583f2365f1dfb41aed7761aae74afb582f03e` (133/133)
- Tracked OLRC ZIP SHA-256: `31929c28f117362ac8788607242795769b05ed7726f07e4ed3b1786f39655ce7`
- `usc42.xml` member SHA-256: `b72955590abe55bdbd1ce5d13c5293955a82add9c84fad92c1674ec469e86624`

Exact provision records:

| Path | Record ID | Body SHA-256 | Raw JSONL row SHA-256 (including newline) |
| --- | --- | --- | --- |
| `us/statute/42/19232/e` | `f45604a0-57d4-5d70-a793-7985a8a3a676` | `16e0b4bbf48ef9bc1621dff32d3084f3b7b3b7498f8063e305b654efeee81fb6` | `a9ab555bd0e1d5261d012dee2208b9ead190d33ea6c392a60ad27f085639f817` |
| `us/statute/42/19232/a` | `e330eef6-b042-51fd-ba83-fc21279772d7` | `ea3241a54755a3f0669c8d7bf16150900d1a4b1f8f2bd5ddf03f6e74d65487a8` | `8efd58a19807c40376b378aa271337b4dbb636785293c7f9151dcd16c3402834` |

The source credit is Pub. L. 117-167, div. B, title VI, § 10632, Aug. 9, 2022, 136 Stat. 1665, with no delayed effective date. The mandatory versions are therefore exactly `2022-08-08: false` and `2022-08-09: <operative formula>`. The corpus snapshot date and the 24-month policy deadline are not policy-establishment dates.

## Required encoding semantics

The only safe positive output is a limitation judgment such as `subsection_a_certification_is_nonretroactively_inapplicable`; it must not decide the underlying subsection (a) certification obligation. The operative formula must guard on R&D scope, actual same-agency policy establishment, and availability of the actual establishment date, compare external agency identifiers directly, and then preserve the strict stage-specific OR:

```text
(application stage AND application submission date < actual same-agency policy establishment date)
OR
(award stage AND award-made date < actual same-agency policy establishment date)
```

No universal agency establishment date may be encoded. Equality is not “prior to.”

## Toolchain

- `axiom-encode`: `3869d66d009f52258be35901edbef370e65a399c`, version `0.2.1200`, clean detached checkout
- `axiom-encode/pyproject.toml` SHA-256: `4b9b24e4e9c78035ac4e66b09b9b9515b28a599660a17c48e031e968592256cd`
- `axiom-encode/uv.lock` SHA-256: `ff0ea7983fe344be90ab54b388b0c4c441a1ac69ecf73937440d12802d92d5fc`
- `axiom-rules-engine`: `ffd8213271947b0189a9dd61a055c1e0e78908a0`, clean detached checkout
- Real Rust debug binary SHA-256: `ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb`
- Encoder context-manifest SHA-256 for all three runs: `69e271446c481687d6e03cf1512f54c306c165bd000a9889faa6e9912247ce31`
- The parsed subsection (a) primary-source continuation body matched the official body SHA-256 exactly.

## Encoder runs

All runs used the real `axiom-encode encode` CLI, backend `codex`, model `gpt-5.5`, exact corpus and engine paths, canonical `us/` policy root resolution, repository-augmented mode, `--no-sync`, and fresh output roots. Each included the exact subsection (a) primary-source continuation and the acceptance constraints. The invocation was the following template, with `N` set to 1, 2, or 3; run 3 passed the already-resolved `.../codex-03/us` content root, which is equivalent to passing the checkout root:

```text
axiom-encode encode us/statute/42/19232/e
  --output /private/tmp/axiom-encode-19232-e-codex-03-runN
  --model gpt-5.5 --backend codex --mode repo-augmented --no-sync
  --corpus-path <specified corpus worktree>
  --axiom-rules-engine-path <specified Rust engine worktree>
  --policy-repo-path <detached task worktree>
  --allow-context <exact subsection (a) primary-source continuation>
  --allow-context <accepted subsection (f) RuleSpec>
  --allow-context <accepted subsection (f) generated fixture>
  --allow-context <committed PROGRESS.md>
  --db /private/tmp/axiom-encode-19232-e-codex-03-runN.sqlite
```

| Run ID | CLI-reported encoder duration | Result | Trace SHA-256 | Repair manifest SHA-256 |
| --- | ---: | --- | --- | --- |
| `4145fe8f` | 37,733 ms | zero-token stream disconnect; no RuleSpec | `c1cf60e5f124d30e9ebba776fd02d43ec29a29411b798f2922af3ca5e60678cd` | `35819904c88bd496d5d2f42f2f01bbde918b094f92fac10e8973ce0f844093cf` |
| `94e778a8` | 50,423 ms | zero-token stream disconnect; no RuleSpec | `40f6049cdbb58f82933d9f59d1bfa21d3b39229fee340938d302efa661490553` | `7b463f0d2f74ec7b84c158295c3460d1d1dbc4ba31154ff22e20ed2f03773e6a` |
| `08ae436e` | 53,274 ms | zero-token stream disconnect; no RuleSpec | `275599194f654c62b784cb514e82cec7ec1f954e2edb08a5f5d6e323e0fadcf8` | `824a2c27403b7954c3faeca534c0181b6b0846766852c326b1b631533243c2b6` |

Each terminal error was `stream disconnected before completion: error sending request for url (https://chatgpt.com/backend-api/codex/responses)` after DNS/transport retries.

## Signing, files, proof, fixtures, and Rust outcomes

- Approved secret lookup: `agent-secret get agent/axiom-encode-apply-signing-key`
- Result: blocked with `missing unlock password`; no alternate key, direct login-keychain dump, unsigned apply, or retrospective manifest signing was used.
- Expected RuleSpec: `us/statutes/42/19232/e.yaml` — absent
- Expected generated fixture: `us/statutes/42/19232/e.test.yaml` — absent
- Expected signed manifest: `us/.axiom/encoding-manifests/statutes/42/19232/e.json` — absent
- Proof validation: not run because no generated candidate existed.
- Generated fixture outcomes: none; no fixture was generated.
- Direct Rust compile/run: not run because no candidate existed. No outcomes are claimed for minus/equal/plus one day, application-before, award-before, neither-before, different-agency, missing-date, non-R&D, or pre-enactment states.

The absence of proof, fixtures, and Rust outcomes is a hard rejection, not a waiver.

## Accept/reject summary

- Source provenance and the exact temporal interpretation were verified.
- Fresh remote fetch was not possible.
- Three independent generated-only attempts produced no candidate.
- Signed apply was unavailable through the only approved secret path.
- No protected RuleSpec content was changed, and no push, PR, or production action occurred.
- Temporary failed-run roots, SQLite logs, the encoder-only subsection (a) continuation, and the incomplete disposable checkout were removed after their hashes and outcomes were recorded.
- Final result: **REJECT; restore/retain no RuleSpec artifacts.**
