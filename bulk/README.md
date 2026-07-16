# Bulk encode

A durable queue -> runner -> PR loop for bulk RuleSpec encoding. It encodes
already-ingested provisions with
`axiom-encode encode <citation> --apply`, pre-checks them with the same gate
battery the PR CI runs, and opens one PR per module.

The encoder and the CI gates own correctness. This system is **plumbing**: it
never edits or invents generated values. Its only judgement is *which*
provisions to queue.

## Pieces

| File | Role |
| --- | --- |
| `bulk/worklist.yaml` | The durable queue. One entry per module. Committed. |
| `bulk/compute_matrix.py` | Turns the worklist into the CI job matrix; single source of truth for status selection. |
| `.axiom/workflow-toolchain.toml` | Immutable checkout SHAs used by CI and generation. |
| `bulk/local_drain.py` | Legacy recovery runner. Do not use it for signed apply with the current broker-only encoder. |
| `bulk/applied_artifacts.py` | Validates the module, companion test, and signed manifest written by one encoder apply. |
| `.github/workflows/bulk-encode.yml` | Protected brokered cloud dispatcher for signed generation. |

## Running it

Dispatch from the Actions tab (**Bulk encode -> Run workflow**) or the CLI:

```bash
# Encode the first 8 pending batch-A entries:
gh workflow run bulk-encode.yml -f batch=A -f limit=8 --repo TheAxiomFoundation/rulespec-us

# Encode up to 12 pending entries regardless of batch:
gh workflow run bulk-encode.yml -f limit=12 --repo TheAxiomFoundation/rulespec-us
```

The `schedule` trigger runs weekly and drains any remaining
`pending` entries with no human action. Parallelism is capped at 4
(`max-parallel`) to stay under OpenAI rate limits; a top-level `concurrency`
group serialises whole dispatches so two runs never fight over the same
`bulk/<slug>` branches.

### Review-safe generation

Signed apply runs only in the main-branch `bulk-encode.yml`
workflow. The workflow provisions a root-owned Python runtime and launches the
current encoder through `axiom-encode-apply-signer`; the private key is consumed
by the external signer and never reaches the encoder process. `allow_context`
and `program_scope_sync` metadata travel with each durable queue entry, so a
restarted job reconstructs the same reviewed command without hand edits.

Every generated PR must complete the independent review/fix cycle and current
CI before merge. RuleSpec YAML and companion fixtures are never hand-edited;
findings are fixed in source material, prompts, harnesses, or encoder code and
then regenerated with `encode --apply`.

### Secrets (repo Actions secrets on rulespec-us)

| Secret | Why |
| --- | --- |
| `OPENAI_API_KEY` | Headless `--backend openai` generation. |
| `AXIOM_ENCODE_APPLY_SIGNING_KEY` | Consumed only by the protected external signer. It must match `AXIOM_ENCODE_APPLY_SIGNING_PUBLIC_KEY`; the encoder never receives it. |
| `BULK_ENCODE_TOKEN` | A `repo`+`workflow`-scoped token used to push the branch and open the draft PR. **Required**: PRs opened by the default `GITHUB_TOKEN` do **not** trigger the `pull_request` event, so required validation would never run. This token makes the PR a real event that triggers CI. |

## Workflow

The protected workflow supplies these jobs:

1. **dispatch** — installs PyYAML, fetches all PR states, then runs
   `compute_matrix.py --status pending` (optionally `--batch`, `--limit`) and
   emits the matrix. Entries whose exact `bulk/<slug>` branch already has an
   open or merged PR are excluded before the limit is applied, so a stale
   `pending` status cannot starve later queue entries. Closed, unmerged PRs stay
   eligible for the workflow's reopen/recreate recovery path.
2. **encode** (one leg per module, ≤4 parallel):
   - Checks out the repo into a leaf dir named exactly `rulespec-us` (the
     `--apply` resolver requirement) using `BULK_ENCODE_TOKEN`.
   - Reads `.axiom/workflow-toolchain.toml` and checks out **the pinned** `axiom-encode`,
     `axiom-rules-engine`, and `axiom-corpus`, then builds the engine. Using the
     pinned encoder means generation and the downstream PR CI validate with the
     identical version — no version-skew surprises.
   - Provisions the protected signing supervisor and runs
     `axiom-encode encode <citation> --apply` through the external apply signer.
     `--apply` validates the main
     file, companion test, and direct dependents in a temporary overlay and
     writes nothing on failure (fail-closed), then installs the three artifacts:
     `statutes/**/<sec>.yaml`, `<sec>.test.yaml`, and a signed
     `.axiom/encoding-manifests/**/<sec>.json`.
   - Runs the gate battery in PR-CI order: `guard-generated` (manifest present),
     `validate --skip-reviewers`, `proof-validate`, then the companion `test`.
   - Opens `bulk/<slug>` as a draft with the acceptance criteria, manifest
     summary, and gate output in the PR body. It never enables auto-merge.

The job **never** uses `--admin`, never bypasses a red check, and never merges
directly. The authoritative gate is the repository's required
`validate / validate` check on the PR.

## Statuses

Set in `worklist.yaml`. The runner reads `pending`; humans/follow-ups own the rest.

| Status | Meaning |
| --- | --- |
| `pending` | Queued. The next dispatch may pick it up. |
| `in-progress` | A run is encoding it (transient). |
| `needs-fixtures` | Encoded + applied, but the gpt-5.5 companion fixtures hit the #1060 ceiling. The draft PR remains open for an encoder fix and rerun. |
| `pr-open` | A draft PR exists and is waiting for its review/fix cycle and CI. |
| `merged` | The PR merged to main. Terminal success. |
| `failed` | Encode or a non-fixture gate failed. Needs human triage. Never auto-retried, never merged. |

Statuses are updated by committing to `worklist.yaml` (a reviewable diff), not by
silent CI mutation. `compute_matrix.py --set-status <citation> <status>` is a
local convenience.

## The fixture-split follow-up loop

`--apply` succeeds when the module compiles, validates, and its proof tree
checks. The **companion test fixtures** are a separate quality tier: the #1060
ceiling means gpt-5.5-authored fixtures sometimes fail. When that happens the
runner marks the module `needs-fixtures` and still opens a draft PR so the
encoded module and failure are reviewable.

A follow-up pass fixes the encoder prompt, harness, source material, or other
root cause and reruns `encode --apply`; generated fixtures are never hand-edited
or back-filled to make a test pass. Once the regenerated artifacts pass review
and CI, the PR can merge. Update the worklist entry to `pr-open`, then `merged`.

## Failure taxonomy

| Symptom | Class | Action |
| --- | --- | --- |
| `Generated RuleSpec failed CI validation` at apply | apply-blocked | Read `*.repair.json` under the run's `encode-out`; usually a bad generated formula or unresolved import. Re-encode (a new run), do not hand-edit. |
| `points to a RuleSpec file that could not be resolved: rulespec-us-<state>/...` | resolver/layout | The checkout leaf dir was not `rulespec-us`, or a sibling checkout was missing. The workflow guards the leaf-dir name; check the sibling symlink step. |
| companion test red only | fixtures (#1060) | `needs-fixtures`; fix the encoder or its inputs and re-encode. |
| self-import / same-section subsection import error | encode#1058 | The section is too cross-reference-heavy for a clean atomic encode. Drop it from the worklist or split the citation to the self-contained fragment. |
| `oracle coverage ... unmapped` on the PR | oracle mapping | The output needs a PolicyEngine oracle mapping entry (`axiom-encode classify`). Out of scope for the encode job; handle as a mapping follow-up. |
| 429 from OpenAI | rate limit | Lower `limit`/`max-parallel` or re-dispatch later. The concurrency group prevents overlapping runs. |

## Extending the worklist

Append entries to `bulk/worklist.yaml` in the existing shape. `citation` is the
corpus citation path the encoder resolves (`<jurisdiction>/statute/<path>`).
Pick self-contained rate/credit/deduction/exemption sections; **skip**
cross-reference-heavy ones (encode#1058) and any known gate-held sections.

To find candidates mechanically, enumerate un-encoded provisions from the public
corpus view and cross-reference the encoded YAML on main:

```bash
# Section-level provisions for a family, minus what is already encoded on main.
# (corpus.current_provisions is the same view the encoder resolves against;
#  has_rulespec in that view can be stale post-merge, so check the YAML tree.)
python - <<'PY'
import urllib.request, urllib.parse, json
from pathlib import Path
BASE="https://swocpijqqahhuwtuahwc.supabase.co"
# anon key is compiled into axiom-encode (validator_pipeline.DEFAULT_AXIOM_SUPABASE_ANON_KEY)
from axiom_encode.harness import validator_pipeline as v
KEY=v.DEFAULT_AXIOM_SUPABASE_ANON_KEY
def q(params):
    p=urllib.parse.urlencode(params)
    r=urllib.request.Request(f"{BASE}/rest/v1/current_provisions?{p}",
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}","Accept-Profile":"corpus"})
    with urllib.request.urlopen(r,timeout=60) as resp: return json.loads(resp.read())
# Range-scan a family (prefix .. prefix+one) at the family's section level.
rows=q({"select":"citation_path,heading,body","level":"eq.3",
        "citation_path":"gte.us-ma/statute/62/","and":"(citation_path.lt.us-ma/statute/620)",
        "order":"citation_path","limit":"800"})
print(len(rows), "section provisions")
PY
```

Then vet each candidate's body: low external-`Section` reference count, a
concrete rate/credit/deduction, non-empty substantive text. That is exactly how
the pilot 20 were chosen.

## Generalising beyond rulespec-us

The dispatcher currently lives in `rulespec-us` because the queue, corpus
resolution, and apply target are US-specific. The reusable *validation* half
already lives org-wide in
`TheAxiomFoundation/.github/.github/workflows/validate-rulespec.yml`. If a second
country adopts bulk encoding, lift `bulk-encode.yml` into the org `.github`
repo as a `workflow_call` reusable workflow parameterised by repo + worklist
path, and keep a thin per-repo `bulk/worklist.yaml` + caller. The gate battery,
toolchain-pin resolution, and draft-PR logic are already repo-agnostic
except for the hard-coded `rulespec-us` leaf-dir guard, which would become an
input.
