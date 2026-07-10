#!/usr/bin/env python3
"""Build compiled program artifacts from every spec in programs/.

For each programs/<jurisdiction>/<program>/<period>.yaml spec this composes the
program (axiom-compose), compiles it to an executable artifact
(axiom-rules-engine compile), stamps provenance into the artifact metadata, and
writes a manifest describing everything that was built.

The output contains no timestamps or deliberate randomness, and records the
exact corpus, composer, encoder, and engine commits. Artifact hashes capture
the actual output; byte identity is expected only under the same runner and
build environment, which this script does not make hermetic.

Modes:
  --check      audit and compile every non-excluded program, write nothing;
               exit 1 if any of those programs fails.
  (default)    build dist/: composed modules, stamped artifacts, manifest.json.

Requirements: `axiom_compose` importable, AXIOM_RULES_ENGINE_BIN pointing at an
axiom-rules-engine binary, exact 40-character AXIOM_COMPOSE_REF,
AXIOM_ENCODE_REF, and AXIOM_RULES_ENGINE_REF values, and this script running
from (or given) the corpus repo root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath

import yaml

MANIFEST_FORMAT_VERSION = 2
JURISDICTION_RE = re.compile(r"^us(?:-[a-z0-9]+)*$")
COMMIT_REF_RE = re.compile(r"^[0-9a-f]{40}$")
TOOLCHAIN_REF_ENV = {
    "axiom_compose_ref": "AXIOM_COMPOSE_REF",
    "axiom_encode_ref": "AXIOM_ENCODE_REF",
    "axiom_rules_engine_ref": "AXIOM_RULES_ENGINE_REF",
}


class BuildSafetyError(ValueError):
    """Raised when artifact isolation cannot be proved."""


@dataclass
class SpecBuild:
    spec_path: Path  # relative to repo root
    jurisdiction: str
    program_id: str
    period: str
    outputs: list[str]
    artifact_name: str


def load_toolchain_provenance(
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Load exact immutable tool refs that define the artifact build."""

    source = os.environ if environ is None else environ
    result: dict[str, str] = {}
    for manifest_key, environment_key in TOOLCHAIN_REF_ENV.items():
        value = source.get(environment_key, "")
        if not COMMIT_REF_RE.fullmatch(value):
            raise BuildSafetyError(
                f"{environment_key} must be exactly 40 lowercase hexadecimal characters"
            )
        result[manifest_key] = value
    return result


def _load_yaml(path: Path) -> object:
    try:
        return yaml.safe_load(path.read_text())
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise BuildSafetyError(f"cannot parse {path}: {error}") from error


def _validate_repo_module_path(root: Path, raw_path: object) -> str:
    if not isinstance(raw_path, str) or not raw_path:
        raise BuildSafetyError("validate_failures keys must be non-empty strings")
    if raw_path != raw_path.strip() or "\\" in raw_path:
        raise BuildSafetyError(f"unsafe validate_failures path: {raw_path!r}")
    pure = PurePosixPath(raw_path)
    if (
        pure.is_absolute()
        or pure.as_posix() != raw_path
        or any(part in {"", ".", ".."} for part in pure.parts)
        or len(pure.parts) < 2
        or not JURISDICTION_RE.fullmatch(pure.parts[0])
        or pure.suffix != ".yaml"
        or pure.name.endswith(".test.yaml")
    ):
        raise BuildSafetyError(f"unsafe validate_failures path: {raw_path!r}")

    module = root.joinpath(*pure.parts)
    try:
        metadata = module.lstat()
    except OSError as error:
        raise BuildSafetyError(
            f"validate_failures path does not exist: {raw_path}"
        ) from error
    if not stat.S_ISREG(metadata.st_mode) or module.is_symlink():
        raise BuildSafetyError(
            f"validate_failures path is not a regular file: {raw_path}"
        )
    resolved_root = root.resolve()
    resolved_module = module.resolve()
    if resolved_root not in resolved_module.parents:
        raise BuildSafetyError(f"validate_failures path escapes the repo: {raw_path}")
    return raw_path


def load_waived_module_paths(root: Path, *, today: date | None = None) -> set[str]:
    """Extract active paths from the canonical validation-waiver model."""

    try:
        from axiom_encode.validation_waivers import load_validation_waivers
    except ImportError as error:
        raise BuildSafetyError(
            "axiom-encode with validation_waivers support is required"
        ) from error

    try:
        waivers = load_validation_waivers(
            root / "known-validation-gaps.yaml",
            repo_root=root,
            today=today,
        )
        raw_active_paths = waivers.active_paths
    except Exception as error:
        raise BuildSafetyError(f"invalid validation waivers: {error}") from error
    if isinstance(raw_active_paths, str):
        raise BuildSafetyError("validation waiver active_paths must be a collection")
    try:
        return {
            _validate_repo_module_path(root, raw_path) for raw_path in raw_active_paths
        }
    except TypeError as error:
        raise BuildSafetyError(
            "validation waiver active_paths must be a collection"
        ) from error


def module_path_to_target(path: str) -> str:
    pure = PurePosixPath(path)
    relative = PurePosixPath(*pure.parts[1:]).with_suffix("")
    return f"{pure.parts[0]}:{relative.as_posix()}"


def normalize_module_target(target: str, *, importer: str | None = None) -> str:
    """Mirror the engine's canonical and relative import normalization."""

    if not isinstance(target, str):
        raise BuildSafetyError(f"RuleSpec import target must be a string: {target!r}")
    trimmed = target.strip().strip("\"'")
    without_fragment = trimmed.split("#", 1)[0].strip()
    if not without_fragment:
        raise BuildSafetyError(f"invalid RuleSpec import target: {target!r}")

    canonical_prefix, separator, canonical_path = without_fragment.partition(":")
    if separator and JURISDICTION_RE.fullmatch(canonical_prefix):
        prefix = canonical_prefix
        relative = canonical_path.strip().strip("/")
        segments: list[str] = []
    else:
        if importer is None or without_fragment.startswith("/"):
            raise BuildSafetyError(f"invalid RuleSpec import target: {target!r}")
        prefix, _, importer_path = normalize_module_target(importer).partition(":")
        segments = importer_path.split("/")[:-1]
        relative = without_fragment

    if relative.endswith(".yaml"):
        relative = relative[: -len(".yaml")]
    elif relative.endswith(".yml"):
        relative = relative[: -len(".yml")]
    for segment in relative.split("/"):
        if segment in {"", "."}:
            continue
        if segment == "..":
            if not segments:
                raise BuildSafetyError(f"invalid RuleSpec import target: {target!r}")
            segments.pop()
        else:
            segments.append(segment)
    if not segments:
        raise BuildSafetyError(f"invalid RuleSpec import target: {target!r}")
    return f"{prefix}:{'/'.join(segments)}"


class CorpusDependencyGraph:
    """Lazy import/extends graph using the engine's monorepo target layout."""

    def __init__(self, root: Path):
        self.root = root
        self._dependencies: dict[str, tuple[str, ...]] = {}

    def _path_for_target(self, target: str) -> Path:
        normalized = normalize_module_target(target)
        prefix, _, relative = normalized.partition(":")
        return self.root / prefix / f"{relative}.yaml"

    def dependencies(self, target: str) -> tuple[str, ...]:
        normalized = normalize_module_target(target)
        if normalized in self._dependencies:
            return self._dependencies[normalized]
        path = self._path_for_target(normalized)
        if not path.exists():
            # The engine is authoritative for unresolved imports. An absent
            # target remains outside this graph and fails the program build.
            self._dependencies[normalized] = ()
            return ()
        if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode):
            raise BuildSafetyError(f"RuleSpec module is not a regular file: {path}")
        payload = _load_yaml(path) or {}
        if not isinstance(payload, Mapping):
            raise BuildSafetyError(f"RuleSpec module root must be a mapping: {path}")

        raw_imports = payload.get("imports") or []
        if isinstance(raw_imports, str) or not isinstance(raw_imports, list):
            raise BuildSafetyError(f"RuleSpec imports must be a list: {path}")
        dependencies: list[str] = []
        raw_extends = payload.get("extends")
        if raw_extends is not None:
            if not isinstance(raw_extends, str):
                raise BuildSafetyError(f"RuleSpec extends must be a string: {path}")
            dependencies.append(
                normalize_module_target(raw_extends, importer=normalized)
            )
        for raw_import in raw_imports:
            dependencies.append(
                normalize_module_target(raw_import, importer=normalized)
            )
        result = tuple(dict.fromkeys(dependencies))
        self._dependencies[normalized] = result
        return result

    def closure(self, roots: list[str] | tuple[str, ...]) -> set[str]:
        seen: set[str] = set()
        stack = [normalize_module_target(target) for target in reversed(roots)]
        while stack:
            target = stack.pop()
            if target in seen:
                continue
            seen.add(target)
            stack.extend(reversed(self.dependencies(target)))
        return seen


def discover_specs(root: Path) -> list[SpecBuild]:
    programs_root = root / "programs"
    try:
        programs_metadata = programs_root.lstat()
    except FileNotFoundError:
        return []
    except OSError as error:
        raise BuildSafetyError(f"cannot inspect program directory: {error}") from error
    if programs_root.is_symlink() or not stat.S_ISDIR(programs_metadata.st_mode):
        raise BuildSafetyError(
            f"program directory is not a regular directory: {programs_root}"
        )

    paths: list[Path] = []
    for current, directories, filenames in os.walk(programs_root, followlinks=False):
        current_path = Path(current)
        directories.sort()
        for directory in directories:
            child = current_path / directory
            if child.is_symlink():
                raise BuildSafetyError(f"program directory is a symlink: {child}")
        for filename in sorted(filenames):
            if filename.endswith(".yaml") and not filename.endswith(".test.yaml"):
                paths.append(current_path / filename)

    builds: list[SpecBuild] = []
    for path in sorted(paths):
        try:
            metadata = path.lstat()
        except OSError as error:
            raise BuildSafetyError(
                f"cannot inspect program spec {path}: {error}"
            ) from error
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise BuildSafetyError(f"program spec is not a regular file: {path}")
        resolved_root = root.resolve()
        resolved_path = path.resolve()
        if resolved_root not in resolved_path.parents:
            raise BuildSafetyError(f"program spec escapes the repository: {path}")

        spec = _load_yaml(path)
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


def declared_program_imports(root: Path, build: SpecBuild) -> tuple[str, ...]:
    payload = _load_yaml(root / build.spec_path) or {}
    if not isinstance(payload, Mapping):
        raise BuildSafetyError(
            f"program spec root must be a mapping: {build.spec_path}"
        )
    program = payload.get("program")
    if not isinstance(program, str) or not program.strip():
        raise BuildSafetyError(f"program spec has no valid program: {build.spec_path}")
    scope = payload.get("scope") or {}
    if not isinstance(scope, Mapping):
        raise BuildSafetyError(
            f"program spec scope must be a mapping: {build.spec_path}"
        )

    roots: list[str] = []
    for raw_scope, raw_paths in scope.items():
        if raw_scope in {"include", "exclude", "jurisdictions"}:
            continue
        if not isinstance(raw_scope, str):
            raise BuildSafetyError(
                f"program spec scope key must be a string: {build.spec_path}"
            )
        if isinstance(raw_paths, str) or not isinstance(raw_paths, list):
            raise BuildSafetyError(
                f"program spec scope.{raw_scope} must be a list: {build.spec_path}"
            )
        if raw_scope == "federal":
            prefix = "us"
        elif raw_scope == "state":
            prefix = program.split("/", 1)[0]
        else:
            prefix = raw_scope.strip()
        if not JURISDICTION_RE.fullmatch(prefix):
            raise BuildSafetyError(
                f"program spec has invalid scope prefix {prefix!r}: {build.spec_path}"
            )
        for raw_path in raw_paths:
            if not isinstance(raw_path, str):
                raise BuildSafetyError(
                    f"program spec scope paths must be strings: {build.spec_path}"
                )
            target = raw_path if ":" in raw_path else f"{prefix}:{raw_path}"
            roots.append(normalize_module_target(target))
    return tuple(dict.fromkeys(roots))


def composed_program_imports(module_path: Path) -> tuple[str, ...]:
    payload = _load_yaml(module_path) or {}
    if not isinstance(payload, Mapping):
        raise BuildSafetyError(
            f"composed program root must be a mapping: {module_path}"
        )
    raw_imports = payload.get("imports") or []
    if isinstance(raw_imports, str) or not isinstance(raw_imports, list):
        raise BuildSafetyError(
            f"composed program imports must be a list: {module_path}"
        )
    roots = [normalize_module_target(item) for item in raw_imports]
    raw_extends = payload.get("extends")
    if raw_extends is not None:
        if not isinstance(raw_extends, str):
            raise BuildSafetyError(
                f"composed program extends must be a string: {module_path}"
            )
        roots.insert(0, normalize_module_target(raw_extends))
    return tuple(dict.fromkeys(roots))


def waived_dependencies(
    graph: CorpusDependencyGraph,
    roots: list[str] | tuple[str, ...],
    waived_by_target: Mapping[str, str],
) -> list[str]:
    return sorted(
        waived_by_target[target]
        for target in graph.closure(roots)
        if target in waived_by_target
    )


def create_non_waived_corpus_mirror(
    root: Path, destination: Path, waived_paths: set[str]
) -> int:
    """Copy RuleSpec modules into an isolated country-monorepo mirror."""

    if destination.name != "rulespec-us":
        raise BuildSafetyError("isolated corpus mirror must be named rulespec-us")
    destination.mkdir(parents=True)
    copied = 0
    excluded: set[str] = set()
    for jurisdiction in sorted(root.iterdir()):
        if not JURISDICTION_RE.fullmatch(jurisdiction.name):
            continue
        if jurisdiction.is_symlink() or not jurisdiction.is_dir():
            raise BuildSafetyError(
                f"jurisdiction root is not a regular directory: {jurisdiction}"
            )
        for current, directories, filenames in os.walk(jurisdiction, followlinks=False):
            current_path = Path(current)
            for directory in directories:
                child = current_path / directory
                if child.is_symlink():
                    raise BuildSafetyError(f"RuleSpec directory is a symlink: {child}")
            for filename in sorted(filenames):
                if not filename.endswith(".yaml") or filename.endswith(".test.yaml"):
                    continue
                source = current_path / filename
                relative = source.relative_to(root).as_posix()
                if source.is_symlink() or not stat.S_ISREG(source.lstat().st_mode):
                    raise BuildSafetyError(
                        f"RuleSpec module is not a regular file: {relative}"
                    )
                if relative in waived_paths:
                    excluded.add(relative)
                    continue
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                copied += 1

    missing = sorted(waived_paths - excluded)
    if missing:
        raise BuildSafetyError(
            "active validate-failure waivers were not excluded from the corpus "
            f"mirror: {missing}"
        )
    for relative in waived_paths:
        if (destination / relative).exists():
            raise BuildSafetyError(
                f"waived module survived corpus isolation: {relative}"
            )
    return copied


def artifact_origin_targets(artifact: Path) -> set[str]:
    try:
        payload = json.loads(artifact.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BuildSafetyError(
            f"cannot parse compiled artifact {artifact}: {error}"
        ) from error
    program = payload.get("program") if isinstance(payload, Mapping) else None
    if not isinstance(program, Mapping):
        raise BuildSafetyError(f"compiled artifact has no program mapping: {artifact}")

    targets: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, Mapping):
            rule_id = value.get("id")
            if isinstance(rule_id, str) and "#" in rule_id:
                raw_target = rule_id.split("#", 1)[0]
                try:
                    targets.add(normalize_module_target(raw_target))
                except BuildSafetyError:
                    # The engine may use non-module IDs for synthetic entries;
                    # only canonical RuleSpec origins participate in this audit.
                    pass
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(program)
    return targets


def assert_artifact_has_no_waived_origins(
    artifact: Path, waived_by_target: Mapping[str, str]
) -> None:
    hits = sorted(
        waived_by_target[target]
        for target in artifact_origin_targets(artifact)
        if target in waived_by_target
    )
    if hits:
        raise BuildSafetyError(
            f"compiled artifact contains waived module origins: {hits}"
        )


def replace_dist(staged_dist: Path, dist: Path, root: Path) -> None:
    """Install exactly the successful staged outputs, removing stale files."""

    if dist != root / "dist":
        raise BuildSafetyError(
            f"refusing to replace anything other than the repository dist/: {dist}"
        )
    if dist.is_symlink():
        raise BuildSafetyError(f"refusing symlink output directory: {dist}")
    if dist.exists() and not dist.is_dir():
        raise BuildSafetyError(f"output path is not a directory: {dist}")
    dist.parent.mkdir(parents=True, exist_ok=True)
    replacement = Path(
        tempfile.mkdtemp(prefix=f".{dist.name}-replacement-", dir=dist.parent)
    )
    try:
        shutil.copytree(staged_dist, replacement, dirs_exist_ok=True)
        if dist.exists():
            shutil.rmtree(dist)
        replacement.replace(dist)
    finally:
        if replacement.exists():
            shutil.rmtree(replacement)


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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compose_spec(
    source_root: Path, corpus_root: Path, build: SpecBuild, out_path: Path
) -> None:
    from axiom_compose import compose, load_corpus_from_roots, load_spec

    spec = load_spec(source_root / build.spec_path)
    corpus = load_corpus_from_roots([corpus_root])
    program = compose(spec, corpus)
    out_path.write_bytes(program.source)


def engine_compile(
    corpus_root: Path,
    module: Path,
    artifact: Path,
    engine_bin: str,
    *,
    cwd: Path,
) -> str:
    """Run the engine compiler; returns its reported engine_version."""
    env = dict(os.environ, AXIOM_RULESPEC_REPO_ROOTS=str(corpus_root))
    result = subprocess.run(
        [
            engine_bin,
            "compile",
            "--exclusive-rulespec-roots",
            "--program",
            str(module),
            "--output",
            str(artifact),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    match = re.search(r"^engine_version:\s*(\S+)", result.stdout, re.M)
    return match.group(1) if match else "unknown"


def stamp_provenance(artifact: Path, provenance: dict) -> None:
    data = json.loads(artifact.read_text())
    data.setdefault("metadata", {})["provenance"] = provenance
    artifact.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--dist", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    engine_bin = os.environ.get("AXIOM_RULES_ENGINE_BIN")
    if not engine_bin:
        print("AXIOM_RULES_ENGINE_BIN is not set", file=sys.stderr)
        return 2

    raw_dist = args.dist or root / "dist"
    if not raw_dist.is_absolute():
        raw_dist = root / raw_dist
    dist = Path(os.path.abspath(raw_dist))

    try:
        builds = discover_specs(root)
        waived_paths = load_waived_module_paths(root)
        waived_by_target = {
            module_path_to_target(path): path for path in sorted(waived_paths)
        }
        toolchain = load_toolchain_provenance()
        corpus = corpus_provenance(root)
    except (BuildSafetyError, OSError, subprocess.CalledProcessError) as error:
        print(f"artifact build configuration is unsafe: {error}", file=sys.stderr)
        return 2

    manifest_programs = []
    excluded_programs: list[dict[str, object]] = []
    build_failures: list[str] = []
    engine_version = "unknown"

    # Compose and compile in a neutral temp directory OUTSIDE the repo. The
    # engine receives only a regular-file mirror with active waivers removed;
    # even if the Python dependency audit misses an edge, the engine cannot
    # resolve that module from the original checkout or an ambient sibling.
    with tempfile.TemporaryDirectory(prefix="program-artifacts-") as temporary:
        workdir = Path(temporary)
        corpus_root = workdir / "rulespec-us"
        staged_dist = workdir / "dist"
        staged_dist.mkdir()
        try:
            copied_modules = create_non_waived_corpus_mirror(
                root, corpus_root, waived_paths
            )
        except BuildSafetyError as error:
            print(f"artifact corpus isolation failed: {error}", file=sys.stderr)
            return 2
        print(
            f"isolated {copied_modules} non-waived modules; "
            f"excluded {len(waived_paths)} active waivers"
        )
        graph = CorpusDependencyGraph(root)

        for build in builds:
            spec_rel = build.spec_path.as_posix()
            module_path = workdir / f"{build.artifact_name}.rulespec.yaml"
            artifact_path = workdir / f"{build.artifact_name}.compiled.json"
            try:
                hits = waived_dependencies(
                    graph,
                    declared_program_imports(root, build),
                    waived_by_target,
                )
                if hits:
                    excluded_programs.append(
                        {
                            "spec_path": spec_rel,
                            "reason": "active_validate_failure_waiver",
                            "waived_modules": hits,
                        }
                    )
                    print(
                        f"EXCLUDED {spec_rel}: {len(hits)} active waived "
                        "module(s) in dependency closure"
                    )
                    continue

                compose_spec(root, corpus_root, build, module_path)
                # Re-audit what the composer actually emitted. This catches
                # future composer behavior that adds roots beyond the declared
                # program scope before the engine sees the module.
                composed_hits = waived_dependencies(
                    graph,
                    composed_program_imports(module_path),
                    waived_by_target,
                )
                if composed_hits:
                    excluded_programs.append(
                        {
                            "spec_path": spec_rel,
                            "reason": "active_validate_failure_waiver",
                            "waived_modules": composed_hits,
                        }
                    )
                    print(
                        f"EXCLUDED {spec_rel}: {len(composed_hits)} active waived "
                        "module(s) in composed dependency closure"
                    )
                    module_path.unlink(missing_ok=True)
                    continue

                engine_version = engine_compile(
                    corpus_root,
                    module_path,
                    artifact_path,
                    engine_bin,
                    cwd=workdir,
                )
                assert_artifact_has_no_waived_origins(artifact_path, waived_by_target)
            except Exception as error:
                message = str(error).splitlines()[0][:200]
                print(f"FAIL {spec_rel}: {message}", file=sys.stderr)
                build_failures.append(spec_rel)
                continue

            provenance = {
                "corpus": corpus,
                "spec_path": spec_rel,
                "spec_sha256": sha256_file(root / build.spec_path),
                "engine_version": engine_version,
                "toolchain": toolchain,
            }
            stamp_provenance(artifact_path, provenance)

            shutil.copy2(module_path, staged_dist / module_path.name)
            staged_artifact = Path(
                shutil.copy2(artifact_path, staged_dist / artifact_path.name)
            )

            program = json.loads(staged_artifact.read_text())["program"]
            manifest_programs.append(
                {
                    "jurisdiction": build.jurisdiction,
                    "program_id": build.program_id,
                    "period": build.period,
                    "spec_path": spec_rel,
                    "spec_sha256": provenance["spec_sha256"],
                    "outputs": build.outputs,
                    "artifact": staged_artifact.name,
                    "artifact_sha256": sha256_file(staged_artifact),
                    "counts": {
                        "derived": len(program.get("derived", [])),
                        "parameters": len(program.get("parameters", [])),
                        "relations": len(program.get("relations", [])),
                    },
                }
            )
            print(
                f"OK   {spec_rel} -> {staged_artifact.name} "
                f"({manifest_programs[-1]['counts']['derived']}d)"
            )

        manifest = {
            "format_version": MANIFEST_FORMAT_VERSION,
            "corpus": corpus,
            "engine_version": engine_version,
            "toolchain": toolchain,
            "programs": manifest_programs,
            "excluded_programs": sorted(
                excluded_programs, key=lambda item: str(item["spec_path"])
            ),
        }
        (staged_dist / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )

        if build_failures:
            print(f"{len(build_failures)} spec(s) failed to build", file=sys.stderr)
            return 1
        if args.check:
            print(
                f"checked {len(manifest_programs)}/{len(builds)} programs; "
                f"excluded {len(excluded_programs)}; wrote nothing"
            )
            return 0
        try:
            replace_dist(staged_dist, dist, root)
        except (BuildSafetyError, OSError) as error:
            print(f"cannot install artifact outputs: {error}", file=sys.stderr)
            return 2

    print(
        f"built {len(manifest_programs)}/{len(builds)} programs; "
        f"excluded {len(excluded_programs)} -> {dist}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
