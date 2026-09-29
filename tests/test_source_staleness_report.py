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
    _write(
        root / "us/programs/spec.yaml",
        _module(f"  source_verification:\n    source_sha256: {SHA_A}\n"),
    )
    _write(
        root / "us/venv/lib/x.yaml",
        _module(f"  source_verification:\n    source_sha256: {SHA_A}\n"),
    )
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


def _encoder_output(root: Path, entries: list[tuple[str, str, str]], total: int) -> str:
    lines = []
    for path, pinned, current in entries:
        lines += [f"STALE {root / path}", f"  pinned  {pinned}", f"  current {current}"]
    lines.append(f"{len(entries)} of {total} pinned module(s) are stale.")
    return "\n".join(lines) + "\n"


def test_parse_encoder_findings_and_scan_completion(tmp_path: Path):
    output = _encoder_output(
        tmp_path, [("us/a.yaml", SHA_A, SHA_B), ("us/b.yaml", "<missing>", ssr.NOT_FOUND)], 3
    )
    assert ssr.parse_encoder_findings(output, tmp_path) == {
        "us/a.yaml": (SHA_A, SHA_B),
        "us/b.yaml": ("<missing>", ssr.NOT_FOUND),
    }
    assert ssr.scan_completed(_verdict(1, output))
    assert ssr.scan_completed(_verdict(0, "All 3 pinned module(s) match corpus release 'r'.\n"))
    assert ssr.scan_completed(_verdict(0, f"No RuleSpec modules found under {tmp_path}.\n"))
    assert not ssr.scan_completed(_verdict(1, SCAN_REFUSAL))
    assert not ssr.scan_completed(_verdict(1, RELEASE_REFUSAL))
    assert not ssr.scan_completed(_verdict(0, ""))


def test_differential_agrees_and_disagrees(tmp_path: Path):
    results = [
        ssr.PinResult("us/match.yaml", "c", "match", SHA_A, SHA_A),
        ssr.PinResult("us/stale.yaml", "c", "stale", SHA_A, SHA_B),
        ssr.PinResult("us/gone.yaml", "c", "unresolved", SHA_A, None, "gone"),
        ssr.PinResult("us-ca/x.yaml", "c", "stale", SHA_A, SHA_B),
    ]
    agreeing = _encoder_output(
        tmp_path,
        [
            ("us/stale.yaml", SHA_A, SHA_B),
            ("us/gone.yaml", SHA_A, ssr.NOT_FOUND),
            ("us/unpinned.yaml", "<missing>", ssr.NOT_FOUND),
        ],
        4,
    )
    verdicts = [_verdict(1, agreeing, "us"), _verdict(1, SCAN_REFUSAL, "us-ca")]
    assert ssr.differential(verdicts, results, tmp_path) == (["us"], [])

    disagreeing = _encoder_output(
        tmp_path,
        [
            ("us/match.yaml", SHA_A, SHA_B),
            ("us/stale.yaml", SHA_A, SHA_A.replace("c", "d")),
            ("us/extra.yaml", SHA_B, SHA_A),
        ],
        4,
    )
    compared, disagreements = ssr.differential([_verdict(1, disagreeing, "us")], results, tmp_path)
    assert compared == ["us"]
    assert [item.split(":")[0] for item in disagreements] == [
        "us/extra.yaml",
        "us/gone.yaml",
        "us/match.yaml",
        "us/stale.yaml",
    ]
    assert ssr.overall_exit_status(results[:1], [], disagreements) == ssr.EXIT_FINDINGS


def test_main_turns_a_crash_into_a_harness_error(tmp_path: Path, monkeypatch):
    def crash(args):
        raise OSError("disk went away")

    monkeypatch.setattr(ssr, "_run", crash)
    report = tmp_path / "report.md"
    status = ssr.main(
        ["--rulespec-root", str(tmp_path), "--corpus-path", str(tmp_path),
         "--report", str(report), "--json", str(tmp_path / "report.json")]
    )
    assert status == ssr.EXIT_HARNESS_ERROR
    assert "OSError: disk went away" in report.read_text()


def test_missing_provisions_hint(tmp_path: Path):
    import json

    corpus = tmp_path / "axiom-corpus"
    assert ssr.missing_provisions_hint(corpus) == ""
    release = corpus / "releases/r/abc.json"
    release.parent.mkdir(parents=True)
    artifacts = [
        {"artifact_class": "provisions", "path": "data/corpus/provisions/us/statute/v.jsonl"},
        {"artifact_class": "sources", "path": "data/corpus/sources/x.html"},
    ]
    release.write_text(json.dumps({"content": {"artifacts": artifacts}}))
    hint = ssr.missing_provisions_hint(corpus)
    assert "1 of 1 provisions artifact(s)" in hint and "axiom-encode#1742" in hint
    assert "corpus-locks" not in hint
    (corpus / ".axiom/corpus-locks").mkdir(parents=True)
    assert "corpus-locks" in ssr.missing_provisions_hint(corpus)
    placed = corpus / "data/corpus/provisions/us/statute/v.jsonl"
    placed.parent.mkdir(parents=True)
    placed.write_text("{}\n")
    assert ssr.missing_provisions_hint(corpus) == ""


def test_summary_line():
    results = [
        ssr.PinResult("a", "c", "match", SHA_A, SHA_A),
        ssr.PinResult("b", "c", "stale", SHA_A, SHA_B),
    ]
    line = ssr.summary_line(results, [_verdict(1, SCAN_REFUSAL)], [], [])
    assert line == (
        "2 pins: 1 match, 1 stale, 0 unresolved, 0 invalid; encoder verdict clean in "
        "0 of 1 roots; differential compared 0 roots, 0 disagreements"
    )


class _FakeEncoder:
    """Stand-in for the axiom_encode functions _run imports, for end-to-end tests."""

    def __init__(
        self,
        corpus: Path,
        *,
        good_key: str,
        refusals: dict[str, int],
        digest: str,
        raises: dict[str, int] | None = None,
    ):
        import contextlib
        import json
        import types

        self.active_key = None
        self.calls: dict[str, int] = {}
        artifact = types.SimpleNamespace(
            artifact_class="provisions", path="data/corpus/provisions/us/statute/v.jsonl"
        )
        release_object = corpus / "releases/r/abc.json"
        release_object.parent.mkdir(parents=True, exist_ok=True)
        release_object.write_text(
            json.dumps(
                {
                    "content": {
                        "git": {"commit": "c" * 40},
                        "artifacts": [
                            {"artifact_class": artifact.artifact_class, "path": artifact.path}
                        ],
                    }
                }
            )
        )
        release = types.SimpleNamespace(
            name="r", content_sha256=SHA_A, artifacts=[artifact], root=corpus,
            release_object_path=release_object,
        )

        @contextlib.contextmanager
        def verification(key):
            self.active_key = key
            try:
                yield
            finally:
                self.active_key = None

        def load(repo_root, corpus_root):
            if self.active_key != good_key:
                raise ValueError("release object signature is invalid")
            return release

        def run_check(argv):
            root = Path(argv[1]).name
            self.calls[root] = self.calls.get(root, 0) + 1
            if self.calls[root] <= (raises or {}).get(root, 0):
                raise OSError(f"probe failed on {root}")
            if self.calls[root] <= refusals.get(root, 0):
                print(f"ERROR {argv[1]}")
                print(f"  error   {ssr.TRANSIENT_ROOT_REFUSAL} country checkout")
                return 1
            if root == "us-ca":
                # The real encoder refuses a root holding the retired plural field.
                print(SCAN_REFUSAL, end="")
                return 1
            print("All 1 pinned module(s) match corpus release 'r'.")
            return 0

        self.modules = {
            "axiom_encode": types.ModuleType("axiom_encode"),
            "axiom_encode.source_hash": types.SimpleNamespace(
                resolved_source_verification_block=lambda rel, c: {"source_sha256": digest},
                run_check_source_staleness=run_check,
            ),
            "axiom_encode.toolchain": types.SimpleNamespace(
                load_rulespec_local_corpus_release=load,
                local_corpus_release_verification=verification,
            ),
        }


def _run_main(
    tmp_path, checkout, monkeypatch, *, refusals=None, digest=SHA_A, place=True, raises=None,
    good_key="GOOD",
):
    import json
    import sys

    corpus = tmp_path / "axiom-corpus"
    fake = _FakeEncoder(
        corpus, good_key=good_key, refusals=refusals or {}, digest=digest, raises=raises
    )
    for name, module in fake.modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    if place:
        provisions = corpus / "data/corpus/provisions/us/statute/v.jsonl"
        provisions.parent.mkdir(parents=True, exist_ok=True)
        provisions.write_text("{}\n")
    report, json_path = tmp_path / "report.md", tmp_path / "report.json"
    status = ssr.main(
        ["--rulespec-root", str(checkout), "--corpus-path", str(corpus),
         "--corpus-release-public-key", "RETIRED=BAD",
         "--corpus-release-public-key", "CURRENT=GOOD",
         "--report", str(report), "--json", str(json_path)]
    )
    return status, report.read_text(), json.loads(json_path.read_text()), fake


def test_main_end_to_end_with_a_fake_encoder(tmp_path, checkout, monkeypatch):
    status, report, payload, fake = _run_main(tmp_path, checkout, monkeypatch, refusals={"us": 2})
    # One pin is invalid (the plural field in us-ca), so the report lists findings.
    assert status == ssr.EXIT_FINDINGS
    assert payload["release"]["key_label"] == "CURRENT"
    assert [p["status"] for p in payload["pins"]] == ["match", "invalid"]
    assert fake.calls == {"us": 3, "us-ca": 1}
    assert {v["jurisdiction"]: v["attempts"] for v in payload["encoder_verdicts"]} == {"us": 3, "us-ca": 1}
    assert payload["differential"] == {"compared": ["us"], "disagreements": []}
    assert "harness_error" not in payload and "Harness error" not in report


def test_main_reports_a_root_still_refused_after_retries(tmp_path, checkout, monkeypatch):
    status, report, payload, _ = _run_main(tmp_path, checkout, monkeypatch, refusals={"us-ca": 9})
    assert status == ssr.EXIT_HARNESS_ERROR
    assert payload["stuck_roots"] == ["us-ca"]
    assert report.startswith("# Source staleness report\n\n**Harness error.**")


def test_main_reports_missing_provisions_after_binding(tmp_path, checkout, monkeypatch):
    status, report, payload, _ = _run_main(tmp_path, checkout, monkeypatch, place=False)
    assert status == ssr.EXIT_HARNESS_ERROR
    assert "provisions artifact(s) of `r` are not in the corpus checkout" in report
    assert "harness_error" in payload


def test_main_end_to_end_differential_catches_a_resolver_disagreement(tmp_path, checkout, monkeypatch):
    # The report's resolver says the us pin is stale; the fake encoder says it matches.
    status, report, payload, _ = _run_main(tmp_path, checkout, monkeypatch, digest=SHA_B)
    assert status == ssr.EXIT_FINDINGS
    assert payload["differential"]["disagreements"] == [
        f"us/statutes/1/a.yaml: report says stale (current {SHA_B}), encoder says match"
    ]


def test_main_retries_an_encoder_exception_then_succeeds(tmp_path, checkout, monkeypatch):
    status, _, payload, fake = _run_main(tmp_path, checkout, monkeypatch, raises={"us": 2})
    assert status == ssr.EXIT_FINDINGS
    assert fake.calls["us"] == 3
    assert {v["jurisdiction"]: v["attempts"] for v in payload["encoder_verdicts"]}["us"] == 3


def test_main_reports_an_encoder_exception_that_persists(tmp_path, checkout, monkeypatch):
    status, report, payload, fake = _run_main(tmp_path, checkout, monkeypatch, raises={"us": 9})
    assert status == ssr.EXIT_HARNESS_ERROR
    assert fake.calls["us"] == ssr.ENCODER_ATTEMPTS
    assert "check-source-staleness failed on us after 3 attempts: OSError" in report
    assert "harness_error" in payload


def test_main_reports_every_key_refusal_and_the_provisions_hint(tmp_path, checkout, monkeypatch):
    status, report, payload, _ = _run_main(
        tmp_path, checkout, monkeypatch, good_key="NEITHER", place=False
    )
    assert status == ssr.EXIT_HARNESS_ERROR
    assert "- `RETIRED`: ValueError" in report and "- `CURRENT`: ValueError" in report
    assert "1 of 1 provisions artifact(s) are not in the corpus checkout" in report


def test_missing_provisions_hint_survives_a_malformed_release_object(tmp_path: Path):
    import json

    release = tmp_path / "releases/r/abc.json"
    release.parent.mkdir(parents=True)
    for content in (
        {"artifacts": [1, {"artifact_class": "provisions", "path": 3}]},
        {"artifacts": None},
        [],
    ):
        release.write_text(json.dumps({"content": content}))
        assert isinstance(ssr.missing_provisions_hint(tmp_path), str)
    release.write_text("not json")
    assert ssr.missing_provisions_hint(tmp_path) == ""
