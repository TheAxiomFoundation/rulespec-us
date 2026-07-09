# Bulk worklist production — federal continuation + omnibus splits

Fuel for the local-drain saturation worker (`--status pending`). Validation year
2026. No amounts are placed in worklist entries — the encoder derives every value
from the corpus. Citation paths are corpus-verified against
`corpus.current_provisions` (exact `eq` match) and, for fragment citations,
slice-verified against the encoder's actual
`_slice_parent_corpus_text_for_requested_path`.

## Mechanism note (why fragment citations resolve without corpus re-anchoring)

The encoder fetches source text by exact `citation_path`, and when a fragment
path (`.../<sec>/<frag>`) has no row it falls back to the parent section row and
slices the requested parenthetical fragment
(`_candidate_corpus_source_lookup_paths` → `_slice_parent_corpus_text_for_requested_path`).
So a subsection split needs only a fragment citation whose top-level marker is
**parenthetical** (`(1)`, `(a)`). Period-marked top levels (`1.`, `A.`) are not
sliceable and are skipped with reason (they would need corpus re-anchoring at
subsection granularity or an encoder period-marker slicer).

## Track 2 — omnibus subsection splits (#757)

Five `needs-subsection-split` parents re-dispositioned; parents set to
`skip-subsection-split` (drain no longer re-attempts the whole section).

| Parent | Disposition | Subsection entries (batch SS1) |
| --- | --- | --- |
| `us-mi/statute/206.30` | split | `/2 /3 /7 /8 /9 /10 /11 /12` (skip `/1`: ~22 KB AGI+modifications omnibus, irreducible) |
| `us-mi/statute/206.51` | split | `/1 /6 /10` (skip earmark/admin subs) |
| `us-nc/statute/105/105-153.5` | split | `/a /a1 /b` (skip `/c /c1 /c2 /c3 /d`: additions omnibus + S-corp/pass-through, oversized/degenerate) |
| `us-nd/statute/57/57-38-30.3` | skip | none — `1.`/`a.` period markers, not parenthetical-sliceable |
| `us-ok/statute/68-2355` | skip | none — `A.`/`B.` period markers, not parenthetical-sliceable |

14 subsection entries produced (8 MI-206.30 + 3 MI-206.51 + 3 NC-105-153.5).

## Track 1 — federal continuation (batch FED1)

F1 spine (26 USC 61/62/64/65/68/102/212) and the named leverage tranche
(surtaxes 1401/1411/3101, credits 22/25A/25B, energy 25C/25D/25E/30D, ACA PTC
36B) are already encoded on `origin/main` — not re-queued. Next un-encoded,
corpus-verified, PE-simulated leverage:

- `us/statute/26/164` — Taxes (SALT/itemized taxes deduction)
- `us/statute/26/221` — Interest on education loans (student-loan-interest deduction)
- `us/statute/26/219/b` — IRA maximum deduction amount
- `us/statute/26/219/g` — IRA active-participant phase-out
- `us/statute/26/223/b` — HSA contribution limitations
- `us/statute/26/1402/a` — Net earnings from self-employment (SECA base)
- `us/statute/26/1402/b` — Self-employment income ($400 floor)

Skipped (documented): `170` (charitable, 94 KB omnibus), `27`/`901` (FTC, low
household leverage / 901 omnibus), `67` (misc-itemized floor, suspended under
current law). Benefit-program surfaces (7 CFR/42 CFR — WIC, school meals, CSFP,
Section 8) are the next tranche, scoped to what PolicyEngine simulates.
