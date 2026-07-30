# PR #1176 round-3 guard subreview

## Result

The source-anchored cardinality guard is sound for the requested adversarial
surface at exact target
`0e042edd42d29e47e39f5b2f5a3ab7085cffe90b`.

Tuple order below is:

`(federal anchor count, canonical integrity, household exclusion, MCE status)`.

| Case | Exact actual tuple | Catch mechanism |
| --- | --- | --- |
| `caller_injected_eligible_canonical_member_fails_closed` | `(1, not_holds, holds, not_holds)` | Cardinality guard. The derived source member remains in the local union and the injected eligible local member adds a second identity. |
| `caller_cannot_spoof_derived_membership_integrity_outputs` | `(1, not_holds, holds, not_holds)` | Cardinality guard. Caller-supplied scalar values under the derived helper IDs do not override their formulas. |
| `rows_added_to_both_surfaces_keep_counts_equal` | `(2, holds, holds, not_holds)` | Same-row exclusion scan. The direct local edges duplicate the two anchor identities, so counts remain equal; `ipv_both` evaluates `calfresh_mce_member_household_exclusion_applies=holds` and the household scan rejects MCE. |
| `equal_supplied_cardinality_membership_swap` | `(1, not_holds, holds, not_holds)` | Cardinality guard. The one anchor row is `excluded_source` (`calfresh_mce_member_eligible=not_holds`) and the one direct local row is the distinct `eligible_replacement` (`calfresh_mce_member_eligible=holds`). Projection preserves the source identity, so the computed local union has two identities even though each supplied list has one. |
| `inconsistent_rows_fed_directly_to_anchor` | `(2, holds, holds, not_holds)` | Same-row exclusion scan. Both anchor rows project into the local canonical relation; `ipv_injected_anchor` evaluates `calfresh_mce_member_household_exclusion_applies=holds`. |

All five target cases returned their lawful fail-closed outputs. The committed
predecessor fixture passed 2/2 cases, and the three explicit-identity
completeness probes passed 3/3.

## Mutation isolation

The only source mutation was:

```yaml
calfresh_mce_canonical_membership_integrity_verified:
  formula: true
```

It was committed locally as `b8df807c3`, tested, and restored as
`f9febb78f`. No PR branch or remote was changed.

- Guard enabled: the exact committed divergent fixture passed 2/2 cases with
  zero failures.
- Guard disabled, lawful expectations retained: 0/2 cases passed and the
  runner emitted six targeted output failures. Both actual tuples became
  `(1, holds, not_holds, holds)`.
- Guard disabled, those actual unsafe outputs used as expectations: both
  divergent cases passed wrongly, 2/2 with zero failures.
- Guard restored: source SHA-256 returned to
  `ba01095a1d8619ece130958a128a662011c685ede2e564802f90b46e3bc628dc`,
  `git diff 0e042edd -- <MCE module>` was empty, and the lawful fixture returned
  to 2/2 green.
- Running the three explicit-identity probes against the disabled artifact
  independently isolated the catch paths: the both-surface and anchor-only IPV
  cases remained fail-closed, while only
  `equal_supplied_cardinality_membership_swap` flipped to
  `(1, holds, not_holds, holds)`.

## Reproducible artifacts

- Exact target canonical-basename fixture root:
  `/private/tmp/pr1176-guard-a91/exact/rulespec-us`
- Disabled guard + lawful expectations:
  `/private/tmp/pr1176-guard-a91/disabled-safe/rulespec-us`
- Disabled guard + unsafe expectations:
  `/private/tmp/pr1176-guard-a91/disabled-unsafe/rulespec-us`
- Target compiled MCE artifact:
  `/private/tmp/pr1176-guard-a91/mce.compiled.json`
- Disabled compiled MCE artifact:
  `/private/tmp/pr1176-guard-a91/mce-disabled.compiled.json`
- Explicit-identity fixtures:
  `review-artifacts/guard-probes.yaml`
- Explicit-identity runner:
  `review-artifacts/run_guard_probes.py`

Relevant SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| Workflow-pinned engine binary | `674ca6e70afdccb59c3d6847933bc24b4590105e49db54790f2dcd0bdbbe32d7` |
| Target MCE module | `ba01095a1d8619ece130958a128a662011c685ede2e564802f90b46e3bc628dc` |
| Disabled MCE module | `2607d55f9714c378285920c5b4bc42ab71ae7287fb4fcf37f289d3998ac62afa` |
| Exact committed injection fixture | `8ac83ee34603c2798ac891248f4656e27f7989edf3d5703609f69f4c5530f663` |
| Disabled unsafe-expectation fixture | `3ff2ae3231bb01a94cae3a86429e9a4af4504e65cb39eda7f5514a0695174685` |
| Target compiled artifact | `f36fedecb7eef0469c4494d31edef28c3304a2e1e8523f9a09337fd53e1d95f6` |
| Disabled compiled artifact | `d1497926b21dbb05f819b89f410367e96284482ee9f8d6b816d2d6a71007aa20` |
| Explicit-identity fixtures | `dc133cc2a2140d69e7e43b5dfea22dbee93039088ef4a0fb3961be381b6f7d52` |
| Explicit-identity runner | `132c9d368a9565ad7710eeb07b84b333d733c77f418f35e1174eeebea5329415` |

All runs used:

```text
AXIOM_CORPUS_REPO=/Users/maxghenis/TheAxiomFoundation/axiom-corpus/.worktrees/pin-8af59216
engine=/private/tmp/pr1176-companion-suite.VXXz3g/axiom-rules-engine/target/release/axiom-rules-engine
```

The companion command shape was:

```text
axiom-encode test --root <canonical rulespec-us root> \
  --axiom-rules-engine-path /private/tmp/pr1176-companion-suite.VXXz3g/axiom-rules-engine \
  --json <canonical MCE companion>
```

The explicit-identity command shape was:

```text
python review-artifacts/run_guard_probes.py \
  --engine <engine> \
  --artifact <target-or-disabled-compiled-artifact> \
  --fixtures review-artifacts/guard-probes.yaml
```

## Limitations and disclosures

The installed GitNexus CLI reported `Repository not indexed`, so no graph
result was available for this narrow executable probe. Direct source,
compiled-artifact, and runtime evidence supplied the mechanism analysis.
An `npx --no-install gitnexus status` attempt did not return within 30 seconds
and was interrupted; the installed binary returned the unindexed result
immediately. No sandbox denial affected compilation or execution, and no
remote, GitHub, corpus, PR-branch, or root-ledger write was made.
