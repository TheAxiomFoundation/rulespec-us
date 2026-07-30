# Chunk 2 taxable-income pipeline progress

## State

The binding SPINE-PLAN §§5, 6.3, and 9 have been read. The designated worktree is on
`fed-parity/chunk2-taxable-income` at `ae64af274`, exactly matching `origin/main`.
Implementation discovery is beginning from a clean tree.

## Done

- Verified that `origin/main` contains merged Chunk 1 and Atomic PR 0.
- Created the requested worktree and branch because neither existed locally.
- Confirmed the exact taxable-income import set, public output, cases, and commit order.

## Next

- Audit merged pipeline precedents, imported surfaces/hashes, schema contracts, index generation,
  pending-ledger format, and manifest commands.
- Design the fail-closed compose and full companion case/mutation suite.
