"""Tests for the provision -> rules reverse-index generator.

These run in the repository's pytest leg (see the org validate-rulespec
workflow, which installs pytest + pyyaml and runs ``tests/``). They cover the
generator's parsing of both grounding sites, prove that the index is derivable
from the current YAML, and assert that no copy of it is tracked in Git.

The index used to be a tracked file with a freshness check. Every encoding pull
request then had to edit the same file, so each merge made every other open
pull request stale or conflicting. It is now generated on demand (see
``generate_reverse_index.py``), and these tests keep it that way.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

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
            "source_verification": {
                "corpus_citation_path": "us/statute/26/32",
                "corpus_citation_paths": [
                    "us/statute/26/32",
                    " us/statute/26/63 ",
                ],
            },
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
    assert refs["us/statute/26/63"] == {gen.MODULE_REFERENCE}
    assert refs["us/statute/26/152/c"] == {gen.PROOF_ATOM_REFERENCE}


def test_citation_paths_ignores_blank_and_non_string():
    payload = {
        "module": {
            "source_verification": {
                "corpus_citation_path": "  ",
                "corpus_citation_paths": ["", 123],
            }
        },
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


def test_repository_index_is_derivable_and_canonical():
    """The generator must run on the real tree and emit a canonical index.

    This replaces the old "committed copy is fresh" check: the pull request
    proves the index can be derived from its own YAML, and nothing has to be
    committed.
    """
    index = gen.build_index(REPO_ROOT)
    rendered = gen.render_index(index)
    assert rendered.endswith("\n")
    parsed = json.loads(rendered)
    assert set(parsed) == {"schema", "description", "provisions"}
    assert parsed["schema"] == "axiom.rulespec.provisions_to_rules/v1"
    provisions = parsed["provisions"]
    assert provisions, "the repository grounds no module to any corpus citation path"
    assert list(provisions) == sorted(provisions)
    assert index["counts"]["provisions"] == len(provisions)
    assert index["counts"]["edges"] == sum(len(entries) for entries in provisions.values())
    for citation, entries in provisions.items():
        assert citation == citation.strip() and citation
        modules = [entry["module"] for entry in entries]
        assert modules == sorted(set(modules)), citation
        for entry in entries:
            assert set(entry) == {"module", "via"}
            assert entry["via"] == sorted(set(entry["via"]))
            assert set(entry["via"]) <= {gen.MODULE_REFERENCE, gen.PROOF_ATOM_REFERENCE}
            module_path = REPO_ROOT / entry["module"]
            assert gen.is_jurisdiction_dir(entry["module"].split("/", 1)[0])
            assert module_path.is_file(), entry["module"]


def _tracked_paths(*pathspecs: str) -> list[str] | None:
    """Return tracked paths matching ``pathspecs``, or None outside a Git checkout."""
    try:
        inside = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if inside.returncode != 0 or Path(inside.stdout.strip()).resolve() != REPO_ROOT.resolve():
        return None
    listed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z", "--", *pathspecs],
        capture_output=True,
        text=True,
        check=True,
    )
    return [path for path in listed.stdout.split("\0") if path]


def test_reverse_index_is_not_tracked():
    """Nothing under ``.axiom/index/`` may be tracked.

    A tracked index is a shared file that every encoding pull request must
    rewrite, which makes open pull requests invalidate each other. The shared
    validation workflow also treats ``.axiom/index/`` as derived metadata that
    cannot change what a shard validates, so that directory must stay empty in
    Git. If this fails on your branch, run
    ``git rm -r --cached .axiom/index`` and commit; do not regenerate and commit.
    """
    tracked = _tracked_paths(".axiom/index")
    if tracked is None:
        pytest.skip("not a Git checkout of this repository")
    assert tracked == [], (
        f"{', '.join(tracked)} is tracked. The reverse index is generated on "
        "demand and must not be committed; run `git rm -r --cached .axiom/index`."
    )


def test_reverse_index_directory_is_git_ignored():
    tracked = _tracked_paths(".gitignore")
    if tracked is None:
        pytest.skip("not a Git checkout of this repository")
    ignored = subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "check-ignore",
            "-q",
            "--no-index",
            gen.INDEX_RELATIVE_PATH.as_posix(),
        ],
        check=False,
    )
    assert ignored.returncode == 0, (
        f"{gen.INDEX_RELATIVE_PATH.as_posix()} must be git-ignored so a locally "
        "generated copy never dirties a checkout or lands in a commit."
    )


def test_cli_writes_and_checks_an_explicit_output(tmp_path, capsys):
    root = tmp_path / "repo"
    _write(
        root / "us" / "statutes" / "a.yaml",
        "module:\n  source_verification:\n    corpus_citation_path: us/statute/26/a\n",
    )
    output = tmp_path / "out" / "index.json"
    assert gen.main(["--repo-root", str(root), "--output", str(output)]) == 0
    assert output.read_text(encoding="utf-8") == gen.render_index(gen.build_index(root))
    assert not (root / gen.INDEX_RELATIVE_PATH).exists()
    assert gen.main(["--repo-root", str(root), "--output", str(output), "--check"]) == 0
    _write(
        root / "us" / "statutes" / "b.yaml",
        "module:\n  source_verification:\n    corpus_citation_path: us/statute/26/b\n",
    )
    assert gen.main(["--repo-root", str(root), "--output", str(output), "--check"]) == 1
    assert "stale or absent" in capsys.readouterr().err
    # The default location is the git-ignored path under the repository root.
    assert gen.main(["--repo-root", str(root), "--check"]) == 1
    assert gen.main(["--repo-root", str(root)]) == 0
    assert gen.main(["--repo-root", str(root), "--check"]) == 0


def test_render_index_omits_counts_but_build_reports_them(tmp_path):
    """Counts stay available to humans via build_index, absent from the file."""
    (tmp_path / "us" / "statutes").mkdir(parents=True)
    _write(
        tmp_path / "us" / "statutes" / "a.yaml",
        "module:\n  source_verification:\n    corpus_citation_path: us/statute/26/a\n",
    )
    index = gen.build_index(tmp_path)
    # build_index still surfaces counts for the CLI summary and callers.
    assert index["counts"]["modules"] == 1
    # ... but they are not serialized into the generated file.
    parsed = json.loads(gen.render_index(index))
    assert "counts" not in parsed
    assert parsed["schema"] == "axiom.rulespec.provisions_to_rules/v1"
    assert "us/statute/26/a" in parsed["provisions"]
