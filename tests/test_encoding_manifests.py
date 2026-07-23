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

# Decrement-only: v1-schema HMAC manifests that predate the protected v5 apply
# signer. They are tracked for encoder-driven re-signing in rulespec-us#944;
# the migration may only remove entries from this explicit inventory.
KNOWN_RETIRED_SCHEMA_MANIFESTS: frozenset[str] = frozenset({
    ".axiom/encoding-manifests/us-ar/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-co/policies/income_tax/eitc_pilot_pipeline.json",
    ".axiom/encoding-manifests/us-co/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-dc/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-ga/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-ga/statutes/48/48-7-20.json",
    ".axiom/encoding-manifests/us-ga/statutes/48/48-7-26.json",
    ".axiom/encoding-manifests/us-ga/statutes/48/48-7-27.json",
    ".axiom/encoding-manifests/us-ga/statutes/48/48-7-29/10.json",
    ".axiom/encoding-manifests/us-ga/statutes/48/48-7A-3.json",
    ".axiom/encoding-manifests/us-hi/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-ia/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-il/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-in/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-in/statutes/6-3-2-1.json",
    ".axiom/encoding-manifests/us-ks/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-mo/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-ms/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-mt/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-nc/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-nc/statutes/105/105-153/7.json",
    ".axiom/encoding-manifests/us-nd/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-nh/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-nj/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-nm/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-ok/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-or/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-pa/policies/income_tax/2026_rate_table.json",
    ".axiom/encoding-manifests/us-pa/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-ri/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-sc/policies/dss/snap-policy-manual/page-215.json",
    ".axiom/encoding-manifests/us-sc/policies/dss/snap-policy-manual/page-345.json",
    ".axiom/encoding-manifests/us-sc/policies/dss/snap-policy-manual/page-385.json",
    ".axiom/encoding-manifests/us-sc/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-ut/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-vt/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-wa/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-wi/policies/income_tax/pilot_liability_pipeline.json",
    ".axiom/encoding-manifests/us-wv/policies/income_tax/pilot_liability_pipeline.json",
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
    seen_manifests: set[str] = set()
    canonical_root = ROOT / ".axiom" / "encoding-manifests"
    for path in ROOT.rglob("*.json"):
        relative = path.relative_to(ROOT)
        if "encoding-manifests" not in path.parts or "_axiom" in relative.parts:
            continue
        relative_text = relative.as_posix()
        seen_manifests.add(relative_text)
        if not path.is_relative_to(canonical_root):
            problems.append(f"{relative_text}: legacy manifest location")
            continue
        payload = json.loads(path.read_text())
        if relative_text in KNOWN_RETIRED_SCHEMA_MANIFESTS:
            if payload.get("schema_version") != "axiom-encode/applied-rulespec/v1":
                problems.append(f"{relative_text}: retired allowance must cover exact v1")
            signature = payload.get("signature")
            if not isinstance(signature, dict) or set(signature) != {
                "algorithm",
                "key_id",
                "value",
            }:
                problems.append(f"{relative_text}: invalid legacy signature envelope")
            elif (
                signature.get("algorithm") != "hmac-sha256"
                or signature.get("key_id") != "axiom-encode-apply-v1"
            ):
                problems.append(f"{relative_text}: invalid legacy signature identity")
            continue
        if payload.get("schema_version") != "axiom-encode/applied-rulespec/v5":
            problems.append(f"{relative_text}: retired manifest schema")
        signature = payload.get("signature")
        if not isinstance(signature, dict) or set(signature) != {
            "algorithm",
            "key_id",
            "value",
        }:
            problems.append(f"{relative_text}: missing signature envelope")
        elif signature.get("algorithm") != "ed25519-domain-v1":
            problems.append(f"{relative_text}: unsupported signature algorithm")

    for missing in sorted(KNOWN_RETIRED_SCHEMA_MANIFESTS - seen_manifests):
        problems.append(f"{missing}: remove missing retired-schema allowance")

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
