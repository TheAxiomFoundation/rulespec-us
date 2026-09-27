"""Tests for tools/migrate_source_verification.py, the #1354 codemod.

Example cases run in the repository's pytest leg; property-based tests of the
same function live in test_migrate_source_verification_properties.py.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "migrate_source_verification.py"
_spec = importlib.util.spec_from_file_location("migrate_source_verification", TOOL_PATH)
msv = importlib.util.module_from_spec(_spec)
sys.modules["migrate_source_verification"] = msv
_spec.loader.exec_module(msv)


def test_own_citation_candidates_follow_the_encoder_layout():
    assert "us/statute/26/59" in msv.own_citation_candidates("us/statutes/26/59.yaml")
    assert "us/regulation/42/435/558" in msv.own_citation_candidates(
        "us/regulations/42-cfr/435/558.yaml"
    )
    assert "us-ca/regulation/mpp/63-503.132" in msv.own_citation_candidates(
        "us-ca/regulations/mpp/63-503/132.yaml"
    )
    policies = msv.own_citation_candidates(
        "us-ks/policies/khpa/policy-memo/2007-05-01/state-supplemental-payment-program.yaml"
    )
    assert "us-ks/guidance/khpa/policy-memo/2007-05-01/state-supplemental-payment-program" in policies
    assert "us-ks/manual/khpa/policy-memo/2007-05-01/state-supplemental-payment-program" in policies
    assert msv.own_citation_candidates("programs/us/snap/fy-2026.yaml") == set()


def test_choose_singular_prefers_existing_then_own_provision_then_first():
    plural = ["us/statute/26/55/d/4", "us/statute/26/59", "us/statute/26/59/a/1"]
    assert msv.choose_singular("us/statutes/26/59.yaml", None, plural) == "us/statute/26/59"
    assert (
        msv.choose_singular("us/statutes/26/59.yaml", "us/statute/26/55/d/4", plural)
        == "us/statute/26/55/d/4"
    )
    assert msv.choose_singular("us/policies/irs/x.yaml", None, plural) == "us/statute/26/55/d/4"


INDENTED = """\
format: rulespec/v1
# leading comment stays
module:
  proof_validation:
    required: true
  source_verification:
    corpus_citation_paths:
      - us/statute/26/55/d/4
      - 'us/statute/26/59'
      - us/statute/26/59/a/1
    upstream_source_check:
      status: official_parameter_source
      checked_paths:
        - us/statute/26/59
      rationale: |-
        The statute is controlling.
  summary: |-
    Alternative minimum tax.
rules:
  - name: x
    kind: parameter
"""


def test_migrates_indented_plural_to_documents_and_own_singular():
    migrated = msv.migrate_text(INDENTED, "us/statutes/26/59.yaml")
    assert migrated == """\
format: rulespec/v1
# leading comment stays
module:
  proof_validation:
    required: true
  source_documents:
    - corpus_citation_path: us/statute/26/55/d/4
    - corpus_citation_path: 'us/statute/26/59'
    - corpus_citation_path: us/statute/26/59/a/1
  source_verification:
    corpus_citation_path: 'us/statute/26/59'
    upstream_source_check:
      status: official_parameter_source
      checked_paths:
        - us/statute/26/59
      rationale: |-
        The statute is controlling.
  summary: |-
    Alternative minimum tax.
rules:
  - name: x
    kind: parameter
"""
    assert msv.migrate_text(migrated, "us/statutes/26/59.yaml") is None


FLUSH = """\
format: rulespec/v1
module:
  kind: composition
  source_verification:
    corpus_citation_paths:
    - us/rulemaking/federal-register/2022-02-09/2022-02906/page-3
    - us/statute/hts/9903.82.02
    upstream_source_check:
      status: composed_from_supplied_current_authority
rules: []
"""


def test_keeps_a_flush_list_style_flush():
    migrated = msv.migrate_text(FLUSH, "us/policies/cbp/us-tariff-schedule/generated/ch01/ch01.yaml")
    assert migrated == """\
format: rulespec/v1
module:
  kind: composition
  source_documents:
  - corpus_citation_path: us/rulemaking/federal-register/2022-02-09/2022-02906/page-3
  - corpus_citation_path: us/statute/hts/9903.82.02
  source_verification:
    corpus_citation_path: us/rulemaking/federal-register/2022-02-09/2022-02906/page-3
    upstream_source_check:
      status: composed_from_supplied_current_authority
rules: []
"""


VALUES = """\
format: rulespec/v1
module:
  source_verification:
    upstream_source_check:
      status: official_parameter_source
    corpus_citation_paths:
      - us/guidance/usda/fns/snap-fy2024-cola/page-4
      - us/guidance/usda/fns/snap-fy2024-cola/page-5
    values:
      # source columns merge sizes 1-2
      table:
        1: 198
        3: 198
      limit: 179.66
  summary: x
rules: []
"""


def test_moves_values_with_their_comments_and_keeps_entry_order():
    migrated = msv.migrate_text(VALUES, "us/policies/usda/snap/fy-2024-cola/deductions.yaml")
    assert migrated == """\
format: rulespec/v1
module:
  source_documents:
    - corpus_citation_path: us/guidance/usda/fns/snap-fy2024-cola/page-4
    - corpus_citation_path: us/guidance/usda/fns/snap-fy2024-cola/page-5
  source_verification:
    upstream_source_check:
      status: official_parameter_source
    corpus_citation_path: us/guidance/usda/fns/snap-fy2024-cola/page-4
  source_values:
    # source columns merge sizes 1-2
    table:
      1: 198
      3: 198
    limit: 179.66
  summary: x
rules: []
"""


def test_singular_with_values_moves_only_the_values():
    text = (
        "format: rulespec/v1\nmodule:\n  source_verification:\n"
        "    corpus_citation_path: us/statute/26/25A\n    values:\n      rate: 0.2\n"
        "rules: []\n"
    )
    assert msv.migrate_text(text, "us/statutes/26/25A.yaml") == (
        "format: rulespec/v1\nmodule:\n  source_verification:\n"
        "    corpus_citation_path: us/statute/26/25A\n  source_values:\n    rate: 0.2\n"
        "rules: []\n"
    )


def test_existing_singular_is_kept_and_not_duplicated():
    text = (
        "format: rulespec/v1\nmodule:\n  source_verification:\n"
        "    corpus_citation_path: us/statute/42/416/l\n    corpus_citation_paths:\n"
        "      - us/statute/42/416/l\n      - us/statute/42/416/l/1\nrules: []\n"
    )
    migrated = msv.migrate_text(text, "us/statutes/42/416/l.yaml")
    payload = yaml.safe_load(migrated)
    assert payload["module"]["source_verification"] == {"corpus_citation_path": "us/statute/42/416/l"}
    assert migrated.count("corpus_citation_path: us/statute/42/416/l\n") == 2


def test_modules_without_retired_fields_are_untouched():
    text = "format: rulespec/v1\nmodule:\n  source_verification:\n    corpus_citation_path: us/statute/26/1\nrules: []\n"
    assert msv.migrate_text(text, "us/statutes/26/1.yaml") is None
    assert msv.migrate_text("format: rulespec/v1\nrules: []\n", "us/statutes/26/1.yaml") is None


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        (
            "module:\n  source_verification:\n    corpus_citation_paths: [us/statute/1, us/statute/2]\n",
            "not a block sequence",
        ),
        (
            "module:\n  source_verification:\n    corpus_citation_paths:\n      # why\n      - us/statute/1\n",
            "comment inside",
        ),
        (
            "module:\n  source_documents: []\n  source_verification:\n    corpus_citation_paths:\n      - us/statute/1\n",
            "already declares source_documents",
        ),
        (
            "module: {source_verification: {corpus_citation_paths: [us/statute/1]}}\n",
            "no block-style top-level module",
        ),
    ],
)
def test_refuses_shapes_it_cannot_rewrite_safely(text, problem):
    with pytest.raises(msv.MigrationError, match=problem):
        msv.migrate_text(text, "us/statutes/1.yaml")


def test_expected_payload_is_the_specification():
    payload = yaml.safe_load(VALUES)
    expected = msv.expected_payload(payload, "us/policies/usda/snap/fy-2024-cola/deductions.yaml")
    module = expected["module"]
    assert module["source_verification"] == {
        "upstream_source_check": {"status": "official_parameter_source"},
        "corpus_citation_path": "us/guidance/usda/fns/snap-fy2024-cola/page-4",
    }
    assert module["source_documents"] == [
        {"corpus_citation_path": "us/guidance/usda/fns/snap-fy2024-cola/page-4"},
        {"corpus_citation_path": "us/guidance/usda/fns/snap-fy2024-cola/page-5"},
    ]
    assert module["source_values"] == {"table": {1: 198, 3: 198}, "limit": 179.66}
    assert payload["module"]["source_verification"]["values"]  # input not mutated
