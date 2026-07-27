# SNAP earned income deduction assessment

Date: 2026-07-27

## Decision

**Do not certify or ship this node tonight.**

The arithmetic is shallow, but its base is not. Both non-parameter inputs to
the existing RuleSpec base formula are derived legal quantities:
`snap_countable_earned_income` is an income inclusion, exclusion,
self-employment, and member-attribution composition, and
`work_supplementation_earned_income` requires a qualifying-program and
public-assistance-attribution determination. Neither quantity is defined by a
complete provision-rooted RuleSpec subtree.

There are three independent stopping defects:

1. The earned-income base is unencoded. The only RuleSpec definition of
   `snap_countable_earned_income` is in the authored
   `state-plan-composition` module.
2. The existing output omits 7 USC 2014(e)(2)(C), which disallows the
   deduction in specified overissuance calculations. The companion
   `e/2/B.yaml` already declares this output deferred for that reason.
3. PolicyEngine has no work-supplementation adjustment and no overissuance
   branch, so the required interaction cannot be tested against its real logic
   without externally precomputing the disputed legal quantity.

Accordingly, no one-output program, registered case grid, or executable golden
case was added. A mechanically compilable program that accepted
`snap_countable_earned_income` as if it were observed would conceal the exact
closure failure this assessment was asked to detect.

## Evidence and pins

- RuleSpec branch fork:
  `f9fb41b9933111ce108cc04d5a603cfdb7f1b940`.
- `origin/main` observed during the final audit:
  `c2bcf2bc06246973fb8429811e2a5d00fc2bdc78`.
- PolicyEngine US: `715373c90b0014561977a1b161f2f4c75bb45c33`.
- RuleSpec-pinned axiom-corpus:
  `bf97b17baebfdf12601f7c23697524bf5adcdaed`.
- Authoritative CFR text supplied for this sprint has expression date
  2026-07-09.

The corpus scan parsed every `.items[]` record in every inventory JSON at the
pinned corpus commit before filtering by citation path:

- 689 inventory files;
- 142,879 raw inventory records;
- 124,463 distinct citation paths;
- 66 raw matches for the initial 33-path direct formula-and-exception filter,
  with each distinct path present in exactly two inventory records.

This was a delimiter-safe citation-path search
(`path == root` or `path` beginning with `root + "/"`), not a filename or
ingest-version search. Final dependency review expanded the declared,
corpus-resolving lower-bound universe to 81 distinct citation paths, counted
below. That number deliberately does not pretend to be full transitive
closure: required cross-references absent from the corpus and open-ended
Federal and State policy branches cannot truthfully be counted as resolved
inventory paths.

## True dependency tree

Legend: **[O]** observed source fact, **[D]** derived quantity or legal
classification, **[P]** provision-set parameter.

```text
[D] snap_earned_income_deduction
├── [D, MISSING] §2014(e)(2)(C) applicability
│   ├── [O] benefit/claim calculation context and issuance history
│   ├── [O] income-change and household-report timestamps
│   ├── [D] whether the income had to be reported, and by when
│   ├── [D] whether untimely nonreporting caused the overissuance
│   └── [D] claim type, including the agency-error exception
├── [P] snap_earned_income_deduction_rate = 0.20
└── [D] snap_earned_income_subject_to_deduction
    ├── [D] snap_countable_earned_income — NOT OBSERVED
    │   ├── [D] gross earned income under 7 CFR 273.9(b)(1)
    │   │   ├── [O] employee wages and salaries
    │   │   ├── [D] countable self-employment income
    │   │   │   ├── [O] enterprise receipts and capital-sale amounts
    │   │   │   ├── [O] rental/roomer/boarder receipts and management hours
    │   │   │   ├── [O] claimed production costs
    │   │   │   ├── [D] allowable production-cost classification
    │   │   │   ├── [D] State actual-cost or standard-percentage method
    │   │   │   └── [D] farm-loss offset, averaging, and attribution
    │   │   ├── [O] training, volunteer, OJT, and work-study payments
    │   │   └── [D] program, reimbursement, age, school, and funding
    │   │       classifications controlling those payments
    │   ├── [D] exclusions under 7 USC 2014(d) / 7 CFR 273.9(c)
    │   │   ├── [O] source amounts and source-record circumstances
    │   │   └── [D] each statutory/regulatory exclusion classification
    │   └── [D] household/member income-counted share
    │   │   ├── [O] residence, relationship, food-purchase/preparation,
    │   │   │   age, disability, school, immigration, work, and waiver facts
    │   │   └── [D] household membership, student eligibility,
    │   │       immigration eligibility, work-rule/ABAWD status, and proration
    ├── [D, MISSING] child-support earnings addback required specifically
    │   for this deduction by 7 CFR 273.9(d)(2)
    │   ├── [O] earnings and legally obligated child-support payment records
    │   └── [D] amount excluded under 7 CFR 273.9(c)(17)
    └── [D] work_supplementation_earned_income — NOT OBSERVED
        ├── [O] wage, payment, and public-assistance funding-source records
        ├── [O] employer, prior-employment, participant, and program facts
        ├── [D] amount attributable to public assistance
        └── [D] qualifying §2025(b) program, State election,
            Secretary/FNS approval, household participation, and resulting
            subsidized wage portion
```

Observed facts can terminate individual leaves; they cannot replace the
derived nodes above. In particular, a field named “countable earned income” is
the result of applying law to facts, not itself an observed fact.

## What the existing RuleSpec graph actually does

`us/statutes/7/2014/e/2.yaml` defines:

```text
snap_earned_income_subject_to_deduction
  = max(0, snap_countable_earned_income
           - work_supplementation_earned_income)

snap_earned_income_deduction
  = snap_earned_income_subject_to_deduction
    * snap_earned_income_deduction_rate
```

- The 20 percent rate is provision-rooted in 7 USC 2014(e)(2)(B) and encoded
  in `us/statutes/7/2014/e/2/B.yaml`.
- `snap_countable_earned_income` and
  `work_supplementation_earned_income` are implicit inputs in this module.
- The only repository definition of `snap_countable_earned_income` is
  `max(0, snap_gross_monthly_earned_income)` in
  `us/policies/usda/snap/state-plan-composition.yaml`, whose module kind is
  explicitly `composition`. No provision module defines the gross input.
- `us/regulations/7-cfr/273/9.yaml` expressly defers both paragraph (b)'s
  income-inclusion composition and paragraph (c)'s income-exclusion
  composition.
- No RuleSpec module encodes 7 CFR 273.11(a)-(b)'s self-employment treatment;
  only paragraph (c) has a module.
- No RuleSpec definition of `work_supplementation_earned_income` was found.
- The unconditional top-level output omits §2014(e)(2)(C), while
  `e/2/B.yaml` expressly defers the deduction output because that exception is
  unavailable.
- The top-level output also omits the child-support earnings addback.

The result is syntactically executable only after callers supply already
derived legal answers.

## Regulatory implementation

The authoritative body for `us/regulation/7/273/9` contains
7 CFR 273.9(d)(2). It does not change the 20 percent rate, but it adds material
implementation detail:

1. the base is gross earned income as defined by paragraph (b)(1);
2. earnings excluded under paragraph (c) are removed from the base; and
3. earnings used to pay child support and excluded under paragraph (c)(17)
   must nevertheless be counted when computing the earned-income deduction.

Item 3 is absent from the existing statute formula. Paragraphs (b), (c), and
(d)(2) all resolve inside the section-level corpus record
`us/regulation/7/273/9`; the corpus does not expose separate paragraph records.

7 CFR 273.10(e)(1)(i)(B) supplies the applied net-income calculation.
Paragraph (e)(1)(ii) makes the handling of cents depend on a State election,
including an option to use the rounding procedures used for TANF. The existing
`273/10.yaml` has a separate
`snap_earned_income_deduction_for_net_income` rule that unconditionally uses
`floor(...)`. It accepts resolved gross monthly earned income and does not
encode the State rounding election. This is downstream context for applying
the deduction in the net-income calculation, not a direct dependency of the
isolated, unrounded §2014(e)(2) output assessed here; it nonetheless means the
separate applied helper is not a universal closure substitute.

7 CFR 273.18(c)(1)(ii)(B) directly implements the overissuance exception: it
withholds the deduction from the untimely unreported portion when that failure
is the claim basis, but applies it to an agency-error claim. Section 273.12
supplies the reporting duties and deadlines. Neither section has a RuleSpec
module.

7 CFR 273.7(l)(1)(i)(G) confirms that the deduction does not apply to the
subsidized wage portion in a work-supplementation program. It resolves in the
corpus but is not encoded by the existing section 273.7 module.

## PolicyEngine comparison

PolicyEngine's `snap_earned_income_deduction` is real logic, not a parameter
passthrough:

```text
snap_earned_income_deduction = snap_earned_income * 0.20
```

But `snap_earned_income` is itself derived. It combines:

- person employment income after child-earner and federal-work-study
  exclusions;
- a derived member income-counted share based on student, immigration,
  work-rule, ABAWD, TANF, and household-composition rules; and
- net self-employment income after a State-dependent actual-cost or
  percentage expense method.

The reachable graph contains at least 75 PolicyEngine variables before
expanding the 51 State TANF programs. Its observed leaves include employment
income, self-employment receipts and expenses, age, disability, enrollment,
work-study and work-hour facts, immigration status, State, household
relationships, and work-program/exemption facts.

PolicyEngine contains no work-supplementation variable or adjustment and no
overissuance branch. Its own focused deduction test inputs already-derived
`snap_earned_income`, so that test proves only the 20 percent multiplication.
Supplying an externally adjusted PolicyEngine base would bypass, rather than
test, the disputed statutory interaction.

For example, with $1,000 of employment income of which $250 is the subsidized
public-assistance portion, the current RuleSpec formula returns $150.
PolicyEngine returns $200 because it sees all $1,000 as `snap_earned_income`.

## Citation-path closure

The declared corpus-resolving lower-bound roots are:

- `us/statute/7/2012/m`;
- `us/statute/7/2014/b`;
- `us/statute/7/2014/e/2`;
- `us/statute/7/2014/d`;
- `us/statute/7/2015/d`, `/e`, `/f`, and `/o`;
- `us/statute/7/2025/b`;
- `us/statute/8/1612`; and
- `us/regulation/7/273/1`, `/4`, `/5`, `/7`, `/9`, `/10`, `/11`, `/12`,
  `/18`, and `/24`.

| Root | Distinct paths | Encoded | Excludable | Pending |
|---|---:|---:|---:|---:|
| 7 USC 2012(m), root plus (1)-(5) | 6 | 1 | 0 | 5 |
| 7 USC 2014(b) | 1 | 0 | 1 | 0 |
| 7 USC 2014(e)(2) | 1 | 0 | 0 | 1 |
| 7 USC 2014(d), root plus (1)-(19) | 20 | 1 | 0 | 19 |
| 7 USC 2015(d), (e), (f), and (o) subtrees | 26 | 10 | 0 | 16 |
| 7 USC 2025(b), root plus (1)-(6) | 7 | 0 | 2 | 5 |
| 8 USC 1612 subtree | 10 | 1 | 0 | 9 |
| 7 CFR 273.1, .4, .5, .7, .9-.12, .18, and .24 | 10 | 0 | 0 | 10 |
| **Resolving lower-bound total** | **81** | **13** | **3** | **65** |

These are provision-content dispositions, not a claim that the encoded
provisions are connected into a closed deduction tree. The 13 encoded paths
are `us/statute/7/2012/m/4`, `us/statute/7/2014/d/7`,
`us/statute/7/2015/d/2`, the `us/statute/7/2015/e` root and its eight
paragraph paths, and `us/statute/8/1612/b/2/G`.
Paragraph 2014(d)(2) has partial RuleSpec rules but remains pending: the
current monthly `min(amount, $30)` formula does not close the statute's
quarterly condition. The other 7 USC 2015 paths do not close the full
membership and member-income attribution branch. The three excludable paths
are 7 USC 2014(b), which states an administrative standards authority rather
than a household computation despite PolicyEngine citing it for
`snap_unit_size`, and §2025(b)(5)-(6)'s program-transition plan and
worker-displacement safeguard.

All 81 paths in this declared lower bound resolve in the pinned corpus.
Resolution is sometimes coarser
than the legal citation:

- 7 USC 2014(e)(2)(B) and (C) resolve within
  `us/statute/7/2014/e/2`; there are no `/B` or `/C` inventory records.
- CFR paragraphs resolve within their section records; there are no inventory
  records such as `us/regulation/7/273/9/d/2` or
  `us/regulation/7/273/11/a`.

This 81-path count is still a conservative resolving lower bound, not full
transitive closure. Section 2014(d)(10)'s open-ended
other-Federal-law exclusions, immigration rules, State option authorities,
State TANF procedures, and State self-employment methods open additional
roots. Exact paths for 20 USC 1087uu and 34 CFR part 675, reached by the
work-study rules, do not resolve in the scanned federal inventories. Because
some required nodes do not resolve and other branches are open-ended, no
honest finite full-closure count can be reported from this corpus. That is
itself an end-to-end provision-rootedness failure.

## Program, grid, and golden-case disposition

- **Program:** not created. A no-`transformations` spec can mechanically expose
  the existing output, but only by presenting derived, unclosed inputs as its
  boundary. That is not an honest provision-rooted program.
- **Grid:** not created and no population-backed suite was run. PolicyEngine
  cannot express the required with/without-work-supplementation boundary, so a
  grid could test only zero and ordinary 20 percent arithmetic.
- **Oracle artifact location:** the committed case-grid convention lives in
  the separate `axiom-oracles` repository. Its case-grid marker is
  `population: case-grid`; its valid provenance value is
  `run_kind: manual`, not `run_kind: case-grid`. Adding a registered grid here
  would place it in the wrong repository and changing the provenance schema
  would violate the toolchain freeze.
- **Golden case:** no executable golden artifact was created because there is
  no certifiable program. The conditional worked example below records the
  arithmetic without claiming closure.

## Conditional worked example (not a certification golden)

Facts for one ordinary current-month calculation:

- adult employee wages: $1,000;
- no self-employment income;
- no §2014(d) / §273.9(c) exclusion other than the specified
  work-supplementation portion;
- no child-support earnings addback;
- qualifying work-supplementation wage portion attributable to public
  assistance: $250;
- the calculation is not an overissuance determination; and
- rate: 20 percent.

Statutory derivation:

1. Gross earned income under 7 CFR 273.9(b)(1)(i): **$1,000**.
2. Other applicable income exclusions: **$0**.
3. Remove the public-assistance-attributable work-supplementation portion under
   7 USC 2014(e)(2)(A)(ii): **$1,000 - $250 = $750**.
4. Child-support earnings addback under 7 CFR 273.9(d)(2): **$0**.
5. Section 2014(e)(2)(C) does not bar the deduction in this stated context.
6. Deduction under §2014(e)(2)(B): **$750 × 0.20 = $150**.

Expected conditional output: **$150**.

The case is hand-checkable but not executable end to end in the current
RuleSpec tree: the “qualifying work-supplementation portion,” the zero
exclusion conclusion, and the non-overissuance context are unresolved derived
quantities.

## Work product

- Added and maintained `PROGRESS.md`.
- Added this committed assessment.
- Validated and proof-validated both existing 7 USC 2014(e)(2) modules with
  `axiom-encode` at the repository-pinned commit
  `3869d66d009f52258be35901edbef370e65a399c`.
- Ran the existing companion tests with `axiom-rules-engine` at the
  repository-pinned commit
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`: two top-level cases and one
  paragraph-(B) case passed.
- Ran no population-backed suite.
- Attempted to place this report at
  `/Users/maxghenis/TheAxiomFoundation/_closure-sprint/out/s1-snap-eid-assessment.md`;
  the managed workspace denied writes outside the RuleSpec worktree. This
  committed file is the canonical report produced in the permitted workspace.
- Did not modify any existing statute or SNAP program specification, oracle
  report/value, toolchain file, CI file, or CODEOWNERS.
