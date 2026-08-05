# Massachusetts SNAP medical-deduction certification evidence

**Decision status:** evidence assembly only; **4 of 5 criteria hold**. This is
not a certification or attestation. The `executable` criterion is false, so a
human must not add this node to `launch-readiness/certified-nodes.yaml`.

**Candidate scope:** only
`us-ma:regulations/106-cmr/364/400/block-1#medical_expense_deduction`, the
January 2026 monthly deduction selected from the medical-expense table in
106 CMR 364.400(C). It does not certify the construction or verification of an
allowable medical expense, any other deduction in 364.400, SNAP eligibility,
or the eventual benefit.

| Criterion | Verdict | Evidence |
| --- | --- | --- |
| `provision_rooted` | **holds** | The exact declared citation path resolves in both corpus inventory occurrences to byte-identical official provision text containing the $35/$155/$190 table. |
| `conformant` | **holds** | The registered five-case grid matches PolicyEngine-US `snap_excess_medical_expense_deduction` 5/5 with zero mismatches on the declared bridge. |
| `exercised` | **holds** | The small census is exactly $0, $35, $36, $190, and $191; every bridged and held dimension is declared below. |
| `closed` | **holds, narrowly** | The required candidate citation-path frontier is one encoded path, zero excluded, zero pending. This is not a claim of semantic completeness for the monolithic 364.400 provision body. |
| `executable` | **does not hold** | The released-v0.1.1 local probe returns the golden $156 value, but the unchanged module compiles to 11 outputs and the artifact is local and unpublished. |

The review-template block below follows the employee-Medicare evidence
package. It is not ready to paste into the certification registry:
`attested_by` remains a placeholder and `criteria.executable.holds` is false.

```yaml
- node: us-ma:regulations/106-cmr/364/400/block-1#medical_expense_deduction
  label: Massachusetts SNAP medical-expense deduction
  provision: 106 CMR 364.400(C)
  corpus_citation_path: us-ma/regulation/106-cmr/364/400/block-1
  mode: attested
  attested_by: <name>
  attested_at: 2026-07-28
  pinned:
    rulespec_us: 738015e4f75d0f2cf20507e50601dbf4a0ba0fbb
    corpus: db12795577c5809009168982cf8a72fb58440620
    engine: v0.1.1
    artifact: sha256:840cb8ec694600ad478e5befaeb81c1d791791157510ffa57acf97fe845e7a5b
  criteria:
    provision_rooted:
      holds: true
      evidence: us-ma/snap/v1-medical-deduction-evidence.md#1-provision_rooted
    conformant:
      holds: true
      evidence: us-ma/snap/v1-medical-deduction-evidence.md#2-conformant
    exercised:
      holds: true
      evidence: us-ma/snap/v1-medical-deduction-evidence.md#3-exercised
    closed:
      holds: true
      evidence: us-ma/snap/v1-medical-deduction-evidence.md#4-closed
    executable:
      holds: false
      evidence: us-ma/snap/v1-medical-deduction-evidence.md#5-executable
```

The RuleSpec pin is the implementation-and-fixture commit, not this narrative
evidence commit. Its tree is
`87220d7d776b9a330b91bae3c42e929adf4ab35a`. The artifact hash pins a
byte-reproducible **local probe artifact**; it is not a publication claim.

## 1. `provision_rooted`

**Verdict: holds.**

The defining module is
`us-ma/regulations/106-cmr/364/400/block-1.yaml` (Git blob
`2ffeea17c6739dd846f2de35e33366c78788e768`, file SHA-256
`c9222dbbd701c29062ce416e4178775c02207301cd9b970f0d581271ebc37e34`).
It declares:

- formal corpus resolution at line 6:
  `us-ma/regulation/106-cmr/364/400/block-1`;
- the $35, $190, and $155 parameters at lines 24-76; and
- the Household/Month/USD output and piecewise formula at lines 78-96.

The exact node identifier is
`us-ma:regulations/106-cmr/364/400/block-1#medical_expense_deduction`. Its only
free RuleSpec fact is
`#input.verified_medical_expense_amount`.

### Corpus resolution across every inventory occurrence

The corpus was inspected at
`axiom-corpus@db12795577c5809009168982cf8a72fb58440620`. A delimiter-safe
citation-path scan of all 691 inventory JSON files finds exactly two raw
occurrences and one unique path:

| Raw row | Inventory location | Citation path | Resolving provision |
| ---: | --- | --- | --- |
| 1 | `data/corpus/inventory/us-ma/regulation/2026-05-28.json:5090` | `us-ma/regulation/106-cmr/364/400/block-1` | corresponding provisions JSONL line 223, id `e83164f7-1126-5a15-b1e1-15d96849f1fb` |
| 2 | `data/corpus/inventory/us-ma/regulation/2026-07-24-ma-dta-regulations-snap-current-union.json:5438` | `us-ma/regulation/106-cmr/364/400/block-1` | corresponding provisions JSONL line 223, id `60dca403-0771-56e8-a42b-2906d6983c62` |

For each inventory row, both `citation_path` and `source_path` match its
provision record. The inventory rows also carry the same source-PDF SHA-256,
`5b010364fc013acd1cb412bab672cd9656215772087095dcae007ceeee413343`.
The two 12,806-byte body strings are byte-identical. Extracted with `jq -r`
(including its terminal newline), each body has SHA-256
`9e3d69d1db9913eb137b451dd7abcca074c3f7f7fa6b8eb8af8513e69cc69ecb`.

The provision body contains the operative excess-medical rule and the table:
$35 or under produces $0; over $35 through $190 produces $155; and over $190
produces the actual amount over $35. The module's short parameter excerpts are
literal. Its long proof excerpt is a normalized one-line rendering that omits
a repeated table header, so this package does not describe that long excerpt
as a byte-verbatim quote.

This path is not one of the j1 audit's three malformed Massachusetts paths:
`364/360/block-1`, `365/030/block-1`, and `366/140/block-1`. The requested
stop-on-nonresolution rule therefore does not trigger.

The two rows are overlapping ingests of one legal path. They are not two
closure obligations.

## 2. `conformant`

**Verdict: holds on the declared comparison boundary.**

The locally committed oracle registration is
`axiom-oracles@929aa84e7db51ff071bb7515fedac7790c44a731` (tree
`1ec16c047caf1e4f28e354823267d01abc975aa8`):

- `comparisons/us-ma-snap-medical-deduction-grid.yaml` registers the
  non-population suite through the period-aware
  `rulespec-policyengine-grid` runner alias;
- `scripts/generate_federal_tax_liability.py` registers the exact five cases,
  monthly periods, bridge, fixture contract, and parameter checks;
- `axiom_oracles/bridges/mappings/us.yaml` promotes the exact node from the
  contradictory `not_comparable` entry to a direct variable mapping; and
- `tests/test_federal_tax_liability_generator.py` protects the registry pin,
  period, bridge, exact fixture inputs, mapping, and output period.

The oracle commit is local because the push attempt could not resolve
`github.com`. That publication failure does not change the local comparison
result, but it is not represented as merged infrastructure.

### PolicyEngine boundary and real logic

The registered execution stack is Python 3.13,
`policyengine==4.18.9`, `policyengine-us==1.767.3`, and
`policyengine-core==3.30.3`. The exact PE-US 1.767.3 source pin is
`49d19b239a593dbac8920ac6fd80cfe33372343a`.

The correct concept is not PE's IRS itemized `medical_expense_deduction`. It is
`snap_excess_medical_expense_deduction`, an SPMUnit/Month/USD variable. Its
real formula body at
`policyengine_us/variables/gov/usda/snap/income/deductions/snap_excess_medical_expense_deduction.py:16-31`
(file SHA-256
`e6120415428e8c60eb43ce62d9ada8741b8b23235be7ef5596f47ce38a03e1c2`)
does all of the following:

1. reads elderly and disabled status for each member;
2. reads allowable medical expenses;
3. sums expenses only for elderly or disabled members;
4. subtracts the $35 disregard with a zero floor;
5. selects the state's standard;
6. makes that standard claimable only for positive excess; and
7. returns the greater of excess and the standard.

This is branching and arithmetic logic, not a parameter passthrough.
`snap_allowable_medical_expenses.py:4-30` is an annual Person variable that
adds medical-insurance premiums and `other_medical_expenses`. The executed
parameter files supply a monthly disregard of $35 and the Massachusetts
standard of $155; the bridge also verifies the USDA elderly threshold is 60.

The r1 sweep read newer PE-US source
`61cc1e63323579deaa4a5070185bdfafcd7e838a` (version 1.782.3), whose lines
16-35 add student and prorated-member filters. That newer source is not
silently substituted for the registered 1.767.3 receipt. The comparison domain
declares both newer-only dimensions false. As a separate source-drift
diagnostic, the same situation was run under PE-US 1.779.4: it returned
`is_snap_ineligible_student=false`,
`is_snap_prorated_income_member=false`, and the same $156 golden output.
That diagnostic adjudicates the source difference; it is not the registered
oracle receipt.

### Registered receipt

The runner first verified the clean pinned RuleSpec tree, then read the five
engine-verified companion expectations and calculated the named PolicyEngine
variable for `2026-01`. It does not execute RuleSpec once per oracle row; the
separate released-engine fixture receipt below establishes those companion
expectations.

Exact registered command:

```sh
UV_OFFLINE=1 \
UV_CACHE_DIR=/private/tmp/medicare-uv-cache.EMOePi \
/Users/maxghenis/TheAxiomFoundation/axiom-oracles/.venv/bin/python \
  scripts/run_comparison.py us-ma-snap-medical-deduction-grid \
  --output-dir /private/tmp/ma-medical-grid-run.VBvieG --summary
```

The runner verified RuleSpec tree
`87220d7d776b9a330b91bae3c42e929adf4ab35a` for upstream commit
`738015e4f75d0f2cf20507e50601dbf4a0ba0fbb`. Receipt:
`axiom-policyengine-us-ma-snap-medical-deduction-grid-all-2026-07-27.json`,
SHA-256
`86b585c42201dce85285fbd2a349d247535a03b464316b8ffbbb62c4188a81ef`.

| Monthly verified amount | Why included | RuleSpec fixture | PolicyEngine | Difference | Result |
| ---: | --- | ---: | ---: | ---: | --- |
| $0 | zero | $0 | $0 | $0 | match |
| $35 | inclusive disregard boundary | $0 | $0 | $0 | match |
| $36 | first dollar above disregard | $155 | $155 | $0 | match |
| $190 | inclusive standard-band ceiling | $155 | $155 | $0 | match |
| $191 | first dollar in actual-over-$35 branch | $156 | $156 | $0 | match |

Receipt disposition:

```yaml
comparison_count: 5
match_count: 5
mismatch_count: 0
error_count: 0
unexplained_mismatch_count: 0
match_rate_percent: 100
```

No mismatch required statutory adjudication. The newer-source diagnostic above
is a disclosed version-boundary check, not a hidden mismatch disposition.

## 3. `exercised`

**Verdict: holds, with a deliberately small census.**

The legal function has two monetary boundaries and no other input. The five
cases are the zero, each inclusive endpoint, and each first dollar after an
endpoint. Adding household profiles or interior dollar values would pad rather
than strengthen the statutory census.

Every bridged or held dimension is declared:

| Dimension | Treatment |
| --- | --- |
| verified medical amount | **Varied RuleSpec boundary fact:** $0, $35, $36, $190, $191 per month. It is already agency-verified and eligible. |
| eligibility and expense classification | **Upstream boundary:** elderly/disabled qualification, allowability, non-reimbursement, special-diet exclusion, and 364.450(A) verification are not recomputed by this node. |
| RuleSpec entity | **Constant:** one Household. |
| PolicyEngine entity | **Bridge:** that Household is represented by one SPMUnit with one Person; one-member tax-unit, family, and household scaffolding supplies relations only. |
| member age | **Constant and verified:** 60, meeting PE's USDA elderly threshold. |
| disability | **Constant:** false; age alone opens the eligible-member branch. |
| citizenship | **Constant:** `CITIZEN`, closing the alien-proration branch in newer PE logic. |
| student/prorated membership | **Restricted-domain declarations:** false. PE-US 1.767.3 does not use these later-added filters; the newer diagnostic confirms both false for the situation. |
| state | **Constant:** Massachusetts, selecting the $155 standard. |
| time | **Constant:** January 2026. No all-history claim is made from the module's open-ended effective date. |
| annual/monthly surface | **Bridge:** RuleSpec monthly amount × 12 is supplied as PE annual `other_medical_expenses`; PE output is read for `2026-01`. |
| premium paths | **Constants:** `health_insurance_premiums=0`, `health_insurance_premiums_without_medicare_part_b=0`, and `medicare_enrolled=false`, preventing hidden premium additions. |
| PE disregard and standard | **Constants and checked:** $35 per month and Massachusetts $155. |
| income, benefit, and other deductions | **Outside scope:** none is supplied or compared. |
| output | **Direct mapping:** RuleSpec Household monthly money to PE SPMUnit monthly `snap_excess_medical_expense_deduction`. |

The companion cases at
`us-ma/regulations/106-cmr/364/400/block-1.test.yaml:1-30` assign the sole
RuleSpec input fact in every row.

## 4. `closed`

**Verdict: holds for the required candidate citation-path frontier.**

```yaml
roots:
  - us-ma/regulation/106-cmr/364/400/block-1
frontier:
  rule: exact or delimiter-safe citation-path descendant
  unique_paths: 1
  raw_inventory_occurrences: 2
rows:
  - citation: us-ma/regulation/106-cmr/364/400/block-1
    status: encoded
    encoded_by:
      - us-ma/regulations/106-cmr/364/400/block-1.yaml
    note: >-
      Both raw rows are duplicate ingests of this one legal path. The candidate
      node and its three table parameters are defined in the named module.
summary:
  encoded: 1
  excluded: 0
  pending: 0
```

No second row is invented for duplicate ingestion. There is no descendant
citation path under the declared root.

This is the r1/v1 candidate-path meaning of closure. The single provision
record is a monolithic body containing all of 106 CMR 364.400, including many
rules this candidate does not compute. This package therefore does **not**
claim semantic completeness for that body, closure of the aggregate
Massachusetts SNAP program, or certification of all 11 outputs in the module.
If the launch reviewer interprets `closed` as full-provision semantic closure
rather than the required candidate citation-path ledger, this criterion must
be changed to false and the package becomes **3 of 5**.

## 5. `executable`

**Verdict: does not hold.**

The local format and arithmetic probes pass, but there is no evidenced
published one-output artifact on a released-binary stranger path.

### Released-v0.1.1 local probe

The clean annotated engine tag `v0.1.1` resolves to tag object
`bdd225c4576ad51c127a10a6516675b09b2fae8d`, peeled commit
`e3e2da83222463d9b68b0681c00820e9d412c011`, and tree
`62014a67b4540c9a5b6e2812838b4ae174bd3e07`. The local tag-built binary
reports `axiom-rules-engine 0.1.1` and has SHA-256
`c1ea7e6c7984df06beef964e4923fa00ca3a4a1aa6e213e561a026ed558c452f`.
It is an exact released-source build, not a development engine, but it was not
freshly downloaded as an official cargo-dist asset.

The implementation commit was exported under a canonical stranger-style
`rulespec-us/us-ma/...` path because v0.1.1 infers legal IDs from that layout:

```sh
ma_probe_dir=$(mktemp -d /private/tmp/ma-snap-medical-v011-exact.XXXXXX)
mkdir -p "$ma_probe_dir/rulespec-us"
git archive 738015e4f75d0f2cf20507e50601dbf4a0ba0fbb \
  us-ma/regulations/106-cmr/364/400/block-1.yaml |
  tar -x -C "$ma_probe_dir/rulespec-us"

engine_bin=/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/engine-v0.1.1/target/release/axiom-rules-engine
"$engine_bin" compile \
  --program "$ma_probe_dir/rulespec-us/us-ma/regulations/106-cmr/364/400/block-1.yaml" \
  --output "$ma_probe_dir/us-ma-snap-medical.compiled.json"
```

Compile receipt:

```yaml
engine_version: 0.1.1
artifact_format_version: 2
fast_path_strategy: generic_bulk
derived_output_count: 11
artifact_sha256: 840cb8ec694600ad478e5befaeb81c1d791791157510ffa57acf97fe845e7a5b
deterministic_recompile_sha256: 840cb8ec694600ad478e5befaeb81c1d791791157510ffa57acf97fe845e7a5b
```

The 11 outputs are the medical deduction plus ten unrelated 364.400
deduction/SUA rules. Released v0.1.1 has no output-pruning compile flag, so the
unchanged committed module cannot truthfully be described as a one-output
program. No synthetic extracted module was substituted.

The golden request was:

```json
{
  "mode": "explain",
  "dataset": {
    "inputs": [{
      "name": "us-ma:regulations/106-cmr/364/400/block-1#input.verified_medical_expense_amount",
      "entity": "Household",
      "entity_id": "household:1",
      "interval": {"start": "2026-01-01", "end": "2026-02-01"},
      "value": {"kind": "decimal", "value": "191"}
    }],
    "relations": []
  },
  "queries": [{
    "entity_id": "household:1",
    "period": {
      "period_kind": "month",
      "start": "2026-01-01",
      "end": "2026-02-01"
    },
    "outputs": [
      "us-ma:regulations/106-cmr/364/400/block-1#medical_expense_deduction"
    ]
  }]
}
```

`run-compiled` exited zero in requested and actual `explain` mode, with no
fallback. It returned decimal USD `156` and traced the value to the
106 CMR 364.400 medical-expense table. Request-with-newline SHA-256:
`4abe0e54581222a9b68cb4b94c221c4dcb6f7a0492bd790ec2d52ab9c2771761`;
pretty-response SHA-256:
`c05ad7c44352f2039fa4b724c73531547b33473f48f35623feec90c196b7247f`.

### Hand-checkable golden case

Premise: the agency has verified **$191** of eligible monthly medical expense
for the candidate boundary fact.

```text
$191 is greater than $190.
Therefore the table selects "actual amount over $35," not the $155 band.
$191 - $35 = $156.
PolicyEngine excess = max($191 - $35, $0) = $156.
PolicyEngine comparison = max($156 excess, $155 MA standard) = $156.
RuleSpec fixture = PolicyEngine receipt = released-v0.1.1 local run = $156.
```

The $190 case returns $155, so $191 checks the exact upper seam rather than
only an interior arithmetic point.

### Blocking findings

1. The existing module compiles to 11 outputs. No allowed one-output medical
   program spec exists, and the launch freeze prohibited adding anything under
   `programs/us-*/snap/`.
2. The deterministic artifact is local and unpublished. Repository history
   exposes only the aggregate Massachusetts SNAP program, whose declared
   outputs are `snap_eligible` and `snap_benefit`; this node merely appears in
   its scope.
3. A fresh anonymous official-v0.1.1 asset and release-artifact check could not
   be completed because `api.github.com` was unreachable. The exact tagged
   source build is a useful probe, not a substitute for that stranger path.

Until a provenance-stamped one-output artifact is published and run by a
stranger with the official released binary, `executable.holds` remains false
and this node must not enter `certified-nodes.yaml`.

## Validation and scope discipline

- Released-v0.1.1 companion run:
  `axiom-encode test .../block-1.test.yaml --root .../rulespec-us/us-ma
  --axiom-rules-engine-path .../engine-v0.1.1 --json` returned one test file,
  33 cases, one compiled program, and zero failures.
- Oracle focused tests:
  `python -m pytest -q tests/test_federal_tax_liability_generator.py` returned
  `26 passed`.
- Oracle Ruff checks on the changed generator, runner, and test returned
  `All checks passed`.
- The registered grid returned 5/5 matches, zero mismatches, and zero errors.
- Both repositories pass `git diff --check` and were clean after their
  coherent commits.
- No population suite was run or changed. No generated dashboard/report was
  committed.
- No file under `programs/`, no certified-node registry, toolchain, CI,
  CODEOWNERS, or dependency pin was changed.

## Handoff status

The RuleSpec evidence was committed locally on `x3-ma-snap-medical`; the
oracle grid was committed locally on `closure/ma-snap-medical-grid`. Pushes
from both worktrees failed because the sandbox could not resolve
`github.com`. No remote branch exists from this session, so no draft PR was
opened or represented as opened.
