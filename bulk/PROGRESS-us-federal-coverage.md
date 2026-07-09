# US coverage wave 1 — federal encode funnel

Mission: ingest-first feeding of the encoder for the federal rows the federal lane
flagged as encode-then-cover (IRC 61-63 assembly; credits 25A/25B/22/27; surtaxes
1401/1411/3101(b); energy 25C/25D/30D/25E; ACA PTC 36B; benefits WIC/Head Start/
school-meals/CSFP/Section-8).

## Key finding: corpus is present; the gap is encoding, not ingest

Every target IRC section already resolves in Supabase `corpus.current_provisions`
with a full section body (bulk Title 26 USLM ingest, version `2026-04-29`,
`source_as_of` 2025-12-03). Verified by exact-equality lookup — the same resolution
the cloud encoder uses. So corpus#108 (ingest 36B) is effectively satisfied: 36B is
present ("Refundable credit for coverage under a qualified health plan"). The corpus
is section-granular (whole-section text in one row's `body`); the encoder resolves the
section row and emits subsection-granular RuleSpec.

Cross-referencing the encoded YAML on `main`, **12 of the 15 target IRC sections are
already encoded**: 63, 22, 25A, 25B, 1401, 1411, 3101, 36B, 25C, 25D, 30D, 25E. The
prior bulk Title 26 wave already covered the surtaxes, energy credits, saver's/elderly/
education credits, and ACA PTC. This mirrors lane A's state finding: uncovered = an
encoding gap, not a corpus gap.

Remaining unencoded tax sections: **61 (gross income), 62 (AGI), 27 (foreign tax
credit)**. `us/statutes/26/63.yaml` is `status: deferred` — its subsection (a)
taxable-income composition is explicitly deferred "until the broader gross-income and
deduction surface is available." Encoding 61/62 directly unblocks that spine.

## Batch F1 queued (bulk/worklist.yaml) — corpus-verified

Ordered by leverage (spine first). Each citation confirmed present in
`current_provisions`; xref = count of external "section N" references in the body
(a #1058 self-import risk proxy).

| citation | class | xref | len | rationale |
| --- | --- | --- | --- | --- |
| us/statute/26/61 | definition | 0 | 892 | Spine root: gross income = enumerated components (1)-(14). |
| us/statute/26/62 | definition | 42 | 14308 | Spine: AGI = gross income minus above-the-line deductions. Refs are 16x/2xx (not 62x siblings), so encode#1058 self-import does not apply; may fail-closed on unresolved imports (165/219/223). |
| us/statute/26/64 | definition | 2 | 469 | Ordinary income defined; self-contained. |
| us/statute/26/65 | definition | 0 | 373 | Ordinary loss defined; self-contained. |
| us/statute/26/68 | limitation | 1 | 702 | Overall (Pease) limitation on itemized deductions. |
| us/statute/26/102 | exclusion | 2 | 1291 | Gifts/inheritances gross-income exclusion. |
| us/statute/26/212 | deduction | 0 | 379 | Expenses for production of income. |

## Deferred with reasons (not queued)

- **27 (foreign tax credit)** — body is a one-line delegation "to the extent provided
  in section 901"; §901 is absent/unencoded. Not self-contained; low microsim leverage.
  Queue after §901 is ingested + encoded.
- **72 / 101 / 108 / 162 / 223 / 219 / 165** — xref density 16-138; cross-reference-heavy,
  encode#1058 risk. Encode bottom-up (self-contained fragments first) in a later batch.
  These are the above-the-line deductions that 62 imports; encoding them first would let
  62 apply cleanly.

## Benefits tier — scoped hand-off (deferred, not fabricated)

Corpus presence probed by exact-equality lookup:

- WIC (42 USC 1786): ABSENT · School lunch/breakfast (42 USC 1758/1773): ABSENT ·
  Head Start (42 USC 9831/9840): ABSENT · Section 8 (42 USC 1437f/1437a): ABSENT ·
  CSFP: only the 7 USC 612c appropriation stub is present (not the program rule).

The statutory authorities are largely un-ingested, and — critically — the *computable*
rule for each lives in CFR plus annual agency notices (USDA Income Eligibility
Guidelines; HUD Fair Market Rents / payment standards), not the USC. USC-only ingest
would not give the encoder a self-contained rule. Per the task's "benefits last; scope
each to what PE simulates before ingesting," these are deferred to the benefits ingest
lane with the operative-authority list above, rather than queued as USC stubs.

## Dispatch + CI

- Batch F1 dispatched via `gh workflow run bulk-encode.yml -f batch=F1 -f limit=8`.
- CI outcomes recorded below by class (merged / pr-open / needs-fixtures / failed).

## Log

- Worktree from origin/main; corpus read verified via the atlas Supabase pooler.
- Confirmed all 15 target IRC sections present in `current_provisions`; diffed against
  encoded YAML on main; only 61/62/27 unencoded.
- Appended batch F1 (7 entries) to `bulk/worklist.yaml`; `compute_matrix.py` selects
  all 7 as pending with correct slugs.
