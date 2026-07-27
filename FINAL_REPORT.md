# CO SNAP deferred-module closure report

## Status

Implementation is complete and committed locally on
`closure/enc-co-stubs`. A draft PR was not created:

- `git push -u origin closure/enc-co-stubs` failed because this sandbox cannot
  resolve `github.com`.
- The connected GitHub app cancelled both attempted repository writes.

The intended draft PR title is
`Resolve or sharpen four CO SNAP deferred modules`, with a reference to
TheAxiomFoundation/rulespec-us#1135.

## Module outcomes

- `4.000.1`: resolved all three outputs (`abawd`, `household`, and
  `person_experiencing_homelessness`) with executable Person/Household
  judgments and boundary/branch tests. The prior `entity_not_supported`
  rationale was false. The pinned engine supports these entity-scoped
  judgments; although it cannot automatically materialize new Household IDs,
  that capability is not needed for a judgment over a caller-supplied
  candidate Household.
- `4.702.4`: resolved the public-institution release-date branch with the
  collision-free export
  `joint_ssi_snap_public_institution_untimely_release_notice_benefits_restored_to_release_date`
  and companion tests.
- `4.903.3`: resolved `snap_me_review_system_administration` and encoded the
  State Department responsibility and four ME-review objectives as
  `StateAgency` judgments with tests.
- `4.903.4`: resolved `snap_qa_review_scope`; also encoded the 12-month period
  value, federal QA purposes, active-case scope, and negative-case scope with
  tests. One deferred output remains:
  `annual_federal_qa_review_period`.

Six of the seven assigned deferred outputs are satisfied. The sole remaining
output is genuinely engine-blocked: pinned engine
`ffd8213271947b0189a9dd61a055c1e0e78908a0` supports Date values,
`period_start`, `period_end`, `date_add_days`, and `days_between`, but the
authoring formula surface has no date-literal expression, calendar-component
extraction, date-from-parts construction, month/year arithmetic, or
interval-valued derived output. Hard-coding one fiscal year or accepting
preclassified calendar booleans would misstate the recurring October 1 through
September 30 rule.

## Validation

Passed:

```text
PYTHONPATH=/private/tmp/axiom-encode-3869d66/src /Users/maxghenis/TheAxiomFoundation/axiom-encode/.venv/bin/axiom-encode validate /private/tmp/rulespec-us/us-co/regulations/10-ccr-2506-1/4.000.1.yaml /private/tmp/rulespec-us/us-co/regulations/10-ccr-2506-1/4.702.4.yaml /private/tmp/rulespec-us/us-co/regulations/10-ccr-2506-1/4.903.3.yaml /private/tmp/rulespec-us/us-co/regulations/10-ccr-2506-1/4.903.4.yaml --skip-reviewers
```

All four modules passed CI validation.

```text
PYTHONPATH=/private/tmp/axiom-encode-3869d66/src /Users/maxghenis/TheAxiomFoundation/axiom-encode/.venv/bin/axiom-encode proof-validate us-co/regulations/10-ccr-2506-1/4.000.1.yaml us-co/regulations/10-ccr-2506-1/4.702.4.yaml us-co/regulations/10-ccr-2506-1/4.903.3.yaml us-co/regulations/10-ccr-2506-1/4.903.4.yaml
```

Proof validation passed with 6, 2, 5, and 7 atoms respectively.

```text
PYTHONPATH=/private/tmp/axiom-encode-3869d66/src /Users/maxghenis/TheAxiomFoundation/axiom-encode/.venv/bin/axiom-encode test --root /Users/maxghenis/TheAxiomFoundation/_worktrees/enc-co-stubs --axiom-rules-engine-path /private/tmp/axiom-rules-engine-ffd8213 us-co/regulations/10-ccr-2506-1/4.000.1.test.yaml us-co/regulations/10-ccr-2506-1/4.702.4.test.yaml us-co/regulations/10-ccr-2506-1/4.903.3.test.yaml us-co/regulations/10-ccr-2506-1/4.903.4.test.yaml
```

All 21 companion cases passed.

```text
/Users/maxghenis/TheAxiomFoundation/axiom-encode/.venv/bin/python tests/generate_reverse_index.py --check
git diff --check origin/main...HEAD
```

The reverse index is current (4,232 provisions, 5,068 edges, 4,483 modules),
and the diff check passed.

Known failing gate:

```text
PYTHONPATH=/private/tmp/axiom-encode-3869d66/src /Users/maxghenis/TheAxiomFoundation/axiom-encode/.venv/bin/axiom-encode guard-generated --repo /Users/maxghenis/TheAxiomFoundation/_worktrees/enc-co-stubs --base-ref origin/main --head-ref HEAD --roots 'us us-co'
```

`guard-generated` reports stale signed apply manifests for the eight changed
module/test files. Refreshing them requires
`AXIOM_ENCODE_APPLY_SIGNING_KEY`, which is not available in this environment.
No unsigned or fabricated manifest was committed.

## Judgment calls

- Treated `4.000.1` as executable definitions, not an engine issue: existing
  sibling modules already encode the same household definition, ABAWD
  conditions, and homelessness residence alternatives on supported entities.
- Kept the 4.702.4 lateness fact neutral about who caused the notice delay; the
  authoritative sentence says only that the local office was not notified
  timely.
- Modeled 4.903.3 and the substantive 4.903.4 requirements as StateAgency
  compliance judgments, consistent with adjacent executable 4.903 modules.
- Preserved only the recurring calendar interval as deferred instead of
  disguising the missing date/interval capability behind caller-supplied
  booleans.

No files under `programs/`, no toolchain pins, CI workflows, CODEOWNERS, or
`oracle-coverage-pending.yaml` were changed.

The required target
`/Users/maxghenis/TheAxiomFoundation/_closure-sprint/out/d1-state-stubs.result.md`
could not be written because it is outside the sandbox's writable roots. This
tracked file is the complete fallback copy.
