# B3 G1 witness-slice rerun after B1 primary-scope repair

Source replay logic: `~/PolicyEngine/_tariff-p5/b16/eval/build_b16.py`, G1
witness slice only, with the repaired primary-or-derivative aluminum feed for
`entry_is_line_b`. Run against rules commit `23a4ec26e`.

| HTS10 | Expected exemplar | Membership-derived true flags | Exclusive-slot result |
|---|---|---|---|
| 7202111000 | line_a | line_a | PASS |
| 7601103000 | line_b | line_b (`s232_aluminum_primary`) | PASS |
| 9506624040 | line_c | line_c | PASS |
| 2203000030 | line_d | line_a (`china_301_list3`) and line_d (exact beer exemplar) | FAIL |
| 8541420010 | line_e | line_e | PASS |

Verdict: **FAIL (4/5 exclusive-slot witness rows pass), but the reported B1
coverage defect is repaired: 7601.10.30.00 now activates line_b from note
19(b) primary membership.** The sole remaining failure is exemplar coupling,
not a legal-membership error. Beer 2203.00.00.30 is both a China List 3 member
and the exact beer exemplar, so lawfully derived line_a and exact line_d are
both true; B3's mutually exclusive witness slots are the artifact.

Formula receipts:

- `ch76.yaml`, `section_232_aluminum_component_rate`, line 2880: `elif
  entry_is_line_b:` selects the applicable aluminum section 232 rate.
- `ch22.yaml`, `china_section_301_component_rate`, lines 3094–3097: the formula
  independently adds `(if entry_is_line_a and origin_is_china: ...)` and `(if
  entry_is_line_d and origin_is_china: ...)`. Thus both true inputs are
  observable and cannot honestly be forced into one exclusive witness slot.
