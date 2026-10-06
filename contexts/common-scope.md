# 45 CFR Part 604 signed-encoding scope

This context constrains generation to the official eCFR Part 604 records in
`2026-08-30-proposal-security-title-45-part-604`.

- Source/expression date `2026-08-27` is not the legal effective date.
- Section 604.110(g) expressly identifies `1989-12-23` as the effective date
  of these provisions. Every executable rule must have a false pre-effective
  version beginning `1900-01-01` and an operative version beginning
  `1989-12-23`. Use `1989-12-22` as an adversarial pre-effective case.
- Covered ordinary instruments are Federal contract, Federal grant, Federal
  loan, and Federal cooperative agreement. Do not silently treat another
  instrument as covered. Loan guarantee and loan insurance are distinct and
  outside this requested atomic slice.
- Preserve transaction identity and linkage: the applicant/recipient or tier
  actor, payment, lobbying purpose, target official, instrument, award or
  subaward, upstream transaction, next tier, and agency must not be inferred
  from unrelated facts.
- Missing instrument, amount, fund source, lobbying purpose, target actor,
  transaction linkage, tier role, or prior-filing facts must never become a
  favorable assumed fact.
- Keep separate executable outputs for the appropriated-fund lobbying
  prohibition, baseline certification, conditional SF-LLL disclosure,
  thresholded lower-tier filing, disclosure-only forwarding, and Appendix A
  award-document language flow-down. Do not collapse them into one judgment.
- Do not encode discretionary enforcement, remedies, penalty selection,
  Part 200, cost principles, debarment, Subpart B/C allowance rules, or any
  content not stated by the selected Part 604 record.
- Generate adversarial companion cases for strict boundaries, noncovered
  instruments, appropriated versus nonappropriated funds, disclosure condition
  present versus absent, correct versus incorrect actors/linkage, missing
  facts, and the `1989-12-22` pre-effective sentinel.

