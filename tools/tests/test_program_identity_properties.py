"""Property-based tests for program identity and artifact naming (#784).

Invariants, for every generated spec tree:

1. Exact refusal. plan_builds refuses a tree iff two specs share
   (jurisdiction, program_id, period), two distinct spec paths join to the
   same case-folded artifact name, or two different (jurisdiction,
   program_id) pairs join to the same case-folded program_key; the error
   lists exactly those groups. A second period of a program is never
   refused on its own.
2. Injective names. On every accepted tree, two specs have the same artifact
   name iff they have the same path, and each name is the hyphen join of the
   path under programs/ without `.yaml`.
3. Stability. The result does not depend on input order, and adding a spec
   to an accepted tree never renames a spec already in it.
4. Period label. period_label is None iff the path under programs/ equals
   the `program:` segments; otherwise it is the path's last segment.
5. Differential against the pre-#784 builder (reimplemented below from
   a9dc38fb0). program_key equals the old artifact name for every spec, and
   every tree the old builder accepted is accepted now unless two of its
   paths join to one name or two of its old names differ only in case (two
   files that overwrite each other on a case-insensitive filesystem).
   Generated `program:` values carry no surrounding whitespace; see 9.
6. Filesystem agreement. discover_specs on a tree written to disk, in any
   creation order and with companion `.test.yaml` files and non-spec YAML
   beside it, returns what plan_builds returns for the specs alone.
7. Manifest compatibility. Every manifest entry has exactly the pre-#784
   keys plus program, program_key and period_label. Every pre-#784 value
   except `artifact` equals what the old builder wrote for the same spec and
   build outputs; `artifact` is the renamed file, and the old one was
   program_key + ".compiled.json".
8. Routing key. On every accepted tree, program_key.casefold() determines
   (jurisdiction, program_id), so (program_key, period) names exactly one
   spec, even ignoring case.
9. Whitespace. Padding every `program:` and `period:` with surrounding
   whitespace never changes the plan: the builder strips both, as
   axiom-compose does.

Most invariants run over two generators: spec_trees, which mixes layouts
freely, and split_key_trees, which splits one hyphenated string into
(jurisdiction, program_id) at different hyphens and in either case. The
second exists because spec_trees rarely produces two programs whose
program_keys coincide while their paths do not collide (about 7 trees in
2,000, against about 300 in 2,000 for split_key_trees).

The tests skip where Hypothesis is not installed; the program-artifacts
builder-tests job installs it from tools/tests/requirements.txt.
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
TOKEN = st.from_regex(r"[aAb1]{1,2}", fullmatch=True)
PERIODS = st.sampled_from(["2026-01", "2026-10", "2026"])
WHITESPACE = st.sampled_from(["", " ", "  ", "\t", " \n"])


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


@st.composite
def split_key_entries(draw):
    """Two to four specs whose programs all split ONE hyphenated string into
    (jurisdiction, program_id): at the same or a different hyphen, in its
    case or swapped, with or without a middle segment, at a period path or
    a chapter path. These are the trees where program_key alone can be
    ambiguous: us-az/snap against us/az-snap, or us-az/snap against
    US-AZ/snap."""
    key = "-".join(draw(st.lists(TOKEN, min_size=2, max_size=4)))
    hyphens = key.count("-")
    # Sometimes every spec is one program (one cut, one case), so the tree
    # is a multi-period program that should be accepted when periods differ.
    one_program = draw(st.booleans())
    fixed = (draw(st.booleans()), draw(st.integers(1, hyphens)))
    entries = []
    for _ in range(draw(st.integers(2, 4))):
        swap, cut = (
            fixed if one_program else (draw(st.booleans()), draw(st.integers(1, hyphens)))
        )
        tokens = (key.swapcase() if swap else key).split("-")
        middle = tuple(draw(st.lists(LOWER_SEGMENT, max_size=1)))
        program = ("-".join(tokens[:cut]), *middle, "-".join(tokens[cut:]))
        if draw(st.booleans()):  # programs/<program...>/<period>.yaml
            parts = program + (draw(MIXED_SEGMENT),)
        else:  # programs/<program...>.yaml
            parts = program
        path = PurePosixPath("programs", *parts[:-1], f"{parts[-1]}.yaml")
        spec = {"program": "/".join(program), "period": draw(PERIODS), "outputs": ["x"]}
        entries.append((path, spec))
    return entries


def first_per_path(entries):
    seen: dict = {}
    for path, spec in entries:
        seen.setdefault(path, spec)
    return list(seen.items())


def split_key_trees():
    """split_key_entries plus up to four unrelated specs, one spec per path."""
    return st.tuples(split_key_entries(), spec_trees(max_size=4)).map(
        lambda pair: first_per_path(pair[0] + pair[1])
    )


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


def expected_ambiguous_keys(tree) -> dict:
    """Case-folded program_keys that more than one (jurisdiction,
    program_id) pair joins to, with every spec path carrying the key."""
    groups: dict = {}
    for path, spec in sorted(tree, key=lambda e: e[0]):
        jurisdiction, program_id, _ = expected_identity(spec)
        groups.setdefault(f"{jurisdiction}-{program_id}".casefold(), []).append(
            (path.as_posix(), (jurisdiction, program_id))
        )
    return {
        key: [path for path, _ in members]
        for key, members in groups.items()
        if len({pair for _, pair in members}) > 1
    }


def expected_problems(tree):
    duplicates = grouped(tree, lambda path, spec: expected_identity(spec))
    collisions = grouped(tree, lambda path, spec: expected_name(path).casefold())
    return duplicates, collisions, expected_ambiguous_keys(tree)


def legacy_names(tree) -> dict[str, str] | None:
    """The pre-#784 naming, reimplemented over in-memory (path, spec) pairs
    from tools/build_program_artifacts.py:63-91 at a9dc38fb0:
    f"{jurisdiction}-{program_id}", and any exact repeat aborts the build.
    Returns None where it aborted."""
    names = {}
    for path, spec in tree:
        segments = [s for s in str(spec["program"]).split("/") if s]
        names[path.as_posix()] = f"{segments[0]}-{segments[-1]}"
    values = list(names.values())
    if any(values.count(name) > 1 for name in values):
        return None
    return names


def refusal(error):
    return ("refused", error.duplicates, error.name_collisions, error.ambiguous_program_keys)


def record_fired_checks(problems) -> None:
    """Record which checks fired, for --hypothesis-show-statistics."""
    names = ("duplicate", "name collision", "ambiguous key")
    fired = [name for name, groups in zip(names, problems) if groups]
    hypothesis.event("refused: " + " + ".join(fired) if fired else "accepted")


def outcome(tree):
    """A comparable summary of plan_builds: the builds, or the refusal."""
    try:
        builds = bpa.plan_builds(tree)
    except bpa.SpecIdentityError as error:
        return refusal(error)
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


def check_exact_refusal(tree):
    problems = expected_problems(tree)
    record_fired_checks(problems)
    result = outcome(tree)
    if any(problems):
        assert result == ("refused", *problems)
    else:
        assert result[0] == "accepted"
        assert len(result[1]) == len(tree)


@settings(max_examples=400, deadline=None)
@given(spec_trees())
def test_refuses_exactly_the_three_clashes(tree):
    check_exact_refusal(tree)


@settings(max_examples=400, deadline=None)
@given(split_key_trees())
def test_refuses_exactly_the_three_clashes_on_split_keys(tree):
    check_exact_refusal(tree)


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
    assert expected_problems(grown) == ({}, {}, {})
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


def check_against_legacy(tree):
    result = outcome(tree)
    legacy = legacy_names(tree)
    if result[0] == "accepted":
        for spec_path, _name, (jurisdiction, program_id, _), _, key, _, _ in result[1]:
            assert key == f"{jurisdiction}-{program_id}"
    if legacy is None:
        return
    if result[0] == "accepted":
        assert {row[0]: row[4] for row in result[1]} == legacy
        return
    # The old builder accepted it, so every old name is distinct, so no
    # (jurisdiction, program_id) repeats and no identity duplicate. What can
    # still refuse it: a hyphen-join name collision, or old names that differ
    # only in case, which overwrote each other on a case-insensitive
    # filesystem.
    hypothesis.event("legacy accepted, now refused")
    _, duplicates, collisions, ambiguous = result
    assert duplicates == {}
    assert collisions or ambiguous
    for key, paths in ambiguous.items():
        old = [legacy[path] for path in paths]
        assert len(set(old)) == len(old)
        assert {name.casefold() for name in old} == {key}


@settings(max_examples=400, deadline=None)
@given(spec_trees())
def test_program_key_is_the_legacy_name_and_legacy_trees_still_build(tree):
    check_against_legacy(tree)


@settings(max_examples=400, deadline=None)
@given(split_key_trees())
def test_program_key_is_the_legacy_name_and_legacy_trees_still_build_on_split_keys(tree):
    check_against_legacy(tree)


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
            discovered = refusal(error)

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


def legacy_entry(path, spec, *, spec_sha256, artifact_sha256, compat, program) -> dict:
    """The pre-#784 manifest entry for one spec, reimplemented from
    tools/build_program_artifacts.py at a9dc38fb0: identity from
    discover_specs (lines 63-91), the entry from build_all (lines 453-470).
    `spec_path` was str(path relative to the root), which is the POSIX form
    on the Linux runner that releases."""
    segments = [s for s in str(spec["program"]).split("/") if s]
    jurisdiction, program_id = segments[0], segments[-1]
    return {
        "jurisdiction": jurisdiction,
        "program_id": program_id,
        "period": str(spec.get("period", "")),
        "spec_path": str(path),
        "spec_sha256": spec_sha256,
        "outputs": [str(o) for o in spec.get("outputs", [])],
        "artifact": f"{jurisdiction}-{program_id}.compiled.json",
        "artifact_sha256": artifact_sha256,
        "compat": compat,
        "counts": {
            "derived": len(program.get("derived", [])),
            "parameters": len(program.get("parameters", [])),
            "relations": len(program.get("relations", [])),
        },
    }


COMPILED_PROGRAMS = st.fixed_dictionaries(
    {
        "derived": st.lists(st.integers(), max_size=3),
        "parameters": st.lists(st.integers(), max_size=3),
        "relations": st.lists(st.integers(), max_size=3),
    }
)


@settings(max_examples=200, deadline=None)
@given(spec_trees(), COMPILED_PROGRAMS)
def test_manifest_entries_match_the_legacy_builder_except_the_file_name(tree, program):
    try:
        builds = bpa.plan_builds(tree)
    except bpa.SpecIdentityError:
        assume(False)
    specs = dict(tree)
    compat = bpa.build_compat("0.1.2", "c" * 40, 2)
    hashes = {"spec_sha256": "d" * 64, "artifact_sha256": "e" * 64}
    for build in builds:
        entry = bpa.manifest_entry(
            build,
            artifact=f"{build.artifact_name}.compiled.json",
            compat=compat,
            program=program,
            **hashes,
        )
        old = legacy_entry(
            PurePosixPath(build.spec_path.as_posix()),
            specs[PurePosixPath(build.spec_path.as_posix())],
            compat=compat,
            program=program,
            **hashes,
        )
        assert set(entry) == set(old) | {"program", "program_key", "period_label"}
        assert set(old) == set(LEGACY_ENTRY_FIELDS)
        for field in LEGACY_ENTRY_FIELDS:
            if field != "artifact":
                assert entry[field] == old[field], field
        assert entry["artifact"] == f"{build.artifact_name}.compiled.json"
        assert old["artifact"] == f"{entry['program_key']}.compiled.json"
        assert entry["program_key"] == f"{build.jurisdiction}-{build.program_id}"
        assert entry["program"] == build.program
        assert entry["period_label"] == build.period_label


# -- 8. Routing key ----------------------------------------------------------


def check_routing_key(tree):
    result = outcome(tree)
    hypothesis.event(result[0])
    if result[0] != "accepted":
        return
    programs: dict = {}
    routes = []
    for _path, _name, (jurisdiction, program_id, period), _p, key, _l, _o in result[1]:
        programs.setdefault(key.casefold(), set()).add((jurisdiction, program_id))
        routes.append((key.casefold(), period))
    assert all(len(pairs) == 1 for pairs in programs.values())
    assert len(set(routes)) == len(routes)


@settings(max_examples=400, deadline=None)
@given(spec_trees())
def test_program_key_names_one_program_on_accepted_trees(tree):
    check_routing_key(tree)


@settings(max_examples=400, deadline=None)
@given(split_key_trees())
def test_program_key_names_one_program_on_accepted_split_key_trees(tree):
    check_routing_key(tree)


# -- 9. Whitespace -----------------------------------------------------------


@settings(max_examples=300, deadline=None)
@given(spec_trees(), st.data())
def test_surrounding_whitespace_never_changes_the_plan(tree, data):
    def pad(value: str) -> str:
        return data.draw(WHITESPACE) + value + data.draw(WHITESPACE)

    padded = [
        (path, dict(spec, program=pad(spec["program"]), period=pad(spec["period"])))
        for path, spec in tree
    ]
    assert outcome(padded) == outcome(tree)
