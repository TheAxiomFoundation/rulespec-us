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
    "encoder_verifier": "main",
    "axiom_encode_ref": "a" * 40,
    "axiom_rules_engine_ref": "e" * 40,
    "axiom_compose_ref": "f" * 40,
    "axiom_corpus_ref": "c" * 40,
    "corpus_release": ["2026-11-01", "d" * 64],
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


def test_loosen_runs_everything_until_waived_files_can_be_validated():
    result = _plan(_state(), [_pr(1, "none"), _pr(2, "loosen")])
    assert result["scope"] == "full"


def test_encoder_commit_without_a_merged_pr_runs_everything():
    result = _plan(_state(), [_pr(1, "none"), {"number": None, "commit": "c" * 40}])
    assert result["scope"] == "full"


def test_future_state_is_not_trusted():
    future = _state(
        encoder_main=CURRENT["encoder_main"],
        last_full_at=(NOW + timedelta(days=30)).isoformat(),
    )
    assert _plan(future, [])["scope"] == "full"


@pytest.mark.parametrize("effect", ["tighten", None, "maybe"])
def test_tighten_or_undeclared_runs_everything(effect):
    result = _plan(_state(), [_pr(1, "loosen"), _pr(2, effect)])
    assert result["scope"] == "full"
    assert result["state"]["last_full_at"] == NOW.isoformat()


@pytest.mark.parametrize(
    "changes",
    [
        {"axiom_rules_engine_ref": "f" * 40},
        {"axiom_compose_ref": "0" * 40},
        {"axiom_encode_ref": "1" * 40},
        {"encoder_verifier": "pinned"},
        {"axiom_corpus_ref": "f" * 40},
        {"corpus_release": ["2026-10-01", "d" * 64]},
        {"last_full_at": (NOW - timedelta(days=7)).isoformat()},
    ],
)
def test_engine_corpus_and_weekly_changes_run_everything(changes):
    previous = _state(encoder_main=CURRENT["encoder_main"], **changes)
    assert _plan(previous, [])["scope"] == "full"


@pytest.mark.parametrize(
    "previous",
    [None, {}, {"schema": "other"}, _state(encoder_main="x"), _state(encoder_verifier="x")],
)
def test_missing_or_foreign_state_runs_everything(previous):
    assert _plan(previous, [])["scope"] == "full"


def test_pinned_mode_ignores_encoder_main_merges():
    pinned = {**CURRENT, "encoder_verifier": "pinned"}
    previous = _state(encoder_verifier="pinned")
    assert _plan(previous, None, current=pinned)["scope"] == "skip"
    assert _plan(previous, [_pr(1, "tighten")], current=pinned)["scope"] == "skip"


def test_unlisted_encoder_merges_run_everything():
    assert _plan(_state(), None)["scope"] == "full"


def test_forced_full_run():
    previous = _state(encoder_main=CURRENT["encoder_main"])
    assert _plan(previous, [], force_full=True)["scope"] == "full"


def test_declared_effect_ignores_template_comments():
    assert drift.declared_effect("<!-- Validation effect: none -->") is None
    assert drift.declared_effect("Validation effect: `Tighten`\n") == "tighten"


LOG = """validate (us)\tRun validation\t2026-11-06T06:40:01.1234567Z Validating 3 files
validate (us)\tRun validation\t2026-11-06T06:40:09.0000000Z
validate (us)\tRun validation\t2026-11-06T06:40:09.0000000Z 2 of 3 file(s) failed:
validate (us)\tRun validation\t2026-11-06T06:40:09.0000000Z   - /home/runner/work/rulespec-us/rulespec-us/us/statutes/7/2015.yaml
validate (us)\tRun validation\t2026-11-06T06:40:09.0000000Z   - us-ma/regulations/106-cmr/1.yaml
validate (us)\tRun validation\t2026-11-06T06:40:09.5000000Z RULESPEC_VALIDATION_CHUNK files=3 status=1 single=-
validate (us)\tRun validation\t2026-11-06T06:40:09.6000000Z RULESPEC_VALIDATION_CHUNKS total=1
validate (us)\tRun validation\t2026-11-06T06:40:10.0000000Z ##[error]Process completed with exit code 1.
validate (us)\tOther\t2026-11-06T06:40:11.0000000Z   - us/not/after/header.yaml
"""


WORKSPACE = "/home/runner/work/rulespec-us/rulespec-us"


def test_failing_files_are_read_from_validate_output():
    # The shared validator passes absolute workspace paths.
    assert drift.failing_files(LOG, WORKSPACE) == [
        "us-ma/regulations/106-cmr/1.yaml",
        "us/statutes/7/2015.yaml",
    ]


def test_report_opens_new_issues_updates_known_ones_and_closes_none():
    plan_result = {"scope": "full", "targets": [], "reasons": ["weekly"]}
    result = drift.report(
        plan_result=plan_result,
        jobs=[{"name": "validate / validate (us)", "conclusion": "failure", "failed_steps": ["Validate RuleSpec YAML"], "log": LOG}],
        validate_result="failure",
        open_issue_paths=["us/statutes/7/2015.yaml", "us/statutes/1.yaml"],
        run_url="https://example.invalid/run",
        workspace=WORKSPACE,
    )
    assert [item["title"] for item in result["open"]] == [
        "Validation drift: us-ma/regulations/106-cmr/1.yaml",
    ]
    assert result["update"] == ["us/statutes/7/2015.yaml"]
    assert "close" not in result
    assert result["labels"] == ["validation-drift", "re-encode-queue"]


def test_report_caps_new_issues_per_run():
    lines = (
        f"{drift.MAX_NEW_ISSUES + 5} of 99 file(s) failed:\n"
        + "".join(f"  - us/statutes/{n}.yaml\n" for n in range(drift.MAX_NEW_ISSUES + 5))
        + "RULESPEC_VALIDATION_CHUNK files=99 status=1 single=-\n"
        + "RULESPEC_VALIDATION_CHUNKS total=1\n"
    )
    result = drift.report(
        plan_result={"scope": "full", "targets": [], "reasons": []},
        jobs=[{"name": "validate / validate (us)", "conclusion": "failure", "failed_steps": ["Validate RuleSpec YAML"], "log": lines}],
        validate_result="failure",
        open_issue_paths=[],
        run_url="u",
    )
    assert len(result["open"]) == drift.MAX_NEW_ISSUES
    assert len(result["deferred"]) == 5


@pytest.mark.parametrize(
    ("jobs", "result"),
    [
        ([], "failure"),
        ([{"name": "validate / validate (us)", "conclusion": "failure", "failed_steps": ["Validate RuleSpec YAML"], "log": ""}], "failure"),
        ([{"name": "validate / validate (us)", "conclusion": "failure", "failed_steps": ["Validate RuleSpec YAML"], "log": LOG}], "cancelled"),
        # A leg's summary lists fewer files than it declares.
        (
            [
                {
                    "name": "validate / validate (us)",
                    "conclusion": "failure",
                    "failed_steps": ["Validate RuleSpec YAML"],
                    "log": LOG.replace("2 of 3 file(s)", "3 of 3 file(s)"),
                }
            ],
            "failure",
        ),
        # A later step of a listing leg also failed.
        (
            [
                {
                    "name": "validate / validate (us)",
                    "conclusion": "failure",
                    "failed_steps": ["Validate RuleSpec YAML", "Run companion tests"],
                    "log": LOG,
                }
            ],
            "failure",
        ),
        # The shards job failed, or a leg was skipped after it.
        ([{"name": "validate / shards", "conclusion": "failure", "log": ""}], "failure"),
        (
            [
                {"name": "validate / validate (us)", "conclusion": "failure",
                 "failed_steps": ["Validate RuleSpec YAML"], "log": LOG},
                {"name": "validate / validate (us-ca)", "conclusion": "skipped", "log": ""},
            ],
            "failure",
        ),
        # One leg lists failures, another failed for another reason.
        (
            [
                {"name": "validate / validate (us)", "conclusion": "failure", "failed_steps": ["Validate RuleSpec YAML"], "log": LOG},
                {"name": "validate / validate (us-ca)", "conclusion": "failure", "failed_steps": ["Validate RuleSpec YAML"], "log": "timeout"},
            ],
            "failure",
        ),
    ],
)
def test_unexplained_failures_report_an_error_not_an_issue(jobs, result):
    """Each case leaves at least one failing job without a full summary."""
    outcome = drift.report(
        plan_result={"scope": "full", "targets": [], "reasons": []},
        jobs=jobs,
        validate_result=result,
        open_issue_paths=[],
        run_url="u",
    )
    assert "error" in outcome


def test_cli_plan_reads_the_repository(tmp_path):
    repo = tmp_path / "rulespec-us"
    (repo / ".axiom").mkdir(parents=True)
    (repo / ".axiom/workflow-toolchain.toml").write_text(
        "[workflow_toolchain]\n"
        f'axiom_encode_ref = "{"a" * 40}"\n'
        f'axiom_rules_engine_ref = "{"e" * 40}"\n'
        f'axiom_compose_ref = "{"f" * 40}"\n'
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
    prs.write_text(json.dumps([_pr(7, "none")]))
    output = tmp_path / "plan.json"
    assert (
        drift.main(
            [
                "plan",
                "--previous-state", str(previous),
                "--encoder-main", "b" * 40,
                "--encoder-verifier", "main",
                "--encoder-prs", str(prs),
                "--repo", str(repo),
                "--output", str(output),
            ]
        )
        == 0
    )
    result = json.loads(output.read_text())
    assert result["scope"] == "skip"
    assert result["state"]["encoder_main"] == "b" * 40


def test_aggregate_and_skipped_helper_jobs_do_not_hide_or_block_results():
    jobs = [
        {"name": "validate / validate (us)", "conclusion": "failure",
         "failed_steps": ["Validate RuleSpec YAML"], "log": LOG},
        {"name": "validate / validate", "conclusion": "failure", "log": ""},
        {"name": "validate / rollback proof", "conclusion": "skipped", "log": ""},
        {"name": "validate / shards", "conclusion": "success", "log": ""},
    ]
    result = drift.report(
        plan_result={"scope": "full", "targets": [], "reasons": []},
        jobs=jobs,
        validate_result="failure",
        open_issue_paths=[],
        run_url="u",
        workspace=WORKSPACE,
    )
    assert "error" not in result
    assert len(result["open"]) == 2


def test_pending_full_state_forces_a_full_run():
    previous = _state(encoder_main=CURRENT["encoder_main"], pending_full=True)
    assert _plan(previous, [])["scope"] == "full"
    assert "pending_full" not in _plan(previous, [])["state"]


def _chunks(*segments: str) -> str:
    return "".join(segments) + f"RULESPEC_VALIDATION_CHUNKS total={len(segments)}\n"


SUMMARY_CHUNK = (
    "2 of 3 file(s) failed:\n  - us/a.yaml\n  - us/b.yaml\n"
    "RULESPEC_VALIDATION_CHUNK files=3 status=1 single=-\n"
)


def test_one_file_chunk_names_its_file_only_when_the_validator_failed_it():
    reached = (
        f"File: {WORKSPACE}/us/statutes/9.yaml\nCI: ✗\nResult: ✗ FAILED\n"
        f"RULESPEC_VALIDATION_CHUNK files=1 status=1 single={WORKSPACE}/us/statutes/9.yaml\n"
    )
    failed, explained = drift.leg_failures(_chunks(SUMMARY_CHUNK, reached), WORKSPACE)
    assert explained and failed == {"us/a.yaml", "us/b.yaml", "us/statutes/9.yaml"}
    # A setup failure in a one-file chunk blames no file.
    setup = (
        "Traceback (most recent call last): engine missing\n"
        f"RULESPEC_VALIDATION_CHUNK files=1 status=1 single={WORKSPACE}/us/statutes/9.yaml\n"
    )
    assert drift.leg_failures(_chunks(SUMMARY_CHUNK, setup), WORKSPACE)[1] is False


def test_crashes_missing_lines_and_old_validators_are_unexplained():
    crashed = "Traceback: boom\nRULESPEC_VALIDATION_CHUNK files=4 status=1 single=-\n"
    assert drift.leg_failures(_chunks(SUMMARY_CHUNK, crashed))[1] is False
    # A chunk line went missing: the total does not match.
    lost = "RULESPEC_VALIDATION_CHUNKS total=2\n"
    assert drift.leg_failures(SUMMARY_CHUNK + lost)[1] is False
    # A path with a space still counts as a chunk line.
    spaced = "RULESPEC_VALIDATION_CHUNK files=1 status=0 single=us/a b.yaml\n"
    assert drift.leg_failures(_chunks(SUMMARY_CHUNK, spaced))[1] is True
    # Without chunk lines (an older validator), nothing is explained.
    assert drift.leg_failures("2 of 2 file(s) failed:\n  - us/a.yaml\n  - us/b.yaml\n")[1] is False
    # A failed leg whose chunks all passed failed for another reason.
    passed = "RULESPEC_VALIDATION_CHUNK files=2 status=0 single=-\n"
    assert drift.leg_failures(_chunks(passed))[1] is False
