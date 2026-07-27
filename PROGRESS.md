# New Jersey WFNJ Maximum-Benefit Evidence Progress

## State

Evidence assembly is in progress from `origin/main` at
`ecb057ef35ab47fb055213b42459c42ae63485ef`. The one-path provision frontier
is resolved, the statutory size schedule has a ten-case companion census, the
pinned RuleSpec toolchain passes all fourteen cases in the section's companion
file, and the registered PolicyEngine grid matches all ten cases. Criterion
verdicts remain provisional until the evidence narrative is complete.

The branch is `x2-nj-wfnj-max` in its own worktree. A refresh of
`origin/main` was attempted first but DNS resolution for `github.com` failed,
so the worktree uses the locally available remote-tracking ref.

## Done

- Read the employee-Medicare five-criteria evidence package and PR #1149.
- Read the r1 rank-4 New Jersey WFNJ row and its implementation pointers.
- Read the closure-sprint hard constraints and root `CLAUDE.md`.
- Created the isolated worktree and branch from the available `origin/main`.
- Confirmed the deliverable must stop short of an executable claim if the
  one-output artifact is unpublished, even when a local v0.1.1 probe passes.
- Resolved the corpus frontier as one raw occurrence and one unique path:
  encoded 1, excluded 0, pending 0.
- Verified the target is the current Schedule II table
  `[214, 425, 559, 644, 728, 814, 894, 961]`, capped at size eight with
  `$66` for each additional person.
- Added a one-input companion census for assistance-unit sizes 1 through 10,
  covering every table cell and two continuation cases.
- Ran the repository-pinned `axiom-encode@3869d66d` and
  `axiom-rules-engine@ffd82132` toolchain: 1 file, 14 cases, all passed.
- Read PolicyEngine's `nj_wfnj_payment_levels` body and confirmed it performs
  real cap, lookup, multiplication, and addition logic rather than forwarding
  a parameter.
- Built and registered the non-population
  `us-nj-wfnj-payment-level-grid` in companion
  `axiom-oracles@4e290421156198b12690cc456888dd203e4f7245`.
- Ran the registered grid on PolicyEngine 4.18.9 / PE-US 1.767.3 / core
  3.30.3: 10 matches, 0 mismatches, 0 errors; receipt SHA-256
  `e2c4d905b0f1fc9ad9ddd92eaa6658a212e35387309bbec717243343f4de7364`.
- Established that the existing section module has four derived outputs and
  composition does not prune them; a literal one-output artifact therefore
  requires a module split, and no published WFNJ program artifact exists.

## Next

- Record the released-v0.1.1 local arithmetic probe without treating the
  temporary, unpublished slice as stranger-path execution.
- Assemble and commit the evidence package, golden derivation, and final
  report with an honest five-criterion verdict.
