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


def test_accepts_manual_bucket_for_manual_source(tmp_path: Path) -> None:
    citation = "us-mo/manual/dss/snap/1115/block-1"
    module = "us-mo/manual/dss/snap/1115/block-1.yaml"
    test_file = "us-mo/manual/dss/snap/1115/block-1.test.yaml"
    manifest = ".axiom/encoding-manifests/us-mo/manual/dss/snap/1115/block-1.json"
    (tmp_path / module).parent.mkdir(parents=True)
    (tmp_path / module).write_text("format: rulespec/v1\n")
    (tmp_path / test_file).write_text("cases: []\n")
    _write_manifest(
        tmp_path / manifest,
        "us-mo:manual/dss/snap/1115/block-1",
        {module, test_file},
    )

    assert discover_applied_artifacts(
        tmp_path,
        citation=citation,
        paths=[module, test_file, manifest],
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


def test_accepts_canonical_cfr_module_for_regulation_source(tmp_path: Path) -> None:
    citation = "us/regulation/7/247/9/b"
    module = "us/regulations/7-cfr/247/9/b.yaml"
    test_file = "us/regulations/7-cfr/247/9/b.test.yaml"
    manifest = "us/.axiom/encoding-manifests/regulations/7-cfr/247/9/b.json"
    (tmp_path / module).parent.mkdir(parents=True)
    (tmp_path / module).write_text("format: rulespec/v1\n")
    (tmp_path / test_file).write_text("cases: []\n")
    _write_manifest(
        tmp_path / manifest,
        citation,
        {"regulations/7-cfr/247/9/b.yaml", "regulations/7-cfr/247/9/b.test.yaml"},
    )

    assert discover_applied_artifacts(
        tmp_path,
        citation=citation,
        paths=[module, test_file, manifest],
    ) == (module, test_file, manifest)


def test_rejects_cfr_module_for_different_regulation(tmp_path: Path) -> None:
    citation = "us/regulation/7/247/9/b"
    module = "us/regulations/7-cfr/247/9/c.yaml"
    test_file = "us/regulations/7-cfr/247/9/c.test.yaml"
    manifest = "us/.axiom/encoding-manifests/regulations/7-cfr/247/9/c.json"
    (tmp_path / module).parent.mkdir(parents=True)
    (tmp_path / module).write_text("format: rulespec/v1\n")
    (tmp_path / test_file).write_text("cases: []\n")
    _write_manifest(tmp_path / manifest, citation, {module, test_file})

    with pytest.raises(ValueError, match="does not match requested citation"):
        discover_applied_artifacts(
            tmp_path,
            citation=citation,
            paths=[module, test_file, manifest],
        )


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


def test_rejects_exact_request_manifest_for_wrong_module(tmp_path: Path) -> None:
    citation = "us-ca/manual/dss/snap/1105/block-1"
    module = "us-mo/policies/dss/snap/1105/block-1.yaml"
    test_file = "us-mo/policies/dss/snap/1105/block-1.test.yaml"
    manifest = ".axiom/encoding-manifests/us-mo/policies/dss/snap/1105/block-1.json"
    (tmp_path / module).parent.mkdir(parents=True)
    (tmp_path / module).write_text("format: rulespec/v1\n")
    (tmp_path / test_file).write_text("cases: []\n")
    _write_manifest(tmp_path / manifest, citation, {module, test_file})

    with pytest.raises(ValueError, match="does not match requested citation"):
        discover_applied_artifacts(
            tmp_path,
            citation=citation,
            paths=[module, test_file, manifest],
        )


def test_rejects_non_object_manifest(tmp_path: Path) -> None:
    citation = "us-mo/manual/dss/snap/1105/block-1"
    module = "us-mo/manual/dss/snap/1105/block-1.yaml"
    test_file = "us-mo/manual/dss/snap/1105/block-1.test.yaml"
    manifest = ".axiom/encoding-manifests/us-mo/manual/dss/snap/1105/block-1.json"
    (tmp_path / module).parent.mkdir(parents=True)
    (tmp_path / module).write_text("format: rulespec/v1\n")
    (tmp_path / test_file).write_text("cases: []\n")
    (tmp_path / manifest).parent.mkdir(parents=True)
    (tmp_path / manifest).write_text("[]\n")

    with pytest.raises(ValueError, match="must contain a JSON object"):
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


def test_wait_for_checks_rejects_stale_validation(monkeypatch) -> None:
    monkeypatch.setattr(
        _local_drain,
        "gh_json",
        lambda _args: {
            "state": "OPEN",
            "isDraft": True,
            "statusCheckRollup": [
                {
                    "name": "validate / validate (us-mo)",
                    "status": "COMPLETED",
                    "conclusion": "STALE",
                }
            ],
        },
    )

    assert _local_drain.wait_for_checks("bulk/example", timeout_s=1) == (
        "checks=STALE (needs triage)"
    )


def test_unstick_recognizes_both_manifest_roots() -> None:
    assert _local_drain.is_encoding_manifest_path(
        ".axiom/encoding-manifests/us-mo/policies/dss/snap/block-1.json"
    )
    assert _local_drain.is_encoding_manifest_path(
        "us-mo/.axiom/encoding-manifests/policies/dss/snap/block-1.json"
    )
    assert not _local_drain.is_encoding_manifest_path(
        "_axiom/axiom-encode/.axiom/encoding-manifests/example.json"
    )


def test_validation_state_aggregates_all_shards() -> None:
    success = {"name": "validate / validate (us-ca)", "conclusion": "SUCCESS"}
    failure = {"name": "validate / validate (us-ny)", "conclusion": "FAILURE"}
    pending = {"name": "validate / validate (us-tx)", "state": "IN_PROGRESS"}

    assert _local_drain.aggregate_validation_state([success, failure]) == "FAILURE"
    assert _local_drain.aggregate_validation_state([success, pending]) == "PENDING"
    assert _local_drain.aggregate_validation_state([success]) == "SUCCESS"
    assert _local_drain.aggregate_validation_state([]) is None


def test_matrix_preserves_acceptance_criteria() -> None:
    data = {
        "defaults": {"backend": "openai", "model": "gpt-5.5"},
        "entries": [
            {
                "citation": "us-sc/manual/dss/snap-policy-manual/page-159",
                "status": "pending-local",
                "batch": "SNAP-SC-UTIL",
                "note": "Verify mutual exclusivity.",
                "allow_context": [
                    "us/regulations/7-cfr/273/9.yaml",
                    "us/regulations/7-cfr/273/9/d/6/iii.yaml",
                ],
                "requires_merged_citations": ["us-sc/manual/page-163"],
                "program_scope_sync": {
                    "program_spec": "programs/us-sc/snap/fy-2026.yaml",
                    "scope": "state",
                    "add": ["policies/dss/snap-policy-manual/page-159"],
                    "remove": ["policies/dss/snap-policy-manual/page-369"],
                },
            }
        ],
    }

    selected = select(data, "pending-local", "SNAP-SC-UTIL", None)

    assert selected[0]["acceptance_criteria"] == "Verify mutual exclusivity."
    assert selected[0]["allow_context"] == [
        "us/regulations/7-cfr/273/9.yaml",
        "us/regulations/7-cfr/273/9/d/6/iii.yaml",
    ]
    assert selected[0]["requires_merged_citations"] == ["us-sc/manual/page-163"]
    assert selected[0]["program_scope_sync"]["scope"] == "state"


def test_program_scope_sync_uses_pinned_encoder(monkeypatch, tmp_path: Path) -> None:
    calls = []

    def fake_run(command, **_kwargs):
        calls.append(command)
        return 0, "updated\n"

    monkeypatch.setattr(_local_drain, "run", fake_run)
    item = {
        "program_scope_sync": {
            "program_spec": "programs/us-sc/snap/fy-2026.yaml",
            "scope": "state",
            "add": ["policies/dss/snap-policy-manual/page-159"],
            "remove": ["policies/dss/snap-policy-manual/page-369"],
        }
    }

    changed = _local_drain.apply_program_scope_sync(tmp_path, item, {})

    assert changed == ["programs/us-sc/snap/fy-2026.yaml"]
    assert calls == [[
        str(_local_drain.COV_AE), "program-scope-sync", "--repo", str(tmp_path),
        "--program-spec", "programs/us-sc/snap/fy-2026.yaml", "--scope", "state",
        "--add", "policies/dss/snap-policy-manual/page-159",
        "--remove", "policies/dss/snap-policy-manual/page-369",
    ]]


def test_program_scope_sync_rejects_empty_mapping(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="program_spec"):
        _local_drain.apply_program_scope_sync(
            tmp_path, {"program_scope_sync": {}}, {}
        )


def test_matrix_rejects_scalar_dependency_metadata() -> None:
    data = {
        "entries": [{
            "citation": "us-sc/manual/page-159",
            "status": "pending-local",
            "requires_merged_citations": "us-sc/manual/page-163",
        }]
    }

    with pytest.raises(ValueError, match="requires_merged_citations"):
        select(data, "pending-local", None, None)


def test_matrix_rejects_context_outside_repository() -> None:
    data = {
        "entries": [{
            "citation": "us-sc/manual/page-163",
            "status": "pending-local",
            "allow_context": ["/etc/passwd"],
        }]
    }

    with pytest.raises(ValueError, match="escapes the repository"):
        select(data, "pending-local", None, None)


def test_matrix_rejects_context_for_cloud_entry() -> None:
    data = {
        "entries": [{
            "citation": "us-sc/manual/page-163",
            "status": "pending",
            "allow_context": ["us/regulations/7-cfr/273/9.yaml"],
        }]
    }

    with pytest.raises(ValueError, match="not supported for cloud pending"):
        select(data, "pending", None, None)


@pytest.mark.parametrize("status", ["pr-open", "needs-fixtures", "failed", "merged"])
def test_matrix_preserves_context_after_local_status_transition(status: str) -> None:
    data = {
        "entries": [{
            "citation": "us-sc/manual/page-163",
            "status": status,
            "allow_context": ["us/regulations/7-cfr/273/9.yaml"],
        }]
    }

    selected = select(data, "any", None, None)

    assert selected[0]["allow_context"] == ["us/regulations/7-cfr/273/9.yaml"]


def test_encode_command_includes_reviewed_repo_context(tmp_path: Path) -> None:
    context = tmp_path / "us/regulations/7-cfr/273/9.yaml"
    context.parent.mkdir(parents=True)
    context.write_text("format: rulespec/v1\n")

    command = _local_drain.encode_command(
        tmp_path,
        tmp_path / "encode-out",
        {
            "citation": "us-sc/manual/dss/snap-policy-manual/page-163",
            "allow_context": ["us/regulations/7-cfr/273/9.yaml"],
        },
    )

    assert command[-2:] == ["--allow-context", str(context.resolve())]


def test_encode_command_rejects_context_outside_checkout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes the RuleSpec checkout"):
        _local_drain.encode_command(
            tmp_path,
            tmp_path / "encode-out",
            {
                "citation": "us-sc/manual/dss/snap-policy-manual/page-163",
                "allow_context": ["../outside.yaml"],
            },
        )


def test_sc_local_queue_schedules_prerequisites_before_dependent() -> None:
    selected = select(_compute_matrix.load(), "pending-local", None, None)

    citations = [item["citation"] for item in selected]
    assert citations.index("us-sc/manual/dss/snap-policy-manual/page-163") < (
        citations.index("us-sc/manual/dss/snap-policy-manual/page-159")
    )
    assert citations.index("us-sc/manual/dss/snap-policy-manual/page-165") < (
        citations.index("us-sc/manual/dss/snap-policy-manual/page-159")
    )


def test_unstick_recognizes_program_specs() -> None:
    assert _local_drain.PROGRAM_SPEC_RE.match("programs/us-sc/snap/fy-2026.yaml")
    assert not _local_drain.PROGRAM_SPEC_RE.match("us-sc/policies/dss/snap/page.yaml")


def test_worklist_item_for_slug_reads_all_statuses(monkeypatch, tmp_path: Path) -> None:
    item = {
        "citation": "us-sc/manual/page-159",
        "slug": "us-sc-manual-page-159",
        "program_scope_sync": {"program_spec": "programs/us-sc/snap/fy-2026.yaml"},
    }
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command, 0, stdout=json.dumps({"include": [item]}), stderr=""
        )

    monkeypatch.setattr(_local_drain.subprocess, "run", fake_run)

    assert _local_drain.worklist_item_for_slug(
        tmp_path, "us-sc-manual-page-159"
    ) == item
    assert "--status" in calls[0][0]
    assert "any" in calls[0][0]


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
    assert "COV_ENCODER_REF = \"f2b7e2393447deecbadf398c86d2b5f07ec5bfdd\"" in local_drain
    assert '"program-scope-sync", "--help"' in local_drain
    assert "COV_ORACLES_REF = \"9901e2479ac39bba865b8232e1c7d879ba447d8d\"" in local_drain
    assert local_drain.count("require_coverage_ref()") >= 5
