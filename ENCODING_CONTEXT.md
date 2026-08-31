# Task-specific encoding constraints for 31 U.S.C. § 1352

Generate one narrow whole-section base module at `statutes/31/1352.yaml` and its companion generated test. This brief constrains selection and naming; the official corpus source and primary-source continuation remain the legal authority.

## Required separation

- Do not emit a generic eligibility or award-eligibility output.
- Keep these legal questions separate: whether an appropriated-funds lobbying payment is prohibited; whether a declaration must be filed; whether the declaration must contain the no-prohibited-payment certification; whether that certification can truthfully be made; whether an LDA registrant's name must be included; whether a lower-tier person must file with the direct agency requestor/recipient; and whether the direct person must file copies received with the agency.
- A prohibited payment never cancels the filing or certification obligation.
- Do not emit `SF-LLL` or any form-specific output. Section 1352 does not name that form.

## Amount and instrument scope

- The subsection (a) prohibition has no dollar threshold.
- Under (d)(2)(B), exactly $100,000 is exempt from subsection (b) reporting for a contract, grant, cooperative agreement, subcontract, or subgrant; coverage begins above $100,000.
- Do not apply $100,000 to a Federal loan, loan-insurance commitment, loan-guaranty commitment, or a contract/subcontract carrying out a particular loan. Under (d)(2)(C), those use an amount greater than the larger of $150,000 and the affected-program single-family maximum mortgage limit.
- Preserve the definitions in (g)(6)-(7): Federal contract/grant/cooperative agreement exclude direct cash assistance to an individual, a loan, loan insurance, and a loan guaranty; a Federal loan is agency-made and excludes insurance/guaranty.
- Require an explicit instrument-classification-complete fact so a noncovered instrument can return `not_holds` without silently treating missing classification as noncoverage.

## Payment source and exceptions

- Appropriated funds used by a statutory recipient to pay a person for covered influencing activity are prohibited, regardless of the award amount, subject to the actual statutory boundaries in (d)(1), (e), and (g)(1)(B)/(3)(B).
- Treat a written DoD national-interest exemption as an input fact about an exemption already made; never compute whether the Secretary may or should grant one.
- Preserve the liaison and professional/technical-services exceptions and the Indian-organization permitted-by-other-Federal-law carveout. Do not import broader cost principles, debarment, or 2 CFR part 200.
- A nonappropriated lobbying payment is not prohibited by (a). Funding source alone does not trigger current statutory disclosure.

## Declaration, disclosure, filing, and actors

- For a direct agency requestor/recipient in a covered transaction above the applicable reporting threshold, the ordinary contract/grant/loan/cooperative-agreement declaration contains both the current (b)(2)(A) LDA-registrant-name item and the independent (b)(2)(B) no-prohibited-payment certification. A loan insurance/guarantee declaration under (b)(3) has the registrant-name item but not the (b)(2)(B) certification.
- The registrant-name inclusion predicate requires a registrant under the Lobbying Disclosure Act of 1995 who made lobbying contacts on behalf of the person with respect to the same transaction. A permitted nonappropriated payment may coexist with and illustrate this predicate, but is not itself the trigger.
- Preserve all three (b)(4) filing events separately: initiating submission; receipt unless previously filed for that transaction; and calendar-quarter end after an event materially affects an earlier declaration's accuracy.
- Preserve direct and lower-tier actors. Under (b)(5), a lower person files with the person who directly requests or receives from the agency for the listed subcontract/subgrant/contract categories. Under (b)(1)(B), that direct person files copies received with the agency. Do not infer recursive all-tier flow-down or an award-document insertion requirement.

## Dates and fail-closed behavior

- The base section applies to the listed instruments entered into or made more than 60 days after 1989-10-23; the first covered date is 1989-12-23. Also require a same-instrument fact that this statutory effective-date condition is met, because a later evaluation date cannot make an older instrument covered.
- The current LDA-registrant-name text begins 1996-01-01. Do not apply that current disclosure content to 1989-1995.
- Use explicit pre-effective false sentinel versions, or an equivalent dated parameter that makes otherwise-positive pre-effective cases return `not_holds` rather than relying on a missing-version error.
- Do not make `false` stand for unknown facts. Every generated positive/negative companion case must assign every required local fact. Missing-required-fact behavior will be checked separately through the real Rust runtime and must fail closed with a missing-input error.

## Minimum adversarial generated coverage

- $100,000 exactly versus $100,000.01 (or an integer amount strictly above $100,000) for a nonloan covered instrument.
- A covered instrument versus direct cash assistance or another expressly noncovered instrument.
- A prohibited appropriated-funds lobbying payment at or below $100,000, proving the prohibition has no reporting threshold.
- A permitted nonappropriated lobbying payment together with a same-transaction LDA registrant contact: payment not prohibited, baseline certification still required above threshold, and registrant name inclusion required on/after 1996-01-01.
- Direct agency actor versus unrelated actor; direct lower-tier subaward declaration and copy-up, without recursive all-tier claims.
- Each filing event, including the receipt/prior-filing distinction.
- A fully positive case immediately before the base effective date that returns `not_holds`.

Defer any surface that cannot satisfy these distinctions. Do not encode the discretionary civil-penalty/enforcement provisions as deterministic eligibility or liability.
