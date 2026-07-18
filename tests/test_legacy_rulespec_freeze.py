from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tomllib
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


def test_generation_workflows_use_immutable_toolchain() -> None:
    toolchain = tomllib.loads((ROOT / ".axiom/workflow-toolchain.toml").read_text())[
        "workflow_toolchain"
    ]
    assert toolchain == {
        "axiom_encode_version": "0.2.1263",
        "axiom_encode_ref": "1d11a50a9d8c60130aab65c808c1d4919b2aeb49",
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

    bulk_encode = (ROOT / ".github/workflows/bulk-encode.yml").read_text()
    assert "disabled pending reviewed activation" in bulk_encode
    assert "exit 1" in bulk_encode
    assert "axiom_encode.cli encode" not in bulk_encode
    assert "schedule:" not in bulk_encode
