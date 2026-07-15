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
- This campaign added source-grounded pilots for **12** jurisdictions (DC, HI,
  IA, IN, LA, MT, NM, OK, OR, RI, WA, WI), bringing liability comparison
  coverage to **33 of 44** jurisdictions when Colorado is included.
- No liability comparison remains for **11** jurisdictions (AR, KS, MO, MS,
  ND, NH, NJ, PA, SC, VT, WV).

The standardized pilots are deliberately narrow resident wage-earner core-
liability grids. They do not claim full-return coverage for every credit,
deduction, local tax, or special income class.

## Current execution batches

| Batch | Jurisdictions | State |
| --- | --- | --- |
| East | DC, HI, IA, IN, LA | 5 pilots; proof/test/PE parity green |
| Central | MT, NM, OK, OR, RI | 5 pilots; proof/test/PE parity green |
| West | WA, WI | 2 pilots; proof/test green |
| Source/vintage blockers | AR, KS, MO, MS, ND, NH, NJ, PA, SC, VT, WV | typed below |

Each candidate must use a primary-source corpus citation or an explicit hashed
RuleSpec import, carry a companion test, reproduce the selected PolicyEngine
2026 target on the standard six-case grid, and complete the independent
review/fix cycle before merge. Missing authority is a typed blocker, never
permission to supply invented law.

The 12 new pipelines pass 72/72 engine companion cases. Eleven reproduce their
selected PolicyEngine 2026 target on 6/6 cases. Wisconsin deliberately follows
the post-2024 statutory bases, actual August 2024-to-August 2025 CPI-U change,
and required $10 rounding; it matches PolicyEngine within $1 on 2/6 cases and
records the other four as dispositioned upstream stale/unrounded-oracle gaps.
The independent review/fix cycle completed with no actionable findings across
the east, central, and west batches.

The remaining typed blockers are:

- AR and MS: legacy, unreviewed Supabase-only authority.
- KS, PA, and VT: operative rate citation absent under the staged deterministic
  identifiers checked.
- MO and NH: source queue marked `blocked_primary_source`; NH is also repealed
  and zero at 2026, so a vacuous zero pilot is not acceptable.
- ND and SC: staged rate schedule is stale against the 2026 law/oracle target.
- NJ: staged rate provision has a null body.
- WV: existing signed modules omit the operative 2026 rate schedule; staged
  section 11-21-4e/4j still requires verified primary text.

## Corpus publication blocker

The 2026-07-10 named-release migration intentionally deleted legacy release
membership before activating the new v2 release model. The active public
`corpus.current_provisions` view now contains named-release scopes but no US
state-statute scope. The underlying versioned state-statute rows remain staged
in `corpus.provisions` for productionized states, but the legacy pinned encoder
resolves only the active public view.

Consequences observed in this campaign:

- SS1 Michigan fragment attempts stopped before model generation because
  neither `us-mi/statute/206.30/<fragment>` nor its parent was active.
- Atomic `encode --apply` work must wait for a reviewed, signed v2 US corpus
  release (or an equivalent approved release repair).
- Existing supplied-current-authority composition modules remain structurally
  testable and are the established path used by the AZ/GA/MI/NC pilots, but
  they do not replace the missing atomic statute encodings.

## Required closeout gates

1. Land the 12 source-grounded liability candidates and companion tests.
2. Sign composition candidates through the reviewed manual-exception path;
   regenerate the reverse index and oracle-pending declaration centrally.
3. Add PolicyEngine/TAXSIM comparison suites and conformance rows in
   `axiom-oracles`; disposition only documented vintage/scope differences.
4. Restore atomic statute encoding after the US named-release repair and drain
   the remaining source-backed worklist.
5. Run focused tests, repository-wide validation, and the mandatory independent
   review/fix cycle. Do not merge with red, stale, or pending CI.
