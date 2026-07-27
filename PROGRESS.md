# SCRETD certification assessment progress

## State

Premise verified. The program is provision-rooted, but it is not currently
certifiable: its executable root omits the statutory household-income
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

## Next

- Record the closure ledger and five-case grid contract in repository
  assessment evidence without claiming a false comparable bridge.
- Write the hand-checkable golden case and explicit defect statement.
- Run safe repository checks (never a population-backed oracle suite).
- Write the requested external assessment, commit the final evidence, push,
  and open only a draft PR if network access permits.
