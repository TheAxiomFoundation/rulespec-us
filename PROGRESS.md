# SCRETD certification assessment progress

## State

Assessment written. The program is provision-rooted, but it is not currently
certifiable: its signed executable root omits the statutory household-income
qualification, corpus closure is incomplete, no live case-grid receipt exists,
and no published compiled artifact has been exercised.

## Done

- Read the encoder preamble, repository rules, and required sibling RuleSpec
  conventions.
- Confirmed the program declares one output:
  `il_scretd_deferral_amount`.
- Confirmed that output is defined only by
  `us-il/statutes/320/30/3.yaml`, with source
  `Sec. 3, application paragraph and clause (1)`.
- Confirmed the program contains no `transformations:` block and does not
  resolve the output through `policies/`.
- Scanned all 728 axiom-corpus inventory files by each record's
  `citation_path` (143,788 records), never by inventory filename.
- Confirmed the 320 ILCS 30 ingest contains the act container and all eight
  sections. Its signed manifest is `complete: true` for the explicitly scoped
  `--only-chapter 320 --only-act 30` ingest only.
- Established the conservative closure census over §§ 1–8:
  **0 encoded / 5 excludable / 3 pending**. Sections 1 and 5–8 are
  content-grounded exclusions; §§ 2–4 remain pending.
- Confirmed that no inventory record covers the outgoing citation paths
  320 ILCS 25/3.05, 3.05a, or 3.07; 35 ILCS 200/15-172; or
  210 ILCS 45/1-113.
- Traced the composed dependency graph and found that
  `il_scretd_deferral_amount` does not consume `qualified_taxpayer` or
  `household_income_no_greater_than_maximum`, even though § 2 defines the
  $77,000 qualification for 2026.
- Confirmed PolicyEngine applies age ≥ 65, income ≤ $77,000, and a $7,500
  annual cap, but omits Axiom's application, property, funding, agreement,
  requested-amount, and equity constraints. The existing oracle bridge
  therefore classifies the surfaces as not comparable.
- Designed a five-case, non-population 2026 boundary grid. Current RuleSpec
  agrees with PolicyEngine on four cases and wrongly pays $7,500 at
  household income $77,001.
- Composed and compiled the program locally. The local engine version differs
  from the repository's pinned engine, so this is diagnostic evidence rather
  than an executable-verdict receipt.
- Repeated focused validation in isolated checkouts at the repository's pinned
  axiom-encode and axiom-rules-engine commits. The current 2 companion files /
  10 cases pass and the composed program has 15 rules.
- Tested the proposed income edge and five-case grid in an isolated checkout:
  without the edge, only the $77,001 case fails; with the edge, all 15
  § 2 + § 3 cases pass.
- Did not commit the semantic repair because the protected § 3 module and test
  are bound by a signed apply manifest. An authorized signed encoder apply is
  required; manual changes would be unshippable.
- Wrote the complete assessment and golden case to
  `bulk/us-il-scretd-certification-assessment.md`.
- Passed the focused non-population repository suite: 15 tests across program
  specs, repository layout, and signed encoding manifests.

## Next

- Copy the committed assessment to the requested closure-sprint output path.
- Push and open only a draft PR if network access permits.
