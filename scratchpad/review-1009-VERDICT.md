VERDICT: REQUEST-CHANGES

# Blind adversarial review — rulespec-us PR #1009

Reviewed PR head `3e31892d3b64cf63368927b57de1946e63bae196`
(`fed-parity/revproc`) alone. The PR's reported base and merge base are
`ba8c2a0158dd9d87cf304bded9c11fc8479d3e5e`. I did not review PR #1004 or use
campaign summaries/workpapers.

## Findings

1. **blocking — the three selectors synthesize a local filing-status legal
   classification instead of importing or deferring an upstream result.**

   - The module has no `imports:` declaration, but
     `us/policies/irs/rev-proc-2025-32/qualified-business-income.yaml:345-351`,
     `:385-391`, and `:426-432` branch on bare `filing_status`. That exposes an
     implicit module-local
     `us:policies/irs/rev-proc-2025-32/qualified-business-income#input.filing_status`.
     The companion sets that free fact at
     `qualified-business-income.test.yaml:7`, `:28`, `:40`, `:52`, and `:64`.
   - Repository-wide search at the frozen head found no executable upstream
     `filing_status` output that this module could be importing. The existing
     `us/statutes/26/199A.yaml` independently consumes its own local
     `#input.filing_status`; it is not an upstream classification output.
   - This is not a genuine factual boundary. Whether a return is joint,
     separate, head-of-household, or surviving-spouse is a derived legal
     classification. The pinned authoring contract in
     `axiom-encode@3869d66d009f52258be35901edbef370e65a399c`,
     `src/axiom_encode/harness/evals.py:5518-5527`, requires an absolute upstream
     filing-status import and expressly forbids downstream local
     `#input.filing_status` facts. Running its deterministic
     `find_tax_filing_status_local_input_issues` check against the PR returned
     one rejection for each of the three selectors.
   - This matters to the advertised #1004 repoint. Importing these selectors
     would not retire the boundary; it would introduce another independently
     settable status fact. A caller could provide contradictory statuses to the
     QBI pipeline and this module and silently select contradictory thresholds.
   - The free integer surface also fails open on invalid status values. With the
     exact pinned engine
     `ffd8213271947b0189a9dd61a055c1e0e78908a0`, I changed the final companion
     input from valid status `4` to invalid status `9`; all five cases still
     passed and status `9` received the all-other amounts. Pinned engine
     `src/formula.rs:1631-1643` lowers the final match arm as an unconditional
     fallback, so the apparent `4 => ...` arm does not constrain the domain.

   **Required fix:** retain the nine source-grounded parameters, but remove and
   explicitly defer the three selector outputs until a canonical upstream
   filing-status output exists, or encode/import that upstream legal
   classification and drive all three selectors from the absolute import. Do
   not leave a module-local status input.

2. **blocking — the PR is currently unmergeable and its green checks do not
   validate the current protected base.**

   - Live GitHub metadata on 2026-07-24 reports `mergeable: false`. The head is
     27 commits behind live `main` (`d5dcc6b3ebc5a5139dfa33d94338190da625a651`)
     with merge base `ba8c2a0`.
   - All three head-associated workflow runs are completed/successful:
     Repository Checks `30085271187`, Source staleness and reverse index
     `30085270744`, and program-artifacts `30085270806`. Generated-guard job
     `89458192778` is green, as are companion, proof, oracle-coverage,
     reverse-index, and artifact jobs.
   - Those runs validated synthetic merge commit `022bf292` into the old base
     `ba8c2a0`, before the 27 current-main commits. The two regenerated shared
     files are base-sensitive, and the currently unmergeable state means the
     old green suite is not a present merge gate.

   **Required fix:** update/rebase the branch onto current `main`, regenerate the
   shared files/manifests as required, resolve mergeability, and obtain a fresh
   complete green suite.

## Statutory and source fidelity

Pinned toolchain/corpus:

- `axiom-encode`: `3869d66d009f52258be35901edbef370e65a399c`
- `axiom-rules-engine`: `ffd8213271947b0189a9dd61a055c1e0e78908a0`
- `axiom-corpus`: `b157a201285a90f185903ba8db6aa52497c201b4`

The pinned Rev. Proc. page 21 says the table applies to taxable years beginning
in 2026. Pinned page 22 publishes exactly:

- married filing jointly: `$403,500` threshold; `$553,500` range endpoint;
- married filing separately: `$201,775`; `$276,775`;
- all other returns: `$201,750`; `$276,750`.

Pinned 26 USC 199A(b)(3) and (d)(3) state `$75,000 ($150,000 in the case of a
joint return)`. Every dollar at policy lines `24-32` and every formula at lines
`70-72`, `98-100`, `126-128`, `154-156`, `182-184`, `210-212`, `243-245`,
`276-278`, and `309-311` matches those sources.

All 12 rule versions declare `2026-01-01` through `2026-12-31`, matching
“taxable years beginning in 2026.” After rebuilding the exact pinned engine, the
normal 2026 companion passed 5/5; moving all cases to 2025 failed 5/5 with no
applicable parameter, and moving all cases to 2027 failed 5/5 with no applicable
derived version. The window is therefore correct and enforced. An initial 2027
pass came from an ambient July 6 stale engine binary; it is excluded from the
verdict in favor of the exact pinned rebuild.

Status `4` correctly receives the all-other amount for this source: §4.26 says
“joint returns,” not “joint or surviving spouse.”

## Independent companion recomputation

This table independently covers at least four cases for each of the threshold,
range-end, and width selectors.

| Companion case | Status | Threshold | Range end | Width recomputation | Expected selectors |
| --- | ---: | ---: | ---: | ---: | --- |
| Joint | 1 | 403,500 | 553,500 | 553,500 − 403,500 = 150,000 | 403,500 / 553,500 / 150,000 |
| Married filing separately | 2 | 201,775 | 276,775 | 276,775 − 201,775 = 75,000 | 201,775 / 276,775 / 75,000 |
| Single | 0 | 201,750 | 276,750 | 276,750 − 201,750 = 75,000 | 201,750 / 276,750 / 75,000 |
| Head of household | 3 | 201,750 | 276,750 | 276,750 − 201,750 = 75,000 | 201,750 / 276,750 / 75,000 |
| Surviving spouse | 4 | 201,750 | 276,750 | 276,750 − 201,750 = 75,000 | 201,750 / 276,750 / 75,000 |

The committed companion's numeric expectations are all correct. Its missing
invalid-domain case allowed the selector problem above to pass unnoticed.

## Diff shape, companions, and generated artifacts

The aggregate diff against the PR base has the expected five-file shape only:

- policy YAML;
- companion YAML;
- signed apply manifest;
- `.axiom/index/provisions_to_rules.json`;
- `oracle-coverage-pending.yaml`.

There is no touch to `.axiom/toolchain.toml`, workflows, `CODEOWNERS`, tools, or
another policy. `git diff --check` is clean. The reverse index adds only the two
Rev. Proc. page keys and this module under existing `us/statute/26/199A`.

The pending-ledger diff is textually noisy because entries were sorted, but a
semantic set comparison is exact: 2,300 → 2,312 entries, 12 QBI IDs added, zero
removed, ceiling 2,300 → 2,312. The module has 12 rules and the 12 pending IDs
match them one-for-one. This substantiates the PR body's “+12 outputs, 0 stale”
claim.

The signed manual-composition manifest names both changed RuleSpec files. Their
independently computed SHA-256 hashes match the manifest:

- policy: `b400bba8371ea7db11a1ec8519e86b1294782ca46b25fe525bb8cf4ee0c97fcb`;
- companion: `b18a65348cc8416517b3d79762001eb9350464cb7950182e53617c32cd918fa9`.

With `AXIOM_ENCODE_APPLY_SIGNING_KEY` unset, local generated-guard failed closed
because HMAC verification requires the secret. That is expected; the old-base CI
generated-guard is green, but must be rerun after the branch update.

## PR-body and oracle cross-check

- Published values, pinned-page provenance, the absence of Notice 2025-67 from
  pinned corpus `b157a201`, the signed manifest, and the fact that #1004's repoint
  is not executed in this PR are all true.
- The sibling committed QBI grid
  `dashboard/public/data/axiom-policyengine-us-qbid-grid.json` uses rulespec-us
  SHA `dc6602f2`, not this PR, and supplies
  `qualified_business_income_threshold_amount_2026` as a runtime input. It
  therefore does not validate this new module or its future import. It
  corroborates `$201,750` single and `$403,500` joint values, but contains no MFS
  case. Its 11 cases are 10 matches and one explained PolicyEngine active-QBI
  floor mismatch; that mismatch is unrelated to PR #1009.

## Local and graph checks run

- `axiom-encode validate ...qualified-business-income.yaml --skip-reviewers`:
  **pass**.
- `axiom-encode proof-validate ...qualified-business-income.yaml`: **pass**, 40
  proof atoms.
- `axiom-encode test` on the committed companion: **pass**, 1 file / 5 cases.
- Exact pinned-engine 2025 and 2027 window probes: **fail closed**, 5/5 each, as
  required.
- Exact pinned-engine invalid status `9` probe: **unexpected pass**, demonstrating
  the blocking free-input/fallback behavior.
- Repository `pytest -q`: **pass**, 67 tests, one known legacy-manifest warning.
- No-key `guard-generated`: **expected fail closed** before HMAC verification.
- `git diff --check`: **pass**.
- GitNexus index at frozen head: 8,998 files, 10,716 nodes, 11,032 edges, 15
  detected processes. The changed YAML files are represented only as `File`
  nodes with folder-containment edges; no symbols, callers, or execution flows
  are available for these YAML rules. Independent repository search likewise
  found no consumer of the new module in PR #1009.

`git fetch origin` was attempted first as required but DNS access to GitHub was
blocked in the sandbox. Frozen local refs supplied the code; the read-only GitHub
connector supplied live PR, comparison, workflow, and job state. No PR, branch,
comment, or remote repository state was changed.
