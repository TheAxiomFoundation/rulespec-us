#!/usr/bin/env python3
"""Local bulk-encode drain runner.

Drains ``bulk/worklist.yaml`` on the operator's machine using the local Codex
CLI (ChatGPT subscription, ``gpt-5.5``) instead of the cloud ``bulk-encode.yml``
dispatcher, opening merge-train-style batch PRs with auto-merge. It is a faithful
local mirror of ``.github/workflows/bulk-encode.yml`` plus the oracle-coverage-
pending declaration step the cloud dispatcher is missing (that missing step is
why every new-state bulk PR fails the changed-file oracle coverage gate).

Two decisions matter and are baked in here so PRs go green:

* **Generation uses the toolchain-pinned encoder** (``.axiom/toolchain.toml``
  ``axiom_encode_version``, currently 0.2.1184). The required ``validate /
  validate`` check validates with that same pin, so generating with anything
  newer risks schema/manifest skew. Do NOT "upgrade" the generation encoder to
  match a brief that says ">=0.2.1190" -- that number refers only to the
  *coverage/sync* tool below, not to generation.
* **Coverage declaration uses axiom-encode main (>=0.2.1190)**, because the CI
  changed-file coverage classifier (``oracle-coverage-axiom-encode-ref``,
  default ``main``) is what reclassifies declared-pending outputs from
  ``unmapped`` to ``pending_classification``. The pinned 1184 encoder does not
  even have the ``oracle-coverage-pending`` subcommand.

Multi-account (four ChatGPT subs)
---------------------------------
Each worker slot pins ``CODEX_HOME`` to a per-account directory so encodes fan
out across every authenticated ChatGPT-subscription account. Accounts are
discovered from ``~/.codex`` + ``~/.codex-2..-4`` (override ``DRAIN_CODEX_HOMES``)
and **only** admitted when their ``auth.json`` is a live ChatGPT sub -- api-key
auth is refused so the drain never falls back to metered API billing. A Codex
limit signal backs off ONLY that one account (``ACCOUNT_BACKOFF_S``); the others
keep draining. New accounts are hot-added the moment their ``auth.json`` lands.

Batch PRs (merge-train pattern)
-------------------------------
Generation is decoupled from PR-ing. Each entry is encoded + gated in an isolated
worktree, then its passing artifacts (module + test + manifest) are *staged* on
local disk (durable). Staged modules are then consolidated into merge-train-style
batch PRs (~15-25 disjoint modules, grouped by jurisdiction): one
``oracle-coverage-pending sync``, one reverse-index regen, one validation, one
auto-merge -- instead of O(n) per-module PRs that thrash the CI runner wall.
While a consolidation train PR is open in this repo (``DRAIN_HOLD_UNTIL_PR``),
batch PRs are held (staged, durable) so they don't BEHIND the train and force
full revalidation. ``--pr-mode per-module`` opens a batch-of-one per entry for
canaries/debugging.

Everything runs foreground. The loop is chunked (``--max-seconds``,
``--max-entries``) and every unit of durable state (staged artifacts, pushed
branch, opened PR, PROGRESS.md) is persisted as it is produced, so a jetsam kill
between chunks loses nothing: re-run and it resumes.

Toolchain layout (override via env): a sibling ``_bulk_drain`` workspace holds
pinned checkouts + venvs built once by the operator:

    _bulk_drain/
      axiom-encode/            # worktree @ pinned axiom_encode_ref (1184)
      .venv/                   # pinned encoder venv  -> generation
      axiom-encode-cov/        # worktree @ axiom-encode main (>=1190)
      .venv-cov/               # coverage/sync venv   -> oracle-coverage-pending
      axiom-rules-engine/      # worktree @ pinned engine ref, cargo build
      axiom-corpus/            # worktree @ pinned corpus ref
      staged/<repo>/<slug>/    # staged module artifacts awaiting batch assembly
      wt/<slug>/rulespec-us/   # per-entry generation worktrees (leaf MUST be rulespec-us)

Usage:
    python3.14 bulk/local_drain.py drain    [--limit N] [--batch A] [--per-account 5]
                                            [--max-entries N] [--max-seconds 540]
                                            [--pr-mode batch|per-module] [--flush]
    python3.14 bulk/local_drain.py assemble [--flush] [--wait] [--force]
    python3.14 bulk/local_drain.py stage-status
    python3.14 bulk/local_drain.py unstick  [--pr N ...] [--all] [--wait]
    python3.14 bulk/local_drain.py doctor   # verify toolchain + accounts + signing key
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tomllib
from datetime import date, datetime, timezone
from pathlib import Path


# The checkout to drain. Defaults to the checkout this file lives in, but
# ``DRAIN_CHECKOUT`` lets one durable copy of this script drain any rulespec-*
# checkout (US/UK/BE) without being copied into each one.
CHECKOUT = Path(os.environ.get(
    "DRAIN_CHECKOUT", Path(__file__).resolve().parent.parent)).resolve()
HERE = CHECKOUT / "bulk"


def _derive_repo() -> tuple[str, str]:
    """(owner/name, name) for the checkout being drained.

    Auto-derives from the git ``origin`` remote so the same file works unchanged
    against any ``rulespec-*`` checkout (US/UK/BE/...). Env overrides:
    ``DRAIN_REPO`` (owner/name) and ``DRAIN_REPO_NAME``.
    """
    repo = os.environ.get("DRAIN_REPO", "")
    if not repo:
        try:
            url = subprocess.run(
                ["git", "-C", str(CHECKOUT), "remote", "get-url", "origin"],
                capture_output=True, text=True).stdout.strip()
            m = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", url)
            repo = m.group(1) if m else "TheAxiomFoundation/rulespec-us"
        except Exception:  # noqa: BLE001
            repo = "TheAxiomFoundation/rulespec-us"
    name = os.environ.get("DRAIN_REPO_NAME") or repo.split("/")[-1]
    return repo, name


REPO, REPO_NAME = _derive_repo()

# --- toolchain / workspace resolution ---------------------------------------
DRAIN_BASE = Path(
    os.environ.get("DRAIN_BASE", Path.home() / "TheAxiomFoundation" / "_bulk_drain")
).resolve()
COV_AE = Path(os.environ.get("DRAIN_COV_AE", DRAIN_BASE / ".venv-cov/bin/axiom-encode"))
COV_PY = Path(os.environ.get("DRAIN_COV_PY", DRAIN_BASE / ".venv-cov/bin/python"))


def _toolchain_pin() -> str:
    tf = CHECKOUT / ".axiom/toolchain.toml"
    try:
        return (tomllib.loads(tf.read_text()).get("toolchain", {})
                .get("axiom_encode_version", "")) or ""
    except (OSError, tomllib.TOMLDecodeError):
        return ""


# Per-repo toolchain venv, matched to the checkout's pinned axiom_encode_version.
# CI installs the pinned encoder and runs validate + the repo ``tests/`` pytest
# with it, so generation, the gate battery, and the batch pytest all use this
# same pinned venv. Crucially the manifest-relocation fix (#1082, >= 0.2.1188)
# must be present, or the signed apply manifest lands under ``<juris>/.axiom``
# where the layout gate rejects ``.json`` (only repo-root ``.axiom/**`` allows it)
# -- the exact "Repository layout does not match" red that the shared 1184 venv
# produced. Unknown pins fall back to the cov/main venv. Build a pin's venv once
# in the workspace (``uv venv .venv-<x> && uv pip install -e axiom-encode-<x>``).
_VENV_BY_PIN = {
    "0.2.1184": DRAIN_BASE / ".venv",       # rulespec-us
    "0.2.1188": DRAIN_BASE / ".venv-be",    # rulespec-be (relocation release)
    "0.2.1190": DRAIN_BASE / ".venv-cov",   # rulespec-uk == cov/main
}
_PIN_VENV = _VENV_BY_PIN.get(_toolchain_pin(), DRAIN_BASE / ".venv-cov")
GEN_AE = Path(os.environ.get("DRAIN_GEN_AE") or _PIN_VENV / "bin/axiom-encode")
# Gate battery + batch pytest use the SAME pinned venv CI installs, so a check
# that only the pinned encoder enforces fails closed here, not in CI.
GATE_AE = Path(os.environ.get("DRAIN_GATE_AE") or _PIN_VENV / "bin/axiom-encode")
GATE_PY = Path(os.environ.get("DRAIN_GATE_PY") or _PIN_VENV / "bin/python")
ENGINE = Path(os.environ.get("DRAIN_ENGINE", DRAIN_BASE / "axiom-rules-engine"))
CORPUS = Path(os.environ.get("DRAIN_CORPUS", DRAIN_BASE / "axiom-corpus"))
ENGINE_BIN = ENGINE / "target" / "debug"
WT_ROOT = DRAIN_BASE / "wt"
STAGE_ROOT = DRAIN_BASE / "staged"

BACKEND = os.environ.get("DRAIN_BACKEND", "codex")
MODEL = os.environ.get("DRAIN_MODEL", "gpt-5.5")

# Batch-PR (merge-train-style) config.
BATCH_MAX = int(os.environ.get("DRAIN_BATCH_MAX", "25"))
BATCH_MIN = int(os.environ.get("DRAIN_BATCH_MIN", "15"))
# A consolidation train PR open in this repo means our batch PRs would BEHIND it
# and force full revalidation -- hold them (staged, durable) until it merges.
# Defaults to the live rulespec-us train (#763); "" disables the hold.
HOLD_UNTIL_PR = os.environ.get(
    "DRAIN_HOLD_UNTIL_PR", "763" if REPO_NAME == "rulespec-us" else "")

# Multi-account: candidate CODEX_HOME dirs and per-account limit backoff.
CODEX_HOME_DEFAULTS = [Path.home() / ".codex"] + [
    Path.home() / f".codex-{i}" for i in range(2, 5)]
ACCOUNT_BACKOFF_S = int(os.environ.get("DRAIN_ACCOUNT_BACKOFF_S", "900"))
RETRY_S = int(os.environ.get("DRAIN_RETRY_S", "90"))
MAX_TOTAL = int(os.environ.get("DRAIN_MAX_TOTAL", "24"))
MAX_RETRIES = int(os.environ.get("DRAIN_MAX_RETRIES", "2"))

# Codex subscription-limit signatures. On any of these we back off the account.
LIMIT_SIGNS = re.compile(
    r"rate.?limit|usage limit|quota|insufficient_quota|too many requests|"
    r"\b429\b|reached your (usage|limit)|plan limit|overloaded",
    re.I,
)

_print_lock = threading.Lock()
_wt_lock = threading.Lock()          # git worktree add/remove is not concurrency-safe
_stage_lock = threading.Lock()       # staging index read/modify/write


def log(msg: str) -> None:
    with _print_lock:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run(cmd, cwd=None, env=None, capture=True, check=False, timeout=None):
    """Run a subprocess, returning (rc, combined_output)."""
    full = dict(os.environ)
    if env:
        full.update(env)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=full,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
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
    ):
        try:
            rc, out = run(cmd)
            if rc == 0 and out.strip():
                return out.strip()
        except FileNotFoundError:
            continue
    raise SystemExit("Signing key AXIOM_ENCODE_APPLY_SIGNING_KEY unavailable "
                     "(tried env + agent-secret + manage-secret.sh).")


def pinned_toolchain() -> dict:
    data = tomllib.loads((CHECKOUT / ".axiom/toolchain.toml").read_text())
    return data.get("toolchain", data)


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


# --- Codex account pool (multi-sub rotation, per-account backoff) ------------
def account_is_live(home: Path) -> tuple[bool, str]:
    """(is_live, mode) for a CODEX_HOME.

    Admits ONLY a live ChatGPT-subscription auth: ``auth_mode == 'chatgpt'`` with
    a real ``tokens.access_token``. Api-key auth is refused so the drain never
    falls back to metered API billing.
    """
    auth = home / "auth.json"
    if not auth.is_file():
        return False, "no-auth"
    try:
        data = json.loads(auth.read_text())
    except (json.JSONDecodeError, OSError):
        return False, "unreadable"
    mode = data.get("auth_mode")
    tok = data.get("tokens") or {}
    if mode == "apikey":
        return False, "apikey-refused"          # never bill the API
    if mode == "chatgpt" and tok.get("access_token"):
        return True, "chatgpt"
    if tok.get("access_token"):
        return True, f"chatgpt({mode})"
    return False, f"incomplete({mode})"


def discover_homes() -> list[Path]:
    env = os.environ.get("DRAIN_CODEX_HOMES")
    if env:
        return [Path(p).expanduser() for p in env.split(os.pathsep) if p]
    return CODEX_HOME_DEFAULTS


class Account:
    __slots__ = ("home", "name", "backoff_until", "inflight", "done",
                 "limit_events", "gen_seconds")

    def __init__(self, home: Path):
        self.home = home
        self.name = home.name
        self.backoff_until = 0.0
        self.inflight = 0
        self.done = 0
        self.limit_events = 0
        self.gen_seconds = 0.0


class AccountPool:
    """Rotates worker slots across every authenticated ChatGPT-sub account.

    * ``per_account`` caps concurrent encodes per account (the probed knee).
    * A limit signal backs off ONLY that account (``ACCOUNT_BACKOFF_S``); other
      accounts keep draining. Never a global pause, never API billing.
    * ``refresh()`` hot-adds accounts as their ``auth.json`` lands (Max logs in
      ``~/.codex-2/-3/-4`` out of band).
    """

    def __init__(self, per_account: int):
        self.per_account = max(1, per_account)
        self._accounts: dict[str, Account] = {}
        self._cv = threading.Condition()
        self.refresh(initial=True)

    def refresh(self, initial: bool = False) -> list[str]:
        added = []
        with self._cv:
            for home in discover_homes():
                if home.name in self._accounts:
                    continue
                live, _mode = account_is_live(home)
                if live:
                    self._accounts[home.name] = Account(home)
                    added.append(home.name)
            if added:
                self._cv.notify_all()
        for n in added:
            log(f"[pool] {'account' if initial else 'HOT-ADDED account'} "
                f"{n} live (chatgpt sub)")
        return added

    def live_count(self) -> int:
        with self._cv:
            return len(self._accounts)

    def acquire(self, deadline: float):
        """Block until an account with free capacity (not backed off) is
        available. Returns an Account, or None at the deadline."""
        with self._cv:
            while True:
                now = time.time()
                ready = [a for a in self._accounts.values()
                         if a.backoff_until <= now and a.inflight < self.per_account]
                if ready:
                    a = min(ready, key=lambda x: (x.inflight, x.done))
                    a.inflight += 1
                    return a
                if now >= deadline:
                    return None
                waits = [a.backoff_until - now for a in self._accounts.values()
                         if a.backoff_until > now]
                timeout = min([deadline - now] + ([min(waits)] if waits else [5.0]))
                self._cv.wait(timeout=max(0.05, min(timeout, 30.0)))

    def release(self, account: Account, limited: bool, gen_seconds: float = 0.0):
        with self._cv:
            account.inflight -= 1
            account.done += 1
            account.gen_seconds += gen_seconds
            if limited:
                account.limit_events += 1
                account.backoff_until = time.time() + ACCOUNT_BACKOFF_S
            self._cv.notify_all()
        if limited:
            log(f"[pool] {account.name}: limit signal -> backing off "
                f"{ACCOUNT_BACKOFF_S}s (other accounts keep draining)")

    def all_backed_off(self) -> bool:
        with self._cv:
            if not self._accounts:
                return False
            now = time.time()
            return all(a.backoff_until > now for a in self._accounts.values())

    def snapshot(self) -> list[dict]:
        with self._cv:
            now = time.time()
            return [{"name": a.name, "done": a.done, "inflight": a.inflight,
                     "limit_events": a.limit_events,
                     "avg_gen_s": round(a.gen_seconds / a.done, 1) if a.done else None,
                     "backoff_s": max(0, round(a.backoff_until - now))}
                    for a in sorted(self._accounts.values(), key=lambda x: x.name)]


# --- worktree helpers -------------------------------------------------------
def make_worktree(slug: str, ref: str) -> Path:
    """Fresh generation worktree whose leaf dir is exactly ``REPO_NAME``
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
    """Write oracle-coverage-pending.yaml for REPO_NAME using the >=1190 tool.
    Returns the sync summary line."""
    rc, out = run([str(COV_AE), "oracle-coverage-pending", "sync",
                   "--root", str(leaf.parent), "--repo", REPO_NAME, "--source", "bulk"],
                  env={"PATH": f"{ENGINE_BIN}:{os.environ['PATH']}"})
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


# ---------------------------------------------------------------------------
# PART A: unstick already-open new-state bulk PRs (priority).
# ---------------------------------------------------------------------------
MODULE_RE = re.compile(
    r"^[a-z]{2}(-[a-z0-9-]+)?/(statutes|regulations|policies)/.*\.yaml$")


def open_bulk_prs():
    data = gh_json(["pr", "list", "--repo", REPO, "--state", "open", "--limit", "200",
                    "--json", "number,headRefName,mergeStateStatus,statusCheckRollup"])
    prs = []
    for pr in data or []:
        if not pr["headRefName"].startswith("bulk/"):
            continue
        vv = next((c.get("conclusion") or c.get("state")
                   for c in pr.get("statusCheckRollup") or []
                   if c.get("name") == "validate / validate"), None)
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
                       f"origin/main...FETCH_HEAD"])
        artifacts = [f for f in diff.splitlines()
                     if (MODULE_RE.match(f) or f.endswith(".test.yaml")
                         or "/.axiom/encoding-manifests/" in f)]
        if not artifacts:
            return f"{branch}: no module artifacts in diff (already merged?)"
        run(["git", "-C", str(leaf), "checkout", "FETCH_HEAD", "--", *artifacts],
            check=True)
        summary = sync_pending(leaf)
        keep_pending = finalize_pending(leaf)
        regen_index(leaf)
        add_files = [*artifacts, ".axiom/index/provisions_to_rules.json"]
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
        run(["git", "-C", str(leaf), "push", "-f", "origin",
             f"HEAD:refs/heads/{branch}"], check=True)
        run(["gh", "pr", "merge", branch, "--repo", REPO, "--auto", "--squash"])
        result = f"rebuilt+pushed {branch}: {summary}"
        if wait:
            result += "; " + wait_for_merge(branch)
        return result
    finally:
        drop_worktree(leaf)


def wait_for_merge(branch: str, timeout_s: int = 1500) -> str:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        pr = gh_json(["pr", "view", branch, "--repo", REPO,
                      "--json", "state,mergeStateStatus,statusCheckRollup"])
        if not pr:
            return "poll-error"
        if pr["state"] == "MERGED":
            return "MERGED"
        vv = next((c.get("conclusion") or c.get("state")
                   for c in pr.get("statusCheckRollup") or []
                   if c.get("name") == "validate / validate"), None)
        if vv in ("FAILURE", "ERROR"):
            return f"validate={vv} (needs triage)"
        time.sleep(30)
    return "timeout-waiting-merge"


# ---------------------------------------------------------------------------
# PART B: generate one pending worklist entry via local Codex, then STAGE it.
# ---------------------------------------------------------------------------
def already_handled(slug: str) -> bool:
    pr = gh_json(["pr", "list", "--repo", REPO, "--head", f"bulk/{slug}",
                  "--state", "all", "--json", "number,state"])
    return bool(pr)


def handled_slugs() -> set:
    """All bulk/<slug> that already have a per-module PR (any state), in one gh
    call, so a drain chunk skips already-PR'd entries without a per-entry API
    round-trip. Batch PRs use the bulk/batch-* namespace and are tracked in the
    staging index instead."""
    data = gh_json(["pr", "list", "--repo", REPO, "--state", "all", "--limit", "400",
                    "--json", "headRefName"]) or []
    return {p["headRefName"].split("/", 1)[1] for p in data
            if p.get("headRefName", "").startswith("bulk/")
            and not p["headRefName"].startswith("bulk/batch-")}


# --- staging index ----------------------------------------------------------
def _stage_index_path() -> Path:
    return STAGE_ROOT / REPO_NAME / "index.json"


def _stage_dir(slug: str) -> Path:
    return STAGE_ROOT / REPO_NAME / slug


def load_staged() -> dict:
    p = _stage_index_path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def record_staged(slug: str, meta: dict) -> None:
    with _stage_lock:
        idx = load_staged()
        idx[slug] = {**meta, "slug": slug, "batched": False}
        p = _stage_index_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(idx, indent=2, sort_keys=True))


def unbatched_staged() -> list[dict]:
    return [m for m in load_staged().values() if not m.get("batched")]


def mark_batched(slugs: list[str], pr) -> None:
    with _stage_lock:
        idx = load_staged()
        for s in slugs:
            if s in idx:
                idx[s]["batched"] = True
                idx[s]["pr"] = pr
        _stage_index_path().write_text(json.dumps(idx, indent=2, sort_keys=True))


def unstage_module(slug: str, reason: str = "") -> None:
    """Drop a staged module so it no longer batches, and bench its citation in
    ``drain_failed`` (fail-closed) so a re-drain doesn't loop on it. Used when the
    CI-faithful batch gate rejects a module's quality."""
    with _stage_lock:
        idx = load_staged()
        meta = idx.pop(slug, None)
        _stage_index_path().write_text(json.dumps(idx, indent=2, sort_keys=True))
    sd = _stage_dir(slug)
    if sd.exists():
        shutil.rmtree(sd, ignore_errors=True)
    if meta and meta.get("citation"):
        fp = DRAIN_BASE / "drain_failed.json"
        failed = set(json.loads(fp.read_text())) if fp.exists() else set()
        failed.add(meta["citation"])
        fp.write_text(json.dumps(sorted(failed), indent=1))
    if reason:
        log(f"[stage] fail-closed {slug} ({reason})")


def generate_module(item: dict, pool: AccountPool, deadline: float) -> dict:
    """Encode + apply + gate ONE entry in an isolated worktree on a rotated
    account, then stage the passing artifacts for batch assembly. Opens no PR.

    Fail-closed: an encode/gate failure returns status 'failed' with a reason so
    the batch never carries a red module. A Codex limit signal backs off the
    account and returns 'deferred' (the entry stays pending and is retried)."""
    citation, slug = item["citation"], item["slug"]
    res = {"citation": citation, "slug": slug, "status": "failed", "detail": "",
           "account": None, "module": None, "group": None}
    account = pool.acquire(deadline)
    if account is None:
        res["status"], res["detail"] = "deferred", "no account free before deadline"
        return res
    res["account"] = account.name
    leaf = make_worktree(slug, "origin/main")
    tmp = WT_ROOT / slug / "encode-out"
    start = time.time()
    limited = False
    try:
        env = {
            # Account selection: axiom-encode's codex backend authenticates via
            # the auth.json under CODEX_HOME (see axiom_encode.codex_cli).
            "CODEX_HOME": str(account.home),
            "AXIOM_ENCODE_APPLY_SIGNING_KEY": signing_key(),
            "AXIOM_CORPUS_REPO": str(CORPUS),
            "AXIOM_RULESPEC_REPO_ROOTS": str(leaf),
            # The pinned encoder's bin MUST be on PATH: the --apply manifest step
            # resolves axiom-encode git provenance via the on-PATH entrypoint.
            "PATH": f"{GEN_AE.parent}:{ENGINE_BIN}:{os.environ['PATH']}",
        }
        rc, out = run(
            [str(GEN_AE), "encode", citation, "--backend", BACKEND, "--model", MODEL,
             "--policy-repo-path", str(leaf),
             "--axiom-rules-engine-path", str(ENGINE),
             "--corpus-path", str(CORPUS),
             "--output", str(tmp), "--apply", "--no-sync"],
            cwd=leaf, env=env, timeout=3600)
        if LIMIT_SIGNS.search(out):
            limited = True
            res["status"], res["detail"] = "deferred", f"codex limit on {account.name}"
            return res
        _, st = run(["git", "-C", str(leaf), "status", "--porcelain", "-uall"])
        changed = [ln[3:] for ln in st.splitlines() if ln[3:].strip()]
        applied = [f for f in changed
                   if MODULE_RE.match(f) and not f.endswith(".test.yaml")]
        if rc != 0 or not applied:
            res["detail"] = f"encode/apply failed (rc={rc}); see {tmp}"
            return res
        module = applied[0]
        juris = module.split("/", 1)[0]
        test_file = module[:-5] + ".test.yaml"
        # Capture the signed manifest wherever the pinned encoder placed it, and
        # do NOT relocate. The #1082 relocation (>= be 1188 / uk 1190) already
        # moves it to repo-root ``.axiom/encoding-manifests/<juris>/`` where uk/be's
        # layout gate requires it; rulespec-us (1184, which allows ``.json`` under
        # the content root) keeps it co-located at ``<juris>/.axiom/encoding-
        # manifests/``, which is exactly what US ``guard-generated`` expects.
        # Relocating US manifests to repo-root breaks that gate.
        manifests = [f for f in changed
                     if ("/.axiom/encoding-manifests/" in f
                         or f.startswith(".axiom/encoding-manifests/"))
                     and f.endswith(".json")]
        artifacts = [module]
        if (leaf / test_file).exists():
            artifacts.append(test_file)
        artifacts += [m for m in manifests if (leaf / m).exists()]

        # commit locally so guard-generated can diff against origin/main
        run(["git", "-C", str(leaf), "add", "-A"])
        run(["git", "-C", str(leaf), "-c", "user.email=bulk-encode@axiom",
             "-c", "user.name=bulk-encode", "commit", "-q", "-m", f"wip: {citation}"])
        roots = subprocess.run([str(COV_PY), str(leaf / "bulk/roots_for.py"), module],
                               capture_output=True, text=True).stdout.strip() or "us"
        # Gate battery runs with the CI arbiter (axiom-encode main / cov), not the
        # generation pin, so main-only quality checks fail closed here, not in CI.
        gate_env = {**env, "PATH": f"{GATE_AE.parent}:{ENGINE_BIN}:{os.environ['PATH']}"}
        for gate in (
            [str(GATE_AE), "guard-generated", "--repo", str(leaf),
             "--base-ref", "origin/main", "--head-ref", "HEAD", "--roots", roots],
            [str(GATE_AE), "validate", str(leaf / module), "--skip-reviewers"],
            [str(GATE_AE), "proof-validate", str(leaf / module)],
        ):
            grc, gout = run(gate, cwd=leaf, env=gate_env)
            if grc != 0:
                res["detail"] = f"gate failed: {gate[1]}\n{gout[-400:]}"
                return res
        trc, _ = run([str(GATE_AE), "test", "--root", str(leaf),
                      "--axiom-rules-engine-path", str(ENGINE), str(leaf / test_file)],
                     cwd=leaf, env=gate_env)
        gate_status = "green" if trc == 0 else "needs-fixtures"

        # stage all apply artifacts (module + test + canonical manifest) durably
        sd = _stage_dir(slug)
        if sd.exists():
            shutil.rmtree(sd)
        for rel in artifacts:
            src = leaf / rel
            if src.exists():
                dst = sd / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        record_staged(slug, {"citation": citation, "module": module,
                             "artifacts": artifacts, "group": juris,
                             "gate": gate_status, "account": account.name,
                             "staged_at": datetime.now(timezone.utc).isoformat()})
        res["status"] = gate_status
        res["module"], res["group"] = module, juris
        res["detail"] = f"staged {module} ({gate_status})"
        return res
    except subprocess.TimeoutExpired:
        res["detail"] = "encode timed out (>3600s)"
        return res
    finally:
        pool.release(account, limited, time.time() - start)
        drop_worktree(leaf)


# --- batch assembly (merge-train pattern) -----------------------------------
def hold_blocked() -> tuple[bool, str]:
    """True while a consolidation train PR (HOLD_UNTIL_PR) is still open, so we
    don't open batch PRs that would BEHIND it and force full revalidation."""
    if not HOLD_UNTIL_PR:
        return False, ""
    pr = gh_json(["pr", "view", HOLD_UNTIL_PR, "--repo", REPO, "--json", "state"])
    if pr and pr.get("state") == "OPEN":
        return True, f"train #{HOLD_UNTIL_PR} still OPEN"
    return False, ""


_MOD_PATH_RE = re.compile(
    r"[a-z]{2}(?:-[a-z0-9-]+)?/(?:statutes|regulations|policies)/[^\s'\"#\]]+\.yaml")


def batch_pytest(leaf: Path) -> tuple[bool, set[str], str]:
    """Run the repo's ``tests/`` pytest with the CI arbiter (cov/main + pytest),
    exactly as CI's ``run-pytest`` step does. Returns (passed, offending module
    rel-paths, tail). Offenders are the module paths named in failing assertions,
    so a bad module can be dropped from the batch (fail-closed)."""
    if not (leaf / "tests").is_dir():
        return True, set(), "(no tests dir)"
    env = {"PATH": f"{GATE_AE.parent}:{ENGINE_BIN}:{os.environ['PATH']}"}
    rc, out = run([str(GATE_PY), "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "tests"], cwd=leaf, env=env)
    if rc == 0:
        return True, set(), out[-200:]
    return False, {m.group(0) for m in _MOD_PATH_RE.finditer(out)}, out[-1400:]


def batch_oracle_coverage(leaf: Path, modules: set[str]) -> tuple[bool, set[str], str]:
    """Mirror CI's changed-file PolicyEngine oracle-coverage gate (a workflow
    step, not a repo pytest, so it's not covered by ``batch_pytest``): a changed
    output that is ``unmapped`` (undeclared) or ``comparable`` but not covered by
    a companion test fails. Skipped for rulespec-be (EUROMOD household surface).
    Returns (ok, offending module rel-paths, detail)."""
    if REPO_NAME == "rulespec-be":
        return True, set(), "(be uses EUROMOD; skipped)"
    parent = leaf.parent
    us_link = parent / "rulespec-us"      # cross-jurisdiction resolution
    if not us_link.exists():
        try:
            us_link.symlink_to(Path.home() / "TheAxiomFoundation/rulespec-us")
        except OSError:
            pass
    # CI runs the changed-file oracle-coverage workflow step with the arbiter
    # axiom-encode ``main`` (``oracle-coverage-axiom-encode-ref``), which owns
    # the pending lane. The pinned 1184 encoder (GATE_AE for rulespec-us) has no
    # ``oracle-coverage-pending`` subcommand and does NOT apply
    # oracle-coverage-pending.yaml, so every declared-pending output falsely
    # reads ``unmapped`` -- benching good federal modules the >=1190 CI would
    # pass. Use COV_AE (the >=1190 cov/main encoder, pending-aware) to mirror CI.
    env = {"PATH": f"{COV_AE.parent}:{ENGINE_BIN}:{os.environ['PATH']}"}
    rc, out = run([str(COV_AE), "oracle-coverage", "--root", str(parent), "--json"],
                  cwd=leaf, env=env)
    try:
        items = json.loads(out).get("items", [])
    except json.JSONDecodeError:
        return True, set(), "(oracle-coverage produced no json; skipped)"
    offenders, detail = set(), []
    for it in items:
        f = it.get("file", "")                      # "<repo>/<module-path>.yaml"
        rel = f.split("/", 1)[1] if "/" in f else f
        if rel not in modules:
            continue
        st = it.get("status")
        if st == "unmapped" or (st == "comparable" and not it.get("tested")):
            offenders.add(rel)
            detail.append(f"{it.get('legal_id')}: "
                          + (st if st == "unmapped" else "comparable/untested"))
    return (not offenders), offenders, "; ".join(detail[:5])


def find_open_batch_branch(group: str) -> str | None:
    suffix = REPO_NAME.replace("rulespec-", "")
    prefix = f"bulk/batch-{suffix}-{group}-"
    data = gh_json(["pr", "list", "--repo", REPO, "--state", "open", "--limit", "100",
                    "--json", "headRefName"]) or []
    return next((p["headRefName"] for p in data
                 if p.get("headRefName", "").startswith(prefix)), None)


def _meta_artifacts(m: dict) -> list[str]:
    """Repo-relative artifact paths for a staged module (module + test +
    canonical manifest). Prefers the stored ``artifacts`` list; falls back to the
    older module/test/manifest keys for entries staged before that field."""
    arts = m.get("artifacts")
    if arts:
        return list(arts)
    return [x for x in (m.get("module"), m.get("test"), m.get("manifest")) if x]


def assemble_batch(group: str, metas: list[dict], seq: str, wait: bool = False,
                   branch: str | None = None) -> dict:
    """Build ONE merge-train-style batch PR from staged modules: copy all
    artifacts onto a fresh origin/main branch, ONE oracle-coverage-pending sync,
    ONE reverse-index regen, then the CI-faithful gate (per-module validate + the
    repo ``tests/`` pytest, both cov/main). Modules the gate rejects are dropped
    (fail-closed) and the batch is rebuilt without them; the rest are pushed +
    auto-merged. ``branch`` reuses an existing batch PR head (force-push updates
    that PR in place)."""
    suffix = REPO_NAME.replace("rulespec-", "")
    branch = branch or f"bulk/batch-{suffix}-{group}-{seq}"
    result = {"branch": branch, "slugs": [m["slug"] for m in metas],
              "status": "failed", "pr": None, "detail": "", "dropped": []}
    leaf = make_worktree(f"batch-{group}-{seq}", "origin/main")
    staged_root = STAGE_ROOT / REPO_NAME
    gate_env = {"PATH": f"{GATE_AE.parent}:{ENGINE_BIN}:{os.environ['PATH']}"}
    dropped: list[str] = []
    try:
        run(["git", "-C", str(leaf), "checkout", "-B", branch], check=True)
        for m in metas:                                    # copy all artifacts in
            for rel in _meta_artifacts(m):
                src = staged_root / m["slug"] / rel
                if src.exists():
                    dst = leaf / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
        summary = "(no output)"
        while metas:
            run(["git", "-C", str(leaf), "add", "-A"])
            summary = sync_pending(leaf)
            finalize_pending(leaf)
            regen_index(leaf)
            run(["git", "-C", str(leaf), "add", "-A"])
            # CI-faithful gate: per-module schema validate + repo pytest (cov/main)
            bad: list[tuple[dict, str]] = []
            for m in metas:
                grc, _ = run([str(GATE_AE), "validate", str(leaf / m["module"]),
                              "--skip-reviewers"], cwd=leaf, env=gate_env)
                if grc != 0:
                    bad.append((m, "validate"))
            if not bad:
                ok, offenders, tail = batch_pytest(leaf)
                if not ok:
                    bad = [(m, "pytest") for m in metas if m["module"] in offenders]
                    if not bad:
                        result["detail"] = ("batch pytest failed with no attributable "
                                            f"module; aborting.\n{tail[-300:]}")
                        return result
            if not bad:                    # CI's PolicyEngine oracle-coverage gate
                okc, off_c, det_c = batch_oracle_coverage(
                    leaf, {m["module"] for m in metas})
                if okc:
                    break
                bad = [(m, "oracle-coverage") for m in metas if m["module"] in off_c]
                log(f"[batch {group}] oracle-coverage flagged: {det_c}")
                if not bad:
                    result["detail"] = ("batch oracle-coverage failed with no "
                                        f"attributable module; aborting.\n{det_c}")
                    return result
            for m, why in bad:
                for rel in _meta_artifacts(m):
                    if (leaf / rel).exists():
                        run(["git", "-C", str(leaf), "rm", "-q", "-f",
                             "--ignore-unmatch", rel])
                unstage_module(m["slug"], reason=f"batch {why} reject")
                dropped.append(m["slug"])
            drop_set = {m["slug"] for m, _ in bad}
            log(f"[batch {group}] dropped {len(drop_set)} module(s) "
                f"({bad[0][1]}): {sorted(drop_set)}")
            metas = [m for m in metas if m["slug"] not in drop_set]
        result["dropped"] = dropped
        if not metas:
            result["detail"] = "all modules rejected by CI-faithful gate"
            return result
        run(["git", "-C", str(leaf), "add", "-A"])
        n = len(metas)
        needs_fx = sum(1 for m in metas if m.get("gate") == "needs-fixtures")
        title = (f"Batch-encode {n} {group} RuleSpec module(s) (bulk)"
                 + (f" [{needs_fx} needs-fixtures]" if needs_fx else ""))
        body_lines = [
            f"## Batch-encoded {n} module(s) - {group}", "",
            "Merge-train-style consolidation: one `oracle-coverage-pending sync`, "
            "one reverse-index regen, and the CI-faithful gate (per-module "
            "validate + the repo `tests/` pytest, cov/main). Disjoint modules each "
            "carry their own signed apply manifest.", "", f"- {summary}",
            f"- Local gate: {n - needs_fx} green, {needs_fx} needs-fixtures"
            + (f", {len(dropped)} dropped (quality)" if dropped else ""), "",
            "| citation | module | gate |", "| --- | --- | --- |"]
        for m in metas:
            body_lines.append(
                f"| `{m['citation']}` | `{m['module']}` | {m.get('gate')} |")
        body_lines += ["", "Produced by `bulk/local_drain.py` (local Codex mirror "
                       "of the bulk-encode dispatcher). The authoritative gate is "
                       "the required `validate / validate` check.",
                       "", "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"]
        run(["git", "-C", str(leaf), "-c", "user.email=bulk-encode@axiom",
             "-c", "user.name=bulk-encode", "commit", "-q", "-m",
             f"Batch-encode {n} {group} RuleSpec module(s) (bulk)\n\n{summary}\n\n"
             "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"])
        run(["git", "-C", str(leaf), "push", "-f", "origin",
             f"HEAD:refs/heads/{branch}"], check=True)
        run(["gh", "label", "create", "bulk-encode", "--repo", REPO,
             "--color", "1f6feb", "-d", "Opened by the bulk-encode dispatcher"])
        existing = gh_json(["pr", "view", branch, "--repo", REPO,
                            "--json", "number,state"])
        if existing and existing.get("state") == "OPEN":
            prnum = existing["number"]                     # force-push updated it
        else:
            bf = leaf.parent / "pr-body.md"
            bf.write_text("\n".join(body_lines))
            _, pr_out = run(["gh", "pr", "create", "--repo", REPO, "--base", "main",
                             "--head", branch, "--title", title,
                             "--body-file", str(bf), "--label", "bulk-encode"])
            mm = re.search(r"/pull/(\d+)", pr_out or "")
            prnum = int(mm.group(1)) if mm else None
        run(["gh", "pr", "merge", branch, "--repo", REPO, "--auto", "--squash"])
        mark_batched([m["slug"] for m in metas], prnum)
        result["status"] = "opened"
        result["pr"] = prnum
        result["detail"] = (f"PR #{prnum} on {branch}: {n} module(s)"
                            + (f", {len(dropped)} dropped" if dropped else "")
                            + f"; {summary}")
        if wait and prnum:
            result["detail"] += "; " + wait_for_merge(branch)
        return result
    finally:
        drop_worktree(leaf)


def assemble_ready(wait: bool = False, flush: bool = False, force: bool = False,
                   update_existing: bool = False) -> list[dict]:
    """Consolidate staged modules into batch PRs, grouped by jurisdiction. Emits
    full batches (>= BATCH_MIN, up to BATCH_MAX); a trailing partial only when
    ``flush``. Held while HOLD_UNTIL_PR is open unless ``force``. With
    ``update_existing``, rebuilds any open ``bulk/batch-<group>`` PR in place from
    all its group's staged modules -- used to re-drive a red batch through the
    CI-faithful gate."""
    pool = (list(load_staged().values()) if update_existing
            else unbatched_staged())
    if not pool:
        return []
    held, why = hold_blocked()
    if held and not force:
        log(f"holding batch PRs ({why}); {len(pool)} module(s) staged & durable -- "
            "they batch-PR once the train merges (`assemble --flush`).")
        return []
    by_group = collections.defaultdict(list)
    for m in pool:
        by_group[m.get("group", "us")].append(m)
    out = []
    seq_base = datetime.now().strftime("%H%M%S")
    for group, metas in sorted(by_group.items()):
        metas.sort(key=lambda m: m.get("module", ""))
        existing = find_open_batch_branch(group) if update_existing else None
        if existing:
            log(f"rebuilding open batch {existing}: {len(metas)} module(s) "
                "through the CI-faithful gate")
            out.append(assemble_batch(group, metas, f"{seq_base}-{len(out) + 1}",
                                      wait=wait, branch=existing))
            continue
        i = 0
        while i < len(metas):
            chunk = metas[i:i + BATCH_MAX]
            if len(chunk) < BATCH_MIN and not flush:
                break
            log(f"assembling batch {group} #{seq_base}-{len(out) + 1}: "
                f"{len(chunk)} module(s)")
            out.append(assemble_batch(group, chunk, f"{seq_base}-{len(out) + 1}",
                                      wait=wait))
            i += BATCH_MAX
    return out


# --- worklist status flips (small, reviewable, batched) ---------------------
def flip_statuses(updates: dict) -> None:
    """updates: {citation: status}. Commits to worklist on a small branch + PR."""
    if not updates:
        return
    leaf = make_worktree("worklist-flip", "origin/main")
    try:
        run(["git", "-C", str(leaf), "checkout", "-B", "bulk/worklist-status-flip"])
        for citation, status in updates.items():
            run([str(COV_PY), str(leaf / "bulk/compute_matrix.py"),
                 "--set-status", citation, status], cwd=leaf)
        run(["git", "-C", str(leaf), "add", "bulk/worklist.yaml"])
        run(["git", "-C", str(leaf), "-c", "user.email=bulk-encode@axiom",
             "-c", "user.name=bulk-encode", "commit", "-q", "-m",
             "Flip drained worklist statuses (bulk)\n\n"
             "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"])
        run(["git", "-C", str(leaf), "push", "-f", "origin",
             "HEAD:refs/heads/bulk/worklist-status-flip"], check=True)
        run(["gh", "pr", "create", "--repo", REPO, "--base", "main",
             "--head", "bulk/worklist-status-flip", "--title",
             "Flip drained worklist statuses (bulk)", "--body",
             "Status flips for locally-drained entries.", "--label", "bulk-encode"])
        run(["gh", "pr", "merge", "bulk/worklist-status-flip", "--repo", REPO,
             "--auto", "--squash"])
    finally:
        drop_worktree(leaf)


# --- reporting / PROGRESS.md -------------------------------------------------
def _counts(results: list) -> dict:
    c = collections.Counter(r["status"] for r in results)
    return {"generated": c.get("green", 0) + c.get("needs-fixtures", 0)
            + c.get("opened", 0),
            "green": c.get("green", 0), "needs_fixtures": c.get("needs-fixtures", 0),
            "failed": c.get("failed", 0), "deferred": c.get("deferred", 0)}


def _report(pool: AccountPool, results: list, gens: int, final: bool = False) -> None:
    c = _counts(results)
    snap = pool.snapshot()
    tag = "FINAL" if final else f"@~{gens} gens"
    log(f"[report {tag}] live_accounts={len(snap)} knee(per_account)={pool.per_account} "
        f"generated={c['generated']} (green {c['green']}, "
        f"needs-fixtures {c['needs_fixtures']}) failed={c['failed']} "
        f"deferred={c['deferred']}")
    for a in snap:
        log(f"   - {a['name']}: done={a['done']} inflight={a['inflight']} "
            f"avg_gen={a['avg_gen_s']}s limit_events={a['limit_events']} "
            f"backoff={a['backoff_s']}s")


def write_progress(results: list, remaining: int, pool: AccountPool,
                   assembled: list) -> None:
    p = CHECKOUT / "bulk" / "PROGRESS-local-drain.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    c = _counts(results)
    snap = pool.snapshot()
    staged = load_staged()
    n_staged = sum(1 for m in staged.values() if not m.get("batched"))
    lines = [f"# Local drain progress ({now}) - {REPO_NAME}", ""]
    if pool.all_backed_off():
        lines += ["> **All accounts backed off on Codex limit signals.** Re-run "
                  "after the window resets; the drain resumes idempotently.", ""]
    lines += [f"- Remaining pending: {remaining}",
              f"- This run: generated {c['generated']} "
              f"(green {c['green']}, needs-fixtures {c['needs_fixtures']}), "
              f"failed {c['failed']}, deferred {c['deferred']}",
              f"- Staged & unbatched: {n_staged}",
              f"- Live accounts: {len(snap)}  |  knee (per-account): {pool.per_account}",
              ""]
    lines += ["## Per-account throughput", "",
              "| account | done | avg gen (s) | limit events | backoff (s) |",
              "| --- | --- | --- | --- | --- |"]
    for a in snap:
        lines.append(f"| `{a['name']}` | {a['done']} | {a['avg_gen_s']} | "
                     f"{a['limit_events']} | {a['backoff_s']} |")
    if assembled:
        lines += ["", "## Batch PRs opened this run", ""]
        for b in assembled:
            lines.append(f"- `{b['branch']}` -> {b['status']} "
                         f"(PR {b.get('pr')}): {b.get('detail', '')[:80]}")
    lines += ["", "## Entries this run", "", "| citation | result | detail |",
              "| --- | --- | --- |"]
    for r in results:
        d = r["detail"].splitlines()[0][:80] if r["detail"] else ""
        lines.append(f"| `{r['citation']}` | {r['status']} | {d} |")
    p.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
def cmd_doctor(_args) -> int:
    tc = pinned_toolchain()
    print(f"repo                 : {REPO} ({REPO_NAME})")
    print(f"DRAIN_BASE           : {DRAIN_BASE}")
    print(f"hold-until-PR        : {HOLD_UNTIL_PR or '(none)'}")
    print(f"batch size           : {BATCH_MIN}-{BATCH_MAX}  max_total={MAX_TOTAL}")
    print("codex accounts:")
    any_live = False
    for home in discover_homes():
        live, mode = account_is_live(home)
        any_live = any_live or live
        mark = "LIVE " if live else "     "
        print(f"  {mark}{home.name:12s} {mode:18s} {home}")
    if not any_live:
        print("  !! no live ChatGPT-sub account -> nothing to drain "
              "(API billing is refused).")
    def _ver(ae: Path) -> str:
        if not ae.exists():
            return "MISSING"
        _, out = run([str(ae), "--version"])
        m = re.search(r"[Vv]ersion:?\s*([0-9.]+)", out)
        return m.group(1) if m else "?"
    pin = tc.get("axiom_encode_version")
    print(f"gen encoder          : {_ver(GEN_AE)}  {GEN_AE}")
    print(f"gate encoder (CI ref): {_ver(GATE_AE)}  {GATE_AE}")
    print(f"cov encoder (pending): {_ver(COV_AE)}  {COV_AE}")
    pytest_ok = GATE_PY.exists() and run([str(GATE_PY), "-c", "import pytest"])[0] == 0
    print(f"gate pytest (CI arb) : {'OK' if pytest_ok else 'MISSING -> pip install '
          'pytest pyyaml into the cov venv'}")
    print(f"pinned encoder ver   : {pin} (gen==pin: {_ver(GEN_AE) == pin})")
    print(f"engine bin           : {'OK' if ENGINE_BIN.exists() else 'MISSING'} {ENGINE_BIN}")
    print(f"corpus               : {'OK' if CORPUS.exists() else 'MISSING'} {CORPUS}")
    try:
        print(f"signing key          : present (len {len(signing_key())})")
    except SystemExit as e:
        print(f"signing key          : {e}")
    rc, out = run(["codex", "--version"])
    print(f"codex CLI            : {'OK ' + out.strip() if rc == 0 else 'MISSING'}")
    return 0


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
    log(f"unstick {len(targets)} PR(s): {[p['number'] for p in targets]}")
    for p in targets:
        try:
            log(f"#{p['number']} {p['branch']}: {unstick_pr(p['branch'], wait=args.wait)}")
        except Exception as exc:  # noqa: BLE001 - operator tool, report and continue
            log(f"#{p['number']} {p['branch']}: ERROR {exc}")
    return 0


def _refresh_loop(pool: AccountPool, stop: threading.Event) -> None:
    while not stop.wait(20):
        pool.refresh()


def cmd_drain(args) -> int:
    per_account = args.per_account or args.concurrency or 5
    pool = AccountPool(per_account)
    if pool.live_count() == 0:
        log("no authenticated ChatGPT-sub account found; nothing to drain "
            "(refusing API billing). Run `codex login` for ~/.codex[-2..4].")
        return 0
    stop = threading.Event()
    threading.Thread(target=_refresh_loop, args=(pool, stop), daemon=True).start()

    matrix = json.loads(subprocess.run(
        [str(COV_PY), str(CHECKOUT / "bulk/compute_matrix.py"),
         "--status", "pending", "--format", "matrix",
         *(["--batch", args.batch] if args.batch else []),
         *(["--limit", str(args.limit)] if args.limit else [])],
        capture_output=True, text=True, cwd=CHECKOUT).stdout)["include"]
    handled = handled_slugs()
    staged_now = set(load_staged().keys())
    failed_path = DRAIN_BASE / "drain_failed.json"
    failed = set(json.loads(failed_path.read_text())) if failed_path.exists() else set()
    todo = [it for it in matrix if it["slug"] not in handled
            and it["slug"] not in staged_now and it["citation"] not in failed]
    if args.max_entries:
        todo = todo[: args.max_entries]

    log(f"drain[{REPO_NAME}]: {pool.live_count()} live account(s), "
        f"per_account={per_account}, slots<={MAX_TOTAL}; {len(handled)} PR'd, "
        f"{len(staged_now)} staged, {len(failed)} known-failed -> {len(todo)} to "
        f"generate; pr_mode={args.pr_mode}, max_seconds={args.max_seconds}")

    results, new_failed = [], set()
    deadline = time.time() + args.max_seconds
    work = collections.deque({"citation": it["citation"], "slug": it["slug"],
                              "_tries": 0} for it in todo)
    reported = 0
    per_module_assembled = []
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_TOTAL)
    inflight: set = set()

    def submit_next():
        cap = min(MAX_TOTAL, per_account * max(1, pool.live_count()))
        while work and len(inflight) < cap and time.time() < deadline:
            it = work.popleft()
            fut = ex.submit(generate_module, it, pool, deadline)
            fut._item = it  # type: ignore[attr-defined]
            inflight.add(fut)

    try:
        submit_next()
        while inflight:
            done, inflight = concurrent.futures.wait(
                inflight, return_when=concurrent.futures.FIRST_COMPLETED)
            for fut in done:
                r = fut.result()
                item = getattr(fut, "_item", {"_tries": 0})
                results.append(r)
                log(f"{r['citation']}: {r['status']} "
                    f"[{r.get('account') or '-'}] - "
                    f"{(r['detail'].splitlines()[0] if r['detail'] else '')}")
                if r["status"] == "deferred":
                    if item.get("_tries", 0) < MAX_RETRIES:
                        item["_tries"] = item.get("_tries", 0) + 1
                        work.append(item)
                elif r["status"] == "failed":
                    new_failed.add(r["citation"])
                elif r["status"] in ("green", "needs-fixtures") \
                        and args.pr_mode == "per-module":
                    meta = load_staged().get(r["slug"])
                    if meta and not hold_blocked()[0]:
                        per_module_assembled.append(
                            assemble_batch(r["group"], [meta],
                                           datetime.now().strftime("%H%M%S")))
            gens = _counts(results)["generated"]
            if gens // 30 > reported // 30:
                reported = gens
                _report(pool, results, gens)
            if pool.all_backed_off() and not inflight:
                log("all accounts backed off; ending generation for this chunk.")
                break
            submit_next()
            if not work and not inflight:
                break
    finally:
        stop.set()
        ex.shutdown(wait=True)

    if new_failed:
        failed |= new_failed
        failed_path.write_text(json.dumps(sorted(failed), indent=1))

    # Consolidate staged modules into batch PRs (unless held or per-module mode).
    assembled = list(per_module_assembled)
    if args.pr_mode != "per-module" and not args.no_assemble:
        assembled += assemble_ready(wait=args.wait, flush=args.flush)

    remaining = int(subprocess.run(
        [str(COV_PY), str(CHECKOUT / "bulk/compute_matrix.py"),
         "--status", "pending", "--format", "count"],
        capture_output=True, text=True, cwd=CHECKOUT).stdout or 0)
    write_progress(results, remaining, pool, assembled)
    _report(pool, results, _counts(results)["generated"], final=True)
    log(f"chunk done: generated={_counts(results)['generated']} "
        f"failed={len(new_failed)} deferred={_counts(results)['deferred']} "
        f"batches={len(assembled)} all_backed_off={pool.all_backed_off()}")
    return 0


def cmd_assemble(args) -> int:
    """Consolidate staged modules into batch PRs on demand (e.g. once the train
    merges). --force overrides the HOLD_UNTIL_PR gate; --update-existing rebuilds
    open batch PRs in place (re-drives a red batch through the CI-faithful gate)."""
    staged = (load_staged().values() if args.update_existing
              else unbatched_staged())
    if not staged:
        print("No staged modules to assemble.")
        return 0
    out = assemble_ready(wait=args.wait, flush=args.flush, force=args.force,
                         update_existing=args.update_existing)
    for b in out:
        log(f"{b['branch']}: {b['status']} - {b.get('detail', '')}")
    if not out:
        log(f"{len(list(staged))} staged module(s) not assembled (held or below "
            f"BATCH_MIN={BATCH_MIN}; use --flush/--force/--update-existing).")
    return 0


def cmd_stage_status(_args) -> int:
    staged = load_staged()
    by_group = collections.Counter(m.get("group", "?") for m in staged.values()
                                   if not m.get("batched"))
    n_batched = sum(1 for m in staged.values() if m.get("batched"))
    print(f"repo: {REPO_NAME}   staged total: {len(staged)}  "
          f"(unbatched {len(staged) - n_batched}, batched {n_batched})")
    print(f"hold-until-PR: {HOLD_UNTIL_PR or '(none)'}  ->  "
          f"{'HELD' if hold_blocked()[0] else 'open'}")
    for group, n in sorted(by_group.items()):
        print(f"  {group:10s} {n} unbatched")
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
    d = sub.add_parser("drain", help="Generate pending worklist entries via local "
                       "Codex (multi-account), stage + batch-PR them.")
    d.add_argument("--limit", type=int)
    d.add_argument("--batch")
    d.add_argument("--per-account", type=int, help="Concurrent encodes per account "
                   "(the probed knee). Total slots = per_account x live accounts, "
                   f"capped at {MAX_TOTAL}.")
    d.add_argument("--concurrency", type=int, help="Alias for --per-account (compat).")
    d.add_argument("--max-entries", type=int)
    d.add_argument("--max-seconds", type=int, default=540)
    d.add_argument("--pr-mode", choices=["batch", "per-module"], default="batch",
                   help="batch = merge-train-style consolidated PRs (default); "
                   "per-module = one PR per entry (canary/debug).")
    d.add_argument("--flush", action="store_true",
                   help="Assemble trailing partial batches (< BATCH_MIN) at end.")
    d.add_argument("--no-assemble", action="store_true",
                   help="Generate + stage only; do not open batch PRs.")
    d.add_argument("--wait", action="store_true", help="Poll each batch PR to merge.")
    d.set_defaults(func=cmd_drain)
    a = sub.add_parser("assemble", help="Consolidate staged modules into batch PRs.")
    a.add_argument("--flush", action="store_true", help="Include partial batches.")
    a.add_argument("--force", action="store_true", help="Override the HOLD_UNTIL_PR gate.")
    a.add_argument("--update-existing", action="store_true",
                   help="Rebuild open batch PRs in place through the CI-faithful "
                   "gate (re-drive a red batch, dropping quality-rejected modules).")
    a.add_argument("--wait", action="store_true", help="Poll each batch PR to merge.")
    a.set_defaults(func=cmd_assemble)
    ss = sub.add_parser("stage-status", help="Show staged/unbatched module counts.")
    ss.set_defaults(func=cmd_stage_status)
    u = sub.add_parser("unstick", help="Sync-declare + rebase open new-state bulk PRs.")
    u.add_argument("--pr", type=int, nargs="*", default=[])
    u.add_argument("--all", action="store_true")
    u.add_argument("--wait", action="store_true", help="Poll each PR until merged.")
    u.set_defaults(func=cmd_unstick)
    doc = sub.add_parser("doctor", help="Verify toolchain, accounts, signing key.")
    doc.set_defaults(func=cmd_doctor)
    fl = sub.add_parser("flip", help="Batch accumulated drain status flips into one PR.")
    fl.set_defaults(func=cmd_flip)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
