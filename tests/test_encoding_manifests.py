from __future__ import annotations

import functools
import hashlib
import json
import warnings
from pathlib import Path

from test_repository_layout import (
    JURISDICTION_DIR_RE,
    ROOT,
    apply_gap_ratchet,
    iter_rulespec_files,
    jurisdiction_dirs,
)

KNOWN_ORPHANED_ENCODING_MANIFESTS = [
    # The module moved to us-ca/policies/cdss/snap/standard-utility-allowance.yaml
    # during subtree absorption; its manifest stayed at the old guidance path.
    "us-ca/guidance/cdss/acin-2025-i-46-25/standard-utility-allowance.yaml",
]

# Replacement manifests record these mutable control files as applied-time
# evidence. Their historical hashes remain signed in the manifest, but later
# reviewed waiver/toolchain updates must not be mistaken for edits to rules.
MUTABLE_ROOT_METADATA_PATHS = frozenset(
    {".axiom/toolchain.toml", "known-validation-gaps.yaml"}
)

# ProgramSpecs under programs/ are assembled axiom-compose specs, not encoder
# output. Since the encoder hard cut (axiom-encode#1108) every signer and
# manifest surface uses only the atomic roots, so no tool can re-attest an
# edited spec. Their legacy manual-composition attestations stay as history and
# are not synced against later reviewed spec edits. The shared validate
# workflow's pre-check gates programs/ by ProgramSpec shape instead.
ASSEMBLED_ROOT = "programs"

# Manifest-sync guard: axiom-encode writes an applied-rulespec manifest
# (schema axiom-encode/applied-rulespec/v1) next to every encoding run,
# recording the sha256 of each file it applied. A hand-edit to an encoded
# rule module that skips the encoder leaves the manifest stale — invisible
# drift between content and provenance. These tests make that drift a CI
# failure. Motivated by the review flag on
# https://github.com/TheAxiomFoundation/rulespec-us/pull/566 and
# https://github.com/TheAxiomFoundation/axiom-rules-engine/issues/88.
#
# Three manifest layouts coexist after the country-monorepo consolidation:
#   .axiom/encoding-manifests/statutes/26/213.json
#       pre-consolidation federal manifests; applied paths relative to us/
#   .axiom/encoding-manifests/us-ny/policies/....json
#       post-consolidation manifests; applied paths relative to the repo root
#   us-ct/.axiom/encoding-manifests/statutes/....json
#       trees absorbed from the standalone state repos; applied paths
#       relative to the jurisdiction directory
# A module re-encoded after the consolidation can therefore be covered by
# manifests in two locations; the entry with the newest generated_at is
# authoritative and older ones are superseded history.


def manifest_roots() -> list[tuple[Path, Path]]:
    """(base directory, manifest directory) pairs for every layout."""
    return [
        (base, base / ".axiom" / "encoding-manifests")
        for base in (ROOT, *jurisdiction_dirs())
        if (base / ".axiom" / "encoding-manifests").is_dir()
    ]


def resolve_applied_path(base: Path, applied: str) -> Path:
    head = applied.split("/", 1)[0]
    if base == ROOT and (
        head == "programs"
        or applied in MUTABLE_ROOT_METADATA_PATHS
    ):
        return ROOT / applied
    if base == ROOT and not JURISDICTION_DIR_RE.match(head):
        # Pre-consolidation federal manifests predate the us/ prefix.
        return ROOT / "us" / applied
    return base / applied


def test_resolve_applied_paths_preserves_root_metadata_and_legacy_layouts() -> None:
    for path in MUTABLE_ROOT_METADATA_PATHS:
        assert resolve_applied_path(ROOT, path) == ROOT / path
        assert resolve_applied_path(ROOT / "us-ct", path) == ROOT / "us-ct" / path
    assert resolve_applied_path(ROOT, "statutes/26/213.yaml") == ROOT / "us/statutes/26/213.yaml"
    assert resolve_applied_path(ROOT, "us/policies/example.yaml") == ROOT / "us/policies/example.yaml"
    assert resolve_applied_path(ROOT, "programs/example.yaml") == ROOT / "programs/example.yaml"


@functools.cache
def latest_manifest_entries() -> dict[Path, tuple[Path, dict]]:
    """Authoritative (manifest path, applied_files entry) per rule module.

    Companion ``.test.yaml`` entries are ignored; when several manifests
    cover one module, the newest ``generated_at`` wins.
    """
    latest: dict[Path, tuple[str, Path, dict]] = {}
    for base, manifest_dir in manifest_roots():
        for manifest_path in sorted(manifest_dir.rglob("*.json")):
            payload = json.loads(manifest_path.read_text())
            generated_at = str(payload.get("generated_at") or "")
            applied_files = payload.get("applied_files")
            if not isinstance(applied_files, list):
                continue
            for entry in applied_files:
                if not isinstance(entry, dict):
                    continue
                applied = entry.get("path")
                if (
                    not applied
                    or applied.endswith(".test.yaml")
                    or (base == ROOT and applied in MUTABLE_ROOT_METADATA_PATHS)
                    or (base == ROOT and applied.split("/", 1)[0] == ASSEMBLED_ROOT)
                ):
                    continue
                module = resolve_applied_path(base, applied)
                current = latest.get(module)
                if current is None or generated_at > current[0]:
                    latest[module] = (generated_at, manifest_path, entry)
    return {
        module: (manifest_path, entry)
        for module, (_, manifest_path, entry) in latest.items()
    }


def test_manifest_sync_excludes_mutable_root_metadata() -> None:
    latest = latest_manifest_entries()
    for path in MUTABLE_ROOT_METADATA_PATHS:
        assert ROOT / path not in latest


def test_manifest_sync_excludes_assembled_program_specs() -> None:
    latest = latest_manifest_entries()
    assembled = ROOT / ASSEMBLED_ROOT
    assert not [module for module in latest if module.is_relative_to(assembled)]
    # Legacy attestations of program specs exist, so the exclusion is live.
    assert any(
        entry.get("path", "").startswith(f"{ASSEMBLED_ROOT}/")
        for manifest in (ROOT / ".axiom" / "encoding-manifests" / ASSEMBLED_ROOT).rglob("*.json")
        for entry in json.loads(manifest.read_text()).get("applied_files", [])
    )


def test_encoded_modules_match_their_manifests() -> None:
    stale: list[str] = []

    for module, (manifest_path, entry) in sorted(latest_manifest_entries().items()):
        if not module.is_file():
            continue  # covered by test_manifests_reference_existing_modules
        expected = entry.get("sha256")
        if entry.get("deleted") or not expected:
            stale.append(
                f"{module.relative_to(ROOT).as_posix()} exists but "
                f"{manifest_path.relative_to(ROOT).as_posix()} records a deletion"
            )
            continue
        if hashlib.sha256(module.read_bytes()).hexdigest() != expected:
            stale.append(module.relative_to(ROOT).as_posix())

    assert stale == [], (
        "Encoded rule modules drifted from their encoding manifests "
        "(edited outside the axiom-encode path?). Re-run axiom-encode for "
        "each module below, or refresh its manifest under "
        ".axiom/encoding-manifests/ if the edit is being accepted as-is:\n"
        + "\n".join(stale)
    )


def test_manifests_reference_existing_modules() -> None:
    orphaned = [
        module.relative_to(ROOT).as_posix()
        for module, (_, entry) in sorted(latest_manifest_entries().items())
        if not module.is_file() and entry.get("sha256") and not entry.get("deleted")
    ]

    assert orphaned == KNOWN_ORPHANED_ENCODING_MANIFESTS, (
        "Encoding manifests reference modules that no longer exist at the "
        "recorded path. Move or regenerate the manifest alongside the "
        "module, or delete it if the module was retired:\n"
        + "\n".join(orphaned)
    )


def test_unmanifested_modules_are_reported_not_failed() -> None:
    manifested = set(latest_manifest_entries())
    unmanifested = [
        path.relative_to(ROOT).as_posix()
        for path in iter_rulespec_files()
        if path not in manifested
    ]

    # Early encodings predate apply-manifests, so a missing manifest is
    # pre-existing debt rather than drift; surface the count without failing.
    if unmanifested:
        warnings.warn(
            f"{len(unmanifested)} rule modules have no encoding manifest and "
            f"are outside the manifest-sync guard (e.g. {unmanifested[0]})",
            stacklevel=1,
        )
