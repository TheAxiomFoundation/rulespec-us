"""Property-based tests for program identity and artifact naming (#784).

Invariants, for every generated spec tree:

1. Exact refusal. plan_builds refuses a tree iff two specs share
   (jurisdiction, program_id, period) or two distinct spec paths join to the
   same case-folded artifact name; the error lists exactly those groups.
   A second period of a program is never refused on its own.
2. Injective names. On every accepted tree, two specs have the same artifact
   name iff they have the same path, and each name is the hyphen join of the
   path under programs/ without `.yaml`.
3. Stability. The result does not depend on input order, and adding a spec
   to an accepted tree never renames a spec already in it.
4. Period label. period_label is None iff the path under programs/ equals
   the `program:` segments; otherwise it is the path's last segment.
5. Differential against the pre-#784 builder. program_key equals the old
   artifact name for every spec, and every tree the old builder accepted is
   accepted now unless two of its paths join to one name. (Generated
   `program:` values carry no surrounding whitespace; the builder strips it,
   as axiom-compose does, where the old builder kept it in the name.)
6. Filesystem agreement. discover_specs on a tree written to disk, in any
   creation order and with companion `.test.yaml` files and non-spec YAML
   beside it, returns what plan_builds returns for the specs alone.
7. Manifest compatibility. Every manifest entry keeps the pre-#784 fields
   with their old values and adds program, program_key and period_label.

The tests skip where Hypothesis is not installed; the program-artifacts
workflow installs it.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path, PurePosixPath

import pytest
import yaml

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import assume, given, settings, strategies as st  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_program_artifacts as bpa  # noqa: E402

# A tiny alphabet with hyphens makes identity duplicates and hyphen-join
# collisions common enough to exercise every branch.
LOWER_SEGMENT = st.from_regex(r"[ab1]{1,2}(-[ab1]{1,2})?", fullmatch=True)
MIXED_SEGMENT = st.from_regex(r"[aAb1]{1,2}(-[aAb1]{1,2})?", fullmatch=True)
PERIODS = st.sampled_from(["2026-01", "2026-10", "2026"])


@st.composite
def spec_entries(draw, segment=MIXED_SEGMENT):
    program = tuple(draw(st.lists(segment, min_size=1, max_size=3)))
    layout = draw(st.sampled_from(["period", "chapter", "free"]))
    if layout == "period":  # programs/<program...>/<period>.yaml
        parts = program + (draw(segment),)
    elif layout == "chapter":  # programs/<program...>.yaml, like ch01
        parts = program
    else:  # anything at all
        parts = tuple(draw(st.lists(segment, min_size=1, max_size=4)))
    path = PurePosixPath("programs", *parts[:-1], f"{parts[-1]}.yaml")
    spec = {"program": "/".join(program), "period": draw(PERIODS), "outputs": ["x"]}
    return path, spec


def spec_trees(segment=MIXED_SEGMENT, max_size=8):
    return st.lists(spec_entries(segment), max_size=max_size, unique_by=lambda e: e[0])


# -- Independent oracles -----------------------------------------------------


def expected_name(path: PurePosixPath) -> str:
    return "-".join(PurePosixPath(*path.parts[1:]).with_suffix("").parts)


def expected_identity(spec: dict) -> tuple[str, str, str]:
    segments = spec["program"].split("/")
    return (segments[0], segments[-1], spec["period"])


def grouped(tree, key) -> dict:
    groups: dict = {}
    for path, spec in sorted(tree, key=lambda e: e[0]):
        groups.setdefault(key(path, spec), []).append(path.as_posix())
    return {k: v for k, v in groups.items() if len(v) > 1}


def expected_problems(tree):
    duplicates = grouped(tree, lambda path, spec: expected_identity(spec))
    collisions = grouped(tree, lambda path, spec: expected_name(path).casefold())
    return duplicates, collisions


def legacy_names(tree) -> dict[str, str] | None:
    """The pre-#784 builder (tools/build_program_artifacts.py:63-91 at
    a9dc38fb0): f"{jurisdiction}-{program_id}", any repeat aborts. Returns
    None where it aborted."""
    names = {}
    for path, spec in tree:
        segments = [s for s in str(spec["program"]).split("/") if s]
        names[path.as_posix()] = f"{segments[0]}-{segments[-1]}"
    values = list(names.values())
    if any(values.count(name) > 1 for name in values):
        return None
    return names


def outcome(tree):
    """A comparable summary of plan_builds: the builds, or the refusal."""
    try:
        builds = bpa.plan_builds(tree)
    except bpa.SpecIdentityError as error:
        return ("refused", error.duplicates, error.name_collisions)
    return (
        "accepted",
        [
            (
                b.spec_path.as_posix(),
                b.artifact_name,
                b.identity,
                b.program,
                b.program_key,
                b.period_label,
                b.outputs,
            )
            for b in builds
        ],
    )


# -- 1. Exact refusal --------------------------------------------------------


@settings(max_examples=400, deadline=None)
@given(spec_trees())
def test_refuses_exactly_identity_duplicates_and_name_collisions(tree):
    duplicates, collisions = expected_problems(tree)
    result = outcome(tree)
    if duplicates or collisions:
        assert result == ("refused", duplicates, collisions)
    else:
        assert result[0] == "accepted"
        assert len(result[1]) == len(tree)


@settings(max_examples=200, deadline=None)
@given(spec_trees(), PERIODS)
def test_a_second_period_alone_is_never_refused(tree, new_period):
    assume(tree)
    path, spec = tree[0]
    assume(outcome(tree)[0] == "accepted")
    # Add another period of the first spec's program under a fresh stem.
    # The stem uses letters outside the generated alphabet, so it is a fresh
    # path whose name cannot collide with any generated one.
    sibling = path.with_name("zz-next-period.yaml")
    added = dict(spec, period=new_period)
    # Only the period is new: no spec in the tree claims it for this program.
    assume(all(expected_identity(other) != expected_identity(added) for _, other in tree))
    grown = tree + [(sibling, added)]
    assert expected_problems(grown) == ({}, {})
    result = outcome(grown)
    assert result[0] == "accepted"
    keys = [row[4] for row in result[1]]
    assert keys.count(f"{expected_identity(spec)[0]}-{expected_identity(spec)[1]}") >= 2


# -- 2. Injective names ------------------------------------------------------


@settings(max_examples=400, deadline=None)
@given(spec_trees())
def test_accepted_trees_have_one_distinct_name_per_path(tree):
    result = outcome(tree)
    assume(result[0] == "accepted")
    rows = result[1]
    assert [row[0] for row in rows] == [p.as_posix() for p, _ in sorted(tree, key=lambda e: e[0])]
    for spec_path, name, *_ in rows:
        assert name == expected_name(PurePosixPath(spec_path))
    for i, a in enumerate(rows):
        for b in rows[i + 1 :]:
            same_path = a[0] == b[0]
            same_name = a[1].casefold() == b[1].casefold()
            assert same_name == same_path


# -- 3. Stability ------------------------------------------------------------


@settings(max_examples=300, deadline=None)
@given(spec_trees(), st.randoms(use_true_random=False))
def test_result_is_independent_of_input_order(tree, rng):
    shuffled = list(tree)
    rng.shuffle(shuffled)
    assert outcome(shuffled) == outcome(tree)
    assert outcome(tree) == outcome(tree)  # rebuild: deterministic


@settings(max_examples=300, deadline=None)
@given(spec_trees(), spec_entries())
def test_adding_a_spec_never_renames_existing_artifacts(tree, extra):
    assume(all(path != extra[0] for path, _ in tree))
    before = outcome(tree)
    after = outcome(tree + [extra])
    assume(before[0] == "accepted" and after[0] == "accepted")
    names_before = {row[0]: row[1] for row in before[1]}
    names_after = {row[0]: row[1] for row in after[1]}
    for spec_path, name in names_before.items():
        assert names_after[spec_path] == name


# -- 4. Period label ---------------------------------------------------------


@settings(max_examples=300, deadline=None)
@given(spec_trees())
def test_period_label_is_the_path_segment_beyond_the_program(tree):
    result = outcome(tree)
    assume(result[0] == "accepted")
    for spec_path, _name, _identity, program, _key, label, _outputs in result[1]:
        parts = PurePosixPath(spec_path).with_suffix("").parts[1:]
        if parts == tuple(program.split("/")):
            assert label is None
        else:
            assert label == parts[-1]


# -- 5. Differential against the pre-#784 builder ----------------------------


@settings(max_examples=400, deadline=None)
@given(spec_trees())
def test_program_key_is_the_legacy_name_and_legacy_trees_still_build(tree):
    result = outcome(tree)
    legacy = legacy_names(tree)
    if result[0] == "accepted":
        for spec_path, _name, (jurisdiction, program_id, _), _, key, _, _ in result[1]:
            assert key == f"{jurisdiction}-{program_id}"
    if legacy is not None:
        # The old builder accepted it, so no (jurisdiction, program_id) repeats,
        # so no identity duplicate: only a hyphen-join collision can refuse it.
        if result[0] == "refused":
            assert result[1] == {} and result[2] != {}
        else:
            assert {row[0]: row[4] for row in result[1]} == legacy


# -- 6. Filesystem agreement -------------------------------------------------


@settings(max_examples=60, deadline=None)
@given(
    spec_trees(segment=LOWER_SEGMENT, max_size=6),
    st.randoms(use_true_random=False),
)
def test_discover_specs_matches_plan_builds_on_disk(tree, rng):
    # Lower-case only: a case-insensitive filesystem cannot hold paths that
    # differ only in case, and that case is covered by the pure tests.
    files = [(path, yaml.safe_dump(spec)) for path, spec in tree]
    # Decoys the builder must ignore: companion tests and non-spec YAML.
    for path, spec in tree:
        files.append((path.with_name(path.stem + ".test.yaml"), yaml.safe_dump(spec)))
    files.append((PurePosixPath("programs/zz-notes.yaml"), yaml.safe_dump({"note": "x"})))
    assume(len({p.as_posix() for p, _ in files}) == len(files))
    rng.shuffle(files)

    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        for path, text in files:
            target = root / path
            if target.exists() or any(parent.is_file() for parent in target.parents):
                return  # a file and a directory share a name; not a real tree
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        try:
            discovered = ("accepted", bpa.discover_specs(root))
        except bpa.SpecIdentityError as error:
            discovered = ("refused", error.duplicates, error.name_collisions)

    expected = outcome(tree)
    if expected[0] == "refused":
        assert discovered == expected
    else:
        assert discovered[0] == "accepted"
        assert [
            (
                b.spec_path.as_posix(),
                b.artifact_name,
                b.identity,
                b.program,
                b.program_key,
                b.period_label,
                b.outputs,
            )
            for b in discovered[1]
        ] == expected[1]


# -- 7. Manifest compatibility -----------------------------------------------

LEGACY_ENTRY_FIELDS = (
    "jurisdiction",
    "program_id",
    "period",
    "spec_path",
    "spec_sha256",
    "outputs",
    "artifact",
    "artifact_sha256",
    "compat",
    "counts",
)


@settings(max_examples=200, deadline=None)
@given(spec_trees())
def test_manifest_entries_keep_legacy_fields_and_add_identity(tree):
    try:
        builds = bpa.plan_builds(tree)
    except bpa.SpecIdentityError:
        assume(False)
    compat = bpa.build_compat("0.1.2", "c" * 40, 2)
    for build in builds:
        entry = bpa.manifest_entry(
            build,
            spec_sha256="d" * 64,
            artifact=f"{build.artifact_name}.compiled.json",
            artifact_sha256="e" * 64,
            compat=compat,
            program={"derived": [1, 2], "parameters": [1], "relations": []},
        )
        assert set(entry) == set(LEGACY_ENTRY_FIELDS) | {"program", "program_key", "period_label"}
        assert entry["jurisdiction"] == build.jurisdiction
        assert entry["program_id"] == build.program_id
        assert entry["period"] == build.period
        assert entry["spec_path"] == build.spec_path.as_posix()
        assert entry["outputs"] == build.outputs
        assert entry["counts"] == {"derived": 2, "parameters": 1, "relations": 0}
        assert entry["program_key"] == f"{build.jurisdiction}-{build.program_id}"
        assert entry["program"] == build.program
        assert entry["period_label"] == build.period_label
