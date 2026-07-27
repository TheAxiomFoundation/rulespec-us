VERDICT: APPROVE

# Round-2 blind review — rulespec-us PR #1139

## Target and review boundary

- Target branch: `fed-parity/snap-sc`
- Reviewed head: `8da79dd4eaee96c471b1b974a60e1478b44b0959`
- Merge base: `6b0773d3f7fa6719f208154f3e609e292ab7abe7`
- Review worktree/branch: `.git/review-worktrees/pr-1139-round2-8da79dd`,
  `review/pr-1139-round2-8da79dd`

The read-only GitHub connector independently verified that PR #1139 is open at the
requested exact head, is eight commits ahead and zero behind its merge base, and has
the same ten paths as the local range. No PR-branch, remote, or GitHub write was made.
Review fixtures and this report exist only on the disposable review branch.

## Findings

No blocking or non-blocking correctness finding remains in the requested scope. Each
round-1 finding is fixed at this head and is detected by an independently written
adversarial or precedence case.

## Independent verification of the four fixes

### 1. Shared-residence disagreement gates every outcome

The retained page 165 requires multiple households in one residence to agree on MUA,
BUA, or actual costs. The repaired agreement judgment is now consumed by final MUA
and BUA entitlements and by actual-cost eligibility; the telephone-only path consumes
the gated actual-cost deduction.

Four independent disagreement cases separately activated otherwise-valid MUA, BUA,
verified actual-water, and telephone-only paths. All four final paths were denied and
the standardized local/federal monetary outputs were `$0`. In particular, the
round-1 LIHEAP/heating adversarial shape that previously awarded `$388` now returns
`$0`. Agreement controls produced `$388`, `$265`, an allowed actual-cost judgment,
and `$27` as applicable.

### 2. Current page-159 telephone precedence is deterministic

The retained sources independently confirm page 159's current `$27` telephone amount
and page 369's historical September 2009 `$33` amount. Page 369 is byte-unchanged
from the merge base. Page 159 now directly imports page 369 and defines its current
setter after imported rules.

Two review compositions imported both pages with opposite explicit root order:

- page 159 then page 369;
- page 369 then page 159.

Both cases preserved page 369's local historical value at `$33`, page 159's current
value at `$27`, the federal individual-allowance target at `$27`, and the composed
utility total at `$27`.

This does not rely on directory or file iteration. At pinned engine ref
`ffd8213271947b0189a9dd61a055c1e0e78908a0`, module loading recursively merges
imports before the importing document, then applies `sets` relations in that merged
rule order. Because page 159 explicitly imports page 369, its own current setter is
topologically later.

The two compiled evaluation orders are byte-identical, with SHA-256
`ff39a74512fe10dac885a5675f68981c6d11570ef3acffe47edc25afe4d1981f`.
The extracted federal target definitions are byte-identical and point to page 159's
current conditional formula in both artifacts. After canonicalizing collection
serialization order, the complete artifacts are also identical, SHA-256
`fb57bb8116d835330dd58ce9c7be81797946d690dd51f369d3e29623cd6151c2`.
The raw JSON files differ only in non-semantic imported-array ordering induced by the
deliberately reversed root import lists.

### 3. Rent exclusion is limited to BUA

The retained page 165 attaches “utility costs are included in rent” to the BUA
exclusion, while allowing actual costs when the household is not entitled to MUA or
BUA. The unsupported rent condition is absent from the repaired actual-cost formula.

An independent mixed case set the rent inclusion flag while supplying a separately
verified utility installation/maintenance charge. BUA was prohibited, but actual-cost
eligibility and the verified actual-cost deduction both held. Separate cases proved
that a verified actual-cost household receives neither actual treatment when entitled
to BUA (`$265`) nor when entitled to MUA (`$388`), while a household entitled to
neither standard retains actual-cost treatment.

### 4. Page-163 timing and separate-from-rent qualifications are restored

The retained page 163 makes separate payment from rent/mortgage a common condition
and distinguishes costs incurred and billed during the year from costs expected in
the next heating/cooling season. The repaired formula preserves that structure.

Independent edge cases proved:

- future cooling, separate from rent, qualifies without a current bill;
- a stale billed cooling cost outside the current year does not qualify;
- a current-year flag without an incurred-and-billed heating/cooling cost does not
  qualify; and
- expected future cooling included in rent does not qualify.

## Independent suite and negative controls

The committed review fixtures contain 14 adversarial cases plus the two reversed-order
precedence cases. The complete 16-case suite passed with both the prescribed local
engine path and an isolated clean build of the pinned engine.

The required mutations demonstrated that the suite is sensitive to the fixes:

- Changing the MUA amount from `388` to `389` caused five mismatches across the
  parameter, local, and federal amount paths.
- Making the shared-residence gate tautological while retaining both input references
  caused 19 mismatches. The failures reopened MUA at `$388`, BUA at `$265`, verified
  actual costs, and telephone at `$27` for the four disagreement variants.

Both mutations were restored with exact patches. The suite then returned to 16/16,
the execution worktree was clean, and the restored module hashes were:

- page 159:
  `ac0c3cb1712f9f3688cba7ce1a411f948aad69303bf437ff8eeb06a78be7ad08`
- page 165:
  `072ff5be167fe30d2ae6e4c762281fa39a8974150bc3f5e91e65ecb7423dd30e`

All three changed checked-in companion files passed together: 3 files, 34 cases.
Strict `validate --skip-reviewers` also passed independently for pages 159, 163, and
165.

## Current inertness

Base and head composition of `programs/us-sc/snap/fy-2026.yaml` is byte-identical:
22,528 bytes with SHA-256
`a660a49b575dcce18a688309b385fb4bcb158c320a451181f9fa0e6c9273777b`.

The compiled dependency closure selected from `snap_eligible` and `snap_benefit`
contains exactly 77 unique entries at both revisions. No closure entry was added,
removed, or changed:

- closure-name-set SHA-256:
  `2497b2569ef9723b5f8e639a7ca836e10cabd5e3f36d50db39a321c82fe32b2f`
- complete closure-definition SHA-256:
  `0e15c89b2f91182fe49ac6f609266566ee27190bee897939d3ea7b6ef1f06f96`

The full compiled artifacts appropriately differ in dormant utility definitions; none
of those changes enters the 77-entry selected-output closure.

## Source, manifest, index, and path spot checks

The corpus checkout is clean at the toolchain-pinned
`bf97b17baebfdf12601f7c23697524bf5adcdaed`. The retained SC manual provision file
has SHA-256
`c21539d472ea105695da5e007b24839b5f4e8cea9f4e6066a933e6d3817a8e13`,
and its source PDF has SHA-256
`e294a0a4bd6090341c37506cb128d4f0a1b7a1e66406913e0c48f909f480c26f`.
Pages 159, 163, 165, and 369 were read directly; the relevant amounts and
qualifications match the encodes described above.

Each re-signed manifest covers exactly its module and companion, and all six hashes
recompute exactly:

- page 159 test/module: `3ef05ee9d0c4…` / `ac0c3cb1712f…`
- page 163 test/module: `80d986299f5e…` / `c9bcd297050a…`
- page 165 test/module: `d7079aeece02…` / `072ff5be167f…`

All external import hashes match their target modules. Each `supersedes` record also
matches the immediate parent manifest and prior signature:

- page 159: manifest `fbd6db0ab974…`, signature `f6f9a77da3cf…`
- page 163: manifest `2167974aa281…`, signature `cf9a1ff88a3b…`
- page 165: manifest `988b4315af77…`, signature `4b42eaa4f215…`

Manifest provenance identifies clean pinned encoder commit
`3869d66d009f52258be35901edbef370e65a399c`, version `0.2.1200`.
The protected HMAC key is unavailable in the sandbox, so signature values could not
be cryptographically recomputed; content hashes, provenance, and ancestry were
checked independently.

Reverse-index regeneration/check passes at 4,233 provisions, 5,069 edges, and 4,484
modules. Focused manifest and reverse-index tests report 9 passed. The exact GitHub
PR path set contains only the three modules, three companions, three manifests, and
the reverse index. It contains no program, toolchain, workflow, dependency,
`PROGRESS.md`, review report, or other ledger path, and `git diff --check` passes.

## Tooling and sandbox disclosures

- GitNexus completed a fresh local index (9,064 files, 164 functions, 15 process
  traces), but sandbox policy blocked its global registration with `EPERM` on
  `/Users/maxghenis/.gitnexus/registry.json`; graph queries were therefore
  unavailable. Direct imports, pinned engine source, compiled artifacts, and selected
  closures supplied the dependency evidence.
- A first execution worktree whose basename was not `rulespec-us` produced false
  canonical-ID/source-relation failures. It was discarded for execution; all reported
  results come from exact-head worktrees with the required canonical basename.
- The first inertness probe used a stale composer checkout and rejected the
  `any_of` transformation. A clean checkout at pinned composer commit
  `331b6aab62cde94a3583a5b1310b530d7b140089` produced the successful byte and closure
  comparisons reported above.
- The prescribed `/Users/maxghenis/axiom-rules` checkout was locally modified and at
  an ancestor of the pinned engine ref. The mandated commands still passed there; an
  isolated archive at the exact pinned ref was built offline and independently passed
  the review suite and page-159 companion cross-check.

No failure was hidden, no PR content was altered, and every temporary mutation was
restored.
