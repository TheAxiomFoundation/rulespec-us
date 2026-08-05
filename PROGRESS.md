# Progress — §112 combat-zone month rules

## State

- Branch: `closure/w5-eitc-112-combat`
- Checkout: `.git/codex-worktrees/w5-eitc-112-combat` (the requested sibling worktree path is outside the writable sandbox)
- Scope: EITC frontier items 19–23, the 26 U.S.C. §112 combat-zone and missing-status month rules
- Status: complete locally; manifest signing, push, and draft PR are blocked
  by unavailable maintainer credentials/network

## Done

- Read the encoder preamble and repository agent rules.
- Created the requested branch from `origin/main`.
- Created this committed progress ledger at the start of work.
- Resolved the assignment numbering: items 19–23 among the 23
  must-encode entries are classification rows 29, 30, 31, 32, and 34.
- Scanned every statute inventory at corpus pin
  `bf97b17baebfdf12601f7c23697524bf5adcdaed`. The relevant §112 paths occur
  only in the 2026-07-13 recovery inventory; Title 5 §5561 and the required
  Title 37 pay provisions do not occur in any inventory.
- Read the bodies at 26 U.S.C. §112(a), (a)(2), (b), (b)(2), (c)(2),
  (c)(3), (c)(5), (d)(2), and (d)(3), each with expression date 2026-07-13.
- Chosen disposition:
  - encode the hospitalization/service/causation composition in
    §112(a)(2), (b)(2), and (c)(2)–(3);
  - encode the final-sentence January 1978 boundary in §112(a) and (b);
  - defer the civilian missing-status output on absent 5 U.S.C. §5561(4)–(5);
  - defer the maximum enlisted amount on absent Title 37 pay provisions;
  - defer post-termination month computation on absent controlling
    Presidential termination designations.
- Identified an existing unit mismatch: the consumer compares a count named
  in months to a parameter encoded as 2 years. The implementation now
  multiplies the source-stated 2-year limit by the 12-month calendar-unit
  factor retained at 26 U.S.C. §7701(a)(24), and tests months 24 and 25.
- Checked both inventory records for `us/statute/26/7701/a/24` at the corpus
  pin (the original and deduplicated Title 26 inventories); their bodies and
  identifiers agree.
- Added executable Judgment outputs for:
  - the hospitalization/service/medical-causation composition; and
  - the Vietnam hospitalization month boundary after January 1978.
- Added honest `deferred_outputs` entries for:
  - civilian missing status (absent 5 U.S.C. §5561 definitions and retained
    Vietnam termination designation);
  - maximum enlisted amount (absent 37 U.S.C. pay table, §310, and §351);
  - post-termination month computation (absent retained zone-specific
    Presidential termination designations).
- Rebound the §112, §32(c)(2), §32, and §24(d) fixtures from the two former
  implicit frontier inputs to their new primitive facts, and refreshed the
  exact §112 import hashes in §32(c)(2) and §24(d).
- The §112 companion now has 13 cases (up from 4), covering every
  hospitalization conjunct, months 24/25, January/February 1978, non-Vietnam
  service, the hospitalization exclusion, and the unaffected direct-service
  branch.
- Focused validation with pinned `axiom-encode` 0.2.1200:
  - `validate --skip-reviewers` passes for §112, §32(c)(2), and §24(d);
  - §112 proof validation passes with 20 atoms;
  - all 25 cases across §112, §32(c)(2), §24(d), and root §32 pass.
- Refreshed the stale root §32 companion inputs and output assertion to the
  current §32(c)(2) interface; this removed four baseline fixture failures.
- Regenerated and checked `.axiom/index/provisions_to_rules.json` (4,246
  provisions, 5,085 edges, 4,486 modules).
- Ran the repository suite: 64 tests pass; the sole failure is the signed
  manifest drift check for the three intentionally changed modules.
- Ran the official signing workflow:
  - dry-run identifies four manifests covering seven changed RuleSpec files;
  - signing cannot proceed because `AXIOM_ENCODE_APPLY_SIGNING_KEY` is absent;
  - `guard-generated` consequently reports those same seven files.
- Left all existing signed manifests untouched for a maintainer with the
  signing key to refresh.
- Attempted to push `closure/w5-eitc-112-combat`; DNS resolution for
  `github.com` failed, so no remote branch or draft PR could be created.
- Attempted to write the requested closure-sprint output file; the sandbox
  rejected the path because it is outside the writable workspace. Preserved
  the complete handoff in committed `FINAL_REPORT.md`.

## Next

1. With `AXIOM_ENCODE_APPLY_SIGNING_KEY`, run the official signer for the four
   manifests covering the seven changed RuleSpec files.
2. Rerun the repository suite and generated-change guard.
3. Copy `FINAL_REPORT.md` to the requested closure-sprint output path.
4. Push the branch and open the draft PR titled
   `Encode §112 combat-zone month rules (EITC frontier)`, referencing
   `rulespec-us#1135`.
