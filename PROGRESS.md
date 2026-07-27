# 7 CFR 273.11 remainder encoding

## State

- Branch: `encode-273-11-remainder`
- Base: `origin/main` at `1158ba5b2`
- Claim: `rulespec-us#1135`
- Scope: encode the point-in-time computational remainder of 7 CFR 273.11,
  preserving the existing paragraph (c) module and classifying purely
  procedural paragraphs for follow-up.
- Source: `us/regulation/7/273/11` in
  `_closure-sprint/data/cfr-273.jsonl` (source as of 2026-07-09).
- Worktree was clean at task start.

## Done

- Read the repository `CLAUDE.md`; it references no additional agent or
  contribution instructions.
- Read the existing `273/11/c.yaml` and companion test.
- Read `273/9.yaml` and `273/10.yaml` for SNAP income and allotment conventions.
- Read the complete cited source text for 7 CFR 273.11(a)-(s).

## Next

- Classify each paragraph as encoded in this change, already encoded, deferred
  for a state-option dependency, or skipped as procedural/out of the claimed
  special-population scope.
- Design one focused RuleSpec module and companion test per encoded paragraph
  or coherent subparagraph.
- Validate each coherent implementation step with the repository tooling.
- Run the full relevant local checks, finalize this progress record and the
  requested output report, then push and open an unmerged PR referencing #1135.
