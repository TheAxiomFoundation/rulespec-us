# B1.4 full-schedule differential

Verdict: **PASS**

- Published modules: 100
- Independently derived rated lines: 13,790
- Published rated-line keys: 13,790
- Matching cells: 48,479 / 48,479
- Missing derived cells: 0
- Extra independently derived rated lines: 0
- Mismatched cells: 0

## Methodology and independence

The B1.4 parser reads the retained, SHA-256-pinned USITC full-schedule JSON bytes directly. It independently selects rate-bearing rows while separating unrated 10-digit statistical children through an indentation-hierarchy walk; constructs zero-padded 10-digit integer keys; parses General and column-2 `Free` and plain ad-valorem rates with exact percent-to-decimal conversion; and classifies both columns into the complete published disposition partition. It then loads every non-test generated module and compares every `values` cell, while separately comparing the independently derived rated-line inventory in both directions.

The two paths share exactly the source snapshot and the published generated module YAMLs used as comparison targets. The differential parser does not read or import the first-path generator, its manifest, reststop JSON, or any other intermediate artifact.
