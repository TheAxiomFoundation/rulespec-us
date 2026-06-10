# rulespec-us-ca Agent Notes

This repo stores California RuleSpec encodings and source registry metadata.

## Do

- Put RuleSpec encodings under `statutes/`, `regulations/`, or `policies/`.
- Put tests beside each encoding as `.test.yaml`.
- Keep only source registry or manifest metadata under `sources/` when needed.

## Do Not

- Add singular rule roots, separate parameter/test fixture files, or generated formula artifacts.
- Put federal source slices or federal RuleSpec outputs here; use `rulespec-us`.
- Add generated source payloads to Git.
