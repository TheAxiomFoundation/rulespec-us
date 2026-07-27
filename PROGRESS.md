# Massachusetts SNAP Medical-Deduction Evidence Progress

## State

Evidence assembly is complete at 4 of 5 criteria. `provision_rooted`,
`conformant`, `exercised`, and candidate citation-path `closed` hold.
`executable` does not: the released-v0.1.1 local probe passes but has 11
derived outputs and is unpublished. This is not a certification.

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
- Compiled the unchanged module twice with the clean v0.1.1 tagged source
  checkout. Both format-2 artifacts had SHA-256
  `840cb8ec694600ad478e5befaeb81c1d791791157510ffa57acf97fe845e7a5b`.
- Ran the committed-node golden request for $191 monthly verified medical
  expense through `run-compiled`; it exited zero and returned decimal USD
  $156 with no fallback.
- Recorded the executable blockers without substituting a development engine
  or synthetic module: the artifact has 11 derived outputs, no one-output
  medical program exists, and the local artifact is unpublished.
- Registered and committed the exact five-case oracle grid at
  `axiom-oracles@929aa84e7db51ff071bb7515fedac7790c44a731`.
  Its pinned PE-US 1.767.3 run matches 5/5 with zero mismatches and zero
  errors; focused tests pass 26/26.
- Promoted the exact oracle mapping to
  `snap_excess_medical_expense_deduction` and disclosed the restricted
  Household-to-SPMUnit, annual-to-monthly, eligibility, and source-version
  boundaries.
- Closed the candidate citation-path ledger at one encoded unique path, zero
  excluded, and zero pending. Preserved the explicit caveat that this is not
  semantic completeness of the monolithic 364.400 provision.
- Wrote the complete five-criterion package at
  `us-ma/snap/v1-medical-deduction-evidence.md`.

## Next

- Publish a provenance-stamped one-output medical artifact and execute it on
  an official released-v0.1.1 stranger path before any certification.
- Obtain human review of the narrow candidate-path meaning of `closed`; use a
  3-of-5 verdict if full-provision semantic closure is required.
- Push the branches and open draft review PRs when GitHub DNS is available.
