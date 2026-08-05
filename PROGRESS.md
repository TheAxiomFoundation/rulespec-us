# Alabama Age-65 Exemption Evidence Progress

## State

Evidence assembly is complete for the Alabama tax-year 2025 age-65
retirement-income exemption. The honest verdict is 3 of 5:
`provision_rooted`, `conformant`, and `exercised` hold; `closed` has one
pending substantive section-root path; and `executable` is blocked by the
missing published artifact and official stranger path. No certification claim
has been made.

## Done

- Read the closure-sprint encoder preamble, repository agent notes, and
  Alabama-specific agent notes.
- Read the rank-6 candidate row and evidence pointers from the r1 sweep.
- Read the employee-Medicare evidence package and draft PR #1149 as the
  required structure and honesty model.
- Created branch and isolated worktree `x4-al-age65-exemption` from
  `origin/main` at `ecb057ef35ab47fb055213b42459c42ae63485ef`.
- Scanned the pinned corpus frontier: one raw inventory occurrence, one unique
  citation path, and one resolving provision record.
- Identified the Act 2026-603 source-text gap and fixed candidate scope to tax
  year 2025.
- Replaced the three tax-year-2024 samples with a five-case tax-year-2025
  companion census crossing age 64/65 and taxable retirement income at zero,
  $5,999, $6,000, and $6,001.
- Passed all five direct companion cases with `axiom-encode test` using the
  released v0.1.1 engine source checkout.
- Audited closure as one partially encoded, pending section path: the corpus
  has no paragraph-level descendant for subsection (a)(13), while the sole
  section body contains other substantive exemption categories explicitly
  deferred by the module.
- Compiled the module twice from a canonical `rulespec-us` checkout with the
  clean v0.1.1 released-tag source build; both artifacts had SHA-256
  `08b6ef3211ea3b3d305be899088b7573896e5838a02069b6eeda9128323d7301`.
- Ran the compiled output for a tax-year-2025 age-65 taxpayer with $7,000 of
  taxable retirement income; the engine returned $6,000 and traced
  `40-18-19(a)`.
- Confirmed that no Alabama income-tax program spec or published one-output
  artifact exists. The executable criterion therefore does not hold.
- Registered the five-case TY2025 grid in
  `axiom-oracles@76b8564ab38c01ffd4d2d361ce4f0cea978973a8`, with an exact
  public nonnegative-input schema and the reviewed PolicyEngine stack.
- Passed 30 focused and federal-runner regression tests plus Ruff check in
  `axiom-oracles`.
- Ran the registered grid against the pinned RuleSpec snapshot: 5 comparisons,
  5 matches, 0 mismatches, and 0 errors. Receipt SHA-256:
  `4924c5c78f25c99388aa4fa7f1d7b8e0838231f5e55abd862068013dd519de35`.
- Wrote the complete five-criteria package at
  `us-al/income-tax/v1-age65-retirement-exemption-evidence.md`.

## Next

- Obtain paragraph-granular corpus resolution for subsection (a)(13), or
  encode the remaining substantive section body, before claiming `closed`.
- Publish a provenance-stamped one-output artifact and reproduce the golden
  value with an attested v0.1.1 release asset before claiming `executable`.
- Human review only; do not add this candidate to `certified-nodes.yaml` while
  either blocker remains.
