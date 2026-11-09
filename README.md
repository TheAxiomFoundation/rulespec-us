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
  changed since the last drift run (`tools/validation_drift.py`). It runs
  every file for an encoder merge that declares `Validation effect: tighten`
  or `loosen` (or no valid effect), an encoder commit without a merged PR, a
  rules-engine, composer or corpus pin or release, a new shared-validator
  commit in the workflow's `uses:` line, or 7 days since the last full run. It skips the run when only `none` merges happened. Each failing
  file opens or updates one `Validation drift: <path>` issue with the
  `re-encode-queue` label (at most 50 new issues per run). People close the
  issues; the run never closes them, because the validator lists only
  failures. The report reads the validator's per-chunk result lines. A leg
  that fails without explained per-file results (a crash, or a later step
  such as companion tests), or more than 50 new failures, fails the report,
  so the state does not advance and the next run reports again. In `pinned`
  verifier mode, encoder main merges do not start a run; a pin change does.
  Run it by hand with `workflow_dispatch` (`scope: full`). A run that cannot
  finish its report opens or refreshes one `Validation drift run failed`
  issue (label `validation-drift-run`). Only the `issues` job can write
  issues; it checks out nothing and runs only `gh` and `jq`.
- The drift run and pull-request gating can call different shared-validator
  commits until `repository-checks.yml` moves to the same commit. Keep them
  equal.
- A red full validation after a push to main still opens or refreshes one
  alarm issue (`push-alarm` in `repository-checks.yml`).
- `.axiom/admissions/` is the reviewed, repository-specific admissions
  registry (axiom-encode#2095). Today it is dormant: it holds an empty
  `coverage-exemptions.jsonl`, and no workflow exports it to the encoder yet
  (`axiom-encode admission-registry export` from the protected `main`
  commit). A follow-up wires it into the shared validator; until then a
  record here admits nothing. `tests/test_admissions_registry.py` checks the
  file layout, and CODEOWNERS requests review.
