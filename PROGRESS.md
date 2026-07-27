# Washington TANF payment-standard evidence package

## State

- Worktree: `x1-wa-tanf-standard`
- Branch: `x1-wa-tanf-standard`
- Base: cached `origin/main` at `ecb057ef35ab47fb055213b42459c42ae63485ef`
- Status: evidence assembly complete; publication handoff blocked by DNS
- Network note: the initial `git fetch origin main` failed because `github.com`
  could not be resolved.

## Done

- Read the encoder preamble and repository agent notes.
- Created the required isolated worktree without modifying the dirty shared
  checkout.
- Read the employee-Medicare evidence package and reconstructed draft PR
  #1149 from its local branch after the GitHub CLI could not connect.
- Read the rank-3 r1 candidate row and every cited RuleSpec, corpus, and
  PolicyEngine source.
- Verified that `wa_tanf_payment_standard` contains real input-sensitive
  logic: it reads SPM-unit size, caps it at ten, and indexes the WAC table.
- Resolved the r1 `1/2` closure shape as one unique citation path appearing in
  two raw inventory records, not two legal paths.
- Added direct companion cases for assistance-unit sizes two through eight,
  completing sizes one through eleven while retaining the explicit
  ten-or-more boundary.
- Passed all 12 companion cases with `axiom-encode test` and released engine
  v0.1.1 through a canonical `rulespec-us` path.
- Passed the repository layout, encoding-manifest, and reverse-index suites
  (18 tests).
- Composed a transient one-output payment-standard program, compiled it with
  released engine v0.1.1, and ran the size-11 golden case to $1,662/month.
  The program was deliberately not committed under the closure-sprint freeze.
- Reproduced that compile from a clean RuleSpec snapshot at
  `65bb172054984d83a5329d1d05cc5b1c605c0479`: two byte-identical format-2
  artifacts have SHA-256
  `0b3dca0bd174e4a6ea928b1ffc8276aa3a6dcc1193ed15e8a8be262a30e1b631`.
- Recorded the released-tag local run response, including size band ten and
  $1,662 USD, while preserving the distinction between this local source-tag
  build and an official cargo-dist release asset.
- Built and registered the non-population
  `wa-tanf-payment-standard-grid` in an isolated `axiom-oracles` clone at
  `637de738198bb761b552acab4128c3fe23b5bb9d`, including its generated
  affected-comparison registration.
- Ran all eleven legal size cases against the real PolicyEngine
  `wa_tanf_payment_standard` variable for June 2026: 11 matches, zero
  mismatches, and zero errors. The runner also verified the size-ten cap and
  all ten PolicyEngine table cells.
- Passed 25 focused oracle tests plus the affected-map integrity check (26
  tests total) and Ruff; no generated comparison report, dashboard file,
  dashboard manifest, or population artifact is committed.
- Added and independently fact-checked
  `us-wa/tanf/v1-payment-standard-evidence.md`, with four criteria holding and
  `executable` explicitly false.
- Re-ran the final repository layout, encoding-manifest-structure, and
  reverse-index suites (18 tests) and all 12 companion cases.
- Attempted to push both RuleSpec and oracle branches. Both failed because
  `github.com` could not be resolved, so no draft PR was opened.

## Next

- Publish the two local branches and open a draft PR when GitHub connectivity
  is restored.
- After the program freeze, land a one-output program spec, publish its
  provenance-stamped artifact, and reproduce the golden case with a freshly
  downloaded official v0.1.1 release binary.
- Keep the candidate out of `certified-nodes.yaml` until that stranger path is
  complete and a human reviews the evidence.
