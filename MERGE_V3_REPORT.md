# Merge v3 report — PR #911 + current `origin/main`

## Result

- Local merge commit: `ead64a07c1adfed2d1d31aab02b45d89ec20df2e`
- Tree: `584de64adb22acb8b3076366a7624e7b45381cfa`
- Parents: `2a503a5c9a2227c363aceaece6c547429c3c0878` and `c55778119c0dd208a5ea3366092a17d0b0392c8b`
- Subject: `Merge current main into PR 911`
- No push, rebase, squash, GitHub access, or network write was performed.
- This report is intentionally untracked and is not part of the commit.

The brief called the intended main `c1387b72…`, but the local `origin/main` was
`c5577811…`. A read-only merge-tree probe showed that `c1387b72…` merged cleanly,
whereas local `origin/main` produced exactly the specified 16 conflicts. I therefore
merged the actual `origin/main`; the second parent records that exact choice.

## Conflict resolutions

| Path | Resolution and rationale |
|---|---|
| Three add/add encoding manifests | Took current main's signed canonical v5 manifests. Every `applied_files` digest matches the final merged-tree bytes. No PR-side pair was retained. |
| `.axiom/pending-validation-fingerprints.json` | Semantic module union; main wins same-path rows. `generated_from` is PR then main, so main wins key collisions while both lineages remain. Other top-level evidence follows newer main. |
| `.axiom/toolchain.toml` | Rewritten to exactly the required three keys. Corpus release and content digest are fixed as instructed; waiver binding is the final ledger SHA below. |
| `.axiom/workflow-toolchain.toml` | Current main verbatim: encoder 0.2.1690 and all eight requested refs/keys. |
| `.github/CODEOWNERS` | Union. Preserved main's newer explanatory header and PR canonical-layout ownership for the legacy freeze and checker. All six retained patterns match tracked paths; no dead pattern was retained. |
| `.github/workflows/repository-checks.yml` | Main's current org pin, permissions, registry inputs, worker count, and root guard, with PR migration authorization, legacy freeze, three-job `needs`, conditional migration inputs, two-job drift alarm, and final bootstrap digests grafted back. Dropped `allow-retired-schema-prefreeze`: the pinned org workflow says it is rejected once base or head contains a freeze, and this head contains one, so retaining it would be wrong rather than harmless. All 13 passed inputs exist in the pinned workflow's `workflow_call.inputs`. |
| `.github/workflows/program-artifacts.yml` | Began from current main, preserving hardened action pins, permissions, separate build/publish jobs, and artifact-engine ref. Reapplied PR main-target gating and canonical-layout wording. |
| `tools/build_program_artifacts.py` | Began from current main. Reapplied jurisdiction-root discovery, content-addressed corpus release identity, `compile-composed --rulespec-root`, resolved neutral temp root, and release manifest plumbing while preserving main's artifact-engine toolchain field and emitted-schema checks. |
| `tools/tests/test_manifest_provenance.py` | Began from current main and added the release/canonical builder assertions associated with the re-applied builder delta. |
| `.github/workflows/source-staleness.yml` | Current main verbatim; diff from second parent is empty. Its use of `source_staleness_axiom_encode_ref` is canonical-layout compatible; no PR-only delta was needed. |
| `bulk/README.md`, `bulk/local_drain.py` | Current main verbatim; diffs from second parent are empty. No PR delta was required for canonical layout. The companion bulk test was aligned to main's current coverage-encoder pin. |
| `known-validation-gaps.yaml` | Semantic three-way merge described below; no new waiver was invented. |
| `oracle-coverage-pending.yaml` | Generated with the required byte-for-byte helper as a normalized `legal_id` three-way union. |

Current main also introduced 100 noncanonical root `programs/` modules and 100
matching root-program manifests. The hard-cut invariant forbids a root `programs/`
directory and canonical jurisdiction copies exist, so both noncanonical sets were
removed from the merge tree. Final tracked root-program count is zero.

`tests/test_encoding_manifests.py` retains the PR's canonical manifest-root and
retired-jurisdiction resolution guards, while accepting current main's authenticated
v1 HMAC backlog alongside v5 manifests. This reconciles the hard-cut layout with
main's expanded signed-manifest inventory. Other current-main companion tests were
retained where their production files came from main.

## Waiver-ledger disposition

| Class | Count | Disposition |
|---|---:|---|
| Identical records on both sides | 316 | Kept once |
| Different records, identical module bytes | 964 | Took main's 0.2.1690-era record |
| Different records, different module bytes | 1 | Kept PR record; re-census listed below |
| Deleted by PR | 5 | Deletion stands |
| Deleted by main | 1,815 | Deletion stands (main consumed/removed the waiver or module) |
| PR-only additions | 0 | None |
| Main-only / pending-only additions | 498 | Kept, including pending-only skip authorizations |
| Base / PR / main / merged rows | 3,101 / 3,096 / 1,784 / 1,779 | Final union after deletion-wins semantics |

Needs re-census at encoder 0.2.1690:

- `us-ca/regulations/mpp/63-410/321.yaml`

Final ledger SHA-256 (`L`):
`4ace5f0b7eedd316e5cb331a7b32a83b092f5a8e5ffceec60911c95a12818f88`.

## Evidence and generated registries

- Pending fingerprint module rows: PR 2,703; main 3,193; merged 3,202.
- Oracle pending union: base 3,208; PR 3,203; main 15,474; merged 15,469; true conflicts 0.
- Retired-schema freeze: 380 artifacts.
- Freeze SHA-256 (`F`): `c247ed9c2e3e1a4d33f86989d4d91aeaf90f1fd8f8ad9bbdf536cf2a7d48f333`.
- Reverse index: 18,173 provisions, 34,770 edges, 4,887 modules.
- Workflow has two occurrences each of `F` and `L` (authorization constants plus conditional bootstrap literals); lockstep tests contain both pins.

## Verification gates

1. Conflict-marker grep: empty.
2. Full suite, using the 0.2.1690 venv interpreter with host pytest exposed via `PYTHONPATH` because the specified venv has no pytest installed: `110 passed, 1 warning in 158.95s (0:02:38)`. Warning: 82 pre-existing unmanifested modules are reported, not failed.
3. Legacy freeze checker: `Legacy RuleSpec freeze inventory verified.`
4. Reverse-index check: `.axiom/index/provisions_to_rules.json is up to date (18173 provisions, 34770 edges, 4887 modules).`
5. Digest lockstep: `L` equals the ledger bytes, three-key toolchain binding, both workflow occurrences, and test pin; `F` equals freeze bytes, both workflow occurrences, and test pin.
6. Org workflow caller check: all 13 passed `with:` inputs exist at pin `7a1eb2439d4cbb3b129811adef7554a2d798bef2`.
7. `git diff --check`: clean.
8. JSON/YAML/TOML parse sweep: clean.
9. Three main-side signed manifests: every applied-file SHA matches merged bytes.
10. Layout: no root `programs/` directory; canonical-layout tests pass.
11. No unmerged index entries or unstaged tracked changes remained at commit time.

The protected-broker `axiom-encode validate` gate was not run, as instructed,
because the signing broker is unavailable; no fingerprint or signature was faked.
The standalone `axiom-encode oracle-coverage --root . --json` command was attempted
but 0.2.1690 rejected the worktree basename `merge-v3` because it requires the exact
canonical checkout name `rulespec-<country>`. The deterministic registry union and
the complete repository tests passed.

## OPEN QUESTIONS

1. Confirm that the dispatcher intended the actual local `origin/main`
   (`c5577811…`) despite the stale `c1387b72…` label in the brief. The exact 16-conflict
   match strongly indicates yes.
2. If a standalone oracle-coverage CLI receipt is required beyond the passing tests
   and deterministic union, rerun it from an exact canonical checkout basename
   (`rulespec-us`); this worktree's name is rejected before analysis.
3. The specified encoder venv lacks pytest. This report records the equivalent pinned
   interpreter invocation with host pytest on `PYTHONPATH`; consider provisioning
   pytest in future verification venvs.
