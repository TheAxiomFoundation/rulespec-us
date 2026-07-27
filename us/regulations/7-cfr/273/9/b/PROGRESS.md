# Progress

## State

Paragraph (b) implementation and companion tests are complete. Targeted,
proof, money-atom, and reverse-index validation pass. Publication is waiting
for approval of the connected GitHub branch-creation action. The sole remaining
repository-suite failure is the unavailable signing-key handoff for the edited
parent manifest.

## Done

- Read the closure-sprint encoder preamble.
- Read the repository agent guidance in `CLAUDE.md`.
- Confirmed the worktree starts clean on `closure/enc-273-9b`.
- Read the required sibling modules and companion tests.
- Extracted the authoritative 7 CFR 273.9(b) text from the sprint corpus.
- Traced existing federal and Colorado SNAP income-composition surfaces.
- Confirmed the root repository layout disallows new top-level files; retained
  this committed ledger under the assigned slice instead.
- Implemented the paragraph (b) earned- and unearned-income classifications,
  paragraph (b)(5) payment-level non-inclusions, attributed/deemed components,
  and the required household-income composition.
- Aligned the payment relation shape and household-total boundary with the
  parallel paragraph (c) implementation. The resolved exclusion total is
  subtracted once and exclusions are not re-encoded here.
- Recorded the remaining upstream self-employment, disqualified-member,
  sponsored-alien, and post-exclusion earned/unearned split deferrals.
- Added 23 companion cases with explicit factual inputs, including rental and
  WIA age boundaries, classification conflicts, repayment exceptions, TANF
  transfers, and household composition.
- Removed only the satisfied paragraph (b) deferred output from the parent
  `273/9.yaml`; the separately owned paragraph (c) deferral remains.
- Passed pinned RuleSpec structural/CI validation for the parent and new module,
  plus all 27 parent and paragraph-(b) companion cases (23 in this slice).
- Hardened earned-source precedence over the broad government-payment residual,
  conservative one-time treatment of genuine earned/unearned conflicts, the
  foster-care-boarder exception, and the workers'/unemployment-only IPV
  withholding rule.
- Defined the paragraph-(c) boundary narrowly: only exclusions attributable to
  income actually included here plus true household-level adjustments, with
  exclusions already reflected upstream removed. The raw paragraph-(c) total
  still requires a scope adapter.
- Passed proof validation with 37 checked atoms and the zero-backlog money-atom
  gate.
- Ran the repository suite: 63 tests passed; the reverse-index freshness test
  and edited-parent signing-manifest test failed as expected.
- Regenerated the reverse index (4,232 provisions, 5,069 edges, 4,484 modules);
  all eight reverse-index tests now pass.
- Re-ran the full repository suite after the index refresh: 64 tests pass and
  only the edited-parent signing-manifest assertion fails.
- Confirmed signing dry-run requires manifests for the parent and new child;
  `AXIOM_ENCODE_APPLY_SIGNING_KEY` is unavailable in this environment.
- Confirmed remote `main` still matches the local base for both edited shared
  files. Direct shell push is DNS-blocked, and two connected GitHub branch
  creation attempts were canceled before making any remote change.

## Next

- Approve connected GitHub branch creation, publish the committed tree, and
  open the draft pull request.
- Hand off generation of the two signed apply manifests to an environment with
  `AXIOM_ENCODE_APPLY_SIGNING_KEY`.
