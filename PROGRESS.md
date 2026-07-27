# Massachusetts SNAP Medical-Deduction Evidence Progress

## State

The citation gate and RuleSpec fixture gate pass. The companion fixture carries
the exact five-case statutory boundary grid at $0, $35, $36, $190, and $191,
and released engine v0.1.1 passes all 33 cases in the source module. Oracle
registration and the one-output execution receipt remain in progress.

## Done

- Read the closure-sprint encoder preamble and repository agent notes.
- Read the r1 candidate row and evidence pointers for the Massachusetts SNAP
  medical-expense deduction.
- Read the employee-Medicare evidence package and draft PR #1149 as the
  required five-criterion model.
- Created the isolated `x3-ma-snap-medical` branch and worktree from cached
  `origin/main`.
- Attempted to refresh `origin/main`; shell network access could not resolve
  `github.com`, so the cached remote-tracking commit is the recorded base.
- Audited `axiom-corpus@db12795577c5809009168982cf8a72fb58440620` by citation
  path. The legacy inventory occurrence is at
  `data/corpus/inventory/us-ma/regulation/2026-05-28.json:5090`; the current
  union occurrence is at
  `data/corpus/inventory/us-ma/regulation/2026-07-24-ma-dta-regulations-snap-current-union.json:5438`.
- Resolved those occurrences to line 223 of their corresponding provision
  JSONL files. Both bodies have SHA-256
  `9e3d69d1db9913eb137b451dd7abcca074c3f7f7fa6b8eb8af8513e69cc69ecb`
  and contain the $35, $155, and $190 medical-deduction table.
- Confirmed the candidate is not one of j1's three malformed Massachusetts
  paths, which are `364/360/block-1`, `365/030/block-1`, and
  `366/140/block-1`.
- Replaced the broader four-case medical sample with a five-case January 2026
  boundary grid at $0, $35, $36, $190, and $191. Each case assigns the only
  RuleSpec input fact used by the medical-deduction output.
- Exported committed RuleSpec tree
  `87220d7d776b9a330b91bae3c42e929adf4ab35a` to a canonical stranger path and
  ran its companion through `axiom-encode test` with the clean released
  `axiom-rules-engine` v0.1.1 checkout. Receipt: one test file, 33 cases, one
  compiled program, zero failures.

## Next

- Inspect the real PolicyEngine variable body and register the five-case
  boundary grid with zero unexplained mismatches.
- Resolve the one-root/two-record closure ledger with zero pending paths.
- Compile and locally run the one-output module with released engine v0.1.1,
  while preserving the unpublished-artifact blocker.
- Assemble the five-criterion narrative, validation receipt, and final sprint
  report.
