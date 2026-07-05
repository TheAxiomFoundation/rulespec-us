# Probe B1 lockfiles — hermetic CO SNAP

These lockfiles pin every input that determines the RuleSpec output for one
program slice (Colorado SNAP), so that regeneration is reproducible and any
diff against the live module can be attributed to a *changed input* rather than
non-determinism. They implement the extended lockfile key from
`axiom-rebuild-plan-2026-07-02.md` §4-B1 (the architecture-review fix that adds
`registry_version` and `oracle_mapping_version` to the original six-key design).

**This is a measurement probe, not a migration.** Nothing here replaces live
content. Regenerated output lives under `.axiom/probes/b1/`.

## One file per module

`<module_path with / → __, .yaml stripped>.lock.json`, plus:
- `_index.json` — the 25-module manifest (n, module_path, lockfile, source_sha, citation, oracle, class).
- `README.md` — this file.

## Lockfile key (`axiom/probe-b1-lockfile/v1`)

| Field | Meaning |
|---|---|
| `module_path` | Live RuleSpec module this lockfile pins (relative to rulespec-us root). |
| `source_sha` / `source_sha_kind` | Git blob SHA-1 of the live module at probe time — the "reviewed content" the regeneration is diffed against. |
| `corpus_citation_path` | The corpus source unit the encoder reads. Resolves against the pinned r0 corpus. |
| `source_id` | Canonical RuleSpec source identifier for policy-file (guidance-page-backed) modules; null for statute/regulation leaves. |
| `oracle` | Per-module benchmark oracle (`policyengine` or `none`). |
| `policyengine_rule_hint` | Oracle target rule name; null when the benchmark uses no hint. |
| `policyengine_mapping_present` | Whether `oracle_mapping` actually contains a PE edge for the hinted rule — `false` means the PE oracle **cannot discriminate** this module (an oracle blind spot). |
| `selection_class` | `bench` / `bench+chain` / `chain` / `chain-backfill` — why the module is in the probe set. |
| `corpus_release` | r0 release id, corpus git commit `9ee50de`, and the r0 `release_manifest.json` sha256. |
| `prompt_version` | axiom-encode package version + git commit (the harness/prompt assembly). |
| `model` | Configured default (`codex:gpt-5.5`) **and** what actually executed, with the substitution reason. |
| `schema_version` | axiom-rules-engine package version + git commit that compiled/validated the module, plus the `rulespec-module.v1` schema family id. |
| `registry_version` | Concept registry the encode pipeline consumed (content-hashed). |
| `oracle_mapping_version` | `oracles/policyengine/mappings/us.yaml` sha256 + git commit. |
| `populace_artifact` | Pinned populace US H5 (plan §A2 pin) used for the population oracle. |
| `probe_meta` | Probe id, plan reference, rulespec-us branch + base commit. |

## Honest deviations recorded in every lockfile

1. **Model.** The configured default `codex:gpt-5.5` was non-runnable at probe
   time (codex CLI binary missing; `gpt-5.5` absent from the available OpenAI
   key; the `claude` backend 401s from the nested CLI). Regeneration executed on
   `openai:gpt-5.2` — the closest available frontier OpenAI model via the
   Responses API. This changes the "model" key of the hermetic tuple; every
   number in the report is a gpt-5.2 measurement and would need re-running under
   the true default model before any consolidation decision leans on absolute
   token/diff counts.
2. **r0 manifest / registry provenance.** The r0 release manifest (corpus) and
   the 40,991-concept registry (corpus#171) are open PRs, not merged to corpus
   main. The lockfiles pin the r0 corpus *git commit* (which is merged) and the
   *encode-side* concept seed that the pipeline actually consumes, and say so.
3. **Schema export.** The A1 published JSON Schemas are not on the engine HEAD
   used here, so `schema_version` pins the engine package version + git commit
   that did the compile/validate rather than a schema-file hash.

## Regeneration command (per module)

```
AXIOM_POPULACE_US_H5=<pinned h5> AXIOM_CORPUS_REPO=<r0 worktree> \
axiom-encode encode <corpus_citation_path> \
  [--source-id <source_id>] \
  --backend openai --model gpt-5.2 --mode repo-augmented \
  --corpus-path <r0 worktree> \
  --policy-repo-path <rulespec-us b1 worktree> \
  [--policyengine-rule-hint <hint>] \
  --output .axiom/probes/b1/regenerated --no-sync
```
