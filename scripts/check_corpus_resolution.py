#!/usr/bin/env python3
"""Detect producer/consumer naming desyncs in a rulespec-us program domain.

Per-file CI catches per-file errors. It does NOT catch the case where two
modules in different files use different names for the same legal concept,
because the engine treats unresolved name references as external inputs by
default. This script composes a domain (e.g. SNAP) into one synthetic
top-level program, compiles it, then walks the lowered expression tree for
``Input { name }`` references that don't have a matching producer.

Most unresolved references are legitimate external inputs (per-household
facts the runtime provides). The script applies a heuristic to flag the
suspicious ones: names that start with the domain prefix (e.g. ``snap_``)
are expected to resolve to producer rules within the corpus; if they don't,
that's almost certainly a producer/consumer naming desync.

Usage::

    python scripts/check_corpus_resolution.py snap

Domains supported today:
- ``snap``: composes statutes/7, regulations/7-cfr/273, policies/usda/snap

Add new domains by editing ``DOMAIN_ROOTS`` below.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path


# Per-domain composition roots. Each entry is a list of corpus subdirectories
# that compose together cleanly (no cross-domain rule-name collisions).
DOMAIN_ROOTS: dict[str, list[str]] = {
    "snap": [
        "statutes/7",
        "regulations/7-cfr/273",
        "policies/usda/snap",
    ],
}

# Names with these prefixes are expected to be producer rules from within the
# domain, not external inputs. Unresolved references with these prefixes are
# treated as bugs.
DOMAIN_PRODUCER_PREFIXES: dict[str, tuple[str, ...]] = {
    "snap": ("snap_",),
}


def find_modules(corpus: Path, roots: list[str]) -> list[str]:
    citations = []
    for relative in roots:
        root = corpus / relative
        if not root.exists():
            continue
        for yaml_path in sorted(root.rglob("*.yaml")):
            if yaml_path.name.endswith(".test.yaml"):
                continue
            rel = yaml_path.relative_to(corpus).with_suffix("")
            citations.append(f"us:{rel}")
    return citations


def synthesize_top_module(citations: list[str], output: Path, domain: str) -> None:
    imports = "\n".join(f"  - {c}" for c in citations)
    output.write_text(
        f"format: rulespec/v1\n"
        f"module:\n"
        f"  summary: |-\n"
        f"    Auto-generated {domain} composition for resolution audit.\n"
        f"imports:\n{imports}\n"
        f"rules: []\n"
    )


def resolve_repo_roots(corpus: Path) -> str:
    """AXIOM_RULESPEC_REPO_ROOTS env value: parent of the corpus."""
    return str(corpus.parent)


def compile_program(engine: Path, program: Path, output: Path, repo_roots: str) -> str:
    env = os.environ.copy()
    env["AXIOM_RULESPEC_REPO_ROOTS"] = repo_roots
    result = subprocess.run(
        [str(engine), "compile", "--program", str(program), "--output", str(output)],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        sys.exit(f"compile failed (exit {result.returncode})")
    return result.stdout


def collect_input_references(expr, accumulator: set[str]) -> None:
    if not isinstance(expr, dict):
        return
    kind = expr.get("kind")
    if kind in {"input", "input_or_else"}:
        name = expr.get("name")
        if name:
            accumulator.add(name)
    if kind == "parameter_lookup":
        collect_input_references(expr.get("index"), accumulator)
    for key in (
        "expr", "condition", "then_expr", "else_expr",
        "left", "right", "value", "item",
        "date", "days", "from", "to",
        "where_clause", "where", "index",
    ):
        if key in expr:
            collect_input_references(expr[key], accumulator)
    for key in ("items",):
        for child in expr.get(key, []) or []:
            collect_input_references(child, accumulator)


def find_unresolved(artifact: dict, prefixes: tuple[str, ...]) -> dict[str, list[str]]:
    program = artifact.get("program", artifact)
    derived = program.get("derived", [])
    parameters = program.get("parameters", [])

    defined = {r["name"] for r in derived}
    defined.update({p["name"] for p in parameters})

    refs_by_name: dict[str, list[str]] = defaultdict(list)
    for rule in derived:
        refs: set[str] = set()
        collect_input_references(rule.get("expr") or rule.get("semantics"), refs)
        for name in refs:
            refs_by_name[name].append(rule["name"])

    suspicious = {}
    for name, consumers in refs_by_name.items():
        if name in defined:
            continue
        if not name.startswith(prefixes):
            continue
        suspicious[name] = sorted(set(consumers))
    return suspicious


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "domain",
        choices=sorted(DOMAIN_ROOTS.keys()),
        help="Program domain to audit.",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Path to the rulespec-us corpus root.",
    )
    parser.add_argument(
        "--engine",
        type=Path,
        default=Path(
            os.environ.get(
                "AXIOM_RULES_ENGINE_BINARY",
                Path.home() / "axiom-rules" / "target" / "release" / "axiom-rules-engine",
            )
        ),
        help="Path to axiom-rules-engine binary.",
    )
    args = parser.parse_args()

    corpus = args.corpus.expanduser().resolve()
    if not corpus.exists():
        sys.exit(f"corpus not found: {corpus}")
    if not args.engine.exists():
        sys.exit(f"engine not found: {args.engine}")

    citations = find_modules(corpus, DOMAIN_ROOTS[args.domain])
    print(f"[{args.domain}] {len(citations)} modules in composition")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        program = tmp / "compose.yaml"
        compiled = tmp / "compose.compiled.json"
        synthesize_top_module(citations, program, args.domain)
        compile_program(args.engine, program, compiled, resolve_repo_roots(corpus))
        artifact = json.loads(compiled.read_text())

    suspicious = find_unresolved(artifact, DOMAIN_PRODUCER_PREFIXES[args.domain])
    if not suspicious:
        print(f"[{args.domain}] no unresolved producer references — corpus is clean.")
        return 0

    print(
        f"\n[{args.domain}] {len(suspicious)} unresolved producer references "
        f"(probable naming desyncs):\n"
    )
    for name in sorted(suspicious):
        consumers = suspicious[name]
        print(f"  {name}")
        for c in consumers[:3]:
            print(f"    consumed by: {c}")
        if len(consumers) > 3:
            print(f"    ... and {len(consumers) - 3} more")

    print(
        f"\nFix by either renaming the consumer to match an existing producer, "
        f"or adding a producer with the expected name. References that are "
        f"genuinely external inputs should not start with `{DOMAIN_PRODUCER_PREFIXES[args.domain][0]}` "
        f"— rename them to a domain-neutral name."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
