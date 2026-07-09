# Local drain progress — generation-saturation session (2026-07-08, ~21:35 UTC)

## Engine (durable: draft PR rus#764, branch `bulk-drain-multi-account`)
- **Multi-account CODEX_HOME rotation** — `AccountPool` fans slots across every
  authed ChatGPT sub (`~/.codex[-2..4]`); chatgpt-only (api-key refused → never
  bills the API); per-account backoff; hot-add on new `auth.json`. Total
  `min(24, per_account × live)`.
- **Merge-train batch PRs** — generate+gate in isolation → stage (durable) →
  consolidate; `--update-existing` rebuilds an open batch PR in place. Held
  behind an open consolidation train (`DRAIN_HOLD_UNTIL_PR`).
- **Per-repo pin venvs** (the BE/UK red fix) — CI installs the toolchain-pinned
  encoder + runs `tests/` pytest with it, so gen + gate + batch pytest all use
  the pin venv: us→`.venv` (1184), be→`.venv-be` (1188, built this session),
  uk→`.venv-cov` (1190). The shared 1184 venv predates the #1082 manifest
  relocation, so it wrote manifests to `<juris>/.axiom` (layout gate rejects
  `.json` there) instead of repo-root `.axiom/encoding-manifests/<juris>/` →
  "Repository layout does not match" red. generate_module now captures the
  canonical repo-root manifest from git status (relocates a co-located one if an
  older encoder made it).
- **CI-faithful gate** — `assemble` runs the repo `tests/` pytest with the pin
  venv (CI's `run-pytest`) and fail-closes any module named in a failing
  assertion (e.g. `proof_atoms_missing_formula_value`), so batches are green by
  construction. Repo-parametric via `DRAIN_CHECKOUT`.
- Verified: py_compile, quota-free AccountPool self-test, per-repo doctor.

## Concurrency knee (single sub)
c=1 → 112s; **c=8 → 70s, 0 limit signals, flat memory (128 GB)**; prior c≤5 also
0 limits. **Knee ≥ 8 per sub.** Steady-state per-account 8; total `min(24, 8·N)`.

## Results this session
- **BE batch rus-be#109 — MERGED** (2 modules; `article/40` fail-closed on a real
  proof-atom quality reject, benched).
- **BE fuel batch rus-be#110 — MERGED** (3 modules; 3 pytest-dropped).
- **US merge train rus#763 — REBASED onto main + MERGED.** It went DIRTY when
  rus#769 (Ohio) landed; rebased by re-applying the 392 clean artifacts onto
  fresh main and regenerating the 2 tool files (reverse index +
  oracle-coverage-pending, 523 declared) — Ohio preserved. This lifts the US
  batch hold.
- **UK batch rus-uk#129 — OPEN, auto-merge armed** (14 modules = 8 + 6 fuel,
  canonical manifests, pending 83 declared; CI running on ~1-wide runners).
- Manifests confirmed at repo-root `.axiom/encoding-manifests/<juris>/…` on all
  rebuilt batches.
- Fuel drained after rus-be#108 / rus-uk#128 merged: BE 6 green / 11 encode-fail
  (benched, batch-C articles), UK 6 green.

## Open / next (armed, not vigiling — runners ~1-wide)
- UK #129 → auto-merges on green.
- US train hold lifted → US fuel from rus#766/#767 batches once those merge;
  `DRAIN_HOLD_UNTIL_PR` should be cleared/retargeted for the next US train.
- **rus#766/#767** both still OPEN → the second to merge needs an update-branch
  nudge (both append at worklist EOF); armed for when the first merges.
- CA deprioritized (re-encode fuel, expected holds); NZ blocked on red main.
- Accounts `.codex-2/-3/-4` not yet logged in — hot-add armed; throughput scales
  to `min(24, 8·N)` automatically.

## Accounts
`.codex` (max@maxghenis.com) LIVE (chatgpt). 2-4 pending Max login.
