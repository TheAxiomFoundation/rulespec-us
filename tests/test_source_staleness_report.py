"""Tests for the report-only source-staleness report.

These run in the repository's pytest leg and in the source-staleness workflow.
The encoder is injected as a resolver callable, so no corpus checkout is
needed. Property tests live in test_source_staleness_report_properties.py.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import source_staleness_report as ssr

SHA_A = hashlib.sha256(b"a").hexdigest()
SHA_B = hashlib.sha256(b"b").hexdigest()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _module(verification: str) -> str:
    return f"module:\n  summary: x\n{verification}rules: []\n"


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    root = tmp_path / "rulespec-us"
    _write(
        root / "us/statutes/1/a.yaml",
        _module(
            "  source_verification:\n"
            "    corpus_citation_path: us/statute/1/a\n"
            f"    source_sha256: {SHA_A}\n"
        ),
    )
    _write(
        root / "us/statutes/1/a.test.yaml",
        _module(f"  source_verification:\n    source_sha256: {SHA_B}\n"),
    )
    _write(
        root / "us/statutes/1/b.yaml",
        _module("  source_verification:\n    corpus_citation_path: us/statute/1/b\n"),
    )
    _write(root / "us/statutes/1/c.yaml", _module(""))
    _write(root / "us/statutes/1/list.yaml", "- not a module\n")
    _write(root / "us/statutes/1/broken.yaml", "module: [unclosed\n")
    _write(
        root / "us-ca/policies/p.yml",
        _module(
            "  source_verification:\n"
            "    corpus_citation_paths: [us-ca/policy/p]\n"
            f"    source_sha256: {SHA_B}\n"
        ),
    )
    _write(
        root / "us/_axiom/hidden.yaml",
        _module(f"  source_verification:\n    source_sha256: {SHA_A}\n"),
    )
    _write(root / "programs/x.yaml", _module(f"  source_verification:\n    source_sha256: {SHA_A}\n"))
    _write(root / "tests/t.yaml", "module: {}\n")
    (root / ".axiom").mkdir()
    return root


def test_jurisdiction_roots_follow_the_country_rule(checkout: Path):
    (checkout / "us-new-york-city").mkdir()
    (checkout / "USX").mkdir()
    (checkout / "uk").mkdir()
    names = [path.name for path in ssr.jurisdiction_roots(checkout)]
    assert names == ["us", "us-ca", "us-new-york-city"]


def test_jurisdiction_roots_reject_a_noncanonical_checkout(tmp_path: Path):
    with pytest.raises(ValueError):
        ssr.jurisdiction_roots(tmp_path)


def test_scan_collects_pins_and_skips_tests_and_ignored_dirs(checkout: Path):
    scan = ssr.scan_modules(checkout, ssr.jurisdiction_roots(checkout))
    assert scan.yaml_files == 6
    assert scan.modules == 4
    assert scan.grounded == 3
    assert scan.unpinned == 1
    assert [pin.path for pin in scan.pins] == ["us/statutes/1/a.yaml", "us-ca/policies/p.yml"]
    assert scan.pins[0] == ssr.Pin("us/statutes/1/a.yaml", "us/statute/1/a", SHA_A)
    assert scan.pins[1].has_plural_citation_field
    assert scan.pins[1].citation_path is None
    assert [path for path, _ in scan.unreadable] == ["us/statutes/1/broken.yaml"]


def _resolver(mapping: dict[str, object]):
    def resolve(citation: str) -> str:
        value = mapping[citation]
        if isinstance(value, BaseException):
            raise value
        return value

    return resolve


class _FakeResolutionError(ValueError):
    """Stands in for the encoder's CorpusResolutionError (a ValueError)."""


@pytest.mark.parametrize(
    ("pin", "mapping", "status"),
    [
        (ssr.Pin("m", "c", SHA_A), {"c": SHA_A}, "match"),
        (ssr.Pin("m", "c", SHA_A), {"c": SHA_B}, "stale"),
        (ssr.Pin("m", "c", SHA_A), {"c": _FakeResolutionError("gone")}, "unresolved"),
        (ssr.Pin("m", "c", SHA_A.upper()), {"c": SHA_A}, "invalid"),
        (ssr.Pin("m", "c", None), {"c": SHA_A}, "invalid"),
        (ssr.Pin("m", "c", 7), {"c": SHA_A}, "invalid"),
        (ssr.Pin("m", None, SHA_A), {}, "invalid"),
        (ssr.Pin("m", "c", SHA_A, has_plural_citation_field=True), {"c": SHA_A}, "invalid"),
    ],
)
def test_check_pin_classifies(pin, mapping, status):
    result = ssr.check_pin(pin, _resolver(mapping))
    assert result.status == status
    if status in {"match", "stale"}:
        assert result.current_sha == mapping["c"]
    else:
        assert result.current_sha is None
        assert result.detail


def test_check_pin_propagates_unexpected_resolver_failures():
    with pytest.raises(RuntimeError):
        ssr.check_pin(ssr.Pin("m", "c", SHA_A), _resolver({"c": RuntimeError("bug")}))


def _verdict(status: int, output: str, root: str = "us") -> ssr.EncoderVerdict:
    return ssr.EncoderVerdict(root, status, output)


SCAN_REFUSAL = (
    "ERROR /w/rulespec-us/us/p.yaml\n"
    "  error   retired corpus_citation_paths field is not supported: "
    "$.module.source_verification.corpus_citation_paths\n"
)
RELEASE_REFUSAL = "ERROR corpus release: RuleSpecToolchainError: A protected signing broker is required\n"
FLAGGED = (
    "STALE /w/rulespec-us/us/a.yaml\n  pinned  <missing>\n  current <provision text not found>\n"
    "1 of 2 pinned module(s) are stale.\n"
)


def test_verdict_reasons_group_without_locations():
    assert (
        ssr._verdict_reason(_verdict(1, SCAN_REFUSAL))
        == "scan refused: retired corpus_citation_paths field is not supported"
    )
    assert ssr._verdict_reason(_verdict(1, RELEASE_REFUSAL)) == (
        "corpus release refused: RuleSpecToolchainError"
    )
    assert ssr._verdict_reason(_verdict(1, FLAGGED)) == "flags unpinned or stale modules"
    assert _verdict(1, FLAGGED).headline == "1 of 2 pinned module(s) are stale."
    assert _verdict(1, SCAN_REFUSAL).headline.startswith("ERROR /w/rulespec-us/us/p.yaml | error")
    assert _verdict(0, "").headline == "(no output)"


def test_exit_status():
    match = ssr.PinResult("m", "c", "match", SHA_A, SHA_A)
    stale = ssr.PinResult("m", "c", "stale", SHA_A, SHA_B)
    clean = _verdict(0, "All 1 pinned module(s) match corpus release 'r'.\n")
    assert ssr.overall_exit_status([match], [clean]) == ssr.EXIT_CLEAN
    assert ssr.overall_exit_status([match, stale], [clean]) == ssr.EXIT_FINDINGS
    assert ssr.overall_exit_status([match], [clean, _verdict(1, SCAN_REFUSAL)]) == ssr.EXIT_FINDINGS
    assert ssr.overall_exit_status([], []) == ssr.EXIT_CLEAN


RELEASE = {
    "name": "us-rulespec-x",
    "content_sha256": SHA_A,
    "commit": "0" * 40,
    "key_label": "AXIOM_CORPUS_RELEASE_PUBLIC_KEY",
    "encoder_ref": "b" * 40,
}


def test_render_report_lists_findings_and_escapes_cells(checkout: Path):
    scan = ssr.scan_modules(checkout, ssr.jurisdiction_roots(checkout))
    results = [
        ssr.PinResult("a|b.yaml", "c", "stale", SHA_A, SHA_B),
        ssr.PinResult("m.yaml", "c", "match", SHA_A, SHA_A),
    ]
    report = ssr.render_report(
        release=RELEASE,
        scan=scan,
        pin_results=results,
        verdicts=[_verdict(0, "ok\n", "us"), _verdict(1, SCAN_REFUSAL, "us-ca")],
    )
    assert "| match | 1 |" in report and "| stale | 1 |" in report
    assert "a\\|b.yaml" in report
    assert "m.yaml" not in report
    assert "- Clean: 1 of 2 jurisdiction roots" in report
    assert "| scan refused: retired corpus_citation_paths field is not supported | 1 |" in report
    assert "us/statutes/1/broken.yaml" in report


def test_main_reports_a_harness_error_without_keys(tmp_path: Path, checkout: Path):
    report = tmp_path / "report.md"
    json_path = tmp_path / "report.json"
    status = ssr.main(
        [
            "--rulespec-root",
            str(checkout),
            "--corpus-path",
            str(tmp_path),
            "--report",
            str(report),
            "--json",
            str(json_path),
        ]
    )
    assert status == ssr.EXIT_HARNESS_ERROR
    assert "could not be produced" in report.read_text()
    assert "harness_error" in json_path.read_text()


def test_labeled_key_parsing():
    assert ssr._parse_labeled_key("LABEL=abc=") == ("LABEL", "abc=")
    for bad in ("", "LABEL", "=abc", "LABEL="):
        with pytest.raises(Exception):
            ssr._parse_labeled_key(bad)
