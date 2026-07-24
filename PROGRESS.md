# PR 1003 round-3 review progress

## State

- In progress: the scoped review supports `REQUEST-CHANGES`; exact-head
  `program-artifacts` CI is the only outstanding observation.
- Review mode: read-only product review in a throwaway worktree.
- Live PR head reported by GitHub and reviewed locally:
  `3327de19395465dee736061b2d4c33108416d261`.
- Round-2 reviewed head: `d486f0997c62e1d3f1fbc382b0675b853bbcc144`.
- Exact rebased round-2 comparison range:
  `88e9b55c37b15c2f04d2142d45da374c041924fc..3327de19395465dee736061b2d4c33108416d261`.

## Done

- Read `rereview-1003-VERDICT.md` in full.
- Captured the rewritten live PR body and remote metadata.
- Confirmed the original checkout contains unrelated user changes and will not be touched.
- Created this isolated worktree from the exact live head.
- Used `git range-diff` to establish that `88e9b55c` is the rebased
  equivalent of the round-2 head; reviewed only the 14 later commits for
  round-2 regressions.
- Confirmed the ordinary SECA outputs now consume the §1401(c) attestation
  guard. The false-attestation companion preserves pre-relief income
  `46175` and makes OASDI, HI, and total tax all zero.
- Confirmed the floor companions now exercise the imported §1402(b)(2)
  branch: gross inputs `433` and `434` produce net earnings `399.8755`
  and `400.799`, respectively, on opposite sides of the `400` floor.
- Found the round-2 provenance blocker unresolved. The exact pinned corpus
  `710a326366bd233c40d64ca89b62a07082f13ce3` has zero matches for the
  corrected §1401(b)(2)(B) excerpt used by the proof atoms and retains the
  defective `3121(b)(2)` wording plus a §45A source artifact. The policy
  and PR body therefore make an unsupported hash-chained provenance claim.
- Found the rewritten body still presents NIIT and SECA 6/6 oracle reports
  from `f0eaa0cf657a40edfcb5491fde243cd051ec67af` as head evidence. Those
  reports omit the new required fail-closed attestation inputs and cannot
  substantiate the reviewed head without qualification or regeneration.
- Ran the focused gates against the exact current pins: validation 3/3,
  proofs 46/46 (10 NIIT, 19 SECA, 17 Additional Medicare), and companions
  42/42 (15 NIIT, 13 SECA, 14 Additional Medicare).
- Checked both the full PR diff and round-2-only diff with `git diff
  --check`. Reviewed the seven-file round-2 net delta; manifests, signed
  supersession metadata, and the sorted duplicate-free oracle ledger are
  internally consistent. The unsupported proof excerpts are the new
  defect introduced by the round-2 commits.
- Observed exact-head CI: Repository Checks `30124844097` and Source
  staleness/reverse index `30124843757` completed successfully.

## Next

- Record the terminal state of exact-head `program-artifacts` run
  `30124843759`.
- Write and commit `round3-1003-VERDICT.md`.
- Copy the committed verdict to the requested scratchpad output and remove
  the throwaway worktree.
