#!/usr/bin/env python3
"""Build compiled program artifacts from every spec in programs/.

For each programs/<jurisdiction>/<program>/<period>.yaml spec this composes the
program (axiom-compose), compiles it to an executable artifact
(axiom-rules-engine compile-composed), stamps provenance into the artifact metadata, and
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
# The compiled-artifact format generation this builder is known to work with.
# It is an EXPECTATION, not the stamped value: what lands in the manifest is
# read back from the artifact the engine emitted (artifact_schema_of), and a
# mismatch fails the build. Bumping the engine across a format boundary without
# bumping this is therefore a hard error, not a silently mislabeled release.
EXPECTED_ARTIFACT_SCHEMA_VERSION = 2
# Supported consumer baseline for this producer. Semver remains advisory:
# released 0.2.2 predates the fixed compiler, so exact build provenance and
# capability negotiation must accompany it. Both capabilities are deliberately
# required for the whole release, including programs without related aggregates.
MIN_ENGINE_VERSION = "0.2.2"
REQUIRED_ENGINE_CAPABILITIES = ("relation_entity_typing", "related_min_max_only")


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


def checkout_identity(path: Path) -> dict:
    """Identify a corpus root by its git checkout; refuse one that has none."""
    resolved = path.resolve()
    try:
        top = Path(git_output(resolved, "rev-parse", "--show-toplevel")).resolve()
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError(
            f"{path}: a --rulespec-root must be a git checkout so its identity can be recorded"
        ) from error
    if top != resolved:
        raise ValueError(f"{path}: a --rulespec-root must be the top of its checkout ({top})")
    return {"name": resolved.name, **corpus_provenance(resolved)}


def corpus_root_identities(root: Path, corpus: dict, rulespec_roots: list[Path] | None) -> list[dict]:
    """Return the identity of every root the composer and compiler read, in order.

    `corpus` describes --root, where the ProgramSpecs are read. A staged root
    of the same repository stands in for it only at that identical clean
    commit; anything else would publish one corpus's rules under another's
    identity.
    """
    if not rulespec_roots:
        return [{"name": root.name, **corpus}]
    identities = []
    for path in rulespec_roots:
        if path.resolve() == root:
            identities.append({"name": root.name, **corpus})
            continue
        identity = checkout_identity(path)
        if identity["repo"] == corpus.get("repo") and (
            identity["sha"] != corpus.get("sha") or identity["dirty"] or corpus.get("dirty")
        ):
            raise ValueError(
                f"{path} is {identity['repo']} at {identity['sha'][:12]} (dirty={identity['dirty']}), "
                f"but --root is {corpus.get('sha', '')[:12]} (dirty={corpus.get('dirty')}); a staged "
                "root must be the same clean commit as the checkout its ProgramSpecs come from"
            )
        identities.append(identity)
    if not any(identity.get("repo") == corpus.get("repo") for identity in identities):
        raise ValueError(f"no --rulespec-root is the {corpus.get('repo')} corpus that --root's "
                         "ProgramSpecs compose")
    return identities


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
        "axiom_artifact_compose_ref": str(data.get("axiom_artifact_compose_ref", "")),
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
    - requires_engine: the supported consumer contract. Format and capabilities
      gate independently; semver is advisory:

      * min_version is a FIXED advisory baseline (not the building engine's
        version). It does not gate loading.
      * artifact_format_version is what the loader matches EXACTLY. An engine
        reporting a different number rejects this artifact however new its
        semver is.

      * capabilities names the supported runtime features of this producer.
        Consumers must provide every listed capability as well as format 2.

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
            "capabilities": list(REQUIRED_ENGINE_CAPABILITIES),
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
    corpus_roots: list | None = None,
) -> dict:
    """Assemble the top-level manifest. Pure function so it is directly testable
    with real inputs (the fields below must come from here, not a test's copy)."""
    return {
        "format_version": MANIFEST_FORMAT_VERSION,
        # The --root checkout: its ProgramSpecs and, through any staged root of
        # the same repository (held to this exact clean commit), its corpus.
        "corpus": corpus,
        # Every root the composer and compiler read, in order.
        "corpus_roots": corpus_roots if corpus_roots is not None else [corpus],
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


def compose_spec(root: Path, build: SpecBuild, out_path: Path, corpus_state) -> None:
    from axiom_compose import compose, load_spec

    spec = load_spec(root / build.spec_path)
    program = compose(spec, corpus_state)
    out_path.write_bytes(program.source)


def engine_compile(
    root: Path, module: Path, artifact: Path, engine_bin: str,
    rulespec_roots: list[Path] | None = None,
) -> str:
    """Compile originless composer output using explicit country authorities.

    Each root must be a real canonical rulespec-<country> directory. Callers
    building from a differently named worktree can supply a staged corpus with
    --rulespec-root; no ambient sibling checkout or legacy environment fallback
    participates in import resolution.
    """
    env = dict(os.environ)
    env.pop("AXIOM_RULESPEC_REPO_ROOTS", None)
    env.pop("AXIOM_RULESPEC_REPO_ROOTS_EXCLUSIVE", None)
    command = [engine_bin, "compile-composed", "--program", str(module.resolve())]
    for country_root in rulespec_roots or [root]:
        command.extend(["--rulespec-root", str(country_root.absolute())])
    command.extend(["--output", str(artifact.resolve())])
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    match = re.search(r"^engine_version:\s*(\S+)", result.stdout, re.M)
    return match.group(1) if match else "unknown"


def checkpoint(path: Path | None, record: dict) -> None:
    """Append a complete per-spec outcome immediately, including exact errors."""
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
            stream.flush()


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
    parser.add_argument("--rulespec-root", action="append", type=Path,
                        help="Absolute canonical country root; repeat for every country (default: --root)")
    parser.add_argument("--results-jsonl", type=Path,
                        help="Append checkpointed per-program results, with complete errors")
    parser.add_argument("--spec", action="append",
                        help="Build only this root-relative ProgramSpec; repeat to split long runs. "
                             "The manifest describes only this selection; use a separate --dist per batch")
    args = parser.parse_args()

    root = args.root.resolve()
    engine_bin = os.environ.get("AXIOM_RULES_ENGINE_BIN")
    if not engine_bin:
        print("AXIOM_RULES_ENGINE_BIN is not set", file=sys.stderr)
        return 2

    dist = (args.dist or root / "dist").resolve()
    if not args.check:
        dist.mkdir(parents=True, exist_ok=True)

    builds = discover_specs(root)
    if args.spec:
        selected = set(args.spec)
        unknown = selected - {str(build.spec_path) for build in builds}
        if unknown:
            parser.error(f"unknown ProgramSpecs: {sorted(unknown)}")
        builds = [build for build in builds if str(build.spec_path) in selected]
    allowlist = load_allowlist(root)
    corpus = corpus_provenance(root)
    composer = composer_version()
    toolchain = validation_toolchain(root)
    engine_sha = engine_build_sha(engine_bin)
    if not re.fullmatch(r"[0-9a-f]{40}", engine_sha):
        print(
            "A full lowercase compiler SHA is required; set AXIOM_RULES_ENGINE_SHA "
            "for a relocated binary",
            file=sys.stderr,
        )
        return 2
    elif toolchain.get("axiom_artifact_rules_engine_ref") and engine_sha != toolchain["axiom_artifact_rules_engine_ref"]:
        print(
            f"WARN: built engine {engine_sha[:12]} != artifact pin "
            f"{toolchain['axiom_artifact_rules_engine_ref'][:12]} — stamping the real build sha",
            file=sys.stderr,
        )

    # Cross-check before building anything: an engine that can report its own
    # loader contract must agree with what this builder expects to stamp.
    # The main compiler contract requires capability negotiation. The helper
    # still recognizes legacy binaries for diagnostics, but they cannot build
    # this producer's release.
    caps = engine_capabilities(engine_bin)
    if caps is None:
        print("engine must support `capabilities` for this producer", file=sys.stderr)
        return 2
    else:
        reported = caps.get("artifact_format_version")
        if reported != EXPECTED_ARTIFACT_SCHEMA_VERSION:
            print(
                f"engine reports artifact_format_version {reported}, builder expects "
                f"{EXPECTED_ARTIFACT_SCHEMA_VERSION} — refusing to publish artifacts whose "
                f"compat contract would be wrong",
                file=sys.stderr,
            )
            return 2
        missing = set(REQUIRED_ENGINE_CAPABILITIES) - set(caps.get("capabilities", []))
        if missing:
            print(f"engine lacks required capabilities: {sorted(missing)}", file=sys.stderr)
            return 2
    try:
        root_identities = corpus_root_identities(root, corpus, args.rulespec_root)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    manifest_programs = []
    unexpected_failures: list[str] = []
    unexpected_successes: list[str] = []
    artifact_schemas: set[int] = set()
    engine_version = "unknown"

    # Generated compositions must be outside every configured country root.
    workspace = tempfile.TemporaryDirectory(prefix="program-artifacts-")
    workdir = Path(workspace.name)

    # The pinned composer treats CorpusState as immutable and compose() as pure.
    # Parse/index this fixed checkout once, rather than once per program.
    from axiom_compose import load_corpus_from_roots

    print("Loading shared RuleSpec corpus", flush=True)
    corpus_roots = [path.absolute() for path in args.rulespec_root] if args.rulespec_root else [root]
    corpus_state = load_corpus_from_roots(corpus_roots) if builds else None

    for build in builds:
        spec_rel = str(build.spec_path)
        module_path = workdir / f"{build.artifact_name}.rulespec.yaml"
        artifact_path = workdir / f"{build.artifact_name}.compiled.json"
        stage = "compose"
        try:
            print(f"BUILD {spec_rel}", flush=True)
            compose_spec(root, build, module_path, corpus_state)
            stage = "compile"
            if args.rulespec_root:
                compiled_version = engine_compile(root, module_path, artifact_path, engine_bin, args.rulespec_root)
            else:
                compiled_version = engine_compile(root, module_path, artifact_path, engine_bin)

            # Validate and stamp before publishing either file. A compiler can
            # exit successfully without producing a usable artifact; that is a
            # per-program failure and must not prevent the remaining census.
            stage = "validate"
            schema = artifact_schema_of(artifact_path)
            if schema != EXPECTED_ARTIFACT_SCHEMA_VERSION:
                raise RuntimeError(
                    f"engine emitted artifact_format_version {schema}, builder expects "
                    f"{EXPECTED_ARTIFACT_SCHEMA_VERSION}. The engine pin moved across a "
                    "format boundary; bump EXPECTED_ARTIFACT_SCHEMA_VERSION deliberately "
                    "and re-cut the engine release."
                )
            program = json.loads(artifact_path.read_text())["program"]
            counts = {
                "derived": len(program.get("derived", [])),
                "parameters": len(program.get("parameters", [])),
                "relations": len(program.get("relations", [])),
            }
            compat = build_compat(compiled_version, engine_sha, schema)
            provenance = {
                "corpus": corpus,
                "corpus_roots": root_identities,
                "spec_path": spec_rel,
                "spec_sha256": sha256_file(root / build.spec_path),
                "composer_version": composer,
                "engine_version": compiled_version,
                "compat": compat,
            }
            stamp_provenance(artifact_path, provenance)

            if not args.check:
                shutil.copy2(module_path, dist / module_path.name)
                artifact_path = Path(shutil.copy2(artifact_path, dist / artifact_path.name))

            program_entry = {
                "jurisdiction": build.jurisdiction,
                "program_id": build.program_id,
                "period": build.period,
                "spec_path": spec_rel,
                "spec_sha256": provenance["spec_sha256"],
                "outputs": build.outputs,
                "artifact": artifact_path.name,
                "artifact_sha256": sha256_file(artifact_path),
                "compat": compat,
                "counts": counts,
            }
        except Exception as error:
            error_message = str(error) or type(error).__name__
            checkpoint(args.results_jsonl, {"spec_path": spec_rel, "status": "failed",
                       "stage": stage, "error": error_message, "engine_sha": engine_sha})
            message = next((line for line in error_message.splitlines() if line.strip()),
                           type(error).__name__)[:200]
            if spec_rel in allowlist:
                print(f"KNOWN-BROKEN {spec_rel}: {message}")
            else:
                print(f"FAIL {spec_rel}: {message}", file=sys.stderr)
                unexpected_failures.append(spec_rel)
            continue

        if spec_rel in allowlist:
            unexpected_successes.append(spec_rel)
        artifact_schemas.add(schema)
        engine_version = compiled_version
        manifest_programs.append(program_entry)
        print(
            f"OK   {spec_rel} -> {artifact_path.name} "
            f"({manifest_programs[-1]['counts']['derived']}d)"
        )
        checkpoint(args.results_jsonl, {"spec_path": spec_rel, "status": "built",
                   "engine_sha": engine_sha, "artifact": artifact_path.name,
                   "artifact_sha256": manifest_programs[-1]["artifact_sha256"]})

    workspace.cleanup()

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
        root_identities,
    )
    if not args.check:
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
