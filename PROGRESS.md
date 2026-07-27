# 7 CFR 273.11 remainder encoding

## State

- Branch: `encode-273-11-remainder`
- Base: `origin/main` at `1158ba5b2`
- Claim: `rulespec-us#1135`
- Scope: encode the point-in-time computational remainder of 7 CFR 273.11,
  preserving the existing paragraph (c) module and classifying purely
  procedural paragraphs for follow-up.
- Source: `us/regulation/7/273/11` in
  `_closure-sprint/data/cfr-273.jsonl` (source as of 2026-07-09).
- Worktree was clean at task start.

## Done

- Read the repository `CLAUDE.md`; it references no additional agent or
  contribution instructions.
- Read the existing `273/11/c.yaml` and companion test.
- Read `273/9.yaml` and `273/10.yaml` for SNAP income and allotment conventions.
- Read the complete cited source text for 7 CFR 273.11(a)-(s).
- Located and smoke-tested the repository's pinned `axiom-encode` 0.2.1200
  toolchain against the existing paragraph (c) proof and companion tests.
- Classified the current section as follows:

  | Paragraph | Treatment in this change |
  | --- | --- |
  | (a) | Encode self-employment averaging, anticipation, farm losses, capital gains, and benefit-level proration envelope. |
  | (b) | Encode actual and simplified allowable-cost methods, including boarder caps; defer the stale foster-care-boarder cross-reference. |
  | (c) | Preserve existing (c)(1)-(2) encoding and (c)(3) deferral; classify (c)(4) notice/hearing workflow as procedural. |
  | (d) | Encode other-nonhousehold-member income, resource, expense, wage, and household-size treatment. |
  | (e) | Encode DAA-resident certification/size and deterministic departure balances; classify administrative mechanics separately. |
  | (f) | Encode GLA qualification/size and deterministic departure balances; classify administrative mechanics separately. |
  | (g) | Encode battered-shelter separate-household, allotment-limit, income/resource, and shelter-expense rules. |
  | (h) | Encode homeless-household prepared-meal purchase permission. |
  | (i) | Skip as prerelease application-timing and cross-reference procedure. |
  | (j) | Encode the current no-increase rule and optional penalty ceiling; classify plans, restoration, and unrelated-change processing as procedural. |
  | (k) | Encode the current comparable-disqualification state option and mandatory FDPIR branch; classify plans/restoration processing separately. |
  | (l) | Skip because it expressly creates no independent SNAP sanction authority. |
  | (m) | Encode drug-felony member eligibility, state relief, and cutoff. |
  | (n) | Encode fleeing-felon/probation-parole status and adverse-action timing gates; skip application-processing workflow. |
  | (o) | Encode the custodial-parent cooperation state option and point-in-time exceptions; classify notice/evidence/requalification procedure separately. |
  | (p) | Encode the noncustodial-parent cooperation state option and refusal determination; classify notice/privacy/requalification procedure separately. |
  | (q) | Encode the child-support-arrears state option and exceptions; skip claim-collection procedure. |
  | (r) | Encode substantial-winnings disqualification and reentry conditions; skip reporting/action procedure. |
  | (s) | Encode qualifying-conviction, sentence/restriction, and conduct-date conditions. |
- Implemented and committed companion-tested modules for paragraphs (a), (b),
  (d), (e), (f), (g), (h), (j), (k), (m), and (n).
- The pinned `axiom-encode` validator, proof validator, and rules-engine
  companion tests pass for each committed module:

  | Module | Proof atoms | Test cases |
  | --- | ---: | ---: |
  | `273/11/a` | 24 | 5 |
  | `273/11/b` | 18 | 10 |
  | `273/11/d` | 11 | 4 |
  | `273/11/e` | 9 | 4 |
  | `273/11/f` | 13 | 5 |
  | `273/11/g` | 8 | 4 |
  | `273/11/h` | 1 | 3 |
  | `273/11/j` | 11 | 5 |
  | `273/11/k` | 12 | 5 |
  | `273/11/m` | 5 | 6 |
  | `273/11/n` | 30 | 9 |

## Next

- Finish and validate the state-option modules for paragraphs (o)-(q).
- Finish and validate the substantial-winnings and convicted-felon modules for
  paragraphs (r)-(s).
- Run the full relevant local checks, finalize this progress record and the
  requested output report, then push and open an unmerged PR referencing #1135.
