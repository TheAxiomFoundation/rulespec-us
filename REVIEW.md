VERDICT: REQUEST-CHANGES

# PR #1176 blind adversarial review

Reviewed the current open PR head
`8d1f31d50cfa094db9206172ee56c6fb68665e7c`
(`fed-parity/ca-bbce`) against base
`af6c57d618acff5cb268d345653ea3e4cf64feb6`. A final read-only GitHub check
confirmed that exact head, nine changed files, open/mergeable/non-draft state,
and no head drift. Legal checks used the required clean corpus worktree at
`8af592162231e9de748ba6b98792b426ad4fe8b7`.

Evidence digest: the declared 44 companions, pinned validation/proofs,
328-output program compile, layout/program tests, intended-path hygiene,
reverse index, non-regression comparisons, and three disposition calculations
all pass. Approval is blocked by a substantive member-relation fail-open, a
ProgramSpec manifest that contradicts its claimed post-encode#1312 provenance,
and one non-verbatim controlling-row excerpt.

## Blocking findings

### 1. High — an omitted barred member can gain BBCE through an independent relation

The new module declares its own
`calfresh_mce_member_of_household` data relation at
`us-ca/policies/cdss/snap/modified-categorical-eligibility.yaml:47-54`.
Both the household exclusion aggregation at lines 155-160 and the final
eligible-member aggregation at lines 404-415 range only over that California
relation. The already imported federal state-plan membership relation is a
separate relation declared at
`us/policies/usda/snap/state-plan-composition.yaml:49-56`.

The exact compiled CA program exposes the federal state-plan and California
relations as independent arity-two inputs, with no equality, subset, or
completeness invariant. I reproduced the resulting fail-open twice:

- Household size 2; gross income $2,596.95, below the $3,526 MCE ceiling.
- Federal state-plan relation: one eligible member plus a second member barred
  for an IPV.
- California MCE relation: only the eligible member.
- Actual result: `calfresh_mce_household_exclusion_applies = not_holds` and
  `calfresh_mce_status_conferred = holds`.
- Replacing the omitted member's IPV with a probation/parole violation
  produced the same result.
- Changing only the expected outputs to the legally required fail-closed
  values produced exactly two targeted failures: exclusion was expected to
  hold but did not, and MCE was expected not to hold but did.

The full companion reproducers are
`/private/tmp/pr1176-divergent-ipv-reproducer.test.yaml`
(SHA-256 `388ab6983342ab97921508f4ae1fbec1626e6d9c437496f6402cb0720a93428c`)
and `/private/tmp/pr1176-divergent-probation-reproducer.test.yaml`
(SHA-256 `ed5d548cadeaa6ac714c5d70e54b09686c30fdfc513c0e770422ee72ca3ff392`).

The initial one-row-per-relation probe was a false negative: the pinned
companion runner assigns `related_{row_index}` independently inside each
relation (`axiom_encode/cli.py:3935-3963`), so both first rows alias to
`related_0`. The two-federal-row/one-California-row probe leaves the barred
`related_1` genuinely outside the California aggregation.

This violates the PR's fail-closed claim and 7 CFR
273.2(j)(2)(vii)'s household-level prohibition. Reuse one canonical household
membership relation, or enforce and test an executable equality/completeness
invariant. Add divergent-relation tests for at least IPV and probation/parole
before re-signing.

### 2. High — the ProgramSpec manifest has the pre-#1312 routing fingerprint

The head commit says, “Program-spec manifest signed via the
post-encode#1312 signer path.” The manifest instead records:

- encoder `3869d66d009f52258be35901edbef370e65a399c`, version `0.2.1200`,
  with `dirty_tracked: false`; and
- `citation: ca-bbce:programs/us-ca/snap/fy-2026`
  at `.axiom/encoding-manifests/programs/us-ca/snap/fy-2026.json:17`.

The merged encode#1312 fix at
`6ef7c14e6e233a4f5ad04172a2603c76813d029c` routes root-level ProgramSpecs
without a repository prefix
(`axiom_encode/cli.py:50847-50851`). Its regression test requires exactly
`programs/us-sc/snap/fy-2026`
(`axiom_encode/tests/test_cli.py:15538-15600`).

Running the recorded pre-fix encoder's routing functions showed:

- canonical `rulespec-us` root: `us:programs/us-ca/snap/fy-2026`;
- noncanonical `/tmp/ca-bbce` root:
  `ca-bbce:programs/us-ca/snap/fy-2026`, exactly the target payload.

Thus the signed payload fingerprints the pre-fix noncanonical-basename
workaround and does not substantiate the commit or PR claim. Regenerate and
sign the ProgramSpec manifest through the actual post-#1312 canonical-root
path after fixing the rules.

### 3. Medium — one controlling ACIN excerpt is not verbatim

The proof excerpt at
`us-ca/policies/cdss/snap/modified-categorical-eligibility.yaml:90-91`
contains `MCE)/Broad-Based Categorical`. The controlling retained row at
`data/corpus/provisions/us-ca/guidance/2025-09-03-ca-cdss-acin.jsonl:8`,
ID `028dddf7-273f-57d4-a05d-f9127b091b5a`, literally contains
`MCE)/Broad- Based Categorical`.

This is the only mismatch among 37 excerpt-bearing proof atoms, and it does
not alter the table arithmetic. It nevertheless fails the explicit
retained-row-verbatim requirement and should be corrected to the pinned row's
text.

## Legal fidelity otherwise

The remaining legal routes match the pinned retained rows:

- WIC §18901.5 supplies the mandate.
- The MCE screen is inclusive: the formula uses `<=`, and the 200% case passes
  while the 201% case fails.
- PUB 275 issuance or online access is required, while receipt alone remains
  insufficient.
- MCE waives resources and the net eligibility ceiling; calculated net income
  still drives allotment.
- E/D status bypasses the ordinary gross screen but not the net test.
- California denies zero-benefit categorical households of three or more.
- All seven paragraph-(vii) household gates cite the retained federal 7 CFR
  273.2 row. WIC §18901.3 removes conviction-alone drug-felony exclusion while
  preserving fleeing-felon and probation/parole bars.
- The five paragraph-(ix) person exclusions remain distinct from the
  household gates.

All 15 declared or checked citation paths resolve. Proof validation passed all
28 MCE atoms and all 9 benefit-composition atoms.

## Executable, composition, and non-regression evidence

- Canonical-basename archive, exact PR bytes, required corpus path:
  pinned validation passed both changed modules with zero errors.
- Exact pinned engine
  `ffd8213271947b0189a9dd61a055c1e0e78908a0`: the two changed companions
  passed 44/44 cases across two compiled programs.
- Coverage includes 130/165/199/200/201% FPL, resource waiver, net waiver with
  benefit calculation, all seven declared exclusion flips, drug-felony versus
  probation, E/D routing, paragraph-(ix) exclusions, and zero-benefit denial.
- Gate mutation: changing the final eligible-member comparator from `> 0` to
  impossible `< 0` caused 13 assertion failures confined to the three intended
  MCE scenarios (resource waiver, net waiver, and MCE zero-benefit denial).
  Restoration returned the source SHA-256 to
  `e119bb7abc2dd05d698b41e854a7b9c4a1b17e00defd559ee0258958beea5c71`
  and the benefit companion to 12/12 green.
- Pinned composition and compile passed with exactly 328 derived outputs.
  Repository-layout and ProgramSpec tests passed 12/12.
- All 32 ProgramSpecs unaffected by CA SNAP composed byte-identically between
  base and head. This includes the nested payroll ProgramSpec.
- The CA SNAP compiled surface moved from 308 to 328 derived outputs. It added
  20 derived outputs, one parameter, and one relation; removed none; and
  changed only the expected existing
  `calfresh_income_and_resource_eligible` and `snap_eligible` bridges. The
  other 306 common derived definitions, units, and extensions are
  byte-identical.
- The pre-existing CA standard-utility companion passed 2/2 on both base and
  head with identical results.

The green declared suite does not cure finding 1 because every new companion
populates the California relation as the complete population it wants the MCE
formulas to inspect; none tests a barred federal household member omitted from
that second relation.

## Independent walkthrough arithmetic

The calculations below use the encoded FY 2026 values: $209 standard
deduction, $663 California SUA, $744 non-E/D shelter cap, $298/$546 maximum
allotments, 30% contribution rounded up, and $24 regular-month minimum for
one- and two-person eligible households.

| Case | Encoded derivation | Eligibility route and result |
| --- | --- | --- |
| `ecps-56918` | Earned $1,784.63; earned deduction `floor(20%) = $356`; net before shelter `$1,784.63 - $356 - $209 = $1,219.63`; shelter `$1,078.50 + $663 = $1,741.50`; rounded excess $1,132 capped at $744; net $475.63; contribution `ceil(30%) = $143`; `$298 - $143 = $155`. | Gross fails $1,696 ordinary ceiling but passes $2,610 MCE ceiling; net passes $1,305. Encoded result: **$155**. |
| `ecps-59281` | Unearned $2,028.17; net before shelter $1,819.17; shelter $868.50 is below half of that income, so excess is $0; net $1,819.17; contribution `ceil($545.751) = $546`; `$546 - $546 = $0`, raised to the $24 minimum. | Gross passes $2,292; net fails $1,763, so MCE's net-ceiling waiver is essential while net still determines the amount. Encoded result: **$24**. |
| `ecps-60516` | Unearned $2,031.99; net before shelter $1,822.99; shelter `$541.08 + $663 = $1,204.08`; rounded excess $293, fully deductible for E/D; net $1,529.99; contribution `ceil($458.997) = $459`; preminimum allotment $0, raised to $24. | E/D bypasses the $1,696 ordinary gross screen, but net still fails $1,305; MCE's net waiver remains necessary. Encoded result: **$24**. |

## Manifests, index, and hygiene

- The target diff is exactly nine intended manifest, index, CA policy/test,
  and ProgramSpec files. There are no workflow, toolchain, mode, or foreign
  changes after the main merge.
- The three manifests' applied-file union is exactly the five protected
  YAML/test files. Every recorded SHA-256 matches target bytes, and each
  applied file was last changed at an ancestor commit.
- Existing `supersedes` records match prior manifest hashes/signatures. All
  three use the allowed `manual_exception: composition`.
- Reverse-index regeneration/check passed: 4,250 provisions, 5,092 edges,
  4,487 modules. The delta is limited to the expected CA provisions and
  federal 273.2 links.
- `oracle-coverage-pending.yaml` is byte-identical to base, unique, sorted, and
  at its 2,139-entry ceiling. All 17 new executable IDs classify as
  known-not-comparable, so no ledger additions are required.

## Limitations and sandbox disclosures

- Cryptographic HMAC verification was not possible because
  `AXIOM_ENCODE_APPLY_SIGNING_KEY` is absent. Structural signature fields,
  supersession data, and every content hash were checked.
- Shell GitHub access failed on sandboxed DNS. The connected read-only GitHub
  service supplied the initial and final live PR metadata instead.
- The GitNexus review workflow parsed the snapshot, but sandbox policy denied
  its global registry write at `/Users/maxghenis/.gitnexus/registry.json`.
  Direct Git, import, compiled-surface, and symbol analysis replaced graph
  queries.
- `uv` could not initialize its home cache in the sandbox, so pinned source
  trees were run through existing Python environments. An attempted direct
  import of the post-#1312 encoder archive also lacked its `receipt`
  dependency; the fix source, regression test, and recorded-encoder routing
  reproduction supplied the provenance evidence.
- One isolated sub-agent patch helper rejected a private `/private/tmp`
  mutation. The reproducer remained confined to a disposable copy, and its
  source and companion were restored to the canonical hashes and rerun green.

No PR branch, remote, corpus, author worktree, or GitHub state was modified.
All review commits exist only on the disposable local
`review/pr-1176-8d1f31d` branch under `.git/review-worktrees/`.
