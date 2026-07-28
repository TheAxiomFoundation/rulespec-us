VERDICT: REQUEST-CHANGES

# Blind adversarial review: rulespec-us PR #1174

## Target and method

- GitHub-verified head:
  `e7c0870eba3b12f0df0c6e99567665c2c2dea03b`
  (`fed-parity/atomic-63c6-67h`).
- GitHub-verified base:
  `af6c57d618acff5cb268d345653ea3e4cf64feb6`.
- The local author ref was still at pre-update head
  `3f933cd935e68cb1cdd50a254ab449aeabe2d468`. Read-only shell fetch was blocked
  by DNS, so I verified through GitHub that the update merge adds only the
  `.axiom/toolchain.toml` corpus-pin delta, obtained its exact blob, and applied
  that delta in the disposable review worktree. The RuleSpec and manifest bytes
  reviewed are therefore the exact remote-head bytes.
- Review-only commits are on `review/pr-1174-e7c0870`; no PR branch, remote, or
  GitHub state was changed.

## Blocking findings

### 1. §6012 has two invalid proof imports after the §63(c) module changed

`us/statutes/26/6012.yaml:100-102` and `:132-134` import
`us:statutes/26/63/c#standard_deduction` while attesting the old module hash:

`sha256:53a218483c6e8d771ed249db38049c358beeb3e1606d621652dddb9732a9ada2`

The head §63(c) module hash is:

`sha256:fbc6f30c840556e4303536a7f2f0bd47bb3612cc2beb30e0bb4ac2f6ac45bbba`

Exact pinned validation of §6012 at the head rejects both imports with
`Proof import hash mismatch`. Its 4/4 companion cases still pass and the
compiled behavior is unchanged after normalizing the moved module ID/source,
so ordinary runtime tests do not reveal this proof-contract regression.
§6012's active validation waiver can also keep unchanged-consumer validation
from surfacing it in the PR matrix.

Remedy: refresh both proof-import hashes with the canonical
`repair-proof-import-hashes` flow and regenerate/sign the required §6012
manifest artifacts.

### 2. The changed §63(c) module retains stale pending-validation evidence

`known-validation-gaps.yaml:20502-20507` still declares §63(c) pending, and
`.axiom/pending-validation-fingerprints.json:13012-13016` binds that declaration
to the old module hash `sha256:53a218...`. The changed module validates cleanly
at the exact pins, but remote Repository Checks job `90409704533` stops first
with:

`pending validation fingerprint evidence mismatch: us/statutes/26/63/c.yaml`

Remedy: because the changed module is now clean, remove its stale pending entry
and corresponding fingerprint record through the repository's canonical
waiver/fingerprint maintenance flow.

### 3. The PR tracks a forbidden top-level `PROGRESS.md`

`.axiom/repository-structure.yaml:63-74` does not allow `PROGRESS.md` at the
repository root. Remote Repository Checks job `90409704542` reports:

`PROGRESS.md: top-level file is not allowed`

Remedy: remove the PR-authored top-level progress file from the PR diff. This
review's separately committed ledger remains only on the local review branch.

## Passing evidence

### Extraction fidelity

- Compared base `c13cdf7dda5948e7a86ff0c317872f93743a2084` with the PR
  content tree. The extracted §63(c)(6) formula is byte-identical; name, kind,
  entity, dtype, period, versions, and the §443 proof import are unchanged.
  Only source spelling/proof expansion and module location differ.
- The other eleven §63(c) rule objects are unchanged after parsing. The parent
  no longer owns `standard_deduction_ineligible` and now imports the extracted
  atom, leaving no duplicate/collision.
- Base and head §63(c) companions have the identical passing set, 6/6. The new
  §63(c)(6) companion passes 5/5.
- Importer search found one executable downstream consumer, §6012, plus a
  deferred blocker reference in §63. No obsolete executable reference to the
  former output location remains. §6012 behavior remains 4/4 despite finding 1.

### Legal fidelity and mutation evidence

- Pinned corpus `8af592162231e9de748ba6b98792b426ad4fe8b7` retains the
  §63(c)(6) parent and A-D rows ingested through PR #550. The implementation
  covers all four branches:
  married filing separately/either spouse itemizes; nonresident alien;
  approved accounting-period change that causes a short return; and
  estate/trust/common trust fund/partnership.
- Supplemental branch-C probes independently removed each conjunct. Approval
  without a resulting short period and a short period without approval both
  produce `not_holds`, demonstrating fail-closed behavior.
- §67(h) encodes the retained 2018-forward suspension as `false`, so a 2026
  individual is `not_holds`. In an isolated canonical mutation checkout,
  `false -> true` caused exactly one expected `not_holds -> holds` failure.
  Restoring the atom restored the original hash and a clean 1/1 pass.

### Proof atoms and pinned validation

- Raw substring checks found every excerpt verbatim in the pinned corpus:
  §63(c) 20/20, §63(c)(6) 5/5, and §67(h) 1/1.
- Exact pinned proof validation reports no issue for 24 §63(c) atoms, six
  §63(c)(6) atoms, or the §67(h) atom.
- Exact pinned module validation with reviewer checks skipped reports
  `all_passed: true` and no errors for all three changed modules.

### Manifests and legacy-manifest adjudication

- All three modern manifests use `applied-rulespec/v1`, manual attestation, and
  `manual_exception: rulespec-us#1001`; none claims composition provenance.
- Their applied-file sets are exact: each attests only its module and companion,
  every recorded SHA-256 matches the applied bytes, the content commit
  `3719b6d90...` is an ancestor, and the subsequent diff consists only of the
  three manifest JSON files.
- Manifest/applied-artifact tests pass 37/37. The remote generated guard also
  passes.
- **Legacy deviation: ACCEPT.** The untouched
  `.axiom/encoding-manifests/statutes/26/63/c.json` truthfully records the older
  pre-extraction bytes and is superseded history, not a false current
  attestation. Main already contains all three supported manifest layouts
  (380 legacy-root statute manifests, 135 root `us/` manifests, and 131
  jurisdiction-local manifests). `tests/test_encoding_manifests.py:36-42` and
  `:64-92` explicitly select the newest `generated_at` entry; that selects the
  new 2026-07-28 modern §63(c) manifest over the 2026-05-22 legacy record.
  Generated guard, validation, and drain consumers likewise resolve the modern
  record or operate only on changed artifacts. I found no consumer that the
  stale historical file can mislead, so deleting or rewriting it is not
  required for this atomic PR.

### Oracle gate, reverse index, and hygiene

- Ran current encode-main classifier content from merged encode #1328 with its
  merged axiom-oracles #422 pin `f8ea6027...`, using the workflow's composed
  checkout layout and exact changed-file filter. It selected 14 outputs.
- `us:statutes/26/63/c/6#standard_deduction_ineligible` is
  `known_not_comparable`, mapped to `separate_filer_itemizes`, and tested.
- `us:statutes/26/67/h#miscellaneous_itemized_deduction_allowed_for_individual`
  is `comparable`, mapped to
  `gov.irs.deductions.itemized.misc.applies`, and tested.
- Gate result: zero pending, unmapped, untested-comparable, workflow failures,
  or missing new outputs.
- Reverse-index regeneration is clean: 4,246 provisions, 5,085 edges, 4,488
  modules.
- The exact PR-only diff has 11 files: the three modern manifests, reverse
  index, two parent §63(c) files, two extracted §63(c)(6) files, two §67(h)
  files, and the disallowed PR progress file. The update merge introduces no
  PR-only toolchain delta because the verified base already has the same pin.
  No NY, workflow, toolchain, or unrelated ledger file appears. `git diff
  --check` passes.
- Focused repository tests pass: 18/18 across manifest, reverse-index, and
  Python layout tests. The reusable workflow's broader root-file shell gate is
  the distinct check that correctly finds blocker 3.

## Environment and verification limitations

- Shell network/DNS could not resolve GitHub or npm, so the exact head and
  current merged dependency state were verified read-only through GitHub and
  locally available exact commit trees/blobs rather than a successful fetch.
- GitNexus built the disposable snapshot graph but sandbox policy denied its
  write to `~/.gitnexus/registry.json`; direct importer searches, compile
  comparisons, and pinned executions supplied the impact evidence instead.
- The local signing secret was unavailable, so I could verify manifest
  structure, signatures' presence, hashes, and ancestry but not independently
  recompute HMACs. The secret-backed remote generated guard passes.
- Sandbox policy rejected the first mutation patch under `/private/tmp`; the
  same mutation was rerun and restored under the writable review-worktree
  ledger. Initial oracle runs used noncanonical directory shapes and were
  rejected before classification; the canonical workflow layout then completed
  successfully.
- The default local Python shim and uv cache were unusable in this sandbox.
  Existing exact-pinned virtual environments completed the reported tests. One
  duplicate broad validation attempt was interrupted after it expanded to a
  repository-wide scan; the targeted exact-pinned validations above completed
  independently.

## Required re-review delta

1. Repair both §6012 proof-import hashes and add the signed §6012 provenance
   artifacts required by that repair.
2. Remove §63(c)'s obsolete pending-waiver and pending-fingerprint records.
3. Remove the PR-authored top-level `PROGRESS.md`.
4. Re-run Repository Checks, pinned validation (including §6012), manifest
   validation, reverse-index regeneration, and the changed-file oracle gate.
