"""Property-based tests for the #1354 codemod (tools/migrate_source_verification.py).

Invariants, for every generated module:

1. Engine shape: the result has no `corpus_citation_paths` anywhere, and
   `source_verification` holds exactly one `corpus_citation_path`, taken from
   the original citations, plus only other engine fields.
2. Nothing is lost: `source_documents` lists every original plural path in
   order, `source_values` equals the original `values`, and every other part
   of the document parses identically.
3. Byte locality: lines before and after the `module` block are unchanged,
   and every removed line came from `source_verification`.
4. Idempotence: migrating the result again is a no-op.

Hypothesis is not installed in the shared validate workflow's pytest leg, so
these skip there; the engine-root-load workflow installs it and runs them.
"""

from __future__ import annotations

import difflib
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st  # noqa: E402

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "migrate_source_verification.py"
_spec = importlib.util.spec_from_file_location("migrate_source_verification", TOOL_PATH)
msv = importlib.util.module_from_spec(_spec)
sys.modules["migrate_source_verification"] = msv
_spec.loader.exec_module(msv)

segments = st.from_regex(r"[a-z0-9][a-z0-9.\-]{0,6}", fullmatch=True)
citations = st.builds(
    lambda juris, cls, parts: "/".join([juris, cls, *parts]),
    st.sampled_from(["us", "us-ca", "us-ny"]),
    st.sampled_from(["statute", "regulation", "guidance", "manual"]),
    st.lists(segments, min_size=1, max_size=4),
)
module_paths = st.builds(
    lambda juris, root, parts: "/".join([juris, root, *parts]) + ".yaml",
    st.sampled_from(["us", "us-ca", "us-ny"]),
    st.sampled_from(["statutes", "regulations", "policies"]),
    st.lists(segments, min_size=1, max_size=4),
)
keys = st.from_regex(r"[a-z][a-z_]{0,10}", fullmatch=True)
scalars = st.one_of(st.integers(-10_000, 10_000), st.sampled_from([0.2, 179.66, 1.0]))
values = st.dictionaries(
    keys,
    st.one_of(scalars, st.dictionaries(st.integers(1, 9), scalars, min_size=1, max_size=4)),
    min_size=1,
    max_size=4,
)


@st.composite
def modules(draw):
    plural = draw(st.lists(citations, min_size=1, max_size=6, unique=True))
    has_plural = draw(st.booleans())
    has_values = draw(st.booleans()) or not has_plural
    singular = None
    if not has_plural or draw(st.booleans()):
        singular = plural[0]
    flush = draw(st.booleans())
    item_pad = 4 if flush else 6
    entries: list[list[str]] = []
    if singular is not None:
        entries.append([f"    corpus_citation_path: {singular}\n"])
    if has_plural:
        entries.append(["    corpus_citation_paths:\n"] + [f"{' ' * item_pad}- {p}\n" for p in plural])
    if draw(st.booleans()):
        entries.append(
            [
                "    upstream_source_check:\n",
                "      status: official_parameter_source\n",
                "      checked_paths:\n",
                f"{' ' * (item_pad + 2)}- {plural[0]}\n",
                "      rationale: |-\n",
                "        Controlling source.\n",
            ]
        )
    if has_values:
        body = yaml.safe_dump(draw(values), sort_keys=False, default_flow_style=False)
        lines = ["    values:\n"]
        if draw(st.booleans()):
            lines.append("      # source columns merge sizes 1-2\n")
        lines += [f"      {line}\n" for line in body.splitlines()]
        entries.append(lines)
    order = draw(st.permutations(range(len(entries))))
    verification = [line for index in order for line in entries[index]]
    before = draw(st.sampled_from([[], ["  proof_validation:\n", "    required: true\n"]]))
    after = draw(st.sampled_from([[], ["  summary: |-\n", "    A summary.\n", "\n", "    Second paragraph.\n"]]))
    text = (
        "format: rulespec/v1\n# header comment\nmodule:\n"
        + "".join(before)
        + "  source_verification:\n"
        + "".join(verification)
        + "".join(after)
        + "rules:\n  - name: x\n    kind: parameter\n"
    )
    return draw(module_paths), text


@settings(max_examples=300, deadline=None)
@given(modules())
def test_migration_invariants(case):
    module_path, text = case
    original = yaml.safe_load(text)
    migrated = msv.migrate_text(text, module_path)
    assert migrated is not None
    result = yaml.safe_load(migrated)

    # 1. Engine shape.
    assert "corpus_citation_paths" not in migrated
    verification = result["module"]["source_verification"]
    assert set(verification) <= msv.ENGINE_SOURCE_VERIFICATION_FIELDS
    source = original["module"]["source_verification"]
    citations = source.get("corpus_citation_paths") or [source.get("corpus_citation_path")]
    assert verification["corpus_citation_path"] in citations

    # 2. Nothing lost.
    if "corpus_citation_paths" in source:
        assert result["module"]["source_documents"] == [
            {"corpus_citation_path": path} for path in source["corpus_citation_paths"]
        ]
    if "values" in source:
        assert result["module"]["source_values"] == source["values"]
    assert result == msv.expected_payload(original, module_path)
    for key in set(original) - {"module"}:
        assert result[key] == original[key]

    # 3. Byte locality.
    old_lines, new_lines = text.splitlines(), migrated.splitlines()
    module_at = old_lines.index("module:")
    assert new_lines[: module_at + 1] == old_lines[: module_at + 1]
    rules_at = old_lines.index("rules:")
    assert new_lines[new_lines.index("rules:") :] == old_lines[rules_at:]
    sv_start = old_lines.index("  source_verification:")
    removed = [
        line[2:]
        for line in difflib.ndiff(old_lines, new_lines)
        if line.startswith("- ")
    ]
    sv_lines = set(old_lines[sv_start:rules_at])
    assert all(line in sv_lines for line in removed)

    # 4. Idempotence.
    assert msv.migrate_text(migrated, module_path) is None
