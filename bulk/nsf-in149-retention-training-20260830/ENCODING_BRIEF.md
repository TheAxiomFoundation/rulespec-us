# NSF IN-149 Items 1–2 encoding contract

This brief constrains two Axiom-generated policy adapters. It is context for
`axiom-encode`, not a manually authored RuleSpec. The generated module and
companion test must remain unchanged from the accepted encoder run.

## Targets and source boundary

Generate these logical targets under the canonical `us/` content root:

1. `us:policies/nsf/important-notice/149-research-security/supporting-document-retention-request-adapter`
2. `us:policies/nsf/important-notice/149-research-security/research-security-training-certification-adapter`

The Item 1 run uses
`us/guidance/nsf/important-notice/149-research-security/1` as its positional
source. The Item 2 run uses
`us/guidance/nsf/important-notice/149-research-security/2`. The only FAQ
continuations allowed are:

- `us/guidance/nsf/important-notice/149-implementation-faq/question-1`
- `us/guidance/nsf/important-notice/149-implementation-faq/question-5`
- `us/guidance/nsf/important-notice/149-implementation-faq/question-6`
- `us/guidance/nsf/important-notice/149-implementation-faq/question-7`
- `us/guidance/nsf/important-notice/149-implementation-faq/question-8`

The directly relevant statutory continuations may be used only for the
higher-authority audit and proof of the explicit prerequisite boundaries:

- `us/statute/42/19233/a/1`
- `us/statute/42/19233/a/2`
- `us/statute/42/19234/a/1/A`
- `us/statute/42/19234/a/1/B`
- `us/statute/42/19234/c/1/A`

At the required rulespec base there is no canonical section 19233 or section
19234 module. Do not import or recreate either section. Expose the relevant
statutory base as an explicit external prerequisite for its adapter, and fail
closed when that prerequisite is false or missing. Do not encode agency risk
assessment, award substitution/removal, funding reduction, suspension,
termination, or any other parallel statutory semantics.

Do not encode Item 3–6 duties, malign-foreign-talent-recruitment certification,
foreign-financial disclosure, Confucius Institute certification, or the
IHE-only responsible-and-ethical-conduct-of-research certification. Do not
declare RECR, IHE, 42 U.S.C. 19039, or 42 U.S.C. 19040 inputs, rules, deferred
outputs, or proof atoms.

## Item 1 atomic duties

Represent a document/organization/senior-key-person/project-or-award case. Keep
these judgments separate:

1. the proposer-or-recipient retention duty;
2. the duty to make an in-scope document available only when an actual NSF
   request covers that same document and case; and
3. the separately conditioned expectation/duty to review the actually
   requested document for NSF award-term, conflict-of-interest, and
   conflict-of-commitment compliance.

The retention judgment must not depend on a request. The availability and
review judgments must fail when there is no actual NSF request. Do not infer a
request from risk assessment, analytics, proposal submission, award status, or
document retention. Do not emit a conclusion that a document or person is
compliant, conflicted, risky, removable, or sanctionable.

Both a proposer and a recipient can bear the Item 1 duty; keep those actor facts
distinct and reject an unrelated actor. Scope each case to the same proposed
project or recipient award. An award made before the effective date is outside
IN-149 under FAQ 7.

An in-scope document is either:

- a contract, grant, or other agreement with the required nexus to a foreign
  appointment, employment with a foreign institution, or participation in a
  foreign talent recruitment program; or
- material reported as current and pending (other) support.

Do not treat an arbitrary contract, grant, agreement, or unrelated document as
in scope. Keep document type and the foreign-relationship nexus separately
testable. Keep the linkage between the document subject and the senior/key
person on the same evaluated project or award separately testable. Item 1 has
no certification requirement.

Every Item 1 operative judgment must depend on an explicit external section
19233 prerequisite for the same evaluated case. A missing or false prerequisite
must fail closed.

## Item 2 atomic certifications

Keep the individual senior/key-person certification separate from the AOR's
organizational certification. Neither certification proves the other.

The individual judgment must require, as distinct facts:

- the actor is the evaluated senior/key person on the same proposed project;
- the certification was actually made at submission for that same proposal;
- the training qualifies either because it addresses the IN-149 subjects or
  because it is an otherwise recognized compliant route;
- the actual training-completion date is not after the actual proposal
  submission date; and
- the completion date is on or after the inclusive start of the proposal's
  twelve-month lookback window.

The AOR judgment must require, as distinct facts:

- the actor is the AOR for the proposing organization and same proposed
  project;
- the AOR certification was actually made at submission for that same
  proposal; and
- all senior/key personnel on that same proposed project completed qualifying
  training within the same required window.

Use a same-proposal identifier comparison or another direct generated linkage;
a certification for another proposal or project must not satisfy either rule.
Proposal certifications apply only to the proposed project.

The named government modules and the condensed SECURE module are examples or
recognized routes, not exclusive vendors or frozen required modules. Do not
hard-code a vendor/module requirement. A source-faithful generic recognized
route or content predicate is acceptable.

Every Item 2 operative judgment must depend on an explicit external section
19234 prerequisite for the same proposal. A missing or false prerequisite must
fail closed.

## Twelve-month window and temporal behavior

The source states twelve months/one year, not 365 days. The pinned Rust runtime
supports Date comparisons and day addition but no calendar-month subtraction.
Do not replace twelve calendar months with 365 or 366 days. Use actual
Date-valued completion and submission facts plus an explicit external
Date-valued start of the twelve-month window for the same proposal, then perform
inclusive Date comparisons in RuleSpec. Missing that external date prerequisite
must fail closed. The exact start date is accepted; one day before it is not;
completion after submission is not.

For both adapters, include an explicit false pre-effective version followed by
the live version on `2025-12-02`. Do not rely on a lone `effective_from`, because
the runtime can otherwise expose undated semantics. Generated fixtures must
prove all-positive cases fail on `2025-12-01` and hold on `2025-12-02`. The
selected sources establish no operative grace period for Items 1–2; do not add
one.

## Proof and fixture acceptance

Require strict proof validation. Every executable rule needs source-backed
proof atoms. Guidance modules need an `upstream_source_check` naming the
relevant statute continuations while explaining why IN-149 and its FAQ remain
the direct NSF implementation sources. Do not import a nonexistent statute
RuleSpec target.

Generated Item 1 fixtures must independently cover, with non-target gates held
at accepting values:

- proposer and recipient acceptance, plus unrelated actor rejection;
- contract, grant, other agreement, and current/pending-support material;
- absent foreign nexus for an agreement and an unrelated document type;
- actual request versus no request, proving retention remains while production
  and review do not;
- same senior/key person versus another person;
- same project/award versus another case;
- false section 19233 prerequisite;
- recipient award before the effective date; and
- `2025-12-01` versus `2025-12-02`.

Generated Item 2 fixtures must independently cover, with non-target gates held
at accepting values:

- individual senior/key-person certification versus AOR certification, with
  paired cases proving one can hold while the other does not;
- same proposal versus another proposal;
- actual certification versus missing certification for each actor;
- qualifying subject-content route and generic recognized-compliant route;
- nonqualifying training;
- exact twelve-month start, one day before the start, same-day completion, and
  completion after submission;
- all same-proposal senior/key personnel completed training versus one missing;
- false section 19234 prerequisite; and
- `2025-12-01` versus `2025-12-02`.

Do not merge the requested distinctions into opaque precomputed gates when the
runtime can compare the underlying actor, identifier, document-type, request,
or Date facts. If faithful execution is impossible, emit a typed deferral
instead of weakening the rule.
