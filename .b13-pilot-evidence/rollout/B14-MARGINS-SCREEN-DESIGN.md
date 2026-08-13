# B1.4 margins-implied-rate screen design

## Objective

Use reported customs value and calculated duty to screen the executable statutory tariff stack against realized line-level collections. This is an economic sanity check, not a legal identity gate: `cal_dut / con_val` contains aggregation, timing, valuation, preference, drawback, quota, and data-quality effects that a statutory ad-valorem stack may not reproduce exactly.

## Inputs

The coordinator supplies the Census merchandise archives already SHA-manifested by the tariff-scorecard work, retaining at minimum month, partner/country of origin, 10-digit HTS line, `cal_dut`, `con_val`, quantity, and any available customs-value/program/regime fields. The executable side supplies, for the same month and partner, the B1 schedule-composition outputs: selected MFN/column-2 base, each additive or in-lieu statutory component, disposition, and total statutory ad-valorem stack. Input archive SHA, engine artifact SHA, rulespec Git SHA, and evaluation date convention must accompany every result.

## Grain and joins

Aggregate raw trade records to `HTS10 × partner × calendar month`, summing `cal_dut` and `con_val` before division. Normalize HTS to a zero-padded 10-digit string, map statistical children to their rate-bearing ancestor with the published membership map, normalize partner to the engine's country code, and evaluate the statutory stack at a documented representative date (month end by default). Preserve both HTS10 and rate-line keys. Do not silently many-to-many join: require one rate-line mapping and one statutory result per line-partner-month, with unmatched and ambiguous rows reported separately.

## Comparison

For cells with positive `con_val`, calculate `implied_rate = cal_dut / con_val`, `absolute_gap = implied_rate - statutory_stack`, and the absolute percentage-point gap. Report value-weighted results and distributions by month, partner, chapter, rate disposition, and statutory component regime. Exclude or separately bucket non-ad-valorem, compound, component-valued, conditional, quota, Chapter 98/99 adjustment, and zero/negative-value observations; never interpret their ad-valorem gap as conformance evidence. Also retain low-value cells rather than allowing them to dominate alert counts.

## Tolerances and red flags

Use three provisional bands, to be calibrated on known-clean months: green at an absolute gap of at most 0.5 percentage point, amber above 0.5 and at most 2 percentage points, and red above 2 percentage points. Suppress cell-level alerts below $100,000 customs value, while still including those cells in aggregates. The 0.5-point band accommodates rounding, within-month effective dates, and ordinary aggregation; 2 points is large relative to those effects but still sensitive to a missing common surcharge. Add a portfolio red flag when a partner-month or chapter-month has a value-weighted absolute gap above 1 point on at least $10 million of covered value, or when at least 20 independently valued cells share the same signed gap.

A compelling red flag is a persistent, high-value cluster aligned with a legal boundary: for example, China lines understated by roughly a Section 301 increment, Russian lines tracking MFN instead of column 2, or an exact step change absent after an effective date. Investigation output should include the top contributing cells, both keys, inputs, statutory component vector, implied rate, gap, coverage/exclusion reason, and provenance SHAs. Findings remain screening signals until reconciled against entry-program claims, timing, and Census field definitions.
