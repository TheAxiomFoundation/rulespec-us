# Washington TANF payment-standard evidence package

## State

- Worktree: `x1-wa-tanf-standard`
- Branch: `x1-wa-tanf-standard`
- Base: cached `origin/main` at `ecb057ef35ab47fb055213b42459c42ae63485ef`
- Status: RuleSpec implementation
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

## Next

- Add and compile the narrow one-output Washington TANF payment-standard
  program.
- Build, register, and run the smallest honest PolicyEngine case grid.
- Assemble and validate the five-criteria evidence package.
- Write the final report, commit each coherent step, and attempt to push and
  open a draft PR.
