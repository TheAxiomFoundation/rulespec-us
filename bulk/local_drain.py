#!/usr/bin/env python3
"""Local bulk-encode drain runner.

Drains ``bulk/worklist.yaml`` on the operator's machine using the local Codex
CLI (ChatGPT subscription, ``gpt-5.5``) instead of the cloud ``bulk-encode.yml``
dispatcher, opening one draft PR per module for independent review. It mirrors
the generation path while adding the exact-checkout oracle-coverage-pending
declaration needed to keep new-state PRs out of the unmapped coverage state.

Two decisions matter and are baked in here so PRs go green:

* **Generation uses the toolchain-pinned encoder**
  (``.axiom/workflow-toolchain.toml`` ``axiom_encode_version``, currently
  0.2.1308). The required ``validate /
  validate`` check validates with that same pin, so generating with anything
  newer risks schema/manifest skew. Do NOT "upgrade" the generation encoder to
  match a brief that says ">=0.2.1190" -- that number refers only to the
  *coverage/sync* tool below, not to generation.
* **Coverage declaration uses an immutable current-CI encoder ref.** Before any
  mutation, the runner requires that exact ref to remain the head of the remote
  ``main`` branch consumed by CI. This keeps the coverage classifier aligned
  with the exact-checkout contract used by required CI.

Everything runs foreground. The loop is chunked (``--max-seconds``,
``--max-entries``) and every unit of durable state (pushed branch, opened PR,
worklist status flip, PROGRESS.md) is committed per entry, so a jetsam kill
between chunks loses nothing: re-run and it resumes. On a Codex
subscription-limit signal it PAUSES (never hammers), writes state, and exits 0.

Toolchain layout (override via env): a sibling ``_bulk_drain`` workspace holds
pinned checkouts + venvs built once by the operator:

    _bulk_drain/
      axiom-encode/            # worktree @ pinned axiom_encode_ref
      .venv/                   # pinned encoder venv  -> generation
      axiom-encode-cov/        # worktree @ COV_ENCODER_REF below
      .venv-cov/               # coverage/sync venv   -> oracle-coverage-pending
      axiom-rules-engine/      # worktree @ pinned engine ref, cargo build
      axiom-corpus/            # worktree @ pinned corpus ref
      wt/<slug>/rulespec-us/   # per-entry generation worktrees (leaf MUST be rulespec-us)

Usage:
    python bulk/local_drain.py drain   [--status pending-local] [--limit N]
                                       [--batch A] [--concurrency 3]
                                       [--max-entries N] [--max-seconds 540]
    python bulk/local_drain.py unstick [--pr N ...] [--all] [--wait]
    python bulk/local_drain.py doctor  # verify toolchain + auth + signing key
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import threading
import time

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 local drain environments.
    import tomli as tomllib
from datetime import datetime, timezone
from pathlib import Path

from applied_artifacts import discover_applied_artifacts

REPO = "TheAxiomFoundation/rulespec-us"
REPO_NAME = "rulespec-us"
COV_ENCODER_REF = "b03fa3c5f6455ec58bdd832f7855a1ffbb136c7d"
COV_ENCODER_REMOTE = "https://github.com/TheAxiomFoundation/axiom-encode.git"
COV_ORACLES_REF = "9901e2479ac39bba865b8232e1c7d879ba447d8d"
HERE = Path(__file__).resolve().parent           # <checkout>/bulk
CHECKOUT = HERE.parent                            # this checkout root

# --- toolchain / workspace resolution ---------------------------------------
DRAIN_BASE = Path(
    os.environ.get("DRAIN_BASE", Path.home() / "TheAxiomFoundation" / "_bulk_drain")
).resolve()
GEN_AE = Path(os.environ.get("DRAIN_GEN_AE", DRAIN_BASE / ".venv/bin/axiom-encode"))
COV_AE = Path(os.environ.get("DRAIN_COV_AE", DRAIN_BASE / ".venv-cov/bin/axiom-encode"))
COV_PY = Path(os.environ.get("DRAIN_COV_PY", DRAIN_BASE / ".venv-cov/bin/python"))
COV_CHECKOUT = Path(
    os.environ.get("DRAIN_COV_CHECKOUT", DRAIN_BASE / "axiom-encode-cov")
).resolve()
ENGINE = Path(os.environ.get("DRAIN_ENGINE", DRAIN_BASE / "axiom-rules-engine"))
CORPUS = Path(os.environ.get("DRAIN_CORPUS", DRAIN_BASE / "axiom-corpus"))
ENGINE_BIN = ENGINE / "target" / "debug"
WT_ROOT = DRAIN_BASE / "wt"

BACKEND = os.environ.get("DRAIN_BACKEND", "codex")
MODEL = os.environ.get("DRAIN_MODEL", "gpt-5.5")

# Codex subscription-limit signatures. On any of these we PAUSE the whole drain.
LIMIT_SIGNS = re.compile(
    r"rate.?limit|usage limit|quota|insufficient_quota|too many requests|"
    r"\b429\b|reached your (usage|limit)|plan limit|overloaded",
    re.I,
)

_print_lock = threading.Lock()
_wt_lock = threading.Lock()          # git worktree add/remove is not concurrency-safe
_PAUSE = threading.Event()


def log(msg: str) -> None:
    with _print_lock:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run(
    cmd,
    cwd=None,
    env=None,
    capture=True,
    check=False,
    timeout=None,
    merge_stderr=True,
):
    """Run a subprocess, returning (rc, combined_output)."""
    full = dict(os.environ)
    if env:
        for key, value in env.items():
            if value is None:
                full.pop(key, None)
            else:
                full[key] = value
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=full,
        stdout=subprocess.PIPE if capture else None,
        stderr=(subprocess.STDOUT if merge_stderr else subprocess.DEVNULL)
        if capture
        else None,
        text=True,
        timeout=timeout,
    )
    out = proc.stdout or "" if capture else ""
    if check and proc.returncode != 0:
        raise RuntimeError(f"cmd failed ({proc.returncode}): {' '.join(map(str, cmd))}\n{out}")
    return proc.returncode, out


def signing_key() -> str:
    key = os.environ.get("AXIOM_ENCODE_APPLY_SIGNING_KEY", "").strip()
    if key:
        return key
    agent_secret = str(Path.home() / "bin/agent-secret")
    for cmd in (
        [agent_secret, "get", "agent/axiom-encode-apply-signing-key"],
        ["agent-secret", "get", "agent/axiom-encode-apply-signing-key"],
        [
            "security",
            "find-generic-password",
            "-a",
            "axiom-encode",
            "-s",
            "AXIOM_ENCODE_APPLY_SIGNING_KEY",
            "-w",
        ],
    ):
        try:
            rc, out = run(cmd)
            if rc == 0 and out.strip():
                return out.strip()
        except FileNotFoundError:
            continue
    raise SystemExit(
        "Signing key AXIOM_ENCODE_APPLY_SIGNING_KEY unavailable "
        "(tried env, agent-secret, and macOS Keychain)."
    )


def pinned_toolchain() -> dict:
    data = tomllib.loads((CHECKOUT / ".axiom/workflow-toolchain.toml").read_text())
    return data.get("workflow_toolchain", data)


def citation_slug(citation: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", citation.strip().lower())
    return slug.strip("-")


def gh_json(args):
    rc, out = run(["gh", *args])
    if rc != 0:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def ensure_draft_pr(branch: str) -> None:
    pr = gh_json(
        ["pr", "view", branch, "--repo", REPO, "--json", "isDraft,autoMergeRequest"]
    )
    if pr is None:
        raise RuntimeError(f"could not read PR state for {branch}")
    if pr.get("autoMergeRequest") is not None:
        run(
            ["gh", "pr", "merge", branch, "--repo", REPO, "--disable-auto"],
            check=True,
        )
    if pr.get("isDraft") is not True:
        run(["gh", "pr", "ready", branch, "--repo", REPO, "--undo"], check=True)

    verified = gh_json(
        ["pr", "view", branch, "--repo", REPO, "--json", "isDraft,autoMergeRequest"]
    )
    if (
        verified is None
        or verified.get("isDraft") is not True
        or verified.get("autoMergeRequest") is not None
    ):
        raise RuntimeError(
            f"refusing to continue: {branch} is not a draft with auto-merge disabled"
        )


def pause_for_retry(result: dict, detail: str) -> dict:
    _PAUSE.set()
    result["status"] = "paused"
    result["detail"] = detail
    return result


# --- worktree helpers -------------------------------------------------------
def make_worktree(slug: str, ref: str) -> Path:
    """Fresh generation worktree whose leaf dir is exactly ``rulespec-us``
    (the --apply resolver requirement) with sibling engine/corpus symlinks."""
    parent = WT_ROOT / slug
    leaf = parent / REPO_NAME
    with _wt_lock:
        if leaf.exists():
            run(["git", "-C", str(CHECKOUT), "worktree", "remove", "--force", str(leaf)])
        parent.mkdir(parents=True, exist_ok=True)
        run(["git", "-C", str(CHECKOUT), "fetch", "origin", "main", "--quiet"])
        run(["git", "-C", str(CHECKOUT), "worktree", "add", "--detach", str(leaf), ref])
    for name, target in (("axiom-rules-engine", ENGINE), ("axiom-corpus", CORPUS)):
        link = parent / name
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(target)
    return leaf


def drop_worktree(leaf: Path) -> None:
    with _wt_lock:
        run(["git", "-C", str(CHECKOUT), "worktree", "remove", "--force", str(leaf)])


def regen_index(leaf: Path) -> None:
    script = leaf / "tests/generate_reverse_index.py"
    if script.exists():
        run([str(COV_PY), str(script)], cwd=leaf)


def sync_pending(leaf: Path) -> str:
    """Write oracle-coverage-pending.yaml using the pinned classifier.
    Returns the sync summary line."""
    require_coverage_ref()
    rc, out = run([str(COV_AE), "oracle-coverage-pending", "sync",
                   "--root", str(leaf), "--source", "bulk"],
                  env={
                      "PATH": f"{ENGINE_BIN}:{os.environ['PATH']}",
                      "AXIOM_ENCODE_APPLY_SIGNING_KEY": None,
                  })
    if rc != 0:
        raise RuntimeError(f"oracle-coverage-pending sync failed:\n{out}")
    return out.strip().splitlines()[-1] if out.strip() else "(no output)"


def finalize_pending(leaf: Path) -> bool:
    """Keep oracle-coverage-pending.yaml only when it declares entries or is
    already tracked on the branch. A fully-mapped module syncs an *empty*
    declaration; committing that empty repo-root file would needlessly flip the
    PR to full-matrix validation. Drop it so mapped modules stay shard-scoped.
    Returns True when a pending file remains to stage."""
    pf = leaf / "oracle-coverage-pending.yaml"
    if not pf.exists():
        return False
    tracked = run(["git", "-C", str(leaf), "ls-files", "--error-unmatch",
                   "oracle-coverage-pending.yaml"])[0] == 0
    has_entries = "- legal_id:" in pf.read_text(encoding="utf-8")
    if not has_entries and not tracked:
        pf.unlink()
        return False
    return True


def is_encoding_manifest_path(path: str) -> bool:
    return path.startswith(".axiom/encoding-manifests/") or bool(
        re.match(
            r"^[a-z]{2}(?:-[a-z0-9-]+)?/\.axiom/encoding-manifests/",
            path,
        )
    )


def aggregate_validation_state(checks: list[dict]) -> str | None:
    states = [
        str(check.get("conclusion") or check.get("state") or "").upper()
        for check in checks
        if str(check.get("name") or "").startswith("validate / validate")
    ]
    if not states:
        return None
    failed = {
        "ACTION_REQUIRED",
        "CANCELLED",
        "ERROR",
        "FAILURE",
        "STALE",
        "TIMED_OUT",
    }
    if any(state in failed for state in states):
        return "FAILURE"
    complete = {"NEUTRAL", "SKIPPED", "SUCCESS"}
    if any(state not in complete for state in states):
        return "PENDING"
    return "SUCCESS"


# ---------------------------------------------------------------------------
# PART A: unstick already-open new-state bulk PRs (priority).
# ---------------------------------------------------------------------------
def open_bulk_prs():
    data = gh_json(["pr", "list", "--repo", REPO, "--state", "open", "--limit", "200",
                    "--json", "number,headRefName,mergeStateStatus,statusCheckRollup"])
    if data is None:
        raise RuntimeError("could not list open bulk PRs")
    prs = []
    for pr in data:
        if not pr["headRefName"].startswith("bulk/"):
            continue
        vv = aggregate_validation_state(pr.get("statusCheckRollup") or [])
        prs.append({"number": pr["number"], "branch": pr["headRefName"],
                    "merge": pr["mergeStateStatus"], "validate": vv})
    return sorted(prs, key=lambda p: p["number"])


def unstick_pr(branch: str, wait: bool) -> str:
    """Rebuild the stuck PR branch as origin/main + the module artifacts + a
    fresh oracle-coverage-pending sync + reverse index.

    Overlay (not merge): a fresh main-based branch with the module's RuleSpec
    artifacts re-applied and the derived files (pending lane, reverse index)
    regenerated. This is always up-to-date with main (strict branch protection)
    and never conflicts on the shared oracle-coverage-pending.yaml as siblings
    merge one after another.
    """
    slug = branch.split("/", 1)[1]
    leaf = make_worktree(f"unstick-{slug}", "origin/main")
    try:
        run(["git", "-C", str(leaf), "checkout", "-B", branch], check=True)
        run(["git", "-C", str(leaf), "fetch", "origin", branch, "--quiet"])
        _, diff = run(["git", "-C", str(leaf), "diff", "--name-only",
                       "origin/main...FETCH_HEAD"])
        program_specs = [f for f in diff.splitlines() if PROGRAM_SPEC_RE.match(f)]
        artifacts = [f for f in diff.splitlines()
                     if (MODULE_RE.match(f) or f.endswith(".test.yaml")
                         or is_encoding_manifest_path(f))]
        if not artifacts:
            return f"{branch}: no module artifacts in diff (already merged?)"
        run(["git", "-C", str(leaf), "checkout", "FETCH_HEAD", "--", *artifacts],
            check=True)
        composition_files = []
        if program_specs:
            item = worklist_item_for_slug(leaf, slug)
            configured_spec = (item.get("program_scope_sync") or {}).get(
                "program_spec")
            if program_specs != [configured_spec]:
                raise RuntimeError(
                    f"{branch}: changed ProgramSpecs {program_specs} do not match "
                    f"the queue configuration {configured_spec!r}"
                )
            composition_files = apply_program_scope_sync(leaf, item, {})
        summary = sync_pending(leaf)
        keep_pending = finalize_pending(leaf)
        regen_index(leaf)
        add_files = [
            *artifacts, *composition_files, ".axiom/index/provisions_to_rules.json"
        ]
        if keep_pending:
            add_files.append("oracle-coverage-pending.yaml")
        run(["git", "-C", str(leaf), "add", "--", *add_files])
        module = next((a for a in artifacts if MODULE_RE.match(a)
                       and not a.endswith(".test.yaml")), artifacts[0])
        msg = (f"Encode {module.rsplit('/', 1)[0]} + declare oracle-coverage "
               f"pending lane ({slug}, bulk)\n\n"
               "Rebuilt on origin/main with the module's unmapped outputs "
               "declared in oracle-coverage-pending.yaml so the changed-file "
               "PolicyEngine oracle-coverage gate passes.\n\n"
               "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>")
        run(["git", "-C", str(leaf), "-c", "user.email=bulk-encode@axiom",
             "-c", "user.name=bulk-encode", "commit", "-q", "-m", msg])
        ensure_draft_pr(branch)
        require_coverage_ref()
        run(["git", "-C", str(leaf), "push", "-f", "origin",
             f"HEAD:refs/heads/{branch}"], check=True)
        ensure_draft_pr(branch)
        result = f"rebuilt+pushed draft {branch}: {summary}"
        if wait:
            result += "; " + wait_for_checks(branch)
        return result
    finally:
        drop_worktree(leaf)


def wait_for_checks(branch: str, timeout_s: int = 1500) -> str:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        pr = gh_json(["pr", "view", branch, "--repo", REPO,
                      "--json", "state,isDraft,statusCheckRollup"])
        if not pr:
            return "poll-error"
        if pr["state"] != "OPEN":
            return pr["state"]
        checks = pr.get("statusCheckRollup") or []
        validation_checks = [
            check
            for check in checks
            if str(check.get("name") or "").startswith("validate / validate")
        ]
        failures = {
            str(check.get("conclusion") or check.get("state") or "").upper()
            for check in checks
        } & {
            "ACTION_REQUIRED",
            "CANCELLED",
            "ERROR",
            "FAILURE",
            "STALE",
            "TIMED_OUT",
        }
        if failures:
            return f"checks={','.join(sorted(failures))} (needs triage)"
        pending = any(
            str(check.get("status") or "").upper()
            not in {"", "COMPLETED"}
            or str(check.get("state") or "").upper() in {"EXPECTED", "PENDING"}
            for check in checks
        )
        if validation_checks and not pending:
            return "checks complete; draft review required"
        time.sleep(30)
    return "timeout-waiting-checks"


# ---------------------------------------------------------------------------
# PART B: generate + PR one pending worklist entry via local Codex.
# ---------------------------------------------------------------------------
MODULE_RE = re.compile(
    r"^[a-z]{2}(-[a-z0-9-]+)?/(manual|statutes|regulations|policies)/.*\.yaml$")
PROGRAM_SPEC_RE = re.compile(
    r"^programs/[a-z]{2}(?:-[a-z0-9]+)*/.+\.yaml$")


def already_handled(slug: str) -> bool:
    pr = gh_json(["pr", "list", "--repo", REPO, "--head", f"bulk/{slug}",
                  "--state", "all", "--json", "number,state"])
    if pr is None:
        raise RuntimeError(f"could not determine PR state for bulk/{slug}")
    return bool(pr)


def handled_slugs() -> set:
    """All bulk/<slug> that already have a PR (any state), in one gh call, so a
    drain chunk skips already-PR'd entries without a per-entry API round-trip."""
    data = gh_json(["pr", "list", "--repo", REPO, "--state", "all", "--limit", "400",
                    "--json", "headRefName"])
    if data is None:
        raise RuntimeError("could not list existing bulk PRs")
    return {p["headRefName"].split("/", 1)[1] for p in data
            if p.get("headRefName", "").startswith("bulk/")}


def worklist_item_for_slug(leaf: Path, slug: str) -> dict:
    process = subprocess.run(
        [str(COV_PY), str(leaf / "bulk/compute_matrix.py"),
         "--status", "any", "--format", "matrix"],
        capture_output=True, text=True, cwd=leaf,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"could not read worklist metadata for {slug}: {process.stderr.strip()}"
        )
    try:
        entries = json.loads(process.stdout)["include"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError(f"invalid worklist matrix while resolving {slug}") from exc
    matches = [entry for entry in entries if entry.get("slug") == slug]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one worklist entry for {slug}; found {len(matches)}"
        )
    return matches[0]


def merged_dependency(citation: str) -> bool:
    branch = f"bulk/{citation_slug(citation)}"
    prs = gh_json([
        "pr", "list", "--repo", REPO, "--state", "merged", "--head", branch,
        "--json", "number",
    ])
    if prs is None:
        raise RuntimeError(f"could not determine merged state for {branch}")
    return bool(prs)


def apply_program_scope_sync(leaf: Path, item: dict, env: dict) -> list[str]:
    spec = item.get("program_scope_sync")
    if spec is None:
        return []
    if not isinstance(spec, dict):
        raise ValueError("program_scope_sync must be a mapping")
    program_spec = spec.get("program_spec")
    scope = spec.get("scope")
    add = spec.get("add", [])
    remove = spec.get("remove", [])
    if not isinstance(program_spec, str) or not program_spec:
        raise ValueError("program_scope_sync.program_spec must be a non-empty string")
    if scope not in {"federal", "state", "local"}:
        raise ValueError("program_scope_sync.scope must be federal, state, or local")
    if not isinstance(add, list) or not all(isinstance(v, str) for v in add):
        raise ValueError("program_scope_sync.add must be a string list")
    if not isinstance(remove, list) or not all(isinstance(v, str) for v in remove):
        raise ValueError("program_scope_sync.remove must be a string list")
    if not add and not remove:
        raise ValueError("program_scope_sync must add or remove at least one module")
    command = [
        str(COV_AE), "program-scope-sync", "--repo", str(leaf),
        "--program-spec", program_spec, "--scope", scope,
    ]
    for value in add:
        command.extend(["--add", value])
    for value in remove:
        command.extend(["--remove", value])
    classifier_env = dict(env)
    classifier_env["AXIOM_ENCODE_APPLY_SIGNING_KEY"] = None
    rc, out = run(command, cwd=leaf, env=classifier_env)
    if rc != 0:
        raise RuntimeError(f"program-scope-sync failed:\n{out}")
    return [program_spec]


def encode_command(leaf: Path, tmp: Path, item: dict) -> list[str]:
    """Build the reviewed encoder command, including repo-local legal context."""
    root = leaf.resolve()
    context_paths: list[Path] = []
    for value in item.get("allow_context", []):
        if not isinstance(value, str) or not value or "\n" in value:
            raise ValueError("allow_context must contain non-empty path strings")
        path = Path(value)
        resolved = (root / path).resolve()
        if path.is_absolute() or not resolved.is_relative_to(root):
            raise ValueError("allow_context path escapes the RuleSpec checkout")
        if not resolved.is_file():
            raise ValueError(f"allow_context file does not exist: {value}")
        context_paths.append(resolved)

    command = [
        str(GEN_AE), "encode", item["citation"], "--backend", BACKEND,
        "--model", MODEL, "--policy-repo-path", str(leaf),
        "--axiom-rules-engine-path", str(ENGINE), "--corpus-path", str(CORPUS),
        "--output", str(tmp), "--apply", "--no-sync",
    ]
    for path in context_paths:
        command.extend(["--allow-context", str(path)])
    return command


def encode_entry(item: dict) -> dict:
    """Full local mirror of bulk-encode.yml for one entry. Returns a result dict."""
    citation, slug = item["citation"], item["slug"]
    res = {"citation": citation, "slug": slug, "status": "failed", "detail": ""}
    if _PAUSE.is_set():
        res["detail"] = "paused"
        return res
    try:
        unmet = [
            dependency
            for dependency in item.get("requires_merged_citations", [])
            if not merged_dependency(dependency)
        ]
    except RuntimeError as exc:
        return pause_for_retry(res, f"{exc}; retry drain")
    if unmet:
        res["status"] = "blocked"
        res["detail"] = "waiting for merged dependencies: " + ", ".join(unmet)
        return res
    try:
        handled = already_handled(slug)
    except RuntimeError as exc:
        return pause_for_retry(res, f"{exc}; retry drain")
    if handled:
        res["status"] = "skipped"
        res["detail"] = "bulk/<slug> PR already exists"
        return res
    leaf = make_worktree(slug, "origin/main")
    tmp = WT_ROOT / slug / "encode-out"
    env = {
        "AXIOM_ENCODE_APPLY_SIGNING_KEY": signing_key(),
        "AXIOM_CORPUS_REPO": str(CORPUS),
        "AXIOM_RULESPEC_REPO_ROOTS": str(leaf),
        # The pinned encoder's bin MUST be on PATH: the --apply manifest step
        # resolves axiom-encode git provenance via the on-PATH entrypoint, and
        # without it apply fails "git provenance is unavailable".
        "PATH": f"{GEN_AE.parent}:{ENGINE_BIN}:{os.environ['PATH']}",
    }
    try:
        rc, out = run(
            encode_command(leaf, tmp, item), cwd=leaf, env=env, timeout=3600
        )
        if LIMIT_SIGNS.search(out):
            _PAUSE.set()
            res["status"], res["detail"] = "paused", "codex subscription-limit signal"
            return res
        if rc != 0:
            failure_log = WT_ROOT / slug / "encode-failure.log"
            failure_log.write_text(out)
            res["detail"] = (
                f"encode/apply failed (rc={rc}); see {failure_log}"
            )
            return res
        try:
            module, test_file, manifest = discover_applied_artifacts(
                leaf, citation=citation
            )
        except ValueError as exc:
            res["detail"] = f"applied artifact discovery failed: {exc}"
            return res
        try:
            composition_files = apply_program_scope_sync(leaf, item, env)
        except (RuntimeError, ValueError) as exc:
            res["detail"] = str(exc)
            return res
        regen_index(leaf)

        # gate battery (fail-closed pre-check, PR-CI order)
        run(["git", "-C", str(leaf), "add", "--", module, test_file, manifest,
             *composition_files, ".axiom/index/provisions_to_rules.json"])
        run(["git", "-C", str(leaf), "-c", "user.email=bulk-encode@axiom",
             "-c", "user.name=bulk-encode", "commit", "-q", "-m", f"wip: {citation}"])
        roots = subprocess.run([str(COV_PY), str(leaf / "bulk/roots_for.py"), module],
                               capture_output=True, text=True).stdout.strip() or "us"
        for gate in (
            [str(GEN_AE), "guard-generated", "--repo", str(leaf),
             "--base-ref", "origin/main", "--head-ref", "HEAD", "--roots", roots],
            [str(GEN_AE), "validate", str(leaf / module), "--skip-reviewers"],
            [str(GEN_AE), "proof-validate", str(leaf / module)],
        ):
            grc, gout = run(gate, cwd=leaf, env=env)
            if grc != 0:
                res["detail"] = f"gate failed: {gate[1]}\n{gout[-800:]}"
                return res
        trc, _ = run([str(GEN_AE), "test", "--root", str(leaf),
                      "--axiom-rules-engine-path", str(ENGINE), str(leaf / test_file)],
                     cwd=leaf, env=env)
        gate_status = "green" if trc == 0 else "needs-fixtures"

        # declare oracle-coverage pending lane (the step the cloud dispatcher lacks)
        sync_summary = sync_pending(leaf)
        keep_pending = finalize_pending(leaf)
        regen_index(leaf)

        branch = f"bulk/{slug}"
        title = f"Encode {citation} (bulk)"
        if gate_status == "needs-fixtures":
            title = f"Encode {citation} (bulk, needs-fixtures)"
        add_files = [*composition_files, ".axiom/index/provisions_to_rules.json"]
        if keep_pending:
            add_files.append("oracle-coverage-pending.yaml")
        run(["git", "-C", str(leaf), "add", "--", *add_files])
        commit_msg = (f"Encode {citation} via local drain\n\n"
                      f"Produced by axiom-encode encode {citation} --apply "
                      f"(backend {BACKEND}, model {MODEL}, pinned encoder). "
                      f"{sync_summary}\n\n"
                      "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>")
        run(["git", "-C", str(leaf), "-c", "user.email=bulk-encode@axiom",
             "-c", "user.name=bulk-encode", "commit", "-q", "--amend", "-m", commit_msg])
        open_prs = gh_json(
            ["pr", "list", "--repo", REPO, "--state", "open", "--head", branch,
             "--json", "number"]
        )
        if open_prs is None:
            return pause_for_retry(
                res,
                f"could not verify PR state for {branch} before push; retry drain",
            )
        if open_prs:
            ensure_draft_pr(branch)
            res["status"] = "skipped"
            res["detail"] = f"existing draft PR normalized for {branch}; no push performed"
            return res
        require_coverage_ref()
        run(["git", "-C", str(leaf), "push", "-f", "origin",
             f"HEAD:refs/heads/{branch}"], check=True)
        run(["gh", "label", "create", "bulk-encode", "--repo", REPO,
             "--color", "1f6feb", "-d", "Opened by the bulk-encode dispatcher"])
        acceptance_criteria = item.get("acceptance_criteria", "")
        body = (f"## Locally bulk-encoded module\n\n- Citation: `{citation}`\n"
                f"- Module: `{module}`\n- Encoder: `{BACKEND}:{MODEL}` "
                f"(toolchain-pinned axiom-encode)\n- Local gate: **{gate_status}**\n"
                f"- ProgramSpec sync: `{', '.join(composition_files) or 'none'}`\n"
                f"- {sync_summary}\n\nProduced by `bulk/local_drain.py` "
                "(local Codex mirror of the bulk-encode dispatcher). The "
                "authoritative gate is the required `validate / validate` check.\n\n"
                f"### Acceptance criteria\n\n{acceptance_criteria}\n")
        bf = WT_ROOT / slug / "pr-body.md"
        bf.write_text(body)
        run(
            ["gh", "pr", "create", "--repo", REPO, "--base", "main", "--head", branch,
             "--title", title, "--body-file", str(bf), "--label", "bulk-encode",
             "--draft"],
            check=True,
        )
        ensure_draft_pr(branch)
        res["status"] = gate_status
        res["detail"] = f"draft PR opened on {branch}; {sync_summary}"
        return res
    except subprocess.TimeoutExpired:
        res["detail"] = "encode timed out (>3600s)"
        return res
    finally:
        drop_worktree(leaf)


# --- worklist status flips (small, reviewable, batched) ---------------------
def flip_statuses(updates: dict) -> None:
    """updates: {citation: status}. Commits to worklist on a small branch + PR."""
    if not updates:
        return
    branch = "bulk/worklist-status-flip"
    open_prs = gh_json(
        [
            "pr",
            "list",
            "--repo",
            REPO,
            "--state",
            "open",
            "--head",
            branch,
            "--json",
            "number",
        ]
    )
    if open_prs is None:
        raise RuntimeError(f"could not determine whether {branch} already has a PR")
    existing_pr = bool(open_prs)
    if existing_pr:
        ensure_draft_pr(branch)

    leaf = make_worktree("worklist-flip", "origin/main")
    try:
        if existing_pr:
            run(["git", "-C", str(leaf), "fetch", "origin", branch], check=True)
            run(["git", "-C", str(leaf), "checkout", "-B", branch, "FETCH_HEAD"], check=True)
            run(["git", "-C", str(leaf), "rebase", "origin/main"], check=True)
        else:
            run(["git", "-C", str(leaf), "checkout", "-B", branch], check=True)
        for citation, status in updates.items():
            run([str(COV_PY), str(leaf / "bulk/compute_matrix.py"),
                 "--set-status", citation, status], cwd=leaf, check=True)
        _, worklist_diff = run(
            ["git", "-C", str(leaf), "status", "--porcelain", "--", "bulk/worklist.yaml"]
        )
        if worklist_diff:
            run(["git", "-C", str(leaf), "add", "bulk/worklist.yaml"])
            run(["git", "-C", str(leaf), "-c", "user.email=bulk-encode@axiom",
                 "-c", "user.name=bulk-encode", "commit", "-q", "-m",
                 "Flip drained worklist statuses (bulk)\n\n"
                 "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"], check=True)
        elif not existing_pr:
            return
        if existing_pr:
            ensure_draft_pr(branch)
        run(["git", "-C", str(leaf), "push", "-f", "origin",
             f"HEAD:refs/heads/{branch}"], check=True)
        if not existing_pr:
            run(["gh", "pr", "create", "--repo", REPO, "--base", "main",
                 "--head", branch, "--title", "Flip drained worklist statuses (bulk)",
                 "--body", "Status flips for locally-drained entries.", "--label",
                 "bulk-encode", "--draft"], check=True)
        ensure_draft_pr(branch)
    finally:
        drop_worktree(leaf)


# --- PROGRESS.md ------------------------------------------------------------
def write_progress(results: list, remaining: int, paused: bool) -> None:
    p = CHECKOUT / "bulk" / "PROGRESS-local-drain.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# Local drain progress ({now})", ""]
    if paused:
        lines += ["> **PAUSED on a retryable condition.** Resolve the condition "
                  "reported below and re-run; the drain resumes idempotently.", ""]
    lines += [f"- Remaining pending: {remaining}",
              f"- Handled this run: {len(results)}", "",
              "| citation | result | detail |", "| --- | --- | --- |"]
    for r in results:
        d = r["detail"].splitlines()[0][:80] if r["detail"] else ""
        lines.append(f"| `{r['citation']}` | {r['status']} | {d} |")
    p.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
def require_coverage_ref() -> str:
    if not COV_CHECKOUT.is_dir():
        raise SystemExit(f"coverage encoder checkout is missing: {COV_CHECKOUT}")
    rc, head = run(
        ["git", "rev-parse", "HEAD"],
        cwd=COV_CHECKOUT,
        merge_stderr=False,
    )
    actual = head.strip() if rc == 0 else "unavailable"
    if actual != COV_ENCODER_REF:
        raise SystemExit(
            f"coverage encoder checkout must be {COV_ENCODER_REF}; got {actual}"
        )
    rc, remote_head = run(
        ["git", "ls-remote", COV_ENCODER_REMOTE, "refs/heads/main"],
        merge_stderr=False,
    )
    remote_fields = remote_head.split()
    current_ci_ref = remote_fields[0] if rc == 0 and remote_fields else "unavailable"
    if current_ci_ref != COV_ENCODER_REF:
        raise SystemExit(
            "coverage encoder ref no longer matches CI's remote main: "
            f"local {COV_ENCODER_REF}; CI {current_ci_ref}"
        )
    rc, dirty = run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=COV_CHECKOUT,
        merge_stderr=False,
    )
    if rc != 0 or dirty.strip():
        raise SystemExit(f"coverage encoder checkout must be clean: {COV_CHECKOUT}")
    if not COV_PY.is_file():
        raise SystemExit(f"coverage encoder interpreter is missing: {COV_PY}")
    if not COV_AE.is_file():
        raise SystemExit(f"coverage encoder executable is missing: {COV_AE}")
    rc, module_file = run(
        [
            str(COV_PY),
            "-c",
            "import axiom_encode; print(axiom_encode.__file__)",
        ],
        merge_stderr=False,
    )
    if rc != 0:
        raise SystemExit(f"coverage encoder import failed via {COV_PY}")
    imported_module = Path(module_file.strip()).resolve()
    expected_module = (COV_CHECKOUT / "src/axiom_encode/__init__.py").resolve()
    if imported_module != expected_module:
        raise SystemExit(
            f"coverage encoder imports {imported_module}; expected {expected_module}"
        )
    expected_executable = COV_PY.parent / "axiom-encode"
    if COV_AE.resolve() != expected_executable.resolve():
        raise SystemExit(
            f"coverage executable must be {expected_executable}; got {COV_AE}"
        )
    rc, oracle_ref = run(
        [
            str(COV_PY),
            "-c",
            (
                "import importlib.metadata,json; "
                "d=importlib.metadata.distribution('axiom-oracles'); "
                "u=json.loads(d.read_text('direct_url.json')); "
                "print(u.get('vcs_info',{}).get('commit_id',''))"
            ),
        ],
        env={"AXIOM_ENCODE_APPLY_SIGNING_KEY": None},
        merge_stderr=False,
    )
    actual_oracle_ref = oracle_ref.strip() if rc == 0 else "unavailable"
    if actual_oracle_ref != COV_ORACLES_REF:
        raise SystemExit(
            f"coverage oracle dependency must be {COV_ORACLES_REF}; "
            f"got {actual_oracle_ref}"
        )
    return actual


def cmd_doctor(_args) -> int:
    tc = pinned_toolchain()
    print(f"DRAIN_BASE           : {DRAIN_BASE}")
    command_ok = True
    for label, ae, required_commands in (
        ("gen encoder (pin)", GEN_AE, ("encode",)),
        ("current encoder", COV_AE,
         ("oracle-coverage-pending", "program-scope-sync")),
    ):
        clean_signing_env = {"AXIOM_ENCODE_APPLY_SIGNING_KEY": None}
        has_pending = ae.exists() and run(
            [str(ae), "oracle-coverage-pending", "--help"],
            env=clean_signing_env,
        )[0] == 0
        has_scope_sync = ae.exists() and run(
            [str(ae), "program-scope-sync", "--help"],
            env=clean_signing_env,
        )[0] == 0
        available = {
            "encode": ae.exists() and run(
                [str(ae), "encode", "--help"], env=clean_signing_env
            )[0] == 0,
            "oracle-coverage-pending": has_pending,
            "program-scope-sync": has_scope_sync,
        }
        ok = ae.exists() and all(available[command]
                                 for command in required_commands)
        command_ok = command_ok and ok
        print(f"{label:20s}: {'OK' if ok else 'CHECK'} "
              f"(commands: {', '.join(command for command in required_commands if available[command])})")
    try:
        actual_cov_ref = require_coverage_ref()
        cov_ref_ok = True
    except SystemExit:
        actual_cov_ref = "unavailable or mismatched"
        cov_ref_ok = False
    print(f"coverage encoder ref: {'OK' if cov_ref_ok else 'CHECK'} "
          f"({actual_cov_ref}; want {COV_ENCODER_REF})")
    print(f"pinned encoder ver   : {tc.get('axiom_encode_version')}")
    engine_ok = ENGINE_BIN.exists()
    corpus_ok = CORPUS.exists()
    print(f"engine bin           : {'OK' if engine_ok else 'MISSING'} {ENGINE_BIN}")
    print(f"corpus               : {'OK' if corpus_ok else 'MISSING'} {CORPUS}")
    try:
        print(f"signing key          : present (len {len(signing_key())})")
        signing_ok = True
    except SystemExit as e:
        print(f"signing key          : {e}")
        signing_ok = False
    rc, out = run(["codex", "--version"])
    print(f"codex CLI            : {'OK ' + out.strip() if rc == 0 else 'MISSING'}")
    return 0 if all(
        (command_ok, cov_ref_ok, engine_ok, corpus_ok, signing_ok, rc == 0)
    ) else 1


def cmd_unstick(args) -> int:
    prs = open_bulk_prs()
    if args.pr:
        targets = [p for p in prs if p["number"] in set(args.pr)]
    elif args.all:
        targets = [p for p in prs if p["validate"] in (None, "FAILURE", "ERROR", "PENDING")]
    else:
        print("Specify --pr N [N ...] or --all. Open bulk PRs:")
        for p in prs:
            print(f"  #{p['number']:4d} {p['branch']:40s} validate={p['validate']} merge={p['merge']}")
        return 0
    if targets:
        require_coverage_ref()
    log(f"unstick {len(targets)} PR(s): {[p['number'] for p in targets]}")
    for p in targets:
        try:
            log(f"#{p['number']} {p['branch']}: {unstick_pr(p['branch'], wait=args.wait)}")
        except Exception as exc:  # noqa: BLE001 - operator tool, report and continue
            log(f"#{p['number']} {p['branch']}: ERROR {exc}")
    return 0


def cmd_drain(args) -> int:
    require_coverage_ref()
    matrix = json.loads(subprocess.run(
        [str(COV_PY), str(CHECKOUT / "bulk/compute_matrix.py"),
         "--status", args.status, "--format", "matrix",
         *(["--batch", args.batch] if args.batch else []),
         *(["--limit", str(args.limit)] if args.limit else [])],
        capture_output=True, text=True, cwd=CHECKOUT).stdout)["include"]
    handled = handled_slugs()
    failed_path = DRAIN_BASE / "drain_failed.json"
    failed = set(json.loads(failed_path.read_text())) if failed_path.exists() else set()
    matrix = [it for it in matrix
              if it["slug"] not in handled and it["citation"] not in failed]
    if args.max_entries:
        matrix = matrix[: args.max_entries]
    log(f"drain: {len(handled)} already PR'd, {len(failed)} known-failed -> "
        f"{len(matrix)} to attempt; concurrency={args.concurrency}, "
        f"max_seconds={args.max_seconds}")
    results, flips = [], {}
    deadline = time.time() + args.max_seconds
    # Rolling bounded pool: keep `concurrency` encodes in flight; stop launching
    # NEW work once the chunk deadline passes or a limit signal pauses us, then
    # let in-flight finish. already_handled() skips already-PR'd entries fast, so
    # the window advances past done work without re-encoding it.
    it = iter(matrix)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        inflight = set()
        for _ in range(args.concurrency):
            item = next(it, None)
            if item is not None:
                inflight.add(ex.submit(encode_entry, item))
        while inflight:
            done, inflight = concurrent.futures.wait(
                inflight, return_when=concurrent.futures.FIRST_COMPLETED)
            for fut in done:
                r = fut.result()
                results.append(r)
                log(f"{r['citation']}: {r['status']} - "
                    f"{r['detail'].splitlines()[0] if r['detail'] else ''}")
                if r["status"] in ("green", "needs-fixtures"):
                    flips[r["citation"]] = ("pr-open" if r["status"] == "green"
                                            else "needs-fixtures")
                elif r["status"] == "failed":
                    flips[r["citation"]] = "failed"
                if not _PAUSE.is_set() and time.time() < deadline:
                    item = next(it, None)
                    if item is not None:
                        inflight.add(ex.submit(encode_entry, item))
    remaining = int(subprocess.run(
        [str(COV_PY), str(CHECKOUT / "bulk/compute_matrix.py"),
         "--status", args.status, "--format", "count"],
        capture_output=True, text=True, cwd=CHECKOUT).stdout or 0)
    write_progress(results, remaining, _PAUSE.is_set())
    # Persist flips durably to a file and batch them into ONE worklist PR later
    # (`local_drain.py flip`), instead of a per-chunk PR that would thrash under
    # rapid draining. already_handled() provides idempotency regardless.
    if flips:
        flip_path = DRAIN_BASE / "drain_flips.json"
        existing = json.loads(flip_path.read_text()) if flip_path.exists() else {}
        existing.update(flips)
        flip_path.write_text(json.dumps(existing, indent=2, sort_keys=True))
    new_failed = {r["citation"] for r in results if r["status"] == "failed"}
    if new_failed:
        failed |= new_failed
        failed_path.write_text(json.dumps(sorted(failed), indent=1))
    log(f"chunk done: opened/gated={sum(1 for r in results if r['status'] in ('green','needs-fixtures'))} "
        f"failed={len(new_failed)} attempted={len(results)}, paused={_PAUSE.is_set()}")
    return 0


def cmd_flip(_args) -> int:
    """Batch the accumulated drain status flips into one worklist PR."""
    flip_path = DRAIN_BASE / "drain_flips.json"
    if not flip_path.exists():
        print("No accumulated flips.")
        return 0
    flips = json.loads(flip_path.read_text())
    if not flips:
        print("No accumulated flips.")
        return 0
    log(f"flipping {len(flips)} worklist statuses in one PR")
    flip_statuses(flips)
    flip_path.write_text("{}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("drain", help="Encode worklist entries via local Codex.")
    d.add_argument("--status", choices=("pending", "pending-local"),
                   default="pending")
    d.add_argument("--limit", type=int)
    d.add_argument("--batch")
    d.add_argument("--concurrency", type=int, default=3)
    d.add_argument("--max-entries", type=int)
    d.add_argument("--max-seconds", type=int, default=540)
    d.set_defaults(func=cmd_drain)
    u = sub.add_parser("unstick", help="Sync-declare + rebase open new-state bulk PRs.")
    u.add_argument("--pr", type=int, nargs="*", default=[])
    u.add_argument("--all", action="store_true")
    u.add_argument("--wait", action="store_true", help="Poll each PR until CI finishes.")
    u.set_defaults(func=cmd_unstick)
    doc = sub.add_parser("doctor", help="Verify toolchain, auth, signing key.")
    doc.set_defaults(func=cmd_doctor)
    fl = sub.add_parser("flip", help="Batch accumulated drain status flips into one PR.")
    fl.set_defaults(func=cmd_flip)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
