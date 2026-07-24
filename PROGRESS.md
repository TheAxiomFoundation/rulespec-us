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
- Added `niit_verified_domain_applies`, which requires zero qualified-plan and
  section-1401(b) inputs, zero imported section-911 adjustment amounts, a
  disjoint post-classification category attestation, and a zero separate
  working-capital slot.
- Gated the public NIIT Money output to return zero whenever that Judgment is
  `not_holds`.
- Declared three deferred unrestricted NIIT surfaces tied to the rulespec-us
  upstream issues referenced in the PR body.
- Added six isolated NIIT fail-closed cases; all 15 NIIT companions pass.
- Pinned NIIT validation passes: schema/CI, 10 proof atoms, and zero missing
  money atoms.
- Added the required
  `additional_medicare_tax_pipeline_self_employment_domain_is_valid` boundary.
  When its section 1401(c) attestation fails, the public self-employment and
  combined outputs return zero while the independently valid wage leg remains
  observable.
- Added a section 1401(c) fail-closed case and a joint two-positive-SE-earner
  case proving one tax-unit threshold; all 14 Additional Medicare companions
  pass.
- Repaired both local section 1401(b)(2)(B) coordination proof atoms with the
  fullest exact excerpt served at `us/statute/26/1401`, including its
  cross-reference, and documented the corpus record's upstream `source_url`
  metadata defect without editing the corpus or statute module.
- Pinned Additional Medicare proof validation passes all 17 atoms with zero
  missing money atoms. Direct validation from this worktree hit the known
  noncanonical-basename import-resolution limitation; the same gate remains
  queued in a committed canonical-basename clone.
- Added the two-positive-earner SECA case proving independent per-person wage
  coordination and OASDI caps before TaxUnit aggregation; all 12 current SECA
  companions pass.
- Added a source-backed, non-tax floor-characterization Judgment accepting a
  completed post-paragraph-(12) amount. Its exact-$400 case proves that the
  imported section 1402(b)(2) threshold is inclusive without approximating the
  repeating pre-adjustment amount or changing any public tax output.
- All 13 SECA companions pass. Pinned validation passes with 17 proof atoms and
  zero focused money-atom omissions.

## Next

- Run the full gate battery and signing dry-run.
- Produce `scratchpad/fix-1003-BODY.md` and `scratchpad/fix-1003-DONE.md` with
  exact counts, ledger delta, gate results, and commit SHAs.
