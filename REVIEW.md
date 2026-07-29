VERDICT: REQUEST-CHANGES

# Blind adversarial review — rulespec-us PR #1177

Risk: HIGH. The legal arithmetic and bounded composition are correct, but two
binding review gates fail: the claimed relation-order diagnostic does not kill
the prescribed mutation, and one proof excerpt is not verbatim in the pinned
corpus.

## Frozen target

- PR: `#1177`, “Spine Chunk 1: SALT and itemized-deduction pipelines”.
- GitHub-verified state: open, non-draft, mergeable.
- Head branch and SHA:
  `fed-parity/chunk1-salt-itemized` at
  `f4cc1b88d1efd8dcca25058695dc1735c0fbb3de`.
- Base: `main` at `54004d3c69beda3c2363f9001ca6e37012348bc2`.
- Immutable range:
  `54004d3c69beda3c2363f9001ca6e37012348bc2..f4cc1b88d1efd8dcca25058695dc1735c0fbb3de`.
- Required corpus: clean, detached
  `/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216`
  at `8af592162231e9de748ba6b98792b426ad4fe8b7`.
- Executable checks ran from the canonical-basename exact-head archive
  `.git/review-worktrees/pr-1177-canonical/rulespec-us`.

## Blocking findings

### 1. The relation-order “witness” survives the required mutation

Binding `SPINE-PLAN.md` §5 line 253 requires a companion relation-order
mutation diagnostic; §10 line 1040 separately says to add a mutation test for
relation argument order.

The target correctly declares:

```yaml
arguments:
  - TaxUnit
  - Person
```

at `salt_deduction_pipeline.yaml:63-70`, and aggregates the Person-level §911
amount at lines 168-173. The named
`itemized-section-911-relation-order-witness` at the itemized companion's lines
601-643 is only a positive fixture: one implicit TaxUnit has two Person rows,
and the case asserts a $10,000 §911 aggregate and $38,900 SALT.

I created a separate exact-head mutation archive and changed only the argument
vector to:

```yaml
arguments:
  - Person
  - TaxUnit
```

Results with pinned encoder `3869d66d...` and a fresh offline build of pinned
engine `ffd821327...`:

- SALT companion: 25/25 passed, one compiled program, zero failures.
- Combined companions: 53/53 passed, two compiled programs, zero failures.
- Pinned validation accepted the mutated SALT module with
  `ci_pass=true`, `all_passed=true`; the itemized module's only error was the
  expected stale whole-file SALT import hash, not relation order.

The current case therefore does not satisfy the binding mutation-test gate.
A coherent edit that refreshed dependent import hashes would retain green
behavioral evidence despite the reversed declaration.

Required remediation: add an asymmetric multi-TaxUnit/Person fixture or a
static relation-schema contract, and demonstrate that this exact two-line swap
fails. Re-run the unchanged target afterward to preserve 53/53 or the updated
prescribed total.

### 2. One §164 proof excerpt is not verbatim in the pinned resolved row

At `salt_deduction_pipeline.yaml:250`, the proof atom says:

```text
modified adjusted gross income means adjusted gross income increased by any
amount excluded from gross income under section 911, 931, or 933
```

The exact pinned encoder resolver selects:

- `data/corpus/provisions/us/statute/2026-07-13-recovery-r2026-07-15-self-contained-r2026-07-17-dedup.jsonl:36`
- provision ID `adcdb93a-c0f8-50e2-b044-3dae29c63fb8`

The retained row instead says:

```text
the term “modified adjusted gross income” means adjusted gross income
increased by any amount excluded from gross income under section 911, 931,
or 933
```

Case-sensitive Unicode substring counts are zero for the PR excerpt and one
for the retained wording. A programmatic audit of every source excerpt found:

- SALT: 24 total proof atoms; 13 source excerpts and 11 imports. Twelve
  excerpts matched uniquely, one was missing, none were ambiguous.
- Itemized: 23 total proof atoms; 14 source excerpts and 9 imports. All
  fourteen excerpts matched uniquely.

Pinned `proof-validate` nevertheless reports 24/24 and 23/23 with zero issues
because that command validates proof structure, not literal excerpt identity.
The task expressly requires the separate programmatic verbatim comparison, so
the structural pass does not waive this defect.

Required remediation: replace the excerpt with exact retained text. Because
that changes the SALT module hash, update the itemized module's dependent SALT
proof-import hashes, rerun all gates, and regenerate/re-sign both affected
manifests after the final content commits.

## Passing evidence

### Legal fidelity and exact tables

- SALT has exactly the eight prescribed imports; itemized has exactly the
  three prescribed imports.
- §164 arithmetic uses the retained 2026 values: $40,400 cap, $505,000
  threshold, 30% phaseout, and $10,000 floor; MFS halves those to $20,200,
  $252,500, and $5,000.
- MAGI is AGI plus imported §§911, 931, and 933 exclusions. There is no
  PolicyEngine simulation-only AGI ceiling.
- The $505,000 and $252,500 boundaries are inclusive because phaseout uses
  `max(0, MAGI - threshold)`.
- Itemized imports §67(h), requires `misc_deduction == 0`, and requires the
  imported judgment to be `not_holds`; it does not re-prove §67(h).
- Itemized imports the §68 final and reduction. It contains no local `2 / 37`,
  bracket-threshold, reduction-base, lesser-of, or final-subtraction
  computation.
- All public local amounts are guarded. Negative components make the verified
  domain fail and return zero; they are not behaviorally clamped through.
- All 16 prescribed SALT cases and all 17 prescribed itemized cases are
  present with the plan's exact tuples and expected values.

Independent exact-rational recomputations included:

- `salt-single-phaseout-plus-one`:
  `40,400 - .30 × (505,001 - 505,000) = 40,399.70`.
- `salt-mfs-phaseout-mid`:
  `20,200 - .30 × (300,000 - 252,500) = 5,950`.
- `salt-magi-911-addback`:
  `40,400 - .30 × ((500,000 + 10,000) - 505,000) = 38,900`.
- `salt-single-phaseout-mid`:
  `40,400 - .30 × 95,000 = 11,900`.
- §68 single plus one: reduction `2/37`, final `1,849,998/37`.
- §68 income lesser: reduction `20,000/37`, final `1,830,000/37`.
- §68 deduction lesser: reduction `100,000/37`, final `1,750,000/37`.
- §68 rational-rate case: reduction `20,000,000/37`, final
  `350,000,000/37`.

There were zero mismatches across all 33 adopted cases.

### Guards and proof atoms

- Companion split: 25 SALT cases = 16 plan cases + 9 fail-closed diagnostics;
  28 itemized cases = 17 plan cases + 10 fail-closed diagnostics + the
  ineffective positive relation witness.
- Invalid status, every-attestation-false across the merged closure, each
  negative component, nonindividual, nonzero misc, false aggregate
  attestation, and imported-SALT-domain failure all return `not_holds`/zero.
- The positive casualty case is present. Both §165 excerpts at itemized module
  lines 193-199 occur exactly once in the pinned §165 rows, including the
  federally declared disaster restriction.
- Pinned structural proof validation passes both modules: 24/24 and 23/23
  atoms, zero issues.

### Import surface

The exact BFS closure has ten modules: the two new pipelines, §§164, 67(h), 68,
68(b), 911(a), 931, 933, and the Rev. Proc. income-tax-brackets module.

- All 13 import selections resolve.
- All 24 proof imports resolve with exact nonlocal hashes or `sha256:local`.
- Eighty declarations have eighty unique names; sixty public rules have no
  duplicate concept.
- Entities agree. The only relation predicate is the SALT
  `(TaxUnit, Person)` relation, with no predicate collision.
- Neither `us/statutes/26/63/c.yaml` nor the Rev. Proc.
  standard-deduction module is in the closure.

### Manifests and mechanics

- The two manifests' disjoint union is exactly the four added protected
  pipeline/companion YAML files.
- Every applied-file SHA-256 matches the exact-head bytes and the signature
  parent's bytes.
- SALT content was committed at ancestor `0b71d6d72...`; itemized content at
  `ee02741beb...`.
- The signature commit is exact head `f4cc1b88d...`, its parent is
  `144d2bb84...`, and it changes only the two manifests.
- Both manifests use manual exception exactly `composition` and declare
  `hmac-sha256` with the expected key ID and 64-hex signature.
- The local HMAC secret was unavailable, but the exact-head GitHub
  `generated-guard` job succeeded. Repository Checks, source
  staleness/reverse-index, and program-artifacts workflows also succeeded.
- Reverse-index regeneration byte-matches the committed file: 4,247
  provisions, 5,105 edges, 4,490 modules. Base-to-head adds exactly 20 edges
  and removes none.
- `oracle-coverage-pending.yaml` is sorted and unique, with
  `ceiling == count == 2148`. It is the exact field-preserving union of merge
  parents `51721f059...` (2,146 entries) and `54004d3c69...` (2,141 entries);
  versus base it adds exactly the seven new executable rule IDs.
- The PR diff is exactly the intended eight files. `git diff --check` passes;
  there are no workflow, toolchain, CODEOWNERS, lockfile, state, or unrelated
  changes.
- Repository layout, reverse-index, and manifest tests: 18 passed, with one
  pre-existing warning about unmanifested modules.

### Required executable gates

- Pinned companion runner: 2 files, 53 cases, 2 compiled programs, zero
  failures.
- Pinned validate against `AXIOM_CORPUS_REPO` at the required pin: both
  modules have `ci_pass=true`, `all_passed=true`, and no errors.
- Pinned proof validation: both modules passed structurally, subject to
  blocking finding 2's independent verbatim check.

## Environment and sandbox disclosures

- Shell `gh pr view` and direct network access to GitHub were blocked. The
  read-only GitHub connector independently verified the live PR head, base,
  filenames, and workflow results. No GitHub or remote write was made.
- GitNexus 1.5.3 reported this repository unindexed. The prescribed `npx`
  path hung on restricted npm networking and its offline mode had no cached
  package. The installed analyzer parsed the exact-head graph worktree but the
  sandbox denied its global registry write to
  `/Users/maxghenis/.gitnexus/registry.json`; direct closure analysis supplied
  the import/blast-radius evidence.
- The first `/private/tmp` mutation edit was rejected by the patch sandbox as
  outside the project. The mutation was rerun under
  `.git/review-worktrees/pr-1177-relation-mutation/` without touching the
  canonical archive.
- The pinned axiom-encode environment did not include pytest, and the system
  `python` shim points to a removed Homebrew interpreter. An existing
  Python 3.14 pytest/PyYAML environment ran the repository tests.
- The local manifest HMAC key was unavailable; exact-head remote
  `generated-guard` supplied the signature verification evidence.

## Recommendation

Do not merge this head. Correct the proof excerpt and dependent import hashes,
add a mutation-killing relation-order diagnostic, rerun the canonical 53-case
suite and pinned validation/proof/verbatim checks, regenerate the index/ledger
if required, and sign the affected manifests last.
