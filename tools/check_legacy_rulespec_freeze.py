#!/usr/bin/env python3
"""Fail when legacy RuleSpec artifacts are unlisted, missing, or changed."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

ATOMIC_ROOTS = frozenset({"legislation", "policies", "regulations", "statutes"})
NON_RULESPEC_ROOTS = frozenset({"programs"})
JURISDICTION_RE = re.compile(r"us(?:-[a-z]{2})?")
MANIFEST_PATH = Path(".axiom/legacy-rulespec-freeze.json")
RETIRED_SCHEMA_TEST_PATH = Path("tests/test_encoding_manifests.py")
SHA256_RE = re.compile(r"[0-9a-f]{64}")


def _git_paths(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _is_legacy_rulespec_path(raw_path: str) -> bool:
    path = Path(raw_path)
    return (
        len(path.parts) >= 2
        and JURISDICTION_RE.fullmatch(path.parts[0]) is not None
        and path.parts[1] not in ATOMIC_ROOTS | NON_RULESPEC_ROOTS
        and path.suffix in {".yaml", ".yml"}
    )


def _is_frozen_artifact_path(raw_path: str) -> bool:
    return _is_legacy_rulespec_path(raw_path)


def _retired_schema_allowlist(source: str) -> frozenset[str]:
    tree = ast.parse(source)
    for node in tree.body:
        target = node.target if isinstance(node, ast.AnnAssign) else None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != "KNOWN_RETIRED_SCHEMA_MANIFESTS":
            continue
        value = node.value
        if (
            not isinstance(value, ast.Call)
            or not isinstance(value.func, ast.Name)
            or value.func.id != "frozenset"
            or len(value.args) != 1
            or value.keywords
        ):
            raise ValueError("retired-schema allowlist must be one literal frozenset")
        parsed = ast.literal_eval(value.args[0])
        if not isinstance(parsed, (set, list, tuple)) or not all(
            isinstance(item, str) for item in parsed
        ):
            raise ValueError("retired-schema allowlist must contain only paths")
        return frozenset(parsed)
    raise ValueError("retired-schema allowlist is missing")


def check(root: Path, *, base_ref: str | None = None) -> None:
    manifest_path = root / MANIFEST_PATH
    payload = json.loads(manifest_path.read_text())
    if payload.get("format") != "axiom/legacy-rulespec-freeze/v1":
        raise ValueError("legacy freeze manifest has an unsupported format")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("legacy freeze manifest must list artifacts")
    if any(
        not isinstance(path, str)
        or not isinstance(digest, str)
        or SHA256_RE.fullmatch(digest) is None
        for path, digest in artifacts.items()
    ):
        raise ValueError("legacy freeze artifacts must map paths to SHA-256 digests")

    tracked = set(_git_paths(root, "ls-files"))
    discovered = {path for path in tracked if _is_frozen_artifact_path(path)}
    if discovered != set(artifacts):
        missing = sorted(discovered - set(artifacts))
        stale = sorted(set(artifacts) - discovered)
        raise ValueError(
            f"legacy freeze inventory mismatch; unlisted={missing}, missing={stale}"
        )

    for relative_path, expected_digest in sorted(artifacts.items()):
        artifact = root / relative_path
        if artifact.is_symlink() or not artifact.is_file():
            raise ValueError(
                f"legacy freeze artifact is not a regular file: {relative_path}"
            )
        actual_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            raise ValueError(
                f"legacy freeze digest mismatch for {relative_path}: {actual_digest}"
            )

    if base_ref:
        changed = _git_paths(root, "diff", "--name-only", f"{base_ref}...HEAD")
        changed_legacy = sorted(
            path for path in changed if _is_frozen_artifact_path(path)
        )
        if changed_legacy:
            raise ValueError(
                "pull request changes frozen legacy RuleSpec artifacts: "
                + ", ".join(changed_legacy)
            )

        allowlist_path = root / RETIRED_SCHEMA_TEST_PATH
        if allowlist_path.is_file():
            base_source = subprocess.run(
                ["git", "show", f"{base_ref}:{RETIRED_SCHEMA_TEST_PATH.as_posix()}"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            current = _retired_schema_allowlist(allowlist_path.read_text())
            base = _retired_schema_allowlist(base_source)
            additions = sorted(current - base)
            if additions:
                raise ValueError(
                    "retired-schema allowlist is decrement-only; added="
                    + ", ".join(additions)
                )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base-ref")
    args = parser.parse_args()
    check(args.root.resolve(), base_ref=args.base_ref)
    print("Legacy RuleSpec freeze inventory verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
