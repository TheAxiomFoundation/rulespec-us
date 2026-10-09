"""Example tests for program identity and artifact naming (rulespec-us#784).

Two legal periods of one program must build side by side; the build refuses
only a genuine (jurisdiction, program_id, period) duplicate, or two spec paths
that would write the same artifact file. These drive the real `main()` with
axiom-compose and the engine stubbed, so they need no Rust build.
Property-based versions of the same invariants are in
test_program_identity_properties.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

import pytest
import yaml

TOOLS = Path(__file__).resolve().parents[1]
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import build_program_artifacts as bpa  # noqa: E402

TARIFF_SCHEDULE_DIR = PurePosixPath("programs/us/us-tariff-schedule")


def legacy_artifact_names(root: Path) -> dict[str, str]:
    """The pre-#784 naming, copied from tools/build_program_artifacts.py
    discover_specs at a9dc38fb0 (lines 63-91): f"{jurisdiction}-{program_id}"."""
    names: dict[str, str] = {}
    for path in sorted((root / "programs").rglob("*.yaml")):
        if path.name.endswith(".test.yaml"):
            continue
        spec = yaml.safe_load(path.read_text())
        if not isinstance(spec, dict) or "program" not in spec:
            continue
        segments = [s for s in str(spec["program"]).split("/") if s]
        names[path.relative_to(root).as_posix()] = f"{segments[0]}-{segments[-1]}"
    return names


def write_spec(root: Path, rel: str, program: str, period: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {"program": program, "period": period, "outputs": ["snap_benefit"]},
            sort_keys=False,
        )
    )


@pytest.fixture
def toolchain(monkeypatch):
    """Stub axiom-compose and the engine. Each artifact embeds the composed
    module's text, so two specs can only share bytes if one was copied over
    the other."""
    calls = SimpleNamespace(composed=[], compiled=[])

    def compose(spec, corpus):
        calls.composed.append(f"{spec['program']}@{spec['period']}")
        return SimpleNamespace(source=f"{spec['program']} {spec['period']}\n".encode())

    def compile_program(root, module, artifact, engine):
        calls.compiled.append(module.name)
        artifact.write_text(
            json.dumps(
                {
                    "artifact_format_version": 2,
                    "program": {
                        "derived": [{"name": module.read_text().strip()}],
                        "parameters": [],
                        "relations": [],
                    },
                }
            )
        )
        return "0.1.2"

    monkeypatch.setitem(
        sys.modules,
        "axiom_compose",
        SimpleNamespace(
            load_corpus_from_roots=lambda roots: object(),
            load_spec=lambda path: yaml.safe_load(Path(path).read_text()),
            compose=compose,
        ),
    )
    monkeypatch.setenv("AXIOM_RULES_ENGINE_BIN", "test-engine")
    monkeypatch.setattr(
        bpa, "corpus_provenance", lambda root: {"repo": "rulespec-us", "sha": "a" * 40, "dirty": False}
    )
    monkeypatch.setattr(bpa, "composer_version", lambda: "test")
    monkeypatch.setattr(bpa, "engine_build_sha", lambda engine: "b" * 40)
    monkeypatch.setattr(bpa, "engine_capabilities", lambda engine: None)
    monkeypatch.setattr(bpa, "engine_compile", compile_program)
    return calls


def run_main(monkeypatch, root: Path, *extra: str) -> int:
    monkeypatch.setattr(sys, "argv", ["build", "--root", str(root), *extra])
    return bpa.main()


def test_two_periods_of_one_program_build_side_by_side(tmp_path, monkeypatch, toolchain):
    root = tmp_path / "rulespec-us"
    write_spec(root, "programs/us-az/snap/fy-2026.yaml", "us-az/snap", "2026-01")
    write_spec(root, "programs/us-az/snap/fy-2027.yaml", "us-az/snap", "2026-10")

    assert run_main(monkeypatch, root) == 0

    dist = root / "dist"
    assert sorted(p.name for p in dist.iterdir()) == [
        "manifest.json",
        "us-az-snap-fy-2026.compiled.json",
        "us-az-snap-fy-2026.rulespec.yaml",
        "us-az-snap-fy-2027.compiled.json",
        "us-az-snap-fy-2027.rulespec.yaml",
    ]
    manifest = json.loads((dist / "manifest.json").read_text())
    entries = {entry["artifact"]: entry for entry in manifest["programs"]}
    fy2026 = entries["us-az-snap-fy-2026.compiled.json"]
    fy2027 = entries["us-az-snap-fy-2027.compiled.json"]

    # Both periods share the period-free key consumers already use.
    assert (fy2026["program_key"], fy2026["period"], fy2026["period_label"]) == (
        "us-az-snap",
        "2026-01",
        "fy-2026",
    )
    assert (fy2027["program_key"], fy2027["period"], fy2027["period_label"]) == (
        "us-az-snap",
        "2026-10",
        "fy-2027",
    )
    # Pre-#784 fields keep their meaning.
    for entry, spec in ((fy2026, "fy-2026"), (fy2027, "fy-2027")):
        assert entry["jurisdiction"] == "us-az"
        assert entry["program_id"] == "snap"
        assert entry["program"] == "us-az/snap"
        assert entry["spec_path"] == f"programs/us-az/snap/{spec}.yaml"
        assert entry["outputs"] == ["snap_benefit"]
        assert entry["artifact_sha256"] == bpa.sha256_file(dist / entry["artifact"])
    # Each file is its own spec's build, not one period copied over the other.
    assert fy2026["artifact_sha256"] != fy2027["artifact_sha256"]
    assert toolchain.composed == ["us-az/snap@2026-01", "us-az/snap@2026-10"]
    assert (dist / "us-az-snap-fy-2027.rulespec.yaml").read_text() == "us-az/snap 2026-10\n"


def test_a_genuine_duplicate_period_fails_before_anything_is_built(
    tmp_path, monkeypatch, toolchain
):
    root = tmp_path / "rulespec-us"
    write_spec(root, "programs/us-az/snap/fy-2026.yaml", "us-az/snap", "2026-01")
    write_spec(root, "programs/us-az/snap/fy-2026-revised.yaml", "us-az/snap", "2026-01")
    write_spec(root, "programs/us-az/snap/fy-2027.yaml", "us-az/snap", "2026-10")

    with pytest.raises(bpa.SpecIdentityError) as excinfo:
        run_main(monkeypatch, root)

    error = excinfo.value
    assert isinstance(error, SystemExit)  # the CLI exits nonzero with the message
    assert error.duplicates == {
        ("us-az", "snap", "2026-01"): [
            "programs/us-az/snap/fy-2026-revised.yaml",
            "programs/us-az/snap/fy-2026.yaml",
        ]
    }
    assert error.name_collisions == {}
    assert "duplicate legal period" in str(error.code)
    assert "programs/us-az/snap/fy-2026-revised.yaml" in str(error.code)
    assert toolchain.composed == []
    assert not (root / "dist").exists()


def test_period_identity_ignores_the_programs_middle_path_segments():
    # axiom-compose reads only the first `program:` segment (state scope
    # prefix) and the last (auto-gate token), so the identity uses only those.
    def spec(program, period):
        return {"program": program, "period": period, "outputs": ["x"]}

    with pytest.raises(bpa.SpecIdentityError) as excinfo:
        bpa.plan_builds(
            [
                (PurePosixPath("programs/us/payroll/oasdi-wage-tax/fy-2026.yaml"), spec("us/payroll/oasdi-wage-tax", "2026")),
                (PurePosixPath("programs/us/oasdi-wage-tax/fy-2026.yaml"), spec("us/oasdi-wage-tax", "2026")),
            ]
        )
    assert list(excinfo.value.duplicates) == [("us", "oasdi-wage-tax", "2026")]

    builds = bpa.plan_builds(
        [
            (PurePosixPath("programs/us/payroll/oasdi-wage-tax/fy-2026.yaml"), spec("us/payroll/oasdi-wage-tax", "2026")),
            (PurePosixPath("programs/us/oasdi-wage-tax/fy-2027.yaml"), spec("us/oasdi-wage-tax", "2027")),
        ]
    )
    assert [b.program_key for b in builds] == ["us-oasdi-wage-tax", "us-oasdi-wage-tax"]
    assert [b.artifact_name for b in builds] == [
        "us-oasdi-wage-tax-fy-2027",
        "us-payroll-oasdi-wage-tax-fy-2026",
    ]


def test_distinct_paths_that_join_to_one_name_fail_with_both_paths():
    # The one tree path-derived names cannot serve: a hyphenated string split
    # differently across directory levels. Never a silent overwrite.
    with pytest.raises(bpa.SpecIdentityError) as excinfo:
        bpa.plan_builds(
            [
                (PurePosixPath("programs/us-az/snap/fy-2026.yaml"), {"program": "us-az/snap", "period": "2026-01"}),
                (PurePosixPath("programs/us/az-snap/fy-2026.yaml"), {"program": "us/az-snap", "period": "2026-01"}),
            ]
        )
    assert excinfo.value.duplicates == {}
    assert excinfo.value.name_collisions == {
        "us-az-snap-fy-2026": [
            "programs/us/az-snap/fy-2026.yaml",
            "programs/us-az/snap/fy-2026.yaml",
        ]
    }
    assert "artifact name collision" in str(excinfo.value.code)


def test_names_differing_only_in_case_collide():
    # Release assets are downloaded onto case-insensitive filesystems (macOS).
    with pytest.raises(bpa.SpecIdentityError) as excinfo:
        bpa.plan_builds(
            [
                (PurePosixPath("programs/us-az/SNAP/fy-2026.yaml"), {"program": "us-az/SNAP", "period": "2026-01"}),
                (PurePosixPath("programs/us-az/snap/fy-2026.yaml"), {"program": "us-az/snap", "period": "2026-01"}),
            ]
        )
    assert list(excinfo.value.name_collisions) == ["us-az-snap-fy-2026"]


def test_specs_without_a_program_are_skipped_and_an_empty_program_is_refused():
    assert bpa.plan_builds(
        [
            (PurePosixPath("programs/notes.yaml"), {"title": "not a spec"}),
            (PurePosixPath("programs/list.yaml"), ["not", "a", "mapping"]),
            (PurePosixPath("programs/empty.yaml"), None),
        ]
    ) == []
    with pytest.raises(SystemExit, match="has no path segments"):
        bpa.plan_builds([(PurePosixPath("programs/x/y.yaml"), {"program": " / ", "period": "2026"})])


def test_naming_helpers():
    assert bpa.artifact_name_for(PurePosixPath("us-az/snap/fy-2026.yaml")) == "us-az-snap-fy-2026"
    assert (
        bpa.artifact_name_for(PurePosixPath("us/payroll/oasdi-wage-tax/fy-2026.yaml"))
        == "us-payroll-oasdi-wage-tax-fy-2026"
    )
    assert bpa.period_label_for(PurePosixPath("us-az/snap/fy-2026.yaml"), ("us-az", "snap")) == "fy-2026"
    assert (
        bpa.period_label_for(
            PurePosixPath("us/us-tariff-schedule/ch01.yaml"), ("us", "us-tariff-schedule", "ch01")
        )
        is None
    )


def test_real_spec_tree_names_are_unique_including_the_tariff_chapters():
    builds = bpa.discover_specs(REPO)
    assert builds, "programs/ holds no specs"
    names = [build.artifact_name.casefold() for build in builds]
    assert len(set(names)) == len(builds)
    assert len({build.identity for build in builds}) == len(builds)

    chapters = [b for b in builds if PurePosixPath(b.spec_path.as_posix()).parent == TARIFF_SCHEDULE_DIR]
    assert chapters, "expected the generated tariff-schedule chapter specs"
    for build in chapters:
        chapter = build.spec_path.stem
        assert build.program == f"us/us-tariff-schedule/{chapter}"
        assert build.artifact_name == f"us-us-tariff-schedule-{chapter}"
        assert build.program_key == f"us-{chapter}"
        assert build.period_label is None  # the stem is the chapter, not a period

    snap_az = next(b for b in builds if b.spec_path.as_posix() == "programs/us-az/snap/fy-2026.yaml")
    assert (snap_az.artifact_name, snap_az.program_key, snap_az.period_label) == (
        "us-az-snap-fy-2026",
        "us-az-snap",
        "fy-2026",
    )


def test_program_key_is_the_pre_784_artifact_name_for_every_real_spec():
    # Differential against the old naming: consumers map old pins to new
    # artifacts through program_key, so it must equal the old name exactly.
    builds = bpa.discover_specs(REPO)
    assert {b.spec_path.as_posix(): b.program_key for b in builds} == legacy_artifact_names(REPO)


def test_discover_skips_companion_tests(tmp_path):
    write_spec(tmp_path, "programs/us-az/snap/fy-2026.yaml", "us-az/snap", "2026-01")
    write_spec(tmp_path, "programs/us-az/snap/fy-2026.test.yaml", "us-az/snap", "2026-01")
    assert [b.spec_path.as_posix() for b in bpa.discover_specs(tmp_path)] == [
        "programs/us-az/snap/fy-2026.yaml"
    ]


def test_check_mode_builds_everything_and_writes_nothing(tmp_path, monkeypatch, toolchain):
    root = tmp_path / "rulespec-us"
    write_spec(root, "programs/us-az/snap/fy-2026.yaml", "us-az/snap", "2026-01")
    write_spec(root, "programs/us-az/snap/fy-2027.yaml", "us-az/snap", "2026-10")
    dist = tmp_path / "out"

    assert run_main(monkeypatch, root, "--check", "--dist", str(dist)) == 0

    assert toolchain.compiled == [
        "us-az-snap-fy-2026.rulespec.yaml",
        "us-az-snap-fy-2027.rulespec.yaml",
    ]
    assert not dist.exists()
    assert not (root / "dist").exists()


def test_check_mode_still_fails_on_a_spec_that_does_not_compile(tmp_path, monkeypatch, toolchain):
    root = tmp_path / "rulespec-us"
    write_spec(root, "programs/us-az/snap/fy-2026.yaml", "us-az/snap", "2026-01")
    write_spec(root, "programs/us-az/snap/fy-2027.yaml", "us-az/snap", "2026-10")
    compile_ok = bpa.engine_compile

    def compile_or_fail(root, module, artifact, engine):
        if "fy-2027" in module.name:
            raise RuntimeError("unresolved import")
        return compile_ok(root, module, artifact, engine)

    monkeypatch.setattr(bpa, "engine_compile", compile_or_fail)
    dist = tmp_path / "out"
    assert run_main(monkeypatch, root, "--check", "--dist", str(dist)) == 1
    assert not dist.exists()


def test_the_scratch_directory_is_removed_after_a_build(tmp_path, monkeypatch, toolchain):
    root = tmp_path / "rulespec-us"
    write_spec(root, "programs/us-az/snap/fy-2026.yaml", "us-az/snap", "2026-01")
    scratch = tmp_path / "scratch"

    def mkdtemp(prefix=""):
        scratch.mkdir()
        return str(scratch)

    monkeypatch.setattr(bpa.tempfile, "mkdtemp", mkdtemp)
    assert run_main(monkeypatch, root) == 0
    assert not scratch.exists()
    assert (root / "dist" / "us-az-snap-fy-2026.compiled.json").exists()
