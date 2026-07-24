# PR 1003 round-4 review progress

## State

- Review in progress on a dedicated throwaway worktree and review-only branch.
- The named PR-1004 and PR-1003 product residuals are fixed at their exact
  live heads, and the focused local gates pass.
- The verdict remains `REQUEST-CHANGES`: PR 1003's live body materially
  contradicts its current head, the round-3 progress record is stale after
  the final re-sign, and one new companion no longer isolates the foreign
  attestation boundary it purports to cover.
- Live PR head reported by GitHub and checked out locally:
  `50b6ec228dba8279526bd692de85af4659557c78`.
- Live base reported by GitHub:
  `836e74b578a35fdfb30bf828e89510cd894e8300`.
- Previously reviewed round-3 head:
  `3327de19395465dee736061b2d4c33108416d261`.
- The subject branch and the user's unrelated dirty checkout remain untouched.

## Done

- Read the GitNexus PR-review, GitHub, and GitNexus CLI workflow instructions.
- Read `round3-1003-VERDICT.md` and its committed `PROGRESS.md` in full.
- Searched for `rereview-1003-VERDICT.md`; it is not present in the local
  repository, refs, or accessible prior scratchpad locations.
- Retrieved the live PR body, base SHA, head SHA, and full patch through the
  GitHub connector.
- Confirmed the current head adds five commits after round 3 and identified
  the exact changed-file set.
- Checked GitNexus status. The repository is not indexed, and this read-only
  review will not create an index.
- Independently inspected the pinned axiom-corpus commit
  `710a326366bd233c40d64ca89b62a07082f13ce3`. Its `us/statute/26/1401`
  record says verbatim that the tax is imposed under `section 3121(b)(2)`;
  it does not contain the corrected `3101(b)(2)` coordination sentence.
- Confirmed the unsupported corrected proof excerpt and input-contract
  quotation are absent from the current Additional Medicare module.
- Confirmed the domain judgment requires both the section 1401(c) attestation
  and zero imported self-employment income. The coordination helper, public
  SE leg, and public combined output fail closed when that judgment does not
  hold; the imported wage leg remains observable.
- Corroborated the legal characterization against primary federal sources:
  Treasury Decision 9645 applies the wage reduction using section
  `3101(b)(2)`, and current Form 8959 instructions use the same coordination.
- Found a blocking live-body contradiction. The earlier Additional-Medicare
  bullet still claims section 1401(b)(2)(B) proof atoms quote the pinned full
  cross-reference sentence and still presents the `$346.725` coordinated
  result. The appended update withdraws that excerpt, and the exact-head
  companion now expects the positive-SE case to fail closed to zero.
- Rechecked the oracle artifacts. NIIT and SECA reports remain at rulespec SHA
  `f0eaa0cf657a40edfcb5491fde243cd051ec67af` and omit their later required
  attestations. The Additional Medicare report remains at SHA
  `8218c7baff9330cf1eb707bb7d2df87bfb4abcfc`, omits the current attestation,
  and reports `346.725` for the positive-SE case that now returns zero. Thus
  the live statement that all six domestic values are unchanged is false.
- Checked PR 1004 at exact live head
  `e25a31417997e27b50ef9d2315d67b9a9036f7b5`. Its QBI pipeline imports all
  nine threshold/range-end/width parameters from the merged Rev. Proc.
  module; its filing-status guard admits only statuses `0..4`; and its
  status-9 companion proves a zero final deduction. Its focused gates pass:
  validation `3/3`, proofs `43/43`, companions `40/40`.
- Audited PR 1003's five post-round-3 commits
  (`3327de19395465dee736061b2d4c33108416d261..50b6ec228dba8279526bd692de85af4659557c78`).
  No executable or manifest defect was found. All current file/output hashes
  and manifest supersession links are internally consistent.
- Found a new committed documentation defect in
  `bulk/fix3-1003/PROGRESS.md`: it still says the manifests are stale, expects
  manifest-sync failure, says NIIT/SECA did not change, and requests a
  keyholder refresh. Commit `50b6ec228` actually refreshed all three
  manifests and made the manifest-sync test pass.
- Found a new companion-coverage defect:
  `amt-foreign-system-boundary-fails-closed` supplies both a false foreign
  attestation and positive imported SE income. The new zero-SE conjunct alone
  makes the domain false, so the case would still pass if the foreign
  attestation guard were removed. A zero-SE, false-attestation companion is
  needed to isolate that boundary.
- Ran PR 1003's focused gates with the exact pinned encoder, engine, and corpus:
  canonical validation `3/3`, proof validation `47/47`, companions `42/42`,
  encoding-manifest pytest `3 passed`, and `git diff --check` all pass.
  The subject worktree remained clean.
- Re-fetched PR 1003 from GitHub after the audit. Its live head remains
  `50b6ec228dba8279526bd692de85af4659557c78`, and the contradictory body text
  remains live.

## Next

- Write and commit `round4-1003-VERDICT.md`.
- Copy the committed report to the requested scratchpad output path without
  staging or otherwise disturbing the user's unrelated dirty checkout.
- Verify artifact identity and remove the throwaway worktree.
