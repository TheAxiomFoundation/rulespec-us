# Employee FICA payroll program: final report

Date: 2026-07-27

## Bottom line

The new `us/payroll/employee-fica-tax` program is **not certifiable yet**. It is
now a credible narrow-profile implementation candidate: the program composes
and compiles with the pinned tooling, all 11 companion cases pass, and exact
PolicyEngine mappings exist for its three outputs. None of that substitutes for
the computed `conformant`, `exercised`, `closed`, or `executable` evidence
required by the certificate producer.

The critical path is:

1. align the corpus pin and classify the full declared-root universe of 143
   citation paths at the adequate cached snapshot: nine section 3101 paths,
   133 section 3121 paths, and one SSA guidance path;
2. review and accept the explicit observed-wage frontier and narrow
   one-employer/no-section-3101(c)-exemption domain, or encode the remaining
   section 3121 and section 3101(c) integration needed for a general program;
3. after the launch freeze, create and register frozen per-case comparison and
   exercise evidence; and
4. publish the compiled artifact and compatible engine, record execution of
   the golden case, and add computed closure and executable verifiers.

The complete verdict-by-verdict analysis and file citations are in
`us/payroll/h1-payroll-assessment.md`.

## What was built

### RuleSpec repository

- Added the sibling program
  `programs/us/payroll/employee-fica-tax/fy-2026.yaml`, leaving every existing
  SNAP program and the existing OASDI program unchanged.
- Added
  `us/policies/payroll/employee_fica_tax_pipeline.yaml`, which publishes:
  - `employee_oasdi_wage_tax` on `Person`, using the 6.2 percent rate and the
    $184,500 tax-year-2026 contribution-and-benefit base;
  - `employee_hospital_insurance_wage_tax` on `Person`, using the uncapped
    1.45 percent rate; and
  - `employee_additional_medicare_wage_tax` on `TaxUnit`, using the 0.9 percent
    rate above the filing-status threshold.
- Defined explicit completed wage facts for pre-cap OASDI wages, Person
  Medicare wages, and TaxUnit Medicare wages. The program fails closed outside
  its declared one-employer or resolved-successor, complete-wage,
  no-section-3101(c)-exemption profile.
- Added 11 companion cases below, at, and above the OASDI base; at and above
  the Additional Medicare threshold; and outside the section 3101(c) supported
  domain.
- Added `us/payroll/employee-fica-tax-golden.md`, a $300,000 single-filer case
  deriving $11,439 OASDI, $4,350 ordinary Medicare, and $900 Additional
  Medicare tax line by line.
- Added and maintained `us/payroll/PROGRESS.md`.

### Oracle repository

The local `axiom-oracles` branch `payroll/employee-fica-mappings` contains:

- `0544f2028718fa503ebad2aa73fd6c3e19e83f05` — three direct program-output
  mappings to `employee_social_security_tax`, `employee_medicare_tax`, and
  `additional_medicare_tax`; and
- `5588560c3d8e80d0d0968b34fd93534395d4ed98` — explicit comparison contracts
  requiring the RuleSpec wage facts to equal PolicyEngine's corresponding
  `payroll_tax_gross_wages` amounts, plus zero taxable self-employment income
  for Additional Medicare Tax.

No comparison suite was run, and no comparison or oracle report was changed or
regenerated.

## Validation performed

- Proof validation passed with 13 proof atoms and no missing money atoms.
- The companion runner passed one file and all 11 cases against
  `axiom-rules-engine@ffd8213271947b0189a9dd61a055c1e0e78908a0`.
- The exact program-artifact composer pin
  `axiom-compose@fabe0b3b3fd6e90d3e8f075516f9b668f524f711` composed the program.
- The pinned engine compiled the composition to a version-2 artifact with 17
  derived rules; each of the three published output names is present exactly
  once.
- The relevant repository layout and program-spec tests passed: 12 tests.
- The PolicyEngine mapping registry loaded and resolved all three exact program
  mappings to the intended variables.
- `git diff --check`, YAML parsing, and forbidden-path review passed.
- Two independent reviews and their follow-up checks are clean after correcting
  the total closure universe and tightening the mapping wage contracts.

## Known boundaries and honest deferrals

- **Conformant:** no registered payroll reference suite, frozen report identity,
  or clean per-case certificate evidence exists. The launch freeze prohibited
  creating it here.
- **Exercised:** the 11 companions are implementation tests, not the certificate
  census, audited bridge, and report-bound per-case evidence.
- **Closed:** the current corpus pin exposes 135 paths under the three declared
  roots, while the adequate cached snapshot exposes 143. The required
  content-level ledger does not exist; 133 section 3121 rows require
  classification in either snapshot.
- **Executable:** local pinned compilation passes, but there is no published
  content-addressed artifact/engine pair, golden execution receipt, or computed
  executable-verdict producer.
- The observed-wage frontier avoids inventing every section 3121 exclusion but
  narrows the supported domain. A general program still needs the final section
  3121 wage/employment chain and Person/TaxUnit treatment of section 3101(c).
- Whole-module composition retains the legacy uncapped
  `us:statutes/26/3101/a#oasdi_wage_tax` internally. Consumers must bind the
  exact three program output IDs rather than treating every compiled derived
  rule as a published output.
- Generic oracle bridge discovery does not yet cover this four-level payroll
  program path, and the current US bridge does not execute TaxUnit mappings.
  Those are toolchain changes and were deliberately deferred.

Declaring these deferrals is the correct outcome; this branch does not claim a
certificate it cannot reproduce.

## Publication and output delivery

- Copying the assessment and final report to
  `/Users/maxghenis/TheAxiomFoundation/_closure-sprint/out/`, including the
  expected `h1-payroll-assessment.md` and `h1-payroll.result.md` paths, failed
  with `Operation not permitted` because that directory is outside the writable
  sandbox.
- Fetching and pushing both repositories failed with
  `Could not resolve host: github.com`.
- No draft PR was opened because neither branch could be pushed.

The reviewed work remains committed locally on:

- `rulespec-us`: `closure/payroll-3101`
- `axiom-oracles`: `payroll/employee-fica-mappings`
