"""Tests for tools/engine_root_load.py, the pinned-engine root-load gate.

These run in the repository's pytest leg without an engine build. They cover
module selection, failure classification, the baseline file format, the gate's
comparison, and the committed baseline's hygiene. The engine run itself is the
engine-root-load workflow; property-based tests of the same logic live in
test_engine_root_load_properties.py.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL_PATH = REPO_ROOT / "tools" / "engine_root_load.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("engine_root_load", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["engine_root_load"] = module
    spec.loader.exec_module(module)
    return module


erl = _load_tool()

PLURAL = (
    "failed to load RuleSpec module `us/statutes/42/402/q.yaml`: RuleSpec module "
    "`us:statutes/42/416/l` declares removed plural `corpus_citation_paths`; every "
    "source/proof node must declare exactly one singular `corpus_citation_path`"
)
VALUES = (
    "failed to load RuleSpec module `us/policies/usda/snap/fy-2026-cola/deductions.yaml`: "
    "yaml parse error: module.source_verification: unknown field `values`, expected one "
    "of `corpus_citation_path`, `source_sha256`, `upstream_source_check` at line 20 column 5"
)
KIND = (
    "failed to load RuleSpec module `us/policies/cbp/us-tariff-duty/composition.yaml`: "
    "atomic RuleSpec module `us/policies/cbp/us-tariff-duty/composition.yaml` must not "
    "declare module.kind; `composition` is accepted only by the composed-program surface"
)
PATH = (
    "failed to load RuleSpec module `us-la/statutes/47:32.yaml`: invalid filesystem "
    "RuleSpec path `us-la/statutes/47:32.yaml`: segment is not canonical"
)
IMPORT = (
    "failed to load RuleSpec module `us-la/policies/income_tax/pilot_liability_pipeline.yaml`: "
    "RuleSpec import `us-la:statutes/47:32#individual_income_tax_rate` in "
    "`us-la:policies/income_tax/pilot_liability_pipeline` could not be resolved"
)


def test_select_modules_keeps_atomic_roots_only():
    paths = [
        "us/statutes/26/32.yaml",
        "us/statutes/26/32.test.yaml",
        "us-ca/regulations/mpp/63-410/321.yaml",
        "us-co/policies/cdhs/snap/fy-2026-benefit-calculation.yaml",
        "us-xx/legislation/act/1.yaml",
        "us-mo/manual/dss/snap/1115-000-00/block-1.yaml",
        "programs/us-co/snap/fy-2026.yaml",
        "tools/known-engine-load-failures.txt",
        "us/policies/usitc/us-tariff-duty/lines/generated/GENERATED-MANIFEST.json",
        "us/statutes/26/32.yml",
        ".axiom/encoding-manifests/us/statutes/26/32.json",
    ]
    assert erl.select_modules(paths) == [
        "us-ca/regulations/mpp/63-410/321.yaml",
        "us-co/policies/cdhs/snap/fy-2026-benefit-calculation.yaml",
        "us-xx/legislation/act/1.yaml",
        "us/statutes/26/32.yaml",
    ]


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        (PLURAL, "plural-corpus-citation-paths"),
        (VALUES, "source-verification-unknown-field"),
        (KIND, "module-kind-on-atomic-surface"),
        (PATH, "invalid-filesystem-path"),
        (IMPORT, "unresolved-import"),
        ("RuleSpec module `x` declares non-canonical corpus_citation_path `a`", "non-canonical-corpus-citation-path"),
        ("invalid composed RuleSpec program `x`: composed output must be outside", "invalid-composed-program"),
        ("yaml parse error: did not find expected key", "yaml-parse"),
        ("unknown derived dependency `a` referenced from `b`", "other"),
        ("", "other"),
    ],
)
def test_classify(message, expected):
    assert erl.classify(message) == expected


def test_classes_are_distinct_and_known():
    names = [name for name, _ in erl.FAILURE_CLASSES]
    assert len(names) == len(set(names))
    assert erl.OTHER not in names
    assert set(names) | {erl.OTHER} == erl.KNOWN_CLASSES


def test_plural_is_classified_before_the_yaml_it_arrives_in():
    # The engine runs the recursive corpus contract before serde, so a plural
    # error never carries "yaml parse error"; a values error always does. The
    # specific classes must still win over the generic yaml-parse class.
    assert erl.classify("yaml parse error: " + VALUES) == "source-verification-unknown-field"


def test_normalize_error_strips_machine_prefixes():
    root = "/home/runner/work/rulespec-us/rulespec-us/rulespec-us"
    composed = "/tmp/engine-root-load-abc/composed"
    message = f"failed to load RuleSpec module `{root}/us/a.yaml`: `{composed}/us/b.yaml`\n  detail"
    assert erl.normalize_error(message, root, composed + "/") == (
        "failed to load RuleSpec module `us/a.yaml`: `us/b.yaml` detail"
    )


def _results(*records):
    return [erl.Result(**record) for record in records]


def test_failures_from_results_ignores_successes():
    results = _results(
        {"module": "us/statutes/26/32.yaml", "surface": "atomic", "ok": True},
        {"module": "us/statutes/42/402/q.yaml", "surface": "atomic", "ok": False, "error": PLURAL},
        {"module": "us/policies/x.yaml", "surface": "composed", "ok": False, "error": VALUES},
    )
    assert erl.failures_from_results(results) == {
        erl.Failure("atomic", "plural-corpus-citation-paths", "us/statutes/42/402/q.yaml"),
        erl.Failure("composed", "source-verification-unknown-field", "us/policies/x.yaml"),
    }


def test_parse_results_rejects_root_error_and_malformed_lines():
    with pytest.raises(SystemExit, match="refused the checkout as a root"):
        erl.parse_results(['{"root_error": "root must be named exactly rulespec-<country>"}'])
    with pytest.raises(SystemExit, match="malformed result"):
        erl.parse_results(['{"module": "us/a.yaml", "surface": "dense", "ok": true}'])
    with pytest.raises(SystemExit, match="malformed result"):
        erl.parse_results(['{"module": "us/a.yaml", "surface": "atomic", "ok": "yes"}'])
    assert erl.parse_results(["", '{"module": "us/a.yaml", "surface": "atomic", "ok": true}']) == [
        erl.Result("us/a.yaml", "atomic", True)
    ]


def test_baseline_round_trip_is_sorted_and_canonical():
    entries = {
        erl.Failure("composed", "plural-corpus-citation-paths", "us/policies/b.yaml"),
        erl.Failure("atomic", "invalid-filesystem-path", "us-nh/regulations/he-w-700/He-W 704/04.yaml"),
        erl.Failure("atomic", "plural-corpus-citation-paths", "us/policies/b.yaml"),
    }
    text = erl.render_baseline(entries)
    assert erl.parse_baseline(text) == entries
    assert erl.render_baseline(erl.parse_baseline(text)) == text
    body = [line for line in text.splitlines() if not line.startswith("#")]
    assert body == sorted(body)


@pytest.mark.parametrize(
    ("line", "problem"),
    [
        ("atomic plural-corpus-citation-paths us/a.yaml", "must be"),
        ("dense\tplural-corpus-citation-paths\tus/a.yaml", "unknown surface"),
        ("atomic\tsomething-new\tus/a.yaml", "unknown class"),
        ("atomic\tother\tprograms/us/a.yaml", "not an atomic module path"),
        ("atomic\tother\tus/a.yaml\textra", "must be"),
    ],
)
def test_parse_baseline_rejects_malformed_lines(line, problem):
    with pytest.raises(ValueError, match=problem):
        erl.parse_baseline(line + "\n")


def test_parse_baseline_rejects_duplicates():
    line = "atomic\tother\tus/statutes/a.yaml\n"
    with pytest.raises(ValueError, match="duplicates"):
        erl.parse_baseline(line + line)


def test_compare_reports_new_stale_and_added():
    a = erl.Failure("atomic", "plural-corpus-citation-paths", "us/statutes/a.yaml")
    b = erl.Failure("atomic", "module-kind-on-atomic-surface", "us/policies/b.yaml")
    c = erl.Failure("composed", "plural-corpus-citation-paths", "us/policies/b.yaml")

    assert erl.compare({a, b}, {a, b}, {a, b, c}).ok
    assert erl.compare({a, b}, {a, b}, None).ok

    verdict = erl.compare({a, c}, {a, b}, {a, b})
    assert verdict.new == {c} and verdict.stale == {b} and not verdict.added
    assert not verdict.ok

    verdict = erl.compare({a, b, c}, {a, b, c}, {a, b})
    assert verdict.added == {c} and not verdict.ok


def test_compare_treats_a_changed_class_as_new_and_stale():
    before = erl.Failure("atomic", "plural-corpus-citation-paths", "us/statutes/a.yaml")
    after = erl.Failure("atomic", "unresolved-import", "us/statutes/a.yaml")
    verdict = erl.compare({after}, {before}, {before})
    assert verdict.new == {after} and verdict.stale == {before}


def test_check_coverage_requires_one_atomic_result_per_module():
    modules = ["us/a.yaml", "us/b.yaml"]
    results = _results(
        {"module": "us/a.yaml", "surface": "atomic", "ok": True},
        {"module": "us/a.yaml", "surface": "composed", "ok": True},
        {"module": "us/c.yaml", "surface": "atomic", "ok": True},
        {"module": "us/c.yaml", "surface": "atomic", "ok": True},
    )
    problems = erl.check_coverage(results, modules)
    assert "no atomic result for us/b.yaml" in problems
    assert "2 atomic results for us/c.yaml" in problems
    assert "result for unselected module us/c.yaml" in problems
    assert not erl.check_coverage(results[:1], ["us/a.yaml"])


def test_engine_pin_reads_the_workflow_toolchain():
    text = '[workflow_toolchain]\naxiom_rules_engine_ref = "af6e"\n'
    assert erl.engine_pin(text) == "af6e"
    assert erl.engine_pin(None) is None
    assert erl.engine_pin("[other]\n") is None


def test_harness_uses_the_engine_compile_entry_points():
    source = erl.HARNESS_SOURCE
    assert "CanonicalRuleSpecRoots::new" in source
    assert "CompiledProgramArtifact::from_rulespec_file" in source
    assert "CompiledProgramArtifact::from_composed_rulespec_file" in source
    assert "ModuleKindOnAtomicSurface" in source


def _tracked_files() -> set[str]:
    listing = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"], check=True, capture_output=True
    ).stdout.decode("utf-8")
    return {path for path in listing.split("\0") if path}


def test_committed_baseline_is_canonical_and_names_tracked_modules():
    path = REPO_ROOT / erl.BASELINE_RELATIVE_PATH
    text = path.read_text(encoding="utf-8")
    entries = erl.parse_baseline(text)
    assert erl.render_baseline(entries) == text, "regenerate with engine_root_load.py baseline"
    tracked = _tracked_files()
    missing = sorted(entry.module for entry in entries if entry.module not in tracked)
    assert not missing, f"baseline names modules that are not tracked: {missing[:10]}"
    composed_only = {e.module for e in entries if e.surface == "composed"} - {
        e.module
        for e in entries
        if e.surface == "atomic" and e.failure_class == "module-kind-on-atomic-surface"
    }
    assert not composed_only, (
        "a composed-surface entry needs its module's atomic kind failure: "
        f"{sorted(composed_only)[:10]}"
    )
