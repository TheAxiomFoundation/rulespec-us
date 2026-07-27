# Illinois SCRETD current-law review

- Review date: 2026-07-27
- Act: 320 ILCS 30
- Corpus expression date for §§ 2 and 3: 2026-06-26
- Computation year under review: tax year 2026

## Bottom line

The RuleSpec modules and corpus are current for the four requested
computation-bearing values and incorporate Public Act 104-452, effective
December 12, 2025:

| Item | Current law | Encoding result |
| --- | --- | --- |
| Maximum household income | $75,000 for TY2025; $77,000 for TY2026; $79,000 for TY2027+ | Matches |
| Equity-interest ceiling | 80% of the taxpayer's equity interest | Matches |
| Annual deferral cap | $5,000 for TY2012–2021; $7,500 for TY2022+ | Matches |
| Interest | 6% for a tax year before 2023; 3% for TY2023+ | Matches |

Public Act 104-452 materially changed the income schedule and made the $7,500
cap permanent after tax year 2021. It did not change the 80% ceiling or the
6%/3% interest break. The local corpus rows selected by exact
`citation_path` contain the Public Act 104-452 text and source note, so the
corpus is not stale for that amendment.

The act corpus is nevertheless not fully current. Public Act 104-468,
effective June 16, 2026, later amended § 3's lien language. It makes deferred
real-estate taxes and taxes paid by the Department of Revenue, together with
accruing interest and costs, a prior and first lien superior to other liens
and encumbrances. The June 26 corpus § 3 row still ends with Public Act
104-452 and omits this amendment, as does the compiled ILCS page currently
published by ILGA. This later change does not alter eligibility, the
deferral-amount formula, the income limit, annual cap, equity percentage, or
interest rate. It does prevent an honest claim that all of current § 3 is in
the corpus or fully encoded.

## Eligibility boundaries

Section 2(a) defines a qualified taxpayer as an individual who:

1. will be at least 65 by June 1 of the deferral year;
2. certifies at least three years of ownership and occupancy of the property,
   or other qualifying Illinois property, except for temporary residence in a
   nursing or sheltered-care home; and
3. has household income no greater than the applicable maximum.

Section 3 repeats the age and three-year ownership/occupancy application
items. Eligibility for the Low-Income Senior Citizens Assessment Freeze
Homestead Exemption may substitute for those two application items. It does
not substitute for § 2(a)(iii)'s household-income qualification.

## Corpus evidence

The act appears in two inventories. Both were searched through each row's
`citation_path`, not inferred from inventory filenames:

- `us-il/statute/320/30/2`
- `us-il/statute/320/30/3`

The paired provision records have `expression_date: 2026-06-26`. Section 2
contains the $75,000/$77,000/$79,000 schedule and a Public Act 104-452 source
note. Section 3 contains the permanent $7,500 cap, 80% ceiling, and 6%/3%
interest break, but not Public Act 104-468's lien-priority amendment.

## Official sources

- [Current compiled act](https://www.ilga.gov/Legislation/ILCS/Articles?ActID=1454&ChapterID=31&Print=True)
- [Current compiled § 2](https://www.ilga.gov/documents/legislation/ilcs/documents/032000300K2.htm)
- [Current compiled § 3](https://www.ilga.gov/documents/legislation/ilcs/documents/032000300K3.htm)
- [Public Act 104-452](https://www.ilga.gov/Legislation/PublicActs/PrinterFriendly/104-0452)
- [Public Act 104-468 and effective date](https://www.ilga.gov/Legislation/PublicActs/View/104-0468)
- [Public Act 104-468 full text](https://www.ilga.gov/Documents/Legislation/PublicActs/104/PDF/104-0468.pdf)
- [IDOR January 2026 program update](https://tax.illinois.gov/localgovernments/localtaxallocation/ltad-quarterly-newsletter/2026-01.html)
- [IDOR program guidance](https://tax.illinois.gov/research/publications/pio-64.html)

