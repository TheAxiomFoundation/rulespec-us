"""Executable artifact comparisons; no test-authored RuleSpec modules."""

from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import sys

from hypothesis import given, strategies as st
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_artifact_semantics as semantics  # noqa: E402


def _rule(name="credit", value=7):
    return {"name": name, "entity": "Person", "dtype": "integer", "unit": None,
            "period": "Year", "semantics": "scalar",
            "expr": {"kind": "literal", "value": {"kind": "integer", "value": value}}}


def _artifact(*rules):
    return {"artifact_format_version": 2, "program": {"derived": list(rules)}}


def _source(name="credit", start="2026-01-01", end=None):
    return {name: semantics.SourceRule("us/statutes/example.yaml", {
        "name": name, "kind": "derived", "versions": [{
            "effective_from": start, "effective_to": end, "formula": "7"}]
    })}


def _version(rule, start="2026-01-01", end=None):
    return {"effective_from": start, "effective_to": end,
            "semantics": rule["semantics"], "expr": deepcopy(rule["expr"])}


@given(start=st.dates(min_value=date(1900, 1, 1), max_value=date(2099, 1, 1)),
       value=st.integers(min_value=-(2**63), max_value=2**63 - 1))
def test_single_open_version_only_changes_effective_date(start, value):
    old = _rule(value=value)
    new = {**deepcopy(old), "versions": [_version(old, start.isoformat())]}
    result = semantics.compare_artifacts(_artifact(old), _artifact(new), _source(start=start))
    assert result["errors"] == []
    assert len(result["restored_open_versions"]) == 1
    assert result["restored_open_versions"][0]["effective_from"] == start.isoformat()


@given(start=st.dates(min_value=date(1900, 1, 1), max_value=date(2098, 1, 1)),
       days=st.integers(min_value=0, max_value=365))
def test_bounded_single_version_is_already_preserved_by_old_compiler(start, days):
    end = start + timedelta(days=days)
    rule = _rule()
    rule["versions"] = [_version(rule, start.isoformat(), end.isoformat())]
    result = semantics.compare_artifacts(_artifact(rule), _artifact(deepcopy(rule)),
                                         _source(start=start, end=end))
    assert result["errors"] == []
    assert result["restored_open_versions"] == []
    assert result["unchanged_rules"] == result["bounded_single_rules"] == 1


@pytest.mark.parametrize("versions", [None, []])
def test_new_single_dated_rule_never_has_empty_versions(versions):
    rule = _rule()
    if versions is not None:
        rule["versions"] = versions
    result = semantics.check_new_artifact(_artifact(rule), _source())
    assert result["errors"][0]["actual_count"] == 0


@pytest.mark.parametrize("field,value", [
    ("effective_from", "2025-01-01"), ("effective_to", None),
])
def test_single_bounded_dates_must_match_source(field, value):
    rule = _rule()
    rule["versions"] = [_version(rule, end="2026-12-31")]
    rule["versions"][0][field] = value
    result = semantics.check_new_artifact(_artifact(rule), _source(end="2026-12-31"))
    assert any(field in error["error"] for error in result["errors"])


@pytest.mark.parametrize("change", ["fallback", "version", "both", "entity", "semantics", "unknown"])
def test_restored_version_cannot_hide_executable_changes(change):
    old, new = _rule(), _rule()
    new["versions"] = [_version(new)]
    if change in {"fallback", "both"}:
        new["expr"]["value"]["value"] = 9
    if change in {"version", "both"}:
        new["versions"][0]["expr"]["value"]["value"] = 9
    if change == "entity":
        new["entity"] = "Household"
    if change == "semantics":
        new["versions"][0]["semantics"] = "judgment"
    if change == "unknown":
        new["future_executable_field"] = True
    assert semantics.compare_artifacts(_artifact(old), _artifact(new), _source())["errors"]


def test_multiple_versions_compare_all_formulas_and_dates():
    old = _rule()
    old["versions"] = [_version(old, "2025-01-01", "2025-12-31"),
                       _version(old, "2026-01-01")]
    source = _source()
    source["credit"].rule["versions"].insert(0, {"effective_from": "2025-01-01", "formula": "7"})
    new = deepcopy(old)
    assert semantics.compare_artifacts(_artifact(old), _artifact(new), source)["errors"] == []
    new["versions"][0]["expr"]["value"]["value"] = 8
    errors = semantics.compare_artifacts(_artifact(old), _artifact(new), source)["errors"]
    assert any(error.get("path") == "versions[0].expr.value.value" for error in errors)


def test_descriptive_changes_are_reported_without_erasing_nested_source_fields():
    old = _rule()
    old["versions"] = [_version(old, end="2026-12-31")]
    new = deepcopy(old)
    new["corpus_citation_path"] = "us/statute/example"
    result = semantics.compare_artifacts(_artifact(old), _artifact(new), _source(end="2026-12-31"))
    assert result["errors"] == []
    assert result["descriptive_changes"][0]["field"] == "corpus_citation_path"
    new["expr"]["source"] = "changed relation"
    result = semantics.compare_artifacts(_artifact(old), _artifact(new), _source(end="2026-12-31"))
    assert any(error.get("path") == "expr.source" for error in result["errors"])


def test_missing_source_and_changed_rule_set_fail_closed():
    assert semantics.check_new_artifact(_artifact(_rule()), {})["errors"]
    assert semantics.compare_artifacts(_artifact(), _artifact(_rule()), _source())["errors"]


def test_duplicate_artifact_rule_names_fail_closed():
    with pytest.raises(ValueError, match="duplicate"):
        semantics.check_new_artifact(_artifact(_rule(), _rule()), _source())


def test_top_level_formula_dates_are_also_checked():
    rule = _rule()
    rule["versions"] = [_version(rule)]
    source = {"credit": semantics.SourceRule("assembled composition", {
        "kind": "derived", "formula": "7", "effective_from": "2026-01-01"})}
    assert semantics.check_new_artifact(_artifact(rule), source)["errors"] == []
    rule["versions"] = []
    assert semantics.check_new_artifact(_artifact(rule), source)["errors"]


@pytest.mark.parametrize("top_level", [False, True])
@pytest.mark.parametrize("bounded", [False, True])
def test_source_date_aliases_follow_the_engine_contract(top_level, bounded):
    dates = {"from": "2026-01-01", "formula": "7"}
    if bounded:
        dates["to"] = "2026-12-31"
    source_rule = {"kind": "derived", **dates} if top_level else {
        "kind": "derived", "versions": [dates]}
    sources = {"credit": semantics.SourceRule("date alias source", source_rule)}
    old = _rule()
    new = {**deepcopy(old), "versions": [_version(old, end=dates.get("to"))]}
    if bounded:
        old["versions"] = deepcopy(new["versions"])
    result = semantics.compare_artifacts(_artifact(old), _artifact(new), sources)
    assert result["errors"] == []
    new["versions"] = []
    assert semantics.check_new_artifact(_artifact(new), sources)["errors"]


@pytest.mark.parametrize("top_level", [False, True])
@pytest.mark.parametrize("canonical,alias", [
    ("effective_from", "from"), ("effective_to", "to")])
def test_duplicate_date_aliases_are_rejected_like_serde(top_level, canonical, alias):
    dates = {"formula": "7", canonical: "2026-01-01", alias: "2026-01-01"}
    rule = dates if top_level else {"versions": [dates]}
    with pytest.raises(ValueError, match="both"):
        semantics.effective_versions(rule)


def test_entity_free_computed_parameter_can_be_an_artifact_derived_rule():
    old = _rule()
    old["entity"] = "Scalar"
    old["expr"] = {"kind": "add", "items": [
        {"kind": "input", "name": "income"},
        {"kind": "literal", "value": {"kind": "integer", "value": 1}}]}
    new = {**deepcopy(old), "versions": [_version(old)]}
    source = _source()
    source["credit"].rule["kind"] = "parameter"
    source["credit"].rule["versions"][0]["formula"] = "income + 1"
    assert semantics.compare_artifacts(_artifact(old), _artifact(new), source)["errors"] == []


@pytest.mark.parametrize("kind", ["source_relation", "derived_relation", "data_relation", None])
def test_artifact_derived_rules_cannot_originate_from_relation_or_missing_kind(kind):
    rule = _rule()
    rule["versions"] = [_version(rule)]
    source = _source()
    source["credit"].rule["kind"] = kind
    errors = semantics.check_new_artifact(_artifact(rule), source)["errors"]
    assert errors[0]["error"] == "artifact derived rule has a non-executable source kind"


@pytest.mark.parametrize("target", ["us:../outside", "../us:statutes/example", "/us:statutes/example", "us:/absolute", "us:statutes/example.yaml"])
def test_source_index_rejects_noncanonical_targets(tmp_path, target):
    with pytest.raises(ValueError, match="target"):
        semantics.SourceIndex([tmp_path])._module_path(target)


def test_source_index_rejects_ambiguous_country_roots(tmp_path):
    roots = [tmp_path / "one", tmp_path / "two"]
    for root in roots:
        path = root / "us/statutes/example.yaml"
        path.parent.mkdir(parents=True)
        # A resolver test needs only file existence, not a hand-written module.
        path.touch()
    with pytest.raises(ValueError, match="found 2"):
        semantics.SourceIndex(roots)._module_path("us:statutes/example")


def test_source_index_uses_canonical_ids_and_originless_composition(tmp_path):
    source_path = tmp_path / "us/statutes/example.yaml"
    source_path.parent.mkdir(parents=True)
    source_path.touch()
    composition = tmp_path / "assembled.rulespec.yaml"
    imported, local = _rule("imported"), _rule("local")
    imported["id"] = "us:statutes/example#imported"
    index = semantics.SourceIndex([tmp_path])
    # Parsed dict fixtures avoid authoring executable RuleSpec module files.
    index.documents[source_path] = {"rules": [{"name": "imported", "kind": "derived"}]}
    index.documents[composition] = {"rules": [{"name": "local", "kind": "derived"}]}
    sources = index.rules_for_artifact(_artifact(imported, local), composition)
    assert sources["imported"].path == str(source_path)
    assert sources["local"].path == str(composition)


def test_source_index_follows_sets_bindings_in_merged_rule_order(tmp_path):
    source_path = tmp_path / "us/statutes/example.yaml"
    source_path.parent.mkdir(parents=True)
    source_path.touch()
    composition = tmp_path / "assembled.rulespec.yaml"
    rules = [_rule("target"), _rule("middle"), _rule("value")]
    for rule in rules:
        rule["id"] = f"us:statutes/example#{rule['name']}"
    declarations = [{"name": name, "kind": "derived", "versions": [{
        "effective_from": f"202{index}-01-01", "formula": "7"}]}
        for index, name in enumerate(("target", "middle", "value"))]
    for target, value in (("middle", "value"), ("target", "middle")):
        declarations.append({"name": f"set_{target}", "kind": "source_relation",
                             "source_relation": {"type": "sets",
                                 "target": f"us:statutes/example#{target}",
                                 "value": f"us:statutes/example#{value}"}})
    index = semantics.SourceIndex([tmp_path])
    index.documents[source_path] = {"rules": declarations}
    index.documents[composition] = {"imports": ["us:statutes/example#target"], "rules": []}
    sources = index.rules_for_artifact(_artifact(*rules), composition)
    assert sources["target"].rule["name"] == "value"
    assert len(sources["target"].bindings) == 2
    assert sources["target"].rule["versions"][0]["effective_from"] == "2022-01-01"


@pytest.mark.parametrize("imported", [False, True])
def test_empty_yaml_imports_value_keeps_source_resolution_and_date_checks(tmp_path, imported):
    """The real TX TANF source uses bare imports:, represented as None here."""
    composition = tmp_path / "assembled.rulespec.yaml"
    rule = _rule()
    rule["versions"] = [_version(rule)]
    source = _source()["credit"].rule
    document = {"imports": None, "rules": [source]}
    index = semantics.SourceIndex([tmp_path])
    if imported:
        path = tmp_path / "us/statutes/example.yaml"
        path.parent.mkdir(parents=True)
        path.touch()
        rule["id"] = "us:statutes/example#credit"
        index.documents[path] = document
        index.documents[composition] = {"imports": ["us:statutes/example"], "rules": []}
    else:
        path = composition
        index.documents[composition] = document
    sources = index.rules_for_artifact(_artifact(rule), composition)
    assert sources["credit"].path == str(path)
    assert semantics.check_new_artifact(_artifact(rule), sources)["errors"] == []
    rule["versions"] = []
    assert semantics.check_new_artifact(_artifact(rule), sources)["errors"]


def test_cli_fails_with_no_paired_artifact_and_writes_coverage_report(tmp_path):
    report = tmp_path / "report.json"
    result = semantics.main(["--old-dir", str(tmp_path / "old"),
                             "--new-dir", str(tmp_path / "new"),
                             "--rulespec-root", str(tmp_path), "--output", str(report)])
    assert result == 1
    data = json.loads(report.read_text())
    assert data["summary"]["paired_artifacts"] == 0
    assert "coverage_error" in data


def test_cli_reports_source_lookup_failure(tmp_path):
    old_dir, new_dir = tmp_path / "old", tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()
    for directory in (old_dir, new_dir):
        (directory / "program.compiled.json").write_text(json.dumps(_artifact(_rule())))
    report = tmp_path / "report.json"
    assert semantics.main(["--old-dir", str(old_dir), "--new-dir", str(new_dir),
                           "--rulespec-root", str(tmp_path), "--output", str(report)]) == 1
    data = json.loads(report.read_text())
    assert data["summary"]["comparisons_completed"] == 0
    assert data["summary"]["errors"] == 1
