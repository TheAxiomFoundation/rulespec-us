from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "tools/check_legacy_rulespec_freeze.py"
FROZEN_PATH = Path("us-mo/manual/snap/block-1.yaml")


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "legacy_rulespec_freeze", CHECKER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _write_manifest(root: Path, artifacts: dict[str, str]) -> None:
    path = root / ".axiom/legacy-rulespec-freeze.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"format": "axiom/legacy-rulespec-freeze/v1", "artifacts": artifacts}
        )
    )


def _freeze_repo(tmp_path: Path) -> tuple[Path, Path]:
    artifact = tmp_path / FROZEN_PATH
    artifact.parent.mkdir(parents=True)
    artifact.write_text("value: original\n")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    _write_manifest(tmp_path, {str(FROZEN_PATH): digest})
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "freeze-test@example.com")
    _git(tmp_path, "config", "user.name", "Freeze Test")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "base")
    return tmp_path, artifact


def test_frozen_legacy_inventory_matches_repository() -> None:
    subprocess.run([sys.executable, CHECKER_PATH], cwd=ROOT, check=True)

    payload = json.loads((ROOT / ".axiom/legacy-rulespec-freeze.json").read_text())
    for relative_path, expected_digest in payload["artifacts"].items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_digest
        )


def test_classifier_covers_only_legacy_yaml() -> None:
    checker = _load_checker()

    assert checker._is_legacy_rulespec_path("us-mo/block-1.yaml")
    assert checker._is_legacy_rulespec_path("us-mo/manual/snap/block-1.yaml")
    assert not checker._is_legacy_rulespec_path("us-mo/policies/snap/block-1.yaml")
    assert not checker._is_legacy_rulespec_path("us-mo/programs/snap/fy-2026.yaml")
    assert not checker._is_frozen_artifact_path(
        ".axiom/encoding-manifests/us-mo/manual/dss/snap/1115-000-00/"
        "1115-035-00/1115-035-25/block-1.json"
    )
    assert not checker._is_frozen_artifact_path(
        ".axiom/encoding-manifests/us-mo/policies/dss/snap/block-1.json"
    )


def test_required_workflow_runs_freeze_before_validation() -> None:
    workflow = (ROOT / ".github/workflows/repository-checks.yml").read_text()

    assert "legacy-rulespec-freeze:" in workflow
    assert "needs: [legacy-rulespec-freeze, workflow-toolchain]" in workflow
    assert "d96c5d81f4e386a4e48b5d4f2a7435a13e28c812" in workflow
    assert (
        "run-generated-guard: ${{ github.event_name != 'pull_request' || "
        "github.event.pull_request.number != 911 }}"
    ) in workflow


def test_generation_workflows_use_immutable_toolchain() -> None:
    toolchain = tomllib.loads((ROOT / ".axiom/workflow-toolchain.toml").read_text())[
        "workflow_toolchain"
    ]
    assert toolchain == {
        "axiom_encode_version": "0.2.1268",
        "axiom_compose_ref": "fabe0b3b3fd6e90d3e8f075516f9b668f524f711",
        "axiom_encode_ref": "1d44d71080df90bfeb514283be2f3ff4ffc04776",
        "axiom_rules_engine_ref": "05eac9d2f89dabe5c6673176260762cef3a58f47",
        "axiom_corpus_ref": "df57dc57cf0152c5747696c078929a12ed2d2239",
        "rulespec_us_ref": "0f291b367bf7e15555f9973112278c5cbf221653",
    }

    source_staleness = (ROOT / ".github/workflows/source-staleness.yml").read_text()
    assert '.axiom/workflow-toolchain.toml").read_text()' in source_staleness
    assert 'ref: "main"' not in source_staleness

    repository_checks = (ROOT / ".github/workflows/repository-checks.yml").read_text()
    assert '.axiom/workflow-toolchain.toml").read_text()' in repository_checks
    workflow_inputs = {
        "axiom-encode-ref": "axiom_encode_ref",
        "axiom-rules-engine-ref": "axiom_rules_engine_ref",
        "axiom-corpus-ref": "axiom_corpus_ref",
        "rulespec-us-ref": "rulespec_us_ref",
    }
    for input_name, output_name in workflow_inputs.items():
        assert (
            f"{input_name}: ${{{{ needs.workflow-toolchain.outputs.{output_name} }}}}"
            in repository_checks
        )
    for value in toolchain.values():
        assert value not in repository_checks

    program_artifacts = (ROOT / ".github/workflows/program-artifacts.yml").read_text()
    assert '.axiom/workflow-toolchain.toml").read_text()' in program_artifacts
    assert "e19f1b7573c74512f20a6b71a0c55dbbf333d41b" not in program_artifacts
    assert "${{ steps.toolchain.outputs.axiom_rules_engine_ref }}" in program_artifacts
    assert "${{ steps.toolchain.outputs.axiom_compose_ref }}" in program_artifacts

    bulk_encode = (ROOT / ".github/workflows/bulk-encode.yml").read_text()
    assert "disabled pending reviewed activation" in bulk_encode
    assert "exit 1" in bulk_encode
    assert "axiom_encode.cli encode" not in bulk_encode
    assert "schedule:" not in bulk_encode


def test_freeze_rejects_unlisted_tracked_addition(tmp_path: Path) -> None:
    root, _ = _freeze_repo(tmp_path)
    addition = root / "us-mo/manual/snap/block-2.yaml"
    addition.write_text("value: added\n")
    _git(root, "add", str(addition.relative_to(root)))

    with pytest.raises(ValueError, match="unlisted=.*block-2.yaml"):
        _load_checker().check(root)


def test_freeze_rejects_tracked_deletion(tmp_path: Path) -> None:
    root, artifact = _freeze_repo(tmp_path)
    artifact.unlink()
    _git(root, "add", "-u")

    with pytest.raises(ValueError, match="missing=.*block-1.yaml"):
        _load_checker().check(root)


def test_freeze_rejects_content_mutation(tmp_path: Path) -> None:
    root, artifact = _freeze_repo(tmp_path)
    artifact.write_text("value: changed\n")

    with pytest.raises(ValueError, match="digest mismatch"):
        _load_checker().check(root)


def test_freeze_rejects_symlink_substitution(tmp_path: Path) -> None:
    root, artifact = _freeze_repo(tmp_path)
    target = root / "replacement.yaml"
    target.write_text("value: original\n")
    artifact.unlink()
    artifact.symlink_to(target)

    with pytest.raises(ValueError, match="not a regular file"):
        _load_checker().check(root)


def test_freeze_rejects_base_ref_change_even_after_digest_update(
    tmp_path: Path,
) -> None:
    root, artifact = _freeze_repo(tmp_path)
    base = _git(root, "rev-parse", "HEAD")
    artifact.write_text("value: reviewed-change\n")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    _write_manifest(root, {str(FROZEN_PATH): digest})
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "change frozen artifact")

    with pytest.raises(ValueError, match="pull request changes frozen"):
        _load_checker().check(root, base_ref=base)
