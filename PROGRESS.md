# CO SNAP deferred-module closure

## State

Implementation and source review are complete for the four modules assigned by
the 2026-07-27 closure audit. Publication is blocked by the current
environment:

- `4.000.1`: encoded all three assigned definitions after confirming that
  Person and Household judgments are supported.
- `4.903.3`: encoded State Department ME-review responsibility, objectives,
  and their aggregate administrative compliance judgment.
- `4.903.4`: encoded the QA purposes and active/negative case review scope;
  retained only the recurring annual interval as an exact engine deferral.
- `4.702.4`: encoded the public-institution release-date restoration branch
  with a collision-free, branch-specific export.

The certified program composition remains frozen and out of scope.

## Done

- Read the encoder preamble and repository-specific agent rules.
- Confirmed the worktree began clean on `closure/enc-co-stubs`.
- Located the required final report at
  `/Users/maxghenis/TheAxiomFoundation/_closure-sprint/out/d1-state-stubs.result.md`.
- Read all four authoritative Colorado provision bodies and each existing
  deferral reason.
- Confirmed from the pinned engine and sibling RuleSpecs that `4.000.1` has no
  entity blocker: caller-supplied Person and Household judgments are supported.
- Encoded and added boundary/branch tests for `abawd`, `household`, and
  `person_experiencing_homelessness`.
- Pinned `axiom-encode` validation, proof validation, and all nine companion
  cases pass for `4.000.1`.
- Removed the collision-only `4.702.4` deferral and encoded the joint SSI/SNAP
  public-institution release-date restoration branch with companion tests.
- Pinned validation, proof validation, and all four companion cases pass for
  `4.702.4`.
- Removed the stale administrative-process deferral from `4.903.3` and
  encoded the State Department's ME-review responsibilities and objectives.
- Pinned validation, proof validation, and all three companion cases pass for
  `4.903.3`.
- Encoded the 4.903.4 twelve-month value, federal QA purposes, and active and
  negative case scope; removed the stale administrative-process deferral.
- Narrowed `4.903.4#annual_federal_qa_review_period` to the pinned engine's
  missing recurring-calendar construction and interval-output capabilities.
- Pinned validation, proof validation, and all five companion cases pass for
  `4.903.4`.
- Independent source review tightened the 4.903.4 liability fact to errors
  above the federal target and expanded the negative-case citation to include
  the paragraph's lead sentence.
- Regenerated the deterministic provision-to-rule reverse index for the three
  modules that gained proof-atom provenance.
- Aggregate pinned validation and proof validation pass for all four modules;
  all 21 companion cases pass, and the reverse source index is current.
- `guard-generated` remains blocked because the four existing signed apply
  manifests need refreshed hashes and this environment does not provide
  `AXIOM_ENCODE_APPLY_SIGNING_KEY`; no unsigned manifest was fabricated.
- `git push -u origin closure/enc-co-stubs` cannot resolve `github.com`, and
  the connected GitHub app cancelled branch-write attempts, so no draft PR was
  falsely reported as created.
- The required closure-sprint output path is outside the sandbox's writable
  roots; the complete report is preserved in tracked `FINAL_REPORT.md`.

## Next

- From a network-enabled or connector-authorized environment, push
  `closure/enc-co-stubs` and open the requested draft PR titled
  `Resolve or sharpen four CO SNAP deferred modules`, referencing
  rulespec-us#1135.
- Refresh the four signed apply manifests from an approved signing environment,
  then rerun `guard-generated`.
