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
| `bulk/roots_for.py` | Maps an applied module path to `guard-generated --roots`. |
| `bulk/local_drain.py` | Former local runner; its local apply-signing credential path is retired. |
| `bulk/applied_artifacts.py` | Validates the module, companion test, and signed manifest written by one encoder apply. |
| `.github/workflows/bulk-encode.yml` | Fail-closed placeholder while protected cloud activation is reviewed. |

## Running it

The cloud bulk workflow is disabled during the protected provenance migration.
Signed reencoding now goes through axiom-encode's
[`targeted-signed-reencode` workflow](https://github.com/TheAxiomFoundation/axiom-encode/actions/workflows/targeted-signed-reencode.yml),
which signs only on `main` in a protected environment.

### Retired local drain

The local apply-signing credential path in `bulk/local_drain.py` was retired on
2026-10-14. It raises an explicit retirement error before consulting the
environment, `agent-secret`, or macOS Keychain. Local drains cannot sign new
applies; use the central workflow above. RuleSpec is still produced only by
the supervised encoder with `--backend codex --apply`.

The former local drain opened generated branches as drafts with auto-merge
disabled. Each PR must complete the independent review/fix cycle and current CI
before a human or agent marks it ready and merges it. RuleSpec YAML and companion
fixtures are never hand-edited; findings are fixed in source material, prompts,
harnesses, or encoder code and then regenerated with `encode --apply`.

### Signing credentials

Do not provision `AXIOM_ENCODE_APPLY_SIGNING_KEY` in this repository, local
environments, agent keychains, or macOS Keychain. Signing is owned by the
central workflow's protected environment. Encoder agents use subscription
Codex auth.

| Secret | Why |
| --- | --- |
| `BULK_ENCODE_TOKEN` | A `repo`+`workflow`-scoped token used to push the branch and open the PR. **Required**: PRs opened by the default `GITHUB_TOKEN` do **not** trigger the `pull_request` event, so the required `validate / validate` check would never run and auto-merge would hang forever. This token makes the PR a real event that triggers CI. |

## Local runner history

Before retirement, the local runner verified the pinned encoder, engine, and
corpus checkouts, ran `encode --apply` and the gate battery, and opened a draft
PR with auto-merge disabled. Independent review and required CI remain
mandatory for centrally signed changes.

## Statuses

Set in `worklist.yaml`. The runner reads `pending`; humans/follow-ups own the rest.

| Status | Meaning |
| --- | --- |
| `pending` | Queued. The next dispatch may pick it up. |
| `in-progress` | A run is encoding it (transient). |
| `needs-fixtures` | Encoded + applied, but the gpt-5.5 companion fixtures hit the #1060 ceiling. The PR opens; auto-merge holds on the red required check until fixtures land. |
| `pr-open` | A PR exists and is set to auto-merge on green. |
| `merged` | The PR merged to main. Terminal success. |
| `failed` | Encode or a non-fixture gate failed. Needs human triage. Never auto-retried, never merged. |

Statuses are updated by committing to `worklist.yaml` (a reviewable diff), not by
silent CI mutation. `compute_matrix.py --set-status <citation> <status>` is a
local convenience.

## The fixture-split follow-up loop

`--apply` succeeds when the module compiles, validates, and its proof tree
checks. The **companion test fixtures** are a separate quality tier: the #1060
ceiling means gpt-5.5-authored fixtures sometimes fail. When that happens the
runner marks the module `needs-fixtures` and still opens the PR, so the encoded
module is reviewable and its auto-merge simply waits.

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
toolchain-pin resolution, and PR/auto-merge logic are already repo-agnostic
except for the hard-coded `rulespec-us` leaf-dir guard, which would become an
input.
