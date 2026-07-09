# US pipeline/suite lane A — composed state income-tax liability pipelines

Mission: turn merged state income-tax cores (states A–M, plus the OH proving
ground) into us-pe covered rows — a composed liability pipeline under
`us-XX/policies/income_tax/pilot_liability_pipeline` (mirroring #561), a
per-case suite vs pinned PolicyEngine-US (penny-exact) and TAXSIM-2024 in
axiom-oracles, coverage registration in `conformance/us-pe.yaml`, and a
scoreboard regen.

## Composable gate

A state is composable only when its rate schedule AND a
deduction/exemption/credit section are encoded on main (the four #561 pilots
all had both: CA rtc/17041+17054, IL 35/5/201+204, MA 62/3+62/4). A rate-only
core is logged as a gap (fail-closed/split ledger, oracle #757), not shipped.

## Status (2026-07-08)

| State | On main | Composable | Pipeline | Suite | Coverage row | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| OH | 5747.02 rate + 5747.71 EITC | yes (CA-style: supply exemption/credit) | DONE | oracles PR | oh_income_tax | penny-exact vs PE 6/6 |
| ME | 36/5219-SS credit only | no | — | — | — | gap: no rate schedule (36/5111 absent) |
| CO | 39-22-104 core (63 files) | already covered | — | co-state-income-tax-ecps | co_income_tax | ECPS-bridge suite exists; do not duplicate |
| CA/IL/MA/NY | rate + ded/exempt | done in #561 | pilot | *-income-tax-liability | covered | — |

## Fan-out queue (blocked on merge train rulespec-us#763)

Train #763 (132 modules) carries A–M income-tax cores: AL (40-18-5/15/19),
AZ (43-1023/1041/1072/1073), CT (12-700/704e/704i), DC (47-1806.03 rate only),
DE (30/1102/1108/1109/1110/1114/1117), GA (48-7-26/27). When #763 lands, re-scan
main and compose each state that has rate + deduction/exemption sections. DC is
rate-only → gap unless its exemption/credit lands too.

## OH decisions

- Target PE `oh_income_tax_before_refundable_credits` (== oh_income_tax for the
  childless wage grid; oh refundable credits = 0).
- Pipeline imports the encoded 5747.02 schedule; supplies the section 5747.025
  personal exemption ($2,400/$2,150/$1,900 per filer by OMAGI band) and the
  section 5747.98 $20-per-exemption exemption credit (below $30k taxable) as
  declared inputs — exactly the CA pilot's supplied-std-deduction pattern.
- Models the ordinary resident wage earner above Ohio's $26,050 no-tax
  threshold; excludes the business-income schedule and the retirement/senior/
  CDCC/joint-filing credits (all zero on the grid).
- `axiom-encode test`: 6/6 cases pass (fixtures == engine to full precision).
- Manifest signed with `--manual-exception composition`; reverse index regen.

## Log

- Worktrees from origin/main as siblings under
  `_axiom-worktrees/lane-a-suite-20260708/{rulespec-us,axiom-oracles}` so the
  oracle generator's `REPO_ROOT.parent/"rulespec-us"` resolves.
- OH pipeline authored, validated (CI ✓), signed, tested, reverse-index regen.
