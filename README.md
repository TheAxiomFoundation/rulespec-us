# rules-us-tx

Texas RuleSpec encodings and source registry metadata.

## Contents

- `statutes/`: Texas statute RuleSpec YAML, with tests beside each encoding as `.test.yaml`.
- `regulations/`: Texas regulation RuleSpec YAML, with tests beside each encoding as `.test.yaml`.
- `policies/`: Texas policy RuleSpec YAML, with tests beside each encoding as `.test.yaml`.
- `sources/`: source registry or manifest metadata when needed.
- `.github/workflows/repository-checks.yml`: wrapper around the shared RuleSpec validation workflow.

## Conventions

Use RuleSpec YAML for encoded rules. Do not add singular rule roots, separate
parameter/test fixture files, or generated formula artifacts.

Jurisdiction-specific materials belong in this repo. Shared federal materials belong in `rules-us`.
