# US composed-pipeline / suite lane B (states N–W)

Mission: build composed state income-tax liability pipelines (rulespec-us#561
pattern, composition exception) + per-case companion suites vs pinned PE-US
(penny-exact) with TAXSIM-2024 as second oracle (mirror axiom-oracles#189) +
coverage registration, for states **N–W**, as their encoder-generated sections
land on origin/main. Validation year 2026; supplied inputs documented where the
2026 schedule is unpublished. Worktree leaf must be `rulespec-us` (the validate
input-resolver keys off it).

## On-main reality (verified via git log at 9f2709e0, 2026-07-08)

The mission's "wv/hi/ut/va/or/ri sections merged pre-train" is **not yet true**:
those states carry only CHIP/Medicaid/TANF rules on main, no income-tax statute.
Their income-tax sections are in the in-flight **merge train PR #763**
("132 bulk-encoded RuleSpec modules") — the individual bulk PRs (#619-636:
or/ri/va/ut/wv/hi) were closed and folded in. #763 is MERGEABLE, CI pending
(build + validate shards). WV credit sections #629/#632 are excluded from #763
(sibling rule-name collision) and stay open.

The only N–W income-tax surface actually on main pre-train: **us-oh** (5747.02
rate + 5747.71 EITC, merged #614/#615) and us-ny (lane A's already-composed
pilot). OH is therefore the pre-train composable; the rest wait on #763.

## Status

| State | Section(s) on main | Pipeline | Suite | PE target | Result |
| --- | --- | --- | --- | --- | --- |
| us-oh | 5747.02 (rate) | ✅ | ✅ 7 cases | oh_income_tax_before_non_refundable_credits | penny-exact (const 0.00204 float residual) |
| us-wv | pending #763 | — | — | — | blocked on train |
| us-hi | pending #763 | — | — | — | blocked on train |
| us-ut | pending #763 | — | — | — | blocked on train |
| us-va | pending #763 | — | — | — | blocked on train |
| us-or | pending #763 | — | — | — | blocked on train |
| us-ri | pending #763 | — | — | — | blocked on train |

### us-oh (done)
ORC 5747.02(A)(3)(c) two-tier nonbusiness tax: 0 at/below the $26,050 no-tax
threshold, else $332.00 + 2.75% of the excess. Supplied inputs = the encoded
5747.02 parameters (threshold 26050, base 332, rate 0.0275) plus PE's tiered
personal exemption (2400/2150/1900 per exemption). Compared against PE
`oh_income_tax_before_non_refundable_credits` at 2026 — PE reproduces the $332
base via an implied first-bracket rate (0.0127448 x 26050 = 332.00204), so the
composed liability matches to the cent (constant 0.00204 float residual, sub-cent).
`oh_income_tax_before_refundable_credits` was rejected as the target because it
nets a $20 low-income exemption credit (single-30k) the before-credits core
excludes. Business-income branch 5747.02(A)(4)(b) deferred (no business income).
Gate battery green: validate, proof-validate (3 atoms), companion test (7 cases),
guard-generated (manual_exception=composition), oracle-coverage pending ratchet,
reverse-index.

## Fan-out plan (on #763 merge)

Foreground-poll #763; when it lands, compose in landing order, only where the
encoded surface covers PE's components (else note gaps to ledger #757). Expected
supplied-rate slices (rate schedule absent from the encoded surface, supplied as
current authority, anchored to the imposition section), mirroring the CA pattern:
- **wv** — 11-21-3 (imposition) + 11-21-10 (taxable income) + 11-21-16
  (exemptions); rate schedule 11-21-4e not encoded → supplied. Credits 11-21-21/23
  excluded from #763.
- **or** 316.037/316.085, **ri** 44-30-2.6, **ut** 59-10-104, **va** 58.1-320/321,
  **hi** 235-51 — compose as their sections land.

Oracle side (axiom-oracles, mirror #189): per state add the pipeline liability
concept to scripts/generate_state_income_tax_liability.py (`_PE_VAR`,
`_TAXSIM_STATE`, grid), a comparison suite yaml, generate the v2 report under
dashboard/public/data, and a disposition for the TAXSIM-2024 residual. Merge one
at a time; rebase immediately before merge; verify after; no admin-merge.

## Log
- Setup: worktree from origin/main (leaf `rulespec-us`); toolchain confirmed by
  validating lane A's us-ca pipeline (validate/proof/test green).
- us-oh: authored pipeline + suite, PE-probed the 2026 grid on pinned PE-US
  (policyengine[us]==4.18.9) for penny-exact inputs, signed manifest, regen index,
  committed. PR opened.
