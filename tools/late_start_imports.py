#!/usr/bin/env python3
"""Ratchet the rule versions that read an import before it has any version.

A late-start import edge is a rule version that references a rule or parameter
from another module whose earliest version starts after that rule version
does. On any date between the two, the engine picks the rule version and then
stops on the import, with `derived ... has no formula version at ...` or a
missing parameter value. Compilation lowers formulas without looking at dates,
so a clean compile does not rule the gap out, and only a query that reaches the
import shows it. That is how 26 USC 6012 stopped on 26 USC 7703 (issue #1971).
The encoder's `temporal-dependency-coverage` validator covers references inside
one file and deliberately stops at imports; this check starts there.

The check is static, so it also covers the modules the pinned engine does not
load, 26 USC 6012 among them, and needs no engine build. It follows
axiom-rules-engine at the pin in `.axiom/workflow-toolchain.toml`:

* Scope. The engine merges every imported module into one namespace, and
  follows those modules' imports too. A `#fragment` is validated and dropped,
  so it does not narrow what a formula sees, and a stored composition may not
  write one. A formula name therefore resolves against the whole import closure.
* References. Formula identifiers come from a port of the engine's lexer, so a
  word in a string or comment is not a reference, nor is a called function.
  Only `parameter` and `derived` rules carry versions the engine enforces at
  run time; relation rules do not.
* Namespaces. `kind` does not decide what a name binds to. A rule with `values`
  in any version is a parameter table, of either kind, and its versions without
  `values` do not exist at run time. Otherwise a rule with an `entity`, or with
  a version that is not a lone literal, is derived; the rest are parameters.
  Parameters of one name merge, and a table of that name removes the others.
* Binding. A name in a scalar position binds to a parameter before a derived
  rule, and one in a judgment position binds only to a derived rule. Telling
  the positions apart takes a parser, so a name defined both ways reads both,
  and a parameter read in a judgment position, which lowers to an input, still
  counts. This can only add edges, and `differential` reports each one.
* Dates. `from` and `to` are aliases of `effective_from` and `effective_to`, and
  a rule with no `versions` may state one version at the top level.

A gap here is one a module reaches through its own imports, compiled as its own
root. A root flattens every module it imports, so under a composition a rule can
also bind a name its own module never imports. Those bindings are not import
edges, and this check does not gate them.

The comparison is per version, not per rule. When a later version of a rule
adds a reference to an import that starts with it, no date reaches a gap; that
shape is the correct way to encode the change and it is not an edge. An edge
records the earliest such rule version, so its gap is the widest one.

`differential` checks the static model against the engine, because a static
reimplementation drifts from the engine it describes. It compiles each module,
stored compositions through their own surface, reads every name the lowered
program binds in that module's own rules, and requires those bindings to equal
the static ones by name, namespace and start date. The engine reattaches ids by
name, so it cannot say which module a colliding name came from; the static model
alone decides whether a binding crosses an import. The run must also cover the
tree: every module needs a result, and every edge a compiled module. It compiles
a scratch copy of the tree with citation metadata removed: that metadata decides
nothing here, and retired forms of it would otherwise stop the engine from
loading most of the references this check exists to compare.

Edges the repository already carries are listed, one per line, in
`tools/known-late-start-imports.txt` as
`<rule id>\\t<target id>\\t<version start>\\t<target start>` (tab separated).
`check` passes only when the edges equal that list exactly: an unlisted edge is
red, and a listed edge that no longer holds, or whose dates moved, is red until
its line changes in the same pull request. Against a protected base, a pull
request may not add a (rule, target) pair to the list, because regenerating the
list would otherwise accept any edge. A dated line may still change. A correct
date repair can expose a gap that was already in the law's encoding, and fail
closed where the module used to answer wrongly; the `late-start-import-accepted`
label on the pull request (`--allow-added`) records that decision.

Subcommands:
  check         compare this checkout's edges with the baseline (the CI gate)
  baseline      print the baseline that exactly matches this checkout
  differential  compare the static references with the pinned engine's

Local use:

  python tools/late_start_imports.py check --base-ref origin/main
  python tools/late_start_imports.py baseline > tools/known-late-start-imports.txt
  python tools/late_start_imports.py differential --engine-src ../axiom-rules-engine \\
      --output /tmp/late-start-differential.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

import yaml

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from engine_root_load import (  # noqa: E402 - beside this file
    canonical_target,
    git_show,
    tracked_modules,
)

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

REPO_ROOT = TOOLS.parent
BASELINE_RELATIVE_PATH = Path("tools") / "known-late-start-imports.txt"
HARNESS_EXAMPLE_NAME = "rulespec_import_references"
ACCEPT_LABEL = "late-start-import-accepted"

# Dropped from the scratch tree `differential` compiles. None of these fields
# reaches formula lowering; the engine's corpus contract reads them.
CITATION_KEYS = frozenset({"corpus_citation_path", "corpus_citation_paths", "metadata"})

# The rule kinds the engine lowers to dated versions (RuleKind::Parameter and
# RuleKind::Derived). A derived relation's predicate takes one formula version
# whose date the engine does not read.
VERSIONED_KINDS = frozenset({"parameter", "derived"})

# The two namespaces a lowered formula reads, whatever a rule's `kind` says.
PARAMETER = "parameter"
DERIVED = "derived"

# `differential` refuses a run that compiled less of the tree than this. The
# pinned engine compiled 4,864 of 4,879 modules when this was set.
MINIMUM_COMPILED_SHARE = 0.99

# Keywords, and the two names the engine lowers to period bounds. The lexer
# turns `true` and friends into keyword tokens, so they never name a rule.
RESERVED = frozenset(
    {
        "entity",
        "amend",
        "from",
        "to",
        "match",
        "if",
        "elif",
        "else",
        "and",
        "or",
        "not",
        "true",
        "True",
        "false",
        "False",
        "period_start",
        "period_end",
    }
)

# axiom-rules-engine formula.rs Lexer::tokenise, in its order. Unnamed branches
# consume what is not a name, so that a word inside them yields no token. A
# name holding a slash is the lexer's Path token: `a/b` is one name, not a
# division, and it never equals a rule name.
TOKEN = re.compile(
    r'''
      """.*?(?:"""|\Z)
    | \#[^\n]*
    | "(?:\\.|[^"\\])*"
    | '(?:\\.|[^'\\])*'
    | \d{4}-\d{2}-\d{2}
    | \d[\d_]*(?:\.\d[\d_]*)?
    | (?P<name>[A-Za-z_][A-Za-z0-9_]*(?:/[A-Za-z_][A-Za-z0-9_]*)*)(?P<call>\s*\()?
    ''',
    re.VERBOSE | re.DOTALL,
)

# formula.rs is_literal_expr over the lexer's output: one number, string or
# boolean, and nothing but trivia around it. A leading `-` is an operator.
_TRIVIA = r'''(?:\s+|\#[^\n]*|""".*?(?:"""|\Z))*'''
LITERAL = re.compile(
    _TRIVIA
    + r'''(?:"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\d[\d_]*(?:\.\d[\d_]*)?|true|True|false|False)'''
    + _TRIVIA,
    re.DOTALL,
)


@dataclass(frozen=True)
class Version:
    start: date
    formula: str = ""


@dataclass(frozen=True)
class Rule:
    name: str
    versions: tuple[Version, ...]
    namespace: str = DERIVED
    table: bool = False

    @property
    def start(self) -> date:
        return min(version.start for version in self.versions)


@dataclass(frozen=True)
class Module:
    imports: tuple[str, ...] = ()
    rules: tuple[Rule, ...] = ()


@dataclass(frozen=True, order=True)
class Reference:
    """One rule version reading a name, in the namespace that name binds to."""

    rule: str
    version_start: date
    target: str
    target_start: date
    namespace: str = DERIVED


@dataclass(frozen=True, order=True)
class Edge:
    """One baseline entry: a rule that reads a target before the target starts."""

    rule: str
    target: str
    version_start: date
    target_start: date

    def render(self) -> str:
        return (
            f"{self.rule}\t{self.target}\t{self.version_start.isoformat()}"
            f"\t{self.target_start.isoformat()}"
        )


def formula_references(formula: str) -> frozenset[str]:
    """The names a formula reads: every lexer name that is not reserved or called."""
    return frozenset(
        match["name"]
        for match in TOKEN.finditer(formula)
        if match["name"]
        and not match["call"]
        and "/" not in match["name"]
        and match["name"] not in RESERVED
    )


def _as_date(value: Any, where: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as error:
        raise ValueError(f"{where}: {value!r} is not a date") from error


def _dated(raw: Iterable[Mapping[str, Any]], where: str) -> tuple[Version, ...]:
    versions = []
    for version in raw:
        start = version.get("effective_from", version.get("from"))
        if start is None:
            continue
        formula = version.get("formula")
        versions.append(
            Version(_as_date(start, where), formula if isinstance(formula, str) else "")
        )
    return tuple(versions)


def _is_literal(version: Mapping[str, Any]) -> bool:
    """A YAML number or boolean reaches the formula layer as its literal text. An
    unquoted date is the one other scalar here, and the engine lexes it as a date."""
    formula = version.get("formula")
    if isinstance(formula, str):
        return LITERAL.fullmatch(formula) is not None
    return not isinstance(formula, date)


def parse_rule(rule: Mapping[str, Any], where: str) -> Rule | None:
    """A rule as the engine lowers it, or None when it holds no version to compare.

    This follows to_program_spec_with_options, is_parameter_table and
    to_indexed_parameter_spec in rulespec.rs and lower_module in formula.rs. A
    version with no date, or a rule with no version, is one the engine refuses.
    """
    if rule.get("kind") not in VERSIONED_KINDS:
        return None
    name = str(rule["name"])
    declared = rule.get("versions") or []
    tabled = [version for version in declared if version.get("values")]
    if tabled:
        return Rule(name, _dated(tabled, where), PARAMETER, table=True)
    raw = declared or [rule]
    versions = _dated(raw, where)
    if not versions:
        return None
    if rule.get("entity") or not all(_is_literal(version) for version in raw):
        return Rule(name, versions, DERIVED)
    return Rule(name, versions, PARAMETER)


def parse_module(text: str, where: str = "<module>") -> Module:
    """The parts of a module that decide its edges; a module with no date to read
    is one the engine refuses, which the engine-root-load gate reports."""
    document = yaml.load(text, Loader=SafeLoader)
    if not isinstance(document, Mapping):
        raise ValueError(f"{where}: not a RuleSpec mapping")
    parsed = (
        parse_rule(rule, f"{where} rule {rule.get('name')}")
        for rule in document.get("rules") or []
    )
    return Module(
        tuple(str(i) for i in document.get("imports") or ()),
        tuple(rule for rule in parsed if rule is not None),
    )


def load_modules(root: Path) -> dict[str, Module]:
    """Every tracked atomic module, by canonical target."""
    return {
        canonical_target(path): parse_module(
            (root / path).read_text(encoding="utf-8"), path
        )
        for path in tracked_modules(root)
    }


def import_closure(target: str, modules: Mapping[str, Module]) -> frozenset[str]:
    """Every module `target` reaches through imports, excluding itself.

    An import that resolves to no module is skipped here: the engine refuses
    it, and the engine-root-load gate reports it as `unresolved-import`.
    """
    seen: set[str] = set()
    pending = [target]
    while pending:
        for specifier in modules[pending.pop()].imports:
            imported = specifier.split("#", 1)[0]
            if imported in modules and imported not in seen:
                seen.add(imported)
                pending.append(imported)
    seen.discard(target)
    return frozenset(seen)


def _binding_groups(
    visible: Iterable[tuple[str, Rule]],
) -> Iterator[tuple[str, list[tuple[str, Rule]]]]:
    """The definitions one formula name can read, one group per namespace.

    Parameters of one name merge into one (compile.rs
    normalize_parameter_duplicates), and a table of that name removes the
    scalar ones (`program.parameters.retain`). A second derived definition is a
    compile error, so the derived group holds one rule in any module that loads.
    """
    candidates = list(visible)
    parameters = [item for item in candidates if item[1].namespace == PARAMETER]
    derived = [item for item in candidates if item[1].namespace == DERIVED]
    tables = [item for item in parameters if item[1].table]
    if parameters:
        yield PARAMETER, tables or parameters
    if derived:
        yield DERIVED, derived


def all_references(modules: Mapping[str, Module]) -> set[Reference]:
    """Every (rule version, name) binding, local ones included, for each module
    compiled as its own root. Only derived rules read names: a parameter's
    versions are literals or values. A binding that any local definition feeds
    counts as local, and its target names this module.
    """
    definitions: dict[str, list[tuple[str, Rule]]] = defaultdict(list)
    for origin, module in modules.items():
        for rule in module.rules:
            definitions[rule.name].append((origin, rule))
    references: set[Reference] = set()
    for origin, module in modules.items():
        scope = import_closure(origin, modules) | {origin}
        for rule in module.rules:
            if rule.namespace != DERIVED:
                continue
            for version in rule.versions:
                for name in formula_references(version.formula):
                    visible = (item for item in definitions.get(name, ()) if item[0] in scope)
                    for namespace, group in _binding_groups(visible):
                        target_start, target = min(
                            (candidate.start, f"{owner}#{name}") for owner, candidate in group
                        )
                        if any(owner == origin for owner, _ in group):
                            target = f"{origin}#{name}"
                        references.add(
                            Reference(
                                f"{origin}#{rule.name}",
                                version.start,
                                target,
                                target_start,
                                namespace,
                            )
                        )
    return references


def import_references(modules: Mapping[str, Module]) -> set[Reference]:
    """The bindings that cross an import, which are the ones this check owns. A
    local one belongs to the encoder's temporal-dependency-coverage validator."""
    return {
        item
        for item in all_references(modules)
        if item.rule.split("#", 1)[0] != item.target.split("#", 1)[0]
    }


def late_start_edges(references: Iterable[Reference]) -> set[Edge]:
    """One edge per (rule, target) that starts late, at its earliest rule version."""
    earliest: dict[tuple[str, str], Reference] = {}
    for reference in references:
        if reference.version_start >= reference.target_start:
            continue
        key = (reference.rule, reference.target)
        known = earliest.get(key)
        if known is None or reference.version_start < known.version_start:
            earliest[key] = reference
    return {
        Edge(item.rule, item.target, item.version_start, item.target_start)
        for item in earliest.values()
    }


def module_path(rule_id: str) -> str:
    """`us:statutes/26/6012#x` -> `us/statutes/26/6012.yaml`."""
    jurisdiction, rest = rule_id.split("#", 1)[0].split(":", 1)
    return f"{jurisdiction}/{rest}.yaml"


def parse_baseline(text: str) -> set[Edge]:
    entries: set[Edge] = set()
    for number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        fields = raw.split("\t")
        if len(fields) != 4:
            raise ValueError(
                f"baseline line {number} must be "
                f"<rule>\\t<target>\\t<version start>\\t<target start>: {raw!r}"
            )
        rule, target, version_start, target_start = fields
        if "#" not in rule or "#" not in target:
            raise ValueError(f"baseline line {number} does not name two rule ids: {raw!r}")
        entry = Edge(
            rule,
            target,
            date.fromisoformat(version_start),
            date.fromisoformat(target_start),
        )
        if entry.version_start >= entry.target_start:
            raise ValueError(f"baseline line {number} does not start late: {raw!r}")
        if entry in entries:
            raise ValueError(f"baseline line {number} duplicates an earlier entry: {raw!r}")
        entries.add(entry)
    return entries


BASELINE_HEADER = """\
# Rule versions that read an imported rule before it has any version. On any
# date in the gap the engine stops on the import, and only at run time.
# Format: <rule id>\\t<target id>\\t<version start>\\t<target start>, sorted.
# Maintained by tools/late_start_imports.py; see that file for the definition.
# The check fails when an edge is not listed or a line no longer holds. Repair
# an edge, then regenerate. A pull request may not add a (rule, target) pair
# unless it carries the late-start-import-accepted label.
"""


def render_baseline(entries: Iterable[Edge]) -> str:
    body = "".join(entry.render() + "\n" for entry in sorted(entries))
    return BASELINE_HEADER + body


@dataclass
class Verdict:
    new: set[Edge]
    stale: set[Edge]
    added: set[Edge]

    @property
    def ok(self) -> bool:
        return not (self.new or self.stale or self.added)


def compare(
    edges: set[Edge],
    baseline: set[Edge],
    base_baseline: set[Edge] | None = None,
    allow_added: bool = False,
) -> Verdict:
    """The gate: edges must equal the baseline.

    When base_baseline is supplied, the (rule, target) pairs may only shrink. A
    listed pair may change dates, which the diff shows, because a repair can
    narrow a gap without closing it. `allow_added` is the accepted-label path.
    """
    base_keys = None if base_baseline is None else {_key(entry) for entry in base_baseline}
    return Verdict(
        new=edges - baseline,
        stale=baseline - edges,
        added=set()
        if base_keys is None or allow_added
        else {entry for entry in baseline if _key(entry) not in base_keys},
    )


def _key(entry: Edge) -> tuple[str, str]:
    return entry.rule, entry.target


def summarize(edges: set[Edge]) -> str:
    jurisdictions = Counter(edge.rule.split(":", 1)[0] for edge in edges)
    top = ", ".join(f"{name} {count}" for name, count in jurisdictions.most_common(5))
    return (
        f"{len(edges)} late-start import edge(s): "
        f"{len({edge.rule for edge in edges})} rules, "
        f"{len({module_path(edge.rule) for edge in edges})} importing modules, "
        f"{len({module_path(edge.target) for edge in edges})} target modules"
        + (f" ({top})" if top else "")
    )


def _describe(edge: Edge) -> str:
    return (
        f"{edge.rule} reads {edge.target} from {edge.version_start}, "
        f"but that target starts {edge.target_start}"
    )


def check(root: Path, baseline_path: Path, base_ref: str | None, allow_added: bool) -> int:
    edges = late_start_edges(import_references(load_modules(root)))
    baseline = parse_baseline(baseline_path.read_text(encoding="utf-8"))
    base_baseline = None
    if base_ref:
        text = git_show(root, base_ref, BASELINE_RELATIVE_PATH)
        base_baseline = None if text is None else parse_baseline(text)
    verdict = compare(edges, baseline, base_baseline, allow_added)
    print(summarize(edges))
    if verdict.new:
        print(f"\n{len(verdict.new)} edge(s) are not in {baseline_path.name}:")
        for entry in sorted(verdict.new):
            print(f"  {_describe(entry)}")
        print(
            "\nStart the rule version no earlier than its target, give the target a"
            " version for those dates, or read the target only from a later rule"
            " version. If the dates are the law's, regenerate the baseline."
        )
    if verdict.stale:
        print(f"\n{len(verdict.stale)} listed edge(s) no longer hold this way:")
        for entry in sorted(verdict.stale):
            print(f"  {entry.render()}")
    if verdict.added:
        print(
            f"\n{len(verdict.added)} edge(s) added to {baseline_path.name}; a pull"
            f" request may only shrink the (rule, target) pairs unless it carries"
            f" the {ACCEPT_LABEL} label:"
        )
        for entry in sorted(verdict.added):
            print(f"  {_describe(entry)}")
    if verdict.new or verdict.stale:
        print(
            "\nRegenerate with: python tools/late_start_imports.py baseline"
            f" > {BASELINE_RELATIVE_PATH.as_posix()}"
        )
    if verdict.ok:
        print(f"\nLate-start imports match {baseline_path.name}.")
        return 0
    return 1


HARNESS_SOURCE = r"""//! Written by rulespec-us tools/late_start_imports.py; see that file for the
//! contract. Do not edit here: the copy in rulespec-us is the source.
//!
//! usage: rulespec_import_references <absolute rulespec-<cc> root> <module list> <composed scratch dir>
//!
//! The module list holds one root-relative module path per line. Every module
//! yields one JSON line on stdout: its compile error, or each name its own rule
//! versions read, with the namespace the lowered program bound it to and the
//! earliest version of what that namespace holds. A module the engine refuses on
//! the atomic surface because it itself declares `module.kind` is compiled from
//! a copy under the scratch directory instead (composed programs must sit
//! outside every root); its own rules carry no id.
//!
//! The engine reattaches ids by name, so when a parameter and a derived rule
//! share a name both carry the same id, and the id cannot say which module either
//! came from. `collisions` lists those names for the caller to weigh.
use std::collections::{BTreeMap, BTreeSet};
use std::io::Write;
use std::path::PathBuf;

use axiom_rules_engine::compile::{CompileError, CompiledProgramArtifact};
use axiom_rules_engine::rulespec::{CanonicalRuleSpecRoots, RuleSpecError};
use chrono::NaiveDate;
use serde_json::{Value, json};

/// Every name a lowered expression reads, by namespace, from its tagged spec.
fn collect(value: &Value, read: &mut BTreeSet<(&'static str, String)>) {
    match value {
        Value::Object(map) => {
            let tagged = match map.get("kind").and_then(Value::as_str) {
                Some("derived") => Some(("derived", "name")),
                Some("parameter_lookup") => Some(("parameter", "parameter")),
                Some("input") => Some(("input", "name")),
                _ => None,
            };
            if let Some((namespace, key)) = tagged
                && let Some(name) = map.get(key).and_then(Value::as_str)
            {
                read.insert((namespace, name.to_string()));
            }
            map.values().for_each(|child| collect(child, read));
        }
        Value::Array(items) => items.iter().for_each(|child| collect(child, read)),
        _ => {}
    }
}

fn earliest<'a>(
    starts: impl Iterator<Item = (&'a str, Option<NaiveDate>)>,
) -> BTreeMap<&'a str, NaiveDate> {
    let mut found: BTreeMap<&str, NaiveDate> = BTreeMap::new();
    for (name, start) in starts {
        if let Some(start) = start {
            found
                .entry(name)
                .and_modify(|known| *known = (*known).min(start))
                .or_insert(start);
        }
    }
    found
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 4 {
        eprintln!("usage: rulespec_import_references <root> <module list> <composed scratch dir>");
        std::process::exit(2);
    }
    let root = PathBuf::from(&args[1]);
    let composed_dir = PathBuf::from(&args[3]);
    let roots = match CanonicalRuleSpecRoots::new([&root]) {
        Ok(roots) => roots,
        Err(error) => {
            println!("{}", json!({ "root_error": error.to_string() }));
            std::process::exit(3);
        }
    };
    let list = std::fs::read_to_string(&args[2]).expect("read module list");
    let stdout = std::io::stdout();
    let mut out = std::io::BufWriter::new(stdout.lock());
    for module in list.lines().filter(|line| !line.is_empty()) {
        let (jurisdiction, rest) = module
            .strip_suffix(".yaml")
            .and_then(|stem| stem.split_once('/'))
            .expect("module path");
        let target = format!("{jurisdiction}:{rest}");
        let own = format!("{target}#");
        let path = root.join(module);
        let result = match CompiledProgramArtifact::from_rulespec_file(&path, &roots) {
            Err(CompileError::RuleSpec {
                error: RuleSpecError::ModuleKindOnAtomicSurface { path: offender },
                ..
            }) if offender == target => {
                let copy = composed_dir.join(module);
                std::fs::create_dir_all(copy.parent().expect("module path has a parent"))
                    .expect("create composed scratch directory");
                std::fs::copy(&path, &copy).expect("copy composition outside the root");
                CompiledProgramArtifact::from_composed_rulespec_file(&copy, &roots)
            }
            other => other,
        };
        let artifact = match result {
            Ok(artifact) => artifact,
            Err(error) => {
                let line = json!({ "module": module, "ok": false, "error": error.to_string() });
                writeln!(out, "{line}").expect("write result line");
                continue;
            }
        };
        let program = &artifact.program;
        let parameters = earliest(program.parameters.iter().map(|parameter| {
            let start = parameter.versions.iter().map(|v| v.effective_from).min();
            (parameter.name.as_str(), start)
        }));
        let derived = earliest(program.derived.iter().map(|rule| {
            let start = rule.versions.iter().map(|v| v.effective_from).min();
            (rule.name.as_str(), start)
        }));
        let collisions: Vec<&str> = parameters
            .keys()
            .filter(|name| derived.contains_key(*name))
            .copied()
            .collect();
        let mut references = Vec::new();
        for rule in &program.derived {
            if !rule.id.as_deref().is_none_or(|id| id.starts_with(&own)) {
                continue;
            }
            for version in &rule.versions {
                let semantics = serde_json::to_value(&version.semantics).expect("semantics as json");
                let mut read = BTreeSet::new();
                collect(&semantics, &mut read);
                for (namespace, name) in read {
                    let start = match namespace {
                        "parameter" => parameters.get(name.as_str()).map(|start| start.to_string()),
                        "derived" => derived.get(name.as_str()).map(|start| start.to_string()),
                        _ => None,
                    };
                    if namespace != "input" && start.is_none() {
                        panic!("{module}: {} reads {namespace} {name}, which has no version", rule.name);
                    }
                    references.push(json!({
                        "rule": format!("{own}{}", rule.name),
                        "version_start": version.effective_from.to_string(),
                        "name": name,
                        "namespace": namespace,
                        "target_start": start,
                    }));
                }
            }
        }
        let line = json!({
            "module": module,
            "ok": true,
            "references": references,
            "collisions": collisions,
        });
        writeln!(out, "{line}").expect("write result line");
    }
    out.flush().expect("flush results");
}
"""


@dataclass(frozen=True, order=True)
class Binding:
    """One name a rule version reads: the key both models answer for."""

    rule: str
    version_start: date
    name: str
    namespace: str
    target_start: date | None = None


@dataclass
class EngineRun:
    """What the harness reported. `collisions` holds `<module>#<name>` ids."""

    results: set[str]
    compiled: set[str]
    refused: dict[str, str]
    bindings: set[Binding]
    inputs: set[Binding]
    collisions: set[str]


def parse_engine_references(lines: Iterable[str]) -> EngineRun:
    run = EngineRun(set(), set(), {}, set(), set(), set())
    for number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        record = json.loads(raw)
        if "root_error" in record:
            raise SystemExit(f"engine refused the checkout as a root: {record['root_error']}")
        if not isinstance(record.get("ok"), bool) or "module" not in record:
            raise SystemExit(f"malformed result on line {number}: {raw}")
        origin = canonical_target(record["module"])
        if origin in run.results:
            raise SystemExit(f"second result for {record['module']} on line {number}")
        run.results.add(origin)
        if not record["ok"]:
            run.refused[origin] = record.get("error", "")
            continue
        run.compiled.add(origin)
        run.collisions.update(f"{origin}#{name}" for name in record["collisions"])
        for item in record["references"]:
            start = item["target_start"]
            binding = Binding(
                item["rule"],
                date.fromisoformat(item["version_start"]),
                item["name"],
                item["namespace"],
                None if start is None else date.fromisoformat(start),
            )
            (run.inputs if item["namespace"] == "input" else run.bindings).add(binding)
    return run


def coverage_failures(
    run: EngineRun, tracked: Iterable[str], edges: Iterable[Edge]
) -> list[str]:
    """Why this run cannot vouch for the static model, however well it agreed."""
    expected = {canonical_target(path) for path in tracked}
    failures = []
    if missing := expected - run.results:
        failures.append(f"no result for {len(missing)} module(s): {sorted(missing)[:10]}")
    if unexpected := run.results - expected:
        failures.append(f"results for untracked module(s): {sorted(unexpected)[:10]}")
    if len(run.compiled) < MINIMUM_COMPILED_SHARE * len(expected):
        failures.append(
            f"the engine compiled {len(run.compiled)} of {len(expected)} modules, below"
            f" the {MINIMUM_COMPILED_SHARE:.0%} floor"
        )
    uncovered = sorted(
        edge.rule for edge in edges if edge.rule.split("#", 1)[0] not in run.compiled
    )
    if uncovered:
        failures.append(f"{len(uncovered)} edge(s) in modules the engine refused: {uncovered[:10]}")
    return failures


def _binding(reference: Reference) -> Binding:
    return Binding(
        reference.rule,
        reference.version_start,
        reference.target.split("#", 1)[1],
        reference.namespace,
        reference.target_start,
    )


@dataclass
class Differences:
    only_engine: set[Binding]
    only_static: set[Binding]
    # Static bindings the model reads by design and the lowered program does
    # not: both sides of a collision, and a parameter read in a judgment
    # position, which lowers to an input. Each can only add an edge.
    over_reported: set[Binding]


def reference_differences(
    run: EngineRun, static: set[Reference], modules: Mapping[str, Module]
) -> Differences:
    """Compare the two models over the modules the engine compiled.

    A rule's id can come from a colliding name, so the harness may report an
    imported derived rule as a module's own. Its bindings say nothing about that
    module, and they drop out here.
    """

    def declared(rule: str) -> bool:
        origin, name = rule.split("#", 1)
        return any(
            item.name == name and item.namespace == DERIVED for item in modules[origin].rules
        )

    in_scope = {
        _binding(item) for item in static if item.rule.split("#", 1)[0] in run.compiled
    }
    engine = {
        item for item in run.bindings if item.rule not in run.collisions or declared(item.rule)
    }
    inputs = {(item.rule, item.version_start, item.name) for item in run.inputs}
    only_static = in_scope - engine
    over_reported = {
        item
        for item in only_static
        if f"{item.rule.split('#', 1)[0]}#{item.name}" in run.collisions
        or (
            item.namespace == PARAMETER
            and (item.rule, item.version_start, item.name) in inputs
        )
    }
    return Differences(engine - in_scope, only_static - over_reported, over_reported)


def without_citation_metadata(document: Any) -> Any:
    """A module's executable content: its imports and rules, and `module.kind`."""
    if isinstance(document, list):
        return [without_citation_metadata(item) for item in document]
    if not isinstance(document, dict):
        return document
    return {
        key: without_citation_metadata(value)
        for key, value in document.items()
        if key not in CITATION_KEYS
    }


def write_scratch_root(root: Path, modules: Iterable[str], scratch: Path) -> Path:
    """Copy the modules' executable content to a root the engine will admit."""
    scratch_root = scratch / "rulespec-us"
    for path in modules:
        document = yaml.load((root / path).read_text(encoding="utf-8"), Loader=SafeLoader)
        kind = (document.get("module") or {}).get("kind")
        document["module"] = {"kind": kind} if kind else {}
        document["imports"] = document.get("imports") or []
        target = scratch_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            yaml.safe_dump(without_citation_metadata(document), sort_keys=False),
            encoding="utf-8",
        )
    return scratch_root


def differential(engine_src: Path, root: Path, output: Path) -> int:
    root = root.resolve()
    if not (engine_src / "Cargo.toml").is_file():
        raise SystemExit(f"{engine_src} is not an axiom-rules-engine checkout")
    example = engine_src / "examples" / f"{HARNESS_EXAMPLE_NAME}.rs"
    example.parent.mkdir(exist_ok=True)
    example.write_text(HARNESS_SOURCE, encoding="utf-8")
    subprocess.run(
        ["cargo", "build", "--release", "--locked", "--example", HARNESS_EXAMPLE_NAME],
        cwd=engine_src,
        check=True,
    )
    binary = engine_src / "target" / "release" / "examples" / HARNESS_EXAMPLE_NAME
    modules = tracked_modules(root)
    with tempfile.TemporaryDirectory(prefix="late-start-imports-") as scratch:
        scratch_path = Path(scratch).resolve()
        scratch_root = write_scratch_root(root, modules, scratch_path)
        module_list = scratch_path / "modules.txt"
        module_list.write_text("".join(f"{module}\n" for module in modules), encoding="utf-8")
        completed = subprocess.run(
            [str(binary), str(scratch_root), str(module_list), str(scratch_path / "composed")],
            check=False,
            capture_output=True,
            text=True,
        )
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        sys.stdout.write(completed.stdout)
        raise SystemExit(f"harness exited {completed.returncode}")
    output.write_text(completed.stdout, encoding="utf-8")
    run = parse_engine_references(completed.stdout.splitlines())
    static_modules = load_modules(root)
    static = all_references(static_modules)
    failures = coverage_failures(run, modules, late_start_edges(import_references(static_modules)))
    differences = reference_differences(run, static, static_modules)
    print(
        f"The engine compiled {len(run.compiled)} of {len(modules)} modules without citation "
        f"metadata and bound {len(run.bindings)} names in their own rules."
    )
    for module, error in sorted(run.refused.items())[:20]:
        reason = error.splitlines()[0].rsplit("`: ", 1)[-1] if error else ""
        print(f"  refused {module}: {reason}")
    if run.collisions:
        print(f"{len(run.collisions)} name(s) bound in both namespaces: {sorted(run.collisions)}")
    if differences.over_reported:
        print(f"{len(differences.over_reported)} static binding(s) over-reported by design:")
        for item in sorted(differences.over_reported)[:20]:
            print(f"  {item.rule} {item.version_start} -> {item.namespace} {item.name}")
    for label, items in (
        ("engine", differences.only_engine),
        ("static model", differences.only_static),
    ):
        if items:
            print(f"\n{len(items)} binding(s) only the {label} found:")
            for item in sorted(items, key=str)[:50]:
                print(
                    f"  {item.rule} {item.version_start} -> {item.namespace} {item.name}"
                    f" {item.target_start}"
                )
    for failure in failures:
        print(f"\nThis run does not cover the tree: {failure}")
    if differences.only_engine or differences.only_static or failures:
        return 1
    print("The static bindings equal the engine's.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    check_parser = sub.add_parser("check", help="compare edges with the baseline")
    check_parser.add_argument("--root", type=Path, default=REPO_ROOT)
    check_parser.add_argument("--baseline", type=Path)
    check_parser.add_argument("--base-ref", help="protected base commit; its baseline bounds this one")
    check_parser.add_argument(
        "--allow-added",
        action="store_true",
        help=f"the pull request carries the {ACCEPT_LABEL} label",
    )

    baseline_parser = sub.add_parser("baseline", help="print the baseline matching this checkout")
    baseline_parser.add_argument("--root", type=Path, default=REPO_ROOT)

    differential_parser = sub.add_parser(
        "differential", help="compare static references with the pinned engine's"
    )
    differential_parser.add_argument("--engine-src", type=Path, required=True)
    differential_parser.add_argument("--root", type=Path, default=REPO_ROOT)
    differential_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "check":
        baseline_path = args.baseline or args.root / BASELINE_RELATIVE_PATH
        return check(args.root, baseline_path, args.base_ref, args.allow_added)
    if args.command == "differential":
        return differential(args.engine_src, args.root, args.output)
    edges = late_start_edges(import_references(load_modules(args.root)))
    sys.stdout.write(render_baseline(edges))
    return 0


if __name__ == "__main__":
    sys.exit(main())
