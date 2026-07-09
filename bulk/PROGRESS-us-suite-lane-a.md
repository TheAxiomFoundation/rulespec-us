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

## Lane A2 — A–M fan-out post-#763 (2026-07-08)

Re-scanned `origin/main` after the merge train. Composable gate = rate-schedule
section AND a deduction/exemption/credit section, both on main.

### Classification (complete A–M slice)

| State | Rate section | Ded/exempt/credit | Composable | Notes |
| --- | --- | --- | --- | --- |
| AL | 40-18-5 (2/4/5%) | 40-18-15 ded, 40-18-19 exempt | **yes** | top-bracket base+5% |
| CT | 12-700 (levy; sched deferred) | 12-704e/704i credits | **yes** | phase-outs → hardest |
| DE | 30/1102 (tax tables) | 30/1108/1110/1117 credits | **yes** | multi-bracket fixed |
| ID | 63-3024 (5.3%) | 63-3022D/E ded | **yes** | flat over 4,920/9,840 |
| KY | 141.020 (levy) | 141.067 family-size | **yes** | flat 3.5%, std ded 3,344 |
| MD | 10-105 (rate sched) | 10-211 exemptions | **yes** | multi-bracket; county tax separate var |
| ME | 36/5111 (tables) | 36/5124-C ded, 5126-A exempt | **yes** | multi-bracket indexed |
| MN | 290.06 (2c sched) | 290.0123 std ded, 290.0121 exempt | **yes** | multi-bracket indexed |
| AZ | **43-1011 absent** | 43-1023/1041/1072/1073 | no | rate on bulk branch, not in train |
| GA | **48-7-20 absent** | 48-7-26/27, -29.10, 7A-3 | no | rate in #757 backlog |
| HI | **235-51 absent** | 235-54, 235-55.x | no | rate in #757 backlog (lane B too) |
| IA | **422.5 absent** | 422/12,12B,12C | no | rate in #757 backlog |
| IN | **6-3-2-1 absent** | 6-3-2-x, 6-3-3-x | no | rate in #757 backlog |
| LA | **47:32 absent** | 47:294 ded, 47:297.x | no | 47:295 imposition shell delegates to 47:32 |
| MI | **206.51 absent** | 206/272 EITC only | no | rate #757 subsection-split |
| MT | **15-30-2103 absent** | 15-30-2318 only | no | rate in #757 backlog |
| DC | 47-1806.03 (rate) | **none** | no | rate-only; 47-1806.04/06 in backlog |

Non-composable logged to rulespec-us#757 (comment, 2026-07-08). CA/CO/IL/MA
already covered (#561/existing). AR/KS blocked at corpus (wave-1). MO/MS: 0 cores.

### Toolchain validated (local, this lane)

- axiom-oracles env pins `policyengine[us]==4.18.9` + `policyengine-taxsim==2.30.0`.
  `uv run --python 3.14 --extra policyengine --extra taxsim` works.
- PE 2026 OH single-60k = 1206.5020752 (axiom fixture 1206.50204) → penny-exact.
  TAXSIM 2024 = 1235.2 (vintage gap, dispositioned). Calibration loop confirmed.
- Generator crashes on UT/VA fixtures (lane B pipelines not yet on rulespec-us
  main; on `origin/laneb-slice`). Workaround: extract UT/VA `.test.yaml` from
  `origin/laneb-slice` into the worktree (untracked) so the generator completes.
  Resolves when lane B's rulespec-us PR merges.
- TAXSIM SOI state codes: AL=1 CT=7 DE=8 ID=13 KY=18 ME=20 MD=21 MN=24.

### Per-state calibration (PE 2026, `_before_refundable_credits` unless noted)

- **AL** `al_income_tax_before_refundable_credits`: single 30k/60k/150k =
  1174 / 2404.5 / 5574.55; married 60k/120k/300k = 2378 / 4809 / 11484.65.
  Two-tier: floor 3000(s)/6000(m), eff first-rate 110/3000, excess 0.05, credit 0.
- **ID** `id_income_tax_before_refundable_credits` (id_income_tax nets refundable
  grocery credit): 475.94/2065.94/6835.94; 951.88/4131.88/13671.88.
  Flat 0.053 over threshold 4920(s)/9840(m).
- **KY** `ky_income_tax_before_refundable_credits`: 932.96/1982.96/5132.96;
  1982.96/4082.96/10382.96. Flat 0.035, std ded 3344.

### Recipe (per composable state)

rulespec-us PR: author `us-XX/policies/income_tax/pilot_liability_pipeline.{yaml,test.yaml}`
(mirror us-oh) → `axiom-encode test <test.yaml> --axiom-rules-engine-path
~/TheAxiomFoundation/axiom-rules-engine` → `axiom-encode sign-applied-files --repo .
--base-ref origin/main --manual-exception composition` → `python tests/generate_reverse_index.py`
→ `axiom-encode oracle-coverage-pending sync --root <ws> --repo rulespec-us` (bump
ceiling +3/state) → commit + PR + auto-merge.

axiom-oracles PR (merge ONE at a time, rebase first): add state to
`scripts/generate_state_income_tax_liability.py` (`_TAXSIM_STATE`,`_PE_VAR`,`_TOL`)
→ run it → author `comparisons/XX-income-tax-liability.yaml` + `dispositions/XX-…yaml`
+ separated `concept_mappings.yaml` block + `affected_map.json` → regen
`scripts/generate_conformance_universe.py --all`, `…_compositions.py --all`,
`conformance_scoreboard.py` → add to `tests/test_conformance.py`.

### Status
- [x] **AL** — pipeline rus#773 (armed); oracle **or#254 MERGED** (us-pe covered 32→35). 6/6 PE-exact.
- [x] **ID** — pipeline rus#773 (armed); oracle or#254 MERGED. 6/6 PE-exact.
- [x] **KY** — pipeline rus#773 (armed); oracle or#254 MERGED. 6/6 PE-exact.
- [ ] MD  [ ] DE  [ ] ME  [ ] MN  [ ] CT — remaining composable; calibration data below.

### Remaining-state calibration (PE 2026 `_before_refundable/credits`, from calibrate run)

Multi-bracket (need per-case bracket floor + cumulative base + marginal, like OH):
- **DE** `de_income_tax_before_refundable_credits` (fixed brackets, no indexation):
  single 30k/60k/150k = 988.125 / 2653.125 / 8559.0; married = 2362.75 / 6254.5 / 18134.5.
  taxable = 26750/56750/146750 (s), 53500/113500/293500 (m). Brackets 0/2.2/3.9/4.8/5.2/5.55/6.6%.
- **MD** `md_income_tax_before_refundable_credits` (state only; county tax is a separate PE var):
  single = 1059 / 2484 / 7039.5; married = 2168.125 / 5018.125 / 14695.75.
  taxable = 23400/53400/145800 (s), 46750/106750/293150 (m). Brackets 2/3/4/4.75/5/5.25/5.5/5.75%.
- **ME** `me_income_tax_before_refundable_credits` (indexed — read PE 2026 brackets):
  single = 565.5 / 2428.52 / 9483.72; married = 1131.0 / 4857.05 / 18966.73.
- **MN** `mn_income_tax_before_refundable_credits` (indexed): single = 789.125 / 2560.00 / 8946.08;
  married = 1575.57 / 5376.45 / 18727.88.
- **CT** `ct_income_tax_before_refundable_credits` — HARDEST (3% phase-out + exemption phase-out +
  tax recapture): single = 361.25 / 2317.5 / 8225.0; married = 1494.0 / 5300.0 / 16450.0. Do last.

TAXSIM SOI codes for these: DE=8 MD=21 ME=20 MN=24 CT=7. Same recipe; add to
`_TAXSIM_STATE`/`_PE_VAR`/`_TOL`, author pipeline+test, `axiom-encode test`, sign,
oracle suite. Signing key: `agent-secret get agent/axiom-encode-apply-signing-key`
→ export `AXIOM_ENCODE_APPLY_SIGNING_KEY`. Generator needs UT/VA `.test.yaml` from
`origin/laneb-slice` present locally (untracked) until lane B's rulespec PR lands.
