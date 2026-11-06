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
  `source_verification` and proof-atom sources). Regenerate with
  `python tests/generate_reverse_index.py`; CI fails if it is stale. Do not
  edit by hand.

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

## Validation drift and admissions

- `.github/workflows/validation-drift.yml` replaces the daily full
  validation (#1274, axiom-encode#2094). Once a day it plans a run from what
  changed since the last drift run (`tools/validation_drift.py`): a full run
  for an encoder merge that declares `Validation effect: tighten` (or no
  valid effect), a rules-engine or corpus pin, or 7 days since the last full
  run; the waived files for `loosen` merges; nothing for `none` merges. Each
  failing file opens or updates one `Validation drift: <path>` issue with the
  `re-encode-queue` label. A file in scope that passes closes its issue. Run
  it by hand with `workflow_dispatch` (`scope: full` for every file).
- `.axiom/admissions/` holds reviewed, repository-specific admissions that
  the encoder reads from the protected `main` commit only
  (axiom-encode#2095). Today it holds `coverage-exemptions.jsonl`, in the
  encoder's coverage-exemption record format. Code owners review it.
