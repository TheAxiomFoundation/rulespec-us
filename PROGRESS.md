# PR #1179 Repair Progress

## State

- Defensive correctness and completeness audit in progress on
  `fed-parity/chunk2-taxable-income`.
- Starting point verified at the current local pushed head
  `4ced8fb7065311338ea732cab0a26105e750c40f`.
- Scope is limited to the five blockers in the frozen PR review plus mechanics
  directly affected by their repair.
- All five review blockers now have source/test repairs in place; final
  mechanical regeneration and full canonical gate execution remain.
- The existing composition manifest is intentionally not re-signed here; its
  applied-file hashes must be refreshed by the authorized main lane after all
  repair content is final.

## Done

- Read the frozen adversarial review at commit `f58fc22a6`.
- Confirmed the branch, `HEAD`, and
  `origin/fed-parity/chunk2-taxable-income` all resolve to the reviewed head.
- Confirmed the only pre-existing worktree change is untracked
  `WORKER-REPORT.md`; it will be preserved and excluded from repair commits.
- Extended the executable relation-schema registry to the §151 exemption and
  senior `(TaxUnit, Person)` relations and the §170(p) charity
  `(TaxUnit, Payment)` relation.
- Demonstrated that reversing each registered argument vector independently
  fails the schema test, restored each imported module byte-for-byte, and
  reconfirmed the positive test after every restoration.
- Replaced the pre-OBBBA §165(d) proof with the resolver-selected current
  sentence proving both the 90-percent-of-losses limitation and wagering-gain
  ceiling, and made the completed input boundary explicit after both limits.
- Added byte-verbatim §61, §62, and §63(a) atoms to bridge the itemizer branch
  into the final alongside the retained §63(b) proof.
- Confirmed every new or retained §61/§62/§63/§165 excerpt is an exact byte
  substring of its resolver-selected pinned-corpus body.
- Added a companion-only §151 diagnostic in which a real $10,000 §931
  exclusion raises single-senior MAGI from $75,000 to $85,000, reduces the
  senior amount to $5,400, produces $23,550 total deductions, and yields
  $51,450 taxable income.
- Confirmed the expanded pinned companion passes all 28 cases.
- Made the individual verified-domain guard reject a simultaneous
  estate/trust/common-trust-fund/partnership fact.
- Converted the former entity-standard-deduction fixture into an explicit
  contradictory-facts regression that asserts the imported disqualifier still
  holds while the local guard, deductions, and taxable income fail closed.
- Regenerated the reverse index after the §61/§62 bridge atoms; the only
  semantic delta marks those two existing taxable-pipeline edges as
  `proof_atom` as well as `module`, with provision/edge/module counts unchanged
  at 4,249/5,120/4,491.
- Corrected the MAGI fixture after pinned validation rejected merge-key
  overrides: common §931 zero facts and the positive-addback variant now use
  disjoint anchors, so the strict YAML loader and companion runner agree.
- Reconfirmed the pinned companion at 28/28 and pinned module validation with
  `ci_pass=true`, `all_passed=true`, and zero errors in the working tree.

## Next

- Run all required canonical archive gates and ledger/diff audits.
- Commit the final progress state and write the untracked repair report.
