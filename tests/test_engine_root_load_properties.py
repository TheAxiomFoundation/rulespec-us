"""Property-based tests for the engine root-load gate (tools/engine_root_load.py).

Invariants, for every input:

1. Baseline round trip: parse(render(S)) == S, and render is canonical
   (sorted, idempotent), so the committed file has exactly one spelling.
2. The gate passes iff the observed failures equal the baseline and, when a
   protected base baseline is given, every failing (surface, module) in the
   baseline was already failing in the base.
3. Monotonicity: an unlisted failure always fails the gate; a listed module
   that stops failing always fails the gate; with an existing protected base
   baseline and unchanged engine pin, a newly failing module always fails it;
   a listed module changing class alone never does.
4. Classification ignores machine-specific prefixes: the class of an engine
   message does not depend on where the checkout or scratch directory lives.

Hypothesis is not installed in the shared validate workflow's pytest leg, so
these skip there; the engine-root-load workflow installs it and runs them.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, given, settings, strategies as st  # noqa: E402

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "engine_root_load.py"
_spec = importlib.util.spec_from_file_location("engine_root_load", TOOL_PATH)
erl = importlib.util.module_from_spec(_spec)
sys.modules["engine_root_load"] = erl
_spec.loader.exec_module(erl)

segment = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789-.: "), min_size=1, max_size=12
).filter(lambda s: s.strip() == s and s not in {".", ".."})
module_paths = st.builds(
    lambda jurisdiction, root, parts: f"{jurisdiction}/{root}/{'/'.join(parts)}.yaml",
    st.sampled_from(["us", "us-ca", "us-ny", "us-dc"]),
    st.sampled_from(["legislation", "policies", "regulations", "statutes"]),
    st.lists(segment, min_size=1, max_size=4),
).filter(lambda path: not path.endswith(".test.yaml"))
failures = st.builds(
    erl.Failure,
    st.sampled_from(erl.SURFACES),
    st.sampled_from(sorted(erl.KNOWN_CLASSES)),
    module_paths,
)
failure_sets = st.sets(failures, max_size=30)

# These check semantics, not performance. Shared-runner load must not turn a
# valid example or its filtered input generation into a timing failure.
semantic_properties = settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])


@semantic_properties
@given(failure_sets)
def test_baseline_round_trip(entries):
    text = erl.render_baseline(entries)
    assert erl.parse_baseline(text) == entries
    assert erl.render_baseline(erl.parse_baseline(text)) == text
    body = [line for line in text.splitlines() if not line.startswith("#")]
    assert body == sorted(body)


def _keys(entries):
    return {(entry.surface, entry.module) for entry in entries}


@semantic_properties
@given(failure_sets, failure_sets, st.one_of(st.none(), failure_sets))
def test_gate_passes_iff_equal_and_shrinking(observed, baseline, base):
    verdict = erl.compare(observed, baseline, base)
    expected = observed == baseline and (base is None or _keys(baseline) <= _keys(base))
    assert verdict.ok == expected


@semantic_properties
@given(failure_sets.filter(bool), st.text(alphabet="0123456789abcdef", min_size=40, max_size=40))
def test_baseline_introduction_differs_from_existing_empty_baseline(entries, pin):
    toolchain = f'[workflow_toolchain]\naxiom_rules_engine_ref = "{pin}"\n'
    with (
        patch.object(erl, "git_show", side_effect=[toolchain, None, toolchain, ""]),
        patch.object(Path, "read_text", return_value=toolchain),
    ):
        introduced = erl.read_base_baseline(Path("rulespec-us"), "protected-base")
        existing = erl.read_base_baseline(Path("rulespec-us"), "protected-base")
    assert introduced is None
    assert erl.compare(entries, entries, introduced).ok
    assert existing == set()
    verdict = erl.compare(entries, entries, existing)
    assert not verdict.ok and verdict.added == entries


@semantic_properties
@given(failure_sets, failures)
def test_unlisted_failure_always_fails(baseline, extra):
    if extra in baseline:
        return
    verdict = erl.compare(baseline | {extra}, baseline, baseline)
    assert not verdict.ok and verdict.new == {extra}


@semantic_properties
@given(failure_sets.filter(bool), st.data())
def test_fixed_but_listed_module_always_fails(baseline, data):
    fixed = data.draw(st.sampled_from(sorted(baseline)))
    verdict = erl.compare(baseline - {fixed}, baseline, baseline)
    assert not verdict.ok and verdict.stale == {fixed}


@semantic_properties
@given(failure_sets, failures)
def test_newly_failing_module_always_fails(base, extra):
    if (extra.surface, extra.module) in _keys(base):
        return
    grown = base | {extra}
    verdict = erl.compare(grown, grown, base)
    assert not verdict.ok and verdict.added == {extra}


@semantic_properties
@given(failure_sets.filter(bool), st.data())
def test_class_change_of_listed_module_passes(base, data):
    entry = data.draw(st.sampled_from(sorted(base)))
    new_class = data.draw(st.sampled_from(sorted(erl.KNOWN_CLASSES)))
    changed = erl.Failure(entry.surface, new_class, entry.module)
    rest = {e for e in base if (e.surface, e.module) != (entry.surface, entry.module)}
    current = rest | {changed}
    assert erl.compare(current, current, base).ok


prefixes = st.builds(
    lambda parts: "/" + "/".join(parts),
    st.lists(st.text(alphabet="abcdefghij-_", min_size=1, max_size=8), min_size=1, max_size=5),
)
engine_messages = st.sampled_from(
    [
        "RuleSpec module `{p}/us/a.yaml` declares removed plural `corpus_citation_paths`; x",
        "failed to load RuleSpec module `{p}/us/a.yaml`: yaml parse error: "
        "module.source_verification: unknown field `values`, expected one of `a`",
        "atomic RuleSpec module `{p}/us/a.yaml` must not declare module.kind; `composition`",
        "invalid filesystem RuleSpec path `{p}/us-la/statutes/47:32.yaml`: bad",
        "RuleSpec import `us:a#b` in `us:c` could not be resolved",
        "unknown derived dependency `a` referenced from `{p}/b`",
    ]
)


@semantic_properties
@given(engine_messages, prefixes, prefixes)
def test_classification_ignores_machine_prefixes(template, first, second):
    one = erl.normalize_error(template.format(p=first), first)
    two = erl.normalize_error(template.format(p=second), second)
    assert one == two
    assert erl.classify(template.format(p=first)) == erl.classify(one)
