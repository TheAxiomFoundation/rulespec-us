# PR #1176 round-2 repair report

## Outcome

Repair complete on `fed-parity/ca-bbce`.

- Final head: `e111d8b8d549fd80012bc7ee7d921c3e940261e9`
- Source/test implementation head: `bf7bc6fbaec50158bc313c0f62d8a5760fed8772`
- Starting resumed head: `02d6244a8`
- No push, GitHub write, signing, or manifest regeneration was performed.
- The pre-existing untracked `WORKER-REPORT.md` was not modified.

The caller-injectable derived-relation hole is closed. The exact round-2
attack and a stronger scalar-spoofing variant now fail closed while the
round-1 IPV, probation, and omission behavior remains intact.

## Fix path and rationale

I used requested path 2: retain the local projection and enforce a
source-anchored, executable fail-closed integrity invariant.

Path 1 is not expressible in the pinned language/module system:

1. Relation arguments in formulas accept bare identifiers, not fully
   qualified relation IDs.
2. Imports do not provide symbol aliases.
3. The composed program contains two relations named `member_of_household`,
   so a California bare reference cannot uniquely bind the federal state-plan
   relation.

The repair adds:

- Private federal derived integer
  `snap_state_plan_member_of_household_count`, evaluated as
  `len(member_of_household)` inside the federal state-plan module. That local
  formula binding compiles to the fully qualified federal relation.
- Private California judgment
  `calfresh_mce_canonical_membership_integrity_verified`, which requires the
  local canonical projection length to equal the trusted federal count.
- A fail-closed guard on both household MCE outputs:
  integrity failure makes household exclusion hold and makes MCE status not
  hold.

This is membership-complete under the pinned engine's union semantics. Let
`F` be the deduplicated federal rows and `C` the canonical projection after
caller rows are unioned. The projection guarantees `F` is a subset of `C`;
therefore `len(C) == len(F)` implies `C == F`. Any novel injected member makes
`C` strictly larger and trips the guard. An exact duplicate tuple is
deduplicated and cannot change any aggregation.

Caller data also cannot spoof either helper scalar: both compile as derived
formula references, not inputs. The stronger regression supplies forged
values under both helper IDs and still fails closed.

## Committed work

- `b197fb225` — expose trusted SNAP household member count.
- `5db993493` — fail closed on injected canonical SNAP members.
- `041092bc6` — record focused repair gate evidence.
- `bf7bc6fba` — isolate the derived-relation injection regression in an
  explicit fixture.
- `e111d8b8d` — complete the final progress/evidence record.

The committed adversarial fixture is
`us-ca/policies/cdss/snap/modified-categorical-eligibility.injection.test.fixture`.
It is intentionally separate from the ordinary companion. The pinned
standalone validator rejects caller inputs whose declared target is
`kind: derived_relation` during static summarization, while the pinned runtime
accepts those inputs and unions their rows. The fixture is therefore copied
over the adjacent companion only in a disposable canonical archive and
executed explicitly with the pinned runtime.

Fixture case 1 was compared programmatically with the reviewer's archived
attack: its input object and expected status are identical. The committed
fixture SHA-256 is
`8ac83ee34603c2798ac891248f4656e27f7989edf3d5703609f69f4c5530f663`.

## Gate results

All source-sensitive gates ran against canonical-root git archives with
`AXIOM_CORPUS_REPO=/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`.
The corpus pin was clean at `8af592162231e9de748ba6b98792b426ad4fe8b7`.
After the final progress commit, the exact final head was archived again:
ordinary companions passed 54/54 and the materialized injection fixture
passed 2/2.

| Gate | Result |
| --- | --- |
| Full changed companions | PASS: 54/54 assertions, 3 files, 3 compiled programs |
| Requested California companions | PASS: 47/47 assertions (35 MCE, 12 benefit) |
| Explicit injection fixture | PASS: 2/2 adversarial cases |
| Pinned module validation | PASS: all 3 modules report `ci_pass=true`, `all_passed=true`, no errors |
| Proof validation | PASS: all 3; MCE proof-required, 30 atoms, no issues |
| Compose/compile | PASS: 330 derived, 100 parameters, 3 relations |
| Layout/program contracts | PASS: 12/12 |
| Reverse-index tests | PASS: 6/6 |
| Reverse-index generator check | PASS: 4,250 provisions, 5,092 edges, 4,487 modules; no diff |
| Mutation evidence | PASS: targeted mutation caused 13 assertion failures in exactly 3 expected cases |
| Retired IPV relation probe | PASS: rejected as undeclared; 24/32 expected validation failures |
| Retired probation relation probe | PASS: rejected as undeclared; 24/32 expected validation failures |
| Round-1 omission regressions | PASS: IPV/probation fail closed; eligible omission still confers |
| Whitespace/error check | PASS: `git diff --check origin/main...HEAD` |

Compose/compile changed only the expected two private derived IDs:

- `us:policies/usda/snap/state-plan-composition#snap_state_plan_member_of_household_count`
- `us-ca:policies/cdss/snap/modified-categorical-eligibility#calfresh_mce_canonical_membership_integrity_verified`

There are no removed derived IDs and no parameter or relation inventory
changes. Compiled-AST inspection confirms:

- the trusted count is `CountRelated` over the fully qualified federal
  relation;
- the integrity guard compares canonical `CountRelated` with the derived
  federal count;
- exclusion starts with `not integrity`;
- status starts with `integrity`;
- neither helper appears as an `Input` AST node.

The mutation changed only the eligible-member comparison from `> 0` to `< 0`.
It produced 13 assertion failures in exactly the resource-waiver,
net-waiver, and zero-benefit cases. The committed source remained unchanged.

## Public-output and mapping implications

There is no new public policy output and no mapping change is needed for the
17 California mappings merged through axiom-oracles PR #424. The ProgramSpec
public outputs remain `snap_eligible` and `snap_benefit`; parameters and
relations are unchanged.

The compiled derived inventory does grow by the two helper IDs above. Both
are marked `private: true` and are implementation-only/noncomparable.
Because privacy is metadata in the pinned engine, downstream tooling that
enumerates every compiled derived ID must filter or honor `metadata.private`;
it must not treat these two helpers as new oracle-facing outputs.

## Signing handoff

The manifest-sync check intentionally does not pass before the main lane
re-signs:

- Result: 1 failed, 2 passed.
- Stale edited module manifests:
  - `us/policies/usda/snap/state-plan-composition.yaml`
  - `us-ca/policies/cdss/snap/modified-categorical-eligibility.yaml`

The changed federal and California companion artifacts must be included when
the main lane refreshes the applicable signed manifests. Existing benefit
and ProgramSpec hashes remain current. This is the only known handoff item.

## Environment and sandbox disclosures

- GitNexus graph tools were unavailable/unindexed, so the investigation used
  direct source searches, compiled artifacts, and executable evidence.
- One initial `uv` compile attempt was denied access to its default
  `~/.cache/uv`; rerunning with an explicit writable temporary path and
  `PYTHONPATH` succeeded.
- An offline `uv` attempt for a negative probe could not fetch
  `cryptography`; the already provisioned pinned environment completed it.
- A process-list diagnostic and an unrelated protected temporary-directory
  traversal were denied by the sandbox. Neither was required for a gate.
- A helper agent accidentally created `/private/tmp/.ignore-not-used`.
  Recursive removal was sandbox-blocked; after verifying the exact target,
  it was safely removed with `unlink`. The repository was unaffected.
- The first mutation-runner invocation used a relative root that doubled the
  module path; the corrected absolute-path invocation produced the evidence
  reported above.
- The first exact-head companion rerun extracted into a randomly named root,
  so canonical `us:` imports did not resolve and zero cases ran. Re-extracting
  under the required `rulespec-us` basename produced the final-head 54/54 and
  2/2 results reported above.

No required gate was skipped, and no sandbox denial changed the result.
