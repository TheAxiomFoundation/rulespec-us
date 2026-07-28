# PR #1174 Blind Adversarial Review Progress

## State

- Review branch: `review/pr-1174-e7c0870`.
- Disposable worktree: `.git/review-worktrees/pr-1174-e7c0870`.
- GitHub-verified PR head: `e7c0870eba3b12f0df0c6e99567665c2c2dea03b`.
- GitHub-verified PR base: `af6c57d618acff5cb268d345653ea3e4cf64feb6`.
- Head branch: `fed-parity/atomic-63c6-67h`.
- Pinned corpus: `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Status: complete.
- Final verdict: `REQUEST-CHANGES` for three integration blockers.

## Done

- Preserved the dirty primary checkout and the author's stale branch worktree.
- Confirmed through the read-only GitHub connector that open PR #1174 now points
  to full head SHA `e7c0870eba3b12f0df0c6e99567665c2c2dea03b`.
- Confirmed the local author branch/ref remains at pre-update commit
  `3f933cd935e68cb1cdd50a254ab449aeabe2d468`.
- Attempted a read-only exact-head fetch; sandbox DNS could not resolve
  `github.com`, and no local ref changed.
- Used GitHub's commit and compare data to verify that the update-branch merge
  changes exactly `.axiom/toolchain.toml` relative to local commit `3f933cd935e6`,
  replacing the corpus pin with `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Fetched that file at the exact remote head (Git blob
  `e6df1f147f2ed48950b8fcdddb1d20339f04955c`) and applied the verified one-line
  delta in this disposable worktree. The review snapshot is therefore
  byte-equivalent to the exact remote head apart from review-only ledger files.
- Audited the 11-file PR-only diff against the verified base. The update merge
  contributes no PR-only foreign file; there are no NY, workflow, toolchain, or
  foreign ledger regressions. `git diff --check` passes. The PR's own top-level
  `PROGRESS.md` is not allowed by `.axiom/repository-structure.yaml`, however,
  and remote Repository Checks run `30399199674`, job `90409704542`, rejects it.
- Proved extraction fidelity from base `c13cdf7dda59` to the pre-update PR tree
  `3f933cd935e6`: the moved formula is byte-identical
  (`sha256:8f24d715...`), the other eleven §63(c) rules are unchanged after
  parsing, the parent no longer owns `standard_deduction_ineligible`, and no
  obsolete executable reference remains. Base and head §63(c) companion sets
  both pass 6/6; the extracted companion passes 5/5.
- Audited downstream consumers. §6012 is the only executable importer and its
  4/4 companion behavior remains identical, but its proof imports at lines
  100-102 and 132-134 still attest the old §63(c) module hash
  `sha256:53a218...`. Exact pinned validation now rejects both imports; the
  current §63(c) hash is `sha256:fbc6f30c...`. This is a proof-contract
  regression masked by §6012's active validation waiver.
- Checked §63(c)(6) against all retained corpus branches: MFS/either spouse
  itemizes, nonresident alien, approved accounting-period change causing a
  short return, and estate/trust/common-trust-fund/partnership. Supplemental
  probes show branch C fails closed when either conjunct is absent.
- Checked §67(h) as `not_holds` for a 2026 individual. An isolated mutation
  `false -> true` reproduced exactly one `not_holds -> holds` failure; restoring
  the source restored a clean pass and the original file hash.
- Verified all 26 proof excerpts as raw verbatim substrings in pinned corpus
  `8af59216...`, including the five §63(c)(6) rows ingested through PR #550.
  Exact pinned proof validation and module validation pass for §63(c), §63(c)(6),
  and §67(h).
- Verified all three modern manifests: exact applied file sets and hashes,
  signed after their content commits, and manual exception exactly
  `rulespec-us#1001` (never composition). Manifest and applied-artifact tests
  pass.
- Adjudicated the untouched legacy
  `.axiom/encoding-manifests/statutes/26/63/c.json` as acceptable historical
  state. Main already mixes three supported layouts; the manifest selector
  makes the newer modern manifest authoritative, and no validation, drain, or
  generated-guard consumer treats the legacy record as current.
- Regenerated the reverse index successfully: 4,246 provisions, 5,085 edges,
  and 4,488 modules, with no diff.
- Exact pinned validation of the three changed modules is clean, but remote CI
  also fails before validation because the PR changes §63(c) without removing
  its now-stale pending waiver/fingerprint evidence
  (`module_sha256: sha256:53a218...`). Repository Checks job `90409704533`
  reports `pending validation fingerprint evidence mismatch`.
- Ran the changed-file oracle-coverage gate in the workflow's composed checkout
  layout with the merged encode #1328 classifier tree and its pinned merged
  oracle #422 mapping (`f8ea6027...`). It inspected 14 outputs: §63(c)(6) is
  `known_not_comparable`, tested, and mapped to `separate_filer_itemizes`;
  §67(h) is `comparable`, tested, and mapped to
  `gov.irs.deductions.itemized.misc.applies`. There are zero pending, unmapped,
  untested-comparable, or missing new outputs.
- Recorded environment limitations: shell DNS blocked the exact-head fetch;
  GitNexus indexed the disposable snapshot but could not register it because
  the sandbox denied `~/.gitnexus/registry.json`; local manifest HMAC
  verification lacked the signing key (remote generated-guard passes). Initial
  noncanonical oracle/mutation paths were rejected and rerun successfully in
  canonical layouts.
- Wrote the complete evidence, legacy-manifest adjudication, remedies, and
  sandbox disclosures to `WORKER-REPORT.md`.

## Next

- Await a corrected PR head containing the three required remediation groups,
  then re-run the targeted review delta.
