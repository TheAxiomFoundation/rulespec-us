# WORKER REPORT — Atomic PR 0 (§63(c)(6) + §67(h))

## Outcome

The defensive correctness and completeness audit is complete for the worker
lane. The §63(c)(6) extraction is committed, the pre-existing §67(h) work is
re-verified against the new corpus pin, and all content/proof/companion/index
gates are green.

The branch still requires two deliberate external handoffs before merge:

1. The main lane must use the ordinary-provenance exception to sign/regenerate
   the manifests for the changed §63(c), new §63(c)(6), and existing §67(h)
   module/companion pairs. No signing was attempted here.
2. The four-repository oracle chain must land the two exact classifications
   described below. The changed-file gate rejects both `unmapped` and
   `pending_classification`, so editing the pending ledger would not unblock
   this PR and was not done.

- Branch: `fed-parity/atomic-63c6-67h`
- Base: local `origin/main` at `c13cdf7dda5948e7a86ff0c317872f93743a2084`
  (merged PR #1173)
- Final head: `3719b6d90fd5d4ecae46f42a34b90df8feab1a49`
- Pushes/GitHub writes/signing: none
- `PROGRESS.md`: tracked and committed as ordered
- `WORKER-REPORT.md`: untracked as ordered

## Required base integration

`git fetch origin main` was attempted first and failed because the sandbox
could not resolve `github.com`. The already-present local `origin/main` ref was
verified to be PR #1173's merge commit, including the corpus bump to
`10142cb0f07403c2de4599c76bec01e96640fda9`, and was merged locally with
signing disabled.

## Exact pinned-source evidence

`.axiom/toolchain.toml` pins:

```text
axiom_corpus_ref = 10142cb0f07403c2de4599c76bec01e96640fda9
```

The exact pin is present in the local axiom-corpus Git object store and was
checked out into a clean temporary clone for pinned validation.

### §63(c)(6)

All five citation paths occur exactly once at:

`data/corpus/provisions/us/statute/2026-07-27-usc-63-repair-165-title-26.jsonl`

| Row | Citation path | Atom ID | Kind | Retained rule |
|---:|---|---|---|---|
| 31 | `us/statute/26/63/c/6` | `993a3c6c-1b60-568f-8f11-9a35949bd63a` | paragraph | All A-D classes and “the standard deduction shall be zero.” |
| 32 | `us/statute/26/63/c/6/A` | `19adc4ad-781d-58c4-a6ea-45606bbc12fd` | subparagraph | MFS individual where either spouse itemizes. |
| 33 | `us/statute/26/63/c/6/B` | `3fe5a90d-7035-51b1-926f-5a1cf5b2004e` | subparagraph | Nonresident alien individual. |
| 34 | `us/statute/26/63/c/6/C` | `fa1d2706-5343-543c-93c3-bcbe79da0f4d` | subparagraph | Qualifying §443(a)(1) short-period return caused by an accounting-period change. |
| 35 | `us/statute/26/63/c/6/D` | `ede30098-e85c-51b4-a0a1-5eb823562279` | subparagraph | Estate, trust, common trust fund, or partnership. |

The parent proof excerpt and all four child excerpts resolve. The underlying
USLM text is at
`data/corpus/sources/us/statute/2026-07-27-usc-63-repair-165-title-26/uslm/usc26.xml:30282-30291`.

### §67(h)

- Provision:
  `data/corpus/provisions/us/statute/2026-07-13-recovery-r2026-07-15-self-contained-r2026-07-17-dedup.jsonl:320`
- Citation path: `us/statute/26/67/h`
- Atom ID: `f0539455-5a34-56fd-8fab-0ff3ca7a038d`
- Kind: `subsection`
- Retained rule: no miscellaneous itemized deduction is allowed for a taxable
  year beginning after December 31, 2017.
- Source XML:
  `data/corpus/sources/us/statute/2026-07-13-recovery-r2026-07-15-self-contained-r2026-07-17-dedup/official-documents/usc26-section-67.xml:206-212`

The current proof excerpt remains an exact normalized substring. The §67(h)
provision and source blobs are unchanged from the prior corpus pin.

## Implemented extraction

- Added `us/statutes/26/63/c/6.yaml`.
  - Public output:
    `us:statutes/26/63/c/6#standard_deduction_ineligible`
  - Retains the exact four statutory disqualifier classes.
  - Retains the import of
    `us:statutes/26/443/a/1#annual_accounting_period_change_with_secretary_approval`.
  - Uses the parent plus A-D exact corpus atoms.
- Added `us/statutes/26/63/c/6.test.yaml` with one eligible baseline and one
  case for each A-D disqualifier.
- Removed the local `standard_deduction_ineligible` rule and direct §443 import
  from `us/statutes/26/63/c.yaml`.
- Imported the new §63(c)(6) output into §63(c), preserving the zero-deduction
  branch without duplicating the public rule surface.
- Rewired only the extracted input/output references in the six existing
  `63/c.test.yaml` cases. The six case names and deduction assertions are
  unchanged.
- Regenerated `.axiom/index/provisions_to_rules.json`.

## Behavior preservation and mutation evidence

| Check | Result |
|---|---|
| Legacy §63(c) before extraction | 1 file, 6/6 cases passed |
| Legacy §63(c) after extraction | Same 6 named cases, 6/6 passed |
| New §63(c)(6) companion | 1 file, 5/5 cases passed |
| Combined §63 companions | 2 files, 11/11 cases passed |
| §67(h) restored companion | 1 file, 1/1 case passed |
| Final combined companion gate | 3 files, 12/12 cases passed |

§63(c)(6) mutation: replacing the nonresident-alien branch with
`nonresident_alien_individual and false` made exactly
`nonresident_alien_individual_is_ineligible` fail: expected `holds`, actual
`not_holds`. Restoration returned the combined §63 suite to 11/11.

§67(h) mutation: changing the formula from `false` to `true` made its sole
companion fail: expected `not_holds`, actual `holds`. Restoration returned the
suite to 1/1 and the module is byte-identical to committed HEAD.

## Gate results

Pinned tools:

- axiom-encode `3869d66d009f52258be35901edbef370e65a399c`
  (`0.2.1200`)
- axiom-rules-engine `ffd8213271947b0189a9dd61a055c1e0e78908a0`
- axiom-corpus `10142cb0f07403c2de4599c76bec01e96640fda9`

| Gate | Result |
|---|---|
| Pinned companions | Pass: 3 files, 12 cases, 3 compiled programs, 0 failures |
| Pinned `validate --skip-reviewers` — `63/c.yaml` | Pass, zero errors |
| Pinned `validate --skip-reviewers` — `63/c/6.yaml` | Pass, zero errors |
| Pinned `validate --skip-reviewers` — `67/h.yaml` | Pass, zero errors |
| Proof validation — `63/c.yaml` | Pass, 24 atoms, zero issues |
| Proof validation — `63/c/6.yaml` | Pass, 6 atoms, zero issues |
| Proof validation — `67/h.yaml` | Pass, 1 atom, zero issues |
| Reverse-index generation/check | Pass and byte-stable: 4,246 provisions, 5,085 edges, 4,488 modules |
| Focused repository tests | 17 passed; 1 expected unsigned-provenance failure |
| `git diff --check origin/main..HEAD` | Pass |

No standalone import-resolution artifact occurred in the integrated checkout.

The focused test failure is
`test_encoded_modules_match_their_manifests`: the changed legacy
`us/statutes/26/63/c.yaml` correctly no longer matches its old manifest hash.
The same run reports 21 unmanifested modules as a non-failing warning. This is
the expected boundary created by the explicit “NO signing” instruction.

`guard-generated` fails with exactly these six expected unsigned paths and no
others:

```text
us/statutes/26/63/c.test.yaml
us/statutes/26/63/c.yaml
us/statutes/26/63/c/6.test.yaml
us/statutes/26/63/c/6.yaml
us/statutes/26/67/h.test.yaml
us/statutes/26/67/h.yaml
```

The main lane must generate/sign the three matching manifest sets through the
ordinary-provenance exception. The composition manual exception is not
appropriate for these atomic-law modules.

## Oracle-pending and mapping audit

The pending ledger was not edited. Both outputs are currently unmapped; merely
declaring either `pending_classification` would still fail the changed-file
gate.

| Legal ID | Required axiom-oracles resolution | Needs a PE bridge? | Verified PE-US 1.767.3 candidate |
|---|---|---|---|
| `us:statutes/26/63/c/6#standard_deduction_ineligible` | P4 `not_comparable` registry entry | No one-to-one bridge exists. It still needs the exact registry entry so the gate reports `known_not_comparable`. | Nearby variable `separate_filer_itemizes` exists, but covers only §63(c)(6)(A), not (B)-(D). |
| `us:statutes/26/67/h#miscellaneous_itemized_deduction_allowed_for_individual` | `parameter_value` mapping | Yes: real positive-polarity availability bridge | `gov.irs.deductions.itemized.misc.applies` |

PolicyEngine-US version evidence came from the exact cached
`policyengine_us-1.767.3.dist-info/METADATA`. Candidate verification:

- `policyengine_us/parameters/gov/irs/deductions/itemized/misc/applies.yaml`
  exists and is boolean: `true` through 2017, `false` from 2018; runtime value
  for 2026 is `false`.
- `policyengine_us/variables/gov/irs/income/taxable_income/deductions/itemizing/misc_deduction.py`
  reads that parameter and returns zero when it is false.
- `policyengine_us/variables/household/demographic/tax_unit/separate_filer_itemizes.py`
  exists.
- `policyengine_us/variables/gov/irs/income/taxable_income/deductions/standard_deduction/basic_standard_deduction.py`
  uses that variable for the separate-filer branch, but the standard-deduction
  subtree has no matching nonresident-alien, qualifying-short-period, or
  estate/trust/common-trust-fund/partnership predicate.

Required four-repository chain:

1. Add both exact entries to axiom-oracles.
2. Bump axiom-encode to the resulting axiom-oracles commit.
3. Advance the org reusable workflow's changed-classifier encoder pin.
4. Re-run the RuleSpec changed-file gate: §63(c)(6) should classify
   `known_not_comparable`; §67(h) should classify companion-tested
   `comparable`.

## Final scope audit

`git diff --name-only origin/main..HEAD` contains exactly:

```text
.axiom/index/provisions_to_rules.json
PROGRESS.md
us/statutes/26/63/c.test.yaml
us/statutes/26/63/c.yaml
us/statutes/26/63/c/6.test.yaml
us/statutes/26/63/c/6.yaml
us/statutes/26/67/h.test.yaml
us/statutes/26/67/h.yaml
```

All are intended. No foreign path required restoration. The corpus pin,
workflow, CODEOWNERS, oracle pending ledger, and manifests have no branch
delta.

## Sandbox/tooling disclosures

- The required fetch failed on sandbox DNS resolution. The local
  remote-tracking ref was independently verified to contain PR #1173 before
  merge.
- The repository `python` shim points to a missing Homebrew interpreter.
  Reverse-index generation used the existing encoder environment's Python with
  PyYAML; generation and `--check` both passed.
- The first isolated PolicyEngine-US verification attempt could not access the
  sandboxed uv cache. Verification was repeated against the exact cached
  1.767.3 wheel with bytecode writes disabled; source and runtime checks passed.
- GitNexus graph tooling was unavailable. Exact Git objects, source inspection,
  pinned validators, companions, mutations, and repository tests supplied the
  audit evidence instead.

No sandbox failure was hidden, and no push, GitHub write, signing operation, or
ledger edit was performed.
