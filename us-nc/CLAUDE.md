# rulespec-us-nc Agent Notes

This repo stores North Carolina RuleSpec source registry materials and related policy metadata.

## Do

- Keep jurisdiction-administered source slices under `sources/` when source slices are present.
- Add or update sidecar `.meta.yaml` files with source provenance, relations, and jurisdiction metadata.
- Add RuleSpec encodings under `statutes/`, `regulations/`, or `policies/` when ready.
- Keep parameter tables as structured YAML when they are useful reference data.
- Keep large source payloads outside Git and point to them through metadata or manifests.

## Do Not

- Add singular rule roots, separate parameter/test fixture files, or generated formula artifacts.
- Put unrelated jurisdiction materials here.
- Add generated source payloads to Git.
