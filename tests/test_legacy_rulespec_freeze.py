from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "tools/check_legacy_rulespec_freeze.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "legacy_rulespec_freeze", CHECKER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_legacy_inventory_matches_repository() -> None:
    subprocess.run([sys.executable, CHECKER_PATH], cwd=ROOT, check=True)

    payload = json.loads((ROOT / ".axiom/legacy-rulespec-freeze.json").read_text())
    for relative_path, expected_digest in payload["artifacts"].items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_digest
        )


def test_classifier_covers_legacy_yaml_and_its_apply_manifest() -> None:
    checker = _load_checker()

    assert checker._is_legacy_rulespec_path("us-mo/block-1.yaml")
    assert checker._is_legacy_rulespec_path("us-mo/manual/snap/block-1.yaml")
    assert not checker._is_legacy_rulespec_path("us-mo/policies/snap/block-1.yaml")
    assert not checker._is_legacy_rulespec_path("us-mo/programs/snap/fy-2026.yaml")
    assert checker._is_frozen_artifact_path(
        ".axiom/encoding-manifests/us-mo/manual/dss/snap/1115-000-00/"
        "1115-035-00/1115-035-25/block-1.json"
    )
    assert not checker._is_frozen_artifact_path(
        ".axiom/encoding-manifests/us-mo/policies/dss/snap/block-1.json"
    )


def test_required_workflow_runs_freeze_before_validation() -> None:
    workflow = (ROOT / ".github/workflows/repository-checks.yml").read_text()

    assert "legacy-rulespec-freeze:" in workflow
    assert "needs: legacy-rulespec-freeze" in workflow
    assert "eeae9f707e71819960c36c7ef0f03e796770096a" in workflow
    assert "d96c5d81f4e386a4e48b5d4f2a7435a13e28c812" in workflow
