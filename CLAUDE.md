# rules-us-tx Agent Notes

This repo stores Texas RuleSpec encodings and source registry metadata.

## Do

- Put RuleSpec encodings under `statutes/`, `regulations/`, or `policies/`.
- Put tests beside each encoding as `.test.yaml`.
- Keep only source registry or manifest metadata under `sources/` when needed.

## Do Not

- Reintroduce `statute/`, `parameters.yaml`, `tests.yaml`, `tests/*.yaml`, or `.rac` artifacts.
- Put unrelated jurisdiction materials here.
- Add generated source payloads to Git.
