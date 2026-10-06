# Encoding acceptance requirements for 42 U.S.C. § 19237(3)

Generate the RuleSpec module and its companion tests from the supplied official corpus source. These requirements specialize the requested output and override generic prompt advice that would omit the required temporal version.

- Export the atomic `foreign_entity_of_concern` Judgment for an entity evaluated on a Day.
- Encode the chapeau exactly as: the entity is a foreign entity AND at least one route in subparagraphs (A) through (E) holds.
- Keep every designation, list membership, covered-nation status, Attorney General allegation/conviction fact, and Commerce determination/consultation fact as an evaluation-time caller-supplied predicate. Do not include or infer any current entity or country name. Do not determine list membership by name matching.
- Preserve the top-level A/B/C/D/E OR structure and each nested statutory alternative:
  - (A) Secretary of State foreign-terrorist-organization designation specifically under 8 U.S.C. § 1189(a).
  - (B) inclusion specifically on the OFAC-maintained SDN list.
  - (C) covered-nation status under 10 U.S.C. § 4872 AND one of ownership by, control by, jurisdiction of, or direction of that covered-nation government.
  - (D) Attorney General allegation of involvement in the same activities for which a conviction was obtained AND the conviction was under one of: title 18 chapter 37; 18 U.S.C. § 951; 18 U.S.C. § 1030; title 18 chapter 90; the Arms Export Control Act; 42 U.S.C. § 2274; § 2275; § 2276; § 2277; § 2284; the Export Control Reform Act of 2018; or IEEPA. Preserve the Attorney General and same-activities/conviction chapeau separately from the authority alternatives so missing allegation or conviction facts fail.
  - (E) a determination made by the Secretary of Commerce, in consultation with both the Secretary of Defense and the Director of National Intelligence, that the entity engaged in unauthorized conduct detrimental to either U.S. national security or U.S. foreign policy. Preserve the determining official, both consultations, unauthorized-conduct predicate, and both detriment alternatives.
- Use exact proof provenance. Declare and cite the paragraph chapeau `us/statute/42/19237/3`; child paths `/3/A`, `/3/B`, `/3/C`, `/3/D`, each `/3/D/i` through `/3/D/vii`, and `/3/E`; and `us/statute/42/19237` for the enactment source credit. A D authority child never substitutes for the `/3/D` Attorney General chapeau.
- Include a literal-false derived-rule version effective on `2022-08-08` and the operative formula effective on `2022-08-09`. Prove the false version as the effective-period atom from the section source credit.
- Generate adversarial companion tests, including an independent positive for every exposed OR leaf; all routes false; an otherwise positive route with the foreign-entity chapeau false; C covered-nation-without-relationship and relationship-to-noncovered-nation cases; D missing Attorney General allegation, missing same-activities conviction, and no qualifying authority cases; E missing each consultation, authorized rather than unauthorized conduct, and no qualifying detriment cases; and a fully positive `2022-08-08` case that is `not_holds`.
- Omitted required inputs must remain missing-input errors, not silently default false. Do not add constants for dynamic facts.
