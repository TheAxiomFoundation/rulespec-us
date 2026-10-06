# Target-validation-pass registration report

## Outcome

Stopped after Step 1. The pinned consumer cannot represent or verify a registration assembled from the listed PR-gate runs. No registration was built, no module or configuration file was changed, and no commit was created.

The required `git fetch origin main` failed because this environment cannot resolve `github.com`. The cached `origin/main` is `747d54f5382f16501fe14dd11ea4a6491d1e120f` (2026-08-14 10:10:27 -0400, merge of PR #1292). Creating the requested sibling worktree was also denied by the filesystem sandbox after the requested branch ref was created. This report therefore resides in the existing worktree, uncommitted.

## Contract findings

The authoritative consumer inspected was:

`TheAxiomFoundation/.github` commit `b380085c`, `.github/workflows/validate-rulespec-legacy-pending-safe.yml`, function `print_protected_target_passes`.

It requires the top-level object to contain exactly:

- `schema_version` equal to `1`
- `evidence_type` equal to `rulespec-target-validation-passes/v1`
- one `source_artifact`
- one exact `toolchain` block
- one `workflow_run`
- one non-empty `modules` object

The single-run binding is substantive, not informational:

1. `workflow_run.run_id` is fetched from GitHub and must be a completed successful `pull_request` run of `.github/workflows/waiver-fingerprint-scratch.yml` with matching `head_sha`.
2. The consumer hard-codes the synthetic execution commit `1f98c0616ffe467cc089341f910e433422a21c6a`, verifies that its second parent is the recorded run head, and derives the protected base from its first parent.
3. It verifies the exact protected-base toolchain bytes, target corpus identity, a hard-coded workflow digest, and exact tool checkout refs.
4. It downloads exactly one artifact named `waiver-fingerprints-chunk-NNN`, verifies its SHA-256, and requires the artifact module inventory to equal the registration module inventory exactly.
5. For every module, it requires `passed: true`, a syntactically valid SHA-256 fingerprint, equality with the fingerprint in that artifact, and `module_sha256` equality to both the module bytes at the hard-coded execution commit and the current protected-base bytes.
6. Companion files are not separate entries in `modules`. Their presence/path and bytes come from each artifact module's `outcome.companion`; current companion bytes must equal the bytes at the same execution commit.
7. Skipping occurs only in `full-waiver-migration` mode, for relevant roots, when the path is not a validation waiver and is unchanged relative to the comparison base.

PR #917's local merge commit is `1dcb080613d50c1bffe9ad8b26fc6b7367217401` (`Record protected v5 target-toolchain passes (#917)`). It introduced only `.axiom/target-validation-passes.json`, registering two modules from run `29466984289` and one `waiver-fingerprints-chunk-000` artifact. The fingerprints are validation-result fingerprints copied from the protected workflow artifact; they are not hashes of module bytes. Module bytes are independently bound by `module_sha256`. Searches in the two requested axiom-encode trees found no producer for this evidence type; the consumer identifies the producer as the separately reviewed scratch workflow and artifact.

## Why the requested build is invalid

The listed evidence spans ten PRs/runs (#1275, #1276, #1280, #1284, #1286, #1287, #1288, #1290, #1292, and #1293). Schema v1 has no run-per-module field or multiple-run collection. More importantly, the consumer requires one artifact whose inventory exactly equals all registered modules and validates every module and companion against one execution commit. Combining fingerprints from several runs would fail the exact artifact-inventory check and execution-commit byte checks.

The existing consumer is additionally pinned to the historical #917 execution commit and reviewed scratch-workflow digest, so merely producing a fresh artifact is insufficient unless the shared workflow's reviewed binding is updated to that new evidence run.

## Recommendation

Trigger one dedicated protected evidence run, from one source revision containing every generated tariff module and companion intended for registration, using a reviewed fingerprint workflow that emits a single artifact covering the exact registration inventory. Then update the shared workflow consumer in `TheAxiomFoundation/.github` through review so its execution-commit and workflow-digest bindings identify that run/harness. After that shared-workflow pin is available to rulespec-us, generate the schema-v1 registration from the one artifact and compute every `module_sha256` from the exact committed bytes.

An alternative is a reviewed schema/consumer v2 that models multiple independently verified runs and binds each module to its source run/artifact/execution commit. The present v1 consumer does not support that design.

## Verification and commit

Steps 2 and 3 were intentionally not run because the contract is blocking. Residual runtime was not estimated because no valid skip set exists yet.

Commit SHA: none (stop-after-Step-1 condition).
