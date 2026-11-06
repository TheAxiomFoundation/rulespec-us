"""Tests for tools/source_conflicts.py and the committed source-conflict register.

These run in the Repository Checks pytest leg, offline. The committed
known-source-conflicts.yaml must pass `check` exactly (schema, status rules,
hygiene, in-repo references, and the scan that every module interpretation
citing two or more provisions is registered). The rest pin each rule on small
fixture repositories. Network verification (excerpts against the pinned corpus
release and snapshots, external refs) is the source-conflicts workflow;
property-based and differential tests live in test_source_conflicts_properties.py.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import io
import json
import math
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL_PATH = REPO_ROOT / "tools" / "source_conflicts.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("source_conflicts", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["source_conflicts"] = module
    spec.loader.exec_module(module)
    return module


sc = _load_tool()
REPO = "TheAxiomFoundation/rulespec-us"
COMMIT = "a" * 40
SHA = "b" * 64


# ---------------------------------------------------------------------------
# The committed register


def test_committed_register_passes_check() -> None:
    payload = sc.load_register(REPO_ROOT / sc.REGISTER_FILENAME)
    issues = sc.check_register(payload, sc.RepoContext(root=REPO_ROOT, repo=REPO))
    assert issues == []


def test_committed_register_cli_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert sc.main(["check", "--root", str(REPO_ROOT)]) == 0
    assert "0 issue(s), 0 unregistered open interpretation(s)" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Fixtures


def make_repo(tmp_path: Path) -> sc.RepoContext:
    (tmp_path / "us" / "statutes" / "42" / "403" / "a").mkdir(parents=True, exist_ok=True)
    (tmp_path / "us-co" / "regulations").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests").mkdir(exist_ok=True)
    return sc.RepoContext(root=tmp_path, repo=REPO)


def entry(**overrides):
    base = {
        "id": "family-maximum-saving-clause",
        "jurisdiction": "us",
        "program": "social-security",
        "question": "Does the saving clause protect every later month, or only months after a PIA increase?",
        "texts": [
            {
                "corpus_citation_path": "us/statute/42/403/a/5",
                "excerpt": "for any such subsequent month",
            }
        ],
        "pending_texts": [
            {
                "citation": "POMS RS 00630.400",
                "kind": "manual",
                "url": "https://secure.ssa.gov/poms.nsf/lnx/0300630400",
                "snapshot": {
                    "repo": "PolicyEngine/microcosm-dynamics",
                    "commit": COMMIT,
                    "path": "tests/data/poms_rs_00630_400.html",
                    "sha256": SHA,
                },
                "excerpt": "Total family payment is less after the PIA increase",
            }
        ],
        "reading": "Protect only when a PIA increase itself lowers the family total.",
        "alternatives": [{"id": "every-later-month", "reading": "Protect every later month.", "effect": "More months refused."}],
        "basis": "SSA's operational chart.",
        "status": "ruled",
        "ruling": {"by": "Axiom Foundation", "date": "2026-10-12", "record": "https://github.com/x/y/pull/1"},
        "outcome": "computed",
        "implementations": [
            {
                "repo": "PolicyEngine/microcosm-dynamics",
                "commit": COMMIT,
                "path": "src/gross_benefits.py",
                "follows": "every-later-month",
                "cites_entry": False,
            }
        ],
        "tests": [
            {
                "repo": "PolicyEngine/microcosm-dynamics",
                "commit": COMMIT,
                "path": "tests/test_g.py",
                "name": "test__given_operational__then_pays",
                "pins": ["reading"],
            },
            {
                "repo": "PolicyEngine/microcosm-dynamics",
                "commit": COMMIT,
                "path": "tests/test_g.py",
                "name": "TestLiteral::test_refuses",
                "pins": ["every-later-month"],
            },
        ],
        "money_case": {
            "description": "A survivor family after a child ages out.",
            "amount": "21.00",
            "currency": "USD",
            "period": "month",
            "computed_by": "test__given_operational__then_pays",
        },
    }
    base.update(overrides)
    return base


def check(ctx, *entries, scan=True):
    return sc.check_register({"version": 1, "entries": list(entries)}, ctx, scan_modules=scan)


def write_module(ctx, rel, interpretations, rules=("rule_a", "rule_b")):
    path = ctx.root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": "rulespec/v1",
        "module": {"summary": "x", "interpretations": interpretations},
        "rules": [{"name": name, "kind": "parameter"} for name in rules],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


# ---------------------------------------------------------------------------
# Top level


def test_valid_entry_has_no_issues(tmp_path):
    assert check(make_repo(tmp_path), entry()) == []


def test_top_level_shape(tmp_path):
    ctx = make_repo(tmp_path)
    assert sc.check_register([], ctx) != []
    issues = sc.check_register({"version": 2, "entries": [], "extra": 1}, ctx)
    assert any("version must be 1" in issue for issue in issues)
    assert any("unknown top-level key `extra`" in issue for issue in issues)
    assert any("entries must be a list" in issue for issue in sc.check_register({"version": 1}, ctx))


def test_duplicate_ids(tmp_path):
    issues = check(make_repo(tmp_path), entry(), entry())
    assert any("`us:family-maximum-saving-clause` duplicates entries[0]" in issue for issue in issues)


def test_the_same_id_in_two_jurisdictions_is_two_entries(tmp_path):
    # Global ids (<jurisdiction>:<id>) are the identity; aggregate checks them across repositories.
    assert check(make_repo(tmp_path), entry(), entry(jurisdiction="us-co")) == []


@pytest.mark.parametrize("jurisdiction", [[], {}, ["us"], 7, None])
def test_malformed_jurisdiction_is_an_issue_not_an_exception(tmp_path, jurisdiction):
    issues = check(make_repo(tmp_path), entry(jurisdiction=jurisdiction))
    assert any(".jurisdiction must be a jurisdiction directory" in issue for issue in issues)


@pytest.mark.parametrize("repo", [[], {"a": 1}, ["PolicyEngine/x"]])
def test_malformed_test_repo_is_an_issue_not_an_exception(tmp_path, repo):
    bad = entry()
    bad["tests"][0]["repo"] = repo
    bad["tests"].append(dict(bad["tests"][0]))
    issues = check(make_repo(tmp_path), bad)
    assert any("repo must be owner/name" in issue for issue in issues)


@pytest.mark.parametrize("bad", ["Has-Caps", "trailing-", "two--dashes", "under_score", ""])
def test_id_pattern(tmp_path, bad):
    issues = check(make_repo(tmp_path), entry(id=bad))
    assert any(".id must match" in issue or ".id" in issue for issue in issues)


def test_jurisdiction_must_be_a_directory_here(tmp_path):
    ctx = make_repo(tmp_path)
    assert check(ctx, entry(jurisdiction="us-co")) == []
    assert any("jurisdiction must be" in issue for issue in check(ctx, entry(jurisdiction="uk")))


def test_unknown_keys_rejected_at_every_level(tmp_path):
    ctx = make_repo(tmp_path)
    bad = entry(extra=1)
    bad["texts"][0]["note"] = "x"
    bad["alternatives"][0]["why"] = "x"
    bad["ruling"]["officer"] = "x"
    bad["pending_texts"][0]["snapshot"]["branch"] = "main"
    bad["money_case"]["fx"] = 1
    issues = check(ctx, bad)
    for key in ("extra", "note", "why", "officer", "branch", "fx"):
        assert any(f"unknown key `{key}`" in issue for issue in issues), key


def test_required_fields(tmp_path):
    ctx = make_repo(tmp_path)
    for key in sc.REQUIRED_ENTRY_KEYS:
        bad = entry()
        del bad[key]
        assert check(ctx, bad), key


# ---------------------------------------------------------------------------
# Interpretation core: the module.interpretations v1 rules


def test_status_open_forbids_ruling(tmp_path):
    ctx = make_repo(tmp_path)
    issues = check(ctx, entry(status="open"))
    assert any("ruling must be absent when status is `open`" in issue for issue in issues)
    opened = entry(status="open")
    del opened["ruling"]
    assert check(ctx, opened) == []


def test_status_ruled_requires_ruling_and_forbids_confirmation(tmp_path):
    ctx = make_repo(tmp_path)
    bad = entry()
    del bad["ruling"]
    assert any("ruling must be a mapping when status is `ruled`" in issue for issue in check(ctx, bad))
    confirmation = {"by": "Social Security Administration", "date": "2026-10-20", "excerpt": "Yes."}
    assert any("confirmation must be absent" in issue for issue in check(ctx, entry(confirmation=confirmation)))


def test_status_confirmed_and_contradicted(tmp_path):
    ctx = make_repo(tmp_path)
    confirmation = {"by": "Social Security Administration", "date": "2026-10-20", "excerpt": "Yes."}
    assert check(ctx, entry(status="confirmed", confirmation=confirmation)) == []
    missing = entry(status="confirmed")
    assert any("confirmation must be a mapping" in issue for issue in check(ctx, missing))
    contradicted = check(ctx, entry(status="contradicted", confirmation=confirmation))
    assert any("contradicted this reading" in issue for issue in contradicted)
    no_excerpt = entry(status="confirmed", confirmation={"by": "SSA", "date": "2026-10-20"})
    assert any("confirmation.excerpt" in issue for issue in check(ctx, no_excerpt))
    bad_record = entry(status="confirmed", confirmation={**confirmation, "record": "http://x"})
    assert any("confirmation.record must be an https URL" in issue for issue in check(ctx, bad_record))


@pytest.mark.parametrize("status", ["Ruled", "pending", "", None, 1])
def test_status_enum(tmp_path, status):
    assert any("status must be" in issue for issue in check(make_repo(tmp_path), entry(status=status)))


@pytest.mark.parametrize("date", ["2026-02-30", "2026-1-01", "12/10/2026", "", 20261012])
def test_ruling_date_must_be_real(tmp_path, date):
    bad = entry()
    bad["ruling"]["date"] = date
    assert any("ruling.date must be a real" in issue for issue in check(make_repo(tmp_path), bad))


def test_unquoted_yaml_date_is_accepted(tmp_path):
    payload = yaml.safe_load(yaml.safe_dump({"version": 1, "entries": [entry()]}).replace("'2026-10-12'", "2026-10-12"))
    assert sc.check_register(payload, make_repo(tmp_path)) == []


@pytest.mark.parametrize("record", ["http://github.com/x", "github.com/x", "https://", "https://exa mple.com", None])
def test_ruling_record_must_be_https(tmp_path, record):
    bad = entry()
    bad["ruling"]["record"] = record
    assert any("ruling.record must be an https URL" in issue for issue in check(make_repo(tmp_path), bad))


def test_alternatives_non_empty(tmp_path):
    assert any("alternatives must be a non-empty list" in issue for issue in check(make_repo(tmp_path), entry(alternatives=[])))


def test_blank_strings_rejected(tmp_path):
    ctx = make_repo(tmp_path)
    for field in ("question", "reading", "basis"):
        assert any(f".{field} must be a non-blank string" in issue for issue in check(ctx, entry(**{field: "  "}))), field


@pytest.mark.parametrize("path", ["US/statute/42/403", "us/statute", "/us/statute/42", "us/statute/42/", "us//statute/42"])
def test_corpus_citation_path_canonical(tmp_path, path):
    bad = entry()
    bad["texts"][0]["corpus_citation_path"] = path
    assert any("canonical corpus citation path" in issue for issue in check(make_repo(tmp_path), bad))


def test_needs_a_provision(tmp_path):
    bad = entry(texts=[])
    del bad["pending_texts"]
    assert any("at least one provision" in issue for issue in check(make_repo(tmp_path), bad))
    only_pending = entry(texts=[])
    assert check(make_repo(tmp_path), only_pending) == []


def test_pending_text_snapshot_shape(tmp_path):
    ctx = make_repo(tmp_path)
    bad = entry()
    bad["pending_texts"][0]["snapshot"] = {"repo": "nope", "commit": "abc", "path": "../x", "sha256": "z"}
    bad["pending_texts"][0]["url"] = "ftp://x"
    issues = check(ctx, bad)
    for fragment in ("repo must be owner/name", "full lowercase commit", "relative path", "sha256 digest", "url must be an https URL"):
        assert any(fragment in issue for issue in issues), fragment


# ---------------------------------------------------------------------------
# Register-only fields


def test_outcome_enum(tmp_path):
    assert any("outcome must be computed or refused" in issue for issue in check(make_repo(tmp_path), entry(outcome="default")))


def test_reading_references(tmp_path):
    ctx = make_repo(tmp_path)
    bad = entry()
    bad["tests"][1]["pins"] = ["no-such-alternative"]
    bad["implementations"][0]["follows"] = "literal"
    issues = check(ctx, bad)
    assert any("pins[0] names `no-such-alternative`, which is neither `reading` nor the id" in issue for issue in issues)
    assert any("follows names `literal`, which is neither" in issue for issue in issues)
    blank = entry()
    blank["implementations"][0]["follows"] = ""
    assert any("follows must be `reading` or the id of one of this entry's alternatives" in issue for issue in check(ctx, blank))


@pytest.mark.parametrize("ref", ["alternatives[0]", "alternatives[1]", "0"])
def test_positional_references_are_rejected(tmp_path, ref):
    # References name alternatives by id: a position would silently move to
    # another alternative when one is inserted or reordered.
    bad = entry()
    bad["implementations"][0]["follows"] = ref
    bad["tests"][1]["pins"] = [ref]
    issues = check(make_repo(tmp_path), bad)
    assert any(f"follows names `{ref}`" in issue for issue in issues)
    assert any(f"pins[0] names `{ref}`" in issue for issue in issues)


def test_reordering_alternatives_keeps_every_reference(tmp_path):
    ctx = make_repo(tmp_path)
    value = entry()
    value["alternatives"].insert(0, {"id": "inserted-first", "reading": "Another reading."})
    assert check(ctx, value) == []
    value["alternatives"].reverse()
    assert check(ctx, value) == []
    assert value["implementations"][0]["follows"] == "every-later-month"


@pytest.mark.parametrize(
    ("alternatives", "fragment"),
    [
        ([{"reading": "No id."}], "alternatives[0].id is required"),
        ([{"id": "Not_Kebab", "reading": "x"}], "alternatives[0].id must match"),
        ([{"id": "reading", "reading": "x"}], "must not be `reading`"),
        ([{"id": "same", "reading": "x"}, {"id": "same", "reading": "y"}], "alternatives[1].id `same` repeats"),
        ([{"id": 3, "reading": "x"}], "alternatives[0].id must match"),
    ],
)
def test_alternative_ids(tmp_path, alternatives, fragment):
    bad = entry(alternatives=alternatives, implementations=[], tests=[])
    del bad["implementations"], bad["tests"]
    assert any(fragment in issue for issue in check(make_repo(tmp_path), bad)), fragment


def test_consumer_adopts_its_own_reading(tmp_path):
    ctx = make_repo(tmp_path)
    value = entry()
    implementation = value["implementations"][0]
    implementation["adopts"] = "every-later-month"
    implementation["basis"] = "This consumer follows the statute when it conflicts with an agency manual."
    implementation["ruling"] = {"by": "PolicyEngine", "date": "2026-10-19", "record": "https://github.com/x/y/pull/2"}
    assert check(ctx, value) == []
    unknown = copy.deepcopy(value)
    unknown["implementations"][0]["adopts"] = "statute"
    assert any("adopts names `statute`, which is neither" in issue for issue in check(ctx, unknown))
    no_basis = copy.deepcopy(value)
    del no_basis["implementations"][0]["basis"]
    assert any("basis is required with adopts or ruling" in issue for issue in check(ctx, no_basis))
    bad_ruling = copy.deepcopy(value)
    bad_ruling["implementations"][0]["ruling"]["record"] = "http://example.com"
    assert any("implementations[0].ruling.record must be an https URL" in issue for issue in check(ctx, bad_ruling))
    blank_basis = copy.deepcopy(value)
    blank_basis["implementations"][0]["basis"] = " "
    assert any("implementations[0].basis must be a non-blank string" in issue for issue in check(ctx, blank_basis))


@pytest.mark.parametrize("principle", sc.PRINCIPLES)
def test_a_consumer_ruling_may_name_its_principle(tmp_path, principle):
    ctx = make_repo(tmp_path)
    value = entry()
    implementation = value["implementations"][0]
    implementation["adopts"] = "every-later-month"
    implementation["basis"] = "This consumer follows the statute when it conflicts with an agency manual."
    implementation["ruling"] = {
        "by": "PolicyEngine", "date": "2026-10-20", "record": "https://github.com/x/y/pull/2", "principle": principle,
    }
    assert check(ctx, value) == []
    rows, _ = sc.aggregate({REPO: {"version": 1, "entries": [value]}})
    assert rows[0]["implementations"][0]["principle"] == principle


@pytest.mark.parametrize("principle", ["statute", "Statute-First", "", None, 7, ["statute-first"], {"a": 1}])
def test_an_unknown_principle_fails(tmp_path, principle):
    ctx = make_repo(tmp_path)
    value = entry()
    implementation = value["implementations"][0]
    implementation["basis"] = "Why."
    implementation["ruling"] = {"by": "PolicyEngine", "date": "2026-10-20", "record": "https://github.com/x/y/pull/2", "principle": principle}
    assert any("implementations[0].ruling.principle must be one of statute-first, regulations-are-law" in issue
               for issue in check(ctx, value))


def test_principle_is_register_only(tmp_path):
    # The entry's own ruling is part of the interpretation core a module
    # carries unchanged, so it takes no principle; only a consumer's does.
    value = entry(status="ruled", ruling={"by": "Axiom Foundation", "date": "2026-10-12",
                                          "record": "https://github.com/x/y/pull/1", "principle": "statute-first"})
    assert any("unknown key `principle`" in issue for issue in check(make_repo(tmp_path), value))
    rows, _ = sc.aggregate({REPO: {"version": 1, "entries": [entry()]}})
    assert rows[0]["implementations"][0]["principle"] is None


def test_every_followed_reading_is_pinned(tmp_path):
    ctx = make_repo(tmp_path)
    bad = entry()
    bad["tests"] = [bad["tests"][0]]  # pins reading only; the implementation follows every-later-month
    assert any("follows every-later-month, which no test pins" in issue for issue in check(ctx, bad))
    both = entry()
    both["tests"] = [{**both["tests"][0], "pins": ["reading", "every-later-month"]}]
    assert check(ctx, both) == []
    no_adopter = entry(tests=[entry()["tests"][1]])
    no_adopter["money_case"]["computed_by"] = "TestLiteral::test_refuses"
    del no_adopter["implementations"]
    assert check(ctx, no_adopter) == []


def test_pins_shape(tmp_path):
    ctx = make_repo(tmp_path)
    for pins, fragment in (("reading", "non-empty list"), ([], "non-empty list"), (["reading", "reading"], "repeats a reading")):
        bad = entry()
        bad["tests"][0]["pins"] = pins
        assert any(fragment in issue for issue in check(ctx, bad)), pins


def test_module_adopter_requires_a_test_pinning_the_reading(tmp_path):
    ctx = make_repo(tmp_path)
    value = adopted_entry()
    del value["implementations"]
    value["tests"] = [value["tests"][1]]
    write_module(ctx, "us/statutes/42/403/a/5.yaml", [sc.to_module_interpretation(value, interpretation_id=value["id"], affects=["rule_a"])])
    assert any("adopted by a module, so at least one test must pin `reading`" in issue for issue in check(ctx, value))


def test_external_refs_need_commits_and_not_this_repo(tmp_path):
    ctx = make_repo(tmp_path)
    bad = entry()
    bad["tests"][0]["commit"] = "main"
    bad["implementations"][0]["repo"] = REPO
    issues = check(ctx, bad)
    assert any("tests[0].commit must be a full lowercase commit SHA" in issue for issue in issues)
    assert any("names this repository" in issue for issue in issues)
    missing_repo = entry()
    del missing_repo["implementations"][0]["repo"]
    assert any("goes in adopted_by" in issue for issue in check(ctx, missing_repo))


def test_cites_entry_must_be_boolean(tmp_path):
    bad = entry()
    bad["implementations"][0]["cites_entry"] = "no"
    assert any("cites_entry must be true or false" in issue for issue in check(make_repo(tmp_path), bad))


def test_in_repo_tests_must_exist(tmp_path):
    ctx = make_repo(tmp_path)
    (ctx.root / "us" / "statutes" / "42" / "403" / "a" / "5.test.yaml").write_text(
        yaml.safe_dump([{"name": "saving_clause_case", "period": "2026-01", "input": {}, "output": {}}])
    )
    (ctx.root / "tests" / "test_local.py").write_text("class TestX:\n    def test_y(self):\n        pass\n")
    good = entry()
    good.pop("money_case")  # its tests are replaced below
    good["tests"] = [
        {"path": "us/statutes/42/403/a/5.test.yaml", "name": "saving_clause_case", "pins": ["reading"]},
        {"path": "tests/test_local.py", "name": "TestX::test_y", "pins": ["every-later-month"]},
    ]
    assert check(ctx, good) == []
    bad = copy.deepcopy(good)
    bad["tests"][0]["name"] = "missing_case"
    bad["tests"][1]["path"] = "tests/test_absent.py"
    issues = check(ctx, bad)
    assert any("missing_case is not a test case in us/statutes/42/403/a/5.test.yaml" in issue for issue in issues)
    assert any("tests/test_absent.py does not exist" in issue for issue in issues)
    local_commit = copy.deepcopy(good)
    local_commit["tests"][0]["commit"] = COMMIT
    assert any("commit is only for a file in another repository" in issue for issue in check(ctx, local_commit))


def test_production_code_cannot_pin_a_reading(tmp_path):
    # Review of #1710: a production function named as a test satisfied the gate.
    ctx = make_repo(tmp_path)
    (ctx.root / "tools").mkdir()
    (ctx.root / "tools" / "source_conflicts.py").write_text("def global_id(entry):\n    return entry\n")
    value = entry()
    del value["implementations"]
    value["tests"] = [{"path": "tools/source_conflicts.py", "name": "global_id", "pins": ["reading"]}]
    issues = check(ctx, value)
    assert any("is not a test file (test_*.py)" in issue for issue in issues), issues
    # A helper inside a test file passes the syntactic screen; pytest does
    # not collect it, so tools/pin_runner.py reports it `missing`.
    (ctx.root / "tests" / "test_helpers.py").write_text("def global_id(entry):\n    return entry\n")
    value["tests"] = [{"path": "tests/test_helpers.py", "name": "global_id", "pins": ["reading"]}]
    value["money_case"]["computed_by"] = "global_id"
    assert check(ctx, value) == []
    value["tests"] = [{"path": "tests/test_helpers.py", "name": "absent", "pins": ["reading"]}]
    assert any("absent is not a test function defined in tests/test_helpers.py" in issue for issue in check(ctx, value))


def test_a_parametrized_case_cannot_be_pinned(tmp_path):
    # Reviews of #1710: ids from a comment, unescaped explicit ids, pytest.param
    # precedence and empty ids in a stack all satisfied the gate. pytest builds
    # case ids from more than the file shows, so a pin names the whole test.
    ctx = make_repo(tmp_path)
    (ctx.root / "tests" / "test_params.py").write_text(
        "import pytest\n"
        "@pytest.mark.parametrize('case', ['real-case', 'café'])\n"
        "def test_case(case):\n    pass\n"
    )
    value = entry()
    value.pop("money_case")  # its tests are replaced below
    del value["implementations"]
    for name, ok in (("test_case", True), ("test_case[real-case]", False), ("test_case[caf\\xe9]", False)):
        value["tests"] = [{"path": "tests/test_params.py", "name": name, "pins": ["reading"]}]
        issues = check(ctx, value)
        assert (issues == []) == ok, (name, issues)
        if not ok:
            assert any("names a parametrized case; pin the whole test function" in issue for issue in issues)


def test_a_non_utf8_test_file_is_read_by_its_coding_cookie(tmp_path):
    # Review of #1710 round 2: a latin-1 test file made check raise.
    ctx = make_repo(tmp_path)
    (ctx.root / "tests" / "test_latin.py").write_bytes(
        b"# -*- coding: latin-1 -*-\nimport pytest\n@pytest.mark.parametrize('x', ['\xe9'])\ndef test_l1(x):\n    pass\n"
    )
    (ctx.root / "us" / "statutes" / "42" / "403" / "a" / "5.test.yaml").write_bytes(b"- name: caf\xe9\n")
    value = entry()
    value.pop("money_case")  # its tests are replaced below
    del value["implementations"]
    value["tests"] = [{"path": "tests/test_latin.py", "name": "test_l1", "pins": ["reading"]}]
    assert check(ctx, value) == []
    value["tests"] = [{"path": "us/statutes/42/403/a/5.test.yaml", "name": "case", "pins": ["reading"]}]
    assert any("case is not a test case in" in issue for issue in check(ctx, value))


@pytest.mark.parametrize(
    ("source", "name", "expected"),
    [
        # The screen is syntax only: a def at module level, or in a module-level class.
        ("def test_a():\n    pass\n", "test_a", True),
        ("async def test_a():\n    pass\n", "test_a", True),
        ("class TestC:\n    def test_d(self):\n        pass\n", "TestC::test_d", True),
        ("class TestC(Base):\n    async def test_d(self):\n        pass\n", "TestC::test_d", True),
        # Compound statements at module level still define at module level.
        ("if X:\n    def test_a():\n        pass\nelse:\n    pass\n", "test_a", True),
        ("try:\n    import x\nexcept ImportError:\n    def test_a():\n        pass\n", "test_a", True),
        ("try:\n    pass\nfinally:\n    def test_a():\n        pass\n", "test_a", True),
        ("with open('x') as f:\n    class TestC:\n        def test_d(self):\n            pass\n", "TestC::test_d", True),
        ("for i in []:\n    pass\nelse:\n    def test_a():\n        pass\n", "test_a", True),
        ("while False:\n    def test_a():\n        pass\n", "test_a", True),
        ("match x:\n    case 1:\n        def test_a():\n            pass\n", "test_a", True),
        ("class TestC:\n    if X:\n        def test_d(self):\n            pass\n", "TestC::test_d", True),
        # Decorators and import-time code are not judged: pytest decides at run time.
        ("import pytest\n@pytest.mark.skip\ndef test_a():\n    pass\n", "test_a", True),
        ("import pytest\npytest.skip('x', allow_module_level=True)\ndef test_a():\n    pass\n", "test_a", True),
        # Not defined where the name says.
        ("def test_a():\n    pass\n", "test_b", False),
        ("def outer():\n    def test_a():\n        pass\n", "test_a", False),
        ("class TestC:\n    def test_d(self):\n        pass\n", "test_d", False),
        ("def test_a():\n    pass\n", "TestC::test_a", False),
        ("class TestC:\n    class Inner:\n        def test_d(self):\n            pass\n", "TestC::test_d", False),
        ("def make():\n    class TestC:\n        def test_d(self):\n            pass\n", "TestC::test_d", False),
        ("test_a = lambda: None\n", "test_a", False),
        ("from helpers import test_a\n", "test_a", False),
        ("class test_a:\n    pass\n", "test_a", False),
        # Names the register refuses, and files that do not parse.
        ("def test_a():\n    pass\n", "test_a[1]", False),
        ("def test_a():\n    pass\n", "A::B::test_a", False),
        ("def test_a(:\n    pass\n", "test_a", False),
        ("def test_a():\n    pass\n\x00", "test_a", False),
    ],
)
def test_python_test_resolution(source, name, expected):
    assert sc.python_test_exists(source, name) == expected
    assert sc.python_test_exists(source.encode(), name) == expected


@pytest.mark.parametrize(
    "prefix",
    [
        # Round-9 review: CPython's parser raises MemoryError ("source too
        # complex") on 20,000 unary operators; deep brackets and indentation
        # raise SyntaxError. Each is a failed screen, never an exception.
        "x = " + "+" * 20000 + "1\n",
        "x = " + "(" * 1000 + ")" * 1000 + "\n",
        "".join("    " * level + "if x:\n" for level in range(101)) + "    " * 101 + "pass\n",
        "x = " + "[" * 5000 + "]" * 5000 + "\n",
    ],
)
def test_the_screen_fails_closed_on_input_the_parser_cannot_handle(tmp_path, prefix):
    source = prefix + "def test_a():\n    pass\n"
    assert sc.python_test_exists(source, "test_a") is False
    assert sc.python_test_exists(source.encode(), "test_a") is False
    ctx = make_repo(tmp_path)
    (ctx.root / "tests" / "test_deep.py").write_text(source)
    value = entry()
    value.pop("money_case")
    del value["implementations"]
    value["tests"] = [{"path": "tests/test_deep.py", "name": "test_a", "pins": ["reading"]}]
    assert any("test_a is not a test function defined in tests/test_deep.py, or the file does not parse" in issue
               for issue in check(ctx, value))


def test_the_scope_walk_is_iterative():
    # Review of #1825 (P3): 98 parsed levels never reach the recursion limit,
    # so they also pass a recursive walk. A tree built directly, 5,000 levels
    # of `if` deep, would raise RecursionError in one; the iterative walk
    # visits every statement.
    inner: list[ast.stmt] = [ast.FunctionDef(name="test_deep", args=ast.arguments(), body=[ast.Pass()], decorator_list=[])]
    for _ in range(5000):
        inner = [ast.If(test=ast.Constant(True), body=inner, orelse=[])]
    statements = list(sc._scope_statements(inner))
    assert len(statements) == 5001
    assert isinstance(statements[-1], ast.FunctionDef) and statements[-1].name == "test_deep"


def test_the_screen_walks_deeply_nested_blocks():
    # The walk over compound statements is iterative; 98 levels of `if`, with
    # the def's body at the 100th (CPython's indentation limit), still find it.
    source = "".join("    " * level + "if x:\n" for level in range(98)) + "    " * 98 + "def test_a():\n" + "    " * 99 + "pass\n"
    assert sc.python_test_exists(source, "test_a") is True


def _field_paths(value, prefix=()):
    if isinstance(value, dict):
        items = value.items()
    elif isinstance(value, list):
        items = enumerate(value)
    else:
        return
    for key, child in items:
        yield prefix + (key,)
        yield from _field_paths(child, prefix + (key,))


def test_check_is_total_with_module_scanning_on_a_malformed_adopted_by(tmp_path):
    # Round-4 review: registered_pairs iterated an unchecked adopted_by, so
    # the default check (module scanning on) raised TypeError.
    ctx = make_repo(tmp_path)
    for bad in (7, "x", {"module": "a"}, [7], None):
        value = entry(adopted_by=bad)
        issues = check(ctx, value, scan=True)
        assert any("adopted_by" in issue for issue in issues), (bad, issues)


def test_check_is_total_on_deep_nesting(tmp_path):
    # Round-8 review: 1,100 nested lists under an unknown field raised
    # RecursionError in the hygiene walk. The walk is iterative now.
    deep: list = []
    cursor = deep
    for _ in range(20000):
        cursor.append([])
        cursor = cursor[0]
    value = entry()
    value["extra_field"] = deep
    issues = check(make_repo(tmp_path), value, scan=True)
    assert issues == ["Entry `family-maximum-saving-clause` (entries[0]) has unknown key `extra_field`."]


def test_a_register_nested_too_deeply_to_parse_is_refused(tmp_path, capsys):
    path = tmp_path / sc.REGISTER_FILENAME
    path.write_text("version: 1\nentries: " + "[" * 5000 + "]" * 5000 + "\n")
    with pytest.raises(sc.RegisterError, match="nests too deeply"):
        sc.load_register(path)
    assert sc.main(["check", "--root", str(tmp_path)]) == 1
    assert "nests too deeply" in capsys.readouterr().err


def test_check_is_total_on_every_field(tmp_path):
    # Review of #1710 round 2: the Hypothesis totality property draws any one
    # field only a few times a run, so a crash on one field was caught in half
    # the seeds. This replaces every field of a well-formed entry, at every
    # depth, with each malformed shape, on every run.
    ctx = make_repo(tmp_path)
    base = entry()
    paths = list(_field_paths(base))
    assert ("jurisdiction",) in paths and ("tests", 1, "name") in paths
    for path in paths:
        for new in ([], {}, None, 7, -1.5, True, "", "x", [[]], {"a": []}):
            value = copy.deepcopy(base)
            target = value
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = new
            issues = check(ctx, value, copy.deepcopy(value), scan=True)
            assert isinstance(issues, list) and all(isinstance(issue, str) for issue in issues), (path, new)


def test_python_test_file_conventions():
    for path, ok in (
        ("tests/test_a.py", True),
        ("test_a.py", True),
        ("tests/sub/a_test.py", False),  # not in every repo's python_files
        ("tools/source_conflicts.py", False),
        ("tests/helpers.py", False),
        ("tests/conftest.py", False),
    ):
        assert sc.python_test_file(path) == ok, path
        assert sc.test_exists(path, "test_a", b"def test_a():\n    pass\n") == ok, path


def test_test_path_and_name_shapes(tmp_path):
    bad = entry()
    bad["tests"][0]["path"] = "tests/test_g.js"
    bad["tests"][1]["name"] = "not a name"
    issues = check(make_repo(tmp_path), bad)
    assert any("relative .py or .yaml path" in issue for issue in issues)
    assert any("must be a test function" in issue for issue in issues)
    local = entry()
    local["tests"] = [{"path": "tests/cases.yaml", "name": "a case", "pins": ["reading"]}]
    assert any("relative .py or .test.yaml path" in issue for issue in check(make_repo(tmp_path), local))


def test_a_test_path_has_no_pin_separator(tmp_path):
    # #1843 review: `path::name` must split one way only.
    value = entry()
    value["tests"][0]["path"] = "tests/a.yaml::b.yaml"
    value["tests"][0]["name"] = "c"
    assert any("contains `::`, which separates a test file" in issue for issue in check(make_repo(tmp_path), value))


def test_external_yaml_test_cases(tmp_path):
    # Another repository's YAML policy tests (PolicyEngine-US) are pinned by
    # repo, commit, path and case name; the case name is free text.
    ctx = make_repo(tmp_path)
    value = entry()
    value["tests"][1] = {
        "repo": "PolicyEngine/policyengine-us",
        "commit": COMMIT,
        "path": "policyengine_us/tests/policy/baseline/gov/states/hi/tax/income/claim_of_right.yaml",
        "name": "Hawaii, repayment over $3,000, statute reading",
        "pins": ["every-later-month"],
    }
    assert check(ctx, value) == []
    for name in ("", " padded", "two\nlines", 7):
        bad = copy.deepcopy(value)
        bad["tests"][1]["name"] = name
        assert any("must be a YAML test case's name, on one line" in issue for issue in check(ctx, bad)), name
    outside = copy.deepcopy(value)
    outside["tests"][1]["path"] = "policyengine_us/variables/claim_of_right.yaml"
    assert any("is not under a tests directory" in issue for issue in check(ctx, outside))
    assert sc.test_exists("cases.yaml", "Hawaii case", b"- name: Hawaii case\n  input: {}\n")
    assert not sc.test_exists("cases.yaml", "Other case", b"- name: Hawaii case\n")


def test_repeated_test_reference(tmp_path):
    bad = entry()
    bad["tests"].append(dict(bad["tests"][0]))
    assert any("repeats tests/test_g.py::test__given_operational__then_pays" in issue for issue in check(make_repo(tmp_path), bad))


@pytest.mark.parametrize(
    ("field", "value", "fragment"),
    [
        ("amount", 21, "decimal string"),
        ("amount", "-3", "decimal string"),
        ("amount", "1,000", "decimal string"),
        ("currency", "usd", "ISO 4217"),
        ("period", "fortnight", "period must be one of"),
    ],
)
def test_money_case(tmp_path, field, value, fragment):
    bad = entry()
    bad["money_case"][field] = value
    assert any(fragment in issue for issue in check(make_repo(tmp_path), bad))


def test_dollar_amounts_in_prose_need_a_money_case(tmp_path):
    # Final review of 6a21582e: removing a money case left "$200 would be
    # charged" in an alternative's effect. Every $ in the entry's own prose
    # must be one its money case (backed by computed_by) states.
    ctx = make_repo(tmp_path)
    good = entry()
    good["alternatives"][0]["effect"] = "The family is paid $21.00 less."
    assert check(ctx, good) == []
    bad = entry()
    bad["alternatives"][0]["effect"] = "The family would be paid $825 instead."
    issues = check(ctx, bad)
    assert any("alternatives[0].effect states $825, which no money case backs" in issue for issue in issues), issues
    no_case = entry()
    del no_case["money_case"]
    no_case["basis"] = "SSA pays $1,500.00 under its reading."
    assert any("basis states $1500, which no money case backs" in issue for issue in check(ctx, no_case))
    described = entry()
    described["money_case"]["description"] = "A survivor family after a child ages out: $1,500.00 against $1,479."
    described["reading"] = "Protect $1,500 from the earlier month."
    assert check(ctx, described) == []


def test_dollar_amounts_the_sources_state_or_consumers_write(tmp_path):
    # An excerpt may state a figure (a statutory threshold); the entry's own
    # prose may not restate it without a money case. Consumer prose (an
    # implementation's basis, the years' note, an unpublished source's
    # description) is checked too.
    ctx = make_repo(tmp_path)
    quoted = entry()
    quoted["texts"][0]["excerpt"] = "a repayment that exceeds $3,000"
    assert not [issue for issue in check(ctx, quoted) if "no money case backs" in issue]
    quoted["question"] = "Does a repayment that exceeds $3,000 sit outside the floor?"
    assert any("question states $3000, which no money case backs" in issue for issue in check(ctx, quoted))
    for path, text in (
        (("implementations", 0, "basis"), "The statute pays $900 more."),
        (("years", "note"), "A program year worth $40."),
    ):
        value = entry(years={"from": 2024, "type": "program", "note": "July to June."})
        target = value
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = text
        assert any("which no money case backs" in issue for issue in check(ctx, value)), path


@pytest.mark.parametrize(
    "text",
    [
        # #1825 reviews (rounds 1 and 2): an excerpt's figure backs no amount in
        # the entry's own prose, however the prose words it. No test on the
        # surrounding words can tell a quoted threshold from a computed claim.
        "A repayment over $3,000 stays outside the floor.",
        "This reading pays $3,000 more in the invented case.",
        "This reading pays over $3,000 more than the statute's reading.",
        "It allows a deduction of $3,000 for the invented filer.",
        "The readings differ by a difference of $3,000.",
        "It costs the filer a tax of $3,000.",
        "It means $3,000 or less in extra tax.",
        "It gives a refund of $3,000.",
        "This reading pays $3000 more.",
        "This reading pays $3,000.00 more.",
        "The repayment is over. $3,000 more tax is due.",
        "A repayment over\u00a0$3,000 stays outside the floor.",
    ],
)
def test_an_excerpts_figure_backs_no_amount_in_prose(tmp_path, text):
    value = entry()
    value["texts"][0]["excerpt"] = "Deduction for repayment of amounts under a claim of right over $3,000."
    value["pending_texts"][0]["excerpt"] = "Deduction for repayment of amounts under a claim of right of $3,000 or less."
    del value["money_case"]
    value["alternatives"][0]["effect"] = text
    issues = check(make_repo(tmp_path), value)
    assert any("states $3000, which no money case backs" in issue for issue in issues), issues
    # Naming the threshold without restating it is the way to cite it.
    value["alternatives"][0]["effect"] = "A repayment above the section 1341 threshold stays outside the floor."
    assert not [issue for issue in check(make_repo(tmp_path), value) if "no money case backs" in issue]


@pytest.mark.parametrize(
    "spelling", ["USD 200", "200 dollars", "$  200", "$ 200", "$.50", "$-200", "$1.5k", "US$200", "$1.5", "$1,23", "50 cents"]
)
def test_money_has_one_spelling(tmp_path, spelling):
    # Round-6 review, nit: other spellings slipped past the money-case rule.
    value = entry()
    value["alternatives"][0]["effect"] = f"The family is paid {spelling} less."
    assert any("writes money as" in issue for issue in check(make_repo(tmp_path), value)), spelling


def test_canonical_money_at_a_sentence_end(tmp_path):
    value = entry()
    value["money_case"]["description"] = "A family: $1,234.56 against $1,213.56."
    value["alternatives"][0]["effect"] = "The family is paid $21.00, then $1,234.56."
    assert check(make_repo(tmp_path), value) == []


def test_the_register_refuses_anchors_and_cycles(tmp_path):
    # Final review of 6a21582e: a recursive alias made check raise RecursionError.
    path = tmp_path / sc.REGISTER_FILENAME
    path.write_text("version: 1\nentries: []\nextra: &self\n  self: *self\n")
    with pytest.raises(sc.RegisterError, match="anchors and aliases are not allowed"):
        sc.load_register(path)
    path.write_text("version: 1\nentries: []\nshared: &a [1]\nother: *a\n")
    with pytest.raises(sc.RegisterError, match="anchors and aliases are not allowed"):
        sc.load_register(path)
    recursive = yaml.safe_load("version: 1\nentries: []\nextra: &self\n  self: *self\n")
    issues = sc.check_register(recursive, make_repo(tmp_path), scan_modules=True)
    assert issues == [f"{sc.REGISTER_FILENAME} contains itself through an alias; anchors and aliases are not allowed."]
    looped = {"version": 1, "entries": [entry()]}
    looped["entries"][0]["alternatives"][0]["effect"] = looped["entries"]
    assert "contains itself" in sc.check_register(looped, make_repo(tmp_path))[0]


def test_a_money_case_names_the_pinned_test_that_computes_it(tmp_path):
    # Round-4 review: a public amount needs a pinned test that computes it.
    ctx = make_repo(tmp_path)
    assert check(ctx, entry()) == []
    for computed_by in (None, "test_not_pinned", "TestLiteral::test_refuses[1]"):
        bad = entry()
        if computed_by is None:
            del bad["money_case"]["computed_by"]
        else:
            bad["money_case"]["computed_by"] = computed_by
        assert any("money_case.computed_by must name the one test" in issue for issue in check(ctx, bad)), computed_by
    ambiguous = entry()
    ambiguous["tests"].append(dict(ambiguous["tests"][0], path="tests/test_h.py"))
    assert any("money_case.computed_by must name the one test" in issue for issue in check(ctx, ambiguous))
    no_amount = entry()
    del no_amount["money_case"]
    assert check(ctx, no_amount) == []


# ---------------------------------------------------------------------------
# Source kinds, years, conflict state, unpublished sources

# Every document class the corpus used when this was written (second segment
# of data/corpus/provisions/<jurisdiction>/<class>/ in axiom-corpus). A class
# missing from DOCUMENT_CLASS_KINDS fails closed, so a new one must get a row.
CORPUS_DOCUMENT_CLASSES = ("statute", "regulation", "rulemaking", "form", "guidance", "manual", "policy", "district-plan")


def test_every_corpus_document_class_has_a_kind_row():
    assert set(CORPUS_DOCUMENT_CLASSES) <= set(sc.DOCUMENT_CLASS_KINDS)
    for document_class, kinds in sc.DOCUMENT_CLASS_KINDS.items():
        assert kinds, document_class
        assert set(kinds) <= set(sc.SOURCE_KINDS), document_class


def test_text_kind_is_derived_from_the_document_class(tmp_path):
    value = entry()
    assert sc.text_kind(value, "us/statute/42/403/a/5") == "statute"
    assert sc.text_kind(value, "us-hi/form/n-11/2024/instructions") == "form"
    assert sc.text_kind(value, "us/unknown-class/x") is None
    value["text_kinds"] = {"us/statute/42/403/a/5": "statute"}
    assert sc.text_kind(value, "us/statute/42/403/a/5") == "statute"


def test_unknown_document_class_fails_closed(tmp_path):
    bad = entry(texts=[{"corpus_citation_path": "us/opinion/2026/1", "excerpt": "x"}])
    assert any("document class `opinion` has no DOCUMENT_CLASS_KINDS row" in issue for issue in check(make_repo(tmp_path), bad))


def test_text_kinds_override(tmp_path):
    ctx = make_repo(tmp_path)
    form_text = {"corpus_citation_path": "us-co/form/dr-0347/2025/line-1", "excerpt": "a qualifying child"}
    good = entry(texts=[entry()["texts"][0], form_text], text_kinds={"us-co/form/dr-0347/2025/line-1": "instructions"})
    assert check(ctx, good) == []
    assert sc.text_kind(good, "us-co/form/dr-0347/2025/line-1") == "instructions"
    for overrides, fragment in (
        ({"us/statute/42/403/a/5": "instructions"}, "a `statute` path can only be statute"),
        ({"us-co/form/dr-0347/2025/line-1": "speech"}, "must be one of statute"),
        ({"us/statute/42/403/a/6": "statute"}, "not one of this entry's texts"),
        ({}, "non-empty mapping"),
        ("instructions", "non-empty mapping"),
    ):
        bad = copy.deepcopy(good)
        bad["text_kinds"] = overrides
        assert any(fragment in issue for issue in check(ctx, bad)), overrides


@pytest.mark.parametrize("kind", [None, "", "Manual", "speech"])
def test_pending_text_kind_is_a_closed_enum(tmp_path, kind):
    bad = entry()
    if kind is None:
        del bad["pending_texts"][0]["kind"]
    else:
        bad["pending_texts"][0]["kind"] = kind
    assert any("pending_texts[0].kind must be one of" in issue for issue in check(make_repo(tmp_path), bad))


@pytest.mark.parametrize(
    ("years", "fragment"),
    [
        ({"from": 2022, "to": 2025, "type": "tax"}, None),
        ({"from": 2024, "type": "tax"}, None),
        ({"from": 2026, "to": 2026, "type": "federal-fiscal"}, None),
        ({"from": 2025, "type": "program", "note": "LIHEAP program year, October to September"}, None),
        ({"from": 2025, "type": "program"}, "note is required when type is `program`"),
        ({"from": 2025, "to": 2022, "type": "tax"}, "is before"),
        ({"from": "2022", "type": "tax"}, "from must be a whole year"),
        ({"from": True, "type": "tax"}, "from must be a whole year"),
        ({"from": 1800, "type": "tax"}, "from must be a whole year"),
        ({"from": 2022, "to": None, "type": "tax"}, "to must be a whole year"),
        ({"to": 2022, "type": "tax"}, "from must be a whole year"),
        ({"from": 2022, "type": "school"}, "type must be one of"),
        ({"from": 2022}, "type must be one of"),
        ({"from": 2022, "type": "tax", "until": 2023}, "unknown key `until`"),
        ({"from": 2022, "type": "tax", "note": " "}, "note must be a non-blank string"),
        ("2022-2025", "years must be a mapping"),
    ],
)
def test_years(tmp_path, years, fragment):
    issues = check(make_repo(tmp_path), entry(years=years))
    if fragment is None:
        assert issues == []
    else:
        assert any(fragment in issue for issue in issues), issues


RESOLUTION = {"by": "legislation", "effective": "2026-01-01", "record": "https://github.com/x/y/issues/3"}


def test_conflict_and_resolution_go_together(tmp_path):
    ctx = make_repo(tmp_path)
    resolved = entry(conflict="resolved", resolution=dict(RESOLUTION), years={"from": 2022, "to": 2025, "type": "tax"})
    assert check(ctx, resolved) == []
    assert check(ctx, entry(conflict="live")) == []
    cases = (
        (entry(conflict="resolved", years={"from": 2022, "to": 2025, "type": "tax"}), "resolution is required when conflict is `resolved`"),
        (entry(resolution=dict(RESOLUTION)), "resolution must be absent while conflict is `live`"),
        (entry(conflict="live", resolution=dict(RESOLUTION)), "resolution must be absent while conflict is `live`"),
        (entry(conflict="resolved", resolution=dict(RESOLUTION), years={"from": 2022, "type": "tax"}), "years.to is required"),
        (entry(conflict="resolved", resolution=dict(RESOLUTION)), "years.to is required"),
        (entry(conflict="closed"), "conflict must be live or resolved"),
    )
    for value, fragment in cases:
        assert any(fragment in issue for issue in check(ctx, value)), fragment
    for field, value, fragment in (
        ("by", "court", "by must be legislation or agency"),
        ("effective", "2026-02-30", "effective must be a real"),
        ("record", "http://example.com", "record must be an https URL"),
    ):
        bad = copy.deepcopy(resolved)
        bad["resolution"][field] = value
        assert any(fragment in issue for issue in check(ctx, bad)), field


UNPUBLISHED = {"kind": "agency-practice", "description": "MN DHS correspondence on approved guardian fees", "date": "2026-10-19"}


@pytest.mark.parametrize(
    ("change", "fragment"),
    [
        ({}, None),
        ({"description": 'The department "approves one hundred dollars a month" in practice'}, "quotes more than 4 words"),
        ({"description": "The department \u201capproves one hundred dollars a month\u201d"}, "quotes more than 4 words"),
        ({"description": 'The department "approves the waiver" in practice'}, None),
        # Review of #1825 (P3): the bound counts every quoted span together,
        # and single quotation marks quote too; an apostrophe does not.
        ({"description": 'It wrote "one two three four" and "five six seven eight"'}, "quotes more than 4 words in all"),
        ({"description": "It wrote \u2018one two three four five six seven eight\u2019"}, "quotes more than 4 words in all"),
        ({"description": "It wrote 'one two three four five six seven eight'"}, "quotes more than 4 words in all"),
        ({"description": "The agency's reply 'approves it' and \"the waiver\""}, None),
        ({"description": "The agency's reply to the board and the clerk's note were brief"}, None),
        # Round 2: a span runs from its opening mark to its closing mark, past
        # apostrophes inside it; an elision or a plural possessive opens nothing.
        ({"description": "It wrote 'the county's policy is to deny every such claim'"}, "quotes more than 4 words in all"),
        ({"description": "It wrote \u2018we\u2019ll deny every claim of this kind\u2019"}, "quotes more than 4 words in all"),
        # Intended (#1867 round 4): an elided year may open a quotation and a
        # later word-end apostrophe may close it, so this is refused; "1990s"
        # passes.
        ({"description": "Since the '90s the clerks in each county office have handled the clerks' files"}, "quotes more than 4 words in all"),
        ({"description": "Since the 1990s the clerks in each county office have handled the clerks' files"}, None),
        ({"description": "The agency's reply was brief, said the clerks' office"}, None),
        ({"description": 'An unclosed "quotation runs to the end of the text'}, "quotes more than 4 words in all"),
        # A trailing-space mark is now eligible; the last closer still wins.
        ({"description": "It wrote 'one two ' three four five six seven'"}, "quotes more than 4 words in all"),
        ({"description": "Reply from someone@example.gov"}, "contains `@`"),
        ({"kind": "phone"}, "kind must be one of"),
        ({"date": "October 19"}, "date must be a real"),
        ({"description": " "}, "description must be a non-blank string"),
        ({"excerpt": "verbatim words"}, "unknown key `excerpt`"),
    ],
)
def test_unpublished_sources(tmp_path, change, fragment):
    issues = check(make_repo(tmp_path), entry(unpublished_sources=[{**UNPUBLISHED, **change}]))
    if fragment is None:
        assert issues == []
    else:
        assert any(fragment in issue for issue in issues), issues


def test_unpublished_sources_shape(tmp_path):
    ctx = make_repo(tmp_path)
    assert any("unpublished_sources must be a non-empty list" in issue for issue in check(ctx, entry(unpublished_sources=[])))
    missing = {key: value for key, value in UNPUBLISHED.items() if key != "date"}
    assert any("unpublished_sources[0].date is required" in issue for issue in check(ctx, entry(unpublished_sources=[missing])))


@pytest.mark.parametrize(
    ("text", "spans"),
    [
        # #1825 round-3 review (P3): a single mark opens at a word's start,
        # after any Unicode whitespace, not only an ASCII space.
        *[(f"It wrote:{space}'one two three'", ["one two three"]) for space in ("\u00a0", "\u202f", "\u2009", "\u3000", "\u2003", "\t", "\n")],
        # After an opening bracket, a dash, a slash, an opening quotation mark
        # that pass 1 does not consume (U+201B), or other punctuation.
        *[(f"x{before}'one two'", ["one two"]) for before in ("(", "[", "{", "\u2014", "\u2013", "-", "/", "\u201b", ":", ".", "!")],
        # This starts an unclosed pass-1 region; its inner single marks are
        # literal text, consumed in pass 1.
        ("x\u300c'one two'", ["'one two'"]),
        # \u00ab also closes \u00bb, so glued to a word it opens nothing (the first
        # known limit), and the single quotation after it is read.
        ("x\u00ab'one two'", ["one two"]),
        # The text's first character, and a combining mark after the opener.
        ("'one two three' said the agency.", ["one two three"]),
        ("\u2018one two\u2019 it said", ["one two"]),
        ("It wrote '\u0301one two'", ["\u0301one two"]),
        # Known limit (#1867 round 4): a mark after a letter or digit is an
        # apostrophe, so a quotation opened mid-word isn't counted.
        ("x'one two'", []),
        ("6'one two'", []),
        # Any other single mark may open: before a digit, a space or a mark.
        ("the '90s and 'old' days", ["90s and 'old"]),
        ("a '30 day limit' it set", ["30 day limit"]),
        ("x ' one two'", [" one two"]),
        # A mark at either end of the text.
        ("ends with '", []),
        ("'", []),
        ("x '", []),
        ("'a b'", ["a b"]),
        # Single marks are read as one span, from the first opener to the
        # last closer: they can't be told from apostrophes (#1867 round 3).
        ("'one' and 'two'", ["one' and 'two"]),
        ("'one two' and the workers' case", ["one two' and the workers"]),
        # A closer precedes no letter or digit, including after whitespace.
        ("the 'one two 6'7 tall", []),
        ("the 'one two's end", []),
        ("the 'one two'.", ["one two"]),
        ("the 'one two', then", ["one two"]),
        # An opener no closer follows is an apostrophe; an unclosed double
        # quote runs to the end.
        ("the 'one two three four five", []),
        ('the "one two', ["one two"]),
        # Each double opener pairs with its own closer only.
        ('\u201ca\u201d x "b c d e f"', ["a", "b c d e f"]),
        ('"a\u201d b c"', ["a\u201d b c"]),
        ('\u201ca" b\u201d', ['a" b']),
        ("\u201ca\u201d", ["a"]),
        ('""', [""]),
    ],
)
def test_quoted_spans(text, spans):
    assert sc.quoted_spans(text) == spans


def test_single_mark_rules():
    # A closer depends only on what follows it: no letter or decimal digit.
    assert sc._closes_single("' x", 0) is True
    assert sc._closes_single("x' y", 1) is True
    assert sc._closes_single("x '", 2) is True
    assert sc._closes_single("x'\u00b9", 1) is True
    assert sc._closes_single("'x", 0) is False
    assert sc._closes_single("'7", 0) is False
    assert sc._closes_single("'\u0663", 0) is False  # an Arabic-Indic digit
    # A single mark may open unless it follows a letter or digit (past any
    # combining marks on it) or ends the text.
    assert sc._opens_single("'x", 0) is True
    assert sc._opens_single("a:'x", 2) is True
    assert sc._opens_single("'9", 0) is True
    assert sc._opens_single("' x", 0) is True
    assert sc._opens_single("''", 1) is False
    assert sc._opens_single("a'x", 1) is False
    assert sc._opens_single("1'x", 1) is False
    assert sc._opens_single("e\u0301'x", 2) is False
    assert sc._opens_single("x '", 2) is False


@pytest.mark.parametrize(
    ("text", "words"),
    [
        # A quotation inside a quotation, and a possessive inside one.
        ("It wrote 'one two three 'inner' four'", 5),
        ("It wrote 'the workers' policy is to deny every such claim'", 9),
        ("It wrote 'one two three 'four five'", 5),
        ("'one 'two three'", 3),
        # Round 1's P1: a delimited quotation inside a single one counts in
        # full, and its words count once.
        ("It wrote:\u00a0'about \"the workers' policy is to deny every such claim\"'", 10),
        ("The agency's reply 'approves it' and \"the waiver\"", 4),
    ],
)
def test_quoted_words(text, words):
    assert sc.quoted_words(text) == words


@pytest.mark.parametrize(
    ("description", "count", "refused"),
    [
        # #1867 round 3 (P2): an elided year, an elision or a dropped g
        # inside a quotation no longer ends it.
        ("It wrote 'the workers' '90s policy is to deny every claim'", 9, True),
        ("It wrote 'the '90s rules' policy is to deny every claim'", 9, True),
        ("It wrote 'the workers' claims denied 'cause ineligible'", 6, True),
        ("It wrote 'the workers' claims denied 'bout ineligible'", 6, True),
        ("It wrote 'we are goin' to deny every claim'", 7, True),
        ("It wrote \u2018we are goin\u2019 to deny every claim\u2019", 7, True),
        # Round 2 (P2): a possessive with an elision or a nested quotation.
        ("It wrote 'the workers' plan won't cover 'em all'", 7, True),
        ("It wrote 'the workers' policy is to deny every 'special' claim'", 9, True),
        ("It wrote 'the 'Benefits' section ends here'", 5, True),
        # Round 3 (P2): a quotation nested in the same delimited marks.
        ("It wrote \u201cone two \u201cthree\u201d four five\u201d", 5, True),
        ("It wrote \u00abone two \u00abthree\u00bb four five\u00bb", 5, True),
        ("It wrote \u300cone two \u300cthree\u300d four five\u300d", 5, True),
        ('It wrote "one two "three" four five"', 5, True),
        ("It wrote \u201ex \u201ca \u201cb\u201d c d e\u201d", 6, True),
        # Round 2 (P1): the floor is main's own count, so a standalone
        # ellipsis still counts as main counted it.
        ('It wrote "one two three four \u2026"', 5, True),
        # Round 2 (P2): an inch mark inside a single quotation, after a
        # no-break space; and before a double quotation (the strict reading).
        ("It wrote:\u00a0'the adult must be at least 6\" tall'", 8, True),
        # (The nested reading reads the inch mark as an unclosed quotation
        # around the real one, so it counts more; it fails closed.)
        ('He is 6" tall and wrote "one two three four five"', 8, True),
        ('He is 6\u201d tall and wrote \u201cone two three four five\u201d', 5, True),
        # A stray low mark can't take a single opener as its closer.
        ("It wrote \u201ax \u2019one two three four five\u2019", 6, True),
        # Round 2 (P2): reversed guillemets, same-direction marks, ’…’, and a
        # closer before a footnote mark.
        ("It wrote \u00bbone two three four five\u00ab", 5, True),
        ("It wrote \u203aone two three four five\u2039", 5, True),
        ("It wrote \u201done two three four five\u201d", 5, True),
        ("It wrote \u00bbone two three four five\u00bb", 5, True),
        ("It wrote \u2019one two three four five\u2019", 5, True),
        ("It wrote \u2018one two three four five\u2019\u00b9", 5, True),
        # A single quotation after other punctuation now counts.
        ("It wrote:'one two three four five'", 5, True),
        # Round 4 closes round 2's documented limits: every Unicode quotation
        # mark, primes and ornaments, a single quotation closed by a double
        # mark, one starting with a digit, and one with a space inside its marks.
        ("It wrote \u2018one two three four five\u201d", 5, True),
        ("It wrote \u2032one two three four five\u2032", 5, True),
        ("It wrote \u2033one two three four five\u2033", 5, True),
        ("It wrote \u2036one two three four five\u2033", 5, True),
        ("It wrote \u201bone two three four five\u2019", 5, True),
        ("It wrote \u201fone two three four five\u201d", 5, True),
        ("It wrote \u2e42one two three four five\u201c", 5, True),
        ("It wrote \ufe41one two three four five\ufe42", 5, True),
        ("It wrote \uff62one two three four five\uff63", 5, True),
        ("It wrote \u275bone two three four five\u275c", 5, True),
        ("It wrote \u275done two three four five\u275e", 5, True),
        ("It wrote \u276eone two three four five\u276f", 5, True),
        ("It wrote \U0001f676one two three four five\U0001f677", 5, True),
        ("It wrote '30 days or more for every claim'", 7, True),
        ("It wrote ' one two three four five '", 5, True),
        # A stray low mark that a possessive closes takes a single quotation's
        # opener in every delimited reading; only the whole-text single span
        # counts it, with the double quotation outside it (mutation round 5).
        ("\u201a\u201d 'claimants\u2019 the' and \"six seven eight\"", 5, True),
        # A double mark closes a single quotation too, even behind a stray low
        # mark (found by Hypothesis), and when it also closes a quotation
        # inside it (the one-pass reading).
        ("\u201aa 'claimants\u2019 the the\u201d ", 4, False),
        ("It wrote 'one two \u201cthree four\u201d", 4, False),
        # #1867 round 4 (P1): a closing double mark after a dash or an
        # apostrophe, before punctuation, closes; a space inside either mark
        # is fine. Each reading counts these exactly.
        ('"a\u2014". b', 1, False),
        ('He said "wait\u2014". Then he went away.', 1, False),
        ('He said "workers\'", then denied every claim.', 1, False),
        ('It wrote " one" today.', 1, False),
        ('It wrote "one two three four " today.', 4, False),
        # A mark before another quotation mark starts a quotation, so straight
        # marks nest at the start too (mutation round 6).
        ('It wrote ""one" two three four five"', 5, True),
        ('It wrote " ""one two" three four five"', 5, True),
        # Intended (#1867 round 5): \u2018 is a single mark that may open, so the
        # whole-text span reads \u2018 the the the workers' as a quotation; \u201a\u2026\u2018
        # is outside the double-quotation exactness scope.
        ("\u201athe \u2018 the the the workers' today.", 5, True),
        # Round 5 (P1): a single quotation that a stray low mark's region
        # swallows still counts in full, whatever its opener follows or its
        # body starts with.
        ("\u201ax \u2019 one two three four five\u2019", 6, True),
        ("\u201ax \u2019\u2014one two three four five\u2019", 6, True),
        ("\u201ax :\u2019one two three four five\u2019", 6, True),
        ("\u201ax:'one workers\u2019 two three four five'", 6, True),
        # Round 5 (P1): a closer before a bracketed citation closes.
        ('It wrote "one two three four\u2014"[1] today.', 4, False),
        ('It wrote "one two three workers\'"[1] today.', 4, False),
        ('It wrote "one two three four "[1] today.', 4, False),
        ('It wrote "one two three four "[1] today, and later "five six".', 6, True),
        # Known limit (#1867 round 5, accepted by ruling): a quotation nested in
        # the same marks whose inner quotation starts with a bracket reads as
        # two quotations, so the words between aren't counted. It is the
        # second fail-open the scanner accepts; changing it is a deliberate
        # decision. Nested in another pair, it counts in full.
        ('It wrote "one two "[sic] three four" five"', 3, False),
        ("It wrote \u201cone two \u00ab[sic] three four\u00bb five\u201d", 6, True),
        # Outside the exactness scope, as the README states: a space after a
        # mark that also closes (read as a closer), a word holding its own
        # quotation's closing mark, and main's floor after \u201e\u2026\u201c.
        ("It wrote \u201d one\u201d today.", 1, False),
        ("It wrote \u201aclaimants\u2019 policy\u2019 today.", 1, False),
        ("It wrote \u201eone\u201c then denied every remaining claim.", 5, True),
        # The boundary rules (mutation round 8): a closer before an opening
        # quotation character or after an apostrophe closes. Nesting in the
        # same marks may overcount, failing closed: the strict reading opens
        # an outer closer that isn't glued to a word (3 words counted 4; 2
        # counted 3).
        ('It wrote "one "two" wait\u2014"[1] today.', 4, False),
        ('It wrote "one "two"" today.', 3, False),
        ('It wrote \u00bbone "two\u2014"\u00ab today.', 2, False),
        ("It wrote \"one \u00abtwo workers'\u00bb\" today.", 3, False),
        # Found by fuzzing: only the standard delimited reading counts both words.
        ("'\u00abb\u2014\u00bbb\u2019", 2, False),
        # #1867 round 6 (P1): an opening mark that can also close opens after
        # punctuation, a dash or a colon; only a letter or digit before it
        # (or, for \u201d \u00bb \u203a \u2033, a space after it) keeps it shut.
        ("It wrote:\u00abone two three four five\u00bb.", 5, True),
        ("It wrote:\u2039one two three four five\u203a.", 5, True),
        ("It wrote:\U0001f676one two three four five\U0001f677.", 5, True),
        ("It wrote\u2014\u00ab one two three four five \u00bb.", 5, True),
        ("It wrote:\u00bbone two three four five\u00ab.", 5, True),
        # Known limit 2, as worded after round 6: a quotation nested inside
        # another, whose opening mark could also close the outer one and
        # that doesn't start with a letter or digit, reads as two quotations.
        ('It wrote "one """two" three" four" five" today.', 4, False),
        ('It wrote "one \u2014"\u00abtwo\u00bb three four" five" today.', 3, False),
        ("It wrote \u201eone \u201c[sic] two three\u201d four five\u201d today.", 3, False),
        # The same after a stray mark (#1867 round 7): its quotation is open, so
        # a quotation after punctuation whose first mark opens a nested one
        # reads as two. After whitespace instead, it counts in full.
        ("A stray \u201e mark, then (\u201c\u201cone\u201d two three four five\u201d).", 3, False),
        ('\u201e :\u201c\u201cthe\u201d the\u201d ', 1, False),
        ('\u201e \u2014\u201c\u201cthe\u201d the\u201d ', 1, False),
        ('\u201e /\u201c\u201cthe\u201d the\u201d ', 1, False),
        ('\u201e \u201c\u201cthe\u201d the\u201d ', 2, False),
        ("A stray \u201e mark, then \u201c\u201cone\u201d two three four five\u201d.", 7, True),
        # Intended (#1867 round 6): \u2018\u2026\u2019 nested in a double quotation is read
        # conservatively, so a later word-end apostrophe stretches it; nested
        # in \u00ab\u2026\u00bb, which the refusal recommends, it counts exactly.
        ("It wrote \u201cone \u2018two\u2019 three\u201d then denied workers\u2019 claims.", 6, True),
        ("It wrote \u201cone \u00abtwo\u00bb three\u201d then denied workers\u2019 claims.", 3, False),
        ("'a\"b\u00ab\"\u00bb", 2, False),
        # Only the standard reading reaches these counts (#1867 round 7's
        # mutation run): strict doesn't open the glued \u201e or ", nested runs the
        # first quotation to the end, and the one-pass reading's single span
        # takes the opener after it. Without the standard reading each fails open.
        ("'a\u201eone \u201e two three\u201d\"four five", 5, True),
        ("'a\"one two \u00bb(three\"\u2033four five", 5, True),
        # Known limit (#1867 round 4, accepted by ruling): a quotation whose
        # opening mark directly follows a letter or digit, where that mark can
        # also close (a single mark, or ” » › ″ “ « ‹), isn't
        # counted. It is one of the two fail-opens the scanner accepts;
        # changing it is a deliberate decision. Main's floor still reads a
        # glued “, and marks that only open (" „ 「 …) open anywhere.
        ("It wrote x'one two three four five'", 0, False),
        ("It wrote x\u00abone two three four five\u00bb", 0, False),
        ("It wrote x\u201cone two three four five\u201d", 5, True),
        ('It wrote x"one two three four five"', 5, True),
        # Plain prose: apostrophes inside or at the end of a word, inch marks
        # and footnote marks open nothing.
        ("Since the 1990s the clerks in each county office have handled the clerks' files", 0, False),
        ("The agency's reply was brief; it's 6'7 wide, 6\u2033 deep, and the workers' union\u2019s 2026 note\u00b9 agrees.", 0, False),
        ("A 6\u201d gap and four more words here", 0, False),
        ("The department's letter calls the fee 'reasonable'.", 1, False),
        # Intended (#1867 round 4): single marks are read conservatively, from
        # the first that may open to the last that may close, so a description
        # that quotes with single marks and has a later word-end apostrophe, a
        # second single quotation, or an elided year with a later apostrophe
        # is read as one quotation. tools/README.md and the refusal say to use
        # double quotation marks then, which are counted exactly.
        ("Since the '90s the clerks in each county office have handled the clerks' files", 11, True),
        ("The agency called it 'routine' and won't reopen the workers' case.", 6, True),
        ("The agency called it \"routine\" and won't reopen the workers' case.", 1, False),
        ("'one' and 'two three four'", 5, True),
        ('"one" and "two three four"', 4, False),
        # A stray mark leaves a quotation open; a mark after a colon or a slash
        # still starts one (round 7, from the recognisable-quotation property).
        ('" :"one two three four five" ', 5, True),
        ('" /"one two three four five" ', 5, True),
        ('»a /«the the» ', 3, False),
        ('\u00bba :\u00abthe the\u00bb ', 3, False),
        ('\u203aa :\u2039the the\u203a ', 3, False),
        ('\u201e :\u201dthe\u201d ', 1, False),
        ('\u00ab :\u00bbthe\u00ab ', 1, False),
        ('\uff02 :\uff02the\uff02 ', 1, False),
        ('\u2039 :\u203athe\u2039 ', 1, False),
        ('A 12" form said\uff1a"one two three four five"', 6, True),
        # The colon can lower a count too (#1867 round 7's review): the " after
        # it now starts a nested quotation, so strict doesn't close there, and
        # by the word rule (a whitespace token holding a letter or digit)
        # two:"three is one word. Before the colon fix this counted 5.
        ("'\"one two:\"three four five\"", 4, False),
    ],
)
def test_publication_regressions(tmp_path, description, count, refused):
    assert sc.quoted_words(description) == count
    issues = check(make_repo(tmp_path), entry(unpublished_sources=[{**UNPUBLISHED, "description": description}]))
    assert any("quotes more than 4 words in all" in issue for issue in issues) is refused


def _readme_quotation_examples():
    text = (REPO_ROOT / "tools" / "README.md").read_text()
    section = text.split("### Quotation examples", 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0].startswith("`") and cells[0].endswith("`"):
            rows.append((cells[0][1:-1], int(cells[1]), cells[2] == "yes"))
    return rows


def test_the_readme_quotation_examples_hold():
    # The eng hub's ruling 3: the README states the ambiguous-opener rule with
    # examples, and each example's documented count and refusal is checked
    # here, so the docs can't drift from the code.
    rows = _readme_quotation_examples()
    assert len(rows) >= 25
    for description, counted, refused in rows:
        assert sc.quoted_words(description) == counted, description
        issues: list[str] = []
        sc._check_unpublished_source({**UNPUBLISHED, "description": description}, label="u", issues=issues)
        assert any("quotes more than 4 words in all" in issue for issue in issues) is refused, description


def test_the_refusal_shows_the_span_and_the_remedy(tmp_path):
    description = "The agency called it 'routine' and won't reopen the workers' case."
    issues = check(make_repo(tmp_path), entry(unpublished_sources=[{**UNPUBLISHED, "description": description}]))
    (issue,) = [issue for issue in issues if "quotes more than 4 words in all" in issue]
    assert "(6, counted in \"routine' and won't reopen the workers\")" in issue
    assert 'one style of double quotation marks ("\u2026" or \u201c\u2026\u201d), nesting with \u00ab\u2026\u00bb if needed and never in the same marks; those are counted exactly in plain prose' in issue
    assert "Describe it instead" in issue
    long = "It wrote '" + " ".join(["word"] * 40) + "'"
    (issue,) = [issue for issue in check(make_repo(tmp_path), entry(unpublished_sources=[{**UNPUBLISHED, "description": long}]))
                if "quotes more than" in issue]
    assert "(40, counted in \"" + "word " * 16 + "\u2026\")" in issue  # shortened to 80 characters


def test_delimited_readings():
    assert sc._opens_delimited("x \u201done", 2) is True
    assert sc._opens_delimited("6\u201d tall", 1) is False
    assert sc._opens_delimited("x \u201d y", 2) is False
    assert sc._opens_delimited("\u00bbone", 0) is True
    assert sc._opens_delimited("x\u00bbone", 1) is False
    # “ also closes „, so glued to a word it opens nothing (main's floor still
    # reads it there); after a space it opens.
    assert sc._opens_delimited("x\u201cone", 1) is False
    assert sc._opens_delimited("x \u201cone", 2) is True
    assert sc._opens_delimited("x\u201eone", 1) is True  # „ only opens
    # « with a space after it opens (French spacing), in each reading.
    assert sc._delimited("\u00ab oui \u00bb") == ([(0, " oui ")], [(0, 7)])
    # The strict reading skips a closer that starts a quotation (the “
    # after a stray „) and closes at the next.
    assert sc._delimited("\u201ex \u201cone two\u201d", "strict") == ([(0, "x \u201cone two")], [(0, 12)])
    # The strict reading opens after an opener prefix and closes at a word's end.
    assert sc._delimited('6" and "a b"', "strict") == ([(7, "a b")], [(7, 12)])
    assert sc._delimited('6" and "a b"') == ([(1, " and "), (11, "")], [(1, 8), (11, 12)])
    # The nested reading counts an asymmetric pair's own marks as brackets.
    nested = "\u201ca \u201cb\u201d c\u201d d"
    assert sc._delimited(nested, "nested") == ([(0, "a \u201cb\u201d c")], [(0, 9)])
    assert sc._delimited(nested) == ([(0, "a \u201cb")], [(0, 6)])
    assert sc._delimited("\u201ca \u201cb", "nested") == ([(0, "a \u201cb")], [(0, 5)])


def test_quoted_spans_finds_each_closer_once(monkeypatch):
    # #1825 round-3 review (P3): unclosed openers made the scan quadratic
    # (24,000 characters took 6 s). Each mark is now tested as a closer at
    # most once a reading.
    calls = []
    real = sc._closes_single
    monkeypatch.setattr(sc, "_closes_single", lambda text, index: calls.append(index) or real(text, index))
    text = "'a " * 20_000 + "end'"
    assert sc.quoted_spans(text) == [text[1:-1]]
    assert len(calls) <= text.count("'")
    calls.clear()
    assert sc.quoted_spans("'a " * 20_000) == []
    assert len(calls) <= 20_000


@pytest.mark.parametrize(
    ("opening", "closing"),
    [
        ('"', '"'), ("\u201c", "\u201d"), ("\u201e", "\u201c"), ("\u201e", "\u201d"), ("\u201a", "\u2018"), ("\u201a", "\u2019"), ("\u201f", "\u201d"), ("\u2e42", "\u201c"), ("\u2e42", "\u201d"),
        ("\u00ab", "\u00bb"), ("\u2039", "\u203a"), ("\u00bb", "\u00ab"), ("\u00bb", "\u00bb"), ("\u203a", "\u2039"), ("\u203a", "\u203a"), ("\u201d", "\u201d"),
        ("\u300c", "\u300d"), ("\u300e", "\u300f"), ("\ufe41", "\ufe42"), ("\ufe43", "\ufe44"), ("\uff62", "\uff63"), ("\u301d", "\u301e"), ("\u301d", "\u301f"), ("\uff02", "\uff02"),
        ("\u2033", "\u2033"), ("\u2036", "\u2033"), ("\u275d", "\u275e"), ("\u2760", "\u275e"), ("\u276e", "\u276f"), ("\U0001f676", "\U0001f677"), ("\U0001f678", "\U0001f676"), ("\U0001f678", "\U0001f677"),
    ],
)
@pytest.mark.parametrize("closed", [True, False])
@pytest.mark.parametrize("include_other_closer", [True, False])
def test_delimited_quotations(tmp_path, opening, closing, closed, include_other_closer):
    # Another pair's closer remains literal inside this delimited region,
    # including when this pair's own closer is missing entirely.
    other_closer = "\u201d" if closing == '"' else '"'
    words = "one two three four five" + (f" {other_closer} six" if include_other_closer else "")
    description = "It wrote " + opening + words + (closing if closed else "")
    assert sc.quoted_spans(description) == [words]
    # main's scanner reads " and “ too, counting a stray mark inside as a
    # word, and its count is the floor.
    expected = len(words.split()) if opening in ('"', "\u201c") else len([word for word in words.split() if any(char.isalnum() for char in word)])
    assert sc.quoted_words(description) == expected
    issues = check(make_repo(tmp_path), entry(unpublished_sources=[{**UNPUBLISHED, "description": description}]))
    assert any("quotes more than 4 words in all" in issue for issue in issues)


@pytest.mark.parametrize("opening", ["'", "\u2018", "\uff07", "\u2019", "\u201b", "\u2032", "\u2035", "\u275b", "\u275f"])
@pytest.mark.parametrize("closing", ["'", "\u2019", "\uff07", "\u2018", "\u2032", "\u275c"])
def test_single_quote_combinations(tmp_path, opening, closing):
    words = "one two three four five"
    description = f"It wrote {opening}{words}{closing}"
    assert sc.quoted_spans(description) == [words]
    assert any(
        "quotes more than 4 words in all" in issue
        for issue in check(make_repo(tmp_path), entry(unpublished_sources=[{**UNPUBLISHED, "description": description}]))
    )


@pytest.mark.parametrize(
    ("description", "spans", "count", "refused"),
    [
        # P1: pass 1 preserves the nine-word double quotation even when an
        # outer opener follows a newly recognised no-break-space prefix.
        ("It wrote:\u00a0'about \"the workers' policy is to deny every such claim\"'",
         ["about  ", "the workers' policy is to deny every such claim"], 10, True),
        # P2: trailing whitespace no longer disables a closing single mark.
        ("It wrote 'one two three four five '", ["one two three four five "], 5, True),
        # P2: a plural possessive inside a quotation stays in it.
        ("It wrote 'the workers' policy is to deny every such claim'",
         ["the workers' policy is to deny every such claim"], 9, True),
        ("It wrote \u2018the workers\u2019 policy is to deny every such claim\u2019",
         ["the workers\u2019 policy is to deny every such claim"], 9, True),
        # Round 2's documented limits, counted since round 4.
        ("It wrote \u2018one two three four five\u201d", ["one two three four five"], 5, True),
        ("It wrote \u2032one two three four five\u2032", ["one two three four five"], 5, True),
        ("It wrote \u2033one two three four five\u2033", ["one two three four five"], 5, True),
        ("It wrote '30 days or more for every claim'", ["30 days or more for every claim"], 7, True),
    ],
)
def test_publication_quote_review_regressions(tmp_path, description, spans, count, refused):
    assert sc.quoted_spans(description) == spans
    assert sc.quoted_words(description) == count
    issues = check(make_repo(tmp_path), entry(unpublished_sources=[{**UNPUBLISHED, "description": description}]))
    assert any("quotes more than 4 words in all" in issue for issue in issues) is refused


@pytest.mark.parametrize(
    ("description", "spans"),
    [
        # A pass-1 single mark cannot split the outer span as an opener.
        ("'outside \"word 'inside\" tail'", ["outside   tail", "word 'inside"]),
        # A pass-1 single mark cannot truncate the outer span as a closer.
        ("'outside \"word'\" tail'", ["outside   tail", "word'"]),
        # Multiple delimited regions are removed separately; their contents
        # are still returned once, in opening-mark order.
        ("'one \"two\" three \u00abfour\u00bb five'", ["one   three   five", "two", "four"]),
        # Eligible-looking single marks within pass 1 are never scanned.
        ("\"one 'two' three\"", ["one 'two' three"]),
        # An unclosed delimited region consumes the putative outer closer.
        ("'one \"two' three", ["two' three"]),
    ],
)
def test_single_quotations_do_not_count_delimited_regions_twice(description, spans):
    assert sc.quoted_spans(description) == spans


@pytest.mark.parametrize(
    ("values", "index", "expected"),
    [([], 0, None), ([0, 2, 4], -1, 0), ([0, 2, 4], 0, 2), ([0, 2, 4], 1, 2), ([0, 2, 4], 2, 4), ([0, 2, 4], 4, None)],
)
def test_next_after_is_exact(values, index, expected):
    assert sc._next_after(values, index) == expected


class _CountedPositions:
    def __init__(self, size):
        self.size = size
        self.accesses = 0

    def __len__(self):
        return self.size

    def __getitem__(self, index):
        self.accesses += 1
        if not 0 <= index < self.size:
            raise IndexError(index)
        return index * 2


@pytest.mark.parametrize("index", [-1, 0, 100_000, 199_998, 200_000])
def test_next_after_uses_logarithmic_accesses(index):
    # Count sequence accesses so a linear lookup mutant fails deterministically.
    size = 100_000
    positions = _CountedPositions(size)
    expected = min(size, max(0, index // 2 + 1))
    assert sc._next_after(positions, index) == (2 * expected if expected < size else None)
    assert positions.accesses <= 2 * math.ceil(math.log2(size)) + 4


def test_every_successor_lookup_is_bounded(monkeypatch):
    # #1867 review round 2 (P2): a linear search for the closer kept every
    # result, so only its running time showed it. The one-pass readings (under
    # this scan's openers and main's) and the main floor find each opener's
    # closer through _next_after (bounded above), once per opener: three
    # lookups per opener on this family. A mutant that searches the closers
    # itself makes fewer calls and fails.
    size = 20_000
    text = "a' " * size + "'a " * size
    calls = []
    real = sc._next_after
    monkeypatch.setattr(sc, "_next_after", lambda positions, index: calls.append(index) or real(positions, index))
    assert sc.quoted_words(text) == 0
    assert len(calls) == 3 * size
    calls.clear()
    closers = [index for index, mark in enumerate(text) if mark == "'" and sc._closes_single(text, index)]
    assert sc._one_pass_words(text, closers) == 0 and len(calls) == size
    calls.clear()
    assert sc._main_words(text) == 0 and len(calls) == size


class _CountedSearch:
    """A compiled pattern whose searches are counted."""

    def __init__(self, pattern, counter):
        self.pattern, self.counter = pattern, counter

    def search(self, *args):
        self.counter["search"] += 1
        return self.pattern.search(*args)


_PATHOLOGICAL = {
    "unclosed-singles": lambda n: "'a " * n,
    "closers-then-openers": lambda n: "a' " * n + "'a " * n,
    "unclosed-doubles": lambda n: '"a ' * n,
    "unclosed-nested": lambda n: "\u201ca " * n,
    "deep-guillemets": lambda n: "\u00aba \u00abb " * n,
    "strict-skips": lambda n: "\u201ea \u201db " * n,
    "inch-marks": lambda n: '6" "a ' * n,
    "alternating-regions": lambda n: "'a' \"b\" " * n,
    "spaced-singles": lambda n: "' a " * n,
}


@pytest.mark.parametrize("family", sorted(_PATHOLOGICAL))
def test_quote_scan_work_is_linear(monkeypatch, family):
    # #1867 review round 3 (P2) and the round-4 ruling: a deterministic bound
    # on the scan's work, so a quadratic regression fails here whatever the
    # machine's speed. Work is every call to the mark predicates and every
    # pattern search; doubling the text must not much more than double it,
    # and it stays under a fixed multiple of the length.
    counter = {"search": 0}
    for name in ("_opens_single", "_closes_single", "_opens_delimited", "_glued", "_starts_a_quotation", "_opens_strict"):
        real = getattr(sc, name)
        monkeypatch.setattr(sc, name, lambda *args, _real=real, _name=name: counter.__setitem__(_name, counter.get(_name, 0) + 1) or _real(*args))
    monkeypatch.setattr(sc, "_DELIMITER_MARK", _CountedSearch(sc._DELIMITER_MARK, counter))
    monkeypatch.setattr(sc, "_DELIMITER_CLOSE", {mark: _CountedSearch(pattern, counter) for mark, pattern in sc._DELIMITER_CLOSE.items()})

    def work(n):
        counter.clear()
        counter["search"] = 0
        text = _PATHOLOGICAL[family](n)
        sc.quoted_reading(text)
        return sum(counter.values()), len(text)

    small, length = work(2_000)
    large, _ = work(4_000)
    assert large <= 2.2 * small + 100, (family, small, large)
    assert small <= 40 * length, (family, small, length)


@pytest.mark.parametrize(
    "text",
    [
        "a' " * 40_000 + "'a " * 40_000,
        "'a " * 80_000,
        '"a ' * 80_000,
        "\u201ea " * 80_000,
        "\u201ca " * 80_000,
        "\u201ca\u201d " * 60_000,
        "'a' \"b\" " * 30_000,
        '6" "a ' * 40_000,
    ],
    ids=["closers-then-openers", "unclosed-singles", "unclosed-doubles", "unclosed-low-doubles", "unclosed-nested",
         "closed-doubles", "alternating-regions", "inch-marks"],
)
def test_quote_scans_stay_fast(text):
    # Coarse wall-clock guard on families that are quadratic under a linear
    # lookup or a rescanned region: each scan of about 240,000 characters
    # takes well under a second.
    import time

    started = time.perf_counter()
    sc.quoted_words(text)
    assert time.perf_counter() - started < 10


# ---------------------------------------------------------------------------
# Adopting modules and the reverse scan


def adopted_entry():
    value = entry()
    del value["pending_texts"]
    value["adopted_by"] = [{"module": "us/statutes/42/403/a/5.yaml", "interpretation": "family-maximum-saving-clause"}]
    return value


def test_adopting_module_carries_the_entry_unchanged(tmp_path):
    ctx = make_repo(tmp_path)
    value = adopted_entry()
    write_module(ctx, "us/statutes/42/403/a/5.yaml", [sc.to_module_interpretation(value, interpretation_id=value["id"], affects=["rule_a"])])
    assert check(ctx, value) == []


def test_adopting_module_drift_is_reported_per_field(tmp_path):
    ctx = make_repo(tmp_path)
    value = adopted_entry()
    carried = sc.to_module_interpretation(value, interpretation_id=value["id"], affects=["rule_a"])
    carried["reading"] = "Something else."
    carried["texts"] = []
    write_module(ctx, "us/statutes/42/403/a/5.yaml", [carried])
    issues = check(ctx, value)
    assert any("`reading` differs" in issue for issue in issues)
    assert any("`texts` differs" in issue for issue in issues)


def test_adopting_module_failures(tmp_path):
    ctx = make_repo(tmp_path)
    value = adopted_entry()
    assert any("does not exist" in issue for issue in check(ctx, value))
    write_module(ctx, "us/statutes/42/403/a/5.yaml", [])
    assert any("has no module.interpretations entry" in issue for issue in check(ctx, value))
    carried = sc.to_module_interpretation(value, interpretation_id=value["id"], affects=["no_such_rule"])
    carried["jurisdiction"] = "us"
    write_module(ctx, "us/statutes/42/403/a/5.yaml", [carried])
    issues = check(ctx, value)
    assert any("affects `no_such_rule`, which is not a rule" in issue for issue in issues)
    assert any("unknown key `jurisdiction`" in issue for issue in issues)


def test_adopted_by_paths_and_pending_texts(tmp_path):
    ctx = make_repo(tmp_path)
    bad = entry(adopted_by=[{"module": "tools/x.yaml", "interpretation": "x"}])
    issues = check(ctx, bad)
    assert any("must be a RuleSpec module path in this repository" in issue for issue in issues)
    assert any("still has pending_texts" in issue for issue in issues)
    test_file = adopted_entry()
    test_file["adopted_by"][0]["module"] = "us/statutes/42/403/a/5.test.yaml"
    assert any("must be a RuleSpec module path" in issue for issue in check(ctx, test_file))


def tension(status="open", interpretation_id="two-provisions"):
    value = {
        "id": interpretation_id,
        "question": "q",
        "texts": [
            {"corpus_citation_path": "us/statute/42/403/a/5", "excerpt": "x"},
            {"corpus_citation_path": "us/regulation/20/404/403", "excerpt": "y"},
        ],
        "reading": "r",
        "alternatives": [{"reading": "s"}],
        "basis": "b",
        "status": status,
        "affects": ["rule_a"],
    }
    if status != "open":
        value["ruling"] = {"by": "Axiom Foundation", "date": "2026-10-12", "record": "https://github.com/x/y/pull/1"}
    return value


def test_unregistered_open_tension_only_warns(tmp_path):
    ctx = make_repo(tmp_path)
    single = {**tension(), "id": "one-provision", "texts": tension()["texts"][:1]}
    write_module(ctx, "us/statutes/42/403/a/5.yaml", [tension(), single])
    assert check(ctx) == []
    failures, warnings = sc.unregistered_tensions(ctx.root, {"version": 1, "entries": []})
    assert failures == []
    assert len(warnings) == 1 and "two-provisions (open) records provisions in tension" in warnings[0]


@pytest.mark.parametrize("status", ["ruled", "confirmed", "contradicted"])
def test_unregistered_decided_tension_fails(tmp_path, status):
    ctx = make_repo(tmp_path)
    write_module(ctx, "us/statutes/42/403/a/5.yaml", [tension(status)])
    issues = check(ctx)
    assert len(issues) == 1 and f"two-provisions ({status}) records provisions in tension" in issues[0]
    assert check(ctx, scan=False) == []


def test_check_cli_writes_warnings(tmp_path, capsys):
    ctx = make_repo(tmp_path)
    write_module(ctx, "us/statutes/42/403/a/5.yaml", [tension()])
    (ctx.root / sc.REGISTER_FILENAME).write_text("version: 1\nentries: []\n")
    out = tmp_path / "warnings.txt"
    assert sc.main(["check", "--root", str(ctx.root), "--warnings-file", str(out)]) == 0
    assert out.read_text().count("\n") == 1 and "two-provisions (open)" in out.read_text()
    assert "1 unregistered open interpretation(s)" in capsys.readouterr().out


def test_registered_tension_is_not_reported(tmp_path):
    ctx = make_repo(tmp_path)
    value = adopted_entry()
    value["texts"].append({"corpus_citation_path": "us/regulation/20/404/403", "excerpt": "y"})
    write_module(ctx, "us/statutes/42/403/a/5.yaml", [sc.to_module_interpretation(value, interpretation_id=value["id"], affects=["rule_a"])])
    assert check(ctx, value) == []


# ---------------------------------------------------------------------------
# Hygiene


@pytest.mark.parametrize(
    "text",
    [
        "Ruled in d1338.",
        "See local_6085d52a-863b for context.",
        "Copied from /Users/someone/notes.md",
        "Copied from ~/notes.md",
        "Ask someone@example.org",
    ],
)
def test_hygiene_flags_private_material(tmp_path, text):
    assert any("the register is public" in issue for issue in check(make_repo(tmp_path), entry(basis=text)))


def test_hygiene_ignores_hashes_and_urls(tmp_path):
    value = entry()
    value["pending_texts"][0]["snapshot"]["commit"] = "d1338" + "0" * 35
    value["pending_texts"][0]["snapshot"]["sha256"] = "d1418" + "0" * 59
    value["ruling"]["record"] = "https://github.com/PolicyEngine/microcosm-dynamics/pull/530#issuecomment-1"
    assert check(make_repo(tmp_path), value) == []


# ---------------------------------------------------------------------------
# Helpers


def test_python_test_exists():
    source = (
        "import pytest\n"
        "def test_a():\n    pass\n"
        "async def test_b():\n    pass\n"
        "class TestC:\n    def test_d(self):\n        pass\n"
        "@pytest.mark.parametrize('x', [pytest.param(1, id='one')])\n"
        "def test_e(x):\n    pass\n"
    )
    assert sc.python_test_exists(source, "test_a")
    assert sc.python_test_exists(source, "test_b")  # defined; whether it runs is the runner's to say
    assert sc.python_test_exists(source, "TestC::test_d")
    assert sc.python_test_exists(source, "test_e")
    assert not sc.python_test_exists(source, "test_e[one]")  # case ids are never pinned
    assert not sc.python_test_exists(source, "test_d")  # method, not module level
    assert not sc.python_test_exists(source, "TestC::test_a")
    assert not sc.python_test_exists("def broken(:\n", "broken")


def test_yaml_test_case_names():
    assert sc.yaml_test_case_names(yaml.safe_dump([{"name": "a"}, {"name": "b"}, "junk"])) == {"a", "b"}
    assert sc.yaml_test_case_names(yaml.safe_dump({"cases": [{"name": "c"}]})) == {"c"}
    assert sc.yaml_test_case_names(": : :") == set()


def test_snapshot_text_strips_markup():
    data = b"<html><head><style>p{}</style><script>var x='<p>hidden</p>';</script></head><body><p>A&nbsp;rule &amp; its\n\n  <b>exception</b>&#8217;s text</p></body></html>"
    assert sc.snapshot_text(data, "x.html") == "A rule & its exception’s text"
    assert sc.snapshot_text(b"<P>Block one</P><P>block <E T=\"03\">two</E><SU>1</SU></P>", "x.xml") == "Block one block two1"
    assert sc.snapshot_text(b"plain\n text ", "x.txt") == "plain text"
    with pytest.raises(ValueError):
        sc.snapshot_text(b"%PDF", "x.pdf")


def test_repo_jurisdiction_ok():
    assert sc.repo_jurisdiction_ok("TheAxiomFoundation/rulespec-us", "us")
    assert sc.repo_jurisdiction_ok("TheAxiomFoundation/rulespec-us", "us-co")
    assert sc.repo_jurisdiction_ok("TheAxiomFoundation/rulespec-uk", "uk-babergh")
    assert not sc.repo_jurisdiction_ok("TheAxiomFoundation/rulespec-us", "uk")
    assert not sc.repo_jurisdiction_ok("TheAxiomFoundation/rulespec-us", "usx")
    assert not sc.repo_jurisdiction_ok("TheAxiomFoundation/axiom-corpus", "us")


# ---------------------------------------------------------------------------
# verify, with a fake network


class FakeNet:
    def __init__(self, files):
        self.files = files

    def __call__(self, repo, commit, path):
        try:
            return self.files[(repo, commit, path)]
        except KeyError:
            raise OSError(f"404 {repo}@{commit}:{path}") from None


def substring(source_text, excerpt):
    return excerpt in source_text


def verified_inputs():
    value = entry()
    snapshot = b"<p>Total family payment is less after the PIA increase than it was before.</p>"
    value["pending_texts"][0]["snapshot"]["sha256"] = hashlib.sha256(snapshot).hexdigest()
    files = {
        ("PolicyEngine/microcosm-dynamics", COMMIT, "tests/data/poms_rs_00630_400.html"): snapshot,
        ("PolicyEngine/microcosm-dynamics", COMMIT, "src/gross_benefits.py"): b"def g():\n    pass\n",
        ("PolicyEngine/microcosm-dynamics", COMMIT, "tests/test_g.py"): (
            b"import pytest\n"
            b"def test__given_operational__then_pays():\n    pass\n"
            b"class TestLiteral:\n"
            b"    @pytest.mark.parametrize('case', ['child-ages-out'])\n"
            b"    def test_refuses(self, case):\n        pass\n"
        ),
    }
    corpus = {"us/statute/42/403/a/5": "... the benefit for any such subsequent month shall be ..."}
    return {"version": 1, "entries": [value]}, FakeNet(files), corpus


def test_verify_passes_and_reports_lag_and_uncited():
    payload, net, corpus = verified_inputs()
    issues, report = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get)
    assert issues == []
    assert report[0] == "verified: 1 texts, 1 pending texts, 1 implementations, 2 tests"
    assert any(line.startswith("uncited:") for line in report)
    assert "lags: us:family-maximum-saving-clause (entries[0]).implementations[0] follows every-later-month, not the reading it adopts (reading)" in report


def test_verify_lag_is_measured_against_what_the_consumer_adopts():
    payload, net, corpus = verified_inputs()
    implementation = payload["entries"][0]["implementations"][0]
    implementation["adopts"] = "every-later-month"
    implementation["basis"] = "Follows the statute."
    issues, report = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get)
    assert issues == []
    assert not any(line.startswith("lags:") for line in report)
    implementation["follows"] = "reading"
    _, report = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get)
    assert any("follows reading, not the reading it adopts (every-later-month)" in line for line in report)


def test_verify_lists_unpublished_sources_as_unverifiable():
    payload, net, corpus = verified_inputs()
    payload["entries"][0]["unpublished_sources"] = [dict(UNPUBLISHED)]
    issues, report = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get)
    assert issues == []
    assert any(line.startswith("unverifiable:") and "MN DHS correspondence" in line for line in report)


def test_verify_findings():
    payload, net, corpus = verified_inputs()
    value = payload["entries"][0]
    value["texts"][0]["excerpt"] = "for every subsequent month"
    value["pending_texts"][0]["excerpt"] = "Total family payment is more"
    value["implementations"][0]["cites_entry"] = True
    value["tests"][0]["name"] = "test_missing"
    issues, _ = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get)
    assert any("not verbatim at us/statute/42/403/a/5" in issue for issue in issues)
    assert any("not verbatim in tests/data/poms_rs_00630_400.html" in issue for issue in issues)
    assert any("cites_entry is true but the file does not contain" in issue for issue in issues)
    assert any("test_missing is not a test function defined in PolicyEngine/microcosm-dynamics@" in issue for issue in issues)


def test_verify_reads_a_test_file_by_its_coding_cookie():
    # Review of #1710 round 2: a non-UTF-8 test file made the tool raise.
    payload, net, corpus = verified_inputs()
    net.files[("PolicyEngine/microcosm-dynamics", COMMIT, "tests/test_g.py")] = (
        b"# -*- coding: latin-1 -*-\n"
        b"import pytest\n"
        b"def test__given_operational__then_pays():\n    assert '\xe9'\n"
        b"class TestLiteral:\n"
        b"    def test_refuses(self):\n        pass\n"
    )
    issues, report = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get)
    assert issues == []
    assert report[0].endswith("2 tests")


def test_verify_sha_mismatch_unresolved_and_no_corpus():
    payload, net, _ = verified_inputs()
    payload["entries"][0]["pending_texts"][0]["snapshot"]["sha256"] = SHA
    issues, _ = sc.verify_register(payload, fetch=net, matches=substring, resolve={}.get)
    assert any("snapshot sha256 is" in issue for issue in issues)
    assert any("is not in the pinned corpus release" in issue for issue in issues)
    issues, _ = sc.verify_register(payload, fetch=net, matches=substring, resolve=None)
    assert any("not verified; no pinned corpus release" in issue for issue in issues)


def test_verify_cites_entry_true_when_file_cites():
    payload, net, corpus = verified_inputs()
    key = ("PolicyEngine/microcosm-dynamics", COMMIT, "src/gross_benefits.py")
    net.files[key] = b"# Source conflict us:family-maximum-saving-clause\n"
    issues, _ = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get)
    assert any("cites_entry is false but the file contains" in issue for issue in issues)
    payload["entries"][0]["implementations"][0]["cites_entry"] = True
    assert sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get)[0] == []


def test_verify_unreadable_files():
    payload, _, corpus = verified_inputs()
    issues, _ = sc.verify_register(payload, fetch=FakeNet({}), matches=substring, resolve=corpus.get)
    assert sum("cannot read" in issue for issue in issues) == 4


# ---------------------------------------------------------------------------
# aggregate


def test_aggregate_rows_and_collisions():
    us = {"version": 1, "entries": [entry(), entry(id="other", jurisdiction="us-co")]}
    uk = {"version": 1, "entries": [entry(jurisdiction="uk-babergh"), entry(id="misplaced", jurisdiction="us")]}
    rows, issues = sc.aggregate({"TheAxiomFoundation/rulespec-uk": uk, "TheAxiomFoundation/rulespec-us": us})
    ids = [row["global_id"] for row in rows]
    assert len(ids) == len(set(ids))
    assert "uk-babergh:family-maximum-saving-clause" in ids and "us:family-maximum-saving-clause" in ids
    assert issues == ["TheAxiomFoundation/rulespec-uk: us:misplaced has a jurisdiction outside that repository."]
    rows, issues = sc.aggregate({"TheAxiomFoundation/rulespec-us": us, "TheAxiomFoundation/rulespec-us-dup": us})
    assert any("is in both" in issue for issue in issues)
    markdown = sc.render_markdown(rows)
    assert markdown.startswith("# Source conflicts across Axiom registers")
    assert "21.00 USD/month" in markdown


def test_aggregate_carries_years_kinds_conflict_and_adopts():
    value = entry(years={"from": 2022, "to": 2025, "type": "tax"}, unpublished_sources=[dict(UNPUBLISHED)])
    value["implementations"][0]["adopts"] = "every-later-month"
    rows, issues = sc.aggregate({"TheAxiomFoundation/rulespec-us": {"version": 1, "entries": [value]}})
    assert issues == []
    row = rows[0]
    assert row["years"] == {"from": 2022, "to": 2025, "type": "tax"}
    assert row["conflict"] == "live"
    assert row["source_kinds"] == ["agency-practice", "manual", "statute"]
    assert row["alternatives"] == [{"id": "every-later-month", "reading": "Protect every later month."}]
    assert row["implementations"][0]["adopts"] == "every-later-month"
    markdown = sc.render_markdown(rows)
    assert "2022\u20132025 (tax)" in markdown
    assert "agency-practice, manual, statute" in markdown
    # Review of #1825 (P3): the Markdown view carries alternative ids and what
    # each consumer follows and adopts, as the JSON rows do.
    assert "PolicyEngine/microcosm-dynamics: follows `every-later-month`, adopts `every-later-month`" not in markdown
    assert "PolicyEngine/microcosm-dynamics: follows `every-later-month` |" in markdown
    value["implementations"][0]["adopts"] = "reading"
    value["alternatives"].append({"id": "only-in-alternatives", "reading": "Another reading."})
    markdown = sc.render_markdown(sc.aggregate({"TheAxiomFoundation/rulespec-us": {"version": 1, "entries": [value]}})[0])
    row = next(line for line in markdown.splitlines() if line.startswith("| `us:"))
    cells = [cell.strip() for cell in row.split(" | ")]
    assert cells[7] == "`every-later-month`, `only-in-alternatives`"  # the Alternatives column
    assert cells[8] == "PolicyEngine/microcosm-dynamics: follows `every-later-month`, adopts `reading`"


def test_citation_label():
    assert sc.citation_label("us/statute/42/403/f/1") == "42 U.S.C. 403(f)(1)"
    assert sc.citation_label("us/statute/26/25A") == "26 U.S.C. 25A"
    assert sc.citation_label("us/regulation/20/404/435") == "20 CFR 404.435"
    assert sc.citation_label("us/regulation/7/273/24/a") == "7 CFR 273.24(a)"
    assert sc.citation_label("uk-babergh/manual/scheme/page-87") == "uk-babergh/manual/scheme/page-87"
    assert sc.citation_label("us/statute/hts/chapter-99") == "us/statute/hts/chapter-99"


def test_aggregate_sources_are_unique_citations():
    value = entry()
    value["pending_texts"].append(dict(value["pending_texts"][0]))
    rows, _ = sc.aggregate({"TheAxiomFoundation/rulespec-us": {"entries": [value]}})
    assert rows[0]["sources"] == ["42 U.S.C. 403(a)(5)", "POMS RS 00630.400"]


def test_aggregate_cli_with_local_registers(tmp_path, capsys):
    path = tmp_path / "r.yaml"
    path.write_text(yaml.safe_dump({"version": 1, "entries": [entry()]}))
    out = tmp_path / "rows.json"
    assert sc.main(["aggregate", "--register", f"TheAxiomFoundation/rulespec-us={path}", "--json", str(out)]) == 0
    assert '"global_id": "us:family-maximum-saving-clause"' in out.read_text()


# ---------------------------------------------------------------------------
# Proposed implementations and shipped commits

PROPOSED = {
    "repo": "PolicyEngine/policyengine-us",
    "pr": "https://github.com/PolicyEngine/policyengine-us/pull/10200",
    "path": "policyengine_us/variables/gov/states/hi/tax/income/claim_of_right/hi_claim_of_right_deduction.py",
    "follows": "reading",
}


@pytest.mark.parametrize(
    ("change", "fragment"),
    [
        ({}, None),
        ({"follows": "every-later-month"}, None),
        ({"pr": "https://github.com/PolicyEngine/policyengine-us/issues/10200"}, "pr must be a github.com pull request URL"),
        ({"pr": "http://github.com/PolicyEngine/policyengine-us/pull/1"}, "pr must be a github.com pull request URL"),
        ({"pr": "https://github.com/PolicyEngine/other/pull/1"}, "is a pull request in PolicyEngine/other"),
        ({"follows": "statute"}, "follows names `statute`"),
        ({"path": "/abs/x.py"}, "path must be a relative path"),
        ({"repo": "nope"}, "repo must be owner/name"),
        ({"commit": COMMIT}, "unknown key `commit`"),
    ],
)
def test_proposed_implementations(tmp_path, change, fragment):
    issues = check(make_repo(tmp_path), entry(proposed=[{**PROPOSED, **change}]))
    if fragment is None:
        assert issues == []
    else:
        assert any(fragment in issue for issue in issues), issues


def test_proposed_must_be_a_non_empty_list(tmp_path):
    assert any("proposed must be a non-empty list" in issue for issue in check(make_repo(tmp_path), entry(proposed=[])))


def test_verify_requires_shipped_commits():
    payload, net, corpus = verified_inputs()
    seen = []

    def on_default_branch(repo, commit):
        seen.append((repo, commit))
        return False

    issues, _ = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get, on_default_branch=on_default_branch)
    labels = [issue.split(":")[1] for issue in issues if "is not on" in issue]
    # The snapshot, the implementation and both tests are external commits.
    assert len([issue for issue in issues if "is not on PolicyEngine/microcosm-dynamics's default branch" in issue]) == 4, issues
    assert {repo for repo, _ in seen} == {"PolicyEngine/microcosm-dynamics"}
    assert labels
    shipped, _ = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get, on_default_branch=lambda repo, commit: True)
    assert shipped == []


def test_verify_reports_when_reachability_is_unchecked_or_unknown():
    payload, net, corpus = verified_inputs()
    issues, report = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get)
    assert issues == []
    assert any(line.startswith("unchecked: default-branch reachability") for line in report)

    def broken(repo, commit):
        raise OSError("network down")

    issues, _ = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get, on_default_branch=broken)
    assert any("cannot tell whether" in issue for issue in issues)


def test_verify_lists_proposed_implementations():
    payload, net, corpus = verified_inputs()
    payload["entries"][0]["proposed"] = [dict(PROPOSED)]
    issues, report = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get)
    assert issues == []
    proposed = [line for line in report if line.startswith("proposed:")]
    assert len(proposed) == 1 and "pull/10200" in proposed[0]
    # Review of #1825 (P3): a proposal is listed, never counted as an implementation.
    assert report[0] == "verified: 1 texts, 1 pending texts, 1 implementations, 2 tests"


# ---------------------------------------------------------------------------
# #1844 round 7 review (P3): files read beside the payload


@pytest.mark.parametrize("value", ["2026-02-30", "1" * 5000])
def test_a_value_yaml_cannot_construct_is_a_register_error(tmp_path, capsys, value):
    # PyYAML raises ValueError for an impossible date or an integer too long
    # to convert; the register's readers report it instead of raising.
    path = tmp_path / sc.REGISTER_FILENAME
    path.write_text(f"version: 1\nentries: []\nextra: {value}\n")
    with pytest.raises(sc.RegisterError, match="holds a value YAML cannot construct"):
        sc.load_register(path)
    assert sc.main(["check", "--root", str(tmp_path)]) == 1
    assert sc.main(["verify", "--root", str(tmp_path)]) == 1
    assert "holds a value YAML cannot construct" in capsys.readouterr().err


def test_yaml_test_case_names_is_total():
    assert sc.yaml_test_case_names("- name: a\n  period: 2026-02-30\n") == set()
    assert sc.yaml_test_case_names("[" * 600 + "]" * 600) == set()


def test_a_local_test_that_cannot_be_read_is_an_issue(tmp_path):
    ctx = sc.RepoContext(root=tmp_path, repo=REPO)
    (tmp_path / "tests").mkdir()
    test_file = tmp_path / "tests" / "default.test.yaml"

    def screen():
        issues: list[str] = []
        sc.check_local_test("tests/default.test.yaml", "Local default", label="tests[0]", ctx=ctx, issues=issues)
        return issues

    test_file.write_text("- name: Local default\n  period: 2026\n")
    assert screen() == []
    for text in ("- name: Local default\n  period: 2026-02-30\n", "[" * 600 + "]" * 600):
        test_file.write_text(text)
        assert screen() == ["tests[0].name Local default is not a test case in tests/default.test.yaml."]
    if os.geteuid() != 0:  # root reads a chmod-0 file
        test_file.write_text("- name: Local default\n")
        test_file.chmod(0)
        try:
            assert screen() == ["tests[0].path tests/default.test.yaml cannot be read: Permission denied."]
        finally:
            test_file.chmod(0o644)


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def _fake_github(files):
    """urlopen for discover_registers: an organisation listing with one
    repository per name in `files`, and each repository's raw file (None
    for a repository without one)."""

    def urlopen(target, timeout=None):
        url = target if isinstance(target, str) else target.full_url
        if "/orgs/" in url:
            page = int(urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["page"][0])
            listing = [{"full_name": f"TheAxiomFoundation/{name}", "name": name, "default_branch": "main"} for name in files]
            return _Response(json.dumps(listing if page == 1 else []).encode())
        name = url.split("/")[4]
        if files[name] is None:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        return _Response(files[name])

    return urlopen


@pytest.mark.parametrize("filename", [sc.REGISTER_FILENAME, sc.CHOICES_FILENAME])
def test_discovery_reads_each_repository_on_its_own(monkeypatch, filename):
    # One repository's unreadable file no longer aborts the Axiom-wide view,
    # and an alias cycle can't reach the JSON renderer.
    good = yaml.safe_dump({"version": 1, "entries": []}).encode()
    files = {
        "rulespec-us": good,
        "rulespec-us-co": b"entries: [\n",
        "rulespec-us-mt": b"version: 1\nentries: []\nextra: &a\n  self: *a\n",
        "rulespec-us-ca": b"version: 1\nentries: []\nextra: 2026-02-30\n",
        "rulespec-us-tx": b"\xff\xfe",
        "rulespec-us-ny": None,
    }
    monkeypatch.setattr(sc.urllib.request, "urlopen", _fake_github(files))
    registers, issues = sc.discover_registers(None, filename=filename)
    assert registers == {"TheAxiomFoundation/rulespec-us": {"version": 1, "entries": []}}
    assert len(issues) == 4
    for name in ("rulespec-us-co", "rulespec-us-mt", "rulespec-us-ca", "rulespec-us-tx"):
        assert any(issue.startswith(f"TheAxiomFoundation/{name}: {filename}") for issue in issues), (name, issues)
    rows, _ = sc.aggregate(registers)
    json.dumps(rows, default=sc._json_default)


def test_aggregate_cli_reports_an_unreadable_local_file(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("version: 1\nentries: []\nextra: 2026-02-30\n")
    good = tmp_path / "good.yaml"
    good.write_text(yaml.safe_dump({"version": 1, "entries": [entry()]}))
    out = tmp_path / "rows.json"
    argv = ["aggregate", "--register", f"TheAxiomFoundation/rulespec-us={good}",
            "--register", f"TheAxiomFoundation/rulespec-uk={bad}", "--json", str(out)]
    assert sc.main(argv) == 1
    assert "TheAxiomFoundation/rulespec-uk: " in capsys.readouterr().err
    assert [row["repository"] for row in json.loads(out.read_text())] == ["TheAxiomFoundation/rulespec-us"]
