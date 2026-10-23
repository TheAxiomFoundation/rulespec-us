# Program Artifact Pipeline

`programs/` specs are source; compiled artifacts are build outputs and are
never committed. The `program-artifacts` workflow compiles every spec through
axiom-compose + axiom-rules-engine (pinned refs in the workflow env):

- **On PRs** it is a gate: any spec outside `tools/known-broken-specs.txt`
  that fails to compile fails the check, so spec/corpus drift (renamed module
  paths, coverage-gate violations) is caught at PR time.
- **On main** it publishes `dist/` — provenance-stamped `*.compiled.json`,
  composed `*.rulespec.yaml`, and `manifest.json` — as a GitHub release
  tagged `program-artifacts-<shortsha>`.

Every artifact's `metadata.provenance` records the corpus SHA, spec path +
sha256, composer version, and engine version; the manifest carries the same
plus artifact sha256s. Given a corpus commit and the pinned toolchain, the
build is byte-reproducible.

Consumers (axiom-api) pin a release tag and per-file sha256s instead of
vendoring artifacts. To admit a program: land its spec here, wait for the
release, then bump the consumer's pin.

## Artifact names and legal periods

A spec's legal identity is `(jurisdiction, program_id, period)`:
`jurisdiction` and `program_id` are the first and last segments of its
`program:` field, and `period` is its `period:` value. Both fields are read
with surrounding whitespace stripped, as axiom-compose reads them.
axiom-compose's behavior depends on `program:` only through those two
segments: the first sets the allowed import prefixes and the `state:` scope
prefix, and the last is the auto-gate program token. The middle segments
appear only in labels (the composition target and summary). One program can
have any number of periods; each is its own spec file and its own artifact.

Each artifact is named after its spec path: the path under `programs/`,
without `.yaml`, joined with `-`. The name depends only on the path, so
adding a period never renames an artifact that already exists.

| Spec | Artifact | `program_key` | `period` | `period_label` |
|---|---|---|---|---|
| `programs/us-az/snap/fy-2026.yaml` | `us-az-snap-fy-2026` | `us-az-snap` | `2026-01` | `fy-2026` |
| `programs/us-az/snap/fy-2027.yaml` (example) | `us-az-snap-fy-2027` | `us-az-snap` | `2026-10` | `fy-2027` |
| `programs/us/payroll/oasdi-wage-tax/fy-2026.yaml` | `us-payroll-oasdi-wage-tax-fy-2026` | `us-oasdi-wage-tax` | `2026` | `fy-2026` |
| `programs/us/us-tariff-schedule/ch01.yaml` | `us-us-tariff-schedule-ch01` | `us-ch01` | `2026-01` | `null` |

Each `manifest.json` program entry carries three fields beside the existing
ones:

- `program`: the spec's `program:` field as written, surrounding whitespace
  stripped.
- `program_key`: `<jurisdiction>-<program_id>`. It is the period-free key
  shared by every period of one program, and it is exactly the name every
  artifact had before rulespec-us#784.
- `period_label`: the path segment that names the period, or `null` when the
  spec path names the program itself. The tariff-schedule chapters are the
  `null` case: in `ch01.yaml` the stem is the chapter, which is part of the
  program, and the period appears only in `period`.

The build refuses a spec tree, before composing anything, in three cases:

- **Duplicate legal period.** Two specs share `(jurisdiction, program_id,
  period)`. Keep one spec per period.
- **Artifact name collision.** Two different spec paths join to the same
  name, compared case-insensitively because release assets land on
  case-insensitive filesystems. This needs one hyphenated string split
  differently across directory levels, such as `programs/us-az/snap/x.yaml`
  and `programs/us/az-snap/x.yaml`. Rename one of the paths.
- **Ambiguous `program_key`.** Two different `(jurisdiction, program_id)`
  pairs join to the same `program_key`, compared case-insensitively. For
  example, `program: us-az/snap` and `program: us/az-snap` are different
  programs (different jurisdictions) that would both have the key
  `us-az-snap`, even at paths whose names do not collide. Change the first
  or last `program:` segment of one of them.

The builder never refuses a second period on its own.

To add a period, add a spec beside the existing one, for example
`programs/us-az/snap/fy-2027.yaml` with the same `program:` and the new
`period:`. Consumers select an artifact by `program_key` and then pick the
entry with the greatest `period` that does not exceed the requested period.
On every tree the builder accepts, a `program_key` names exactly one
`(jurisdiction, program_id)`. Together with the duplicate check, that makes
`(program_key, period)` unique, so the rule always picks exactly one
artifact. The manifest does not record when a period ends.

The workflow also signs GitHub build-provenance attestations for
`manifest.json` and every `*.compiled.json`. Consumers can verify a
downloaded artifact was built by this workflow from this repo:

```bash
gh attestation verify manifest.json --repo TheAxiomFoundation/rulespec-us
```

Run locally:

```bash
AXIOM_RULES_ENGINE_BIN=~/axiom-rules/target/release/axiom-rules-engine \
  python tools/build_program_artifacts.py --check   # gate mode: builds, writes nothing
  python tools/build_program_artifacts.py           # writes dist/
```

Pre-flight refuses a build, leaving `dist/` untouched, when the engine binary
is missing or not executable, axiom-compose is not importable, the engine's
artifact format disagrees with the builder, the spec tree clashes, or a file
the build would write in `dist/` is a symlink (writing it would follow the
link). Once the pre-flight checks pass and before it writes, a build deletes
the top-level `*.compiled.json`, `*.rulespec.yaml` and `manifest.json` regular
files an earlier build left in `dist/`, so a `dist/` from before the #784
rename never mixes old names with new ones. Other files, symlinks and
subdirectories are left alone. `--check` touches nothing. After a failing
build `dist/` holds only the specs that built; don't use it.

The builder's own tests need no engine. CI runs them in the `builder-tests`
job from the hash-pinned `tools/tests/requirements.txt`:

```bash
uv run --no-project --python 3.14 --with-requirements tools/tests/requirements.txt \
  python -m pytest -q tools/tests
```

# Engine root load

The `engine-root-load` workflow asks the question issue #1354 showed nothing
else asked: does `axiom-rules-engine`, at `axiom_rules_engine_ref` in
`.axiom/workflow-toolchain.toml`, load this checkout as a corpus root?
Repository Checks skips every module with an active known-validation-gaps
waiver, so it stayed green while hundreds of modules declared fields that
engine had removed.

`tools/engine_root_load.py` writes a small Rust harness into the pinned engine
checkout as a Cargo example, builds it with `--locked`, admits the checkout
once as a `CanonicalRuleSpecRoots` root, and compiles every atomic module
under `<jurisdiction>/{legislation,policies,regulations,statutes}/` through
`CompiledProgramArtifact::from_rulespec_file`, the entry point behind
`axiom-rules-engine compile`. A stored `module.kind: composition` module, which
the engine refuses on that surface, is also compiled from a copy outside the
checkout through `from_composed_rulespec_file`.

Failures must equal `tools/known-engine-load-failures.txt`
(`<surface>\t<class>\t<module>`) exactly:

- a module that fails and is not listed fails the check;
- a listed module that no longer fails that way fails the check, so a fix
  deletes its line in the same change;
- when the protected base already has a baseline and the engine pin is
  unchanged, a pull request may only shrink the failing `(surface, module)`
  set. A listed module may change class: the engine reports only a module's
  first error, so fixing one can expose another;
- when the protected base has no baseline, the check establishes the first
  baseline without enforcing that shrinking rule. Moving
  `axiom_rules_engine_ref` also permits baseline growth: a newer engine may
  reject more, and the pin bump is where those failures are listed and reviewed.

Run locally from a checkout whose directory is named exactly `rulespec-us`:

```bash
python tools/engine_root_load.py run --engine-src ../axiom-rules-engine \
  --output /tmp/engine-root-load.jsonl
python tools/engine_root_load.py check --results /tmp/engine-root-load.jsonl \
  --base-ref origin/main
python tools/engine_root_load.py baseline --results /tmp/engine-root-load.jsonl \
  > tools/known-engine-load-failures.txt   # after deliberately fixing modules
```

# Source-conflict register

`known-source-conflicts.yaml` records the places where a jurisdiction's
sources disagree, the readings each side supports, and the reading adopted.
Disagreements include a statute against a regulation, a regulation against an
agency manual, and one manual section against another. Every rulespec
repository keeps its own register at its root. The Axiom-wide view is
generated from them with `tools/source_conflicts.py aggregate`; nothing keeps
a second copy.

## Entry shape

An entry's interpretation core is a RuleSpec `module.interpretations` v1
entry: `question`, `texts`, `reading`, `alternatives`, `basis`, `status`,
`ruling` and `confirmation`, with the same field names and status rules.
`open` forbids `ruling` and `confirmation`; `ruled` requires `ruling`;
`confirmed` and `contradicted` require both, and `contradicted` is always a
finding. So when the provision is encoded, the entry moves into the module
unchanged and the module adds `affects`. The register then names that module
under `adopted_by`. The global id of an entry is `<jurisdiction>:<id>`, for
example `us:oasdi-family-maximum-saving-clause`; code outside RuleSpec cites
that id, as `# Source conflict <global id>` at the line that decides the
reading.

Every alternative has an `id`: kebab-case, unique within the entry, and never
`reading`. A reading reference (`follows`, `adopts`, `pins`) is `reading`,
meaning the entry's adopted reading, or an alternative's id. References never
use positions, so inserting or reordering an alternative cannot move anyone's
pick. The `id` is part of the interpretation core: engine#247 and encode#1835
add it to `module.interpretations` before either lands.

Register-only fields:

| Field | Meaning |
|---|---|
| `jurisdiction`, `program` | A jurisdiction directory of this repository, and a kebab-case program slug. |
| `pending_texts` | Provisions the pinned corpus release lacks. Each gives `citation`, its `kind` (see below), `url`, an `excerpt`, and a `snapshot`: repo, commit, path and sha256 of a captured copy (`.txt`, `.md`, `.html`, `.htm` or `.xml`). An entry that a module adopts cannot have any; ingest them first. |
| `text_kinds` | Optional. Narrows the kind of a corpus text, as `{corpus citation path: kind}`. A text's kind is otherwise the first kind its document class allows (below). The kind must be one its path's class allows, so a `/statute/` path is always `statute`. |
| `unpublished_sources` | Sources with no public text, such as an agency's correspondence: `kind`, `description` and `date`. They are described, never quoted: a description holds no `@` and at most four words in quotation marks, counted across all its quoted spans. A span runs from an opening mark to its closing mark. A double quote, straight or curly, that is never closed quotes the rest of the description. A single quote, straight or curly, opens only at the start of a word and closes only at its end, so an apostrophe ("county's", "we’ll") or an elision ("the '90s") is neither. Verify cannot check them and lists them as unverifiable. |
| `years` | Optional. The years the sources disagree: `from`, and optionally `to` (both inclusive; no `to` means still running). `type` says which year: `calendar`, `tax`, `federal-fiscal`, `state-fiscal` or `program`. `program` also needs `note`, saying what the program year is. |
| `conflict`, `resolution` | `conflict` is `live` (the default) or `resolved`. `resolved` means a legislature or agency has closed the disagreement. It needs a `resolution` (`by`: `legislation` or `agency`; `effective`, a date; `record`, a public https URL) and `years.to`, the last year the sources disagree. A `live` entry has no `resolution`. |
| `outcome` | `computed` or `refused`: whether the adopted reading computes the contested cases or refuses them. For a refusal, `reading` says what is refused and the substantive readings go in `alternatives`. |
| `adopted_by` | RuleSpec modules in this repository that carry the entry, as `module` (path) and `interpretation` (id) pairs. |
| `implementations` | Code outside RuleSpec that takes a reading: `repo`, `commit`, `path`, `follows` (what the code does today) and `cites_entry`, which says whether the file contains the global id. A consumer may adopt a reading other than the entry's: `adopts` (default `reading`) names the reading it intends, `basis` says why, and an optional `ruling` (`by`, `date`, public `record`) is the consumer's own ruling. That ruling may also name the `principle` it applies, from a closed list: `statute-first` (a statute over a conflicting form, instructions or practice), `regulations-are-law` (a regulation binds like the statute), `agency-breaks-ties` (the administering agency's reading decides a true tie) or `taxpayer-choice` (the taxpayer's cheapest election or allocation). `basis` stays the free-text reason, and the aggregate view carries the principle. PolicyEngine-US follows the statute where the entry adopts an agency's practice. An implementation lags when `follows` differs from `adopts`. |
| `proposed` | Changes not yet merged that would implement a reading: `repo`, `pr` (the pull request URL), `path` and `follows`. Verify lists them but never counts them as implementations; move one to `implementations` once it merges, pinned to the commit on the default branch. |
| `tests` | Tests that pin readings: `path`, `name` and `pins`, a list of reading references. Here, `name` is a test function (or `Class::function`) in a `.py` file, or a case name in a companion `.test.yaml`. A test in another repository adds `repo` and `commit`. It may also be a YAML test file (`.yaml`) whose `name` is the case's name, on one line, such as a PolicyEngine-US policy test. Verify checks that the case still exists at that commit. Another repository's YAML test file must sit under a `tests` directory. A Python test is a whole test function. `check` screens only a pin's syntax; a pin is established once the `pinned-tests` job has run it at its pinned commit and it passed. The runner executes a YAML case through its repository's own YAML test runner, so a YAML pin needs a `YAML_RUNNERS` entry (today, PolicyEngine-US's policyengine-core). See [Test references](#test-references). |
| `money_case` | Optional. An invented case showing the size of the difference: `description`, `amount` (a decimal string), `currency`, `period` (once, week, month or year) and `computed_by`, the name of the one test in the entry's `tests` that computes the amount, asserting it or both figures whose difference it is. A public file carries no amount that no pinned test computes: leave the money case out instead. `check` also requires every `$` amount in the entry's own prose to be one the money case states. The prose is `question`, `reading`, `basis`, each alternative's `reading` and `effect`, and the consumer fields (an implementation's `basis`, `years.note`, an unpublished source's `description`). Excerpts are the sources' own words and may state any figure. The prose names a threshold without restating it ("above the section 1341 threshold"), because no test on the words around an amount can tell a quoted threshold from a computed one. So an entry without a money case has no dollar figures in its prose. Money is written one way, `$` and digits with commas between groups of three and optional two-digit cents (`$1,234.56`); other spellings (`USD 200`, `200 dollars`, `$ 200`, `$.50`, `$1.5k`) are issues. |

Source kinds are `statute`, `regulation`, `rulemaking`, `form`,
`instructions`, `worksheet`, `manual`, `guidance`, `policy`, `plan`,
`calculator` and `agency-practice`. `DOCUMENT_CLASS_KINDS` in
`tools/source_conflicts.py` maps each corpus document class to the kinds it
allows; the first is the default:

| Document class | Kinds |
|---|---|
| `statute` | statute |
| `regulation` | regulation |
| `rulemaking` | rulemaking |
| `form` | form, instructions, worksheet |
| `guidance` | guidance, instructions, calculator, plan |
| `manual` | manual |
| `policy` | policy, manual, guidance, plan |
| `district-plan` | plan |

A text whose class has no row is a finding, so a new corpus class fails
closed until it gets one.

The register is public. These publication rules are reviewed by hand: it
carries no people's names; `ruling.by` and `confirmation.by` name
organisations; `ruling.record` is a public PR, issue or comment; and nothing
private is quoted. `check` automates only part of that: `by` must be
non-blank and `record` an https URL, and every string must be free of four
token patterns (decision-queue ids such as `d1234`, session ids, local paths
and email addresses). It cannot tell a person's name from an organisation's,
or a private page from a public one. The file may not use YAML anchors or
aliases; `load_register` refuses them, so no entry can contain itself.

## Checks

`tools/source_conflicts.py check` runs offline. `tests/test_source_conflicts.py`
runs it inside the required Repository Checks pytest leg, and it fails on any
of these:

- a malformed entry, an unknown key or a broken status rule;
- an alternative without an id, or a reading reference (`follows`, `adopts`,
  `pins`) that is neither `reading` nor one of the entry's alternative ids;
- a text whose document class has no `DOCUMENT_CLASS_KINDS` row, or a kind
  its class does not allow;
- a `resolution` without `conflict: resolved`, or a resolved entry without a
  `resolution` or `years.to`;
- a hygiene hit (one of the four token patterns below);
- an adopting module that is missing, or that does not carry the entry's
  interpretation core unchanged, or whose `affects` name no rule in the module;
- an in-repo test whose file does not exist or does not define the named
  test. This is a syntactic screen and says nothing about running (see
  [Test references](#test-references));
- a followed reading that no test pins, or a module adopter whose `reading`
  no test pins;
- a ruled, confirmed or contradicted module interpretation whose texts cite
  two or more provisions but which no entry adopts. Provisions in tension are
  a source disagreement, so they belong in the register. An unregistered `open`
  one is only a warning, because signed encoder re-encodes carry the module and
  its manifest alone and may emit open interpretations. The `source-conflicts`
  workflow lists those warnings in a tracking issue. Its entry is written when
  a ruling or a publisher's reply arrives.

Verification needs the network and runs in the `source-conflicts` workflow
on pull requests touching the register or these tools, on pushes to main,
daily and on dispatch, as two jobs. `tools/source_conflicts.py verify` (the
`source-conflicts` job) checks:

- every `texts` excerpt is verbatim at its citation in the pinned corpus release
  from `.axiom/toolchain.toml`;
- every `pending_texts` excerpt is verbatim in its snapshot, whose sha256 must
  match;
- external implementations, tests and snapshots are pinned to commits reachable from their repository's default branch (a squash-merged pull request's own commits are not), and they exist there; each external Python test file defines its pinned test (the same syntactic screen), and each external YAML test file has its pinned case;
- each `cites_entry` claim matches its file.

`tools/pin_runner.py` (the `pinned-tests` job) runs every pinned test at its
pinned commit and fails unless pytest reports it passed; see
[Test references](#test-references).

Both excerpt checks use axiom-encode's own resolver and proof-atom matcher at
`axiom_encode_ref`. The verify report lists:
- implementations that do not cite their entry yet;
- implementations that lag (they follow a reading other than the one they adopt);
- unpublished sources, which it cannot check.

Neither job is a required check; a red scheduled or main run opens an alarm
issue (see [Merge gate](#merge-gate)). `tests/test_source_conflicts_properties.py`
(Hypothesis) states the tool's invariants, including a differential test
against axiom-encode's `_validate_module_interpretations`, which runs once the
pinned encoder accepts module interpretations with alternative ids
(encode#1835, engine#247), and a differential of the syntactic test screen
against Python's own symbol table. `tests/test_pin_runner_properties.py`
states the runner classifier's. The `source-conflicts` workflow is the gate
for these properties: it installs Hypothesis and the pinned pytest.
Repository Checks' shared workflow runs the suite without Hypothesis, so the
properties skip there.

Run locally:

```bash
python tools/source_conflicts.py check
AXIOM_CORPUS_RELEASE_PUBLIC_KEY=... python tools/source_conflicts.py verify \
  --corpus-path ../axiom-corpus          # needs axiom-encode importable
python tools/pin_runner.py --report /tmp/pinned-tests.json   # needs git and uv
python tools/source_conflicts.py aggregate --markdown /tmp/conflicts.md
```

## Test references

A pinned test is established only by running it. `tools/source_conflicts.py
check` screens a pin's syntax, and that is all it does: the path is a
`test_*.py` file (or a companion `.test.yaml`), and the file defines the named
function at module level or in a module-level class (`Class::function`), or
has a case with that name. Definitions under `if`, `try`, `with`, loops and
`match` count as module level. A file the parser can't handle (a syntax
error, or input too deep or too complex for CPython's parser) fails the
screen. The screen says nothing about whether pytest
collects or runs the test: import-time code, conftest files, plugins and ini
settings decide that, and no static check can.

`tools/pin_runner.py` asks pytest. For each repository and commit the register
pins, it:

0. asks GitHub's API, before fetching anything, whether the commit is shipped
   code of that repository. GitHub's canonical name must be exactly the pinned
   one (no rename, transfer or redirect), the repository must not be a fork,
   and comparing its default branch with the commit must say `identical` or
   `behind`, meaning the commit is reachable from that branch. GitHub serves
   every object of a fork network through the parent's URL, so a fetch that
   succeeds proves nothing about who wrote a commit, and neither does a
   `refs/pull/*` ref. Any failed or unexpected answer is a refusal, including
   an exhausted rate limit. The job that runs pinned code holds no token, and
   GitHub's unauthenticated limit (60 requests an hour, one per repository
   plus one per commit) runs out on shared runners. So the workflow's
   `pin-provenance` job, which runs no pinned code, asks first with the run's
   read-only token (`pin_runner.py --record-provenance`), and the run reads its
   record (`--provenance`) before any pinned code runs, asking GitHub
   unauthenticated only for a commit the record lacks;
1. fetches the commit (`git fetch --depth 1`) into a fresh checkout;
2. picks the newest Python from 3.14 down to 3.9 that the project's
   `requires-python` allows;
3. installs the repository's own test install into a fresh environment with
   `uv pip install --exclude-newer <the commit's committer date>`, so registry
   packages resolve as they did when the commit was made. `--exclude-newer`
   applies to registry packages only; a Git or direct-URL requirement follows
   the repository's own declaration. The install is `-e ".[dev]"`, or the
   repository's entry in `INSTALL_SPECS` if it keeps its test dependencies
   elsewhere;
4. runs pytest from the checkout root on the pinned files, under the
   repository's own ini, conftest files and `addopts`, with
   `-p no:cacheprovider` and a scratch `--basetemp`. A plugin
   (`tools/pin_oracle`) records what pytest collected, deselected and
   reported, and lets only the pinned tests run;
5. classifies each pin from that record.

**The claim.** Verification passing means each pinned test was collected and
passed at its pinned commit, in the repository's own install resolved as of
that commit's date, under its own pytest configuration. `check` alone
establishes nothing about running. A pin is established only once
verification is green: the `pinned-tests` job, together with the
`source-conflicts` job for the excerpts, snapshots and files. The pinned
commit is also shipped code: GitHub says it is on the default branch of the
canonical, non-fork repository the pin names.

Only the outcome `passed` passes. That means every collected case of the
pinned function passed its setup, call and teardown. Two further conditions
are checked separately, and each alone fails the commit: pytest's process
must exit 0, and the session status the plugin recorded must be 0. A
repository hook can change the session's status after the plugin has written
its record, so the process exit is authoritative. Each of these fails the pin:

- a commit GitHub does not confirm as shipped code of the pinned repository
  (`untrusted commit`); nothing is fetched;
- a fetch, environment or install failure, or an install that does not
  provide pytest;
- a collection error, a module skipped at collection (`not collected`), a
  test that is not in pytest's collection (`missing`), a pinned file that is
  not in the checkout, or a case that the repository's own `-m`, `-k` or
  conftest hooks deselect;
- a case that is `skipped`, `xfail`, `xpass`, `failed` or `error`, or that
  never ran;
- a pytest process exit other than 0, a session status other than 0, a case
  reported twice for one phase, or a run that pytest-xdist distributes;
- the per-commit timeout (15 minutes, from fetch to pytest);
- any exception in the runner.

Pins the runner cannot execute as stated fail too, with the reason:

- a pin in a repository outside `TheAxiomFoundation/*` and `PolicyEngine/*`,
  spelled exactly as GitHub does ("the runner won't execute pins in <repo>");
- a pin in this repository, which has no pinned commit;
- a YAML test case in a repository with no `YAML_RUNNERS` entry, including
  a companion `.test.yaml` here.

**YAML cases.** A YAML pin in a repository that `YAML_RUNNERS` lists runs
through that repository's own YAML test runner, in a second process beside
pytest. PolicyEngine-US's runner is policyengine-core:
`python -m policyengine_core.scripts.policyengine_command test <files> -c policyengine_us`.
policyengine-core calls `pytest.main` itself with its own plugin, so the
oracle is loaded through `PYTEST_ADDOPTS`, along with `-p no:cacheprovider`
and a scratch `--basetemp`. Its YAML items have no name until they run, so
every case in a file shares the node id `path::`. The oracle therefore keys a
YAML item by its case's `name` (`item.test["name"]`), and records each report
against the item `pytest_runtest_protocol` is running, by its position in the
collection. A YAML pin names exactly one case: two cases with the pinned name are `ambiguous`, which fails, even if both pass. The YAML run's
process exit and session status are checked on their own, like pytest's.
The install check fails closed if the repository's install does not provide
the runner's package. Running in-repo companion tests is future work.

A parametrized case (`test_x[case-1]`) cannot be pinned. Pin the whole
function; every case pytest collects for it must pass.

The report (`--report`, kept as the `pinned-tests` artifact) records, for
each commit:

- the Python chosen, the Python installed and the `requires-python` it came
  from;
- the uv version, the `--exclude-newer` date and the install spec;
- pytest's version, ini file and `addopts`;
- each step's time, and each pin's outcome and cases.

A commit whose pins all passed is cached (`--cache-dir`). The key is the
repository, the commit, the sorted pinned ids and the runner version, a hash
of the runner and the plugin, so a runner change re-runs everything. Failures
are never cached, and neither is a nonzero exit. A cached record is used only
if it names the same repository, commit and ids, every pin passed with at
least one passing case, and the process exit was 0; provenance is checked
again first (from this run's record, or GitHub). Those checks catch corruption and stale records, but
they cannot authenticate a record someone forged on purpose. So the workflow
restores the cache only for pull requests; pushes to main and the daily run
execute every pin and save fresh results.

**Isolation.** The runner executes code from other repositories, so its job
holds nothing worth taking:

- no secret or token reaches its environment;
- the checkout does not persist credentials;
- its permissions are `contents: read`, with no `id-token`;
- every step the runner starts gets a fixed environment with a scratch
  `HOME`.

Its result leaves only as the JSON artifact. The alarm job reads that artifact
with main's `pin_runner.py --summarize`, which checks every field's type and
prints only fields that match fixed patterns. A missing or malformed artifact,
including one without the `commits`, `unrun` and `issues` lists or a commit
without its `pins` and `issues` lists (the runner always writes them),
becomes its own alarm line ("pinned-tests artifact malformed"); the summary
never crashes the alarm step. No runner output is interpolated into a
workflow script.
`tests/test_pin_runner.py` checks these properties of the workflow file.

### Merge gate

Neither verification job is a required check in branch protection, so an
outage of GitHub or a package index cannot block a merge mechanically. Register
pull requests are merged only when every check on the head is green
(`gh pr checks` exits 0), so a register change lands only on a green run of
both jobs on its head.

### Evidence

`tests/test_pin_runner.py` runs the runner on fixture repositories (`git
init` in a temporary directory, a small `pyproject.toml`), one per way a pin
fails closed. The fixtures cover:

- a pass;
- round 6's module skip through `partial(pytest.skip, allow_module_level=True)`;
- a skip mark, a skip in the body, and a skip that a conftest hook adds;
- xfail, xpass and strict xpass;
- a failure, a fixture error and a collection error;
- an install failure, a missing test and a missing file;
- an unfetchable commit and a timeout;
- round 8's probes: a `pytest_sessionfinish` hookwrapper that sets exit 1
  after the plugin wrote, a `pytest_unconfigure` that raises, and a
  duplicated item whose first run fails and second passes;
- an outside contributor's commit kept only under `refs/pull/1/head` and
  served through the parent's URL, a renamed repository, a fork, an unknown
  commit, a redirect and an exhausted rate limit, each refused before any
  fetch, against a fake GitHub API that answers from git itself;
- a repository off the allowlist, and a deselection through `addopts = "-m
  'not slow'"`;
- YAML cases through a stand-in with policyengine-core's shape (it calls
  `pytest.main` itself, with items that have no name until they run): a case
  that passes, fails or is skipped, two cases with one name, a missing case, a
  missing file, a Python pin at the same commit with its own exit, a passing
  YAML commit that is cached, and an install without the runner's package.

The fixtures also check that no secret in the caller's environment reaches
the pinned tests. `tests/test_pin_runner_properties.py` checks the classifier
and the commit-level exit conditions against an independent statement of when
a pin passes, provenance against an independent statement over any API
answer, and that `--summarize` exits 0 with a valid summary or the
malformed-artifact alarm for any JSON artifact.

### Known limits

- The install is the repository's own, resolved as of the commit date. It is
  not the exact environment its CI used: a dependency released between the
  commit and that CI run is excluded, and a release yanked since can make an
  old commit uninstallable. That fails closed.
- One Python runs, the newest the project allows. The repository's CI may
  test others.
- The runner names the pinned files on pytest's command line. Settings that
  only shape a default run (`testpaths`, `norecursedirs`, `collect_ignore`,
  `--ignore`) do not stop a named file being collected. So a pinned test that
  the repository's own CI never runs is still run here, and its result stands
  for the pinned commit. Marks, `-m`, `-k`, `--deselect` and conftest hooks
  still apply.
- A pinned test needs whatever it reads to be in the repository at that
  commit. A test that needs unpublished data skips and fails the pin; pin a
  test that runs from a clean checkout.
- `passed` means pytest passed the test. Whether the test computes what an
  entry's money case states is for the entry's reviewers (`computed_by`).
- The Python request is a minor version (the newest that `requires-python`
  allows for some patch release). uv installs that minor's newest patch, and
  a narrow patch constraint it misses fails the install, closed.
- A conftest hook can rewrite a report, turning a failure into a pass. That
  is the repository's own pytest configuration, which the claim covers; it
  does not prove the underlying assertion.
- The runner scrubs each step's environment and gives it a scratch `HOME`,
  but it is not an operating-system sandbox: the pinned code runs as the job's
  user. The job's isolation (no secrets, read-only permissions) is the
  boundary.
- Provenance comes from the run's `pin-provenance` record, asked with the
  run's read-only token. If that job fails, `pinned-tests` doesn't run, and
  the check fails closed.
- Deliberate evasion, such as a test that detects the runner, is out of
  scope: the register guards against honest mistakes.
