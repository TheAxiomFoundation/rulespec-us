VERDICT: REQUEST-CHANGES

# Blind adversarial review — rulespec-us PR #1179

Risk: HIGH. The prescribed arithmetic and most mechanical gates are clean,
but five binding legal/proof/diagnostic guards fail.

## Frozen target

- Expected branch: `fed-parity/chunk2-taxable-income`.
- Frozen candidate head:
  `4ced8fb7065311338ea732cab0a26105e750c40f`.
- Local branch and `origin/fed-parity/chunk2-taxable-income` agree at that
  commit; the remote-tracking reflog records an update by push at
  `2026-07-29 22:42:47 -0400`.
- Local base: `origin/main` at
  `ae64af2740340a40d04ed3c652254f53e62fab61`.
- Immutable reviewed range:
  `ae64af2740340a40d04ed3c652254f53e62fab61..4ced8fb7065311338ea732cab0a26105e750c40f`.
- Pinned corpus: clean, detached
  `/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`
  at `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Executable checks ran from the canonical-basename exact-head archive
  `.git/review-worktrees/pr-1179-canonical/rulespec-us`.

## Blocking findings

### 1. The §165 proof quotes prior law and omits the 2026 90% limit

`taxable_income_pipeline.yaml:127-128` says wagering losses are allowed only
to the extent of wagering gains. That sentence occurs zero times in the
resolver-selected pinned §165 provision.

Current §165(d) at pinned
`data/corpus/provisions/us/statute/2026-07-27-usc-63-repair-165-title-26.jsonl:64`
requires both:

- the deductible amount equals 90% of wagering losses; and
- the deduction cannot exceed wagering gains.

A byte-level audit of all nine source excerpts in the new compose found eight
unique exact matches and this one missing. Pinned structural proof validation
still passed 33/33 because it does not compare excerpt bytes.

The completed input at pipeline lines 389-394 mentions the gains ceiling but
not the 90% haircut. Replace the proof with current verbatim text and define
the completed boundary explicitly as after both limits.

### 2. The itemizer final has no §63(a) taxable-income proof

The final at `taxable_income_pipeline.yaml:345-382` executes both election
branches but labels and proves itself only under §63(b), the nonitemizer
definition. Its sole definition excerpt is “adjusted gross income, minus—”.
The itemizer branch at lines 325-333 is governed by §63(a)'s general
gross-income-minus-chapter-deductions definition.

The imported itemized module proves §63(d)-(e), not §63(a), and the target
contains no §63(a) atom. Sections 61 and 62 appear in module-level source
metadata but not in a proof atom establishing the AGI boundary. This misses
the binding §6.3 proof table and the task's explicit §63(a)/(b) dimension.

Add the exact current §63(a) definition and the §§61/62 bridge that justifies
the itemizer's equivalent AGI-based computation; source the final to both
§63(a) and §63(b).

### 3. The required §151 MAGI-addback diagnostic is absent

Binding §6.3 expressly requires a RuleSpec diagnostic showing that §§911,
931, or 933 exclusions increase senior-deduction MAGI and affect its phaseout.

The shared fixture at
`taxable_income_pipeline.test.yaml:18-35` makes every such fact false or zero.
An alias-expanded scan across all 27 cases found no true/nonzero exclusion
fact. The senior MAGI assertions at lines 464, 501, and 550 therefore prove
only `MAGI == AGI`.

Add at least one companion-only case with a real imported addback and assert
the resulting senior MAGI, phaseout amount, total deductions, and taxable
income.

### 4. Three imported relation schemas have no executable contract

The merged closure has four injectable relations:

- SALT `(TaxUnit, Person)`;
- §151 exemption `(TaxUnit, Person)`;
- §151 senior `(TaxUnit, Person)`; and
- §170(p) charity `(TaxUnit, Payment)`.

`tests/test_income_tax_pipeline_relation_schemas.py:17-24` pins only SALT.
The test itself explains at lines 3-8 that the engine ignores the declared
`arguments` vector, so a positive companion fixture cannot enforce its order.
The new witness at
`taxable_income_pipeline.test.yaml:818-857` is therefore insufficient.

I reversed only the §151 senior declaration from `(TaxUnit, Person)` to
`(Person, TaxUnit)` in a separate exact-head mutation archive. Both checks
still passed:

- static relation-schema contract: 1/1;
- taxable-income companion: 27/27, including the orientation witness.

Extend the executable schema registry to the two §151 relations and the
§170(p) relation, and demonstrate that each argument-order mutation fails.

### 5. Contradictory nonindividual facts pass the individual domain

The compose declares a 2026 individual boundary and checks
`taxpayer_is_individual` at `taxable_income_pipeline.yaml:206`. It does not
reject the independent
`estate_or_trust_common_trust_fund_or_partnership` fact.

The companion's `ti-entity-zeroes-standard` case inherits
`taxpayer_is_individual: true` from line 76, sets the nonindividual entity fact
to true at line 805, and nevertheless expects the verified domain to hold and
taxable income to equal $100,000 through the outputs at lines 745-750 and
alias at line 816.

That is an injectable contradiction outside the claimed boundary. The Atomic
§63(c)(6) module already proves the entity disqualifier; this individual
compose should fail closed when the nonindividual flag is true, rather than
compute a nonzero individual taxable-income result.

## Passing evidence

### Legal arithmetic and cases

- The first 14 companion cases exactly match the §6.3 case IDs, order, and
  expected values.
- Independent exact-decimal recomputation matched all 14. Representative
  checks:
  - `ti-choice-equal`: `100,000 - 16,100 = 83,900`; the resolved standard
    election controls rather than a tax-minimizing heuristic.
  - `ti-nonitemizer-all-components`: deductions `42,650`, taxable income
    `32,350`.
  - `ti-itemizer-all-components`: deductions `59,000`, taxable income
    `16,000`.
  - `ti-floor-zero`: `max(0, 10,000 - 16,100) = 0`.
  - `ti-senior-single-plus-one`: senior deduction `5,999.94`, total
    deductions `24,149.94`, taxable income `50,851.06`.
  - `ti-senior-joint-threshold`: deductions `47,500`, taxable income
    `102,500`.
- The §63(e) resolved election directly selects the branch and is
  cross-checked against the imported §170(p) fact. The mismatch diagnostic
  fails closed.
- The Atomic §63(c)(6) judgment is imported and consumed. MFS-with-itemizing
  spouse, nonresident alien, qualifying §443 short return, and entity flags
  each zero the standard component, subject to blocking finding 5.
- The local deduction intermediate and final are guarded; every added money
  component has a nonnegative condition. Invalid status, nonindividual,
  false-attestation, imported-domain failure, election mismatch, negative
  wagering, and temporal-window diagnostics return zero/not-holds.

### Imports and hashes

The full closure contains 25 modules and 227 unique rule declarations.

- All 54 declared imports resolve.
- All 119 proof imports resolve; all 69 nonlocal hashes match current bytes.
- Chunk 1 hashes are current at merged main:
  - SALT `81d049791e96d949b63b0b7599f88b4767ab4c68d5e05389d49ead70afb063b8`;
  - itemized
    `da533e2f7e0cfd79c11e35c502860c7c5b09b7b197ab78e6266ecbced9bde56a`.
- Rule names and relation predicates have no collisions.
- The closure contains the Rev. Proc. standard-deduction module and does not
  contain `us/statutes/26/63/c.yaml`; there is exactly one
  `standard_deduction` definition.

### Executable and mechanical gates

- Pinned companion: 1 file, 27 cases, 1 compiled program, zero failures.
- Pinned `axiom-encode` validation against the required corpus:
  `ci_pass=true`, `all_passed=true`, zero errors.
- Structural proof validation: passed, 33 atoms, zero issues, subject to
  blocking finding 1's independent byte audit.
- Focused layout/index/manifest/relation tests: 19 passed, with one
  report-only warning for 19 pre-existing unmanifested modules. An independent
  full repository run passed 74 tests with the same warning.
- Reverse-index regeneration is byte-current: 4,249 provisions, 5,120 edges,
  4,491 modules.
- Pending ledger is sorted and unique with `ceiling == count == 2,151`; it is
  the exact field-preserving base union, loses zero records, and adds exactly
  the three taxable-income entries.
- The composition manifest attests exactly the compose and companion. Both
  hashes match current bytes, the content commit, and the pre-signature
  ancestor. The content commit is an ancestor; the signature commit changes
  only the manifest; the exception is exactly `composition`; no candidate
  commit follows it.
- The diff is exactly the intended five files. `git diff --check` passes, with
  no workflow, toolchain, lockfile, state, or tracked session-ledger change.

## Sandbox and tooling disclosures

- Shell `gh pr view` and `git fetch` could not resolve GitHub because network
  access is disabled. The optional GitHub plugin was not installed. Exact live
  PR metadata and CI therefore could not be re-read; the frozen head is
  supported by the agreeing local branch and remote-tracking ref plus its
  same-day “update by push” reflog.
- GitNexus reported the exact-head graph worktree unindexed. Offline `npx`
  lacked a cached package; the installed analyzer parsed the tree but the
  sandbox denied its global registry write. Direct merged-closure analysis
  supplied the dependency evidence.
- `AXIOM_ENCODE_APPLY_SIGNING_KEY` was absent and the local secret store was
  locked. The signature envelope and all non-secret ancestor/hash/provenance
  checks pass, but the HMAC value was not cryptographically reverified here.
- No PR branch, remote, or GitHub write was made.

## Recommendation

Do not merge this head. Correct the §165 and §63 proofs, add the required
senior-MAGI addback case, extend relation-schema mutation coverage, and make
the individual domain reject contradictory nonindividual facts. Then
regenerate any affected mechanics, re-sign the applied files last, and rerun
the canonical 27-case-or-expanded companion, pinned validation, byte-verbatim
proof audit, mutation tests, closure audit, and manifest gates.
