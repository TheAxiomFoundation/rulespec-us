# Washington TANF payment-standard certification evidence

**Decision status:** evidence assembly only; **4 of 5 criteria hold**. This is
not a certification or an attestation. A human may make that decision at the
2026-07-28 decision point only after the `executable` blocker below is closed.
`launch-readiness/certified-nodes.yaml` was not changed.

**Candidate scope:** only
`us-wa:regulations/388/388-478/388-478-0020#cash_assistance_unit_maximum_monthly_payment_standard`,
the current Washington maximum monthly payment-standard table used here for
TANF. It does not certify TANF eligibility, income or resource tests,
disregards, sanctions, proration, grant calculation, or an effective-benefit
pipeline. WAC 388-478-0020 also names SFA and RCA, but this evidence package
tests the named PolicyEngine TANF variable and makes no broader certification
claim for those programs.

| Criterion | Verdict | Evidence |
|---|---|---|
| `provision_rooted` | **holds** | Exact RuleSpec module and citation path resolve through both corpus inventory occurrences. |
| `conformant` | **holds** | Registered 11-case grid against PolicyEngine `wa_tanf_payment_standard`: 11 matches, zero mismatches or errors. |
| `exercised` | **holds** | Sizes 1 through 11 exercise every table cell once and the first value above the “10 or more” boundary. |
| `closed` | **holds** | Two raw corpus records deduplicate to one legal citation path; that path is encoded, with zero pending. |
| `executable` | **does not hold** | Released-tag local compile and golden run pass, but the artifact is unpublished and no official-binary stranger path exists. |

The block below copies the certified-node entry shape. It is a review template,
not an entry ready to paste: `attested_by` remains a placeholder and
`criteria.executable.holds` is false.

```yaml
- node: us-wa:regulations/388/388-478/388-478-0020#cash_assistance_unit_maximum_monthly_payment_standard
  label: Washington TANF maximum monthly payment standard
  provision: WAC 388-478-0020
  corpus_citation_path: us-wa/regulation/388/388-478/388-478-0020
  mode: attested
  attested_by: <name>
  attested_at: 2026-07-28
  pinned:
    rulespec_us: 65bb172054984d83a5329d1d05cc5b1c605c0479
    corpus: db12795577c5809009168982cf8a72fb58440620
    engine: v0.1.1
    artifact: sha256:0b3dca0bd174e4a6ea928b1ffc8276aa3a6dcc1193ed15e8a8be262a30e1b631
  criteria:
    provision_rooted:
      holds: true
      evidence: us-wa/tanf/v1-payment-standard-evidence.md:70
    conformant:
      holds: true
      evidence: us-wa/tanf/v1-payment-standard-evidence.md:177
    exercised:
      holds: true
      evidence: us-wa/tanf/v1-payment-standard-evidence.md:297
    closed:
      holds: true
      evidence: us-wa/tanf/v1-payment-standard-evidence.md:352
    executable:
      holds: false
      evidence: us-wa/tanf/v1-payment-standard-evidence.md:401; local load and value pass, published-artifact stranger path blocked
```

The RuleSpec pin is the implementation-and-fixture commit, not this narrative
evidence commit. Its tree is
`05ffa5a3da111ad6247074bc3d3f6347ed5e4867`. The artifact hash pins a
byte-reproducible **local probe artifact**; it is not a publication claim.

All conformance and exercise claims in this package are limited to June 2026.
The RuleSpec module uses the repository's sentinel
`effective_from: 0001-01-01`, while the audited PolicyEngine table's current
values begin on 2024-01-01. This package does not claim historical parity.

## 1. `provision_rooted`

**Verdict: holds.**

The defining module is
`us-wa/regulations/388/388-478/388-478-0020.yaml` (Git blob
`835bce8b66eac0a01651cdd4de2b5bdcfbe53eae`, file SHA-256
`08acd66f02914850317de18f204c2d7ed551746002bb37af59d5c02453ff5406`).
It declares:

- the formal corpus path
  `us-wa/regulation/388/388-478/388-478-0020` at line 6;
- the final-row size floor of ten at lines 10-25;
- the “10 or more” size-cap logic at lines 27-50;
- all ten payment-standard values at lines 52-82; and
- the AssistanceUnit/Month/USD target output at lines 84-114.

The exact node identifier is
`us-wa:regulations/388/388-478/388-478-0020#cash_assistance_unit_maximum_monthly_payment_standard`.
Its sole observed input is `assistance_unit_size`.

### Corpus resolution across every inventory occurrence

Corpus was inspected at
`axiom-corpus@db12795577c5809009168982cf8a72fb58440620`, tree
`9393fe1555be6c60dd759fbb45586f65223a7087`. A delimiter-safe citation-path
scan of all 691 inventory JSON files and 142,902 inventory items finds two raw
occurrences, one unique citation path, and no descendants under
`us-wa/regulation/388/388-478/388-478-0020`.

Inventory abbreviations:

- `I-original` =
  `data/corpus/inventory/us-wa/regulation/2026-06-25-388-478.json`
- `I-dedup` =
  `data/corpus/inventory/us-wa/regulation/2026-06-25-388-478-r2026-07-15-self-contained-r2026-07-17-dedup.json`

Provision abbreviations:

- `P-original` =
  `data/corpus/provisions/us-wa/regulation/2026-06-25-388-478.jsonl`
- `P-dedup` =
  `data/corpus/provisions/us-wa/regulation/2026-06-25-388-478-r2026-07-15-self-contained-r2026-07-17-dedup.jsonl`

| Raw row | Inventory location | Citation path | Resolving provision record |
|---:|---|---|---|
| 1 | `I-original:161` | `us-wa/regulation/388/388-478/388-478-0020` | `P-original:7` |
| 2 | `I-dedup:138` | `us-wa/regulation/388/388-478/388-478-0020` | `P-dedup:5` |

Both records are active and carry:

- UUID `3a1bf803-60b9-5116-93a6-7c4ecd13acfd`;
- source URL
  `https://app.leg.wa.gov/WAC/default.aspx?cite=388-478-0020`;
- stored chapter-source SHA-256
  `375b1127bb44f4833d2270d1865ac2b67f660809af9df6b10a4f16119f574d33`;
- exact extracted-body SHA-256
  `7ac11a2d3a7a6bf43f6e21066f5fe27e3a3829d4b9f0a3ac860b851342d17c56`;
  and
- the same WAC table, from $450 for size one through $1,662 for size ten or
  more.

The source history identifies WSR 23-23-054, filed 2023-11-08 and effective
2024-01-01. There is no conflicting occurrence or descendant to adjudicate.

The checked-in reverse index maps this citation path to the module via both
`module` and `proof_atom` at
`.axiom/index/provisions_to_rules.json:34253-34260`.

Reproduction:

```sh
ref=db12795577c5809009168982cf8a72fb58440620
repo=/Users/maxghenis/TheAxiomFoundation/axiom-corpus
root=us-wa/regulation/388/388-478/388-478-0020

git -C "$repo" ls-tree -r --name-only "$ref" -- data/corpus/inventory |
while IFS= read -r file; do
  git -C "$repo" show "$ref:$file" |
  jq -r --arg file "$file" --arg root "$root" '
    .items[]? |
    select(
      .citation_path == $root or
      (.citation_path | startswith($root + "/"))
    ) |
    [$file, .citation_path, .sha256, .source_url] | @tsv
  '
done | sort

git -C "$repo" ls-tree -r --name-only "$ref" -- data/corpus/provisions |
while IFS= read -r file; do
  git -C "$repo" show "$ref:$file" |
  jq -r --arg file "$file" --arg root "$root" '
    select(
      .citation_path == $root or
      (.citation_path | startswith($root + "/"))
    ) |
    [$file, .citation_path, .metadata.status, .source_url] | @tsv
  '
done | sort
```

The repository's pending-validation fingerprint still says `passed: false`
at `.axiom/pending-validation-fingerprints.json:10652-10655`. This package
does not relabel it as an automated proof-validation pass. `provision_rooted`
rests on the independent pinned-corpus scan above.

## 2. `conformant`

**Verdict: holds.**

The registered case-grid suite is committed locally at
`axiom-oracles@637de738198bb761b552acab4128c3fe23b5bb9d`, tree
`d57e7d2da2518ca9c31f1e5d5f21822ae3085843`. Its implementation commit is
`38fadf0581bfb3eb9216a869972cc335ee4fb8ec`; the follow-up commit adds only
the generated affected-comparison registration. The oracle push attempt was
blocked because `github.com` could not be resolved, so this branch is not
published:

- `comparisons/wa-tanf-payment-standard-grid.yaml` registers the named suite;
- `comparisons/affected_map.json` registers its affected RuleSpec repositories;
- `scripts/generate_federal_tax_liability.py` registers the cases, exact
  AssistanceUnit-to-SPMUnit bridge, monthly period, and PolicyEngine parameter
  validators; and
- `tests/test_federal_tax_liability_generator.py` verifies the registry,
  one-input fixture contract, member-count bridge, parameter table, cap, and
  diagnostic output.

This is an eleven-case grid, not a population suite. It pins the clean local
RuleSpec snapshot
`65bb172054984d83a5329d1d05cc5b1c605c0479`, tree
`05ffa5a3da111ad6247074bc3d3f6347ed5e4867`.

The actual nested oracle runtime selected by `uv` was Python 3.13.9,
`policyengine==4.18.9`, `policyengine-us==1.767.3`, and
`policyengine-core==3.30.3`. The cached control-plane interpreter launching
`run_comparison.py` was Python 3.13.12; it did not replace the nested runtime.
The reviewed PolicyEngine-US source pin is
`61cc1e63323579deaa4a5070185bdfafcd7e838a`, tree
`58e468983a566d3e83aa2ac2ddf67171fa3af4fb`.

The named PolicyEngine variable has real input-sensitive logic. At
`policyengine_us/variables/gov/states/wa/dshs/tanf/benefit/wa_tanf_payment_standard.py:13-17`
it:

1. reads `spm_unit_size`;
2. caps that size with `min_(size, p.maximum_family_size)`; and
3. indexes `p.payment_standard.amount[size_capped]`.

It is not an input leaf, direct parameter return, or parameter passthrough.

The relevant PolicyEngine source blobs are:

| Source | Git blob | File SHA-256 |
|---|---|---|
| `wa_tanf_payment_standard.py` | `8de376f7ef767ed6e04c08cf27811653cdc377f8` | `660be26fa6b7feb651b5a50482066b130b7a296d3becca96b96c37dea0718a9b` |
| `payment_standard/amount.yaml` | `545dd0a0327abcc767c4d279fbfd7e2adc66de7e` | `f386565470265cd904333331eadfbcf454a9a36d7b837c36d9b32d0bc30b07e6` |
| `maximum_family_size.yaml` | `2dec8783cd6bb11a9c1dc6f7b4941fffee1725d4` | `8374838e1c3f923d38fed53032f1d25e6b80b838068a1280b483a5d821b4cb67` |

The installed PolicyEngine-US 1.767.3 copies of those three files are
byte-identical to the reviewed source pin. This statement is limited to the
three relevant files; it does not represent the full 1.767.3 package as source
commit `61cc1e6`, whose project version is 1.782.3.

The comparison is like-for-like:

- Axiom caps `assistance_unit_size` at ten and indexes the WAC table.
- The adapter creates exactly that many people in one Washington SPMUnit.
- PolicyEngine derives `spm_unit_size` from membership, caps it at ten, and
  indexes the same table.
- The adapter never directly supplies `spm_unit_size` or calculates a payment
  amount.

Registered run:

```sh
cd /private/tmp/axiom-oracles-x1-wa-tanf-standard-grid

UV_OFFLINE=1 \
UV_CACHE_DIR=/private/tmp/medicare-uv-cache.EMOePi \
/Users/maxghenis/.cache/uv/archive-v0/KHsnHQNgjRDE2PQFz-DN-/bin/python \
  scripts/run_comparison.py wa-tanf-payment-standard-grid \
  --output-dir /private/tmp/wa-tanf-registered-oracle-receipts \
  --summary
```

Receipt:
`axiom-policyengine-wa-tanf-payment-standard-grid-all-2026-07-27.json`,
SHA-256
`caf76de015d8a35b4778c5b587f2992cb74026dd0ce2c89d79b1146afd560a55`,
generated at `2026-07-27T23:11:38Z`.

| Assistance-unit size | Axiom | PolicyEngine `spm_unit_size` | PolicyEngine standard | Difference | Result |
|---:|---:|---:|---:|---:|---|
| 1 | $450 | 1 | $450 | $0 | match |
| 2 | $570 | 2 | $570 | $0 | match |
| 3 | $706 | 3 | $706 | $0 | match |
| 4 | $833 | 4 | $833 | $0 | match |
| 5 | $959 | 5 | $959 | $0 | match |
| 6 | $1,090 | 6 | $1,090 | $0 | match |
| 7 | $1,258 | 7 | $1,258 | $0 | match |
| 8 | $1,392 | 8 | $1,392 | $0 | match |
| 9 | $1,529 | 9 | $1,529 | $0 | match |
| 10 | $1,662 | 10 | $1,662 | $0 | match |
| 11 | $1,662 | 11 | $1,662 | $0 | match |

Receipt result:

```yaml
comparison_count: 11
match_count: 11
mismatch_count: 0
error_count: 0
axiom_vs_policyengine_match_rate: 100.0
```

The focused oracle tests passed `25 passed`; the affected-map registration
check plus those tests passed `26 passed`; Ruff reported all checks passed.
No generated comparison report, dashboard file, or dashboard manifest is
committed. The generated `comparisons/affected_map.json` registry metadata is
committed because the repository's deterministic registration check requires
it.

The oracle commits and receipt are local and unpublished. As in the employee
Medicare package, that transport limitation is disclosed but does not turn
eleven exact named-variable comparisons into mismatches.

## 3. `exercised`

**Verdict: holds, with a deliberately small census.**

WAC 388-478-0020 is a one-input lookup table with one cap boundary. Household
profiles, income amounts, filing statuses, or benefit-calculation scenarios
would add no legal variation to this node.

| Input region | Cases | What it exercises |
|---|---|---|
| first explicit row | size 1 | lowest lawful table row |
| interior explicit rows | sizes 2-9 | every interior table cell once |
| final explicit row | size 10 | cap threshold and final indexed row |
| “10 or more” region | size 11 | first value above the threshold; must reuse row ten |

Every bridged or constant dimension is declared:

| Dimension | Treatment |
|---|---|
| assistance-unit size | **Observed input:** integer sizes 1 through 11. |
| Axiom entity | **Constant:** one AssistanceUnit. |
| PolicyEngine entity bridge | **Bridged:** one SPMUnit containing exactly the reported number of people. |
| `spm_unit_size` | **Derived diagnostic:** never directly supplied; PolicyEngine returns 1 through 11 from membership. |
| state | **Constant:** Washington. |
| time | **Constant:** June 2026. |
| head age | **Constant scaffolding:** 30. |
| additional-member age | **Constant scaffolding:** 10. |
| tax unit, family, and household | **Constant scaffolding:** all constructed with the same members because PolicyEngine requires entity relationships; they do not select a payment-table row. |
| maximum family size | **Constant and verified:** ten. |
| payment amounts | **Verified parameter table:** all ten values are checked independently before comparisons run. |
| money unit and period | **Constant:** USD per month. |
| income, resources, work activity, sanctions, and eligibility | **Outside scope:** not inputs to this payment-standard node. |
| TANF effective grant | **Outside scope:** the payment standard is a ceiling/table value, not a promise of actual assistance. |
| SFA and RCA program rules | **Outside scope:** the WAC table mentions them, but the named oracle is Washington TANF. |

No size-zero or negative case is included. The WAC table begins at one person;
adding invalid sizes would test defensive behavior rather than a legal
boundary.

The direct companion file
`us-wa/regulations/388/388-478/388-478-0020.test.yaml` has Git blob
`38f7e2ddc51e84ad24f74ed48124f1cd95b8bfb3` and file SHA-256
`0caf82e6f4880d56640e38f5022956ecafe2f1e127645c0c7f4901332bd7e106`.
It contains eleven target-output cases for sizes 1 through 11. A twelfth,
older fixture exercises the standalone indexed parameter and is not counted
as a target-output case.

All 12 file cases passed with `axiom-encode test` and released engine v0.1.1
through a canonical `rulespec-us` path. Repository layout,
encoding-manifest-structure, and reverse-index tests also passed: 18 tests.

The checked-in encoding manifests retain pre-augmentation test hashes and are
not used as evidence for the new cases. The evidence is the pinned fixture
blob plus the direct execution receipt.

## 4. `closed`

**Verdict: holds for repository closure.**

Declared root and frontier:

```yaml
roots:
  - us-wa/regulation/388/388-478/388-478-0020
frontier:
  rule: delimiter-safe citation-path descendants of each declared root
  unique_provisions: 1
  raw_inventory_records: 2
summary:
  encoded: 1
  excluded: 0
  pending: 0
```

The r1 sweep's “1/2” means **one unique citation path from two raw inventory
records**, not one closed path plus one open legal path. The second occurrence
is a duplicate citation identity. Inventing an exclusion for it would
double-count one WAC provision.

Closure ledger:

```yaml
rows:
  - citation: us-wa/regulation/388/388-478/388-478-0020
    heading: Payment standards for TANF, SFA, and RCA
    status: encoded
    encoded_by:
      - us-wa/regulations/388/388-478/388-478-0020.yaml
    note: >-
      Both raw inventory occurrences resolve to the same active WAC section,
      UUID, source URL, and body. There are no delimiter-safe descendants.
findings:
  - Two raw inventory records deduplicate to one citation path.
  - The one unique provision is encoded.
  - No provision is excluded.
  - No provision is pending.
```

This is the certified-node schema's source-side criterion: every provision in
the declared frontier is encoded, excluded with reason, or pending, with zero
pending. It does not prove that an end-to-end TANF benefit program wires
eligibility, income, sanctions, and payment reductions into this maximum
standard. Those paths are outside this one-node candidate.

## 5. `executable`

**Verdict: does not hold.**

The format and arithmetic probes pass, but the literal criterion requires a
**published** artifact executed using the **official released binary** by a
stranger. Only a locally compiled, unpublished artifact was available.

### Local released-tag probe

The clean annotated engine tag `v0.1.1` resolves to tag object
`bdd225c4576ad51c127a10a6516675b09b2fae8d`, peeled commit
`e3e2da83222463d9b68b0681c00820e9d412c011`, tree
`62014a67b4540c9a5b6e2812838b4ae174bd3e07`.

The source was built with:

```sh
cargo build --release --locked --bin axiom-rules-engine
```

The resulting local arm64 binary reports `axiom-rules-engine 0.1.1` and has
SHA-256
`c1ea7e6c7984df06beef964e4923fa00ca3a4a1aa6e213e561a026ed558c452f`.
This is a clean released-tag source build, not a development engine, but its
hash is not represented as an official cargo-dist release asset.

A transient program spec selected one public output and no transformations
(spec SHA-256
`5f915c7c1df993e49b43be9b5a5c2228deb40a13de92bbd91f6d97a9eeaee453`):

```yaml
program: us-wa/tanf/payment-standard
period: 2026-01
outputs:
  - cash_assistance_unit_maximum_monthly_payment_standard
scope:
  state:
    - regulations/388/388-478/388-478-0020
```

The program spec was deliberately not committed because the closure-sprint
brief froze `programs/`. Its composed local RuleSpec has SHA-256
`d31d8dd45b19d7cb18dc12af0ac166fa12308bcd7942488edffb238a140004c8`.

Exact compile and deterministic recompile, resolving imports from the clean
RuleSpec snapshot:

```sh
AXIOM_RULESPEC_REPO_ROOTS=/private/tmp/wa-tanf-oracle-input/rulespec-us \
/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/engine-v0.1.1/target/release/axiom-rules-engine \
  compile \
  --program /private/tmp/wa-tanf-executable-receipt/payment-standard.rulespec.yaml \
  --output /private/tmp/wa-tanf-executable-receipt/payment-standard.compiled.json

AXIOM_RULESPEC_REPO_ROOTS=/private/tmp/wa-tanf-oracle-input/rulespec-us \
/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/engine-v0.1.1/target/release/axiom-rules-engine \
  compile \
  --program /private/tmp/wa-tanf-executable-receipt/payment-standard.rulespec.yaml \
  --output /private/tmp/wa-tanf-executable-receipt/payment-standard.recompiled.json
```

Receipt:

```yaml
rulespec_commit: 65bb172054984d83a5329d1d05cc5b1c605c0479
rulespec_tree: 05ffa5a3da111ad6247074bc3d3f6347ed5e4867
engine_version: 0.1.1
artifact_format_version: 2
selected_public_output_count: 1
selected_public_output: us-wa:regulations/388/388-478/388-478-0020#cash_assistance_unit_maximum_monthly_payment_standard
compiled_derived_node_count: 2
compiled_dependencies:
  - us-wa:regulations/388/388-478/388-478-0020#cash_assistance_payment_standard_size_band
  - us-wa:regulations/388/388-478/388-478-0020#cash_assistance_unit_maximum_monthly_payment_standard
fast_path_strategy: generic_bulk
fast_path_compatible: true
artifact_sha256: 0b3dca0bd174e4a6ea928b1ffc8276aa3a6dcc1193ed15e8a8be262a30e1b631
deterministic_recompile_sha256: 0b3dca0bd174e4a6ea928b1ffc8276aa3a6dcc1193ed15e8a8be262a30e1b631
```

The compiled graph has two derived nodes because the selected output depends
on the internal size-band node. The transient program selected and queried one
public output; this package does not claim the artifact contains only one
derived node.

Exact replay request:

```json
{
  "mode": "explain",
  "dataset": {
    "inputs": [{
      "name": "us-wa:regulations/388/388-478/388-478-0020#input.assistance_unit_size",
      "entity": "AssistanceUnit",
      "entity_id": "assistance-unit:1",
      "interval": {
        "start": "2026-06-01",
        "end": "2026-07-01"
      },
      "value": {
        "kind": "integer",
        "value": 11
      }
    }],
    "relations": []
  },
  "queries": [{
    "entity_id": "assistance-unit:1",
    "period": {
      "period_kind": "month",
      "start": "2026-06-01",
      "end": "2026-07-01"
    },
    "outputs": [
      "us-wa:regulations/388/388-478/388-478-0020#cash_assistance_unit_maximum_monthly_payment_standard"
    ]
  }]
}
```

The compact newline-terminated replay request has SHA-256
`78bfe73c9e43f4502afb00b0c666cac67feb522b34e4f9bd81a807ccd83e722c`.
The original request bytes were not retained, so this is labeled a replay
hash, not an original-input receipt hash.

Run:

```sh
printf '%s\n' '{"mode":"explain","dataset":{"inputs":[{"name":"us-wa:regulations/388/388-478/388-478-0020#input.assistance_unit_size","entity":"AssistanceUnit","entity_id":"assistance-unit:1","interval":{"start":"2026-06-01","end":"2026-07-01"},"value":{"kind":"integer","value":11}}],"relations":[]},"queries":[{"entity_id":"assistance-unit:1","period":{"period_kind":"month","start":"2026-06-01","end":"2026-07-01"},"outputs":["us-wa:regulations/388/388-478/388-478-0020#cash_assistance_unit_maximum_monthly_payment_standard"]}]}' |
/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/engine-v0.1.1/target/release/axiom-rules-engine \
  run-compiled \
  --artifact /private/tmp/wa-tanf-executable-receipt/payment-standard.compiled.json
```

The command exits zero, reports requested and actual mode `explain`, traces
`cash_assistance_payment_standard_size_band` to ten, and returns integer
`1662` USD. The response receipt has SHA-256
`49498ca90a9b5300a6ca0cd3609d6ee62b661aff47bf369074f80430d4341a06`.

### Hand-checkable golden case

For an assistance unit of **11 people** in June 2026:

```text
1. Observed assistance-unit size                         = 11
2. WAC final-row threshold                              = 10
3. Is 11 at least 10?                                   = yes
4. Applied size band                                    = 10
5. WAC row for size 10 or more                          = $1,662
6. Maximum monthly payment standard                     = $1,662/month
```

Equivalently:

```text
size_band = min(11, 10) = 10
payment_standard[10] = $1,662
```

The companion fixture, PolicyEngine named-variable grid, and local compiled
run all return $1,662. This is the maximum monthly payment standard, not an
actual-benefit determination.

### Blocking findings

1. There is no committed one-output Washington TANF program spec and no
   corresponding artifact in a published `program-artifacts-*` release.
   Repository policy says compiled artifacts are build outputs, never
   committed, and are published only from program specs after they land on
   `main` (`tools/README.md:3-21`). The sprint constraints prohibited changing
   `programs/`.
2. Fresh anonymous download and attestation of the official v0.1.1 cargo-dist
   binary could not be completed because the GitHub API was unreachable. The
   local probe used the exact clean released source tag, but that is not
   equivalent to an anonymous official-release-asset execution.
3. Consequently there is no honest stranger-path command pairing an official
   released binary with a published artifact at the pinned artifact hash.
4. The RuleSpec sentinel effective date is broader than the audited legal and
   oracle period. This evidence supports June 2026 only and must not be used
   as historical-parity evidence.
5. The checked-in test-manifest hashes predate the augmented fixture, and the
   proof-validation fingerprint is not an automated pass. Neither is used as
   evidence for the verdicts above.

Until a provenance-stamped one-output artifact is published and a fresh
release-asset stranger run reproduces $1,662, `executable.holds` must remain
false and this candidate must not be added to `certified-nodes.yaml`.
