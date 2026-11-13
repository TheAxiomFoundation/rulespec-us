"""Build the provision -> rules reverse index for this monorepo.

Every RuleSpec module grounds to legal text through corpus citation paths in
two places:

- ``module.source_verification.corpus_citation_path`` or
  ``module.source_verification.corpus_citation_paths`` (module-level grounding);
- ``rules[].metadata.proof.atoms[].source.corpus_citation_path`` (per-atom
  proof grounding).

This script scans every non-test RuleSpec YAML under the jurisdiction roots and
emits the provision -> rules index: for each corpus citation path
referenced anywhere, the sorted list of module paths that depend on it, plus the
kinds of reference (``module`` and/or ``proof_atom``). The output is fully
deterministic (sorted keys, sorted module lists), so any two runs over the same
tree produce the same bytes.

The index is NOT tracked in Git. It is a pure function of the tracked RuleSpec
YAML, so it is generated where it is needed: locally with this script (write it
outside the checkout with ``--output``; this is the trusted way), or from the
``provisions-to-rules-index`` artifact that the ``reverse-index`` CI job
uploads for each commit on ``main`` (take it only from a successful ``push``
run whose head commit is on ``main``; see the README). A tracked copy was the
one file that every encoding pull request had to edit, so each merge made every
other open pull request stale or conflicting, and the signed encoder workflow
(which may only write signed RuleSpec paths) could not produce it at all.
``tests/test_reverse_index.py`` fails if anything under ``.axiom/index/`` is
tracked again. ``--output`` is required and there is no default location inside
the checkout: the encoder's clean-checkout gates reject untracked and ignored
files, so a copy left in the checkout would block signed applies there.
``.axiom/index/`` is git-ignored only so that a stray copy cannot be committed
by accident.

The index is read-only tooling metadata. It does not participate in RuleSpec
validation and nothing in the engine binds to it; it exists so that a change to
a corpus provision can be traced to every module that must be re-checked
(Axiom platform plan A5), and it is the dependency half of the source-staleness
check.

Usage:
    python tests/generate_reverse_index.py --output /tmp/provisions_to_rules.json
    python tests/generate_reverse_index.py --output PATH --check   # exit 1 if PATH is stale
    python tests/generate_reverse_index.py --output PATH --deferred-provisions-output REPORT

The optional deferred-provisions report is a separate artifact. It matches
structured deferrals against candidate provider modules in the same checkout.
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
            citations = [verification.get("corpus_citation_path")]
            plural_citations = verification.get("corpus_citation_paths")
            if isinstance(plural_citations, list):
                citations.extend(plural_citations)
            for value in citations:
                citation = _clean_citation_path(value)
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
    index, _ = build_reports(repo_root)
    return index


def build_reports(
    repo_root: Path, *, include_deferrals: bool = False
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Generate the source index and optional deferral report from one scan."""
    # citation_path -> module_path -> {reference kinds}
    provisions: dict[str, dict[str, set[str]]] = {}
    providers: dict[str, list[str]] = {}
    deferred_outputs: list[tuple[str, str, list[str]]] = []
    module_count = 0

    for path in sorted(iter_module_files(repo_root)):
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue
        module_path = path.relative_to(repo_root).as_posix()
        if include_deferrals:
            _collect_deferred_provisions(payload, module_path, providers, deferred_outputs)
        references = citation_paths_for_module(payload)
        if not references:
            continue
        module_count += 1
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

    index = {
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
    report = (
        _build_deferral_report(providers, deferred_outputs) if include_deferrals else None
    )
    return index, report


def _has_formula(version: dict[str, Any]) -> bool:
    formula = version.get("formula")
    return isinstance(formula, (bool, int, float)) or (
        isinstance(formula, str) and bool(formula.strip())
    )


def _has_executable_version(rule: Any) -> bool:
    if not isinstance(rule, dict):
        return False
    kind = rule.get("kind")
    if kind not in ("parameter", "derived", "derived_relation"):
        return False
    name = rule.get("name")
    if not isinstance(name, str) or not name.strip():
        return False
    versions = rule.get("versions", [])
    if not isinstance(versions, list):
        return False
    # The engine accepts a single legacy version from fields on the rule.
    if not versions:
        versions = [
            {
                "formula": rule.get("formula"),
                "effective_from": rule.get("effective_from") or rule.get("from"),
            }
        ]
    if kind == "derived_relation":
        return (
            isinstance(rule.get("derived_relation"), dict)
            and len(versions) == 1
            and isinstance(versions[0], dict)
            and _has_formula(versions[0])
        )
    for version in versions:
        if not isinstance(version, dict) or not (
            version.get("effective_from") or version.get("from")
        ):
            continue
        values = version.get("values")
        if _has_formula(version) or (
            kind == "parameter"
            and rule.get("indexed_by")
            and isinstance(values, dict)
            and values
        ):
            return True
    return False


def _collect_deferred_provisions(
    payload: Any,
    module_path: str,
    providers: dict[str, list[str]],
    deferred_outputs: list[tuple[str, str, list[str]]],
) -> None:
    if not isinstance(payload, dict) or payload.get("format") != "rulespec/v1":
        return
    module = payload.get("module")
    if not isinstance(module, dict):
        return
    verification = module.get("source_verification")
    citation = (
        verification.get("corpus_citation_path")
        if isinstance(verification, dict)
        else None
    )
    rules = payload.get("rules")
    # Only primary module grounding identifies a possible provider. Proof
    # citations and historic multi-source fields do not assign ownership.
    if (
        isinstance(citation, str)
        and citation
        and module.get("status") not in ("deferred", "entity_not_supported", "stub")
        and isinstance(rules, list)
        and any(_has_executable_version(rule) for rule in rules)
    ):
        providers.setdefault(citation, []).append(module_path)

    entries = module.get("deferred_outputs")
    if not isinstance(entries, list):
        return
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        output = entry.get("output")
        blockers = entry.get("blocked_by_provisions")
        if (
            isinstance(output, str)
            and output.strip()
            and isinstance(blockers, list)
            and blockers
            and all(
                isinstance(blocker, str) and blocker.strip() for blocker in blockers
            )
        ):
            deferred_outputs.append((module_path, output, sorted(set(blockers))))


def _build_deferral_report(
    providers: dict[str, list[str]],
    deferred_outputs: list[tuple[str, str, list[str]]],
) -> dict[str, Any]:
    deferrals = []
    for module, output, citations in sorted(deferred_outputs):
        blockers = [
            {
                "provision": citation,
                "provider_modules": sorted(
                    path for path in providers.get(citation, []) if path != module
                ),
            }
            for citation in citations
        ]
        has_candidates = all(blocker["provider_modules"] for blocker in blockers)
        deferrals.append(
            {
                "module": module,
                "output": output,
                "status": "review_linkage" if has_candidates else "waiting",
                "blockers": blockers,
            }
        )
    return {"schema": "axiom.rulespec.deferred_provisions/v1", "deferrals": deferrals}


def _render_deferral_summary(report: dict[str, Any]) -> str:
    deferrals = report["deferrals"]
    ready = sum(item["status"] == "review_linkage" for item in deferrals)
    lines = [
        "### Deferred RuleSpec provisions",
        "",
        f"{len(deferrals) - ready} waiting. {ready} to review for linkage.",
    ]
    # Reviewable candidates come first. The JSON artifact keeps the full list.
    for item in sorted(deferrals, key=lambda item: item["status"])[:50]:
        label = "Review linkage" if item["status"] == "review_linkage" else "Waiting"
        lines.extend(("", f"    {label}: {item['output']!r} in {item['module']!r}"))
        for blocker in item["blockers"]:
            providers = ", ".join(repr(path) for path in blocker["provider_modules"])
            lines.append(
                f"      {blocker['provision']!r}: {providers or 'no candidate provider'}"
            )
    if len(deferrals) > 50:
        lines.extend(
            ("", f"Showing 50 of {len(deferrals)} deferrals. See the JSON report.")
        )
    return "\n".join(lines)


def render_index(index: dict[str, Any]) -> str:
    """Serialize the index deterministically with a trailing newline.

    The ``counts`` block is intentionally omitted from the serialized file;
    counts are still computed and printed for humans (see ``main``). The
    serialized shape is unchanged from the time the index was tracked in Git,
    so existing readers of the file keep working on a generated copy.
    """
    serializable = {key: value for key, value in index.items() if key != "counts"}
    return json.dumps(serializable, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def _is_inside(path: Path, directory: Path) -> bool:
    """True when ``path`` is ``directory`` or lies under it.

    Compares by file identity as well as by name, so a symlink or a
    case-variant spelling on a case-insensitive filesystem is still caught.
    """
    resolved = path.resolve()
    if resolved.is_relative_to(directory):
        return True
    for candidate in (resolved, *resolved.parents):
        try:
            if candidate.exists() and candidate.samefile(directory):
                return True
        except OSError:
            continue
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the copy at --output is up to date; exit 1 if it is stale or absent.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help=(
            "Where to write (or check) the index. Use a path outside the "
            "checkout: the index is not tracked, and the encoder's "
            "clean-checkout gates reject stray files inside it."
        ),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root to scan (defaults to this repo).",
    )
    parser.add_argument(
        "--deferred-provisions-output",
        type=Path,
        help="Also write (or check) a separate deferral report outside the checkout.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    output_path = args.output
    report_path = args.deferred_provisions_output
    options = (("--output", output_path), ("--deferred-provisions-output", report_path))
    for option, path in options:
        if path is not None and _is_inside(path, repo_root):
            print(
                f"{option} {path.as_posix()} is inside the repository being scanned. "
                "The index is not tracked and the encoder's clean-checkout gates "
                "reject stray files there; choose a path outside the checkout.",
                file=sys.stderr,
            )
            return 2
    if report_path is not None and report_path.resolve() == output_path.resolve():
        parser.error("--output and --deferred-provisions-output must use different files")

    index, report = build_reports(repo_root, include_deferrals=report_path is not None)
    artifacts = [(output_path, render_index(index))]
    if report_path is not None and report is not None:
        rendered_report = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        artifacts.append((report_path, rendered_report))

    output_label = output_path.as_posix()
    counts = index["counts"]

    if args.check:
        for path, rendered in artifacts:
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            if existing != rendered:
                print(
                    f"{path.as_posix()} is stale or absent. "
                    "Run the generator again without --check to regenerate it.",
                    file=sys.stderr,
                )
                return 1
        print(
            f"{output_label} is up to date "
            f"({counts['provisions']} provisions, {counts['edges']} edges, "
            f"{counts['modules']} modules)."
        )
        return 0

    for path, rendered in artifacts:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    print(
        f"Wrote {output_label}: "
        f"{counts['provisions']} provisions, {counts['edges']} edges, "
        f"{counts['modules']} modules."
    )
    if report is not None:
        print()
        print(_render_deferral_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
