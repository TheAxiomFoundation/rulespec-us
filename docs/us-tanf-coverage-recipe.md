# US per-state TANF coverage recipe

Reproducible recipe for covering a per-state TANF row in the `us-pe` conformance
universe (Axiom RuleSpec composition validated against a pinned PolicyEngine
`XX_tanf`). Written by the wave-1 scout after proving it end to end. Precise
enough for a wave-2 lane to execute without rediscovery.

Scope covered by this recipe = exactly what PolicyEngine simulates for a state's
TANF: the **payment/grant standard**, **earned-income disregards**, the
**income-eligibility / benefit-deficit** calculation, and the **demographic
gate** (minor or pregnant member). Work requirements, time limits, resource
tests, and immigration proration are PE-side gates that the composed slice
declares `acknowledged_incomplete` and dispositions as bridge artifacts, not
things this recipe encodes.

## Premise corrections (read first — the wave-1 brief was wrong on these)

Verified against the repos on 2026-07-08; do not build the worklist on the
original assumptions:

1. **No `.rac` files.** Every encoded provision is YAML tagged
   `format: rulespec/v1`. "RuleSpec" is the DSL; the extension is `.yaml`.
2. **`rulespec-us-XX` standalone repos mostly do not exist.** Only
   `rulespec-us-co` and `rulespec-us-ny` are separate repos; every other state
   (AL, KS, GA, …) lives inside the monorepo `rulespec-us/us-XX/`. Author there.
3. **Corpus PRs #97/#109/#111 do not exist.** Real TANF corpus PRs: GA #127/#124/#129,
   WA #131, DE #175, ME #183, NY #85, KS SSPP #202. **Colorado has no TANF corpus
   ingest at all** — CO Works was encoded from a dedicated CCR adapter path, not
   the generic ingest.
4. **`axiom-encode` issue #1058 is not a "skip xref-heavy TANF" rule.** It is an
   open bug: the encoder emits a self-import on NY Tax Law §606/§616 (income-tax
   credits). Unrelated to TANF. There is no documented "xref-heavy → skip" policy.
5. **"fixture-split" is not a thing.** The real pattern is the mandatory companion
   test: every `foo.yaml` ships a sibling `foo.test.yaml`.
6. **TANF suites are not Python and not per-case grids.** They are declarative
   `comparisons/<st>-tanf-ecps.yaml` configs run at **ECPS population scale**
   (`population: enhanced-cps`, `sample_size: 0`, filtered by state FIPS). There
   are **zero** TANF entries in `grids/us.yaml`. Population is correct here because
   the populace-us loader already carries every state's household facts — "the
   ECPS bridge already maps the state's variables" is true for all TANF states.
7. **"composition exception" = `manual_exception: composition` / `backend: deterministic`.**
   The AI encoder produces net-new leaf modules; the composed pipeline is a pure
   deterministic assembly and is exempted via that marker, not an encoder run.
8. **PDF `page_windows` (manifest field) and `--source-xml` (XML-statute CLI flag)
   are unrelated.** Do not combine them.

## Candidate universe

PolicyEngine simulates a `XX_tanf` variable for ~29 states + DC. Wave-1 proved
the pipeline on the ripe subset (corpus already ingested). Covered before wave-1:
AZ, CA, CO, KS, MN, NY, WA. Uncovered **with corpus already ingested** (ripe):
**AL, GA, DE, ME, HI**. Uncovered, no corpus yet (need the ingest step): DC, IL,
IN (in progress — has mapping entries, avoid), MO, MS, MT, NC, ND, NV, OK, OR,
PA, SC, SD, TX, VA. Everything else PE does not simulate → wave-2 files these as
`in_scope: false` / `suite: null` rows, not encodings.

Pick order = PE module simplicity (fewer variable+parameter files = less to
compose/disposition). Measured file counts (`variables`+`parameters` under the
state `tanf/` tree): AL 6/3 (simplest), MS 6/7, ND 9/7, NC 9/8, SD 10/7, GA 10/9,
HI 10/9, ME 11/10, SC 11/9 … up to MT 30/18, TX 28/25, IL 26/21 (hard cases).

## One-time infra setup (per machine/lane)

The oracle runner hard-codes canonical `$HOME` checkout locations. A lane must
wire these once:

```bash
# Canonical checkouts (symlink worktrees to these names if you use worktrees)
ln -sfn <your>/axiom-rules-engine   ~/axiom-rules-engine     # Rust engine
ln -sfn <your>/axiom-compose        ~/axiom-compose          # has .venv/bin/axiom-compose
# ~/axiom-oracles must expose programs/: ln -sfn <oracles-checkout>/programs ~/axiom-oracles/programs
# rulespec compose roots (real dir copies, name == rulespec-<prefix>):
scripts/sync_rulespec_roots.sh        # rsyncs ~/rulespec-us/us-XX/ -> ~/.axiom-oracles/roots/rulespec-us-XX/

# Build the Rust engine once (release):
cargo build --manifest-path ~/axiom-rules-engine/Cargo.toml --bin axiom-rules-engine --release
```

Pins that must stay coherent (do not drift):
- Oracle runner PE pins (`scripts/run_comparison.py::_PE_ORACLE_PINS`):
  `policyengine==4.18.9`, `policyengine-us==1.752.2`, `policyengine-core==3.28.0`.
  The runner installs these into a throwaway `uv run --with` env per invocation —
  you do **not** need PE in the oracles venv for a comparison.
- Populace data pin (`axiom_oracles/bridges/population.py::POPULACE_PINS['us']`):
  `populace_us_2024.h5` @ revision `…f0af251…`, sha256-verified, built_with 1.729.0.
  Cached under `~/.cache/huggingface/hub/datasets--policyengine--populace-us`
  (no HF token needed once cached; unauthenticated works, just rate-limited).
- Conformance universe label (`conformance/us-pe.yaml` header): policyengine-us
  1.767.3 — used only to enumerate which PE policies exist to score, can differ
  from the runner pin.

## The pipeline, per state

### Step 1 — Corpus ingest (skip if already ingested)

Signed, verbatim ingest into `axiom-corpus`. One command per source; the
manifest's `source_format` + `extraction:` block is the only thing that changes
between source types.

```bash
cd ~/TheAxiomFoundation/axiom-corpus && uv sync
# Author manifests/us-<st>-tanf-<slug>.yaml (see source-type playbook below), then:
uv run axiom-corpus-ingest extract-official-documents \
  --base data/corpus --version <YYYY-MM-DD>-<st>-tanf --manifest manifests/us-<st>-tanf-<slug>.yaml
AXIOM_CORPUS_INGEST_PRIVATE_KEY=… uv run axiom-corpus-ingest sign-ingest-manifest \
  --jurisdiction us-<st> --document-class <regulation|manual|policy> \
  --version <YYYY-MM-DD>-<st>-tanf \
  --command "<the extract command above>" \
  --reasoning-log .axiom/reasoning-logs/us-<st>-<class>-<version>.md
AXIOM_CORPUS_INGEST_PUBLIC_KEY=… uv run axiom-corpus-ingest guard-ingested --base-ref origin/main --head-ref HEAD --json
```

Writes `data/corpus/{sources,inventory,provisions,coverage}/us-<st>/…` +
`.axiom/ingest-manifests/us-<st>/<class>/<version>.json` (Ed25519-signed over
canonical JSON, per-file sha256). CI (`guard-ingested`) rejects any changed file
under the protected prefixes without a matching signed manifest, and rejects
agent-written digests under `official-documents/` (that is what "verbatim" means
operationally). Coverage must be `complete: true`
(`matched_count == source_count == provision_count`) before signing.

Requires `AXIOM_CORPUS_INGEST_PRIVATE_KEY` (Ed25519 signing) + network to the
source. Do **not** publish to R2/Supabase unless explicitly asked.

### Step 2 — Encode leaf modules (skip if already encoded)

Net-new statutory encoding of the payment-standard and disregard/computation
provisions. This is the only AI step.

```bash
cd ~/TheAxiomFoundation/axiom-encode
AXIOM_ENCODE_APPLY_SIGNING_KEY=… uv run axiom-encode encode \
  "us-<st>/<class>/<citation-path>/<module>" \
  --backend codex --model gpt-5.5 --mode repo-augmented \
  --output /tmp/axiom-encode-<st>-tanf --apply
```

Defaults are `--backend codex --model gpt-5.5 --mode repo-augmented`. Needs codex
auth (`~/.codex/auth.json` via `codex login`, or `$OPENAI_API_KEY`) and
`AXIOM_ENCODE_APPLY_SIGNING_KEY`. `--apply` validates main + companion test in a
temp overlay, copies both into `rulespec-us/us-<st>/…`, and writes a signed
apply manifest (`.axiom/encoding-manifests/…json`, HMAC-SHA256,
`"backend":"codex"`). CI `axiom-encode guard-generated` rejects any changed
RuleSpec YAML under `statutes/`/`regulations/`/`policies/` without a matching
signed manifest. Target output shape (real, from NY): separate
`standard-of-need-and-monthly-grant.yaml` (payment standard) and
`financial-eligibility-and-income-disregards.yaml` (disregards), each a list of
`kind: parameter` / `kind: derived` rules with `metadata.proof.atoms` grounding
every value to a corpus excerpt.

### Step 3 — Compose the benefit pipeline (deterministic, no AI)

Author `programs/us-<st>/tanf/fy-2026.yaml` (in `axiom-oracles/programs/` — the
runner reads `$HOME/axiom-oracles/programs/…`; mirror into `rulespec-us/programs/`).
Shape: `program`, `period: 2026-01`, `outputs`, `acknowledged_incomplete`,
`scope.state` (the leaf module citations to import), `transformations`. The
transformations bind the leaf free-inputs and add the demographic gate + the
annualized output. Real wave-1 Alabama spec:
`programs/us-al/tanf/fy-2026.yaml` (this recipe's worked example). Verify it
composes and compiles:

```bash
export AXIOM_RULESPEC_REPO_ROOTS=~/.axiom-oracles/roots/rulespec-us-<st>
~/axiom-compose/.venv/bin/axiom-compose programs/us-<st>/tanf/fy-2026.yaml \
  -o /tmp/<st>-tanf-composed.yaml --rulespec-root $AXIOM_RULESPEC_REPO_ROOTS
~/axiom-rules-engine/target/release/axiom-rules-engine compile \
  --program /tmp/<st>-tanf-composed.yaml --output /tmp/<st>-tanf-compiled.json
#   ^ compile resolves the composition's `imports:` via AXIOM_RULESPEC_REPO_ROOTS.
```

`axiom-compose` is a pure function (spec + corpus roots → runnable RuleSpec, no
LLM). Because this is a hand-authored composition, attest it with
`axiom-encode sign-applied-files --repo rulespec-us --manual-exception composition`.

### Step 4 — Oracle suite vs pinned PE (ECPS population)

Add the concept mapping and the comparison config, then run:

```bash
# a) axiom_oracles/config/concept_mappings.yaml — add:
#   us-<st>:policies/<agency>/tanf#<st>_tanf_benefit:
#     description: <ST> TANF benefit (annualized)
#     category: cash; comparison: amount; tolerance: 25; priority: high
#     targets: { axiom: <st>_tanf_annual_benefit, policyengine: <st>_tanf }
# b) comparisons/<st>-tanf-ecps.yaml — copy co-tanf-ecps.yaml, set name, concept,
#    jurisdiction_fips, axiom_program/composed/compiled paths, rulespec_roots.
uv run scripts/run_comparison.py <st>-tanf-ecps --summary
```

`run_comparison.py` composes, compiles, then spins an isolated
`uv run --with policyengine==4.18.9 --with policyengine-us==1.752.2 …` env and
runs PE `Microsimulation` over every populace-us household filtered to the state
FIPS, comparing the compiled Axiom output against PE `<st>_tanf` (annualized;
`tolerance: 25`/yr absorbs rounding). Output: `… (N cases … mismatches: M)` plus a
report under `reports/`. Smoke tip: `--sample-size` subsets the **national**
draw, so a tiny sample yields zero in-state cases ("No cases remain after …
filters") — use `sample_size: 0` (full population) for real numbers.

### Step 5 — Disposition residuals + register coverage

```bash
# dispositions/<st>-tanf-ecps.yaml (schema axiom_oracles.dispositions.v1):
#   one entry per residual, disposition: bridge_artifact (composed-slice vs
#   full-PE-model gap) | axiom_encoding_gap (real bug — fix instead), with a
#   linked_issue. Goal: unexplained == 0.
# conformance/us-pe.yaml: on the us-pe:<st>_tanf row set `suite: <st>-tanf-ecps`
#   and a `note:` (in_scope/suite/note are hand-authored & preserved on regen).
uv run scripts/generate_conformance_universe.py us-pe --check
uv run scripts/conformance_scoreboard.py --snapshot   # -> scoreboard.json + detail/us-pe.json + history snapshot
uv run scripts/conformance_ratchet.py                 # tightens floors (never loosens)
uv run scripts/conformance_burndown.py
```

Ratchet CI fails if a later run drops `covered` below the floor or pushes
`unexplained`/`axiom_attributed_open` above 0. "Covered" means every residual has
a written, linked disposition — not that the legal encoding is gate-complete
(the slice stays `acknowledged_incomplete`).

## Source-type playbook (the `extraction:` block)

Same ingest command for all; only the manifest differs.

- **Clean HTML admin code / manual** (e.g. GA `pamms.dhs.ga.gov`):
  `source_format: html` + `extraction.html_content_selector: <css>` (GA uses
  `article.doc`). BeautifulSoup walks the subtree, one block per element. No OCR.
- **PDF administrative code** (e.g. AL `admincode.legislature.state.al.us`):
  `source_format: pdf`. No `extraction:` → one provision per page. Add
  `request.range_fetch: true` / `range_backend: curl` / `browser_user_agent: true`
  to get past bot protection on large PDFs.
- **PDF agency manual, section-structured** (DE Title 16 §4000, ME Rule 125A):
  `segmentation: labeled_sections` + `section_heading_pattern` +
  `drop_line_patterns` (strip headers/footers). `start_page`/`end_page` for a
  single contiguous window; `page_windows` (list of `{start_page,end_page,
  start_at_pattern?,stop_at_pattern?}`, ascending, non-overlapping) for
  discontiguous slices of one big PDF. Cannot combine `page_windows` with the
  single-window fields.
- **Scanned/image PDF** (some HI/Ghana): add `extraction.ocr: true` +
  `ocr_dpi/ocr_language/ocr_psm`; requires Tesseract on `PATH`.
- **Hard case** (TX Texas Works Handbook, MT, IL): giant multi-section manuals;
  budget several `labeled_sections` manifests with `page_windows`, expect
  multiple ingest iterations to get coverage complete, and a larger PE module
  (25–30 files) that needs more `not_comparable` helper mappings and more
  dispositions.

## Worked example: Alabama (wave-1 flagship)

- **Sources** (already ingested, corpus PRs "Add Alabama TANF …"): AL Admin Code
  660-2-2 "Aid to Dependent Children" (PDF, 45 provisions) + 660-2-4 (62); 2024
  TANF State Plan (payment standards, Attachment E) + Public Assistance Payment
  Manual Appendix N §2 (20% work-expense disregard, $10 minimum grant).
- **Leaf modules** (already encoded): `us-al/policies/dhr/tanf/state-plan/2024/
  payment-standards.yaml` (`al_tanf_payment_standard` = chart[unit_size 1..16],
  FY2026 = 264/304/344/… effective 2023-10-01) and
  `us-al/policies/dhr/public-assistance-payment-manual/appendix-n/section-2/
  payment-computation.yaml` (`al_tanf_countable_income`, `al_tanf_entitlement_amount`
  = max(0, payment_standard − countable_income), `al_tanf_payment_eligible`).
- **Compose** (`programs/us-al/tanf/fy-2026.yaml`, this PR): bridge
  `payment_standard := al_tanf_payment_standard`, gate on
  `household_has_minor_or_pregnant_member and al_tanf_payment_eligible`, output
  `al_tanf_annual_benefit = al_tanf_monthly_benefit * 12`. Composes to 18 derived
  outputs; compiles clean through the Rust engine.
- **Oracle**: `comparisons/al-tanf-ecps.yaml` + concept
  `us-al:policies/dhr/tanf#al_tanf_benefit` → PE `al_tanf`, FIPS 01.

- **Result** (wave-1, PE pin 1.752.2, populace-us 2024, FIPS 01): **1444 / 1444
  comparisons match, 0 mismatches = 100.0%**. `al_tanf_annual_benefit` reproduces
  PE `al_tanf` on every Alabama ECPS household. Zero residuals → `dispositions/
  al-tanf-ecps.yaml` is empty; `unexplained == 0` with no bridge artifacts needed.
  (For comparison, re-running the covered CO suite in the same environment
  reproduced its pinned 1042 / 1045 = 99.71%, validating the harness.)

## Time / cost per state (wave-1 observed)

Assuming infra is already set up (Step 0 done once):

- **Corpus already ingested + leaf modules already encoded** (AL, and any state a
  prior parity sweep touched): ~compose + oracle + register only. **~30–60 min**,
  ~$0 model spend (deterministic compose; no encoder call). Dominated by the full
  ECPS run (~2–4 min wall per state) + dispositioning residuals.
- **Corpus ingested, leaf modules NOT encoded** (GA, DE, ME, HI): add Step 2 —
  one encoder run per leaf module (payment standard + disregards ≈ 2 runs). **~1–2 h**,
  a few $ of gpt-5.5 codex spend, plus iteration if the encoder trips (below).
- **No corpus** (TX/MT/IL and most wave-2): add Step 1 — author manifest(s), fetch,
  extract, sign, guard; iterate until coverage complete. Clean HTML/admin-code:
  **+30–60 min**. PDF manual with `labeled_sections`/`page_windows`: **+1–3 h**.
  Scanned/OCR or a 25–30-file PE module (hard case): **+half a day**, more
  dispositions.

## Failure modes seen

- **Compile can't resolve `imports:`** — the composed YAML keeps import refs; the
  Rust `compile` resolves them via the `AXIOM_RULESPEC_REPO_ROOTS` env var (or the
  runner wires it). Standalone `compile` without that env fails
  "could not be resolved." Also export the root before composing.
- **Leaf free-input naming gap** — a computation leaf may reference `payment_standard`
  while the payment-standard leaf defines `al_tanf_payment_standard`. Bridge it
  with a `derived_formula` in the program spec (done for AL). Watch for the same
  on `gross_earned_income` / `countable_unearned_income` / `assistance_unit_size`.
- **Rulespec root drift** — the comparison composes against
  `~/.axiom-oracles/roots/rulespec-us-<st>/` (an rsync copy, `.axiom` excluded),
  not your checkout. Re-run `sync_rulespec_roots.sh` (extend it to add the new
  state) after every `rulespec-us` pull or the suite validates stale encodings.
- **Small-sample smoke → 0 cases** — `--sample-size` samples the national draw;
  in-state count collapses. Only `sample_size: 0` is meaningful for a single state.
- **Encoder self-import (axiom-encode #1058)** — codex/gpt-5.5 deterministically
  emits a self-import when a provision cross-references a sibling sharing its
  citation prefix (seen on NY Tax 606/616). If a TANF leaf hits it, hold the
  section and file, don't hand-patch (attesting a hand-patch of net-new law needs
  a named `--manual-exception <issue-ref>`).

## Wave-2 worklist entry (template)

One row per uncovered PE-simulated state. Fill from the candidate table:

```yaml
- state: <st>                     # e.g. ga
  fips: "<NN>"                     # 13
  pe_variable: <st>_tanf
  pe_module_files: <v>/<p>         # 10/9  (complexity signal)
  corpus: ingested|needs_ingest    # link the corpus version if ingested
  source_type: html_manual|pdf_admin_code|pdf_manual|scanned|hard
  leaf_modules: encoded|needs_encode
  steps_remaining: [ingest?, encode?, compose, oracle, disposition, register]
  est_effort: 30-60m | 1-2h | half-day
  notes: <e.g. "GA CAPS+SSP manuals also present; PDF manual via article.doc selector">
```

Ready-now (corpus + leaves may exist): **AL (done, this PR), GA, DE, ME, HI**.
Then simplest-PE-module-first through the no-corpus set (MS, ND, NC, SD before
TX/MT/IL). Skip IN (another lane holds it) and non-simulated states (file as
`in_scope: false`).

## Oracle-repo merge discipline

Three other lanes run concurrently. Merge **one PR at a time**: rebase on
`origin/main` immediately before merge, keep the `concept_mappings.yaml` /
`bridges/mappings/us.yaml` additions in separated blocks (append per-state, never
reflow neighbors), re-run the suite after rebase, and **never** admin-merge —
let CI (ratchet + guard) gate. Small durable commits; update `PROGRESS.md`.
