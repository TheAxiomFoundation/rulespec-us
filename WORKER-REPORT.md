# Atomic PR A worker report

## Result

- Status: complete
- Branch: `fed-parity/atomicA-57-58-59-55`
- Base: `origin/main` at `ae64af2740340a40d04ed3c652254f53e62fab61`
- Head: `84f8226cfcc10628c63977b78b2e68d64925a5d4`
- Tracked delta: 13 intended files
- Provenance: ordinary atomic-law lane; no signing, push, PR, or GitHub write
- Manifests: unchanged. In particular,
  `.axiom/encoding-manifests/statutes/26/55.json` is untouched, and no modern
  `us/` manifest was emitted. That remains for the main-lane signer.
- Progress ledger: committed and marked complete in `PROGRESS.md`
- This report: intentionally untracked

## Source and toolchain proof

- Corpus: `8af592162231e9de748ba6b98792b426ad4fe8b7`,
  detached and clean at
  `/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`.
- Encoder: `3869d66d009f52258be35901edbef370e65a399c`.
- Rules engine: `ffd8213271947b0189a9dd61a055c1e0e78908a0`.
  The exact archived source was built at
  `/private/tmp/atomicA-engine-usD0xb`; the release binary SHA-256 is
  `674ca6e70afdccb59c3d6847933bc24b4590105e49db54790f2dcd0bdbbe32d7`.
- Every declared corpus path in §§55/57/58/59 resolves exactly once at the
  pinned corpus. For the new proof atoms, this includes:
  - §57: `/57/a`, `/57/a/5/A`, `/57/a/5/C`
  - §58: `/58/a`, `/58/b`, `/58/c/1`, `/58/c/2`
  - §59: `/59`, `/59/a/1`, `/59/a/2`, `/59/e`, `/59/g`, `/59/h`,
    `/59/j`, plus `/55/d/4` for post-2017 §59(j) inapplicability

The corpus stop condition therefore cleared before encoding.

## Delivered modules

### §57

`us/statutes/26/57.yaml` exposes exactly:

- `no_other_section_57_preference`
- `section_57_a_5_specified_private_activity_bond_interest`

The completed §57(a)(5) amount is guarded, and the bounded no-other judgment
requires explicit zero attestations for the other operative 2026 preferences.

### §58

`us/statutes/26/58.yaml` exposes exactly:

- `section_58_completed_loss_domain_is_satisfied`
- `section_58_a_tax_shelter_farm_loss_adjustment_after_insolvency`
- `section_58_b_passive_activity_loss_adjustment_after_insolvency`

Both adjustments are guarded, signed, completed after-insolvency aliases.
The module does not infer an allocation or ordering for the single
§58(c)(1) insolvency amount. Adopted fixtures prove both signed adjustments
are zero.

### §59

`us/statutes/26/59.yaml` accepts raw
`completed_alternative_minimum_tax_foreign_tax_credit` only behind the
completed-special-rule domain and exposes exactly:

- `section_59_completed_special_rule_domain_is_satisfied`
- `alternative_minimum_tax_foreign_tax_credit`
- `section_59_e_qualified_expenditure_adjustment`
- `section_59_g_tax_benefit_rule_adjustment`
- `section_59_h_limitation_coordination_adjustment`
- `section_59_j_kiddie_exemption_limit_applies`

The three adjustments are signed and are all proven zero in the adopted
fixture. The §59(j) judgment is proven `not_holds` after 2017 from
§55(d)(4).

## §55 correction walkthrough

1. **Verified bounded domain.** The private
   `section_55_verified_domain_is_satisfied` judgment requires the §56 and
   §57 no-other judgments, the completed §§58–59 domains, post-2017
   `not section_59_j_kiddie_exemption_limit_applies`, zero §911(a)
   exclusion, and zero Form 4972 amount. This is grounded in
   §§55(b)(1), 56(b)(1), 55(d)(4), 911(f), and 26(b). Nonnegative completed
   ordinary amounts are also guarded; the completed §58 and
   §59(e)/(g)/(h) adjustments remain signed.

2. **Itemized-deduction reversal.** For an itemizer,
   `amt_excluded_deductions` is
   `salt_deduction + misc_deduction - section_68_reduction`; for a
   nonitemizer it is the standard deduction. Section 56(b)(1)(E) says §68
   does not apply in AMTI, while §68(a) defines a reduction already reflected
   in taxable income, so subtracting that reduction from the addback reverses
   it exactly once.

3. **AMTI additions.** Under §§55(b)(1)(B), 56–59, and 151(d)(5),
   `amt_income` now adds:
   - the §151 exemption deduction and senior deduction;
   - the guarded §57(a)(5) preference;
   - both signed completed §58 adjustments; and
   - the signed §59(e), §59(g), and §59(h) adjustments.

4. **One §26(b) regular-tax total and separate FTC sides.** The regular side
   now uses only
   `section_26_b_regular_tax_liability_before_credits`, then subtracts
   `ordinary_foreign_tax_credit`, as §55(c)(1) defines regular tax by reference
   to §26(b) reduced by the §27 credit. The tentative-minimum-tax side alone
   subtracts `alternative_minimum_tax_foreign_tax_credit`, as required by
   §§55(b)(1)(A) and 59(a):

   ```text
   tentative_minimum_tax_after_amtftc =
       max(0, amt_tax_before_foreign_tax_credit - AMTFTC)
   regular_tax_after_ordinary_ftc =
       max(0, section_26_b_regular_tax_liability_before_credits - ordinary_FTC)
   alternative_minimum_tax =
       max(0, tentative_minimum_tax_after_amtftc
              - regular_tax_after_ordinary_ftc)
   ```

5. **Post-2017 kiddie branch removed.** Section 55(d)(4) states that §59(j)
   does not apply. `amt_exemption` therefore passes through the ordinary
   exemption calculation without the former filer-earnings/kiddie cap branch.
   The legacy helper name `amt_exemption_before_kiddie_tax_limit` is retained
   for surface compatibility, but no kiddie limit is applied.

6. **Form 4972 is no longer subtracted.** The bounded module requires the Form
   4972 scalar to be zero and never subtracts it from the §26(b) total. Broader
   nonzero support remains deferred until §402/Form 4972 provenance and the
   special Form 6251 coordination are encoded.

7. **§911(f) is fail closed.** A nonzero §911(a) exclusion makes the bounded
   domain fail because §911(f) requires a separate special AMT computation.

Every monetary §55 output returns zero outside the verified domain. The
companion includes targeted senior-deduction, §68-reversal, combined
§§57–59, unequal-FTC, Part III, MFS, and each fail-closed-domain case.

## Gate table

| Module | Companion | Pinned deterministic validate | Proof / money atoms | Mutation evidence |
|---|---:|---|---:|---|
| `55.yaml` | 14/14 | pass | 81 atoms; 0 missing | Negating the §56 domain condition produced 48 failures; restored to 14/14 |
| `57.yaml` | 8/8 | pass | 4 atoms; 0 missing | Negating the §57(a)(7) zero attestation produced 5 failures; restored |
| `58.yaml` | 6/6 | pass | 13 atoms; 0 missing | Negating the §58(c)(2) completion attestation produced 7 failures; restored |
| `59.yaml` | 8/8 | pass | 16 atoms; 0 missing | Independent completion-domain and §59(j) truth flips killed their named expectations; both restored |

Combined exact-pinned companion result: 4 files, 36 cases passed.

Additional gates:

- Strict explicit-key YAML parsing passed for all four modules and companions.
- §§57–59 public output sets are exactly 2/3/6.
- Focused `validate --skip-reviewers` returned `CI: ✓` for all four modules.
- Proof validation checked 114 atoms total; the money-atom gate reported zero
  missing under its zero allowance.
- Direct §55 compile passed with 84 rules.
- The FY2026 FIIT program scope composed and compiled against the exact engine:
  artifact format 2, 150 derived outputs, engine 0.1.0, fast-path compatible.
- Repository suites passed: reverse index, layout, and income-tax relation
  schemas, 16 tests total.
- Reverse index is current: 4,272 provisions, 5,132 edges, 4,493 modules.
- `git diff --check` passed.
- All mutations were restored and the tracked worktree was clean before this
  untracked report was created.

No module in the branch adds a local `data_relation`, so no new runtime-inert
`arguments` vector or injectable derived-relation surface exists. The §55
companion supplies explicit empty/imported §151 relation vectors, and the
existing static relation-schema suite passes. No multi-relation divergence
probe is introduced, so there is no new `related_N` aliasing surface.

## Import cascade

Repository-wide search found no external RuleSpec module importing §§55,
57, 58, or 59. The only broader consumer is the unpinned
`programs/us/fiit/fy-2026.yaml` scope, which composes and compiles successfully.
The new §55 imports are pinned to exact bytes:

- §57: `5e92f5faae26d4974f073fedbdeb82853744670762c98da21632028ec7115844`
- §58: `b93ffa4fce240ee5d8511502d07e8cee8fc14cd5764683efc820e9e42157ea8e`
- §59: `97fe6fb67b7d97a95cec9ce73b7eee124e152fb7c734e3b1bb2d3afcf606d129`
- §151: `28fb0e7c50d48ad764ff1ddee8b654a18006fc3dde026034b4dfb6efb90a0fb2`
- Rev. Proc. AMT fragment:
  `50808ccfc0d1acba5cf639fc31620169d76d8f44e82905d73644987e8c3380b9`
- §911(a):
  `b128d251a0f74fc46a27e516e864e53c8d25442f5b419c7bb3bb4b607542d725`

Because there is no external module importer, no additional companion/hash
cascade file was required.

## Pending oracle coverage

The ledger is an exact sorted union:

- previous count/ceiling: 2,148
- current count/ceiling: 2,159
- added: exactly 11
- removed: 0
- duplicates: 0
- all new entries: `source: manual`, `since: '2026-07-29'`

All 11 new public outputs remain pending classification.

### PolicyEngine-US 1.767.3 mapping audit

Evidence was taken from the exact cached 1.767.3 wheel:

- wheel SHA-256:
  `777be3f3a66cbd266959791b007571a8fce94b1d0c2d13f40f8e991ca106fa6f`
- unpacked source:
  `/Users/maxghenis/.cache/uv/archive-v0/-QudTS5FEzSKZ0Anf7ddx`
- runtime registry: 5,785 variables

| New RuleSpec output | PE-US 1.767.3 candidate | Proposed classification / finding |
|---|---|---|
| `section_57_a_5_specified_private_activity_bond_interest` | `tax_exempt_interest_income`; generic `amt_non_agi_income` | Non-directly-comparable. Neither isolates §57(a)(5), and neither is consumed by PE AMTI. |
| `no_other_section_57_preference` | none | Non-directly-comparable; PE has no §57 completion inventory judgment. |
| `section_58_completed_loss_domain_is_satisfied` | none | Non-directly-comparable; PE has no completed §58 domain. |
| `section_58_a_tax_shelter_farm_loss_adjustment_after_insolvency` | `farm_income`; generic `amt_non_agi_income` | Non-directly-comparable; `farm_income` is not the §58 adjustment and PE has no tax-shelter/insolvency surface. |
| `section_58_b_passive_activity_loss_adjustment_after_insolvency` | generic `amt_non_agi_income` | Non-directly-comparable; PE has no passive-loss/insolvency output. |
| `section_59_completed_special_rule_domain_is_satisfied` | none | Non-directly-comparable; PE has no §59 completion judgment. |
| `alternative_minimum_tax_foreign_tax_credit` | `amt_foreign_tax_credit` | Useful suite bridge/diagnostic candidate, not a direct mapping: PE's variable is a Person-level pure input and is not consumed by PE's AMT formula; RuleSpec is guarded at TaxUnit. |
| `section_59_e_qualified_expenditure_adjustment` | generic `amt_non_agi_income` | Non-directly-comparable; no §59(e) election/writeoff variable exists. |
| `section_59_g_tax_benefit_rule_adjustment` | generic `amt_non_agi_income` | Non-directly-comparable; no tax-benefit-rule adjustment exists. |
| `section_59_h_limitation_coordination_adjustment` | generic `amt_non_agi_income` | Non-directly-comparable; no §§704(d)/465/1366(d) coordination output exists. |
| `section_59_j_kiddie_exemption_limit_applies` | `amt_kiddie_tax_applies` | Related divergence diagnostic, not equivalent. PE can apply its child cap after 2017; RuleSpec asks whether §59(j) legally applies and returns `not_holds`. |

Source inspection confirmed that PE's `amt_income` omits the §§57–59 additions,
`amt_foreign_tax_credit` is an otherwise unused pure input, PE's AMT comparison
instead uses `foreign_tax_credit_potential`, and PE retains the post-2017
kiddie branch.

## Exact containment

The tracked diff against `origin/main` contains only:

1. `.axiom/index/provisions_to_rules.json`
2. `.axiom/pending-validation-fingerprints.json`
3. `PROGRESS.md`
4. `known-validation-gaps.yaml`
5. `oracle-coverage-pending.yaml`
6. `us/statutes/26/55.test.yaml`
7. `us/statutes/26/55.yaml`
8. `us/statutes/26/57.test.yaml`
9. `us/statutes/26/57.yaml`
10. `us/statutes/26/58.test.yaml`
11. `us/statutes/26/58.yaml`
12. `us/statutes/26/59.test.yaml`
13. `us/statutes/26/59.yaml`

The §55 pending waiver and matching fingerprint row were removed after the
corrected module validated cleanly. No other waiver evidence changed.

## Commits

All commits report signature grade `N` (unsigned):

- `1170564be` — initialize progress ledger
- `a523bdd47` — record source and impact audit
- `6207bc851` — encode bounded §59 rules
- `d85394407` — encode bounded §57 preferences
- `8ddb71c3c` — initial bounded §58 encoding
- `f2acdaf47` — correct §58 to preserve signed completed adjustments
- `10a1e714d` — correct §55 AMT integration
- `f4e5c4b5e` — retire stale §55 validation waiver
- `13b003f37` — declare §§57–59 pending oracle debt
- `b00d87018` — regenerate reverse index
- `84f8226cf` — close progress ledger

## Tooling and sandbox disclosures

- The required deterministic validation path is green. An exploratory
  validation run without `--skip-reviewers` could not run the optional
  reviewer agents because the local reviewer CLI was not logged in; all four
  deterministic CI validations still reported `CI: ✓`.
- The exact July 9 encoder/oracles pin cannot perform a clean July 29
  whole-repository pending-ratchet census: it reports 437 unrelated,
  pre-existing undeclared outputs. It nevertheless applied all 2,159 current
  declarations with zero stale entries. The committed ledger was therefore
  verified by an explicit base-versus-head set proof: exact `+11/-0`, sorted,
  unique, and `ceiling == count`. An overbroad generated sync was discarded
  before any commit.
- One read-only process-inspection attempt (`ps`) was blocked by the managed
  sandbox with `operation not permitted`. It did not affect repository files
  or any required gate.
- The system-level Python/pytest entry points were unusable, so every Python
  gate used the working pinned project virtual environment explicitly.
- No network-dependent action, signing operation, push, or GitHub write was
  attempted.
