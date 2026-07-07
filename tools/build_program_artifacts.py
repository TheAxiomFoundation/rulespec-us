#!/usr/bin/env python3
"""Build compiled program artifacts from every spec in programs/.

For each programs/<jurisdiction>/<program>/<period>.yaml spec this composes the
program (axiom-compose), compiles it to an executable artifact
(axiom-rules-engine compile), stamps provenance into the artifact metadata, and
writes a manifest describing everything that was built.

The output is deterministic for a given (corpus SHA, composer version, engine
version): no timestamps or randomness enter the artifacts or the manifest, so
rebuilding the same commit yields byte-identical outputs.

Modes:
  --check      compile everything, write nothing; exit 1 if any spec outside
               tools/known-broken-specs.txt fails (and if an allowlisted spec
               unexpectedly succeeds, say so, so the allowlist shrinks).
  (default)    build dist/: composed modules, stamped artifacts, manifest.json.

Requirements: `axiom_compose` importable, AXIOM_RULES_ENGINE_BIN pointing at an
axiom-rules-engine binary, and this script running from (or given) the corpus
repo root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

MANIFEST_FORMAT_VERSION = 1


@dataclass
class SpecBuild:
    spec_path: Path  # relative to repo root
    jurisdiction: str
    program_id: str
    period: str
    outputs: list[str]
    artifact_name: str


def discover_specs(root: Path) -> list[SpecBuild]:
    builds: list[SpecBuild] = []
    for path in sorted((root / "programs").rglob("*.yaml")):
        if path.name.endswith(".test.yaml"):
            continue
        spec = yaml.safe_load(path.read_text())
        if not isinstance(spec, dict) or "program" not in spec:
            continue
        program_field = str(spec["program"])
        segments = [s for s in program_field.split("/") if s]
        jurisdiction = segments[0]
        program_id = segments[-1]
        period = str(spec.get("period", ""))
        outputs = [str(o) for o in spec.get("outputs", [])]
        builds.append(
            SpecBuild(
                spec_path=path.relative_to(root),
                jurisdiction=jurisdiction,
                program_id=program_id,
                period=period,
                outputs=outputs,
                artifact_name=f"{jurisdiction}-{program_id}",
            )
        )
    names = [b.artifact_name for b in builds]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        raise SystemExit(f"artifact name collision: {sorted(dupes)}")
    return builds


def git_output(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def corpus_provenance(root: Path) -> dict:
    sha = git_output(root, "rev-parse", "HEAD")
    # Untracked files (e.g. a previous dist/) don't affect what compiles;
    # only tracked modifications make the corpus state unreproducible.
    dirty = bool(git_output(root, "status", "--porcelain", "--untracked-files=no"))
    origin = ""
    try:
        origin = git_output(root, "remote", "get-url", "origin")
    except subprocess.CalledProcessError:
        pass
    repo = re.sub(r"\.git$", "", origin.rsplit("/", 1)[-1]) if origin else root.name
    return {"repo": repo, "sha": sha, "dirty": dirty}


def composer_version() -> str:
    try:
        from importlib.metadata import version

        return version("axiom-compose")
    except Exception:
        return "unknown"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compose_spec(root: Path, build: SpecBuild, out_path: Path) -> None:
    from axiom_compose import compose, load_corpus_from_roots, load_spec

    spec = load_spec(root / build.spec_path)
    corpus = load_corpus_from_roots([root])
    program = compose(spec, corpus)
    out_path.write_bytes(program.source)


def engine_compile(root: Path, module: Path, artifact: Path, engine_bin: str) -> str:
    """Run the engine compiler; returns its reported engine_version."""
    env = dict(os.environ, AXIOM_RULESPEC_REPO_ROOTS=str(root))
    result = subprocess.run(
        [engine_bin, "compile", "--program", str(module), "--output", str(artifact)],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    match = re.search(r"^engine_version:\s*(\S+)", result.stdout, re.M)
    return match.group(1) if match else "unknown"


def stamp_provenance(artifact: Path, provenance: dict) -> None:
    data = json.loads(artifact.read_text())
    data.setdefault("metadata", {})["provenance"] = provenance
    artifact.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")


def load_allowlist(root: Path) -> set[str]:
    path = root / "tools" / "known-broken-specs.txt"
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--dist", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    engine_bin = os.environ.get("AXIOM_RULES_ENGINE_BIN")
    if not engine_bin:
        print("AXIOM_RULES_ENGINE_BIN is not set", file=sys.stderr)
        return 2

    dist = (args.dist or root / "dist").resolve()
    dist.mkdir(parents=True, exist_ok=True)

    builds = discover_specs(root)
    allowlist = load_allowlist(root)
    corpus = corpus_provenance(root)
    composer = composer_version()

    manifest_programs = []
    unexpected_failures: list[str] = []
    unexpected_successes: list[str] = []
    engine_version = "unknown"

    # Compose and compile in a neutral temp directory OUTSIDE the repo: the
    # engine discovers additional rulespec repos by walking up from the module
    # path, so building inside the checkout lets stray sibling checkouts leak
    # modules into the artifact (observed: a legacy per-state repo resolving an
    # import the pinned corpus cannot). Neutral cwd keeps local builds
    # byte-identical to CI.
    workdir = Path(tempfile.mkdtemp(prefix="program-artifacts-"))

    for build in builds:
        spec_rel = str(build.spec_path)
        module_path = workdir / f"{build.artifact_name}.rulespec.yaml"
        artifact_path = workdir / f"{build.artifact_name}.compiled.json"
        try:
            compose_spec(root, build, module_path)
            engine_version = engine_compile(root, module_path, artifact_path, engine_bin)
        except Exception as error:
            message = str(error).splitlines()[0][:200]
            if spec_rel in allowlist:
                print(f"KNOWN-BROKEN {spec_rel}: {message}")
            else:
                print(f"FAIL {spec_rel}: {message}", file=sys.stderr)
                unexpected_failures.append(spec_rel)
            continue

        if spec_rel in allowlist:
            unexpected_successes.append(spec_rel)

        provenance = {
            "corpus": corpus,
            "spec_path": spec_rel,
            "spec_sha256": sha256_file(root / build.spec_path),
            "composer_version": composer,
            "engine_version": engine_version,
        }
        stamp_provenance(artifact_path, provenance)

        shutil.copy2(module_path, dist / module_path.name)
        artifact_path = Path(shutil.copy2(artifact_path, dist / artifact_path.name))

        program = json.loads(artifact_path.read_text())["program"]
        manifest_programs.append(
            {
                "jurisdiction": build.jurisdiction,
                "program_id": build.program_id,
                "period": build.period,
                "spec_path": spec_rel,
                "spec_sha256": provenance["spec_sha256"],
                "outputs": build.outputs,
                "artifact": artifact_path.name,
                "artifact_sha256": sha256_file(artifact_path),
                "counts": {
                    "derived": len(program.get("derived", [])),
                    "parameters": len(program.get("parameters", [])),
                    "relations": len(program.get("relations", [])),
                },
            }
        )
        print(
            f"OK   {spec_rel} -> {artifact_path.name} "
            f"({manifest_programs[-1]['counts']['derived']}d)"
        )

    manifest = {
        "format_version": MANIFEST_FORMAT_VERSION,
        "corpus": corpus,
        "composer_version": composer,
        "engine_version": engine_version,
        "programs": manifest_programs,
    }
    (dist / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    if unexpected_successes:
        print(
            "NOTE: allowlisted specs now compile — remove from known-broken-specs.txt: "
            + ", ".join(unexpected_successes)
        )
    if unexpected_failures:
        print(f"{len(unexpected_failures)} spec(s) failed to build", file=sys.stderr)
        return 1
    print(f"built {len(manifest_programs)}/{len(builds)} programs -> {dist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
