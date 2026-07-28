# CalFresh BBCE progress

## State

- Branch: `fed-parity/ca-bbce`
- Base merge: local `origin/main` at
  `c13cdf7dda5948e7a86ff0c317872f93743a2084`; the sandbox cannot resolve
  GitHub to refresh the remote-tracking ref.
- Pin merge: locally retained #1175 head
  `6f17fe22f437fe29886d2ed053d360ce231a87e6`, merged as
  `b94b84627`; this is the exact pin change reported merged upstream.
- Status: implementation and defensive correctness/completeness audit are
  complete. All locally runnable gates are green; the untracked worker report
  and final handoff are next.
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
- Added 32 isolated companion cases covering 130/165/199/200/201% FPL,
  exact large-household amounts, the seven effective California exclusion
  switches, conviction-alone drug-felony treatment, and all five member
  exclusions, plus same-person adversaries that prevent different household
  members from splitting generic/categorical eligibility or the serious-crime
  conviction and sentence-noncompliance predicates.
- Built the exact pinned rules engine offline after the source archive lacked a
  binary. The isolated pinned companion passed 32/32 cases after the final
  source-scope correction.
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
  12/12; together the two changed companions pass 44/44.
- Scoped 7 CFR 273.2(j) and the California MCE module only into the California
  FY 2026 SNAP program. The pinned composer and engine compile that program to
  328 derived outputs; the resulting `snap_eligible` expression is the intended
  residency/member/income-resource/zero-denial conjunction.
- Explicit proof validation passes the MCE module (29 atoms) and composition
  module (9 atoms) with zero issues.
- Repository layout and program-spec tests pass 12/12.
- Mutation evidence is complete: forcing only the MCE eligibility branch false
  produced seven assertions failing across exactly the resource-waiver,
  net-waiver, and MCE zero-benefit cases. Traditional CE, E/D, and ordinary
  routes stayed green. The exact source was restored (`git diff --exit-code`)
  and the composition companion returned to 12/12 passing.
- Added the required higher-authority checks for the retained CDSS
  implementation letters.
- Moved all member-triggered paragraph-(vii) bars to `Person` scope and
  aggregates them through the MCE household relation; only the whole-household
  workfare bar remains a direct household fact. This both matches source scope
  and prevents split-witness false positives.
- Removed the unreachable current-law effective drug-felony intermediate:
  California's WIC 18901.3 opt-out is applied directly to the retained federal
  pre-opt-out member gate.
- Expanded companion YAML aliases mechanically so the strict duplicate-key
  loader sees one unambiguous input value per fixture.
- Exact pinned `validate --skip-reviewers` passes both changed modules with
  `ci_pass=true`, `all_passed=true`, and zero errors from an isolated
  canonical-directory copy.
- Exact pinned companion execution passes 44/44; proof validation passes 28
  MCE atoms and 9 composition atoms with zero issues.
- Re-composed and compiled the California FY 2026 SNAP program after the
  member-scope correction; the exact pinned engine emits 328 derived outputs.
- Regenerated the reverse provision index: 4,250 provisions, 5,092 edges, and
  4,487 modules. The follow-up `--check` passes; the diff contains only the
  expected retained BBCE authority links to the two changed California modules.
- Replayed the disabled-BBCE-branch mutation against the final tree: 7
  assertions failed across exactly the resource-waiver (3), net-waiver (3),
  and MCE zero-benefit (1) fixtures. Restoring the branch returned the
  composition companion to 12/12, and `git diff --exit-code` confirms the
  mutation is absent.
- Re-ran repository layout and program-spec tests: 12/12 pass.
- Audited oracle coverage against axiom-oracles `origin/main`: the 17 new
  executable IDs all have positive companion assertions but are classified
  only by the broad `us-ca:` P4 fallback. The general pending ratchet therefore
  reports zero undeclared/stale entries, while the changed-file exact-mapping
  contract still requires an accompanying axiom-oracles PR with 1
  `parameter_value`, 1 `direct_variable`, and 15 exact
  `not_comparable` rows.
- Verified every proposed bridge candidate in PolicyEngine-US 1.767.3 source.
  Its California BBCE gross factor is 2 and asset limit is infinite, but both
  net-test applicability parameters are `true`; it has no PUB 275 or member-bar
  facts, so those surfaces are not legally comparable.
- Audited the final diff against both the locally available `origin/main` and
  the retained #1175 pin head. Only the upstream corpus pin, committed ledger
  and reverse index, California program/module/test files are present; no
  federal RuleSpec file or foreign path changed.

## Next

- Rewrite the intentionally untracked `WORKER-REPORT.md` with the final head,
  six conditional oracle walkthroughs, gate evidence, sandbox disclosures, and
  exact 17-row bridge mapping handoff.
