from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import date
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
import yaml


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools/build_program_artifacts.py"
MODULE_SPEC = importlib.util.spec_from_file_location(
    "build_program_artifacts", MODULE_PATH
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
artifacts = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = artifacts
MODULE_SPEC.loader.exec_module(artifacts)

TEST_TOOLCHAIN = {
    "axiom_compose_ref": "1" * 40,
    "axiom_encode_ref": "2" * 40,
    "axiom_rules_engine_ref": "3" * 40,
}


def write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def write_module(path: Path, *, imports: list[str] | None = None, extends=None) -> None:
    payload: dict[str, object] = {
        "format": "rulespec/v1",
        "module": {"summary": path.stem},
        "rules": [],
    }
    if imports is not None:
        payload["imports"] = imports
    if extends is not None:
        payload["extends"] = extends
    write_yaml(path, payload)


def write_program(root: Path, *, scope_path: str = "policies/root") -> Path:
    path = root / "programs" / "us" / "demo" / "fy-2026.yaml"
    write_yaml(
        path,
        {
            "program": "us/demo",
            "period": "2026-01",
            "outputs": ["demo"],
            "scope": {"federal": [scope_path]},
        },
    )
    return path


def patch_non_git_build(
    monkeypatch: pytest.MonkeyPatch, active_paths: set[str] | None = None
) -> None:
    monkeypatch.setenv("AXIOM_RULES_ENGINE_BIN", "fake-engine")
    monkeypatch.setattr(
        artifacts,
        "load_waived_module_paths",
        lambda root: set(active_paths or ()),
    )
    monkeypatch.setattr(
        artifacts,
        "corpus_provenance",
        lambda root: {"repo": "rulespec-us", "sha": "a" * 40, "dirty": False},
    )
    for manifest_key, environment_key in artifacts.TOOLCHAIN_REF_ENV.items():
        monkeypatch.setenv(environment_key, TEST_TOOLCHAIN[manifest_key])


def install_fake_waiver_core(
    monkeypatch: pytest.MonkeyPatch,
    *,
    active_paths: object,
    error: Exception | None = None,
) -> dict[str, object]:
    captured: dict[str, object] = {}
    package = ModuleType("axiom_encode")
    package.__path__ = []  # type: ignore[attr-defined]
    core = ModuleType("axiom_encode.validation_waivers")

    def load_validation_waivers(path, *, repo_root, today=None):
        captured.update(path=path, repo_root=repo_root, today=today)
        if error is not None:
            raise error
        return SimpleNamespace(active_paths=active_paths)

    core.load_validation_waivers = load_validation_waivers  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "axiom_encode", package)
    monkeypatch.setitem(sys.modules, "axiom_encode.validation_waivers", core)
    return captured


def test_waiver_loader_delegates_schema_to_canonical_core(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "rulespec-us"
    write_module(root / "us" / "policies" / "active.yaml")
    captured = install_fake_waiver_core(
        monkeypatch,
        active_paths={"us/policies/active.yaml"},
    )

    assert artifacts.load_waived_module_paths(root, today=date(2026, 7, 10)) == {
        "us/policies/active.yaml"
    }
    assert captured == {
        "path": root / "known-validation-gaps.yaml",
        "repo_root": root,
        "today": date(2026, 7, 10),
    }


def test_waiver_loader_wraps_canonical_schema_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "rulespec-us"
    install_fake_waiver_core(
        monkeypatch,
        active_paths=set(),
        error=ValueError("duplicate waiver key"),
    )

    with pytest.raises(artifacts.BuildSafetyError, match="duplicate waiver key"):
        artifacts.load_waived_module_paths(root)


@pytest.mark.parametrize(
    "environment_key, value",
    [
        ("AXIOM_COMPOSE_REF", "main"),
        ("AXIOM_ENCODE_REF", "A" * 40),
        ("AXIOM_RULES_ENGINE_REF", "3" * 39),
    ],
)
def test_toolchain_provenance_requires_exact_commit_refs(
    environment_key: str, value: str
) -> None:
    environ = {
        artifacts.TOOLCHAIN_REF_ENV[key]: ref for key, ref in TEST_TOOLCHAIN.items()
    }
    environ[environment_key] = value

    with pytest.raises(artifacts.BuildSafetyError, match=environment_key):
        artifacts.load_toolchain_provenance(environ)


@pytest.mark.parametrize(
    "active_path, message",
    [
        ("../outside.yaml", "unsafe"),
        ("us/policies/missing.yaml", "does not exist"),
    ],
)
def test_waiver_loader_rechecks_rulespec_us_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    active_path: str,
    message: str,
) -> None:
    root = tmp_path / "rulespec-us"
    install_fake_waiver_core(monkeypatch, active_paths={active_path})

    with pytest.raises(artifacts.BuildSafetyError, match=message):
        artifacts.load_waived_module_paths(root)


def test_corpus_mirror_physically_omits_active_waivers(tmp_path: Path) -> None:
    root = tmp_path / "source" / "rulespec-us"
    write_module(root / "us" / "policies" / "safe.yaml")
    write_module(root / "us" / "policies" / "waived.yaml")
    write_module(root / "us" / "policies" / "pending.yaml")
    write_module(root / "us" / "policies" / "safe.test.yaml")
    mirror = tmp_path / "sandbox" / "rulespec-us"

    copied = artifacts.create_non_waived_corpus_mirror(
        root, mirror, {"us/policies/waived.yaml"}
    )

    assert copied == 2
    assert (mirror / "us/policies/safe.yaml").is_file()
    assert (mirror / "us/policies/pending.yaml").is_file()
    assert not (mirror / "us/policies/waived.yaml").exists()
    assert not (mirror / "us/policies/safe.test.yaml").exists()


def test_corpus_mirror_rejects_module_symlinks(tmp_path: Path) -> None:
    root = tmp_path / "source" / "rulespec-us"
    outside = tmp_path / "outside.yaml"
    write_module(outside)
    linked = root / "us" / "policies" / "linked.yaml"
    linked.parent.mkdir(parents=True)
    linked.symlink_to(outside)

    with pytest.raises(artifacts.BuildSafetyError, match="not a regular file"):
        artifacts.create_non_waived_corpus_mirror(
            root, tmp_path / "sandbox/rulespec-us", set()
        )


def test_program_discovery_rejects_symlink_specs(tmp_path: Path) -> None:
    root = tmp_path / "rulespec-us"
    outside = tmp_path / "outside-program.yaml"
    write_yaml(
        outside,
        {
            "program": "us/demo",
            "period": "2026-01",
            "outputs": ["demo"],
        },
    )
    linked = root / "programs" / "us" / "demo" / "fy-2026.yaml"
    linked.parent.mkdir(parents=True)
    linked.symlink_to(outside)

    with pytest.raises(artifacts.BuildSafetyError, match="not a regular file"):
        artifacts.discover_specs(root)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO requires POSIX")
def test_program_discovery_rejects_non_regular_specs(tmp_path: Path) -> None:
    root = tmp_path / "rulespec-us"
    fifo = root / "programs" / "us" / "demo" / "fy-2026.yaml"
    fifo.parent.mkdir(parents=True)
    os.mkfifo(fifo)

    with pytest.raises(artifacts.BuildSafetyError, match="not a regular file"):
        artifacts.discover_specs(root)


def test_real_composer_resolves_country_monorepo_targets(tmp_path: Path) -> None:
    pytest.importorskip("axiom_compose")
    root = tmp_path / "source" / "rulespec-us"
    write_module(
        root / "us" / "policies" / "root.yaml",
        imports=["us:policies/child"],
    )
    write_module(root / "us" / "policies" / "child.yaml")
    write_program(root)
    mirror = tmp_path / "sandbox" / "rulespec-us"
    artifacts.create_non_waived_corpus_mirror(root, mirror, set())

    output = tmp_path / "program.rulespec.yaml"
    artifacts.compose_spec(root, mirror, artifacts.discover_specs(root)[0], output)

    payload = yaml.safe_load(output.read_text())
    assert payload["imports"] == [
        "us:policies/root",
        "us:policies/child",
    ]


def test_dependency_audit_finds_relative_transitive_and_extends_waiver(
    tmp_path: Path,
) -> None:
    root = tmp_path / "rulespec-us"
    write_module(
        root / "us" / "policies" / "root.yaml",
        imports=["./child.yaml#child"],
    )
    write_module(
        root / "us" / "policies" / "child.yaml",
        extends="./waived#base",
    )
    write_module(root / "us" / "policies" / "waived.yaml")
    program = write_program(root)
    build = artifacts.discover_specs(root)[0]
    graph = artifacts.CorpusDependencyGraph(root)

    assert program == root / build.spec_path
    assert artifacts.waived_dependencies(
        graph,
        artifacts.declared_program_imports(root, build),
        {"us:policies/waived": "us/policies/waived.yaml"},
    ) == ["us/policies/waived.yaml"]


def test_compiled_origin_audit_is_defense_in_depth(tmp_path: Path) -> None:
    artifact = tmp_path / "compiled.json"
    artifact.write_text(
        json.dumps(
            {
                "program": {
                    "derived": [{"id": "us:policies/waived#amount", "name": "amount"}]
                }
            }
        )
    )

    with pytest.raises(artifacts.BuildSafetyError, match="waived module origins"):
        artifacts.assert_artifact_has_no_waived_origins(
            artifact,
            {"us:policies/waived": "us/policies/waived.yaml"},
        )


def test_engine_compile_uses_only_isolated_root_and_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus_root = tmp_path / "sandbox" / "rulespec-us"
    module = tmp_path / "sandbox" / "program.rulespec.yaml"
    artifact = tmp_path / "sandbox" / "program.compiled.json"
    captured = {}

    def fake_run(command, **kwargs):
        captured.update(command=command, **kwargs)
        return SimpleNamespace(returncode=0, stdout="engine_version: test\n", stderr="")

    monkeypatch.setattr(artifacts.subprocess, "run", fake_run)

    assert (
        artifacts.engine_compile(
            corpus_root,
            module,
            artifact,
            "engine",
            cwd=tmp_path / "sandbox",
        )
        == "test"
    )
    assert captured["env"]["AXIOM_RULESPEC_REPO_ROOTS"] == str(corpus_root)
    assert "--exclusive-rulespec-roots" in captured["command"]
    assert captured["cwd"] == tmp_path / "sandbox"


def test_main_excludes_waived_program_and_removes_stale_dist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "rulespec-us"
    write_module(root / "us" / "policies" / "waived.yaml")
    write_program(root, scope_path="policies/waived")
    dist = root / "dist"
    dist.mkdir()
    (dist / "stale-waived.compiled.json").write_text("stale")
    patch_non_git_build(monkeypatch, {"us/policies/waived.yaml"})
    monkeypatch.setattr(
        artifacts,
        "compose_spec",
        lambda *args, **kwargs: pytest.fail("waived program was composed"),
    )

    assert artifacts.main(["--root", str(root), "--dist", str(dist)]) == 0

    manifest = json.loads((dist / "manifest.json").read_text())
    assert manifest["format_version"] == 2
    assert manifest["programs"] == []
    assert manifest["excluded_programs"] == [
        {
            "spec_path": "programs/us/demo/fy-2026.yaml",
            "reason": "active_validate_failure_waiver",
            "waived_modules": ["us/policies/waived.yaml"],
        }
    ]
    assert not (dist / "stale-waived.compiled.json").exists()


def test_main_rejects_non_waived_failure_even_with_legacy_allowlist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "rulespec-us"
    write_module(root / "us" / "policies" / "broken.yaml")
    program = write_program(root, scope_path="policies/broken")
    legacy_allowlist = root / "tools" / "known-broken-specs.txt"
    legacy_allowlist.parent.mkdir(parents=True)
    legacy_allowlist.write_text(program.relative_to(root).as_posix() + "\n")
    patch_non_git_build(monkeypatch)

    def fail_compose(*args, **kwargs):
        raise RuntimeError("does not compile")

    monkeypatch.setattr(artifacts, "compose_spec", fail_compose)

    assert artifacts.main(["--root", str(root)]) == 1
    captured = capsys.readouterr()
    assert "FAIL programs/us/demo/fy-2026.yaml: does not compile" in captured.err
    assert "1 spec(s) failed to build" in captured.err
    assert not (root / "dist").exists()


def test_main_reaudits_composer_imports_before_engine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "rulespec-us"
    write_module(root / "us" / "policies" / "safe.yaml")
    write_module(root / "us" / "policies" / "waived.yaml")
    write_program(root, scope_path="policies/safe")
    patch_non_git_build(monkeypatch, {"us/policies/waived.yaml"})

    def fake_compose(source_root, corpus_root, build, out_path):
        write_yaml(
            out_path,
            {
                "format": "rulespec/v1",
                "module": {"kind": "composition"},
                "imports": ["us:policies/waived"],
            },
        )

    monkeypatch.setattr(artifacts, "compose_spec", fake_compose)
    monkeypatch.setattr(
        artifacts,
        "engine_compile",
        lambda *args, **kwargs: pytest.fail("waived composition reached the engine"),
    )

    assert artifacts.main(["--root", str(root)]) == 0
    manifest = json.loads((root / "dist/manifest.json").read_text())
    assert manifest["programs"] == []
    assert manifest["excluded_programs"][0]["waived_modules"] == [
        "us/policies/waived.yaml"
    ]


def test_main_stamps_exact_toolchain_refs_in_artifact_and_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "rulespec-us"
    write_module(root / "us" / "policies" / "safe.yaml")
    write_program(root, scope_path="policies/safe")
    patch_non_git_build(monkeypatch)

    def fake_compose(source_root, corpus_root, build, out_path):
        write_yaml(
            out_path,
            {
                "format": "rulespec/v1",
                "module": {"kind": "composition"},
                "imports": ["us:policies/safe"],
            },
        )

    def fake_engine(corpus_root, module, artifact, engine_bin, *, cwd):
        artifact.write_text(
            json.dumps(
                {
                    "program": {
                        "derived": [],
                        "parameters": [],
                        "relations": [],
                    }
                }
            )
        )
        return "test-engine"

    monkeypatch.setattr(artifacts, "compose_spec", fake_compose)
    monkeypatch.setattr(artifacts, "engine_compile", fake_engine)

    assert artifacts.main(["--root", str(root)]) == 0

    manifest = json.loads((root / "dist/manifest.json").read_text())
    compiled = json.loads((root / "dist/us-demo.compiled.json").read_text())
    assert manifest["toolchain"] == TEST_TOOLCHAIN
    provenance = compiled["metadata"]["provenance"]
    assert provenance["toolchain"] == TEST_TOOLCHAIN
    assert "composer_version" not in manifest
    assert "composer_version" not in provenance


def test_check_mode_leaves_existing_dist_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "rulespec-us"
    dist = root / "dist"
    dist.mkdir(parents=True)
    sentinel = dist / "sentinel"
    sentinel.write_text("keep")
    patch_non_git_build(monkeypatch)

    assert artifacts.main(["--root", str(root), "--dist", str(dist), "--check"]) == 0
    assert sentinel.read_text() == "keep"
    assert sorted(path.name for path in dist.iterdir()) == ["sentinel"]


def test_check_mode_does_not_create_missing_dist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "rulespec-us"
    root.mkdir()
    dist = root / "dist"
    patch_non_git_build(monkeypatch)

    assert artifacts.main(["--root", str(root), "--check"]) == 0
    assert not dist.exists()


def test_dist_replacement_refuses_repository_source_directories(tmp_path: Path) -> None:
    root = tmp_path / "rulespec-us"
    staged = tmp_path / "staged"
    staged.mkdir()
    source_directory = root / "us"
    source_directory.mkdir(parents=True)

    with pytest.raises(artifacts.BuildSafetyError, match="repository dist"):
        artifacts.replace_dist(staged, source_directory, root)


def test_dist_replacement_refuses_external_directory(tmp_path: Path) -> None:
    root = tmp_path / "rulespec-us"
    root.mkdir()
    staged = tmp_path / "staged"
    staged.mkdir()
    external = tmp_path / "sibling-repository"
    external.mkdir()
    sentinel = external / "keep.txt"
    sentinel.write_text("owned elsewhere")

    with pytest.raises(artifacts.BuildSafetyError, match="repository dist"):
        artifacts.replace_dist(staged, external, root)

    assert sentinel.read_text() == "owned elsewhere"
