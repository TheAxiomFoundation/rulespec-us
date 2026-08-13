# B1.3 all-chapter structure audit

Verdict: **PASS**

- Inventory: 100 compositions, 100 companion tests, and 100 program specs for chapters 01–76, 78–98, and 99a/99b/99c.
- Each composition has the chapter table plus the witness's 87 overlay imports; each program has the exact resulting 89-module scope.
- Each companion has 97 deterministic cases. Ninety-nine compositions have 115 rules; chapter 76 has one additional proved local Russian-base parameter and therefore 116.
- Chapter 99a and 99b have no flat column-2 table because every source cell is conditional or specific. Their `schedule_column2_flat_rate` output is explicitly deferred and their column-2 selector requires the caller's resolved non-ad-valorem rate; it never substitutes zero or General.
- Elsewhere, disposition-only lines are deliberately absent from flat-rate maps. A missing key remains structurally unavailable and is never read as a silent zero.
- Repository layout/program tests: 12 passed.
