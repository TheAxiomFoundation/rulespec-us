# rac-us-tx

**Texas state tax statute encodings for Rules Foundation.**

Texas has no personal income tax, but has significant business and consumption taxes:
- **Franchise Tax** (Margin Tax) - Texas Tax Code Chapter 171
- **Sales and Use Tax** - Texas Tax Code Chapter 151
- **Property Tax Framework** - Texas Tax Code Chapter 11

## Structure

Files organized under `statute/` by Texas Tax Code chapter and section:

```
rac-us-tx/
├── statute/
│   ├── tex_tax_code/
│   │   ├── 171/               # Chapter 171 - Franchise Tax
│   │   │   ├── 001/           # § 171.001 - Definitions
│   │   │   ├── 002/           # § 171.002 - Imposition of Tax
│   │   │   ├── 101/           # § 171.101 - Determination of Taxable Margin
│   │   │   ├── 1011/          # § 171.1011 - Cost of Goods Sold
│   │   │   ├── 1012/          # § 171.1012 - Compensation
│   │   │   ├── 1013/          # § 171.1013 - E-Z Computation
│   │   │   └── 1016/          # § 171.1016 - Allocation and Apportionment
│   │   │
│   │   ├── 151/               # Chapter 151 - Limited Sales Tax
│   │   │   ├── 051/           # § 151.051 - Sales Tax Imposed
│   │   │   ├── 101/           # § 151.101 - Use Tax Imposed
│   │   │   └── 801/           # § 151.801 - Local Sales Tax
│   │   │
│   │   └── 11/                # Chapter 11 - Taxable Property and Exemptions
│   │       ├── 01/            # § 11.01 - Real and Tangible Personal Property
│   │       └── 13/            # § 11.13 - Residence Homestead Exemptions
│   │
│   └── state_laws/            # Other relevant state statutes
│
├── guidance/
│   └── comptroller/           # Texas Comptroller guidance
│
└── tests/
    ├── franchise_tax.yaml
    ├── sales_tax.yaml
    └── property_tax.yaml
```

## Key Texas Tax Features

### No Personal Income Tax
Texas Constitution Article VIII, Section 24-a prohibits a state personal income tax
unless approved by voters.

### Franchise Tax (Margin Tax)
- Applies to entities doing business in Texas
- Based on "taxable margin" (lowest of: 70% of total revenue, total revenue minus COGS,
  total revenue minus compensation, or $1 million)
- Tax rates: 0.75% (retail/wholesale), 0.375% (other), 0.331% (E-Z computation)
- No tax due if total revenue <= $2.47 million (2024)

### Sales Tax
- State rate: 6.25%
- Local jurisdictions may add up to 2%
- Maximum combined rate: 8.25%

### Property Tax
- No state property tax (since 1982)
- Local entities (counties, cities, school districts) levy property taxes
- Homestead exemptions available

## References

Cross-file references use paths relative to the repo root:
```
references {
  taxable_margin: statute/tex_tax_code/171/101/taxable_margin
  total_revenue: statute/tex_tax_code/171/1011/total_revenue
}
```

## Related Repos

- **rac-us** - US federal statutes
- **atlas** - Source document archive
- **rac-compile** - DSL compiler and runtime
