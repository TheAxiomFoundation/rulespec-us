import json
import subprocess
from pathlib import Path

import pytest

from bulk.applied_artifacts import changed_paths, discover_applied_artifacts
from bulk.compute_matrix import select


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


def test_bulk_runners_require_review_before_merge() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/bulk-encode.yml").read_text()
    local_drain = (root / "bulk/local_drain.py").read_text()

    assert "python bulk/applied_artifacts.py" in workflow
    assert 'git switch --detach "origin/$DEFAULT_BRANCH"' in workflow
    assert "--label bulk-encode --draft" in workflow
    assert ".isDraft == true and .autoMergeRequest == null" in workflow
    assert workflow.count("ensure_draft") >= 3
    assert "ensure_draft_pr(branch)" in local_drain
    assert local_drain.count("ensure_draft_pr(branch)") >= 4
    assert 'gh pr merge "$branch" --repo "$GITHUB_REPOSITORY" --auto' not in workflow
    assert '"--label", "bulk-encode",\n             "--draft"' in local_drain
    assert '"pr", "merge", branch, "--repo", REPO, "--auto"' not in local_drain
    assert '"--head",\n            branch,\n            "--json",\n            "number"' in local_drain
    assert "if not existing_pr:" in local_drain
