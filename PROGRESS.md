# Lane E witness-line encode progress

## State

The witness-line encoding and every gate permitted by the required unsigned
handoff are complete on branch `laneE/tariff-witness-encode` from
`47a176d02`. The tracked tree is ready for operator signing and transplant.

## Done

- Read `.laneE-encode-inputs/SPEC.md` before taking build actions.
- Verified the requested worktree, branch, base commit, and untracked input area.
- Read the root `CLAUDE.md` and inspected the existing tariff composition and
  companion-test idioms for entry facts, MFN selection, section 232, section
  301, proof atoms, and component totals.
- Confirmed that the panel-facing total is expressed as an ad-valorem rate and
  currently has no aluminum-content-value input.
- Verified exact corpus excerpts and date/version behavior for both witness
  lines, section 201, section 338, beer section 232, beer section 301, and
  solar section 301 against corpus commit `ed7d4e4f`.
- Verified the working-oracle schedules and identified the two deliberate
  law/oracle differences: Yale's flat full-value beer section 232 proxy before
  April 6 and its expired 14.5 percent solar section 201 proxy.
- Fixed the representation choice: expose a date-sensitive beer section 232
  content-basis applicability judgment, return no false flat rate from the
  existing ad-valorem component, and document that the non-flat amount is
  outside the five-input total.
- Verified the hand-edited pending-ledger format and baseline: 3,208 entries,
  ceiling 3,208, with one entry required for every added composition rule.
- Added `entry_is_line_d` and `entry_is_line_e` with parent and statistical-line
  proof atoms, registered their authority paths, and extended MFN selection.
- Preserved beer's 13.2 cents-per-liter column 2 rate as non-ad-valorem rather
  than converting it; encoded solar's 35 percent column 2 branch through a
  separately proved rate parameter.
- Confirmed the edited composition parses as YAML with 109 rules and passes
  `git diff --check` at this checkpoint.
- Added an evidence-rich zero section 201 component grounded in all four staged
  rates, the 5 GW quota change, the February 6 end date, and the HTS compiler's
  expiry note.
- Added beer section 232 content-basis applicability through April 5 and its
  Proclamation 11021 termination from April 6; the flat component explicitly
  returns no full-value proxy for that non-flat charge.
- Added the Canada beer section 338 component with its August 19 boundary,
  stacking language, and section 232/civil-aircraft exception authorities.
- Extended China section 301 to 25 percent for beer and 50 percent for solar,
  and added section 201 and section 338 to the total.
- Confirmed the composition parses with 112 unique rules and 254 proof atoms,
  with `git diff --check` clean.
- Split both IEEPA outputs at the dispatch-required February 20 SCOTUS
  handoff: the new February 20–23 zero version is grounded in EO 14389's date
  and termination language, while the February 24 replacement zero remains a
  separate version. The composition now has 258 proof atoms.
- Added 10 companion cases (131 total) covering line D/E polarity, beer section
  232 April 5/6, section 338 August 18/19 and country/product polarity, lawful
  section 201 zero, beer/solar China section 301, IEEPA February 19/20,
  section 122, and forced labor.
- Extracted the solar column 2, solar China section 301, and Canada alcohol
  section 338 rates into separately proved parameters so component formulas do
  not embed legal scalar literals. The final composition has 115 unique rules
  and 261 proof atoms, and the companion cases expose all three parameters.
- Ran the canonical engine battery successfully: 131/131 cases passed.
- Hand-edited the pending ledger by +8 rules and raised its ceiling from 3,208
  to 3,216; verified sorted/unique exact coverage for all 115 composition rules.
- Regenerated the reverse index: 4,521 provisions, 5,510 edges, and 4,672
  modules. The prescribed ephemeral `--with pyyaml` form could not reach PyPI,
  so the same script ran from the existing encode environment with
  `--no-sync`; no dependency or toolchain changed.
- Ran the canonical pending ratchet successfully: 3,216 declared, 3,216
  applied, zero stale.
- Passed canonical `axiom-encode validate --skip-reviewers` with CI enabled.
- Passed canonical `proof-validate`: 261 atoms checked.
- Passed the full oracle-coverage gate with `GATE_OK`, zero untested comparable
  outputs, and zero incomplete comparable outputs.
- Ran the repository suite from the prescribed encode interpreter using the
  locally available offline pytest packages. The raw unsigned run produced 73
  passes and the sole expected manifest-hash failure for `composition.yaml`;
  the unsigned-compatible run produced 73 passes with that one operator-only
  signing assertion deselected.
- Confirmed final `git diff --check` is clean. The reverse-index, ledger, and
  manifest-provenance tests all pass; the applied-files manifest remains
  deliberately untouched and unsigned.

## Next

- Operator signs the applied-files record for `composition.yaml` and
  `composition.test.yaml` with the manual composition exception.
- Operator transplants the single feature commit and pushes it; this build does
  not push the local-origin branch.
