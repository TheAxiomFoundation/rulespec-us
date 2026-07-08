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


def _derive_repo() -> tuple[str, str]:
    """(owner/name, name) for the checkout this script lives in.

    Auto-derives from the git ``origin`` remote so the same file works unchanged
    when copied into any ``rulespec-*`` checkout (US/UK/BE/...). Env overrides:
    ``DRAIN_REPO`` (owner/name) and ``DRAIN_REPO_NAME``.
    """
    repo = os.environ.get("DRAIN_REPO", "")
    if not repo:
        try:
            url = subprocess.run(
                ["git", "-C", str(Path(__file__).resolve().parent.parent),
                 "remote", "get-url", "origin"],
                capture_output=True, text=True).stdout.strip()
            m = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", url)
            repo = m.group(1) if m else "TheAxiomFoundation/rulespec-us"
        except Exception:  # noqa: BLE001
            repo = "TheAxiomFoundation/rulespec-us"
    name = os.environ.get("DRAIN_REPO_NAME") or repo.split("/")[-1]
    return repo, name


REPO, REPO_NAME = _derive_repo()
HERE = Path(__file__).resolve().parent           # <checkout>/bulk
CHECKOUT = HERE.parent                            # this checkout root

# --- toolchain / workspace resolution ---------------------------------------
DRAIN_BASE = Path(
    os.environ.get("DRAIN_BASE", Path.home() / "TheAxiomFoundation" / "_bulk_drain")
).resolve()
GEN_AE = Path(os.environ.get("DRAIN_GEN_AE", DRAIN_BASE / ".venv/bin/axiom-encode"))
COV_AE = Path(os.environ.get("DRAIN_COV_AE", DRAIN_BASE / ".venv-cov/bin/axiom-encode"))
COV_PY = Path(os.environ.get("DRAIN_COV_PY", DRAIN_BASE / ".venv-cov/bin/python"))
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
        applied = [ln[3:] for ln in st.splitlines()
                   if MODULE_RE.match(ln[3:]) and not ln[3:].endswith(".test.yaml")]
        if rc != 0 or not applied:
            res["detail"] = f"encode/apply failed (rc={rc}); see {tmp}"
            return res
        module = applied[0]
        test_file = module[:-5] + ".test.yaml"
        juris = module.split("/", 1)[0]
        rest = module[len(juris) + 1:]
        manifest = f"{juris}/.axiom/encoding-manifests/{rest[:-5]}.json"
        if not (leaf / manifest).exists():
            hits = list((leaf / juris / ".axiom/encoding-manifests").rglob(
                Path(module).stem + ".json"))
            manifest = str(hits[0].relative_to(leaf)) if hits else manifest

        # commit locally so guard-generated can diff against origin/main
        run(["git", "-C", str(leaf), "add", "--", module, test_file, manifest])
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
                res["detail"] = f"gate failed: {gate[1]}\n{gout[-400:]}"
                return res
        trc, _ = run([str(GEN_AE), "test", "--root", str(leaf),
                      "--axiom-rules-engine-path", str(ENGINE), str(leaf / test_file)],
                     cwd=leaf, env=env)
        gate_status = "green" if trc == 0 else "needs-fixtures"

        # stage the module + test + manifest (durable) for batch assembly
        sd = _stage_dir(slug)
        if sd.exists():
            shutil.rmtree(sd)
        for rel in (module, test_file, manifest):
            src = leaf / rel
            if src.exists():
                dst = sd / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        record_staged(slug, {"citation": citation, "module": module,
                             "test": test_file, "manifest": manifest,
                             "group": juris, "gate": gate_status,
                             "account": account.name,
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


def assemble_batch(group: str, metas: list[dict], seq: str, wait: bool = False) -> dict:
    """Build ONE merge-train-style batch PR from staged modules: copy all
    artifacts onto a fresh origin/main branch, ONE oracle-coverage-pending sync,
    ONE reverse-index regen, ONE validation over the whole set, push, auto-merge.
    Disjoint modules each carry their own signed apply manifest."""
    slugs = [m["slug"] for m in metas]
    suffix = REPO_NAME.replace("rulespec-", "")
    branch = f"bulk/batch-{suffix}-{group}-{seq}"
    result = {"branch": branch, "slugs": slugs, "status": "failed",
              "pr": None, "detail": ""}
    leaf = make_worktree(f"batch-{group}-{seq}", "origin/main")
    staged_root = STAGE_ROOT / REPO_NAME
    try:
        run(["git", "-C", str(leaf), "checkout", "-B", branch], check=True)
        copied = []
        for m in metas:
            for rel in (m.get("module"), m.get("test"), m.get("manifest")):
                if not rel:
                    continue
                src = staged_root / m["slug"] / rel
                if src.exists():
                    dst = leaf / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    copied.append(rel)
        if not copied:
            result["detail"] = "no staged artifacts found on disk"
            return result
        run(["git", "-C", str(leaf), "add", "--", *copied])
        # ONE sync + ONE index regen for the whole batch
        summary = sync_pending(leaf)
        keep_pending = finalize_pending(leaf)
        regen_index(leaf)
        add_files = [*copied, ".axiom/index/provisions_to_rules.json"]
        if keep_pending:
            add_files.append("oracle-coverage-pending.yaml")
        run(["git", "-C", str(leaf), "add", "--", *add_files])
        # fail-closed local validation: every module must validate before PR
        env = {"PATH": f"{GEN_AE.parent}:{ENGINE_BIN}:{os.environ['PATH']}"}
        for m in metas:
            grc, gout = run([str(GEN_AE), "validate", str(leaf / m["module"]),
                             "--skip-reviewers"], cwd=leaf, env=env)
            if grc != 0:
                result["detail"] = (f"batch validate failed on {m['module']}; "
                                    "aborting batch (staged modules preserved)")
                return result
        n = len(metas)
        needs_fx = sum(1 for m in metas if m.get("gate") == "needs-fixtures")
        title = (f"Batch-encode {n} {group} RuleSpec module(s) (bulk)"
                 + (f" [{needs_fx} needs-fixtures]" if needs_fx else ""))
        body_lines = [
            f"## Batch-encoded {n} module(s) - {group}", "",
            "Merge-train-style consolidation: one `oracle-coverage-pending sync`, "
            "one reverse-index regen, one validation, auto-merge. Modules are "
            "disjoint by construction; each carries its own signed apply manifest.",
            "", f"- {summary}",
            f"- Local gate: {n - needs_fx} green, {needs_fx} needs-fixtures", "",
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
        bf = leaf.parent / "pr-body.md"
        bf.write_text("\n".join(body_lines))
        _, pr_out = run(["gh", "pr", "create", "--repo", REPO, "--base", "main",
                         "--head", branch, "--title", title,
                         "--body-file", str(bf), "--label", "bulk-encode"])
        run(["gh", "pr", "merge", branch, "--repo", REPO, "--auto", "--squash"])
        mm = re.search(r"/pull/(\d+)", pr_out or "")
        prnum = int(mm.group(1)) if mm else None
        mark_batched(slugs, prnum)
        result["status"] = "opened"
        result["pr"] = prnum
        result["detail"] = f"PR #{prnum} on {branch}: {n} modules; {summary}"
        if wait and prnum:
            result["detail"] += "; " + wait_for_merge(branch)
        return result
    finally:
        drop_worktree(leaf)


def assemble_ready(wait: bool = False, flush: bool = False,
                   force: bool = False) -> list[dict]:
    """Consolidate unbatched staged modules into batch PRs, grouped by
    jurisdiction. Emits full batches (>= BATCH_MIN, up to BATCH_MAX); a trailing
    partial is emitted only when ``flush``. Held while HOLD_UNTIL_PR is open
    unless ``force``."""
    staged = unbatched_staged()
    if not staged:
        return []
    held, why = hold_blocked()
    if held and not force:
        log(f"holding batch PRs ({why}); {len(staged)} module(s) staged & "
            "durable -- they batch-PR once the train merges "
            "(`local_drain.py assemble --flush`).")
        return []
    by_group = collections.defaultdict(list)
    for m in staged:
        by_group[m.get("group", "us")].append(m)
    out = []
    seq_base = datetime.now().strftime("%H%M%S")
    for group, metas in sorted(by_group.items()):
        metas.sort(key=lambda m: m.get("module", ""))
        i = 0
        while i < len(metas):
            chunk = metas[i:i + BATCH_MAX]
            if len(chunk) < BATCH_MIN and not flush:
                break
            seq = f"{seq_base}-{len(out) + 1}"
            log(f"assembling batch {group} #{seq}: {len(chunk)} module(s)")
            out.append(assemble_batch(group, chunk, seq, wait=wait))
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
    for label, ae, want_pending in (("gen encoder (pin)", GEN_AE, False),
                                    ("cov encoder (main)", COV_AE, True)):
        has_pending = ae.exists() and run(
            [str(ae), "oracle-coverage-pending", "--help"])[0] == 0
        ok = ae.exists() and (has_pending == want_pending)
        print(f"{label:20s}: {'OK' if ok else 'CHECK'} "
              f"(oracle-coverage-pending {'present' if has_pending else 'absent'})")
    print(f"pinned encoder ver   : {tc.get('axiom_encode_version')}")
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
    merges). Use --force to override the HOLD_UNTIL_PR gate."""
    staged = unbatched_staged()
    if not staged:
        print("No unbatched staged modules.")
        return 0
    out = assemble_ready(wait=args.wait, flush=args.flush, force=args.force)
    for b in out:
        log(f"{b['branch']}: {b['status']} - {b.get('detail', '')}")
    if not out:
        log(f"{len(staged)} staged module(s) not assembled (held or below "
            f"BATCH_MIN={BATCH_MIN}; use --flush/--force).")
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
