import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


def _load_bulk_module(name: str):
    bulk_dir = Path(__file__).resolve().parents[1] / "bulk"
    path = bulk_dir / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"bulk_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(bulk_dir))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(bulk_dir))
    return module


_applied_artifacts = _load_bulk_module("applied_artifacts")
_compute_matrix = _load_bulk_module("compute_matrix")
_local_drain = _load_bulk_module("local_drain")
changed_paths = _applied_artifacts.changed_paths
discover_applied_artifacts = _applied_artifacts.discover_applied_artifacts
select = _compute_matrix.select


def _write_manifest(path: Path, citation: str, applied_paths: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "citation": citation,
                "applied_files": [
                    {"path": applied_path, "sha256": "0" * 64}
                    for applied_path in sorted(applied_paths)
                ],
            }
        )
    )


def test_discovers_repo_root_manifest_for_manual_module(tmp_path: Path) -> None:
    citation = "us-mo/manual/dss/snap/1105/block-1"
    module = "us-mo/policies/dss/snap/1105/block-1.yaml"
    test_file = "us-mo/policies/dss/snap/1105/block-1.test.yaml"
    manifest = ".axiom/encoding-manifests/us-mo/policies/dss/snap/1105/block-1.json"
    (tmp_path / module).parent.mkdir(parents=True)
    (tmp_path / module).write_text("format: rulespec/v1\n")
    (tmp_path / test_file).write_text("cases: []\n")
    _write_manifest(
        tmp_path / manifest,
        "us-mo:policies/dss/snap/1105/block-1",
        {module, test_file},
    )
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)

    assert discover_applied_artifacts(
        tmp_path,
        citation=citation,
    ) == (module, test_file, manifest)


def test_discovers_jurisdiction_manifest_for_legacy_module(tmp_path: Path) -> None:
    citation = "us-oh/statute/5747.71"
    module = "us-oh/statutes/5747/71.yaml"
    test_file = "us-oh/statutes/5747/71.test.yaml"
    manifest = "us-oh/.axiom/encoding-manifests/statutes/5747/71.json"
    (tmp_path / module).parent.mkdir(parents=True)
    (tmp_path / module).write_text("format: rulespec/v1\n")
    (tmp_path / test_file).write_text("cases: []\n")
    _write_manifest(
        tmp_path / manifest,
        citation,
        {"statutes/5747/71.yaml", "statutes/5747/71.test.yaml"},
    )

    assert discover_applied_artifacts(
        tmp_path,
        citation=citation,
        paths=[module, test_file, manifest],
    ) == (module, test_file, manifest)


def test_changed_paths_ignores_rename_source_record(tmp_path: Path) -> None:
    old_module = "us-mo/manual/dss/snap/old.yaml"
    new_module = "us-mo/manual/dss/snap/new.yaml"
    (tmp_path / old_module).parent.mkdir(parents=True)
    (tmp_path / old_module).write_text("format: rulespec/v1\n")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", old_module], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=Axiom Test",
            "-c",
            "user.email=test@axiom.invalid",
            "commit",
            "-q",
            "-m",
            "fixture",
        ],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "mv", old_module, new_module], check=True
    )

    assert changed_paths(tmp_path) == [new_module]


def test_accepts_manifest_covering_only_changed_module(tmp_path: Path) -> None:
    citation = "us-mo/manual/dss/snap/1105/block-1"
    module = "us-mo/policies/dss/snap/1105/block-1.yaml"
    test_file = "us-mo/policies/dss/snap/1105/block-1.test.yaml"
    manifest = ".axiom/encoding-manifests/us-mo/policies/dss/snap/1105/block-1.json"
    (tmp_path / module).parent.mkdir(parents=True)
    (tmp_path / module).write_text("format: rulespec/v1\n")
    (tmp_path / test_file).write_text("cases: []\n")
    _write_manifest(tmp_path / manifest, citation, {module})

    assert discover_applied_artifacts(
        tmp_path,
        citation=citation,
        paths=[module, manifest],
    ) == (module, test_file, manifest)


@pytest.mark.parametrize(
    ("extra_path", "message"),
    [
        ("us-mo/manual/dss/snap/1105/other.yaml", "expected one applied module"),
        (
            ".axiom/encoding-manifests/us-mo/manual/dss/snap/1105/other.json",
            "expected one applied manifest",
        ),
    ],
)
def test_rejects_ambiguous_artifacts(
    tmp_path: Path, extra_path: str, message: str
) -> None:
    citation = "us-mo/manual/dss/snap/1105/block-1"
    module = "us-mo/manual/dss/snap/1105/block-1.yaml"
    test_file = "us-mo/manual/dss/snap/1105/block-1.test.yaml"
    manifest = ".axiom/encoding-manifests/us-mo/manual/dss/snap/1105/block-1.json"
    (tmp_path / test_file).parent.mkdir(parents=True)
    (tmp_path / module).write_text("format: rulespec/v1\n")
    (tmp_path / test_file).write_text("cases: []\n")
    _write_manifest(tmp_path / manifest, citation, {module, test_file})
    if extra_path.endswith(".json"):
        _write_manifest(tmp_path / extra_path, citation, {module, test_file})

    with pytest.raises(ValueError, match=message):
        discover_applied_artifacts(
            tmp_path,
            citation=citation,
            paths=[module, test_file, manifest, extra_path],
        )


def test_rejects_manifest_for_different_citation(tmp_path: Path) -> None:
    citation = "us-mo/manual/dss/snap/1105/block-1"
    module = "us-mo/manual/dss/snap/1105/block-1.yaml"
    test_file = "us-mo/manual/dss/snap/1105/block-1.test.yaml"
    manifest = ".axiom/encoding-manifests/us-mo/manual/dss/snap/1105/block-1.json"
    (tmp_path / test_file).parent.mkdir(parents=True)
    (tmp_path / module).write_text("format: rulespec/v1\n")
    (tmp_path / test_file).write_text("cases: []\n")
    _write_manifest(tmp_path / manifest, "us-mo:policies/dss/snap/other", {module, test_file})

    with pytest.raises(ValueError, match="does not match"):
        discover_applied_artifacts(
            tmp_path,
            citation=citation,
            paths=[module, test_file, manifest],
        )


def test_rejects_canonical_manifest_for_wrong_requested_jurisdiction(
    tmp_path: Path,
) -> None:
    citation = "us-ca/manual/dss/snap/1105/block-1"
    module = "us-mo/policies/dss/snap/1105/block-1.yaml"
    test_file = "us-mo/policies/dss/snap/1105/block-1.test.yaml"
    manifest = ".axiom/encoding-manifests/us-mo/policies/dss/snap/1105/block-1.json"
    (tmp_path / module).parent.mkdir(parents=True)
    (tmp_path / module).write_text("format: rulespec/v1\n")
    (tmp_path / test_file).write_text("cases: []\n")
    _write_manifest(
        tmp_path / manifest,
        "us-mo:policies/dss/snap/1105/block-1",
        {module, test_file},
    )

    with pytest.raises(ValueError, match="does not match"):
        discover_applied_artifacts(
            tmp_path,
            citation=citation,
            paths=[module, test_file, manifest],
        )


def test_pr_lookup_failure_pauses_without_permanent_failure(monkeypatch) -> None:
    _local_drain._PAUSE.clear()
    monkeypatch.setattr(_local_drain, "gh_json", lambda _args: None)

    result = _local_drain.encode_entry(
        {"citation": "us-mo/manual/dss/snap/1105/block-1", "slug": "retry"}
    )

    assert result["status"] == "paused"
    assert "retry drain" in result["detail"]
    assert _local_drain._PAUSE.is_set()
    _local_drain._PAUSE.clear()


def test_matrix_preserves_acceptance_criteria() -> None:
    data = {
        "defaults": {"backend": "openai", "model": "gpt-5.5"},
        "entries": [
            {
                "citation": "us-sc/manual/dss/snap-policy-manual/page-159",
                "status": "pending",
                "batch": "SNAP-SC-UTIL",
                "note": "Verify mutual exclusivity.",
            }
        ],
    }

    selected = select(data, "pending", "SNAP-SC-UTIL", None)

    assert selected[0]["acceptance_criteria"] == "Verify mutual exclusivity."


def test_local_runner_requires_review_before_merge() -> None:
    root = Path(__file__).resolve().parents[1]
    local_drain = (root / "bulk/local_drain.py").read_text()

    assert "discover_applied_artifacts(" in local_drain
    assert "ensure_draft_pr(branch)" in local_drain
    assert local_drain.count("ensure_draft_pr(branch)") >= 4
    assert '"--label", "bulk-encode",\n             "--draft"' in local_drain
    assert '"pr", "merge", branch, "--repo", REPO, "--auto"' not in local_drain
    assert '"--head",\n            branch,\n            "--json",\n            "number"' in local_drain
    assert "if not existing_pr:" in local_drain
    assert "wait_for_merge" not in local_drain
    assert 'startswith("validate / validate")' in local_drain
    assert "if validation_checks and not pending:" in local_drain
    assert 'return "checks complete; draft review required"' in local_drain
    assert "could not determine PR state" in local_drain
    assert "before push" in local_drain
    assert "COV_ENCODER_REF = \"c83416309a4331d225bcde16907e3b4eb79e26f1\"" in local_drain
    assert "COV_ORACLES_REF = \"9901e2479ac39bba865b8232e1c7d879ba447d8d\"" in local_drain
    assert local_drain.count("require_coverage_ref()") >= 5
