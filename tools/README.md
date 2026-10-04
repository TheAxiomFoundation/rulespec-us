# Program Artifact Pipeline

`programs/` specs are source; compiled artifacts are build outputs and are
never committed. The `program-artifacts` workflow compiles every spec through
axiom-compose + axiom-rules-engine (pinned refs in the workflow env):

- **On PRs** it is a gate: any spec outside `tools/known-broken-specs.txt`
  that fails to compile fails the check, so spec/corpus drift (renamed module
  paths, coverage-gate violations) is caught at PR time.
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

# Engine root load

The `engine-root-load` workflow asks the question issue #1354 showed nothing
else asked: does `axiom-rules-engine`, at `axiom_rules_engine_ref` in
`.axiom/workflow-toolchain.toml`, load this checkout as a corpus root?
Repository Checks skips every module with an active known-validation-gaps
waiver, so it stayed green while hundreds of modules declared fields that
engine had removed.

`tools/engine_root_load.py` writes a small Rust harness into the pinned engine
checkout as a Cargo example, builds it with `--locked`, admits the checkout
once as a `CanonicalRuleSpecRoots` root, and compiles every atomic module
under `<jurisdiction>/{legislation,policies,regulations,statutes}/` through
`CompiledProgramArtifact::from_rulespec_file`, the entry point behind
`axiom-rules-engine compile`. A stored `module.kind: composition` module, which
the engine refuses on that surface, is also compiled from a copy outside the
checkout through `from_composed_rulespec_file`.

Failures must equal `tools/known-engine-load-failures.txt`
(`<surface>\t<class>\t<module>`) exactly:

- a module that fails and is not listed fails the check;
- a listed module that no longer fails that way fails the check, so a fix
  deletes its line in the same change;
- when the protected base already has a baseline and the engine pin is
  unchanged, a pull request may only shrink the failing `(surface, module)`
  set. A listed module may change class: the engine reports only a module's
  first error, so fixing one can expose another;
- when the protected base has no baseline, the check establishes the first
  baseline without enforcing that shrinking rule. Moving
  `axiom_rules_engine_ref` also permits baseline growth: a newer engine may
  reject more, and the pin bump is where those failures are listed and reviewed.

Run locally from a checkout whose directory is named exactly `rulespec-us`:

```bash
python tools/engine_root_load.py run --engine-src ../axiom-rules-engine \
  --output /tmp/engine-root-load.jsonl
python tools/engine_root_load.py check --results /tmp/engine-root-load.jsonl \
  --base-ref origin/main
python tools/engine_root_load.py baseline --results /tmp/engine-root-load.jsonl \
  > tools/known-engine-load-failures.txt   # after deliberately fixing modules
```
