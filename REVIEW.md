VERDICT: REQUEST-CHANGES

# PR #1176 repair-round re-review

## Evidence digest

Reviewed exact live PR head
`686d413cfe15410dc160010f7863096c8c20ef48`
(`fed-parity/ca-bbce`). A final read-only GitHub query confirmed the PR was
open, mergeable, non-draft, still at that exact head, and contained 11 changed
files. The head is the manifest re-sign commit directly after the expected
repair evidence commit
`79ad71497a291f0bde3a827f6d3ac556b4f87a66`.

Two of the three prior blockers are fully repaired:

- The ProgramSpec manifest has the correct bare citation, content hashes,
  ancestor attestation, supersession history, and encode#1322-compatible
  routing provenance.
- All 38 proof excerpts are byte-verbatim against every matching retained row
  in the clean pinned corpus, including `Broad- Based`.

The old independent relation is also retired correctly: both SHA-verified
predecessor reproducers are rejected as undeclared. Approval remains blocked,
however, because the replacement `private` derived relation is itself
caller-populable. The pinned engine unions caller-supplied rows with its
source-derived rows. An adversarial caller can therefore inject an eligible
member absent from the federal relation and falsely change MCE from
`not_holds` to `holds`.

## Blocking finding

### High — the private canonical projection can still diverge through direct input

The MCE module declares
`calfresh_mce_canonical_member_of_household` as a derived relation at
`us-ca/policies/cdss/snap/modified-categorical-eligibility.yaml:47`. Its source
is the fully qualified federal state-plan relation at line 52, its
`private: true` metadata is at line 56, and its tautological predicate is at
line 66. Static aggregation scope is otherwise correct:

- household exclusion scans it at lines 169–172;
- eligible-member existence scans it at lines 424–427; and
- the benefit module contains no member-scanning aggregation.

The privacy marker is not an executable dataset restriction. In the compiled
artifact, the canonical relation is a normal declared relation with a
derivation and no private/input-prohibition field. At pinned engine commit
`ffd8213271947b0189a9dd61a055c1e0e78908a0`:

- `src/spec.rs:1149-1159` accepts a dataset relation whenever its name resolves
  to any declared relation;
- `src/engine.rs:740-747` first collects direct caller-supplied records for
  that relation; and
- `src/engine.rs:749-782` appends records projected from its federal source.

The direct and derived rows are therefore a union, not an immutable
projection.

I reproduced the fail-open from an exact-head canonical-basename archive. In
the existing only-excluded-member case, the federal relation contained one
excluded member. I directly populated the private canonical relation with a
second, eligible member absent federally. The pinned runner accepted the
derived relation key and the actual result became:

`calfresh_mce_status_conferred = holds`

The companion retained the legally required `not_holds` expectation, so the
run produced exactly one targeted failure across 35 cases. Evidence:

- probe:
  `/private/tmp/pr1176-rereview-projection-injection-686d413`
- fixture SHA-256:
  `a652857f11f99949a959acbd38951d4a0dcd598d1b264c5149d296ae85d03ad8`
- result SHA-256:
  `9a4d9cc94eec5b6b757d9e6fb9e6375be71d5f40b84c50cd045ec9b8398c9118`

An independent probe confirmed the same behavior with an explicit
unsafe/control pair:

- injected fixture SHA-256
  `2cd77445112f14c6513505dc1fce99e4c32ba02ab30c5c15366aa2b958731e25`:
  federal relation has only an SSI-cash-out-excluded member; a direct canonical
  row supplies an eligible member; unsafe `holds` expectation passes 35/35;
- control fixture SHA-256
  `3a03a63c25c1e6f6a10ef9f37d96beee95130de899183905f7d188bb9109a3af`:
  no direct canonical rows; correct `not_holds` expectation passes 35/35.

This preserves the substantive fail-open through a new input name. The repair
must make derived/private relations invalid dataset inputs, or otherwise make
the aggregations range over a relation whose population cannot be supplied
independently. Add a regression proving that direct input under
`#relation.calfresh_mce_canonical_member_of_household` is rejected.

## Claimed repair checks

### Retired relation and declared regressions

The predecessor artifacts retained their exact hashes:

- IPV:
  `388ab6983342ab97921508f4ae1fbec1626e6d9c437496f6402cb0720a93428c`
- probation/parole:
  `ed5d548cadeaa6ac714c5d70e54b09686c30fdfc513c0e770422ee72ca3ff392`

Each exact file was substituted only inside a disposable exact-head archive
and run with pinned encoder `3869d66d...` and the pinned engine. Each exited
nonzero with 24 failures across 32 cases, all reporting that
`#relation.calfresh_mce_member_of_household` does not resolve to a declared
relation. The restored companion hash was
`bfcd734d642d38524d29e4c36eebf6bbe473042b9166ae6091a188e026270270`.

The three new canonical regressions have the claimed outcomes:

- IPV omission (`.test.yaml:446-494`): exclusion `holds`, MCE `not_holds`;
- probation/parole omission (`:495-542`): exclusion `holds`, MCE `not_holds`;
- eligible-member omission (`:543-590`): exclusion `not_holds`, MCE `holds`.

The unmodified companions passed 47/47 cases across two compiled programs.
The new blocker is not covered because none of those cases attempts direct
population of the declared derived relation.

### ProgramSpec manifest

The re-sign commit `686d413cf` has parent `79ad71497` and changes only the
three manifest JSON files. The ProgramSpec manifest records exactly:

`"citation": "programs/us-ca/snap/fy-2026"`

All five applied-file SHA-256 values match the bytes at both the direct parent
and the target:

| Applied file | SHA-256 |
| --- | --- |
| `programs/us-ca/snap/fy-2026.yaml` | `1868d8431567654c48e65b4b37a86c93400efa3ff78dc9aca0d351318453a0a2` |
| benefit companion | `5914bbc9f6822e2fdc385fece397d4f6291f69f29b0836af5a828ac189d19177` |
| benefit module | `a02c74c91457ac9aff7189ff069f54d9bbad0e760a59272fa82cf5d058ffc036` |
| MCE companion | `bfcd734d642d38524d29e4c36eebf6bbe473042b9166ae6091a188e026270270` |
| MCE module | `e3f0cba2db961677b93da24ff6246dfed52da6ca60b9f91e308e8015e3170adc` |

Their last-change commits are ancestors of `79ad71497`, and all three
supersession hashes and prior signatures match their historical manifests.

The recorded encoder bridge is clean at
`7121774c254ca8b34d05009202a32d7e6f7d16d7`, with ancestry
`3869d66d -> 0114ccb3 -> 7121774c` and version `0.2.1201`.
The merged encode#1322 regression requires exactly
`programs/us-sc/snap/fy-2026`; its focused test passed 1/1, and the bridge
helper returned the analogous bare CA citation and manifest path.

The three HMAC fields are structurally valid, but cryptographic authentication
could not be repeated because the signing key was unavailable. Content,
ancestry, routing, provenance, and supersession checks passed.

### Excerpt fidelity

The pinned corpus worktree was clean at
`8af592162231e9de748ba6b98792b426ad4fe8b7`. A strict UTF-8 comparison, with no
normalization, checked every proof excerpt against every retained row having
the same exact citation path:

- MCE module: 29 atoms;
- benefit module: 9 atoms;
- total: 38/38 atoms;
- atom × retained-row comparisons: 59/59;
- missing citations: 0;
- byte mismatches: 0.

The repaired excerpt at MCE line 103 contains `Broad- Based`. The controlling
ACIN row contains those exact bytes and contains zero instances of the old
`Broad-Based` spelling.

## Executable and containment evidence

All source-sensitive gates used a fresh `git archive` of the exact target
under the canonical basename `rulespec-us`.

- companions: 47/47, two test files, two compiled programs;
- pinned validation: both modules `ci_pass=true`, `all_passed=true`, zero
  errors;
- proof validation: 29/29 MCE atoms and 9/9 benefit atoms;
- mutation (`eligible-member > 0` to `< 0`): 13 assertion failures confined to
  exactly three MCE-dependent benefit cases (5 resource-waiver, 5 net-waiver,
  3 zero-benefit); restoration returned the module SHA above and 47/47 green;
- compose/compile: 328 derived outputs, 100 parameters, three relations;
- repository layout and ProgramSpec contracts: 12/12;
- reverse-index tests: 6/6; committed index current at 4,250 provisions,
  5,092 edges, and 4,487 modules;
- `git diff --check origin/main...686d413cf`: clean.

Compiled repair-vs-original-PR-head comparison shows narrow intended impact:

- derived IDs: 0 added, 0 removed;
- parameter IDs: 0 added, 0 removed;
- changed derived definitions: only
  `calfresh_mce_household_exclusion_applies` and
  `calfresh_mce_status_conferred`;
- relation change: retire the old CA input relation and add the derived CA
  relation;
- units, module metadata, and extension shape: identical.

The 32 unaffected ProgramSpecs were explicitly not in dispute. The repair
sequence changes no other ProgramSpec or non-CA module, so it does not widen
that prior non-regression surface.

The live 11-file GitHub diff and local `origin/main...target` diff agree:
three manifests, the reverse index, required progress/report files, the CA
SNAP ProgramSpec, and the two CA modules with their companions. There are no
workflow, toolchain, mode, or foreign-jurisdiction changes.

Mapping containment also passes. Merged axiom-oracles PR #424 added exactly 17
rule-output mapping rows. None references either relation name and none has a
`#relation.` legal ID. The repair changes an input/relation contract, not a
public mapped output.

## Limitations and sandbox disclosures

- HMAC authentication was not rerun because no signing key was available.
- GitNexus graph tools were not exposed and the CLI reported this repository
  unindexed. Direct source, compiled-artifact, diff, and execution analysis
  supplied the blast-radius evidence.
- A first attempt to patch a disposable mutation under `/private/tmp` was
  denied because the patch helper only writes inside the project. No file was
  changed; the mutation was rerun in review-local scratch, restored, verified
  green, and moved to `/private/tmp`.
- The first focused encode regression passed its test but pytest-cov was
  denied writing `.coverage` in the external read-only worktree. It was rerun
  with coverage and cache writes disabled and passed 1/1.
- `uv` could not initialize its home cache, and the ambient `pytest` wrapper
  referenced a missing interpreter. Existing pinned/repository virtual
  environments ran every required gate successfully.
- One subtask's diagnostic `tee /dev/stderr` and direct `gh`/`npx` network
  attempts were denied. Local exact commits plus the connected read-only
  GitHub service supplied the same checks.

No PR branch, remote, corpus, author worktree, or GitHub state was modified.
All review commits exist only on local branch
`review/pr-1176-repair-686d413` under `.git/review-worktrees/`.
