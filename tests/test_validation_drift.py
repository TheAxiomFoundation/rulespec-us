"""The event-driven validation drift run (axiom-encode#2094)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import validation_drift as drift  # noqa: E402

NOW = datetime(2026, 11, 6, 6, 23, tzinfo=timezone.utc)
CURRENT = {
    "encoder_main": "b" * 40,
    "axiom_rules_engine_ref": "e" * 40,
    "axiom_corpus_ref": "c" * 40,
    "corpus_release": ["2026-11-01", "d" * 64],
}
LEDGER = {
    "validate_failures": {
        "us/statutes/7/2015.yaml": {"active": {}},
        "us-ma/regulations/106-cmr/1.yaml": {"active": {}},
    }
}


def _state(**changes):
    state = {
        "schema": drift.STATE_SCHEMA,
        **CURRENT,
        "encoder_main": "a" * 40,
        "last_full_at": (NOW - timedelta(days=2)).isoformat(),
    }
    state.update(changes)
    return state


def _pr(number, effect):
    body = f"Change.\n\nValidation effect: {effect}\n" if effect else "No field.\n"
    if effect in ("loosen", "tighten"):
        body += "Changed checks: proof.source\n"
    return {"number": number, "body": body}


def _plan(previous, prs, **kwargs):
    return drift.plan(
        previous=previous,
        current=kwargs.pop("current", CURRENT),
        encoder_prs=prs,
        ledger=kwargs.pop("ledger", LEDGER),
        now=NOW,
        **kwargs,
    )


def test_none_only_merges_skip_and_advance_the_state():
    result = _plan(_state(), [_pr(1, "none"), _pr(2, "none")])
    assert result["scope"] == "skip"
    assert result["state"]["encoder_main"] == CURRENT["encoder_main"]
    assert result["state"]["last_full_at"] == _state()["last_full_at"]


def test_nothing_changed_skips():
    assert _plan(_state(encoder_main=CURRENT["encoder_main"]), [])["scope"] == "skip"


def test_loosen_checks_the_waived_files():
    result = _plan(_state(), [_pr(1, "none"), _pr(2, "loosen")])
    assert result["scope"] == "waived"
    assert result["targets"] == sorted(LEDGER["validate_failures"])


@pytest.mark.parametrize("effect", ["tighten", None, "maybe"])
def test_tighten_or_undeclared_runs_everything(effect):
    result = _plan(_state(), [_pr(1, "loosen"), _pr(2, effect)])
    assert result["scope"] == "full"
    assert result["state"]["last_full_at"] == NOW.isoformat()


@pytest.mark.parametrize(
    "changes",
    [
        {"axiom_rules_engine_ref": "f" * 40},
        {"axiom_corpus_ref": "f" * 40},
        {"corpus_release": ["2026-10-01", "d" * 64]},
        {"last_full_at": (NOW - timedelta(days=7)).isoformat()},
    ],
)
def test_engine_corpus_and_weekly_changes_run_everything(changes):
    previous = _state(encoder_main=CURRENT["encoder_main"], **changes)
    assert _plan(previous, [])["scope"] == "full"


@pytest.mark.parametrize("previous", [None, {}, {"schema": "other"}, _state(encoder_main="x")])
def test_missing_or_foreign_state_runs_everything(previous):
    assert _plan(previous, [])["scope"] == "full"


def test_unlisted_encoder_merges_run_everything():
    assert _plan(_state(), None)["scope"] == "full"


def test_forced_full_run():
    previous = _state(encoder_main=CURRENT["encoder_main"])
    assert _plan(previous, [], force_full=True)["scope"] == "full"


def test_loosen_without_waived_files_skips():
    result = _plan(_state(), [_pr(1, "loosen")], ledger={"validate_failures": {}})
    assert result["scope"] == "skip"


def test_unsafe_waived_path_fails():
    with pytest.raises(ValueError, match="invalid waived path"):
        _plan(_state(), [_pr(1, "loosen")], ledger={"validate_failures": {"../x.yaml": {}}})


def test_declared_effect_ignores_template_comments():
    assert drift.declared_effect("<!-- Validation effect: none -->") is None
    assert drift.declared_effect("Validation effect: `Tighten`\n") == "tighten"


LOG = """validate (us)\tRun validation\t2026-11-06T06:40:01.1234567Z Validating 3 files
validate (us)\tRun validation\t2026-11-06T06:40:09.0000000Z
validate (us)\tRun validation\t2026-11-06T06:40:09.0000000Z 2 of 3 file(s) failed:
validate (us)\tRun validation\t2026-11-06T06:40:09.0000000Z   - us/statutes/7/2015.yaml
validate (us)\tRun validation\t2026-11-06T06:40:09.0000000Z   - us-ma/regulations/106-cmr/1.yaml
validate (us)\tRun validation\t2026-11-06T06:40:10.0000000Z ##[error]Process completed with exit code 1.
validate (us)\tOther\t2026-11-06T06:40:11.0000000Z   - us/not/after/header.yaml
"""


def test_failing_files_are_read_from_validate_output():
    assert drift.failing_files(LOG) == [
        "us-ma/regulations/106-cmr/1.yaml",
        "us/statutes/7/2015.yaml",
    ]


def test_report_opens_one_issue_per_failing_file_and_closes_fixed_ones():
    plan_result = {"scope": "full", "targets": [], "reasons": ["weekly"]}
    result = drift.report(
        plan_result=plan_result,
        log=LOG,
        validate_result="failure",
        open_issue_paths=["us/statutes/7/2015.yaml", "us/statutes/1.yaml"],
        all_files=["us/statutes/1.yaml", "us/statutes/7/2015.yaml"],
        run_url="https://example.invalid/run",
    )
    assert [item["title"] for item in result["open"]] == [
        "Validation drift: us-ma/regulations/106-cmr/1.yaml",
        "Validation drift: us/statutes/7/2015.yaml",
    ]
    assert result["close"] == ["us/statutes/1.yaml"]
    assert result["labels"] == ["validation-drift", "re-encode-queue"]


def test_waived_scope_closes_only_issues_in_scope():
    result = drift.report(
        plan_result={"scope": "waived", "targets": ["us/a.yaml"], "reasons": []},
        log="",
        validate_result="success",
        open_issue_paths=["us/a.yaml", "us/b.yaml"],
        all_files=["us/a.yaml", "us/b.yaml"],
        run_url="u",
    )
    assert result["open"] == [] and result["close"] == ["us/a.yaml"]


@pytest.mark.parametrize(("log", "result"), [("", "failure"), (LOG, "cancelled")])
def test_unreadable_failures_report_an_error_not_an_issue(log, result):
    outcome = drift.report(
        plan_result={"scope": "full", "targets": [], "reasons": []},
        log=log,
        validate_result=result,
        open_issue_paths=[],
        all_files=[],
        run_url="u",
    )
    assert "error" in outcome


def test_cli_plan_reads_the_repository(tmp_path):
    repo = tmp_path / "rulespec-us"
    (repo / ".axiom").mkdir(parents=True)
    (repo / ".axiom/workflow-toolchain.toml").write_text(
        "[workflow_toolchain]\n"
        f'axiom_rules_engine_ref = "{"e" * 40}"\n'
        f'axiom_corpus_ref = "{"c" * 40}"\n'
    )
    (repo / ".axiom/toolchain.toml").write_text(
        '[toolchain]\naxiom_corpus_release = "2026-11-01"\n'
        f'axiom_corpus_release_content_sha256 = "{"d" * 64}"\n'
    )
    (repo / "known-validation-gaps.yaml").write_text(
        "validate_failures:\n  us/statutes/1.yaml:\n    active: {}\n"
    )
    (repo / "us/statutes").mkdir(parents=True)
    (repo / "us/statutes/1.yaml").write_text("format: rulespec/v1\n")
    previous = tmp_path / "state.json"
    previous.write_text(json.dumps(_state()))
    prs = tmp_path / "prs.json"
    prs.write_text(json.dumps([_pr(7, "loosen")]))
    output = tmp_path / "plan.json"
    assert (
        drift.main(
            [
                "plan",
                "--previous-state", str(previous),
                "--encoder-main", "b" * 40,
                "--encoder-prs", str(prs),
                "--repo", str(repo),
                "--output", str(output),
            ]
        )
        == 0
    )
    result = json.loads(output.read_text())
    assert result["scope"] == "waived"
    assert result["targets"] == ["us/statutes/1.yaml"]
