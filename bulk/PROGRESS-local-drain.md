# Local drain progress — generation-saturation session (2026-07-08 ~17:25 UTC)

## Engine shipped
`bulk/local_drain.py` extended + verified + durable (draft PR **rus#764**,
branch `bulk-drain-multi-account`, off origin/main):

- **Multi-account CODEX_HOME rotation** — `AccountPool` fans worker slots across
  every authenticated ChatGPT-sub (`~/.codex[-2..4]`, `DRAIN_CODEX_HOMES`).
  Admits `auth_mode=chatgpt` only — **api-key auth refused, never bills the API.**
  Per-account backoff on a limit signal (only that account pauses); **hot-add**
  the moment a new `auth.json` lands. Total slots = per_account × live, cap 24.
- **Merge-train batch PRs** — generation decoupled from PR-ing: encode+gate in an
  isolated worktree → stage artifacts (durable) → consolidate ~15-25 disjoint
  modules per batch (one `oracle-coverage-pending sync`, one reverse-index regen,
  one validation, auto-merge). Fail-closed: a red module is skipped, never
  batched. Held behind an open consolidation train (`DRAIN_HOLD_UNTIL_PR`).
- **Repo-parametric** — `DRAIN_CHECKOUT`/git-remote derivation drains
  rulespec-us / -uk / -be from one durable script copy.
- Verified: py_compile (3.14), `doctor`, quota-free `AccountPool` self-test
  (discovery, per-account knee, backoff, hot-add, all-backed-off) — all pass.

## Concurrency probe — single sub
| per-account | encodes | result | avg gen (s) | limit signals | memory |
| --- | --- | --- | --- | --- | --- |
| 1 (canary) | 1 (BE) | green | 111.9 | 0 | flat |
| 8 (UK) | 10 | 8 green / 2 fail-closed | 70.0 | 0 | flat (128 GB) |
| 8 (BE) | 2 | 2 green | 138.5 | 0 | flat |

Prior runs (same sub): c=3/4/5 all `paused=False` (no limits).
**Knee ≥ 8 on one sub — no rate-limit ceiling or latency degradation observed;
memory negligible at 8-wide.** Recommended steady-state per-account = 8 (headroom
to 10-12). With N live accounts: total = min(24, 8·N) → 3 accounts saturate the
24 cap; 4th is backoff resilience. Raise `DRAIN_MAX_TOTAL` after the plan upgrade.

## Drained this session (feeder lanes; not held by rus#763)
- **UK batch PR rus-uk#129** — 8 modules, one sync (78 declared, +33), auto-merge
  on, `validate/shards` running.
- **BE batch PR rus-be#109** — 3 modules, one sync (0 declared), auto-merge on,
  `validate/shards` running.
- 11 modules generated green, 2 fail-closed (UK 80C, uk 2003/1/681C), 0 deferred.
- Staging idempotent: UK 8/8, BE 3/3 marked batched (no re-generation).

## rulespec-us
No fresh work to generate: the 173 "pending" are already drained into open
`bulk/<slug>` PRs (132 in train **rus#763** + others) or known-failed (36).
US batches **held** behind #763 (OPEN/BLOCKED). US staging empty → nothing to
flush. New US work arrives from the producer lanes; `assemble --force` (or the
default gate, once #763 merges) opens US batches then.

## Accounts
- `.codex` (max@maxghenis.com) — LIVE (chatgpt).
- `.codex-2/-3/-4` — awaiting Max's out-of-band login; hot-add is armed.

## Next
- Accounts 2-4 online → total jumps to min(24, 8·N) automatically.
- rus#763 merges → `local_drain.py assemble --force` flushes any US staging; new
  US batches follow the train convention.
- Producers append US/UK/BE work → `drain --per-account 8` per lane, auto-batches.
