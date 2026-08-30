# Progress

## State

- Active Axiom-native encoding audit for the NSF Important Notice 149 and implementation FAQ MFTRP certification adapter.
- Worktree is detached at the required `origin/main` object `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- A live `git fetch origin main` was attempted on 2026-08-30 but the sandbox could not resolve `github.com`; the existing remote-tracking ref exactly matches the required object.
- No existing branch, accepted candidate, or axiom-corpus PR #631 worktree has been modified.
- The exact source and Axiom toolchain custody audit is complete; no generated
  adapter has been accepted yet.
- Signed apply is waiting on the missing `agent-secret` keychain unlock item;
  the signing key itself has not been read or printed.

## Done

- Created a unique detached worktree and verified a clean base checkout.
- Read the repository instructions and the `agent-secrets` workflow required for signed apply.
- Started independent read-only audits of the selected official corpus records, the pinned encoder, and the real Rust engine.
- Confirmed the selected guidance records do not themselves establish a precise earlier effective date for proposal MFTRP certification.
- Confirmed no canonical `us/statutes/42/19232` module exists at the required
  base, so the adapter must expose rather than import that prerequisite.
- Recorded the source-faithful atomic rule, temporal, proof, and fixture
  contract in `bulk/ENCODING_BRIEF.md` without editing any RuleSpec YAML.

## Next

- Restore access to the dedicated signer through `agent-secret`.
- Run the actual pinned `axiom-encode` signed generation/apply against canonical `us/`, using only the allowed guidance records and committed brief.
- Accept only unchanged generated artifacts with complete proof and fixtures.
- Exercise every requested actor, role, award-status/date, project-linkage, membership, missing-gate, lapse/grace, and pre-effective adversary in generated fixtures and direct Rust.
- Record exact base, source, run, custody, artifact, fixture, proof, and Rust outcomes in `bulk/FINAL_REPORT.md`.
