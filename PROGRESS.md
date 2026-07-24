# PR #1003 blind-review fix wave

## State

- Active on `fed-parity/surtaxes`.
- Scope is limited to the three locally authored federal surtax pipelines,
  companion cases, generated local artifacts, and scratchpad handback files.
- `us/statutes/**` is read-only for this wave.
- No pushes or GitHub writes.
- Read the full blind-review verdict from the session scratchpad at
  `/private/tmp/claude-501/-Users-maxghenis-TheAxiomFoundation/53bdb134-6cd3-452d-89aa-000a8b5d77e3/scratchpad/review-1003-VERDICT.md`.

## Done

- Confirmed a clean starting worktree at `805542a2`.
- Confirmed the two existing local commits are the surtax implementation and
  regenerated shared indexes.
- Located the NIIT, self-employment-tax, and additional-Medicare-tax pipelines
  and their companion case suites.
- Read and mapped all ten blind-review findings.
- Confirmed the NIIT defects are upstream encoding defects that must be
  constrained locally rather than repaired under `us/statutes/**`.
- Confirmed the section 1401(c) defect is the missing runtime boundary on the
  additional-Medicare self-employment and combined outputs.
- Located existing fail-closed supported-domain patterns in the resident income
  tax pipelines and the explicit-boundary pattern in the WIC composition.
- Attempted the GitNexus debugging workflow. Its analyzer could not register
  inside the sandbox and indexed unrelated content, so the generated untracked
  index was removed and source inspection is being used instead.

## Next

- Add fail-closed NIIT domain guards and companion cases.
- Add the section 1401(c) boundary gate and companion case.
- Repair the locally authored section 1401 coordination proof citation.
- Add the requested boundary and joint-earner companion cases.
- Run the full gate battery and signing dry-run.
- Produce `scratchpad/fix-1003-BODY.md` and `scratchpad/fix-1003-DONE.md` with
  exact counts, ledger delta, gate results, and commit SHAs.
