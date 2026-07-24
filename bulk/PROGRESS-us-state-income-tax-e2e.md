# US resident state income-tax end-to-end campaign

Mission: extend the 44 jurisdiction-level individual-income-tax schedule
pipelines into source-grounded tax-year 2026 resident-liability programs. The
program boundary begins with federal return outputs and raw taxpayer facts and
ends with state income tax after refundable and nonrefundable credits, before
payments.

The earlier 44-jurisdiction campaign remains useful schedule coverage, but its
completed-return inputs (for example, completed state taxable income or a
caller-supplied state credit) are not an end-to-end boundary.

## Liability contract

Every completed jurisdiction program with an imposed individual income tax
must expose these semantic stages, using jurisdiction-prefixed RuleSpec output
names:

1. state income or adjusted gross income after state additions and
   subtractions;
2. state taxable income after the encoded deduction and exemption rules;
3. tax before credits, including ordinary schedules and applicable surtaxes;
4. tax after nonrefundable credits, floored at zero unless the controlling
   authority provides a different ordering rule; and
5. net state income-tax liability after refundable credits and before
   withholding, estimated payments, extensions, penalties, interest, and
   refunds of payments.

The final stage may be negative when refundable credits exceed pre-credit tax.
Each program manifest must expose the final output without listing it under
`acknowledged_incomplete`.

A jurisdiction whose individual income tax has been repealed or does not exist
must not invent zero-dollar state-income or state-taxable-income concepts. Its
program instead exposes the applicable liability stages and must prove from
current authority that no resident individual income tax is imposed throughout
the program period. The source and eval gates still apply, including a
positive-control oracle probe when an oracle retains a disabled legacy model.

### Allowed caller inputs

- federal return outputs whose federal computation is outside the state
  program, such as federal adjusted gross income, federal taxable income,
  federal itemized deductions, and federal credit amounts when state law
  explicitly uses them;
- filing status, ages, disability or blindness facts, dependent and qualifying
  child facts, residency facts fixed to the full-year-resident program scope,
  and other raw eligibility facts;
- raw income, loss, expense, contribution, and transaction facts needed by a
  state-specific addition, subtraction, deduction, exemption, surtax, or
  credit.

### Prohibited completion shortcuts

A program is not end to end if it requires a caller to supply:

- completed state adjusted gross income or state taxable income;
- a completed state deduction, exemption, surtax, or credit amount;
- a state tax rate, bracket, threshold, phaseout, or indexed parameter; or
- tax before or after credits.

An explicitly named federal output remains allowed even when a state form
copies that amount onto a state line. State parameters must come from encoded
official authority, including the operative tax-year inflation adjustment.

## Scope

Included: full-year resident individual returns; state additions and
subtractions; standard/itemized deductions; exemptions; ordinary income-tax
schedules; state surtaxes; and refundable and nonrefundable state income-tax
credits.

Excluded unless required to determine state liability: withholding, estimated
payments, extension payments, filing and collection administration, penalties,
interest, local income taxes, nonresident sourcing/allocation, part-year
allocation, and corporate or pass-through-entity-level taxes.

## Completion gates

A jurisdiction is complete only when all of the following are true:

1. operative TY2026 official sources are present in the pinned corpus;
2. the RuleSpec program satisfies the input and output contract above;
3. focused tests cover every material stage, filing-status path, threshold
   boundary, credit ordering rule, and refundable-credit sign behavior;
4. a PolicyEngine, TAXSIM, official example, or independently calculated eval
   suite is recorded, with source/oracle differences dispositioned rather than
   hidden; a repealed/no-tax surface may instead carry a typed oracle exclusion
   backed by a positive pre-repeal activation control and post-repeal zero
   probes;
5. strict source, proof, compile, and repository validation pass against the
   pinned toolchain; and
6. the mandatory independent review/fix cycle ends with no actionable finding.

Missing TY2026 authority is a typed source hold. It is never permission to use
a projected parameter as law or to mark a partial program complete.

## Progress

| Jurisdiction | State | Notes |
| --- | --- | --- |
| NH | complete | RSA Chapter 77 was repealed effective 2025-01-01, so state-income and taxable-income stages are legally inapplicable. The TY2026 program has no taxpayer inputs and returns zero at each applicable liability stage. `axiom-oracles` records the typed `oracle_models_repealed_law` exclusion and a positive 2024 interest/dividend activation control followed by exact-zero 2025/2026 probes. |
| Remaining 43 | audit/implementation | Schedule pilots exist; upstream state base construction and/or credit surfaces remain to be encoded. |

The first nonzero implementation lanes are selected by source readiness rather
than alphabetical order:

| Lane | Jurisdictions | Readiness |
| --- | --- | --- |
| Source-rich first wave | GA, NC, PA, MO, LA, DE, IA, WV, OK | Core statutes and the operative 2026 rate regime are present; ingest or verify the final-return instructions and credit schedules as each state starts. |
| Source-rich follow-on | RI, MT, ND, NJ, HI, OR, SC, WI | Broad governing chapters are present, but the return chain or credit surface is larger. |
| Partial-source buildout | AL, AR, AZ, CA, CT, DC, IL, IN, KS, KY, MA, MD, ME, MI, MN, MS, NE, NM, NY, OH, UT, VA | Important rate modules exist; additional statutes, forms, instructions, or indexed parameters are needed before completion. |
| Explicit 2026 publication hold | CO, ID, VT, WA | A revenue-triggered rate/refund determination or official 2026 indexed parameter remains unpublished or absent from the pinned official corpus. |

These lanes are planning order, not reduced scope. A source-rich state remains
incomplete until specialty income, deductions, exemptions, surtaxes, and all
applicable refundable and nonrefundable income-tax credits satisfy the
completion gates.
