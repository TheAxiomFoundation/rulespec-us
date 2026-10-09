"""Example tests for program identity and artifact naming (rulespec-us#784).

Two legal periods of one program must build side by side; the build refuses
only a genuine (jurisdiction, program_id, period) duplicate, two spec paths
that would write the same artifact file, or two different programs that would
share a program_key. These drive the real `main()` with axiom-compose and the
engine stubbed, so they need no Rust build.
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
    """The pre-#784 naming, reimplemented from tools/build_program_artifacts.py
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
    # axiom-compose's behavior depends on `program:` only through its first
    # segment (import and `state:` scope prefixes) and its last (auto-gate
    # token); middle segments are labels. The identity uses only those two.
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
    # The two programs also share program_key us-az-snap; both are reported.
    assert excinfo.value.ambiguous_program_keys == {
        "us-az-snap": [
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
    # us-az-SNAP and us-az-snap are one routing key once case is ignored.
    assert list(excinfo.value.ambiguous_program_keys) == ["us-az-snap"]


@pytest.mark.parametrize("other_period", ["2026-01", "2026-10"])
def test_distinct_programs_sharing_a_program_key_are_refused(
    tmp_path, monkeypatch, toolchain, other_period
):
    # us-az/snap and us/az-snap are different programs: different
    # jurisdictions, so different import and `state:` scopes in compose. Both
    # hyphen-join to program_key us-az-snap. The stems differ, so their
    # artifact names do not collide. Accepted, a consumer routing by
    # (program_key, period) would read them as one program: with equal
    # periods it could not choose, and with different periods it would
    # silently treat one program as another's earlier period.
    root = tmp_path / "rulespec-us"
    write_spec(root, "programs/us-az/snap/fy-2026.yaml", "us-az/snap", "2026-01")
    write_spec(root, "programs/us/az-snap/fy-2026b.yaml", "us/az-snap", other_period)

    with pytest.raises(bpa.SpecIdentityError) as excinfo:
        run_main(monkeypatch, root)

    error = excinfo.value
    assert error.duplicates == {}
    assert error.name_collisions == {}
    assert error.ambiguous_program_keys == {
        "us-az-snap": [
            "programs/us/az-snap/fy-2026b.yaml",
            "programs/us-az/snap/fy-2026.yaml",
        ]
    }
    assert "ambiguous program_key" in str(error.code)
    assert toolchain.composed == []
    assert not (root / "dist").exists()


def test_program_keys_differing_only_in_case_are_refused():
    # Different paths, so no name collision, and different identities, but
    # us-az-snap and US-AZ-snap are one key to a case-insensitive consumer
    # (and were one file on macOS under the pre-#784 names).
    with pytest.raises(bpa.SpecIdentityError) as excinfo:
        bpa.plan_builds(
            [
                (PurePosixPath("programs/us-az/snap/fy-2026.yaml"), {"program": "us-az/snap", "period": "2026-01"}),
                (PurePosixPath("programs/legacy/snap/fy-2027.yaml"), {"program": "US-AZ/snap", "period": "2026-10"}),
            ]
        )
    assert excinfo.value.duplicates == {}
    assert excinfo.value.name_collisions == {}
    assert excinfo.value.ambiguous_program_keys == {
        "us-az-snap": [
            "programs/legacy/snap/fy-2027.yaml",
            "programs/us-az/snap/fy-2026.yaml",
        ]
    }


def test_surrounding_whitespace_in_program_and_period_is_stripped():
    # compose strips both fields (_non_empty_string, spec.py:151-154 at
    # fabe0b3); the builder must agree, or " 2026-01 " and "2026-01" would be
    # two periods of one program.
    padded = {"program": "  us-az/snap ", "period": " 2026-01 ", "outputs": ["x"]}
    [build] = bpa.plan_builds([(PurePosixPath("programs/us-az/snap/fy-2026.yaml"), padded)])
    assert (build.program, build.jurisdiction, build.program_id, build.period) == (
        "us-az/snap",
        "us-az",
        "snap",
        "2026-01",
    )
    assert build.program_key == "us-az-snap"
    assert build.period_label == "fy-2026"
    entry = bpa.manifest_entry(
        build,
        spec_sha256="d" * 64,
        artifact="us-az-snap-fy-2026.compiled.json",
        artifact_sha256="e" * 64,
        compat={},
        program={},
    )
    assert (entry["program"], entry["period"]) == ("us-az/snap", "2026-01")

    with pytest.raises(bpa.SpecIdentityError) as excinfo:
        bpa.plan_builds(
            [
                (PurePosixPath("programs/us-az/snap/fy-2026.yaml"), padded),
                (PurePosixPath("programs/us-az/snap/fy-2026-copy.yaml"), {"program": "us-az/snap", "period": "2026-01"}),
            ]
        )
    assert list(excinfo.value.duplicates) == [("us-az", "snap", "2026-01")]


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
    # program_key names one program, so (program_key, period) names one spec.
    programs_by_key: dict[str, set[tuple[str, str]]] = {}
    for build in builds:
        programs_by_key.setdefault(build.program_key.casefold(), set()).add(
            (build.jurisdiction, build.program_id)
        )
    assert all(len(pairs) == 1 for pairs in programs_by_key.values())
    assert len({(b.program_key.casefold(), b.period) for b in builds}) == len(builds)

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


def test_a_build_clears_artifacts_an_earlier_build_left_in_dist(tmp_path, monkeypatch, toolchain):
    root = tmp_path / "rulespec-us"
    write_spec(root, "programs/us-az/snap/fy-2026.yaml", "us-az/snap", "2026-01")
    dist = root / "dist"
    dist.mkdir(parents=True)
    # What a pre-#784 build wrote, plus files the builder does not own.
    (dist / "us-az-snap.compiled.json").write_text("{}\n")
    (dist / "us-az-snap.rulespec.yaml").write_text("old\n")
    (dist / "manifest.json").write_text('{"programs": []}\n')
    (dist / "notes.txt").write_text("keep me\n")
    (dist / "nested").mkdir()
    (dist / "nested" / "keep.compiled.json").write_text("{}\n")
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text("{}\n")
    (dist / "linked.compiled.json").symlink_to(elsewhere)

    assert run_main(monkeypatch, root) == 0

    assert sorted(p.name for p in dist.iterdir()) == [
        "linked.compiled.json",
        "manifest.json",
        "nested",
        "notes.txt",
        "us-az-snap-fy-2026.compiled.json",
        "us-az-snap-fy-2026.rulespec.yaml",
    ]
    assert (dist / "nested" / "keep.compiled.json").exists()
    assert (dist / "linked.compiled.json").is_symlink()
    assert elsewhere.read_text() == "{}\n"
    manifest = json.loads((dist / "manifest.json").read_text())
    assert [entry["artifact"] for entry in manifest["programs"]] == [
        "us-az-snap-fy-2026.compiled.json"
    ]


def test_a_refused_preflight_leaves_an_existing_dist_untouched(tmp_path, monkeypatch, toolchain):
    root = tmp_path / "rulespec-us"
    write_spec(root, "programs/us-az/snap/fy-2026.yaml", "us-az/snap", "2026-01")
    dist = root / "dist"
    dist.mkdir(parents=True)
    (dist / "us-az-snap-fy-2026.compiled.json").write_text("{}\n")
    (dist / "manifest.json").write_text('{"programs": []}\n')
    # An engine whose loader contract disagrees with the builder is refused
    # before anything is built.
    monkeypatch.setattr(
        bpa,
        "engine_capabilities",
        lambda engine: {"artifact_format_version": bpa.EXPECTED_ARTIFACT_SCHEMA_VERSION + 1},
    )

    assert run_main(monkeypatch, root) == 2

    assert sorted(p.name for p in dist.iterdir()) == [
        "manifest.json",
        "us-az-snap-fy-2026.compiled.json",
    ]
    assert toolchain.composed == []


def test_check_mode_leaves_an_existing_dist_untouched(tmp_path, monkeypatch, toolchain):
    root = tmp_path / "rulespec-us"
    write_spec(root, "programs/us-az/snap/fy-2026.yaml", "us-az/snap", "2026-01")
    dist = tmp_path / "out"
    dist.mkdir()
    (dist / "us-az-snap.compiled.json").write_text("{}\n")

    assert run_main(monkeypatch, root, "--check", "--dist", str(dist)) == 0

    assert sorted(p.name for p in dist.iterdir()) == ["us-az-snap.compiled.json"]


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
