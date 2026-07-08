# US coverage wave 1 — ingest lane A

Mission: corpus-ingest individual income tax statutes for uncovered state-income-tax
rows whose **state name starts A–K**, then feed `bulk/worklist.yaml` so the cloud
dispatcher (gpt-5.5) encodes them. Read authoritative list from
`axiom-oracles conformance/detail/us-pe.json` (uncovered `*_income_tax`; covered
already: CA/NY/IL/MA/CO).

## Slice (13 jurisdictions, name A–K)

| Jur | State | Corpus queue status | Income-tax citations verified | Worklist | Bulk PR |
| --- | --- | --- | --- | --- | --- |
| us-al | Alabama | done (57667) | pending | – | – |
| us-az | Arizona | done (28283) | pending | – | – |
| us-ar | Arkansas | **blocked_primary_source** | pending | – | – |
| us-ct | Connecticut | done (31301) | pending | – | – |
| us-de | Delaware | done (25739) | pending | – | – |
| us-dc | District of Columbia | done (24346) | pending | – | – |
| us-ga | Georgia | done (32457) | pending | – | – |
| us-hi | Hawaii | done (20962) | pending | – | – |
| us-id | Idaho | done (22255) | pending | – | – |
| us-in | Indiana | done (91620) | pending | – | – |
| us-ia | Iowa | done (36595) | pending | – | – |
| us-ks | Kansas | done (49565) | pending | – | – |
| us-ky | Kentucky | done (40088) | pending | – | – |

Key finding: 12/13 states already have full statute corpora productionized in
Supabase `corpus.current_provisions` ("uncovered" is an *oracle*/encoding gap, not a
corpus gap). Lane work = verify the PE-simulated income-tax sections (rate/brackets,
standard deduction, personal exemption, headline credits) exist as `citation_path`s,
scope per `<state>_income_tax` PE-US module, skip xref-heavy sections (encode#1058),
append corpus-VERIFIED worklist entries, dispatch bulk workflow in batches of 6–8.

## Recipe (per state)
1. Read PE-US `variables|parameters/gov/states/<st>/tax/income` → statutory refs.
2. Map refs → corpus `citation_path`; verify each in Supabase current_provisions
   (>0 rows, substantive body). 0 rows = do NOT list.
3. Append entries to `bulk/worklist.yaml` (small PR, rebase before merge — sibling
   lanes share the file).
4. Dispatch `bulk-encode.yml` per batch of ~6–8; poll CI foreground; note
   fail-closed rejections for pipeline lanes. No admin-merge.

## Log
- Setup: worktree `us-coverage-wave1-lane-a` from origin/main; Supabase read verified.
