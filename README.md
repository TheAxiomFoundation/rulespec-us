# rulespec-us

United States RuleSpec encodings — the country monorepo. One directory per
jurisdiction, plus the declarative program specs that assemble atomic rules
into runnable programs.

## Layout

- `us/`: federal encodings (`statutes/`, `regulations/`, `policies/`), with
  tests beside each encoding as `.test.yaml`.
- `us-al/` … `us-tx/`: one directory per state, same internal convention.
  Absorbed from the former standalone `rulespec-us-<state>` repos with full
  history; those repos are archived pointers.
- `programs/`: declarative compose specs, one YAML per
  (jurisdiction, program, period), consumed by `axiom-compose`. Absorbed
  from `axiom-programs` (US specs) with full history.
- `tests/`: repository-wide validation — layout, companion-test pairing,
  RuleSpec shape, derived-rule coverage, and program-spec scope auditing —
  plus `generate_reverse_index.py`, which builds the provision→rules index.
- `.axiom/toolchain.toml`: signed corpus-release and validation-waiver binding.
- `.axiom/workflow-toolchain.toml`: immutable validation, generation,
  artifact-publication, and legacy staleness-scan checkout identities (full
  commit SHAs). Role-specific pins keep compatibility migrations explicit.
- `.axiom/index/provisions_to_rules.json`: generated reverse index mapping
  each corpus citation path to the modules that depend on it (via module
  `source_verification` and proof-atom sources). It is **not tracked**: it
  is a pure function of the RuleSpec YAML, and a tracked copy made every
  encoding pull request edit the same file. Generate it outside the
  checkout with `python tests/generate_reverse_index.py --output <path>`
  (the script refuses a path inside the checkout, because a copy there
  blocks the encoder's clean-checkout gates). This is the trusted way.
  As a convenience, commits on `main` also upload it as the
  `provisions-to-rules-index` artifact of the `Source staleness and reverse
  index` workflow. Take the artifact only from a successful `push` run
  (`gh run list --workflow source-staleness.yml --branch main --event push
  --status success`) whose `headSha` is a commit on `origin/main`: a pull
  request run can upload an artifact with the same name. Never commit the
  index; a test fails if anything under `.axiom/index/` is tracked.
- Pass `--deferred-provisions-output <path>` alongside `--output` to generate
  a separate report for `module.deferred_outputs[].blocked_by_provisions`.
  The report lists the affected output and candidate providers for each
  provision. When every provision has a candidate, review and link the
  compatible executable outputs before removing the deferral. CI shows
  these states in its job summary and publishes the full
  `deferred-provisions-report` artifact on `main`, with the same provenance
  guidance as the reverse index.

Durable ids are `<jurisdiction>:<path>#<rule>` — `us:statutes/7/2015/e`
lives at `us/statutes/7/2015/e.yaml`, `us-ca:regulations/mpp/63-300/1` at
`us-ca/regulations/mpp/63-300/1.yaml`. Ids are identical to the
pre-consolidation layout; only file locations changed.

## Known gaps (ratcheted)

- `known-dangling.yaml`: program-spec scope entries that don't resolve to a
  module yet (axiom-programs#14).
- `known-validation-gaps.yaml`: pre-existing content debt surfaced when
  repository-wide discipline first ran across all jurisdictions
  (rulespec-us#394). `tools/waiver_issues.py` fails when a waiver cites an
  issue that isn't open.
- `known-missing-money-atoms.yaml`: policy-bearing monetary values
  (currency parameters, currency parameter-table cells, and currency
  literals in derived formulas) that still lack a proof atom citing a
  provision. Seeded from the current backlog measured by
  `axiom-encode proof-validate --emit-ratchet`; the org
  `validate-rulespec` workflow's money-atom step reads it so CI blocks any
  new atom-less monetary value while the existing 151 are burned down.

These lists fail CI on new entries AND on listed entries that get fixed
without being removed, so they only shrink.

Do not add singular rule roots, separate parameter/test fixture files, or
generated formula artifacts.
