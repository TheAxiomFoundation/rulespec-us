# B1.6-C structural note

Generated component formulas now consume membership-semantic inputs for China 301 list 1/2/3 and list 4A, section 232 aluminum and steel, section 201 CSPV, section 122 unconditional exemptions, and section 232 coverage. Section 122 returns zero only for its exemption input or section-232 coverage; all dates and declared gates are unchanged. Direct component-formula exemplar references are gone except the intentionally retained beer/section-338 `entry_is_line_d` slots. The copied reciprocal-duty helper predicates remain witness-compatible caller facts and are outside the component rewrite.

Brazil-301 and forced-labor-301 require their own list inputs. Entry preparation cannot yet populate those lists, so the flag tool emits the declared-boolean FALSE default. Their effective dates, 2026-07-22 and 2026-07-24, are outside the April-June evaluation window. China 2024-action and solar inputs likewise default FALSE pending note-31 membership tables.

The steel parameter is a Rev. 15 single-version 0.50 rate; the April-June window is entirely post-escalation. Rev. 15 has no operative 9903.81.x row: consolidated HTS 9903.82.02 covers primary and derivative steel and prints `Rates of duty (1-General): The duty provided in the applicable subheading + 50%`. The witness line 7202.11.10.00 is ferroalloy and outside note 16(c), consistent with the repaired note-16 primary-heading membership table, so the untouched witness correctly has no steel slot.

Each of 100 generated modules adds two outputs: `s232_steel_heading_rate` and `section_232_steel_component_rate` (200 new module outputs total). The coordinator should add these outputs to the ledger; this change does not edit the ledger.
