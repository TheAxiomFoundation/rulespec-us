# PR #1176 Blind Adversarial Review Progress

## State

- Review status: in progress.
- Review branch: `review/pr-1176-8d1f31d`.
- Disposable worktree: `.git/review-worktrees/pr-1176-8d1f31d`.
- GitHub-verified PR: open, mergeable, non-draft PR #1176.
- GitHub-verified head branch: `fed-parity/ca-bbce`.
- Pinned PR head: `8d1f31d50cfa094db9206172ee56c6fb68665e7c`.
- GitHub-verified base ref/tip: `main` at
  `af6c57d618acff5cb268d345653ea3e4cf64feb6`.
- Immutable PR range:
  `af6c57d618acff5cb268d345653ea3e4cf64feb6..8d1f31d50cfa094db9206172ee56c6fb68665e7c`.
- Required corpus checkout:
  `/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`.
- Required corpus pin: `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Canonical exact-head archive:
  `.git/review-worktrees/pr-1176-canonical/rulespec-us`.
- Exact pinned engine build:
  `/private/tmp/pr1176-engine-ffd82132/target/debug/axiom-rules-engine`.
- Composed/compiled program artifacts: `/private/tmp/pr1176-program`.
- Final report: `REVIEW.md`.

## Done

- Loaded the GitNexus PR-review workflow.
- Preserved the dirty primary checkout and the author's worktree.
- Verified the PR number, title, state, base, head branch, and exact head SHA
  through the read-only GitHub connector.
- Confirmed the local branch and remote-tracking ref both equal the verified
  head SHA.
- Confirmed the live compare is 17 commits ahead of current `main`, zero
  behind, with exactly the nine intended CA/program/index/manifest files.
- Created this disposable local review worktree and branch from the exact PR
  head. No PR-branch, remote, or GitHub write was made.
- Recorded the shell-network failure from `gh pr view`; the connector supplied
  the live metadata instead.
- Confirmed the required corpus worktree is clean and detached at exactly
  `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Created a canonical-basename `git archive` root from the exact PR head and
  proved a changed module's archive bytes match its target-commit bytes.
- Ran pinned-encoder validation against the required corpus checkout from the
  canonical root: both changed policy modules report `ci_pass=true`,
  `all_passed=true`, and no errors.
- Ran proof validation: all 28 MCE atoms and all 9 benefit-composition atoms
  passed.
- Built axiom-rules-engine offline from exact pin
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`.
- Ran the two changed companions from the canonical root with that engine:
  2 files, 44 cases, 2 compiled programs, zero failures.
- Composed `programs/us-ca/snap/fy-2026.yaml` with axiom-compose at exact
  workflow pin `fabe0b3b3fd6e90d3e8f075516f9b668f524f711`; the pinned engine compiled
  it successfully with exactly 328 derived outputs.
- Ran the complete repository-layout and program-spec set from the canonical
  root: 12 tests passed.
- Attempted the GitNexus review graph workflow. The exact snapshot was
  unindexed; analysis parsed it but sandbox policy denied the global registry
  write to `/Users/maxghenis/.gitnexus/registry.json`. Direct import/symbol
  searches will supply the blast-radius evidence.
- Recorded environment-only failures and successful fallbacks: shell GitHub
  DNS was blocked; `uv` could not initialize its home cache; the first Python
  environment lacked pytest; and `/Users/maxghenis/bin/pytest` points to a
  removed Homebrew Python. Read-only connector metadata, exact-source
  `PYTHONPATH` execution, and an existing pytest/PyYAML environment completed
  the required checks.
- Re-ran the exact-head canonical companion set independently: 2 files, 44
  cases, 2 compiled programs, zero failures.
- Reproduced the BBCE-gate mutation in a separate exact-head archive. Changing
  the eligible-member count gate from `> 0` to the impossible `< 0` produced
  13 assertion failures confined to exactly three intended MCE cases:
  resource waiver, net-ceiling waiver, and MCE zero-benefit denial. Restoring
  the target formula restored the target SHA-256
  `e119bb7abc2dd05d698b41e854a7b9c4a1b17e00defd559ee0258958beea5c71`
  and returned the composition companion to 12/12 green.
- Adversarially probed the apparently divergent
  `calfresh_mce_member_of_household` relation. A barred IPV member supplied
  only through the canonical federal `member_of_household` relation still
  made `calfresh_mce_household_exclusion_applies` hold and prevented MCE
  status, despite an eligible-only MCE relation row. The executable result
  refutes the provisional fail-closed seam.
- One provisional legal-proof blocker remains pending independent source
  confirmation: an ACIN proof excerpt changes retained `Broad- Based` to
  `Broad-Based`, contrary to the requested verbatim-row standard.

## Next

- Complete the manifest/index/oracle-ledger audit and independently confirm
  the remaining provisional legal-proof blocker.
- Compare federal/non-BBCE base and head compose surfaces, run a retained CA
  companion against both snapshots, finish the three disposition arithmetic
  walkthroughs, and write the evidence-backed verdict to `REVIEW.md`.
