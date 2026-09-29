"""Property tests for the report-only source-staleness report.

They need Hypothesis, which the source-staleness workflow installs; the
repository's pytest leg skips this module when Hypothesis is absent.

Invariants, checked for every input Hypothesis generates:

1. ``check_pins`` returns exactly one result per pin, in order, each with a
   status from ``PIN_STATUSES``.
2. A pin is ``match`` iff its pin is a canonical digest, it has a singular
   citation and no plural field, and the resolver returns exactly that digest.
3. ``stale`` carries the resolver's digest, and it differs from the pin.
4. The exit status is clean iff every pin matches and every verdict is 0.
5. ``render_report`` is deterministic and lists every non-match.
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
)
def test_property_exit_status(statuses, verdict_codes):
    results = [ssr.PinResult(f"m{i}", "c", s, SHA_A) for i, s in enumerate(statuses)]
    verdicts = [ssr.EncoderVerdict("us", code, "") for code in verdict_codes]
    clean = all(s == "match" for s in statuses) and all(c == 0 for c in verdict_codes)
    expected = ssr.EXIT_CLEAN if clean else ssr.EXIT_FINDINGS
    assert ssr.overall_exit_status(results, verdicts) == expected


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
