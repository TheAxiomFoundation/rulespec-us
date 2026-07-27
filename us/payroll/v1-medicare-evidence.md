# Employee Medicare tax certification evidence

**Decision status:** evidence assembly only; **4 of 5 criteria hold**. This is
not a certification or an attestation. A human may make that decision at the
2026-07-28 09:00 decision point only after the `executable` blocker below is
closed. `launch-readiness/certified-nodes.yaml` was not changed.

**Candidate scope:** only
`us:statutes/26/3101/b/1#hospital_insurance_wage_tax`, the employee tax imposed
by 26 USC 3101(b)(1). It does not certify the employee FICA family, the OASDI
tax, the additional Medicare tax, or an aggregate payroll pipeline.

The block below copies the exact entry shape from
`ops@125791409df96920f33487e4bd8ee289af344b3a:launch-readiness/certified-nodes.yaml`.
It is a review template, not an entry ready to paste: `attested_by` is still a
placeholder and `criteria.executable.holds` is false.

```yaml
- node: us:statutes/26/3101/b/1#hospital_insurance_wage_tax
  label: Employee Medicare payroll tax
  provision: 26 USC 3101(b)(1)
  corpus_citation_path: us/statute/26/3101
  mode: attested
  attested_by: <name>
  attested_at: 2026-07-28
  pinned:
    rulespec_us: 3b7f2384d2f322d8ade4d093de35d2bd1aeb3927
    corpus: db12795577c5809009168982cf8a72fb58440620
    engine: v0.1.1
    artifact: sha256:2a937800a7295db8220be9a8c087116b4caf532c50bd5f64cddc7a3d16dd5e41
  criteria:
    provision_rooted:
      holds: true
      evidence: us/payroll/v1-medicare-evidence.md:54
    conformant:
      holds: true
      evidence: us/payroll/v1-medicare-evidence.md:163
    exercised:
      holds: true
      evidence: us/payroll/v1-medicare-evidence.md:240
    closed:
      holds: true
      evidence: us/payroll/v1-medicare-evidence.md:284
    executable:
      holds: false
      evidence: us/payroll/v1-medicare-evidence.md:379; local load and value pass, published-artifact stranger path blocked
```

The RuleSpec pin is the implementation-and-fixture commit, not this narrative
evidence commit. Its tree is
`6031843ea7892d281dcffc4e06e169701d76f9a5`. The artifact hash pins the
byte-reproducible **local probe artifact**; it is not a publication claim.

## 1. `provision_rooted`

**Verdict: holds.**

The defining module is
`us/statutes/26/3101/b/1.yaml` (Git blob
`c3e52dd35990f5f50cd49fa5b5e9dced165cdad9`, file SHA-256
`64d00415ea67352bdb3776153a15a32b8fa8554435a422dab0cda4f2b5e98863`).
It declares:

- formal corpus resolution at line 6:
  `corpus_citation_path: us/statute/26/3101`;
- the rate source `26 USC 3101(b)(1)` at lines 10-25;
- the derived Person/Year/USD node and the same citation at lines 27-33; and
- `wages * hospital_insurance_wage_tax_rate` at lines 53-56.

The exact node identifier is
`us:statutes/26/3101/b/1#hospital_insurance_wage_tax`. The illustrative
`#medicare_wage_tax` identifier in the schema comment does not exist and is not
used here.

### Corpus resolution across every inventory occurrence

Corpus was inspected at
`axiom-corpus@db12795577c5809009168982cf8a72fb58440620`. A citation-path scan of
all 691 inventory JSON files and 142,902 inventory items finds 11 raw
occurrences under the delimiter-safe root `us/statute/26/3101`: two legacy
root occurrences and the current root plus eight descendants. Every occurrence
is accounted for below.

Inventory file abbreviations:

- `I-0510` =
  `data/corpus/inventory/us/statute/2026-05-10-tax-sections-r2026-07-15-self-contained-r2026-07-15-self-contained.json`
- `I-0719` =
  `data/corpus/inventory/us/statute/2026-07-19-rulespec-title-26-consolidated.json`
- `I-0724` =
  `data/corpus/inventory/us/statute/2026-07-24-1401-coordination-repair-title-26.json`

The corresponding provision files are:

- `P-0510` =
  `data/corpus/provisions/us/statute/2026-05-10-tax-sections-r2026-07-15-self-contained-r2026-07-15-self-contained.jsonl`
- `P-0719` =
  `data/corpus/provisions/us/statute/2026-07-19-rulespec-title-26-consolidated.jsonl`
- `P-0724` =
  `data/corpus/provisions/us/statute/2026-07-24-1401-coordination-repair-title-26.jsonl`

| Raw row | Inventory location | Citation path | Resolving provision record |
|---:|---|---|---|
| 1 | `I-0510:132` | `us/statute/26/3101` | `P-0510:5` |
| 2 | `I-0719:120` | `us/statute/26/3101` | `P-0719:5` |
| 3 | `I-0724:294` | `us/statute/26/3101` | `P-0724:13` |
| 4 | `I-0724:324` | `us/statute/26/3101/a` | `P-0724:14` |
| 5 | `I-0724:346` | `us/statute/26/3101/b` | `P-0724:15` |
| 6 | `I-0724:368` | `us/statute/26/3101/b/1` | `P-0724:16` |
| 7 | `I-0724:392` | `us/statute/26/3101/b/2` | `P-0724:17` |
| 8 | `I-0724:416` | `us/statute/26/3101/b/2/A` | `P-0724:18` |
| 9 | `I-0724:440` | `us/statute/26/3101/b/2/B` | `P-0724:19` |
| 10 | `I-0724:464` | `us/statute/26/3101/b/2/C` | `P-0724:20` |
| 11 | `I-0724:488` | `us/statute/26/3101/c` | `P-0724:21` |

The current provisions file is
`data/corpus/provisions/us/statute/2026-07-24-1401-coordination-repair-title-26.jsonl`.
Its line 16 is the exact paragraph record, labeled `26 U.S.C. § 3101(b)(1)`,
whose body says the tax is 1.45 percent of wages received with respect to
employment. Thus both the module's formal section-root path and the exact leaf
path resolve.

There is a corpus metadata defect worth preserving in the evidence: both
legacy root records have a `source_url` pointing to section 45A, although their
`citation_path`, label, identifiers, and §3101 body are correct. The three root
bodies are byte-equivalent after extraction, SHA-256
`62357dd1c3f8ea155f14b7e90bb52dcaa052c59f9dfca28f849f2230a0e92dc6`.
The 2026-07-24 record links correctly to section 3101 and is the canonical
source used for content review. Resolution here is by citation path, not by
the defective legacy URL.

Reproduction:

```sh
ref=db12795577c5809009168982cf8a72fb58440620
repo=/Users/maxghenis/TheAxiomFoundation/axiom-corpus
git -C "$repo" ls-tree -r --name-only "$ref" -- data/corpus/inventory |
while IFS= read -r file; do
  git -C "$repo" show "$ref:$file" |
  jq -r --arg file "$file" '
    .items[]? |
    select(
      .citation_path == "us/statute/26/3101" or
      (.citation_path | startswith("us/statute/26/3101/"))
    ) |
    [$file, .citation_path, (.source_path // "")] | @tsv
  '
done | sort

git -C "$repo" ls-tree -r --name-only "$ref" -- data/corpus/provisions |
while IFS= read -r file; do
  git -C "$repo" show "$ref:$file" |
  jq -r --arg file "$file" '
    select(
      .citation_path == "us/statute/26/3101" or
      (.citation_path | startswith("us/statute/26/3101/"))
    ) |
    [$file, .citation_path, (.source_url // "")] | @tsv
  '
done | sort
```

## 2. `conformant`

**Verdict: holds.**

The registered case-grid suite is committed locally at
`axiom-oracles@75782c6574e6219bfbc98ab679d6524ecccc0259`; the push attempt could
not resolve GitHub, so this commit was not published:

- `comparisons/us-employee-medicare-grid.yaml` registers
  `us-employee-medicare-grid` using the same
  `federal-tax-liability-grid` registration shape as
  `us-additional-medicare-grid`;
- `scripts/generate_federal_tax_liability.py` registers the Medicare-only
  cases and boundary adapters; and
- `tests/test_federal_tax_liability_generator.py` verifies the registry,
  one-input fixture contract, bridge, and PolicyEngine rate.

This is a five-case grid, not a population suite. It pins
`rulespec-us@3b7f2384d2f322d8ade4d093de35d2bd1aeb3927` and tree
`6031843ea7892d281dcffc4e06e169701d76f9a5`. The execution stack is Python
3.13, `policyengine==4.18.9`, `policyengine-us==1.767.3`, and
`policyengine-core==3.30.3`. The reviewed PolicyEngine-US source pin is
`49d19b239a593dbac8920ac6fd80cfe33372343a`.

The comparison is like-for-like at the completed-wage boundary:

- Axiom:
  `hospital_insurance_wage_tax = 0.0145 * wages`;
- PolicyEngine-US:
  `employee_medicare_tax =
  gov.irs.payroll.medicare.rate.employee * payroll_tax_gross_wages`; and
- the adapter supplies the same completed W-2 Box 5 amount directly as
  `wages` and `payroll_tax_gross_wages`, then verifies the 2026 PolicyEngine
  employee rate is exactly `0.0145`.

Exact run:

```sh
UV_OFFLINE=1 \
UV_CACHE_DIR=/private/tmp/medicare-uv-cache.EMOePi \
/Users/maxghenis/.cache/uv/archive-v0/KHsnHQNgjRDE2PQFz-DN-/bin/python \
  scripts/run_comparison.py us-employee-medicare-grid \
  --output-dir /private/tmp/medicare-oracle-receipts --summary
```

The runner verified the pinned RuleSpec tree before comparison. Receipt:
`axiom-policyengine-us-employee-medicare-grid-all-2026-07-27.json`, SHA-256
`5cf53d53f21a6cb14f1bd3573f0c37f82572dd1915cf50fcbb39f7ca4b182873`.

| Completed wages | Why included | Axiom | PolicyEngine | Absolute difference | Result |
|---:|---|---:|---:|---:|---|
| $0 | zero intercept | $0 | $0 | $0 | match |
| $100,000 | ordinary positive wages | $1,450 | $1,450 | $0 | match |
| $184,500 | at 2026 OASDI wage base | $2,675.25 | $2,675.25 | $0 | match |
| $184,501 | $1 above OASDI wage base | $2,675.2645 | $2,675.264404296875 | $0.000095703125 | match |
| $300,000 | well above OASDI wage base | $4,350 | $4,350 | $0 | match |

The nonzero sub-cent residual is PolicyEngine's numeric representation, not a
statutory disagreement; the exact statute arithmetic is $2,675.2645. It is
less than the suite's declared absolute tolerance of $0.01.

Receipt result and derived disposition counts (the last two derive from the
empty `mismatches` list):

```yaml
comparison_count: 5
match_count: 5
mismatch_count: 0
error_count: 0
unexplained_mismatch_count: 0
axiom_attributed_mismatch_count: 0
match_rate_percent: 100
```

Focused registry tests passed `20 passed`; Ruff passed. No generated
conformance report, dashboard, manifest, or population result is committed.

## 3. `exercised`

**Verdict: holds, with a deliberately small census.**

Section 3101(b)(1) is a one-input flat-rate rule. It has no bracket, phase-in,
filing-status threshold, or wage cap. Padding the census with household
profiles would add no legal variation. The suite varies only completed
Medicare wages:

| Input dimension | Values | What it exercises |
|---|---|---|
| completed Medicare wages | $0; $100,000; $184,500; $184,501; $300,000 | zero behavior, an ordinary positive value, and continuity at and above the OASDI cap |

The $184,500 seam is a wiring diagnostic, not a claim that §3101(b)(1) changes
there. Medicare remains linear while §3101(a) OASDI stops increasing after the
separately defined contribution and benefit base. The $184,501 and $300,000
cases would detect an accidental OASDI cap or family-output substitution.
SSA independently reports the
[2026 contribution and benefit base as $184,500](https://www.ssa.gov/OACT/COLA/cbbdet.html),
and IRS says both that Medicare has no wage-base limit and that Box 5 is the
[Medicare wages-and-tips surface](https://www.irs.gov/instructions/iw2w3).

Every bridged or constant dimension is declared:

| Dimension | Treatment |
|---|---|
| wage surface | **Bridged:** one completed W-2 Box 5 fact maps to Axiom `#input.wages` and PolicyEngine `payroll_tax_gross_wages`. |
| §3121 wage/employment classification | **Boundary fact:** already reflected in completed Medicare wages; no §3121 inclusion/exclusion facts are recomputed by this node. |
| §3101(c) international-agreement exemption | **Boundary fact:** completed Medicare wages are supplied after upstream exemption/classification; no agreement flag is evaluated by this one-node comparison. |
| employee rate | **Constant and verified:** 0.0145 in both engines for 2026. |
| time | **Constant:** tax year 2026. |
| entity | **Constant:** one Person (`head`). |
| age and location | **Constant scaffolding:** age 40 and Texas; immaterial to the Person formula. |
| household and tax-unit membership | **Constant scaffolding:** one adult in one household and tax unit. |
| filing status | **Constant scaffolding:** single; §3101(b)(1) has no filing-status branch. |
| employment income and pretax deductions | **Not supplied:** the bridge directly supplies completed payroll-tax gross wages, avoiding a second wage-classification oracle. |
| OASDI wage base | **Not an input:** $184,500 is used only to choose diagnostic wage values. |
| additional Medicare tax | **Outside scope:** §3101(b)(2) is neither an input nor an output. |
| employer Medicare tax and self-employment tax | **Outside scope:** §3111(b) and §1401(b) are not compared. |

The direct companion suite at
`us/statutes/26/3101/b/1.test.yaml` contains the same five wage facts and
expected values. It passed all 5 cases using the canonical RuleSpec root.

## 4. `closed`

**Verdict: holds for repository closure.**

Declared root and frontier:

```yaml
roots:
  - us/statute/26/3101
frontier:
  rule: delimiter-safe citation-path descendants of each declared root
  unique_provisions: 9
summary:
  encoded: 9
  excluded: 0
  pending: 0
```

The r1 sweep's “9/11” is **nine unique citation paths from eleven raw inventory
occurrences**, not nine closed paths plus two open paths. The two extra
occurrences are legacy duplicates of `us/statute/26/3101`; inventing two
taxonomy exclusions for them would double-count one legal provision.

There are, however, two substantive aggregation paths without same-path leaf
modules after the obvious leaf mapping:

- `us/statute/26/3101`; and
- `us/statute/26/3101/b`.

Both have bodies, so `container_heading` would be false. They resolve as
`encoded` only through the reviewed union of their child-scope modules:
`a.yaml`, `b/1.yaml`, `b/2.yaml`, and `c.yaml` for the section root; `b/1.yaml`
and `b/2.yaml` for subsection (b). No path is excluded. The ledger is:

```yaml
rows:
  - citation: "us/statute/26/3101"
    heading: "Rate of tax"
    status: encoded
    encoded_by:
      - "us/statutes/26/3101/a.yaml"
      - "us/statutes/26/3101/b/1.yaml"
      - "us/statutes/26/3101/b/2.yaml"
      - "us/statutes/26/3101/c.yaml"
    note: "Substantive aggregate body; encoded collectively, not a container."
  - citation: "us/statute/26/3101/a"
    heading: "Old-age, survivors, and disability insurance"
    status: encoded
    encoded_by: ["us/statutes/26/3101/a.yaml"]
  - citation: "us/statute/26/3101/b"
    heading: "Hospital insurance"
    status: encoded
    encoded_by:
      - "us/statutes/26/3101/b/1.yaml"
      - "us/statutes/26/3101/b/2.yaml"
    note: "Substantive aggregate body; encoded collectively, not a container."
  - citation: "us/statute/26/3101/b/1"
    heading: "In general"
    status: encoded
    encoded_by: ["us/statutes/26/3101/b/1.yaml"]
  - citation: "us/statute/26/3101/b/2"
    heading: "Additional tax"
    status: encoded
    encoded_by: ["us/statutes/26/3101/b/2.yaml"]
  - citation: "us/statute/26/3101/b/2/A"
    heading: ""
    status: encoded
    encoded_by: ["us/statutes/26/3101/b/2.yaml"]
  - citation: "us/statute/26/3101/b/2/B"
    heading: ""
    status: encoded
    encoded_by: ["us/statutes/26/3101/b/2.yaml"]
  - citation: "us/statute/26/3101/b/2/C"
    heading: ""
    status: encoded
    encoded_by: ["us/statutes/26/3101/b/2.yaml"]
  - citation: "us/statute/26/3101/c"
    heading: "Relief from taxes in cases covered by certain international agreements"
    status: encoded
    encoded_by: ["us/statutes/26/3101/c.yaml"]
findings:
  - "Eleven inventory occurrences deduplicate to nine citation paths."
  - "Two legacy root records have incorrect section-45A source URLs."
  - "The section and subsection-b aggregate bodies are covered by multiple reviewed modules."
```

This is the certified-nodes schema's source-side criterion: every provision
under the declared root is encoded, excluded with reason, or pending, with
zero pending. It does **not** prove a composed effective-liability program
wires the §3101(c) exemption into the §3101(b)(1) multiplication. This
candidate instead takes completed Medicare wages as its explicit boundary.
If the human reviewer interprets `closed` as composed-program closure rather
than repository closure, this criterion must be changed to pending and the
verdict remains blocked.

## 5. `executable`

**Verdict: does not hold.**

The format and arithmetic probes pass, but the literal criterion requires a
**published** artifact executed using the **released binary** by a stranger.
Only a locally compiled, unpublished artifact was available for this node.

### Local released-tag probe

The clean annotated engine tag `v0.1.1` resolves to tag object
`bdd225c4576ad51c127a10a6516675b09b2fae8d` and peeled commit
`e3e2da83222463d9b68b0681c00820e9d412c011`. The source was built with:

```sh
cargo build --release --locked --bin axiom-rules-engine
```

The resulting local binary reports `axiom-rules-engine 0.1.1` and has SHA-256
`c1ea7e6c7984df06beef964e4923fa00ca3a4a1aa6e213e561a026ed558c452f`.
That hash describes the local build; it is not represented as an official
cargo-dist asset.

Exact compile:

```sh
/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/engine-v0.1.1/target/release/axiom-rules-engine \
  compile \
  --program /private/tmp/medicare-engine-release.0IIypP/rulespec-us/us/statutes/26/3101/b/1.yaml \
  --output /private/tmp/medicare-engine-release.0IIypP/us-employee-medicare.compiled.json
```

Receipt:

```yaml
engine_version: 0.1.1
artifact_format_version: 2
derived_output_count: 1
derived_output: us:statutes/26/3101/b/1#hospital_insurance_wage_tax
artifact_sha256: 2a937800a7295db8220be9a8c087116b4caf532c50bd5f64cddc7a3d16dd5e41
deterministic_recompile_sha256: 2a937800a7295db8220be9a8c087116b4caf532c50bd5f64cddc7a3d16dd5e41
```

The input, in the same legal-ID request shape used by the ops quickstart/parity
fixture, is:

```json
{
  "mode": "explain",
  "dataset": {
    "inputs": [{
      "name": "us:statutes/26/3101/b/1#input.wages",
      "entity": "Person",
      "entity_id": "person:1",
      "interval": {"start": "2026-01-01", "end": "2027-01-01"},
      "value": {"kind": "decimal", "value": "300000"}
    }],
    "relations": []
  },
  "queries": [{
    "entity_id": "person:1",
    "period": {
      "period_kind": "tax_year",
      "start": "2026-01-01",
      "end": "2026-12-31"
    },
    "outputs": [
      "us:statutes/26/3101/b/1#hospital_insurance_wage_tax"
    ]
  }]
}
```

Exact run as executed:

```sh
printf '%s\n' '{"mode":"explain","dataset":{"inputs":[{"name":"us:statutes/26/3101/b/1#input.wages","entity":"Person","entity_id":"person:1","interval":{"start":"2026-01-01","end":"2027-01-01"},"value":{"kind":"decimal","value":"300000"}}],"relations":[]},"queries":[{"entity_id":"person:1","period":{"period_kind":"tax_year","start":"2026-01-01","end":"2026-12-31"},"outputs":["us:statutes/26/3101/b/1#hospital_insurance_wage_tax"]}]}' |
/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/engine-v0.1.1/target/release/axiom-rules-engine \
  run-compiled \
  --artifact /private/tmp/medicare-engine-release.0IIypP/us-employee-medicare.compiled.json
```

The command exits 0, reports requested/actual mode `explain`, returns decimal
`4350` USD, and traces the output to `26 USC 3101(b)(1)`. Therefore there is no
v0.1.1 format gap: the released-tag engine loads format 2 and computes the
golden value.

### Hand-checkable golden case

Statutory premise: §3101(b)(1) imposes “a tax equal to 1.45 percent of the
wages.” For completed W-2 Box 5 wages of **$300,000**:

```text
1.00% of $300,000 = $3,000
0.40% of $300,000 = $1,200
0.05% of $300,000 =   $150
                       ------
1.45% of $300,000 = $4,350
```

Equivalently, `$300,000 × 0.0145 = $4,350`. Section 3101(b)(1) contains no
OASDI wage-base cap, so none is applied. The companion fixture, PolicyEngine
grid, and local compiled run all return $4,350.

### Blocking findings

1. There is no one-output §3101(b)(1) program artifact in a published
   `rulespec-us` program-artifacts release. Repository policy says compiled
   artifacts are never committed and are published from program specs only
   after they land on `main` (`tools/README.md:3-21`). The freeze constraints
   for this evidence task prohibit adding a program spec.
2. Fresh anonymous download and attestation of the official v0.1.1 cargo-dist
   binary could not be performed in this sandbox because the GitHub API
   endpoint `api.github.com` was unreachable. The local probe used the exact
   released source tag, not a development-engine substitute, but it is not
   equivalent to executing the published release asset.
3. Consequently there is no honest stranger-path command pairing an official
   released binary with a published artifact at the pinned artifact hash.

Until a provenance-stamped one-output artifact is published and a fresh
release-asset stranger run reproduces $4,350, `executable.holds` must remain
false and this candidate must not be added to `certified-nodes.yaml`.
