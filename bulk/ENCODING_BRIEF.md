# NSF IN-149 MFTRP certification adapter

Generate one canonical policy adapter at
`us:policies/nsf/important-notice/149-research-security/mftrp-certification-adapter`.
The positional item 3 provision and the six explicit primary-source continuation
files in `bulk/nsf-in149-mftrp-context/` are the complete authorized source set.
Do not read or cite any other FAQ question, source record, neighboring candidate,
or RuleSpec worktree artifact.

## Atomic runtime surface

Keep each fact, role, linkage, duty, and attestation independently observable.
Use raw proposed-project and award identifiers with generated equality checks
where linkage matters; do not replace linkage with a caller-computed compliance
boolean.

Generate separate executable outputs for all of the following:

1. The evaluated individual is barred from serving as senior/key on the
   evaluated NSF proposal because the individual is an actual current party to
   an MFTRP. Require the actual membership fact, individual actor, senior/key
   role, NSF-proposal fact, and same-proposed-project role linkage separately.
2. The evaluated individual is barred from serving as senior/key on the
   evaluated NSF award because the individual is an actual current party to an
   MFTRP. Require the actual membership fact, individual actor, senior/key role,
   NSF-award fact, same-award role linkage, and an award date strictly after
   2024-05-20 separately.
3. The senior/key individual's proposal-submission certification is documented
   for the evaluated proposed project. Require individual actor, identified
   senior/key role, same-project role linkage, same-project certification
   linkage, a declaration that the individual is not an MFTRP party, the
   required proposal-document channel facts, and the explicit external
   42 U.S.C. 19232 individual-responsibility prerequisite separately.
4. The AOR organizational proposal certification is documented for the
   evaluated proposed project. Require AOR actor, same-project certification
   linkage, Cover Sheet channel, a complete identified-senior/key roster, all
   identified senior/key personnel made aware, all identified senior/key
   personnel compliant with their individual certification responsibility, and
   the explicit external 42 U.S.C. 19232 individual and AOR responsibility
   prerequisites separately. This output is not an individual certification
   and is not proof of any person's actual MFTRP status.
5. The annual MFTRP-status certification is required for the evaluated
   individual. Require individual actor, PI-or-co-PI role, same-award role
   linkage, NSF-award fact, active-award fact, and an award date on or after
   2024-05-20 separately. Treat the evaluated person/award tuple as one
   candidate for the source's existential "at least one" test; one accepting
   linked award is sufficient, while an unlinked award is not.
6. The required annual MFTRP participation-status certification is documented.
   In addition to the annual-duty gates, require Research.gov, a submitted
   MFTRP participation-or-non-participation status certification, and the
   current annual cycle separately. This is a person-level annual certification,
   not a proposal-project certification and not an attestation attached to all
   senior/key personnel.

The actual-current-MFTRP-party fact must never be inferred from any attestation,
missing certification, role, or linkage. Conversely, a submitted attestation
must not be treated as proof of actual membership or non-membership. Preserve
contradictory fact/attestation cases as separate outputs.

## External statutory prerequisite

The required base has no canonical `us:statutes/42/19232` RuleSpec module. Do
not import, recreate, or quote one. Represent the incorporated individual and
AOR responsibilities as explicit external prerequisite inputs that fail closed
when missing or false. The guidance module's upstream-authority audit may name
42 U.S.C. 19232 as the externally checked authority, but it must not add that
statute to `module.source_verification.corpus_citation_paths`, use statutory
text not supplied here, or emit an import to a nonexistent target. Encode no
NSF agency duty as an applicant compliance output.

## Temporal treatment

- FAQ question 8 establishes 2025-12-02 as the general IN-149 effective date.
- FAQ question 3 says MFTRP certifications were already in effect during the
  appropriations lapse, but the authorized records do not establish a precise
  earlier proposal-certification effective date or exact lapse bounds.
- Do not invent an earlier date, treat 2025-10-10 as the MFTRP start date, or
  use the 2025-11-24 expression date as an operative date.
- Make proposal-certification documentation outputs fail closed before
  2025-12-02 by generating a Boolean temporal parameter with an explicit false
  version through 2025-12-01 and a true version beginning 2025-12-02. Derived
  outputs should consume that gate rather than use multiple derived versions.
- Exercise proposal periods 2025-10-09, 2025-10-10, 2025-12-01, and
  2025-12-02. The first three must not affirm proposal certification
  documentation; the final date is the first definite accepting edge.
- Do not extend the proposal-only project limitation to the separate annual
  certification.

Generate the 2024-05-20 cutoff as a real `dtype: Date` parameter table with an
explicit integer selector and a Date value in `versions[].values`. Compare the
actual Date-valued award fact directly to the selected parameter cell. Do not
emit a bare Date literal as a formula and do not accept a caller-precomputed
cutoff Boolean. Use `>` for award-side senior/key ineligibility and `>=` for the
annual-certification duty.

## Generated bundle and proof contract

Emit only the normal generated RuleSpec module and its adjacent companion
`.test.yaml`; signed apply may additionally emit its standard manifest and
mechanically generated repository indexes. Require strict proof validation.
List exactly these seven guidance paths in source verification and use only
them in source-backed proof atoms:

- `us/guidance/nsf/important-notice/149-research-security/3`
- `us/guidance/nsf/important-notice/149-research-security/4`
- `us/guidance/nsf/important-notice/149-implementation-faq/question-3`
- `us/guidance/nsf/important-notice/149-implementation-faq/question-5`
- `us/guidance/nsf/important-notice/149-implementation-faq/question-6`
- `us/guidance/nsf/important-notice/149-implementation-faq/question-7`
- `us/guidance/nsf/important-notice/149-implementation-faq/question-8`

Every generated derived output must appear in at least one companion fixture.
Fixtures must isolate, with all non-target gates accepting, actual membership
true/false, individual/AOR, senior-key/PI-co-PI, same/other proposed project,
same/other award linkage, active/inactive and NSF/non-NSF award, award dates
2024-05-19/20/21, both Date comparison edges, complete/incomplete AOR roster,
each external prerequisite, each certification channel, current/noncurrent
annual cycle, missing inputs/gates, the four proposal timing boundaries, and
logical independence between actual membership and every certification.

If the generator cannot produce faithful executable proof and these atomic
fixtures, emit a typed deferral instead of weakening or guessing the rule.
