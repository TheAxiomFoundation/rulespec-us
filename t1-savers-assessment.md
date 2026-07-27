# Saver's Credit §25B launch assessment

Date: 2026-07-27

## Decision

**Do not certify or ship a direct Saver's Credit program from the current
`us:statutes/26/25B#savers_credit` node.**

The direct node mechanically composes, compiles, and evaluates, but it does
not produce the full section 25B credit:

1. It has one TaxUnit eligibility screen and one $2,000 cap. Section 25B(a)
   applies the cap separately to each eligible individual, so a joint return
   with two eligible contributors is understated.
2. It negates
   `us:statutes/26/151#exemption_individual_eligible`. That rule asks whether
   the individual is the taxpayer or spouse for whom a section 151 exemption
   is available. Section 25B(c)(2)(A) instead excludes an individual for whom
   another taxpayer is allowed a section 151 deduction.
3. It does not import the 2026 limits from IRS Notice 2025-67. It expects a
   caller-supplied derived input, `cost_of_living_adjustment_25b`.

The merged pipeline states the first two defects itself. The pipeline is
therefore doing substantive legal work that belongs in the statute module.
This triggers the brief's explicit stop condition. No program spec, grid
suite, or golden case was added.

## Revisions and audit method

- `rulespec-us`: local `origin/main` and starting commit
  `c2bcf2bc06246973fb8429811e2a5d00fc2bdc78`.
- `axiom-corpus`: pinned `origin/main`
  `db12795577c5809009168982cf8a72fb58440620`.
- `policyengine-us`: source read from `upstream/main`
  `61cc1e63323579deaa4a5070185bdfafcd7e838a`; the working checkout was
  dirty and behind, so it was not modified or used as source authority.

The corpus audit archived the pinned inventory, parsed every
`.items[].citation_path` from all **691** inventory JSON files, and only then
filtered by exact path. It covered **142,902 records** and **124,483 unique
citation paths**, with no parse error. No inventory filename was used to
select a source.

## Exhaustive frontier

`O` means a raw or directly recorded fact. `D` means an amount,
classification, comparison, or aggregation produced by another legal rule
that the reached graph does not compute. A recorded transaction amount may be
raw, but an input already named as a qualifying section-specific amount is
classified `D`.

There are **31 module-qualified scalar leaves: 7 observed and 24 derived**.
They lower to only 30 bare runtime slots because the section 25B and section
151 `filing_status` inputs collide. The first section 25B companion case
assigns those two qualified inputs different values, so this is not a safely
namespaced boundary.

### Section 25B leaves

| Class | Input | Reason |
|---|---|---|
| O | `us:statutes/26/25B#input.filing_status` | Filed-return status. |
| D | `us:statutes/26/25B#input.adjusted_gross_income` | Section 62 assembled tax-law amount. |
| D | `us:statutes/26/25B#input.section_911_excluded_income` | Exclusion amount determined under section 911; zero must be an affirmative fact. |
| D | `us:statutes/26/25B#input.section_931_excluded_income` | Exclusion amount determined under section 931; zero must be an affirmative fact. |
| D | `us:statutes/26/25B#input.section_933_excluded_income` | Exclusion amount determined under section 933; zero must be an affirmative fact. |
| D | `us:statutes/26/25B#input.cost_of_living_adjustment_25b` | Section 1(f)(3) calculation with section 25B(b)(3)'s substituted base year. |
| O | `us:statutes/26/25B#input.age_at_close_of_taxable_year` | Age/date fact at year end. |
| D | `us:statutes/26/25B#input.is_student_under_section_152_f_2` | Section 152(f)(2) legal classification from enrollment facts. |
| D | `us:statutes/26/25B#input.retirement_contribution_inclusion_window_applies` | Legal effective-period conclusion. |
| D | `us:statutes/26/25B#input.able_account_contributions` | Amount already classified under sections 25B(d)(1)(A) and 529A. |
| D | `us:statutes/26/25B#input.qualified_retirement_contributions` | Amount already classified under section 219(e). |
| D | `us:statutes/26/25B#input.elective_deferrals` | Amount already classified under section 402(g)(3). |
| D | `us:statutes/26/25B#input.eligible_deferred_compensation_deferrals` | Amount already classified under section 457(b) and (e)(1)(A). |
| D | `us:statutes/26/25B#input.voluntary_employee_qualified_plan_contributions` | Amount already classified under section 4974(c). |
| D | `us:statutes/26/25B#input.individual_testing_period_distributions` | Aggregate over the section 25B(d)(2)(B) testing period. |
| D | `us:statutes/26/25B#input.spouse_testing_period_distributions` | Spouse-level testing-period aggregate. |
| O | `us:statutes/26/25B#input.filing_status_for_spouse_distribution_year` | Filed status for the distribution year. |
| D | `us:statutes/26/25B#input.trustee_to_trustee_transfer_or_rollover_distribution_portion` | Legally classified excluded distribution portion. |
| D | `us:statutes/26/25B#input.section_72_p_distribution` | Section-specific legal classification. |
| D | `us:statutes/26/25B#input.section_401_k_8_distribution` | Section-specific legal classification. |
| D | `us:statutes/26/25B#input.section_401_m_6_distribution` | Section-specific legal classification. |
| D | `us:statutes/26/25B#input.section_402_g_2_distribution` | Section-specific legal classification. |
| D | `us:statutes/26/25B#input.section_404_k_distribution` | Section-specific legal classification. |
| D | `us:statutes/26/25B#input.section_408_d_4_distribution` | Section-specific legal classification. |
| D | `us:statutes/26/25B#input.section_408A_d_3_distribution` | Section-specific legal classification. |

### Imported section 151 leaves

| Class | Input | Reason |
|---|---|---|
| O | `us:statutes/26/151#input.tin_included_on_return_claiming_exemption` | Return-field fact. |
| O | `us:statutes/26/151#input.is_taxpayer` | Filing-unit role fact. |
| O | `us:statutes/26/151#input.is_spouse_of_taxpayer` | Filing-unit relationship fact. |
| O | `us:statutes/26/151#input.filing_status` | Filed-return status; distinct qualified input but colliding runtime name. |
| D | `us:statutes/26/151#input.spouse_has_no_gross_income_for_calendar_year` | Gross-income legal aggregation and zero test. |
| D | `us:statutes/26/151#input.spouse_is_dependent_of_another_taxpayer` | Section 152 dependency conclusion. |

### Section 25B(d) conclusion

The final qualified retirement savings contribution is **derived, not
observed**. The direct module computes one leg as gross qualifying categories
minus testing-period distributions, after exceptions, floored at zero.
However, all category classifications, exception classifications, and
testing-period aggregates above remain derived frontier inputs. It also
computes only one TaxUnit leg.

The pipeline accepts two completed net section 25B(d) amounts—one for the
primary individual and one for the spouse—and explicitly defers the
per-person category/distribution composition. Raw contribution and
distribution transactions may be observed; the legally usable section
25B(d) amount is not.

## Direct execution and provision-rootedness

The reachable direct-output ancestry contains **33 executable nodes**:

- 17 section 25B derived rules;
- 15 section 25B parameters; and
- `us:statutes/26/151#exemption_individual_eligible`.

All 32 section 25B nodes cite `us/statute/26/25B`, and the imported node cites
`us/statute/26/151`. Both citation paths occur exactly once in the pinned
corpus inventory. Thus the authored internal nodes have resolving legal
sources. That mechanical rootedness does not cure the semantic defects above.

**End-to-end provision-rootedness fails.** The graph accepts 24 derived
frontier leaves as caller-supplied values instead of reaching encoded
provision nodes that determine them. Eleven explicit section 25B(d)
cross-reference paths are also absent from the pinned corpus. Resolving the
proof roots of the 33 authored executable nodes establishes internal source
resolution, not an unbroken provision-rooted path from the output through
every legal dependency.

A temporary transformation-free spec with sole output `savers_credit` and
scope `statutes/26/25B` composed and compiled. Module-granular loading emitted
41 derived outputs because section 151 has unrelated top-level imports, while
only the 33 nodes above are reachable from `savers_credit`.

A diagnostic joint case at $40,000 AGI, a 0.61 caller-supplied COLA, and
$10,000 of combined qualifying contributions returned:

- rate: 50%;
- contributions taken into account: $2,000; and
- direct credit: **$1,000**.

If the $10,000 represents $5,000 contributed by each of two eligible spouses,
section 25B(a) requires two separately capped $2,000 legs:
`50% × ($2,000 + $2,000) = $2,000`. The direct node has no way to represent
that result.

The imported eligibility predicate is independently wrong for the target.
For an ordinary taxpayer with a TIN, section 151's reached rule can hold;
section 25B then negates it and disqualifies the taxpayer. Existing direct
tests obtain eligibility by setting the section 151 taxpayer/spouse/TIN facts
false, which is not the section 25B(c)(2)(A) question.

## IRS Notice 2025-67

The guidance transcription is honest source evidence as it stands:

- `us/guidance/irs/notice-2025-67/page-3` resolves once;
- `us/guidance/irs/notice-2025-67/page-4` resolves once;
- `us/statute/26/25B/b` resolves once; and
- all 27 Notice proof atoms (nine parameters times amount,
  `effective_from`, and `effective_to`) resolve, with excerpts matching the
  pinned corpus text exactly.

The defect is the relationship, not the copied values. Today the
statute-to-guidance link is prose, co-listed source paths, and nine opaque
imports in the policy pipeline. The direct section 25B node reaches none of
those parameters. Its existing five companion cases all set
`cost_of_living_adjustment_25b` and all three add-backs to zero, so they prove
neither the official 2026 tiers nor the add-back behavior. Supplying 0.61
does produce the three joint limits numerically, but it is a caller-supplied
derived fact.

When axiom-rules-engine#117 makes the relationship first-class, the edge must:

1. originate at section **25B(b)(3)**;
2. target the tax-year-2026 Notice provisions/parameters on pages 3-4;
3. carry 2026 applicability; and
4. feed the statutory threshold nodes, likely changing import hashes.

The brief's reference to **§25B(j) does not resolve** at the pinned corpus.
The pinned section contains only subsections (a)-(f); the inflation delegation
is `us/statute/26/25B/b/3`. A future relation targeting `/j` would fail.
The head-of-household paragraph crosses PDF pages 3-4, so a first-class proof
may also need multi-page provenance or a narrower guidance child provision.

## Closure status by citation path: incomplete

**Task 4 cannot be honestly certified for the current graph.** The wrong
eligibility dependency and 24 externally supplied derived leaves prevent a
closed legal dependency universe from being enumerated. The counts below are
an exact audited source slice and a conservative repair inventory, not a
claim of transitive closure.

The smallest audited authored/guidance slice is **19 exact citation paths**:

- all 14 paths under `us/statute/26/25B`;
- `us/statute/26/151`;
- `us/statute/26/151/b`;
- `us/statute/26/151/e`; and
- Notice pages 3 and 4.

For launch certification, its conservative disposition is:

| Disposition | Paths | Count |
|---|---|---:|
| Encoded | Notice page-3 and page-4 snippets supporting the nine parameters | 2 |
| Excludable | `us/statute/26/25B/f`, investment-in-contract coordination, which does not change the section 25B potential amount | 1 |
| Pending | The remaining section 25B and section 151 paths | 16 |
| **Total** |  | **19** |

This treats the exact cited Notice excerpts as encoded, not every unrelated
rule printed on those two pages. It is deliberately conservative: correct
subformulas in section 25B remain pending until the joint-person,
eligibility, and guidance edges are repaired.

The 19 paths are an audited slice, not a final semantic universe. A conservative
eligibility repair scope using whole sections is already **61 paths**:
14 section 25B + 11 section 151 + 34 section 152 + 2 Notice pages.

Adding immediate present roots for AGI, add-backs, COLA, and section 25B(d)
classifications raises that lower bound to **158 present citation paths**:

- section 62: 53;
- sections 911, 931, and 933: 29 + 9 + 1;
- section 1(f)(3): 1;
- section 219(e): 3; and
- section 408(d)(4): 1.

Eleven additional exact section 25B(d) cross-reference paths have **zero**
records in the pinned corpus and are pending outside that 158-path count:

- sections 529A, 402(g)(3), 457(b), 457(e)(1)(A), and 4974(c);
- sections 72(p), 401(k)(8), 401(m)(6), 402(g)(2), and 404(k); and
- section 408A(d)(3).

The resulting **169-path conservative repair inventory** has this disposition:

| Disposition | Present paths | Absent paths | Total |
|---|---:|---:|---:|
| Encoded | 2 | 0 | 2 |
| Excludable for the potential-credit output | 1 | 0 | 1 |
| Pending | 155 | 11 | 166 |
| **Total** | **158** | **11** | **169** |

Even this 169-path inventory is not transitive closure of section 62 or the
retirement-plan definitions, and its whole-section repair scopes may include
provisions that a corrected dependency graph would not reach. The honest
closure result is therefore **incomplete and uncertifiable**, not 169 of 169.

## PolicyEngine counterpart

PolicyEngine's implementation is real logic, not a parameter passthrough:

- `savers_credit_potential` sums person-level credits;
- each eligible person's qualifying contributions are computed, capped at
  $2,000, multiplied by a filing-status/AGI-selected rate, and then summed;
- `savers_credit` further limits the potential credit by tax liability and
  preceding credits; and
- qualifying contributions sum named retirement contribution variables and
  subtract retirement distributions.

The closest provision quantity is therefore `savers_credit_potential`, not
the final `savers_credit` after other credit-order law. Current axiom-oracles
marks `us:statutes/26/25B#savers_credit` `not_comparable` to that candidate and
records the Saver's Credit as uncovered.

PolicyEngine also has two visible source-model differences that a future grid
must not hide:

1. It treats each published AGI maximum as the next bracket's lower bound.
   At the exact 2026 maxima it returns the lower next-step amount, while
   section 25B's “not over” grammar keeps the prior rate through the maximum.
2. Its Saver's Credit reads plain `adjusted_gross_income` and does not add
   section 911, 931, or 933 excluded income.

A clean future nonzero-add-back probe is single AGI $24,249 plus $2 under any
one of sections 911, 931, or 933, with $2,000 contributions. Section 25B(e)
uses $24,251 and produces $400; PolicyEngine currently ignores the add-back
and produces $1,000. AGI $24,250 plus $1 must not be used because the separate
boundary bug masks the add-back defect.

No population-backed suite was run. No comparison report or committed oracle
number was changed.

## Validation

The temporary direct program was created and composed with:

```zsh
compose_root=$(mktemp -d /private/tmp/savers-compose.XXXXXX)
mkdir "$compose_root/rulespec-us"
ln -s "$PWD/us" "$compose_root/rulespec-us/us"

~/axiom-compose/.venv/bin/axiom-compose \
  <(printf '%s\n' \
    'program: us/savers-credit' \
    "period: '2026'" \
    'outputs:' \
    '  - savers_credit' \
    'scope:' \
    '  federal:' \
    '    - statutes/26/25B') \
  --rulespec-root "$compose_root/rulespec-us" \
  -o /private/tmp/us-savers-credit.rulespec.yaml
```

It had no `transformations:` block and imported only section 25B plus the
section 151 eligibility rule. The exact compile command was:

```zsh
AXIOM_RULESPEC_REPO_ROOTS="$compose_root" \
  ~/axiom-rules/target/release/axiom-rules-engine compile \
  --program /private/tmp/us-savers-credit.rulespec.yaml \
  --output /private/tmp/us-savers-credit.compiled.json
```

It exited successfully with 41 emitted derived outputs, engine 0.1.0, and
the generic fast path. Replaying the first committed section 25B companion
case through `axiom-rules-engine run-compiled
--artifact /private/tmp/us-savers-credit.compiled.json` returned
`{'kind': 'decimal', 'value': '1000'}` for the direct legal root.

Repository checks:

```zsh
pytest -q tests/test_repository_layout.py
pytest -q tests/test_program_specs.py
git diff --check
```

The results were 9 tests passed, 3 tests passed, and no whitespace errors,
respectively. An independent read-only review found the stop decision
well-evidenced and, after revision, found the frontier, rootedness, and
closure-inventory arithmetic internally consistent.

## Deliverables and next work

Built:

- this committed assessment; and
- the committed `PROGRESS.md` handoff ledger.

The requested copy to
`~/TheAxiomFoundation/_closure-sprint/out/t1-savers-assessment.md` was
attempted, but the managed filesystem rejected the write with
`Operation not permitted`. This committed file is the canonical report.

Not built because the stop condition was met:

- no one-output launch program;
- no grid suite; and
- no golden-case artifact.

The shortest honest repair is to move the pipeline's separate per-person
credit legs into the section 25B provision module, replace the section 151
predicate with the actual “allowed to another taxpayer” dependency, encode a
first-class section 25B(b)(3) → Notice relation, connect the section
911/931/933 outputs, and resolve the section 25B(d) per-person frontier. Only
then should a transformation-free program and synthetic grid be added.

**Certifiability by the launch deadline: no. Launch smaller.**
