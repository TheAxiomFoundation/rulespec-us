from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "us-sc"
    / "policies"
    / "income_tax"
    / "2026_full_year_resident_core.yaml"
)
ALLOWED_INPUT_KEYS = {
    "name",
    "entity",
    "dtype",
    "period",
    "unit",
    "description",
}


def test_south_carolina_inputs_use_only_declared_contract_fields() -> None:
    payload = yaml.safe_load(MODULE_PATH.read_text(encoding="utf-8"))

    assert payload["inputs"]
    assert all(
        isinstance(item, dict) and set(item) <= ALLOWED_INPUT_KEYS
        for item in payload["inputs"]
    )
