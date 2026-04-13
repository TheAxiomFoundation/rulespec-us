# rac-us-tx

Texas jurisdiction repo for the [Rules Foundation](https://rules.foundation) policy rules engine.

## Overview

Texas has a unique tax structure with **no personal income tax** (prohibited by Texas Constitution Article VIII, Section 24-a). Instead, Texas relies on:

- **Franchise Tax (Margin Tax)** - Business tax based on taxable margin
- **Sales and Use Tax** - 6.25% state rate + up to 2% local
- **Property Tax** - Local taxes with state-defined exemptions
- **Texas-administered overlays for federal programs** - for example Texas SNAP current-effective handbook and bulletin parameters

## Structure

```
rac-us-tx/
├── statute/
│   └── tex_tax_code/
│       ├── 171/          # Chapter 171 - Franchise Tax
│       │   ├── 001/      # Definitions
│       │   ├── 002/      # Tax imposition
│       │   ├── 101/      # Taxable margin
│       │   ├── 1011/     # Total revenue, COGS
│       │   ├── 1012/     # Compensation
│       │   └── 1013/     # E-Z computation
│       │
│       ├── 151/          # Chapter 151 - Sales Tax
│       │   ├── 051/      # Sales tax imposed
│       │   └── 101/      # Use tax imposed
│       │
│       └── 11/           # Chapter 11 - Property Tax
│           ├── 01/       # Taxable property
│           └── 13/       # Homestead exemptions
│
└── tests/
    ├── franchise_tax.yaml
    ├── sales_tax.yaml
    └── property_tax.yaml
```

Texas-administered current-effective overlays and guidance-derived source slices live under `sources/slices/`.

When a Texas authority sets a jurisdiction-specific value under delegated federal authority, record the authoritative excerpt in `sources/slices/...` and attach a `*.meta.yaml` sidecar with `relation: sets` pointing at the canonical upstream slot.

## Texas Franchise Tax

The franchise tax (margin tax) applies to most entities doing business in Texas:

- **Tax Base**: Taxable margin = lowest of:
  - 70% of total revenue
  - Total revenue minus COGS
  - Total revenue minus compensation
  - Total revenue minus $1 million

- **Tax Rates** (2024):
  - 0.375% for retail/wholesale trade
  - 0.75% for all other businesses
  - 0.331% for E-Z computation (simplified)

- **No Tax Due** if total revenue ≤ $2,470,000

## Texas Sales Tax

- State rate: 6.25%
- Maximum local rate: 2%
- Maximum combined: 8.25%

**Key Exemptions**:
- Grocery food
- Prescription and OTC medicines
- Medical equipment

## Texas Property Tax

Texas has no state property tax. Local taxing entities set their own rates.

**State-Mandated Exemptions**:
- $100,000 school district homestead exemption
- $10,000 additional for 65+ or disabled
- 100% exemption for 100% disabled veterans
- 10% annual appraisal cap for homesteads

## Usage

```bash
# Validate rules
rac check statute/

# Run tests
rac test tests/

# Calculate franchise tax
rac calc franchise_tax --input business.yaml
```

## References

- [Texas Tax Code](https://statutes.capitol.texas.gov/Docs/TX/htm/TX.htm)
- [Texas Comptroller](https://comptroller.texas.gov/taxes/)
- [Franchise Tax Overview](https://comptroller.texas.gov/taxes/franchise/)

## License

Apache 2.0
