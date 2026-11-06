"""Property-based and differential tests for tools/source_conflicts.py.

Invariants, for every input:

1. Acceptance: every generated well-formed entry (any status, with the
   ruling and confirmation its status requires, any mix of corpus and pending
   texts) passes `check`.
2. Status rules: a ruling present on an open entry, or missing from a ruled,
   confirmed or contradicted one, is always reported; so is a confirmation on
   an open or ruled entry or missing from a confirmed or contradicted one.
3. Totality: `check` returns a list of strings for any YAML-shaped input and
   never raises, including a well-formed entry with any one known field (at
   any depth) replaced by an arbitrary YAML value.
4. Round trip: a register entry turned into a module interpretation and
   written into a module passes the adopting-module check, and its
   interpretation core equals the entry's.
5. Drift: changing any one core field in the module's copy is reported, and
   the report names that field; for a confirmed entry that includes any one
   field of its confirmation record.
6. Hygiene: a decision-queue id, session id, local path or email address in
   any free-text field is reported; hex digests in commit and sha256 fields
   never are.
7. Aggregation: global ids in the output are unique, the rows do not depend on
   the order registers are given, and each distinct global id appears once.
8. Snapshot text is whitespace-normalised and stable: re-reading its own
   output as plain text returns it unchanged.
9. Differential (when axiom-encode with module.interpretations support is
   importable): `check_module_interpretation` and axiom-encode's
   `_validate_module_interpretations` agree on whether an entry is valid, for
   well-formed entries and for single-field mutations of them.
10. Matcher consistency (when axiom-encode is importable): every run of whole
    words taken from a snapshot's text matches it under axiom-encode's
    proof-atom matcher.
11. Differential: the syntactic test screen (`python_test_exists`) agrees
    with Python's own symbol table on whether a generated module defines each
    name at module level or in a module-level class, through if, try, with,
    loops, match and nested functions; and it never raises on any text or
    bytes (input CPython's parser cannot handle, too deep or too complex, is a
    failed screen; tests/test_source_conflicts.py has bounded cases). The screen decides nothing about collection; tools/pin_runner.py
    asks pytest (tests/test_pin_runner*.py).
12. References by id: a `follows`, `adopts` or `pins` value that is neither
    `reading` nor an alternative id of the entry is always reported, and
    reordering an entry's alternatives never changes whether it passes or
    which reading any reference names.
13. Conflict state: `resolution` present without `conflict: resolved`, or
    `conflict: resolved` without a `resolution` or `years.to`, is always
    reported.
14. Kinds: a `text_kinds` override is accepted exactly when its kind is one
    its path's document class allows; a document class without a
    DOCUMENT_CLASS_KINDS row is always reported.
15. Lag: verify reports an implementation as lagging exactly when what it
    follows differs from what it adopts (`reading` when it names none).
16. Shipped commits: verify reports an external commit (snapshot,
    implementation or test) exactly when it is not reachable from its
    repository's default branch.
17. Quoted words, differentially and against main:
    - `quoted_spans` returns exactly the spans an independently written
      quadratic reference finds for the standard reading, and `quoted_words`
      equals an independent envelope: under each delimited reading (standard,
      strict, nested), delimited words once plus the single span from the
      first mark that may open to the last that may close; that span over
      the whole text, with the delimited quotations' parts outside it; a
      one-pass reading under both opener rules; and main's count. A refusal
      shows that reading's spans.
    - Every Unicode Quotation_Mark character is read.
    - A quotation of N words delimited by single marks at word boundaries
      counts at least N, whatever apostrophes it holds (possessives,
      elisions, elided years, dropped letters, nested quotations) and
      whatever surrounds it; so does any recognisable delimited quotation,
      nested in the same marks or not.
    - Double quotations in plain prose are counted exactly in each delimited
      reading, within the README's scope: every pair but ‚…‘ and ‚…’ (single
      marks), words holding none of the quotation's own closing marks, and no
      space after ” » › ″ as an opener; whatever the words end in or follows
      the closer, citations included, in a description with no single mark
      that may open. Overall they are too, unless main's count is higher
      (main read “ as an opener). A quotation nested in a pair that shares
      no mark with the outer one counts exactly in the nested reading and
      overall, and no reading counts more; nesting in the same marks, or a
      pair sharing a mark, with the inner quotation starting with a letter or
      digit, counts at least in full. Plain prose quotes nothing.
    - The floor is main's scanner exactly (`_main_words` equals a verbatim
      copy of main's function), so the count is never below main's; and
      widening the single openers never lowers it.

Hypothesis is not installed in the shared validate workflow's pytest leg, so
these skip there; the source-conflicts workflow installs it and runs them.
"""

from __future__ import annotations

import copy
import importlib.util
import string
import sys
import unicodedata
from pathlib import Path

import pytest
import yaml

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, assume, example, given, settings, strategies as st  # noqa: E402

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "source_conflicts.py"
_spec = importlib.util.spec_from_file_location("source_conflicts", TOOL_PATH)
sc = importlib.util.module_from_spec(_spec)
sys.modules["source_conflicts"] = sc
_spec.loader.exec_module(sc)

REPO = "TheAxiomFoundation/rulespec-us"
SETTINGS = settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])

# Free text without digits, '@', '/' or '~', so it never trips hygiene by
# accident, and without a money spelling ("usd" is one), so it never trips the
# money rule.
prose = st.text(alphabet=string.ascii_letters + " ,.;:'()-", min_size=1, max_size=40).filter(
    lambda s: s.strip() and not sc._unsupported_money(s)
)
# A slug such as "d1338" reads as a decision-queue id, which hygiene rightly
# rejects (an intended violation), so generated slugs avoid that shape.
kebab = st.from_regex(r"[a-z0-9]{1,6}(-[a-z0-9]{1,6}){0,3}", fullmatch=True).filter(
    lambda s: not __import__("re").search(r"\bd[0-9]{3,5}\b", s)
)
hexs = lambda n: st.text(alphabet="0123456789abcdef", min_size=n, max_size=n)  # noqa: E731
dates = st.dates(min_value=__import__("datetime").date(1990, 1, 1), max_value=__import__("datetime").date(2040, 12, 31))
corpus_paths = st.builds(
    lambda j, c, segs: "/".join([j, c, *segs]),
    st.sampled_from(["us", "us-co", "uk-babergh"]),
    st.sampled_from(["statute", "regulation", "guidance", "manual", "form", "policy"]),
    st.lists(st.from_regex(r"[a-z0-9][a-z0-9.-]{0,5}", fullmatch=True), min_size=1, max_size=4),
).filter(lambda path: not any(pattern.search(path) for pattern, _ in sc.HYGIENE_PATTERNS))  # e.g. us/statute/d000
urls = st.builds(lambda host, path: f"https://{host}.org/{path}", st.from_regex(r"[a-z]{3,8}", fullmatch=True), kebab)
texts = st.lists(st.fixed_dictionaries({"corpus_citation_path": corpus_paths, "excerpt": prose}), max_size=3)
pending = st.lists(
    st.fixed_dictionaries(
        {
            "citation": prose,
            "kind": st.sampled_from(sc.SOURCE_KINDS),
            "url": urls,
            "snapshot": st.fixed_dictionaries(
                {
                    "repo": st.just("PolicyEngine/microcosm-dynamics"),
                    "commit": hexs(40),
                    "path": st.builds(lambda k: f"tests/data/{k}.html", kebab),
                    "sha256": hexs(64),
                }
            ),
            "excerpt": prose,
        }
    ),
    max_size=3,
)
alternative_ids = kebab.filter(lambda s: s != sc.ADOPTED_READING)


@st.composite
def alternatives(draw):
    ids = draw(st.lists(alternative_ids, min_size=1, max_size=3, unique=True))
    return [
        {"id": alternative_id, "reading": draw(prose), **({"effect": draw(prose)} if draw(st.booleans()) else {})}
        for alternative_id in ids
    ]


years_values = st.one_of(
    st.builds(lambda start, span, kind: {"from": start, "to": start + span, "type": kind},
              st.integers(1990, 2030), st.integers(0, 10), st.sampled_from([t for t in sc.YEAR_TYPES if t != "program"])),
    st.builds(lambda start, note: {"from": start, "type": "program", "note": note}, st.integers(1990, 2030), prose),
)
unpublished = st.lists(
    st.fixed_dictionaries({"kind": st.sampled_from(sc.SOURCE_KINDS), "description": prose, "date": dates.map(str)}),
    min_size=1,
    max_size=2,
)
records = st.fixed_dictionaries({"by": prose, "date": st.one_of(dates, dates.map(str)), "record": urls})
confirmations = st.fixed_dictionaries(
    {"by": prose, "date": dates.map(str), "excerpt": prose}, optional={"record": urls}
)


@st.composite
def entries(draw, jurisdiction="us"):
    status = draw(st.sampled_from(sc.STATUSES[:3]))  # contradicted is always a finding
    body_texts = draw(texts)
    body_pending = draw(pending)
    assume(body_texts or body_pending)
    alts = draw(alternatives())
    ids = [alt["id"] for alt in alts]
    value = {
        "id": draw(kebab),
        "jurisdiction": jurisdiction,
        "program": draw(kebab),
        "question": draw(prose),
        "texts": body_texts,
        "reading": draw(prose),
        "alternatives": alts,
        "basis": draw(prose),
        "status": status,
        "outcome": draw(st.sampled_from(sc.OUTCOMES)),
    }
    if body_pending:
        value["pending_texts"] = body_pending
    if draw(st.booleans()):
        value["years"] = draw(years_values)
    if draw(st.booleans()) and "to" in value.get("years", {}):
        value["conflict"] = "resolved"
        value["resolution"] = {"by": draw(st.sampled_from(sc.RESOLVERS)), "effective": str(draw(dates)), "record": draw(urls)}
    if draw(st.booleans()):
        value["unpublished_sources"] = draw(unpublished)
    overridable = [
        text["corpus_citation_path"]
        for text in body_texts
        if len(sc.DOCUMENT_CLASS_KINDS[sc.document_class(text["corpus_citation_path"])]) > 1
    ]
    if overridable and draw(st.booleans()):
        path = draw(st.sampled_from(overridable))
        value["text_kinds"] = {path: draw(st.sampled_from(sc.DOCUMENT_CLASS_KINDS[sc.document_class(path)]))}
    if status != "open":
        value["ruling"] = draw(records)
    if status == "confirmed":
        value["confirmation"] = draw(confirmations)
    if draw(st.booleans()):
        commit = draw(hexs(40))
        value["implementations"] = [
            {
                "repo": "PolicyEngine/microcosm-dynamics",
                "commit": commit,
                "path": "src/x.py",
                "follows": draw(st.sampled_from(["reading", *ids])),
                "cites_entry": draw(st.booleans()),
            }
        ]
        if draw(st.booleans()):
            value["implementations"][0]["adopts"] = draw(st.sampled_from(["reading", *ids]))
            value["implementations"][0]["basis"] = draw(prose)
            if draw(st.booleans()):
                value["implementations"][0]["ruling"] = draw(records)
                if draw(st.booleans()):
                    value["implementations"][0]["ruling"]["principle"] = draw(st.sampled_from(sc.PRINCIPLES))
        value["tests"] = [
            {"repo": "PolicyEngine/microcosm-dynamics", "commit": commit, "path": "tests/test_x.py", "name": "test_default", "pins": ["reading"]}
        ] + [
            {"repo": "PolicyEngine/microcosm-dynamics", "commit": commit, "path": "tests/test_x.py", "name": f"test_alt_{i}", "pins": [alternative_id]}
            for i, alternative_id in enumerate(ids)
        ]
    if value.get("tests") and draw(st.booleans()):
        value["money_case"] = {
            "description": draw(prose),
            "amount": draw(st.from_regex(r"(0|[1-9][0-9]{0,4})(\.[0-9]{2})?", fullmatch=True)),
            "currency": "USD",
            "period": draw(st.sampled_from(sc.PERIODS)),
            "computed_by": draw(st.sampled_from([test["name"] for test in value["tests"]])),
        }
    return value


def repo(tmp_path: Path) -> sc.RepoContext:
    for directory in ("us/statutes", "us-co/regulations"):
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)
    return sc.RepoContext(root=tmp_path, repo=REPO)


# 1. Acceptance
@SETTINGS
@given(value=entries())
def test_generated_entries_pass(tmp_path, value):
    assert sc.check_register({"version": 1, "entries": [value]}, repo(tmp_path), scan_modules=False) == []


# 2. Status rules
@SETTINGS
@given(value=entries(), status=st.sampled_from(sc.STATUSES), ruling=records, confirmation=confirmations, keep_ruling=st.booleans(), keep_confirmation=st.booleans())
def test_status_rules(tmp_path, value, status, ruling, confirmation, keep_ruling, keep_confirmation):
    value = copy.deepcopy(value)
    value["status"] = status
    value.pop("ruling", None)
    value.pop("confirmation", None)
    if keep_ruling:
        value["ruling"] = ruling
    if keep_confirmation:
        value["confirmation"] = confirmation
    issues = sc.check_register({"version": 1, "entries": [value]}, repo(tmp_path), scan_modules=False)
    ruling_wrong = keep_ruling != (status != "open")
    confirmation_wrong = keep_confirmation != (status in {"confirmed", "contradicted"})
    assert any(".ruling must be" in issue for issue in issues) == ruling_wrong
    assert any(".confirmation must be" in issue for issue in issues) == confirmation_wrong
    assert any("contradicted this reading" in issue for issue in issues) == (status == "contradicted")


# 3. Totality
yaml_values = st.recursive(
    st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=8), dates),
    lambda children: st.one_of(st.lists(children, max_size=4), st.dictionaries(st.text(max_size=8), children, max_size=4)),
    max_leaves=25,
)


@SETTINGS
@given(payload=st.one_of(yaml_values, st.fixed_dictionaries({"version": st.just(1), "entries": st.lists(yaml_values, max_size=3)})))
def test_check_is_total(tmp_path, payload):
    issues = sc.check_register(payload, repo(tmp_path), scan_modules=True)
    assert isinstance(issues, list) and all(isinstance(issue, str) for issue in issues)


# Totality where it matters most: a well-formed entry with one known field,
# at any depth, replaced by an arbitrary YAML value. Random keys rarely hit
# the schema's own (often long) field names, so target them directly.
FIELD_PATHS = [
    (key,) for key in sorted(sc.ENTRY_KEYS)
] + [
    ("texts", 0, "corpus_citation_path"), ("texts", 0, "excerpt"),
    ("pending_texts", 0, "citation"), ("pending_texts", 0, "url"), ("pending_texts", 0, "snapshot"),
    ("pending_texts", 0, "snapshot", "repo"), ("pending_texts", 0, "snapshot", "commit"),
    ("pending_texts", 0, "snapshot", "sha256"), ("alternatives", 0, "reading"), ("alternatives", 0, "effect"),
    ("ruling", "by"), ("ruling", "date"), ("ruling", "record"),
    ("implementations", 0, "repo"), ("implementations", 0, "commit"), ("implementations", 0, "path"),
    ("implementations", 0, "follows"), ("implementations", 0, "cites_entry"),
    ("tests", 0, "repo"), ("tests", 0, "commit"), ("tests", 0, "path"), ("tests", 0, "name"), ("tests", 0, "pins"),
    ("money_case", "amount"), ("money_case", "currency"), ("money_case", "period"), ("money_case", "description"),
    ("money_case", "computed_by"),
]


def _set_path(value, path, new):
    target = value
    for key in path[:-1]:
        if isinstance(target, dict) and key in target:
            target = target[key]
        elif isinstance(target, list) and isinstance(key, int) and key < len(target):
            target = target[key]
        else:
            return False
    if isinstance(target, dict) or (isinstance(target, list) and isinstance(path[-1], int) and path[-1] < len(target)):
        target[path[-1]] = new
        return True
    return False


@SETTINGS
@given(value=entries(), path=st.sampled_from(FIELD_PATHS), new=yaml_values)
def test_check_is_total_on_malformed_known_fields(tmp_path, value, path, new):
    value = copy.deepcopy(value)
    assume(_set_path(value, path, new))
    issues = sc.check_register({"version": 1, "entries": [value, copy.deepcopy(value)]}, repo(tmp_path), scan_modules=True)
    assert isinstance(issues, list) and all(isinstance(issue, str) for issue in issues)


# 4 and 5. Round trip and drift
@SETTINGS
@given(value=entries(), field=st.sampled_from([f for f in sc.INTERPRETATION_CORE if f != "confirmation"]))
def test_round_trip_and_drift(tmp_path, value, field):
    ctx = repo(tmp_path)
    value = copy.deepcopy(value)
    value.pop("pending_texts", None)
    assume(value["texts"])
    module = "us/statutes/42/403.yaml"
    value["adopted_by"] = [{"module": module, "interpretation": value["id"]}]
    # The module is the only adopter here; an implementation following an
    # alternative would need its own pinning test.
    value.pop("implementations", None)
    value["tests"] = [{"path": "us/statutes/42/403.test.yaml", "name": "case", "pins": ["reading"]}]
    if "money_case" in value:
        value["money_case"]["computed_by"] = "case"
    carried = sc.to_module_interpretation(value, interpretation_id=value["id"], affects=["rule_a"])
    assert sc.interpretation_core(carried) == sc.interpretation_core(value)
    path = ctx.root / module
    path.parent.mkdir(parents=True, exist_ok=True)
    (ctx.root / "us/statutes/42/403.test.yaml").write_text(yaml.safe_dump([{"name": "case"}]))

    def write(item):
        path.write_text(yaml.safe_dump({"format": "rulespec/v1", "module": {"interpretations": [item]}, "rules": [{"name": "rule_a"}]}))

    write(carried)
    assert sc.check_register({"version": 1, "entries": [value]}, ctx) == []
    drifted = copy.deepcopy(carried)
    drifted[field] = {"texts": [], "alternatives": [{"id": "different", "reading": "different"}]}.get(field, "different")
    if field == "status":
        drifted["status"] = "open" if value["status"] != "open" else "ruled"
    if field == "ruling":
        drifted["ruling"] = {**(value.get("ruling") or {}), "by": "Someone Else Organisation"}
    assume(drifted[field] != carried.get(field))
    write(drifted)
    issues = sc.check_register({"version": 1, "entries": [value]}, ctx)
    assert any(f"`{field}` differs" in issue for issue in issues)


# 5b. Drift of a confirmation record: a confirmed entry whose module copy
# carries a different confirmation is reported, naming the field.
@SETTINGS
@given(value=entries(), confirmation=confirmations, field=st.sampled_from(["by", "date", "excerpt", "record"]), other=prose)
def test_confirmation_drift(tmp_path, value, confirmation, field, other):
    ctx = repo(tmp_path)
    value = copy.deepcopy(value)
    value.pop("pending_texts", None)
    assume(value["texts"])
    value["status"] = "confirmed"
    value.setdefault("ruling", {"by": "Org", "date": "2026-10-12", "record": "https://example.org/r"})
    value["confirmation"] = dict(confirmation)
    module = "us/statutes/42/403.yaml"
    value["adopted_by"] = [{"module": module, "interpretation": value["id"]}]
    value.pop("implementations", None)
    value["tests"] = [{"path": "us/statutes/42/403.test.yaml", "name": "case", "pins": ["reading"]}]
    if "money_case" in value:
        value["money_case"]["computed_by"] = "case"
    carried = sc.to_module_interpretation(value, interpretation_id=value["id"], affects=["rule_a"])
    drifted = copy.deepcopy(carried)
    replacement = {"date": "2031-01-02", "record": "https://example.org/other"}.get(field, other)
    assume(drifted["confirmation"].get(field) != replacement)
    drifted["confirmation"][field] = replacement
    path = ctx.root / module
    path.parent.mkdir(parents=True, exist_ok=True)
    (ctx.root / "us/statutes/42/403.test.yaml").write_text(yaml.safe_dump([{"name": "case"}]))
    path.write_text(yaml.safe_dump({"format": "rulespec/v1", "module": {"interpretations": [drifted]}, "rules": [{"name": "rule_a"}]}))
    issues = sc.check_register({"version": 1, "entries": [value]}, ctx)
    assert any("`confirmation` differs" in issue for issue in issues), issues


# 6. Hygiene
private = st.sampled_from(["d1338", "local_6085d52a", "/Users/x/y", "~/notes", "a.b@example.org"])


@SETTINGS
@given(value=entries(), token=private, field=st.sampled_from(["question", "reading", "basis"]))
def test_hygiene(tmp_path, value, token, field):
    value = copy.deepcopy(value)
    value[field] = f"{value[field]} {token} end"
    issues = sc.check_register({"version": 1, "entries": [value]}, repo(tmp_path), scan_modules=False)
    assert any("the register is public" in issue for issue in issues)


@SETTINGS
@given(value=entries(), digest=hexs(64))
def test_hygiene_ignores_digests(tmp_path, value, digest):
    value = copy.deepcopy(value)
    for item in value.get("pending_texts", []):
        item["snapshot"]["sha256"] = digest
        item["snapshot"]["commit"] = digest[:40]
    issues = sc.check_register({"version": 1, "entries": [value]}, repo(tmp_path), scan_modules=False)
    assert not any("the register is public" in issue for issue in issues)


# 7. Aggregation
@SETTINGS
@given(us=st.lists(entries(), max_size=4), uk=st.lists(entries(jurisdiction="uk"), max_size=4))
def test_aggregate(us, uk):
    registers = {"TheAxiomFoundation/rulespec-us": {"entries": us}, "TheAxiomFoundation/rulespec-uk": {"entries": uk}}
    rows, issues = sc.aggregate(registers)
    reversed_rows, _ = sc.aggregate(dict(reversed(list(registers.items()))))
    ids = [row["global_id"] for row in rows]
    assert len(ids) == len(set(ids))
    assert rows == reversed_rows
    assert set(ids) == {sc.global_id(e) for e in us + uk}
    assert not any("outside that repository" in issue for issue in issues)


# 8. Snapshot text
@SETTINGS
@given(parts=st.lists(st.one_of(prose, st.sampled_from(["<p>", "</p>", "<b>", "</b>", "<br/>", "&amp;", "&#8217;", "\n\n", "\t"])), max_size=20))
def test_snapshot_text_normalised(parts):
    text = sc.snapshot_text("".join(parts).encode(), "x.html")
    assert text == text.strip() and "  " not in text and "\n" not in text and "<" not in text
    assert sc.snapshot_text(text.encode(), "x.txt") == text


# 9. Differential against axiom-encode
def _encoder_validator():
    proof_validator = pytest.importorskip("axiom_encode.harness.proof_validator")
    validator = getattr(proof_validator, "_validate_module_interpretations", None)
    if validator is None:
        pytest.skip("this axiom-encode predates module.interpretations")
    probe = {
        "id": "probe",
        "question": "q",
        "texts": [{"corpus_citation_path": "us/statute/1/1", "excerpt": "x"}],
        "reading": "r",
        "alternatives": [{"id": "other", "reading": "a"}],
        "basis": "b",
        "status": "open",
        "affects": ["rule_a"],
    }
    if validator({"module": {"interpretations": [probe]}, "rules": [{"name": "rule_a"}]}, source_texts=None):
        pytest.skip(
            "this axiom-encode does not accept alternatives[].id yet; the required id lands in "
            "TheAxiomFoundation/axiom-encode#1835 and TheAxiomFoundation/axiom-rules-engine#247"
        )
    return validator


MUTATIONS = [
    lambda item: item.pop("question"),
    lambda item: item.__setitem__("reading", "   "),
    lambda item: item.__setitem__("alternatives", []),
    lambda item: item.__setitem__("texts", []),
    lambda item: item.__setitem__("status", "pending"),
    lambda item: item.__setitem__("id", "Bad_Id"),
    lambda item: item.__setitem__("affects", ["no_such_rule"]),
    lambda item: item.__setitem__("affects", []),
    lambda item: item.__setitem__("extra", 1),
    lambda item: item["alternatives"][0].__setitem__("why", "x"),
    lambda item: item["texts"][0].__setitem__("note", "x") if item.get("texts") else item.__setitem__("texts", []),
    lambda item: item.__setitem__("ruling", {"by": "Org", "date": "2026-02-30", "record": "https://x.org/1"}),
    lambda item: item.__setitem__("ruling", {"by": "Org", "date": "2026-02-03", "record": "http://x.org/1"}),
    lambda item: item.__setitem__("confirmation", {"by": "Org", "date": "2026-02-03"}),
    lambda item: item["alternatives"][0].pop("id"),
    lambda item: item["alternatives"][0].__setitem__("id", "Not_Kebab"),
    lambda item: item["alternatives"].append(dict(item["alternatives"][0])),
]


@SETTINGS
@given(value=entries(), mutation=st.one_of(st.none(), st.sampled_from(range(len(MUTATIONS)))))
def test_matches_encoder_interpretation_rules(value, mutation):
    validator = _encoder_validator()
    assume(value["texts"])
    item = sc.to_module_interpretation(value, interpretation_id=value["id"], affects=["rule_a"])
    if mutation is not None:
        MUTATIONS[mutation](item)
    ours = sc.check_module_interpretation(item, rule_names={"rule_a"}, label="x")
    theirs = validator({"module": {"interpretations": [item]}, "rules": [{"name": "rule_a"}]}, source_texts=None)
    assert bool(ours) == bool(theirs), (ours, theirs)


# 10. Matcher consistency
@SETTINGS
@given(words=st.lists(st.from_regex(r"[A-Za-z][a-z]{0,8}[.,;]?", fullmatch=True), min_size=3, max_size=30), data=st.data())
def test_word_runs_match_under_encoder_matcher(words, data):
    pytest.importorskip("axiom_encode.harness.proof_validator")
    matches = sc.encoder_matcher()
    html = "<p>" + " ".join(f"<b>{w}</b>" if i % 4 == 0 else w for i, w in enumerate(words)) + "</p>"
    text = sc.snapshot_text(html.encode(), "x.html")
    tokens = text.split(" ")
    start = data.draw(st.integers(0, len(tokens) - 1))
    end = data.draw(st.integers(start + 1, len(tokens)))
    assert matches(text, " ".join(tokens[start:end]))


# 11. Differential: the syntactic test screen against Python's own symbol
# table. A def is defined at module level, or in a module-level class, exactly
# when symtable gives the module (or that class) a child function scope with
# that name; compound statements (if, try, with, loops, match) open no scope.
# The screen says nothing about collection: tools/pin_runner.py asks pytest.
DEF_NAMES = ["test_a", "test_b"]
CLASS_NAMES = ["TestC", "TestD"]
CANDIDATES = DEF_NAMES + [f"{cls}::{name}" for cls in CLASS_NAMES for name in DEF_NAMES]


def _indent(lines: list[str]) -> list[str]:
    return ["    " + line for line in lines]


@st.composite
def blocks(draw, depth: int = 0) -> list[str]:
    """A non-empty block of statements, as source lines."""

    lines: list[str] = []
    for _ in range(draw(st.integers(1, 3))):
        kinds = ["pass", "def", "assign"] + (["class", "if", "try", "with", "for", "while", "match", "nested"] if depth < 3 else [])
        kind = draw(st.sampled_from(kinds))
        name = draw(st.sampled_from(DEF_NAMES))
        if kind == "pass":
            lines.append("pass")
        elif kind == "assign":
            lines.append(f"{name} = lambda: None")
        elif kind == "def":
            lines += [f"{draw(st.sampled_from(['def', 'async def']))} {name}(self=None):", *_indent(["pass"])]
        elif kind == "nested":  # a def inside a function is not module level
            lines += [f"def outer_{depth}():", *_indent(draw(blocks(depth + 1)))]
        elif kind == "class":
            lines += [f"class {draw(st.sampled_from(CLASS_NAMES))}:", *_indent(draw(blocks(depth + 1)))]
        elif kind == "if":
            lines += ["if X:", *_indent(draw(blocks(depth + 1)))]
            if draw(st.booleans()):
                lines += ["else:", *_indent(draw(blocks(depth + 1)))]
        elif kind == "try":
            lines += ["try:", *_indent(draw(blocks(depth + 1))), "except ImportError:", *_indent(draw(blocks(depth + 1)))]
            if draw(st.booleans()):
                lines += ["finally:", *_indent(draw(blocks(depth + 1)))]
        elif kind == "with":
            lines += ["with open('x') as handle:", *_indent(draw(blocks(depth + 1)))]
        elif kind == "for":
            lines += ["for item in []:", *_indent(draw(blocks(depth + 1)))]
        elif kind == "while":
            lines += ["while False:", *_indent(draw(blocks(depth + 1)))]
        else:
            lines += ["match X:", *_indent(["case 1:", *_indent(draw(blocks(depth + 1)))])]
    return lines


def _symtable_defines(source: str, name: str) -> bool:
    import symtable

    scope, _, function = name.rpartition("::")
    tables = symtable.symtable(source, "test_generated.py", "exec").get_children()
    if scope:
        tables = [child for table in tables if table.get_type() == "class" and table.get_name() == scope for child in table.get_children()]
    return any(table.get_type() == "function" and table.get_name() == function for table in tables)


@SETTINGS
@given(lines=blocks())
def test_screen_matches_the_symbol_table(lines):
    source = "\n".join(lines) + "\n"
    for name in CANDIDATES:
        assert sc.python_test_exists(source, name) == _symtable_defines(source, name), (name, source)
        assert sc.python_test_exists(source.encode(), name) == _symtable_defines(source, name), (name, source)


# 12. References by id
@SETTINGS
@given(value=entries(), ref=st.text(max_size=20), field=st.sampled_from(["follows", "adopts", "pins"]))
def test_unknown_reading_references_fail(tmp_path, value, ref, field):
    value = copy.deepcopy(value)
    assume(ref != sc.ADOPTED_READING and ref not in sc.alternative_ids(value["alternatives"]))
    commit = "c" * 40
    implementation = {"repo": "PolicyEngine/policyengine-us", "commit": commit, "path": "x.py", "follows": "reading", "cites_entry": False}
    value["implementations"] = [implementation]
    value["tests"] = [{"repo": "PolicyEngine/policyengine-us", "commit": commit, "path": "t.py", "name": "test_x", "pins": ["reading"]}]
    if field == "pins":
        value["tests"][0]["pins"] = ["reading", ref]
    else:
        implementation[field] = ref
        implementation["basis"] = "why"
    issues = sc.check_register({"version": 1, "entries": [value]}, repo(tmp_path), scan_modules=False)
    assert any("which is neither `reading` nor the id" in issue or "must be `reading` or the id" in issue for issue in issues)


def _resolved_reading(entry, ref):
    if ref == sc.ADOPTED_READING:
        return entry["reading"]
    return next(alt["reading"] for alt in entry["alternatives"] if alt["id"] == ref)


@SETTINGS
@given(value=entries(), data=st.data())
def test_reordering_alternatives_keeps_validity_and_picks(tmp_path, value, data):
    shuffled = copy.deepcopy(value)
    shuffled["alternatives"] = data.draw(st.permutations(value["alternatives"]))
    ctx = repo(tmp_path)
    check = lambda e: sc.check_register({"version": 1, "entries": [e]}, ctx, scan_modules=False)  # noqa: E731
    assert check(shuffled) == check(value) == []
    for before, after in zip(value.get("implementations", []), shuffled.get("implementations", [])):
        for key in ("follows", "adopts"):
            if key in before:
                assert _resolved_reading(value, before[key]) == _resolved_reading(shuffled, after[key])


# 13. Conflict state
@SETTINGS
@given(value=entries(), conflict=st.sampled_from([None, "live", "resolved"]), with_resolution=st.booleans(), with_to=st.booleans())
def test_conflict_state_rules(tmp_path, value, conflict, with_resolution, with_to):
    value = copy.deepcopy(value)
    for key in ("conflict", "resolution"):
        value.pop(key, None)
    value["years"] = {"from": 2020, "type": "tax", **({"to": 2023} if with_to else {})}
    if conflict is not None:
        value["conflict"] = conflict
    if with_resolution:
        value["resolution"] = {"by": "agency", "effective": "2024-01-01", "record": "https://example.org/r"}
    issues = sc.check_register({"version": 1, "entries": [value]}, repo(tmp_path), scan_modules=False)
    resolved = conflict == "resolved"
    expected_wrong = (resolved and not with_resolution) or (not resolved and with_resolution) or (resolved and not with_to)
    assert bool(issues) == expected_wrong, issues
    if not resolved and with_resolution:
        assert any("resolution must be absent while conflict is `live`" in issue for issue in issues)


# 14. Kinds
@SETTINGS
@given(value=entries(), document_class=st.sampled_from(sorted(sc.DOCUMENT_CLASS_KINDS)), kind=st.sampled_from(sc.SOURCE_KINDS))
def test_text_kind_overrides_match_the_document_class(tmp_path, value, document_class, kind):
    value = copy.deepcopy(value)
    path = f"us/{document_class}/a/1"
    value["texts"] = [{"corpus_citation_path": path, "excerpt": "words"}]
    value["text_kinds"] = {path: kind}
    issues = sc.check_register({"version": 1, "entries": [value]}, repo(tmp_path), scan_modules=False)
    allowed = kind in sc.DOCUMENT_CLASS_KINDS[document_class]
    assert (not any("text_kinds" in issue for issue in issues)) == allowed
    assert sc.text_kind(value, path) == kind


@SETTINGS
@given(value=entries(), document_class=st.from_regex(r"[a-z][a-z-]{1,12}", fullmatch=True))
def test_unknown_document_classes_fail_closed(tmp_path, value, document_class):
    assume(document_class not in sc.DOCUMENT_CLASS_KINDS)
    value = copy.deepcopy(value)
    value.pop("text_kinds", None)
    value["texts"] = [{"corpus_citation_path": f"us/{document_class}/a/1", "excerpt": "words"}]
    issues = sc.check_register({"version": 1, "entries": [value]}, repo(tmp_path), scan_modules=False)
    assert any("has no DOCUMENT_CLASS_KINDS row" in issue for issue in issues)
    assert sc.text_kind(value, f"us/{document_class}/a/1") is None


# 15. Lag
@SETTINGS
@given(value=entries(), data=st.data())
def test_verify_lag_iff_follows_differs_from_adopts(value, data):
    value = copy.deepcopy(value)
    value["texts"] = []
    value.pop("pending_texts", None)
    refs = ["reading", *sc.alternative_ids(value["alternatives"])]
    follows = data.draw(st.sampled_from(refs))
    adopts = data.draw(st.one_of(st.none(), st.sampled_from(refs)))
    implementation = {"repo": "PolicyEngine/policyengine-us", "commit": "c" * 40, "path": "x.py", "follows": follows, "cites_entry": False}
    if adopts is not None:
        implementation["adopts"] = adopts
    value["implementations"] = [implementation]
    value["tests"] = []
    _, report = sc.verify_register(
        {"version": 1, "entries": [value]}, fetch=lambda repo, commit, path: b"", matches=lambda a, b: True, resolve=None
    )
    lagging = any(line.startswith("lags:") for line in report)
    assert lagging == (follows != (adopts or "reading"))


# 16. Shipped commits
@SETTINGS
@given(value=entries(), data=st.data())
def test_verify_flags_exactly_the_unshipped_commits(value, data):
    value = copy.deepcopy(value)
    value["texts"] = []
    external = []
    for item in value.get("pending_texts", []):
        external.append((item["snapshot"]["repo"], item["snapshot"]["commit"]))
    for key in ("implementations", "tests"):
        for item in value.get(key, []):
            if "repo" in item:
                external.append((item["repo"], item["commit"]))
    shipped = {pair: data.draw(st.booleans()) for pair in set(external)}
    issues, _ = sc.verify_register(
        {"version": 1, "entries": [value]},
        fetch=lambda repo, commit, path: b"",
        matches=lambda a, b: True,
        resolve=None,
        on_default_branch=lambda repo, commit: shipped[(repo, commit)],
    )
    flagged = [issue for issue in issues if "default branch; pin a commit" in issue]
    assert len(flagged) == sum(1 for pair in external if not shipped[pair])


@SETTINGS
@given(source=st.one_of(st.text(max_size=200), st.binary(max_size=200)), name=st.one_of(st.sampled_from(CANDIDATES), st.text(max_size=20)))
def test_screen_is_total(source, name):
    assert sc.python_test_exists(source, name) in (True, False)


# An alphabet that reaches every branch of the quote scanner: letters, a
# decimal and a superscript digit, a combining mark, ASCII and Unicode
# spaces, every recognised mark, brackets and dashes, and other punctuation.
QUOTE_ALPHABET = "abs1\u00b9\u0301 \u00a0\u3000'\u2018\u2019\u201b\"\u201c\u201d\u201e\u201a\u201f\u2e42\u00ab\u00bb\u2039\u203a\u300c\u300d\u300e\u300f\ufe41\ufe42\ufe43\ufe44\uff62\uff63\u301d\u301e\u301f\uff02\uff07\u2032\u2033\u2035\u2036\u275b\u275c\u275d\u275e\u275f\u2760\u276e\u276f([-\u2014/:."
# Whole words and marks, so possessives (as' a), elisions ('em), elided
# years ('1) and nested marks turn up more often than letter by letter.
QUOTE_TOKENS = [
    "a", "b", "s", "as", "em", "tis", "1", "\u00b9", " ", " ", "\u00a0", "'", "\u2018", "\u2019", "\uff07", "\u201b", "\u2032",
    '"', "\u201c", "\u201d", "\u201e", "\u201a", "\u00ab", "\u00bb", "\u2039", "\u203a", "\u300c", "\u300d", "\u301d", "\u301e", "\uff02", "\u2033", "\u275d", "\u275e", ":", "(", "\u2014", "/", ".",
]
quote_texts = st.one_of(
    st.text(alphabet=QUOTE_ALPHABET, max_size=60),
    st.lists(st.sampled_from(QUOTE_TOKENS), max_size=30).map("".join),
)

# The reference scanner below is deliberately independent of the production
# constants, predicates and searches: membership and suffix scans, quadratic.
REF_PAIRS = {
    '"': '"', "\u201c": "\u201d", "\u201e": "\u201c\u201d", "\u201a": "\u2018\u2019", "\u201f": "\u201d", "\u2e42": "\u201c\u201d", "\u00ab": "\u00bb", "\u2039": "\u203a", "\u201d": "\u201d", "\u00bb": "\u00ab\u00bb",
    "\u203a": "\u2039\u203a", "\u300c": "\u300d", "\u300e": "\u300f", "\ufe41": "\ufe42", "\ufe43": "\ufe44", "\uff62": "\uff63", "\u301d": "\u301e\u301f", "\uff02": "\uff02", "\u2033": "\u2033",
    "\u2036": "\u2033", "\u275d": "\u275e", "\u2760": "\u275e", "\u276e": "\u276f", "\U0001f676": "\U0001f677", "\U0001f678": "\U0001f676\U0001f677",
}
REF_CONTEXT = "\u201d\u00bb\u203a\u2033"
REF_SINGLE_OPENERS = "'\u2018\u2019\uff07\u201b\u2032\u2035\u275b\u275f"
REF_MARKS = set("".join(REF_PAIRS) + "".join(REF_PAIRS.values()) + REF_SINGLE_OPENERS + "\u275c")
# Unicode 17's Quotation_Mark characters (PropList.txt).
UNICODE_QUOTATION_MARKS = set("\"'\u00ab\u00bb\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\u2039\u203a\u2e42\u300c\u300d\u300e\u300f\u301d\u301e\u301f\ufe41\ufe42\ufe43\ufe44\uff02\uff07\uff62\uff63")


def test_every_unicode_quotation_mark_is_read():
    assert UNICODE_QUOTATION_MARKS <= REF_MARKS
    assert REF_MARKS == set(sc._QUOTATION_MARKS)


def _ref_wide(text, i):
    if i == 0:
        return True
    before = text[i - 1]
    return before.isspace() or before in "/:\uff1a" or before in REF_MARKS or unicodedata.category(before) in ("Ps", "Pd", "Pi")


def _ref_word_char(char):
    return char.isalpha() or unicodedata.category(char) == "Nd"


def _ref_closer_context(text, i):
    return i + 1 == len(text) or not _ref_word_char(text[i + 1])


def _ref_word_count(span):
    return len([token for token in span.split() if any(char.isalnum() for char in token)])


# Openers that also close another pair.
REF_ALSO_CLOSES = {mark for mark in REF_PAIRS if any(mark in closers for opener, closers in REF_PAIRS.items() if opener != mark)}


def _ref_starts(text, i):
    # Reads as an opener: an opener prefix, then a letter or a digit; or,
    # after the start or whitespace, then a mark.
    if not (i + 1 < len(text) and _ref_wide(text, i)):
        return False
    after = text[i + 1]
    if _ref_word_char(after):
        return True
    return after in REF_MARKS and (i == 0 or text[i - 1].isspace())


def _ref_glued(text, i):
    j = i - 1
    while j >= 0 and i - j <= 4 and unicodedata.category(text[j]).startswith("M"):
        j -= 1
    return j >= 0 and text[j].isalnum()


def _ref_opens_delimited(text, i):
    if text[i] not in REF_PAIRS:
        return False
    if text[i] not in REF_ALSO_CLOSES or _ref_starts(text, i):
        return True
    if _ref_glued(text, i):
        return False
    return text[i] not in REF_CONTEXT or (i + 1 < len(text) and not text[i + 1].isspace())


def _ref_close(text, i, reading):
    mark = text[i]
    if reading == "nested":
        stack = [mark]
        for j in range(i + 1, len(text)):
            opens = _ref_opens_delimited(text, j)
            if text[j] in REF_PAIRS[stack[-1]] and not (opens and _ref_starts(text, j)):
                stack.pop()
                if not stack:
                    return j
            elif opens:
                stack.append(text[j])
        return len(text)
    for j in range(i + 1, len(text)):
        if text[j] in REF_PAIRS[mark] and (reading != "strict" or not _ref_starts(text, j)):
            return j
    return len(text)


def _ref_delimited(text, reading="standard"):
    spans, regions, i = [], [], 0
    while i < len(text):
        if reading == "strict":
            opens = text[i] in REF_PAIRS and i + 1 < len(text) and not _ref_glued(text, i)
        else:
            opens = _ref_opens_delimited(text, i)
        if not opens:
            i += 1
            continue
        end = _ref_close(text, i, reading)
        spans.append((i, text[i + 1:end]))
        regions.append((i, min(end + 1, len(text))))
        i = end + 1
    return spans, regions


def _ref_opener(text, i):
    if text[i] not in REF_SINGLE_OPENERS or i + 1 >= len(text):
        return False
    j = i - 1
    while j >= 0 and i - j <= 4 and unicodedata.category(text[j]).startswith("M"):
        j -= 1
    return j < 0 or not text[j].isalnum()


def _ref_closer(text, i):
    return text[i] in REF_MARKS and _ref_closer_context(text, i)


def _ref_single(text, regions):
    # The first opener outside the regions, and the last closer after it.
    outside = [i for i in range(len(text)) if not any(start <= i < end for start, end in regions)]
    opens = [i for i in outside if _ref_opener(text, i)]
    if not opens:
        return None
    closes = [i for i in outside if i > opens[0] and _ref_closer(text, i)]
    return (opens[0], closes[-1]) if closes else None


def _ref_whole_text(text, regions):
    # The first opener anywhere, and the last closer after it that is a
    # single mark, or another mark outside the standard reading's regions.
    opens = [i for i in range(len(text)) if _ref_opener(text, i)]
    if not opens:
        return None
    closes = [
        i for i in range(opens[0] + 1, len(text))
        if _ref_closer(text, i) and (text[i] in REF_SINGLE_OPENERS + "\u275c" or not any(rs <= i < re for rs, re in regions))
    ]
    return (opens[0], closes[-1]) if closes else None


def _ref_span_text(text, regions, start, close):
    # Each enclosed pass-1 region becomes one space, including its marks, so
    # no word is counted a second time.
    pieces, cursor = [], start + 1
    for region_start, region_end in regions:
        if start < region_start < close:
            pieces.extend((text[cursor:region_start], " "))
            cursor = region_end
    pieces.append(text[cursor:close])
    return "".join(pieces)


def _ref_main_opener(text, i):
    return (text[i] in REF_SINGLE_OPENERS and i + 1 < len(text) and text[i + 1].isalpha()
            and (i == 0 or text[i - 1] in " \t\n\r([{\u2014\u2013-/"))


def _ref_one_pass(text, opener=None):
    opener = _ref_opener if opener is None else opener
    every = [i for i in range(len(text)) if _ref_closer(text, i)]
    words, i = 0, 0
    while i < len(text):
        if _ref_opens_delimited(text, i):
            end = _ref_close(text, i, "standard")
            words += _ref_word_count(text[i + 1:end])
            i = end + 1
            continue
        if opener(text, i):
            after = [c for c in every if c > i]
            if after:
                words += _ref_word_count(text[i + 1:after[0]])
                i = after[0] + 1
                continue
        i += 1
    return words


def _reference_spans(text):
    spans, regions = _ref_delimited(text)
    single = _ref_single(text, regions)
    if single is not None:
        spans.append((single[0], _ref_span_text(text, regions, *single)))
    return [span for _, span in sorted(spans)]


def _reference_words(text):
    # quoted_words's envelope, independently: under each delimited reading
    # (standard, strict, nested), delimited words once plus the single span
    # from the first opener to the last closer; that span over the whole
    # text, with the standard quotations outside it; the one-pass reading;
    # and main's count.
    best = 0
    for reading in ("standard", "strict", "nested"):
        spans, regions = _ref_delimited(text, reading)
        words = sum(_ref_word_count(span) for _, span in spans)
        single = _ref_single(text, regions)
        if single is not None:
            words += _ref_word_count(_ref_span_text(text, regions, *single))
        best = max(best, words)
    spans, regions = _ref_delimited(text)
    raw = _ref_whole_text(text, regions)
    if raw is not None:
        # Each standard quotation on its own, and the span's text outside them.
        inside = {j for rs, re in regions for j in range(rs, re)}
        own = "".join(" " if j in inside else text[j] for j in range(raw[0] + 1, raw[1]))
        best = max(best, sum(_ref_word_count(span) for _, span in spans) + _ref_word_count(own))
    return max(best, _ref_one_pass(text), _ref_one_pass(text, _ref_main_opener), _main_quoted_words(text))


def _main_quoted_words(text):
    # main's scanner (its last commit before this change), verbatim apart
    # from nesting it here: doubles and singles in one pass, ASCII prefixes,
    # the first closer after a non-space, and words counted by whitespace.
    _DOUBLE_CLOSERS = {'"': '"', "\u201c": "\u201d"}
    _SINGLE_OPENERS = ("'", "\u2018")
    _SINGLE_CLOSERS = ("'", "\u2019")
    _BEFORE_OPENER = frozenset(" \t\n\r([{\u2014\u2013-/")

    def _opens_single(text: str, index: int) -> bool:
        before_ok = index == 0 or text[index - 1] in _BEFORE_OPENER
        return before_ok and index + 1 < len(text) and text[index + 1].isalpha()

    def _closes_single(text: str, index: int) -> bool:
        return (
            index > 0
            and not text[index - 1].isspace()
            and (index + 1 == len(text) or not text[index + 1].isalnum())
        )

    def quoted_spans(text: str) -> list[str]:
        spans: list[str] = []
        index = 0
        while index < len(text):
            mark = text[index]
            if mark in _DOUBLE_CLOSERS:
                close = text.find(_DOUBLE_CLOSERS[mark], index + 1)
                close = len(text) if close == -1 else close
                spans.append(text[index + 1 : close])
                index = close + 1
                continue
            if mark in _SINGLE_OPENERS and _opens_single(text, index):
                close = next(
                    (
                        position
                        for position in range(index + 1, len(text))
                        if text[position] in _SINGLE_CLOSERS and _closes_single(text, position)
                    ),
                    None,
                )
                if close is not None:
                    spans.append(text[index + 1 : close])
                    index = close + 1
                    continue
            index += 1
        return spans

    return sum(len(span.split()) for span in quoted_spans(text))


@settings(max_examples=2000, deadline=None)
@given(text=quote_texts)
def test_quoted_spans_agree_with_a_reference(text):
    spans = sc.quoted_spans(text)
    assert spans == _reference_spans(text)
    assert sum(len(span) for span in spans) <= len(text)
    # The count takes the largest of several readings; the standard is one.
    assert sc.quoted_words(text) >= sum(_ref_word_count(span) for span in spans)


@settings(max_examples=2000, deadline=None)
@example(text="It wrote 'the workers' '90s policy is to deny every claim'")
@example(text="It wrote \u201cone two \u201cthree\u201d four five\u201d")
@example(text="It wrote 'em \u201cx'\u201d all at once'")
@example(text='He is 6" tall and wrote "one two three four five"')
@example(text="'a\"b\u00ab\"\u00bb")
@given(text=quote_texts)
def test_quoted_words_agree_with_a_reference(text):
    count, spans = sc.quoted_reading(text)
    assert count == _reference_words(text)
    # The spans shown in a refusal are those of a reading that gives the count.
    assert count in (sum(_ref_word_count(span) for span in spans), sum(len(span.split()) for span in spans))


@settings(max_examples=2000, deadline=None)
@example(text='It wrote "one two three four \u2026"')
@example(text="'one' and 'two \u2019 three'")
@given(text=quote_texts)
def test_the_main_floor_is_mains_count(text):
    # #1867 review round 2 (P1): the floor is main's count exactly, its
    # whitespace word count included, not a copy with this change's rules.
    assert sc._main_words(text) == _main_quoted_words(text)


@settings(max_examples=2000, deadline=None)
@example(text="It wrote:\u00a0'about \"the workers' policy is to deny every such claim\"'")
@example(text="'one' and\u00a0'two three four'")
@example(text="It wrote 'one two three 'inner' four'")
@example(text='It wrote "one two three four \u2026"')
@given(text=quote_texts)
def test_quoted_words_never_count_below_main(text):
    # #1867 review (P1): this change must not accept a description main's
    # scanner refused, so it never counts fewer quoted words than main did.
    assert sc.quoted_words(text) >= _main_quoted_words(text), text


@settings(max_examples=2000, deadline=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@example(text="'one' and\u00a0'two three four'")
@example(text="\u2019a[\"'\"\u00b9")
@example(text="\u00aba b \u20191\u00bb \u00ab 'c\u00bb d'")
@example(text="\u00aba \u20191\u00bb\u00abb\u00bb \u00ab 'c\u00bb d'")
@given(text=quote_texts)
def test_quoted_words_monotonic_when_openers_widen(monkeypatch, text):
    # Narrowing single openers to main's rule (an ASCII prefix before a
    # letter) never raises the count, so widening them never lowers it.
    expanded = sc.quoted_words(text)

    def main_opens(value, index):
        return (index + 1 < len(value) and value[index + 1].isalpha()
                and (index == 0 or value[index - 1] in " \t\n\r([{\u2014\u2013-/"))

    with monkeypatch.context() as patch:
        patch.setattr(sc, "_opens_single", main_opens)
        narrowed = sc.quoted_words(text)
    assert expanded >= narrowed, (text, expanded, narrowed)


# Plain prose: words, contractions, possessives (singular and plural), inch
# marks and footnote marks, with no single mark that may open (none after
# anything but a letter or digit).
PROSE_WORDS = ["the", "agency", "workers", "policy", "claims", "yes", "no", "case", "rules", "Benefits"]
PROSE_TOKENS = PROSE_WORDS + [
    "won't", "agency's", "it\u2019s", "don\u2019t", "6'7", "the workers'", "claimants\u2019", "6\u201d", "6\u2033", "note\u00b9", "goin'",
    "o'clock", "1990s",
]
# A double quotation's words: plain, or ending in punctuation, a dash, a
# possessive or a dropped letter, or holding an apostrophe; none opens a
# single quotation.
QUOTED_WORDS = PROSE_WORDS + ["wait\u2014", "workers'", "claimants\u2019", "goin'", "it's", "6'7", "no.", "yes,", "(see)", "x\u2014y", "end?"]
# Apostrophe contexts that a single quotation may contain: possessives,
# elisions, elided years, dropped letters, contractions, and nested double and
# single quotations.
INSIDE_TOKENS = PROSE_WORDS + [
    "workers'", "claimants\u2019", "'cause", "'em", "'90s", "\u201990s", "goin'", "won't", "agency's", "'n'",
    "\u201cone two\u201d", '"one"', "\u00abone two\u00bb", "\u201eone\u201c", "'one'", "\u2018one\u2019",
]


@settings(max_examples=2000, deadline=None)
@example(tokens=["the", "workers'", "case", "won't", "1990s"])
@given(tokens=st.lists(st.sampled_from(PROSE_TOKENS), max_size=20))
def test_plain_prose_quotes_nothing(tokens):
    # #1867 review round 2 (P1): an apostrophe inside a word or at its end,
    # an inch mark or a footnote mark never opens a quotation.
    text = " ".join(tokens) + "."
    assert sc.quoted_words(text) == 0, text


@st.composite
def single_quotation_in_text(draw):
    """A quotation in single marks at word boundaries, holding any of
    INSIDE_TOKENS, with anything around it; and how many words it holds."""

    before = draw(st.lists(st.sampled_from(QUOTE_TOKENS + PROSE_TOKENS), max_size=10))
    inside = draw(st.lists(st.sampled_from(INSIDE_TOKENS), min_size=1, max_size=8))
    after = draw(st.lists(st.sampled_from(QUOTE_TOKENS + PROSE_TOKENS), max_size=10))
    opener = draw(st.sampled_from(sorted(REF_SINGLE_OPENERS)))
    closer = draw(st.sampled_from(["'", "\u2019", "\uff07", "\u2032", "\u275c", "\u2018"]))
    # The mark right before the opener (anything but a letter or digit) and
    # the start of its body vary too (#1867 round 5).
    prefix = draw(st.sampled_from([" ", " ", ":", "(", "\u2014", "/", "\u00a0", "\u201a", "\u201ax ", " \u201ax "]))
    lead = draw(st.sampled_from(["", " ", "\u2014", "\u2026", "("]))
    body = lead + " ".join(inside)
    words = _ref_word_count(body)
    return "".join(before) + prefix + opener + body + closer + " " + "".join(after), words


@settings(max_examples=3000, deadline=None)
@example(case=("It wrote 'the workers' claims denied 'cause ineligible'", 6))
@example(case=("It wrote 'we are goin' to deny every claim'", 7))
@example(case=("It wrote 'the workers' '90s policy is to deny every claim'", 9))
@example(case=("It wrote 'one \u201ctwo three\u201d four'", 4))
@example(case=("\u201a\u201d 'claimants\u2019 the' ", 2))
@example(case=("\u201ax \u2019 one two three four five\u2019", 5))
@example(case=("\u201ax \u2019\u2014one two three four five\u2019", 5))
@example(case=("\u201ax :\u2019one two three four five\u2019", 5))
@example(case=("\u201ax:'one workers\u2019 two three four five'", 6))
@given(case=single_quotation_in_text())
def test_a_single_quotation_counts_at_least_its_words(case):
    # The invariant (#1867 round 4): for any text where a quotation of N words
    # is delimited by single marks at word boundaries, whatever apostrophes it
    # holds and whatever surrounds it, the count is at least N.
    text, words = case
    assert sc.quoted_words(text) >= words, text


@st.composite
def double_quotations_in_prose(draw):
    """Plain prose with closed double quotations in it, none nested, and how
    many words they hold. A quotation's words may end in punctuation, a
    dash, a possessive or a dropped letter, it may have a space inside either
    mark (except after a mark that also closes), and punctuation may follow
    its closer (#1867 round 4)."""

    pieces, quoted = [], 0
    for _ in range(draw(st.integers(0, 8))):
        if draw(st.booleans()):
            # Every pair but \u201a\u2026\u2018 and \u201a\u2026\u2019, whose closers are single marks.
            opener = draw(st.sampled_from(sorted(set(REF_PAIRS) - {"\u201a"})))
            # Its words hold none of its own closing marks (‚claimants’ …’
            # can't be told apart), and no single mark starts a word.
            own = [word for word in QUOTED_WORDS if not any(mark in word for mark in REF_PAIRS[opener])]
            words = draw(st.lists(st.sampled_from(own), min_size=1, max_size=5))
            # A space after an opening mark that also closes (\u201d \u00bb \u203a \u2033) reads
            # it as a closer, as in French \u00ab \u2026 \u00bb spacing, so those open with none.
            inside = draw(st.sampled_from([""] if opener in REF_CONTEXT else ["", " ", "\u00a0"])), draw(st.sampled_from(["", " "]))
            after = draw(st.sampled_from(["", ".", ",", ";", ":", "!", "?", ")", "\u2014", "[1]", "(2026)", "[1]."]))
            before = draw(st.sampled_from(["", "(", ":", "\u2014", "/"]))
            pieces.append(before + opener + inside[0] + " ".join(words) + inside[1] + draw(st.sampled_from(REF_PAIRS[opener])) + after)
            quoted += len(words)
        else:
            pieces.append(draw(st.sampled_from(PROSE_TOKENS)))
    return " ".join(pieces) + " today.", quoted


@settings(max_examples=3000, deadline=None)
@example(case=('"a\u2014". b', 1))
@example(case=('He said "wait\u2014". Then he went away.', 1))
@example(case=('He said "workers\'", then denied every claim.', 1))
@example(case=('It wrote " one" today.', 1))
@example(case=('It wrote "one two three four " today.', 4))
@example(case=('It wrote "one two three four\u2014"[1] today.', 4))
@example(case=('It wrote "one two three workers\'"[1] today.', 4))
@example(case=('It wrote "one two three four "[1] today.', 4))
@given(case=double_quotations_in_prose())
def test_double_quotations_are_counted_exactly(case):
    # The invariant (#1867 round 4): double quotations in plain prose are
    # counted exactly in each of the three delimited readings, and overall.
    text, quoted = case
    for reading in sc._DELIMITED_READINGS:
        spans, _ = sc._delimited(text, reading)
        assert sum(sc._words(span) for _, span in spans) == quoted, (reading, text)
    # Overall too, unless main's floor counts more: main read \u201c as an
    # opener, so after a German \u201e\u2026\u201c it quoted the rest.
    assert sc.quoted_words(text) == max(quoted, _main_quoted_words(text)), text


def _pair_marks(opener):
    return set(opener) | set(REF_PAIRS[opener])


NESTING_PREFIXES = ["", "", ":", "\u2014", "(", "/"]


@st.composite
def nested_quotation(draw, shared):
    """One double quotation holding another (or, for disjoint pairs, two
    levels), whose inner quotations start with a plain word; and its words.
    `shared`: the inner pair is the outer one or shares a mark with it;
    otherwise their marks are disjoint."""

    openers = sorted(set(REF_PAIRS) - {"\u201a"})
    outer = draw(st.sampled_from(openers))
    if shared:
        inners = [o for o in openers if _pair_marks(o) & _pair_marks(outer)]
    else:
        inners = [o for o in openers if not _pair_marks(o) & _pair_marks(outer)]
    inner = draw(st.sampled_from(inners))
    marks = _pair_marks(outer) | _pair_marks(inner)
    own = [w for w in QUOTED_WORDS if not any(m in w for m in marks)]
    head = draw(st.lists(st.sampled_from(own), min_size=1, max_size=3))
    middle = [draw(st.sampled_from(PROSE_WORDS))] + draw(st.lists(st.sampled_from(own), max_size=2))
    words = len(head) + len(middle)
    if not shared and draw(st.booleans()):
        # A third level, in a pair disjoint from both.
        third = [o for o in openers if not _pair_marks(o) & marks]
        if third:
            deepest = draw(st.sampled_from(third))
            deep_words = [draw(st.sampled_from(PROSE_WORDS))] + draw(st.lists(st.sampled_from(PROSE_WORDS), max_size=1))
            middle = middle + [deepest + " ".join(deep_words) + draw(st.sampled_from(REF_PAIRS[deepest]))]
            words += len(deep_words)
    tail = draw(st.lists(st.sampled_from(own), max_size=2))
    words += len(tail)
    inner_close = draw(st.sampled_from(REF_PAIRS[inner])) + draw(st.sampled_from(["", ",", "[1]"]))
    body = " ".join(head) + " " + inner + " ".join(middle) + inner_close + (" " + " ".join(tail) if tail else "")
    after = draw(st.sampled_from(["", ".", ",", "[1]", "(2026)"]))
    prefix = draw(st.sampled_from(NESTING_PREFIXES))
    return prefix + outer + body + draw(st.sampled_from(REF_PAIRS[outer])) + after, words


@st.composite
def nested_double_quotations_in_prose(draw, shared=False):
    """Plain prose with nested double quotations in it (nested_quotation),
    citations after closers; and how many words they hold in all. Neither
    documented limit's shape is drawn."""

    pieces, quoted = [], 0
    for _ in range(draw(st.integers(1, 4))):
        if draw(st.booleans()):
            piece, words = draw(nested_quotation(shared))
            pieces.append(piece)
            quoted += words
        else:
            pieces.append(draw(st.sampled_from(PROSE_TOKENS)))
    return " ".join(pieces) + " today.", quoted


@settings(max_examples=3000, deadline=None)
@example(case=("It wrote \u201cone \u00abtwo\u00bb three\u201d today.", 3))
@example(case=('It wrote "one \u201ctwo\u201d three" today.', 3))
@example(case=("It wrote:\u201cone \u00abtwo \u300cthree\u300d\u00bb four\u201d today.", 4))
@given(case=nested_double_quotations_in_prose())
def test_nesting_in_a_disjoint_pair_counts_exactly(case):
    # The eng hub's rulings 2 and 3: outside the ambiguous-opener predicate,
    # a quotation nested in a pair that shares no mark with the outer one is
    # counted exactly in each of the three readings, and overall unless
    # main's floor counts more.
    text, quoted = case
    counts = {reading: sum(sc._words(span) for _, span in sc._delimited(text, reading)[0]) for reading in sc._DELIMITED_READINGS}
    assert set(counts.values()) == {quoted}, (counts, text)
    assert sc.quoted_words(text) == max(quoted, _main_quoted_words(text)), text


@settings(max_examples=3000, deadline=None)
@example(case=('It wrote "one "two" three" today.', 3))
@example(case=("It wrote \u201eone \u201ctwo\u201d three\u201c today.", 3))
@example(case=('It wrote "one "two"[1] three"[2] today.', 3))
@example(case=("\u00abthe \u00abthe\u00bb\u00bb. today.", 2))
@given(case=nested_double_quotations_in_prose(shared=True))
def test_nesting_in_a_shared_pair_counts_in_full(case):
    # Inside the ambiguous-opener predicate (ruling 3): nesting in the same
    # marks, or in a pair that shares a mark with the outer one, with the
    # inner quotation starting with a letter or digit, counts at least in full
    # (the second known limit covers the rest). It may count more, failing
    # closed; the README's Quotation examples pin a case.
    text, quoted = case
    assert sum(sc._words(span) for _, span in sc._delimited(text, "nested")[0]) >= quoted, text
    assert sc.quoted_words(text) >= quoted, text


@st.composite
def text_around_a_quotation(draw):
    """Any marks and words around one recognisable quotation of plain words
    (a delimited one, or one nested in the same marks), and how many words it
    holds."""

    before = draw(st.lists(st.sampled_from(QUOTE_TOKENS + PROSE_TOKENS), max_size=12))
    after = draw(st.lists(st.sampled_from(QUOTE_TOKENS + PROSE_TOKENS), max_size=12))
    words = draw(st.lists(st.sampled_from(PROSE_WORDS), min_size=1, max_size=8))
    opener = draw(st.sampled_from(sorted(REF_PAIRS)))
    closer = draw(st.sampled_from(REF_PAIRS[opener]))
    nested_first = False
    if draw(st.booleans()):
        cut = draw(st.integers(0, len(words) - 1))
        words_text = " ".join(words[:cut] + [opener + words[cut] + closer] + words[cut + 1:])
        nested_first = cut == 0
    else:
        words_text = " ".join(words)
    # The mark right before the opener: anything but a letter or digit
    # (#1867 round 6), with a space before it. A quotation whose first word
    # is itself a nested quotation starts with a quotation mark, which starts
    # a quotation only at the start or after whitespace; after punctuation,
    # inside a quotation a stray mark before it left open, it is the second
    # known limit (pinned in test_publication_regressions). So only that shape,
    # after a quotation mark, keeps to a whitespace prefix (#1867 round 7).
    stray = any(char in sc._QUOTATION_MARKS for token in before for char in token)
    prefix = draw(st.sampled_from(["", "\u00a0"] if nested_first and stray else ["", ":", "\u2014", "(", "/", "\u00a0"]))
    return "".join(before) + " " + prefix + opener + words_text + closer + " " + "".join(after), len(words)


@settings(max_examples=3000, deadline=None)
@given(case=text_around_a_quotation())
def test_every_recognisable_quotation_counts_in_full(case):
    # Whatever surrounds it, a delimited quotation the scanner recognises (an
    # opener after a space, a closer before one; nesting in the same marks
    # included) counts at least its own words.
    text, words = case
    assert sc.quoted_words(text) >= words, text
