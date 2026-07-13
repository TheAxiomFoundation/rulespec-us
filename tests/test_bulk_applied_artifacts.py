import json
import subprocess
from pathlib import Path

import pytest

from bulk.applied_artifacts import discover_applied_artifacts


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
    module = "us-mo/manual/dss/snap/1105/block-1.yaml"
    test_file = "us-mo/manual/dss/snap/1105/block-1.test.yaml"
    manifest = ".axiom/encoding-manifests/us-mo/manual/dss/snap/1105/block-1.json"
    (tmp_path / module).parent.mkdir(parents=True)
    (tmp_path / module).write_text("format: rulespec/v1\n")
    (tmp_path / test_file).write_text("cases: []\n")
    _write_manifest(tmp_path / manifest, citation, {module, test_file})
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
    _write_manifest(tmp_path / manifest, "us-mo/manual/different", {module, test_file})

    with pytest.raises(ValueError, match="does not match"):
        discover_applied_artifacts(
            tmp_path,
            citation=citation,
            paths=[module, test_file, manifest],
        )
