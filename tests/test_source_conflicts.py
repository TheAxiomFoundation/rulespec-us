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

import copy
import hashlib
import importlib.util
import sys
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


def test_corpus_checkout_keeps_historical_locked_blobs() -> None:
    # actions/checkout makes sparse checkouts blobless. corpus-fetch refuses
    # lazy network reads, so historical git_blob locks need ordinary history.
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/source-conflicts.yml").read_text())
    checkouts = [
        step["with"]
        for step in workflow["jobs"]["verify"]["steps"]
        if step.get("with", {}).get("repository") == "TheAxiomFoundation/axiom-corpus"
    ]
    assert len(checkouts) == 1
    assert checkouts[0].get("fetch-depth") == 0
    assert "sparse-checkout" not in checkouts[0]
    assert "filter" not in checkouts[0]


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
        "alternatives": [{"reading": "Protect every later month.", "effect": "More months refused."}],
        "basis": "SSA's operational chart.",
        "status": "ruled",
        "ruling": {"by": "Axiom Foundation", "date": "2026-10-12", "record": "https://github.com/x/y/pull/1"},
        "outcome": "computed",
        "implementations": [
            {
                "repo": "PolicyEngine/microcosm-dynamics",
                "commit": COMMIT,
                "path": "src/gross_benefits.py",
                "follows": "alternatives[0]",
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
                "pins": ["alternatives[0]"],
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


def proposal_entry(**proposal_overrides):
    value = entry(status="open")
    for key in ("ruling", "implementations", "tests", "money_case"):
        del value[key]
    value["proposed"] = [{
        "repo": "PolicyEngine/policyengine-us",
        "path": "policyengine_us/parameters/example.yaml",
        "follows": "reading",
        "basis": "The unshipped change uses the operational manual pending clarification.",
        **proposal_overrides,
    }]
    return value


@pytest.mark.parametrize("extra", [{}, {"pull_request": "https://github.com/PolicyEngine/policyengine-us/pull/123"}])
def test_proposal_needs_no_shipped_commit_or_test_pin(tmp_path, extra):
    assert check(make_repo(tmp_path), proposal_entry(**extra)) == []


@pytest.mark.parametrize("field", ["repo", "path", "follows", "basis"])
def test_proposal_requires_its_file_and_reason(tmp_path, field):
    value = proposal_entry()
    del value["proposed"][0][field]
    assert any(f".{field} " in issue for issue in check(make_repo(tmp_path), value))


@pytest.mark.parametrize("extra, message", [
    ({"commit": COMMIT}, "unknown key `commit`"),
    ({"cites_entry": True}, "unknown key `cites_entry`"),
    ({"repo": REPO}, ".repo must be an external owner/name"),
    ({"repo": []}, ".repo must be an external owner/name"),
    ({"path": "../outside.py"}, ".path must be a relative path"),
    ({"follows": "alternatives[2]"}, ".follows"),
    ({"basis": ""}, ".basis"),
    ({"basis": "It pays $100."}, "which no money case backs"),
    ({"pull_request": "https://github.com/PolicyEngine/another-repo/pull/123"}, ".pull_request"),
    ({"pull_request": "https://github.com/PolicyEngine/policyengine-us/issues/123"}, ".pull_request"),
])
def test_proposal_rejects_invalid_or_shipped_claims(tmp_path, extra, message):
    assert any(message in issue for issue in check(make_repo(tmp_path), proposal_entry(**extra)))


def test_duplicate_proposed_file_is_rejected(tmp_path):
    value = proposal_entry()
    value["proposed"].append(dict(value["proposed"][0]))
    assert any("repeats (PolicyEngine/policyengine-us," in issue for issue in check(make_repo(tmp_path), value))


@pytest.mark.parametrize("value", [None, {}, "proposal", [], [None], [[]]])
def test_malformed_proposals_are_findings_not_exceptions(tmp_path, value):
    assert check(make_repo(tmp_path), entry(proposed=value))


def test_aggregation_preserves_unshipped_proposals_separately():
    value = proposal_entry()
    rows, issues = sc.aggregate({REPO: {"entries": [value]}})
    assert issues == []
    assert rows[0]["implementations"] == []
    assert rows[0]["proposed"] == value["proposed"]


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
    bad["tests"][1]["pins"] = ["alternatives[3]"]
    bad["implementations"][0]["follows"] = "literal"
    issues = check(ctx, bad)
    assert any("names alternatives[3], which this entry does not have" in issue for issue in issues)
    assert any("follows must be `reading` or `alternatives[N]`" in issue for issue in issues)
    assert sc.reading_index("reading") is None
    assert sc.reading_index("alternatives[12]") == 12
    with pytest.raises(ValueError):
        sc.reading_index("alternatives[01]")


def test_every_followed_reading_is_pinned(tmp_path):
    ctx = make_repo(tmp_path)
    bad = entry()
    bad["tests"] = [bad["tests"][0]]  # pins reading only; the implementation follows alternatives[0]
    assert any("follows alternatives[0], which no test pins" in issue for issue in check(ctx, bad))
    both = entry()
    both["tests"] = [{**both["tests"][0], "pins": ["reading", "alternatives[0]"]}]
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
        {"path": "tests/test_local.py", "name": "TestX::test_y", "pins": ["alternatives[0]"]},
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
    assert any("relative .py or .test.yaml path" in issue for issue in issues)
    assert any("must be a test function" in issue for issue in issues)


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
    assert any(line.startswith("lags:") for line in report)


def test_verify_reports_proposals_without_fetching_or_counting_them():
    payload, net, corpus = verified_inputs()
    payload["entries"][0]["proposed"] = proposal_entry()["proposed"]
    issues, report = sc.verify_register(payload, fetch=net, matches=substring, resolve=corpus.get)
    assert issues == []
    assert report[0] == "verified: 1 texts, 1 pending texts, 1 implementations, 2 tests"
    assert any(line.startswith("proposed:") and "unshipped" in line and "not verified" in line for line in report)


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
