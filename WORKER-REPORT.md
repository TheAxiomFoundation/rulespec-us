# Worker report: rulespec-us#1098 — CalFresh BBCE

## Outcome

The California CalFresh broad-based categorical eligibility policy, called
modified categorical eligibility (MCE) by CDSS, is encoded and defensively
audited on `fed-parity/ca-bbce`.

- Final committed HEAD:
  `ca6394d30cd3e1138beac6cf2fd634ba7556605c`
- Worktree:
  `/Users/maxghenis/TheAxiomFoundation/rulespec-us/.worktrees/ca-bbce`
- Required corpus pin:
  `8af592162231e9de748ba6b98792b426ad4fe8b7`
- Exact pinned axiom-encode:
  `3869d66d009f52258be35901edbef370e65a399c`
- Exact pinned rules engine:
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`
- Program composer workflow pin:
  `fabe0b3b3fd6e90d3e8f075516f9b668f524f711`

The implementation is California-only. No federal RuleSpec file changed, and
non-California program composition is untouched. The California FY 2026
program imports the retained federal `7 CFR 273.2(j)` module and the new CDSS
MCE module.

The program-spec file remains unsigned. All commits are unsigned (`%G? = N`);
signing remains the main lane's job. Nothing was pushed and no GitHub write was
made.

## Base and pin audit

The sandbox could not resolve GitHub, so `git fetch origin main` failed and the
local `origin/main` remains
`c13cdf7dda5948e7a86ff0c317872f93743a2084`. The locally retained #1175 head,
`6f17fe22f437fe29886d2ed053d360ce231a87e6`, is a one-commit child of that
base and contains the required toolchain pin. It was merged locally as
`b94b84627`.

`.axiom/toolchain.toml` directly pins corpus
`8af592162231e9de748ba6b98792b426ad4fe8b7`. All authority and proof checks
below used a local corpus checkout at exactly that commit.

The final diff against the available `origin/main` contains eight expected
paths:

- the upstream `.axiom/toolchain.toml` pin;
- committed `PROGRESS.md`;
- the generated reverse index;
- `programs/us-ca/snap/fy-2026.yaml`;
- the California FY 2026 composition and companion;
- the new California MCE module and companion.

The diff against retained #1175 pin head contains the same list without
`.axiom/toolchain.toml`. No foreign path was found or required restoration.

## Encoded policy

### MCE status gate

`us-ca/policies/cdss/snap/modified-categorical-eligibility.yaml` confers MCE
only when all of the following hold:

1. The household was issued PUB 275 or has online access to it.
2. Gross income is inclusively at or below the exact FY 2026 200% FPL amount.
3. The household is not barred by paragraph (vii).
4. At least one same person is both generally SNAP-member eligible and not
   excluded from categorical-household membership under paragraph (ix).

The inclusive comparison is `<=`. Exact values use the retained FY 2026 table,
including $9,026 for eight members and a $918 increment thereafter.

The paragraph-(vii) model is fail-closed and source-scoped:

- whole-household workfare disqualification remains a `Household` fact;
- IPV, monthly reporting, head-of-household work, the federal pre-opt-out drug
  felony condition, fleeing-felon status, probation/parole violation, and the
  serious-crime sentence condition are `Person` facts;
- the person facts are aggregated through the dedicated
  `calfresh_mce_member_of_household` relation;
- serious-crime conviction and sentence noncompliance must hold for the same
  person;
- head-of-household status and work disqualification must hold for the same
  person.

California's WIC §18901.3 drug-felony opt-out is applied directly to the
federal pre-opt-out member condition. Conviction alone therefore does not bar
MCE, while fleeing-felon and probation/parole-violation conditions remain
bars. There is no fabricated applicant-controlled opt-out switch and no
unreachable “effective drug exclusion” output.

The five separate paragraph-(ix) member exclusions are also encoded:
ineligible alien, ineligible student, cash-out-state SSI recipient,
nonexempt-facility institutionalization, and §273.7 work noncompliance. These
exclude the affected person; they do not become household bars.

### California eligibility composition

`us-ca/policies/cdss/snap/fy-2026-benefit-calculation.yaml` preserves the two
existing routes and adds MCE as a third OR branch:

```text
traditional categorical resource exemption
or (ordinary resource test and ordinary income tests)
or (
  gross income <= MCE limit
  and MCE resource test waived
  and MCE net eligibility ceiling waived
)
```

The branch exposes distinct resource-test and net-ceiling waiver outputs.
Actual net income still flows through federal deduction and allotment
arithmetic; only the eligibility ceiling is waived.

The explicit gross precheck on the MCE branch keeps above-200% households out
of MCE even when some downstream MCE inputs are not needed. Elderly/disabled
households above 200% retain their existing route: no standard gross screen,
but ordinary resource and net tests still apply.

ACL 14-63's option is encoded after the pre-minimum allotment is calculated.
A traditional-CE or MCE household of three or more whose calculated allotment
is zero is denied/discontinued. Using the pre-minimum amount avoids a formula
cycle and avoids treating the minimum allotment as positive eligibility.

## Retained authority and proof audit

Every new policy-bearing parameter and formula has a proof atom with a
retained citation path and verbatim excerpt. The operative map is:

| Rule surface | Retained authority and encoded effect |
| --- | --- |
| California mandate | WIC §18901.5, `us-ca/statute/wic/18901.5`: “The department shall establish a program of categorical eligibility for CalFresh”. |
| Inclusive gross screen | ACL 14-56 page 1: “at or below 200 percent”; corrected ACL 14-56E page 2: “at or less than 200 percent”; ACIN I-46-25 page 7 supplies the FY 2026 200% table. |
| PUB 275 trigger | ACL 15-42 page 2 requires issuance or online access and all other eligibility conditions. ACL 14-56 page 3 states: “Receipt of the PUB 275, in and of itself, does not confer MCE status.” |
| Resource waiver | ACL 14-56 page 3: “receipt of the PUB 275 exempts all resources in the determination of eligibility”. |
| Net eligibility waiver and benefit calculation | Retained 7 CFR 273.2(j)(2)(xi) excludes §273.10(c) for eligibility; ACL 15-42 page 4 says eligible households receive the table allotment even when net income exceeds the ceiling. Net income is still computed for the amount. |
| Household bars | Retained 7 CFR 273.2(j)(2)(vii), beginning: “Under no circumstances shall any household be considered categorically eligible if:”. Every federal subcondition is separately represented. |
| Drug/fleeing overlay | WIC §18901.3 opts California out of the federal drug-felony ban but preserves when “the individual is in violation of probation or parole or ... is a fleeing felon”. |
| Member exclusions | Retained 7 CFR 273.2(j)(2)(ix), beginning: “No person shall be included as a member in any household which is otherwise categorically eligible if that person is:”. All five listed exclusions are encoded. |
| Zero benefit | ACL 14-63 page 2: a traditional-CE or MCE household of three or more with a zero-result net amount is denied. |
| Elderly/disabled path | ACL 13-32 page 3: E/D households are not subject to the gross test, but still must satisfy resources and net income outside MCE. |

The module-level higher-authority checks record WIC §§18901.5/18901.3 and
retained 7 CFR §§273.2, 273.8, 273.9, and 273.10. Exact proof validation
checked 28 atoms in the MCE module and 9 in the composition with zero issues.

## Companion coverage

The exact pinned runner passes 44/44 cases: 32 isolated MCE cases and 12
composed eligibility/benefit cases.

The isolated companion covers:

- 130%, 165%, 199%, exactly 200%, and 201% FPL;
- exact eight- and nine-person table behavior;
- paper PUB 275, online access, no trigger, and receipt alone above the limit;
- all seven effective California bars flipping MCE off: IPV, monthly
  reporting, whole-household workfare, head work, fleeing felon,
  probation/parole violation, and serious-crime sentence noncompliance;
- drug-felony conviction alone not excluding;
- serious conviction and sentence noncompliance separately not excluding;
- a two-person adversary proving those serious-crime predicates cannot be
  split across people;
- all five paragraph-(ix) member exclusions;
- an excluded-only household, a mixed household, and a two-person adversary
  proving general SNAP eligibility and categorical inclusion cannot be split
  across different people.

The composed companion covers:

- a $3,001 resource balance failing the ordinary resource test but qualifying
  through MCE, with a $120 benefit;
- a three-person household with $2,291 net income above the $2,221 ceiling,
  still receiving the computed $97 allotment;
- an E/D household above 200% passing the standard E/D route with a $24
  allotment;
- the same E/D route failing at $10,000 resources;
- separate MCE and traditional-CE three-person zero-benefit denials;
- all six pre-existing non-BBCE composition cases, which remain green.

### Mutation evidence

The final-tree mutation inserted `false and` at the start of only the MCE
branch of `calfresh_income_and_resource_eligible`.

It produced exactly seven failed assertions:

- `mce_waives_the_resource_eligibility_test`: 3;
- `mce_waives_the_net_ceiling_but_net_income_still_computes_the_benefit`: 3;
- `mce_three_person_zero_benefit_household_is_denied`: 1.

Traditional categorical eligibility, ordinary eligibility, and both E/D cases
remained green. The source was restored with `apply_patch`,
`git diff --exit-code` confirmed no mutation residue, and the composition
companion returned to 12/12.

## Six oracle disposition walk-throughs

The disposition file has 243 issue-linked rows: 138 eligibility residuals and
105 benefit residuals. Among the 138 unique eligibility cases, 80 fail only
gross income, 42 fail only net income, and 16 fail both. None fails the
resource test or materializes a countable-resource input, so the resource
waiver necessarily uses a synthetic companion.

The raw disposition payloads do not materialize PUB 275 or the new exclusion
facts. Each walk-through below is therefore conditional on:

- `household_was_issued_pub_275=true` or online access;
- every effective household bar being false;
- at least one same-person generally eligible and categorically includable
  member;
- the already-observed passing resource path.

| Case | Household facts | Encoded path and expected flip |
| --- | --- | --- |
| `ecps-56918` | One person, age 44; $1,784.63 earned; gross 136.75% FPL. The 130% limit is $1,696 and 200% limit is $2,610. Net is $475.63 ≤ $1,305. | Gross-only standard failure; inclusive MCE gross screen passes, net/resources already pass. Eligibility flips to true and the encoded pre-gate allotment becomes payable at $155. PE reports $159.04. |
| `ecps-57033` | Three people, ages 19/41/38; $2,915.49 earned; gross 131.27% FPL. Limits are $2,888 at 130% and $4,442 at 200%. Net is $1,379.49 ≤ $2,221. | Gross-only failure; MCE passes without changing benefit arithmetic. Eligibility flips to true, $371. PE reports $377.27. |
| `ecps-57143` | Four people; $3,188.82 earned plus $926.46 unearned; gross $4,115.28, or 153.56% FPL. Limits are $3,483/$5,360. Net is $2,529.28 ≤ $2,680. | Gross-only failure; MCE passes the 200% screen. Eligibility flips to true, $235. PE reports $242.00. |
| `ecps-59281` | Two people, ages 56/17; $2,028.17 unearned; gross 115.04% FPL; net $1,819.17 > $1,763. | Gross already passes; MCE waives only the net eligibility ceiling, while net still computes the amount. Eligibility flips to true, $24. PE reports $23.97. |
| `ecps-60516` | One person, age 80 and E/D; $2,031.99 unearned; gross 155.71% FPL and net $1,529.99 > $1,305. | The standard E/D gross bypass already holds; MCE is within 200% and waives the failing net ceiling. Eligibility flips to true, $24. PE reports $23.97. |
| `ecps-62420` | Two people, ages 59/8; $1,171.80 earned plus $2,006.89 unearned; gross $3,178.69, or 180.30% FPL. Limits are $2,292/$3,526. Net is $1,991.69 > $1,763. | Standard gross and net both fail; MCE passes the 200% screen and waives net eligibility. Eligibility flips to true, $24. PE reports $23.97. |

These cases validate expected rule paths and arithmetic, not the PUB trigger
itself. The retained-source synthetic companions provide the direct PUB and
exclusion evidence.

## Validation and integration gates

| Gate | Result |
| --- | --- |
| Exact pinned companion runner | PASS, 44/44. |
| Exact pinned `validate --skip-reviewers` | PASS on both changed modules from an isolated canonical `rulespec-us/us-ca` copy; `ci_pass=true`, `all_passed=true`, errors `[]`. |
| Exact proof validation | PASS, 28 MCE atoms plus 9 composition atoms, zero issues. |
| Program compose and compile | PASS with pinned composer and pinned engine; 328 derived outputs. |
| Repository layout and program-spec tests | PASS, 12/12. |
| Reverse index | Regenerated and `--check` PASS: 4,250 provisions, 5,092 edges, 4,487 modules. Delta contains only expected WIC/ACL/ACIN/7 CFR links. |
| Mutation | PASS: seven targeted failures with BBCE disabled; restored tree 12/12. |
| Oracle pending ratchet | PASS with zero undeclared and zero stale entries, because the existing broad `us-ca:` P4 fallback classifies the new outputs. |
| Final diff check | `git diff --check origin/main...HEAD` emits no output; no federal RuleSpec or foreign path changed. |

The direct nested-worktree companion invocation hit the known standalone
import-resolution artifact, and a symlink-root standalone validate attempt
spent its time recursively indexing candidate roots. The canonical alias and
an isolated real-directory copy eliminate those artifacts and produced the
green results above.

## Oracle bridge handoff

There are 17 new executable legal IDs. All have positive companion output
coverage. On axiom-oracles `origin/main`, every one currently resolves only to
the broad exact-inadequate prefix row:

```text
legal_id: us-ca:
mapping_type: not_comparable
match_type: prefix
candidate_priority: P4
```

Consequently the general pending report shows no pending IDs, but the
changed-file contract still needs an accompanying axiom-oracles mappings PR.
Do not add these to `oracle-coverage-pending.yaml`; pending classification is
not the intended final state.

The mappings PR needs exactly these rows.

### Exact comparable mappings

1. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_mce_gross_income_limit_rate`
   - `mapping_type: parameter_value`
   - `policyengine_parameter: gov.hhs.tanf.non_cash.income_limit.gross`
   - key `CA`; month; rate.
2. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_categorical_member_student_exclusion_applies`
   - `mapping_type: direct_variable`
   - `policyengine_variable: is_snap_ineligible_student`
   - Person; month; boolean.

### Exact P4 `not_comparable` mappings

1. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_mce_gross_income_limit`
   - Candidate `meets_tanf_non_cash_gross_income_test` is a predicate, not the
     encoded household-size Money ceiling.
2. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_wic_18901_3_drug_felony_opt_out_applies`
   - No PolicyEngine drug-felony opt-out variable.
3. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_mce_federal_drug_felony_exclusion_before_state_opt_out`
   - No PolicyEngine drug-felony member fact.
4. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_mce_household_exclusion_applies`
   - No single PolicyEngine variable represents the full paragraph-(vii)
     household disjunction.
5. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_mce_member_household_exclusion_applies`
   - `meets_snap_work_requirements` covers only one limb and not the full
     member-bar disjunction.
6. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_categorical_member_ineligible_alien_exclusion_applies`
   - `is_snap_immigration_status_eligible` is opposite polarity.
7. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_categorical_member_cash_out_ssi_exclusion_applies`
   - No PolicyEngine candidate.
8. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_categorical_member_institution_exclusion_applies`
   - No PolicyEngine candidate.
9. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_categorical_member_work_exclusion_applies`
   - `meets_snap_work_requirements` has different polarity/semantic scope.
10. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_categorical_member_inclusion_status`
    - Immigration, student, and work variables cover only three of five limbs;
      there is no exact composite.
11. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_mce_member_eligible`
    - No same-person PolicyEngine composite.
12. `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_mce_status_conferred`
    - Candidate `is_tanf_non_cash_eligible` lacks the PUB 275 trigger and
      federal/state bars and imposes PolicyEngine's net test.
13. `us-ca:policies/cdss/snap/fy-2026-benefit-calculation#calfresh_mce_resource_eligibility_test_waived`
    - `meets_tanf_non_cash_asset_test` is a test outcome, not an explicit legal
      waiver.
14. `us-ca:policies/cdss/snap/fy-2026-benefit-calculation#calfresh_mce_net_income_eligibility_test_waived`
    - `meets_tanf_non_cash_net_income_test` is opposite to the legal waiver.
15. `us-ca:policies/cdss/snap/fy-2026-benefit-calculation#calfresh_categorical_zero_benefit_denial_applies`
    - `is_snap_eligible` and `snap_normal_allotment` are downstream/amount
      candidates, not this California denial predicate.

The existing exact P4 rows for
`calfresh_income_and_resource_eligible` and `snap_eligible` remain in place;
the mappings PR should review their rationales but does not need new IDs for
them.

All named candidates were verified in the PolicyEngine-US 1.767.3 source tree.
That version has:

- California gross ratio `2`;
- California TANF non-cash asset limit `.inf`;
- both California `net_applies/hheod` and `net_applies/non_hheod` set to
  `true`;
- no PUB 275, IPV, monthly-reporting, drug-felony, fleeing-felon,
  probation/parole, serious-crime, cash-out SSI, or institutionalization facts.

The net applicability values are why PolicyEngine's aggregate TANF non-cash
eligibility cannot stand in for the retained California MCE rule.

## Sandbox and tooling disclosures

- `git fetch origin main` failed because the sandbox could not resolve
  `github.com`; the final remote comparison is against the locally available
  ref plus the retained #1175 pin head.
- An initial `uv` path hit cache-permission and network clone failures for
  axiom-oracles. Validation used local installed environments and pinned source
  archives instead.
- The pinned rules-engine archive did not include a binary. The exact pinned
  source was built successfully offline and used for every companion and
  compile result.
- Direct nested-worktree resolution produced the documented standalone import
  artifact. Canonical aliases and isolated real-directory copies were used for
  authoritative gates.
- The GitNexus graph connector was unavailable. The architecture check used
  direct source/module-graph inspection and an end-to-end program compile.

No destructive command, push, GitHub mutation, signing action, or
axiom-oracles write occurred.

## Final repository audit

```text
HEAD ca6394d30cd3e1138beac6cf2fd634ba7556605c
branch fed-parity/ca-bbce
available origin/main c13cdf7dda5948e7a86ff0c317872f93743a2084
retained pin head 6f17fe22f437fe29886d2ed053d360ce231a87e6
corpus 8af592162231e9de748ba6b98792b426ad4fe8b7

git status --short
?? WORKER-REPORT.md
```

`WORKER-REPORT.md` is intentionally untracked. The committed worktree is
otherwise clean.
