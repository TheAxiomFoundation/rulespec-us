"""Tests for the provision -> rules reverse-index generator.

These run in the repository's pytest leg (see the org validate-rulespec
workflow, which installs pytest + pyyaml and runs ``tests/``). They cover the
generator's parsing of both grounding sites and assert that the committed
``.axiom/index/provisions_to_rules.json`` is in sync with the current YAML.
"""

from __future__ import annotations

import json
from pathlib import Path

import generate_reverse_index as gen

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_is_jurisdiction_dir_matches_convention():
    assert gen.is_jurisdiction_dir("us")
    assert gen.is_jurisdiction_dir("us-ca")
    assert gen.is_jurisdiction_dir("us-dc")
    assert not gen.is_jurisdiction_dir(".axiom")
    assert not gen.is_jurisdiction_dir("programs")
    assert not gen.is_jurisdiction_dir("tests")
    assert not gen.is_jurisdiction_dir("_worktrees")
    assert not gen.is_jurisdiction_dir("US")


def test_citation_paths_collects_module_and_proof_atoms():
    payload = {
        "module": {
            "source_verification": {"corpus_citation_path": "us/statute/26/32"},
        },
        "rules": [
            {
                "metadata": {
                    "proof": {
                        "atoms": [
                            {"source": {"corpus_citation_path": "us/statute/26/32"}},
                            {"source": {"corpus_citation_path": "us/statute/26/152/c"}},
                            {"kind": "import", "import": {"target": "x"}},
                        ]
                    }
                }
            }
        ],
    }
    refs = gen.citation_paths_for_module(payload)
    assert refs["us/statute/26/32"] == {gen.MODULE_REFERENCE, gen.PROOF_ATOM_REFERENCE}
    assert refs["us/statute/26/152/c"] == {gen.PROOF_ATOM_REFERENCE}


def test_citation_paths_ignores_blank_and_non_string():
    payload = {
        "module": {"source_verification": {"corpus_citation_path": "  "}},
        "rules": [
            {"metadata": {"proof": {"atoms": [{"source": {"corpus_citation_path": 123}}]}}}
        ],
    }
    assert gen.citation_paths_for_module(payload) == {}


def test_build_index_is_deterministic_and_counts_edges(tmp_path):
    root = tmp_path
    _write(
        root / "us" / "statutes" / "26" / "a.yaml",
        "module:\n"
        "  source_verification:\n"
        "    corpus_citation_path: us/statute/26/a\n"
        "rules:\n"
        "  - name: r\n"
        "    metadata:\n"
        "      proof:\n"
        "        atoms:\n"
        "          - source:\n"
        "              corpus_citation_path: us/statute/26/shared\n",
    )
    _write(
        root / "us-ca" / "statutes" / "26" / "b.yaml",
        "module:\n"
        "  source_verification:\n"
        "    corpus_citation_path: us/statute/26/shared\n",
    )
    # A companion test file must be ignored.
    _write(root / "us" / "statutes" / "26" / "a.test.yaml", "cases: []\n")
    # A non-jurisdiction directory must be ignored.
    _write(
        root / "programs" / "x.yaml",
        "module:\n  source_verification:\n    corpus_citation_path: us/statute/99/z\n",
    )

    index = gen.build_index(root)
    assert index["counts"] == {"provisions": 2, "edges": 3, "modules": 2}
    shared = index["provisions"]["us/statute/26/shared"]
    assert [entry["module"] for entry in shared] == [
        "us-ca/statutes/26/b.yaml",
        "us/statutes/26/a.yaml",
    ]
    # us/statute/99/z under programs/ must not appear.
    assert "us/statute/99/z" not in index["provisions"]
    # Rendering is stable across runs.
    assert gen.render_index(index) == gen.render_index(gen.build_index(root))


def test_committed_index_is_up_to_date():
    """The checked-in index must match a fresh generation of the repo."""
    index = gen.build_index(REPO_ROOT)
    rendered = gen.render_index(index)
    committed_path = REPO_ROOT / gen.INDEX_RELATIVE_PATH
    assert committed_path.exists(), f"{gen.INDEX_RELATIVE_PATH} is missing"
    committed = committed_path.read_text(encoding="utf-8")
    assert committed == rendered, (
        f"{gen.INDEX_RELATIVE_PATH.as_posix()} is stale; run "
        "`python tests/generate_reverse_index.py` and commit the result."
    )
    # The committed file must be valid JSON with the declared schema.
    parsed = json.loads(committed)
    assert parsed["schema"] == "axiom.rulespec.provisions_to_rules/v1"
