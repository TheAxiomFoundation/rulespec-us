# Section 338 Canada build-and-park report

Date: 2026-08-26  
Branch: `b1/section-338-canada`  
Implementation head: `8653074163d3fe8b6546d179b12271e791a23fde`  
Worktree: `/Users/maxghenis/TheAxiomFoundation/_b1wt/rulespec-us/.worktrees/rulespec-us-338`  
Base: cached `origin/main` at `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`

## Executive status

The branch is built, locally validated, committed, unpushed, and parked. It corrects the stale Section 338 witness start from August 19 to August 22 and adds the complete corpus-groundable Proclamation 11046 alcohol incidence surface.

The full three-action closure line is **not yet closed**. The selected successor corpus release does not contain citable Annex II page provisions for Proclamations 11047 (dairy) or 11048 (motor vehicles), and its Rev-15 notes scope contains no U.S. note 51 or headings 9903.03.12–9903.03.14. Inventing the missing list atoms, paraphrasing graphic omissions, or adding a provenance waiver would violate the binding provenance regime. The branch therefore records four explicit semantic deferrals and must remain parked until a signed corpus successor and toolchain rebind exist.

No push or pull request was made. No toolchain pin, waiver, pending fingerprint, workflow, applied manifest, reverse index, or ProgramSpec was edited.

The requested external report path, `/Users/maxghenis/PolicyEngine/_tariff-p5/burndown/338-build-report.md`, is outside the session's writable roots. The sandbox rejected the write and left that pre-existing file at zero bytes. This committed file is the complete deliverable copy.

## Source and successor audit

The intended successor selector is `us-rulespec-2026-08-23-canada-338-suspension-union` (selector commit `3506cdf9`, merged as `87eddac3`). It selects the Rev-15 notes, the 2026-08-09 tariff-rulemaking union, the August 18 suspension scope, and the full schedule surface.

The build pins and independently verifies these exact source snapshots:

| Snapshot | SHA-256 | Finding |
|---|---|---|
| `2026-08-09-rulespec-tariff-rulemaking-union.jsonl` | `b25c5a42c47683b4f9fc0ad548007d10f97dd8ead629e6d1de872494030e05e0` | 40 provisions; only Proclamation 11046 alcohol Annex I/II physical pages are present for Section 338 |
| `2026-08-18-canada-338-suspension.jsonl` | `ea27a56ab605ff1dbda1a9b4a9e9bfbb38c8064b3510202d98625b19f461abb5` | 18 provisions; operative `clause-1` is present and verbatim-resolvable |
| `2026-08-04-usitc-hts-2026-rev15-notes.jsonl` | `0f3ed7ef2efb64383825db65e615959200770e8511c8d4834b16e02892cb9ec8` | 815 records; no U.S. note 51 and no 9903.03.12, .13, or .14 |

The standalone retained Federal Register roots for Proclamations 11047 and 11048 substitute graphic-omission markers for the Annex lists. Their Annex II page provisions are also absent from the successor rulemaking union. Consequently, dairy and motor-vehicle list values cannot receive verbatim page proof atoms from this release.

The successor does ground the Proclamation 11046 alcohol list: 63 unique HTS-8 values, split 12 on Annex II page 1 and 51 on page 2. It also grounds the 50-percent rate, the Section 232 exclusion, and the August 22 successor date.

Refreshing `origin/main` was attempted before worktree creation but failed because this sandbox could not resolve `github.com`. The requested branch was therefore created from the existing remote-tracking `origin/main`, not local `main`.

## Encoded inventory

### New atomic surface

- 3 new RuleSpec modules: 2 singular-source per-page incidence modules and 1 plural-source component module.
- 4 new rules: 2 page membership parameters, 1 rate parameter, and 1 derived component rate.
- 70 verbatim proof atoms: 63 membership value atoms and 7 component/rate atoms.
- 63 encoded membership values: 12 on page 1 and 51 on page 2.
- 3 companion files with 8 pure-function cases; every local input is assigned, including FALSE facts.
- 4 explicit `deferred_outputs`: dairy membership, motor-vehicle membership, dairy component rate, and motor-vehicle component rate.

### Witness and generated propagation

- 1 hand-built witness module updated.
- 5 Section 338 witness-family rules retained: the 50-percent scalar plus 4 temporally versioned applicability/entry rules.
- 26 witness-family proof atoms after correction, including 8 clause-1 successor atom occurrences across the 4 delayed rules.
- 100 generated schedule-composition modules regenerated deterministically.
- 500 generated Section 338 rule instances: 100 scalar copies and 400 delayed derived-rule copies.
- 2,600 generated Section 338 proof-atom occurrences, including 800 exact clause-1 atoms.
- 1,200 generated temporal versions across the 400 delayed rule copies.
- 100 generated companion files now contain 200 explicit Aug-21/Aug-22 rate boundary cases, with 1,400 textual input assignments including 1,000 FALSE facts. YAML aliases are not used.
- 100 ProgramSpecs remain byte-identical.

Gross Section 338 RuleSpec surface touched or added: 104 modules, 509 rule instances, and 2,696 proof-atom occurrences. These gross counts include deterministic witness copies; the unique new incidence payload is the 63-value alcohol list.

The final branch changes 213 distinct files relative to its cached `origin/main`, including committed generators, checkers, companions, `PROGRESS.md`, and this report.

## Temporal design

The design preserves the distinction between the amount proclaimed in July and legal application after the August 18 successor:

| Surface | Through Aug 18 | Aug 19–21 | From Aug 22 |
|---|---|---|---|
| `section_338_alcohol_additional_duty_rate` | no applicable scalar version | 0.50 declared amount | 0.50 declared amount |
| Component/applicability rules | zero or false | explicit zero or false successor | existing active formula |
| Canadian beer witness Section 338 component | 0 | 0 | 0.50 |
| Forced-labor Section 301 sibling | 0.10 | 0.10 | 0.10 |
| Witness total | 0.10 | 0.10 | 0.60 |
| Duty on the $10,000 witness | $1,000 | $1,000 | $6,000 |

The four witness applicability/entry rules each have three versions:

1. `2026-02-15` through `2026-08-18`: the pre-action zero/false version.
2. `2026-08-19` through `2026-08-21`: an explicit zero/false successor, proved by the clause deleting August 19 and inserting August 22.
3. From `2026-08-22`: the existing active formula, proved by the clause setting 12:01 a.m. eastern time on August 22.

The scalar intentionally remains 0.50 from August 19 because the August 18 instrument changed the effective date, not the proclaimed amount. Collection is gated by the temporally corrected component/applicability rules.

The per-page alcohol modules remain an atomic incidence surface. The standalone component consumes a caller-supplied `section_338_alcohol_annex_ii_membership` fact; end-to-end aggregation of the page-suffixed outputs into entry preparation remains merge-time wiring. The hand witness retains its narrow beer `entry_is_line_d` gate.

## Deferrals and blockers

Four module-declared outputs are deferred:

1. Dairy Annex II membership.
2. Motor-vehicle Annex II membership.
3. Dairy 50-percent component rate.
4. Motor-vehicle 50-percent component rate.

All four share the same blocking condition: the signed successor has no citable Proclamation 11047/11048 Annex II page provisions, the retained documents omit the graphics, and Rev-15 predates Note 51. A new signed corpus successor is required before verbatim values and rate/scope atoms can be emitted.

Additional parked merge-time work:

- Aggregate the page-suffixed alcohol outputs into the entry-preparation membership interface.
- Generate applied manifests for the 3 new modules and refresh the 101 existing changed module manifests (witness plus 100 generated modules).
- Rebuild `.axiom/index/provisions_to_rules.json` for the new clause and new page/component modules.
- Resolve the encoder/engine interface mismatch through the sanctioned toolchain rebind.

## Local validation

### Passing checks

- `ruff check` passes for both Section 338 tools and the schedule-composition generator.
- `generate_section_338_canada.py --check`: 6 deterministic generated files match.
- `generate_schedule_compositions.py --check`: 300 deterministic outputs match.
- Independent Section 338 checker: 2 pages, 63 atoms, 4 witness temporal rules, 100 generated modules, and 200 generated boundary cases pass source and structure assertions.
- Legacy pinned proof validation against the explicit hash-pinned extracted successor: 3 files, 70/70 atoms, no issues (12 + 51 + 7).
- New atomic pure harness: 3 test files, 8 cases, 3 compiled programs, zero failures.
- Hand witness pure harness: 137 cases, 1 compiled program, zero failures.
- All generated companions: 100 test files, 9,400 cases, 100 compiled programs, zero failures.
- Pinned engine direct compilation passes for all 3 new atomic modules.
- Pinned engine direct compilation passes for the hand witness: artifact format 2, engine 0.1.0, 727 derived outputs, fast-path compatible.
- Pinned engine direct compilation passes for representative generated shard ch72.
- Repository layout and ProgramSpec tests pass.
- All 100 ProgramSpecs have zero byte changes relative to branch base.
- All 100 generated companions have zero YAML anchor/alias hits; both temporal cases textually assign all seven local inputs.

### Expected parked failures

- `.axiom/toolchain.toml` remains bound to `us-rulespec-2026-08-08-obbb-alien-snap`, which predates this family. It was not edited.
- Strict proof validation cannot verify the protected pinned release without an attached signing broker; the local legacy proof pass used only the explicit hash-pinned extracted snapshots.
- The strict encoder paired with the c6 pinned engine fails with `unknown compile argument --rulespec-root`, confirming the anticipated toolchain-rebind boundary. Direct pinned-engine compilation succeeds.
- `test_encoded_modules_match_their_manifests` reports exactly 101 stale existing applied manifests: the witness and 100 regenerated composition modules. The 3 new atomic modules are intentionally unmanifested pending brokered apply.
- `python tests/generate_reverse_index.py --check` reports the reverse index stale. It was intentionally not regenerated before the successor rebind.

These are not waivable defects and no waiver or fingerprint was added.

## Implementation commits

1. `948dd7518` — `docs: start section 338 build progress ledger`
2. `6e0557a13` — `docs: record section 338 source audit`
3. `6936063d8` — `feat: generate grounded section 338 alcohol incidence`
4. `8d04093d8` — `fix: ground section 338 carveout proof`
5. `865307416` — `fix: delay section 338 application to August 22`

The report and final `PROGRESS.md` state are committed as the subsequent documentation checkpoint.

## Exact merge-time checklist

1. Refresh `origin/main` over a working network and confirm the branch base against the current remote; do not use local `main` as the authority.
2. In axiom-corpus, ingest official, text-bearing Annex II pages for Proclamations 11047 and 11048 through the canonical pipeline. Preserve source URLs, retrieval metadata, page boundaries, document hashes, and broker-signed manifests. Do not encode from `[GRAPHIC][TIFF OMITTED]` placeholders.
3. Re-audit the full Proclamation 11046/11047/11048 page family and independently count and deduplicate every HTS-8 atom. Reconcile the expected approximately 554-line union without treating that approximate dispatch count as an assertion oracle.
4. Rebuild the tariff-rulemaking union so it contains all three Annex II page families, Proclamation 11046 Annex I, the August 18 suspension scope, and the applicable HTS notes/schedule scope.
5. Verify—do not assume—whether the selected HTS notes scope contains U.S. note 51 and headings 9903.03.12–.14. If Rev-15 is still selected, record that it predates Note 51 and ground Note 51 exclusively to the proclamation Annex pages; otherwise select and verify the first official successor HTS revision containing the note.
6. Publish an immutable, signed corpus successor selector. Record its release name, content SHA-256, selector commit, merge commit, exact scope count, and per-scope SHA-256 values.
7. Perform the dedicated rulespec toolchain rebind under the trusted broker. Update `.axiom/toolchain.toml` only through the sanctioned rebind flow; do not hand-edit the corpus pin or validation-waiver hash.
8. Rebase or merge this parked branch onto the refreshed `origin/main` after the rebind, preserving the coherent commits and resolving any #1311 incidence overlap deliberately.
9. Point `generate_section_338_canada.py` at the canonical bound corpus checkout. Update pinned snapshot hashes only after reviewing the exact corpus diff.
10. Extend the generator with singular-source, per-page dairy and motor-vehicle modules; emit one verbatim atom per value, deterministic page companions, and exact page-count/uniqueness assertions. Remove each of the four deferrals only when its output is fully grounded.
11. Add the common 50-percent dairy and motor component surfaces with the same Aug-19–21 inert and Aug-22 active temporal design, origin gating, and Section 232/other Note 51 exclusions proved from exact pages.
12. Wire the page-suffixed alcohol/dairy/motor memberships into entry preparation or an explicit aggregation surface. Preserve per-page source singularity and test every local input, including FALSE facts.
13. Regenerate the witness and all 100 schedule compositions if the completed incidence wiring changes their dependency closure. Confirm ProgramSpecs remain unchanged unless imports intentionally change; if imports change, regenerate program scopes through the canonical tool.
14. Under the brokered apply flow, create manifests for every new RuleSpec module and refresh the 101 current stale manifests plus every newly generated dairy/motor module. Do not copy #1311's historical manual exception.
15. Regenerate and commit `.axiom/index/provisions_to_rules.json` with `python tests/generate_reverse_index.py`, then require `--check` to pass.
16. Refresh or retire existing validation fingerprints/waiver entries only through the sanctioned rebind/broker workflow. Add no feature-specific waiver.
17. Rerun both deterministic generators and the independent Section 338 checker against the canonical signed successor. Require exact list equality, no duplicates, verbatim excerpts, and stable double-render bytes.
18. Run strict broker-backed proof validation against the newly pinned release; require every new atom and every copied clause atom to resolve.
19. Run the full pure companion suite, all 100 generated companions, pinned-engine compilation for the new atomic modules, witness, and generated shards, and the complete repository pytest suite. Require manifest, reverse-index, provenance, source, and generated guards to pass with no waiver.
20. Reconcile the certificate/Yale boundary from `bnd_2026-08-19` to `bnd_2026-08-22`; verify only Aug 19–21 Canadian beer cells move from Section 338 0.50/total 0.60/$6,000 to 0/0.10/$1,000, then re-mint the certificate.
21. Mark the Section 338 closure-ledger line closed only after all three list families, their rates/exclusions, aggregation, manifests, reverse index, and bound-release validation are complete.
22. Push/open the PR only after the preceding steps. Let the broker perform manifest signing at merge time; do not sign locally.

Until that checklist is complete, retain this branch as an unmerged build artifact and do not represent the four deferred outputs—or the Section 338 ledger line—as closed.
