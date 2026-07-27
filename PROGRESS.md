# Progress — employer Medicare evidence

## State

Part 1 is implemented. Part 2 is active: build the targeted employer-aggregate
oracle grid and assemble the five-criterion evidence.

## Done

- Read the closure-sprint encoder preamble, task-specific brief, repository
  instructions, and the employer-Medicare row in the r1 candidate sweep.
- Created an isolated clean worktree without modifying the shared dirty
  checkout.
- Chose native leaf production over a section-plus-span fallback. The old
  section body is correct, but its raw object and URL point to 26 USC 45A, so
  a span would preserve false provenance.
- Re-indexed the already-retained official Title 26 USLM bytes through the
  standard `extract-usc` pipeline on the dedicated axiom-corpus branch
  `repair/usc-3111-provenance`.
- Produced 24/24 complete extraction rows, 22 asserted descendants, and a
  114/114 complete consolidated successor; committed the corpus repair at
  `43636a86e8e0f3c4bfdbefffd5ef4289921dc1b9`.
- Confirmed the successor release has zero errors and exactly the same 541
  inherited warnings as its predecessor; the focused corpus quality suite
  passes 17/17. The ingest attestation cannot be signed locally because the
  signing key is unavailable.
- Repointed the section 3111(a) and (b) module/proof citations to their exact
  native leaf identifiers and expanded the subsection (b) deterministic
  boundary cases.

## Next

- Register and run a non-population PolicyEngine grid against the explicit
  employer-aggregate variable; do not rely on the legacy Person-level mapping
  or population receipt.
- Compile and run the golden RuleSpec case on a released engine binary, while
  keeping `executable` false unless a published artifact and stranger path
  actually exist.
- Assemble and validate the five-criterion employer Medicare evidence package.
- Write the final report to `OUTPUT.md`, attempt the sprint output path, push,
  and open a draft PR.
