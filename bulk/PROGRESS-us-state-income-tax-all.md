# US state individual-income-tax completion campaign

Mission: cover every jurisdiction-level individual-income-tax liability surface
implemented by the pinned PolicyEngine-US oracle with a source-grounded RuleSpec
liability pipeline and an independent comparison suite. Corporate income taxes
are out of scope. Alaska, Florida, Nevada, South Dakota, Tennessee, Texas, and
Wyoming have no broad PolicyEngine-US individual-income-tax liability surface
and are not counted in the 44-jurisdiction universe.

## Baseline (2026-07-15)

- PolicyEngine-US jurisdiction income-tax surfaces: **44**.
- Standardized RuleSpec pilot pipelines and 6-case PolicyEngine suites: **20**
  (AL, AZ, CA, CT, DE, GA, ID, IL, KY, MA, MD, ME, MI, MN, NC, NE, NY, OH,
  UT, VA). Every committed Axiom-versus-PolicyEngine grid is 6/6.
- Colorado has separate ECPS/TAXSIM bridge coverage and extensive Title 39
  encodings. It is counted covered, but not as a standardized pilot.
- This campaign added source-grounded pilots for **23** jurisdictions (AR, DC,
  HI, IA, IN, KS, LA, MO, MS, MT, ND, NH, NJ, NM, OK, OR, PA, RI, SC, VT, WA,
  WI, WV), bringing liability comparison coverage to **44 of 44** jurisdictions
  when Colorado is included.
- No jurisdiction-level liability comparison remains.

The standardized pilots are deliberately narrow resident wage-earner core-
liability grids. They do not claim full-return coverage for every credit,
deduction, local tax, or special income class.

## Current execution batches

| Batch | Jurisdictions | State |
| --- | --- | --- |
| East | DC, HI, IA, IN, LA | 5 pilots; proof/test/PE parity green |
| Central | MT, NM, OK, OR, RI | 5 pilots; proof/test/PE parity green |
| West | WA, WI | 2 pilots; proof/test green |
| Source-ready follow-on | AR, KS, MO, MS, ND, NH, NJ, PA, SC, VT, WV | 11 pilots; proof/test green; oracle residuals typed below |
| Source/vintage blockers | None | campaign liability grid complete |

Each candidate must use a primary-source corpus citation or an explicit hashed
RuleSpec import, carry a companion test, reproduce the selected PolicyEngine
2026 target on the standard six-case grid, and complete the independent
review/fix cycle before merge. Missing authority is a typed blocker, never
permission to supply invented law.

The 23 new pipelines pass 139/139 engine companion cases. Nineteen reproduce
their selected PolicyEngine 2026 target on 6/6 cases. Kansas matches its closest
target within one cent on 6/6; PolicyEngine starts its upper marginal brackets
one dollar above the statutory cumulative-base floors. Missouri follows the
Department of Revenue's official 2026 schedule and matches its closest target
within $1 on 6/6; PolicyEngine's modeled uprating produces nonofficial 2026
thresholds and a roughly $0.563 residual. Wisconsin deliberately follows the
post-2024 statutory bases, actual August 2024-to-August 2025 CPI-U change, and
required $10 rounding; it matches PolicyEngine within $1 on 2/6 cases and
records the other four as dispositioned upstream stale/unrounded-oracle gaps.
North Dakota follows the Tax Commissioner's official 2026 schedule overlay;
three zero cases match, while three positive cases expose PolicyEngine's
carried-forward 2025 thresholds. New Hampshire encodes the Chapter 77 repeal
result, rather than a fictional active zero-rate schedule. West Virginia adds
one non-oracle 2027 boundary case so section 4J cannot be silently carried past
the section 4H trigger. Vermont follows the section 5822 statutory rates and
annual inflation authority using supplied current 2026 indexed thresholds; its
six cases match PolicyEngine at return-cent precision. The independent
review/fix cycle completed across the east, central, and west batches; the
AR/KS/MO/MS/ND/NH/NJ/PA/SC/VT/WV follow-on remains subject to the full-PR cycle
before merge.

There are no remaining jurisdiction-level liability-grid blockers.

## Corpus source-recovery blocker

The signed v2 release `us-rulespec-2026-07-16` is active with content SHA-256
`33ba06e3f3b62df2fd623669de0b14534dade2631b410be325f1465ff5f7f0bc` and
signed corpus provenance `21d898b8ad07f6f7a27b63b8190d76866ad14348`.
Its public object verifies, exposes US state statutes, and restores the
Michigan `206.30/2` fragment that was previously unavailable.

The release is only a partial unblock for this campaign: strict CI resolves 3
of the 43 citations used by the 23 pilots. Source verification still lacks
these 40 active citation paths:

- AR `act-2-2026` and `act-2-2026/section-1`;
- DC `47-1801.04`;
- HI `235-51` and `235-2.4`;
- IA `422.5` and `422.7`;
- IN `6-3-2-1` and `6-3-1-3.5`;
- KS `79-32-110`, `79-32-110c`, and `79-32-116`;
- LA `47:32`;
- MO `143.011` and `143.021`;
- MS `27-7-5`;
- MT `15-30-2103`;
- ND `57/57-38-30.3`;
- NH `title-v` and `chapter-77`;
- NJ `54a:2-1`;
- NM `7-2-7`;
- OK `68-2355`;
- OR `316.037`;
- PA `act-1971-2/article-3/section-302`;
- RI `44-30-2.6`;
- SC `12-6-510`;
- VT `title-32`, `chapter-151`, `32-5811`, `32-5822`, and `32-5823`;
- WA `82/82.87/82.87.040`, `82/82.87/82.87.060`, and
  `82/82.87/82.87.080`;
- WI `71.06`; and
- WV `chapter-11/article-21`, `11-21-3`, `11-21-4H`, and `11-21-4J`.

Corpus integration now contains body-bearing official recovery for Arkansas
Act 2 of 2026 and its canonical section 1, Kansas `79-32-110`, `79-32-110c`,
and `79-32-116`, Mississippi `27-7-5`, North Dakota
`57/57-38-30.3` with the Tax Commissioner's 2026 schedule overlay, the
canonical New Hampshire Title V root and body-bearing repealed Chapter 77, New
Jersey `54a:2-1`, Missouri
`143.011` and `143.021` with the Department of Revenue's 2026 schedule overlay,
Pennsylvania `act-1971-2/article-3/section-302`, South Carolina `12-6-510`,
Vermont's canonical Chapter 151 roots and body-bearing sections 5811, 5822, and
5823 with the 2026 Act 152 and Act 164 overlays, the canonical dotted
Washington RCW provisions, and West Virginia's complete Article 21 package
including sections 3, 4H, and 4J. Strict RuleSpec CI will remain blocked until
those recoveries are included in a reviewed, signed successor corpus release.

The RuleSpec PR must remain draft until these primary-source provisions are
recovered into a reviewed, signed successor release and strict source
validation passes. Existing supplied-current-authority composition modules
remain structurally testable, but they do not replace the missing atomic
statute encodings.

## Required closeout gates

1. Land the 23 source-grounded liability candidates and companion tests.
2. Sign composition candidates through the reviewed manual-exception path;
   regenerate the reverse index and oracle-pending declaration centrally.
3. Add PolicyEngine/TAXSIM comparison suites and conformance rows in
   `axiom-oracles`; disposition only documented vintage/scope differences.
4. Restore atomic statute encoding after the US named-release repair and drain
   the remaining source-backed worklist.
5. Run focused tests, repository-wide validation, and the mandatory independent
   review/fix cycle. Do not merge with red, stale, or pending CI.
