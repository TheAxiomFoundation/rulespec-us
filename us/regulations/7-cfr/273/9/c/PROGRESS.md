# 7 CFR 273.9(c) income exclusions

## State

In progress. All twenty top-level exclusions and their nested conditions are
encoded. The exclusion layer now separates ordinary payment rows from the
education, charitable-donation, self-employment-cost, and outgoing-child-
support aggregates that require shared pools, quarterly history, or non-income
accounting items. Companion tests are being rebuilt for the final interfaces.

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
- Encoded every paragraph (c)(1)-(20) route with paragraph-specific sources and
  proof atoms.
- Removed only the assigned paragraph-(c) deferral from the shared parent; the
  paragraph-(b) deferral remains untouched.
- Added payment-level maximum composition so overlapping legal routes on one
  atomic payment are counted once.
- Added an individual/assistance-period education relation that applies
  expenses to unearned aid before earned aid and caps exclusions at the
  individual's educational income.
- Added a Federal-fiscal-quarter donation-history relation that applies the
  $300 cap across all current-month donations.
- Moved outgoing child support to its own relation and moved paragraph-(c)(9)
  production costs to a household boundary, avoiding false incoming-payment
  caps.
- Recorded the unresolved § 273.11(a) production-cost determination as a
  narrow deferred output instead of recreating another worker's source.
- Corrected the PASS, VISTA contract, student-break, migrant-travel, State-plan
  election, dependent-care coordination, partial demonstration, and partial
  combat-pay branches identified during independent legal review.
- Capped payment, education-case, and charitable-donation exclusions at the
  amounts staged by paragraph (b)'s pre-exclusion composition while leaving
  paragraph (c)(9) costs and paragraph (c)(17) outgoing support uncapped by an
  incoming receipt.
- Added the shared paragraph-(c)(12) interface for quarterly limit already used
  by donations resolved inside paragraph-(b)(3) or (b)(4) components.
- Wired the standalone 20 U.S.C. 1087uu/BIA education determination into the
  paragraph-(c)(3) amount composition and completed the final module audit.
- Confirmed the live 104-rule module parses, passes pinned proof validation
  (130 atoms), and compiles to 103 executable rules with the pinned engine.

## Next

- Rebuild payment, education-case, donation-history, child-support, and
  household companion tests with every input fact assigned.
- Run pinned runtime/proof validation and repository-wide structural,
  coverage, reverse-index, and generated-artifact checks.
- Record exact results, push the branch, and open the required draft PR.
