from pathlib import Path

import pytest

from bulk import local_drain
from bulk.compute_matrix import APPROVED_ENCODER_REFS, select

APPROVED_ENCODER_REF = next(iter(APPROVED_ENCODER_REFS))
APPROVED_CLASSIFIER_REF = "d052eabfaa2e209654aa979638672b28d71b3957"
WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "bulk-encode.yml"
REPOSITORY_CHECKS = (
    Path(__file__).parents[1] / ".github" / "workflows" / "repository-checks.yml"
)
LOCAL_DRAIN = Path(__file__).parents[1] / "bulk" / "local_drain.py"


def test_oracle_classifier_does_not_receive_apply_signing_key() -> None:
    workflow = WORKFLOW.read_text()

    assert (
        'env -u AXIOM_ENCODE_APPLY_SIGNING_KEY "$COV_AE" '
        "oracle-coverage-pending sync"
    ) in workflow


def test_bulk_branch_push_uses_full_destination_ref() -> None:
    workflow = WORKFLOW.read_text()

    assert 'push -f origin "HEAD:refs/heads/$branch"' in workflow
    assert 'push -f origin "HEAD:$branch"' not in workflow


def test_review_fix_attestation_is_isolated_and_pinned() -> None:
    workflow = WORKFLOW.read_text()

    assert (
        "if: ${{ github.event_name != 'workflow_dispatch' || "
        "inputs.attest_ref == '' }}" in workflow
    )
    assert (
        "if: ${{ github.event_name == 'workflow_dispatch' && "
        "inputs.attest_ref != '' }}" in workflow
    )
    assert 'bulk/*) ;;' in workflow
    assert "ref: 9978ad8181914affdebcd6fb881291198c3bc839" in workflow
    assert 'python-version: "3.14"' in workflow
    assert "path: target/rulespec-us" in workflow
    assert "working-directory: trusted/axiom-encode-signer" in workflow
    assert "--roots \"$roots\"" in workflow
    assert "generated_paths=(.axiom)" in workflow
    assert 'if [ -d "$target/$jurisdiction/.axiom" ]' in workflow
    assert 'generated_paths+=("$jurisdiction/.axiom")' in workflow
    assert 'git -C "$target" add -A -- "${generated_paths[@]}"' in workflow
    assert "AXIOM_ENCODE_APPLY_SIGNING_KEY: ${{ secrets.AXIOM_ENCODE_APPLY_SIGNING_KEY }}" in workflow
    assert "axiom-encode sign-applied-files" in workflow
    assert "--manual-exception repair" in workflow
    assert 'git -C "$target" push origin "HEAD:refs/heads/$ATTEST_REF"' in workflow


def test_oracle_classifier_uses_reviewed_sync_writer() -> None:
    workflow = WORKFLOW.read_text()

    assert (
        "Checkout oracle-coverage classifier (pinned sync writer)" in workflow
    )
    assert f"ref: {APPROVED_CLASSIFIER_REF}" in workflow
    assert f'expected="{APPROVED_CLASSIFIER_REF}"' in workflow
    assert 'actual="$(git -C _axiom/axiom-encode-oracle-coverage rev-parse HEAD)"' in workflow
    assert '--root "$GITHUB_WORKSPACE/.."' in workflow
    assert "--repo rulespec-us" not in workflow
    assert (
        f"oracle-coverage-axiom-encode-ref: {APPROVED_CLASSIFIER_REF}"
        in REPOSITORY_CHECKS.read_text()
    )


def test_local_drain_uses_exact_checkout_sync_contract() -> None:
    local_drain = LOCAL_DRAIN.read_text()

    assert '"--root", str(leaf.parent), "--source", "bulk"' in local_drain
    assert '"--root", str(leaf.parent), "--repo"' not in local_drain


def test_local_pending_sync_strips_apply_signing_key(monkeypatch, tmp_path) -> None:
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured.update(kwargs)
        return 0, "synced"

    monkeypatch.setattr(local_drain, "run", fake_run)

    assert local_drain.sync_pending(tmp_path) == "synced"
    assert captured["unset_env"] == ("AXIOM_ENCODE_APPLY_SIGNING_KEY",)
    assert captured["cmd"][-4:] == [
        "--root",
        str(tmp_path.parent),
        "--source",
        "bulk",
    ]


def test_local_worktree_uses_same_named_wrapper(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(local_drain, "WT_ROOT", tmp_path / "wt")
    monkeypatch.setattr(local_drain, "CHECKOUT", tmp_path / "checkout")
    monkeypatch.setattr(local_drain, "ENGINE", tmp_path / "engine")
    monkeypatch.setattr(local_drain, "CORPUS", tmp_path / "corpus")
    monkeypatch.setattr(local_drain, "run", lambda *_args, **_kwargs: (0, ""))

    leaf = local_drain.make_worktree("example", "origin/main")

    assert leaf == tmp_path / "wt/example/rulespec-us/rulespec-us"
    assert (leaf.parent / "axiom-rules-engine").is_symlink()
    assert (leaf.parent / "axiom-corpus").is_symlink()


def test_local_encoder_mismatch_is_resumable(monkeypatch) -> None:
    monkeypatch.setattr(local_drain, "already_handled", lambda _slug: False)
    monkeypatch.setattr(
        local_drain,
        "run",
        lambda *_args, **_kwargs: (0, "3869d66d009f52258be35901edbef370e65a399c\n"),
    )

    result = local_drain.encode_entry(
        {
            "citation": "us-mo/manual/example/block-1",
            "slug": "us-mo-manual-example-block-1",
            "encoder_ref": APPROVED_ENCODER_REF,
        }
    )

    assert result["status"] == "config-mismatch"
    assert "generation encoder revision mismatch" in result["detail"]


def test_local_doctor_rejects_obsolete_sync_contract(monkeypatch, tmp_path) -> None:
    interpreter = tmp_path / "python"
    interpreter.touch()
    checkout = tmp_path / "axiom-encode-cov"
    package = checkout / "src/axiom_encode"
    package.mkdir(parents=True)
    source = package / "__init__.py"
    source.touch()
    monkeypatch.setattr(local_drain, "COV_PY", interpreter)
    monkeypatch.setattr(local_drain, "COV_CHECKOUT", checkout)

    def fake_run(cmd, **_kwargs):
        if cmd[0] == "git":
            if cmd[-2:] == ["rev-parse", "HEAD"]:
                return 0, f"{APPROVED_CLASSIFIER_REF}\n"
            return 0, ""
        if "-c" in cmd:
            if "direct_url.json" in cmd[-1]:
                return 0, f"{local_drain.APPROVED_ORACLES_REF}\n"
            return 0, f"{source.resolve()}\n"
        return 0, "usage: sync --root ROOT --repo REPO"

    monkeypatch.setattr(local_drain, "run", fake_run)

    ok, detail = local_drain.coverage_sync_writer_status()
    assert not ok
    assert detail == "executable lacks exact-checkout sync contract"


def test_select_carries_entry_encoder_ref_into_matrix() -> None:
    data = {
        "defaults": {
            "backend": "openai",
            "model": "gpt-5.5",
                "encoder_ref": APPROVED_ENCODER_REF,
        },
        "entries": [
            {
                "citation": "us-mo/manual/dss/snap/1105/block-1",
                "repo": "rulespec-us",
                "batch": "SNAP-MO-1",
                "status": "pending",
                "encoder_ref": APPROVED_ENCODER_REF,
            },
            {
                "citation": "us-il/statute/35/5/402",
                "status": "pending",
            },
        ],
    }

    selected = select(data, "pending", "snap-mo-1", 1)

    assert selected == [
        {
            "citation": "us-mo/manual/dss/snap/1105/block-1",
            "repo": "rulespec-us",
            "backend": "openai",
            "model": "gpt-5.5",
            "encoder_ref": APPROVED_ENCODER_REF,
            "slug": "us-mo-manual-dss-snap-1105-block-1",
        }
    ]


def test_select_uses_default_encoder_ref() -> None:
    data = {
        "defaults": {"encoder_ref": APPROVED_ENCODER_REF},
        "entries": [
            {
                "citation": "us-il/statute/35/5/402",
                "status": "pending",
            }
        ],
    }

    assert select(data, "pending", None, None)[0]["encoder_ref"] == APPROVED_ENCODER_REF


def test_select_rejects_mutable_encoder_ref() -> None:
    data = {
        "entries": [
            {
                "citation": "us-mo/manual/dss/snap/1105/block-1",
                "status": "pending",
                "encoder_ref": "compat/manual-signing",
            }
        ]
    }

    with pytest.raises(ValueError, match="full 40-character lowercase commit SHA"):
        select(data, "pending", None, None)


def test_select_without_override_keeps_toolchain_fallback() -> None:
    data = {
        "entries": [
            {
                "citation": "us-il/statute/35/5/402",
                "status": "pending",
            }
        ]
    }

    assert select(data, "pending", None, None)[0]["encoder_ref"] == ""


def test_select_rejects_unapproved_immutable_encoder_ref() -> None:
    data = {
        "entries": [
            {
                "citation": "us-mo/manual/dss/snap/1105/block-1",
                "status": "pending",
                "encoder_ref": "f" * 40,
            }
        ]
    }

    with pytest.raises(ValueError, match="reviewed compatibility allowlist"):
        select(data, "pending", None, None)
