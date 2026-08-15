# B1.6-C report — generalized component surface

## Outcome

The generated compositions are decoupled from exemplar flags at the authority-component layer. China list123/list4A, aluminum, steel, CSPV, section-122 exemption/section-232 coverage, Brazil, forced-labor, China-2024, and solar now have explicit caller inputs. Beer/section-338 retains exact `entry_is_line_d` semantics. The hand-built five-line witness was not changed.

Section 232 steel adds `s232_steel_heading_rate` and `section_232_steel_component_rate` to every generated module and to `schedule_statutory_stack`: 2 outputs/module, 200 outputs total. Ledger action is left to the coordinator.

## Steel proof

- Rev. 15 consolidated 9903.82.02 (primary and derivative steel): `Rates of duty (1-General): The duty provided in the applicable subheading + 50%`.

The task's 9903.81.x locator is stale for this corpus vintage: Rev. 15 contains no operative 9903.81.x row and consolidates the charge at 9903.82.02. April-June is wholly post-escalation. HTS 7202.11.10.00 is ferroalloy outside note 16(c), so the witness has no steel slot.

## Gates

- G1 PASS: 300 deterministic outputs; full `--check` clean.
- G2 PASS: 342 exact + 18 explained / 360 executable total-stack cells; zero unexplained. The 18 are 2026-08-01 Brazil/forced-labor own-list corrections on ch95/ch85. Beer line-D remains an exact structural component check because the schedule total is non-ad-valorem/unavailable.
- G3 PASS: 1,300 comparisons over 100 certified cells; 91 exact cells, 9 explained coupling-bound ch95 cells, zero unexplained. Every delta is enumerated in `c-g3-certified-replay.json`.
- G4 PASS: ch72/ch76/ch95 plus ch01/ch22/ch99a.
- Flag tests PASS: 7/7. German HTS 0203.29.20.00 is list123 TRUE, section-122-exempt FALSE, and section-232-covered FALSE, so the existing section-122 window/rate machinery now applies.

Implementation commit: `c27e3d99fbb61b311fd47de1fd53969ef1c63dfb`. Evidence/report commit is recorded by the final handoff.
