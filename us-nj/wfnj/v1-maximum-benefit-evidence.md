# New Jersey WFNJ maximum-benefit certification evidence

**Decision status:** evidence assembly only; **4 of 5 criteria hold**. This is
not a certification or an attestation. A human may make that decision at the
2026-07-28 decision point only after the `executable` blockers below are
closed. `launch-readiness/certified-nodes.yaml` was not changed.

**Candidate scope:** only
`us-nj:regulations/njac-10-90/10-90-3/3#tanf_maximum_benefit_payment_level`,
the monthly Schedule II maximum-benefit amount in N.J.A.C. 10:90-3.3(b). It
does not certify Schedule I, WFNJ eligibility, income or resource rules,
dependent-child eligibility, reporting duties, take-up, or a final cash
benefit.

| Criterion | Verdict | Evidence summary |
|---|---|---|
| `provision_rooted` | **holds** | The module names the exact corpus path; the one matching inventory record resolves to the official § 3.3 provision and its Schedule II table. |
| `conformant` | **holds** | A registered ten-case grid compares the RuleSpec output with PolicyEngine's real `nj_wfnj_payment_levels` arithmetic: 10 matches, 0 mismatches, 0 errors. |
| `exercised` | **holds** | Sizes 1 through 10 cover every listed table cell, the size-eight seam, and two $66 continuation cases; every bridge and constant is declared. |
| `closed` | **holds for the candidate's repository frontier** | One unique citation path from one raw inventory record is encoded; there are no pending paths. |
| `executable` | **does not hold** | Released v0.1.1 computes the golden value from a deterministic local one-output artifact, but that artifact is a temporary unpublished slice and no published NJ WFNJ program artifact exists. |

The block below copies the exact entry shape from
`ops@125791409df96920f33487e4bd8ee289af344b3a:launch-readiness/certified-nodes.yaml`.
It is a review template, not an entry ready to paste: `attested_by` is still a
placeholder and `criteria.executable.holds` is false.

```yaml
- node: us-nj:regulations/njac-10-90/10-90-3/3#tanf_maximum_benefit_payment_level
  label: New Jersey WFNJ/TANF maximum benefit payment level
  provision: N.J.A.C. 10:90-3.3(b), Schedule II
  corpus_citation_path: us-nj/regulation/njac-10-90/10-90-3.3
  mode: attested
  attested_by: <name>
  attested_at: 2026-07-28
  pinned:
    rulespec_us: 5b51301a2d29b099f9fa167d403a1a2eb0921fef
    corpus: db12795577c5809009168982cf8a72fb58440620
    engine: v0.1.1
    artifact: sha256:3af5f1d4968b80ea0e9dd5fd1e5696ace78b041f9c3d29fb066cd19d8247c0ba
  criteria:
    provision_rooted:
      holds: true
      evidence: us-nj/wfnj/v1-maximum-benefit-evidence.md:64
    conformant:
      holds: true
      evidence: us-nj/wfnj/v1-maximum-benefit-evidence.md:158
    exercised:
      holds: true
      evidence: us-nj/wfnj/v1-maximum-benefit-evidence.md:270
    closed:
      holds: true
      evidence: us-nj/wfnj/v1-maximum-benefit-evidence.md:328
    executable:
      holds: false
      evidence: us-nj/wfnj/v1-maximum-benefit-evidence.md:381; local load and value pass, unpublished artifact blocks stranger path
```

The RuleSpec pin is the implementation-and-fixture commit, not this narrative
evidence commit. Its tree is
`06fef82924e2b29c0b5e8afd79341ae3baabfa2c`. The artifact hash pins the
byte-reproducible **local probe artifact**; it is not a publication claim.

## 1. `provision_rooted`

**Verdict: holds.**

The defining module is
`us-nj/regulations/njac-10-90/10-90-3/3.yaml` (Git blob
`76598d1ce6d660b477d8e03a0fb1f5af881e8fe7`, file SHA-256
`c28a7f8daa9e557b791fb08e1cd3a5e2563b32b30b17247d30f5396c69f8a35e`).
It declares:

- formal corpus resolution at line 6:
  `corpus_citation_path: us-nj/regulation/njac-10-90/10-90-3.3`;
- the listed-size limit of eight at lines 14-28, proved by the source phrase
  `More than 8`;
- the Schedule II table at lines 59-88:
  `[214, 425, 559, 644, 728, 814, 894, 961]`;
- the $66 additional-person amount at lines 106-122, proved by the source
  phrase `Add $ 66 for each additional person`; and
- the TanfUnit/Month/USD derived node and piecewise formula at lines 162-185.

The exact node identifier is
`us-nj:regulations/njac-10-90/10-90-3/3#tanf_maximum_benefit_payment_level`.
The node namespace uses `regulations` while the corpus taxonomy uses the
singular `regulation`; those spellings are intentional and both resolve in
their respective systems.

### Corpus resolution across every inventory occurrence

Corpus was inspected at
`axiom-corpus@db12795577c5809009168982cf8a72fb58440620`. A delimiter-safe scan
of all 691 inventory JSON files and all 142,902 inventory items used
`path == root || path.startswith(root + "/")`. It finds exactly one raw
occurrence, exactly one unique citation path, and no descendants:

| Raw row | Inventory location | Citation path | Resolving provision record |
|---:|---|---|---|
| 1 | `data/corpus/inventory/us-nj/regulation/2026-07-13-recovery.json:9441-9456` | `us-nj/regulation/njac-10-90/10-90-3.3` | `data/corpus/provisions/us-nj/regulation/2026-07-13-recovery.jsonl:556` |

The inventory file has Git blob
`657319e1f61fdd256361e9be1ce79ddfd57c5eab`; the provision file has Git blob
`448139831b1f0683ff1dbd82c0361249e7cd5e19`. The inventory record identifies
page 89 of the official New Jersey WFNJ manual, source SHA-256
`687a14f299cad3038e27ea9c404d5461cf35b71a4db1ea0ae04ed4af11ef3cfe`,
and the official URL
`https://www.nj.gov/humanservices/notices/documents/rules-and-regulations/WFNJ_Manual_12.17.24.pdf`.

Provision line 556 is a section record labeled `10-90-3.3`. Its body states
that Schedule II gives the maximum benefit payment levels for the appropriate
assistance-unit size for families with dependent children, reproduces the
eight amounts, and says “More than 8 Add $ 66 for each additional person.”
Thus the module's formal root resolves by citation path and its numeric
premises resolve in the body, without relying on a filename.

The module versions begin `2023-07-10`. The official linked PDF's regulatory
history supports that version date, but the flattened JSONL record stops after
the table and does not retain the history text. This package therefore makes a
current January 2026 arithmetic claim, not a historical-period completeness
claim.

Reproduction:

```sh
corpus_ref=db12795577c5809009168982cf8a72fb58440620
corpus_repo=/Users/maxghenis/TheAxiomFoundation/axiom-corpus
root=us-nj/regulation/njac-10-90/10-90-3.3

git -C "$corpus_repo" ls-tree -r --name-only "$corpus_ref" \
  -- data/corpus/inventory |
while IFS= read -r file; do
  git -C "$corpus_repo" show "$corpus_ref:$file" |
  jq -r --arg file "$file" --arg root "$root" '
    .items[]? |
    select(
      .citation_path == $root or
      (.citation_path | startswith($root + "/"))
    ) |
    [$file, .citation_path, (.source_path // "")] | @tsv
  '
done | sort

git -C "$corpus_repo" ls-tree -r --name-only "$corpus_ref" \
  -- data/corpus/provisions |
while IFS= read -r file; do
  git -C "$corpus_repo" show "$corpus_ref:$file" |
  jq -r --arg file "$file" --arg root "$root" '
    select(
      .citation_path == $root or
      (.citation_path | startswith($root + "/"))
    ) |
    [$file, .citation_path, (.source_url // "")] | @tsv
  '
done | sort
```

## 2. `conformant`

**Verdict: holds.**

The registered non-population case grid is committed in the companion
`axiom-oracles` repository at
`e9fc5ca0f623a97b2fceae561bbf24aefe77dd85` (tree
`73928393e147a50ce1fa1ecfca9b4e76cb086c9d`):

- `comparisons/us-nj-wfnj-payment-level-grid.yaml` registers
  `us-nj-wfnj-payment-level-grid` and pins the RuleSpec commit and tree;
- `scripts/generate_nj_wfnj_payment_level.py` defines the one-input fixtures,
  TanfUnit-to-SPMUnit adapter, parameter checks, and comparison report; and
- `tests/test_nj_wfnj_payment_level_generator.py` verifies the registry,
  fixture contract, bridge, dependent-child-domain scaffold, PolicyEngine
  parameters, and values.

This is a ten-case statutory schedule grid, not a population suite. It pins
`rulespec-us@5b51301a2d29b099f9fa167d403a1a2eb0921fef` and tree
`06fef82924e2b29c0b5e8afd79341ae3baabfa2c`. The execution stack is Python
3.13, `policyengine==4.18.9`, `policyengine-us==1.767.3`, and
`policyengine-core==3.30.3`.

### PolicyEngine variable-body review

The named oracle is the intermediate monthly variable
`nj_wfnj_payment_levels`, not the final `nj_wfnj` benefit. The reviewed source
pin is
`PolicyEngine/policyengine-us@61cc1e63323579deaa4a5070185bdfafcd7e838a`.
At
`policyengine_us/variables/gov/states/nj/njdhs/wfnj/nj_wfnj_payment_levels.py:13-20`
its body:

1. reads `spm_unit_size`;
2. caps size at `max_household_size`;
3. looks up the capped-size base amount;
4. multiplies the number above the cap by `additional_person`; and
5. returns base plus the additional amount.

That is real cap, lookup, multiplication, and addition logic, not a parameter
passthrough. The size diagnostic is also real:
`spm_unit_size.py:10-11` returns `spm_unit.nb_persons()`.

The executable PE-US 1.767.3 wheel contains byte-identical reviewed variable
and parameter bodies. Installed-file SHA-256 identities are:

| PolicyEngine source | SHA-256 | Reviewed current value |
|---|---|---|
| `nj_wfnj_payment_levels.py` | `a356c835aaaa01068e6679639de56a5208d85242bfeb0fee1c0cf23f10e1ae20` | cap, lookup, multiply, add |
| `max_household_size.yaml` | `f5119b37c4085ff0bb9e67f1578c06da830a6e0262bc6303b6520c5e78ca9e73` | 8 |
| `payment_levels/amount.yaml` | `c1a4a46c92124541ef3f431c3acd628d946e014c9c691521cc7dad2aef418ded` | `[214, 425, 559, 644, 728, 814, 894, 961]` |
| `payment_levels/additional_person.yaml` | `42b942af6ee26ccbe3be7b6f8cc8b9c061dd0473fee2c272acf9383b6bed5474` | $66 |

The comparison is like-for-like at the maximum-payment-level boundary:

- Axiom:
  `table[N]` for `N <= 8`, otherwise `table[8] + (N - 8) * $66`;
- PolicyEngine:
  `payment_levels.amount[min(N, 8)] +
  (N - min(N, 8)) * additional_person`; and
- the adapter realizes the RuleSpec integer `N` as exactly `N` people in one
  PolicyEngine SPM unit, then asserts that PolicyEngine's own
  `spm_unit_size == N`.

Exact registered run:

```sh
UV_OFFLINE=1 \
UV_CACHE_DIR=/private/tmp/x2-nj-wfnj-max-uv-cache \
PYTHONPATH=/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/x2-nj-wfnj-max-axiom-oracles \
/Users/maxghenis/.cache/uv/archive-v0/KHsnHQNgjRDE2PQFz-DN-/bin/python \
  scripts/run_comparison.py us-nj-wfnj-payment-level-grid \
  --output-dir /private/tmp/x2-nj-wfnj-max-oracle-receipts-final3 \
  --summary
```

The runner verified the pinned RuleSpec commit and tree before comparison.
Receipt:
`axiom-policyengine-us-nj-wfnj-payment-level-grid-all-2026-07-27.json`,
SHA-256
`5b67928d7b973958af134278e22d23a3a8fe5c5ff947fd56f06e3e1411ccde78`.

| Assistance-unit size | Axiom | PolicyEngine | Difference | Result |
|---:|---:|---:|---:|---|
| 1 | $214 | $214 | $0 | match |
| 2 | $425 | $425 | $0 | match |
| 3 | $559 | $559 | $0 | match |
| 4 | $644 | $644 | $0 | match |
| 5 | $728 | $728 | $0 | match |
| 6 | $814 | $814 | $0 | match |
| 7 | $894 | $894 | $0 | match |
| 8 | $961 | $961 | $0 | match |
| 9 | $1,027 | $1,027 | $0 | match |
| 10 | $1,093 | $1,093 | $0 | match |

Receipt result and derived disposition counts:

```yaml
comparison_count: 10
match_count: 10
mismatch_count: 0
error_count: 0
unexplained_mismatch_count: 0
axiom_attributed_mismatch_count: 0
match_rate_percent: 100
```

The last two counts derive from the empty `mismatches` list. Focused registry
and runner tests passed `43 passed`; Ruff check passed the touched Python
surfaces, and the two new Python files pass Ruff format check. No generated
report, dashboard, manifest, or population result is committed.

## 3. `exercised`

**Verdict: holds, with a deliberately small census.**

N.J.A.C. 10:90-3.3(b) is a one-input schedule with eight explicit cells and a
linear continuation. The honest census is therefore every listed size plus
two continuation sizes:

| Input dimension | Values | What it exercises |
|---|---|---|
| assistance-unit size | 1, 2, 3, 4, 5, 6, 7, 8 | every Schedule II table cell, including the last listed size |
| assistance-unit size | 9 | first person above the table; exactly one $66 increment |
| assistance-unit size | 10 | second person above the table; verifies repeated increments rather than a one-time add-on |

Every bridged or constant dimension is declared:

| Dimension | Treatment |
|---|---|
| assistance-unit size | **Varied observed input:** positive integers 1 through 10. RuleSpec receives `#input.assistance_unit_size`; PolicyEngine receives exactly that many people. |
| entity bridge | **Bridged:** one RuleSpec `TanfUnit` maps to one PolicyEngine `SPMUnit`; the comparison asserts PE's computed member count. |
| valid numeric domain | **Restricted:** `N >= 1`. The source table begins at one and the RuleSpec node has no local lower-bound guard; zero and negative sizes are out of scope, not silent passing cases. |
| maximum listed size | **Constant and verified:** 8 in the provision, RuleSpec, and PolicyEngine. |
| Schedule II values | **Constants and verified:** all eight current values are asserted before comparison. |
| additional-person amount | **Constant and verified:** $66 per person above eight. |
| time | **Constant:** January 2026, a month in the current version. No historical schedule claim is made. |
| state | **Constant:** New Jersey. |
| people and ages | **Scaffolding:** size 1 uses one age-10 member; sizes 2-10 use one age-40 head plus age-10 members, keeping every profile in a dependent-child family context. Ages do not enter `nj_wfnj_payment_levels`. |
| memberships | **Scaffolding:** the same people are placed in one SPM unit, household, tax unit, and family so entity realization is explicit. |
| dependent-child status | **Scope boundary:** the source describes families with dependent children and the profiles stay in that context, but neither compared payment-level formula adjudicates categorical eligibility. |
| Schedule I and income/resources | **Outside scope:** no initial-income threshold, countable income, resource rule, or eligibility predicate is compared. |
| reporting, FPL, and agency action | **Outside scope:** the six-month reporting exception, 130 percent FPL rule, and duty to act on a reported change are not inputs to this numeric node. |
| final WFNJ benefit and take-up | **Outside scope:** `nj_wfnj`, income subtraction, eligibility gates, and behavioral take-up are not substituted for the named intermediate variable. |

The direct companion file
`us-nj/regulations/njac-10-90/10-90-3/3.test.yaml` contains the same ten
one-input facts at lines 57-116. Its Git blob at the implementation pin is
`27bc7ee63ff8fc990993f4399850e9607f723b89`; file SHA-256 is
`c32e49799bdcd87389d34e924b1fbcbd2a1ad178b05d7bbeae7bb68a0a0b7c77`.

The repository-pinned
`axiom-encode@3869d66d009f52258be35901edbef370e65a399c` and
`axiom-rules-engine@ffd8213271947b0189a9dd61a055c1e0e78908a0` toolchain ran:

```sh
CARGO_NET_OFFLINE=true \
PYTHONPATH=/private/tmp/x2-nj-toolchain/axiom-encode/src:/private/tmp/x2-nj-wfnj-max-receipt-path \
/Users/maxghenis/TheAxiomFoundation/axiom-encode/.venv/bin/python \
  -c 'from axiom_encode.entrypoint import main; raise SystemExit(main())' \
  test \
  --root /private/tmp/x2-nj-wfnj-max-companion/rulespec-us \
  --axiom-rules-engine-path /private/tmp/x2-nj-toolchain/axiom-rules-engine \
  /private/tmp/x2-nj-wfnj-max-companion/rulespec-us/us-nj/regulations/njac-10-90/10-90-3/3.test.yaml
```

Result: `RuleSpec companion tests passed: 1 file(s), 14 case(s)`. The total is
the ten candidate cases plus four pre-existing broad-section cases. Repository
layout tests also passed `9 passed`.

## 4. `closed`

**Verdict: holds for the candidate's repository frontier.**

Declared root and frontier:

```yaml
roots:
  - us-nj/regulation/njac-10-90/10-90-3.3
frontier:
  rule: delimiter-safe exact root or root + "/" descendants
  raw_inventory_records: 1
  unique_provisions: 1
summary:
  encoded: 1
  excluded: 0
  pending: 0
```

The ledger is:

```yaml
rows:
  - citation: us-nj/regulation/njac-10-90/10-90-3.3
    heading: WFNJ/TANF-initial allowable maximum income and maximum benefit payment levels (Schedules I and II)
    status: encoded
    encoded_by:
      - us-nj/regulations/njac-10-90/10-90-3/3.yaml
    node: us-nj:regulations/njac-10-90/10-90-3/3#tanf_maximum_benefit_payment_level
    note: >-
      The candidate is the Schedule II numeric maximum. The corpus has no
      delimiter-safe descendants beneath this section path.
findings:
  - One raw inventory occurrence is one unique citation path; there are no duplicate records to classify.
  - The module also encodes Schedule I and financial-eligibility outputs, but those are not candidate outputs.
scope_exclusions:
  - text: the county/municipal agency shall act on a voluntarily reported change
    reason: >-
      Procedural agency action is not a numeric Schedule II output and has no
      independent descendant citation path in the corpus inventory.
```

This is the certified-nodes schema's source-side criterion: every citation
path under the declared root is encoded, excluded with reason, or pending,
with zero pending. It is not a claim that the one numeric node operationalizes
every normative sentence in § 3.3, and it is not composed-program closure for
the final WFNJ benefit.

If a human reviewer interprets `closed` to require operationalization of every
obligation embedded in the section body rather than closure of the candidate's
citation-path frontier, this criterion must be changed to pending. Under that
broader interpretation only 3 of 5 criteria hold.

## 5. `executable`

**Verdict: does not hold.**

The released-tag format and arithmetic probe passes, but the literal criterion
requires a **published one-output artifact** executed with the **released
binary** by a stranger. The only literal one-output artifact available here is
a deterministic local artifact compiled from a temporary, unpublished slice.

### Why the repository module is not a one-output program

The section module has four derived outputs:

1. `tanf_initial_maximum_allowable_income_level`;
2. `tanf_maximum_benefit_payment_level`;
3. `tanf_initial_financial_eligibility_exists`; and
4. `tanf_financial_eligibility_exists`.

The exact `axiom-compose@fabe0b3b3fd6e90d3e8f075516f9b668f524f711`
program spec selected only the candidate output, but composition imports the
whole module and does not prune unrelated derived rules. The composed YAML
has SHA-256
`0d91c537ee57f6cb9e21de708da66bdea408c7b82746278c309bc0f7bc875576`;
released v0.1.1 compiles it to a four-derived-output artifact with SHA-256
`50f82f9027243c98c48449b487a4ea1636dd1d1c1fb193ad02f6b0ac42a4ad5c`.
That broad artifact does not satisfy the requested one-output shape.

The probe therefore made a faithful temporary slice containing only the
listed-size cap, Schedule II table, $66 continuation, and target derived rule.
The temporary source has SHA-256
`5e736e1c97efaa9b3d5ce21d9ee6fd3df4f6c93bf0198ef1ad8b2d7449aa537d`.
It is not committed RuleSpec source and is not publishable evidence by itself.

### Local released-v0.1.1 probe

The clean annotated engine tag `v0.1.1` resolves to tag object
`bdd225c4576ad51c127a10a6516675b09b2fae8d` and peeled commit
`e3e2da83222463d9b68b0681c00820e9d412c011`, source tree
`62014a67b4540c9a5b6e2812838b4ae174bd3e07`. `Cargo.lock` SHA-256 is
`948f4add115a74e96164c5ee2894ee2acfc3dbe1172714001f4df2c5de34d248`.
It was built fresh, offline, and locked:

```sh
cargo build --release --locked --bin axiom-rules-engine
```

The resulting local binary reports `axiom-rules-engine 0.1.1` and has SHA-256
`c1ea7e6c7984df06beef964e4923fa00ca3a4a1aa6e213e561a026ed558c452f`.
This is the exact released source tag, not a development-engine substitute;
the hash describes the local build, not an official cargo-dist asset.

Exact compile:

```sh
/private/tmp/nj-wfnj-v011.AcF6jo/engine-src/target/release/axiom-rules-engine \
  compile \
  --program /private/tmp/nj-wfnj-v011.AcF6jo/rulespec-us/us-nj/regulations/njac-10-90/10-90-3/3.yaml \
  --output /private/tmp/nj-wfnj-v011.AcF6jo/nj-wfnj-one-output.fresh-build.compiled.json
```

Receipt:

```yaml
engine_version: 0.1.1
artifact_format_version: 2
derived_output_count: 1
derived_output: us-nj:regulations/njac-10-90/10-90-3/3#tanf_maximum_benefit_payment_level
artifact_sha256: 3af5f1d4968b80ea0e9dd5fd1e5696ace78b041f9c3d29fb066cd19d8247c0ba
deterministic_recompile_sha256: 3af5f1d4968b80ea0e9dd5fd1e5696ace78b041f9c3d29fb066cd19d8247c0ba
publication_status: local and unpublished
```

The one-input request is:

```json
{
  "mode": "explain",
  "dataset": {
    "inputs": [{
      "name": "us-nj:regulations/njac-10-90/10-90-3/3#input.assistance_unit_size",
      "entity": "TanfUnit",
      "entity_id": "tanf_unit:1",
      "interval": {"start": "2026-01-01", "end": "2026-02-01"},
      "value": {"kind": "integer", "value": 10}
    }],
    "relations": []
  },
  "queries": [{
    "entity_id": "tanf_unit:1",
    "period": {
      "period_kind": "month",
      "start": "2026-01-01",
      "end": "2026-01-31"
    },
    "outputs": [
      "us-nj:regulations/njac-10-90/10-90-3/3#tanf_maximum_benefit_payment_level"
    ]
  }]
}
```

Exact run as executed:

```sh
printf '%s\n' '{"mode":"explain","dataset":{"inputs":[{"name":"us-nj:regulations/njac-10-90/10-90-3/3#input.assistance_unit_size","entity":"TanfUnit","entity_id":"tanf_unit:1","interval":{"start":"2026-01-01","end":"2026-02-01"},"value":{"kind":"integer","value":10}}],"relations":[]},"queries":[{"entity_id":"tanf_unit:1","period":{"period_kind":"month","start":"2026-01-01","end":"2026-01-31"},"outputs":["us-nj:regulations/njac-10-90/10-90-3/3#tanf_maximum_benefit_payment_level"]}]}' |
/private/tmp/nj-wfnj-v011.AcF6jo/engine-src/target/release/axiom-rules-engine \
  run-compiled \
  --artifact /private/tmp/nj-wfnj-v011.AcF6jo/nj-wfnj-one-output.fresh-build.compiled.json
```

The command exits 0, reports requested/actual mode `explain`, returns decimal
`1093` USD, and traces the output to
`N.J.A.C. 10:90-3.3(b), Schedule II`. Thus there is no released-v0.1.1 format
or arithmetic gap in the local probe.

### Hand-checkable golden case

For an assistance unit of **10 people**:

```text
1. Maximum explicitly listed size                         = 8 people
2. People above the table                       10 - 8   = 2 people
3. Schedule II maximum at size 8                          =   $961/month
4. Additional-person amount                    2 × $66   =   $132/month
5. Maximum benefit payment level             $961 + $132 = $1,093/month
```

The companion fixture, PolicyEngine grid, and local released-v0.1.1
one-output probe all return **$1,093 per month**.

### Publication search and blocking findings

The local repository contains 222 fetched `program-artifacts-*` tags. The tag
for the pinned main commit, `program-artifacts-ecb057ef35ab`, contains 33
program specs and zero paths under `programs/us-nj`. A full local history
search finds zero commits touching `programs/us-nj` and zero program-history
hits for `tanf_maximum_benefit_payment_level`.

1. There is no committed one-output WFNJ program source. The current § 3.3
   module compiles four derived outputs, so meeting the literal shape requires
   a module split/refactor or a future composition-pruning capability. This
   evidence sprint does not authorize toolchain changes.
2. The faithful one-output slice and its artifact are temporary and
   unpublished. A local artifact hash and successful local released-tag run
   cannot be substituted for a stranger-path publication receipt.
3. There is no published NJ WFNJ artifact URL for a fresh consumer to pair
   with the released v0.1.1 engine.

Until a provenance-stamped one-output artifact is published and a stranger
using released v0.1.1 reproduces $1,093, `executable.holds` must remain false
and this candidate must not be added to `certified-nodes.yaml`.
