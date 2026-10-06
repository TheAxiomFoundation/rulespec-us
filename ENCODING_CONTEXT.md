# 31 U.S.C. § 1352 base-module encoding contract

Encode only the current normalized official corpus unit `us/statute/31/1352` into the canonical `us/` rules root. Generate the RuleSpec and its companion fixtures; do not hand-author or repair either artifact.

## Temporal contract

- The normalized provision records expose `expression_date` and `source_as_of` as `2026-07-12`; the separately supplied `Primary source continuation` reproduces the official USLM effective-date and amendment notes from the same corpus source.
- The base section applies to listed instruments entered into or made more than 60 days after `1989-10-23`, so the first covered date is `1989-12-23`. Do not use `1989-10-23` itself as the effective date.
- The current subsection (b)(2)(A) LDA-registrant disclosure wording and current subsection (b)(2)(B) placement became effective `1996-01-01`. Do not backdate the current registrant-contact disclosure to 1989.
- The current subsection (d) and (g) labels resulted from the same 1995 redesignation effective `1996-01-01`; do not assert current-subsection provenance before that date unless the historical former-subsection path is separately represented.
- Before each atom's supported effective date, every affirmative obligation/compliance judgment must fail closed through a false sentinel or an equivalent faithful dated mechanism.
- If the supplied primary-source continuation does not support an earlier date for a specific current-form atom, use the normalized `2026-07-12` retained-snapshot boundary rather than inventing a date. Never use `1900-01-01`.

## Atomic statutory scope

- Separate subsection (a)'s prohibition on a recipient using appropriated funds for covered influencing activity from subsection (b)'s declaration filing, certification, and registrant-contact disclosure duties.
- The subsection (a) prohibition applies to Federal contracts, grants, loans, and cooperative agreements and the award/making/entry plus extension, continuation, renewal, amendment, or modification actions listed in subsection (a)(2). It has no transaction-amount threshold.
- Never model SF-LLL or another disclosure as curing a prohibited appropriated-fund payment.
- Subsection (b)(2)(B)'s no-prohibited-payment certification is independent of subsection (b)(2)(A)'s disclosure of the name of an LDA registrant who made lobbying contacts on behalf of the person with respect to the transaction.
- A permitted nonappropriated payment is not by itself the current statutory disclosure trigger. A disclosure-positive fixture must also supply the supported LDA-registrant lobbying-contact fact.
- Preserve subsection (b)(4)'s filing events: initiating submission; receipt if no prior declaration for that transaction; and quarter end after an explicit material-accuracy event. Do not deterministically classify materiality.
- Preserve subsection (b)(5)'s downstream actor separation: the downstream person files its declaration with the upstream person; subsection (b)(1)(B) separately requires the upstream person to send received declarations to the agency.
- Subsection (d)(2)(B) exempts the subsection (b) reporting requirement when a covered non-loan contract, grant, cooperative agreement, subcontract, or subgrant does not exceed $100,000. Therefore the statutory filing/certification/disclosure boundary for those instruments is strictly greater than $100,000; exactly $100,000 is exempt.
- Do not apply the $100,000 boundary to Federal loans or loan-insurance/guarantee commitments. Subsection (d)(2)(C) gives those a separate threshold involving $150,000 or an applicable single-family mortgage limit; expose any unavailable program-specific mortgage-limit comparison as an explicit fact/review gate or defer that branch.
- Preserve subsection (g)'s instrument definitions and exclusions needed for scope. Do not treat direct United States cash assistance to an individual, loan insurance, or a loan guaranty as a Federal contract/grant/cooperative agreement. A Federal loan is a loan made by an agency and excludes loan insurance and guaranty.
- Keep the direct requester/recipient, downstream requester/recipient, and agency as distinct actors. Do not convert an agency duty, discretionary exemption, civil penalty, or enforcement choice into deterministic applicant eligibility or compliance.
- Do not infer intent, reasonableness, regularly-employed status, professional/technical-services classification, Defense exemption, materiality, LDA registration, lobbying contact, payment source, prior filing, or actor role from free text. Missing facts must prevent affirmative compliance/obligation conclusions rather than accuse an actor.
- Do not import Part 200, broader cost principles, debarment, or unrelated award administration.

## Required generated adversarial coverage

The generated companion fixtures must cover at least:

1. A covered recipient's appropriated-fund payment for a covered influencing action: prohibition true regardless of amount.
2. A nonappropriated lobbying payment with an explicit LDA registrant/contact: prohibition false but conditional disclosure true when the subsection (b) filing gate is met.
3. Baseline certification required when the subsection (b) filing gate is met and no lobbying/disclosure occurred.
4. Exactly `$100,000` for a covered non-loan instrument: subsection (b) filing/certification/disclosure false because exempt.
5. Strictly over `$100,000` for each supported non-loan instrument category, with at least one direct and one downstream actor.
6. A Federal loan demonstrating that the `$100,000` gate is not used.
7. A noncovered instrument or excluded instrument definition.
8. Downstream declaration to the upstream person and upstream transmission of received declarations to the agency, without collapsing actors.
9. Missing/ambiguous facts that fail closed.
10. A period before `2026-07-12` that returns no affirmative obligation.

Keep enforcement and penalty outputs deferred. Generate proof atoms with exact subsection-level corpus citation paths for every accepted executable predicate and monetary boundary.
