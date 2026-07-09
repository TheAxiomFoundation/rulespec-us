# US pipeline/suite lane B — composed state income-tax liability pipelines (N–W)

Mission: turn merged N–W state income-tax cores into us-pe covered rows — a
composed liability pipeline under `us-XX/policies/income_tax/pilot_liability_pipeline`
(mirroring #561), a per-case suite vs pinned PolicyEngine-US (penny-exact) and
TAXSIM-2024 in axiom-oracles, coverage registration in `conformance/us-pe.yaml`,
scoreboard regen. Mirrors lane A's runbook (PROGRESS-us-suite-lane-a.md).
Ohio was lane A's proving ground (rus#769 + or#245); this lane owns N–W.

## Composable gate (from lane A)

Composable only when the rate schedule AND a deduction/exemption/credit section
are encoded on main. Rate-only or ded-only → gap (oracle #757), not shipped.

## Status (2026-07-08)

| State | Sections (in merge train #763) | Composable | Pipeline | Suite | PE target | Result |
| --- | --- | --- | --- | --- | --- | --- |
| VA | 58.1-320 rate + 322.03 ded + 321 exempt | yes | DONE | 7 cases | va_income_tax_before_non_refundable_credits | penny-exact 6/6 (zero residual) |
| UT | 59-10-104 rate + 59-10-1018 credit | yes (flat) | DONE | 6 cases | ut_income_tax_before_credits | exact 6/6 |
| NE | 77-2715.03 rate + 77-2716.01 std ded | yes | DONE | 7 cases | ne_income_tax_before_credits | penny-exact 6/6 |
| WV | 11-21-3/-10/-16 (no rate 4e/4j) | no | — | — | — | gap: rate schedule not encoded |
| OR | 315.264/266 + 316.085 (no rate 316.037) | no | — | — | — | gap: rate not in #763 |
| RI | 44-30-103 (child rebate, not the rate) | no | — | — | — | gap: rate 44-30-2.6 not encoded |
| HI | 235-54 + 235-55.6/.7/.85 (no rate 235-51) | no | — | — | — | gap: rate 235-51 not encoded |
| NC | 105-153.7 flat rate + 105-153.9 (only an other-state credit) | no | — | — | — | gap: std-deduction §105-153.5 not encoded (the wage-slice's only taxable-income reduction; 153.9 other-state credit is $0 for a single-state filer) |
| NM | 7-2-5.8 exemption + 7-2-18.15 WFTC | no | — | — | — | gap: rate §7-2-7 not encoded |
| ND | 57-38-01.28 (joint marriage credit only) | no | — | — | — | gap: rate §57-38-30.3 not encoded |
| SC | 12-6-520 (bracket inflation adj only) | no | — | — | — | gap: base rate §12-6-510 + deduction not encoded |
| NJ | 54A:4-7 (NJ EITC only) | no | — | — | — | gap: rate §54A:2-1 not encoded |
| NE-adc/OK/WI | — | no | — | — | — | OK/WI: no income-tax statutes dir on main |

VA and UT pipelines are composed, validated (validate CI ✓, proof-validate,
companion test), signed (--manual-exception composition), and committed on this
branch (laneb-slice, based on the #763 head so the cited sections resolve for
local gates). They are HELD from PR until #763 merges; then rebase onto
post-#763 main (drops the 132 train commits, replays VA+UT), regen the reverse
index (adds only VA/UT), push, open PRs, arm auto-merge.

### VA decisions
- Va. Code 58.1-320 four-bracket progressive (2/3/5/5.75% at 3k/5k/17k), fixed
  (unindexed). Supplied floors/rates + 58.1-322.03 std deduction ($8,750 single
  / $17,500 MFJ) + 58.1-321 $930 personal exemption. taxable = AGI − ded − exempt.
- PE va_income_tax_before_non_refundable_credits == before_refundable == final on
  the childless grid (no VA credits). Penny-exact, ZERO residual (fixed brackets).

### UT decisions
- Utah Code 59-10-104(2) flat 4.45% (H.B. 106 of 2025) on Utah taxable income
  (= federal AGI for the wage earner; no separate standard deduction).
- Target ut_income_tax_before_credits (pure flat tax). Excludes the 59-10-1018
  taxpayer tax credit that PE nets into before_non_refundable_credits (phased out;
  a future enrichment could model it and target before_non_refundable).

### NE decisions (new composable state, post-train fan-out)
- Neb. Rev. Stat. 77-2715.03 four-bracket progressive tax. 2026 rates 2.46/3.51/
  4.55/4.55% (L.B. 754 compresses the top two rates to a common 4.55% in 2026) at
  the PE-2026 inflation-indexed floors: single 0/4,030/24,120/38,870, MFJ
  0/8,040/48,250/77,730. Supplied floors/rates + 77-2716.01 std deduction ($8,750
  single / $17,550 MFJ). taxable = AGI − std ded (no pre-tax exemption).
- Target ne_income_tax_before_credits (pure bracket tax). NE's personal exemption
  is a POST-tax credit (ne_exemptions, netted into before_refundable_credits), so
  it is excluded from before_credits. Penny-exact 6/6 vs pinned PE (4.18.9).
- TAXSIM-2024 residual reconstructs exactly: siitax = PE-2024 before_credits −
  2024 exemption credit ($166 single / $332 MFJ); residual = 2024→2026 rate-
  compression/indexation vintage + the credit scope. All 6 dispositioned.

## Gaps (rate section not yet encoded → not shippable; note to oracle #757)

WV/OR/RI/HI have deduction/exemption/credit sections in #763 but NOT their rate
schedule (WV §11-21-4e/4j, OR §316.037, RI §44-30-2.6, HI §235-51). They become
composable when those rate sections land in a later train; not a permanent gap.

## Fan-out on #763 merge
1. `git rebase` this branch onto post-#763 origin/main.
2. Regen reverse index (`python tests/generate_reverse_index.py`) — adds VA/UT.
3. Push, open one PR per state (or a combined VA+UT PR), arm `gh pr merge --auto`.
4. Oracle side (axiom-oracles, sibling worktree): concept mapping + suite +
   generator (_TAXSIM_STATE UT=45, VA=47; _PE_VAR; _grid) + report + dispositions
   + conformance/us-pe.yaml covered row + scoreboard regen. Merge one-at-a-time
   (behind lane A + tanf). Mirror or#245.
5. Re-scan main for any newly-landed N–W rate sections (WV/OR/RI/HI) and compose.

## Oracle side — SHIPPED decoupled from the train

axiom-oracles PR #251 (branch laneb-slice-oracles, off origin/main): VA + UT
concept mappings + suites + reports + dispositions + conformance covered rows +
scoreboard regen. Mirrors or#245 (which merged OH's oracle side while OH's
rulespec pipeline #769 was still open — proving the oracle side is independent of
the rulespec merge train). PE 6/6 exact both states; TAXSIM-2024 dispositioned
(VA std-deduction vintage; UT rate vintage + taxpayer-credit scope). 134 oracle
tests + apply_dispositions/scoreboard/vacuous-gate --checks pass locally. Merge
one-at-a-time behind lane A + tanf (or#248 GA); rebase just before merge.

## Executed — post-#763 fan-out (2026-07-08)

- **VA + UT rulespec**: rebased laneb-slice onto post-#763 origin/main
  (`git rebase --onto origin/main <train-head>` dropped the 2 train commits,
  replayed VA/UT + progress), regenerated reverse index (adds VA/UT edges only),
  pushed. **PR rus#771** open, auto-merge (squash) armed. Full-matrix CI (the
  repo-global index touch triggers it).
- **NE rulespec** (new composable state): branch `laneb-slice-ne` off origin/main;
  pipeline + 7-case companion suite + signed manifest (`sign-applied-files
  --manual-exception composition`) + index regen. `axiom-encode test` 7/7,
  proof-validate ✓, validate CI ✓. **PR rus#772** open, auto-merge armed.
- **NE oracle**: branch `laneb-slice-oracles-ne` off origin/main; concept mapping,
  comparison, dispositions (all 6 reconstructed), conformance covered row,
  scoreboard/detail/affected_map/freshness regen. Rebased behind or#248 (ga_tanf)
  and re-regenerated aggregates. pytest 132 passed; all --check gates pass.
  **PR or#253** open + MERGEABLE. Auto-merge NOT available on axiom-oracles (no
  branch protection) → maintainer merges one-at-a-time. If another oracle PR
  lands first, re-rebase + regen the aggregates (they conflict on covered count).
- **Scoreboard delta (us-pe)**: VA/UT already merged via or#251. NE adds +1 →
  **33 covered / 24.09%** (was 32 after or#248's ga_tanf).
- **Non-composable N–W** (empirical scan of main): WV/OR/RI/HI/NM/ND/SC/NJ lack
  the rate schedule; NC has the flat rate but lacks the std-deduction §105-153.5
  (only an other-state credit, $0 for the wage slice); OK/WI have no income-tax
  statutes on main. All become composable when the missing section lands in a
  later train (note to oracle #757).

## Log
- Verified my slice not on origin/main (still 9f2709e0); sections live in unmerged
  #763 (BLOCKED, throttled runners). Composed VA + UT off the #763 head.
- PE-probed both on pinned PE-US (policyengine[us]==4.18.9) for penny-exact inputs.
- rulespec VA+UT committed on laneb-slice (held for #763 rebase). Oracle side
  opened as #251; freshness.json regen fixed the vacuous-gate CI check.
