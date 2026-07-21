from __future__ import annotations

import functools
import hashlib
import json
import warnings
from pathlib import Path

from test_repository_layout import (
    ROOT,
    iter_rulespec_files,
)

KNOWN_ORPHANED_ENCODING_MANIFESTS: list[str] = []

# Decrement-only: v1-schema hmac manifests merged to main by the CO
# income-tax pilot lane (#942/#943) after this test hardened. They predate
# the v5 apply signer and are tracked for re-signing in rulespec-us#944;
# nothing new may join this list.
KNOWN_RETIRED_SCHEMA_MANIFESTS: frozenset[str] = frozenset({
    ".axiom/encoding-manifests/us-co/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-co/policies/income_tax/eitc_pilot_pipeline.json",
    ".axiom/encoding-manifests/us-sc/policies/dss/snap-policy-manual/page-215.json",
    ".axiom/encoding-manifests/us-sc/policies/dss/snap-policy-manual/page-345.json",
    ".axiom/encoding-manifests/us-sc/policies/dss/snap-policy-manual/page-385.json",
    ".axiom/encoding-manifests/us/regulations/42-cfr/435/552.json",
    ".axiom/encoding-manifests/us/regulations/42-cfr/435/555.json",
    ".axiom/encoding-manifests/us/regulations/42-cfr/435/557.json",
    ".axiom/encoding-manifests/us/regulations/42-cfr/435/558.json",
    ".axiom/encoding-manifests/us/regulations/42-cfr/435/559.json",
    ".axiom/encoding-manifests/us/regulations/42-cfr/435/561.json",
    ".axiom/encoding-manifests/us/regulations/42-cfr/435/563.json",
    ".axiom/encoding-manifests/us/statutes/42/1396a/xx.json",
})


def test_encoding_manifests_use_current_signed_schema() -> None:
    """New manifests must not reintroduce a retired legacy layout or schema.

    `_axiom/` holds workflow-provisioned dependency checkouts pinned at
    foreign refs; their manifests are not this repo's and are excluded.
    Cryptographic verification is performed by the protected
    ``guard-generated`` workflow.
    """
    problems: list[str] = []
    canonical_root = ROOT / ".axiom" / "encoding-manifests"
    for path in ROOT.rglob("*.json"):
        relative = path.relative_to(ROOT)
        if "encoding-manifests" not in path.parts or "_axiom" in relative.parts:
            continue
        if not path.is_relative_to(canonical_root):
            problems.append(f"{relative.as_posix()}: legacy manifest location")
            continue
        if relative.as_posix() in KNOWN_RETIRED_SCHEMA_MANIFESTS:
            continue
        payload = json.loads(path.read_text())
        if payload.get("schema_version") != "axiom-encode/applied-rulespec/v5":
            problems.append(f"{relative.as_posix()}: retired manifest schema")
        signature = payload.get("signature")
        if not isinstance(signature, dict) or set(signature) != {
            "algorithm",
            "key_id",
            "value",
        }:
            problems.append(f"{relative.as_posix()}: missing signature envelope")
        elif signature.get("algorithm") != "ed25519-domain-v1":
            problems.append(f"{relative.as_posix()}: unsupported signature algorithm")

    assert problems == []

# Manifest-sync guard: axiom-encode writes an applied-rulespec manifest
# (schema axiom-encode/applied-rulespec/v5) next to every encoding run,
# recording the sha256 of each file it applied. A hand-edit to an encoded
# rule module that skips the encoder leaves the manifest stale — invisible
# drift between content and provenance. These tests make that drift a CI
# failure. Motivated by the review flag on
# https://github.com/TheAxiomFoundation/rulespec-us/pull/566 and
# https://github.com/TheAxiomFoundation/axiom-rules-engine/issues/88.
#
# The canonical-provenance hard cut removed legacy per-jurisdiction and
# pre-consolidation layouts. All new manifests are rooted at the repository.


def manifest_roots() -> list[tuple[Path, Path]]:
    """Return the canonical (base directory, manifest directory) pair."""
    manifest_dir = ROOT / ".axiom" / "encoding-manifests"
    return [(ROOT, manifest_dir)] if manifest_dir.is_dir() else []


def resolve_applied_path(base: Path, applied: str) -> Path:
    return base / applied


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
                if not applied or applied.endswith(".test.yaml"):
                    continue
                module = resolve_applied_path(base, applied)
                current = latest.get(module)
                if current is None or generated_at > current[0]:
                    latest[module] = (generated_at, manifest_path, entry)
    return {
        module: (manifest_path, entry)
        for module, (_, manifest_path, entry) in latest.items()
    }


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
