# Local drain progress — FED1+SS1 saturation, COMPLETE (2026-07-09, ~16:00 UTC)

## Headline
US FED1 + SS1 fully drained and **merged** (4 batch PRs). Root-caused and fixed
a runner bug that was falsely benching good federal modules; verified end-to-end
(batch #779 landed all 6 federal modules, 0 dropped). UK pre-batch orphans
consolidated into one batch and the red singles closed. UK/BE have no new
pending work. Accounts healthy throughout (0 limit signals).

## Runner fixes committed (branch `bulk-local-drain-runner`)
1. **`0409b1e7` — oracle-coverage gate encoder (the blocker).**
   `batch_oracle_coverage` ran with `GATE_AE` = the pinned **0.2.1184** encoder
   for rulespec-us. That encoder predates the pending lane (no
   `oracle-coverage-pending` subcommand) and does NOT apply
   `oracle-coverage-pending.yaml`, so every declared-pending output read
   `unmapped` and good `us/` federal + `us-mi` modules were benched. CI runs the
   oracle-coverage workflow step with axiom-encode **main (>=1190)**, which owns
   the pending lane, so those modules pass in CI. Fixed the gate to use `COV_AE`
   (.venv-cov, 1190). Proof: identical content, COV_AE reports the 578
   declarations `pending_classification`; the 1184 pin reports them `unmapped`
   (0 applied). UK immune (its GATE_AE is already 1190); BE skips the gate.
2. **`d9682c08` — opt-in `--apply-target-only`** (`DRAIN_APPLY_TARGET_ONLY=1`)
   + **`find_open_batch_branch` prefix-collision fix** (group `us` no longer
   matches `us-mi`/`us-nc` branches).
3. **`de5e5d1f` — `DRAIN_IGNORE_HANDLED=1`** to re-drain a slug whose only PR is
   closed (used to re-encode the closed UK singles into a batch).

## US outcome — all merged
- **FED1 (8):** MERGED via **#779** — `26/164`, `26/221`, `26/219/b`,
  `26/219/g`, `26/223/b`, `7 CFR 247.9(b)`. **Fail-closed (benched):**
  `26/1402/a`, `26/1402/b` — SECA net-earnings fragment splits, dense
  dependency web; failed 3× on both closure- and target-apply. Correct outcome.
- **SS1 (14 MI/NC):** MERGED — 9 us-mi via **#775** (206.30/8, 206.51/6,
  206.51/10) + **#780** (206.30/2,3,7,10,11,12); 3 us-nc via **#776**
  (105-153.5/a,a1,b). **Benched:** 206.30/9, 206.51/1 (pre-existing hard).
- #599 (7 CFR 273.11(c), unrelated orphan) self-healed — merged 15:26Z.

## UK / BE (brief item 2)
- No new pending to drain — UK 24 / BE 23 "pending" are already-merged
  uk#129 / BE-batch modules whose worklist status was never flipped.
- **UK orphan cleanup:** 4 pre-batch singles (#120/121/122/126:
  ukpga/1992/4/171ZA, uksi/2006/213/70+71, ukpga/2003/1/681G) were red on
  current main (stale schema, pre-1190; not carried by uk#129). Closed the
  singles, re-encoded fresh (4 green), consolidated into batch **#130**
  (open, CI running, auto-merge armed).

## Accounts (3 distinct chatgpt subs; .codex-4 EXCLUDED — dup account_id of .codex)
DRAIN_CODEX_HOMES = `~/.codex:~/.codex-2:~/.codex-3`. Pool 3×8=24. Across all
drain chunks (US + UK): **0 limit signals**, avg gen ~35–185s, all three healthy.

## Open / follow-up
- **#130 (UK batch, 4 modules):** open, auto-merge armed — merges when CI passes
  (no siblings).
- Worklist status flips for the drained FED1/SS1/UK entries are local-only; a
  `flip` PR can reflect them on main later (cosmetic).
- CA/NZ skipped per brief. BE known fuel stays benched.
