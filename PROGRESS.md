# CalFresh BBCE progress

## State

- Branch: `fed-parity/ca-bbce`
- Base merge: local `origin/main` at
  `c13cdf7dda5948e7a86ff0c317872f93743a2084`; the sandbox cannot resolve
  GitHub to refresh the remote-tracking ref.
- Pin merge: locally retained #1175 head
  `6f17fe22f437fe29886d2ed053d360ce231a87e6`, merged as
  `b94b84627`; this is the exact pin change reported merged upstream.
- Status: active defensive correctness and completeness audit; the
  authority-backed MCE gate is integrated into the California FY 2026
  composition and program. Final validation, mutation, index, and oracle
  mapping audits are next.
- Repository corpus pin:
  `8af592162231e9de748ba6b98792b426ad4fe8b7`.

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
- Confirmed the existing branch already contains the locally available
  `origin/main`.
- Attempted to refresh `origin/main`; recorded the sandbox DNS failure.
- Merged the locally retained #1175 head and verified the required corpus pin
  directly in `.axiom/toolchain.toml`.
- Verified the operative WIC, ACL, ACIN, and retained 7 CFR excerpts at corpus
  commit `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Added a California-only MCE module with an inclusive 200% FPL screen, the PUB
  275 service trigger, all paragraph-(vii) household gates, WIC 18901.3's
  complete drug-felony opt-out, and all five paragraph-(ix) person exclusions.
- Reused the canonical federal alien, student, and section 273.7 work
  predicates; added new facts only for cash-out SSI and nonexempt institution
  exclusions that the federal composition does not expose.
- Added 29 isolated companion cases covering 130/165/199/200/201% FPL,
  exact large-household amounts, the seven effective California exclusion
  switches, conviction-alone drug-felony treatment, and all five member
  exclusions, plus a same-person adversary that prevents different household
  members from splitting generic and categorical member eligibility.
- Built the exact pinned rules engine offline after the source archive lacked a
  binary. The isolated pinned companion passes 29/29 cases.
- Added MCE to the California-only income/resource gate without changing the
  federal composition or the existing traditional categorical and standard
  California branches.
- Added explicit resource-test and net-ceiling waiver outputs while preserving
  the ordinary net-income allotment calculation.
- Added ACL 14-63's denial/discontinuance rule for zero-benefit traditional CE
  and MCE households of three or more, using the acyclic pre-minimum allotment.
- Preserved the ACL 13-32 E/D route above 200% FPL: MCE is off, the federal
  gross screen remains bypassed, and resource plus net tests still apply.
- Added six composed fixtures for resource waiver, net waiver with a $97
  computed benefit, E/D above-200 pass and resource-fail paths, and separate
  MCE/traditional-CE zero denials. The pinned composition companion passes
  12/12; together the two changed companions pass 41/41.
- Scoped 7 CFR 273.2(j) and the California MCE module only into the California
  FY 2026 SNAP program. The pinned composer and engine compile that program to
  328 derived outputs; the resulting `snap_eligible` expression is the intended
  residency/member/income-resource/zero-denial conjunction.
- Explicit proof validation passes the MCE module (29 atoms) and composition
  module (9 atoms) with zero issues.
- Repository layout and program-spec tests pass 12/12.

## Next

- Run the disabled-gate mutation and restore the exact source.
- Run pinned `validate --skip-reviewers`, reverse-index regeneration, and
  changed-file oracle-pending/mapping audits.
- Verify the final diff against the available `origin/main`, rewrite the
  intentionally untracked worker report with the six oracle walkthroughs, and
  record the final committed head.
