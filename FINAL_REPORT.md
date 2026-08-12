# Final report — §112 combat-zone month rules

## Delivery status

- Branch: `closure/w5-eitc-112-combat`
- Base: `origin/main` at `ecb057ef3`
- Worktree: `/Users/maxghenis/TheAxiomFoundation/rulespec-us/.git/codex-worktrees/w5-eitc-112-combat`
- The requested sibling worktree path was outside the writable sandbox. The
  exact requested `git worktree add` created the branch but could not create
  that directory, so work continued in the repository-internal worktree above
  on the required branch.
- The requested output file
  `/Users/maxghenis/TheAxiomFoundation/_closure-sprint/out/w5-eitc-112-combat.result.md`
  is also outside the writable sandbox. The attempted write was rejected;
  this committed report is the complete handoff.
- Push attempted: failed with `Could not resolve host: github.com`.
- Draft PR: not created because the branch could not be pushed. Intended title:
  `Encode §112 combat-zone month rules (EITC frontier)`; intended issue
  reference: `rulespec-us#1135`.

## Per-item disposition

| Item | Disposition | Governing text and corpus paths | Focused tests | Result / blocker |
|---|---|---|---:|---|
| 19 — civilian missing-status month | Deferred | 26 USC 112(d)(2)-(3): `us/statute/26/112/d/2`, `us/statute/26/112/d/3` | 0 | Added an explicit `deferred_outputs` entry. The pinned corpus has no 5 USC 5561 record defining “active service,” “employee,” and “missing status,” and no retained Executive Order record for the President-designated Vietnam termination date. The existing aggregate missing-status regression remains. |
| 20 — hospitalization composition | Encoded | 26 USC 112(a)(2), (b)(2), (c)(2)-(3): `us/statute/26/112/a/2`, `/b/2`, `/c/2`, `/c/3` | 4 | Added a Judgment requiring hospitalization in the compensation month, medical causation, and incurrence during recorded combat-zone service. One positive case and one negative case for each required conjunct pass. |
| 21 — maximum enlisted amount | Deferred | 26 USC 112(c)(5): `us/statute/26/112/c/5` | 0 | Added an explicit `deferred_outputs` entry. Computing the amount requires the absent 37 USC 203 monthly basic-pay table plus absent 37 USC 310 and 351 special-pay rules. The existing commissioned-officer cap regression remains. |
| 22 — post-termination months | Deferred upstream computation; consumer boundary encoded | 26 USC 112(a)(2), (b)(2), (c)(3): `us/statute/26/112/a/2`, `/b/2`, `/c/3`; calendar-unit support at 26 USC 7701(a)(24): `us/statute/26/7701/a/24` | 2 | Added an explicit deferral for computing elapsed months because the corpus retains no controlling zone-specific Presidential termination designations. Corrected the consumer comparison so month 24 is included and month 25 is excluded. |
| 23 — Vietnam January 1978 transition | Encoded | Final sentences of 26 USC 112(a) and (b): `us/statute/26/112/a`, `us/statute/26/112/b` | 5 | January 1978 remains eligible; February 1978 and later Vietnam hospitalization months are barred. Tests also prove the rule does not apply to non-Vietnam hospitalization or direct combat-zone service. |

Focused counts overlap where a boundary test proves more than one provision.
The §112 companion now has 13 cases total, up from 4. The four affected
companion files have 25 cases total: 13 in §112 and 4 each in §32(c)(2),
§24(d), and root §32.

## Changes

- Extended `us/statutes/26/112.yaml` and its companion test.
- Rebound dependent §32(c)(2), §24(d), and root §32 fixtures to primitive §112
  facts; refreshed the exact §112 import-proof hashes in §32(c)(2) and §24(d).
- Refreshed `.axiom/index/provisions_to_rules.json`.
- Maintained committed `PROGRESS.md` throughout.
- Did not touch any `programs/us-*/snap/` path, toolchain file, CI workflow, or
  CODEOWNERS.

## Judgment calls

1. “Items 19–23” was interpreted as ordinals among the 23 `must_encode`
   entries, corresponding to classification rows 29, 30, 31, 32, and 34.
2. Hospitalization eligibility is a three-part conjunction: hospitalization,
   causation by the identified wound/disease/injury, and incurrence while
   serving in a legally recorded combat zone. The combat-zone/service
   definitions remain primitive where their Executive Orders are absent.
3. “More than 2 years” was applied to the existing whole-month elapsed input
   as an inclusive 24-month boundary. The retained 12-month accounting-period
   text at §7701(a)(24) supplies transparent calendar-unit support only; it is
   not treated as a substantive §112 eligibility rule.
4. The January 1978 sentence exists only at the parent `/a` and `/b` corpus
   paths, so those are cited rather than inventing unavailable leaf paths.
   The exception is a composable date-and-zone Judgment and is applied only
   to paragraph (2) hospitalization, not paragraph (1) direct service.
5. The transition rules use `1976-10-20`, the enactment date in the
   authoritative XML source credit for Pub. L. 94-569.
6. Raw corpus notes mention historical zone dates but do not retain normalized
   governing Executive Order citation paths. No dates were guessed; affected
   upstream classifications remain explicitly deferred.

## Validation

- Pinned corpus commit:
  `bf97b17baebfdf12601f7c23697524bf5adcdaed`.
- Pinned `axiom-encode` 0.2.1200 was loaded from the repository toolchain ref
  because the current checkout's environment contains a newer incompatible
  source tree.
- `axiom-encode validate --skip-reviewers` on §112, §32(c)(2), and §24(d):
  all 3 passed.
- Reviewer-enabled `axiom-encode validate` reached `CI: ✓` for all 3 modules
  but the four optional reviewers could not run because their CLI reported
  `Not logged in · Please run /login`.
- `axiom-encode proof-validate .../112.yaml`: passed, 20 atoms checked.
- `axiom-encode test` on §112, §32(c)(2), §24(d), and root §32: passed,
  4 files / 25 cases.
- `python tests/generate_reverse_index.py --check`: passed, 4,246 provisions /
  5,085 edges / 4,486 modules.
- `python -m pytest -q tests`: 64 passed, 1 failed, 1 warning. The sole failure
  is `test_encoded_modules_match_their_manifests` for the three intentionally
  changed modules: §112, §24(d), and §32(c)(2).
- Official signer dry-run with `--manual-exception '#1135'`: 4 manifests for
  7 changed RuleSpec files.
- Official signing attempt: blocked because
  `AXIOM_ENCODE_APPLY_SIGNING_KEY` is unavailable.
- `axiom-encode guard-generated`: consequently reports those same 7 files as
  lacking refreshed matching manifests. Existing signed manifests were left
  untouched; a maintainer with the signing key must run the signer and rerun
  the repository suite before merge.

## Commits

- `815a06ad6` — initialize progress ledger
- `fe2c7156b` — record source findings
- `97f742617` — encode §112 combat-zone month rules
- `63d7f173f` — refresh §112 reverse index
- `b7514d9af` — refresh top-level EITC fixture inputs
- `ca616e55f` — record validation results
