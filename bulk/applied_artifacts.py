#!/usr/bin/env python3
"""Locate and validate the artifacts written by one bulk encode apply."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

MODULE_BUCKETS = {"manual", "policies", "regulations", "statutes"}
JURISDICTION_RE = re.compile(r"[a-z]{2}(?:-[a-z0-9-]+)?")
SOURCE_BUCKETS = {
    "manual": frozenset({"manual", "policies"}),
    "policy": frozenset({"policies"}),
    "policies": frozenset({"policies"}),
    "regulation": frozenset({"regulations"}),
    "regulations": frozenset({"regulations"}),
    "statute": frozenset({"statutes"}),
    "statutes": frozenset({"statutes"}),
}


def changed_paths(repo: Path) -> list[str]:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ],
        check=True,
        capture_output=True,
    )
    records = completed.stdout.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2:3] != b" ":
            raise ValueError("malformed git status --porcelain=v1 -z output")
        status = record[:2]
        paths.append(record[3:].decode("utf-8", errors="strict"))
        if b"R" in status or b"C" in status:
            if index >= len(records) or not records[index]:
                raise ValueError("git rename/copy status is missing its source path")
            index += 1
    return paths


def _is_module(path: PurePosixPath) -> bool:
    return (
        len(path.parts) >= 3
        and bool(JURISDICTION_RE.fullmatch(path.parts[0]))
        and path.parts[1] in MODULE_BUCKETS
        and path.suffix == ".yaml"
        and not path.name.endswith(".test.yaml")
    )


def _is_manifest(path: PurePosixPath) -> bool:
    parts = path.parts
    return (
        bool(parts)
        and parts[0] != "_axiom"
        and path.suffix == ".json"
        and any(
            parts[index : index + 2] == (".axiom", "encoding-manifests")
            for index in range(len(parts) - 1)
        )
    )


def _canonical_module_citation(module: str) -> str:
    path = PurePosixPath(module)
    relative = path.with_suffix("").parts
    return f"{relative[0]}:{'/'.join(relative[1:])}"


def _legal_path_tokens(parts: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        token.lower()
        for part in parts
        for token in re.findall(r"[a-z0-9]+", part.lower())
    )


def _module_matches_request(citation: str, module: str) -> bool:
    request = PurePosixPath(citation)
    output = PurePosixPath(module).with_suffix("")
    if len(request.parts) < 3 or len(output.parts) < 3:
        return False
    jurisdiction, source_bucket, *request_tail = request.parts
    expected_buckets = SOURCE_BUCKETS.get(source_bucket.lower())
    if expected_buckets is None:
        return False
    return (
        output.parts[0].lower() == jurisdiction.lower()
        and output.parts[1].lower() in expected_buckets
        and _legal_path_tokens(tuple(request_tail))
        == _legal_path_tokens(output.parts[2:])
    )


def discover_applied_artifacts(
    repo: Path,
    *,
    citation: str,
    paths: list[str] | None = None,
) -> tuple[str, str, str]:
    repo = Path(repo)
    candidates = paths if paths is not None else changed_paths(repo)
    modules = sorted(path for path in candidates if _is_module(PurePosixPath(path)))
    manifests = sorted(
        path for path in candidates if _is_manifest(PurePosixPath(path))
    )
    if len(modules) != 1:
        raise ValueError(f"expected one applied module; found {len(modules)}: {modules}")
    if len(manifests) != 1:
        raise ValueError(
            f"expected one applied manifest; found {len(manifests)}: {manifests}"
        )

    module = modules[0]
    test_file = f"{module[:-len('.yaml')]}.test.yaml"
    if not (repo / module).is_file():
        raise ValueError(f"applied module does not exist: {module}")
    if not (repo / test_file).is_file():
        raise ValueError(f"companion test does not exist: {test_file}")

    manifest_rel = manifests[0]
    try:
        manifest = json.loads((repo / manifest_rel).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read applied manifest {manifest_rel}: {exc}") from exc
    if not _module_matches_request(citation, module):
        raise ValueError(
            f"applied module {module!r} does not match requested citation {citation!r}"
        )
    manifest_citation = manifest.get("citation")
    accepted_citations = {citation, _canonical_module_citation(module)}
    if manifest_citation not in accepted_citations:
        raise ValueError(
            f"manifest citation {manifest_citation!r} does not match input "
            f"{citation!r} or generated module {module!r}"
        )

    applied_files = manifest.get("applied_files")
    if not isinstance(applied_files, list):
        raise ValueError(f"manifest {manifest_rel} has no applied_files list")
    actual_paths = {
        item.get("path")
        for item in applied_files
        if isinstance(item, dict)
        and item.get("deleted") is not True
        and isinstance(item.get("path"), str)
    }
    expected_full = {module, test_file}
    expected_local = {
        path.split("/", 1)[1] if "/" in path else path for path in expected_full
    }
    local_module = module.split("/", 1)[1]
    covers_changed_module = (
        actual_paths <= expected_full and module in actual_paths
    ) or (
        actual_paths <= expected_local and local_module in actual_paths
    )
    if not covers_changed_module:
        raise ValueError(
            f"manifest {manifest_rel} covers {sorted(actual_paths)}; expected the "
            f"changed module in {sorted(expected_full)} or {sorted(expected_local)}"
        )
    return module, test_file, manifest_rel


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--citation", required=True)
    args = parser.parse_args()
    try:
        artifacts = discover_applied_artifacts(args.repo, citation=args.citation)
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        parser.error(str(exc))
    print("\n".join(artifacts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
