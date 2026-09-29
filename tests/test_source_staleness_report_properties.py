"""Property tests for the report-only source-staleness report.

They need Hypothesis, which the source-staleness workflow installs; the
repository's pytest leg skips this module when Hypothesis is absent.

Invariants, checked for every input Hypothesis generates:

1. ``check_pins`` returns exactly one result per pin, in order, each with a
   status from ``PIN_STATUSES``.
2. A pin is ``match`` iff its pin is a canonical digest, it has a singular
   citation and no plural field, and the resolver returns exactly that digest.
3. ``stale`` carries the resolver's digest, and it differs from the pin.
4. The exit status is clean iff every pin matches, every verdict is 0, and
   there are no disagreements.
5. ``render_report`` is deterministic and lists every non-match.
6. ``differential`` finds no disagreement when the encoder output is built
   from the same pin statuses, and exactly one when one entry is changed.
"""

from __future__ import annotations

import hashlib

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

import source_staleness_report as ssr  # noqa: E402

SHA_A = hashlib.sha256(b"a").hexdigest()
SHA_B = hashlib.sha256(b"b").hexdigest()
RELEASE = {
    "name": "us-rulespec-x",
    "content_sha256": SHA_A,
    "commit": "0" * 40,
    "key_label": "AXIOM_CORPUS_RELEASE_PUBLIC_KEY",
    "encoder_ref": "b" * 40,
}


class _FakeResolutionError(ValueError):
    """Stands in for the encoder's CorpusResolutionError (a ValueError)."""


digests = st.sampled_from([SHA_A, SHA_B, SHA_A.upper(), "abc", ""]) | st.none() | st.integers()
citations = st.sampled_from(["c1", "c2", "c3"]) | st.none()
outcomes = st.sampled_from([SHA_A, SHA_B, "error"])
pins = st.lists(
    st.builds(
        ssr.Pin,
        path=st.text(min_size=1, max_size=12),
        citation_path=citations,
        pinned_sha=digests,
        has_plural_citation_field=st.booleans(),
    ),
    max_size=25,
)


@given(pins=pins, table=st.fixed_dictionaries({c: outcomes for c in ("c1", "c2", "c3")}))
def test_property_classification(pins, table):
    def resolve(citation: str) -> str:
        if table[citation] == "error":
            raise _FakeResolutionError(citation)
        return table[citation]

    results = ssr.check_pins(pins, resolve)
    assert len(results) == len(pins)
    for pin, result in zip(pins, results):
        assert result.path == pin.path
        assert result.status in ssr.PIN_STATUSES
        valid = (
            isinstance(pin.pinned_sha, str)
            and ssr.SHA256_RE.fullmatch(pin.pinned_sha) is not None
            and pin.citation_path is not None
            and not pin.has_plural_citation_field
        )
        resolved = table.get(pin.citation_path) if valid else None
        assert (result.status == "match") == (valid and resolved == pin.pinned_sha)
        if result.status == "stale":
            assert result.current_sha == resolved != pin.pinned_sha
        if not valid:
            assert result.status == "invalid"
        elif resolved == "error":
            assert result.status == "unresolved"


@given(
    statuses=st.lists(st.sampled_from(ssr.PIN_STATUSES), max_size=10),
    verdict_codes=st.lists(st.sampled_from([0, 1]), max_size=5),
    disagreements=st.lists(st.text(min_size=1, max_size=5), max_size=2),
)
def test_property_exit_status(statuses, verdict_codes, disagreements):
    results = [ssr.PinResult(f"m{i}", "c", s, SHA_A) for i, s in enumerate(statuses)]
    verdicts = [ssr.EncoderVerdict("us", code, "") for code in verdict_codes]
    clean = (
        all(s == "match" for s in statuses)
        and all(c == 0 for c in verdict_codes)
        and not disagreements
    )
    expected = ssr.EXIT_CLEAN if clean else ssr.EXIT_FINDINGS
    assert ssr.overall_exit_status(results, verdicts, disagreements) == expected


@given(statuses=st.lists(st.sampled_from(ssr.PIN_STATUSES), max_size=40))
def test_property_render_lists_every_finding(statuses):
    results = [
        ssr.PinResult(f"module-{i}.yaml", "c", s, SHA_A, SHA_B) for i, s in enumerate(statuses)
    ]
    kwargs = dict(release=RELEASE, scan=ssr.ScanResult(), pin_results=results, verdicts=[])
    report = ssr.render_report(**kwargs)
    assert report == ssr.render_report(**kwargs)
    for index, status in enumerate(statuses):
        listed = f"| module-{index}.yaml |" in report
        assert listed == (status != "match")


def _encoder_output_for(root, results, unpinned):
    """Render what the encoder prints for these pin statuses (see source_hash.py)."""
    lines = []
    for item in results:
        if item.status == "match":
            continue
        current = item.current_sha if item.status == "stale" else ssr.NOT_FOUND
        lines += [f"STALE {root / item.path}", f"  pinned  {item.pinned_sha}", f"  current {current}"]
    for index in range(unpinned):
        lines += [f"STALE {root / f'us/unpinned-{index}.yaml'}", "  pinned  <missing>",
                  f"  current {ssr.NOT_FOUND}"]
    flagged = sum(1 for item in results if item.status != "match") + unpinned
    lines.append(f"{flagged} of {len(results) + unpinned} pinned module(s) are stale.")
    return "\n".join(lines) + "\n"


@given(
    statuses=st.lists(st.sampled_from(ssr.PIN_STATUSES), min_size=1, max_size=15),
    unpinned=st.integers(min_value=0, max_value=3),
    victim=st.integers(min_value=0),
)
def test_property_differential(tmp_path_factory, statuses, unpinned, victim):
    root = tmp_path_factory.getbasetemp() / "rulespec-us"
    results = [
        ssr.PinResult(
            f"us/m{i}.yaml", "c", s, SHA_A, SHA_B if s == "stale" else (SHA_A if s == "match" else None)
        )
        for i, s in enumerate(statuses)
    ]
    verdict = ssr.EncoderVerdict("us", 1, _encoder_output_for(root, results, unpinned))
    assert ssr.differential([verdict], results, root) == (["us"], [])

    index = victim % len(results)
    changed = list(results)
    item = changed[index]
    if item.status == "match":
        flipped = ssr.PinResult(item.path, "c", "stale", SHA_A, SHA_B)
    else:
        flipped = ssr.PinResult(item.path, "c", "match", SHA_A, SHA_A)
    changed[index] = flipped
    compared, disagreements = ssr.differential([verdict], changed, root)
    assert compared == ["us"]
    assert len(disagreements) == 1 and disagreements[0].startswith(item.path + ":")
