# EITC golden case: two children, tax year 2026

This is a hand-checkable arithmetic case for the encoded section 32 output. It
is not a closure certificate: the assessment documents legal conclusions that
still enter the graph as frontier inputs.

## Facts and declared bridges

- The taxpayer files a non-joint return and is not married under 26 USC
  7703(a).
- Two eight-year-old children are related to the taxpayer, reside with the
  taxpayer all year in the United States, do not file disqualifying joint
  returns, satisfy the section 152(c) tiebreaker path, and have the required
  names, ages, and Social Security numbers on the return.
- Employee compensation includible in gross income is **$28,890**. Net
  self-employment earnings and every section 32(c)(2) exclusion are zero, so
  encoded earned income is **$28,890**.
- Adjusted gross income is supplied as the explicitly declared,
  evidence-free bridge at **$28,890**.
- Section 32(i)(2) investment income is supplied as **$0**. This assembled
  amount is one of the additional unencoded legal quantities identified in
  the assessment.
- The taxpayer has the required Social Security number, does not claim section
  911 benefits, is not a nonresident alien or another taxpayer's dependent or
  qualifying child, has no section 32(k) disallowance, and otherwise satisfies
  the supplied eligibility conclusions.

## Statutory derivation

1. Each child's facts satisfy the reached section 152(c) relationship, abode,
   age, joint-return, and tiebreaker rules. The section 32(c)(3) additions are
   also satisfied. Therefore `eitc_child_count = 2` and
   `eitc_capped_child_count = 2`.
2. Section 32(c)(2) produces earned income of
   **$28,890 + $0 - $0 = $28,890**.
3. For two qualifying children, 26 USC 32(b)(1) supplies a **40%** credit
   percentage and a **21.06%** phaseout percentage.
4. Rev. Proc. 2025-32 section 3.06(1), implementing the section 32(j)
   inflation adjustment, supplies the 2026 two-child values: earned-income
   amount **$18,290**, maximum credit **$7,316**, and non-joint phaseout start
   **$23,890**. The rate calculation agrees exactly:
   `40% × $18,290 = $7,316`.
5. Under section 32(a)(1), earned income exceeds the earned-income amount, so
   the phased-in credit is the maximum: **$7,316**.
6. Under section 32(a)(2)(B), phaseout income is the greater of AGI and earned
   income: `max($28,890, $28,890) = $28,890`.
7. Income above the phaseout start is
   **$28,890 - $23,890 = $5,000**.
8. The phaseout reduction is
   **21.06% × $5,000 = $1,053**.
9. Section 32(a) limits the amount to
   `max($0, min($7,316, $7,316 - $1,053)) = $6,263`.
10. The supplied demographic and identification conditions hold, and
    investment income **$0** does not exceed the 2026 section 32(i) limit of
    **$12,200** published in Rev. Proc. 2025-32 section 3.06(2).

The encoded output is therefore:

```text
eitc = $6,263
```

Every multiplication in this example is exact, so the result does not depend
on an unstated rounding convention or on the deferred section 32(f) credit
table.
