# B1.6 B2 flag-to-action map

The hand-built witness derives five mutually exclusive HTS exemplars. The generated compositions now reference these names without defining them, making them caller inputs. The formulas below are the complete set of witness formulas that consume each flag. Shared base-selection text is quoted once per flag as its relevant line.

## `entry_is_line_a` — HTS 7202.11.10.00

- `line_a_special_rate_applies`: `entry_is_line_a and origin_is_korea`
- `mfn_ad_valorem_rate`: `if entry_is_line_a:`
- `entry_is_reciprocal_annex_excluded`: `entry_is_line_a`
- `section_122_component_rate`: `if entry_is_line_a or entry_is_line_b: 0`
- `china_section_301_component_rate`: `(if entry_is_line_a and origin_is_china: list_1_additional_ad_valorem_rate else: 0)`
- `brazil_section_301_component_rate`: `if entry_is_line_a or entry_is_line_b: 0`
- `forced_labor_section_301_component_rate`: `if entry_is_line_a or entry_is_line_b: 0`

Generalized receipts: section 122 unconditional exemptions are the union of `s122_aa_ii_membership`, `s122_aa_ii_membership_hts10`, and `s122_aa_iii_membership`; GN6 conditions remain separate in `s122_gn6_conditional_membership`. Steel incidence is kept in its exact slots: `s232_steel_primary_membership`, legacy/april/equipment 8- and 10-digit pairs, and `s232_steel_derivative_mobile_membership`. China list membership is not inferred from this legacy flag. The exemplar is actually in `china_301_list3_membership`, although the quoted witness formula selects the list-1 rate. That mismatch is explicit; the generalized tool reports list 3, while exact witness identity supplies line A.

## `entry_is_line_b` — HTS 7601.10.30.00

- `line_b_special_rate_applies`: `entry_is_line_b and origin_is_korea`
- `mfn_ad_valorem_rate`: `elif entry_is_line_b:`
- `entry_is_reciprocal_metals_excluded`: `entry_is_line_b`
- both IEEPA component variants: `+ (if origin_is_brazil and not entry_is_line_b: brazil_ieepa_additional_duty_rate else: 0)`
- `section_122_component_rate`: `if entry_is_line_a or entry_is_line_b: 0`
- `section_232_aluminum_component_rate` (both versions): `elif entry_is_line_b:` / `if entry_is_line_b:`
- `china_section_301_component_rate`: `+ (if entry_is_line_b and origin_is_china: china_301_action_additional_ad_valorem_rate else: 0)`
- Brazil and forced-labor section 301 components: `if entry_is_line_a or entry_is_line_b: 0`

Generalized receipts: aluminum derivatives use `s232_aluminum_derivative_membership` plus `s232_aluminum_derivative_membership_hts10`. The China `china_301_action` witness slot is broader/ambiguous: its proof is the 2024 action at 9903.91.01, while the note-20 incidence module only publishes list 1/2/3/4A. Therefore no note-20 list is relabeled as that action; the lane tool reports the four lists separately.

## `entry_is_line_c` — HTS 9506.62.40.40

- `mfn_ad_valorem_rate`: `elif entry_is_line_c:`
- `china_section_301_component_rate`: `+ (if entry_is_line_c and origin_is_china: list_4a_additional_ad_valorem_rate else: 0)`

Generalized receipt: list 4A is the union of `china_301_list4a_membership` and `china_301_list4a_membership_hts10`. The exemplar is a member of that slot.

## `entry_is_line_d` — HTS 2203.00.00.30

- `mfn_ad_valorem_rate`: `elif entry_is_line_d:`
- `beer_section_232_aluminum_content_basis_duty_applies`: `entry_is_line_d`
- `section_338_component_rate`: `if entry_is_line_d and origin_is_canada and not beer_section_232_aluminum_content_basis_duty_applies: section_338_alcohol_additional_duty_rate`
- `section_338_reduced_duty_base_applies`: `entry_is_line_d`
- `china_section_301_component_rate`: `+ (if entry_is_line_d and origin_is_china: list_1_additional_ad_valorem_rate else: 0)`

Generalized receipts: aluminum incidence uses the note-19 pair named above. Section 338 is not among the five B1 incidence modules and remains a separately prepared action fact. The exemplar is in `china_301_list3_membership`, but the witness formula selects the list-1 rate; as with line A, generalized output truthfully reports list 3 rather than rewriting the receipt.

## `entry_is_line_e` — HTS 8541.42.00.10

- `mfn_ad_valorem_rate`: `elif entry_is_line_e:`
- `section_201_component_rate`: `if entry_is_line_e: 0`
- `china_section_301_component_rate`: `+ (if entry_is_line_e and origin_is_china: solar_china_section_301_additional_duty_rate else: 0)`

Generalized receipt: section 201 CSPV is the union of `s201_cspv_membership` and `s201_cspv_membership_hts10`. The solar China action is proved under note 31/9903.91.02, not note 20, so it is not falsely mapped into list 1/2/3/4A.

## China list-to-slot rule

The lane classifier exposes `china_301_list1`, `china_301_list2`, `china_301_list3`, and `china_301_list4a` from the exact same-named note-20 membership tables (with the additional 10-digit table for 4A). Lists 1, 2, and 3 all select the witness's 25-percent China-301 action machinery; list 4A selects `list_4a_additional_ad_valorem_rate`. The witness has only per-exemplar slots, not a complete per-list predicate surface, which is why the generalized outputs remain separate instead of being collapsed into the five compatibility flags.
