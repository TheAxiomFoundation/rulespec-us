# PR #1007 re-review progress

## State

Adversarial review complete at the unchanged live PR head `db782aeadddba87f2d00713ff3e744471a54ca62`, compared with live base `8b5e7a18a9f91d73d1f618cdc4931ad16eac46fc`. Verdict: request changes.

## Done

- Loaded the PolicyEngine review workflow and original verdict.
- Confirmed the source checkout is detached and dirty; created this isolated throwaway worktree instead.
- Confirmed the live GitHub PR head/base metadata and that the head is four commits ahead of the current base.
- Captured the exact six-path base-to-head diff; `git diff --check` passes.
- Confirmed PR-only history names no `PROGRESS` or session-ledger path and no other policy lane.
- Baseline companion passes all 39 cases through the requested `~/axiom-rules` engine.
- Baseline companion passes all 39 cases through the exact pinned engine `ffd8213271947b0189a9dd61a055c1e0e78908a0`.
- B3 mutant commit `2ae14ee6a`: reversed relation arguments to applicant-first/member-second.
- The complete 39-case companion still passed on both requested and pinned engines (exit 0).
- Pinned compiled IR remained `current_slot=1, related_slot=0`, proving the declared argument mutation was not observed at runtime.
- B4 mutant commit `5fc355740`: swapped the selected current-month and projected-annual ratio streams.
- The companion failed on both requested and pinned engines (exit 1; 11 assertions).
- The asymmetric B4 case changed from ratio `1.5`/ineligible to `0.5545286506...`/eligible, directly detecting reversal.
- Pinned `axiom-encode 0.2.1200` validate passes against the exact pinned corpus archive.
- Proof validation passes with 82 atoms.
- Federal money-proof passes: 40 missing among 540 obligations, within the 151 ratchet.
- Focused contract tests pass: 4/4.
- Reverse index regeneration check passes: 4,222 provisions, 5,043 edges, 4,476 modules.
- Source policy is restored byte-for-byte to the live PR head after both mutants.
- Manifest policy, companion, generated-output, and supersedes hashes all match exactly.
- Independent B6 probes found two remaining fail-open contradictions: family-1 size with family-2 FPL plus a true attestation, and canonical age 19 with self-row age 65.
- Base/head semantic comparison of `oracle-coverage-pending.yaml` found 17 removed non-Medicaid declarations: 12 Head Start and 5 WIC.
- Merge commit `a8686bc05` remerge evidence identifies a shared-ledger conflict resolution as the removal source.
- The pending-ratchet check reports those 17 outputs as undeclared; all 61 new Medicaid entries are present.
- Live GitHub validation is red across all jurisdiction shards and the aggregate `validate` job at the unchanged PR head.
- Confirmed the original B1, B2, B4, and B5 defects are repaired and State elections fail closed when unresolved.
- Replayed both B6 contradictions independently; exact normalized output hashes match the recorded probes.
- Rechecked live PR metadata immediately before consolidation; head and base SHAs are unchanged.

## Next

- Make the B3 companion fail when the declared relation arguments are reversed, including surfacing the `$9,876.54` nonmember sentinel.
- Replace the family-size/FPL attestation with executable correspondence validation, and reject contradictory canonical versus row-level applicant ages.
- Restore the 12 Head Start and 5 WIC pending-oracle declarations dropped by the repair merge, then rerun the exact CI ratchet.
- Re-run the adversarial mutants and fail-closed counterexamples before approval.

