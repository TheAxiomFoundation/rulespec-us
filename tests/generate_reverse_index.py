"""Build the provision -> rules reverse index for this monorepo.

Every RuleSpec module grounds to legal text through corpus citation paths in
two places:

- ``module.source_verification.corpus_citation_path`` (module-level grounding);
- ``rules[].metadata.proof.atoms[].source.corpus_citation_path`` (per-atom
  proof grounding).

This script scans every non-test RuleSpec YAML under the jurisdiction roots and
emits ``.axiom/index/provisions_to_rules.json``: for each corpus citation path
referenced anywhere, the sorted list of module paths that depend on it, plus the
kinds of reference (``module`` and/or ``proof_atom``). The output is fully
deterministic (sorted keys, sorted module lists) so CI can regenerate it and
diff against the committed copy.

The index is read-only tooling metadata. It does not participate in RuleSpec
validation and nothing in the engine binds to it; it exists so that a change to
a corpus provision can be traced to every module that must be re-checked
(Axiom platform plan A5), and it is the dependency half of the source-staleness
check.

Usage:
    python tests/generate_reverse_index.py            # write the index
    python tests/generate_reverse_index.py --check    # exit 1 if stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml

# Jurisdiction roots are top-level directories named like ``us`` or ``us-ca``
# that hold RuleSpec YAML. Non-jurisdiction roots (``.axiom``, ``.github``,
# ``programs``, ``tests``) never carry ground-truth citation paths, so the
# scan restricts to the jurisdiction-directory convention the org validate
# workflow uses (``validate-roots: auto``): a two-letter code optionally
# followed by hyphenated segments.
REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_RELATIVE_PATH = Path(".axiom") / "index" / "provisions_to_rules.json"

MODULE_REFERENCE = "module"
PROOF_ATOM_REFERENCE = "proof_atom"


def is_jurisdiction_dir(name: str) -> bool:
    """Match the ``validate-roots: auto`` jurisdiction-directory convention."""
    if not name or name.startswith((".", "_")):
        return False
    segments = name.split("-")
    if len(segments[0]) != 2 or not segments[0].isalpha() or not segments[0].islower():
        return False
    for segment in segments[1:]:
        if not segment or not all(ch.isalnum() and (ch.islower() or ch.isdigit()) for ch in segment):
            return False
    return True


def jurisdiction_dirs(repo_root: Path) -> list[str]:
    return sorted(
        entry.name
        for entry in repo_root.iterdir()
        if entry.is_dir() and is_jurisdiction_dir(entry.name)
    )


def iter_module_files(repo_root: Path) -> Iterable[Path]:
    """Yield every non-test RuleSpec YAML file under jurisdiction roots."""
    for root in jurisdiction_dirs(repo_root):
        base = repo_root / root
        for pattern in ("*.yaml", "*.yml"):
            for path in base.rglob(pattern):
                if not path.is_file():
                    continue
                name = path.name
                if name.endswith((".test.yaml", ".test.yml")):
                    continue
                yield path


def _clean_citation_path(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def citation_paths_for_module(payload: Any) -> dict[str, set[str]]:
    """Return ``{citation_path: {reference_kind, ...}}`` for one module payload."""
    references: dict[str, set[str]] = {}
    if not isinstance(payload, dict):
        return references

    module = payload.get("module")
    if isinstance(module, dict):
        verification = module.get("source_verification")
        if isinstance(verification, dict):
            citation = _clean_citation_path(verification.get("corpus_citation_path"))
            if citation is not None:
                references.setdefault(citation, set()).add(MODULE_REFERENCE)

    rules = payload.get("rules")
    if isinstance(rules, list):
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            metadata = rule.get("metadata")
            if not isinstance(metadata, dict):
                continue
            proof = metadata.get("proof")
            if not isinstance(proof, dict):
                continue
            atoms = proof.get("atoms")
            if not isinstance(atoms, list):
                continue
            for atom in atoms:
                if not isinstance(atom, dict):
                    continue
                source = atom.get("source")
                if not isinstance(source, dict):
                    continue
                citation = _clean_citation_path(source.get("corpus_citation_path"))
                if citation is not None:
                    references.setdefault(citation, set()).add(PROOF_ATOM_REFERENCE)

    return references


def build_index(repo_root: Path) -> dict[str, Any]:
    """Build the reverse index mapping citation paths to dependent modules."""
    # citation_path -> module_path -> {reference kinds}
    provisions: dict[str, dict[str, set[str]]] = {}
    module_count = 0

    for path in sorted(iter_module_files(repo_root)):
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue
        references = citation_paths_for_module(payload)
        if not references:
            continue
        module_count += 1
        module_path = path.relative_to(repo_root).as_posix()
        for citation, kinds in references.items():
            provisions.setdefault(citation, {}).setdefault(module_path, set()).update(kinds)

    edge_count = 0
    provisions_out: dict[str, Any] = {}
    for citation in sorted(provisions):
        module_map = provisions[citation]
        modules_out = []
        for module_path in sorted(module_map):
            modules_out.append(
                {
                    "module": module_path,
                    "via": sorted(module_map[module_path]),
                }
            )
        edge_count += len(modules_out)
        provisions_out[citation] = modules_out

    return {
        "schema": "axiom.rulespec.provisions_to_rules/v1",
        "description": (
            "Reverse index from corpus citation path to the RuleSpec modules "
            "that depend on it (module source_verification and proof-atom "
            "sources). Generated by tests/generate_reverse_index.py; do not "
            "edit by hand."
        ),
        "counts": {
            "provisions": len(provisions_out),
            "edges": edge_count,
            "modules": module_count,
        },
        "provisions": provisions_out,
    }


def render_index(index: dict[str, Any]) -> str:
    """Serialize the index deterministically with a trailing newline."""
    return json.dumps(index, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the committed index is up to date; exit 1 if it is stale.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root to scan (defaults to this repo).",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    index = build_index(repo_root)
    rendered = render_index(index)
    output_path = repo_root / INDEX_RELATIVE_PATH
    counts = index["counts"]

    if args.check:
        existing = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        if existing != rendered:
            print(
                f"{INDEX_RELATIVE_PATH.as_posix()} is stale. "
                "Run `python tests/generate_reverse_index.py` and commit the result.",
                file=sys.stderr,
            )
            return 1
        print(
            f"{INDEX_RELATIVE_PATH.as_posix()} is up to date "
            f"({counts['provisions']} provisions, {counts['edges']} edges, "
            f"{counts['modules']} modules)."
        )
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(
        f"Wrote {INDEX_RELATIVE_PATH.as_posix()}: "
        f"{counts['provisions']} provisions, {counts['edges']} edges, "
        f"{counts['modules']} modules."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
