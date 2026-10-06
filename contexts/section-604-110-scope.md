# Atomic scope for 45 CFR 604.110

Encode the currently operative mandatory filing and routing rules that can be
proved from paragraphs (a)-(e), while keeping their outputs separate.

- For an initiating submission and for receipt (unless previously filed), the
  certification filing rule covers a Federal contract, grant, or cooperative
  agreement strictly exceeding `$100,000`, and a Federal loan strictly
  exceeding `$150,000`.
- The disclosure filing rule uses the same instrument-specific threshold and
  filing occasion but is additionally conditional on the separate disclosure
  trigger from section 604.100(c). Certification remains required when the
  disclosure trigger is false.
- For contract, grant, and cooperative-agreement boundary fixtures, `$99,999`
  and `$100,000` are false and `$100,001` is true. For a Federal loan, all
  three values are false because the loan threshold is `$150,000`.
- Paragraph (c) requires a quarter-end disclosure upon a reportable event or a
  material accuracy change. A cumulative increase of `$25,000` or more, change
  in lobbying persons, or change in contacted officials is sufficient, but the
  word `includes` means those examples are not an exhaustive definition.
- Paragraph (d) lower-tier filing is only to the next tier above and only for:
  a subcontract over `$100,000` under a Federal contract; a subgrant, contract,
  or subcontract over `$100,000` under a Federal grant; a contract or
  subcontract over `$100,000` under a Federal loan that itself exceeds
  `$150,000`; or a contract or subcontract over `$100,000` under a Federal
  cooperative agreement. Require the tier actor and upstream/downstream
  transaction linkage explicitly.
- Paragraph (e) forwards disclosure forms, not certifications, tier-to-tier to
  the paragraph (a)/(b) prime person, and then from that person to the agency.
  Keep lower-tier filing and forwarding as distinct outputs.

Do not encode paragraph (f)'s liability, erroneous-representation consequence,
or discretionary remedies. Use paragraph (g) only as proof of the
`1989-12-23` effective date; do not encode its exhausted transition. Do not
encode paragraph (h) because Subparts B/C are outside scope. Do not combine a
loan with loan guarantee or loan insurance.

