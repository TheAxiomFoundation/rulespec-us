# Progress

## State

Running repository-wide validation for the completed federal joint-resource,
exclusion, vehicle, and transfer modules.

## Done

- Read the encoder preamble and repository instructions.
- Confirmed the worktree is clean and scoped to the assigned branch.
- Read the required sibling modules and tests and the authoritative
  2026-07-09 corpus text for 7 CFR 273.8.
- Compared the federal provisions with Colorado's resource rules.
- Added federal paragraph (d) joint-resource attribution and tests.
- Added federal paragraph (h) transfer disqualification, duration bands,
  effective-date judgments, and tests.
- Added all twenty paragraph (e) resource-exclusion branches, including
  partial-property valuation under (e)(16), and 30 complete companion cases.
- Passed pinned deterministic validation, proof validation, and companion
  execution for the paragraph (e) module.
- Added paragraph (f)'s fair-market-value and equity tests, vehicle-test
  exemptions, valuation methodology safeguards, and optional TANF-rule
  substitution, with 13 complete companion cases.
- Corrected paragraph (e)(8)'s partial trust-income exclusion and paragraph
  (e)(18)'s alternative relatively-great-selling-cost branch; added the
  explicit documentation, verification, and State-standard duties.
- Added a household relation check for paragraph (f)(2)(ii)'s one-vehicle-per-
  adult cap and narrow deferrals for per-vehicle selection and TANF
  highest-value ranking that current RuleSpec cannot derive.
- Added paragraph (h)(1)'s application inquiry and paragraph (h)(3)'s denial,
  adverse-action, content, and first-allotment notice outputs.
- Replaced the four now-satisfied paragraph (d), (e), (f), and (h) deferrals
  in the top-level section module with narrower household-composition and
  dated-timeline deferrals.
- Passed pinned deterministic validation, proof validation, and companion
  execution for all four new modules: 7 paragraph (d), 38 paragraph (e), 17
  paragraph (f), and 10 paragraph (h) cases.
- Regenerated and verified the provision-to-rule reverse index; the 7 CFR
  273.8 provision now points to all four new modules.

## Next

- Run monetary-proof and repository-wide test suites.
- Generate signed encoding manifests if a signing key becomes available.
- Push the branch and open the required draft PR.

## Concerns

- Paragraph (e)(2) duplicates the label `(iv)`, and its Federal Thrift Savings
  Fund sentence is malformed in the authoritative corpus.
- Paragraph (h)(2)(iv) appears to miscite educational trusts as paragraph
  (e)(9), while the trust conditions are in paragraph (e)(8).
- Paragraph (h)(3) does not state the replacement disqualification start date
  when a participant requests a fair hearing and continued benefits; the new
  paragraph (h) module narrows this to an explicit deferred output.
- Paragraph (f) does not specify which vehicles receive the one-per-adult
  exemption, and current RuleSpec cannot rank related vehicles for paragraph
  (f)(4)(iv)'s highest-value TANF allocation; both unresolved collection-level
  outputs are explicitly deferred.
- Signed encoding manifests require `AXIOM_ENCODE_APPLY_SIGNING_KEY`, which is
  not present in this environment. The manual-exception issue reference does
  not bypass signature generation.
