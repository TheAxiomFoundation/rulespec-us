# rules-us-sc Agent Notes

This repo stores South Carolina RuleSpec source registry materials and related policy metadata.

## Do

- Keep jurisdiction-administered source slices under `sources/` when source slices are present.
- Add or update sidecar `.meta.yaml` files with source provenance, relations, and jurisdiction metadata.
- Keep parameter tables as structured YAML when they are useful reference data.
- Keep large source payloads outside Git and point to them through metadata or manifests.

## Do Not

- Reintroduce legacy executable formula payloads.
- Put unrelated jurisdiction materials here.
- Add AKN/XML source payloads to Git.
