# rulespec-us-ca

California RuleSpec encodings and source registry metadata.

## Contents

- `statutes/`: California statute RuleSpec YAML, with tests beside each encoding as `.test.yaml`.
- `regulations/`: California regulation RuleSpec YAML, with tests beside each encoding as `.test.yaml`.
- `policies/`: California policy RuleSpec YAML, with tests beside each encoding as `.test.yaml`.
- `sources/`: source registry or manifest metadata when needed.
- `.github/workflows/repository-checks.yml`: wrapper around the shared RuleSpec validation workflow.

## Conventions

Use RuleSpec YAML for encoded rules. Do not add singular rule roots, separate
parameter/test fixture files, or generated formula artifacts.

Federal materials belong in `rulespec-us`. California-administered materials belong here.
