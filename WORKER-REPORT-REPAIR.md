# PR #1176 blockers 1 and 3 repair report

## Outcome

The defensive correctness and completeness audit is complete. The verified
implementation commit is
`bfadb955942721ce4bb31ea784a9d4beaede3f90`; the final branch head also includes
this report and the completed progress record. No push, GitHub write, signing,
or blocker-2 ProgramSpec manifest fingerprint repair was performed.

The blind-review report was read first from
`.git/review-worktrees/pr-1176-8d1f31d/REVIEW.md`. At the original PR head, both
SHA-verified reviewer reproducers demonstrated the fail-open:

- IPV: `388ab6983342ab97921508f4ae1fbec1626e6d9c437496f6402cb0720a93428c`
- probation/parole:
  `ed5d548cadeaa6ac714c5d70e54b09686c30fdfc513c0e770422ee72ca3ff392`

Each original reproducer passed with the unsafe expectations and produced the
two targeted assertion failures when changed to the required fail-closed
expectations.

## Defensive repair

The independent caller-populated
`calfresh_mce_member_of_household` relation was removed. The module now defines
the private derived relation
`calfresh_mce_canonical_member_of_household`, whose executable
`source_relation` is the fully qualified federal state-plan relation:

`us:policies/usda/snap/state-plan-composition#relation.member_of_household`

Its predicate is tautologically true, so it is a complete projection rather
than a filter. Both member-sensitive MCE gates range only over that projection:

- `calfresh_mce_household_exclusion_applies`
- the eligible-member existence aggregation in `calfresh_mce_status_conferred`

The benefit module performs no direct member-relation aggregation; its
resource, net-income, and zero-benefit rules consume MCE status instead.

The first direct-import implementation was not accepted on inspection alone.
Full compilation revealed that the bare short relation name remained an
unqualified implicit relation because the program contains two federal
relations with the same short name. The private projection fixes that compiler
ambiguity. The final compiled artifact contains no bare `member_of_household`
relation and no retired California input relation.

Three companion regressions preserve the reviewer's adversarial two-member
federal shape:

- omitted IPV-barred second member: household exclusion `holds`, MCE
  `not_holds`
- omitted probation/parole-barred second member: household exclusion `holds`,
  MCE `not_holds`
- omitted only-eligible second member: household exclusion `not_holds`, MCE
  `holds`

The pinned companion runner rejects the retired California relation key
because it no longer resolves to a declared data relation. Thus the literal
two-federal/one-California divergent dataset is no longer representable; the
green regressions exercise its canonical two-row equivalent. Existing benefit
cases were also migrated by merging California-only member facts into their
federal rows, including preservation of elderly/disabled facts.

## Excerpt repair

The ACIN excerpt was corrected from `Broad-Based` to the retained corpus row's
byte-verbatim `Broad- Based`. A programmatic UTF-8 sweep compared every proof
excerpt in both modules with every matching row in the pinned corpus:

- MCE module: 29/29
- benefit module: 9/9
- total: 38/38, with 0 missing citations and 0 byte mismatches

## Final gate evidence

All source-sensitive final gates used a fresh `git archive` of
`bfadb955942721ce4bb31ea784a9d4beaede3f90` extracted under the canonical
basename `rulespec-us`, with:

- corpus: `8af592162231e9de748ba6b98792b426ad4fe8b7`
- pinned encoder: `3869d66d009f52258be35901edbef370e65a399c`
- pinned composer: `fabe0b3b3fd6e90d3e8f075516f9b668f524f711`
- engine SHA-256:
  `6f4ae58db61cb72fdb0d42a497161c15fccf4e60b4ccd09795580b2dc1041007`

Results:

- full MCE and benefit companions: 47/47 cases, 2/2 compiled programs
- both module validations: `ci_pass=true`, `all_passed=true`, 0 errors
- proof validation: MCE 29/29 atoms; benefit 9/9 atoms; 0 issues
- repository layout and ProgramSpec contracts: 12/12 tests
- compose/compile: 328 derived outputs, 100 parameters, 3 relations
- relation graph: two pre-existing federal input relations plus one private
  derived CA projection sourced by the federal state-plan relation
- mutation (`eligible-member > 0` to `< 0`): 13 assertion failures confined to
  the three intended MCE-dependent benefit cases; untouched companion 12/12
- reverse index check: current, 4,250 provisions / 5,092 edges / 4,487 modules
- `git diff --check origin/main...HEAD`: clean

The mutation archive was moved intact to
`/private/tmp/pr1176-mutation-evidence-bfadb9559`; it did not alter the branch.

## Surface and oracle impact

Repair versus the original PR head:

- derived IDs: 0 added, 0 removed
- parameter IDs: 0 added, 0 removed
- removed caller-populated input relation:
  `us-ca:policies/cdss/snap/modified-categorical-eligibility#relation.calfresh_mce_member_of_household`
- added internal private derived relation:
  `us-ca:policies/cdss/snap/modified-categorical-eligibility#relation.calfresh_mce_canonical_member_of_household`

The program's public outputs remain `snap_eligible` and `snap_benefit`. No
public derived output was added, removed, or renamed by this repair. Therefore:

- new axiom-oracles mapping rows needed: none
- retired axiom-oracles mapping rows needed: none
- the already-merged 17 mapping rows remain unchanged

The retired California relation is an input-contract retirement, not an oracle
output retirement. Relative to `origin/main`, the PR still adds its existing 20
derived outputs and one parameter; this repair adds only the private derived
relation and no new caller-populated relation.

## Scope and handoff

The pre-existing untracked `WORKER-REPORT.md` was left untouched. The branch
diff contains only the PR's CA modules/companions, ProgramSpec, encoding
manifests, reverse index, and the two explicitly required progress/report
files.

Blocker 2 remains deliberately out of scope. Because this repair changes
module/test bytes, the main lane must refresh and re-sign the affected encoding
and ProgramSpec manifests before merge.

GitNexus graph tools were unavailable in this session, so dependency and
surface checks used direct source tracing and normalized compiled-artifact
comparisons. One attempt to patch a disposable mutation archive directly under
`/private/tmp` was rejected by the filesystem sandbox; the same archive was
created under the writable worktree, patched there, run, and then moved intact
to `/private/tmp`. No requested gate was skipped, and no source change was lost.
