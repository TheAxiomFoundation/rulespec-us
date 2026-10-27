#!/usr/bin/env python3
"""Check the dated-derived-rule fix against paired old/new program artifacts.

The old 98af0dce compiler drops a derived rule's only *open-ended* version.
It already preserves a lone version with effective_to (formula.rs:1205).
This check permits precisely the restoration of the open-ended version and
checks new single-version dates against their actual source. Everything else
the engine executes must be identical: derived formula ASTs, parameters
(values, dates, unit, index), relations, unit definitions, selected-year
inputs and the artifact format. Descriptive rule and parameter fields are
reported separately, never normalized inside formula ASTs. Changes the engine
does not execute (module metadata, advisory fast-path metadata, producer
stamps, added unit definitions) are listed under schema_changes.

Both directories should contain the same composer output beside their
*.compiled.json files. Imported rules are resolved through their canonical id;
originless composition rules are read from the matching *.rulespec.yaml.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping

import yaml

# These fields are descriptive according to engine spec.rs / model.rs. In
# particular, do not remove fields recursively: "source" inside an expression
# can be executable, and every unknown derived field must still be compared.
# `id` is executable: model.rs resolve_derived_name / resolve_parameter_name
# resolve a query's output reference through it.
DESCRIPTIVE_RULE_FIELDS = frozenset({"source", "source_url", "corpus_citation_path"})
# spec.rs IndexedParameterSpec carries the same descriptive fields for
# consumers; lowering reads a parameter's unit, indexed_by and versions.
DESCRIPTIVE_PARAMETER_FIELDS = DESCRIPTIVE_RULE_FIELDS
# spec.rs `id` is an Option with serde(default, skip_serializing_if = None):
# null and omission are one value.
OPTIONAL_ID = {"id": None}
# spec.rs ProgramSpec: `module` is pass-through metadata ("execution semantics
# do not depend on it"). Every other section executes.
DESCRIPTIVE_PROGRAM_SECTIONS = frozenset({"module"})
# Fields whose serde default makes omission equal to this value.
RELATION_DEFAULTS = {"slot_entities": [], "derivation": None}
DERIVATION_DEFAULTS = {"entity": None, "member_relation": None, "slot_entities": []}


@dataclass(frozen=True)
class SourceRule:
    path: str
    rule: dict[str, Any]
    bindings: tuple[str, ...] = ()


def effective_versions(rule: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Mirror RuleDefinition::effective_versions without lowering formulas."""
    def canonical_dates(version: Mapping[str, Any]) -> dict[str, Any]:
        result = dict(version)
        for canonical, alias in (("effective_from", "from"), ("effective_to", "to")):
            if canonical in result and alias in result:
                raise ValueError(f"source declares both {canonical} and its alias {alias}")
            if alias in result:
                result[canonical] = result.pop(alias)
        return result

    if rule.get("versions"):
        return [canonical_dates(version) for version in rule["versions"]]
    canonical_rule = canonical_dates(rule)
    if canonical_rule.get("formula") is not None or canonical_rule.get("effective_from") is not None:
        return [{key: canonical_rule.get(key) for key in (
            "effective_from", "effective_to", "formula"
        )}]
    return []


def _date(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if isinstance(value, date) else str(value)


def _single_dated_version(source: SourceRule) -> dict[str, Any] | None:
    versions = effective_versions(source.rule)
    if len(versions) == 1 and versions[0].get("effective_from") is not None:
        return versions[0]
    return None


def _derived_by_name(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rules = artifact["program"].get("derived", [])
    indexed = {rule["name"]: rule for rule in rules}
    if len(indexed) != len(rules):
        raise ValueError("artifact has duplicate derived rule names")
    return indexed


def _executable_rule(rule: Mapping[str, Any]) -> dict[str, Any]:
    result = _without_defaults({key: value for key, value in rule.items()
                                if key not in DESCRIPTIVE_RULE_FIELDS}, OPTIONAL_ID)
    result.setdefault("versions", [])
    # Omission and null represent the same unbounded end in the artifact schema.
    for version in result["versions"]:
        version.setdefault("effective_to", None)
    return result


def _without_defaults(value: Mapping[str, Any], defaults: Mapping[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(item) for key, item in value.items()
            if not (key in defaults and item == defaults[key])}


def _executable_parameter(parameter: Mapping[str, Any]) -> dict[str, Any]:
    result = {key: deepcopy(value) for key, value in parameter.items()
              if key not in DESCRIPTIVE_PARAMETER_FIELDS}
    # unit, indexed_by and id are Options, so null and omission are one value.
    result = _without_defaults(result, {"unit": None, "indexed_by": None, **OPTIONAL_ID})
    result.setdefault("versions", [])
    for version in result["versions"]:
        version.setdefault("effective_to", None)
    return result


def _executable_relation(relation: Mapping[str, Any]) -> dict[str, Any]:
    result = _without_defaults(relation, RELATION_DEFAULTS)
    if isinstance(result.get("derivation"), dict):
        result["derivation"] = _without_defaults(result["derivation"], DERIVATION_DEFAULTS)
    return result


def _grouped(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Index by name, keeping order; the loader collapses compatible parameter duplicates."""
    result: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        result.setdefault(item["name"], []).append(item)
    return result


def _compare_named(label, old_items, new_items, executable, descriptive_fields=frozenset()):
    errors, descriptive = [], []
    old_index, new_index = _grouped(old_items), _grouped(new_items)
    for name in sorted(old_index.keys() | new_index.keys()):
        before, after = old_index.get(name, []), new_index.get(name, [])
        if len(before) != len(after):
            errors.append({label: name, "error": f"{label} set changed",
                           "old_count": len(before), "new_count": len(after)})
            continue
        for left, right in zip(before, after):
            errors.extend({label: name, "error": f"unexpected {label} executable change", **delta}
                          for delta in _deltas(executable(left), executable(right)))
            for field in sorted(descriptive_fields):
                if left.get(field) != right.get(field):
                    descriptive.append({label: name, "field": field,
                                        "old": left.get(field), "new": right.get(field)})
    return errors, descriptive


def _strings(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        return set().union(*map(_strings, value.values()))
    if isinstance(value, list):
        return set().union(*map(_strings, value))
    return set()


def _compare_units(old_units, new_units, old_references=frozenset()):
    """A unit definition acts only through the names that reference it. An
    old reference to an undefined unit fails (engine.rs validate_unit,
    UnknownUnit), so defining that unit changes execution. A unit may be
    added only when no old executable string names it; an existing
    definition may not change or disappear."""
    errors, added = [], []
    old_index, new_index = _grouped(old_units), _grouped(new_units)
    for name in sorted(old_index.keys() | new_index.keys()):
        if name not in old_index and name in old_references:
            errors.append({"unit": name, "error": "unit added that the old program references",
                           "new": new_index[name]})
        elif name not in old_index:
            added.append({"path": f"program.units.{name}", "change": "added",
                          "new": new_index[name],
                          "reason": "unit definition added; no old reference names it"})
        elif old_index[name] != new_index.get(name):
            errors.append({"unit": name, "error": "unit definition changed or removed",
                           "old": old_index[name], "new": new_index.get(name)})
    return errors, added


def _presence_change(path, old, new, key, reason, *, values=False):
    change = {"path": path, "change": "added" if key not in old else
              "removed" if key not in new else "changed", "reason": reason}
    if values:
        change.update(old=old.get(key), new=new.get(key))
    return change


def compare_program(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, Any]:
    """Compare every artifact field outside program.derived.

    compile.rs CompiledProgramArtifact is {artifact_format_version,
    engine_version, program, metadata}. The loader recomputes
    metadata.evaluation_order and input_catalog from the program and checks
    them, so a present value must agree; fast_path is advisory ("Execution
    never reads it"); other metadata keys, such as the producer's provenance
    stamp, are not CompiledProgramMetadata fields and the loader ignores them.
    """
    errors, descriptive, schema = [], [], []
    for key in sorted(old.keys() | new.keys()):
        if key in {"program", "metadata"}:
            continue
        if key == "engine_version":
            if old.get(key) != new.get(key):
                schema.append(_presence_change(key, old, new, key, "compiler identity", values=True))
        elif key not in old or key not in new or old[key] != new[key]:
            errors.append({"path": key, "error": "unexpected artifact field change",
                           "old": old.get(key), "new": new.get(key)})

    old_meta, new_meta = old.get("metadata") or {}, new.get("metadata") or {}
    for key in sorted(old_meta.keys() | new_meta.keys()):
        path = f"metadata.{key}"
        both = key in old_meta and key in new_meta
        if key == "evaluation_order" and (not both or old_meta[key] != new_meta[key]):
            errors.append({"path": path, "error": "evaluation order changed",
                           "old": old_meta.get(key), "new": new_meta.get(key)})
        elif key == "input_catalog":
            if both and old_meta[key] != new_meta[key]:
                errors.append({"path": path, "error": "input catalog changed"})
            elif not both:
                schema.append(_presence_change(path, old_meta, new_meta, key,
                              "the loader fills an absent catalog from the program"))
        elif key == "fast_path":
            if not both or old_meta[key] != new_meta[key]:
                schema.append(_presence_change(path, old_meta, new_meta, key,
                              "advisory; execution never reads it", values=True))
        elif key != "evaluation_order" and (not both or old_meta[key] != new_meta[key]):
            schema.append(_presence_change(path, old_meta, new_meta, key,
                          "not a CompiledProgramMetadata field; the loader ignores it"))

    old_program, new_program = old.get("program") or {}, new.get("program") or {}
    counts = {"parameters_compared": len(new_program.get("parameters") or []),
              "relations_compared": len(new_program.get("relations") or [])}
    for section in sorted(old_program.keys() | new_program.keys()):
        before, after = old_program.get(section), new_program.get(section)
        path = f"program.{section}"
        if section == "derived":
            continue
        if section in DESCRIPTIVE_PROGRAM_SECTIONS:
            descriptive.extend({"section": path, **delta}
                               for delta in _deltas(before or {}, after or {}, path))
        elif section == "units":
            # Fail closed: any old string outside the pass-through module
            # counts as a possible reference.
            references = _strings([value for key, value in old_program.items()
                                   if key not in DESCRIPTIVE_PROGRAM_SECTIONS]
                                  + [old_meta.get("input_catalog")])
            unit_errors, added = _compare_units(before or [], after or [], references)
            errors.extend(unit_errors)
            schema.extend(added)
        elif section == "parameters":
            found, notes = _compare_named("parameter", before or [], after or [],
                                          _executable_parameter, DESCRIPTIVE_PARAMETER_FIELDS)
            errors.extend(found)
            descriptive.extend(notes)
        elif section == "relations":
            found, _ = _compare_named("relation", before or [], after or [], _executable_relation)
            errors.extend(found)
        elif section == "selected_year_inputs":
            errors.extend({"error": "unexpected selected-year input change", **delta}
                          for delta in _deltas(before or [], after or [], path))
        elif before is None and after is None:
            # Not a ProgramSpec field on this engine; null and absent agree.
            if (section in old_program) != (section in new_program):
                schema.append(_presence_change(path, old_program, new_program, section,
                              "unknown section; null and absent are equal", values=True))
        else:
            errors.append({"path": path, "error": "unknown program section changed",
                           "old": before, "new": after})
    return {**counts, "descriptive_changes": descriptive, "schema_changes": schema,
            "errors": errors}


def _deltas(old: Any, new: Any, path: str = "") -> list[dict[str, Any]]:
    """Return exact JSON differences, including paths and values for review."""
    if isinstance(old, dict) and isinstance(new, dict):
        result = []
        for key in sorted(old.keys() | new.keys()):
            location = f"{path}.{key}" if path else key
            if key not in old:
                result.append({"path": location, "old_missing": True, "new": new[key]})
            elif key not in new:
                result.append({"path": location, "old": old[key], "new_missing": True})
            else:
                result.extend(_deltas(old[key], new[key], location))
        return result
    if isinstance(old, list) and isinstance(new, list) and len(old) == len(new):
        return [delta for index, (left, right) in enumerate(zip(old, new))
                for delta in _deltas(left, right, f"{path}[{index}]")]
    if type(old) is not type(new) or old != new:
        return [{"path": path, "old": old, "new": new}]
    return []


def check_new_artifact(
    artifact: dict[str, Any], source_rules: Mapping[str, SourceRule]
) -> dict[str, Any]:
    """Check every new derived rule, failing closed on missing source evidence."""
    errors = []
    single_dated = 0
    bounded_single = 0
    rules = _derived_by_name(artifact)
    for name, rule in sorted(rules.items()):
        source = source_rules.get(name)
        if source is None:
            errors.append({"rule": name, "error": "source rule is unresolved"})
            continue
        # The formula layer lowers entity-free computed parameters to derived
        # rules on synthetic Scalar. Source kind alone does not determine the
        # executable category (formula.rs::is_parameter_variable).
        if source.rule.get("kind") not in {"derived", "parameter"}:
            errors.append({"rule": name, "source": source.path,
                           "error": "artifact derived rule has a non-executable source kind"})
            continue
        version = _single_dated_version(source)
        if version is None:
            continue
        single_dated += 1
        bounded_single += version.get("effective_to") is not None
        actual = rule.get("versions", [])
        if len(actual) != 1:
            errors.append({"rule": name, "source": source.path,
                           "error": "single dated source version must remain exactly one artifact version",
                           "expected_count": 1, "actual_count": len(actual)})
            continue
        for field in ("effective_from", "effective_to"):
            expected_date, actual_date = _date(version.get(field)), _date(actual[0].get(field))
            if expected_date != actual_date:
                errors.append({"rule": name, "source": source.path,
                               "error": f"source {field} was not preserved",
                               "expected": expected_date, "actual": actual_date})
    return {"derived_rules": len(rules), "single_dated_rules": single_dated,
            "bounded_single_rules": bounded_single, "errors": errors}


def compare_artifacts(
    old: dict[str, Any], new: dict[str, Any], source_rules: Mapping[str, SourceRule]
) -> dict[str, Any]:
    """Permit only the verified 98af0dce single-open-version lowering defect."""
    invariants = check_new_artifact(new, source_rules)
    errors = list(invariants["errors"])
    old_rules, new_rules = _derived_by_name(old), _derived_by_name(new)
    restored, descriptive = [], []
    unchanged = 0
    for name in sorted(old_rules.keys() | new_rules.keys()):
        if name not in old_rules or name not in new_rules:
            errors.append({"rule": name, "error": "derived rule set changed",
                           "in_old": name in old_rules, "in_new": name in new_rules})
            continue
        before, after = _executable_rule(old_rules[name]), _executable_rule(new_rules[name])
        source = source_rules.get(name)
        version = _single_dated_version(source) if source else None
        if version is not None and version.get("effective_to") is None:
            if before["versions"]:
                errors.append({"rule": name, "source": source.path,
                               "error": "old 98af0dce artifact unexpectedly retained its single open-ended version"})
            elif len(after["versions"]) == 1:
                actual = after["versions"][0]
                semantics = {key: value for key, value in actual.items()
                             if key not in {"effective_from", "effective_to"}}
                # The restored AST must be precisely the previously timeless AST
                # and the new fallback AST; a date-only comparison misses edits.
                for label, rule in (("old", before), ("new", after)):
                    fallback = {key: rule[key] for key in ("semantics", "expr") if key in rule}
                    for delta in _deltas(fallback, semantics, "versions[0]"):
                        errors.append({"rule": name, "error": f"restored version differs from {label} fallback semantics", **delta})
                restored.append({"rule": name, "source": source.path,
                                 "effective_from": _date(version["effective_from"]),
                                 "effective_to": None,
                                 "source_relation_bindings": list(source.bindings)})
                after["versions"] = []
        changes = _deltas(before, after)
        errors.extend({"rule": name, "error": "unexpected derived executable change", **delta}
                      for delta in changes)
        if not changes and not (version is not None and version.get("effective_to") is None):
            unchanged += 1
        for field in sorted(DESCRIPTIVE_RULE_FIELDS):
            if old_rules[name].get(field) != new_rules[name].get(field):
                descriptive.append({"rule": name, "field": field,
                                    "old": old_rules[name].get(field),
                                    "new": new_rules[name].get(field)})
    rest = compare_program(old, new)
    return {"derived_rules": len(new_rules), "single_dated_rules": invariants["single_dated_rules"],
            "bounded_single_rules": invariants["bounded_single_rules"],
            "parameters_compared": rest["parameters_compared"],
            "relations_compared": rest["relations_compared"],
            "restored_open_versions": restored, "unchanged_rules": unchanged,
            "descriptive_changes": descriptive + rest["descriptive_changes"],
            "schema_changes": rest["schema_changes"], "errors": errors + rest["errors"]}


class SourceIndex:
    """Resolve canonical ids only within explicitly supplied country roots."""

    def __init__(self, roots: list[Path]):
        self.roots = [root.resolve() for root in roots]
        self.documents: dict[Path, dict[str, Any]] = {}

    def _document(self, path: Path) -> dict[str, Any]:
        if path not in self.documents:
            document = yaml.safe_load(path.read_text())
            if not isinstance(document, dict):
                raise ValueError(f"{path}: source document is not a mapping")
            self.documents[path] = document
        return self.documents[path]

    def _module_path(self, target: str) -> Path:
        jurisdiction, separator, relative = target.partition(":")
        parts = PurePosixPath(relative).parts
        if not separator or not re.fullmatch(r"[a-z]{2}(?:-[a-z0-9]+)*", jurisdiction) or not parts or any(
            part in {".", "..", "/"} for part in parts
        ) or any(part in {"", ".", ".."} for part in relative.split("/")):
            raise ValueError(f"noncanonical source module target: {target!r}")
        if relative.endswith((".yaml", ".yml")):
            raise ValueError(f"source target must omit its YAML suffix: {target!r}")
        candidates = [root / jurisdiction / f"{relative}.yaml" for root in self.roots]
        matches = [path for path in candidates if path.is_file()]
        if len(matches) != 1:
            raise ValueError(f"{target}: expected exactly one source module in explicit roots, found {len(matches)}")
        return matches[0]

    def _ordered_documents(self, composition: Path) -> list[tuple[Path, dict[str, Any]]]:
        """Mirror the engine's imports-first, once-per-module merge order."""
        loaded, loading = set(), set()
        documents = []

        def visit(path: Path):
            if path in loading:
                raise ValueError(f"{path}: source import cycle")
            if path in loaded:
                return
            loading.add(path)
            document = self._document(path)
            # serde_yaml accepts an empty `imports:` value on the validated
            # TX TANF compile path; PyYAML represents that value as None.
            imports = document.get("imports")
            for dependency in [] if imports is None else imports:
                target = dependency.split("#", 1)[0]
                visit(self._module_path(target))
            documents.append((path, document))
            loaded.add(path)
            loading.remove(path)

        visit(composition)
        return documents

    def rules_for_artifact(
        self, artifact: dict[str, Any], composition: Path
    ) -> dict[str, SourceRule]:
        result = {}
        for name, rule in _derived_by_name(artifact).items():
            identity = rule.get("id")
            if identity:
                target, separator, source_name = identity.partition("#")
                if not separator or source_name != name:
                    raise ValueError(f"{name}: invalid canonical rule id {identity!r}")
                path = self._module_path(target)
            else:
                path = composition
            candidates = [candidate for candidate in self._document(path).get("rules", [])
                          if candidate.get("name") == name]
            if len(candidates) != 1:
                raise ValueError(f"{path}: expected exactly one source rule {name!r}, found {len(candidates)}")
            result[name] = SourceRule(str(path), candidates[0])
        # `sets` is an executable compile-time binding. The engine preserves a
        # target's id while replacing its semantics and versions from `value`.
        # Check dates against that effective producer, replaying only bindings
        # whose two derived endpoints exist in this artifact. Parameter sets do
        # not alter any derived rule and need no handling here.
        identities = {rule["id"]: name for name, rule in _derived_by_name(artifact).items()
                      if rule.get("id")}
        for path, document in self._ordered_documents(composition):
            for declaration in document.get("rules", []):
                relation = declaration.get("source_relation") or {}
                target, value = relation.get("target"), relation.get("value")
                if relation.get("type") != "sets" or target == value:
                    continue
                if target in identities and value in identities:
                    producer = result[identities[value]]
                    binding = f"{path}#{declaration['name']}: {target} <- {value}"
                    result[identities[target]] = SourceRule(
                        producer.path, producer.rule, (*producer.bindings, binding)
                    )
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-dir", type=Path, required=True)
    parser.add_argument("--new-dir", type=Path, required=True)
    parser.add_argument("--rulespec-root", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if any(not root.is_absolute() for root in args.rulespec_root):
        parser.error("--rulespec-root must be absolute")
    old_paths = {path.name: path for path in args.old_dir.glob("*.compiled.json")}
    new_paths = {path.name: path for path in args.new_dir.glob("*.compiled.json")}
    paired = sorted(old_paths.keys() & new_paths.keys())
    index = SourceIndex(args.rulespec_root)
    comparisons, new_checks = [], []
    for name, path in sorted(new_paths.items()):
        try:
            artifact = json.loads(path.read_text())
            composition = path.with_name(name.removesuffix(".compiled.json") + ".rulespec.yaml")
            sources = index.rules_for_artifact(artifact, composition)
            checked = check_new_artifact(artifact, sources)
            new_checks.append({"artifact": name, **checked})
            if name in old_paths:
                old = json.loads(old_paths[name].read_text())
                comparison = compare_artifacts(old, artifact, sources)
                # Report invariant errors once, under new_artifact_invariants.
                comparison["errors"] = comparison["errors"][len(checked["errors"]):]
                comparisons.append({"artifact": name, **comparison})
        except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
            new_checks.append({"artifact": name, "errors": [{"error": str(error)}]})
    error_count = sum(len(item["errors"]) for item in new_checks + comparisons)
    summary = {
        "new_artifacts": len(new_paths), "old_artifacts": len(old_paths),
        "paired_artifacts": len(paired), "comparisons_completed": len(comparisons),
        "derived_rules_compared": sum(item["derived_rules"] for item in comparisons),
        "parameters_compared": sum(item["parameters_compared"] for item in comparisons),
        "relations_compared": sum(item["relations_compared"] for item in comparisons),
        "schema_changes": sum(len(item["schema_changes"]) for item in comparisons),
        "descriptive_changes": sum(len(item["descriptive_changes"]) for item in comparisons),
        "restored_open_versions": sum(len(item["restored_open_versions"]) for item in comparisons),
        "bounded_single_rules": sum(item["bounded_single_rules"] for item in comparisons),
        "unchanged_rules": sum(item["unchanged_rules"] for item in comparisons),
        "errors": error_count,
    }
    report = {"summary": summary,
              "old_only": sorted(old_paths.keys() - new_paths.keys()),
              "new_only": sorted(new_paths.keys() - old_paths.keys()),
              "new_artifact_invariants": new_checks, "comparisons": comparisons}
    if not paired:
        report["coverage_error"] = "no artifacts were built by both compilers"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))
    return int(bool(error_count or not paired or len(comparisons) != len(paired)))


if __name__ == "__main__":
    raise SystemExit(main())
