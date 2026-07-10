# Program Artifact Pipeline

`programs/` specs are source; compiled artifacts are build outputs and are
never committed. The `program-artifacts` workflow compiles every spec through
axiom-compose + axiom-rules-engine (pinned refs in the workflow env):

- **On PRs** it is a gate: every program not excluded by an active module
  waiver must compile, so spec/corpus drift (renamed module paths,
  coverage-gate violations) is caught at PR time.
- **On main** it publishes `dist/` — provenance-stamped `*.compiled.json`
  files and `manifest.json` — as a GitHub release
  tagged `program-artifacts-<shortsha>`.

Before composition, the builder loads the canonical strict waiver model from
`known-validation-gaps.yaml`. It physically omits every active
`validate_failures` module from an isolated `rulespec-us` mirror, computes the
full `imports`/`extends` closure of each program, and excludes any contaminated
program from both RuleSpec and compiled output. Exclusions appear in manifest
format v2 under `excluded_programs`; pending approvals never exclude anything.
Compilation uses the engine's configured-root-only canonical import mode, and
the builder re-audits composed imports and compiled rule origins as
defense-in-depth. Ambient checkouts cannot supply an omitted module.

Every artifact's `metadata.provenance` records the corpus SHA, spec path +
sha256, engine version, and exact composer, encoder, and engine commit refs;
the manifest carries the same plus artifact sha256s. CI runs from the
checked-out encoder's frozen lock and the exact composer source. The build adds
no timestamps or deliberate randomness, but does not claim hermetic byte
reproducibility across changes to the runner OS, Rust toolchain, or actions.

Artifact builds require a source checkout that exactly matches `HEAD`.
Modified tracked files and untracked program or RuleSpec YAML are rejected;
only ignored, unconsumed build locations such as `dist/`, `_axiom/`,
`.engine-src/`, virtual environments, and caches may differ. This guarantees
that the recorded corpus commit represents every source byte the builder can
consume.

Consumers must pin a release tag and per-file sha256s from its manifest;
vendored or unpinned artifacts are unsupported. To admit a program: land its
spec here, wait for the release, then bump the consumer's pin.

The workflow also signs GitHub build-provenance attestations for
`manifest.json` and every `*.compiled.json`. Consumers can verify a
downloaded artifact was built by this workflow from this repo:

```bash
gh attestation verify manifest.json --repo TheAxiomFoundation/rulespec-us
```

Run locally:

```bash
export AXIOM_RULES_ENGINE_BIN=~/axiom-rules/target/release/axiom-rules-engine
export AXIOM_COMPOSE_REF=<40-character-commit>
export AXIOM_ENCODE_REF=<40-character-commit>
export AXIOM_RULES_ENGINE_REF=<40-character-commit>
python tools/build_program_artifacts.py --check   # gate mode; leaves dist/ untouched
python tools/build_program_artifacts.py           # atomically replaces dist/
```

The local Python environment must contain the workflow-pinned `axiom-compose`
and an `axiom-encode` version with the strict validation-waiver model. All
three tool commit pins live in `.axiom/toolchain.toml`; split workflow-local
pins are unsupported.
