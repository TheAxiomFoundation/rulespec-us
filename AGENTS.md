# rulespec-us agent instructions

Every RuleSpec YAML file is protected output in this repository, including
atomic modules, companion tests, root `programs/` compositions, and the legacy
`<jurisdiction>/manual/` module.

- Install every atomic RuleSpec module and companion `.test.yaml` only with
  the repository-pinned `axiom-encode encode <citation> --apply` command. The
  apply must produce the protected signed encoding receipt under
  `.axiom/encoding-manifests/`.
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
- Before commit, run
  `python -m pytest -q tests/test_encoding_manifests.py::test_locally_changed_rulespec_has_same_change_encoder_receipt`
  for fast local receipt feedback. Fetch `origin` first: this scans from the
  unique merge-base with canonical `origin/main` through `HEAD`, plus staged,
  unstaged, and untracked changes. In GitHub push CI, a validated nonzero
  event `before` may only widen that range to a unique ancestor no newer than
  both coverage witnesses; it can never narrow canonical coverage. Missing,
  unavailable, zero-without-an-older-boundary, or ambiguous bases fail closed.
- When remote publication is authorized, open a draft PR promptly after the
  first signed apply so shared `guard-generated` runs. Never override an
  explicit instruction to keep work local or unpublished.
- Never create, copy, modify, or delete RuleSpec YAML with an editor,
  `apply_patch`, or another manual write path. Never hand-create or refresh an
  encoding manifest.
- If the encoder, source corpus, or signing broker prevents apply, retirement,
  or migration, stop and report the exact blocker. Do not copy candidate YAML
  into the live RuleSpec tree as a workaround.
