# PR 1002 residual fix progress

## State

In progress. The round-two verdict identifies one implementation residual:
public legally operative ACA PTC intermediates still emit the unrounded
calculation chain when `aca_ptc_full_year_runtime_inputs_valid` is
`not_holds`.

## Done

- Read `rereview-1002-VERDICT.md`.
- Confirmed the requested scope: gate every public arithmetic output on the
  existing runtime-input-validity judgment, extend the 210%-FPL off-grid
  companion, run focused validation/proof/companion gates and repository
  pytest, and leave the PR body and `us/statutes` untouched.

## Next

- Trace the policy outputs, schema conventions, and focused test commands.
- Implement fail-closed gates and companion expectations.
- Run the requested gates, record results, and write
  `fix2-1002-DONE.md` with the final commit SHA.
