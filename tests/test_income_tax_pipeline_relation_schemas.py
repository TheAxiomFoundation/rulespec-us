"""Static relation-schema contracts for the income-tax pipeline modules.

The axiom-rules engine consumes only ``data_relation.arity`` at runtime; the
declared ``arguments`` vector documents the aggregation direction (which
entity's amounts roll up to which) and is otherwise behaviorally inert, so no
companion fixture can detect a reversed declaration. These contracts make the
declared vectors executable: reversing an argument vector fails this test even
though every runtime companion still passes.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

EXPECTED_RELATION_SCHEMAS = {
    "us/policies/income_tax/salt_deduction_pipeline.yaml": {
        "salt_section_911_individual_of_tax_unit": {
            "arity": 2,
            "arguments": ["TaxUnit", "Person"],
        },
    },
}


def _declared_relations(module_path: Path) -> dict[str, dict]:
    payload = yaml.safe_load(module_path.read_text())
    found: dict[str, dict] = {}
    for rule in payload.get("rules") or []:
        if rule.get("kind") != "data_relation":
            continue
        spec = rule.get("data_relation") or {}
        found[rule["name"]] = {
            "arity": spec.get("arity"),
            "arguments": list(spec.get("arguments") or []),
        }
    return found


def test_income_tax_pipeline_relation_schemas_are_exact() -> None:
    for rel_path, expected in EXPECTED_RELATION_SCHEMAS.items():
        module_path = ROOT / rel_path
        assert module_path.is_file(), f"missing module: {rel_path}"
        declared = _declared_relations(module_path)
        assert declared == expected, (
            f"{rel_path} data_relation schemas drifted from the documented "
            f"aggregation direction: declared {declared!r}, expected "
            f"{expected!r}. The argument order is load-bearing documentation "
            "of which entity aggregates which; update this contract only "
            "with a deliberate, reviewed schema change."
        )
