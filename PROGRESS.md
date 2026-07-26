# PR #1008 round-3 re-review

## State

Complete. Exact PR head `efc1d36023d0d820d938f698ed8e431b37962f8d` received a `REQUEST-CHANGES` verdict solely because the PR-only history retains the deleted session ledger. All substantive policy and focused-gate claims pass. No GitHub writes or pushes were made.

## Done

- Confirmed through the GitHub connector that PR #1008 points to the required head.
- Confirmed the connector-reported net diff contains five files and omits the atomic 7 CFR 247.9(a) files.
- Isolated the review from the dirty shared checkout.
- Audited the exact base-to-head diff and all 15 PR-only commits.
- Confirmed the atomic 247.9(a) YAML, companion, and manifest are absent from both the net diff and the base/head trees.
- Found that PR-only history still contains the session ledger: four commits add/update `PROGRESS.md`, and a fifth deletes it.
- Ran baseline validation successfully.
- Removed only the 247.9(a) condition proof atom and reproduced the exact Person-versus-Household source-scope validation failure, then restored the head file byte-for-byte.
- Grepped and read all five formulas in the changed policy. None computes or compares an age; the final formula consumes only a caller-supplied Boolean attestation.
- Audited every age numeral: `59`/`60` occur only in the source quotation, explanatory prose/comments, and one non-executable test name; no `61` occurs.
- Confirmed both State-Plan election omissions fail closed: complete-input controls return `holds`, while removing only the applicable election attestation makes the engine reject the evaluation with the exact missing-input error.
- Passed focused validation, proof validation (14 atoms), changed-module money proof, scoped `us/` money proof, and all 15 companion cases using `~/axiom-rules`.
- Matched both manifest-recorded SHA-256 values to the exact policy and companion bytes; the manifest-sync pytest file passes.
- Confirmed the corrected-head GitHub Actions `validate / generated-guard` job succeeds, verifying the signed manifest with the CI-held HMAC key.
- Wrote `/private/tmp/rereview2-1008-VERDICT.md`.
- Copied the byte-identical report to the requested Claude scratchpad path and verified both first lines and SHA-256 digests.
- Removed the generated GitNexus index from the review worktree, leaving the disposable review branch clean.

## Next

- No remaining review work.
