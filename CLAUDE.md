# rulespec-us Agent Notes

This repo stores US federal RuleSpec encodings and source registry metadata.

## Do

- Put RuleSpec encodings under `statutes/`, `regulations/`, or `policies/`.
- Put tests beside each encoding as `.test.yaml`.
- Keep only source registry or manifest metadata under `sources/` when needed.
- Treat all RuleSpec YAML as protected output, including atomic modules,
  companion tests, root `programs/` compositions, and legacy
  `<jurisdiction>/manual/` modules.
- Install atomic RuleSpec modules and companion tests only with the
  repository-pinned `axiom-encode encode <citation> --apply`. This command
  writes the protected signed apply receipt.
- Do not modify root `programs/` compositions. The pinned toolchain has no
  current signed ProgramSpec-authoring receipt path. The repository's local
  and base-to-head CI freezes reject ProgramSpec changes while shared CI still
  sets `guard-programs-root: false`; stop and report that blocker.
- Treat legacy `<jurisdiction>/manual/` RuleSpec as immutable. Its v1 owner
  requires the pinned encoder's specialized legacy replacement workflow,
  which the local and base-to-head CI freezes intentionally do not accept yet;
  stop and report the needed migration.
- Retire RuleSpec YAML only with the repository-pinned `axiom-encode retire`.
- Rename RuleSpec paths only with the repository-pinned
  `axiom-encode migrate-rulespec-paths`.
- Run the fast local receipt preflight before commit:
  `python -m pytest -q tests/test_encoding_manifests.py::test_locally_changed_rulespec_has_same_change_encoder_receipt`.
  Fetch `origin` first: this scans from the unique merge-base with canonical
  `origin/main` through `HEAD`, plus staged, unstaged, and untracked changes.
  In GitHub push CI, a validated nonzero event `before` may only widen that
  range to a unique ancestor no newer than both coverage witnesses; it can
  never narrow canonical coverage. Missing, unavailable,
  zero-without-an-older-boundary, or ambiguous bases fail closed.
- When remote publication is authorized, open a draft PR promptly after the
  first signed apply so shared `guard-generated` runs. Never override an
  explicit instruction to keep work local or unpublished.

## Do Not

- Add singular rule roots, separate parameter/test fixture files, or generated formula artifacts.
- Put unrelated jurisdiction materials here.
- Add generated source payloads to Git.
- Create, copy, modify, or delete RuleSpec YAML with an editor, `apply_patch`,
  or any other manual write path. Do not hand-refresh an encoding manifest. If
  the encoder, corpus, or signing broker blocks apply, retirement, or migration,
  stop and report the exact blocker instead of changing RuleSpec YAML manually.
