# NSF TIP person-or-entity-of-concern adapter constraints

Generate only the narrow implementation adapter at canonical target
`us:policies/nsf/research-security/tip-person-entity-of-concern/implementation`,
using the requested corpus provision
`us/guidance/nsf/research-security/tip-person-entity-of-concern/implementation`.

The principal positive Judgment must preserve these independent gates:

- an explicit caller-supplied fact confirms that the applicable 42 U.S.C.
  19235 statutory prerequisite holds, because the target base has no reusable
  `us/statutes/42/19235` RuleSpec module;
- a person is published on the section 1237(b) list as of the evaluation date,
  OR an entity is identified under the section 1260H list as of that date;
- the person or entity would receive OR participate in the covered matter;
- the matter is a grant, award, program, support, or other activity; and
- the matter is under the U.S. National Science Foundation Directorate for
  Technology, Innovation and Partnerships.

Keep the person/entity routes, the two lists, receive/participate, covered
matter, TIP scope, and statutory prerequisite as distinct facts. Do not create
or import a nonexistent statute module. Do not collapse wrong-type routes: the
1237(b) route applies to a person and the 1260H route applies to an entity.

List membership is a required, caller-supplied, time-indexed dynamic fact for
the evaluation date. Never encode a company name, a current or historical list,
the guidance page's present-tense list narrative, or a default that converts
missing list data into listed or unlisted. Missing interval-covering membership
data must remain a runtime missing-input error. Provider retrieval success,
provider/list version, currentness, and historical as-of coverage may be
separate caller facts if needed for an explicit fail-closed review Judgment.

The effective date is `2022-08-09`, grounded in the official OLRC USLM
`sourceCredit` for 42 U.S.C. 19235: Pub. L. 117-167, div. B, title VI,
section 10636, Aug. 9, 2022, 136 Stat. 1669. Encode an explicit pre-effective
false version and the operative version on `2022-08-09`. The NSF publication,
page-update, corpus snapshot, and linked list-version dates are not the legal
effective date.

The direct guidance proof has exact body SHA-256
`de23799bdc7629f8691faccec0a7b45a0873b10ea7bf409212032699a12ed738`.
Because guidance is lower authority, the upstream-source check must include
`us/statute/42/19235` and `us/statute/42/19235/1`, explaining that paragraph
(1) is the NSF TIP Directorate branch. Require strict proof validation and
proof atoms for the operative formula, both OR branches, TIP scope, the
external statutory prerequisite, and the effective period.

Generate the adjacent companion fixture. It must cover at least:

- listed person / section 1237(b) / receive / TIP;
- listed entity / section 1260H / participate / TIP;
- listed and unlisted controls for both person and entity;
- wrong person/entity list-route controls;
- receive and participate branches;
- TIP and non-TIP scopes;
- covered and non-covered matter kinds;
- statutory prerequisite false;
- missing required dynamic membership input;
- a historical evaluation with caller-supplied interval-covering membership;
- a historical lookup without interval-covering membership data; and
- the all-positive pre-effective `2022-08-08` case.

Assign every local fact consumed by the operative formula in each non-missing
fixture. Do not add a static registry, a manually authored evaluator, or a
parallel 42 U.S.C. 19235 implementation.
