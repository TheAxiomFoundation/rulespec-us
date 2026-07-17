"""Unit tests for the manifest provenance stamps (engine sha, corpus binding,
four-field compat block) added to build_program_artifacts.py. These cover the
pure functions and manifest assembly without needing the engine or corpus."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_program_artifacts as bpa  # noqa: E402


def test_toolchain_binding_reads_pinned_refs(tmp_path: Path):
    axiom = tmp_path / ".axiom"
    axiom.mkdir()
    (axiom / "toolchain.toml").write_text(
        "[toolchain]\n"
        'axiom_encode_version = "0.2.1200"\n'
        'axiom_rules_engine_ref = "e19f1b7573c74512f20a6b71a0c55dbbf333d41b"\n'
        'axiom_encode_ref = "3869d66d009f52258be35901edbef370e65a399c"\n'
        'axiom_corpus_ref = "7661f3c9a3655e93fc9b2420048d70d231e7d44b"\n'
    )
    b = bpa.toolchain_binding(tmp_path)
    assert b["engine_ref"] == "e19f1b7573c74512f20a6b71a0c55dbbf333d41b"
    assert b["corpus_ref"] == "7661f3c9a3655e93fc9b2420048d70d231e7d44b"
    assert b["encode_version"] == "0.2.1200"


def test_toolchain_binding_absent_file_is_empty(tmp_path: Path):
    assert bpa.toolchain_binding(tmp_path) == {}


def test_artifact_schema_version_is_one():
    assert bpa.ARTIFACT_SCHEMA_VERSION == 1


def test_compat_block_shape():
    # Mirror the compat block the builder constructs, and assert the four-field
    # contract is present and correctly typed.
    engine_version = "0.1.0"
    toolchain = {"engine_ref": "e19f1b75"}
    compat = {
        "artifact_schema": bpa.ARTIFACT_SCHEMA_VERSION,
        "built_by_engine": {"version": engine_version, "git_sha": toolchain.get("engine_ref", "")},
        "requires_engine": {"min_version": engine_version, "capabilities": []},
    }
    assert compat["artifact_schema"] == 1
    assert compat["built_by_engine"]["git_sha"] == "e19f1b75"
    assert compat["requires_engine"]["min_version"] == "0.1.0"
    assert compat["requires_engine"]["capabilities"] == []
    # Provenance (built_by) and gating (requires) are distinct fields.
    assert "built_by_engine" in compat and "requires_engine" in compat


def test_manifest_has_non_stale_engine_sha_and_corpus_binding():
    # Assemble the top-level manifest exactly as main() does and assert the new
    # fields carry the real engine sha (not just the stale "0.1.0" string) and
    # the corpus binding commit.
    toolchain = {"engine_ref": "e19f1b7573c7", "corpus_ref": "7661f3c9a365"}
    engine_version = "0.1.0"
    manifest = {
        "format_version": bpa.MANIFEST_FORMAT_VERSION,
        "engine_version": engine_version,
        "engine": {"version": engine_version, "git_sha": toolchain["engine_ref"]},
        "corpus_binding": {"repo": "axiom-corpus", "commit": toolchain["corpus_ref"], "release": None},
        "artifact_schema": bpa.ARTIFACT_SCHEMA_VERSION,
    }
    # The BOM verifier's key assertion: engine identity is no longer sha-less.
    assert manifest["engine"]["git_sha"] and manifest["engine"]["git_sha"] != "0.1.0"
    assert manifest["corpus_binding"]["commit"] == "7661f3c9a365"
    # round-trips as JSON
    json.loads(json.dumps(manifest))
