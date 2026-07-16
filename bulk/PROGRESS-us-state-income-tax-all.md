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
- This campaign added source-grounded pilots for **20** jurisdictions (AR, DC,
  HI, IA, IN, KS, LA, MO, MS, MT, ND, NJ, NM, OK, OR, PA, RI, SC, WA, WI),
  bringing liability comparison coverage to **41 of 44** jurisdictions when
  Colorado is included.
- No liability comparison remains for **3** jurisdictions (NH, VT, WV).

The standardized pilots are deliberately narrow resident wage-earner core-
liability grids. They do not claim full-return coverage for every credit,
deduction, local tax, or special income class.

## Current execution batches

| Batch | Jurisdictions | State |
| --- | --- | --- |
| East | DC, HI, IA, IN, LA | 5 pilots; proof/test/PE parity green |
| Central | MT, NM, OK, OR, RI | 5 pilots; proof/test/PE parity green |
| West | WA, WI | 2 pilots; proof/test green |
| Source-ready follow-on | AR, KS, MO, MS, ND, NJ, PA, SC | 8 pilots; proof/test green; oracle residuals typed below |
| Source/vintage blockers | NH, VT, WV | typed below |

Each candidate must use a primary-source corpus citation or an explicit hashed
RuleSpec import, carry a companion test, reproduce the selected PolicyEngine
2026 target on the standard six-case grid, and complete the independent
review/fix cycle before merge. Missing authority is a typed blocker, never
permission to supply invented law.

The 20 new pipelines pass 120/120 engine companion cases. Sixteen reproduce
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
carried-forward 2025 thresholds. The independent review/fix cycle completed
across the east, central, and west batches; the AR/KS/MO/MS/ND/NJ/PA/SC follow-on
remains subject to the full-PR cycle before merge.

The remaining typed blockers are:

- VT: operative rate citation absent under the staged deterministic identifier
  checked.
- NH: source queue marked `blocked_primary_source`; the tax is also repealed and
  zero at 2026, so a vacuous zero pilot is not acceptable.
- WV: existing signed modules omit the operative 2026 rate schedule; staged
  section 11-21-4e/4j still requires verified primary text.

## Corpus source-recovery blocker

The signed v2 release `us-rulespec-2026-07-16` is active with content SHA-256
`33ba06e3f3b62df2fd623669de0b14534dade2631b410be325f1465ff5f7f0bc` and
signed corpus provenance `21d898b8ad07f6f7a27b63b8190d76866ad14348`.
Its public object verifies, exposes US state statutes, and restores the
Michigan `206.30/2` fragment that was previously unavailable.

The release is only a partial unblock for this campaign: strict CI resolves 3
of the 32 citations used by the 20 pilots. Source verification still lacks
these 29 active citation paths:

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
- NJ `54a:2-1`;
- NM `7-2-7`;
- OK `68-2355`;
- OR `316.037`;
- PA `act-1971-2/article-3/section-302`;
- RI `44-30-2.6`;
- SC `12-6-510`;
- WA `82/82.87/82.87.040`, `82/82.87/82.87.060`, and
  `82/82.87/82.87.080`; and
- WI `71.06`.

Corpus integration now contains body-bearing official recovery for Arkansas
Act 2 of 2026 and its canonical section 1, Kansas `79-32-110`, `79-32-110c`,
and `79-32-116`, Mississippi `27-7-5`, North Dakota
`57/57-38-30.3` with the Tax Commissioner's 2026 schedule overlay, New Jersey
`54a:2-1`, Missouri `143.011` and `143.021` with the Department of Revenue's
2026 schedule overlay, Pennsylvania `act-1971-2/article-3/section-302`, South
Carolina `12-6-510`, and the canonical dotted Washington RCW provisions. Strict
RuleSpec CI will remain blocked until those recoveries are included in a
reviewed, signed successor corpus release.

The RuleSpec PR must remain draft until these primary-source provisions are
recovered into a reviewed, signed successor release and strict source
validation passes. Existing supplied-current-authority composition modules
remain structurally testable, but they do not replace the missing atomic
statute encodings.

## Required closeout gates

1. Land the 20 source-grounded liability candidates and companion tests.
2. Sign composition candidates through the reviewed manual-exception path;
   regenerate the reverse index and oracle-pending declaration centrally.
3. Add PolicyEngine/TAXSIM comparison suites and conformance rows in
   `axiom-oracles`; disposition only documented vintage/scope differences.
4. Restore atomic statute encoding after the US named-release repair and drain
   the remaining source-backed worklist.
5. Run focused tests, repository-wide validation, and the mandatory independent
   review/fix cycle. Do not merge with red, stale, or pending CI.
