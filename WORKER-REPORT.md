VERDICT: APPROVE

# PR #1176 round-3 correctness re-review

No blocking correctness or containment finding remains at exact head
`0e042edd42d29e47e39f5b2f5a3ab7085cffe90b`. The read-only GitHub connector
confirmed that open PR #1176 still names `fed-parity/ca-bbce` at that exact
SHA, with 14 changed files. No PR branch, remote, corpus, or GitHub write was
made.

## Guard soundness

The repair adds a source-side private count,
`snap_state_plan_member_of_household_count = len(member_of_household)`, and a
California private integrity judgment comparing it with
`len(calfresh_mce_canonical_member_of_household)`. Integrity failure is wired
fail-closed in both directions: it makes
`calfresh_mce_household_exclusion_applies` hold and prevents
`calfresh_mce_status_conferred` from holding.

Tuple order below is:

`(federal anchor count, canonical integrity, household exclusion, MCE status)`.

| Adversarial case | Actual tuple | Catch mechanism |
| --- | --- | --- |
| Exact predecessor injection: extra eligible row supplied directly to the local canonical relation | `(1, not_holds, holds, not_holds)` | Cardinality guard. The projected source identity remains in the local union, so the injected identity makes the local count larger. |
| Same injection plus caller attempts to spoof both derived helper scalars | `(1, not_holds, holds, not_holds)` | Cardinality guard; supplied values cannot override derived formulas. |
| Two rows supplied to both local and anchor relations with the same identities, preserving equal counts | `(2, holds, holds, not_holds)` | Same-row exclusion scan. The IPV member evaluates `calfresh_mce_member_household_exclusion_applies=holds`. |
| Equal supplied cardinality but barred anchor member exchanged for a distinct eligible local member | `(1, not_holds, holds, not_holds)` | Cardinality guard. Projection retains the barred source identity, so the computed local union has two identities although each supplied list has one. |
| Inconsistent eligible plus IPV-barred rows supplied only to the anchor | `(2, holds, holds, not_holds)` | Same-row exclusion scan. Both anchor rows project into the local canonical relation and the IPV row is scanned. |

The committed engine-only attack fixture passed 2/2 cases, and the three
explicit-identity completeness probes passed 3/3. Thus every requested shape
returned the lawful fail-closed household outputs.

## Mutation isolation

The sole mutation replaced the integrity comparison with `formula: true`.

- Enabled: the two exact divergent fixtures passed 2/2.
- Disabled with lawful expectations retained: 0/2 passed, with six targeted
  assertion failures. Both actual tuples flipped to
  `(1, holds, not_holds, holds)`.
- Disabled with those unsafe outcomes as expectations: the fixtures passed
  wrongly 2/2.
- Restored: the MCE module returned byte-for-byte to target SHA-256
  `ba01095a1d8619ece130958a128a662011c685ede2e564802f90b46e3bc628dc`,
  its diff from `0e042edd4` became empty, and the lawful fixture returned to
  2/2 green.

With the guard disabled, the equal-count dual-surface and anchor-only IPV
cases remained fail-closed through their exclusion scans; only the distinct
membership swap became eligible. This independently isolates the two claimed
catch mechanisms.

## Canonical companion and validation gates

From fresh `git archive` content extracted under the literal basename
`rulespec-us`, using corpus
`8af592162231e9de748ba6b98792b426ad4fe8b7` at the requested path:

- Federal state-plan companion: 7/7.
- California MCE companion: 35/35, including the IPV and probation/parole
  divergent-member regressions.
- California benefit companion: 12/12.
- Combined gate: 54/54, three compiled programs, zero failures.
- Separate engine-only predecessor attack fixture: 2/2.
- Standalone validation of the federal, MCE, and benefit modules:
  `ci_pass=true`, `all_passed=true`, zero errors for all three.
- Proof validation: 41 atoms checked, zero issues.
- Manifest/layout/reverse-index/provenance contracts: 26 passed. The only
  warning is the unchanged repository backlog of 19 unmanifested modules.

The companion runs used pinned `axiom-encode` source commit
`3869d66d009f52258be35901edbef370e65a399c` (version 0.2.1200) and a fresh
release build of pinned engine commit
`ffd8213271947b0189a9dd61a055c1e0e78908a0`.

## Federal module blast radius

A main snapshot at `ae64af2740340a40d04ed3c652254f53e62fab61`
was archived, then overlaid with only the target federal state-plan source,
companion, and manifest. Arizona and New York state source/companion files
were themselves byte-identical between the base and target.

- Arizona: base 6/6 and overlay 6/6. Complete canonicalized engine
  request/response transcripts are byte-identical, SHA-256
  `d4fa6b91785ab0f7dc6d53091e2782337666e90d629c038b4ce19da9e19bc8d6`.
- New York: base 12/12 and overlay 12/12. Complete transcripts are
  byte-identical, SHA-256
  `2686ce396c888032994fc78797a1f78ff7713d1dc690e3801de014b065404186`.
- Raw compiled artifacts appropriately contain one additional private helper
  and its evaluation-order entry. Those are the only two raw diff hunks;
  removing only those inert entries makes the artifacts byte-identical
  (Arizona `48e094f2...`, New York `e95bd4c9...`).
- The target federal module's own companion passes 7/7 and its validator
  reports zero findings.

The target has six federal state-plan importers. Neither new helper is
referenced by a non-California consumer, and the byte-identical state runtime
transcripts confirm that the imported private count is inert.

## Manifests, surface, and containment

The requested ancestry is exact:

`e111d8b8d549fd80012bc7ee7d921c3e940261e9`
→ `01ec7fb5e6d5997ce4393fc27a1155f1840b6bff` (deletes only `PROGRESS.md`)
→ `0e042edd42d29e47e39f5b2f5a3ab7085cffe90b` (changes only four manifests).

- All four manifests declare `backend=manual`,
  `manual_exception=composition`, `hmac-sha256`, key ID
  `axiom-encode-apply-v1`, and a 64-hex signature.
- Their seven applied-file hashes match both ancestor `01ec7fb5e` and head.
  Every `supersedes.manifest_sha256` matches the corresponding parent
  manifest bytes.
- The ProgramSpec citation is exactly bare
  `programs/us-ca/snap/fy-2026`.
- The apply-signing secret was not available, so the HMAC values could not be
  independently recomputed. The available corpus-release key is a different
  key and, as expected, does not verify apply-manifest signatures. Signature
  structure, supersession, and every attested file hash were independently
  checked.

Relative to pre-round-3 `686d413cfe15410dc160010f7863096c8c20ef48`,
exactly two rule IDs are added and none removed:

- `snap_state_plan_member_of_household_count`
- `calfresh_mce_canonical_membership_integrity_verified`

Both are private. The pre-existing private canonical projection remains
private. The 17 mapping rows merged by axiom-oracles PR #424 are byte-identical
on oracle `origin/main`; neither helper occurs in them.

The PR-semantic triple-dot diff against current `origin/main` has the same
merge base `af6c57d618acff5cb268d345653ea3e4cf64feb6`, is clean under
`git diff --check`, and contains exactly the intended 14 paths: four
manifests; CA ProgramSpec, MCE, and benefit paths; the federal state-plan
source/companion; reverse index; injection fixture; and repair report.
`PROGRESS.md` is not tracked at PR head.

## Tooling and sandbox disclosures

- GitNexus was initially unindexed. The required analysis attempt parsed the
  repository but the sandbox denied writing
  `/Users/maxghenis/.gitnexus/registry.json` with `EPERM`; the lingering
  process was interrupted. Direct git/source tracing, compiled-IR diffs, and
  full runtime comparisons supplied the dependency evidence instead.
- `apply_patch` rejected a disposable edit under `/private/tmp` as outside the
  project. The same canonical-basename fixture archive was created under
  `.git/review-worktrees/`, where the patch and 2/2 run succeeded.
- One federal lane could not initialize `uv` under
  `/Users/maxghenis/.cache/uv` because of sandbox permissions. It used an
  existing dependency environment with `PYTHONPATH` pinned to the audited
  source commit. Harmless `nice(5) failed` warnings also appeared during
  parallel archive extraction; archive hashes and all executions completed.

None of these limitations skipped a requested gate or changed the reviewed
branch.
