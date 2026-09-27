"""Property-based tests for the engine root-load gate (tools/engine_root_load.py).

Invariants, for every input:

1. Baseline round trip: parse(render(S)) == S, and render is canonical
   (sorted, idempotent), so the committed file has exactly one spelling.
2. The gate passes iff the observed failures equal the baseline and, when a
   protected base baseline is given, the baseline is a subset of it.
3. Monotonicity: an unlisted failure always fails the gate; a listed module
   that stops failing always fails the gate; an added line always fails it.
4. Classification ignores machine-specific prefixes: the class of an engine
   message does not depend on where the checkout or scratch directory lives.

Hypothesis is not installed in the shared validate workflow's pytest leg, so
these skip there; the engine-root-load workflow installs it and runs them.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, strategies as st  # noqa: E402

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


@given(failure_sets)
def test_baseline_round_trip(entries):
    text = erl.render_baseline(entries)
    assert erl.parse_baseline(text) == entries
    assert erl.render_baseline(erl.parse_baseline(text)) == text


@given(failure_sets, failure_sets, st.one_of(st.none(), failure_sets))
def test_gate_passes_iff_equal_and_shrinking(observed, baseline, base):
    verdict = erl.compare(observed, baseline, base)
    expected = observed == baseline and (base is None or baseline <= base)
    assert verdict.ok == expected


@given(failure_sets, failures)
def test_unlisted_failure_always_fails(baseline, extra):
    if extra in baseline:
        return
    verdict = erl.compare(baseline | {extra}, baseline, baseline)
    assert not verdict.ok and verdict.new == {extra}


@given(failure_sets.filter(bool), st.data())
def test_fixed_but_listed_module_always_fails(baseline, data):
    fixed = data.draw(st.sampled_from(sorted(baseline)))
    verdict = erl.compare(baseline - {fixed}, baseline, baseline)
    assert not verdict.ok and verdict.stale == {fixed}


@given(failure_sets, failures)
def test_added_line_always_fails(base, extra):
    if extra in base:
        return
    grown = base | {extra}
    verdict = erl.compare(grown, grown, base)
    assert not verdict.ok and verdict.added == {extra}


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


@given(engine_messages, prefixes, prefixes)
def test_classification_ignores_machine_prefixes(template, first, second):
    one = erl.normalize_error(template.format(p=first), first)
    two = erl.normalize_error(template.format(p=second), second)
    assert one == two
    assert erl.classify(template.format(p=first)) == erl.classify(one)
