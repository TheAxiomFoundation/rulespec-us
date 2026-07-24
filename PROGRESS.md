# PR #1003 blind-review fix wave

## State

- Active on `fed-parity/surtaxes`.
- Scope is limited to the three locally authored federal surtax pipelines,
  companion cases, generated local artifacts, and scratchpad handback files.
- `us/statutes/**` is read-only for this wave.
- No pushes or GitHub writes.
- The requested `scratchpad/review-1003-VERDICT.md` is not present in the
  worktree or elsewhere under the accessible Axiom Foundation directories;
  implementation is proceeding from the adjudicated findings in the task.

## Done

- Confirmed a clean starting worktree at `805542a2`.
- Confirmed the two existing local commits are the surtax implementation and
  regenerated shared indexes.
- Located the NIIT, self-employment-tax, and additional-Medicare-tax pipelines
  and their companion case suites.

## Next

- Trace existing validation, deferred-output, proof-atom, and case conventions.
- Add fail-closed NIIT domain guards and companion cases.
- Add the section 1401(c) boundary gate and companion case.
- Repair the locally authored section 1401 coordination proof citation.
- Add the requested boundary and joint-earner companion cases.
- Run the full gate battery and signing dry-run.
- Produce `scratchpad/fix-1003-BODY.md` and `scratchpad/fix-1003-DONE.md` with
  exact counts, ledger delta, gate results, and commit SHAs.
