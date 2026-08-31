# Generation custody

## First disposable attempts

Both first attempts used the pinned `axiom-encode` executable in
repo-augmented mode with Codex `gpt-5.5`, the exact positional source, the
authorized primary-source continuations, the committed encoding brief, the
canonical `us/` policy root, and the pinned real Rust engine path. They used
isolated output roots and isolated `encodings.db` files. Neither command used
`--apply`, a signing key, or synchronization.

| Item | Output root | Run/session | Duration | Result |
|---|---|---|---:|---|
| Supporting documents | `/Users/maxghenis/tmp/axiom-nsf-in149-item1-run-47290-a1` | `a80c2aa7` / `encode-a80c2aa7` | 53,412 ms | failed before model output |
| Training certifications | `/Users/maxghenis/tmp/axiom-nsf-in149-item2-run-47290-a1` | `9fa1c0ca` / `encode-9fa1c0ca` | 72,418 ms | failed before model output |

For both runs, the database records encoder version `0.2.1200`, model
`gpt-5.5`, zero input/output tokens, zero RuleSpec bytes,
`apply_requested=false`, an empty `applied_files` list, and
`standalone_failed`. The traces record DNS lookup failures, WebSocket-to-HTTPS
fallback, five HTTPS reconnect attempts, and a terminal `turn.failed` with
`stream disconnected before completion` from the Codex responses endpoint.

No target `.yaml`, companion `.test.yaml`, prompt/output receipt, signed apply
manifest, or generated policy file exists in either root. Item 1 contains 16
files and Item 2 contains 17 files: source/context custody, trace, repair
manifest, and database only.

## First-attempt hashes

The aggregate hashes are SHA-256 over the byte stream produced by, from within
each run root, sorting all `rg --files` paths by raw bytes and applying
`shasum -a 256` to each file.

| Artifact | Item 1 SHA-256 | Item 2 SHA-256 |
|---|---|---|
| Aggregate file-hash ledger | `b71f2f8c249aceeadf75232e4350b4e247a1e72901107814ab8eda302e04d033` | `0b56a9371907cd1269c6ec45fd6854c491dec00238ef1c5cfb33d4892e7bbe34` |
| Combined `source.txt` | `af84a3c80d813d8111ce5eed1ece9035a6585619cf20f770300081b344c11aa2` | `7211f22db14a5077d32fb3b9308b9128d6e61ebbf66464db96d2b03298ba5d0b` |
| `source-metadata.json` | `494a13f5168f5be04688013dbc64f3e033f6f84916867f36df53ef876968b769` | `60ed072378c25386a9de72bb981fcb4ca2b0ababc16b8b47350bdd5cd340d1f8` |
| `context-manifest.json` | `0a8ff9043bff3c12eda9c2248fcd31fbe8282508c4a709d2dc7bc5be89c04fe8` | `828d56932a09e574f9c11a493710f1d1c37b29462c0c35bf6de8bd206190de1e` |
| Trace | `7a53f407dd58c997edabcbb0b0e9decdc257440ac0764b1b0fd3f9834b384f56` | `557d6e0447e4aaadfd4a553c31d44b6de2e32f70b0062eaee7906c2ed7f6c37b` |
| Repair manifest | `73dc2a2cd1de2f44b9437cf36bb81b87ee2ad04f6de16dc02e35733538627059` | `945e9aeb88d1591bbc4b9ba583a360df5fac51711dfdb9b320b555e6a6001792` |
| `encodings.db` | `b2ad9aa3262699c6509bfe490ac1aaeb6e718583d86bec0ce008278aed366c01` | `6e0c307073db71a71780335f7d7bb5482321b7f70d5ea570ca25e4bc8c723a1c` |

The repo-augmented context selector also copied the existing 26 U.S.C. 3304
module and test after matching the source's excluded institution-of-higher-
education wording. Those two files are implementation context only, not an
authorized legal source or accepted dependency. Any candidate that imports or
encodes that IHE concept is out of scope and must be rejected.

## Retry state

One identical retry per item is in flight in fresh isolated roots ending in
`-a2`. The retries remain disposable and cannot be accepted without unchanged
generated output, successful validation/proof/Rust execution, and signed apply
through `agent-secret`.
