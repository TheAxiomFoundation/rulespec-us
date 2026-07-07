"""Ratchet check for the oracle-coverage pending lane.

``oracle-coverage-pending.yaml`` declares executable outputs awaiting oracle
classification so bulk PRs pass without a per-output axiom-oracles pin dance.
This test enforces the ratchet both ways, mirroring known-validation-gaps:

  * every unmapped output in this repo is declared (nothing silent), and
  * every declaration is still unmapped — an output classified upstream in
    axiom-oracles must be removed here, so the debt only ratchets down.

It delegates to ``axiom-encode oracle-coverage-pending check`` (the same
authority the bulk lane and the gate use) scoped to this repo, so it runs
inside the toolchain-pinned validate job where axiom-encode and the sibling
rulespec checkouts are already installed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_oracle_coverage_pending_ratchet() -> None:
    axiom_encode = shutil.which("axiom-encode")
    if axiom_encode is None:
        pytest.skip("axiom-encode is not installed; ratchet runs in the validate job")

    result = subprocess.run(
        [
            axiom_encode,
            "oracle-coverage-pending",
            "check",
            "--root",
            str(REPO_ROOT.parent),
            "--repo",
            REPO_ROOT.name,
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        payload = {}
    problems = payload.get("problems") or [result.stderr.strip() or "<no output>"]

    assert result.returncode == 0, (
        "oracle-coverage-pending ratchet failed. Declare new unmapped outputs in "
        "oracle-coverage-pending.yaml, and remove declarations whose output is "
        "now classified upstream:\n- " + "\n- ".join(problems)
    )
