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
* Dates. `from` and `to` are aliases of `effective_from` and `effective_to`, and
  a rule with no `versions` may state one version at the top level.

The comparison is per version, not per rule. When a later version of a rule
adds a reference to an import that starts with it, no date reaches a gap; that
shape is the correct way to encode the change and it is not an edge. An edge
records the earliest such rule version, so its gap is the widest one.

`differential` checks the static model against the engine, because a static
reimplementation drifts from the engine it describes. It compiles each module,
stored compositions through their own surface, reads the references out of the
lowered program, and requires them to equal the static ones. It compiles a
scratch copy of the tree with citation metadata removed: that metadata decides
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
from typing import Any, Iterable, Mapping

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


@dataclass(frozen=True)
class Version:
    start: date
    formula: str = ""


@dataclass(frozen=True)
class Rule:
    name: str
    versions: tuple[Version, ...]

    @property
    def start(self) -> date:
        return min(version.start for version in self.versions)


@dataclass(frozen=True)
class Module:
    imports: tuple[str, ...] = ()
    rules: tuple[Rule, ...] = ()


@dataclass(frozen=True, order=True)
class Reference:
    """One rule version reading a rule that another module defines."""

    rule: str
    version_start: date
    target: str
    target_start: date


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


def _rule_versions(rule: Mapping[str, Any], where: str) -> tuple[Version, ...]:
    """RuleDefinition::effective_versions, keeping the versions that carry a date."""
    raw = rule.get("versions") or [rule]
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


def parse_module(text: str, where: str = "<module>") -> Module:
    """The parts of a module that decide its edges; a module with no date to read
    is one the engine refuses, which the engine-root-load gate reports."""
    document = yaml.load(text, Loader=SafeLoader)
    if not isinstance(document, Mapping):
        raise ValueError(f"{where}: not a RuleSpec mapping")
    rules = []
    for rule in document.get("rules") or []:
        if rule.get("kind") not in VERSIONED_KINDS:
            continue
        name = str(rule["name"])
        versions = _rule_versions(rule, f"{where} rule {name}")
        if versions:
            rules.append(Rule(name, versions))
    return Module(tuple(str(i) for i in document.get("imports") or ()), tuple(rules))


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


def import_references(modules: Mapping[str, Module]) -> set[Reference]:
    """Every (rule version, imported rule) pair, resolved as the engine resolves it.

    A name the module defines itself is a local reference. Otherwise a name two
    imported modules define is one the engine merges (parameters, when their
    declarations agree) or refuses (derived rules), so the earliest definition
    is the one in force first.
    """
    definitions: dict[str, list[tuple[str, Rule]]] = defaultdict(list)
    for origin, module in modules.items():
        for rule in module.rules:
            definitions[rule.name].append((origin, rule))
    references: set[Reference] = set()
    for origin, module in modules.items():
        closure = import_closure(origin, modules)
        if not closure:
            continue
        local = {rule.name for rule in module.rules}
        for rule in module.rules:
            for version in rule.versions:
                for name in formula_references(version.formula) - local:
                    visible = [
                        (candidate.start, f"{owner}#{candidate.name}")
                        for owner, candidate in definitions.get(name, ())
                        if owner in closure
                    ]
                    if visible:
                        target_start, target = min(visible)
                        references.add(
                            Reference(
                                f"{origin}#{rule.name}", version.start, target, target_start
                            )
                        )
    return references


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
//! yields one JSON line on stdout: its compile error, or each reference its own
//! rule versions make to a rule the lowered program says another module defined.
//! A module the engine refuses on the atomic surface because it itself declares
//! `module.kind` is compiled from a copy under the scratch directory instead
//! (composed programs must sit outside every root); its own rules carry no id.
//!
//! The engine reattaches ids by name, so when a local parameter table and an
//! imported derived rule share a name, the derived rule carries the local id
//! and its origin cannot be read. Such rules are named under `shadowed`, not
//! attributed to this module.
use std::collections::{BTreeMap, BTreeSet};
use std::io::Write;
use std::path::PathBuf;

use axiom_rules_engine::compile::{CompileError, CompiledProgramArtifact};
use axiom_rules_engine::rulespec::{CanonicalRuleSpecRoots, RuleSpecError};
use serde_json::{Value, json};

/// Every rule a lowered expression reads, by its tagged spec shape.
fn collect(value: &Value, names: &mut BTreeSet<String>) {
    match value {
        Value::Object(map) => {
            let key = match map.get("kind").and_then(Value::as_str) {
                Some("derived") => "name",
                Some("parameter_lookup") => "parameter",
                _ => "",
            };
            if let Some(name) = map.get(key).and_then(Value::as_str) {
                names.insert(name.to_string());
            }
            map.values().for_each(|child| collect(child, names));
        }
        Value::Array(items) => items.iter().for_each(|child| collect(child, names)),
        _ => {}
    }
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
        let parameters = program.parameters.iter().map(|parameter| {
            let start = parameter.versions.iter().map(|v| v.effective_from).min();
            (parameter.name.as_str(), (parameter.id.as_deref(), start))
        });
        let derived = program.derived.iter().map(|rule| {
            let start = rule.versions.iter().map(|v| v.effective_from).min();
            (rule.name.as_str(), (rule.id.as_deref(), start))
        });
        let catalog: BTreeMap<_, _> = parameters.chain(derived).collect();
        let is_own = |id: Option<&str>| id.is_none_or(|id| id.starts_with(&own));
        let mut references = Vec::new();
        let mut shadowed = Vec::new();
        for rule in &program.derived {
            if !is_own(rule.id.as_deref()) {
                continue;
            }
            if program.parameters.iter().any(|parameter| parameter.name == rule.name) {
                shadowed.push(rule.name.clone());
                continue;
            }
            for version in &rule.versions {
                let semantics = serde_json::to_value(&version.semantics).expect("semantics as json");
                let mut names = BTreeSet::new();
                collect(&semantics, &mut names);
                for name in names {
                    let Some((id, Some(start))) = catalog.get(name.as_str()) else {
                        continue;
                    };
                    if !is_own(*id) {
                        references.push(json!({
                            "rule": format!("{own}{}", rule.name),
                            "version_start": version.effective_from.to_string(),
                            "target": id,
                            "target_start": start.to_string(),
                        }));
                    }
                }
            }
        }
        let line = json!({
            "module": module,
            "ok": true,
            "references": references,
            "shadowed": shadowed,
        });
        writeln!(out, "{line}").expect("write result line");
    }
    out.flush().expect("flush results");
}
"""


def parse_engine_references(
    lines: Iterable[str],
) -> tuple[set[str], set[Reference], list[str]]:
    """The modules the engine compiled, the references it resolved in them, and
    the rule ids it could not attribute."""
    compiled: set[str] = set()
    references: set[Reference] = set()
    shadowed: list[str] = []
    for number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        record = json.loads(raw)
        if "root_error" in record:
            raise SystemExit(f"engine refused the checkout as a root: {record['root_error']}")
        if not isinstance(record.get("ok"), bool) or "module" not in record:
            raise SystemExit(f"malformed result on line {number}: {raw}")
        if not record["ok"]:
            continue
        origin = canonical_target(record["module"])
        compiled.add(origin)
        shadowed += [f"{origin}#{name}" for name in record["shadowed"]]
        references.update(
            Reference(
                item["rule"],
                date.fromisoformat(item["version_start"]),
                item["target"],
                date.fromisoformat(item["target_start"]),
            )
            for item in record["references"]
        )
    return compiled, references, shadowed


def reference_differences(
    compiled: set[str], engine: set[Reference], static: set[Reference]
) -> tuple[set[Reference], set[Reference]]:
    """References only the engine resolved, and only this tool resolved, over the
    modules the engine compiled. Modules it refuses have no engine side."""
    in_scope = {item for item in static if item.rule.split("#", 1)[0] in compiled}
    return engine - in_scope, in_scope - engine


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
    compiled, engine, shadowed = parse_engine_references(completed.stdout.splitlines())
    only_engine, only_static = reference_differences(
        compiled, engine, import_references(load_modules(root))
    )
    print(
        f"The engine compiled {len(compiled)} of {len(modules)} modules without citation "
        f"metadata and resolved {len(engine)} cross-module references in them."
    )
    if shadowed:
        print(f"{len(shadowed)} rule(s) left out, shadowed by a parameter's name: {shadowed}")
    for label, items in (("engine", only_engine), ("static model", only_static)):
        if items:
            print(f"\n{len(items)} reference(s) only the {label} found:")
            for item in sorted(items)[:50]:
                print(f"  {item.rule} {item.version_start} -> {item.target} {item.target_start}")
    if only_engine or only_static:
        return 1
    print("The static references equal the engine's.")
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
