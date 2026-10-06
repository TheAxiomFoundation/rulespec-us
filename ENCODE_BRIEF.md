# Encode brief: Social Security Title II benefit formulas (42 USC 415, 402(q)/(w), 416(l))

You are encoding the OASI retirement-benefit computation chain into
RuleSpec for this repo (rulespec-us). This is the rules layer the
populace-dynamics scoring program will run earnings histories
through, so statutory fidelity and testable formulas matter more
than breadth.

## Scope, in build order (commit and push after EACH section)

1. `us/statutes/42/415/b.yaml` — Average Indexed Monthly Earnings:
   indexing of creditable earnings by the average wage index to the
   year the worker attains age 60 (unindexed thereafter), benefit
   computation years = elapsed years after 1950 (or age 21) through
   age 61 minus 5 dropout years (minimum 2), highest-N selection,
   AIME = sum / (12 * N), rounded down to the dollar.
2. `us/statutes/42/415/a.yaml` — PIA formula: 90% / 32% / 15%
   brackets over the bend points; reference the existing bend-point
   parameters (see `us/policies/ssa/pia-bend-points/2026.yaml` —
   the per-eligibility-year derivation is already encoded there;
   your formula should take first/second bend points as inputs the
   same way SSI encodings take parameters). Round per 415(g)
   (next lower multiple of $0.10).
3. `us/statutes/42/415/i.yaml` — cost-of-living adjustment
   application to the PIA (COLA percentages are parameters; encode
   the application rule, with the COLA values sourced like the
   bend points are).
4. `us/statutes/42/416/l.yaml` — retirement age: the age-65-to-67
   schedule by year of birth, exactly per the statute's table.
5. `us/statutes/42/402/q.yaml` — reduction for early claiming:
   5/9 of 1% per month for the first 36 months before retirement
   age, 5/12 of 1% per month beyond 36.
6. `us/statutes/42/402/w.yaml` — delayed retirement credits: the
   percentage-per-month table by year of birth (2/3 of 1% per month
   for workers born 1943 or later), applied for months from
   retirement age to 70.

## House style (imitate, do not invent)

- Read THREE existing encodings first and imitate their structure
  exactly: `us/statutes/42/1382/a/1.yaml` (+ its `.test.yaml`),
  `us/statutes/26/1/h.yaml`, and
  `us/policies/ssa/pia-bend-points/2026.yaml`.
- format: rulespec/v1; rules carry kind (parameter/formula), dtype,
  source, metadata.proof.atoms with corpus_citation_path + excerpt,
  and versions with effective_from.
- Statutory text excerpts in proof atoms must be VERBATIM from
  42 USC. Use citation paths in the same style the SSI encodings
  use for their statute text.
- Tests go BESIDE each encoding as `.test.yaml`, imitating the SSI
  test format. Use SSA's own published examples as test vectors
  where possible (e.g., the 2026 bend points 1286/7749 imply: a
  worker with AIME 8000 and 2026 eligibility has
  PIA = 0.9*1286 + 0.32*(7749-1286) + 0.15*(8000-7749)
      = 1157.40 + 2068.16 + 37.65 = 3263.21 -> 3263.20 after
  415(g) rounding). Derive every expected value in a comment.
- Repo rules (CLAUDE.md): encodings under statutes/, tests beside
  as .test.yaml, no separate parameter/fixture files, no generated
  artifacts.

## Working rules

- You are on branch ss-title-ii-benefit-formulas in a dedicated
  worktree. Commit after every completed section with a clear
  message and PUSH immediately (git push -u origin
  ss-title-ii-benefit-formulas on the first push). Never batch all
  work into one commit.
- Maintain PROGRESS.md at the worktree root from the start: state /
  done / next / open questions. Update it in every commit.
- If the repo has a validation or test runner (check scripts/ and
  tests/), run it on your files before each commit and fix what it
  flags.
- Where the statute's text and current SSA practice diverge (e.g.,
  amounts superseded by wage indexing), encode the STATUTE and note
  the operational parameter in the summary, following how the
  existing encodings handle it.
- When done: open a DRAFT pull request against main titled
  "Encode Title II benefit formulas (415, 402(q)/(w), 416(l))" with
  a section-by-section summary, and note in PROGRESS.md that the PR
  exists. Do not merge anything.
