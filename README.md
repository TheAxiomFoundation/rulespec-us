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
- `.axiom/toolchain.toml`: pinned validation toolchain (full commit SHAs).
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
  (rulespec-us#394).

Both lists fail CI on new entries AND on listed entries that get fixed
without being removed, so they only shrink.

Do not add singular rule roots, separate parameter/test fixture files, or
generated formula artifacts.
