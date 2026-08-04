# Program Artifact Pipeline

Jurisdiction `programs/` specs are source; compiled artifacts are build outputs and are
never committed. The `program-artifacts` workflow compiles every spec through
axiom-compose + axiom-rules-engine (pinned refs in the workflow env):

- **On PRs targeting `main`** it is a gate: any spec outside
  `tools/known-broken-specs.txt` that fails to compile fails the check, so
  spec/corpus drift (renamed module paths, coverage-gate violations) is caught
  before it reaches the deployable branch. Migration staging PRs use the
  signed validation and provenance pipeline instead because their frozen
  legacy paths are intentionally not canonical-engine inputs.
- **On main** it publishes `dist/` — provenance-stamped `*.compiled.json`,
  composed `*.rulespec.yaml`, and `manifest.json` — as a GitHub release
  tagged `program-artifacts-<shortsha>`.

Every artifact's `metadata.provenance` records the corpus SHA, spec path +
sha256, composer version, and engine version; the manifest carries the same
plus artifact sha256s. Given a corpus commit and the pinned toolchain, the
build is byte-reproducible.

Consumers (axiom-api) pin a release tag and per-file sha256s instead of
vendoring artifacts. To admit a program: land its spec here, wait for the
release, then bump the consumer's pin.

The workflow also signs GitHub build-provenance attestations for
`manifest.json` and every `*.compiled.json`. Consumers can verify a
downloaded artifact was built by this workflow from this repo:

```bash
gh attestation verify manifest.json --repo TheAxiomFoundation/rulespec-us
```

Run locally:

```bash
AXIOM_RULES_ENGINE_BIN=~/axiom-rules/target/release/axiom-rules-engine \
  python tools/build_program_artifacts.py --check   # gate mode
  python tools/build_program_artifacts.py           # writes dist/
```
