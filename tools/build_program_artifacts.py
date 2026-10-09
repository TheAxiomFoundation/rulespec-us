#!/usr/bin/env python3
"""Build compiled program artifacts from every spec in programs/.

For each programs/<jurisdiction>/<program>/<period>.yaml spec this composes the
program (axiom-compose), compiles it to an executable artifact
(axiom-rules-engine compile), stamps provenance into the artifact metadata, and
writes a manifest describing everything that was built.

Identity and naming (rulespec-us#784):
  - A spec's legal identity is (jurisdiction, program_id, period): the first
    and last segments of its `program:` field, plus its `period:`, each with
    surrounding whitespace stripped. Several periods of one program build
    side by side.
  - An artifact is named after its spec path: the path under programs/,
    without `.yaml`, joined with "-". programs/us-az/snap/fy-2026.yaml builds
    us-az-snap-fy-2026.compiled.json. The name depends on nothing but the
    path, so it never changes when another spec is added or removed.
  - The manifest also records program_key ("<jurisdiction>-<program_id>", the
    period-free name every artifact had before #784) and period_label (the
    path segment that names the period, or null when the path names the
    program itself, as the tariff-schedule chapters do).
  - The build refuses a tree, before composing anything, in exactly three
    cases (plan_builds): two specs share an identity; two spec paths join to
    the same case-folded artifact name; or two different (jurisdiction,
    program_id) pairs join to the same case-folded program_key. On every tree
    it accepts, a program_key names one program and (program_key, period)
    names one artifact.

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
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePath

import yaml

MANIFEST_FORMAT_VERSION = 1
# The compiled-artifact format generation this builder is known to work with.
# It is an EXPECTATION, not the stamped value: what lands in the manifest is
# read back from the artifact the engine emitted (artifact_schema_of), and a
# mismatch fails the build. Bumping the engine across a format boundary without
# bumping this is therefore a hard error, not a silently mislabeled release.
EXPECTED_ARTIFACT_SCHEMA_VERSION = 2
# The fixed, tested lower bound an artifact requires of the engine. A floor, not
# the building engine's version — any engine >= this that supports the artifact
# schema can load it. Raise only when an emitted feature demands a newer engine.
MIN_ENGINE_VERSION = "0.1.0"


@dataclass
class SpecBuild:
    spec_path: Path  # relative to repo root
    jurisdiction: str
    program_id: str
    period: str
    outputs: list[str]
    artifact_name: str
    # The spec's `program:` field as written, surrounding whitespace stripped
    # (e.g. us/payroll/oasdi-wage-tax).
    program: str = ""
    # The path segment naming the legal period (fy-2026), or None when the
    # spec path names the program itself (us-tariff-schedule/ch01.yaml).
    period_label: str | None = None

    @property
    def program_key(self) -> str:
        """Period-free program identity; the artifact name before #784."""
        return f"{self.jurisdiction}-{self.program_id}"

    @property
    def identity(self) -> tuple[str, str, str]:
        """What two specs may not share: (jurisdiction, program_id, period)."""
        return (self.jurisdiction, self.program_id, self.period)


def artifact_name_for(spec_path: PurePath) -> str:
    """The artifact name for a spec at `spec_path` (relative to programs/).

    A pure function of the path: "-".join of its segments without `.yaml`.
    Nothing else about the spec or the tree enters it.
    """
    return "-".join(spec_path.with_suffix("").parts)


def period_label_for(spec_path: PurePath, program_segments: tuple[str, ...]) -> str | None:
    """The path segment naming the spec's legal period, if the path has one.

    programs/us-az/snap/fy-2026.yaml (program us-az/snap) -> "fy-2026".
    programs/us/us-tariff-schedule/ch01.yaml (program
    us/us-tariff-schedule/ch01) -> None: the stem is the chapter, which is part
    of the program, and the period lives only in `period:`.
    """
    parts = spec_path.with_suffix("").parts
    if parts == program_segments:
        return None
    return parts[-1]


class SpecIdentityError(SystemExit):
    """The spec tree cannot be built without two specs sharing an output or a
    routing key.

    `duplicates` maps each (jurisdiction, program_id, period) claimed by more
    than one spec to those spec paths. `name_collisions` maps each artifact
    name (case-folded, because release assets land on case-insensitive
    filesystems) that more than one spec path would produce to those paths.
    `ambiguous_program_keys` maps each program_key (case-folded) that two or
    more different (jurisdiction, program_id) pairs produce to every spec
    path carrying that key.
    """

    def __init__(
        self,
        duplicates: dict[tuple[str, str, str], list[str]],
        name_collisions: dict[str, list[str]],
        ambiguous_program_keys: dict[str, list[str]] | None = None,
    ) -> None:
        self.duplicates = duplicates
        self.name_collisions = name_collisions
        self.ambiguous_program_keys = ambiguous_program_keys or {}
        lines: list[str] = []
        if duplicates:
            lines.append(
                "duplicate legal period: more than one spec claims the same "
                "(jurisdiction, program_id, period); keep one spec per period:"
            )
            for (jurisdiction, program_id, period), paths in sorted(duplicates.items()):
                lines.append(
                    f"  {jurisdiction} {program_id} period {period!r}: {', '.join(paths)}"
                )
        if name_collisions:
            lines.append(
                "artifact name collision: distinct spec paths join to the same "
                "artifact name; rename one of the paths:"
            )
            for name, paths in sorted(name_collisions.items()):
                lines.append(f"  {name}: {', '.join(paths)}")
        if self.ambiguous_program_keys:
            lines.append(
                "ambiguous program_key: different (jurisdiction, program_id) "
                "pairs join to the same program_key, compared case-insensitively; "
                "consumers route by program_key, so change the first or last "
                "`program:` segment of one program:"
            )
            for key, paths in sorted(self.ambiguous_program_keys.items()):
                lines.append(f"  {key}: {', '.join(paths)}")
        super().__init__("\n".join(lines))


def plan_builds(specs: Iterable[tuple[PurePath, object]]) -> list[SpecBuild]:
    """Name and key every spec, refusing only trees whose outputs would clash.

    `specs` holds (path relative to the repo root, parsed YAML) pairs; every
    path must sit under programs/. Pure: the result depends only on the
    pairs, never on their order or on the filesystem. Raises
    SpecIdentityError when two specs share (jurisdiction, program_id, period),
    when two distinct paths would write the same artifact file, or when two
    different (jurisdiction, program_id) pairs share a program_key.

    The third check is what makes program_key a routing key: on an accepted
    tree, program_key.casefold() determines (jurisdiction, program_id), so
    together with the first check (program_key, period) names exactly one
    spec. Without it, us-az/snap and us/az-snap would both carry program_key
    us-az-snap and read as two periods of one program.
    """
    builds: list[SpecBuild] = []
    for spec_path, spec in sorted(specs, key=lambda item: PurePath(item[0])):
        if not isinstance(spec, Mapping) or "program" not in spec:
            continue
        spec_path = Path(spec_path)
        under_programs = spec_path.relative_to("programs")
        program_field = str(spec["program"]).strip()
        segments = tuple(s for s in program_field.split("/") if s)
        if not segments:
            raise SystemExit(f"{spec_path.as_posix()}: `program` has no path segments")
        builds.append(
            SpecBuild(
                spec_path=spec_path,
                jurisdiction=segments[0],
                program_id=segments[-1],
                period=str(spec.get("period", "")).strip(),
                outputs=[str(o) for o in spec.get("outputs", [])],
                artifact_name=artifact_name_for(under_programs),
                program=program_field,
                period_label=period_label_for(under_programs, segments),
            )
        )

    by_identity: dict[tuple[str, str, str], list[str]] = {}
    by_name: dict[str, list[str]] = {}
    by_key: dict[str, list[SpecBuild]] = {}
    for build in builds:
        by_identity.setdefault(build.identity, []).append(build.spec_path.as_posix())
        by_name.setdefault(build.artifact_name.casefold(), []).append(
            build.spec_path.as_posix()
        )
        by_key.setdefault(build.program_key.casefold(), []).append(build)
    duplicates = {key: paths for key, paths in by_identity.items() if len(paths) > 1}
    collisions = {name: paths for name, paths in by_name.items() if len(paths) > 1}
    ambiguous = {
        key: [b.spec_path.as_posix() for b in group]
        for key, group in by_key.items()
        if len({(b.jurisdiction, b.program_id) for b in group}) > 1
    }
    if duplicates or collisions or ambiguous:
        raise SpecIdentityError(duplicates, collisions, ambiguous)
    return builds


def discover_specs(root: Path) -> list[SpecBuild]:
    specs: list[tuple[Path, object]] = []
    for path in sorted((root / "programs").rglob("*.yaml")):
        if path.name.endswith(".test.yaml"):
            continue
        specs.append((path.relative_to(root), yaml.safe_load(path.read_text())))
    return plan_builds(specs)


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


def validation_toolchain(root: Path) -> dict:
    """Read immutable validation and generation checkout identities.

    These pins describe what validated the repository, not necessarily what
    compiled an artifact. The artifact workflow independently resolves the
    execution pins from the same protected file before it builds.
    """
    path = root / ".axiom" / "workflow-toolchain.toml"
    if not path.exists():
        return {}
    try:
        import tomllib

        data = tomllib.loads(path.read_text()).get("workflow_toolchain", {})
    except Exception:
        return {}
    return {
        "axiom_compose_ref": str(data.get("axiom_compose_ref", "")),
        "axiom_artifact_rules_engine_ref": str(
            data.get("axiom_artifact_rules_engine_ref", "")
        ),
        "axiom_rules_engine_ref": str(data.get("axiom_rules_engine_ref", "")),
        "axiom_corpus_ref": str(data.get("axiom_corpus_ref", "")),
        "axiom_encode_ref": str(data.get("axiom_encode_ref", "")),
        "axiom_encode_version": str(data.get("axiom_encode_version", "")),
        "rulespec_us_ref": str(data.get("rulespec_us_ref", "")),
    }


def engine_build_sha(engine_bin: str) -> str:
    """The git SHA of the axiom-rules-engine checkout the binary was built from.

    This is real build provenance, not a pin: prefer an explicit
    AXIOM_RULES_ENGINE_SHA (CI can set it from the engine checkout), else derive
    it by walking up from the binary path to its git repo and reading HEAD.
    Returns "" if neither is available (e.g. a relocated binary) — callers must
    treat "" as "unknown", never substitute a pin.
    """
    explicit = os.environ.get("AXIOM_RULES_ENGINE_SHA", "").strip()
    if explicit:
        return explicit
    try:
        # .../<engine-checkout>/target/{release,debug}/axiom-rules-engine
        bin_path = Path(engine_bin).resolve()
        for parent in bin_path.parents:
            if (parent / ".git").exists():
                return git_output(parent, "rev-parse", "HEAD")
    except Exception:
        pass
    return ""


def build_compat(engine_version: str, engine_sha: str, artifact_schema: int) -> dict:
    """The four-field compatibility contract carried by every artifact.

    - artifact_schema: the compiled-artifact format generation, READ BACK from
      the artifact the engine actually emitted — never a hardcoded claim.
    - built_by_engine: pure provenance (version + real build sha) — never gates.
    - requires_engine: the negotiation floor. It carries BOTH dimensions,
      because they move independently and only one of them gates:

      * min_version is a FIXED tested semver lower bound (not the building
        engine's version). It does not gate loading.
      * artifact_format_version is what the loader matches EXACTLY. An engine
        reporting a different number rejects this artifact however new its
        semver is.

      Emitting only min_version is what let engine v0.1.0 (format 1) and these
      artifacts (format 2) both advertise "0.1.0" and read as compatible while
      every load failed. Released v0.2.0 widens the same false pass: a consumer
      compares 0.2.0 >= 0.1.0, concludes compatible, and is refused at load.
      Compare `axiom-rules-engine capabilities`.artifact_format_version against
      requires_engine.artifact_format_version; treat semver as advisory.
    """
    return {
        "artifact_schema": artifact_schema,
        "built_by_engine": {"version": engine_version, "git_sha": engine_sha},
        "requires_engine": {
            "min_version": MIN_ENGINE_VERSION,
            "artifact_format_version": artifact_schema,
            "capabilities": [],
        },
    }


def artifact_schema_of(artifact: Path) -> int:
    """The format generation the engine actually stamped into this artifact.

    Ground truth, not a declaration: the loader compares this exact number, so
    the manifest must report what was emitted rather than what the builder
    believes. Any engine produces it; no new engine feature is required.
    """
    found = json.loads(artifact.read_text()).get("artifact_format_version")
    if not isinstance(found, int):
        raise RuntimeError(
            f"{artifact.name}: artifact_format_version is {found!r}, expected an int"
        )
    return found


def engine_capabilities(engine_bin: str) -> dict | None:
    """What the binary says it can load, or None on engines predating the
    `capabilities` subcommand.

    Only a nonzero exit (unknown subcommand) or a missing binary reads as
    "legacy engine". An engine that CLAIMS the subcommand — exits zero — and
    then emits something unparseable is broken, not old, and must fail the
    build rather than masquerade as legacy and bypass the cross-check. Same
    for a hang: a 60s timeout on printing two fields is not a legacy engine.
    """
    try:
        out = subprocess.run(
            [engine_bin, "capabilities"], capture_output=True, text=True, timeout=60
        )
    except (OSError, FileNotFoundError):
        return None  # missing/unrunnable binary; the first compile will say so
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"{engine_bin}: `capabilities` hung; broken engine, not a legacy one")
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"{engine_bin}: `capabilities` exited 0 but emitted non-JSON; "
            f"refusing to treat a broken engine as a legacy one"
        )


def assemble_manifest(
    programs: list,
    corpus: dict,
    composer: str,
    engine_version: str,
    engine_sha: str,
    toolchain: dict,
    artifact_schema: int,
) -> dict:
    """Assemble the top-level manifest. Pure function so it is directly testable
    with real inputs (the fields below must come from here, not a test's copy)."""
    return {
        "format_version": MANIFEST_FORMAT_VERSION,
        # What actually composed these artifacts (rulespec-us repo provenance).
        "corpus": corpus,
        "composer_version": composer,
        # Kept for backward compatibility (was the only engine identity);
        # `engine.git_sha` is the real, non-stale one consumers should read.
        "engine_version": engine_version,
        "engine": {"version": engine_version, "git_sha": engine_sha},
        # The pins the repo is VALIDATED against — provenance of validation, not
        # of the build. Explicitly labeled to avoid the "corpus that compiled
        # this" misreading; the published corpus *release* identity is a
        # separate deliberate binding (see corpus_release).
        "validation_toolchain": toolchain,
        # The immutable published corpus release these artifacts cite. Left null
        # until bound authoritatively: the toolchain pins a corpus *commit*, and
        # a release name may be stamped only when an axiom-corpus release
        # manifest's provenance commit exactly equals that pin.
        "corpus_release": None,
        # Observed from the emitted artifacts, not declared. See build_compat.
        "artifact_schema": artifact_schema,
        "programs": programs,
    }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_entry(
    build: SpecBuild,
    *,
    spec_sha256: str,
    artifact: str,
    artifact_sha256: str,
    compat: dict,
    program: dict,
) -> dict:
    """One manifest `programs[]` entry. Every pre-#784 field keeps its meaning;
    `program`, `program_key` and `period_label` are additive."""
    return {
        "jurisdiction": build.jurisdiction,
        "program_id": build.program_id,
        "program": build.program,
        "program_key": build.program_key,
        "period": build.period,
        "period_label": build.period_label,
        "spec_path": build.spec_path.as_posix(),
        "spec_sha256": spec_sha256,
        "outputs": build.outputs,
        "artifact": artifact,
        "artifact_sha256": artifact_sha256,
        "compat": compat,
        "counts": {
            "derived": len(program.get("derived", [])),
            "parameters": len(program.get("parameters", [])),
            "relations": len(program.get("relations", [])),
        },
    }


def compose_spec(root: Path, build: SpecBuild, out_path: Path, corpus_state) -> None:
    from axiom_compose import compose, load_spec

    spec = load_spec(root / build.spec_path)
    program = compose(spec, corpus_state)
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
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--dist", type=Path, default=None)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compile every spec and run every check, but write nothing to --dist",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    engine_bin = os.environ.get("AXIOM_RULES_ENGINE_BIN")
    if not engine_bin:
        print("AXIOM_RULES_ENGINE_BIN is not set", file=sys.stderr)
        return 2

    dist = (args.dist or root / "dist").resolve()

    # Refuse a clashing spec tree before writing anything.
    builds = discover_specs(root)
    if not args.check:
        dist.mkdir(parents=True, exist_ok=True)
    allowlist = load_allowlist(root)
    corpus = corpus_provenance(root)
    composer = composer_version()
    toolchain = validation_toolchain(root)
    engine_sha = engine_build_sha(engine_bin)
    if not engine_sha:
        print(
            "WARN: could not derive engine build sha (relocated binary?); "
            "manifest engine.git_sha will be empty",
            file=sys.stderr,
        )
    elif toolchain.get("axiom_rules_engine_ref") and engine_sha != toolchain["axiom_rules_engine_ref"]:
        print(
            f"WARN: built engine {engine_sha[:12]} != validation pin "
            f"{toolchain['axiom_rules_engine_ref'][:12]} — stamping the real build sha",
            file=sys.stderr,
        )

    # Cross-check before building anything: an engine that can report its own
    # loader contract must agree with what this builder expects to stamp.
    # Engines predating `capabilities` return None and the emitted artifacts
    # remain the sole authority (artifact_schema_of, below).
    caps = engine_capabilities(engine_bin)
    if caps is not None:
        reported = caps.get("artifact_format_version")
        if reported != EXPECTED_ARTIFACT_SCHEMA_VERSION:
            print(
                f"engine reports artifact_format_version {reported}, builder expects "
                f"{EXPECTED_ARTIFACT_SCHEMA_VERSION} — refusing to publish artifacts whose "
                f"compat contract would be wrong",
                file=sys.stderr,
            )
            return 2

    # Compose and compile in a neutral temp directory OUTSIDE the repo: the
    # engine discovers additional rulespec repos by walking up from the module
    # path, so building inside the checkout lets stray sibling checkouts leak
    # modules into the artifact (observed: a legacy per-state repo resolving an
    # import the pinned corpus cannot). Neutral cwd keeps local builds
    # byte-identical to CI.
    workdir = Path(tempfile.mkdtemp(prefix="program-artifacts-"))
    try:
        return build_all(
            root, builds, dist, workdir, engine_bin, engine_sha, allowlist,
            corpus, composer, toolchain, write=not args.check,
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def build_all(
    root: Path,
    builds: list[SpecBuild],
    dist: Path,
    workdir: Path,
    engine_bin: str,
    engine_sha: str,
    allowlist: set[str],
    corpus: dict,
    composer: str,
    toolchain: dict,
    *,
    write: bool,
) -> int:
    """Compose and compile every build in `workdir`.

    With write=False (--check) every check still runs and the manifest is
    still assembled, but nothing reaches `dist`.
    """
    manifest_programs = []
    unexpected_failures: list[str] = []
    unexpected_successes: list[str] = []
    artifact_schemas: set[int] = set()
    engine_version = "unknown"

    # The pinned composer treats CorpusState as immutable and compose() as pure.
    # Parse/index this fixed checkout once, rather than once per program.
    from axiom_compose import load_corpus_from_roots

    print("Loading shared RuleSpec corpus", flush=True)
    corpus_state = load_corpus_from_roots([root]) if builds else None

    for build in builds:
        spec_rel = str(build.spec_path)
        module_path = workdir / f"{build.artifact_name}.rulespec.yaml"
        artifact_path = workdir / f"{build.artifact_name}.compiled.json"
        try:
            print(f"BUILD {spec_rel}", flush=True)
            compose_spec(root, build, module_path, corpus_state)
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

        # The four-field compatibility contract, self-describing inside each
        # artifact so a consumer can negotiate with the engine before loading.
        schema = artifact_schema_of(artifact_path)
        if schema != EXPECTED_ARTIFACT_SCHEMA_VERSION:
            print(
                f"FAIL {spec_rel}: engine emitted artifact_format_version {schema}, "
                f"builder expects {EXPECTED_ARTIFACT_SCHEMA_VERSION}. The engine pin moved "
                f"across a format boundary; bump EXPECTED_ARTIFACT_SCHEMA_VERSION "
                f"deliberately and re-cut the engine release.",
                file=sys.stderr,
            )
            unexpected_failures.append(spec_rel)
            continue
        artifact_schemas.add(schema)
        compat = build_compat(engine_version, engine_sha, schema)
        provenance = {
            "corpus": corpus,
            "spec_path": spec_rel,
            "spec_sha256": sha256_file(root / build.spec_path),
            "composer_version": composer,
            "engine_version": engine_version,
            "compat": compat,
        }
        stamp_provenance(artifact_path, provenance)

        if write:
            shutil.copy2(module_path, dist / module_path.name)
            artifact_path = Path(shutil.copy2(artifact_path, dist / artifact_path.name))

        program = json.loads(artifact_path.read_text())["program"]
        manifest_programs.append(
            manifest_entry(
                build,
                spec_sha256=provenance["spec_sha256"],
                artifact=artifact_path.name,
                artifact_sha256=sha256_file(artifact_path),
                compat=compat,
                program=program,
            )
        )
        print(
            f"OK   {spec_rel} -> {artifact_path.name} "
            f"({manifest_programs[-1]['counts']['derived']}d)"
        )

    if len(artifact_schemas) > 1:
        print(
            f"artifacts disagree on artifact_format_version {sorted(artifact_schemas)} — "
            f"a single manifest cannot describe them",
            file=sys.stderr,
        )
        return 1
    manifest = assemble_manifest(
        manifest_programs,
        corpus,
        composer,
        engine_version,
        engine_sha,
        toolchain,
        artifact_schemas.pop() if artifact_schemas else EXPECTED_ARTIFACT_SCHEMA_VERSION,
    )
    if write:
        (dist / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    if unexpected_successes:
        print(
            "NOTE: allowlisted specs now compile — remove from known-broken-specs.txt: "
            + ", ".join(unexpected_successes)
        )
    if unexpected_failures:
        print(f"{len(unexpected_failures)} spec(s) failed to build", file=sys.stderr)
        return 1
    if write:
        print(f"built {len(manifest_programs)}/{len(builds)} programs -> {dist}")
    else:
        print(f"built {len(manifest_programs)}/{len(builds)} programs (--check: nothing written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
