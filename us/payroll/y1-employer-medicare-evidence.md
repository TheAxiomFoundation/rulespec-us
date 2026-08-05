# Employer Medicare tax certification evidence

**Decision status:** evidence assembly only; **4 of 5 criteria hold**. This is
not a certification or an attestation. `launch-readiness/certified-nodes.yaml`
was not changed. The strict `executable` criterion remains false because only
a local, unpublished artifact was available.

**Candidate scope:** only
`us:statutes/26/3111/b#hospital_insurance_employer_tax`, the gross employer
hospital-insurance excise tax imposed by 26 USC 3111(b) on completed aggregate
Medicare-taxable wages. It does not certify employer identity, section 3121
wage or employment classification, the section 3111(c) international-agreement
exemption, section 3111(f) credits, or net employer payroll-tax liability.

The block below copies the entry shape used by
`ops@125791409df96920f33487e4bd8ee289af344b3a:launch-readiness/certified-nodes.yaml`.
It is a review template, not an entry ready to paste: `attested_by` is a
placeholder and `criteria.executable.holds` is false.

```yaml
- node: us:statutes/26/3111/b#hospital_insurance_employer_tax
  label: Employer Medicare payroll tax
  provision: 26 USC 3111(b)
  corpus_citation_path: us/statute/26/3111
  mode: attested
  attested_by: <name>
  attested_at: 2026-07-28
  pinned:
    rulespec_us: 3a1694e9d94f7e9684ffbff4abd39b262c424227
    corpus: 43636a86e8e0f3c4bfdbefffd5ef4289921dc1b9
    engine: v0.1.1
    artifact: sha256:4edcb5e31d4af139c6347a9e275bad92c4bf0c15fde91465617007b0236f4cbc
  criteria:
    provision_rooted:
      holds: true
      evidence: "us/payroll/y1-employer-medicare-evidence.md#1-provision_rooted"
    conformant:
      holds: true
      evidence: "us/payroll/y1-employer-medicare-evidence.md#2-conformant"
    exercised:
      holds: true
      evidence: "us/payroll/y1-employer-medicare-evidence.md#3-exercised"
    closed:
      holds: true
      evidence: "us/payroll/y1-employer-medicare-evidence.md#4-closed"
    executable:
      holds: false
      evidence: "us/payroll/y1-employer-medicare-evidence.md#5-executable; local load and value pass, published-artifact stranger path blocked"
```

The RuleSpec pin is the implementation-and-fixture commit, not this narrative
evidence commit. Its tree is
`6b6f41cd5c30f63ae41e98ec935103c829a11a7a`. The artifact hash pins the
byte-reproducible **local probe artifact**; it is not a publication claim.

## Provenance repair decision

**Choice: produce native leaf rows through the corpus pipeline.**

The section-plus-span fallback was rejected because it would have preserved
false raw provenance. The two historical section-only records have the correct
5,071-character section 3111 body, but their `source_url` selects section 45A
and their retained raw object is literally titled `26 USC 45A: Indian
employment credit`. A span would make a lookup syntactically convenient
without correcting either object.

The standard `extract-usc` pipeline instead re-indexed the already-retained
official Title 26 USLM file; it did not fetch or author text. That file has
SHA-256
`d2f67de8052e9e2a96e3da34d84cbe2d677bc1b5840e8fa0e79cbfa7e9b28621`
and natively identifies `/us/usc/t26/s3111/a`, `/b`, and the remaining
descendants. The extraction produced 24/24 complete rows and 22
`machine_asserted` descendant anchors. Consolidation with the former RuleSpec
Title 26 scope produced 114/114 complete unique rows. The immutable successor
selector `us-rulespec-2026-07-27-3111-provenance` replaces only the old
consolidated Title 26 carrier.

Corpus implementation:

- commit `43636a86e8e0f3c4bfdbefffd5ef4289921dc1b9`;
- tree `e99b8631c661af4ee3d85f8a41d7227aaa2e93a7`; and
- release-selector SHA-256
  `d80fb90e403f8eb209e0ea1af371aabe8431029ff5bb6e0fff385648d130de57`.

The successor release validates with zero errors. Its 541 warnings are exactly
the inherited warnings in its predecessor, not new section 3111 findings. The
focused release-quality suite passed 17/17.

The signed a/b RuleSpec modules retain their formal section-root proof paths.
Leaf production itself resolves the audited `/a` and `/b` legal identifiers,
so changing those paths—and invalidating their signed encoding
manifests—was neither necessary nor honest. The expanded b fixture is new and
is not claimed to be covered by the older apply-manifest signature.

The corpus signing key was unavailable, so no ingest signature was fabricated.
The corpus commit and selector are local evidence pins pending maintainer
signing, review, and merge. No publication, load, or release activation was
performed.

## 1. `provision_rooted`

**Verdict: holds at the pinned local corpus commit.**

The defining module is `us/statutes/26/3111/b.yaml`:

- Git blob `f0376d33b190d1acab2c479d409108d4444a8dfa`;
- file SHA-256
  `02cb26afb163a49113d15e8cea6adc2f2c8e82e67a2dc46b905950d39c2f198e`;
- formal corpus path `us/statute/26/3111`;
- legal source `26 USC 3111(b)`;
- output entity/type/period/unit `Employer` / `Money` / `Year` / `USD`; and
- formula `wages * hospital_insurance_employer_tax_rate`, with rate `0.0145`.

The selected corpus successor contains exactly one corrected section row and
one exact subsection-b row:

| Field | Section 3111 | Section 3111(b) |
|---|---|---|
| Citation path | `us/statute/26/3111` | `us/statute/26/3111/b` |
| Provision ID | `262b1f9e-a5f1-5ae4-8461-f4660890b0be` | `16d804f2-9bb1-5f40-87bf-a485c197901f` |
| Body length | 5,071 | 314 |
| Body SHA-256 | `d997d5ff5be0f67762689cbc42728cb142a29dd7724e829caed1ec05d3dcd28c` | `3ef83f4284fce89cb4fb71410a22fc5cab6905d45ac0310bdb9ecf169d4d644b` |
| Source ID | `/us/usc/t26/s3111` | `/us/usc/t26/s3111/b` |
| Source/expression date | 2026-07-12 | 2026-07-12 |

Both use the official section 3111 URL:

```text
https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section3111&num=0&edition=prelim
```

The exact leaf's asserted anchor is active and `machine_asserted`, spans
characters `[332, 669)` of the selected parent body, and binds to the same
parent provision ID and parent-body hash shown above.

The rate excerpt `equal to 1.45 percent` is unique in both the formal section
body and the exact leaf. The wage/employment excerpt occurs twice in the parent
because subsections (a) and (b) use parallel language, but once in the exact
leaf. The formal proof path therefore remains broader than ideal; the rule's
`source: 26 USC 3111(b)` and the now-resolving exact legal leaf remove the
legal-node ambiguity without rewriting a signed module.

## 2. `conformant`

**Verdict: holds for the stated aggregate-value boundary.**

The registered, non-population case grid is committed locally at
`axiom-oracles@29bef862b7a12c4e3012e00ae88d0d2ed1543797`, tree
`664fce4455049f0f6ef67848cf5d71d4e1fab040`. It adds:

- `comparisons/us-employer-medicare-grid.yaml`;
- the registered generator policy and aggregate adapter in
  `scripts/generate_federal_tax_liability.py`;
- focused source/entity/fixture/carrier tests; and
- the regenerated comparison affected map.

The stack is Python 3.13, `policyengine==4.18.9`,
`policyengine-us==1.767.3`, and `policyengine-core==3.30.3`. The reviewed
PolicyEngine-US source commit is
`49d19b239a593dbac8920ac6fd80cfe33372343a`.

### Honest Employer aggregate seam

PolicyEngine has no legal `Employer` entity. Its dedicated
`employer_total_medicare_tax` variable is technically Person-grain, but its
documentation expressly defines employer-level Medicare liability from
aggregate payroll wages. It computes the employer rate times
`employer_total_payroll_tax_gross_wages`.

The adapter therefore creates exactly one PolicyEngine Person as a transparent
storage carrier for one externally supplied Employer aggregate. It records:

```yaml
entity: Person
count: 1
role: Transparent carrier for one aggregate employer wage input; not a legal Employer and not a worker allocation.
is_legal_employer: false
```

The primary and only PolicyEngine query is `employer_total_medicare_tax`.
Ordinary per-worker `employer_medicare_tax` is not used. The adapter separately
verifies that the RuleSpec output remains entity `Employer`, that the fixture
has exactly one RuleSpec wage input, and that the 2026 PolicyEngine employer
rate is exactly `0.0145`.

Relevant PolicyEngine source pins:

| Surface | Git blob | File SHA-256 |
|---|---|---|
| aggregate employer Medicare formula | `9441a3068f77e0d928522d924a9faaf4d9b6b80e` | `cba1f93aa7179fe749b2cf54bfb12579bde073313eaee88184137566b9b1f331` |
| aggregate employer input file | `4aff703de142254a4b1cac2cc84b205590111c60` | `146935bd68e28d8dfad01ea13ded5ee7498b0e615f507cbb78ce5040801729af` |
| employer Medicare rate parameter | `4431543357edf70a68cbdb55477bae5756d9548e` | `96541f1c0f88a5d561df95c3cb3604d4b8a80940078a6f5707e1b5ee14860955` |

This validates only `1.45% × completed aggregate Medicare-taxable wages`. It
does not validate employer identity, worker/employer relationships, wage
classification, exemptions, or downstream credits.

### Receipt

Exact run:

```sh
PYTHONPATH=/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/y1-employer-medicare-axiom-oracles \
/Users/maxghenis/.cache/uv/archive-v0/KHsnHQNgjRDE2PQFz-DN-/bin/python \
  scripts/generate_federal_tax_liability.py \
  --policy employer_medicare_tax \
  --rulespec-root /private/tmp/y1-employer-medicare-oracle/rulespec-us \
  --output /private/tmp/y1-employer-medicare-oracle/us-employer-medicare-grid.json
```

The RuleSpec checkout was detached at the pinned implementation commit and
tree. The 7,279-byte deterministic receipt has SHA-256
`d689f112b9c87573c33a66d125a83cc89ea6507a9f96690d5f55bc38ce347c42`.

| Case | Diagnostic partition | Axiom | PolicyEngine | Axiom − PE | Result |
|---|---|---:|---:|---:|---|
| zero | `[0]` | 0 | 0 | 0 | match |
| one dollar | `[1]` | 0.0145 | 0.014499999582767487 | 0.000000000417232514 | match |
| ordinary | `[100000]` | 1450 | 1450 | 0 | match |
| OASDI-base diagnostic | `[184500]` | 2675.25 | 2675.25 | 0 | match |
| one dollar above base | `[184501]` | 2675.2645 | 2675.264404296875 | 0.00009570312522555469 | match |
| high, unsplit | `[300000]` | 4350 | 4350 | 0 | match |
| high, equal split | `[150000, 150000]` | 4350 | 4350 | 0 | match |
| high, uneven split | `[1, 2, 3, 299994]` | 4350 | 4350 | 0 | match |

The receipt preserves raw floats and applies no pre-rounding. Every difference
is within the declared `$0.01` absolute tolerance.

```yaml
population: case-grid
comparison_count: 8
match_count: 8
mismatch_count: 0
error_count: 0
unexplained_mismatch_count: 0  # derived from the empty mismatch list
axiom_attributed_mismatch_count: 0  # derived from the empty mismatch list
match_rate_percent: 100
```

The legacy Person-level mapping and population receipts are not evidence for
this criterion and were not used. Focused oracle tests passed 53/53, the
affected map and vacuous gate are current, and Ruff passed.

## 3. `exercised`

**Verdict: holds, with an explicitly aggregate census.**

Section 3111(b) is a one-input flat-rate rule with no employer threshold or
wage-base cap. The companion fixture has eight cases but six unique scalar
wage values:

| Dimension | Values | Purpose |
|---|---|---|
| completed aggregate Medicare wages | `$0`, `$1`, `$100,000`, `$184,500`, `$184,501`, `$300,000` | zero and low-value behavior, ordinary wages, anti-OASDI-cap seam, and high wages |
| diagnostic worker partitions at `$300,000` | `[300000]`, `[150000,150000]`, `[1,2,3,299994]` | validates the adapter's external aggregation contract; not projected as PE entities |
| employer Medicare rate | `0.0145` | constant, verified independently in both systems |
| time | tax year 2026 | constant |

The three `$300,000` RuleSpec fixtures are identical at the RuleSpec surface.
Their distinct partitions exist only in oracle case metadata, are required to
sum exactly to the supplied aggregate, and never become PolicyEngine people or
worker allocations. That is deliberate: the honest seam is the dedicated
aggregate variable, not an invented Employer membership relation.

Every bridged or constant dimension is declared:

| Dimension | Treatment |
|---|---|
| wage surface | **Bridged:** one completed Employer aggregate maps to RuleSpec `#input.wages` and PE `employer_total_payroll_tax_gross_wages`. |
| RuleSpec entity | **Constant and validated:** one legal `Employer`. |
| PE carrier | **Technical scaffold:** one `Person`, explicitly not the Employer and not a worker allocation. |
| employer identity/grouping | **Boundary fact:** externally asserted; not validated by PolicyEngine. |
| section 3121 wage/employment classification | **Boundary fact:** already reflected in completed Medicare-taxable wages. |
| section 3111(c) international-agreement relief | **Boundary fact:** cases supply wages after any applicable exemption; no agreement flag is evaluated. |
| section 3111(f) credits | **Outside scope:** downstream credits against the gross tax, not inputs to the amount imposed by subsection (b). |
| OASDI wage base | **Not an input:** `$184,500/$184,501` is an anti-cap wiring diagnostic, not a section 3111(b) legal boundary. |
| ordinary per-worker PE Medicare tax | **Not queried:** it is the wrong legal entity surface for this candidate. |
| employee and Additional Medicare taxes | **Outside scope:** sections 3101(b)(1) and (2) are not compared. |

The released-tag local artifact also passed all eight fixtures exactly.

## 4. `closed`

**Verdict: holds for the same repository/source-side meaning used by PR
#1149.**

The honest declared root is the module's formal
`us/statute/26/3111`, not a cherry-picked one-row subsection-b frontier. The
selected consolidated scope has 23 delimiter-safe unique paths: the section
and 22 descendants.

```yaml
roots:
  - us/statute/26/3111
frontier:
  unique_provisions: 23
summary:
  encoded: 22
  excluded: 1
  pending: 0
```

Closure ledger:

| Provision(s) | Status | Mapping |
|---|---|---|
| `/3111` | encoded collectively | `a.yaml`, `b.yaml`, `c.yaml`, `e.yaml`, `f.yaml` |
| `/3111/a` | encoded | `a.yaml` |
| `/3111/b` | encoded | `b.yaml` |
| `/3111/c` | encoded | `c.yaml` |
| `/3111/d` | excluded | repealed; `d.yaml` records no operative consequence |
| `/3111/e`, `/e/1`, `/e/2`, `/e/3`, `/e/3/A-C`, `/e/4`, `/e/5`, `/e/5/A-B` | encoded | `e.yaml` |
| `/3111/f`, `/f/1`, `/f/1/A-B`, `/f/2-4` | encoded | `f.yaml` |

This is source-side repository closure only. The aggregate
`us/statutes/26/3111.yaml` module is explicitly `entity_not_supported` and
defers composition of subsection (c) exemptions and subsection (e)/(f)
credits into effective liability. If a reviewer interprets `closed` as
executable composed-liability closure, this criterion **fails** and must be
changed to false. It holds here only under PR #1149's narrower source-side
criterion: every provision is encoded or terminally excluded, with zero
pending source provisions.

## 5. `executable`

**Verdict: does not hold.**

The format and arithmetic probes pass, but the literal criterion requires a
**published** artifact executed with the **released binary** through a
stranger-reproducible path. Only a locally compiled, unpublished artifact was
available.

The clean annotated engine tag `v0.1.1` resolves to tag object
`bdd225c4576ad51c127a10a6516675b09b2fae8d` and peeled commit
`e3e2da83222463d9b68b0681c00820e9d412c011`. The local released-tag binary:

```yaml
version: axiom-rules-engine 0.1.1
sha256: c1ea7e6c7984df06beef964e4923fa00ca3a4a1aa6e213e561a026ed558c452f
```

Exact compile:

```sh
/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/engine-v0.1.1/target/release/axiom-rules-engine \
  compile \
  --program /private/tmp/y1-employer-medicare-final-engine.ajAxZu/rulespec-us-3a1694e9/us/statutes/26/3111/b.yaml \
  --output /private/tmp/y1-employer-medicare-final-engine.ajAxZu/us-employer-medicare.compiled.v0.1.1.json
```

Receipt:

```yaml
engine_version: 0.1.1
artifact_format_version: 2
derived_output_count: 1
derived_output: us:statutes/26/3111/b#hospital_insurance_employer_tax
artifact_sha256: 4edcb5e31d4af139c6347a9e275bad92c4bf0c15fde91465617007b0236f4cbc
deterministic_recompile_sha256: 4edcb5e31d4af139c6347a9e275bad92c4bf0c15fde91465617007b0236f4cbc
```

The golden request supplies one annual legal-ID input on Employer
`employer:1`:

```text
us:statutes/26/3111/b#input.wages = 100000
```

The released-tag local binary exits 0 in `explain` mode and returns decimal
USD `1450`, traced to `26 USC 3111(b)`. All eight companion cases also pass
exactly.

### Hand-checkable golden case

For completed aggregate Medicare-taxable wages of **$100,000**:

```text
$100,000 × 0.0145 = $1,450
```

### Blocking findings

1. No employer-Medicare program spec exists in the published-artifact
   pipeline. Repository policy publishes compiled artifacts only from landed
   program specs and never commits them.
2. The compiled artifact above is local and unpublished.
3. A fresh anonymous official v0.1.1 binary download could not be attested
   because the GitHub API was unreachable; the probe used a local build from
   the exact released source tag.
4. Therefore there is no honest official released-binary plus published
   artifact stranger path.

Until that path exists and reproduces the golden case,
`executable.holds` remains false and this node must not be added to
`certified-nodes.yaml`.

## Validation summary

```text
RuleSpec repository layout + reverse index: 15 passed
RuleSpec encoding-manifest guard + reverse index: 9 passed, 1 inherited warning
Corpus release-quality tests: 17 passed
Corpus successor release: 0 errors; 541 predecessor-identical warnings
Oracle focused tests: 53 passed
Oracle affected-map check: 167 suites / 176 edges, OK
Oracle vacuous-gate check: OK
Oracle Ruff: all checks passed
Oracle live grid: 8/8 matches, zero mismatches/errors
Released-tag local engine: 8/8 fixtures exact
```
