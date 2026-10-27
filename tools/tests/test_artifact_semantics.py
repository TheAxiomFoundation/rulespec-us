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


def _parameter(name="rate", value="0.062", start="1990-01-01", end=None):
    version = {"effective_from": start, "values": {"0": {"kind": "decimal", "value": value}}}
    if end is not None:
        version["effective_to"] = end
    return {"name": name, "unit": "ratio", "indexed_by": None, "versions": [version],
            "source": "26 USC 3101(a)", "corpus_citation_path": "us/statute/26/3101/a"}


def _relation(name="member_of_household"):
    return {"name": name, "arity": 2, "slot_entities": ["Person", "Household"]}


def _full_artifact():
    return {
        "artifact_format_version": 2, "engine_version": "0.2.2",
        "program": {
            "module": {"kind": "composition"},
            "units": [{"name": "USD", "kind": "currency", "minor_units": 2},
                      {"name": "ratio", "kind": "ratio"}],
            "relations": [_relation()],
            "parameters": [_parameter()],
            "derived": [],
        },
        "metadata": {"evaluation_order": [], "input_catalog": [],
                     "fast_path": {"strategy": "generic_bulk", "compatible": True, "blockers": []}},
    }


def _mutate(artifact, change):
    program, metadata = artifact["program"], artifact["metadata"]
    parameter, relation = program["parameters"][0], program["relations"][0]
    version = parameter["versions"][0]
    {
        "parameter value": lambda: version["values"]["0"].update(value="0.99"),
        "parameter value kind": lambda: version["values"]["0"].update(kind="integer"),
        "parameter bracket": lambda: version["values"].update({"1": {"kind": "decimal", "value": "0"}}),
        "parameter start": lambda: version.update(effective_from="1991-01-01"),
        "parameter end": lambda: version.update(effective_to="2030-12-31"),
        "parameter version added": lambda: parameter["versions"].append(
            {"effective_from": "2031-01-01", "values": {"0": {"kind": "decimal", "value": "0.07"}}}),
        "parameter unit": lambda: parameter.update(unit="USD"),
        "parameter index": lambda: parameter.update(indexed_by="wages"),
        "parameter added": lambda: program["parameters"].append(_parameter("other")),
        "parameter removed": lambda: program["parameters"].clear(),
        "relation arity": lambda: relation.update(arity=3),
        "relation slot entity": lambda: relation.update(slot_entities=["Person", "TaxUnit"]),
        "relation derivation": lambda: relation.update(derivation={
            "source_relation": "member_of_household", "current_slot": 0, "related_slot": 1,
            "predicate": {"kind": "literal", "value": {"kind": "bool", "value": True}}}),
        "relation added": lambda: program["relations"].append(_relation("spouse_of")),
        "unit changed": lambda: program["units"][0].update(minor_units=0),
        "unit removed": lambda: program["units"].pop(),
        "selected year input": lambda: program.update(selected_year_inputs=[{"name": "year"}]),
        "unknown section": lambda: program.update(extends="us-base"),
        "format version": lambda: artifact.update(artifact_format_version=999),
        "unknown envelope field": lambda: artifact.update(defaults={"period": "2026"}),
        "evaluation order": lambda: metadata.update(evaluation_order=["credit"]),
        "input catalog": lambda: metadata.update(input_catalog=[
            {"slot": "wages", "canonical_request_name": "wages", "request_names": ["wages"]}]),
    }[change]()
    return artifact


EXECUTABLE_CHANGES = [
    "parameter value", "parameter value kind", "parameter bracket", "parameter start",
    "parameter end", "parameter version added", "parameter unit", "parameter index",
    "parameter added", "parameter removed", "relation arity", "relation slot entity",
    "relation derivation", "relation added", "unit changed", "unit removed",
    "selected year input", "unknown section", "format version", "unknown envelope field",
    "evaluation order", "input catalog",
]


@pytest.mark.parametrize("change", EXECUTABLE_CHANGES)
def test_every_executable_change_outside_derived_rules_is_an_error(change):
    old = _full_artifact()
    assert semantics.compare_artifacts(old, deepcopy(old), {})["errors"] == []
    result = semantics.compare_artifacts(old, _mutate(deepcopy(old), change), {})
    assert result["errors"], change


@pytest.mark.parametrize("change", ["parameter value", "relation slot entity", "unit changed"])
def test_cli_exits_nonzero_for_parameter_relation_and_unit_changes(tmp_path, monkeypatch, change):
    """The audit's command-line result, not only its report, must reject these."""
    monkeypatch.setattr(semantics.SourceIndex, "rules_for_artifact",
                        lambda self, artifact, composition: {})
    old_dir, new_dir = tmp_path / "old", tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()
    old = _full_artifact()
    (old_dir / "program.compiled.json").write_text(json.dumps(old))
    arguments = ["--old-dir", str(old_dir), "--new-dir", str(new_dir),
                 "--rulespec-root", str(tmp_path), "--output", str(tmp_path / "report.json")]
    (new_dir / "program.compiled.json").write_text(json.dumps(old))
    assert semantics.main(arguments) == 0
    (new_dir / "program.compiled.json").write_text(json.dumps(_mutate(deepcopy(old), change)))
    assert semantics.main(arguments) == 1
    summary = json.loads((tmp_path / "report.json").read_text())["summary"]
    assert summary["errors"] >= 1 and summary["parameters_compared"] == 1


@pytest.mark.parametrize("field,value", [
    ("source", "26 USC 3101(b)"), ("source_url", "https://example.org/3101"),
    ("corpus_citation_path", "us/statute/26/3101/b"),
])
def test_descriptive_parameter_fields_are_reported_not_errors(field, value):
    old = _full_artifact()
    new = deepcopy(old)
    new["program"]["parameters"][0][field] = value
    result = semantics.compare_artifacts(old, new, {})
    assert result["errors"] == []
    assert result["descriptive_changes"] == [{"parameter": "rate", "field": field,
                                              "old": old["program"]["parameters"][0].get(field),
                                              "new": value}]


ID_CHANGES = {
    "changed": ("us:statutes/26/3101#rate", "us:statutes/26/3111#rate"),
    "missing to present": (None, "us:statutes/26/3101#rate"),
    "present to missing": ("us:statutes/26/3101#rate", None),
}


def _with_id(item, identity):
    item = deepcopy(item)
    if identity is not None:
        item["id"] = identity
    return item


@pytest.mark.parametrize("change", sorted(ID_CHANGES))
def test_a_parameter_id_change_is_an_error(change):
    """A query resolves an output through its id (model.rs resolve_parameter_name)."""
    before, after = ID_CHANGES[change]
    old, new = _full_artifact(), _full_artifact()
    old["program"]["parameters"] = [_with_id(_parameter(), before)]
    new["program"]["parameters"] = [_with_id(_parameter(), after)]
    result = semantics.compare_artifacts(old, new, {})
    assert [error["parameter"] for error in result["errors"]] == ["rate"]
    assert result["descriptive_changes"] == []


@pytest.mark.parametrize("change", sorted(ID_CHANGES))
def test_a_derived_rule_id_change_is_an_error(change):
    """model.rs resolve_derived_name resolves a derived output through its id."""
    before, after = ID_CHANGES[change]
    rule = _rule()
    rule["versions"] = [_version(rule, end="2026-12-31")]
    result = semantics.compare_artifacts(_artifact(_with_id(rule, before)),
                                         _artifact(_with_id(rule, after)),
                                         _source(end="2026-12-31"))
    assert [error.get("path") for error in result["errors"]] == ["id"]


def test_a_null_id_and_an_omitted_id_are_one_value():
    old = _full_artifact()
    new = deepcopy(old)
    old["program"]["parameters"][0]["id"] = None
    assert semantics.compare_artifacts(old, new, {})["errors"] == []
    rule = _rule()
    rule["versions"] = [_version(rule, end="2026-12-31")]
    assert semantics.compare_artifacts(_artifact(dict(rule, id=None)), _artifact(rule),
                                       _source(end="2026-12-31"))["errors"] == []


@pytest.mark.parametrize("reference", ["parameter unit", "derived unit", "input catalog"])
def test_adding_a_unit_the_old_program_references_is_an_error(reference):
    """An old reference to an undefined unit fails with UnknownUnit; defining
    the unit turns that failure into a value."""
    old = _full_artifact()
    if reference == "parameter unit":
        old["program"]["parameters"][0]["unit"] = "CHF"
    elif reference == "derived unit":
        old["program"]["derived"] = [dict(_rule(), unit="CHF")]
    else:
        old["metadata"]["input_catalog"] = [{"slot": "wages", "unit": "CHF"}]
    new = deepcopy(old)
    new["program"]["units"].append({"name": "CHF", "kind": "currency", "minor_units": 2})
    source = {"credit": semantics.SourceRule("us/statutes/example.yaml",
                                             {"name": "credit", "kind": "derived"})}
    result = semantics.compare_artifacts(old, new, source)
    assert [error.get("unit") for error in result["errors"]] == ["CHF"]
    assert not any(change["path"] == "program.units.CHF" for change in result["schema_changes"])


def test_permitted_schema_changes_are_listed_explicitly():
    old = _full_artifact()
    old["program"]["extends"] = None
    del old["metadata"]["input_catalog"]
    old["metadata"]["comparison_build"] = {"engine_sha": "9" * 40}
    new = _full_artifact()
    new["engine_version"] = "0.3.0"
    new["program"]["units"].append({"name": "CHF", "kind": "currency", "minor_units": 2})
    new["program"]["module"]["interpretations"] = ["one reading"]
    new["metadata"]["fast_path"] = {"strategy": "generic_bulk", "compatible": False,
                                    "blockers": ["credit: related"]}
    new["metadata"]["provenance"] = {"corpus": {"sha": "c" * 40}}
    result = semantics.compare_artifacts(old, new, {})
    assert result["errors"] == []
    assert {(change["path"], change["change"]) for change in result["schema_changes"]} == {
        ("engine_version", "changed"), ("program.extends", "removed"),
        ("program.units.CHF", "added"), ("metadata.input_catalog", "added"),
        ("metadata.comparison_build", "removed"), ("metadata.fast_path", "changed"),
        ("metadata.provenance", "added"),
    }
    assert [change["section"] for change in result["descriptive_changes"]] == ["program.module"]


@pytest.mark.parametrize("omitted", ["slot_entities", "derivation", "unit", "indexed_by", "effective_to"])
def test_serde_defaults_are_not_reported_as_changes(omitted):
    old = _full_artifact()
    new = deepcopy(old)
    if omitted in {"slot_entities", "derivation"}:
        old["program"]["relations"][0] = {"name": "pairs", "arity": 2}
        new["program"]["relations"][0] = {"name": "pairs", "arity": 2,
                                          **{omitted: semantics.RELATION_DEFAULTS[omitted]}}
    elif omitted == "effective_to":
        new["program"]["parameters"][0]["versions"][0]["effective_to"] = None
    else:
        old["program"]["parameters"][0][omitted] = None
        del new["program"]["parameters"][0][omitted]
    assert semantics.compare_artifacts(old, new, {})["errors"] == []


@given(old_value=st.decimals(allow_nan=False, allow_infinity=False, places=4),
       new_value=st.decimals(allow_nan=False, allow_infinity=False, places=4),
       start=st.dates(min_value=date(1900, 1, 1), max_value=date(2099, 1, 1)),
       descriptive=st.sampled_from(sorted(semantics.DESCRIPTIVE_PARAMETER_FIELDS)),
       text=st.text(max_size=12))
def test_a_parameter_comparison_errs_exactly_when_an_executable_value_differs(
    old_value, new_value, start, descriptive, text
):
    old = _full_artifact()
    old["program"]["parameters"] = [_parameter(value=str(old_value), start=start.isoformat())]
    new = deepcopy(old)
    new["program"]["parameters"][0]["versions"][0]["values"]["0"]["value"] = str(new_value)
    new["program"]["parameters"][0][descriptive] = text
    errors = semantics.compare_artifacts(old, new, {})["errors"]
    assert bool(errors) == (str(old_value) != str(new_value))
