# Local drain progress — generation-saturation session (2026-07-09, ~02:30 UTC)

## Engine (durable: draft PR rus#764, branch `bulk-drain-multi-account`)
Multi-account CODEX_HOME rotation (chatgpt-only, per-account backoff, hot-add) +
merge-train batch PRs + per-repo pin venvs (us `.venv`/1184, be `.venv-be`/1188,
uk `.venv-cov`/1190) + canonical repo-root manifest capture. **Full CI-faithful
gate battery** per repo — every module fail-closes locally on anything CI checks:
1. per-module `validate` (pin encoder),
2. repo `tests/` pytest (`run-pytest` — proof-atom quality + oracle-coverage
   pending ratchet), and
3. **PolicyEngine `oracle-coverage`** workflow step (unmapped-undeclared or
   comparable-but-untested; skipped for rulespec-be/EUROMOD).
Knee ≥ 8/sub, 0 limit signals.

## Merged
rus-be#109, rus-be#110, rus#763 (merge train, rebased onto main), **rus#766** —
all MERGED. US batch hold lifted.

## uk#129 — resolved (three layered reds, all diagnosed + fixed)
1. "unmapped" was a red herring — reproduced the pending ratchet locally with
   CI's exact oracles SHA (980d2ec5); it passes.
2. Real red #1: the workflow-only PolicyEngine `oracle-coverage` gate
   (comparable-but-untested output). Added `batch_oracle_coverage` mirroring CI.
3. Real red #2: repeated re-drives left an orphan manifest
   (`.axiom/encoding-manifests/regulations/…/schedule/1.json`, no `uk/` prefix)
   after a dropped module → kingston-upon-thames guard-generated red.
Fixed by a **clean regenerate**: cleared UK staging, re-drained fresh (22 green,
all manifests uniformly `.axiom/encoding-manifests/uk/…`), assembled #129 fresh.
**#129 = 22 modules, 0 dropped, 0 orphans, all local gates green** (validate +
pytest + oracle-coverage); CI running, auto-merge armed.

## Queue
- **uk#129** — 22 modules, CI running, auto-merge armed.
- **rus#766** — MERGED. **rus#767** — rebased current by the background task,
  CI running, auto-merge armed. **rus#773** — update-branch nudged, auto armed.
- **US FED1+SS1 fuel** — armed to drain once #767 lands (adds the worklist
  entries; US hold is lifted). Drain with `DRAIN_CHECKOUT=…/rulespec-us
  local_drain.py drain --per-account 8` then `assemble --flush`.
- CA deprioritized; NZ blocked-on-red-main.

## Accounts
`.codex` LIVE (chatgpt). `.codex-2/-3/-4` not logged in — hot-add armed;
throughput scales to min(24, 8·N).

## Known
- BE batch-C fuel: 11/17 encode/apply rc=1 (benched) — check corpus coverage for
  those `arrete`/`loi` articles.
- `DRAIN_HOLD_UNTIL_PR=763` now auto-false (763 merged); retarget for the next US
  train when one opens.
