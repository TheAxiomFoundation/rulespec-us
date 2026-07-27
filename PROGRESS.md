# PR #1139 Round-2 Blind Review

## State

- Review branch: `review/pr-1139-round2-8da79dd`
- Pinned PR head: `8da79dd4eaee96c471b1b974a60e1478b44b0959`
- GitHub metadata verification: complete (read-only connector)
- PR base: `6b0773d3f7fa6719f208154f3e609e292ab7abe7`
- Pinned corpus checkout: `bf97b17baebfdf12601f7c23697524bf5adcdaed`
- Verdict: `APPROVE`
- Final report: `REVIEW.md`
- Review status: complete

## Done

- Verified PR #1139 is open at the requested exact head.
- Created an isolated disposable worktree at that head without modifying the PR branch.
- Confirmed the eight-commit PR is strictly ahead of its GitHub merge base and changes
  only the three SC page encodes/tests, their three manifests, and the reverse index.
- Read retained corpus records for pages 159, 163, 165, and 369 from the corpus checkout
  pinned by `.axiom/toolchain.toml`; the retained PDF is SHA-256
  `e294a0a4bd6090341c37506cb128d4f0a1b7a1e66406913e0c48f909f480c26f`.
- Independently traced source-relation setter precedence in the rules engine: imports
  are recursively merged before the importing module, and `sets` rules are then
  applied in that merged rule order.
- Built an up-to-date GitNexus index in a detached analysis worktree. Final global
  registry registration was sandbox-blocked (`EPERM` on
  `/Users/maxghenis/.gitnexus/registry.json`), so graph queries are unavailable even
  though the local index completed.
- Proved inertness independently:
  - base/head composed source is byte-identical at 22,528 bytes and SHA-256
    `a660a49b575dcce18a688309b385fb4bcb158c320a451181f9fa0e6c9273777b`;
  - both selected-output closures contain exactly 77 unique derived definitions;
  - full closure definitions have identical SHA-256
    `0e15c89b2f91182fe49ac6f609266566ee27190bee897939d3ea7b6ef1f06f96`;
  - no closure definitions were added, removed, or changed.
- Spot-checked integrity: all six applied-file hashes and external import hashes
  match; each re-signed manifest's ancestry matches its immediate parent; reverse
  index generation/check passes; focused manifest/index tests report 9 passed; the
  ten GitHub PR paths contain no program, toolchain, ledger, progress, or report path.
- Diagnosed and corrected a review-path artifact: using a worktree whose basename was
  not `rulespec-us` produced false unknown-ID/source-relation failures. A detached
  execution worktree at the same exact head under a canonical `rulespec-us` basename
  passes all 14 page-159 companion cases with both the prescribed local engine binary
  and an isolated build of the pinned engine ref.
- Added 14 independent adversarial cases spanning disagreement across MUA, BUA,
  actual-cost, and telephone paths; agreement controls; actual-cost households both
  entitled and not entitled to MUA/BUA; the removed rent exclusion; and page-163
  current-year, billing, future-season, and separate-from-rent edges.
- Added two explicit precedence compositions with the page-159/page-369 root import
  lists reversed. The complete independent suite passes 16/16 with both the prescribed
  local engine and the isolated pinned-engine build; both compositions preserve page
  369's local `$33`, page 159's current `$27`, and the federal target at `$27`.
- Proved that the precedence result is structural rather than filesystem iteration:
  both reversed-import compositions have identical evaluation-order SHA-256
  `ff39a74512fe10dac885a5675f68981c6d11570ef3acffe47edc25afe4d1981f`;
  after normalizing only array serialization order, their complete artifact SHA-256
  is `fb57bb8116d835330dd58ce9c7be81797946d690dd51f369d3e29623cd6151c2`.
  The federal target definition itself is byte-identical and points to page 159's
  current telephone allowance formula in both artifacts.
- Ran all three changed companion suites together with the prescribed invocation:
  3 files and 34 cases passed.
- Ran strict `validate --skip-reviewers` on pages 159, 163, and 165; all three passed.
- Ran the required amount mutation (`388` to `389`): the independent suite failed
  with five amount-path mismatches, then returned to 16/16 after restoration.
- Ran a behavioral shared-residence mutation that made the gate tautological while
  retaining both gate inputs: the independent suite failed with 19 mismatches across
  all four disagreement variants (MUA, BUA, actual-cost, and telephone), then returned
  to 16/16 after restoration.
- Verified exact post-mutation restoration: page 159 SHA-256 is
  `ac0c3cb1712f9f3688cba7ce1a411f948aad69303bf437ff8eeb06a78be7ad08`,
  page 165 SHA-256 is
  `072ff5be167fe30d2ae6e4c762281fa39a8974150bc3f5e91e65ecb7423dd30e`,
  and the detached execution worktree is clean.
- Wrote the final evidence-backed report to `REVIEW.md`.

## Next

- None; review complete.
