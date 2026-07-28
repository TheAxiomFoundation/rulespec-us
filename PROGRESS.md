# CalFresh BBCE progress

## State

- Branch: `fed-parity/ca-bbce`
- Base merge: `origin/main` at `c13cdf7dd7004659096641444f4795683689e96b`.
- Status: active defensive correctness and completeness audit; encoding not yet started.
- Repository pin after the merge: `10142cb0f07403c2de4599c76bec01e96640fda9`.
- Required California-authority corpus commit: `8af592162231e9de748ba6b98792b426ad4fe8b7`
  (available locally, but pin PR #1175 is not in `origin/main`; validation will use
  an isolated local checkout at this commit).

## Done

- Created an isolated worktree from `origin/main`.
- Recorded issue constraints and validation requirements.
- Verified that retained ACIN I-46-25 labels the CalFresh MCE/BBCE gross-income standard as 200% of the federal poverty level.
- Verified that retained MPP and 7 CFR provisions describe categorical-eligibility treatment, including the resource and income tests that categorical eligibility bypasses.
- Confirmed that the pinned corpus does not retain the controlling California authority that confers MCE through the PUB 275 TANF-funded service, nor a current authoritative exclusion set.
- Located the existing state overlay integration point without changing the federal composition or allotment arithmetic.
- Reviewed all 243 issue-linked oracle residuals at `axiom-oracles` commit `5a747cac` and documented six representative gross-only, net-only, and combined-failure cases.
- Confirmed that none of the 138 unique eligibility cases fails the resource test, so later asset-waiver coverage must use a synthetic companion.
- Wrote the source audit, case walk-throughs, skipped-gate rationale, and pending/mapping implications to the intentionally untracked `WORKER-REPORT.md`.
- Reopened the source gate after axiom-corpus#552 supplied the pinned California
  authority.
- Merged the current `origin/main`; confirmed pin PR #1175 has not landed yet and
  confirmed the required corpus commit exists in the local corpus object store.

## Next

- Verify every required retained excerpt and legal ID at corpus commit `8af592162`.
- Implement the fail-closed California BBCE overlay without changing the federal
  composition or narrowing non-BBCE California paths.
- Add boundary, waiver, exclusion, elderly/disabled, zero-benefit, and mutation
  companions.
- Run the local-pinned companion, validation, reverse-index, and pending/mapping
  audits; then finalize the six-case walkthrough report.
