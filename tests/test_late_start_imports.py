"""Tests for tools/late_start_imports.py, the late-start import ratchet.

These run in the repository's pytest leg without an engine build, which is a
required check, so `test_committed_baseline_matches_this_checkout` enforces the
ratchet on every pull request. They cover formula lexing, version parsing,
import scope, edge detection, the baseline file format and the gate's
comparison. The base-bound and engine comparisons run in the late-start-imports
workflow; property-based tests of the same logic live in
test_late_start_imports_properties.py.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL_PATH = REPO_ROOT / "tools" / "late_start_imports.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("late_start_imports", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["late_start_imports"] = module
    spec.loader.exec_module(module)
    return module


lsi = _load_tool()

Y2018 = date(2018, 1, 1)
Y2026 = date(2026, 1, 1)


def _rule(name: str, *versions: tuple[date, str]) -> "lsi.Rule":
    return lsi.Rule(name, tuple(lsi.Version(start, formula) for start, formula in versions))


def _edge(rule="us:a#r", target="us:b#t", version_start=Y2018, target_start=Y2026):
    return lsi.Edge(rule, target, version_start, target_start)


def _edges(modules):
    return lsi.late_start_edges(lsi.import_references(modules))


LATE_TARGET = lsi.Module(rules=(_rule("later_amount", (Y2026, "100")), _rule("other", (Y2018, "7"))))


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("a + b", {"a", "b"}),
        ("max(a, b)", {"a", "b"}),
        ("max (a)", {"a"}),
        ("table[size]", {"table", "size"}),
        ("sum(members.wages)", {"members", "wages"}),
        ('if "a" == b: 1 else: 2', {"b"}),
        ("'a' + b", {"b"}),
        ('"it\\"s a" + b', {"b"}),
        ("1 # a\n+ b", {"b"}),
        ('"""a\nb""" + c', {"c"}),
        ('"""a', set()),
        ("a/b + c", {"c"}),
        ("a / b", {"a", "b"}),
        ("2018-01-01", set()),
        ("1_000 + a", {"a"}),
        ("2018_a", {"a"}),
        ("if a and not b: true else: False", {"a", "b"}),
        ("period_start + period_end", set()),
        ("match a:\n  1 => b\n  _ => c", {"a", "b", "c", "_"}),
        ("", set()),
    ],
)
def test_formula_references_follow_the_engine_lexer(formula, expected):
    assert lsi.formula_references(formula) == expected


def test_parse_module_reads_both_date_spellings():
    module = lsi.parse_module(
        """
imports:
  - us:b#t
rules:
  - name: long_form
    kind: derived
    versions:
      - effective_from: 2018-01-01
        formula: a
  - name: alias_form
    kind: parameter
    versions:
      - from: '2019-01-01'
        to: 2019-12-31
        formula: 1
  - name: top_level
    kind: derived
    from: 2020-01-01
    formula: b
"""
    )
    assert module.imports == ("us:b#t",)
    assert [(rule.name, rule.start) for rule in module.rules] == [
        ("long_form", date(2018, 1, 1)),
        ("alias_form", date(2019, 1, 1)),
        ("top_level", date(2020, 1, 1)),
    ]
    assert module.rules[0].versions[0].formula == "a"
    assert module.rules[1].versions[0].formula == ""
    assert module.rules[2].versions[0].formula == "b"


def test_parse_module_keeps_only_kinds_the_engine_versions():
    module = lsi.parse_module(
        """
rules:
  - {name: a, kind: data_relation}
  - {name: b, kind: source_relation}
  - {name: c, kind: derived_relation, versions: [{effective_from: 2018-01-01, formula: d}]}
  - {name: e, kind: derived, versions: [{effective_from: 2018-01-01, formula: d}]}
"""
    )
    assert [rule.name for rule in module.rules] == ["e"]


def test_parse_module_handles_null_imports_and_table_parameters():
    module = lsi.parse_module(
        """
imports:
rules:
  - name: table
    kind: parameter
    indexed_by: size
    versions:
      - effective_from: '2018-01-01'
        values: {1: 10, 2: 20}
"""
    )
    assert module.imports == ()
    assert module.rules == (_rule("table", (Y2018, "")),)


@pytest.mark.parametrize("text", ["- a\n", "just text\n", ""])
def test_parse_module_rejects_a_non_mapping(text):
    with pytest.raises(ValueError, match="not a RuleSpec mapping"):
        lsi.parse_module(text, "us/a.yaml")


def test_parse_module_rejects_a_date_it_cannot_read():
    with pytest.raises(ValueError, match="rule r.*not a date"):
        lsi.parse_module(
            "rules: [{name: r, kind: derived, versions: [{from: soon, formula: 1}]}]\n",
            "us/a.yaml",
        )


def test_import_closure_is_transitive_drops_fragments_and_survives_cycles():
    modules = {
        "us:a": lsi.Module(imports=("us:b#t",)),
        "us:b": lsi.Module(imports=("us:c",)),
        "us:c": lsi.Module(imports=("us:a", "us:missing")),
    }
    assert lsi.import_closure("us:a", modules) == {"us:b", "us:c"}


def test_the_6012_shape_is_an_edge():
    modules = {
        "us:statutes/26/7703": lsi.Module(rules=(_rule("considered_married", (Y2026, "1")),)),
        "us:statutes/26/6012": lsi.Module(
            imports=("us:statutes/26/7703#considered_married",),
            rules=(_rule("return_required", (Y2018, "considered_married")),),
        ),
    }
    assert _edges(modules) == {
        lsi.Edge(
            "us:statutes/26/6012#return_required",
            "us:statutes/26/7703#considered_married",
            Y2018,
            Y2026,
        )
    }


@pytest.mark.parametrize(
    "specifier",
    ["us:b#later_amount", "us:b", "us:b#other"],
    ids=["named-fragment", "no-fragment", "fragment-names-another-rule"],
)
def test_a_fragment_does_not_narrow_what_a_formula_sees(specifier):
    # The sweep this tool replaced read only `#fragment` imports, so it missed
    # the last two. All three stop at run time on the pinned engine.
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(imports=(specifier,), rules=(_rule("r", (Y2018, "later_amount")),)),
    }
    assert _edges(modules) == {_edge(target="us:b#later_amount")}


def test_a_name_reached_through_a_transitive_import_is_an_edge():
    modules = {
        "us:c": LATE_TARGET,
        "us:b": lsi.Module(imports=("us:c",)),
        "us:a": lsi.Module(imports=("us:b",), rules=(_rule("r", (Y2018, "later_amount")),)),
    }
    assert _edges(modules) == {_edge(target="us:c#later_amount")}


def test_a_later_version_that_starts_with_its_target_is_not_an_edge():
    # This is how to encode the change. The rule-level reading of "starts
    # late" would flag it, and no date reaches a gap.
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(_rule("r", (Y2018, "1"), (Y2026, "later_amount")),),
        ),
    }
    assert _edges(modules) == set()


def test_an_edge_records_the_earliest_late_version():
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(
                _rule(
                    "r",
                    (date(2010, 1, 1), "1"),
                    (Y2018, "later_amount"),
                    (date(2020, 1, 1), "later_amount + 1"),
                    (Y2026, "later_amount + 2"),
                ),
            ),
        ),
    }
    assert _edges(modules) == {_edge(target="us:b#later_amount")}


def test_starting_on_the_same_day_is_not_an_edge():
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(imports=("us:b",), rules=(_rule("r", (Y2026, "later_amount")),)),
    }
    assert _edges(modules) == set()


def test_a_local_name_is_not_an_import_edge():
    # The encoder's temporal-dependency-coverage validator owns these. A local
    # definition also wins over an imported rule of the same name.
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(
                _rule("r", (Y2018, "later_amount + own")),
                _rule("later_amount", (Y2018, "1")),
                _rule("own", (Y2026, "1")),
            ),
        ),
    }
    assert _edges(modules) == set()


def test_a_name_outside_the_import_closure_is_not_a_reference():
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(rules=(_rule("r", (Y2018, "later_amount")),)),
    }
    assert lsi.import_references(modules) == set()


def test_a_name_two_imports_define_resolves_to_the_earliest_definition():
    modules = {
        "us:b": lsi.Module(rules=(_rule("shared", (Y2026, "1")),)),
        "us:c": lsi.Module(rules=(_rule("shared", (date(2010, 1, 1), "1")),)),
        "us:a": lsi.Module(imports=("us:b", "us:c"), rules=(_rule("r", (Y2018, "shared")),)),
    }
    assert lsi.import_references(modules) == {
        lsi.Reference("us:a#r", Y2018, "us:c#shared", date(2010, 1, 1))
    }
    assert _edges(modules) == set()


def test_a_word_in_a_comment_or_string_is_not_a_reference():
    modules = {
        "us:b": LATE_TARGET,
        "us:a": lsi.Module(
            imports=("us:b",),
            rules=(_rule("r", (Y2018, '1 # later_amount\n + "later_amount"')),),
        ),
    }
    assert _edges(modules) == set()


def test_module_path_inverts_canonical_target():
    assert lsi.module_path("us:statutes/26/6012#x") == "us/statutes/26/6012.yaml"
    assert lsi.module_path("us-la:statutes/47:32#x") == "us-la/statutes/47:32.yaml"


def test_baseline_rejects_malformed_lines():
    line = "us:a#r\tus:b#t\t2018-01-01\t2026-01-01"
    assert lsi.parse_baseline(f"# comment\n\n{line}\n") == {_edge()}
    for bad, message in (
        ("us:a#r\tus:b#t\t2018-01-01", "must be"),
        ("us:a\tus:b#t\t2018-01-01\t2026-01-01", "two rule ids"),
        ("us:a#r\tus:b#t\t2026-01-01\t2026-01-01", "does not start late"),
        ("us:a#r\tus:b#t\t2027-01-01\t2026-01-01", "does not start late"),
        (f"{line}\n{line}", "duplicates"),
    ):
        with pytest.raises(ValueError, match=message):
            lsi.parse_baseline(bad + "\n")


def test_baseline_rejects_a_date_that_is_not_one():
    with pytest.raises(ValueError):
        lsi.parse_baseline("us:a#r\tus:b#t\tsoon\t2026-01-01\n")


def test_gate_accepts_a_matching_baseline():
    assert lsi.compare({_edge()}, {_edge()}).ok


def test_gate_fails_on_an_unlisted_edge():
    verdict = lsi.compare({_edge()}, set())
    assert not verdict.ok and verdict.new == {_edge()} and not verdict.stale


def test_gate_fails_on_a_listed_edge_that_no_longer_holds():
    verdict = lsi.compare(set(), {_edge()})
    assert not verdict.ok and verdict.stale == {_edge()} and not verdict.new


def test_gate_fails_when_a_listed_edges_dates_move():
    wider = _edge(version_start=date(2010, 1, 1))
    verdict = lsi.compare({wider}, {_edge()})
    assert verdict.new == {wider} and verdict.stale == {_edge()}


def test_regenerating_cannot_add_a_pair_against_the_protected_base():
    verdict = lsi.compare({_edge()}, {_edge()}, set())
    assert not verdict.ok and verdict.added == {_edge()}


def test_the_accepted_label_allows_a_regenerated_pair_and_nothing_else():
    assert lsi.compare({_edge()}, {_edge()}, set(), allow_added=True).ok
    unlisted = lsi.compare({_edge()}, set(), set(), allow_added=True)
    assert not unlisted.ok and unlisted.new == {_edge()}
    stale = lsi.compare(set(), {_edge()}, set(), allow_added=True)
    assert not stale.ok and stale.stale == {_edge()}


def test_a_listed_pair_may_change_dates_against_the_protected_base():
    narrower = _edge(version_start=date(2024, 1, 1))
    assert lsi.compare({narrower}, {narrower}, {_edge()}).ok


def test_a_pull_request_may_shrink_the_baseline():
    other = _edge(rule="us:a#s")
    assert lsi.compare({_edge()}, {_edge()}, {_edge(), other}).ok


def test_introducing_the_baseline_has_no_base_bound():
    assert lsi.compare({_edge()}, {_edge()}, None).ok


def test_summarize_counts_rules_and_modules():
    summary = lsi.summarize({_edge(), _edge(rule="us:a#s"), _edge(rule="us-co:c#r", target="us:d#t")})
    assert summary.startswith(
        "3 late-start import edge(s): 3 rules, 2 importing modules, 2 target modules"
    )
    assert lsi.summarize(set()).startswith("0 late-start import edge(s)")


def _tracked_files() -> set[str]:
    listing = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"], check=True, capture_output=True
    ).stdout.decode("utf-8")
    return {path for path in listing.split("\0") if path}


def test_committed_baseline_is_canonical_and_names_tracked_modules():
    text = (REPO_ROOT / lsi.BASELINE_RELATIVE_PATH).read_text(encoding="utf-8")
    entries = lsi.parse_baseline(text)
    assert lsi.render_baseline(entries) == text, "regenerate with late_start_imports.py baseline"
    tracked = _tracked_files()
    named = {lsi.module_path(id_) for entry in entries for id_ in (entry.rule, entry.target)}
    assert not sorted(named - tracked)[:10], "baseline names modules that are not tracked"


def test_committed_baseline_matches_this_checkout():
    edges = lsi.late_start_edges(lsi.import_references(lsi.load_modules(REPO_ROOT)))
    baseline = lsi.parse_baseline(
        (REPO_ROOT / lsi.BASELINE_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    verdict = lsi.compare(edges, baseline)
    assert verdict.ok, (
        f"new edges: {sorted(map(lsi.Edge.render, verdict.new))[:10]}\n"
        f"lines that no longer hold: {sorted(map(lsi.Edge.render, verdict.stale))[:10]}\n"
        "See tools/README.md, Late-start imports."
    )


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


MODULE_TEMPLATE = """\
format: rulespec/v1
imports:
  - us:statutes/1/target
module: {{}}
rules:
  - name: answer
    kind: derived
    versions:
      - effective_from: '{start}'
        formula: later_amount
"""
TARGET = """\
format: rulespec/v1
module: {}
rules:
  - name: later_amount
    kind: parameter
    versions:
      - effective_from: '2026-01-01'
        formula: '100'
"""


def _write(root: Path, relative: str, text: str) -> None:
    (root / relative).parent.mkdir(parents=True, exist_ok=True)
    (root / relative).write_text(text, encoding="utf-8")


@pytest.fixture
def repository(tmp_path):
    """A checkout whose base commit carries an empty baseline and no edge."""
    root = tmp_path / "rulespec-us"
    _write(root, "us/statutes/1/target.yaml", TARGET)
    _write(root, "us/statutes/1/importer.yaml", MODULE_TEMPLATE.format(start="2026-01-01"))
    _write(root, lsi.BASELINE_RELATIVE_PATH.as_posix(), lsi.render_baseline(set()))
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
    return root, _git(root, "rev-parse", "HEAD")


def _check(root: Path, base: str | None, allow_added: bool = False) -> int:
    return lsi.check(root, root / lsi.BASELINE_RELATIVE_PATH, base, allow_added)


def test_check_passes_on_a_checkout_that_matches_its_base(repository):
    root, base = repository
    assert _check(root, base) == 0


def test_check_fails_when_a_change_adds_an_edge(repository, capsys):
    root, base = repository
    _write(root, "us/statutes/1/importer.yaml", MODULE_TEMPLATE.format(start="2018-01-01"))
    _git(root, "add", "-A")
    assert _check(root, base) == 1
    output = capsys.readouterr().out
    assert "1 edge(s) are not in known-late-start-imports.txt" in output
    assert (
        "us:statutes/1/importer#answer reads us:statutes/1/target#later_amount "
        "from 2018-01-01, but that target starts 2026-01-01"
    ) in output


def test_regenerating_does_not_pass_the_base_bound_without_the_label(repository, capsys):
    root, base = repository
    _write(root, "us/statutes/1/importer.yaml", MODULE_TEMPLATE.format(start="2018-01-01"))
    _git(root, "add", "-A")
    edges = lsi.late_start_edges(lsi.import_references(lsi.load_modules(root)))
    _write(root, lsi.BASELINE_RELATIVE_PATH.as_posix(), lsi.render_baseline(edges))
    assert _check(root, base) == 1
    assert lsi.ACCEPT_LABEL in capsys.readouterr().out
    assert _check(root, base, allow_added=True) == 0
    assert _check(root, None) == 0


def test_check_has_no_base_bound_while_the_baseline_is_introduced(repository):
    root, base = repository
    (root / lsi.BASELINE_RELATIVE_PATH).unlink()
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "no baseline")
    without = _git(root, "rev-parse", "HEAD")
    _write(root, "us/statutes/1/importer.yaml", MODULE_TEMPLATE.format(start="2018-01-01"))
    _git(root, "add", "-A")
    edges = lsi.late_start_edges(lsi.import_references(lsi.load_modules(root)))
    _write(root, lsi.BASELINE_RELATIVE_PATH.as_posix(), lsi.render_baseline(edges))
    assert _check(root, without) == 0


def test_check_fails_when_a_repair_leaves_its_line_behind(repository, capsys):
    root, base = repository
    edge = lsi.Edge(
        "us:statutes/1/importer#answer", "us:statutes/1/target#later_amount", Y2018, Y2026
    )
    _write(root, lsi.BASELINE_RELATIVE_PATH.as_posix(), lsi.render_baseline({edge}))
    assert _check(root, None) == 1
    assert "1 listed edge(s) no longer hold" in capsys.readouterr().out


def test_the_cli_regenerates_the_committed_baseline_format(repository, capsys):
    root, _ = repository
    assert lsi.main(["baseline", "--root", str(root)]) == 0
    assert capsys.readouterr().out == lsi.render_baseline(set())


def test_harness_uses_the_engine_compile_entry_points():
    source = lsi.HARNESS_SOURCE
    assert "CanonicalRuleSpecRoots::new" in source
    assert "CompiledProgramArtifact::from_rulespec_file" in source
    assert "CompiledProgramArtifact::from_composed_rulespec_file" in source
    assert "ModuleKindOnAtomicSurface" in source


def _result(module: str, *references: dict, **extra) -> str:
    return json.dumps(
        {"module": module, "ok": True, "references": list(references), "shadowed": [], **extra}
    )


REFERENCE = {
    "rule": "us:a#r",
    "version_start": "2018-01-01",
    "target": "us:b#t",
    "target_start": "2026-01-01",
}


def test_parse_engine_references_reads_compiled_modules_only():
    lines = [
        _result("us/a.yaml", REFERENCE),
        json.dumps({"module": "us/b.yaml", "ok": False, "error": "refused"}),
        _result("us/c.yaml", shadowed=["hidden"]),
        "",
    ]
    compiled, references, shadowed = lsi.parse_engine_references(lines)
    assert compiled == {"us:a", "us:c"}
    assert references == {lsi.Reference("us:a#r", Y2018, "us:b#t", Y2026)}
    assert shadowed == ["us:c#hidden"]


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ('{"root_error": "not canonical"}', "refused the checkout"),
        ('{"module": "us/a.yaml"}', "malformed result"),
        ('{"ok": true}', "malformed result"),
    ],
)
def test_parse_engine_references_refuses_what_it_cannot_read(line, message):
    with pytest.raises(SystemExit, match=message):
        lsi.parse_engine_references([line])


def test_reference_differences_compare_only_modules_the_engine_compiled():
    both = lsi.Reference("us:a#r", Y2018, "us:b#t", Y2026)
    only_engine = lsi.Reference("us:a#s", Y2018, "us:b#t", Y2026)
    only_static = lsi.Reference("us:a#u", Y2018, "us:b#t", Y2026)
    refused = lsi.Reference("us:refused#r", Y2018, "us:b#t", Y2026)
    assert lsi.reference_differences({"us:a"}, {both, only_engine}, {both, only_static, refused}) == (
        {only_engine},
        {only_static},
    )


def test_scratch_copy_keeps_executable_content_and_drops_citations(tmp_path):
    source = {
        "format": "rulespec/v1",
        "imports": None,
        "module": {
            "kind": "composition",
            "source_verification": {"corpus_citation_paths": ["us/statute/1"]},
        },
        "rules": [
            {
                "name": "r",
                "kind": "derived",
                "metadata": {"proof": {"atoms": []}},
                "versions": [{"effective_from": "2018-01-01", "formula": "a"}],
            }
        ],
    }
    atomic = {"format": "rulespec/v1", "module": {"summary": "text"}, "rules": []}
    _write(tmp_path, "us/a.yaml", yaml.safe_dump(source))
    _write(tmp_path, "us/b.yaml", yaml.safe_dump(atomic))
    root = lsi.write_scratch_root(tmp_path, ["us/a.yaml", "us/b.yaml"], tmp_path / "scratch")
    assert root.name == "rulespec-us"
    written = yaml.safe_load((root / "us/a.yaml").read_text(encoding="utf-8"))
    assert written["module"] == {"kind": "composition"}
    assert written["imports"] == []
    assert written["rules"] == [
        {
            "name": "r",
            "kind": "derived",
            "versions": [{"effective_from": "2018-01-01", "formula": "a"}],
        }
    ]
    assert yaml.safe_load((root / "us/b.yaml").read_text(encoding="utf-8"))["module"] == {}
    assert lsi.parse_module((tmp_path / "us/a.yaml").read_text(), "a") == lsi.parse_module(
        (root / "us/a.yaml").read_text(), "a"
    )
