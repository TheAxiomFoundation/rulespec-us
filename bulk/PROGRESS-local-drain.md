# Local bulk-encode drain — progress

Draining `bulk/worklist.yaml` on the operator's machine with the local Codex CLI
(ChatGPT subscription, `gpt-5.5`) instead of the cloud `bulk-encode.yml`
dispatcher. One PR per module, auto-merge on green — identical to the cloud path.
Runner: [`bulk/local_drain.py`](./local_drain.py).

## Why this PR exists (repo-side integration of the oracle-coverage pending lane)

Every new-state bulk PR (rulespec-us #614-616, #619-636, …) was failing the
required `validate / validate` check on the changed-file PolicyEngine
oracle-coverage gate: the module's executable outputs are `unmapped` and nothing
declared them. `axiom-encode oracle-coverage-pending sync` writes
`oracle-coverage-pending.yaml`, which the coverage classifier (axiom-encode
`main`, the `oracle-coverage-axiom-encode-ref` default) reclassifies from
`unmapped` to `pending_classification`, clearing the gate. But the tool side
shipped without the repo side:

1. **`tests/test_repository_layout.py`** rejected `oracle-coverage-pending.yaml`
   as a stray root YAML → every shard's whole-repo layout gate failed. Fixed
   here by allowlisting the file.
2. **`.github/workflows/bulk-encode.yml`** never ran the sync, so the dispatcher
   kept opening PRs that fail the gate. Fixed here by installing the
   axiom-encode `main` classifier in an isolated venv and syncing the pending
   lane after `--apply`, staging the declaration into the module commit.

With both landed on `main`, new-state modules self-declare and merge cleanly.

## Toolchain (non-obvious, load-bearing)

- **Generation** uses the **toolchain-pinned** encoder (`.axiom/toolchain.toml`,
  `axiom_encode_version` = 0.2.1184). The required `validate` check validates
  with that same pin; generating with anything newer risks schema/manifest skew.
- **Coverage declaration** uses **axiom-encode `main` (≥0.2.1190)** — the pinned
  1184 encoder has no `oracle-coverage-pending` subcommand, and `main` is what
  CI's coverage classifier runs.

Operator workspace (`_bulk_drain/`, built once, not committed): pinned
axiom-encode venv (`.venv`), main classifier venv (`.venv-cov`), pinned engine
(`cargo build`), pinned corpus, per-entry worktrees whose leaf dir is exactly
`rulespec-us` (the `--apply` resolver requirement). `python bulk/local_drain.py
doctor` verifies all of it.

## Status

- Authoritative queue (origin/main): **173 pending**, ~27 open bulk PRs, 3 merged.
- **Unstick mechanism proven** on #614 (us-oh/5747.02): sync flips its 10 outputs
  `unmapped → pending_classification`; the `validate / validate (us-oh)` shard
  goes green. It surfaced the two repo-side gaps fixed in this PR.
- **Part B generation proven** end-to-end on us-il/statute/35/5/705: local Codex
  `gpt-5.5` generated a valid module in ~45s (`compile=yes ci=yes`), `--apply`
  installed module+test+signed manifest, and the full gate battery passed
  (guard-generated, validate, proof-validate, companion test = 4 cases). Its
  outputs are already oracle-mapped, so sync is a no-op and no pending file is
  added (mapped modules stay shard-scoped).
- Runner `doctor` green: pinned encoder 1184, classifier ≥1190, engine, corpus,
  signing key, codex CLI all resolve.

### Open bulk PRs to drain (as of this writing)

- **New-state, fail the coverage gate → need sync** (`unstick`): #614-616 (oh),
  #619-620 (or), #621 (ri), #623/#627 (va), #624-626 (ut), #629-633 (wv),
  #634-636 (hi), #638 (az).
- **Mapped, pass validate but stale → need up-to-date** (`unstick`, sync no-op):
  #589-594 (il), #622 (sc), #637 (az).

Branch protection is `strict` (up-to-date required) and the pending lane is one
repo-root file, so unstick PRs merge **sequentially** (`unstick --wait`, rebuild
each on the newly-advanced main). This file is rewritten by `local_drain.py
drain` each chunk with per-entry results and the paused/limit state.
