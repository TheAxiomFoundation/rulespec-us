# Progress — §112 combat-zone month rules

## State

- Branch: `closure/w5-eitc-112-combat`
- Checkout: `.git/codex-worktrees/w5-eitc-112-combat` (the requested sibling worktree path is outside the writable sandbox)
- Scope: EITC frontier items 19–23, the 26 U.S.C. §112 combat-zone and missing-status month rules
- Status: source research complete; implementation in progress

## Done

- Read the encoder preamble and repository agent rules.
- Created the requested branch from `origin/main`.
- Created this committed progress ledger at the start of work.
- Resolved the assignment numbering: items 19–23 among the 23
  must-encode entries are classification rows 29, 30, 31, 32, and 34.
- Scanned every statute inventory at corpus pin
  `bf97b17baebfdf12601f7c23697524bf5adcdaed`. The relevant §112 paths occur
  only in the 2026-07-13 recovery inventory; Title 5 §5561 and the required
  Title 37 pay provisions do not occur in any inventory.
- Read the bodies at 26 U.S.C. §112(a), (a)(2), (b), (b)(2), (c)(2),
  (c)(3), (c)(5), (d)(2), and (d)(3), each with expression date 2026-07-13.
- Chosen disposition:
  - encode the hospitalization/service/causation composition in
    §112(a)(2), (b)(2), and (c)(2)–(3);
  - encode the final-sentence January 1978 boundary in §112(a) and (b);
  - defer the civilian missing-status output on absent 5 U.S.C. §5561(4)–(5);
  - defer the maximum enlisted amount on absent Title 37 pay provisions;
  - defer post-termination month computation on absent controlling
    Presidential termination designations.
- Identified an existing unit mismatch: the consumer compares a count named
  in months to a parameter encoded as 2 years. The implementation will use
  the exact 24-month boundary and test months 24 and 25.

## Next

1. Add the two derived rules, three exact deferrals, and granular proof atoms.
2. Update all affected companion tests and add statutory boundary cases.
3. Refresh generated provenance/index artifacts and commit each coherent step.
4. Run focused and repository validation, update this ledger, push, and open the required draft PR if network access permits.
