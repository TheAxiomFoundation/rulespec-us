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
- when the protected base already has a baseline, a pull request may only
  shrink the failing `(surface, module)` set. A listed module may change
  class: the engine reports only a module's first error, so fixing one can
  expose another;
- when the protected base has no baseline, the check establishes the first
  baseline without enforcing that shrinking rule;
- a change that moves `axiom_rules_engine_ref` may add modules it leaves
  byte-identical, because a newer engine may reject more and the pin bump is
  where those failures are listed and reviewed. A module the change edits or
  renames must still load if it loaded before.

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
a second copy. It reads each repository's file as `check` reads one (no
anchors or aliases), and a file it can't read is left out of the view and
reported, so one repository can't stop the view; the command then exits 1.

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
| `unpublished_sources` | Sources with no public text, such as an agency's correspondence: `kind`, `description` and `date`. They are described, never quoted: a description holds no `@` and at most four words in quotation marks, counted across all its quoted spans. **Quote with one style of double quotation marks** (`"…"` or `“…”`), nesting with `«…»` if needed and never in the same marks; those are counted exactly in plain prose with no single mark that may open (see the invariant below). Single marks, `‘…’` included, are read conservatively. Or describe the source instead; a refusal says so and shows the span it counted. The scanner reads every character Unicode gives the Quotation_Mark property, plus primes (`′ ″ ‵ ‶`) and the quotation-mark ornaments (`❛ ❜ ❝ ❞ ❟ ❠ ❮ ❯ 🙶 🙷 🙸`). **Delimited quotations** are read first, over the whole description: `"…"`, `“…”`, `„…“`, `„…”`, `‚…‘`, `‚…’`, `‟…”`, `⹂…“`, `«…»`, `‹…›`, `»…«`, `›…‹`, `»…»`, `›…›`, `”…”`, `「…」`, `『…』`, `﹁…﹂`, `﹃…﹄`, `｢…｣`, `〝…〞`, `〝…〟`, `＂…＂`, `″…″`, `‶…″`, `❝…❞`, `❠…❞`, `❮…❯` and `🙶…🙷`. An unclosed opener quotes the rest of the description. A mark that also closes another pair (`”`, `»`, `›`, `″`, `“`, `«`, `‹`, `🙶`) opens where it starts a quotation, and otherwise unless it directly follows a letter or digit; `”`, `»`, `›` and `″`, which close the commonest pairs, also need a non-space after them. So the inch marks in 6” and 6″ open nothing, and nor do inner closers glued to a word (`„a „b“ c“`), while `:«one»` and `—« one »` open. They are read three ways. Standard: each opener closes at its first closing mark. Strict: a mark opens unless it directly follows a letter or digit, and closes at the first closing mark that doesn't itself start a quotation, so a stray mark before a quotation (an inch mark, `6" tall and "…"`, or a low mark used as a comma) can't hide it. A mark that can both close and open starts a quotation when it comes before a letter or digit after an opener prefix (the start of the description, whitespace, a slash, a colon, an opening bracket, a dash or a quotation mark), or before a quotation mark at the start or after whitespace; so `"wait—".`, `"workers'",` and `"four—"[1]` close where they should. Nested: the marks nest like brackets across pairs, with a mark that could close or open read as an opener only where it starts a quotation, so `“one “two” three”` and `"one "two" three"` count three words. **Single quotation marks** can't be told from apostrophes (`'cause`, `goin'`, `the workers'`), so they are read conservatively. A single mark (`'`, `‘`, `’`, `＇`, `‛`, `′`, `‵`, `❛` or `❟`) may open unless it follows a letter or digit; any quotation mark may close if no letter or decimal digit follows it, so a footnote mark may follow, and `‘…”` closes. Every word from the first single mark that may open to the last mark that may close counts. That is read outside each delimited reading's quotations, and over the whole text (closing at a single mark anywhere or another mark outside the quotations, and counting each delimited quotation on its own plus the span's text outside them), so a stray delimiter can't swallow a single quotation's opener. The count is the largest of these readings, a one-pass reading of delimited and single marks together (under these single openers and the previous scanner's, so widening the openers never lowers the count), and the count the previous scanner gave. That last is kept exactly, with its words counted by whitespace, so `"one two three four …"` counts five, and this scan refuses whatever that one did. Otherwise a word is a token with a letter or digit, and a delimited quotation inside the single span counts once. **Invariant** (tested with possessives, elisions, elided years, dropped letters and nested quotations): a quotation of N words opened and closed by single marks at word boundaries counts at least N, whatever it holds and whatever surrounds it; double quotations in plain prose are counted exactly in each delimited reading, whatever their words end in (punctuation, a dash, a possessive) and whatever follows the closer (punctuation, a bracketed citation), so long as they hold none of the quotation's own closing marks, and with a space inside either mark (except after `”`, `»`, `›` or `″`, which a space after reads as a closer); this covers every listed pair but `‚…‘` and `‚…’`, whose closers are single marks and so read conservatively, in a description with no single mark that may open; a quotation nested in a pair that shares no mark with the outer one counts exactly too, while nesting in the same marks, or in a pair that shares one (`“…”` inside `„…“`), counts at least in full and may count more; overall, `"…"` and `“…”` are counted exactly, and the other pairs unless the previous scanner's count is higher (it read `“` as an opener, so after `„…“` it quoted the rest); and the count is never below the previous scanner's. **Known limits**, the only fail-opens the scanner accepts, come from one rule, the ambiguous opener (`_ambiguous_opener`): a mark that could open a quotation but could as well close one isn't read as opening it. Inside a quotation it could close, a mark is ambiguous unless it starts a quotation (a letter or digit follows it after an opener prefix, or a quotation mark follows it at the start or after whitespace), so a nested quotation that doesn't start with a letter or digit reads as two quotations, and the words between them aren't counted. Elsewhere, a single mark, or a mark that also closes another pair (`”`, `»`, `›`, `″`, `“`, `«`, `‹`, `🙶`), is ambiguous when it directly follows a letter or digit, so a quotation it opens isn't counted (the previous scanner's count still reads a glued `“…”`; marks that only open, such as `"`, `„` and `「`, are never ambiguous). `”`, `»`, `›` and `″` are ambiguous before a space too, though the strict reading still counts that quotation. Nesting in the same marks, or in a pair that shares one, may count more, failing closed. **Intended refusals.** A description that quotes with single marks, `‘…’` nested in a double quotation included, and also has a later apostrophe at a word's end, a second single quotation, or an elided year with a later apostrophe, is read as one quotation from the first mark to the last, and is refused when that holds more than four words. Write the quotation in double marks, nest with `«…»`, or write the year in full. Apostrophes in prose with no single mark that may open quote nothing. [Quotation examples](#quotation-examples) shows each case with its count, and a test checks every one. The publication rules reviewed by hand (below) still apply, including that nothing private is quoted. Verify cannot check them and lists them as unverifiable. |
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

### Excerpts

An excerpt (`texts[].excerpt` or `pending_texts[].excerpt`) is the source's
own words. `verify` matches it with axiom-encode's proof-atom matcher, which
reads whitespace through `collapse_evidence_whitespace` at
`axiom_encode_ref`. That function keeps every paragraph gap. In the source
and the excerpt alike, a run of whitespace holding two or more line ends, or
a paragraph separator (form feed, vertical tab, U+0085, U+2028 or U+2029),
becomes one blank line, and any other run becomes one space. So where the
corpus text sets a subparagraph off with a blank line, the excerpt has a
blank line there too, and it has a blank line nowhere else. Line wraps and
extra spaces don't matter. Write such an excerpt as a literal block
(`excerpt: |-`), which keeps its blank lines:

```yaml
texts:
- corpus_citation_path: us/statute/26/199A/a/2
  excerpt: |-
    an amount equal to 20 percent of the excess (if any) of—

    (A) the taxable income of the taxpayer for the taxable year, over

    (B) the net capital gain (as defined in section 1(h)) of the taxpayer for such taxable year.
```

Written on one line (`… of— (A) the taxable income …`), the same words don't
match. In a plain, single-quoted or folded (`>-`) scalar, one blank line
folds to a single line break, which reads as a space, so those styles lose
the gap too. `check` can't see the corpus, so it can't catch a gap mismatch
in `texts`. When the words match once every paragraph gap is read as a
space, `verify`'s issue says to keep the source's paragraph gaps; it flattens
both texts with the encoder's own normaliser to tell. A snapshot is
different: `verify` reads it with every run of whitespace as one space
(`snapshot_text`), so a `pending_texts` excerpt never has a blank line, and
`check` refuses one that has.

YAML keeps a backslash as itself outside double quotes, so an excerpt copied
from escaped text holds `\n` as two characters and never matches its source.
`check` refuses an excerpt holding a backslash and `n`, whatever follows it
(`who\nis`, `\n(1)`, `\n\n(1)`), or a backslash and `t` or `r` that no
letter follows (`\t2,000`, `\r\n`). Write a real line break or a space
instead. A backslash and `t` or `r` before a letter is left alone, because a
source may set a real backslash there (`applicant\recipient`, `\times`,
`C:\temp`). A real backslash before `n` (`citizen\noncitizen`, `\neq`), or
before `t` or `r` and no letter, is refused too: quote a span that stops
before it. If the
corpus text itself shows an escape, that is an ingest defect to fix in
axiom-corpus, not text to quote. Module interpretations are left to
axiom-encode's own validation, which `check_module_interpretation` mirrors.

### Quotation examples

How `check` counts the quoted words of an `unpublished_sources` description.
`tests/test_source_conflicts.py` reads this table and checks each row, so it
can't drift from the code. A description is refused when the count is more
than four.

| Description | Counted | Refused | Why |
|---|---|---|---|
| `The letter calls the fee "reasonable" and "customary".` | 2 | no | Double marks are counted exactly. |
| `The letter calls the fee “reasonable” and the rate “standard”.` | 2 | no | Double marks are counted exactly. |
| `It wrote “one «two three» four”.` | 4 | no | Nesting in a pair that shares no mark counts exactly. |
| `It wrote "one two three four five".` | 5 | yes | More than four quoted words. |
| `A stray " mark, then it said:"one two three four five".` | 8 | yes | A mark after a colon starts a quotation, even inside one a stray mark left open; the stray mark's span counts too. |
| `It wrote "one two three four …".` | 5 | yes | The previous scanner counted the ellipsis as a word, and its count is the floor. |
| `It wrote "one two three four—"[1] today.` | 4 | no | A closer before a citation closes. |
| `It wrote:«one two three four five».` | 5 | yes | A mark that can also close opens after punctuation. |
| `It wrote « one two three four five ».` | 5 | yes | French spacing. |
| `It wrote —» one two three four five «.` | 5 | yes | Ambiguous before a space in the standard reading, counted by the strict one. |
| `It wrote x'one two three four five'.` | 0 | no | Known limit: an ambiguous opener glued to a word. |
| `It wrote x«one two three four five».` | 0 | no | Known limit: an ambiguous opener glued to a word. |
| `It wrote x”one two three four five”.` | 0 | no | Known limit: an ambiguous opener glued to a word. |
| `It wrote x“one two three four five”.` | 5 | yes | Glued, but the previous scanner read “ and its count is the floor. |
| `It wrote x"one two three four five".` | 5 | yes | " only opens or closes itself, so it is never ambiguous. |
| `It wrote "one "[sic] two three" four".` | 2 | no | Known limit: a nested quotation that doesn't start with a letter or digit. |
| `It wrote „one “[sic] two” three”.` | 2 | no | Known limit: the same, in a pair sharing a mark. |
| `It wrote "one —"«two» three".` | 3 | no | Known limit: the same, starting with a quotation mark after punctuation. |
| `A stray „ mark, then (““one” two three four five”).` | 3 | no | Known limit: the same, inside the quotation a stray mark left open. |
| `It wrote “one «[sic] two three» four”.` | 5 | yes | Nesting in a pair that shares no mark counts in full. |
| `It wrote "one "two"" today.` | 3 | no | Nesting in the same marks may count more (two words here), failing closed. |
| `The agency called it 'routine' and won't reopen the workers' case.` | 6 | yes | Intended: single marks are read from the first opener to the last closer. |
| `The agency called it "routine" and won't reopen the workers' case.` | 1 | no | The same in double marks. |
| `It wrote 'one' and then 'two three four'.` | 6 | yes | Intended: two single quotations read as one. |
| `Since the '90s the clerks in each county office have handled the clerks' files.` | 11 | yes | Intended: an elided year may open, and a later apostrophe may close. |
| `Since the 1990s the clerks in each county office have handled the clerks' files.` | 0 | no | The year in full. |
| `It wrote “one ‘two’ three” then denied workers’ claims.` | 6 | yes | Intended: ‘…’ is a single mark, read conservatively. |
| `It wrote “one «two» three” then denied workers’ claims.` | 3 | no | Nested in «…», as the refusal recommends. |
| `The agency's reply was brief; it's 6'7 wide and the workers' union agrees.` | 0 | no | Apostrophes in prose quote nothing. |

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
- an excerpt holding an escape sequence as text, or a `pending_texts`
  excerpt with a paragraph gap (see [Excerpts](#excerpts));
- a global id that `household-choices.yaml` also uses (see
  [Household choices](#household-choices); both checks call one function);
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
- each `cites_entry` claim matches its file, which must name the global id
  as a whole id (a cite of `us:a-b` is not a cite of `us:a`).

`tools/pin_runner.py` (the `pinned-tests` job) runs every pinned test at its
pinned commit and fails unless pytest reports it passed; see
[Test references](#test-references).

Both excerpt checks use axiom-encode's own resolver and proof-atom matcher at
`axiom_encode_ref`. A corpus excerpt that matches once every paragraph gap is
read as a space is reported with a hint to keep the source's paragraph gaps
(see [Excerpts](#excerpts)). The verify report lists:
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
or the household choices pin, it:

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
prints only fields that match fixed patterns. The one free text it prints is a
YAML case's name, inside its pin id in a code span, and only when the name has
no backtick, `@` or angle bracket. The rule refuses every Unicode category C
character (control, format, private-use, surrogate and unassigned), every
separator except a space, and every Default_Ignorable_Code_Point character,
including those outside category C: U+034F, U+115F–U+1160, U+17B4–U+17B5,
U+180B–U+180D, U+180F, U+3164, U+FE00–U+FE0F, U+FFA0 and
U+E0100–U+E01EF. "Café" and "A case!" print; a line break, a bidirectional
override or a default-ignorable character makes the pin malformed. Tests check
that names stay inside one code span, contain none of those forbidden
characters, and cannot insert lines, mentions or angle brackets. They do not
establish that every accepted Unicode character is visibly distinguishable.
At most 200 characters of a YAML case name are displayed; longer names use
the first 200 characters, right-stripped, followed by `…`. The summary holds
at most 100 detail lines and 60,000 UTF-16 code units, the measure GitHub
limits an issue body by (65,536), including an overflow line pointing to the
report artifact; the workflow's own text fits in the rest.
A missing or malformed artifact,
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
  YAML commit that is cached, and an install without the runner's package;
- household-choice optimum pins through that stand-in: a case the model
  chooses, a forced input, axes, an override, a reform, an extension, an enum,
  two entries pinning one case on different variables, and a case where only
  one unit chooses, pinned with and without `instances`.

`tests/test_pin_oracle_core.py` runs the oracle through the real
policyengine-core YAML runner, with a minimal model. The cases are the
reviews' counterexamples and the legitimate case next to each, 27 pins on 20
cases. The `pinned-tests` job runs it in an environment of its own with
policyengine-core 3.33.12; elsewhere it skips when policyengine-core isn't
installed.

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

# Household choices

`household-choices.yaml`, beside the register at each rulespec repository's
root, records the points where the law lets a household pick among options
and the pick can change tax or benefits. Examples are an election
(itemizing, IRC 63(e)), an allocation between spouses, columns or returns,
a method, or the kind of return. The law agrees with itself at these points,
so they are not source conflicts. The open question is which option a model
assumes.

Axiom stays deterministic. A choice is an ordinary free input of the module
that grants it, and the caller supplies it. RuleSpec has no defaulted input:
it refuses a rule-level `default`, and its docs say so since
TheAxiomFoundation/axiom-rules-engine#265.
The file holds the default a caller supplies when the household states
nothing, the authority for that default, and the objective a household
would pursue. The simulation layer does the optimizing (PolicyEngine-US
today). For each consumer, the file records how it models the choice and
which tests pin that. `tools/household_choices.py` checks, verifies and
aggregates the file. It imports the register's loader and validators, so
texts, snapshots, years, test references, hygiene and provenance follow the
register's rules exactly.

## Entry shape

| Field | Meaning |
|---|---|
| `id`, `jurisdiction`, `program` | As in the register. The global id is `<jurisdiction>:<id>`. It shares the register's namespace: `check` on either file refuses an id the other file uses. One function, `id_collision_issues`, does this for both. |
| `question` | The choice, as a question. |
| `actor` | Who the law lets choose: `taxpayer`, `spouses-jointly`, `either-spouse`, `eligible-claimants` (the taxpayers who could each claim a person), `household`, `provider-household` or `state-agency`. `provider-household` and `state-agency` are the unit-derivation RFC's terms (axiom-rules-engine `docs/unit-derivation.md`, section 4.3). Where the State agency decides, the household optimizes nothing. Such an entry has no `optimization`, its implementations and proposals model `convention`, `input` or `absent`, and it pins no optimum. |
| `texts`, `pending_texts`, `text_kinds`, `years` | The provision that grants the choice, and when, checked as in the register. At least one text is required. |
| `domain` | `kind` (`boolean`, `enum`, `share` or `amount`) and `per`, the entity each value belongs to (`person`, `marital-unit`, `tax-unit`, `family`, `spm-unit`, `household` or `benefit-unit`). An enum lists at least two kebab-case `options`. A share or amount has `bounds`, two quoted decimal strings, low then high; a share lies within 0 and 1, and an amount gives its `currency`. An optional `coupled_with` lists other entries in the file that must be chosen together, and each must list this one back. |
| `default` | `value`, an option of the domain, and its `basis`: `statute`, `regulation`, `agency` or `convention`. A basis other than `convention` needs a cited text of that kind. Agency kinds are forms, instructions, worksheets, manuals, guidance, policies, plans, calculators, rulemaking and agency practice. A convention needs a `note` saying what it is. A statute that sets its own default ("unless the taxpayer elects") is already encoded as the statutory branch keyed on the election input, with "no election" as `false`. So a statutory default is just the value a caller supplies. |
| `objective` | What a household would pursue: `measure` (`net-income`, the standard, or `total-tax` for a choice that moves only tax, which is the same choice) and `scope` (`tax-unit` or `household`). A choice that can move more than one tax unit takes the household as its scope. That is any choice whose actor is `eligible-claimants`, `household` or `provider-household`, or whose entity is a family, SPM unit, household or benefit unit. `tax-unit` means the model's tax unit with every member's liability combined. For a filing-status choice between spouses, such as filing jointly or separately, or Montana's separate filing on one form, that is both spouses' liability together. PolicyEngine-US keeps the spouses in one tax unit there, so the choice needs no narrower scope. |
| `multi_year` | Optional, `true` only. The choice binds later years or carries amounts forward, and is optimized one year at a time for now. |
| `optimization` | `structure`, how an optimum can be found: `two-way` (a boolean or a two-option enum), `finite` (a boolean or an enum), `piecewise-linear` (a share or an amount, exact at the endpoints and kinks) or `search`. It may add `candidates`, a description of a cheap candidate set. |
| `axiom` | `input`: the input key of the choice's slot in the module that encodes the provision granting the choice, `<jurisdiction>:<module path>#input.<slot>`. `consumers`: other input slots that take the same choice, each with its `polarity`, `same` or `inverse` (true there means the other option). Consumers are only for a boolean choice: a mapping between other kinds of slot values isn't defined, so `check` refuses them rather than guess. A consumer may sit in the granting module, as a different slot. It may give either or both. `check` screens every slot: the module exists in this repository, the slot is not one of its rules or imports, and some formula in it reads the slot as a whole word. When the module declares the slot under `inputs:`, its entity and dtype must fit the domain: `per` is the declared entity (`TaxUnit` is `tax-unit`), and the dtype can hold the kind (`Boolean` or `Judgment` for a boolean, `Money` for an amount, `Rate`, `Decimal` or `Number` for a share, `Text`, `String` or `Integer` for an enum). A consumer is not `input` itself and is listed once. Axiom modules carry no marker, because they are encoder output; this field is the only link from Axiom. |
| `implementations` | Code outside RuleSpec that models the choice: `repo`, `commit`, `path`, `models`, `cites_entry` and `variable`, the model variable that holds the choice. `variable` is required when the implementation optimizes, and `verify` parses a Python `path` and checks that it defines `class <variable>` in module scope: inside a module-level `if`, `try`, `with`, loop or `match` counts, and a class in a docstring, a comment, or a function or class body doesn't. `models` is one of:<br>• `optimized`: the exact optimum. This includes an implementation that evaluates the structure's whole exact set: both branches, every option, or every endpoint and listed kink of a piecewise-linear choice.<br>• `candidate-min`: the best of a cheap subset of that set, which may miss the optimum.<br>• `convention`: a fixed, documented rule.<br>• `input`: the user supplies it, with the default.<br>• `absent`: not modeled.<br>So the worklist's "uses candidate-min where a … comparison finds the exact optimum" always names a real gap. An implementation that optimizes states its own `objective`, which may be narrower than the entry's, such as `federal-income-tax` over the `tax-unit`. Its measures are `net-income`, `total-tax`, `federal-income-tax` and `state-income-tax`. `optimized` needs a structure other than `search`, and `candidate-min` needs `candidates`. `basis` may say how the code decides. |
| `proposed` | Unmerged changes: `repo`, `pr`, `path` and `models`, listed by verify and never counted. |
| `tests` | Tests that pin a consumer: `pins` is `[default]` or `[optimum]`. Each implementation that models the choice is pinned in its repository at its own commit: one that optimizes by an `optimum` pin on its `variable`, so two optimizing implementations need a pin each, and a `convention` or `input` one by a `default` pin. An `absent` one needs none. An `optimum` pin is another repository's YAML test case. It names the decision `variable`, which the runner reads from the case's own simulation (the case need not assert it), and the option the model `chooses`, which must be an option of the domain and not the default. Its optional `instances` lists the case's entity instance ids that must compute that option (for a case where only some tax units or people choose it); without it, every instance must. |
| `source_conflict` | Optional: the global id of a register entry this choice meets, such as a form that forbids an allocation a regulation allows. The conflict entry settles which options the law grants; this entry records which one models assume. |
| `full_optimization` | Optional prose: what exact optimization would take. |

`statutory_not_choice` lists the near misses, so an inventory does not raise
them again. These are a "whichever is greater" that the statute computes, or
a split the statute fixes, such as Montana's equal division of the dependent
care deduction between spouses filing separately on one form. Each item has
a `jurisdiction`, a `citation` and a `note`, and needs no tests.

The file is public, so the register's hygiene rules apply to it. Its prose
also states no money: the file has no money cases, and a public figure needs
a test that computes it.

## Checks and the worklist

`tools/household_choices.py check` runs offline. `tests/test_household_choices.py`
runs it inside the Repository Checks pytest leg. It fails on any of these:

- a malformed entry or an unknown key;
- a default outside the domain, or without the authority its basis names;
- a choice spanning tax units scoped to one;
- a modeling state without what it needs: an optimizing implementation with
  no objective, structure or candidates, or a state-agency entry that is
  optimized;
- an implementation without the pin its state needs, or a vacuous `optimum`
  pin;
- an `axiom.input`, `source_conflict` or `coupled_with` that names nothing;
- a global id that the register also uses;
- an excerpt holding an escape sequence as text, or a `pending_texts`
  excerpt with a paragraph gap, as in the register (see [Excerpts](#excerpts));
- a hygiene hit, or an amount of money in prose.

`verify` (the `source-conflicts` job) checks excerpts, snapshots, shipped
commits and external test files, as the register's verify does. Each
implementation's `cites_entry` must match whether its file carries
`# Household choice <global id>`, compared as a whole id, so a cite of
`us:a-b` is never a cite of `us:a`. The register's verify now compares ids
the same way. The report adds the worklist:

- an implementation that does not model the choice;
- a `convention` or `candidate-min` where a two-way, finite or
  piecewise-linear comparison finds the exact optimum;
- an objective narrower than the entry's;
- a choice no implementation is recorded for;
- a multi-year choice;
- a choice with no Axiom input slot in the module that grants it, naming any
  consumer slots, which a caller sets consistently. The line lists them; it
  doesn't claim their encodings agree, which only a test setting the choice
  once and checking every consumer could show.

`tools/pin_runner.py` runs the household choices' pins with the register's,
labelled `choices.entries[i].tests[j]`. An `optimum` pin must pass and also be
non-vacuous, or it is `vacuous`. The runner hands the oracle each optimum
pin's decision variable; two entries can pin one case on different
variables. After the case runs, the oracle reads each of those variables from
the case's own simulation at the case's period (`simulation.calculate`), with
the id of the entity instance each value belongs to, the dtype the model
stored it in, the variable's definition period and the unit and size of the
period it was read at, and the variables the simulation took as inputs
(`simulation.input_variables`, which counts direct inputs and axes). It also
records whether the case changes the model: a top-level dotted input key (a
parameter override, as the YAML runner reads it), a reform or an extension.
The runner judges each pin on the record for its own variable only, and
requires:

- the case runs the model as shipped: no parameter override, reform or
  extension;
- the decision variable is not among the simulation's inputs;
- the variable was read at one of its own periods: a period of its definition
  period's unit and of size 1, or any period for a variable defined for
  eternity. Core otherwise sums a monthly variable over a year (or takes its
  last month, for a stock) and divides a yearly one into months, and twelve
  monthly defaults can sum to another option. So a monthly choice needs a
  case for one month;
- the model computed at least one value, and the value at every instance the
  pin's `instances` names (at every instance, if it names none) is the chosen
  option;
- the chosen option is not the default.

The check reads the model's own computed value, not the case's stated
output, and the case need not assert the variable. So an error margin, an
implicit tolerance, an entity instance named like the variable, or another
entry's pin on the same case can't stand in for the choice.

Computed values compare as the model stored them:
- An enum or string value compares by name and never as a number:
  `head-of-household` matches PolicyEngine-US's `HEAD_OF_HOUSEHOLD`, and an
  enum member named `16777219` is not one named `16777220`.
- A boolean must be a boolean: 1 is not true.
- An integer, signed or unsigned, compares exactly, and a float64 as a float64.
- A float32, and a number whose dtype the oracle couldn't record, compare as
  float32 numbers.

Whether the chosen option is the default is judged before the case runs, as
float32 numbers whatever the dtype: `16777217` and `16777216` are one option,
so neither shows the other, and `check` refuses such a `chooses` too. That
fails closed.

One more limit, documented here rather than checked: a choice forced through
an input upstream of the variable (an input the variable's formula reads,
which makes it compute the option whatever the household's circumstances) is
not seen. The variable is not itself an input, so the pin passes.

So each `optimum` pin shows the model choosing something other than the
default. It does not show which rule chose it: a convention that picks the
same option in that case passes too. For itemizing, every PolicyEngine-US case
(at main `505f530e49b9`, 2026-10-22) that states `tax_unit_itemizes` without
changing the model also agrees with the deduction comparison, or doesn't state the
deductions. So none of them tells the two apart, and the entry's `basis`
records the code that compares tax.

A `default` pin is checked only to pass; its reviewers check what it asserts.

An `optimum` pin is an example test. The property it samples is that an
optimizing implementation's choice is no worse, on its objective, than every
listed candidate, or any point of the domain for an exact structure. Testing
that property is the implementing repository's job, for example with
Hypothesis over households, forcing each option on a branch.

`aggregate` collects every rulespec repository's file into one JSON or
Markdown view: each entry once, as it is in its file, with its repository,
global id and worklist, and every `statutory_not_choice` item. It reads
repositories in sorted order and entries in file order, and writes JSON with
sorted keys. So the same files give byte-identical output in any order, and
`files_from_view` rebuilds the files it read, empty files included. As for
the register, a file it can't read is left out and reported, and the command
exits 1.
`tests/test_household_choices_properties.py` states these properties and the
tool's other invariants: one namespace from either side, vacuity, scope, the
worklist, and totality. It also includes a differential test of the check's
and the runner's notion of one option.

Run locally:

```bash
python tools/household_choices.py check
AXIOM_CORPUS_RELEASE_PUBLIC_KEY=... python tools/household_choices.py verify \
  --corpus-path ../axiom-corpus          # needs axiom-encode importable
python tools/household_choices.py aggregate --markdown /tmp/choices.md
```
