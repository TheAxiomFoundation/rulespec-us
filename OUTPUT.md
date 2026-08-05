# Final report — employer Medicare evidence

## Outcome

Part 1 is repaired through native corpus leaf generation. Part 2 produces a
truthful five-criterion package with **4 of 5 criteria holding**.
`executable` fails because no published employer-Medicare artifact and
released-binary stranger path exists. No population suite or
`certified-nodes.yaml` write was made.

The full evidence is
`us/payroll/y1-employer-medicare-evidence.md`.

## Part 1 choice

**Chosen:** re-index the already-retained official Title 26 USLM bytes through
the standard axiom-corpus pipeline and produce source-native section 3111
leaves, including `/a` and `/b`.

**Why:** the former section-only rows had the correct 5,071-character section
body, but their raw object and URL pointed to 26 USC 45A. Repointing the
RuleSpec modules to that section with spans would have preserved false
provenance. The retained OLRC XML already identifies the subsection frontier,
so leaf generation is re-indexing existing bytes, not fetching or authoring
law.

Results:

- extraction scope: 24/24 complete, including 22 asserted descendants;
- consolidated successor: 114/114 complete;
- exact `/3111/b`: one selected-release row, 314 characters, correct official
  section 3111 URL and retained USLM source;
- release selector: `us-rulespec-2026-07-27-3111-provenance`;
- corpus commit: `43636a86e8e0f3c4bfdbefffd5ef4289921dc1b9`;
- release validation: zero errors and the same 541 inherited warnings as the
  predecessor; and
- focused corpus quality tests: 17 passed.

The signed a/b modules keep their existing formal section-root proof paths.
The new corpus leaves themselves resolve the audited `/a` and `/b` legal
identifiers. This avoids invalidating the signed module manifests. The corpus
ingest manifest remains unsigned because the local signing key was unavailable;
no signature was fabricated.

## Part 2 criteria

| Criterion | Verdict | Evidence |
|---|---|---|
| `provision_rooted` | **holds** | The selected successor resolves one corrected `/3111` row and one exact `/3111/b` row from official retained USLM bytes. The RuleSpec node names 26 USC 3111(b), remains entity `Employer`, and computes `wages × 0.0145`. |
| `conformant` | **holds at the aggregate-value boundary** | A new non-population oracle grid queries only PE-US `employer_total_medicare_tax` from `employer_total_payroll_tax_gross_wages`. Its one technical Person is recorded as `is_legal_employer: false`. Eight cases pass with zero mismatches/errors; receipt SHA-256 `d689f112b9c87573c33a66d125a83cc89ea6507a9f96690d5f55bc38ce347c42`. |
| `exercised` | **holds** | Six unique aggregate wage values cover zero, one dollar, ordinary wages, the OASDI-base anti-cap seam, one dollar above it, and high wages. Three `$300,000` partition diagnostics validate the adapter's aggregation contract but are not represented as legal PE Employer relations. All constants and boundary facts are declared. |
| `closed` | **holds for repository/source closure** | The honest formal `/3111` frontier has 23 paths: 22 encoded, one repealed subsection excluded, zero pending. The aggregate module still defers effective-liability composition across exemptions and credits; under a composed-liability interpretation this criterion fails. |
| `executable` | **fails** | Released-tag engine v0.1.1 compiles deterministically and all eight local fixtures pass; `$100,000 → $1,450`. Artifact SHA-256 is `4edcb5e31d4af139c6347a9e275bad92c4bf0c15fde91465617007b0236f4cbc`. It is local and unpublished, and there is no released-binary plus published-artifact stranger path. |

## Pins and receipts

- RuleSpec implementation/fixture:
  `3a1694e9d94f7e9684ffbff4abd39b262c424227`, tree
  `6b6f41cd5c30f63ae41e98ec935103c829a11a7a`.
- axiom-corpus:
  `43636a86e8e0f3c4bfdbefffd5ef4289921dc1b9`, tree
  `e99b8631c661af4ee3d85f8a41d7227aaa2e93a7`.
- axiom-oracles:
  `29bef862b7a12c4e3012e00ae88d0d2ed1543797`, tree
  `664fce4455049f0f6ef67848cf5d71d4e1fab040`.
- PolicyEngine stack: `policyengine==4.18.9`,
  `policyengine-us==1.767.3`, `policyengine-core==3.30.3`;
  reviewed PE-US source
  `49d19b239a593dbac8920ac6fd80cfe33372343a`.
- Engine: annotated tag `v0.1.1`, peeled commit
  `e3e2da83222463d9b68b0681c00820e9d412c011`.

## Validation

```text
RuleSpec repository layout + reverse index + manifest guard:
  18 passed, 1 inherited unmanifested-module warning
RuleSpec reverse-index freshness:
  4,239 provisions / 5,078 edges / 4,486 modules, up to date
Released-tag local engine:
  8/8 fixtures exact; deterministic artifact hash
Corpus release-quality tests:
  17 passed
Corpus successor release:
  0 errors; 541 predecessor-identical warnings
Oracle focused tests:
  53 passed
Oracle affected map:
  167 suites / 176 edges, OK
Oracle vacuous gate:
  OK
Oracle Ruff:
  all checks passed
Oracle live grid:
  8/8 matches, zero mismatches/errors
```

The current `axiom-encode` checkout could not launch its CLI because its local
environment lacks the `receipt` module. This did not hide a module failure:
the signed module is byte-identical to `origin/main`, its manifest guard
passes, and the changed eight-case fixture was run directly through the
released-tag engine.

## Delivery status

All requested work is committed locally on dedicated branches:

- rulespec-us: `y1-employer-medicare`;
- axiom-corpus: `repair/usc-3111-provenance`; and
- axiom-oracles: `evidence/employer-medicare-grid`.

Pushes failed because the environment could not resolve `github.com`. The
draft RuleSpec PR attempt also failed because `api.github.com` was unreachable,
so no PR URL exists. A connected GitHub write fallback was not completed.

Intended draft PR title:

```text
Employer Medicare tax (26 USC 3111(b)): provenance repair and five-criteria evidence
```

Maintainer next steps are to push and review the three branches, sign and merge
the corpus successor, and publish a one-output employer-Medicare artifact
before reconsidering `executable`.
