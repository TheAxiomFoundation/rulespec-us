VERDICT: REQUEST-CHANGES

# Blind adversarial review — rulespec-us PR #1139

## Target and review boundary

- Target branch: `fed-parity/snap-sc`
- Reviewed head: `bec5142d32a84bc6a8bb51ed5d96682f6b00cbf7`
- Merge base: `6b0773d3f7fa6719f208154f3e609e292ab7abe7`
- PR-only commits: `d5394fc03955fc723a26cdb8f33cc380d6ff6c23` then `bec5142d32a84bc6a8bb51ed5d96682f6b00cbf7`
- Review worktree/branch: `.git/review-worktrees/pr-1139-bec5142`, `review/pr-1139-bec5142`

The exact target object was reviewed in disposable detached worktrees. Direct `git ls-remote` verification was attempted but the sandbox could not resolve `github.com`. Both local branch refs resolve to the requested head, and a read-only GitHub connector independently reported the same two commits, merge base, and ten-file diff for both `fed-parity/snap-sc` and the exact SHA. No PR-branch, remote, or GitHub write was made.

Program-spec scoping is deliberately excluded and its absence is not a finding. The review does, however, find assignment and federal-hook defects that must be resolved before these encodes can be safely activated.

## Blocking findings

### 1. High — the required shared-residence agreement cannot affect the assigned allowance

The retained page 165 says multiple households in one residence must agree on MUA, BUA, or actual costs. `page-165.yaml:220-237` encodes `same_residence_utility_allowance_agreement_requirement_satisfied`, but that judgment has no consumer. The page-159 amount formulas at lines 117-237 do not import it, and a dependency closure from `local_snap_utility_allowance_for_shelter_costs` excludes it.

A temporary adversarial companion set shared residence to true, agreement to false, and separately billed heating cost to true. The agreement judgment correctly returned `not_holds`, but both the local allowance and federal utility hook still returned `$388`; the added expectations failed twice. The checked-in page-165 test only asserts the orphan judgment, so the companions do not detect the broken assignment.

Gate the selected allowance/entitlement path on a satisfied agreement (or model an unresolved assignment explicitly), and test disagreement through the monetary local and federal outputs for MUA, BUA, and actual/telephone paths.

### 2. High — the new telephone setter collides with an already-scoped stale setter

`page-159.yaml:49-58` sets the federal individual-utility hook to the new conditional `$27` value. Existing `page-369.yaml:11-25,84-105` sets the same hook to an unconditional `$33` value effective in 2009, and the current SC program scopes page 369 at line 266.

The pinned rules engine applies duplicate `sets` relations sequentially, replacing the target with the later setter. The program's state list is lexicographically ordered, so normal future insertion of page 159 near pages 158–160 leaves page 369 later. A disposable exact-head wrapper importing page 159 and then page 369 confirmed that the federal individual hook evaluates to page 369's unconditional `$33`, even with empty inputs.

If activated in that order, the federal sum at `7-cfr/273/9.yaml:112-124` would produce `$421` for an MUA household, `$298` for a BUA household, and `$33` for a household with no qualifying utility cost. This is not a complaint that page 159 is presently unscoped; it is a duplicate-setter/supersession defect in the activation structure. Establish deterministic current-page precedence or explicitly remove/supersede page 369 as part of activation, with a composed integration test.

### 3. High — page 165 adds a rent exclusion to actual costs that the cited source does not contain

The retained page 165 applies “utility costs are included in the rent payment” to the BUA exclusion. Its separate actual-cost rule says actual costs are allowed when the household is not entitled to MUA or BUA. The PR newly adds:

`page-165.yaml:147-149`

```text
not multiple_utility_allowance_entitlement
and not basic_utility_allowance_entitlement
and not household_utility_costs_included_in_rent_payment
```

That third condition is not carried by the cited actual-cost text. It can deny a household that has some utilities included in rent but also has a separately paid, verified, listed utility cost. Remove the extra condition or narrow/source the input so it provably means every claimed actual charge is already included in rent, then add the mixed rent-plus-separate-cost case.

### 4. Medium — the MUA heating/cooling formula drops a common source qualifier

The retained page 163 requires that, “During the year, separately from their rent or mortgage,” households incur and are billed for, or expect next season to incur, heating/cooling costs. `page-163.yaml:65-68` has no timing predicate. Its incurred-cost inputs include “billed separately,” but the two future-cost inputs do not encode the separately-from-rent qualifier.

As modeled, a stale historic incurred cost or a future cost included in rent can satisfy this branch. Page 164's broader rent exclusion partly overlaps but does not preserve the exact common condition. Encode the timing and separate-payment qualification explicitly and cover all four current/future heating/cooling alternatives.

## Evidence digest

### Source fidelity

The pinned corpus checkout is clean at `bf97b17baebfdf12601f7c23697524bf5adcdaed`, exactly matching `.axiom/toolchain.toml`. The retained manual rows are:

- page 159: JSONL line 160, provision `54428e77-42da-5f45-90c5-4289d4479e0d`
- page 163: JSONL line 164, provision `e5dac343-0f44-56f2-951f-3d6a8d806e9f`
- page 165: JSONL line 166, provision `6661957c-9fd7-5334-8850-b85fcd9e1c3e`

The retained PDF SHA-256 is `e294a0a4bd6090341c37506cb128d4f0a1b7a1e66406913e0c48f909f480c26f`. `$388` MUA, `$265` BUA, `$27` telephone, the strict `> $20` LIHEAP threshold, 12-month lookback, BUA categories/exclusions, actual-cost categories/continuation, agreement, and non-proration text were checked directly. No PolicyEngine or FNS table supplied a policy value.

One low-impact fidelity issue remains outside the blockers: the orphan `basic_utility_allowance_covered_cost_exists` helper omits non-heating/non-cooling fuel from the list continued from page 164. The final BUA entitlement instead uses page 164's stronger at-least-two-utilities aggregate, so this helper currently has no monetary effect.

### 273.9(d)(6)(iii) structure

The intended mapping is otherwise sound: MUA maps to the federal standard hook, BUA to the limited hook, and telephone to the individual hook. Exhaustive analysis of the page-159 selection predicates found no overlapping combination: MUA wins first; BUA requires no MUA plus entitlement and verification; telephone requires neither MUA nor BUA plus its verified actual-cost path. The federal sum therefore contains at most one page-159 amount, and the fixed full amounts implement the manual's non-proration rule. Actual verified utility dollars appropriately remain outside the three standard hooks and must remain in the separate shelter-cost term when program composition is later designed.

### Companion, mutation, and validation evidence

The mandated exact-head command passed all three companions: `3 file(s), 25 case(s)`.

- Amount mutation: `mandatory_utility_allowance_amount` `388 -> 389` caused 10 failures across the parameter, local amount, and federal hook.
- Assignment mutation: flipping the BUA `not household_entitled_to_mandatory_utility_allowance` guard caused 11 failures across all three companions, including BUA loss and simultaneous MUA/BUA behavior.
- Both mutations were restored with patches; the final run passed 25/25 and the detached exact-head worktree was clean.
- The separate shared-residence adversarial case failed as described in finding 1, exposing missing companion coverage; its probe was also removed and the checkout restored clean.
- Pinned strict validation passed for all three modules.
- Manifest/reverse-index hygiene tests passed 9/9.

Additional companion gaps include the exact `$20` boundary, three of the four heating/cooling routes, stale-cost timing, mixed rent plus separate actual cost, monetary effect of disagreement, Lifeline representation, and the second non-proration branch.

### Current inertness and behavior neutrality

Current inertness passes:

- Page 159 is absent from every program spec.
- The federal module imports no SC module, and no non-PR module consumes a changed SC output.
- The sole active SC program scopes legacy pages 163 and 165, but its selected outputs are only `snap_eligible` and `snap_benefit`; its shelter transformation uses only `household_shelter_costs_incurred`.
- Base and head SC compositions are byte-identical, both SHA-256 `a660a49b575dcce18a688309b385fb4bcb158c320a451181f9fa0e6c9273777b`.
- Compiled base/head dependency closures from `snap_eligible` and `snap_benefit` each contain the same 77 items with no additions, removals, or semantic changes. The changed utility judgments are outside that closure.
- No other companion imports the changed paths/outputs. The reverse-index change is citation metadata, not a runtime import.

I did not brute-force all 4,478 repository companion files. The exact import search plus byte-identical composition and selected-output closure prove that every currently active program output and every graph-disconnected existing companion is behavior-neutral at this head.

### Manifests, index, ancestry, and diff hygiene

- The PR range contains exactly ten paths: six page YAML/companion files, three manifests, and the reverse index. It contains no program, toolchain, workflow, CODEOWNERS, dependency/lock, report, or ledger path.
- Each manifest's `applied_files` is exactly its page YAML and test; the three unions cover exactly six unique files. All six recomputed SHA-256 values, all generated-output hashes, and page-163/page-165 import hashes match.
- The manifest provenance names clean encoder commit `3869d66d009f52258be35901edbef370e65a399c`, exactly the pinned encoder ref. The range is linear: merge base → content/index commit → manifest commit.
- Local HMAC verification could not run without the protected signing key. The read-only GitHub log for the exact head shows the secret-backed `guard-generated` check received the masked key and passed all changed manifests.
- Canonical reverse-index checking reports current: 4,233 provisions, 5,069 edges, 4,484 modules. The PR index diff is only the expected nine-line page-159 citation mapping.
- Relative to the earlier encode, page 163 now composes page 164's MUA/BUA prerequisites and exclusions, adds verification, and enforces MUA precedence. Page 165 now consumes those authoritative entitlements and adds a coherent telephone-only path. These are sensible repairs, subject to the findings above.

## Tooling and sandbox disclosures

- `git ls-remote` and shell GitHub commands failed because sandbox DNS could not resolve `github.com`; read-only GitHub connector data supplied independent head/diff/check corroboration.
- GitNexus graph tools were unavailable, and the no-install CLI status probe hung until interrupted. Direct import searches, reverse-index inspection, pinned engine source, composition, and compiled dependency closure were used instead.
- The protected manifest HMAC key was unavailable locally.
- The pinned encoder virtual environment lacks pytest, and the system pytest wrapper has a broken interpreter path. The focused hygiene tests were run successfully with an available repository-compatible environment.

No failure was hidden, no PR content was altered, and all temporary mutations/probes were restored.
