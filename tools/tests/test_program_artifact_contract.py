"""Producer contract tests using composed JSON and mocked compiler artifacts.

These fixtures contain no hand-authored atomic RuleSpec modules. Actual corpus
semantics are checked separately against artifacts built by the real compilers.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

from hypothesis import HealthCheck, given, settings, strategies as st
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_program_artifacts as bpa  # noqa: E402


ENGINE_SHA = "363c6a6c56f7ad130996b63f7a09cfd4c3d9b021"
CAPABILITIES = {
    "engine_version": "0.2.2",
    "artifact_format_version": 2,
    "capabilities": ["relation_entity_typing", "related_min_max_only"],
}


@pytest.mark.parametrize("explicit_roots", [False, True])
def test_compile_composed_uses_absolute_explicit_roots_and_no_legacy_env(
    tmp_path, monkeypatch, explicit_roots
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AXIOM_RULESPEC_REPO_ROOTS", "/unrelated/rulespec-us")
    monkeypatch.setenv("AXIOM_RULESPEC_REPO_ROOTS_EXCLUSIVE", "1")
    monkeypatch.setenv("KEEP_COMPILER_SETTING", "preserved")
    root = Path("rulespec-us")
    roots = [root, Path("rulespec-nz")] if explicit_roots else [root]
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, "engine_version: 0.2.2\n", "")

    monkeypatch.setattr(bpa.subprocess, "run", run)
    options = {"rulespec_roots": roots} if explicit_roots else {}
    for _ in range(2):
        assert bpa.engine_compile(
            root, Path("composed.json"), Path("compiled.json"), "test-engine", **options
        ) == "0.2.2"

    assert calls[0] == calls[1], "identical inputs must produce identical compiler calls"
    argv, kwargs = calls[0]
    assert argv[:2] == ["test-engine", "compile-composed"]
    assert argv[argv.index("--program") + 1] == str((tmp_path / "composed.json").resolve())
    assert argv[argv.index("--output") + 1] == str((tmp_path / "compiled.json").resolve())
    supplied_roots = [argv[i + 1] for i, value in enumerate(argv) if value == "--rulespec-root"]
    assert supplied_roots == [str(path.resolve()) for path in roots]
    assert "AXIOM_RULESPEC_REPO_ROOTS" not in kwargs["env"]
    assert "AXIOM_RULESPEC_REPO_ROOTS_EXCLUSIVE" not in kwargs["env"]
    assert kwargs["env"]["KEEP_COMPILER_SETTING"] == "preserved"


def test_compile_failure_retains_the_full_engine_diagnostic(tmp_path, monkeypatch):
    diagnostic = "us:statutes/example: invalid relation\n  rule: benefit\n  slot: Household\n"

    def run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 1, "", diagnostic)

    monkeypatch.setattr(bpa.subprocess, "run", run)
    with pytest.raises(RuntimeError) as error:
        bpa.engine_compile(tmp_path / "rulespec-us", tmp_path / "composed.json",
                           tmp_path / "compiled.json", "test-engine")
    assert str(error.value) == diagnostic.strip()


def _mock_build(monkeypatch, root: Path, *, names=("first", "second"), sha=ENGINE_SHA):
    root.mkdir(parents=True, exist_ok=True)
    (root / "us").mkdir(exist_ok=True)
    builds = []
    for name in names:
        relative = Path("programs/us") / name / "2026.yaml"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        # ProgramSpecs are declarative composer input, not atomic RuleSpecs.
        path.write_text(json.dumps({"program": f"us/{name}", "period": "2026", "outputs": [name]}))
        builds.append(bpa.SpecBuild(relative, "us", name, "2026", [name], f"us-{name}"))
    state = object()
    compositions = []
    compilations = []

    def compose(spec, corpus):
        assert corpus is state
        compositions.append(spec["program"])
        return SimpleNamespace(source=json.dumps({
            "format": "rulespec/v1", "module": {"kind": "composition"},
            "rules": [],
        }).encode())

    def compile_program(root, module, artifact, engine, rulespec_roots=None):
        assert json.loads(module.read_bytes())["module"]["kind"] == "composition"
        compilations.append(module.name)
        artifact.write_text(json.dumps({
            "artifact_format_version": 2,
            "engine_version": "0.2.2",
            "program": {"derived": [], "parameters": [], "relations": []},
        }))
        return "0.2.2"

    monkeypatch.setitem(sys.modules, "axiom_compose", SimpleNamespace(
        load_corpus_from_roots=lambda roots: state,
        load_spec=lambda path: json.loads(path.read_text()),
        compose=compose,
    ))
    monkeypatch.setenv("AXIOM_RULES_ENGINE_BIN", "test-engine")
    monkeypatch.setattr(bpa, "discover_specs", lambda root: builds)
    monkeypatch.setattr(bpa, "corpus_provenance", lambda root: {"sha": "c" * 40, "dirty": False})
    monkeypatch.setattr(bpa, "composer_version", lambda: "test-composer")
    monkeypatch.setattr(bpa, "validation_toolchain", lambda root: {
        "axiom_artifact_rules_engine_ref": sha,
        "axiom_rules_engine_ref": "b" * 40,
    })
    monkeypatch.setattr(bpa, "engine_build_sha", lambda engine: sha)
    monkeypatch.setattr(bpa, "engine_capabilities", lambda engine: dict(CAPABILITIES))
    monkeypatch.setattr(bpa, "engine_compile", compile_program)
    return builds, compositions, compilations


@pytest.mark.parametrize("sha", ["", "unknown", "a" * 39, "a" * 41, "A" * 40, "g" * 40])
def test_build_refuses_unknown_or_malformed_compiler_sha_before_composing(tmp_path, monkeypatch, sha):
    root = tmp_path / "rulespec-us"
    _, compositions, compilations = _mock_build(monkeypatch, root, sha=sha)
    monkeypatch.setattr(sys, "argv", ["build", "--root", str(root)])
    assert bpa.main() == 2
    assert compositions == []
    assert compilations == []
    assert not list((root / "dist").glob("*.compiled.json"))


@pytest.mark.parametrize("reported", [
    None,
    {"engine_version": "0.2.2", "artifact_format_version": 2, "capabilities": []},
    {"engine_version": "0.2.2", "artifact_format_version": 2,
     "capabilities": ["relation_entity_typing"]},
    {"engine_version": "0.2.2", "artifact_format_version": 2,
     "capabilities": ["related_min_max_only"]},
    {"engine_version": "0.2.2", "artifact_format_version": 1,
     "capabilities": CAPABILITIES["capabilities"]},
])
def test_build_refuses_an_engine_without_the_supported_contract(tmp_path, monkeypatch, reported):
    root = tmp_path / "rulespec-us"
    _, compositions, compilations = _mock_build(monkeypatch, root)
    monkeypatch.setattr(bpa, "engine_capabilities", lambda engine: reported)
    monkeypatch.setattr(sys, "argv", ["build", "--root", str(root)])
    assert bpa.main() == 2
    assert compositions == compilations == []


@settings(max_examples=12, deadline=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(sha=st.text(alphabet="0123456789abcdef", min_size=40, max_size=40),
       count=st.integers(min_value=1, max_value=5))
def test_every_emitted_artifact_records_the_exact_sha_and_manifest_hash(
    tmp_path, monkeypatch, sha, count
):
    # Isolate each generated build; pytest's basetemp is supplied outside the
    # worktree when this suite runs, and this fixture creates no git repository.
    with tempfile.TemporaryDirectory(dir=tmp_path) as scratch:
        root = Path(scratch) / "rulespec-us"
        names = tuple(f"program-{index}" for index in range(count))
        builds, compositions, compilations = _mock_build(monkeypatch, root, names=names, sha=sha)
        monkeypatch.setattr(sys, "argv", ["build", "--root", str(root)])
        assert bpa.main() == 0
        manifest = json.loads((root / "dist/manifest.json").read_text())
        assert manifest["engine"]["git_sha"] == sha
        assert len(manifest["programs"]) == len(builds) == len(compositions) == len(compilations)
        for program in manifest["programs"]:
            artifact = root / "dist" / program["artifact"]
            payload = json.loads(artifact.read_text())
            provenance = payload["metadata"]["provenance"]
            assert provenance["compat"]["built_by_engine"]["git_sha"] == sha
            assert program["compat"] == provenance["compat"]
            assert program["artifact_sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
            assert program["spec_sha256"] == hashlib.sha256((root / program["spec_path"]).read_bytes()).hexdigest()
            assert provenance["spec_sha256"] == program["spec_sha256"]


def test_validation_pin_does_not_trigger_an_artifact_compiler_warning(tmp_path, monkeypatch, capsys):
    root = tmp_path / "rulespec-us"
    _mock_build(monkeypatch, root)
    monkeypatch.setattr(sys, "argv", ["build", "--root", str(root)])
    assert bpa.main() == 0
    assert "WARN" not in capsys.readouterr().err


def test_artifact_pin_mismatch_reports_the_real_compiler(tmp_path, monkeypatch, capsys):
    root = tmp_path / "rulespec-us"
    _mock_build(monkeypatch, root)
    monkeypatch.setattr(bpa, "validation_toolchain", lambda root: {
        "axiom_artifact_rules_engine_ref": "a" * 40,
        "axiom_rules_engine_ref": ENGINE_SHA,
    })
    monkeypatch.setattr(sys, "argv", ["build", "--root", str(root)])
    assert bpa.main() == 0
    warning = capsys.readouterr().err
    assert "WARN" in warning
    assert "artifact" in warning.lower()
    manifest = json.loads((root / "dist/manifest.json").read_text())
    assert manifest["engine"]["git_sha"] == ENGINE_SHA


def test_check_compiles_every_program_without_creating_or_changing_dist(tmp_path, monkeypatch):
    root = tmp_path / "rulespec-us"
    builds, _, compilations = _mock_build(monkeypatch, root)
    dist = root / "existing-output"
    dist.mkdir()
    sentinel = dist / "manifest.json"
    sentinel.write_bytes(b"existing release bytes\n")
    monkeypatch.setattr(sys, "argv", ["build", "--root", str(root), "--dist", str(dist), "--check"])
    assert bpa.main() == 0
    assert len(compilations) == len(builds)
    assert list(dist.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"existing release bytes\n"

    absent = root / "absent-output"
    monkeypatch.setattr(sys, "argv", ["build", "--root", str(root), "--dist", str(absent), "--check"])
    assert bpa.main() == 0
    assert not absent.exists()


def test_checkpoint_preserves_every_full_error_and_appends_successes(tmp_path, monkeypatch):
    root = tmp_path / "rulespec-us"
    builds, _, _ = _mock_build(monkeypatch, root, names=("bad-compose", "bad-compile", "built"))
    compose_error = "composition has omitted eligibility rules\n" + "full diagnostic " * 30
    compile_error = "us:statutes/example: relation slot mismatch\n" + "full compiler diagnostic " * 30
    original_compose = bpa.compose_spec
    original_compile = bpa.engine_compile

    def compose(root, build, module, state):
        if build.program_id == "bad-compose":
            raise RuntimeError(compose_error)
        return original_compose(root, build, module, state)

    def compile_program(root, module, artifact, engine, rulespec_roots=None):
        if module.name.startswith("us-bad-compile."):
            raise RuntimeError(compile_error)
        return original_compile(root, module, artifact, engine, rulespec_roots)

    monkeypatch.setattr(bpa, "compose_spec", compose)
    monkeypatch.setattr(bpa, "engine_compile", compile_program)
    results = tmp_path / "evidence" / "results.jsonl"
    argv = ["build", "--root", str(root), "--results-jsonl", str(results)]
    monkeypatch.setattr(sys, "argv", argv)
    assert bpa.main() == 1
    records = [json.loads(line) for line in results.read_text().splitlines()]
    assert [record["spec_path"] for record in records] == [str(build.spec_path) for build in builds]
    assert records[0]["status"] == records[1]["status"] == "failed"
    assert records[0]["stage"] == "compose"
    assert records[0]["error"] == compose_error
    assert records[1]["stage"] == "compile"
    assert records[1]["error"] == compile_error
    assert records[2]["status"] == "built"
    assert all(record["engine_sha"] == ENGINE_SHA for record in records)
    artifact = root / "dist" / records[2]["artifact"]
    assert records[2]["artifact_sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()

    monkeypatch.setattr(sys, "argv", [*argv, "--spec", str(builds[2].spec_path)])
    assert bpa.main() == 0
    appended = [json.loads(line) for line in results.read_text().splitlines()]
    assert appended[:3] == records
    assert len(appended) == 4
    assert appended[-1]["spec_path"] == str(builds[2].spec_path)
    assert appended[-1]["status"] == "built"


@pytest.mark.parametrize("payload", [
    None,  # compiler claims success without creating its output
    "not valid JSON",
    json.dumps({"program": {}}),
    json.dumps({"artifact_format_version": 3, "program": {}}),
    json.dumps({"artifact_format_version": 2}),
    json.dumps({"artifact_format_version": 2, "program": {}, "metadata": None}),
])
def test_invalid_compiler_output_is_checkpointed_and_later_programs_build(
    tmp_path, monkeypatch, payload
):
    root = tmp_path / "rulespec-us"
    builds, _, _ = _mock_build(monkeypatch, root)
    original_compile = bpa.engine_compile

    def compile_program(root, module, artifact, engine, rulespec_roots=None):
        if module.name == "us-first.rulespec.yaml":
            if payload is not None:
                artifact.write_text(payload)
            return "0.2.2"
        return original_compile(root, module, artifact, engine, rulespec_roots)

    monkeypatch.setattr(bpa, "engine_compile", compile_program)
    results = tmp_path / "results.jsonl"
    monkeypatch.setattr(sys, "argv", ["build", "--root", str(root), "--results-jsonl", str(results)])
    assert bpa.main() == 1
    records = [json.loads(line) for line in results.read_text().splitlines()]
    assert len(records) == 2
    assert records[0]["spec_path"] == str(builds[0].spec_path)
    assert records[0]["stage"] == "validate"
    assert records[0]["status"] == "failed"
    assert records[0]["error"]
    assert records[1]["status"] == "built"
    assert not (root / "dist/us-first.compiled.json").exists()
    manifest = json.loads((root / "dist/manifest.json").read_text())
    assert [program["program_id"] for program in manifest["programs"]] == ["second"]


@pytest.mark.parametrize("failure_point", ["stamp", "copy", "hash"])
def test_output_failure_is_checkpointed_before_later_programs_continue(
    tmp_path, monkeypatch, failure_point
):
    root = tmp_path / "rulespec-us"
    _mock_build(monkeypatch, root)
    diagnostic = f"cannot {failure_point} first artifact\ncomplete filesystem diagnostic"
    if failure_point == "copy":
        original = bpa.shutil.copy2

        def copy(source, destination):
            if Path(source).name.startswith("us-first."):
                raise OSError(diagnostic)
            return original(source, destination)

        monkeypatch.setattr(bpa.shutil, "copy2", copy)
    elif failure_point == "hash":
        original = bpa.sha256_file

        def hash_file(path):
            if path.name == "us-first.compiled.json":
                raise OSError(diagnostic)
            return original(path)

        monkeypatch.setattr(bpa, "sha256_file", hash_file)
    else:
        original = bpa.stamp_provenance

        def stamp(path, provenance):
            if path.name == "us-first.compiled.json":
                raise OSError(diagnostic)
            return original(path, provenance)

        monkeypatch.setattr(bpa, "stamp_provenance", stamp)
    results = tmp_path / "results.jsonl"
    monkeypatch.setattr(sys, "argv", ["build", "--root", str(root), "--results-jsonl", str(results)])
    assert bpa.main() == 1
    records = [json.loads(line) for line in results.read_text().splitlines()]
    assert records[0]["stage"] == "validate"
    assert records[0]["error"] == diagnostic
    assert records[1]["status"] == "built"


def test_empty_exception_message_does_not_abort_remaining_programs(tmp_path, monkeypatch, capsys):
    root = tmp_path / "rulespec-us"
    _mock_build(monkeypatch, root)
    original = bpa.compose_spec

    def compose(root, build, module, state):
        if build.program_id == "first":
            raise RuntimeError()
        return original(root, build, module, state)

    monkeypatch.setattr(bpa, "compose_spec", compose)
    results = tmp_path / "results.jsonl"
    monkeypatch.setattr(sys, "argv", ["build", "--root", str(root), "--results-jsonl", str(results)])
    assert bpa.main() == 1
    records = [json.loads(line) for line in results.read_text().splitlines()]
    assert records[0]["error"] == "RuntimeError"
    assert records[1]["status"] == "built"
    assert "RuntimeError" in capsys.readouterr().err


def _git(path: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(path), "-c", "init.defaultBranch=main", "-c", "core.hooksPath=/dev/null",
         "-c", "commit.gpgsign=false", "-c", "user.name=fixture", "-c", "user.email=fixture@example.org",
         *args], check=True, capture_output=True, text=True,
    ).stdout.strip()


def _checkout(path: Path) -> str:
    path.mkdir(parents=True, exist_ok=True)
    (path / "README.md").write_text(f"{path.name}\n")
    _git(path, "init", "-q")
    _git(path, "add", "-A")
    _git(path, "commit", "-qm", "fixture")
    return _git(path, "rev-parse", "HEAD")


def _staged_build(tmp_path, monkeypatch, layout):
    """Mocked composer/compiler, real git identities for --root and every staged root."""
    root = tmp_path / "primary" / "rulespec-us"
    _mock_build(monkeypatch, root)
    monkeypatch.setattr(bpa, "corpus_provenance", ORIGINAL_CORPUS_PROVENANCE)
    head = _checkout(root)
    staged = tmp_path / "staged" / "rulespec-us"
    loads = []
    state = sys.modules["axiom_compose"]
    original_load = state.load_corpus_from_roots
    state.load_corpus_from_roots = lambda roots: (loads.append(list(roots)), original_load(roots))[1]
    roots = layout(root, staged, tmp_path)
    argv = ["build", "--root", str(root)]
    for path in roots:
        argv.extend(["--rulespec-root", str(path)])
    monkeypatch.setattr(sys, "argv", argv)
    return root, head, loads


ORIGINAL_CORPUS_PROVENANCE = bpa.corpus_provenance


def test_a_staged_root_at_the_same_clean_commit_records_its_own_identity(tmp_path, monkeypatch):
    def layout(root, staged, tmp_path):
        subprocess.run(["git", "clone", "-q", str(root), str(staged)], check=True)
        nz = tmp_path / "staged" / "rulespec-nz"
        _checkout(nz)
        return [staged, nz]

    root, head, loads = _staged_build(tmp_path, monkeypatch, layout)
    assert bpa.main() == 0
    staged, nz = tmp_path / "staged" / "rulespec-us", tmp_path / "staged" / "rulespec-nz"
    assert loads == [[staged.absolute(), nz.absolute()]]
    expected = [
        {"name": "rulespec-us", "repo": "rulespec-us", "sha": head, "dirty": False},
        {"name": "rulespec-nz", "repo": "rulespec-nz", "sha": _git(nz, "rev-parse", "HEAD"), "dirty": False},
    ]
    manifest = json.loads((root / "dist/manifest.json").read_text())
    assert manifest["corpus"] == {"repo": "rulespec-us", "sha": head, "dirty": False}
    assert manifest["corpus_roots"] == expected
    for program in manifest["programs"]:
        provenance = json.loads((root / "dist" / program["artifact"]).read_text())["metadata"]["provenance"]
        assert provenance["corpus_roots"] == expected


def _advance(path: Path):
    (path / "README.md").write_text("changed\n")
    _git(path, "commit", "-qam", "later")


def _modify(path: Path):
    (path / "README.md").write_text("uncommitted\n")


REFUSALS = {
    "staged root at another commit": "same clean commit",
    "staged root dirty": "(dirty=True), but --root",
    "primary dirty": "(dirty=True); a staged root",
    "staged root is not a checkout": "must be a git checkout",
    "staged root is a subdirectory": "must be the top of its checkout",
    "primary repository absent": "no --rulespec-root is the rulespec-us corpus",
}


@pytest.mark.parametrize("case", sorted(REFUSALS))
def test_a_staged_root_that_cannot_carry_the_primary_identity_is_refused(tmp_path, monkeypatch, capsys, case):
    def layout(root, staged, tmp_path):
        if case == "staged root is not a checkout":
            staged.mkdir(parents=True)
            return [staged]
        if case == "primary repository absent":
            nz = tmp_path / "staged" / "rulespec-nz"
            _checkout(nz)
            return [nz]
        subprocess.run(["git", "clone", "-q", str(root), str(staged)], check=True)
        if case == "staged root at another commit":
            _advance(staged)
        elif case == "staged root dirty":
            _modify(staged)
        elif case == "primary dirty":
            _modify(root)
        elif case == "staged root is a subdirectory":
            return [staged / "programs"]
        return [staged]

    root, _, loads = _staged_build(tmp_path, monkeypatch, layout)
    assert bpa.main() == 2
    assert loads == [], "nothing may be composed under a wrong identity"
    assert not (root / "dist" / "manifest.json").exists()
    assert REFUSALS[case] in capsys.readouterr().err


def test_the_primary_root_passed_explicitly_keeps_the_primary_identity(tmp_path, monkeypatch):
    """CI passes --rulespec-root "$GITHUB_WORKSPACE", which is --root itself."""
    root, head, loads = _staged_build(tmp_path, monkeypatch, lambda root, staged, tmp_path: [root])
    assert bpa.main() == 0
    manifest = json.loads((root / "dist/manifest.json").read_text())
    assert manifest["corpus_roots"] == [{"name": "rulespec-us", **manifest["corpus"]}]
    assert manifest["corpus"]["sha"] == head
