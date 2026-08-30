# NSF IN-149 MFTRP certification adapter request

Encode a single canonical policy adapter at
`us:policies/nsf/important-notice/149-research-security/mftrp-certification-adapter`.
The positional source and the six exact continuation files are the complete
source set. Do not use any other FAQ question, source record, candidate YAML,
or neighboring worktree artifact.

## Source-faithful atomic boundaries

- Keep an actual fact that an individual is a current party to an MFTRP
  separate from every certification assertion. Never infer actual membership
  or non-membership from a certification.
- Encode the current-party senior/key eligibility bar separately from each
  certification duty. Preserve the distinction between an NSF proposal and an
  NSF award, including the source's strict "after May 20, 2024" boundary for
  award-side senior/key ineligibility.
- Encode the senior/key individual's proposal-submission MFTRP certification
  separately from the AOR's organizational proposal certification. The AOR
  statement concerns whether every senior/key individual on that same proposed
  project was made aware of and complied with the individual's responsibility;
  it is not the individual's certification and is not proof of actual MFTRP
  status.
- Proposal-submission certifications are linked only to the same proposed
  project. Keep actor role and project linkage as separate gates. A
  certification linked to another proposal or project must not satisfy the
  evaluated project's rule.
- Encode the annual Research.gov certification separately. It applies only to
  a PI or co-PI who is linked to at least one active NSF award made on or after
  May 20, 2024. Keep PI/co-PI role, same-award linkage, NSF-award status,
  active status, actual award date, annual cycle, and Research.gov channel as
  distinct gates. Merely being senior/key personnel must not trigger it.
- Keep agency prerequisites and applicant duties distinct. At the required
  rulespec base there is no canonical `us/statutes/42/19232` module. Do not
  import or recreate one. Express the relevant 42 U.S.C. 19232 responsibility
  as explicit external prerequisite input gates on the applicant certification
  rules. Missing or false prerequisites must fail closed.

## Temporal treatment

- FAQ question 8 states a general effective date of 2025-12-02. FAQ question 3
  says MFTRP certifications were already in effect during the appropriations
  lapse, but this selected source set supplies no precise earlier proposal-
  certification effective date and no exact lapse bounds. Do not invent an
  earlier effective date and do not use 2025-10-10 as the MFTRP start date.
- Proposal-certification outputs must fail closed before 2025-12-02. Include
  an explicit false pre-version covering all requested pre-effective and
  transition fixtures, followed by the live version on 2025-12-02. Do not rely
  on a lone `effective_from`, because the pinned Rust runtime treats one
  unbounded version as undated semantics.
- Encode the annual award-date cutoff using the actual Date-valued award fact
  and an encoder-generated Date parameter/table or another direct generated
  date comparison. Do not replace it with a caller-precomputed cutoff boolean.
- Preserve `on or after 2024-05-20` for annual certification and strict
  `after 2024-05-20` for the award-side current-party eligibility bar.

## Generated proof and fixture acceptance requirements

Emit only the standard two-file generated bundle: the RuleSpec module and its
adjacent companion test. Require strict proof validation. Use only the seven
selected corpus citation paths in source verification and source proof atoms.
The upstream-authority audit may name 42 U.S.C. 19232 as the checked external
statutory prerequisite, but must not import a nonexistent RuleSpec target or
quote or use unprovided statutory text.

Generated fixtures must independently cover, with all non-target gates held at
their accepting values:

1. actual current MFTRP party true versus false;
2. individual senior/key actor versus AOR actor;
3. senior/key role versus PI/co-PI role;
4. same proposed project versus another proposal or project;
5. same award linkage versus another award;
6. active versus inactive NSF award;
7. award made 2024-05-19, 2024-05-20, and where needed 2024-05-21;
8. annual Research.gov channel versus another channel and current annual cycle
   versus a noncurrent cycle;
9. each external statutory prerequisite false, plus accepting true cases;
10. proposal dates 2025-10-09, 2025-10-10, 2025-12-01, and 2025-12-02,
    demonstrating fail-closed transition behavior and the precise live edge;
11. paired cases proving one atomic actor or duty output can hold while the
    other actor or duty output does not; and
12. certifications and actual MFTRP membership remain logically independent.

Do not merge these gates into opaque precomputed inputs. Do not encode an NSF
agency duty as an applicant compliance result. If faithful executable proof or
the requested atomic fixtures cannot be generated, emit a typed deferral
instead of weakening or guessing the rule.
