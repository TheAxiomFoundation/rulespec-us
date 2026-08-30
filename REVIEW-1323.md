# Adversarial review — rulespec-us#1323 (§199A QBI + §1411 NIIT business-income layer)

Independent Fable reviewer, 2026-08-30. Read-only audit of
https://github.com/TheAxiomFoundation/rulespec-us/issues/1323 against `origin/main`
(d58cc0ce6) and linked work (#1052, #1053, #1003, #1004, #1009, #1057, #1179,
axiom-api#208, axiom-rules-engine#155/#115). Every mechanism claim below was
verified this session against repository files, the pinned corpus tree, or the
official USC prelim text; citations inline.

## Findings, ordered by severity

### F1 (BLOCKING — legal defect in the plan itself): acceptance criterion 2 is false as written; §199A(i)(2)(B) ties QBI to §469(h) material participation

Verified against the USC prelim text of §199A(i) (the issue's own primary
source): *"The term 'active qualified trade or business' means … any qualified
trade or business of the taxpayer in which the taxpayer materially participates
(within the meaning of section 469(h))."*

The issue asserts "Section 199A qualified-trade-or-business treatment does not
depend on section 469 material participation." That is true for §199A(d)
classification and false for §199A(i): the post-OBBBA $400 minimum deduction
keys "applicable taxpayer" to aggregate QBI from **materially participating**
businesses. The composed pipeline already consumes this as the opaque input
`aggregate_qualified_business_income_from_active_qualified_trades_or_businesses`
(`us/policies/income_tax/qualified_business_income_deduction_pipeline.yaml:570-575`,
used at `:448` and `:498`).

Consequences for the slice as proposed:

- The paired case "changing material participation changes NIIT classification
  **without changing** otherwise-qualified non-SSTB QBI" fails in the region
  where the §199A(i) floor is live: toggling participation off removes the
  business from the active aggregate; if that drops the aggregate below $1,000
  (single-business slice: it always does), applicable-taxpayer status flips and
  the deduction changes wherever the computed amount is below the floor.
  The invariance criterion must be restated as holding for
  `pipeline_qbi_deduction_before_minimum_active_qbi` (or for fixtures chosen
  outside the floor-binding region), and a **second** paired case must prove
  the floor *does* respond to participation — otherwise the suite will encode
  the pre-OBBBA fiction that §199A is participation-blind.
- If slice 1 derives NIIT passivity from a `materially_participates` fact but
  leaves the §199A(i) active aggregate as an opaque input, the shared-fact goal
  is violated in the exact way the epic exists to prevent: a caller can assert
  participation to §1411 and non-participation to §199A(i). The slice must
  derive both from the one fact.

### F2 (BLOCKING — slice entity form): the "partnership/S-corporation" slice is only honest for an S corporation at current pins; the partnership leg collides with the un-repaired §1411(c)(6) defect and §469(h)(2)

- A materially participating **general partner's** distributive share is
  §1402(a) self-employment income taken into account under §1401(b), hence
  excluded from NII by §1411(c)(6). But the encoded (c)(6) treats exclusions as
  offsets against unrelated income (`us/statutes/26/1411.yaml:190-236`; the
  companion locks the defective $760 expectation at
  `us/statutes/26/1411.test.yaml:92`), and the composed verified domain
  therefore requires `self_employment_income_subject_to_1401_b == 0`
  (`us/policies/income_tax/net_investment_income_tax_pipeline.yaml:156`).
  So the participating side of the participation-toggle pair, built on a
  partnership general partner, is **out of the verified domain** until #1052
  lands — the issue sequences the repair (step 2) but never connects it to the
  feasibility of its own paired case.
- A **limited partner** claiming material participation triggers §469(h)(2)
  (presumptively not participating except as regulations provide, i.e.
  1.469-5T(e)) — machinery nobody proposes to encode in slice 1.
- An **S-corporation shareholder's** K-1 ordinary income is never §1402 SE
  income, sidestepping (c)(6) entirely, and has no §469(h)(2) presumption.

Revision: define slice 1 as *one S-corporation activity*, with
`entity_type != s_corp` fail-closed; partnerships become an explicitly named
follow-on slice gated on the #1052 re-encode and a general/limited fact.

### F3 (BLOCKING — prerequisite): the corpus contains none of the law the classification layer must cite

Verified in the pinned federal corpus (`axiom-corpus/data/corpus/sources/us`):
statute releases carry `usc26-section-199A.xml` and `usc26-section-1411.xml`,
but there is **no §469, no §475, no §162** source file, and
`sources/us/regulation` holds only 42/47/20/7 CFR material — **no 26 CFR
part 1 at all** (no 1.199A-1…-6, no 1.1411-1…-10, no 1.469-4/-5T/-9).
This repo likewise has no `us/statutes/26/469|475|162` modules.

Under the provenance regime every proof atom cites a `corpus_citation_path`;
even the minimal passivity mapping (participation fact → §469(c)(1) status,
rental carve-out §469(c)(2), trading §475(e)(2)) cannot be encoded before
ingest. #1323's delivery sequence has no corpus step. Add step 0: an
axiom-corpus ingest PR pinning at minimum 26 USC 162, 469, 475 and 26 CFR
1.199A-1…-6, 1.1411-1…-10, 1.469-4, 1.469-5T (note -5T is a *temporary*
regulation — the ingest and citation regime must handle the TD-based text).

### F4 (BLOCKING — scope guard): rental per-se passivity and ordinary-course boundaries must be modeled as facts and fail-closed, or slice 1 silently overclaims §469(c)(2)

"Materially participates → non-passive" is §469(c)(1) logic and is **wrong for
rental activities**, which are passive regardless of participation
(§469(c)(2)) outside §469(c)(7). The slice text ("ordinary income" of one
activity) never says the activity-type is a fact. Slice 1 needs
`activity_is_rental` (rental → unevaluable/fail-closed) and the existing
zero-domain gate on `financial_trading_business_income` retained, each with a
companion proving the closure. Same for negative income: a loss at the activity
triggers §199A(c)(2) carryforward and §469(a) disallowance machinery — slice 1
must fail-close on `ordinary_business_income < 0` and prove it, and fix the
ownership share at 100% with any other value fail-closed (otherwise the slice
implicitly claims §704/§1377 allocation).

### F5 (MAJOR — unrecorded defect): 199A `threshold_amount` repeats the status-4 error that #1053 records only for the phase-in width

`us/statutes/26/199A.yaml:308` grants filing status 4 the 200%-of-base joint
threshold; #1053 cites only `qbi_phasein_range` (`:288`). Rev. Proc. 2025-32
§4.26 treats a qualifying surviving spouse as an all-other return (per #1009,
and the pipeline's own correct mapping at
`qualified_business_income_deduction_pipeline.yaml:143`, tested by
`qbid-surviving-spouse-uses-all-other-width`). No composed output is wrong
today because the pipeline shadows the atomic rule (deferral declared at
pipeline `:61-70`), but the #1053 re-encode must cover **both** rules or it
will re-validate a wrong one. Relatedly: the atomic `threshold_amount` has no
§199A(e)(2)(B) COLA machinery and is not declared deferred in the atomic
module — acceptable only while shadowed; the re-encode should declare it.

Counterpoint worth a dedicated test: the NIIT atomic mapping of status 4 to
the joint $250,000 threshold (`us/statutes/26/1411.yaml:118`) is **correct** —
§1411(b)(1) covers "a joint return … or a surviving spouse" while §199A/Rev.
Proc. put surviving spouses in all-other. The two sections genuinely diverge on
the same fact. Add a surviving-spouse paired case proving the divergence; any
temptation toward a shared "filing status → threshold category" abstraction is
legally wrong and this test pins that.

### F6 (MAJOR — architecture): entity/relation machinery exists in RuleSpec but the serving layer cannot yet host it; the epic's attestation-elimination criterion is unachievable as worded

- RuleSpec supports non-TaxUnit entities (946 `entity: Person`, 9
  `entity: Business` uses repo-wide), `data_relation` declarations and
  `sum_where` aggregation over a relation
  (`us/policies/income_tax/salt_deduction_pipeline.yaml:63-71`, `:169`). So a
  Business entity with an ownership relation is *encodable and
  companion-testable* today.
- But axiom-rules-engine#155 (OPEN) documents that compiled artifacts declare
  no entity roster and that axiom-api "collapses every non-Person entity onto
  household:1 — unservable for TaxUnit programs"; engine#115 (pending/derived
  node states) is also OPEN. A Business-entity slice can be green in
  companions/oracles yet unservable. #1323's acceptance criteria are silent on
  serving. Either scope slice 1 explicitly to companion/oracle execution
  (state it as a non-goal), or make engine#155's interface block a named
  prerequisite. Do not let "it compiles and the companions pass" stand in for
  "the app can evaluate it."
- The SALT pattern also shows relations are not closed-world: completeness is
  itself an attestation (`salt_deduction_pipeline.yaml:384`). Criterion 1
  ("outputs no longer depend on … attestations") can therefore never fully
  hold — the disjointness attestation migrates into relation-completeness and
  raw-fact truthfulness. Reword to name the residual attestation surface
  ("the only remaining attestations are X, Y") instead of promising
  elimination; otherwise a future reviewer must either fail the criterion or
  pretend.

### F7 (MAJOR — epic structure): one epic is right, but §469 must be its own workstream, not a limb of the NIIT workstream

One combined epic with a shared fact model is legally and architecturally
sound: the fact graph (activities, ownership, item character, participation,
wages, UBIA) genuinely is shared, and #1323 correctly keeps the predicates
distinct (SSTB must not imply passive; participation must not touch §199A(d)).
But the issue files §469 under the NIIT workstream. After F1, §469(h) is a
dependency of **both** workstreams (§1411(c)(2)(A) and §199A(i)(2)(B)). Encode
§469 classification as a standalone module set with its own companions,
imported by both — otherwise it gets shaped around NIIT's needs and the QBI
minimum-deduction leg re-imports it awkwardly or duplicates it. This is the
one place the epic's "two workstreams" framing must become three.

### F8 (test-plan gaps in the acceptance criteria)

Beyond the paired cases already discussed:

1. **Temporal fail-closure**: every composed rule is pinned 2026-01-01…12-31;
   the atomic 199A module is 2026-only; §199A(i)(3) COLA starts after 2026. No
   criterion requires that a 2027 evaluation be unevaluable rather than
   silently reusing 2026 parameters. Add one.
2. **Below-threshold SSTB invariance**: §199A(d)(3) makes SSTB status
   irrelevant below the threshold. Criterion 3's "SSTB classification changes
   QBI treatment" is only true above it. Require both region cases: SSTB
   toggle at TI < $201,750 (no change — and that *no change* is law), and in
   the phase-in / above the range end (partial / full disqualification).
3. **Mutation specificity**: "off-grid and mutation tests" is generic. Name
   the mutations: participation, SSTB, rental, entity-type, ownership-share,
   filing-status-4, each toggled alone with exact expected deltas *including
   the zero-delta legs* — zero-delta assertions are what catch fact-graph
   cross-contamination.
4. **Match fail-open guard**: the engine lowers a final `match` arm as a
   fallback (documented in this repo's own pipeline summary,
   `qualified_business_income_deduction_pipeline.yaml:41-44`, and #1009). Any
   new enum over participation/entity-type/activity-type needs the enumerated-
   value judgment guard; the criteria should require it for every new enum.
5. **Spine regression**: #1179's `federal_taxable_income` imports the QBI
   final; #1057 is in flight on the §63(b) side. The criterion "existing
   direct QBI and NIIT arithmetic behavior remains covered" should name
   `us/policies/income_tax/taxable_income_pipeline.yaml` explicitly — changing
   the QBI pipeline's input surface ripples into spine companions.
6. **Oracle honesty**: the criteria correctly refuse to treat finite PE grids
   as full-law evidence, but should also require the *new* off-grid cases to
   sit in the interaction region where NIIT thresholds ($200k/$250k MAGI) and
   the QBI phase-in band ($201,750–$276,750 / $403,500–$553,500 TI) are
   simultaneously active, since both now derive from shared income facts.
7. **Waiver hygiene**: both atomic files carry pending validation waivers
   expiring 2026-10-08 (`known-validation-gaps.yaml:15408`, `:15546`, issue
   #782). The #1052/#1053 re-encodes must clear validation, not renew waivers;
   worth stating in the epic so a deadline crunch doesn't produce a renewal.

## Recommended PR sequence

0. **axiom-corpus ingest** (blocking everything): 26 USC 162, 469, 475;
   26 CFR 1.199A-1…-6, 1.1411-1…-10, 1.469-4, 1.469-5T (temporary-reg
   provenance handled). Pinned release, provenance manifests.
1. **PR A — §1411 re-encode (#1052)**: (c)(5)/(6) as domain exclusions rather
   than offsets; (d)(2) limited to AGI-recognized, §911(a)(1)-attributable
   amounts; corrected companions (retire the $760 fixture); NIIT pipeline
   verified-domain guards retained until a follow-up relaxes them with
   fail-closed proofs. No new inputs.
2. **PR B — §199A re-encode (#1053, widened per F5)**: status mapping fixed in
   *both* `qbi_phasein_range` and `threshold_amount`; COLA non-encoding of the
   atomic threshold explicitly declared deferred; status-4 companions on both
   rules.
3. **PR C — axiom-api#208 census** (parallel, read-only): the composed-input
   inventory that makes "which opaque inputs may be retired" a computed answer
   rather than a narrative one.
4. **PR D — §469 classification module** (new, standalone): inputs
   `materially_participates` (raw fact), `activity_is_rental`,
   `is_limited_partner`; output passive/non-passive under §469(c)(1)-(2) and
   (h)(2); rental, limited-partner, and grouping paths fail-closed/deferred;
   enumerated-value guards; companions including the fail-closures.
5. **PR E — the vertical slice**, exact scope:
   - Business/Activity entity (single instance), ownership relation
     TaxUnit↔Business with a completeness judgment; raw facts: `entity_type`
     (S corp only in-domain), `is_sstb`, `materially_participates`,
     `ordinary_business_income` (≥ 0 in-domain), `w2_wages`, `ubia`,
     ownership share fixed at 100%.
   - Derives: per-business QBI under §199A(d)(1)/(d)(3) region logic from the
     SSTB fact; NIIT `passive_activity_business_income` from PR D's status;
     §199A(i) active aggregate from the *same* participation fact (F1).
   - Retires `qualified_business_income`,
     `passive_activity_business_income`, and the disjointness attestation
     **only within this covered domain**; everything else keeps the current
     fail-closed guards.
   - Tests: the four paired cases (participation toggle away from the floor —
     NIIT changes, pre-minimum QBI invariant; participation toggle at the
     floor — QBID changes; SSTB toggle below threshold — invariant; SSTB
     toggle in/above phase-in — changes, NIIT invariant); surviving-spouse
     divergence; every fail-closure of F4; mutation set of F8.3; temporal
     2027 fail-closure; off-grid interaction-region cases; spine regression.
   - Non-goals (state in the PR): partnerships and any §1402 interplay,
     rentals, trading businesses, losses/carryforwards, multiple businesses,
     aggregation (1.199A-4), dispositions (§1411(c)(4)), REIT/PTP/cooperative
     derivation, trusts/estates, §911 interplay, and axiom-api serving of the
     Business entity (engine#155).
6. **PR F+** (later slices, in roughly this order): partnership general/limited
   with §1402 coordination (needs PR A); losses and the §199A(c)(2)
   carryforward; multi-business aggregation and ordering invariance;
   dispositions and the (c)(4) look-through; special entities and elections.

## Verdict

**Approve with named revisions** — the combined epic with distinct legal
predicates is the right structure, the slice is the right shape, and the
fail-closed discipline in the landed foundations (#1003/#1004/#1009) is real
and worth extending. But the plan as written cannot be executed honestly:

- Acceptance criterion 2 contradicts §199A(i)(2)(B) (F1) and must be restated,
  with the active-QBI aggregate derived from the shared participation fact.
- The slice must name the S corporation as its entity form or make #1052 an
  explicit blocker of its own participation pair (F2).
- Corpus ingest of §§162/469/475 and the part-1 regulations is an unstated
  hard prerequisite and must become delivery step 0 (F3).
- Rental, negative-income, ownership-share, and entity-type fail-closures must
  be in the slice's declared scope with tests (F4), the #1053 repair must be
  widened to `threshold_amount` (F5), §469 must be a standalone workstream
  (F7), the attestation-elimination criterion must be reworded to name the
  residual attestation surface, and serving must be scoped out or gated on
  engine#155 (F6).

None of these reject the plan; all of them, left unfixed, would let a
green-looking slice overclaim §469, §1411(c)(6), or the post-OBBBA §199A(i) —
precisely the class of quiet overreach this epic was filed to end.
