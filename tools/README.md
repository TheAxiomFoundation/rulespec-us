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

The workflow also signs GitHub build-provenance attestations for
`manifest.json` and every `*.compiled.json`. Consumers can verify a
downloaded artifact was built by this workflow from this repo:

```bash
gh attestation verify manifest.json --repo TheAxiomFoundation/rulespec-us
```

Run locally:

```bash
AXIOM_RULES_ENGINE_BIN=~/axiom-rules/target/release/axiom-rules-engine \
  python tools/build_program_artifacts.py --check   # gate mode
  python tools/build_program_artifacts.py           # writes dist/
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
that id.

Register-only fields:

| Field | Meaning |
|---|---|
| `jurisdiction`, `program` | A jurisdiction directory of this repository, and a kebab-case program slug. |
| `pending_texts` | Provisions the pinned corpus release lacks. Each gives `citation`, `url`, an `excerpt`, and a `snapshot`: repo, commit, path and sha256 of a captured copy. An entry that a module adopts cannot have any; ingest them first. |
| `outcome` | `computed` or `refused`: whether the adopted reading computes the contested cases or refuses them. For a refusal, `reading` says what is refused and the substantive readings go in `alternatives`. |
| `adopted_by` | RuleSpec modules in this repository that carry the entry, as `module` (path) and `interpretation` (id) pairs. |
| `implementations` | Code outside RuleSpec that adopts a reading: `repo`, `commit`, `path`, `follows` (`reading` or `alternatives[N]`, meaning what the code does today) and `cites_entry`, which says whether the file contains the global id. |
| `proposed` | Unshipped changes outside RuleSpec: `repo`, `path`, `follows`, and `basis` for the intended reading. Optional `pull_request` is a GitHub PR URL for that repository. A proposal may precede a public PR and carries no commit, `cites_entry`, or test-run claim. It creates no obligation for that file to exist on main. Once shipped, replace it with an `implementations` record and pinned tests under the existing checks. |
| `tests` | Tests that pin readings: `path`, `name` (a test function, `Class::function`, or a companion-test case name) and `pins`, a list of `reading` or `alternatives[N]`. Add `repo` and `commit` for a test in another repository. A Python test is a whole test function. `check` screens only a pin's syntax; a pin is established once the `pinned-tests` job has run it at its pinned commit and it passed. See [Test references](#test-references). |
| `money_case` | Optional. An invented case showing the size of the difference: `description`, `amount` (a decimal string), `currency`, `period` (once, week, month or year) and `computed_by`, the name of the one test in the entry's `tests` that computes the amount, asserting it or both figures whose difference it is. A public file carries no amount that no pinned test computes: leave the money case out instead. `check` also requires every `$` amount in the entry's own prose (`question`, `reading`, `basis`, each alternative's `reading` and `effect`, and each proposal's `basis`) to be one the money case states, so an entry without one has no dollar figures. Money is written one way, `$` and digits with commas between groups of three and optional two-digit cents (`$1,234.56`); other spellings (`USD 200`, `200 dollars`, `$ 200`, `$.50`, `$1.5k`) are issues. |

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
- external implementations and test files exist at their pinned commits, and
  each test file defines its pinned test (the same syntactic screen);
- each `cites_entry` claim matches its file.

`tools/pin_runner.py` (the `pinned-tests` job) runs every pinned test at its
pinned commit and fails unless pytest reports it passed; see
[Test references](#test-references).

Both excerpt checks use axiom-encode's own resolver and proof-atom matcher at
`axiom_encode_ref`. The verify report lists implementations that do not cite
their entry yet and implementations that follow an alternative rather than
the adopted reading. Neither job is a required check; a red scheduled or main
run opens an alarm issue (see [Merge gate](#merge-gate)).
Proposals are reported explicitly as unshipped and unverified; they do not
count as verified implementations and are never fetched or run as test pins.
`tests/test_source_conflicts_properties.py` (Hypothesis) states the tool's
invariants, including a differential test against axiom-encode's
`_validate_module_interpretations` that runs once the pinned encoder has
module interpretations, and a differential of the syntactic test screen
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
`match` count as module level. The screen says nothing about whether pytest
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
   an exhausted rate limit; the job holds no token, so it asks
   unauthenticated, which allows 60 requests an hour (one per repository plus
   one per commit);
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
- a YAML test case: a companion `.test.yaml` here, or another repository's
  YAML tests.

So every pin in the register must, for now, be a Python test in an allowed
repository. Running in-repo and YAML pins is future work.

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
least one passing case, and the process exit was 0; provenance is asked of
GitHub again first. Those checks catch corruption and stale records, but
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
prints only fields that match fixed patterns. A missing or malformed artifact
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
  'not slow'"`.

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
- Provenance is asked unauthenticated, so GitHub's rate limit (60 requests an
  hour per address) can refuse a run; that fails closed and passes on retry.
- Deliberate evasion, such as a test that detects the runner, is out of
  scope: the register guards against honest mistakes.
