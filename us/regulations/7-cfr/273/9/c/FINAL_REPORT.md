# ENC-273-9C final report

## Status and pull request

- Local branch: `closure/enc-273-9c`
- Required PR title: `Encode 7 CFR 273.9(c) income exclusions`
- PR URL: not created. `git push -u origin closure/enc-273-9c` failed
  because the sandbox could not resolve `github.com`. The connected GitHub
  branch-creation call was canceled before creating a remote branch.
- The committed worktree is clean. It was not merged.
- The requested external result path,
  `/Users/maxghenis/TheAxiomFoundation/_closure-sprint/out/enc-273-9c.result.md`,
  is outside the writable roots. The sandbox rejected the write, so this
  committed file preserves the complete report.

## Delivered files

- `us/regulations/7-cfr/273/9/c.yaml`
- `us/regulations/7-cfr/273/9/c.test.yaml`
- `us/regulations/7-cfr/273/9/c/PROGRESS.md`
- `us/regulations/7-cfr/273/9/c/FINAL_REPORT.md`
- Minimal parent change in `us/regulations/7-cfr/273/9.yaml`
- Regenerated `.axiom/index/provisions_to_rules.json`

The child module contains 104 rules: 4 relations, 4 parameters, 95 derived
rules, and 1 non-executable source relation. It compiles to 103 executable
rules. Every paragraph-(c) exclusion and every nested enumerated branch has its
own paragraph-specific rule and citation. Ordinary payment exclusions compose
by maximum per payment so overlapping legal routes are counted once.
Education, charitable donations, self-employment costs, and outgoing child
support use separate relations because they require shared pools, history, or
non-income accounting rows. The final
`household_income_exclusion_composition` combines those layers.

## Deferrals and paragraph-(b) coordination

- Satisfied the parent deferral for
  `us:regulations/7-cfr/273/9/c#household_income_exclusion_composition`.
  The parent now delegates non-executably to the child.
- Left the separately owned paragraph-(b) inclusion deferral unchanged.
  Paragraph (c) consumes the amount staged by paragraph (b)'s pre-exclusion
  composition and does not encode any inclusion rule.
- Left one narrow child deferral:
  `us:regulations/7-cfr/273/9/c/9#self_employment_production_cost_determination`.
  Section 273.9(c)(9) supplies the exclusion boundary, but the actual production
  cost determination belongs to the unresolved § 273.11(a) self-employment
  calculation.
- Did not edit the frozen `programs/` tree, toolchain pins, CI, CODEOWNERS, or
  `oracle-coverage-pending.yaml`.

## State options

Formal State options are:

- (c)(3)(v): exclude State educational assistance excluded under the State's
  title XIX Medicaid rules.
- (c)(17): elect the outgoing-child-support exclusion instead of the
  § 273.9(d)(5) deduction, with the election in the State plan.
- (c)(18): exclude complementary-assistance income excluded under the State's
  § 1931 Medicaid rules, with the option in the State plan.
- (c)(19): align specified TANF/Medicaid income exclusions, with State-plan and
  financial-circumstance conditions and nine prohibited income categories.

Paragraph (c)(8)'s TANF diversion treatment is discretionary State treatment,
but not one of those formal State-plan options. The school-clothing allowance
in (c)(5)(i)(E) is mandatory when its conditions hold; it is not a State
option.

## 7 U.S.C. 2014(d) crosswalk

- (d)(1)-(5) map to (c)(1)-(5). In particular, (d)(5)'s reimbursements and
  school-clothing allowance resolve in (c)(5).
- (d)(6) maps to (c)(6) and the State election in (c)(17).
- (d)(7) maps to (c)(7).
- (d)(8) maps to (c)(8) and (c)(12).
- (d)(9) maps to (c)(9), subject to the § 273.11(a) deferral above.
- (d)(10) maps to (c)(10).
- (d)(11) maps to (c)(11).
- (d)(12) has no current paragraph-(c) counterpart.
- (d)(13) and (d)(14) map to (c)(13) and (c)(14).
- (d)(15) maps to (c)(16).
- (d)(16) maps to the State option in (c)(3)(v).
- (d)(17) maps to the State complementary-assistance option in (c)(18).
- (d)(18) maps to the State-alignment option in (c)(19).
- (d)(19) maps to (c)(20).
- Paragraph (c)(15) is an additional foster-care-boarder exclusion.

The statutory aggregate remains partial where its own resource composition,
§ 273.11 determination, open-ended Federal-statute universe, missing (d)(12)
counterpart, or Secretary-designated combat-pay alternative is not supplied by
paragraph (c). No statute or oracle-pending row was edited.

## Judgment calls

- (c)(1): unclear PA/GA vendor-payment cases require the stated FNS regional
  office determination. The educational vendor route is a neutral direct-
  treatment helper, not a standalone (c)(1) exclusion.
- (c)(2): the $30 quarterly test is all-or-nothing, not a first-$30 cap.
- (c)(3): the printed “20 CFR 1087uu” cross-reference was treated as the
  standalone 20 U.S.C. 1087uu/BIA route. Ordinary aid still requires qualifying
  enrollment, use, and timing. Shared expenses reduce unearned aid before
  earned aid, and the same dependent-care cost is coordinated with (c)(5).
- (c)(4): repayment beginning by day 60 qualifies; day 61 does not.
- (c)(5): migrant travel is independent of the above-wages condition.
  Flat/multiple-purpose allowances are supported but capped at actual
  qualifying expense. School clothing is excluded only when separately
  identified, intended for school clothing, not federally funded, and not
  offset by a TANF reduction in that month.
- (c)(6): beneficiary-care payments use the nested minimum and proration in
  the text.
- (c)(7): the child must be under 18; GED, home-school, and break routes retain
  their stated enrollment conditions, and multiple children's shares pool.
- (c)(8) and (c)(12): a qualifying charitable donation is kept in the (c)(12)
  quarterly pool and cannot be rerouted through (c)(8) or (c)(2) after the cap.
  The $300 limit applies across the Federal fiscal quarter. This routing also
  follows the USDA final-rule explanation:
  https://www.govinfo.gov/content/pkg/FR-1989-05-09/pdf/FR-1989-05-09.pdf
- (c)(10): all ten named Federal-statute routes are explicit; the VISTA legacy
  route requires the pre-1979 contract to remain in effect.
- (c)(11): installment treatment requires both as-needed receipt and treatment
  under Federal or State law.
- (c)(15): the stale § 273.1(c) citation was aligned to the current foster-
  boarder provision at § 273.1(b)(4).
- (c)(16): PASS income needs to be necessary for an approved PASS; no extra
  spent-or-deposited condition was invented.
- (c)(17): deduction treatment displaces exclusion only when the State has
  made the State-plan election.
- (c)(18)-(19): both exclusions require their respective State-plan choices;
  (c)(19) also enforces all nine prohibited categories.
- (c)(20): only the qualifying excess combat pay is excluded, capped at combat
  pay actually received.

## Validation

All commands used the pinned encoder at
`3869d66d009f52258be35901edbef370e65a399c` and engine at
`ffd8213271947b0189a9dd61a055c1e0e78908a0`.

- `axiom_encode.cli validate us/regulations/7-cfr/273/9.yaml
  us/regulations/7-cfr/273/9/c.yaml --skip-reviewers` — pass for both.
- `axiom_encode.cli proof-validate us/regulations/7-cfr/273/9.yaml
  us/regulations/7-cfr/273/9/c.yaml` — pass; 130 child proof atoms.
- `axiom_encode.cli test --root "$PWD" --axiom-rules-engine-path <pinned>
  us/regulations/7-cfr/273/9.test.yaml
  us/regulations/7-cfr/273/9/c.test.yaml` — pass; 2 files, 73 cases.
- `axiom_encode.cli compile .../273/9/c.yaml --as-of 2026-07-09
  --axiom-rules-engine-path <pinned>` — pass; 103 executable rules.
- `axiom_encode.cli proof-validate --require-money-atoms
  --money-atoms-only .../273/9.yaml .../273/9/c.yaml` — pass; zero missing
  atoms across two monetary obligations.
- `tests/generate_reverse_index.py --check` — pass; 4,232 provisions, 5,069
  edges, and 4,484 modules.
- Paragraph-(c) oracle slice — 99 `known_not_comparable`, zero unmapped, zero
  pending-classification.
- Frozen-program artifact check — pass; 33/33 programs, including Colorado
  SNAP with 789 derived outputs.
- `git diff --check 6b0773d3f...HEAD` and protected-path diff — pass.
- `/opt/homebrew/bin/pytest -q tests` — 64 passed, 1 failed, 1 warning. The sole
  failure is the edited parent's stale applied-file manifest; the warning is
  the existing set of 18 unmanifested modules.
- `axiom_encode.cli guard-generated --repo . --base-ref 6b0773d3f
  --head-ref HEAD` — expected failure naming exactly `273/9.yaml`,
  `273/9/c.yaml`, and `273/9/c.test.yaml`. A signing dry run would create two
  manifests covering the three files. `AXIOM_ENCODE_APPLY_SIGNING_KEY` is
  unset, so no provenance was forged.
- Global SNAP oracle coverage remains red on repository-wide baseline debt:
  9,465 executable outputs, 87 comparable, 9,311 known-not-comparable, 67
  unmapped, and 2,293 stale pending declarations. The paragraph-(c) slice
  itself is clean.
