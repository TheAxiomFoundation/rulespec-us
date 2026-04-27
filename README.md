# rules-us-sc

South Carolina RuleSpec source registry and policy metadata.

## Contents

- `sources/`: source slices, target manifests, and sidecar metadata when available.
- `statute/`, `regulation/`, or `legislation/`: retained structured source metadata and parameter tables when available.
- `.github/workflows/`: repository guards that keep legacy executable formula payloads out of Git.

## Conventions

Use RuleSpec YAML for new encoded rules. Keep source text with matching `.meta.yaml` files that record provenance and relations. Large XML or source payloads belong in object storage, with only registry or manifest metadata in Git.

Jurisdiction-specific materials belong in this repo. Shared federal materials belong in `rules-us`.
