# Illinois SCRETD closure repair report

- Report date: 2026-07-27
- Program: `us-il/scretd`
- Branch: `closure/scretd`
- Target year: tax year 2026

## Outcome

The material graph defect is repaired in the committed RuleSpec source:
§ 3 now imports § 2's
`household_income_no_greater_than_maximum` judgment and requires it
unconditionally in `application_requirements_satisfied`. The assessment-freeze
shortcut can still substitute for the age and three-year-residency application
items, but it cannot bypass the income ceiling.

The five-case diagnostic grid moved from **4/5 (80%)** before the repair to
**5/5 (100%)** after it. Its repaired vector is:

```text
[0, 7499, 7500, 0, 7500]
```

In particular, the tax-year-2026 case with household income of **$77,001**
now produces a deferral of **$0**, not $7,500.

The after-rate is the pinned RuleSpec rerun against the prior assessment's
enumerated reference vector. This sprint did not create a fresh exact-pin
PolicyEngine cross-engine receipt; the baseline PolicyEngine probe used
PolicyEngine-US 1.779.4 after source-equivalence review against the intended
1.767.3 version.

This semantic result is not yet a signed deliverable. The authorized
`sign-applied-files` dry run selected exactly the replacement manifests for
§§ 2 and 3, but actual signing is fail-closed: the configured `agent-secret`
store reports a missing unlock password and
`AXIOM_ENCODE_APPLY_SIGNING_KEY` is absent. No signature or manifest was
forged, copied, or bypassed.

## Current-law result

The corpus and modules are current for the four requested
computation-bearing values and incorporate Public Act 104-452, effective
December 12, 2025:

| Item | Current law | Encoding |
| --- | --- | --- |
| Maximum household income | $75,000 for TY2025; $77,000 for TY2026; $79,000 for TY2027+ | Matches |
| Equity-interest ceiling | 80% | Matches |
| Annual deferral cap | $5,000 for TY2012–2021; $7,500 for TY2022+ | Matches |
| Interest rate | 6% before TY2023; 3% for TY2023+ | Matches |

The paired § 2 and § 3 corpus records have
`expression_date: 2026-06-26` and contain the Public Act 104-452 changes.
Thus the December 2025 eligibility expansion is not missing from the
computation.

**The act corpus is nevertheless technically stale for current § 3.**
Public Act 104-468, effective June 16, 2026, changed the priority of the
deferred-tax lien. The June 26 corpus row still ends with Public Act 104-452
and omits that amendment; the ILGA compiled page also had not incorporated
it at review time. The amendment does not change eligibility, income, the
deferral amount, the cap, the 80% ceiling, or the interest rate. The current
lien-priority output is therefore explicitly deferred rather than inferred
from stale text.

Full source comparison and official links are in
`bulk/us-il-scretd-current-law-review.md`.

## Dependency frontier

At the parallel corpus job's final commit
`5e074e9cc10035be60d2ff29e40bfa126cc0839a`, an exact scan of all 730
inventory files and 143,811 `.items[]` records found zero matches for each of:

- `us-il/statute/320/25/3.05`
- `us-il/statute/320/25/3.05a`
- `us-il/statute/320/25/3.07`
- `us-il/statute/35/200/15-172`
- `us-il/statute/210/45/1-113`

The parallel job repaired the retired ILGA full-text route, but authentic
source bytes were unavailable and it correctly generated no legal artifacts.
Accordingly:

- § 2 now names the three absent household-income-definition paths and the
  absent licensed-facility path in `deferred_outputs`; and
- § 3 names the absent assessment-freeze definition and the newer
  lien-priority source in `deferred_outputs`.

The modules consume the facts that §§ 2 and 3 themselves require as typed
boundary inputs. They do not invent the cross-referenced definitions.

## Companion coverage

Coverage increased from 10 to **23** companion cases: 6 for § 2 and 17 for
§ 3. The committed suite covers:

- the five-case root grid;
- 2026 income below, exactly at, and above $77,000;
- deferral below, exactly at, and above the $7,500 annual cap;
- the $5,000-to-$7,500 cap version break;
- the 6%-to-3% interest-rate version break;
- positive capacity, exact 80% exhaustion, and above-80% equity cases;
- age failure without the assessment-freeze shortcut;
- three-year-residency failure without the shortcut;
- successful use of the shortcut for age and residency; and
- failure of the shortcut to override excess household income.

The current encoding accepts the age-by-June-1 and three-year-residency
conditions as Boolean legal judgments, so the companion suite can exercise
their true/false statutory sides but not reconstruct day-level age or
residency duration from dates.

This clears the requested 15-case floor and materially improves boundary
coverage. It does not, by count alone, establish a complete exercise verdict:
the suite still lacks a committed provision-derived case-to-obligation set
cover for every application and agreement gate and every independent minimum
operand.

An independent coverage audit identified a minimum remaining set of 11 causal
cases before such a set cover could be claimed: isolated failures for the
correct-collector, prescribed-form, qualifying-property-through-root,
scope/amount, and valuation-or-appraisal gates; isolated failures for all
three agreement gates; uniquely binding payable-tax and revolving-fund
operands; and a low-equity interaction in which the annual cap independently
binds. The obligation map itself would also need to be committed.

## Closure universe

The explicit denominator is the eight sections of 320 ILCS 30. Chapter and
act inventory containers are not provisions and are excluded from the
denominator.

| Status | Count |
| --- | ---: |
| Encoded at full-section granularity | 0 |
| Excluded with closed-taxonomy reason | 5 |
| Pending | 3 |
| Total | 8 |

The five exclusions comprise three `no_household_computation` sections and
two `procedural_no_point_in_time_effect` sections. Sections 2 and 3 remain
pending because their partial encodings have explicit deferred outputs.
Section 4 remains pending because its filing fee becomes part of deferred
taxes due and can affect later 80%-capacity calculations. The authoritative
ledger is `bulk/us-il-scretd-closure-universe.yaml`.

## Validation

Pinned toolchain:

- `axiom-encode`
  `3869d66d009f52258be35901edbef370e65a399c`
  (reported version 0.2.1200);
- `axiom-rules-engine`
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`; and
- corpus pin
  `db12795577c5809009168982cf8a72fb58440620`.

Results:

- YAML parsing and diff checks: passed.
- Full pinned CI validation of §§ 2 and 3 in a canonical checkout: passed.
- Proof validation: § 2 passed 11 atoms; § 3 passed 15 atoms.
- Companion execution: 2 files, 23 cases, 2 compiled programs, 0 failures.
- Independent read-only review found one mixed-entity expected-output issue in
  nine new § 3 cases; the redundant intermediate assertions were removed, and
  all validation above passed again.
- `sign-applied-files --dry-run`: selected 2 manifests covering the 2 modules
  and changed § 3 companion file.
- `guard-generated`: expected failure on those 3 protected changed files
  because the replacement signatures could not be created.
- Focused repository suite: 14 passed and 1 failed; the sole failure was
  `test_encoded_modules_match_their_manifests` for two intentionally
  fail-closed stale signed manifests covering three changed protected files.

The branch must not merge until an authorized lane signs the replacement
manifests and both `guard-generated` and the 15-test repository suite are
green.

## Verdicts

| Verdict | Honest status after this work |
| --- | --- |
| Provision-rooted | **Yes.** Unchanged and supported by the § 3 source/proof root. |
| Conformant | **Not yet as a certification verdict.** The known bounded overlap is semantically repaired and now 5/5, so bounded conformance is honestly reachable after signed application and a live pinned grid receipt. Full-surface conformance still lacks a commensurate reference for constraints PolicyEngine does not model. |
| Exercised | **No, but materially closer.** The requested boundary floor is exceeded at 23 passing cases; a reviewed case-to-obligation set cover is still missing. |
| Closed | **No.** The act remains 0 encoded / 5 excluded / 3 pending, with all five outgoing definitions absent. |
| Executable | **No.** Local pinned compilation is green, but there is no published compiled artifact × released-engine receipt bound to this repaired source. |

The only verdict already green remains provision-rooted. The repair makes the
bounded five-case conformance claim technically reachable; it does not justify
promoting any of the four previously failing program-level verdicts while the
signature, oracle-receipt, closure, exercise-census, and released-artifact
requirements remain open.

## Delivery state

Changed implementation artifacts:

- `us-il/statutes/320/30/2.yaml`
- `us-il/statutes/320/30/3.yaml`
- `us-il/statutes/320/30/3.test.yaml`

No file under `programs/`, no toolchain pin, no CI workflow, no CODEOWNERS
file, and no `oracle-coverage-pending.yaml` entry was changed.

`closure/scretd` was pushed successfully through the implementation and main
report commit `b9a091d30`. The final delivery-status update and a clean merge
of the newly advanced `origin/main` remain local because subsequent push
attempts could not resolve `github.com`; the local branch is now 0 commits
behind that upstream ref. No draft PR was opened: `gh auth status` reports
that the active `MaxGhenis` token is invalid. The GitHub connector was offered
as a fallback but was not installed, and a signed-in browser fallback was not
used without explicit approval.

Remaining mechanical unblock:

1. unlock the authorized secret store or provide the signing key through the
   approved environment;
2. run `sign-applied-files` with `--manual-exception repair` against this
   committed branch;
3. commit the two generated manifests;
4. rerun `guard-generated`, full validation, companion tests, and the focused
   repository suite; and
5. restore GitHub CLI/connector authentication and open a draft PR referencing
   rulespec-us#1135.
