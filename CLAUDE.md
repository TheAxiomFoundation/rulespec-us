# rulespec-us Agent Notes

This repo stores US federal RuleSpec encodings and source registry metadata.

## Do

- Put RuleSpec encodings under `statutes/`, `regulations/`, or `policies/`.
- Put tests beside each encoding as `.test.yaml`.
- Keep only source registry or manifest metadata under `sources/` when needed.

## Do Not

- Add singular rule roots, separate parameter/test fixture files, or generated formula artifacts.
- Put unrelated jurisdiction materials here.
- Add generated source payloads to Git.

## Versions and effective dates

- A rule's `versions[]` is the history of the law, not the history of the file.
  When an amendment changes a rule, **append a version** and close the previous
  one with `effective_to`. Never edit an existing version's `formula`, `values`,
  or `effective_from` to reflect a change in the law (#1310).
- Editing a version in place is correct only to fix an *encoding* error — a date
  or value that was always wrong. Say so in the commit, and name the rule.
- `effective_from` is the date the *provision as written* began to apply, not:
  - the date the surrounding subsection was enacted (an amended value inside a
    long-lived subsection has its own, later date — #1319);
  - a compliance or implementation deadline;
  - the date you encoded it.
- `effective_from` and `effective_to` are **inclusive**. Statutory language of the
  form "after December 31, 2026" means `effective_from: 2027-01-01` (#1320).
  "The first day of the first quarter that begins after December 31, 2026" is
  January 1, 2027, not April 1.
- Prefer a real date to a placeholder. Do not write `0001-01-01` for "unknown" —
  it makes the rule answer as in force for all of history (#1322).
- Cite the amending instrument on the version it produced (`source:` on the
  version; the key parses today and the API reads it as version-level
  provenance), and anchor a proof atom on each `versions[i].formula`.
- Derived rules cannot yet carry more than one version
  (axiom-rules-engine#133, #64). When an amendment changes a derived rule's
  logic, date the new version from the amendment and let earlier periods stay
  unresolved — a fail-closed answer is preferable to a confidently wrong one.
