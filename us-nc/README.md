# rulespec-us-nc

North Carolina RuleSpec source registry and policy metadata.

## Contents

- `sources/`: source slices, target manifests, and sidecar metadata when available.
- `statutes/`, `regulations/`, or `policies/`: RuleSpec YAML when encoded rules are added.
- `.github/workflows/`: wrapper around the shared RuleSpec validation workflow.

## Conventions

Use RuleSpec YAML under `statutes/`, `regulations/`, or `policies/` for encoded rules. Keep source text with matching `.meta.yaml` files that record provenance and relations. Large XML or source payloads belong in object storage, with only registry or manifest metadata in Git.

Jurisdiction-specific materials belong in this repo. Shared federal materials belong in `rulespec-us`.
