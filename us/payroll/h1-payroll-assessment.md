# Employee-side federal payroll taxes: certification assessment

Date: 2026-07-27

## Bottom line

The proposed employee-side federal payroll-tax program is **not certifiable
today**, although it remains a strong candidate for a second certificate. This
assessment was committed before the program implementation, as required by the
task order. The branch now contains a narrow supported-domain sibling program
that applies the 2026 OASDI base, distinguishes Person and TaxUnit Medicare
wages, and exercises the actual base and threshold boundaries. [R27] [R28]

That implementation resolves the first integration prerequisite for its
declared one-employer, no-section-3101(c)-exemption profile. It does not produce
any of the four certificate verdicts. The older `oasdi-wage-tax` program still
merely imports section 3101(a) and section 3121(a)(1): its OASDI formula remains
`0.062 * wages`, while the wage-base exclusion remains a separate
Payment-level output. [R1] [R2] [R3] [R4]

The critical path is:

1. review and accept the explicit observed-fact frontier and narrow supported
   profile, or complete the section 3121 wage/employment and section 3101(c)
   integration needed to generalize it; [R5] [R6] [R27]
2. align the closure corpus pin to a snapshot with paragraph-granular section
   3101, then classify all 143 citation paths under the three roots consumed by
   the implemented program; [R7] [R8] [R17] [R31]
3. create frozen, committed program-level reference evidence and an exercise
   census after the launch freeze ends; and [R9] [R10]
4. add computed closure and executable-verdict producers plus a published
   engine-by-artifact execution receipt. [R10] [R11]

Mappings alone cannot satisfy any of those missing evidence steps. The task
brief expressly freezes comparison-suite reruns, so this work must not claim
conformance from newly added mapping rows. [R9]

## Verdict snapshot

| Verdict | Current answer | What is missing |
|---|---|---|
| `conformant` | No computed verdict; narrow-profile integration prerequisite implemented | A payroll program entry in the certificate registry; at least one committed reference-oracle suite/report bound by exact path and SHA; and clean per-case evidence with zero unexplained and zero open Axiom-attributed mismatches. The comparison must enforce the mapping's wage-identity and zero-self-employment restrictions. [R10] [R30] |
| `exercised` | No computed verdict; 11 boundary companions pass | A suite census row, exact report identity, per-case evidence fields, a non-contested report, and an audited bridge. Companion tests are necessary but do not themselves meet the certificate's exercise predicate. [R10] [R28] [R29] |
| `closed` | Not computed | A reviewed root declaration, a citation-path-derived universe, one content-grounded `encoded` / `excluded-with-reason` / `pending` classification per row, a frontier census, and a computed producer. The two statutory roots produce 134 paths at the present pin and 142 at the adequate newer snapshot; the implemented program's SSA guidance root makes the total declared-root universes 135 and 143. [R7] [R8] [R11] [R14] [R31] |
| `executable` | Not computed; local pinned composition and compilation pass | A published compiled program artifact, its compatible public engine, a receipt showing that the pair loads and reproduces the benchmark, and a computed verifier. A local compile is only a prerequisite. [R10] [R15] [R29] |

The current certificate producer contains only `us-co/snap` in its program
registry, computes conformance from clean reference legs, and computes exercise
from its census. It still carries `closed` and `executable` as attested
scaffolding, making the overall certified state unavailable until both become
computed and true. [R10]

## The legacy integration defect and the narrow-profile repair

The canonical OASDI program declares two scope entries but no transformation:
`statutes/26/3101/a` and `statutes/26/3121/a/1`. [R1] The composer turns scope
roots into imports and emits only those imports plus any explicitly declared
transformations; it does not infer a dataflow from one imported output into
another imported rule. [R4]

Consequently:

- section 3101(a) computes `oasdi_wage_tax_rate * wages` on `Person`; [R2]
- section 3121(a)(1) separately computes
  `oasdi_wage_base_excess_excluded_remuneration` on `Payment`; [R3]
- no current rule subtracts that exclusion from remuneration, aggregates the
  result to the person/year level, or supplies capped wages to
  `oasdi_wage_tax`; [R1] [R2] [R3] and
- the existing real-program acceptance case uses only $1,000, so it cannot
  expose the missing cap. [R16]

This matters at the exact boundary the task requires. The encoded 2026
contribution-and-benefit base is $184,500. [R17] PolicyEngine applies the
employee OASDI rate to `min(cap, payroll_tax_gross_wages)`, while its ordinary
Medicare variable applies 1.45 percent to uncapped payroll wages. [R18] Its
Additional Medicare Tax is tax-unit level and includes both payroll wages and
taxable self-employment income, so a direct wage-tax comparison must constrain
self-employment income to zero. [R19]

The parent section 3121(a) module explicitly defers the final `wages` output
because faithfully computing it requires all enumerated exclusions; the parent
section 3121(b) module likewise defers the final `employment` output because an
exclusion branch remains unresolved. [R6] Treating observed W-2 wage boxes as
frontier facts can avoid that upstream computation, but the program must then
distinguish OASDI wages from uncapped Medicare wages and must not claim that its
mere import of section 3121(a)(1) proves the cap. [R1] [R3] [R6]

Section 3101(c) is also operative: it exempts covered wages from the taxes in
section 3101 when a qualifying international social-security agreement applies.
The exception is encoded, but the current OASDI output does not consume its
exempt-wage output. A general program must wire it; a narrower program must
state and test that such wages are outside its supported profile. [R5]

The new sibling program takes the narrower route. It defines separate completed
pre-cap OASDI, Person Medicare, and TaxUnit Medicare wage facts; requires one
employer or already-resolved successor continuity; requires no section 3101(c)
exempt wages; and publishes three new, exact output names. Its 11 companions
cover below, at, and above the $184,500 base; at and above the Additional
Medicare thresholds; and the fail-closed section 3101(c) boundary. [R27] [R28]
These facts repair the above-cap arithmetic for the declared profile, but they
are frontier declarations rather than an encoding of every section 3121
exclusion.

## `closed`: declared roots and exact universe

### Reviewed root declaration

For the implemented program, I would declare these roots:

- `us/statute/26/3101`; and
- `us/statute/26/3121`; and
- `us/guidance/ssa/contribution-and-benefit-base/2026/block-1`.

Section 3101 expressly defines the taxed wages through section 3121(a) and
employment through section 3121(b), while section 3121 contains the exclusions
and cross-references that determine those concepts. [R20] Declaring only the
already encoded paragraph 3121(a)(1) would hand-pick the favorable branch and
would not establish closure of the legal wage or employment definitions. [R3]
[R6]

The third, non-statutory root is unconditional for the program built here:
the pipeline imports the RuleSpec module that computes the $184,500 value from
SSA's official determination. [R17] [R27] A future program could instead treat
the published base as an observed frontier fact and remove this import, but it
must not import the computed guidance module while omitting its source root
from closure.

The frontier must separately declare facts the program does not derive, such as
the relevant wage inputs, filing status, self-employment-income restriction for
the direct PolicyEngine comparison, and any supported-profile exclusion for
international-agreement wages. [R5] [R19]

### Citation-path count

The rulespec validation toolchain pins axiom-corpus commit
`bf97b17baebfdf12601f7c23697524bf5adcdaed`. [R7] I enumerated
`.items[].citation_path` from **every** inventory under
`data/corpus/inventory/us`, selected the three exact roots or their descendants,
and deduplicated paths. Inventory rows are the corpus's expected normalized
provisions, keyed by `citation_path`. [R21]

| Corpus snapshot | §3101 paths | §3121 paths | SSA guidance paths | Total declared-root universe |
|---|---:|---:|---:|---:|
| pinned `bf97b17…` | 1 | **133** | 1 | **135** |
| cached `origin/main` `db127955…` | 9 | **133** | 1 | **143** |

Thus **133 section 3121 rows need content classification** under either
snapshot. The two statutory roots account for 134 paths at the pin and 142 at
the newer snapshot; the extra path in each total is the exact SSA guidance
root. The brief's “~138” section 3121 count is not the repository-derived
count. [R8] [R22] [R31]

The difference is certificate-critical. At the current pin, section 3101 is
represented only by its root citation path, so the corpus cannot independently
account for 3101(a), 3101(b)(1), and 3101(b)(2). The later cached snapshot adds
nine paths: the section root, (a), (b), (b)(1), (b)(2), (b)(2)(A)-(C), and (c).
[R8] A certificate must name one exact corpus commit; it must not claim the
142-row statutory denominator while retaining the older `bf97b17…` pin.
[R7] [R8]

The concrete future classification workload is therefore **143 rows** after a
deliberate alignment to at least `db127955…`: nine section 3101 rows, 133
section 3121 rows, and one SSA guidance row. This is a classification workload,
not an encoding estimate: each row must be read and marked encoded, excluded
with a content-grounded reason, or pending. A module filename alone is not a
content-level closure verdict. [R11] [R31]

### Ingest scope

`complete: true` in axiom-corpus means that a nonempty inventory has no missing,
extra, or duplicate provision paths; the implementation makes no broader
full-title or full-root assertion. [R23]

- The older tax ingest is **scoped**, with six matched source/provision rows;
  its completeness flag certifies only those six declared rows. [R24]
- The consolidated Title 26 ingest is also **scoped**: its command combines two
  named source versions and reports 92 matched rows, not all of Title 26. [R25]
- The section 3121 carrier is a **full-section extraction at the corpus's
  structural granularity**: its provenance declares the exact citation root
  `us/statute/26/3121` and “exact cited section with required structural
  ancestors.” It yields the 133 distinct paths above. [R22] The recovery
  release's `complete: true` covers its entire selected 2,453-row batch, not all
  of Title 26. [R26]
- The newer section 3101 structural repair is **scoped to the repaired
  sections**, not all of Title 26; its inventory is the source of the nine
  section 3101 paths counted at `db127955…`. [R8]

No closure ledger with one reviewed disposition per row, no committed frontier
census for this program, and no computed closed-verdict producer were located
in the repositories inspected. The closure prototype itself describes those as
the artifacts that should be added, and the current certificate producer
continues to treat closure as attested. [R10] [R11]

## Detailed remaining work by verdict

### Conformant

1. Preserve the three exact program-output mappings and enforce their declared
   wage-identity, one-employer, and zero-self-employment comparison
   restrictions. [R30]
2. After the launch freeze, create a committed reference suite/report covering
   below-base, above-base, and Additional Medicare threshold cases. The task
   currently authorizes mappings only, not a suite rerun. [R9]
3. Register that suite in the certificate producer, bind the exact report path
   and SHA, retain per-case evidence, and resolve every unexplained or
   Axiom-attributed mismatch. [R10]
4. Restrict the Additional Medicare comparison to wage-only cases unless the
   RuleSpec program also models taxable self-employment income. [R19]

### Exercised

The existing statute companions exercise $0 and $100,000 for section 3101(a),
$0 and $100,000 for section 3101(b)(1), multiple filing statuses above the
Additional Medicare thresholds for section 3101(b)(2), and a payment crossing a
synthetic $100,000 OASDI base for section 3121(a)(1). [R13] The new integration
companion closes the implementation-level boundary gap with distinct OASDI and
Medicare wage facts below, at, and above the actual $184,500 cap and at and
above the Additional Medicare threshold. [R17] [R28]

The certificate's exercised verdict additionally requires, for each registered
suite, a census row whose report path and SHA match the registry, nonempty
per-case evidence fields, no contested report identity, and an audited bridge.
[R10] Those artifacts do not exist for this payroll program, and the suite
freeze prevents creating them in this task. [R9]

### Closed

Align the corpus snapshot, adopt the reviewed roots above, classify all 143
rows, record exclusions only with content-grounded reasons, retain pending rows
for unresolved content, census the program frontier, and add a producer that
recomputes the ledger and root counts. [R7] [R8] [R11] [R31] The two deferred
final definitions in section 3121 are known pending items unless the program's
observed-fact frontier is reviewed and accepted as its explicit boundary. [R6]

### Executable

The new program composes, compiles, and passes its boundary integration tests
against the pinned tooling. [R29] The repository artifact builder can compose
and compile every discovered program and stamp provenance, but those local or
build-time operations do not themselves produce a public execution receipt.
[R15] The remaining work is to publish a content-addressed artifact, identify a
compatible released engine, execute the golden case through that exact pair,
commit the receipt, and add a computed verifier. The current certificate
producer has no computed closed or executable premise, so certification remains
unavailable even though the local program runs. [R10]

## Reproduction command for the counts

The count used this shape at each named corpus commit; it intentionally searches
all statute inventories and never filters by ingest filename:

```sh
git ls-tree -r --name-only <ref> -- data/corpus/inventory/us \
  | while IFS= read -r inventory_file; do
      git show "<ref>:${inventory_file}"
    done \
  | jq -r '.items[]?.citation_path // empty' \
  | awk '<exact 3101/3121 descendants or exact SSA-guidance-root predicate>' \
  | sort -u
```

## Evidence files read

- **R1** — `rulespec-us/programs/us/payroll/oasdi-wage-tax/fy-2026.yaml:1-14`.
- **R2** — `rulespec-us/us/statutes/26/3101/a.yaml:27-56`.
- **R3** — `rulespec-us/us/statutes/26/3121/a/1.yaml:49-110`.
- **R4** — `axiom-compose@fabe0b3/src/axiom_compose/core.py:95-128,345-370`.
- **R5** — `rulespec-us/us/statutes/26/3101/c.yaml:8-57`.
- **R6** — `rulespec-us/us/statutes/26/3121/a.yaml:3-21` and
  `rulespec-us/us/statutes/26/3121/b.yaml:8-20`.
- **R7** — `rulespec-us/.axiom/toolchain.toml:1-8`.
- **R8** —
  `axiom-corpus@db127955/data/corpus/inventory/us/statute/2026-07-24-1401-coordination-repair-title-26.json:294-488`,
  plus every statute inventory at `bf97b17…` and `db127955…` enumerated by the
  reproduction command above.
- **R9** —
  `_closure-sprint/briefs/h1-payroll-program.md:11-18`.
- **R10** —
  `axiom-oracles evidence-validator@336b0a1/scripts/certify.py:57-115,553-570,574-699,703-782`.
- **R11** — `_closure-sprint/data/closure-doc.md:102-144`.
- **R12** —
  `axiom-oracles@9b889a2/axiom_oracles/bridges/mappings/us.yaml:8314-8369`.
- **R13** —
  `rulespec-us/us/statutes/26/3101/a.test.yaml:1-26`,
  `3101/b/1.test.yaml:1-20`, `3101/b/2.test.yaml:1-87`, and
  `3121/a/1.test.yaml:1-128`.
- **R14** — `axiom-corpus@bf97b17/data/corpus/inventory/us/statute/2026-07-13-recovery-r2026-07-15-self-contained-r2026-07-17-dedup.json`
  (all exact descendants of `us/statute/26/3121`).
- **R15** — `rulespec-us/tools/build_program_artifacts.py:1-21,60-88,227-248`.
- **R16** — `axiom-compose/tests/test_real_program_oasdi.py:13-42,110-154`.
- **R17** —
  `rulespec-us/us/policies/ssa/contribution-and-benefit-base/2026.yaml:5-12,97-140`
  and its companion `2026.test.yaml:1-10`.
- **R18** —
  `policyengine-us/policyengine_us/variables/gov/irs/tax/payroll/social_security/employee_social_security_tax.py:4-14`,
  `.../social_security/taxable_earnings_for_social_security.py:4-13`, and
  `.../medicare/employee_medicare_tax.py:4-14`.
- **R19** —
  `policyengine-us/policyengine_us/variables/gov/irs/tax/federal_income/additional_medicare_tax.py:4-19`.
- **R20** — `rulespec-us/us/statutes/26/3101.yaml:8-13`.
- **R21** —
  `axiom-corpus/src/axiom_corpus/corpus/models.py:32-66` and
  `axiom-corpus/src/axiom_corpus/corpus/io.py:11-14`.
- **R22** —
  `axiom-corpus/data/corpus/sources/us/statute/2026-07-13-recovery-r2026-07-15-self-contained-r2026-07-17-dedup/provenance/usc26-section-3121.xml.json:2-7`.
- **R23** — `axiom-corpus/src/axiom_corpus/corpus/coverage.py:34-42,60-81`.
- **R24** —
  `axiom-corpus/.axiom/ingest-manifests/us/statute/2026-05-10-tax-sections-r2026-07-15-self-contained-r2026-07-15-self-contained.json:30-39`.
- **R25** —
  `axiom-corpus/.axiom/ingest-manifests/us/statute/2026-07-19-rulespec-title-26-consolidated.json:34-43`.
- **R26** —
  `axiom-corpus/.axiom/ingest-manifests/us/statute/2026-07-13-recovery-r2026-07-15-self-contained-r2026-07-17-dedup.json:184-185,616-617,886-895`.
- **R27** —
  `rulespec-us/programs/us/payroll/employee-fica-tax/fy-2026.yaml:1-18` and
  `rulespec-us/us/policies/payroll/employee_fica_tax_pipeline.yaml:1-240`.
- **R28** —
  `rulespec-us/us/policies/payroll/employee_fica_tax_pipeline.test.yaml:1-130`
  and `rulespec-us/us/payroll/employee-fica-tax-golden.md:1-78`.
- **R29** — `rulespec-us/us/payroll/PROGRESS.md`.
- **R30** —
  `axiom-oracles@5588560c/axiom_oracles/bridges/mappings/us.yaml:28436-28474`.
- **R31** —
  `axiom-corpus@bf97b17` and `axiom-corpus@db127955`,
  `data/corpus/inventory/us/guidance/2026-05-17-ssa-automatic-determinations-2026.json:15-24`.
