# Local drain progress — generation-saturation session (2026-07-09, ~02:20 UTC)

## Engine (durable: draft PR rus#764, branch `bulk-drain-multi-account`)
Multi-account CODEX_HOME rotation (chatgpt-only, per-account backoff, hot-add) +
merge-train batch PRs + per-repo pin venvs (us `.venv`/1184, be `.venv-be`/1188,
uk `.venv-cov`/1190) + canonical repo-root manifest capture. **CI-faithful gate
battery** now runs everything CI does, per repo:
1. per-module `validate` (pin encoder),
2. repo `tests/` pytest (`run-pytest`; catches proof-atom quality + the
   oracle-coverage-pending ratchet), and
3. **PolicyEngine `oracle-coverage`** (workflow-only step — flags `unmapped`
   undeclared or `comparable`-but-untested; skipped for rulespec-be/EUROMOD).
Any module a gate flags is fail-closed and dropped; batches are green by
construction. Knee ≥ 8/sub, 0 limit signals.

## Merged this session
- **rus-be#109, rus-be#110, rus#763 (merge train, rebased onto main)** — all
  MERGED. US batch hold lifted.

## uk#129 — diagnosed + fixed (was red)
The red was NOT the "unmapped" oracle-cache issue first suspected. Reproduced
locally with the exact CI oracles SHA (980d2ec5, == my cov venv): the pending
ratchet **passes**. The real failure was the workflow-only PolicyEngine
`oracle-coverage` step: `uk:regulations/uksi/2004/692/schedule/1#colour_tv_
licence_general_form_issue_fee` is **comparable but not covered by companion
tests**. My local gate ran the repo pytest but not that workflow step → it
slipped. Added `batch_oracle_coverage` (mirrors CI exactly); re-drove #129 → the
module fail-closed, **13-module clean batch** (validate + pytest + oracle-coverage
all green locally), CI re-running, auto-merge armed.

## Queue state
- **uk#129** — 13 modules, CI running, auto-merge armed.
- **rus#766 / rus#773** — were BEHIND after the train merged; **update-branch
  nudged** (auto-merge armed, CI recomputing).
- **rus#767** — owned by a background rebase task (not touched).
- Fuel: rus-be#108 / rus-uk#128 merged and drained (BE 6 green / 11 encode-fail
  benched; UK 6 green, consolidated into #129). FED1+SS1 fuel is armed to drain
  **once #766/#767 land** (they add the worklist entries).
- CA deprioritized; NZ blocked-on-red-main.

## Accounts
`.codex` LIVE (chatgpt). `.codex-2/-3/-4` not yet logged in — hot-add armed;
throughput scales to min(24, 8·N) automatically.

## Known
- BE batch-C fuel: 11/17 encode/apply rc=1 (benched in drain_failed.json) — worth
  checking corpus coverage for those `arrete`/`loi` articles vs a toolchain issue.
- `DRAIN_HOLD_UNTIL_PR=763` should be cleared/retargeted for the next US train
  (763 merged; hold now auto-false since it's not OPEN).
