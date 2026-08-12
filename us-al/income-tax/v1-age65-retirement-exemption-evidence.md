# Alabama age-65 retirement-income exemption certification evidence

**Decision status:** evidence assembly only; **3 of 5 criteria hold**. This is
not a certification or an attestation. A human must not certify this candidate
while either the `closed` or `executable` blocker below remains open.
`launch-readiness/certified-nodes.yaml` was not changed.

**Candidate scope:** tax year 2025 only, nonnegative taxable retirement income
only, and only
`us-al:statutes/40-18-19#taxable_retirement_income_exemption`, the Person-level
age-65 exemption in Alabama Code § 40-18-19(a)(13). It does not certify the
other exemptions in § 40-18-19, a tax-unit exemption total, Alabama taxable
income, or an Alabama individual-income-tax liability program. It makes no
claim for tax year 2026 or later.

The block below copies the exact entry shape from
`ops@125791409df96920f33487e4bd8ee289af344b3a:launch-readiness/certified-nodes.yaml`.
It is a review template, not an entry ready to paste: `attested_by` is still a
placeholder, and both `criteria.closed.holds` and
`criteria.executable.holds` are false.

```yaml
- node: us-al:statutes/40-18-19#taxable_retirement_income_exemption
  label: Alabama age-65 taxable-retirement-income exemption, TY2025
  provision: Alabama Code 40-18-19(a)(13)
  corpus_citation_path: us-al/statute/40-18-19
  mode: attested
  attested_by: <name>
  attested_at: 2026-07-28
  pinned:
    rulespec_us: 101c34f12faf48588d79f07d67c45dbcea25963b
    corpus: db12795577c5809009168982cf8a72fb58440620
    engine: v0.1.1
    artifact: sha256:08b6ef3211ea3b3d305be899088b7573896e5838a02069b6eeda9128323d7301
  criteria:
    provision_rooted:
      holds: true
      evidence: us-al/income-tax/v1-age65-retirement-exemption-evidence.md:58
    conformant:
      holds: true
      evidence: us-al/income-tax/v1-age65-retirement-exemption-evidence.md:149
    exercised:
      holds: true
      evidence: us-al/income-tax/v1-age65-retirement-exemption-evidence.md:246
    closed:
      holds: false
      evidence: us-al/income-tax/v1-age65-retirement-exemption-evidence.md:299; one partially encoded section-root path remains pending
    executable:
      holds: false
      evidence: us-al/income-tax/v1-age65-retirement-exemption-evidence.md:369; local load and value pass, published-artifact stranger path blocked
```

The RuleSpec pin is the implementation-and-fixture commit, not this narrative
evidence commit. Its tree is
`f15cbee2616b7e8dbf8162196e7dbc7e5d54742d`. The artifact hash pins the
byte-reproducible **local probe artifact**; it is not a publication claim.

## 1. `provision_rooted`

**Verdict: holds for tax year 2025.**

The defining module is `us-al/statutes/40-18-19.yaml` (Git blob
`38716efd740d7b9f14b73e09f3e2ad19fa3dff31`, file SHA-256
`303f699a0a2c6af8a94fcf1897367c85a350bc0d380d127ca518d6eac58a7bb9`).
It declares:

- formal corpus resolution at line 6:
  `corpus_citation_path: us-al/statute/40-18-19`;
- the $6,000 cap from subsection (a)(13) at lines 13-29;
- the age-65 threshold from subsection (a)(13) at lines 31-46;
- the derived Person/Year/USD output at lines 48-54; and
- `if age >= 65: min(max(0, taxable retirement income), 6000) else: 0`
  through the two parameters at lines 68-71.

The exact candidate identifier is
`us-al:statutes/40-18-19#taxable_retirement_income_exemption`.

### Tax-year boundary

The pinned corpus page displays the rule added by Act 2022-294: beginning
January 1, 2023, the first $6,000 of taxable retirement income may be claimed
by an individual taxpayer age 65 or older. The same page warns that Act
2026-603 amends the section effective October 1, 2026 and that the revised
language is not displayed. That is a source defect for a full-year 2026 or
current-law claim, but not for this expressly bounded tax-year-2025 candidate.
No 2026 text is projected backward into 2025.

### Corpus resolution across every inventory occurrence

Corpus was inspected at
`axiom-corpus@db12795577c5809009168982cf8a72fb58440620`. A
delimiter-safe citation-path scan of all 691 inventory JSON files and 142,902
inventory items finds exactly one occurrence at the declared root and no
descendants:

| Raw row | Inventory location | Citation path | Resolving provision record |
|---:|---|---|---|
| 1 | `data/corpus/inventory/us-al/statute/2026-07-13-recovery.json:15` | `us-al/statute/40-18-19` | `data/corpus/provisions/us-al/statute/2026-07-13-recovery.jsonl:2` |

The inventory row has official source path
`sources/us-al/statute/2026-07-13-recovery/official-documents/us-al-code-40-18-19`
and SHA-256
`7f0ee234c9cd1a2bd5802f33c275d37548f2dd7bf62fd8a57e3ecbbfa38a61aa`.
The corresponding provision record is ID
`0fd715e1-d5d7-5c20-8c86-6f6626266c84`, labels the section
`40-18-19`, and contains subsection (a)(13)'s amount and age condition. The
provenance record at
`data/corpus/sources/us-al/statute/2026-07-13-recovery/provenance/us-al-code-40-18-19.json:2-7`
records the same hash, official URL, HTTP 200, and browser fetch.

A scan of all 699 corpus provision JSONL files, 698 nonempty files, and 143,015
records likewise finds exactly that one delimiter-safe resolver. Thus every
inventory occurrence resolves by citation path. The lack of a paragraph-level
descendant is material to `closed`, not to resolution of the module's declared
root.

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
      .citation_path == "us-al/statute/40-18-19" or
      (.citation_path | startswith("us-al/statute/40-18-19/"))
    ) |
    [$file, .citation_path, (.source_path // "")] | @tsv
  '
done | sort

git -C "$repo" ls-tree -r --name-only "$ref" -- data/corpus/provisions |
while IFS= read -r file; do
  git -C "$repo" show "$ref:$file" |
  jq -r --arg file "$file" '
    select(
      .citation_path == "us-al/statute/40-18-19" or
      (.citation_path | startswith("us-al/statute/40-18-19/"))
    ) |
    [$file, .citation_path, .id] | @tsv
  '
done | sort
```

## 2. `conformant`

**Verdict: holds.**

The bounded registered case grid is committed locally at
`axiom-oracles@76b8564ab38c01ffd4d2d361ce4f0cea978973a8`.
It contains:

- `comparisons/us-al-age65-retirement-exemption-grid.yaml`, which registers
  `us-al-age65-retirement-exemption-grid` and publicly limits
  `taxable_retirement_income` to a minimum of zero;
- `scripts/generate_al_retirement_exemption.py`, which rejects negative
  retirement-income cases instead of silently clamping or filtering them;
- `scripts/run_comparison.py`, which dispatches the registered grid; and
- `tests/test_al_retirement_exemption_generator.py`, which verifies the
  registry, five-case contract, nonnegative domain, input bridge, and
  PolicyEngine constants.

This is a five-case grid, not a population suite. It pins
`rulespec-us@101c34f12faf48588d79f07d67c45dbcea25963b` and tree
`f15cbee2616b7e8dbf8162196e7dbc7e5d54742d`. The execution stack is Python
3.13, `policyengine==4.18.9`, `policyengine-us==1.767.3`, and
`policyengine-core==3.30.3`. The reviewed PolicyEngine-US source pin is
`49d19b239a593dbac8920ac6fd80cfe33372343a`.

The PolicyEngine target has real logic; it is not a parameter passthrough:

- `al_retirement_exemption_eligible_person.py:17-22` reads the age-threshold
  parameter, tests `age >= age_threshold`, reads
  `is_tax_unit_head_or_spouse`, and conjoins those facts;
- `al_retirement_exemption_person.py:16-25` is defined for that eligibility
  output, adds `taxable_retirement_distributions` and
  `taxable_pension_income`, then takes the minimum of that total and the cap;
- `taxable_retirement_distributions.py:10-16` itself adds taxable IRA, 401(k),
  SEP, 403(b), and Keogh distributions;
- `taxable_pension_income.py:11` adds taxable public and private pension
  income; and
- `age_threshold.yaml:1-3` and `cap.yaml:1-3` provide 65 and $6,000 from
  January 1, 2023.

The comparison is like-for-like inside the public nonnegative domain:

- Axiom:
  `age >= 65 ? min(max(0, taxable_retirement_income), 6000) : 0`;
- PolicyEngine-US:
  an eligible head or spouse receives
  `min(taxable_retirement_distributions + taxable_pension_income, 6000)`; and
- the adapter supplies the same nonnegative completed taxable-retirement
  amount as `taxable_retirement_distributions`, fixes
  `taxable_pension_income` to zero, and fixes the one compared Person as the
  tax-unit head.

PolicyEngine does not apply Axiom's `max(0, ...)`. Therefore the public
minimum-zero schema and generator rejection are part of the claim boundary;
negative amounts are neither compared nor represented as matches.

Exact run:

```sh
UV_CACHE_DIR=/private/tmp/medicare-uv-cache.EMOePi \
UV_OFFLINE=1 \
PYTHONDONTWRITEBYTECODE=1 \
/Users/maxghenis/TheAxiomFoundation/axiom-oracles/.venv/bin/python \
  scripts/run_comparison.py us-al-age65-retirement-exemption-grid \
  --output-dir /private/tmp/al-age65-oracle/reports --summary
```

Receipt:
`axiom-policyengine-us-al-age65-retirement-exemption-grid-all-2026-07-27.json`,
SHA-256
`4924c5c78f25c99388aa4fa7f1d7b8e0838231f5e55abd862068013dd519de35`.

| Age | Nonnegative taxable retirement income | Why included | Axiom | PolicyEngine | Absolute difference | Result |
|---:|---:|---|---:|---:|---:|---|
| 64 | $6,000 | one year below age threshold, at cap | $0 | $0 | $0 | match |
| 65 | $0 | age threshold and public-domain lower bound | $0 | $0 | $0 | match |
| 65 | $5,999 | one dollar below cap | $5,999 | $5,999 | $0 | match |
| 65 | $6,000 | exactly at cap | $6,000 | $6,000 | $0 | match |
| 65 | $6,001 | one dollar above cap | $6,000 | $6,000 | $0 | match |

Receipt result and derived disposition counts (the final two follow from the
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

The focused Alabama tests plus the federal-runner regression tests pass
`30 passed`; Ruff check passes. No generated conformance report, dashboard,
manifest, or population result is committed.

## 3. `exercised`

**Verdict: holds, with a deliberately small census.**

Section 40-18-19(a)(13) has two statutory seams inside this candidate's public
domain: the age threshold at 65 and the $6,000 cap on a nonnegative income
amount. The five witnesses cover both sides of age eligibility at the cap,
then zero and both sides of the cap for an eligible taxpayer:

| Input dimension | Values | What it exercises |
|---|---|---|
| age | 64; 65 | immediately below and exactly at the eligibility threshold |
| nonnegative taxable retirement income | $0; $5,999; $6,000; $6,001 | public-domain lower bound and immediately below, at, and above the cap |

This is intentionally not a Cartesian product. Extra ages or repeated income
amounts would add no legal branch. Negative income is outside the publicly
declared comparison domain; neither the grid nor this evidence treats Axiom's
defensive nonnegative clamp as PolicyEngine parity.

Every bridged or constant dimension is declared:

| Dimension | Treatment |
|---|---|
| taxable-retirement-income surface | **Bridged:** one completed nonnegative annual amount maps to Axiom `#input.taxable_retirement_income` and PolicyEngine `taxable_retirement_distributions`. |
| PolicyEngine taxable pension income | **Constant:** $0, so the PolicyEngine sum equals the bridged completed amount. |
| lower bound | **Public claim boundary:** taxable retirement income must be greater than or equal to $0; the generator rejects a negative case. |
| age | **Varied:** 64 and 65. |
| exemption cap | **Constant and verified:** $6,000 in both engines for 2025. |
| age threshold | **Constant and verified:** 65 in both engines for 2025. |
| time | **Constant:** tax year 2025 only. |
| state | **Constant:** Alabama. |
| entity | **Constant:** one Person (`head`) in one TaxUnit. |
| tax-unit role | **Constant:** the compared Person is the tax-unit head, satisfying PolicyEngine's explicit head-or-spouse eligibility branch. |
| filing and household scaffolding | **Constant:** one adult, single-filer household and tax unit; no dependent or spouse. |
| other § 40-18-19 exemptions | **Outside candidate scope:** no personal, dependent, retirement-system, 529, ABLE, or foreign-earned-income exemption is supplied or compared. |
| Alabama taxable income and liability | **Outside candidate scope:** the one-output comparison stops at the Person exemption amount. |

The direct companion suite at
`us-al/statutes/40-18-19.test.yaml` contains the same five age/income facts and
expected values. It passed all five cases against a canonical `rulespec-us`
root:

```sh
/Users/maxghenis/TheAxiomFoundation/_bulk_drain/.venv/bin/axiom-encode \
  test \
  /private/tmp/al-age65-fixtures.YNGzCs/rulespec-us/us-al/statutes/40-18-19.test.yaml \
  --root /private/tmp/al-age65-fixtures.YNGzCs/rulespec-us \
  --axiom-rules-engine-path \
  /Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/engine-v0.1.1
```

Receipt: `RuleSpec companion tests passed: 1 file(s), 5 case(s)`.

## 4. `closed`

**Verdict: does not hold.**

Declared root and frontier:

```yaml
roots:
  - us-al/statute/40-18-19
frontier:
  rule: delimiter-safe citation-path descendants of each declared root
  raw_occurrences: 1
  unique_provisions: 1
summary:
  encoded: 0
  excluded: 0
  pending: 1
```

The sole corpus path is a substantive whole-section record, not a container
heading. It contains the candidate at subsection (a)(13), but also contains
the distinct exemptions in subsections (a)(1)-(12), nonresident rules in
subsection (b), and administrative authority in subsection (c). Corpus has no
paragraph-level `us-al/statute/40-18-19/a/13` descendant that could isolate
this candidate from the remainder.

The module itself preserves this scope boundary honestly:
`us-al/statutes/40-18-19.yaml:9-11` defers the whole-subsection
`#resident_income_tax_exemptions` aggregate because the other categories need
external retirement-system, beneficiary, federal-tax, college-savings, ABLE,
foreign-income, and filing-status definitions. Merely appearing in the reverse
index at `.axiom/index/provisions_to_rules.json:1076-1090` does not make the
entire section body encoded.

The closure ledger is:

```yaml
rows:
  - citation: "us-al/statute/40-18-19"
    heading: "Exemptions - Generally"
    status: pending
    partial_coverage:
      encoded_by:
        - "us-al/statutes/40-18-19.yaml#taxable_retirement_income_exemption"
        - "other independent scalar parameters in us-al/statutes/40-18-19.yaml"
      encoded_fragment: "40-18-19(a)(13), TY2025 nonnegative-income candidate"
    pending_remainder:
      - "unencoded and uncomposed portions of 40-18-19(a)(1)-(12)"
      - "40-18-19(a) aggregate"
      - "40-18-19(b)"
      - "40-18-19(c)"
    reason: "The one substantive corpus path combines the encoded candidate with explicitly deferred exemption categories and has no paragraph descendant."
findings:
  - "One inventory occurrence deduplicates to one substantive citation path."
  - "The path is partially encoded but cannot be counted encoded under the zero-pending closure rule."
  - "The path cannot be excluded because it contains the candidate itself."
  - "Closure requires paragraph-granular corpus paths or encoding the remaining substantive section body."
```

The tax-year-2026 Alabama resident-liability source hold independently
confirms that the complete exemption chain is unavailable:
`us-al/policies/income_tax/2026_resident_liability_source_hold.yaml:17-44`
describes the missing amendment and income-base authorities, and lines 62-89
defer deductions, exemptions, and taxable income. That 2026 source hold does
not invalidate the narrower 2025 calculation, but it prevents treating this
partial section encoding as a closed annual-return surface.

This criterion permits only encoded, excluded-with-reason, or pending rows and
requires zero pending. With one pending row, `closed.holds` must remain false.

## 5. `executable`

**Verdict: does not hold.**

The format and arithmetic probes pass, but the literal criterion requires a
**published** artifact executed using the **released binary** by a stranger.
Only a locally compiled, unpublished artifact was available for this node.

### Local released-tag probe

The clean annotated engine tag `v0.1.1` resolves to tag object
`bdd225c4576ad51c127a10a6516675b09b2fae8d`, peeled commit
`e3e2da83222463d9b68b0681c00820e9d412c011`, and tree
`62014a67b4540c9a5b6e2812838b4ae174bd3e07`. The local source-tag binary
reports `axiom-rules-engine 0.1.1` and has SHA-256
`c1ea7e6c7984df06beef964e4923fa00ca3a4a1aa6e213e561a026ed558c452f`.
That hash describes the local build; it is not represented as an official
cargo-dist asset.

Canonical repository naming matters: compiling directly from a linked
worktree path would put `.git/codex-worktrees/...` into the legal ID. The
probe therefore compiled from a clean checkout directory literally named
`rulespec-us`.

Exact compile and deterministic recompile:

```sh
engine=/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/engine-v0.1.1/target/release/axiom-rules-engine
root=/private/tmp/al-age65-canonical-release.uSq0lX/rulespec-us

AXIOM_RULESPEC_REPO_ROOTS="$root" "$engine" compile \
  --program "$root/us-al/statutes/40-18-19.yaml" \
  --output /private/tmp/al-age65-canonical-release.uSq0lX/us-al-age65-retirement-exemption.compiled.json

AXIOM_RULESPEC_REPO_ROOTS="$root" "$engine" compile \
  --program "$root/us-al/statutes/40-18-19.yaml" \
  --output /private/tmp/al-age65-canonical-release.uSq0lX/us-al-age65-retirement-exemption.recompiled.json
```

Receipt:

```yaml
engine_version: 0.1.1
artifact_format_version: 2
derived_output_count: 1
derived_output: us-al:statutes/40-18-19#taxable_retirement_income_exemption
artifact_sha256: 08b6ef3211ea3b3d305be899088b7573896e5838a02069b6eeda9128323d7301
deterministic_recompile_sha256: 08b6ef3211ea3b3d305be899088b7573896e5838a02069b6eeda9128323d7301
```

The golden input, in the same legal-ID request shape used by the ops
quickstart/parity fixture, is:

```json
{
  "mode": "explain",
  "dataset": {
    "inputs": [
      {
        "name": "us-al:statutes/40-18-19#input.age",
        "entity": "Person",
        "entity_id": "person:1",
        "interval": {"start": "2025-01-01", "end": "2026-01-01"},
        "value": {"kind": "integer", "value": 65}
      },
      {
        "name": "us-al:statutes/40-18-19#input.taxable_retirement_income",
        "entity": "Person",
        "entity_id": "person:1",
        "interval": {"start": "2025-01-01", "end": "2026-01-01"},
        "value": {"kind": "decimal", "value": "7000"}
      }
    ],
    "relations": []
  },
  "queries": [{
    "entity_id": "person:1",
    "period": {
      "period_kind": "tax_year",
      "start": "2025-01-01",
      "end": "2025-12-31"
    },
    "outputs": [
      "us-al:statutes/40-18-19#taxable_retirement_income_exemption"
    ]
  }]
}
```

Exact run as executed:

```sh
printf '%s\n' '{"mode":"explain","dataset":{"inputs":[{"name":"us-al:statutes/40-18-19#input.age","entity":"Person","entity_id":"person:1","interval":{"start":"2025-01-01","end":"2026-01-01"},"value":{"kind":"integer","value":65}},{"name":"us-al:statutes/40-18-19#input.taxable_retirement_income","entity":"Person","entity_id":"person:1","interval":{"start":"2025-01-01","end":"2026-01-01"},"value":{"kind":"decimal","value":"7000"}}],"relations":[]},"queries":[{"entity_id":"person:1","period":{"period_kind":"tax_year","start":"2025-01-01","end":"2025-12-31"},"outputs":["us-al:statutes/40-18-19#taxable_retirement_income_exemption"]}]}' |
/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/engine-v0.1.1/target/release/axiom-rules-engine \
  run-compiled \
  --artifact /private/tmp/al-age65-canonical-release.uSq0lX/us-al-age65-retirement-exemption.compiled.json
```

The command exits 0, reports requested/actual mode `explain`, returns decimal
`6000` USD, and traces the output to `40-18-19(a)`. Therefore there is no
v0.1.1 format gap: the released-tag source build loads format 2 and computes
the golden value.

### Hand-checkable golden case

For a tax-year-2025 individual taxpayer who is exactly **65** and has exactly
**$7,000** of nonnegative taxable retirement income:

```text
age test:                    65 >= 65            = eligible
public-domain lower bound:   max($0, $7,000)     = $7,000
statutory cap:               min($7,000, $6,000) = $6,000
                                                    ------
exemption                                          $6,000
```

The statute exempts the first $6,000, not the entire $7,000. Under the
PolicyEngine bridge, taxable retirement distributions are $7,000, taxable
pension income is $0, and the Person is the tax-unit head:

```text
PolicyEngine retirement total: $7,000 + $0        = $7,000
eligibility:                    age 65 and head    = true
PolicyEngine cap:               min($7,000, $6,000) = $6,000
```

The companion formula, PolicyEngine grid, and local compiled run all return
$6,000.

### Blocking findings

1. There is no Alabama income-tax or age-65-exemption program spec under
   `programs/us-al/`; only SNAP and TANF specs exist. Repository policy says
   compiled artifacts are never committed and are published from program
   specs only after they land on `main` (`tools/README.md:3-21`). The launch
   freeze for this evidence task prohibits adding a program spec.
2. Consequently there is no one-output exemption artifact in a published
   `rulespec-us` program-artifacts release, no provenance-stamped manifest row
   at the pinned hash, and no artifact URL a stranger can fetch.
3. Fresh anonymous download and attestation of an official v0.1.1 cargo-dist
   binary was unavailable in this sandbox. The probe used the exact clean
   released source tag, not a development engine, but that does not turn the
   unpublished local artifact into a stranger path.
4. Independently, source closure still has the one pending whole-section path
   documented above.

Until the corpus can isolate or the repository can encode the remaining
substantive section body, a provenance-stamped one-output artifact is
published, and a fresh released-binary stranger run reproduces $6,000, this
candidate remains an honest **3 of 5** and must not be added to
`certified-nodes.yaml`.
