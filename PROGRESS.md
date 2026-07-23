# PR #1003 Additional Medicare CI Fix Progress

## State

- Defensive correctness and completeness audit in progress on branch
  `fed-parity/surtaxes`.
- Scope is limited to deferring the generic Additional Medicare international
  agreement surface that overlaps the upstream deferred
  `self_employment_tax_after_international_agreement_exemption`.
- No pushes, manifest re-signing, workflow edits, or toolchain edits are
  authorized.
- The worktree was clean at the start.
- Read-only PR metadata confirms PR #1003 is open at head
  `8218c7baff9330cf1eb707bb7d2df87bfb4abcfc`.
- The local `gh` credential is invalid, so the supplied Actions job/error is
  the CI-log source of record; read-only PR context was retrieved through the
  GitHub connector.

## Done

- Read the `gh-fix-ci` workflow instructions.
- Confirmed the current worktree, branch, remote, and clean starting state.
- Confirmed the requested fix is already explicitly approved and constrained:
  defer the generic surface, preserve public output names and six grid results,
  and do not push or re-sign manifests.

## Next

- Identify the exact shared-workflow `Validate RuleSpec YAML` command.
- Inspect the Additional Medicare module, companions, upstream deferred output,
  and passing sibling patterns.
- Implement the smallest YAML and fixture change.
- Run CI-mode validation on all three PR #1003 pipelines and the PR #1002 PTC
  pipeline, plus proof validation, companions, reverse-index, and grid-result
  invariance checks.
- Record exact commands/results, final commit SHA, and any tooling limitations
  in the required DONE marker.
