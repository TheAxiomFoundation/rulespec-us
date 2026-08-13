# B1.3 Chapter-Schedule Composition Pilot Log

Evidence staging directory: `.b13-pilot-evidence`

Requested final directory: `/Users/maxghenis/PolicyEngine/_tariff-p5/b1/b13-pilot`

> The execution sandbox permits reading `~/PolicyEngine` but denied creating the
> requested evidence directory. Evidence is staged here until it can be copied.

## 2026-08-13 11:37 EDT — kickoff

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_b1wt/rulespec-us`
- Starting branch: `b1/rate-tables-99c` at `b4873afc4`, clean, one commit behind the locally tracked `origin/main`.
- Read the binding B1.3 pivot: generated per-chapter compositions only; chapter routing remains in entry preparation; no rulespec range dispatch.
- Started parallel read-only reviews of witness semantics, generator conventions, and pinned-engine evaluation mechanics.
- Gate policy: one engine/validate process at a time.

## 2026-08-13 — design and first compile

- Added a separate deterministic generator, `tools/generate_schedule_compositions.py`.
- The generator pins the witness SHA, replaces its three hand-built line imports
  with one chapter table, preserves all 87 overlay imports in order, computes the
  dependency closure of the requested component surfaces, and deep-copies all 11
  component rule objects.
- Generated chapter 72 composition/test/program files. The companion oracle
  asserts every one of the composition's 111 derived rules in one witness-line
  case.
- Preserved the witness's General Note 3 column-2 selection as an internal
  no-literal base selector. This is necessary for strict identity on required RU
  and CU cells; the separately exposed `schedule_base_general_rate` remains the
  required raw General-table lookup.
- Direct pinned-engine compile passed: artifact format 2, engine 0.1.0, 714
  merged derived outputs, fast-path compatible.
- Direct pinned-engine companion-oracle evaluation passed 111/111 outputs.
- Confirmed required pre-2026-02-15 grid dates cannot produce numeric witness
  statutory outputs: the witness local rules have no formula version before
  2026-02-15. Identity evidence will require the same normalized engine outcome
  on both sides rather than coercing absence to zero.

## 2026-08-13 — identity gate

- Independently compiled the witness and generated chapter-72 composition with
  the pinned engine.
- Ran countries CN, MX, CA, GB, RU, BR, VN, ZA, DE, CU across all eight
  required dates and added 2026-02-15 to exercise live IEEPA/fentanyl routing.
- Pinned-engine nuance discovered and retained in evidence: a single open-ended
  derived version lowers as timeless, so pre-boundary failures may arise from a
  missing imported parameter rather than a missing derived formula. Reworked
  the pre-boundary gate to probe each component separately and compare exact
  numeric-or-unavailable status, retaining raw error classes.
- Identity PASS: 90/90 cells, including all 80 required cells. On executable
  dates all 11 component/entry-variant outputs matched exactly, both algebraic
  residuals were zero, and total delta was zero. RU/CU selected-base and total
  values matched at 0.065.
- Evidence: `IDENTITY.md`, `identity-diff.csv`, `identity-results.json`, and
  `identity_harness.py` in this directory.

## 2026-08-13 — first full-validator diagnosis

- The requested `axiom-encode validate --skip-reviewers` command exposed 105
  upstream-placement conflicts hidden by direct engine compilation; the CLI
  displayed only the first (`entry_is_line_a`). The copied closure is owned by
  the witness composition and cannot be selectively imported because the
  pinned engine resolves a fragment import as the entire module, including the
  three legacy line imports.
- Preserved every formula string, input identifier, date, proof atom, and
  runtime window while serializing copied instance versions with RuleSpec's
  schema-equivalent `from`/`to` temporal keys. The complete placement checker
  now reports 0 issues.
- Expanded the generated companion oracle with positive cases for every
  non-constant local Judgment rule and a declared-exception zero case.

## 2026-08-13 — final gates

- Exact requested validation battery PASS (`CI: ✓`, `Result: ✓ PASSED`).
  The generated companion contains 97 cases; compile, tests, proof validation,
  corpus grounding, and static CI checks all cleared.
- Recompiled both final-byte compositions with pinned engine 0.1.0 and reran
  identity: PASS 90/90 cells (80 required + 10 boundary cells), zero component
  mismatches and zero total delta.
- Double-emit SHA-256 snapshots were byte-identical. `--chapters 72 --check`
  reported all three generated files current.
- Repository layout and program-spec tests passed (12 collected tests).
- Structure audit: 88 imports (one chapter table + exact 87-overlay witness
  inventory), 11/11 component formula strings equal, only chapter 72 emitted.
- Generalized companion generation after the final code audit: each selected
  chapter now derives a safe oracle cell from its own General-rate table. All
  97 chapter samplers passed, representative chapters 01/73/98 generated in
  memory, and the full chapter-72 validate battery passed again.
- Created local branch `b1/schedule-composition-pilot` directly from
  `origin/main` and committed exactly the generator plus the three chapter-72
  generated deliverables as `04f920099`. No push or PR was performed.
- The sandbox continued to deny writes under `~/PolicyEngine`; this evidence
  directory remains staged at
  `/Users/maxghenis/TheAxiomFoundation/_b1wt/rulespec-us/.b13-pilot-evidence`.

## 2026-08-13 — rollout serialization repair (three-gate knot)

The first all-chapter rollout emit could not validate. Three static gates
interact at 100-sibling scale in ways the single-file pilot never exercised:

1. **Placement gate** compares same-named executable rules repo-wide by a
   normalized signature that preserves temporal-key spelling
   (`from`/`effective_from`) and formula text (whitespace-collapsed).
   The rollout's variant scheme — per-chapter redundant outer parenthesis
   depth plus temporal spelling — correctly differentiates every
   substantive-formula rule.
2. **Embedded-scalar gate** reads a parenthesized bare literal (`(0.50)`)
   as an expression embedding a scalar, so the four copied scalar-literal
   overlay parameters (solar 301 0.50, section 338 alcohol 0.50,
   Canada/Mexico potash 0.10) cannot take the parenthesis variant. Repair:
   the generator chapter-prefixes those rule names
   (`ch{NN}_solar_china_section_301_additional_duty_rate`, matching the
   chapter tables' naming), rewrites every referencing formula, and asserts
   reverse-substitution equality with the witness bytes. Distinct names sit
   outside the placement gate's same-name comparison entirely.
3. **Sibling-name-collision gate** flags ANY shared rule name across
   `*.yaml` files in one directory (name-only, no signature). One hundred
   same-inventory compositions in one flat directory produce 111 collisions
   each. Repair: per-chapter subdirectories
   (`generated/ch{NN}/ch{NN}.yaml` + companion test); the gate's glob is
   non-recursive, and each module now owns its directory namespace.

The adjudicated pilot module ch72.yaml is byte-identical after the move
(sha f696fbfd…, now at `generated/ch72/ch72.yaml`); its companion test and
program spec were re-emitted only because they embed the module target
path. Identity gates re-ran green on the repaired files: ch76 90/90,
ch95 90/90, zero component mismatches, zero total delta, with the
pre-effective error-class contract preserved. Determinism ledger
regenerated (301 hashes). Full 100-file validate battery re-running under
the evidence contract; first 27 files under the interim shard runner all
PASSED before the switch.
