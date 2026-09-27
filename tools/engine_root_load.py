#!/usr/bin/env python3
"""Load every RuleSpec module in this checkout with the pinned engine.

Repository Checks answers "does each changed module validate?", and it skips
every module with an active known-validation-gaps waiver. It never asks the
question a consumer asks: does axiom-rules-engine, at the revision this
repository pins, load this checkout as a corpus root? Issue #1354 is what that
gap looks like: hundreds of modules on main declared fields the pinned engine
had already removed, and nothing went red.

This tool asks that question with the engine's own library. A small Rust
harness (``HARNESS_SOURCE`` below) is written into an axiom-rules-engine
checkout as a Cargo example and built with ``--locked``, so it links exactly the
pinned engine and its lockfile. The harness admits this checkout once as a
``CanonicalRuleSpecRoots`` root, then compiles every atomic module under
``<jurisdiction>/{legislation,policies,regulations,statutes}/`` with
``CompiledProgramArtifact::from_rulespec_file``, the same entry point as
``axiom-rules-engine compile``. A module the engine refuses on the atomic
surface because it declares ``module.kind: composition`` is also compiled
through ``from_composed_rulespec_file`` from a copy outside the checkout, the
way ``compile-composed`` requires, so a stored composition's own schema drift
is not hidden behind its kind error.

Failures the repository already carries are listed, one per line, in
``tools/known-engine-load-failures.txt`` as ``<surface> <class> <module>``
(tab separated). ``check`` passes only when the failures equal that list
exactly, and, given the protected base's copy, only when the list has not
grown. So a new failure is red, a fixed module must leave the list in the same
change, and the list can only shrink. The one exception is a change that moves
``axiom_rules_engine_ref``: a newer engine may reject what the old one loaded,
and the pin bump is where those failures are listed and reviewed.

Subcommands:
  install-harness  write the harness into an engine checkout's examples/
  run              build the harness and load every module (JSONL results)
  check            compare results with the baseline (the CI gate)
  baseline         print the baseline that exactly matches a results file

Local use (the checkout directory must be named exactly ``rulespec-us``,
because the engine admits only a canonical ``rulespec-<country>`` root):

  python tools/engine_root_load.py run --engine-src ../axiom-rules-engine \\
      --output /tmp/engine-root-load.jsonl
  python tools/engine_root_load.py check --results /tmp/engine-root-load.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE_RELATIVE_PATH = Path("tools") / "known-engine-load-failures.txt"
TOOLCHAIN_RELATIVE_PATH = Path(".axiom") / "workflow-toolchain.toml"
HARNESS_EXAMPLE_NAME = "rulespec_root_load"

ATOMIC = "atomic"
COMPOSED = "composed"
SURFACES = (ATOMIC, COMPOSED)

# The engine's atomic roots (axiom-rules-engine RULESPEC_ATOMIC_ROOTS).
# `programs/` holds ProgramSpecs for axiom-compose, not RuleSpec modules, and
# legacy trees such as `manual/` are not admitted by the engine at all.
MODULE_PATH = re.compile(
    r"^[a-z]{2}(?:-[a-z0-9]+)*/(?:legislation|policies|regulations|statutes)/.+\.yaml$"
)

# Failure classes, most specific first. The class is part of a baseline entry,
# so a module that stops failing for one reason and starts failing for another
# is a new failure, not a silent substitution.
FAILURE_CLASSES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("plural-corpus-citation-paths", re.compile(r"removed plural `corpus_citation_paths`")),
    (
        "source-verification-unknown-field",
        re.compile(r"module\.source_verification: unknown field"),
    ),
    ("module-kind-on-atomic-surface", re.compile(r"must not declare module\.kind")),
    ("invalid-filesystem-path", re.compile(r"invalid filesystem RuleSpec path")),
    ("unresolved-import", re.compile(r"RuleSpec import `[^`]*` in `[^`]*` could not be resolved")),
    ("non-canonical-corpus-citation-path", re.compile(r"non-canonical corpus_citation_path")),
    ("invalid-composed-program", re.compile(r"invalid composed RuleSpec program")),
    ("yaml-parse", re.compile(r"yaml parse error")),
)
OTHER = "other"
KNOWN_CLASSES = frozenset(name for name, _ in FAILURE_CLASSES) | {OTHER}

HARNESS_SOURCE = r"""//! Written by rulespec-us tools/engine_root_load.py; see that file for the
//! contract. Do not edit here: the copy in rulespec-us is the source.
//!
//! usage: rulespec_root_load <absolute rulespec-<cc> root> <module list> <composed scratch dir>
//!
//! The module list holds one root-relative module path per line. Every module
//! yields one JSON line on stdout for the atomic surface; a module the engine
//! refuses on that surface because it itself declares `module.kind` yields a
//! second line for the composed surface, compiled from a copy under the
//! scratch directory (composed programs must sit outside every root).
use std::io::Write;
use std::path::{Path, PathBuf};

use axiom_rules_engine::compile::{CompileError, CompiledProgramArtifact};
use axiom_rules_engine::rulespec::{CanonicalRuleSpecRoots, RuleSpecError};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 4 {
        eprintln!("usage: rulespec_root_load <root> <module list> <composed scratch dir>");
        std::process::exit(2);
    }
    let root = PathBuf::from(&args[1]);
    let composed_dir = PathBuf::from(&args[3]);
    let roots = match CanonicalRuleSpecRoots::new([&root]) {
        Ok(roots) => roots,
        Err(error) => {
            println!("{}", serde_json::json!({ "root_error": error.to_string() }));
            std::process::exit(3);
        }
    };
    let list = std::fs::read_to_string(&args[2]).expect("read module list");
    let stdout = std::io::stdout();
    let mut out = std::io::BufWriter::new(stdout.lock());
    for module in list.lines().filter(|line| !line.is_empty()) {
        let path = root.join(module);
        let atomic = CompiledProgramArtifact::from_rulespec_file(&path, &roots);
        let declares_kind = declares_own_kind(&atomic, &path, module);
        emit(&mut out, module, "atomic", &atomic);
        if declares_kind {
            let copy = composed_dir.join(module);
            std::fs::create_dir_all(copy.parent().expect("module path has a parent"))
                .expect("create composed scratch directory");
            std::fs::copy(&path, &copy).expect("copy composition outside the root");
            let composed = CompiledProgramArtifact::from_composed_rulespec_file(&copy, &roots);
            emit(&mut out, module, "composed", &composed);
        }
    }
    out.flush().expect("flush results");
}

/// True only when the module itself declares `module.kind`, not when an
/// import it pulls in does: the engine names the offending module in the
/// error, by file path for the loaded file or by canonical target otherwise.
fn declares_own_kind(
    result: &Result<CompiledProgramArtifact, CompileError>,
    path: &Path,
    module: &str,
) -> bool {
    let Err(CompileError::RuleSpec {
        error: RuleSpecError::ModuleKindOnAtomicSurface { path: offender },
        ..
    }) = result
    else {
        return false;
    };
    let target = module
        .strip_suffix(".yaml")
        .and_then(|stem| stem.split_once('/'))
        .map(|(jurisdiction, rest)| format!("{jurisdiction}:{rest}"));
    *offender == path.display().to_string() || Some(offender) == target.as_ref()
}

fn emit(
    out: &mut impl Write,
    module: &str,
    surface: &str,
    result: &Result<CompiledProgramArtifact, CompileError>,
) {
    let line = match result {
        Ok(_) => serde_json::json!({ "module": module, "surface": surface, "ok": true }),
        Err(error) => serde_json::json!({
            "module": module,
            "surface": surface,
            "ok": false,
            "error": error.to_string(),
        }),
    };
    writeln!(out, "{line}").expect("write result line");
}
"""


@dataclass(frozen=True, order=True)
class Failure:
    """One baseline entry: a module that fails to load on one surface."""

    surface: str
    failure_class: str
    module: str

    def render(self) -> str:
        return f"{self.surface}\t{self.failure_class}\t{self.module}"


@dataclass(frozen=True)
class Result:
    module: str
    surface: str
    ok: bool
    error: str = ""


def select_modules(paths: Iterable[str]) -> list[str]:
    """Atomic RuleSpec modules among repository-relative paths, sorted."""
    return sorted(
        path for path in paths if MODULE_PATH.match(path) and not path.endswith(".test.yaml")
    )


def tracked_modules(root: Path) -> list[str]:
    listing = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    return select_modules(path for path in listing.split("\0") if path)


def normalize_error(message: str, *prefixes: str) -> str:
    """Strip machine-specific absolute prefixes so messages are stable."""
    for prefix in prefixes:
        if prefix:
            message = message.replace(prefix.rstrip("/") + "/", "")
    return " ".join(message.split())


def classify(message: str) -> str:
    for name, pattern in FAILURE_CLASSES:
        if pattern.search(message):
            return name
    return OTHER


def parse_results(lines: Iterable[str]) -> list[Result]:
    results: list[Result] = []
    for number, raw in enumerate(lines, start=1):
        raw = raw.strip()
        if not raw:
            continue
        record = json.loads(raw)
        if "root_error" in record:
            raise SystemExit(f"engine refused the checkout as a root: {record['root_error']}")
        if record.get("surface") not in SURFACES or not isinstance(record.get("ok"), bool):
            raise SystemExit(f"malformed result on line {number}: {raw}")
        results.append(
            Result(
                module=str(record["module"]),
                surface=record["surface"],
                ok=record["ok"],
                error=str(record.get("error", "")),
            )
        )
    return results


def failures_from_results(results: Iterable[Result]) -> set[Failure]:
    return {
        Failure(result.surface, classify(result.error), result.module)
        for result in results
        if not result.ok
    }


def parse_baseline(text: str) -> set[Failure]:
    entries: set[Failure] = set()
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 3:
            raise ValueError(f"baseline line {number} must be <surface>\\t<class>\\t<module>: {raw!r}")
        surface, failure_class, module = fields
        if surface not in SURFACES:
            raise ValueError(f"baseline line {number} has unknown surface {surface!r}")
        if failure_class not in KNOWN_CLASSES:
            raise ValueError(f"baseline line {number} has unknown class {failure_class!r}")
        if not MODULE_PATH.match(module):
            raise ValueError(f"baseline line {number} is not an atomic module path: {module!r}")
        entry = Failure(surface, failure_class, module)
        if entry in entries:
            raise ValueError(f"baseline line {number} duplicates an earlier entry: {raw!r}")
        entries.add(entry)
    return entries


BASELINE_HEADER = """\
# Modules the pinned axiom-rules-engine does not load from this checkout.
# Format: <surface>\\t<class>\\t<module>, sorted. Maintained by
# tools/engine_root_load.py; the engine-root-load workflow fails when a module
# fails that is not listed, when a listed module no longer fails, or when a
# pull request adds a line. Fix a module, then delete its line.
"""


def render_baseline(entries: Iterable[Failure]) -> str:
    body = "".join(entry.render() + "\n" for entry in sorted(entries))
    return BASELINE_HEADER + body


@dataclass
class Verdict:
    new: set[Failure]
    stale: set[Failure]
    added: set[Failure]

    @property
    def ok(self) -> bool:
        return not (self.new or self.stale or self.added)


def compare(
    failures: set[Failure],
    baseline: set[Failure],
    base_baseline: set[Failure] | None = None,
) -> Verdict:
    """The gate: failures must equal the baseline, which may only shrink."""
    return Verdict(
        new=failures - baseline,
        stale=baseline - failures,
        added=set() if base_baseline is None else baseline - base_baseline,
    )


def check_coverage(results: list[Result], modules: list[str]) -> list[str]:
    """Every selected module must have exactly one atomic result."""
    counts = Counter(result.module for result in results if result.surface == ATOMIC)
    problems = [f"no atomic result for {module}" for module in modules if counts[module] == 0]
    problems += [f"{count} atomic results for {module}" for module, count in counts.items() if count > 1]
    problems += [f"result for unselected module {module}" for module in counts if module not in set(modules)]
    return problems


def install_harness(engine_src: Path) -> Path:
    if not (engine_src / "Cargo.toml").is_file():
        raise SystemExit(f"{engine_src} is not an axiom-rules-engine checkout")
    target = engine_src / "examples" / f"{HARNESS_EXAMPLE_NAME}.rs"
    target.parent.mkdir(exist_ok=True)
    target.write_text(HARNESS_SOURCE, encoding="utf-8")
    return target


def run(engine_src: Path, root: Path, output: Path) -> int:
    root = root.resolve()
    if root.name != "rulespec-us":
        raise SystemExit(f"the engine admits only a root named rulespec-us, not {root.name}")
    install_harness(engine_src)
    subprocess.run(
        ["cargo", "build", "--release", "--locked", "--example", HARNESS_EXAMPLE_NAME],
        cwd=engine_src,
        check=True,
    )
    binary = engine_src / "target" / "release" / "examples" / HARNESS_EXAMPLE_NAME
    modules = tracked_modules(root)
    with tempfile.TemporaryDirectory(prefix="engine-root-load-") as scratch:
        scratch_path = Path(scratch).resolve()
        if scratch_path.is_relative_to(root):
            raise SystemExit("the composed scratch directory must be outside the root")
        module_list = scratch_path / "modules.txt"
        module_list.write_text("".join(f"{module}\n" for module in modules), encoding="utf-8")
        composed = scratch_path / "composed"
        completed = subprocess.run(
            [str(binary), str(root), str(module_list), str(composed)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            sys.stderr.write(completed.stderr)
            sys.stdout.write(completed.stdout)
            raise SystemExit(f"harness exited {completed.returncode}")
        lines = [
            json.dumps(
                {
                    **record,
                    **(
                        {"error": normalize_error(record["error"], str(root), str(composed))}
                        if "error" in record
                        else {}
                    ),
                },
                sort_keys=True,
            )
            for record in map(json.loads, completed.stdout.splitlines())
        ]
    output.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    results = parse_results(lines)
    problems = check_coverage(results, modules)
    if problems:
        raise SystemExit("incomplete harness output:\n  " + "\n  ".join(problems))
    print(summarize(results))
    return 0


def summarize(results: list[Result]) -> str:
    atomic = [result for result in results if result.surface == ATOMIC]
    composed = [result for result in results if result.surface == COMPOSED]
    by_class = Counter(
        (failure.surface, failure.failure_class) for failure in failures_from_results(results)
    )
    lines = [
        f"atomic: {sum(r.ok for r in atomic)}/{len(atomic)} modules load",
        f"composed: {sum(r.ok for r in composed)}/{len(composed)} stored compositions load",
    ]
    lines += [f"  {count:5d} {surface} {name}" for (surface, name), count in sorted(by_class.items())]
    return "\n".join(lines)


def git_show(root: Path, ref: str, path: Path) -> str | None:
    shown = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:{path.as_posix()}"],
        capture_output=True,
        text=True,
    )
    if shown.returncode == 0:
        return shown.stdout
    exists = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{ref}^{{commit}}"],
        capture_output=True,
    )
    if exists.returncode != 0:
        raise SystemExit(f"base ref {ref} is not a commit in {root}")
    return None


def engine_pin(toolchain_text: str | None) -> str | None:
    if toolchain_text is None:
        return None
    return tomllib.loads(toolchain_text).get("workflow_toolchain", {}).get("axiom_rules_engine_ref")


def read_base_baseline(root: Path, base_ref: str) -> set[Failure] | None:
    """The protected base's baseline, or None when it may not bound this one.

    None means the baseline is being introduced, or the change moves the engine
    pin: a newer engine may reject modules the old one loaded, and the pin bump
    is where those new failures get listed and reviewed.
    """
    base_pin = engine_pin(git_show(root, base_ref, TOOLCHAIN_RELATIVE_PATH))
    head_pin = engine_pin((root / TOOLCHAIN_RELATIVE_PATH).read_text(encoding="utf-8"))
    if base_pin != head_pin:
        print(f"Engine pin moves {base_pin} -> {head_pin}; the baseline may grow in this change.")
        return None
    text = git_show(root, base_ref, BASELINE_RELATIVE_PATH)
    return None if text is None else parse_baseline(text)


def check(results_path: Path, baseline_path: Path, root: Path, base_ref: str | None) -> int:
    results = parse_results(results_path.read_text(encoding="utf-8").splitlines())
    problems = check_coverage(results, tracked_modules(root))
    if problems:
        print("Results do not cover this checkout:\n  " + "\n  ".join(problems[:50]))
        return 1
    baseline = parse_baseline(baseline_path.read_text(encoding="utf-8"))
    base_baseline = read_base_baseline(root, base_ref) if base_ref else None
    verdict = compare(failures_from_results(results), baseline, base_baseline)
    errors = {(result.module, result.surface): result.error for result in results if not result.ok}
    print(summarize(results))
    if verdict.new:
        print(f"\n{len(verdict.new)} module(s) fail to load and are not in {baseline_path.name}:")
        for entry in sorted(verdict.new):
            print(f"  {entry.render()}\n    {errors[(entry.module, entry.surface)]}")
    if verdict.stale:
        print(f"\n{len(verdict.stale)} listed module(s) no longer fail this way; delete their lines:")
        for entry in sorted(verdict.stale):
            print(f"  {entry.render()}")
    if verdict.added:
        print(f"\n{len(verdict.added)} line(s) added to {baseline_path.name}; the list may only shrink:")
        for entry in sorted(verdict.added):
            print(f"  {entry.render()}")
    if verdict.ok:
        print(f"\nEngine root load matches {baseline_path.name} ({len(baseline)} known failure(s)).")
        return 0
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    install = sub.add_parser("install-harness", help="write the harness into an engine checkout")
    install.add_argument("--engine-src", type=Path, required=True)

    run_parser = sub.add_parser("run", help="build the harness and load every module")
    run_parser.add_argument("--engine-src", type=Path, required=True)
    run_parser.add_argument("--root", type=Path, default=REPO_ROOT)
    run_parser.add_argument("--output", type=Path, required=True)

    check_parser = sub.add_parser("check", help="compare results with the baseline")
    check_parser.add_argument("--results", type=Path, required=True)
    check_parser.add_argument("--root", type=Path, default=REPO_ROOT)
    check_parser.add_argument("--baseline", type=Path)
    check_parser.add_argument(
        "--base-ref",
        help="protected base commit; its baseline bounds this one (decrement-only)",
    )

    baseline_parser = sub.add_parser("baseline", help="print the baseline matching a results file")
    baseline_parser.add_argument("--results", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "install-harness":
        print(install_harness(args.engine_src))
        return 0
    if args.command == "run":
        return run(args.engine_src, args.root, args.output)
    if args.command == "check":
        baseline_path = args.baseline or args.root / BASELINE_RELATIVE_PATH
        return check(args.results, baseline_path, args.root, args.base_ref)
    results = parse_results(args.results.read_text(encoding="utf-8").splitlines())
    sys.stdout.write(render_baseline(failures_from_results(results)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
