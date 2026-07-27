# 7 CFR 273.9(c) income exclusions

## State

In progress. The authoritative paragraph (c) text and RuleSpec composition
conventions have been inventoried. The implementation will classify individual
income payments and sum each excluded payment once, preventing overlap among
the regulation's alternative exclusion routes.

## Done

- Read `ENCODER-PREAMBLE.md` and the slice brief.
- Read the repository `CLAUDE.md`.
- Confirmed the frozen `programs/` tree and other protected files are out of
  scope.
- Confirmed the assigned branch is `closure/enc-273-9c`.
- Read every required sibling module and companion test.
- Extracted all twenty paragraph (c) exclusions and their nested conditions
  from the 2026-07-09 authoritative corpus row.
- Identified the explicit State options in paragraphs (c)(3)(v), (c)(17),
  (c)(18), and (c)(19), and confirmed the school-clothing allowance in
  (c)(5)(i)(E) is not an optional SNAP treatment.
- Confirmed the exclusion output must remain independent of the separately
  owned paragraph (b) inclusion layer.
- Chose payment-level classification plus a household relation aggregate to
  avoid double-counting payments that qualify under multiple exclusions.

## Next

- Encode every paragraph (c) exclusion with exact citations and proof atoms.
- Add payment-level and aggregate companion tests that assign every input fact.
- Remove only the paragraph (c) deferred-output block from the parent module.
- Run repository validation, update this ledger, commit each coherent step,
  push the branch, and open the required draft PR.
