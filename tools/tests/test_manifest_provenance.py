"""Unit tests for the manifest provenance stamps (real engine sha, validation
toolchain, four-field compat contract). These call the ACTUAL production
functions — assemble_manifest / build_compat / engine_build_sha /
validation_toolchain — so a field omitted or misspelled in production code
fails the test (they do not recreate dicts by hand)."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_program_artifacts as bpa  # noqa: E402


def test_validation_toolchain_reads_pins(tmp_path: Path):
    axiom = tmp_path / ".axiom"
    axiom.mkdir()
    (axiom / "toolchain.toml").write_text(
        "[toolchain]\n"
        'axiom_encode_version = "0.2.1200"\n'
        'axiom_rules_engine_ref = "e19f1b7573c74512f20a6b71a0c55dbbf333d41b"\n'
        'axiom_corpus_ref = "7661f3c9a3655e93fc9b2420048d70d231e7d44b"\n'
    )
    t = bpa.validation_toolchain(tmp_path)
    assert t["axiom_rules_engine_ref"] == "e19f1b7573c74512f20a6b71a0c55dbbf333d41b"
    assert t["axiom_corpus_ref"] == "7661f3c9a3655e93fc9b2420048d70d231e7d44b"
    assert t["axiom_encode_version"] == "0.2.1200"


def test_validation_toolchain_absent_is_empty(tmp_path: Path):
    assert bpa.validation_toolchain(tmp_path) == {}


def test_engine_build_sha_prefers_explicit_env(monkeypatch):
    monkeypatch.setenv("AXIOM_RULES_ENGINE_SHA", "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef")
    assert bpa.engine_build_sha("/nonexistent/bin") == "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"


def test_engine_build_sha_derives_from_checkout(tmp_path, monkeypatch):
    monkeypatch.delenv("AXIOM_RULES_ENGINE_SHA", raising=False)
    # Build a tiny git repo with a fake binary at target/release/ and check the
    # function walks up to it and returns HEAD.
    repo = tmp_path / "engine-src"
    (repo / "target" / "release").mkdir(parents=True)
    binp = repo / "target" / "release" / "axiom-rules-engine"
    binp.write_text("#!/bin/sh\n")
    for args in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    (repo / "f").write_text("x")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True, capture_output=True)
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    assert bpa.engine_build_sha(str(binp)) == head


def test_engine_build_sha_unknown_returns_empty(tmp_path, monkeypatch):
    monkeypatch.delenv("AXIOM_RULES_ENGINE_SHA", raising=False)
    assert bpa.engine_build_sha(str(tmp_path / "no" / "git" / "bin")) == ""


def test_build_compat_contract_shape_and_floor():
    compat = bpa.build_compat(engine_version="0.1.0", engine_sha="e19f1b75cafe")
    assert compat["artifact_schema"] == 1
    # Provenance carries the real build sha; gating carries the FIXED floor,
    # not the building version (so older schema-1 engines aren't rejected).
    assert compat["built_by_engine"] == {"version": "0.1.0", "git_sha": "e19f1b75cafe"}
    assert compat["requires_engine"]["min_version"] == bpa.MIN_ENGINE_VERSION == "0.1.0"
    assert compat["requires_engine"]["capabilities"] == []
    # A newer building engine still stamps the fixed floor, not its own version.
    assert bpa.build_compat("0.9.0", "abc")["requires_engine"]["min_version"] == "0.1.0"


def test_assemble_manifest_stamps_real_engine_sha_not_stale():
    toolchain = {"axiom_rules_engine_ref": "e19f1b75", "axiom_corpus_ref": "7661f3c9"}
    m = bpa.assemble_manifest(
        programs=[{"program_id": "co-snap", "compat": bpa.build_compat("0.1.0", "cafef00dbabe")}],
        corpus={"repo": "rulespec-us", "sha": "733d1a17", "dirty": False},
        composer="0.1.0",
        engine_version="0.1.0",
        engine_sha="cafef00dbabe",
        toolchain=toolchain,
    )
    # The BOM's key assertion: engine identity is a real sha, not the "0.1.0" string.
    assert m["engine"]["git_sha"] == "cafef00dbabe"
    assert m["engine"]["git_sha"] != m["engine_version"]
    # format_version stays 1 (additive change).
    assert m["format_version"] == 1
    # Validation pins are labeled as validation, not build provenance.
    assert m["validation_toolchain"] == toolchain
    # Release binding deferred (not invented).
    assert m["corpus_release"] is None
    # The "corpus" field remains what actually composed (rulespec-us provenance).
    assert m["corpus"]["repo"] == "rulespec-us"
    json.loads(json.dumps(m))  # serializable


def test_manifest_and_program_compat_cannot_disagree():
    # Both the artifact provenance and the per-program manifest entry take the
    # SAME compat object; prove equality holds for a shared instance.
    compat = bpa.build_compat("0.1.0", "cafef00d")
    program_entry = {"program_id": "co-snap", "compat": compat}
    m = bpa.assemble_manifest([program_entry], {}, "0.1.0", "0.1.0", "cafef00d", {})
    assert m["programs"][0]["compat"] is compat
    assert m["programs"][0]["compat"]["built_by_engine"]["git_sha"] == "cafef00d"
