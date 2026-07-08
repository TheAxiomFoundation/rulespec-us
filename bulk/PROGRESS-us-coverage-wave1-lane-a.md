# US coverage wave 1 — ingest lane A

Mission: corpus-verify individual income tax statutes for uncovered state-income-tax
rows whose **state name starts A–K**, then feed `bulk/worklist.yaml` so the cloud
dispatcher (gpt-5.5) encodes them. Authoritative list: `axiom-oracles
conformance/detail/us-pe.json` (uncovered `*_income_tax`; covered already
CA/NY/IL/MA/CO). Slice = 13 jurisdictions.

Key finding: 11/13 slice states already have full statute corpora productionized in
Supabase `corpus.current_provisions` — "uncovered" is an *oracle/encoding* gap, not a
corpus gap. Lane work = map each `<state>_income_tax` PE-US module to its operative
statutory sections, verify every `citation_path` in Supabase (exact `eq.` query, the
same view the cloud encoder resolves against), skip AGI/IRC-conformity umbrellas and
transitory rebates (encode#1058), and queue corpus-VERIFIED entries.

## Slice status

| Jur | State | Corpus | Verified income-tax sections | Batches |
| --- | --- | --- | --- | --- |
| us-hi | Hawaii | done | 6 (rate, exemption, EITC, renters, CDCC, food/excise) | AK1 |
| us-az | Arizona | done | 7 (rate, std ded, exemption, family/dependent/excise/property credits) | AK1–AK2 |
| us-ct | Connecticut | done | 6 (rate, exemption, personal/property/EITC/stillborn credits) | AK2–AK3 |
| us-ky | Kentucky | done | 5 (rate, std ded, family-size/CDCC/tuition credits) | AK3 |
| us-de | Delaware | done | 6 (rate, std ded, itemized, personal/CDCC/EITC credits) | AK4 |
| us-ga | Georgia | done | 5 (rate, exemption, std-ded computation, CDCC, low-income) | AK4–AK5 |
| us-al | Alabama | done | 3 (rate, deductions std+FIT, exemptions) | AK5 |
| us-dc | District of Columbia | done | 3 (rate, EITC/CDCC credits, Schedule H property) | AK5–AK6 |
| us-id | Idaho | done | 8 (rate, food/aged/CTC credits, retirement/care/aged/capgains deductions) | AK6–AK7 |
| us-in | Indiana | done | 9 (rate, 5 deductions, elderly/529/EITC credits) | AK7–AK8 |
| us-ia | Iowa | done | 4 (rate, exemption, EITC, CDCC) | AK8 |
| us-ar | Arkansas | **blocked_primary_source** | 0 corpus statute rows — cannot verify/queue | — |
| us-ks | Kansas | **income-tax article gap** | article 79-32 absent from corpus (only 79-32,100b) | — |

62 corpus-VERIFIED entries queued across 11 states, batches AK1–AK8 (8×7 + 6).
Every heading is verbatim from corpus; every citation confirmed FOUND with a
substantive operative body via live `current_provisions` `eq.` query.

## Remaining in slice (for the pipeline/ingest-adapter lanes)
- **us-ar (Arkansas)** — 0 statute provisions in corpus (queue: `blocked_primary_source`).
  Needs a primary official source ingest; secondary summaries (Justia/FindLaw) forbidden.
  No corpus write creds in-lane (corpus service_role key unavailable), so not ingestible here.
- **us-ks (Kansas)** — the income-tax article (79-32,101…) is missing from an otherwise
  complete KS corpus (adapter dropped the comma-format sections; only `79-32,100b` landed).
  Needs a scoped KS income-tax re-ingest.

## Corpus gaps noted (PE simulates, section absent — for corpus refresh)
- us-dc: KCCATC (§47-1806.15) and DC CTC (§47-1806.17) — snapshot predates enactment.
- us-ga: surplus tax rebate (§48-7-20.2) and itemizer credit (§48-7-27.1) — not codified in snapshot.
- Various one-time rebates (AZ/CT/DE/GA/ID/IN) are session-law/transitory — intentionally not queued.

## Log
- Setup: worktree from origin/main; Supabase read verified; PROGRESS committed at start.
- Verified all 11 corpus-present states (PE module → statutory refs → Supabase `eq.` confirm).
- Appended 62 entries (AK1–AK8) to `bulk/worklist.yaml`; compute_matrix parses all batches.
- Note: shared scratchpad `verify.py` was clobbered by the L–N sibling lane mid-run; used a
  private re-verification gate — no impact on results.
