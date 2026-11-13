"""The reviewed admissions registry (axiom-encode#2095).

The encoder reads `.axiom/admissions/` only from the protected main commit
(`axiom-encode admission-registry export`), so a pull request can never
admit itself. This test keeps proposed records well formed; the encoder
applies the full schema when it loads them.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / ".axiom/admissions"
ALLOWED = {"coverage-exemptions.jsonl"}
FIELDS = {
    "citation_path", "requested_scope", "source_text_sha256", "label",
    "physical_start", "window_sha256", "window", "reason", "owner_evidence",
    "corpus_artifact", "artifact_sha256", "row", "reviewer", "reviewed_at",
}
JURISDICTION = re.compile(r"us(?:-[a-z]{2})?")


def test_registry_holds_only_known_regular_files():
    names = {path.name for path in REGISTRY.iterdir()}
    assert names <= ALLOWED, names - ALLOWED
    for path in REGISTRY.iterdir():
        assert path.is_file() and not path.is_symlink(), path


def test_coverage_exemptions_are_well_formed_and_in_this_repository():
    path = REGISTRY / "coverage-exemptions.jsonl"
    keys = set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        record = json.loads(line)
        assert set(record) == FIELDS, (number, set(record) ^ FIELDS)
        for field in ("citation_path",):
            assert JURISDICTION.fullmatch(record[field].split("/", 1)[0]), number
        assert JURISDICTION.fullmatch(
            record["owner_evidence"]["citation_path"].split("/", 1)[0]
        ), number
        key = (
            record["citation_path"], json.dumps(record["requested_scope"]),
            record["source_text_sha256"], record["label"], record["physical_start"],
        )
        assert key not in keys, (number, key)
        keys.add(key)
