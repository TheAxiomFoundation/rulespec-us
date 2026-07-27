# Progress — employer Medicare evidence

## State

Complete. Both parts are implemented, the final report is in `OUTPUT.md`, and
the evidence package records 4/5 criteria holding. `executable` remains false
because no published artifact and released-binary stranger path exists.

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
- Preserved the signed modules' formal section-root citations: leaf production
  itself resolves the audited `/a` and `/b` identifiers, while changing the
  module paths would unnecessarily invalidate their signed encoding
  manifests. Expanded only the subsection (b) deterministic boundary cases.
- Built and registered the non-population `us-employer-medicare-grid` on the
  dedicated axiom-oracles branch. It compares only PolicyEngine's explicit
  aggregate employer-Medicare variable, records its one Person as
  `is_legal_employer: false`, and passes 8/8 with zero mismatches or errors.
  Oracle commit: `29bef862b7a12c4e3012e00ae88d0d2ed1543797`;
  deterministic receipt SHA-256:
  `d689f112b9c87573c33a66d125a83cc89ea6507a9f96690d5f55bc38ce347c42`.
- Verified repository/source-side closure at the formal `/3111` root: 22
  provisions encoded, one repealed subsection excluded, and zero pending.
  Effective-liability composition remains explicitly deferred, so a composed
  interpretation of `closed` would fail.
- Compiled the pinned module twice with released engine tag v0.1.1 and obtained
  identical artifact SHA-256
  `4edcb5e31d4af139c6347a9e275bad92c4bf0c15fde91465617007b0236f4cbc`.
  The golden `$100,000 -> $1,450` run and all eight fixtures pass exactly.
- Wrote the five-criterion evidence package at
  `us/payroll/y1-employer-medicare-evidence.md`; it keeps `executable: false`
  and makes no certification claim.
- Final RuleSpec guards pass 18/18 with one inherited warning; the reverse
  index is current. The oracle checks and live grid remain green.
- Attempted pushes for the dedicated branches and a draft RuleSpec PR. GitHub
  DNS/API access was unavailable, so no remote branches or PR were created.
- Wrote the final handoff report to `OUTPUT.md`.

## Next

- A maintainer with GitHub access should push the three branches and open the
  intended draft PRs.
- Review, sign, and merge the corpus successor before treating the new leaves
  as shared provenance.
- Publish a one-output employer-Medicare artifact and perform a stranger-path
  released-binary run before reconsidering `executable`.
