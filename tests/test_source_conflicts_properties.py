"""Property-based and differential tests for tools/source_conflicts.py.

Invariants, for every input:

1. Acceptance: every generated well-formed entry (any status, with the
   ruling and confirmation its status requires, any mix of corpus and pending
   texts) passes `check`.
2. Status rules: a ruling present on an open entry, or missing from a ruled,
   confirmed or contradicted one, is always reported; so is a confirmation on
   an open or ruled entry or missing from a confirmed or contradicted one.
3. Totality: `check` returns a list of strings for any YAML-shaped input and
   never raises.
4. Round trip: a register entry turned into a module interpretation and
   written into a module passes the adopting-module check, and its
   interpretation core equals the entry's.
5. Drift: changing any one core field in the module's copy is reported, and
   the report names that field.
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

Hypothesis is not installed in the shared validate workflow's pytest leg, so
these skip there; the source-conflicts workflow installs it and runs them.
"""

from __future__ import annotations

import copy
import importlib.util
import string
import sys
from pathlib import Path

import pytest
import yaml

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, assume, given, settings, strategies as st  # noqa: E402

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "source_conflicts.py"
_spec = importlib.util.spec_from_file_location("source_conflicts", TOOL_PATH)
sc = importlib.util.module_from_spec(_spec)
sys.modules["source_conflicts"] = sc
_spec.loader.exec_module(sc)

REPO = "TheAxiomFoundation/rulespec-us"
SETTINGS = settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])

# Free text without digits, '@', '/' or '~', so it never trips hygiene by accident.
prose = st.text(alphabet=string.ascii_letters + " ,.;:'()-", min_size=1, max_size=40).filter(lambda s: s.strip())
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
    st.sampled_from(["statute", "regulation", "guidance", "manual"]),
    st.lists(st.from_regex(r"[a-z0-9][a-z0-9.-]{0,5}", fullmatch=True), min_size=1, max_size=4),
)
urls = st.builds(lambda host, path: f"https://{host}.org/{path}", st.from_regex(r"[a-z]{3,8}", fullmatch=True), kebab)
texts = st.lists(st.fixed_dictionaries({"corpus_citation_path": corpus_paths, "excerpt": prose}), max_size=3)
pending = st.lists(
    st.fixed_dictionaries(
        {
            "citation": prose,
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
alternatives = st.lists(
    st.one_of(
        st.fixed_dictionaries({"reading": prose}),
        st.fixed_dictionaries({"reading": prose, "effect": prose}),
    ),
    min_size=1,
    max_size=3,
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
    alts = draw(alternatives)
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
                "follows": draw(st.sampled_from(["reading", *[f"alternatives[{i}]" for i in range(len(alts))]])),
                "cites_entry": draw(st.booleans()),
            }
        ]
        value["tests"] = [
            {"repo": "PolicyEngine/microcosm-dynamics", "commit": commit, "path": "tests/test_x.py", "name": "test_default", "pins": ["reading"]}
        ] + [
            {"repo": "PolicyEngine/microcosm-dynamics", "commit": commit, "path": "tests/test_x.py", "name": f"test_alt_{i}", "pins": [f"alternatives[{i}]"]}
            for i in range(len(alts))
        ]
    if draw(st.booleans()):
        value["money_case"] = {
            "description": draw(prose),
            "amount": draw(st.from_regex(r"(0|[1-9][0-9]{0,4})(\.[0-9]{2})?", fullmatch=True)),
            "currency": "USD",
            "period": draw(st.sampled_from(sc.PERIODS)),
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
    issues = sc.check_register(payload, repo(tmp_path), scan_modules=False)
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
    drifted[field] = {"texts": [], "alternatives": [{"reading": "different"}]}.get(field, "different")
    if field == "status":
        drifted["status"] = "open" if value["status"] != "open" else "ruled"
    if field == "ruling":
        drifted["ruling"] = {**(value.get("ruling") or {}), "by": "Someone Else Organisation"}
    assume(drifted[field] != carried.get(field))
    write(drifted)
    issues = sc.check_register({"version": 1, "entries": [value]}, ctx)
    assert any(f"`{field}` differs" in issue for issue in issues)


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
