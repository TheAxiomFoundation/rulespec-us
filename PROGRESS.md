# PR 1003 round-4 review progress

## State

- Review in progress on a dedicated throwaway worktree and review-only branch.
- The PR-1003 product residual is fixed at the exact head, but the live body
  remains materially inconsistent with that head; this is currently blocking.
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

## Next

- Verify the inherited PR-1004 threshold import and enumerated-status
  fail-closed behavior, including status 9.
- Review the five post-round-3 commits for regressions.
- Run focused gates, re-fetch the live body/head, and write the final verdict
  to `round4-1003-VERDICT.md` and the requested output file.
