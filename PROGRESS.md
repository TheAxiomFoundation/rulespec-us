# CalFresh BBCE progress

## State

- Branch: `fed-parity/ca-bbce`
- Base: `origin/main` at `f06d6dbbdb4ba376e991020c13d1656d3839e1ec`
- Status: blocked on a pinned-corpus ingest prerequisite; no policy rule has been encoded.
- Pinned corpus: `db12795577c5809009168982cf8a72fb58440620`.

## Done

- Created an isolated worktree from `origin/main`.
- Recorded issue constraints and validation requirements.
- Verified that retained ACIN I-46-25 labels the CalFresh MCE/BBCE gross-income standard as 200% of the federal poverty level.
- Verified that retained MPP and 7 CFR provisions describe categorical-eligibility treatment, including the resource and income tests that categorical eligibility bypasses.
- Confirmed that the pinned corpus does not retain the controlling California authority that confers MCE through the PUB 275 TANF-funded service, nor a current authoritative exclusion set.
- Located the existing state overlay integration point without changing the federal composition or allotment arithmetic.
- Reviewed all 243 issue-linked oracle residuals at `axiom-oracles` commit `5a747cac` and documented six representative gross-only, net-only, and combined-failure cases.
- Confirmed that none of the 138 unique eligibility cases fails the resource test, so later asset-waiver coverage must use a synthetic companion.
- Wrote the source audit, case walk-throughs, skipped-gate rationale, and pending/mapping implications to the intentionally untracked `WORKER-REPORT.md`.

## Next

- Ingest an official California source establishing the PUB 275/MCE categorical trigger and current exclusions (for example, the June 30, 2014 CDSS MCE letter, ACL 14-56/15-42, or current WIC § 18901.5), then update the corpus pin.
- Re-run source verification after the new authority is retained.
- Only then implement the BBCE overlay, add the required boundary/waiver/exclusion and mutation tests, and run the pinned companion, validation, and reverse-index gates.
- Re-run the 243 oracle residuals after merge in the main lane and classify any new output mappings before the changed-file gate.
