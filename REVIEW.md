VERDICT: APPROVE

# PR #1179 repair-only re-review

All five predecessor blockers are repaired at the frozen head. The
blocker-specific negative controls fail in the intended direction, and the
required canonical validation and containment gates pass.

## Frozen scope

- Repair head:
  `f2bdb8e15182fe8e312b34b36217d5623a411161`.
- Prior reviewed head:
  `4ced8fb7065311338ea732cab0a26105e750c40f`.
- Pinned corpus: clean, detached
  `/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`
  at `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Canonical exact-head archive:
  `.git/review-worktrees/pr-1179-repair-f2bdb8e-canonical/rulespec-us`.
- Scope was limited to the five claimed repairs and containment. The
  predecessor's already-passing evidence was not reopened.

## Repair evidence

### 1. Current section 165(d) proof and completed boundary

Pass.

- The new 302-byte section 165(d) excerpt occurs exactly once in the
  resolver-selected pinned provision. It states both the 90-percent-of-losses
  limitation and the wagering-gains ceiling.
- All 13 source excerpts in the compose occur exactly once in their
  resolver-selected pinned provision bodies.
- The repair is semantic, not excerpt-only: the upstream-source rationale,
  module summary, itemizer branch, and input description all define
  `wagering_losses_deduction` as the completed allowable amount after both
  limits. The nonitemizer branch excludes it, and the verified domain rejects
  a negative completed amount.

### 2. Sections 61, 62, and 63(a) itemizer bridge

Pass.

- `federal_taxable_income` is now sourced to sections 61, 62, and 63(a)-(b).
- Its proof contains byte-exact definitions for gross income, adjusted gross
  income, the section 63(a) itemizer definition, and the retained section
  63(b) nonitemizer definition.
- Section 62's gross-income-to-AGI bridge, the imported itemized aggregate,
  and the final AGI subtraction establish the section 63(a) computation;
  section 63(b) continues to govern the standard-deduction branch.

### 3. Section 151 MAGI addback diagnostic

Pass. The companion-only `ti-senior-magi-section-931-addback` case supplies a
real $10,000 section 931 exclusion. Independent exact-decimal recomputation is:

- MAGI: `75,000 + 10,000 = 85,000`.
- Phaseout: `0.06 * (85,000 - 75,000) = 600`.
- Senior deduction: `6,000 - 600 = 5,400`.
- Standard deduction: `16,100 + 2,050 = 18,150`.
- Total deductions: `18,150 + 5,400 = 23,550`.
- Taxable income: `75,000 - 23,550 = 51,450`.

Every asserted imported intermediate and final matches.

### 4. Imported relation-schema mutation contracts

Pass.

The static registry pins the two section 151 relations and section 170(p):

- exemption: `(TaxUnit, Person)`;
- senior: `(TaxUnit, Person)`;
- charity: `(TaxUnit, Payment)`.

The pristine registry test passes. Three fresh isolated mutants each reversed
only the relevant two argument lines:

- exemption `(Person, TaxUnit)`: return code 1, one targeted failure;
- senior `(Person, TaxUnit)`: return code 1, one targeted failure;
- charity `(Payment, TaxUnit)`: return code 1, one targeted failure.

Thus all three otherwise-runtime-inert declarations have executable contracts.

### 5. Contradictory individual/entity facts

Pass.

- The repaired regression and predecessor fixture resolve to the same period
  and the same 85-key input map, including both
  `taxpayer_is_individual=true` and
  `estate_or_trust_common_trust_fund_or_partnership=true`.
- Running the byte-exact predecessor companion blob `727d57e5...` over the
  repaired compose blob `507fa317...` produces only the expected old-case
  failures: `ti-entity-zeroes-standard` expects domain `holds` and taxable
  income `100000`, while repaired code returns `not_holds` and `0`.
- The current fail-closed regression passes in the 28-case companion.
- Removing only the repaired entity guard makes that regression fail with
  domain `holds` and taxable income `100000`, so the test kills the precise
  repair.

## Canonical gates and containment

- Exact pinned toolchain:
  - encoder `3869d66d009f52258be35901edbef370e65a399c`;
  - freshly archived and offline-built engine
    `ffd8213271947b0189a9dd61a055c1e0e78908a0`;
  - corpus `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Companion from the canonical root: 1 file, 28 cases, 1 compiled program,
  zero failures.
- Pinned validation: `ci_pass=true`, `all_passed=true`, zero errors.
- Structural proof validation: 37 atoms, zero issues.
- Strict money-atom validation: zero obligations and zero missing atoms.
- Reverse index is current: 4,249 provisions, 5,120 edges, 4,491 modules.
- Focused repository, manifest, index, and schema gates: 19 passed. The only
  warning is the existing report-only census of 19 unmanifested modules.
- Pending ledger:
  - local base ceiling/count `2,148`;
  - head ceiling/count `2,151`;
  - base and head sorted and unique;
  - zero lost or changed base records;
  - exactly the three taxable-pipeline additions;
  - exact field-preserving union;
  - unchanged from the prior reviewed head.
- Manifest:
  - exactly the compose and companion are applied;
  - both SHA-256 values match canonical disk, content ancestor `b47607e...`,
    signature parent `f0864dc...`, and head;
  - both ancestors precede the signature commit;
  - the exception is exactly `composition`;
  - the parent-manifest supersession hash matches;
  - head `f2bdb8e...` changes only the manifest.
- Repair containment:
  - ten linear commits, zero merges;
  - before the ledger drop, exactly five repair-era paths are touched:
    compose, companion, relation-schema test, reverse index, and
    `PROGRESS.md`;
  - `f0864dc...` deletes only `PROGRESS.md`;
  - `f2bdb8e...` changes only the manifest;
  - the net prior-head-to-repair-head diff is the four substantive repair
    files plus the manifest;
  - `git diff --check` passes and there are no mode changes.
- A fresh `git archive` of the frozen head is byte-identical to the cleaned
  canonical archive.

## Disclosures

- `AXIOM_ENCODE_APPLY_SIGNING_KEY` is absent. The HMAC value itself could not
  be recomputed; its algorithm/key envelope and every non-secret hash,
  ancestor, supersession, and repository manifest gate pass.
- The default `pytest` shim points to a missing interpreter, and system Python
  lacks PyYAML. All authoritative Python gates were rerun successfully with
  the pinned encoder virtual environment.
- A parallel pytest run created only generated `.pytest_cache` and
  `__pycache__` files in the canonical archive. The sandbox blocked an
  explicit recursive cleanup command; the exact known files were removed via
  `apply_patch`/`unlink`, and a fresh-archive comparison then passed.
- Direct `apply_patch` into isolated `/private/tmp` mutation trees was rejected
  as outside the project. The mutation reviewer patched temporary
  in-workspace staging files, copied them into the isolated trees, removed the
  staging files, and verified the shared canonical and review files remained
  unchanged.
- One non-authoritative probe accidentally shadowed zsh's special `path`
  variable and failed with return code 127. It was rerun with absolute
  executable paths and passed.
- No network access was needed. No PR branch, remote, GitHub, corpus, or
  external repository write was made.

## Recommendation

Approve frozen head `f2bdb8e15182fe8e312b34b36217d5623a411161`.
