# rulespec-us

United States RuleSpec encodings — the country monorepo. One directory per
jurisdiction, plus the declarative program specs that assemble atomic rules
into runnable programs.

## Layout

- `us/`: federal encodings (`statutes/`, `regulations/`, `policies/`), with
  tests beside each encoding as `.test.yaml`.
- `us-al/` … `us-tx/`: one directory per state, same internal convention.
  Absorbed from the former standalone `rulespec-us-<state>` repos with full
  history; those repos are archived pointers.
- `programs/`: declarative compose specs, one YAML per
  (jurisdiction, program, period), consumed by `axiom-compose`. Absorbed
  from `axiom-programs` (US specs) with full history.
- `tests/`: repository-wide validation — layout, companion-test pairing,
  RuleSpec shape, derived-rule coverage, and program-spec scope auditing —
  plus `generate_reverse_index.py`, which builds the provision→rules index.
- `.axiom/toolchain.toml`: signed corpus-release and validation-waiver binding.
- `.axiom/workflow-toolchain.toml`: immutable validation, generation,
  artifact-publication, and legacy staleness-scan checkout identities (full
  commit SHAs). Role-specific pins keep compatibility migrations explicit.
- `.axiom/index/provisions_to_rules.json`: generated reverse index mapping
  each corpus citation path to the modules that depend on it (via module
  `source_verification` and proof-atom sources). Regenerate with
  `python tests/generate_reverse_index.py`; CI fails if it is stale. Do not
  edit by hand.

Durable ids are `<jurisdiction>:<path>#<rule>` — `us:statutes/7/2015/e`
lives at `us/statutes/7/2015/e.yaml`, `us-ca:regulations/mpp/63-300/1` at
`us-ca/regulations/mpp/63-300/1.yaml`. Ids are identical to the
pre-consolidation layout; only file locations changed.

## Known gaps (ratcheted)

- `known-dangling.yaml`: program-spec scope entries that don't resolve to a
  module yet (axiom-programs#14).
- `known-validation-gaps.yaml`: pre-existing content debt surfaced when
  repository-wide discipline first ran across all jurisdictions
  (rulespec-us#394). `tools/waiver_issues.py` fails when a waiver cites an
  issue that isn't open.
- `known-missing-money-atoms.yaml`: policy-bearing monetary values
  (currency parameters, currency parameter-table cells, and currency
  literals in derived formulas) that still lack a proof atom citing a
  provision. Seeded from the current backlog measured by
  `axiom-encode proof-validate --emit-ratchet`; the org
  `validate-rulespec` workflow's money-atom step reads it so CI blocks any
  new atom-less monetary value while the existing 151 are burned down.

These lists fail CI on new entries AND on listed entries that get fixed
without being removed, so they only shrink.

Do not add singular rule roots, separate parameter/test fixture files, or
generated formula artifacts.

## Validation drift and admissions

- `.github/workflows/validation-drift.yml` replaces the daily full
  validation (#1274, axiom-encode#2094). Once a day it plans a run from what
  changed since the last drift run (`tools/validation_drift.py`). It runs
  every file for an encoder merge that declares `Validation effect: tighten`
  or `loosen` (or no valid effect), an encoder commit without a merged PR, a
  rules-engine, composer or corpus pin or release, a new shared-validator
  commit in the workflow's `uses:` line, or 7 days since the last full run. It skips the run when only `none` merges happened. Each failing
  file opens or updates one `Validation drift: <path>` issue with the
  `re-encode-queue` label (at most 50 new issues per run). People close the
  issues; the run never closes them, because the validator lists only
  failures. The report reads the validator's per-chunk result lines. A leg
  that fails without explained per-file results (a crash, or a later step
  such as companion tests), fails the report, so this run's state is not
  recorded and the next run reports again. More than 50 new failures open
  50 issues and record that the next run must be full, which opens the
  rest. In `pinned`
  verifier mode, encoder main merges do not start a run; a pin change does.
  Run it by hand with `workflow_dispatch` (`scope: full`). A run that cannot
  finish its report opens or refreshes one `Validation drift run failed`
  issue (label `validation-drift-run`). Only the `issues` job can write
  issues; it checks out nothing and runs only `gh` and `jq`.
- The drift run and pull-request gating can call different shared-validator
  commits until `repository-checks.yml` moves to the same commit. Keep them
  equal.
- A red full validation after a push to main still opens or refreshes one
  alarm issue (`push-alarm` in `repository-checks.yml`).
- `.axiom/admissions/` is the reviewed, repository-specific admissions
  registry (axiom-encode#2095). Today it is dormant: it holds an empty
  `coverage-exemptions.jsonl`, and no workflow exports it to the encoder yet
  (`axiom-encode admission-registry export` from the protected `main`
  commit). A follow-up wires it into the shared validator; until then a
  record here admits nothing. `tests/test_admissions_registry.py` checks the
  file layout, and CODEOWNERS requests review.

## Switching to the encoder-main verifier

This repository verifies pull requests with the pinned encoder
(`encoder_verifier` absent, which means `pinned`). The switch to
`encoder_verifier = "main"` (axiom-encode#2091) is one configuration-only
pull request, after axiom-encode#2097 and #2101 and
TheAxiomFoundation/.github#154 have merged. Both callers
(`repository-checks.yml` and `validation-drift.yml`) must use a shared
validator commit that contains .github#154 with the verifier hold (the
.github#154 merge commit); an older validator ignores the hold. Follow
these steps.

1. Choose the verifier commit. Use an axiom-encode first-parent `main`
   commit that passed the offline replay benchmark of axiom-encode#1891.
   #1891 is an open pull request; until it merges and branch protection
   makes it a required check, run the benchmark locally on that commit. Do
   not use a commit only because it is the current tip.
2. Measure before you open the pull request. Run the full validation and
   the waiver audit of this repository with the chosen commit (locally, or
   in an encoder-side run). List every new failure and every waiver whose
   fingerprint changed.
3. Fix what step 2 found before the switch. The switch pull request must be
   configuration-only: the shared validator refuses a dependency or mode
   change beside any other path, including `known-validation-gaps.yaml`
   (TheAxiomFoundation/.github#152). So a waiver restate cannot ride in the
   switch pull request today. Re-encode the failing files, or land the
   waiver changes in their own pull requests under the pinned verifier
   where the pinned verifier accepts them. Each ledger change also changes
   `validation_waiver_set_sha256` and makes every open manifest that binds
   the whole ledger (all manifests signed before the switch) stale, so
   batch ledger changes into one pull request and plan the re-signing. If
   a restate under the new
   verifier is unavoidable, decide first whether the shared validator may
   accept the ledger in a mode-switch pull request (open question on
   TheAxiomFoundation/.github#152).
4. Open the switch pull request. It changes only:
   - `.axiom/workflow-toolchain.toml`: add `encoder_verifier = "main"` and
     `encoder_verifier_hold = "<commit from step 1>"`. Keep
     `axiom_encode_ref`; it becomes the producer floor and must be on
     first-parent axiom-encode `main` (2bdc3b421 is).
   - `.github/workflows/repository-checks.yml`: move the `uses:` line of
     `validate-rulespec.yml` to the commit that `validation-drift.yml`
     uses, and pass `encoder-verifier: main` (read it from the table, as
     `validation-drift.yml` does).

   Its CI is a full dependency change: every file and every waiver is
   checked under the held verifier (about 3.6 hours and 46 runner-hours),
   and the generated guard compares the pinned base with the new verifier.
5. Use the hold rather than a freeze of encoder merges. Each run resolves
   the verifier once, but a re-run, a later push run on `main` and the
   drift run would each pick a newer encoder `main`. The hold fixes the
   verifier commit for the switch pull request, its re-runs and the first
   push run, without asking encoder authors to stop merging. A freeze of
   validation-affecting encoder merges is the fallback if the hold is not
   available.
6. After the switch is green on `main`, remove `encoder_verifier_hold` in
   a separate pull request. A hold-only change runs the first shard and the
   guard, not a full validation, so first measure the current tip as in
   step 2, and after the merge dispatch `validation-drift` with
   `scope: full`. From then on, the drift run checks encoder merges that
   declare `loosen` or `tighten`.

Timing: all 1,939 waiver records expire on 2026-12-21 (#1980). Do the
measurement of step 2 and the switch on the same side of that date, and
renew the waivers in one ledger pull request, because a renewal changes
every waived file's record.

Producers below `axiom_encode_ref` stay rejected after the switch. Signed
pull requests from such producers need a new signed run.
