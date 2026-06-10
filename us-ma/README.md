# rulespec-us-ma

Massachusetts RuleSpec encodings.

## Contents

- `statutes/`, `regulations/`, or `policies/`: RuleSpec YAML when encoded rules are added.
- `.github/workflows/`: wrapper around the shared RuleSpec validation workflow.

## Conventions

Use RuleSpec YAML under `statutes/`, `regulations/`, or `policies/` for encoded rules. Do not add source text, source registry sidecars, generated source payloads, extracted document snapshots, or wave manifests to Git; source material belongs in the corpus database/object storage.

Jurisdiction-specific materials belong in this repo. Shared federal materials belong in `rulespec-us`.
