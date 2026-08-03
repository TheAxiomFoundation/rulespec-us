from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "tools/build_program_artifacts.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_program_artifacts", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_engine_compile_uses_explicit_root_and_composed_entrypoint(
    monkeypatch, tmp_path: Path
) -> None:
    builder = load_builder()
    root = tmp_path / "rulespec-us"
    module = tmp_path / "program.rulespec.yaml"
    artifact = tmp_path / "program.compiled.json"
    observed: dict[str, object] = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            command, 0, stdout="engine_version: test-engine\n", stderr=""
        )

    monkeypatch.setattr(builder.subprocess, "run", fake_run)

    version = builder.engine_compile(root, module, artifact, "/bin/engine")

    assert version == "test-engine"
    assert observed == {
        "command": [
            "/bin/engine",
            "compile-composed",
            "--program",
            str(module),
            "--rulespec-root",
            str(root),
            "--output",
            str(artifact),
        ],
        "kwargs": {"capture_output": True, "text": True},
    }
