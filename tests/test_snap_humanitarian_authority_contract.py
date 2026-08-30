"""Source and execution contracts for the humanitarian SNAP authority layers.

The optional corpus check is lexical/structural proof validation only. It is
not a substitute for a protected signed corpus-release validation. Set
AXIOM_PROOF_CORPUS_ROOT and AXIOM_RULES_ENGINE_BINARY to run both integration
checks against real local Axiom dependencies.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
NEW_MODULES = (
    "us/statutes/7/2015/f.yaml",
    "us/statutes/8/1612/a/2.yaml",
    "us/statutes/8/1612/a/2-dates.yaml",
    "us/statutes/8/1613/a.yaml",
    "us/statutes/8/1613/a-dates.yaml",
    "us/statutes/8/1613/b/1.yaml",
    "us/statutes/8/1641/c.yaml",
    "us/statutes/8/1641/qualified-alien.yaml",
    "us/policies/usda/snap/obbb-alien-eligibility-memo.yaml",
    "us/policies/usda/snap/obbb-alien-eligibility-qanda-1.yaml",
    "us/policies/usda/snap/obbb-alien-eligibility-qanda-1-dates.yaml",
    "us/policies/usda/snap/obbb-alien-eligibility.yaml",
)
SNAPSHOT_MODULES = tuple(
    path for path in NEW_MODULES if path.startswith("us/statutes/8/")
)


def _load(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def _atoms(module: dict):
    for rule in module["rules"]:
        for atom in rule.get("metadata", {}).get("proof", {}).get("atoms", []):
            yield rule["name"], atom


def _import_path(target: str) -> str:
    return target.split("#", 1)[0].replace("us:", "us/", 1) + ".yaml"


def _source_snapshot_key(item: dict) -> tuple:
    return (
        item.get("source_as_of", ""),
        item.get("expression_date", ""),
        item.get("version", ""),
    )


@pytest.mark.parametrize("path", SNAPSHOT_MODULES)
def test_modern_title_8_rules_have_an_explicit_supported_snapshot(path):
    module = _load(path)
    verification = module["module"]["source_verification"]
    assert verification["supported_snapshot_from"] == "2025-07-04"
    assert verification["validity_basis"] == (
        "supported_post_obbb_snapshot_not_original_enactment_date"
    )
    assert (
        verification["unsupported_period_behavior"]
        == "missing_dated_snapshot_support_parameter"
    )
    assert verification["historical_amendment_versions_encoded"] is False
    assert all(
        version["effective_from"] == "2025-07-04"
        for rule in module["rules"]
        for version in rule.get("versions", [])
    )


@pytest.mark.parametrize(
    "path", ("us/statutes/8/1612/a/2.yaml", "us/statutes/8/1613/a.yaml")
)
def test_clock_consumers_import_subsections_b_and_c(path):
    imports = _load(path)["imports"]
    assert (
        "us:statutes/8/1641/qualified-alien#qualified_alien_under_subsections_b_or_c"
        in imports
    )
    assert "us:statutes/8/1641/b#qualified_alien" not in imports


def test_no_generic_battered_classification_substitutes_for_subsection_c_findings():
    module = _load("us/statutes/8/1641/c.yaml")
    formulas = "\n".join(rule["versions"][0]["formula"] for rule in module["rules"])
    assert "member_is_battered_alien" not in formulas
    for relation in ("alien", "child", "parent"):
        assert (
            "benefits_agency_finds_substantial_connection_to_need_from_"
            f"{relation}_battery_or_cruelty" in formulas
        )
    assert "and not alien_actively_participated_in_child_battery_or_cruelty" in formulas
    assert "and not subsection_c_abuser_household_exclusion_applies" in formulas


def test_exact_date_proofs_do_not_stitch_the_preamble_to_numbered_clauses():
    module = _load("us/statutes/8/1612/a/2-dates.yaml")
    excerpts = [
        atom["source"]["excerpt"]
        for _, atom in _atoms(module)
        if "excerpt" in atom.get("source", {})
    ]
    assert len(excerpts) == 5
    assert all(excerpt.startswith("an alien") for excerpt in excerpts)
    assert all(
        "until 7 years after the date an alien" not in excerpt for excerpt in excerpts
    )


def test_new_import_proof_hashes_bind_actual_local_module_bytes():
    checked = 0
    for path in NEW_MODULES:
        for name, atom in _atoms(_load(path)):
            imported = atom.get("import")
            if imported is None or imported["hash"] == "sha256:local":
                continue
            target = ROOT / _import_path(imported["target"])
            actual = "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
            assert imported["hash"] == actual, (path, name, imported["target"])
            checked += 1
    assert checked >= 30


def test_signed_predecessor_artifacts_are_unchanged():
    originals = {
        "us/regulations/7-cfr/273/4.yaml": "c404469290002f5e2e5d5dc92686b36f994d924da97d9c31c118979ef5c5c3da",
        "us/statutes/8/1641/b.yaml": "7a98dbc72ac610e0af2df7e37d61bb8b24bfc2b8da7219ac5cdfa1f3af8986bc",
    }
    for path, expected in originals.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected


def test_dense_composition_has_no_date_rules_and_no_claim_of_as_known_selection():
    pending = ["us/policies/usda/snap/obbb-alien-eligibility.yaml"]
    seen = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        module = _load(path)
        assert all(rule.get("dtype") != "Date" for rule in module["rules"])
        pending.extend(_import_path(target) for target in module.get("imports", []))
    verification = _load(NEW_MODULES[-1])["module"]["source_verification"]
    assert (
        verification["bitemporal_runtime_selection"][
            "assessment_date_selects_known_authority"
        ]
        is False
    )
    assert verification["supersedes_or_clarifies"]["relation"] == "clarifies"
    assert verification["authority_edges"][0]["text_formally_amended"] is False


def test_all_new_proof_excerpts_match_actual_local_corpus_text():
    corpus_root = os.environ.get("AXIOM_PROOF_CORPUS_ROOT")
    if not corpus_root:
        pytest.skip("AXIOM_PROOF_CORPUS_ROOT is not configured")
    validator = pytest.importorskip("axiom_encode.harness.proof_validator")
    modules = {path: _load(path) for path in NEW_MODULES}
    citations = {
        atom["source"]["corpus_citation_path"]
        for module in modules.values()
        for _, atom in _atoms(module)
        if "source" in atom
    }
    provisions = Path(corpus_root) / "data/corpus/provisions/us"
    command = ["rg", "-l", "-F", "--glob", "*.jsonl"]
    for citation in sorted(citations):
        command.extend(["-e", json.dumps(citation)])
    command.append(str(provisions))
    located = subprocess.run(command, check=True, capture_output=True, text=True)
    source_records = {}
    for filename in sorted(located.stdout.splitlines()):
        with Path(filename).open(encoding="utf-8") as records:
            for line in records:
                record = json.loads(line)
                citation = record.get("citation_path")
                if citation not in citations:
                    continue
                old = source_records.get(citation)
                if old is None or _source_snapshot_key(record) >= _source_snapshot_key(
                    old
                ):
                    source_records[citation] = record
    assert citations <= source_records.keys()
    source_texts = {key: record["body"] for key, record in source_records.items()}
    checked = 0
    for path, module in modules.items():
        for name, atom in _atoms(module):
            source = atom.get("source", {})
            for field in ("excerpt", "quote"):
                if field not in source:
                    continue
                assert validator._source_contains_proof_evidence(
                    source_text=source_texts[source["corpus_citation_path"]],
                    evidence_text=source[field],
                ), (path, name, source[field])
                checked += 1
        result = validator.validate_rulespec_proofs(
            (ROOT / path).read_text(encoding="utf-8"), source_texts=source_texts
        )
        assert result.passed, (path, result.issues)
    print(f"Matched {checked} exact proof excerpts across {len(modules)} modules")


@pytest.mark.parametrize(
    ("path", "output"),
    (
        ("us/statutes/8/1612/a/2.yaml", "cofa_lawful_resident_exception_applies"),
        (
            "us/statutes/8/1613/a.yaml",
            "qualified_alien_within_subsection_a_five_year_period_before_exceptions",
        ),
        (
            "us/statutes/8/1641/qualified-alien.yaml",
            "qualified_alien_under_subsections_b_or_c",
        ),
        (
            "us/policies/usda/snap/obbb-alien-eligibility.yaml",
            "snap_obbb_status_and_waiting_period_eligible",
        ),
    ),
)
@pytest.mark.parametrize("mode", ("explain", "fast"))
@pytest.mark.parametrize(
    ("start", "end"), (("2023-06-01", "2023-07-01"), ("2025-07-01", "2025-08-01"))
)
def test_real_engine_rejects_unsupported_pre_snapshot_period(
    path, output, mode, start, end, tmp_path
):
    binary = os.environ.get("AXIOM_RULES_ENGINE_BINARY")
    if not binary:
        pytest.skip("AXIOM_RULES_ENGINE_BINARY is not configured")
    environment = dict(
        os.environ,
        AXIOM_RULESPEC_REPO_ROOTS=str(ROOT),
        AXIOM_RULESPEC_REPO_ROOTS_EXCLUSIVE="1",
    )
    artifact = tmp_path / "authority-snapshot.compiled.json"
    compiled = subprocess.run(
        [
            binary,
            "compile",
            "--program",
            str(ROOT / path),
            "--exclusive-rulespec-roots",
            "--output",
            str(artifact),
        ],
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert compiled.returncode == 0, compiled.stderr
    request = {
        "mode": mode,
        "dataset": {"inputs": [], "relations": []},
        "queries": [
            {
                "entity_id": "person",
                "period": {"period_kind": "month", "start": start, "end": end},
                "outputs": [
                    path.removesuffix(".yaml").replace("us/", "us:", 1) + "#" + output
                ],
            }
        ],
    }
    result = subprocess.run(
        [binary, "run-compiled", "--artifact", str(artifact)],
        input=json.dumps(request),
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode != 0
    assert f"snapshot_supported` has no value for key `0` at {start}" in result.stderr


@pytest.mark.parametrize("mode", ("explain", "fast"))
def test_real_engine_allows_first_complete_supported_month(mode, tmp_path):
    binary = os.environ.get("AXIOM_RULES_ENGINE_BINARY")
    if not binary:
        pytest.skip("AXIOM_RULES_ENGINE_BINARY is not configured")
    environment = dict(
        os.environ,
        AXIOM_RULESPEC_REPO_ROOTS=str(ROOT),
        AXIOM_RULESPEC_REPO_ROOTS_EXCLUSIVE="1",
    )
    artifact = tmp_path / "authority-snapshot.compiled.json"
    compiled = subprocess.run(
        [
            binary,
            "compile",
            "--program",
            str(ROOT / "us/statutes/8/1612/a/2.yaml"),
            "--exclusive-rulespec-roots",
            "--output",
            str(artifact),
        ],
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert compiled.returncode == 0, compiled.stderr
    period = {"period_kind": "month", "start": "2025-08-01", "end": "2025-09-01"}
    request = {
        "mode": mode,
        "dataset": {
            "inputs": [
                {
                    "entity": "Person",
                    "entity_id": "person",
                    "name": "us:statutes/8/1612/a/2#input.individual_lawfully_resides_in_united_states_in_accordance_with_compact_of_free_association_referred_to_in_section_1612_b_2_G",
                    "interval": {"start": period["start"], "end": period["end"]},
                    "value": {"kind": "bool", "value": True},
                }
            ]
        },
        "queries": [
            {
                "entity_id": "person",
                "period": period,
                "outputs": [
                    "us:statutes/8/1612/a/2#cofa_lawful_resident_exception_applies"
                ],
            }
        ],
    }
    result = subprocess.run(
        [binary, "run-compiled", "--artifact", str(artifact)],
        input=json.dumps(request),
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    outputs = json.loads(result.stdout)["results"][0]["outputs"]
    assert [output["outcome"] for output in outputs.values()] == ["holds"]
