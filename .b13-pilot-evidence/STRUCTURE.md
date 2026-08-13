# B1.3 chapter-72 structure audit

Verdict: **PASS**

- Composition imports: 88 total = one chapter table plus the witness's same 87
  overlay modules in the same order.
- Legacy witness line imports: none.
- Local rules: 115, including the three requested schedule table surfaces,
  the General Note 3 base selector, all 11 requested component/entry-variant
  surfaces, their witness dependency closure, and the statutory stack.
- All 11 component formula strings are exactly equal to the witness strings.
- After normalizing `from`/`to` to their schema-equivalent
  `effective_from`/`effective_to` spelling, all 11 component rule objects are
  equal to the witness objects (formulas, inputs, dates, source, and proofs).
- Companion cases: 97; every local derived output is asserted, every
  non-constant Judgment output has a positive oracle, and zero branches have
  zero-output coverage.
- Program scope: 89 modules = the exact 88 imports plus the generated
  composition.
- Only chapter 72 was emitted.
- The chapter sampler found a safe General-rate oracle cell in all 97 unsplit
  chapter modules; representative in-memory generation for chapters 01, 73,
  and 98 produced all nine selected composition/test/program outputs without
  writing them.

The raw General rate surface is deliberately a direct table lookup:
`ch72_general_rate[hts_line]`. Callers must query it only for `ad_valorem` or
`free` dispositions. An absent table key raises a lookup error by design and is
never interpreted as zero.
