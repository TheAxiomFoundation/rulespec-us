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

## Second-attempt outcomes

The Item 2 `-a2` retry finished as another transport failure before model
output. Run `21131959` / session `encode-21131959` recorded 63,313 ms, zero
input/output tokens, zero RuleSpec bytes, `apply_requested=false`, and
`standalone_failed`. Its 17-file aggregate ledger SHA-256 is
`a0249ffcce025447352ac4396a84a9ada6d6314168f4cbf2fe1a77d607c46257`.
The trace, repair manifest, and database hashes are respectively
`9b5b1601caddef2a2bfed59c396fe2cb1bf615c76fc170e1323c64d78b5f89c7`,
`28c86d0ee092934498363169b15db911fb1088c7f6d0bf172ff9e982414a5af4`,
and `d139bf3275ba295bf914b77c24f0ad31d8f23cbc6eb05962f08c2a423bb4357f`.

The Item 1 `-a2` retry was interrupted after context staging and before model
execution or run registration. Its root contains 13 source/context files and
no trace, repair manifest, database, run/session ID, generated YAML, or test.
Its aggregate ledger SHA-256 is
`8596891d503cf85ef38b087041e11b654f6ed2aae19181db490c4be091d413fd`.
The last write was `2026-08-30T20:29:50-0400`; a later `lsof +D` found no open
file. There is no encoder resume command, so this root is custody evidence only.

## Fresh signed-apply attempts

Fresh `-a3` roots invoked the same pinned encoder with `--apply`, `--no-sync`,
the canonical `us/` policy root, and the inherited signing environment. The
signing value was not printed, logged, hashed, retrieved, or otherwise
inspected. Both runs failed at the Codex transport boundary before generation,
validation, or signing. Their database outcomes are
`apply_blocked_generation`, with `apply_requested=true`,
`apply_success=false`, `applied_files=[]`, and zero RuleSpec bytes.

Item 1 used only directly relevant FAQ questions 1, 5, 7, and 8, the two
section 19233 prerequisite continuations, and the encoding brief. Item 2 used
FAQ questions 1, 5, 6, 7, and 8, the three section 19234 prerequisite
continuations, and the encoding brief.

| Item | Output root | Run/session | Duration | Files | Aggregate ledger SHA-256 |
|---|---|---|---:|---:|---|
| Supporting documents | `/Users/maxghenis/tmp/axiom-nsf-in149-item1-run-47290-a3` | `28d303f4` / `encode-28d303f4` | 61,956 ms | 15 | `85383a7e1d8bf2edc913fc3742432a2dd6527c96abea500bdaad3ea2fdbedac2` |
| Training certifications | `/Users/maxghenis/tmp/axiom-nsf-in149-item2-run-47290-a3` | `d369ad07` / `encode-d369ad07` | 42,419 ms | 17 | `d6cb1c0ed83f22f306c80143890e460303e4e98951c29bdc3f14c9d93be5cbf0` |

| Artifact | Item 1 SHA-256 | Item 2 SHA-256 |
|---|---|---|
| Combined `source.txt` | `8f0defb6c30e263780323ad1f7bf90e326351b9186126178921475946ee6932f` | `7211f22db14a5077d32fb3b9308b9128d6e61ebbf66464db96d2b03298ba5d0b` |
| `source-metadata.json` | `cd3f7765afce6287b44d369d400c2a4375457a95b6bb8f9ecb1ce896c666b144` | `60ed072378c25386a9de72bb981fcb4ca2b0ababc16b8b47350bdd5cd340d1f8` |
| `context-manifest.json` | `88f420297f63b3d5c6b9a591a72adb17c1771b35b95a1cf578037dc2edae72fb` | `828d56932a09e574f9c11a493710f1d1c37b29462c0c35bf6de8bd206190de1e` |
| Trace | `4f4a189554f34412c6d4a72df8ad7e3cdcc8f8fb362989e0b0de7a236bd93d88` | `d4d5a0148bb31cfc7472e7aa8c5b37379581dd98d9c9c23355e2f6eee69a896f` |
| Repair manifest | `ca59443e99a08b0c27cb58ea7df3e8a4adc58b2b6e052e8d6b54daef2f19fc81` | `2cb2af423cc044845256d292a1fd57e2401f2371af21ea9ec055a05599737840` |
| `encodings.db` | `c226c4a19133fbca2a6a08740e8d79e75ea03dc25f1ca6d12681a0abe5c904cf` | `3b8bffcc9f2da2c88ada40f9b293f947df441f9fc251e710e56e1999be0f4d12` |
| Generated output | absent | absent |

Each trace has 14 events: a thread and turn start, DNS lookup failures, a
WebSocket-to-HTTPS fallback, five HTTPS reconnects, a terminal transport error,
and `turn.failed`. Neither run emitted a target YAML, companion test, prompt
receipt, signed apply manifest, fixture, proof result, or Rust result.
