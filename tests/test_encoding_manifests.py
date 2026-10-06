from __future__ import annotations

import base64
import binascii
import functools
import hashlib
import json
import os
import subprocess
import tomllib
import warnings
from pathlib import Path, PurePosixPath

from test_repository_layout import (
    CONTENT_DIRS,
    JURISDICTION_DIR_RE,
    ROOT,
    iter_rulespec_files,
    jurisdiction_dirs,
)

KNOWN_ORPHANED_ENCODING_MANIFESTS = [
    # The module moved to us-ca/policies/cdss/snap/standard-utility-allowance.yaml
    # during subtree absorption; its manifest stayed at the old guidance path.
    "us-ca/guidance/cdss/acin-2025-i-46-25/standard-utility-allowance.yaml",
]
APPLIED_ENCODING_MANIFEST_SCHEMA = "axiom-encode/applied-rulespec/v5"
APPLIED_ENCODING_DELETED_MARKER = "<deleted>"
PATH_MIGRATION_RECEIPT_SCHEMA = "axiom-encode/rulespec-path-migration-receipt/v1"
PATH_MIGRATION_TOOL = "axiom-encode migrate-rulespec-paths"
PATH_MIGRATION_RECEIPT_DIR = PurePosixPath(".axiom/path-migrations")
GIT_EMPTY_TREE_SHA1 = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
ENCODER_BACKENDS = frozenset({"claude", "codex", "openai"})
MODEL_APPLY_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "generated_at",
        "tool",
        "axiom_encode_version",
        "axiom_encode_git",
        "generation_prompt_sha256",
        "run_id",
        "citation",
        "runner",
        "backend",
        "model",
        "validation_waiver_set_sha256",
        "generated_output_root",
        "generated_output_file",
        "generated_output_sha256",
        "trace_file",
        "trace_sha256",
        "context_manifest_file",
        "context_manifest_sha256",
        "applied_files",
        "source_attestation",
        "validation_execution",
        "signature",
    }
)
CREATION_TARGET_FIELDS = frozenset(
    {
        "base_commit",
        "base_tree",
        "primary",
        "companion",
        "canonical_manifest",
        "orphan_manifest",
    }
)
RETIRE_APPLY_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "generated_at",
        "tool",
        "reason",
        "axiom_encode_version",
        "axiom_encode_git",
        "validation_waiver_set_sha256",
        "applied_files",
        "retired_manifest",
        "source_attestation",
        "signature",
    }
)
PATH_MIGRATION_APPLY_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "generated_at",
        "tool",
        "axiom_encode_version",
        "axiom_encode_git",
        "validation_waiver_set_sha256",
        "applied_files",
        "migrated_manifest",
        "migration",
        "source_attestation",
        "signature",
    }
)
PATH_MIGRATION_RECEIPT_FIELDS = frozenset(
    {
        "schema_version",
        "generated_at",
        "tool",
        "plan_sha256",
        "plan",
        "repository",
        "axiom_encode_version",
        "axiom_encode_git",
        "validation_waiver_set_sha256",
        "corpus_release",
        "moves",
        "rewrites",
        "manifests",
        "signature",
    }
)

# Manifest-sync guard: axiom-encode writes an applied-rulespec manifest next to
# every encoding run, recording the sha256 of each file it applied. Historical
# full-repo checks below tolerate legacy receipt schemas already in the tree;
# the changed-file structural preflight requires the repository-pinned current
# v5 shape. A hand-edit that skips the encoder leaves the manifest stale —
# invisible drift between content and provenance. These tests make that drift
# a failure. Motivated by the review flag on
# https://github.com/TheAxiomFoundation/rulespec-us/pull/566 and
# https://github.com/TheAxiomFoundation/axiom-rules-engine/issues/88.
#
# Three manifest layouts coexist after the country-monorepo consolidation:
#   .axiom/encoding-manifests/statutes/26/213.json
#       pre-consolidation federal manifests; applied paths relative to us/
#   .axiom/encoding-manifests/us-ny/policies/....json
#       post-consolidation manifests; applied paths relative to the repo root
#   us-ct/.axiom/encoding-manifests/statutes/....json
#       trees absorbed from the standalone state repos; applied paths
#       relative to the jurisdiction directory
# A module re-encoded after the consolidation can therefore be covered by
# manifests in two locations; the entry with the newest generated_at is
# authoritative and older ones are superseded history.


def manifest_roots() -> list[tuple[Path, Path]]:
    """(base directory, manifest directory) pairs for every layout."""
    return [
        (base, base / ".axiom" / "encoding-manifests")
        for base in (ROOT, *jurisdiction_dirs())
        if (base / ".axiom" / "encoding-manifests").is_dir()
    ]


def resolve_applied_path(base: Path, applied: str, *, repo: Path = ROOT) -> Path:
    head = applied.split("/", 1)[0]
    if base == repo and head == "programs":
        return repo / applied
    if base == repo and not JURISDICTION_DIR_RE.fullmatch(head):
        # Pre-consolidation federal manifests predate the us/ prefix.
        return repo / "us" / applied
    return base / applied


def changed_worktree_entries(repo: Path) -> list[tuple[str, str]]:
    """Return status/path pairs, expanding rename sources as deletions."""
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ],
        check=True,
        capture_output=True,
    )
    records = completed.stdout.split(b"\0")
    changes: list[tuple[str, str]] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2:3] != b" ":
            raise ValueError("malformed git status --porcelain=v1 -z output")
        status = record[:2].decode("ascii", errors="strict")
        destination = record[3:].decode("utf-8", errors="strict")
        changes.append((status, destination))
        if "R" in status or "C" in status:
            if index >= len(records) or not records[index]:
                raise ValueError("git rename/copy status is missing its source path")
            source = records[index].decode("utf-8", errors="strict")
            index += 1
            if "R" in status:
                changes.append(("D " if status[0] == "R" else " D", source))
    return changes


def changed_ref_paths(repo: Path, base_ref: str, head_ref: str) -> list[str]:
    """Return base-to-head paths without rename collapsing."""
    if base_ref == GIT_EMPTY_TREE_SHA1:
        command = [
            "git",
            "-C",
            str(repo),
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--no-renames",
            "--name-only",
            "-r",
            "-z",
            head_ref,
            "--",
        ]
    else:
        command = [
            "git",
            "-C",
            str(repo),
            "diff",
            "--no-renames",
            "--name-only",
            "-z",
            base_ref,
            head_ref,
            "--",
        ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
    )
    return sorted(
        path.decode("utf-8", errors="strict")
        for path in completed.stdout.split(b"\0")
        if path
    )


def github_base_to_head_refs(repo: Path = ROOT) -> tuple[str, str] | None:
    """Resolve the canonical protected diff for a GitHub Actions checkout.

    Event ``before`` and pull-request base fields describe one delivery, not
    the complete branch review surface.  In particular, a push ``before`` can
    already contain an unauthorized RuleSpec commit.  Start from the checked-
    out canonical ``origin/main`` merge base, then allow a validated nonzero
    push ``before`` only to widen that range.  The selected base is a unique
    ancestor no newer than either witness.
    """
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return None
    head_ref = os.environ.get("GITHUB_SHA")
    if (
        not isinstance(head_ref, str)
        or len(head_ref) != 40
        or any(character not in "0123456789abcdef" for character in head_ref)
    ):
        raise AssertionError("GitHub Actions head SHA is not canonical")
    checkout_head = git_commit_ref(repo, "HEAD")
    if checkout_head is None or git_commit_ref(repo, head_ref) is None:
        raise AssertionError("GitHub Actions head commit is unavailable")
    if checkout_head != head_ref:
        raise AssertionError(
            "GitHub Actions head SHA does not match the checked-out HEAD"
        )
    refs, issues = committed_base_to_head_refs(repo, use_github_event=False)
    if refs is None:
        raise AssertionError("; ".join(issues))
    canonical_base, canonical_head = refs
    event_name = os.environ.get("GITHUB_EVENT_NAME")
    if event_name != "push":
        return refs
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise AssertionError("GitHub Actions push event path is unavailable")
    event = json.loads(Path(event_path).read_text())
    if not isinstance(event, dict):
        raise AssertionError("GitHub Actions push event is not an object")
    event_after = event.get("after")
    if (
        not isinstance(event_after, str)
        or len(event_after) != 40
        or any(character not in "0123456789abcdef" for character in event_after)
    ):
        raise AssertionError("GitHub Actions push after SHA is not canonical")
    if event_after != canonical_head:
        raise AssertionError("GitHub Actions push after SHA does not match HEAD")
    push_before = event.get("before")
    if push_before == "0" * 40:
        if canonical_base != canonical_head:
            return refs
        completed = subprocess.run(
            ["git", "-C", str(repo), "rev-list", "--parents", "-n", "1", canonical_head],
            check=False,
            capture_output=True,
            text=True,
        )
        fields = completed.stdout.split()
        if completed.returncode == 0 and len(fields) == 1:
            return GIT_EMPTY_TREE_SHA1, canonical_head
        raise AssertionError(
            "GitHub Actions zero-before push has no trustworthy pre-push "
            "coverage boundary; canonical origin/main already equals HEAD"
        )
    if (
        not isinstance(push_before, str)
        or len(push_before) != 40
        or any(character not in "0123456789abcdef" for character in push_before)
    ):
        raise AssertionError("GitHub Actions push before SHA is not canonical")
    if git_commit_ref(repo, push_before) is None:
        raise AssertionError("GitHub Actions push before commit is unavailable")
    push_base = unique_merge_base(
        repo,
        push_before,
        canonical_head,
        label="push before and HEAD",
    )
    coverage_base = unique_merge_base(
        repo,
        canonical_base,
        push_base,
        label="canonical and push coverage bases",
    )
    return coverage_base, canonical_head


def git_commit_ref(repo: Path, ref: str) -> str | None:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "--verify",
            "--quiet",
            f"{ref}^{{commit}}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    resolved = completed.stdout.strip()
    return resolved if len(resolved) == 40 else None


def unique_merge_base(repo: Path, left: str, right: str, *, label: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--all", left, right],
        check=False,
        capture_output=True,
        text=True,
    )
    merge_bases = sorted(set(completed.stdout.split()))
    if completed.returncode != 0 or not merge_bases:
        raise AssertionError(f"GitHub Actions {label} have no merge base")
    if len(merge_bases) != 1:
        raise AssertionError(
            f"GitHub Actions {label} have ambiguous merge bases: "
            + ", ".join(merge_bases)
        )
    return merge_bases[0]


def committed_base_to_head_refs(
    repo: Path,
    *,
    use_github_event: bool = False,
) -> tuple[tuple[str, str] | None, list[str]]:
    """Resolve the canonical committed branch diff or fail closed."""
    head_ref = git_commit_ref(repo, "HEAD")
    if head_ref is None:
        # A new repository has no committed history to conceal.
        return None, []

    if use_github_event:
        try:
            github_refs = github_base_to_head_refs(repo)
        except (AssertionError, json.JSONDecodeError, OSError) as exc:
            return None, [f"cannot resolve GitHub base-to-head RuleSpec diff: {exc}"]
        if github_refs is not None:
            return github_refs, []

    canonical_main = git_commit_ref(repo, "refs/remotes/origin/main")
    if canonical_main is None:
        return None, [
            "cannot verify committed RuleSpec changes because canonical "
            "refs/remotes/origin/main is missing"
        ]
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "merge-base",
            "--all",
            head_ref,
            canonical_main,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    merge_bases = sorted(set(completed.stdout.split()))
    if completed.returncode != 0 or not merge_bases:
        return None, [
            "cannot verify committed RuleSpec changes because HEAD and "
            "canonical origin/main have no merge base"
        ]
    if len(merge_bases) != 1:
        return None, [
            "cannot verify committed RuleSpec changes because HEAD and "
            "canonical origin/main have ambiguous merge bases: "
            + ", ".join(merge_bases)
        ]
    return (merge_bases[0], head_ref), []


def git_tree_ref(repo: Path, commit: str) -> str | None:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "--verify",
            "--quiet",
            f"{commit}^{{tree}}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    resolved = completed.stdout.strip()
    return resolved if len(resolved) == 40 else None


def git_blob_sha256(repo: Path, commit: str, relative: str) -> str | None:
    """Hash the exact Git blob at ``commit`` without consulting the worktree."""
    listed = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-z", commit, "--", relative],
        check=False,
        capture_output=True,
    )
    records = [record for record in listed.stdout.split(b"\0") if record]
    if listed.returncode != 0 or len(records) != 1:
        return None
    metadata, separator, path = records[0].partition(b"\t")
    fields = metadata.split()
    if separator != b"\t" or path.decode("utf-8", errors="strict") != relative:
        return None
    if len(fields) != 3 or fields[1] != b"blob" or len(fields[2]) != 40:
        return None
    completed = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "blob", fields[2].decode("ascii")],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        return None
    return hashlib.sha256(completed.stdout).hexdigest()


def git_path_present_at_ref(repo: Path, commit: str, relative: str) -> bool:
    listed = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-z", commit, "--", relative],
        check=False,
        capture_output=True,
    )
    return listed.returncode == 0 and bool(
        [record for record in listed.stdout.split(b"\0") if record]
    )


def receipt_operation_base_ref(
    repo: Path,
    manifest_relative: str,
    *,
    resolved_refs: tuple[str, str] | None,
    worktree_changed_paths: set[str],
) -> tuple[str | None, str | None]:
    """Return the exact pre-operation commit for a changed receipt.

    An index/worktree receipt must have been generated from checked-out HEAD.
    For a committed receipt, its latest introducing commit in the canonical
    merge-base-to-HEAD range must have exactly one parent; that parent is the
    pre-operation snapshot.  This prevents arbitrary signed metadata from
    selecting an unrelated repository history.
    """
    if resolved_refs is None:
        return None, (
            f"{manifest_relative} cannot bind its before-state because the "
            "canonical base-to-head refs are unavailable"
        )
    base_ref, head_ref = resolved_refs
    if manifest_relative in worktree_changed_paths:
        return head_ref, None
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "log",
            "-1",
            "--format=%H %P",
            f"{base_ref}..{head_ref}",
            "--",
            manifest_relative,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    line = completed.stdout.strip()
    if completed.returncode != 0 or not line:
        return None, (
            f"{manifest_relative} cannot be bound to a receipt-introducing "
            "commit in the canonical base-to-head range"
        )
    fields = line.split()
    if len(fields) != 2:
        return None, (
            f"{manifest_relative} receipt-introducing commit does not have "
            "one unambiguous parent"
        )
    return fields[1], None


def is_protected_rulespec_path(path: PurePosixPath) -> bool:
    """Whether ``path`` is RuleSpec YAML protected by encoder receipts."""
    if path.suffix not in {".yaml", ".yml"}:
        return False
    if len(path.parts) >= 2 and path.parts[0] == "programs":
        return True
    return (
        len(path.parts) >= 3
        and bool(JURISDICTION_DIR_RE.fullmatch(path.parts[0]))
        and path.parts[1] in {*CONTENT_DIRS, "manual"}
    )


def unsupported_protected_path_issue(relative: str) -> str | None:
    path = PurePosixPath(relative)
    if not is_protected_rulespec_path(path):
        return None
    if path.parts and path.parts[0] == "programs":
        return (
            f"{relative} is a ProgramSpec, but the pinned toolchain has no "
            "signed ProgramSpec-authoring receipt path; ProgramSpec changes "
            "are blocked"
        )
    if len(path.parts) >= 2 and path.parts[1] == "manual":
        return (
            f"{relative} is legacy manual RuleSpec whose v1 owner requires an "
            "unsupported specialized encoder legacy-replacement receipt; "
            "legacy manual changes are blocked"
        )
    return None


def is_encoding_manifest_path(path: PurePosixPath) -> bool:
    parts = path.parts
    return (
        bool(parts)
        and parts[0] != "_axiom"
        and path.suffix == ".json"
        and any(
            parts[index : index + 2] == (".axiom", "encoding-manifests")
            for index in range(len(parts) - 1)
        )
    )


def is_current_encoding_manifest_path(path: PurePosixPath) -> bool:
    return (
        len(path.parts) >= 3
        and path.parts[:2] == (".axiom", "encoding-manifests")
        and path.suffix == ".json"
    )


def is_path_migration_receipt_path(path: PurePosixPath) -> bool:
    return (
        len(path.parts) == 3
        and path.parent == PATH_MIGRATION_RECEIPT_DIR
        and path.suffix == ".json"
    )


def changed_snapshot_issues(changes: list[tuple[str, str]]) -> list[str]:
    """Reject a mixed index/worktree view before hashing live files."""
    staged: set[str] = set()
    unstaged: set[str] = set()
    unmerged: set[str] = set()
    unmerged_statuses = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}
    for status, changed in changes:
        relative = PurePosixPath(changed)
        if not (
            is_protected_rulespec_path(relative)
            or is_encoding_manifest_path(relative)
            or is_path_migration_receipt_path(relative)
        ):
            continue
        if status in unmerged_statuses:
            unmerged.add(changed)
            continue
        if status == "??":
            unstaged.add(changed)
            continue
        if status[0] not in {" ", "?", "!"}:
            staged.add(changed)
        if status[1] not in {" ", "?", "!"}:
            unstaged.add(changed)

    issues = [
        f"{path} has an unresolved index conflict; reconcile it before the "
        "RuleSpec receipt preflight"
        for path in sorted(unmerged)
    ]
    if staged and unstaged:
        issues.append(
            "protected RuleSpec changes span both the index and worktree; the "
            "local structural preflight cannot prove the pending commit from "
            "live worktree bytes. Stage the complete encoder transaction or "
            "unstage it before rerunning (staged: "
            + ", ".join(sorted(staged))
            + "; unstaged: "
            + ", ".join(sorted(unstaged))
            + ")"
        )
    return issues


def manifest_base(repo: Path, manifest_path: PurePosixPath) -> Path:
    parts = manifest_path.parts
    for index in range(len(parts) - 1):
        if parts[index : index + 2] == (".axiom", "encoding-manifests"):
            return repo.joinpath(*parts[:index])
    raise ValueError(f"not an encoding manifest path: {manifest_path}")


def signature_is_structurally_valid(payload: dict) -> bool:
    """Check current receipt shape; protected CI verifies the Ed25519 value."""
    signature = payload.get("signature")
    if not isinstance(signature, dict) or set(signature) != {
        "algorithm",
        "key_id",
        "value",
    }:
        return False
    key_id = signature.get("key_id")
    value = signature.get("value")
    if (
        signature.get("algorithm") != "ed25519-domain-v1"
        or not isinstance(key_id, str)
        or not key_id.startswith("sha256:")
        or len(key_id) != len("sha256:") + 64
        or any(character not in "0123456789abcdef" for character in key_id[7:])
        or not isinstance(value, str)
    ):
        return False
    try:
        decoded = base64.b64decode(value.encode("ascii"), validate=True)
    except (binascii.Error, UnicodeEncodeError):
        return False
    return len(decoded) == 64


def is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def is_git_sha1(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(character in "0123456789abcdef" for character in value)
    )


def canonical_repo_path(value: object) -> PurePosixPath | None:
    if not isinstance(value, str) or not value:
        return None
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        return None
    return path


def expected_creation_orphan_manifest(primary: PurePosixPath) -> str | None:
    if (
        len(primary.parts) >= 3
        and primary.parts[0] == "us"
        and primary.parts[1] in {"policies", "statutes"}
    ):
        return (
            PurePosixPath(".axiom/encoding-manifests")
            .joinpath(*primary.parts[1:])
            .with_suffix(".json")
            .as_posix()
        )
    return None


def creation_target_is_structurally_valid(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != CREATION_TARGET_FIELDS:
        return False
    primary = canonical_repo_path(value.get("primary"))
    companion = canonical_repo_path(value.get("companion"))
    canonical_manifest = canonical_repo_path(value.get("canonical_manifest"))
    orphan_value = value.get("orphan_manifest")
    orphan_manifest = (
        canonical_repo_path(orphan_value) if orphan_value is not None else None
    )
    if (
        primary is None
        or companion is None
        or canonical_manifest is None
        or (orphan_value is not None and orphan_manifest is None)
        or not is_git_sha1(value.get("base_commit"))
        or not is_git_sha1(value.get("base_tree"))
        or len(primary.parts) < 3
        or primary.parts[1] != "policies"
        or primary.suffix != ".yaml"
        or primary.name.endswith(".test.yaml")
        or companion
        != primary.with_name(f"{primary.stem}.test.yaml")
        or canonical_manifest
        != PurePosixPath(".axiom/encoding-manifests").joinpath(primary).with_suffix(
            ".json"
        )
        or (orphan_manifest.as_posix() if orphan_manifest is not None else None)
        != expected_creation_orphan_manifest(primary)
    ):
        return False
    return is_protected_rulespec_path(primary) and (
        unsupported_protected_path_issue(primary.as_posix()) is None
    )


def model_manifest_expected_fields(payload: dict) -> frozenset[str] | None:
    operation_present = "target_operation" in payload
    creation_present = "creation_target" in payload
    if not operation_present:
        return MODEL_APPLY_MANIFEST_FIELDS if not creation_present else None
    operation = payload.get("target_operation")
    if operation == "replace" and not creation_present:
        return MODEL_APPLY_MANIFEST_FIELDS | {"target_operation"}
    if (
        operation == "create"
        and creation_present
        and creation_target_is_structurally_valid(payload.get("creation_target"))
    ):
        return MODEL_APPLY_MANIFEST_FIELDS | {
            "target_operation",
            "creation_target",
        }
    return None


def pinned_encoder_identity(repo: Path) -> tuple[str, str]:
    toolchain = tomllib.loads((repo / ".axiom/workflow-toolchain.toml").read_text())[
        "workflow_toolchain"
    ]
    return str(toolchain["axiom_encode_version"]), str(toolchain["axiom_encode_ref"])


def manifest_uses_pinned_encoder(
    payload: dict,
    *,
    version: str,
    commit: str,
) -> bool:
    provenance = payload.get("axiom_encode_git")
    return (
        payload.get("axiom_encode_version") == version
        and isinstance(provenance, dict)
        and set(provenance)
        == {
            "root",
            "commit",
            "dirty_tracked",
            "version",
            "version_commit",
            "identity_source",
        }
        and isinstance(provenance.get("root"), str)
        and bool(provenance["root"])
        and provenance.get("commit") == commit
        and provenance.get("dirty_tracked") is False
        and provenance.get("version") == version
        and isinstance(provenance.get("version_commit"), str)
        and len(provenance["version_commit"]) == 40
        and all(
            character in "0123456789abcdef"
            for character in provenance["version_commit"]
        )
        and provenance.get("identity_source")
        in {"github-sha", "git", "trusted-runtime-attestation"}
    )


def has_exact_model_manifest_structure(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    codex_fields = {"codex_cli_version", "codex_cli_sha256"}
    present_codex_fields = set(payload) & codex_fields
    backend = payload.get("backend")
    exact_fields = set(payload) - codex_fields
    expected_fields = model_manifest_expected_fields(payload)
    return (
        expected_fields is not None
        and exact_fields == expected_fields
        and backend in ENCODER_BACKENDS
        and payload.get("schema_version") == APPLIED_ENCODING_MANIFEST_SCHEMA
        and payload.get("tool") == "axiom-encode encode --apply"
        and (
            (backend == "codex" and present_codex_fields in (set(), codex_fields))
            or (backend != "codex" and not present_codex_fields)
        )
        and isinstance(payload.get("source_attestation"), dict)
        and isinstance(payload.get("validation_execution"), dict)
        and signature_is_structurally_valid(payload)
    )


def retirement_paths_match(payload: dict) -> bool:
    retired = payload.get("retired_manifest")
    outer = payload.get("applied_files")
    inner = retired.get("applied_files") if isinstance(retired, dict) else None
    if not isinstance(outer, list) or not isinstance(inner, list):
        return False
    deleted_paths = {
        item.get("path")
        for item in outer
        if isinstance(item, dict) and item.get("deleted") is True
    }
    retired_paths = {
        item.get("path")
        for item in inner
        if isinstance(item, dict) and isinstance(item.get("sha256"), str)
    }
    return bool(deleted_paths) and deleted_paths == retired_paths


def applied_repo_relative(
    repo: Path,
    manifest_relative: str,
    applied: object,
) -> tuple[str | None, str | None]:
    if not isinstance(applied, str):
        return None, f"{manifest_relative} has an applied file without a path"
    applied_path = PurePosixPath(applied)
    if (
        applied_path.is_absolute()
        or applied_path.as_posix() != applied
        or any(part in {"", ".", ".."} for part in applied_path.parts)
    ):
        return None, f"{manifest_relative} has a noncanonical applied path: {applied}"
    base = manifest_base(repo, PurePosixPath(manifest_relative))
    resolved = resolve_applied_path(base, applied, repo=repo).resolve()
    try:
        return resolved.relative_to(repo.resolve()).as_posix(), None
    except ValueError:
        return None, f"{manifest_relative} applied path escapes the repository: {applied}"


def retirement_before_state_issue(
    repo: Path,
    manifest_relative: str,
    payload: dict,
    operation_base_ref: str,
) -> str | None:
    retired = payload.get("retired_manifest")
    nested_entries = retired.get("applied_files") if isinstance(retired, dict) else None
    if not isinstance(nested_entries, list):
        return f"{manifest_relative} retirement before-state is malformed"
    for entry in nested_entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            return f"{manifest_relative} retirement before-state is malformed"
        relative, path_issue = applied_repo_relative(
            repo,
            manifest_relative,
            entry.get("path"),
        )
        if path_issue is not None or relative is None or not is_sha256(
            entry.get("sha256")
        ):
            return path_issue or f"{manifest_relative} retirement before-state is malformed"
        actual = git_blob_sha256(repo, operation_base_ref, relative)
        if actual is None:
            return (
                f"{manifest_relative} retirement before-state path is absent "
                f"from its exact Git base: {relative}"
            )
        if actual != entry["sha256"]:
            return (
                f"{manifest_relative} retirement before sha256 does not match "
                f"its exact Git base blob: {relative}"
            )
    return None


def creation_before_state_issue(
    repo: Path,
    manifest_relative: str,
    payload: dict,
    operation_base_ref: str,
) -> str | None:
    creation = payload.get("creation_target")
    if not creation_target_is_structurally_valid(creation):
        return f"{manifest_relative} creation target evidence is malformed"
    assert isinstance(creation, dict)
    expected_tree = git_tree_ref(repo, operation_base_ref)
    if expected_tree is None:
        return f"{manifest_relative} creation exact Git base is unavailable"
    if creation.get("base_commit") != operation_base_ref or creation.get(
        "base_tree"
    ) != expected_tree:
        return (
            f"{manifest_relative} creation identity does not match its exact "
            "pre-operation commit and tree"
        )
    if creation.get("canonical_manifest") != manifest_relative:
        return (
            f"{manifest_relative} creation evidence names a different canonical "
            "manifest"
        )
    protected_paths = [
        creation["primary"],
        creation["companion"],
        creation["canonical_manifest"],
    ]
    if creation.get("orphan_manifest") is not None:
        protected_paths.append(creation["orphan_manifest"])
    occupied = sorted(
        path
        for path in protected_paths
        if git_path_present_at_ref(repo, operation_base_ref, path)
    )
    if occupied:
        return (
            f"{manifest_relative} creation target was not absent from its exact "
            "Git base: "
            + ", ".join(occupied)
        )
    applied_files = payload.get("applied_files")
    applied_paths = {
        item.get("path")
        for item in applied_files
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    } if isinstance(applied_files, list) else set()
    required = {creation["primary"], creation["companion"]}
    if not required <= applied_paths:
        return (
            f"{manifest_relative} creation receipt does not claim its exact "
            "primary and companion"
        )
    return None


def migration_repository_binding_issue(
    repo: Path,
    manifest_relative: str,
    receipt: dict,
    operation_base_ref: str,
) -> str | None:
    repository = receipt.get("repository")
    expected_tree = git_tree_ref(repo, operation_base_ref)
    if expected_tree is None:
        return f"{manifest_relative} path migration exact Git base is unavailable"
    if not isinstance(repository, dict) or repository != {
        "base_commit": operation_base_ref,
        "head_commit": operation_base_ref,
        "base_tree": expected_tree,
    }:
        return (
            f"{manifest_relative} path migration repository identity does not "
            "match its exact pre-operation commit and tree"
        )
    plan = receipt.get("plan")
    if not isinstance(plan, dict) or plan.get("base_commit") != operation_base_ref:
        return (
            f"{manifest_relative} path migration plan does not bind its exact "
            "pre-operation commit"
        )
    return None


def migration_manifest_structure_issue(
    repo: Path,
    manifest_relative: str,
    payload: dict,
    changed_paths: set[str],
    *,
    encoder_version: str,
    encoder_commit: str,
    operation_base_ref: str,
) -> str | None:
    migrated_manifest = payload.get("migrated_manifest")
    migration = payload.get("migration")
    if not has_exact_model_manifest_structure(
        migrated_manifest
    ) or not manifest_uses_pinned_encoder(
        migrated_manifest,
        version=encoder_version,
        commit=encoder_commit,
    ):
        return f"{manifest_relative} migrated_manifest is not an exact model v5 receipt"
    if not isinstance(migration, dict) or set(migration) != {
        "receipt_path",
        "receipt_sha256",
        "plan_sha256",
        "prior_manifest_path",
        "prior_manifest_sha256",
    }:
        return f"{manifest_relative} lacks its migrated manifest or migration record"
    receipt_path = migration.get("receipt_path")
    receipt_sha256 = migration.get("receipt_sha256")
    plan_sha256 = migration.get("plan_sha256")
    if (
        not isinstance(receipt_path, str)
        or not is_sha256(receipt_sha256)
        or not is_sha256(plan_sha256)
        or not isinstance(migration.get("prior_manifest_path"), str)
        or not is_sha256(migration.get("prior_manifest_sha256"))
    ):
        return f"{manifest_relative} has a malformed migration record"
    receipt_relative = PurePosixPath(receipt_path)
    if (
        receipt_relative.as_posix() != receipt_path
        or receipt_relative.parent != PATH_MIGRATION_RECEIPT_DIR
        or receipt_relative.name != f"{plan_sha256}.json"
        or any(part in {"", ".", ".."} for part in receipt_relative.parts)
    ):
        return f"{manifest_relative} names a noncanonical path-migration receipt"
    if receipt_path not in changed_paths or not (repo / receipt_path).is_file():
        return f"{manifest_relative} path-migration receipt is not in the same change"
    receipt_file = repo / receipt_path
    if hashlib.sha256(receipt_file.read_bytes()).hexdigest() != receipt_sha256:
        return f"{manifest_relative} path-migration receipt sha256 does not match"
    try:
        receipt = json.loads(receipt_file.read_text())
    except (json.JSONDecodeError, OSError):
        return f"{manifest_relative} path-migration receipt is not readable JSON"
    if (
        not isinstance(receipt, dict)
        or set(receipt) != PATH_MIGRATION_RECEIPT_FIELDS
        or receipt.get("schema_version") != PATH_MIGRATION_RECEIPT_SCHEMA
        or receipt.get("tool") != PATH_MIGRATION_TOOL
        or receipt.get("plan_sha256") != plan_sha256
        or not signature_is_structurally_valid(receipt)
        or not manifest_uses_pinned_encoder(
            receipt, version=encoder_version, commit=encoder_commit
        )
    ):
        return f"{manifest_relative} path-migration receipt has invalid structure"
    repository_issue = migration_repository_binding_issue(
        repo,
        manifest_relative,
        receipt,
        operation_base_ref,
    )
    if repository_issue is not None:
        return repository_issue
    receipt_moves = receipt.get("moves")
    receipt_rewrites = receipt.get("rewrites")
    receipt_manifests = receipt.get("manifests")
    if (
        not isinstance(receipt_moves, list)
        or not isinstance(receipt_rewrites, list)
        or not isinstance(receipt_manifests, list)
        or not receipt_manifests
    ):
        return f"{manifest_relative} path migration path bindings are incomplete"

    expected_manifest_binding = {
        "prior_path": migration["prior_manifest_path"],
        "prior_sha256": migration["prior_manifest_sha256"],
        "replacement_path": manifest_relative,
    }
    if expected_manifest_binding not in receipt_manifests:
        return f"{manifest_relative} is not bound by its path-migration receipt"

    receipt_applied_live: set[str] = set()
    receipt_applied_deleted: set[str] = set()
    seen_prior_manifests: set[str] = set()
    seen_replacement_manifests: set[str] = set()
    for binding in receipt_manifests:
        if (
            not isinstance(binding, dict)
            or set(binding) != {"prior_path", "prior_sha256", "replacement_path"}
            or not isinstance(binding.get("prior_path"), str)
            or not is_sha256(binding.get("prior_sha256"))
            or not isinstance(binding.get("replacement_path"), str)
        ):
            return f"{manifest_relative} path migration manifest bindings are malformed"
        prior_path = binding["prior_path"]
        replacement_path = binding["replacement_path"]
        if (
            prior_path in seen_prior_manifests
            or replacement_path in seen_replacement_manifests
            or not is_current_encoding_manifest_path(PurePosixPath(prior_path))
            or not is_current_encoding_manifest_path(PurePosixPath(replacement_path))
        ):
            return f"{manifest_relative} path migration manifest bindings are malformed"
        seen_prior_manifests.add(prior_path)
        seen_replacement_manifests.add(replacement_path)
        actual_prior_sha256 = git_blob_sha256(repo, operation_base_ref, prior_path)
        if actual_prior_sha256 != binding["prior_sha256"]:
            return (
                f"{manifest_relative} path migration prior manifest sha256 "
                f"does not match its exact Git base blob: {prior_path}"
            )
        if replacement_path not in changed_paths or not (repo / replacement_path).is_file():
            return (
                f"{manifest_relative} path migration transaction is missing "
                f"replacement manifest: {replacement_path}"
            )
        if prior_path != replacement_path and (
            prior_path not in changed_paths or (repo / prior_path).exists()
        ):
            return (
                f"{manifest_relative} path migration transaction did not "
                f"replace prior manifest: {prior_path}"
            )
        try:
            replacement_payload = json.loads((repo / replacement_path).read_text())
        except (json.JSONDecodeError, OSError):
            return (
                f"{manifest_relative} path migration replacement manifest is "
                f"unreadable: {replacement_path}"
            )
        expected_migration = {
            "receipt_path": receipt_path,
            "receipt_sha256": receipt_sha256,
            "plan_sha256": plan_sha256,
            "prior_manifest_path": prior_path,
            "prior_manifest_sha256": binding["prior_sha256"],
        }
        if (
            not isinstance(replacement_payload, dict)
            or replacement_payload.get("schema_version")
            != APPLIED_ENCODING_MANIFEST_SCHEMA
            or replacement_payload.get("tool") != PATH_MIGRATION_TOOL
            or replacement_payload.get("migration") != expected_migration
            or not isinstance(replacement_payload.get("applied_files"), list)
        ):
            return (
                f"{manifest_relative} path migration replacement manifest is "
                f"not transaction-bound: {replacement_path}"
            )
        for applied_entry in replacement_payload["applied_files"]:
            if not isinstance(applied_entry, dict):
                return (
                    f"{manifest_relative} path migration replacement applied "
                    "files are malformed"
                )
            relative, applied_issue = applied_repo_relative(
                repo,
                replacement_path,
                applied_entry.get("path"),
            )
            if applied_issue is not None or relative is None:
                return applied_issue or (
                    f"{manifest_relative} path migration replacement applied "
                    "files are malformed"
                )
            if applied_entry.get("deleted") is True:
                if set(applied_entry) != {"path", "deleted"}:
                    return (
                        f"{manifest_relative} path migration replacement applied "
                        "files are malformed"
                    )
                receipt_applied_deleted.add(relative)
            elif set(applied_entry) == {"path", "sha256"} and is_sha256(
                applied_entry.get("sha256")
            ):
                receipt_applied_live.add(relative)
            else:
                return (
                    f"{manifest_relative} path migration replacement applied "
                    "files are malformed"
                )

    seen_move_sources: set[str] = set()
    seen_move_destinations: set[str] = set()
    for move in receipt_moves:
        if (
            not isinstance(move, dict)
            or set(move) != {"from", "to", "from_sha256", "to_sha256", "kind"}
            or not isinstance(move.get("from"), str)
            or not isinstance(move.get("to"), str)
            or not is_sha256(move.get("from_sha256"))
            or not is_sha256(move.get("to_sha256"))
            or move.get("kind") not in {"primary", "companion"}
        ):
            return f"{manifest_relative} path migration moves are malformed"
        old_path = move["from"]
        new_path = move["to"]
        old_posix = PurePosixPath(old_path)
        new_posix = PurePosixPath(new_path)
        if (
            old_posix.is_absolute()
            or new_posix.is_absolute()
            or old_posix.as_posix() != old_path
            or new_posix.as_posix() != new_path
            or any(part in {"", ".", ".."} for part in old_posix.parts)
            or any(part in {"", ".", ".."} for part in new_posix.parts)
            or old_path in seen_move_sources
            or new_path in seen_move_destinations
        ):
            return f"{manifest_relative} path migration moves are malformed"
        seen_move_sources.add(old_path)
        seen_move_destinations.add(new_path)
        actual_before = git_blob_sha256(repo, operation_base_ref, old_path)
        if actual_before != move["from_sha256"]:
            return (
                f"{manifest_relative} path migration before sha256 does not "
                f"match its exact Git base blob: {old_path}"
            )
        new_file = repo / new_path
        if (
            old_path not in changed_paths
            or new_path not in changed_paths
            or (repo / old_path).exists()
            or not new_file.is_file()
            or hashlib.sha256(new_file.read_bytes()).hexdigest()
            != move["to_sha256"]
            or old_path not in receipt_applied_deleted
            or new_path not in receipt_applied_live
        ):
            return (
                f"{manifest_relative} path migration transaction is incomplete "
                f"for move: {old_path} -> {new_path}"
            )

    seen_rewrites: set[str] = set()
    for rewrite in receipt_rewrites:
        if (
            not isinstance(rewrite, dict)
            or set(rewrite)
            != {"path", "before_sha256", "after_sha256", "replacements"}
            or not isinstance(rewrite.get("path"), str)
            or not is_sha256(rewrite.get("before_sha256"))
            or not is_sha256(rewrite.get("after_sha256"))
            or not isinstance(rewrite.get("replacements"), list)
        ):
            return f"{manifest_relative} path migration rewrites are malformed"
        rewrite_path = rewrite["path"]
        rewrite_posix = PurePosixPath(rewrite_path)
        if (
            rewrite_posix.is_absolute()
            or rewrite_posix.as_posix() != rewrite_path
            or any(part in {"", ".", ".."} for part in rewrite_posix.parts)
            or rewrite_path in seen_rewrites
        ):
            return f"{manifest_relative} path migration rewrites are malformed"
        seen_rewrites.add(rewrite_path)
        actual_before = git_blob_sha256(repo, operation_base_ref, rewrite_path)
        live_file = repo / rewrite_path
        if actual_before != rewrite["before_sha256"]:
            return (
                f"{manifest_relative} path migration rewrite before sha256 "
                f"does not match its exact Git base blob: {rewrite_path}"
            )
        if (
            rewrite_path not in changed_paths
            or not live_file.is_file()
            or hashlib.sha256(live_file.read_bytes()).hexdigest()
            != rewrite["after_sha256"]
            or rewrite_path not in receipt_applied_live
        ):
            return (
                f"{manifest_relative} path migration transaction is incomplete "
                f"for rewrite: {rewrite_path}"
            )

    nested_entries = migrated_manifest.get("applied_files")
    outer_entries = payload.get("applied_files")
    if not isinstance(nested_entries, list) or not isinstance(outer_entries, list):
        return f"{manifest_relative} path migration applied files are malformed"

    nested_hashes: dict[str, str] = {}
    for entry in nested_entries:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"path", "sha256"}
            or not isinstance(entry.get("path"), str)
            or not is_sha256(entry.get("sha256"))
            or entry["path"] in nested_hashes
        ):
            return f"{manifest_relative} migrated_manifest file entries are malformed"
        nested_hashes[entry["path"]] = entry["sha256"]
    if not nested_hashes:
        return f"{manifest_relative} migrated_manifest has no protected files"

    relevant_moves: dict[str, dict] = {}
    for move in receipt_moves:
        if not isinstance(move, dict) or move.get("from") not in nested_hashes:
            continue
        old_path = move["from"]
        if (
            set(move) != {"from", "to", "from_sha256", "to_sha256", "kind"}
            or not isinstance(move.get("to"), str)
            or not is_sha256(move.get("from_sha256"))
            or not is_sha256(move.get("to_sha256"))
            or move.get("kind") not in {"primary", "companion"}
            or old_path in relevant_moves
        ):
            return f"{manifest_relative} has malformed relevant migration moves"
        relevant_moves[old_path] = move

    actual_live: dict[str, str] = {}
    actual_deleted: set[str] = set()
    for entry in outer_entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            return f"{manifest_relative} path migration applied files are malformed"
        path = entry["path"]
        if entry.get("deleted") is True:
            if set(entry) != {"path", "deleted"} or path in actual_deleted:
                return f"{manifest_relative} path migration deletions are malformed"
            actual_deleted.add(path)
        elif set(entry) == {"path", "sha256"} and is_sha256(entry.get("sha256")):
            if path in actual_live:
                return f"{manifest_relative} path migration live files are duplicated"
            actual_live[path] = entry["sha256"]
        else:
            return f"{manifest_relative} path migration applied files are malformed"

    moved_paths = {
        old_path: str(move["to"]) for old_path, move in relevant_moves.items()
    }
    expected_deleted = set(moved_paths)
    expected_live = {moved_paths.get(old_path, old_path) for old_path in nested_hashes}
    if (
        not actual_deleted <= set(nested_hashes)
        or actual_deleted != expected_deleted
        or set(actual_live) != expected_live
    ):
        return (
            f"{manifest_relative} applied files do not match its relevant "
            "path-migration moves"
        )

    rewrites_by_path = {
        rewrite.get("path"): rewrite
        for rewrite in receipt_rewrites
        if isinstance(rewrite, dict) and isinstance(rewrite.get("path"), str)
    }
    for old_path, old_hash in nested_hashes.items():
        live_path = moved_paths.get(old_path, old_path)
        live_hash = actual_live[live_path]
        move = relevant_moves.get(old_path)
        if move is not None and (
            move["from_sha256"] != old_hash or move["to_sha256"] != live_hash
        ):
            return f"{manifest_relative} file hashes disagree with its migration move"
        rewrite = rewrites_by_path.get(live_path)
        if old_hash != live_hash and (
            not isinstance(rewrite, dict)
            or rewrite.get("before_sha256") != old_hash
            or rewrite.get("after_sha256") != live_hash
        ):
            return (
                f"{manifest_relative} changed file is not hash-bound to a "
                "migration rewrite"
            )
        if rewrite is not None and (
            rewrite.get("before_sha256") != old_hash
            or rewrite.get("after_sha256") != live_hash
        ):
            return (
                f"{manifest_relative} file hashes disagree with its migration rewrite"
            )
    return None


def changed_manifest_entries(
    repo: Path,
    changes: list[tuple[str, str]],
    *,
    resolved_refs: tuple[str, str] | None,
    worktree_changed_paths: set[str],
) -> tuple[dict[str, set[str]], set[str], set[str], list[str]]:
    """Load receipt entries only from manifests changed in this worktree."""
    entries: dict[str, set[str]] = {}
    authorized_deleted_manifests: set[str] = set()
    authorized_migration_receipts: set[str] = set()
    issues: list[str] = []
    changed_paths = {changed for _, changed in changes}
    changed_protected_paths = {
        changed
        for changed in changed_paths
        if is_protected_rulespec_path(PurePosixPath(changed))
    }
    valid_manifest_claims: dict[str, set[str]] = {}
    claim_transactions: dict[str, dict[str, set[str]]] = {}
    encoder_version, encoder_commit = pinned_encoder_identity(repo)
    noncanonical_manifests = sorted(
        {
            changed
            for _, changed in changes
            if is_encoding_manifest_path(PurePosixPath(changed))
            and not is_current_encoding_manifest_path(PurePosixPath(changed))
            and (repo / changed).is_file()
        }
    )
    issues.extend(
        f"{manifest} is not in the canonical root encoding-manifest directory"
        for manifest in noncanonical_manifests
    )
    manifest_paths = sorted(
        {
            changed
            for _, changed in changes
            if is_current_encoding_manifest_path(PurePosixPath(changed))
            and (repo / changed).is_file()
        }
    )
    for manifest_relative in manifest_paths:
        manifest_file = repo / manifest_relative
        try:
            payload = json.loads(manifest_file.read_text())
        except (json.JSONDecodeError, OSError):
            issues.append(f"{manifest_relative} is not valid readable JSON")
            continue
        if not isinstance(payload, dict):
            issues.append(f"{manifest_relative} is not a JSON object")
            continue
        if payload.get("schema_version") != APPLIED_ENCODING_MANIFEST_SCHEMA:
            issues.append(f"{manifest_relative} is not an encoder apply manifest")
            continue
        if not signature_is_structurally_valid(payload):
            issues.append(
                f"{manifest_relative} lacks a structurally valid protected signature"
            )
            continue
        if not manifest_uses_pinned_encoder(
            payload, version=encoder_version, commit=encoder_commit
        ):
            issues.append(
                f"{manifest_relative} does not identify the repository-pinned encoder"
            )
            continue
        tool = payload.get("tool")
        is_apply = tool == "axiom-encode encode --apply"
        is_retire = tool == "axiom-encode retire"
        is_migration = tool == PATH_MIGRATION_TOOL
        if not (is_apply or is_retire or is_migration):
            issues.append(
                f"{manifest_relative} is not an axiom-encode "
                "apply/retire/migration receipt"
            )
            continue
        operation_base_ref: str | None = None
        expected_fields = (
            model_manifest_expected_fields(payload)
            if is_apply
            else (
                RETIRE_APPLY_MANIFEST_FIELDS
                if is_retire
                else PATH_MIGRATION_APPLY_MANIFEST_FIELDS
            )
        )
        if expected_fields is None:
            issues.append(
                f"{manifest_relative} has invalid target-operation or creation evidence"
            )
            continue
        codex_fields = {"codex_cli_version", "codex_cli_sha256"}
        actual_fields = set(payload)
        if is_apply and payload.get("backend") == "codex":
            exact_fields = actual_fields - codex_fields
            codex_shape_valid = actual_fields & codex_fields in (set(), codex_fields)
        else:
            exact_fields = actual_fields
            codex_shape_valid = not (actual_fields & codex_fields)
        if exact_fields != expected_fields or not codex_shape_valid:
            issues.append(
                f"{manifest_relative} does not match the exact current-v5 "
                "apply manifest fields"
            )
            continue
        if is_apply and payload.get("backend") not in ENCODER_BACKENDS:
            issues.append(
                f"{manifest_relative} does not record a genuine encoder backend"
            )
            continue
        if is_apply and not has_exact_model_manifest_structure(payload):
            issues.append(
                f"{manifest_relative} is not an exact model-generated v5 receipt"
            )
            continue
        if is_retire and (
            not isinstance(payload.get("reason"), str)
            or not payload["reason"].strip()
            or not has_exact_model_manifest_structure(payload.get("retired_manifest"))
            or not manifest_uses_pinned_encoder(
                payload["retired_manifest"],
                version=encoder_version,
                commit=encoder_commit,
            )
            or not isinstance(payload.get("source_attestation"), dict)
            or not retirement_paths_match(payload)
        ):
            issues.append(f"{manifest_relative} is not an exact retirement v5 receipt")
            continue
        if is_retire:
            operation_base_ref, operation_base_issue = receipt_operation_base_ref(
                repo,
                manifest_relative,
                resolved_refs=resolved_refs,
                worktree_changed_paths=worktree_changed_paths,
            )
            if operation_base_issue is not None or operation_base_ref is None:
                issues.append(
                    operation_base_issue
                    or f"{manifest_relative} exact pre-operation Git base is unavailable"
                )
                continue
            retirement_issue = retirement_before_state_issue(
                repo,
                manifest_relative,
                payload,
                operation_base_ref,
            )
            if retirement_issue is not None:
                issues.append(retirement_issue)
                continue
        if is_apply and payload.get("target_operation") == "create":
            operation_base_ref, operation_base_issue = receipt_operation_base_ref(
                repo,
                manifest_relative,
                resolved_refs=resolved_refs,
                worktree_changed_paths=worktree_changed_paths,
            )
            if operation_base_issue is not None or operation_base_ref is None:
                issues.append(
                    operation_base_issue
                    or f"{manifest_relative} exact pre-operation Git base is unavailable"
                )
                continue
            creation_issue = creation_before_state_issue(
                repo,
                manifest_relative,
                payload,
                operation_base_ref,
            )
            if creation_issue is not None:
                issues.append(creation_issue)
                continue
        if is_migration:
            if not isinstance(payload.get("source_attestation"), dict):
                issues.append(
                    f"{manifest_relative} path migration source attestation is invalid"
                )
                continue
            operation_base_ref, operation_base_issue = receipt_operation_base_ref(
                repo,
                manifest_relative,
                resolved_refs=resolved_refs,
                worktree_changed_paths=worktree_changed_paths,
            )
            if operation_base_issue is not None or operation_base_ref is None:
                issues.append(
                    operation_base_issue
                    or f"{manifest_relative} exact pre-operation Git base is unavailable"
                )
                continue
            migration_issue = migration_manifest_structure_issue(
                repo,
                manifest_relative,
                payload,
                changed_paths,
                encoder_version=encoder_version,
                encoder_commit=encoder_commit,
                operation_base_ref=operation_base_ref,
            )
            if migration_issue:
                issues.append(migration_issue)
                continue
            authorized_deleted_manifests.add(
                payload["migration"]["prior_manifest_path"]
            )
            authorized_migration_receipts.add(payload["migration"]["receipt_path"])
        transaction_id = (
            f"migration:{payload['migration']['receipt_path']}"
            if is_migration
            else f"manifest:{manifest_relative}"
        )
        manifest_claims = valid_manifest_claims.setdefault(manifest_relative, set())
        applied_files = payload.get("applied_files")
        if not isinstance(applied_files, list):
            issues.append(f"{manifest_relative} does not list applied files")
            continue
        seen_manifest_applied: set[str] = set()
        for entry in applied_files:
            if not isinstance(entry, dict):
                issues.append(
                    f"{manifest_relative} has a malformed applied file entry"
                )
                continue
            applied = entry.get("path")
            if not isinstance(applied, str):
                issues.append(
                    f"{manifest_relative} has an applied file without a path"
                )
                continue
            relative, applied_issue = applied_repo_relative(
                repo,
                manifest_relative,
                applied,
            )
            if applied_issue is not None or relative is None:
                issues.append(
                    applied_issue
                    or f"{manifest_relative} has an invalid applied file path"
                )
                continue
            if relative in seen_manifest_applied:
                issues.append(
                    f"{manifest_relative} has a duplicate applied file: {relative}"
                )
                continue
            seen_manifest_applied.add(relative)
            manifest_claims.add(relative)
            claim_transactions.setdefault(relative, {}).setdefault(
                transaction_id,
                set(),
            ).add(manifest_relative)
            current = repo / relative
            if entry.get("deleted") is True:
                if set(entry) != {"path", "deleted"}:
                    issues.append(
                        f"{manifest_relative} has a malformed deleted file entry"
                    )
                    continue
                if not (is_retire or is_migration):
                    issues.append(
                        f"{manifest_relative} lists a deletion but is not an "
                        "axiom-encode retire receipt"
                    )
                    continue
                if current.exists() and relative not in changed_protected_paths:
                    issues.append(
                        f"{manifest_relative} claims a deletion that is not "
                        f"present in the complete transaction: {relative}"
                    )
                entries.setdefault(relative, set()).add(APPLIED_ENCODING_DELETED_MARKER)
            elif isinstance(entry.get("sha256"), str):
                if set(entry) != {"path", "sha256"} or not is_sha256(
                    entry.get("sha256")
                ):
                    issues.append(
                        f"{manifest_relative} has a malformed live file entry"
                    )
                    continue
                if not (is_apply or is_migration):
                    issues.append(
                        f"{manifest_relative} lists live content but is an "
                        "axiom-encode retire receipt"
                    )
                    continue
                if not current.is_file() and relative not in changed_protected_paths:
                    issues.append(
                        f"{manifest_relative} claims live content missing from "
                        f"the complete transaction: {relative}"
                    )
                current_hash = (
                    hashlib.sha256(current.read_bytes()).hexdigest()
                    if current.is_file()
                    else None
                )
                if (
                    current_hash != entry["sha256"]
                    and relative not in changed_protected_paths
                ):
                    issues.append(
                        f"{manifest_relative} claims a live sha256 that does not "
                        f"match the complete transaction: {relative}"
                    )
                entries.setdefault(relative, set()).add(entry["sha256"])
            else:
                issues.append(f"{manifest_relative} has an invalid applied file entry")
    for manifest_relative, claims in sorted(valid_manifest_claims.items()):
        if not (claims & changed_protected_paths):
            issues.append(
                f"{manifest_relative} changed without claiming any protected "
                "RuleSpec path in its own same-change transaction"
            )
    for relative, transactions in sorted(claim_transactions.items()):
        if len(transactions) <= 1:
            continue
        claimants = sorted(
            manifest
            for manifests in transactions.values()
            for manifest in manifests
        )
        issues.append(
            f"{relative} is claimed by conflicting changed receipt transactions: "
            + ", ".join(claimants)
        )
    return (
        entries,
        authorized_deleted_manifests,
        authorized_migration_receipts,
        issues,
    )


def changed_rulespec_receipt_issues(
    repo: Path,
    *,
    use_github_event: bool | None = None,
) -> list[str]:
    """Preflight branch and worktree RuleSpec against same-change receipts.

    This unions the canonical merge-base-to-HEAD diff with staged, unstaged,
    and untracked state. The protected ``guard-generated`` run remains
    authoritative for trust-root signature verification.
    """
    worktree_changes = changed_worktree_entries(repo)
    if use_github_event is None:
        use_github_event = repo.resolve() == ROOT.resolve()
    resolved_refs, committed_issues = committed_base_to_head_refs(
        repo,
        use_github_event=use_github_event,
    )
    committed_changes: list[tuple[str, str]] = []
    if resolved_refs is not None:
        try:
            committed_changes = [
                ("H ", path) for path in changed_ref_paths(repo, *resolved_refs)
            ]
        except subprocess.CalledProcessError as exc:
            committed_issues.append(
                f"cannot read committed base-to-head RuleSpec diff: {exc}"
            )
    changes = committed_changes + worktree_changes
    snapshot_issues = changed_snapshot_issues(worktree_changes)
    changed_manifests = sorted(
        {
            changed
            for _, changed in changes
            if is_encoding_manifest_path(PurePosixPath(changed))
        }
    )
    changed_migration_receipts = sorted(
        {
            changed
            for _, changed in changes
            if is_path_migration_receipt_path(PurePosixPath(changed))
        }
    )
    protected = sorted(
        {
            changed
            for _, changed in changes
            if is_protected_rulespec_path(PurePosixPath(changed))
        }
    )
    if not protected:
        return sorted(
            committed_issues
            + snapshot_issues
            + [
                f"{manifest} changed without any protected RuleSpec path; "
                "encoding manifests may be written only by the matching "
                "encoder operation"
                for manifest in changed_manifests
            ]
            + [
                f"{receipt} changed without any protected RuleSpec path; "
                "path-migration receipts may be written only by "
                "`axiom-encode migrate-rulespec-paths`"
                for receipt in changed_migration_receipts
            ]
        )

    (
        receipt_entries,
        authorized_deleted_manifests,
        authorized_migration_receipts,
        issues,
    ) = changed_manifest_entries(
        repo,
        changes,
        resolved_refs=resolved_refs,
        worktree_changed_paths={changed for _, changed in worktree_changes},
    )
    issues.extend(committed_issues)
    issues.extend(snapshot_issues)
    issues.extend(
        f"{receipt} changed without a changed path-migration replacement manifest"
        for receipt in sorted(
            set(changed_migration_receipts) - authorized_migration_receipts
        )
    )
    deleted_manifests = {
        changed
        for _, changed in changes
        if is_encoding_manifest_path(PurePosixPath(changed))
        and not (repo / changed).exists()
    }
    issues.extend(
        f"{manifest} was deleted without a changed path-migration replacement"
        for manifest in sorted(deleted_manifests - authorized_deleted_manifests)
    )
    for relative in protected:
        unsupported_issue = unsupported_protected_path_issue(relative)
        if unsupported_issue is not None:
            issues.append(unsupported_issue)
            continue
        expected = receipt_entries.get(relative)
        if expected is None:
            issues.append(
                f"{relative} changed but is not listed in a same-change "
                "encoder apply/retire/migration receipt"
            )
            continue
        current = repo / relative
        if current.exists():
            if APPLIED_ENCODING_DELETED_MARKER in expected:
                issues.append(
                    f"{relative} is listed as deleted in a changed receipt "
                    "but still exists"
                )
                continue
            current_hash = hashlib.sha256(current.read_bytes()).hexdigest()
            if current_hash not in expected:
                issues.append(
                    f"{relative} content does not match a same-change "
                    "encoder apply receipt sha256"
                )
        elif APPLIED_ENCODING_DELETED_MARKER not in expected:
            issues.append(
                f"{relative} was deleted but lacks a same-change "
                "axiom-encode retire marker"
            )
    return sorted(set(issues))


def test_locally_changed_rulespec_has_same_change_encoder_receipt() -> None:
    issues = changed_rulespec_receipt_issues(ROOT)

    assert issues == [], (
        "Branch/worktree RuleSpec receipt structural preflight failed. Manual "
        "RuleSpec "
        "changes are not allowed. Every new, modified, renamed, or deleted "
        "RuleSpec module and companion must be installed by "
        "`axiom-encode encode <citation> --apply` (or retired by "
        "`axiom-encode retire`, or renamed by "
        "`axiom-encode migrate-rulespec-paths`) with a matching current-v5 "
        "receipt in the same change. This local preflight checks receipt "
        "structure and hashes only; "
        "the shared protected `guard-generated` gate authenticates Ed25519 "
        "signatures across the committed base-to-head diff. Never create, copy, "
        "edit, or delete RuleSpec YAML manually. If the encoder, corpus, or "
        "signing broker blocks apply, stop and report the blocker:\n"
        + "\n".join(issues)
    )


def test_committed_unsupported_rulespec_surfaces_are_frozen_in_ci() -> None:
    """Keep ProgramSpecs and legacy manual RuleSpec closed after commit too."""
    refs = github_base_to_head_refs()
    if refs is None:
        return
    changed = changed_ref_paths(ROOT, *refs)
    issues = sorted(
        issue
        for relative in changed
        if (issue := unsupported_protected_path_issue(relative)) is not None
    )

    assert issues == [], (
        "Committed RuleSpec changed on a surface with no accepted signed "
        "authoring path. The local worktree preflight and this base-to-head CI "
        "freeze must agree; add a protected encoder contract before changing "
        "these files:\n" + "\n".join(issues)
    )


@functools.cache
def latest_manifest_entries() -> dict[Path, tuple[Path, dict]]:
    """Authoritative (manifest path, applied_files entry) per rule module.

    Companion ``.test.yaml`` entries are ignored; when several manifests
    cover one module, the newest ``generated_at`` wins.
    """
    latest: dict[Path, tuple[str, Path, dict]] = {}
    for base, manifest_dir in manifest_roots():
        for manifest_path in sorted(manifest_dir.rglob("*.json")):
            payload = json.loads(manifest_path.read_text())
            generated_at = str(payload.get("generated_at") or "")
            applied_files = payload.get("applied_files")
            if not isinstance(applied_files, list):
                continue
            for entry in applied_files:
                if not isinstance(entry, dict):
                    continue
                applied = entry.get("path")
                if not applied or applied.endswith(".test.yaml"):
                    continue
                module = resolve_applied_path(base, applied)
                current = latest.get(module)
                if current is None or generated_at > current[0]:
                    latest[module] = (generated_at, manifest_path, entry)
    return {
        module: (manifest_path, entry)
        for module, (_, manifest_path, entry) in latest.items()
    }


def test_encoded_modules_match_their_manifests() -> None:
    stale: list[str] = []

    for module, (manifest_path, entry) in sorted(latest_manifest_entries().items()):
        if not module.is_file():
            continue  # covered by test_manifests_reference_existing_modules
        expected = entry.get("sha256")
        if entry.get("deleted") or not expected:
            stale.append(
                f"{module.relative_to(ROOT).as_posix()} exists but "
                f"{manifest_path.relative_to(ROOT).as_posix()} records a deletion"
            )
            continue
        if hashlib.sha256(module.read_bytes()).hexdigest() != expected:
            stale.append(module.relative_to(ROOT).as_posix())

    assert stale == [], (
        "Encoded rule modules drifted from their encoding manifests "
        "(edited outside the axiom-encode path?). RuleSpec YAML must be "
        "installed only by `axiom-encode encode <citation> --apply`; do not "
        "hand-edit the YAML or refresh its manifest manually. Re-run the "
        "encoder for each module below:\n" + "\n".join(stale)
    )


def test_manifests_reference_existing_modules() -> None:
    orphaned = [
        module.relative_to(ROOT).as_posix()
        for module, (_, entry) in sorted(latest_manifest_entries().items())
        if not module.is_file() and entry.get("sha256") and not entry.get("deleted")
    ]

    assert orphaned == KNOWN_ORPHANED_ENCODING_MANIFESTS, (
        "Encoding manifests reference modules that no longer exist at the "
        "recorded path. Move or regenerate the manifest alongside the "
        "module, or delete it if the module was retired:\n" + "\n".join(orphaned)
    )


def test_unmanifested_modules_are_reported_not_failed() -> None:
    manifested = set(latest_manifest_entries())
    unmanifested = [
        path.relative_to(ROOT).as_posix()
        for path in iter_rulespec_files()
        if path not in manifested
    ]

    # Early encodings predate apply-manifests, so an unchanged missing manifest
    # is pre-existing debt rather than drift. The changed-file ratchet below
    # fails if any of these legacy modules is touched without the encoder.
    if unmanifested:
        warnings.warn(
            f"{len(unmanifested)} rule modules have no encoding manifest and "
            "remain grandfathered only while unchanged "
            f"(e.g. {unmanifested[0]})",
            stacklevel=1,
        )


def _initialize_git_fixture(repo: Path) -> None:
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    toolchain = repo / ".axiom/workflow-toolchain.toml"
    toolchain.parent.mkdir(parents=True, exist_ok=True)
    toolchain.write_text(
        '[workflow_toolchain]\naxiom_encode_version = "0.2.1690"\n'
        'axiom_encode_ref = "29b30fb7855c7306d9ead9ddba020dea40f938cc"\n'
    )


def _write_rulespec_fixture(repo: Path, relative: str) -> None:
    rulespec_file = repo / relative
    rulespec_file.parent.mkdir(parents=True, exist_ok=True)
    if relative.endswith(".test.yaml"):
        rulespec_file.write_text("cases: []\n")
    else:
        rulespec_file.write_text("format: rulespec/v1\nrules: []\n")


def _commit_rulespec_fixtures(repo: Path, *relatives: str) -> None:
    _initialize_git_fixture(repo)
    for relative in relatives:
        _write_rulespec_fixture(repo, relative)
    _commit_fixture_paths(repo, *relatives)


def _commit_fixture_paths(repo: Path, *relatives: str) -> None:
    subprocess.run(["git", "-C", str(repo), "add", *relatives], check=True)
    _commit_staged_fixture(repo)


def _commit_staged_fixture(repo: Path, *, message: str = "fixture") -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "user.name=Axiom Test",
            "-c",
            "user.email=test@axiom.invalid",
            "commit",
            "-q",
            "-m",
            message,
        ],
        check=True,
    )
    if git_commit_ref(repo, "refs/remotes/origin/main") is None:
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "update-ref",
                "refs/remotes/origin/main",
                "HEAD",
            ],
            check=True,
        )


def _fixture_commit_tree(
    repo: Path,
    *,
    parents: list[str],
    message: str,
) -> str:
    tree = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
        text=True,
    ).strip()
    command = ["git", "-C", str(repo), "commit-tree", tree]
    for parent in parents:
        command.extend(["-p", parent])
    fixture_env = os.environ.copy()
    fixture_env.update(
        {
            "GIT_AUTHOR_NAME": "Axiom Test",
            "GIT_AUTHOR_EMAIL": "test@axiom.invalid",
            "GIT_COMMITTER_NAME": "Axiom Test",
            "GIT_COMMITTER_EMAIL": "test@axiom.invalid",
        }
    )
    return subprocess.check_output(
        command,
        input=message + "\n",
        text=True,
        env=fixture_env,
    ).strip()


def _structural_signature() -> dict[str, str]:
    # Local preflight checks shape only. Protected CI verifies Ed25519.
    return {
        "algorithm": "ed25519-domain-v1",
        "key_id": "sha256:" + "0" * 64,
        "value": base64.b64encode(b"\0" * 64).decode("ascii"),
    }


def _fake_encoder_git() -> dict[str, object]:
    return {
        "root": "/opt/axiom/axiom-encode",
        "commit": "29b30fb7855c7306d9ead9ddba020dea40f938cc",
        "dirty_tracked": False,
        "version": "0.2.1690",
        "version_commit": "1" * 40,
        "identity_source": "trusted-runtime-attestation",
    }


def _model_receipt_payload(applied_files: list[dict[str, object]]) -> dict:
    return {
        "schema_version": APPLIED_ENCODING_MANIFEST_SCHEMA,
        "generated_at": "2026-08-30T00:00:00+00:00",
        "tool": "axiom-encode encode --apply",
        "axiom_encode_version": "0.2.1690",
        "axiom_encode_git": _fake_encoder_git(),
        "generation_prompt_sha256": "2" * 64,
        "run_id": "fixture-run",
        "citation": "us/statute/26/9998",
        "runner": "openai-fixture",
        "backend": "openai",
        "model": "fixture-model",
        "validation_waiver_set_sha256": "3" * 64,
        "generated_output_root": "/tmp/fixture",
        "generated_output_file": "/tmp/fixture/rulespec.yaml",
        "generated_output_sha256": "4" * 64,
        "trace_file": "/tmp/fixture/trace.json",
        "trace_sha256": "5" * 64,
        "context_manifest_file": "/tmp/fixture/context.json",
        "context_manifest_sha256": "6" * 64,
        "applied_files": applied_files,
        "source_attestation": {},
        "validation_execution": {},
        "signature": _structural_signature(),
    }


def _write_changed_receipt(
    repo: Path,
    manifest_relative: str,
    applied: dict[str, str | None],
    *,
    retire: bool = False,
    retired_hashes: dict[str, str] | None = None,
    target_operation: str | None = None,
    creation_target: dict[str, object] | None = None,
) -> None:
    manifest_file = repo / manifest_relative
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    applied_files = []
    for relative, expected_hash in applied.items():
        if expected_hash is None:
            applied_files.append({"path": relative, "deleted": True})
        else:
            applied_files.append({"path": relative, "sha256": expected_hash})
    if retire:
        payload: dict[str, object] = {
            "schema_version": APPLIED_ENCODING_MANIFEST_SCHEMA,
            "generated_at": "2026-08-30T00:00:00+00:00",
            "tool": "axiom-encode retire",
            "reason": "fixture retirement",
            "axiom_encode_version": "0.2.1690",
            "axiom_encode_git": _fake_encoder_git(),
            "validation_waiver_set_sha256": "3" * 64,
            "applied_files": applied_files,
            "retired_manifest": _model_receipt_payload(
                [
                    {"path": relative, "sha256": expected_hash}
                    for relative, expected_hash in (retired_hashes or {}).items()
                ]
            ),
            "source_attestation": {},
            "signature": _structural_signature(),
        }
    else:
        payload = _model_receipt_payload(applied_files)
        if target_operation is not None:
            payload["target_operation"] = target_operation
        if creation_target is not None:
            payload["creation_target"] = creation_target
    manifest_file.write_text(json.dumps(payload) + "\n")


def _sha256(repo: Path, relative: str) -> str:
    return hashlib.sha256((repo / relative).read_bytes()).hexdigest()


def _creation_target_fixture(
    *,
    primary: str,
    base_commit: str,
    base_tree: str,
) -> tuple[str, str, dict[str, object]]:
    primary_path = PurePosixPath(primary)
    companion = primary_path.with_name(f"{primary_path.stem}.test.yaml").as_posix()
    manifest = (
        PurePosixPath(".axiom/encoding-manifests")
        .joinpath(primary_path)
        .with_suffix(".json")
        .as_posix()
    )
    return (
        companion,
        manifest,
        {
            "base_commit": base_commit,
            "base_tree": base_tree,
            "primary": primary,
            "companion": companion,
            "canonical_manifest": manifest,
            "orphan_manifest": expected_creation_orphan_manifest(primary_path),
        },
    )


def test_model_manifest_accepts_exact_historical_replace_and_create_shapes() -> None:
    historical = _model_receipt_payload([])
    assert has_exact_model_manifest_structure(historical)

    replacement = {**historical, "target_operation": "replace"}
    assert has_exact_model_manifest_structure(replacement)

    _companion, _manifest, creation = _creation_target_fixture(
        primary="us-nc/policies/income_tax/encoder_guard.yaml",
        base_commit="a" * 40,
        base_tree="b" * 40,
    )
    created = {
        **historical,
        "target_operation": "create",
        "creation_target": creation,
    }
    assert has_exact_model_manifest_structure(created)

    assert not has_exact_model_manifest_structure(
        {**historical, "target_operation": "unknown"}
    )
    assert not has_exact_model_manifest_structure(
        {**replacement, "creation_target": creation}
    )
    assert not has_exact_model_manifest_structure(
        {**historical, "creation_target": creation}
    )
    assert not has_exact_model_manifest_structure(
        {
            **created,
            "creation_target": {**creation, "base_tree": "not-a-tree"},
        }
    )


def test_replace_operation_receipt_satisfies_local_preflight(tmp_path: Path) -> None:
    primary = "us-nc/policies/income_tax/encoder_guard.yaml"
    companion = "us-nc/policies/income_tax/encoder_guard.test.yaml"
    manifest = ".axiom/encoding-manifests/us-nc/policies/income_tax/encoder_guard.json"
    _commit_rulespec_fixtures(tmp_path, primary, companion)
    (tmp_path / primary).write_text("format: rulespec/v1\nrules: [replacement]\n")
    (tmp_path / companion).write_text("cases: [{name: replacement}]\n")
    _write_changed_receipt(
        tmp_path,
        manifest,
        {primary: _sha256(tmp_path, primary), companion: _sha256(tmp_path, companion)},
        target_operation="replace",
    )

    assert changed_rulespec_receipt_issues(tmp_path) == []


def test_create_operation_receipt_binds_exact_absent_git_base(tmp_path: Path) -> None:
    _initialize_git_fixture(tmp_path)
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", ".axiom/workflow-toolchain.toml"],
        check=True,
    )
    _commit_staged_fixture(tmp_path, message="creation base")
    base_commit = git_commit_ref(tmp_path, "HEAD")
    base_tree = git_tree_ref(tmp_path, "HEAD")
    assert base_commit is not None and base_tree is not None
    primary = "us-nc/policies/income_tax/encoder_guard.yaml"
    companion, manifest, creation = _creation_target_fixture(
        primary=primary,
        base_commit=base_commit,
        base_tree=base_tree,
    )
    _write_rulespec_fixture(tmp_path, primary)
    _write_rulespec_fixture(tmp_path, companion)
    _write_changed_receipt(
        tmp_path,
        manifest,
        {primary: _sha256(tmp_path, primary), companion: _sha256(tmp_path, companion)},
        target_operation="create",
        creation_target=creation,
    )

    assert changed_rulespec_receipt_issues(tmp_path) == []

    payload = json.loads((tmp_path / manifest).read_text())
    payload["creation_target"]["base_tree"] = "0" * 40
    (tmp_path / manifest).write_text(json.dumps(payload) + "\n")
    assert (
        f"{manifest} creation identity does not match its exact pre-operation "
        "commit and tree"
        in changed_rulespec_receipt_issues(tmp_path)
    )


def test_create_operation_fails_when_target_existed_at_git_base(
    tmp_path: Path,
) -> None:
    primary = "us-nc/policies/income_tax/encoder_guard.yaml"
    companion = "us-nc/policies/income_tax/encoder_guard.test.yaml"
    _commit_rulespec_fixtures(tmp_path, primary, companion)
    base_commit = git_commit_ref(tmp_path, "HEAD")
    base_tree = git_tree_ref(tmp_path, "HEAD")
    assert base_commit is not None and base_tree is not None
    _companion, manifest, creation = _creation_target_fixture(
        primary=primary,
        base_commit=base_commit,
        base_tree=base_tree,
    )
    (tmp_path / primary).write_text("format: rulespec/v1\nrules: [forged-create]\n")
    (tmp_path / companion).write_text("cases: [{name: forged-create}]\n")
    _write_changed_receipt(
        tmp_path,
        manifest,
        {primary: _sha256(tmp_path, primary), companion: _sha256(tmp_path, companion)},
        target_operation="create",
        creation_target=creation,
    )

    assert (
        f"{manifest} creation target was not absent from its exact Git base: "
        f"{companion}, {primary}"
        in changed_rulespec_receipt_issues(tmp_path)
    )


def _assert_new_modified_deleted_paths_require_receipts(
    tmp_path: Path,
    *,
    new_path: str,
    modified_path: str,
    deleted_path: str,
) -> None:
    expected_suffix = (
        " changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    )

    def expected_issue(path: str) -> str:
        return unsupported_protected_path_issue(path) or path + expected_suffix

    new_repo = tmp_path / "new"
    _initialize_git_fixture(new_repo)
    _write_rulespec_fixture(new_repo, new_path)
    assert changed_rulespec_receipt_issues(new_repo) == [expected_issue(new_path)]

    modified_repo = tmp_path / "modified"
    _commit_rulespec_fixtures(modified_repo, modified_path)
    with (modified_repo / modified_path).open("a") as fixture:
        fixture.write("# manual edit\n")
    assert changed_rulespec_receipt_issues(modified_repo) == [
        expected_issue(modified_path)
    ]

    deleted_repo = tmp_path / "deleted"
    _commit_rulespec_fixtures(deleted_repo, deleted_path)
    (deleted_repo / deleted_path).unlink()
    assert changed_rulespec_receipt_issues(deleted_repo) == [
        expected_issue(deleted_path)
    ]


def test_program_specs_are_protected_when_new_modified_or_deleted(
    tmp_path: Path,
) -> None:
    program = "programs/us/encoder-guard/fy-2026.yaml"
    _assert_new_modified_deleted_paths_require_receipts(
        tmp_path,
        new_path=program,
        modified_path=program,
        deleted_path=program,
    )


def test_legacy_manual_rulespec_and_companion_are_protected(
    tmp_path: Path,
) -> None:
    module = "us-mo/manual/dss/snap/encoder-guard/block-1.yaml"
    companion = "us-mo/manual/dss/snap/encoder-guard/block-1.test.yaml"
    _assert_new_modified_deleted_paths_require_receipts(
        tmp_path,
        new_path=module,
        modified_path=companion,
        deleted_path=module,
    )


def test_base_to_head_freeze_detects_program_and_legacy_manual_changes(
    tmp_path: Path,
) -> None:
    seed = "us/statutes/26/9998.yaml"
    _commit_rulespec_fixtures(tmp_path, seed)
    base_ref = subprocess.check_output(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    program = "programs/us/encoder-guard/fy-2026.yaml"
    manual = "us-mo/manual/dss/snap/encoder-guard/block-1.yaml"
    _write_rulespec_fixture(tmp_path, program)
    _write_rulespec_fixture(tmp_path, manual)
    _commit_fixture_paths(tmp_path, program, manual)
    head_ref = subprocess.check_output(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        text=True,
    ).strip()

    changed = changed_ref_paths(tmp_path, base_ref, head_ref)

    assert changed == [program, manual]
    assert [unsupported_protected_path_issue(path) for path in changed] == [
        (
            f"{program} is a ProgramSpec, but the pinned toolchain has no "
            "signed ProgramSpec-authoring receipt path; ProgramSpec changes "
            "are blocked"
        ),
        (
            f"{manual} is legacy manual RuleSpec whose v1 owner requires an "
            "unsupported specialized encoder legacy-replacement receipt; "
            "legacy manual changes are blocked"
        ),
    ]


def test_unsupported_surface_freeze_ignores_non_rulespec_files() -> None:
    assert unsupported_protected_path_issue("programs/us/README.md") is None
    assert (
        unsupported_protected_path_issue(
            "us-mo/manual/dss/snap/encoder-guard/source.json"
        )
        is None
    )


def test_committed_atomic_new_modified_deleted_and_renamed_require_receipts(
    tmp_path: Path,
) -> None:
    suffix = (
        " changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    )

    new_repo = tmp_path / "new"
    seed = "us/statutes/26/9997.yaml"
    new_module = "us/statutes/26/9998.yaml"
    _commit_rulespec_fixtures(new_repo, seed)
    _write_rulespec_fixture(new_repo, new_module)
    _commit_fixture_paths(new_repo, new_module)
    assert changed_rulespec_receipt_issues(new_repo) == [new_module + suffix]

    modified_repo = tmp_path / "modified"
    modified_module = "us/regulations/26-cfr/1/9998.yaml"
    _commit_rulespec_fixtures(modified_repo, modified_module)
    (modified_repo / modified_module).write_text(
        "format: rulespec/v1\nrules: []\n# committed manual edit\n"
    )
    _commit_fixture_paths(modified_repo, modified_module)
    assert changed_rulespec_receipt_issues(modified_repo) == [modified_module + suffix]

    deleted_repo = tmp_path / "deleted"
    deleted_module = "us/policies/income_tax/encoder_guard_fixture.yaml"
    _commit_rulespec_fixtures(deleted_repo, deleted_module)
    (deleted_repo / deleted_module).unlink()
    _commit_fixture_paths(deleted_repo, deleted_module)
    assert changed_rulespec_receipt_issues(deleted_repo) == [deleted_module + suffix]

    renamed_repo = tmp_path / "renamed"
    old_module = "us/statutes/26/9998.yaml"
    new_module = "us/statutes/26/9999.yaml"
    _commit_rulespec_fixtures(renamed_repo, old_module)
    subprocess.run(
        ["git", "-C", str(renamed_repo), "mv", old_module, new_module],
        check=True,
    )
    _commit_staged_fixture(renamed_repo)
    assert changed_rulespec_receipt_issues(renamed_repo) == [
        old_module + suffix,
        new_module + suffix,
    ]


def test_committed_apply_and_retire_receipts_satisfy_branch_preflight(
    tmp_path: Path,
) -> None:
    apply_repo = tmp_path / "apply"
    seed = "us/statutes/26/9997.yaml"
    module = "us/policies/income_tax/encoder_guard_fixture.yaml"
    manifest = (
        ".axiom/encoding-manifests/us/policies/income_tax/encoder_guard_fixture.json"
    )
    _commit_rulespec_fixtures(apply_repo, seed)
    _write_rulespec_fixture(apply_repo, module)
    _write_changed_receipt(
        apply_repo,
        manifest,
        {module: _sha256(apply_repo, module)},
    )
    _commit_fixture_paths(apply_repo, module, manifest)
    assert changed_rulespec_receipt_issues(apply_repo) == []

    retire_repo = tmp_path / "retire"
    retired_module = "us/statutes/26/9998.yaml"
    retired_manifest = ".axiom/encoding-manifests/us/statutes/26/9998.json"
    _commit_rulespec_fixtures(retire_repo, retired_module)
    retired_hash = _sha256(retire_repo, retired_module)
    (retire_repo / retired_module).unlink()
    _write_changed_receipt(
        retire_repo,
        retired_manifest,
        {retired_module: None},
        retire=True,
        retired_hashes={retired_module: retired_hash},
    )
    _commit_fixture_paths(retire_repo, retired_module, retired_manifest)
    assert changed_rulespec_receipt_issues(retire_repo) == []


def test_canonical_origin_main_wins_over_feature_branch_upstream(
    tmp_path: Path,
) -> None:
    seed = "us/statutes/26/9997.yaml"
    module = "us/statutes/26/9998.yaml"
    _commit_rulespec_fixtures(tmp_path, seed)
    base_ref = git_commit_ref(tmp_path, "HEAD")
    assert base_ref is not None
    _write_rulespec_fixture(tmp_path, module)
    _commit_fixture_paths(tmp_path, module)
    head_ref = git_commit_ref(tmp_path, "HEAD")
    assert head_ref is not None
    branch = subprocess.check_output(
        ["git", "-C", str(tmp_path), "branch", "--show-current"],
        text=True,
    ).strip()
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "update-ref",
            "refs/remotes/feature/topic",
            head_ref,
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "config",
            f"branch.{branch}.remote",
            "feature",
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "config",
            f"branch.{branch}.merge",
            "refs/heads/topic",
        ],
        check=True,
    )

    refs, issues = committed_base_to_head_refs(tmp_path)
    assert issues == []
    assert refs == (base_ref, head_ref)
    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    ]


def test_origin_main_stale_or_advanced_uses_unique_merge_base(tmp_path: Path) -> None:
    seed = "us/statutes/26/9997.yaml"
    module = "us/statutes/26/9998.yaml"
    _commit_rulespec_fixtures(tmp_path, seed)
    base_ref = git_commit_ref(tmp_path, "HEAD")
    assert base_ref is not None
    _write_rulespec_fixture(tmp_path, module)
    _commit_fixture_paths(tmp_path, module)
    head_ref = git_commit_ref(tmp_path, "HEAD")
    assert head_ref is not None

    refs, issues = committed_base_to_head_refs(tmp_path)
    assert issues == []
    assert refs == (base_ref, head_ref)

    advanced_main = _fixture_commit_tree(
        tmp_path,
        parents=[base_ref],
        message="advanced canonical main",
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "update-ref",
            "refs/remotes/origin/main",
            advanced_main,
        ],
        check=True,
    )
    refs, issues = committed_base_to_head_refs(tmp_path)
    assert issues == []
    assert refs == (base_ref, head_ref)
    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    ]


def test_missing_or_ambiguous_canonical_base_fails_closed(tmp_path: Path) -> None:
    missing_repo = tmp_path / "missing"
    seed = "us/statutes/26/9997.yaml"
    _commit_rulespec_fixtures(missing_repo, seed)
    subprocess.run(
        [
            "git",
            "-C",
            str(missing_repo),
            "update-ref",
            "-d",
            "refs/remotes/origin/main",
        ],
        check=True,
    )
    assert changed_rulespec_receipt_issues(missing_repo) == [
        "cannot verify committed RuleSpec changes because canonical "
        "refs/remotes/origin/main is missing"
    ]

    unrelated_repo = tmp_path / "unrelated"
    _commit_rulespec_fixtures(unrelated_repo, seed)
    unrelated_main = _fixture_commit_tree(
        unrelated_repo,
        parents=[],
        message="unrelated canonical main",
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(unrelated_repo),
            "update-ref",
            "refs/remotes/origin/main",
            unrelated_main,
        ],
        check=True,
    )
    assert changed_rulespec_receipt_issues(unrelated_repo) == [
        "cannot verify committed RuleSpec changes because HEAD and canonical "
        "origin/main have no merge base"
    ]

    ambiguous_repo = tmp_path / "ambiguous"
    _commit_rulespec_fixtures(ambiguous_repo, seed)
    base_ref = git_commit_ref(ambiguous_repo, "HEAD")
    assert base_ref is not None
    left = _fixture_commit_tree(
        ambiguous_repo,
        parents=[base_ref],
        message="left",
    )
    right = _fixture_commit_tree(
        ambiguous_repo,
        parents=[base_ref],
        message="right",
    )
    left_merge = _fixture_commit_tree(
        ambiguous_repo,
        parents=[left, right],
        message="left merge",
    )
    right_merge = _fixture_commit_tree(
        ambiguous_repo,
        parents=[right, left],
        message="right merge",
    )
    subprocess.run(
        ["git", "-C", str(ambiguous_repo), "update-ref", "HEAD", left_merge],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(ambiguous_repo),
            "update-ref",
            "refs/remotes/origin/main",
            right_merge,
        ],
        check=True,
    )
    merge_bases = subprocess.check_output(
        [
            "git",
            "-C",
            str(ambiguous_repo),
            "merge-base",
            "--all",
            left_merge,
            right_merge,
        ],
        text=True,
    ).split()
    assert sorted(merge_bases) == sorted([left, right])
    refs, issues = committed_base_to_head_refs(ambiguous_repo)
    assert refs is None
    assert issues == [
        "cannot verify committed RuleSpec changes because HEAD and canonical "
        "origin/main have ambiguous merge bases: " + ", ".join(sorted([left, right]))
    ]


def test_committed_and_worktree_changes_are_validated_as_one_union(
    tmp_path: Path,
) -> None:
    seed = "us/statutes/26/9997.yaml"
    committed_module = "us/statutes/26/9998.yaml"
    worktree_module = "us/statutes/26/9999.yaml"
    _commit_rulespec_fixtures(tmp_path, seed)
    _write_rulespec_fixture(tmp_path, committed_module)
    _commit_fixture_paths(tmp_path, committed_module)
    _write_rulespec_fixture(tmp_path, worktree_module)

    suffix = (
        " changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    )
    assert changed_rulespec_receipt_issues(tmp_path) == [
        committed_module + suffix,
        worktree_module + suffix,
    ]


def test_github_event_before_cannot_launder_an_earlier_unauthorized_commit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = tmp_path / "repo"
    event_path = tmp_path / "event.json"
    seed = "us/statutes/26/9997.yaml"
    module = "us/statutes/26/9998.yaml"
    _commit_rulespec_fixtures(repo, seed)
    base_ref = git_commit_ref(repo, "HEAD")
    assert base_ref is not None
    _write_rulespec_fixture(repo, module)
    _commit_fixture_paths(repo, module)
    unauthorized_ref = git_commit_ref(repo, "HEAD")
    assert unauthorized_ref is not None
    readme = repo / "README.md"
    readme.write_text("unrelated follow-up\n")
    _commit_fixture_paths(repo, "README.md")
    head_ref = git_commit_ref(repo, "HEAD")
    assert head_ref is not None
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_SHA", head_ref)

    event_path.write_text(
        json.dumps({"before": unauthorized_ref, "after": head_ref}) + "\n"
    )
    refs, issues = committed_base_to_head_refs(repo, use_github_event=True)
    assert issues == []
    assert refs == (base_ref, head_ref)
    assert changed_rulespec_receipt_issues(repo, use_github_event=True) == [
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    ]

    retire_repo = tmp_path / "retire"
    retired_module = "us/statutes/26/9998.yaml"
    retired_manifest = ".axiom/encoding-manifests/us/statutes/26/9998.json"
    _commit_rulespec_fixtures(retire_repo, retired_module)
    retire_base = git_commit_ref(retire_repo, "HEAD")
    assert retire_base is not None
    retired_hash = _sha256(retire_repo, retired_module)
    (retire_repo / retired_module).unlink()
    _write_changed_receipt(
        retire_repo,
        retired_manifest,
        {retired_module: None},
        retire=True,
        retired_hashes={retired_module: retired_hash},
    )
    _commit_fixture_paths(retire_repo, retired_module, retired_manifest)
    retire_head = git_commit_ref(retire_repo, "HEAD")
    assert retire_head is not None
    subprocess.run(
        [
            "git",
            "-C",
            str(retire_repo),
            "update-ref",
            "refs/remotes/origin/main",
            retire_head,
        ],
        check=True,
    )
    event_path.write_text(
        json.dumps({"before": retire_base, "after": retire_head}) + "\n"
    )
    monkeypatch.setenv("GITHUB_SHA", retire_head)
    assert changed_rulespec_receipt_issues(
        retire_repo,
        use_github_event=True,
    ) == []

    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_SHA", head_ref)
    event_path.write_text(
        json.dumps({"pull_request": {"base": {"sha": unauthorized_ref}}}) + "\n"
    )
    refs, issues = committed_base_to_head_refs(repo, use_github_event=True)
    assert issues == []
    assert refs == (base_ref, head_ref)
    assert changed_rulespec_receipt_issues(repo, use_github_event=True) == [
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    ]


def test_github_push_main_widens_when_origin_main_already_equals_head(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = tmp_path / "repo"
    event_path = tmp_path / "push-main.json"
    seed = "us/statutes/26/9997.yaml"
    module = "us/statutes/26/9998.yaml"
    _commit_rulespec_fixtures(repo, seed)
    base_ref = git_commit_ref(repo, "HEAD")
    assert base_ref is not None
    _write_rulespec_fixture(repo, module)
    _commit_fixture_paths(repo, module)
    head_ref = git_commit_ref(repo, "HEAD")
    assert head_ref is not None
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "update-ref",
            "refs/remotes/origin/main",
            head_ref,
        ],
        check=True,
    )
    event_path.write_text(
        json.dumps({"before": base_ref, "after": head_ref}) + "\n"
    )
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_SHA", head_ref)

    refs, issues = committed_base_to_head_refs(repo, use_github_event=True)
    assert issues == []
    assert refs == (base_ref, head_ref)
    assert changed_rulespec_receipt_issues(repo, use_github_event=True) == [
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    ]


def test_github_push_after_must_be_canonical_and_match_head(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = tmp_path / "repo"
    event_path = tmp_path / "push.json"
    seed = "us/statutes/26/9997.yaml"
    _commit_rulespec_fixtures(repo, seed)
    head_ref = git_commit_ref(repo, "HEAD")
    assert head_ref is not None
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_SHA", head_ref)

    cases = [
        (
            {"before": head_ref},
            "GitHub Actions push after SHA is not canonical",
        ),
        (
            {"before": head_ref, "after": "F" * 40},
            "GitHub Actions push after SHA is not canonical",
        ),
        (
            {"before": head_ref, "after": "f" * 40},
            "GitHub Actions push after SHA does not match HEAD",
        ),
    ]
    for event, expected in cases:
        event_path.write_text(json.dumps(event) + "\n")
        refs, issues = committed_base_to_head_refs(repo, use_github_event=True)
        assert refs is None
        assert issues == [
            f"cannot resolve GitHub base-to-head RuleSpec diff: {expected}"
        ]


def test_github_zero_before_push_cannot_bypass_atomic_or_frozen_surfaces(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = tmp_path / "non-root"
    event_path = tmp_path / "zero-before.json"
    seed = "us/statutes/26/9997.yaml"
    atomic = "us/statutes/26/9998.yaml"
    program = "programs/us/encoder-guard/fy-2026.yaml"
    manual = "us-mo/manual/dss/snap/encoder-guard/block-1.yaml"
    _commit_rulespec_fixtures(repo, seed)
    base_ref = git_commit_ref(repo, "HEAD")
    assert base_ref is not None
    for path in (atomic, program, manual):
        _write_rulespec_fixture(repo, path)
    _commit_fixture_paths(repo, atomic, program, manual)
    head_ref = git_commit_ref(repo, "HEAD")
    assert head_ref is not None
    event_path.write_text(
        json.dumps({"before": "0" * 40, "after": head_ref}) + "\n"
    )
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_SHA", head_ref)

    assert github_base_to_head_refs(repo) == (base_ref, head_ref)
    changed = changed_ref_paths(repo, base_ref, head_ref)
    assert changed == [program, manual, atomic]
    assert sorted(
        issue
        for path in changed
        if (issue := unsupported_protected_path_issue(path)) is not None
    ) == sorted(
        [
            unsupported_protected_path_issue(program),
            unsupported_protected_path_issue(manual),
        ]
    )
    zero_before_issues = changed_rulespec_receipt_issues(
        repo,
        use_github_event=True,
    )
    assert unsupported_protected_path_issue(program) in zero_before_issues
    assert unsupported_protected_path_issue(manual) in zero_before_issues
    assert (
        f"{atomic} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    ) in zero_before_issues

    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "update-ref",
            "refs/remotes/origin/main",
            head_ref,
        ],
        check=True,
    )
    assert changed_rulespec_receipt_issues(
        repo,
        use_github_event=True,
    ) == [
        "cannot resolve GitHub base-to-head RuleSpec diff: GitHub Actions "
        "zero-before push has no trustworthy pre-push coverage boundary; "
        "canonical origin/main already equals HEAD"
    ]

    unrelated_main = _fixture_commit_tree(
        repo,
        parents=[],
        message="unrelated canonical main",
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "update-ref",
            "refs/remotes/origin/main",
            unrelated_main,
        ],
        check=True,
    )
    assert changed_rulespec_receipt_issues(
        repo,
        use_github_event=True,
    ) == [
        "cannot resolve GitHub base-to-head RuleSpec diff: cannot verify "
        "committed RuleSpec changes because HEAD and canonical origin/main "
        "have no merge base"
    ]


def test_clean_tracked_legacy_module_remains_grandfathered(tmp_path: Path) -> None:
    module = "us/statutes/26/9998.yaml"
    _commit_rulespec_fixtures(tmp_path, module)

    assert changed_rulespec_receipt_issues(tmp_path) == []


def test_modified_tracked_legacy_module_requires_manifest(tmp_path: Path) -> None:
    module = "us/statutes/26/9998.yaml"
    _commit_rulespec_fixtures(tmp_path, module)
    (tmp_path / module).write_text("format: rulespec/v1\nrules: []\n# manual edit\n")

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    ]


def test_untracked_new_module_requires_manifest(tmp_path: Path) -> None:
    module = "us/regulations/26-cfr/1/9998.yaml"
    _initialize_git_fixture(tmp_path)
    _write_rulespec_fixture(tmp_path, module)

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    ]


def test_staged_new_module_requires_manifest(tmp_path: Path) -> None:
    module = "us/policies/income_tax/encoder_guard_fixture.yaml"
    _initialize_git_fixture(tmp_path)
    _write_rulespec_fixture(tmp_path, module)
    subprocess.run(["git", "-C", str(tmp_path), "add", module], check=True)

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    ]


def test_mismatched_staged_snapshot_cannot_hide_behind_matching_worktree(
    tmp_path: Path,
) -> None:
    module = "us/policies/income_tax/encoder_guard_fixture.yaml"
    manifest = (
        ".axiom/encoding-manifests/us/policies/income_tax/encoder_guard_fixture.json"
    )
    _initialize_git_fixture(tmp_path)
    _write_rulespec_fixture(tmp_path, module)
    _write_changed_receipt(tmp_path, manifest, {module: "f" * 64})
    subprocess.run(["git", "-C", str(tmp_path), "add", module, manifest], check=True)

    (tmp_path / module).write_text(
        "format: rulespec/v1\nrules: []\n# unstaged matching content\n"
    )
    _write_changed_receipt(
        tmp_path,
        manifest,
        {module: _sha256(tmp_path, module)},
    )

    issues = changed_rulespec_receipt_issues(tmp_path)
    assert len(issues) == 1
    assert "span both the index and worktree" in issues[0]
    assert "Stage the complete encoder transaction or unstage it" in issues[0]


def test_new_main_and_companion_pass_with_same_change_apply_receipt(
    tmp_path: Path,
) -> None:
    module = "us/policies/income_tax/encoder_guard_fixture.yaml"
    companion = "us/policies/income_tax/encoder_guard_fixture.test.yaml"
    manifest = (
        ".axiom/encoding-manifests/us/policies/income_tax/encoder_guard_fixture.json"
    )
    _initialize_git_fixture(tmp_path)
    _write_rulespec_fixture(tmp_path, module)
    _write_rulespec_fixture(tmp_path, companion)
    _write_changed_receipt(
        tmp_path,
        manifest,
        {module: _sha256(tmp_path, module), companion: _sha256(tmp_path, companion)},
    )

    assert changed_rulespec_receipt_issues(tmp_path) == []


def test_partial_apply_validates_claimed_unchanged_companion_hash(
    tmp_path: Path,
) -> None:
    module = "us/statutes/26/9998.yaml"
    companion = "us/statutes/26/9998.test.yaml"
    manifest = ".axiom/encoding-manifests/us/statutes/26/9998.json"
    _commit_rulespec_fixtures(tmp_path, module, companion)
    (tmp_path / module).write_text("format: rulespec/v1\nrules: []\n# encoded\n")
    _write_changed_receipt(
        tmp_path,
        manifest,
        {module: _sha256(tmp_path, module), companion: "f" * 64},
    )

    assert (
        f"{manifest} claims a live sha256 that does not match the complete "
        f"transaction: {companion}"
        in changed_rulespec_receipt_issues(tmp_path)
    )


def test_unrelated_manifest_cannot_hitchhike_on_valid_protected_change(
    tmp_path: Path,
) -> None:
    existing = "us/statutes/26/9997.yaml"
    module = "us/statutes/26/9998.yaml"
    manifest = ".axiom/encoding-manifests/us/statutes/26/9998.json"
    unrelated_manifest = ".axiom/encoding-manifests/us/statutes/26/9997.json"
    _commit_rulespec_fixtures(tmp_path, existing)
    _write_rulespec_fixture(tmp_path, module)
    _write_changed_receipt(
        tmp_path,
        manifest,
        {module: _sha256(tmp_path, module)},
    )
    _write_changed_receipt(
        tmp_path,
        unrelated_manifest,
        {existing: _sha256(tmp_path, existing)},
    )

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{unrelated_manifest} changed without claiming any protected RuleSpec "
        "path in its own same-change transaction"
    ]


def test_conflicting_duplicate_receipts_cannot_authorize_one_path(
    tmp_path: Path,
) -> None:
    module = "us/statutes/26/9998.yaml"
    first = ".axiom/encoding-manifests/us/statutes/26/9998.json"
    second = ".axiom/encoding-manifests/us/statutes/26/duplicate-9998.json"
    _initialize_git_fixture(tmp_path)
    _write_rulespec_fixture(tmp_path, module)
    module_hash = _sha256(tmp_path, module)
    _write_changed_receipt(tmp_path, first, {module: module_hash})
    _write_changed_receipt(tmp_path, second, {module: module_hash})

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{module} is claimed by conflicting changed receipt transactions: "
        f"{first}, {second}"
    ]


def test_modified_companion_requires_same_change_receipt(tmp_path: Path) -> None:
    module = "us/statutes/26/9998.yaml"
    companion = "us/statutes/26/9998.test.yaml"
    _commit_rulespec_fixtures(tmp_path, module, companion)
    (tmp_path / companion).write_text("cases:\n  - name: manual\n")

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{companion} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt"
    ]


def test_deleted_main_and_companion_require_retire_receipt(tmp_path: Path) -> None:
    module = "us/statutes/26/9998.yaml"
    companion = "us/statutes/26/9998.test.yaml"
    _commit_rulespec_fixtures(tmp_path, module, companion)
    (tmp_path / module).unlink()
    (tmp_path / companion).unlink()

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{companion} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt",
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt",
    ]


def test_deleted_main_and_companion_pass_with_retire_receipt(tmp_path: Path) -> None:
    module = "us/statutes/26/9998.yaml"
    companion = "us/statutes/26/9998.test.yaml"
    manifest = ".axiom/encoding-manifests/us/statutes/26/9998.json"
    _commit_rulespec_fixtures(tmp_path, module, companion)
    retired_hashes = {
        module: _sha256(tmp_path, module),
        companion: _sha256(tmp_path, companion),
    }
    (tmp_path / module).unlink()
    (tmp_path / companion).unlink()
    _write_changed_receipt(
        tmp_path,
        manifest,
        {module: None, companion: None},
        retire=True,
        retired_hashes=retired_hashes,
    )

    assert changed_rulespec_receipt_issues(tmp_path) == []


def test_retirement_before_hash_must_match_exact_git_base_blob(
    tmp_path: Path,
) -> None:
    module = "us/statutes/26/9998.yaml"
    manifest = ".axiom/encoding-manifests/us/statutes/26/9998.json"
    _commit_rulespec_fixtures(tmp_path, module)
    (tmp_path / module).unlink()
    _write_changed_receipt(
        tmp_path,
        manifest,
        {module: None},
        retire=True,
        retired_hashes={module: "f" * 64},
    )

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{manifest} retirement before sha256 does not match its exact Git "
        f"base blob: {module}",
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt",
    ]


def test_partial_retirement_cannot_claim_an_unchanged_live_companion(
    tmp_path: Path,
) -> None:
    module = "us/statutes/26/9998.yaml"
    companion = "us/statutes/26/9998.test.yaml"
    manifest = ".axiom/encoding-manifests/us/statutes/26/9998.json"
    _commit_rulespec_fixtures(tmp_path, module, companion)
    before = {
        module: _sha256(tmp_path, module),
        companion: _sha256(tmp_path, companion),
    }
    (tmp_path / module).unlink()
    _write_changed_receipt(
        tmp_path,
        manifest,
        {module: None, companion: None},
        retire=True,
        retired_hashes=before,
    )

    assert (
        f"{manifest} claims a deletion that is not present in the complete "
        f"transaction: {companion}"
        in changed_rulespec_receipt_issues(tmp_path)
    )


def test_rename_requires_receipts_for_old_and_new_paths(tmp_path: Path) -> None:
    old_module = "us/statutes/26/9998.yaml"
    old_companion = "us/statutes/26/9998.test.yaml"
    new_module = "us/statutes/26/9999.yaml"
    new_companion = "us/statutes/26/9999.test.yaml"
    _commit_rulespec_fixtures(tmp_path, old_module, old_companion)
    subprocess.run(
        ["git", "-C", str(tmp_path), "mv", old_module, new_module], check=True
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "mv", old_companion, new_companion],
        check=True,
    )

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{old_companion} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt",
        f"{old_module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt",
        f"{new_companion} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt",
        f"{new_module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt",
    ]


def _write_path_migration_fixture(
    tmp_path: Path,
) -> tuple[str, str, str]:
    old_module = "us/statutes/26/9998.yaml"
    old_companion = "us/statutes/26/9998.test.yaml"
    new_module = "us/statutes/26/9999.yaml"
    new_companion = "us/statutes/26/9999.test.yaml"
    dependent = "us/policies/income_tax/dependent.yaml"
    dependent_companion = "us/policies/income_tax/dependent.test.yaml"
    plan_sha256 = "a" * 64
    receipt = f".axiom/path-migrations/{plan_sha256}.json"
    prior_manifest = ".axiom/encoding-manifests/us/statutes/26/9998.json"
    replacement_manifest = ".axiom/encoding-manifests/us/statutes/26/9999.json"
    dependent_manifest = (
        ".axiom/encoding-manifests/us/policies/income_tax/dependent.json"
    )
    _initialize_git_fixture(tmp_path)
    for relative in (old_module, old_companion, dependent, dependent_companion):
        _write_rulespec_fixture(tmp_path, relative)
    _write_changed_receipt(
        tmp_path,
        prior_manifest,
        {
            old_module: _sha256(tmp_path, old_module),
            old_companion: _sha256(tmp_path, old_companion),
        },
    )
    _write_changed_receipt(
        tmp_path,
        dependent_manifest,
        {
            dependent: _sha256(tmp_path, dependent),
            dependent_companion: _sha256(tmp_path, dependent_companion),
        },
    )
    _commit_fixture_paths(
        tmp_path,
        old_module,
        old_companion,
        dependent,
        dependent_companion,
        prior_manifest,
        dependent_manifest,
    )
    base_commit = git_commit_ref(tmp_path, "HEAD")
    assert base_commit is not None
    base_tree = git_tree_ref(tmp_path, base_commit)
    assert base_tree is not None
    old_module_sha256 = _sha256(tmp_path, old_module)
    old_companion_sha256 = _sha256(tmp_path, old_companion)
    old_dependent_sha256 = _sha256(tmp_path, dependent)
    dependent_companion_sha256 = _sha256(tmp_path, dependent_companion)
    prior_manifest_sha256 = _sha256(tmp_path, prior_manifest)
    dependent_manifest_sha256 = _sha256(tmp_path, dependent_manifest)
    prior_manifest_payload = json.loads((tmp_path / prior_manifest).read_text())
    dependent_manifest_payload = json.loads((tmp_path / dependent_manifest).read_text())
    subprocess.run(
        ["git", "-C", str(tmp_path), "mv", old_module, new_module], check=True
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "mv", old_companion, new_companion],
        check=True,
    )
    (tmp_path / dependent).write_text(
        "format: rulespec/v1\nrules: []\n# migrated reference rewrite\n"
    )
    (tmp_path / prior_manifest).unlink()
    receipt_file = tmp_path / receipt
    receipt_file.parent.mkdir(parents=True)
    receipt_file.write_text(
        json.dumps(
            {
                "schema_version": PATH_MIGRATION_RECEIPT_SCHEMA,
                "generated_at": "2026-08-30T00:00:00+00:00",
                "tool": PATH_MIGRATION_TOOL,
                "plan_sha256": plan_sha256,
                "plan": {
                    "schema_version": "axiom-encode/rulespec-path-migration-plan/v1",
                    "base_commit": base_commit,
                    "moves": [{"from": old_module, "to": new_module}],
                },
                "repository": {
                    "base_commit": base_commit,
                    "head_commit": base_commit,
                    "base_tree": base_tree,
                },
                "axiom_encode_version": "0.2.1690",
                "axiom_encode_git": _fake_encoder_git(),
                "validation_waiver_set_sha256": "3" * 64,
                "corpus_release": {
                    "name": "fixture",
                    "content_sha256": "7" * 64,
                    "selector_sha256": "8" * 64,
                },
                "moves": [
                    {
                        "from": old_module,
                        "to": new_module,
                        "from_sha256": old_module_sha256,
                        "to_sha256": _sha256(tmp_path, new_module),
                        "kind": "primary",
                    },
                    {
                        "from": old_companion,
                        "to": new_companion,
                        "from_sha256": old_companion_sha256,
                        "to_sha256": _sha256(tmp_path, new_companion),
                        "kind": "companion",
                    },
                ],
                "rewrites": [
                    {
                        "path": dependent,
                        "before_sha256": old_dependent_sha256,
                        "after_sha256": _sha256(tmp_path, dependent),
                        "replacements": [],
                    }
                ],
                "manifests": [
                    {
                        "prior_path": prior_manifest,
                        "prior_sha256": prior_manifest_sha256,
                        "replacement_path": replacement_manifest,
                    },
                    {
                        "prior_path": dependent_manifest,
                        "prior_sha256": dependent_manifest_sha256,
                        "replacement_path": dependent_manifest,
                    },
                ],
                "signature": _structural_signature(),
            }
        )
        + "\n"
    )
    replacement_file = tmp_path / replacement_manifest
    replacement_file.parent.mkdir(parents=True, exist_ok=True)
    replacement_file.write_text(
        json.dumps(
            {
                "schema_version": APPLIED_ENCODING_MANIFEST_SCHEMA,
                "generated_at": "2026-08-30T00:00:00+00:00",
                "tool": PATH_MIGRATION_TOOL,
                "axiom_encode_version": "0.2.1690",
                "axiom_encode_git": _fake_encoder_git(),
                "validation_waiver_set_sha256": "3" * 64,
                "applied_files": [
                    {"path": old_module, "deleted": True},
                    {
                        "path": new_module,
                        "sha256": _sha256(tmp_path, new_module),
                    },
                    {"path": old_companion, "deleted": True},
                    {
                        "path": new_companion,
                        "sha256": _sha256(tmp_path, new_companion),
                    },
                ],
                "migrated_manifest": prior_manifest_payload,
                "migration": {
                    "receipt_path": receipt,
                    "receipt_sha256": hashlib.sha256(
                        receipt_file.read_bytes()
                    ).hexdigest(),
                    "plan_sha256": plan_sha256,
                    "prior_manifest_path": prior_manifest,
                    "prior_manifest_sha256": prior_manifest_sha256,
                },
                "source_attestation": {},
                "signature": _structural_signature(),
            }
        )
        + "\n"
    )
    dependent_manifest_file = tmp_path / dependent_manifest
    dependent_manifest_file.parent.mkdir(parents=True, exist_ok=True)
    dependent_manifest_file.write_text(
        json.dumps(
            {
                "schema_version": APPLIED_ENCODING_MANIFEST_SCHEMA,
                "generated_at": "2026-08-30T00:00:00+00:00",
                "tool": PATH_MIGRATION_TOOL,
                "axiom_encode_version": "0.2.1690",
                "axiom_encode_git": _fake_encoder_git(),
                "validation_waiver_set_sha256": "3" * 64,
                "applied_files": [
                    {"path": dependent, "sha256": _sha256(tmp_path, dependent)},
                    {
                        "path": dependent_companion,
                        "sha256": dependent_companion_sha256,
                    },
                ],
                "migrated_manifest": dependent_manifest_payload,
                "migration": {
                    "receipt_path": receipt,
                    "receipt_sha256": hashlib.sha256(
                        receipt_file.read_bytes()
                    ).hexdigest(),
                    "plan_sha256": plan_sha256,
                    "prior_manifest_path": dependent_manifest,
                    "prior_manifest_sha256": dependent_manifest_sha256,
                },
                "source_attestation": {},
                "signature": _structural_signature(),
            }
        )
        + "\n"
    )
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)

    return receipt, replacement_manifest, dependent_manifest


def _refresh_migration_receipt_bindings(
    repo: Path,
    receipt: str,
    manifests: tuple[str, ...],
) -> None:
    receipt_sha256 = _sha256(repo, receipt)
    for manifest in manifests:
        manifest_file = repo / manifest
        payload = json.loads(manifest_file.read_text())
        payload["migration"]["receipt_sha256"] = receipt_sha256
        manifest_file.write_text(json.dumps(payload) + "\n")


def test_rename_passes_with_structurally_current_path_migration_receipts(
    tmp_path: Path,
) -> None:
    _write_path_migration_fixture(tmp_path)

    assert changed_rulespec_receipt_issues(tmp_path) == []


def test_committed_path_migration_receipts_satisfy_branch_preflight(
    tmp_path: Path,
) -> None:
    _write_path_migration_fixture(tmp_path)
    _commit_staged_fixture(tmp_path)

    assert changed_rulespec_receipt_issues(tmp_path) == []


def test_path_migration_receipt_must_bind_each_replacement_manifest(
    tmp_path: Path,
) -> None:
    receipt, replacement_manifest, dependent_manifest = _write_path_migration_fixture(
        tmp_path
    )
    receipt_file = tmp_path / receipt
    receipt_payload = json.loads(receipt_file.read_text())
    receipt_payload["manifests"][0]["replacement_path"] = (
        ".axiom/encoding-manifests/us/statutes/26/not-the-replacement.json"
    )
    receipt_file.write_text(json.dumps(receipt_payload) + "\n")
    receipt_sha256 = hashlib.sha256(receipt_file.read_bytes()).hexdigest()
    for manifest in (replacement_manifest, dependent_manifest):
        manifest_file = tmp_path / manifest
        manifest_payload = json.loads(manifest_file.read_text())
        manifest_payload["migration"]["receipt_sha256"] = receipt_sha256
        manifest_file.write_text(json.dumps(manifest_payload) + "\n")

    assert (
        f"{replacement_manifest} is not bound by its path-migration receipt"
        in changed_rulespec_receipt_issues(tmp_path)
    )


def test_path_migration_before_hash_must_match_exact_git_base_blob(
    tmp_path: Path,
) -> None:
    receipt, replacement_manifest, dependent_manifest = _write_path_migration_fixture(
        tmp_path
    )
    receipt_file = tmp_path / receipt
    receipt_payload = json.loads(receipt_file.read_text())
    old_path = receipt_payload["moves"][0]["from"]
    receipt_payload["moves"][0]["from_sha256"] = "f" * 64
    receipt_file.write_text(json.dumps(receipt_payload) + "\n")
    replacement_file = tmp_path / replacement_manifest
    replacement_payload = json.loads(replacement_file.read_text())
    replacement_payload["migrated_manifest"]["applied_files"][0]["sha256"] = (
        "f" * 64
    )
    replacement_file.write_text(json.dumps(replacement_payload) + "\n")
    _refresh_migration_receipt_bindings(
        tmp_path,
        receipt,
        (replacement_manifest, dependent_manifest),
    )

    assert any(
        issue.endswith(
            "path migration before sha256 does not match its exact Git "
            f"base blob: {old_path}"
        )
        for issue in changed_rulespec_receipt_issues(tmp_path)
    )


def test_path_migration_repository_metadata_is_exactly_git_bound(
    tmp_path: Path,
) -> None:
    for field in ("base_commit", "head_commit", "base_tree"):
        repo = tmp_path / field
        receipt, replacement_manifest, dependent_manifest = (
            _write_path_migration_fixture(repo)
        )
        receipt_file = repo / receipt
        receipt_payload = json.loads(receipt_file.read_text())
        receipt_payload["repository"][field] = "f" * 40
        receipt_file.write_text(json.dumps(receipt_payload) + "\n")
        _refresh_migration_receipt_bindings(
            repo,
            receipt,
            (replacement_manifest, dependent_manifest),
        )

        assert any(
            "path migration repository identity does not match its exact "
            "pre-operation commit and tree" in issue
            for issue in changed_rulespec_receipt_issues(repo)
        ), field


def test_path_migration_plan_base_is_exactly_git_bound(tmp_path: Path) -> None:
    receipt, replacement_manifest, dependent_manifest = _write_path_migration_fixture(
        tmp_path
    )
    receipt_file = tmp_path / receipt
    receipt_payload = json.loads(receipt_file.read_text())
    receipt_payload["plan"]["base_commit"] = "f" * 40
    receipt_file.write_text(json.dumps(receipt_payload) + "\n")
    _refresh_migration_receipt_bindings(
        tmp_path,
        receipt,
        (replacement_manifest, dependent_manifest),
    )

    assert any(
        "path migration plan does not bind its exact pre-operation commit" in issue
        for issue in changed_rulespec_receipt_issues(tmp_path)
    )


def test_path_migration_rejects_partial_companion_move(tmp_path: Path) -> None:
    receipt, replacement_manifest, dependent_manifest = _write_path_migration_fixture(
        tmp_path
    )
    receipt_payload = json.loads((tmp_path / receipt).read_text())
    companion_move = next(
        move for move in receipt_payload["moves"] if move["kind"] == "companion"
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "mv",
            companion_move["to"],
            companion_move["from"],
        ],
        check=True,
    )

    assert any(
        "path migration transaction is incomplete for move: "
        f"{companion_move['from']} -> {companion_move['to']}" in issue
        for issue in changed_rulespec_receipt_issues(tmp_path)
    )


def test_path_migration_rejects_omitted_signed_move(tmp_path: Path) -> None:
    receipt, replacement_manifest, dependent_manifest = _write_path_migration_fixture(
        tmp_path
    )
    receipt_file = tmp_path / receipt
    receipt_payload = json.loads(receipt_file.read_text())
    receipt_payload["moves"] = [
        move for move in receipt_payload["moves"] if move["kind"] != "companion"
    ]
    receipt_file.write_text(json.dumps(receipt_payload) + "\n")
    _refresh_migration_receipt_bindings(
        tmp_path,
        receipt,
        (replacement_manifest, dependent_manifest),
    )

    assert any(
        "applied files do not match its relevant path-migration moves" in issue
        for issue in changed_rulespec_receipt_issues(tmp_path)
    )


def test_path_migration_rejects_partial_dependent_rewrite(tmp_path: Path) -> None:
    receipt, replacement_manifest, dependent_manifest = _write_path_migration_fixture(
        tmp_path
    )
    receipt_payload = json.loads((tmp_path / receipt).read_text())
    dependent = receipt_payload["rewrites"][0]["path"]
    before = subprocess.check_output(
        ["git", "-C", str(tmp_path), "show", f"HEAD:{dependent}"],
    )
    (tmp_path / dependent).write_bytes(before)
    subprocess.run(["git", "-C", str(tmp_path), "add", dependent], check=True)

    assert any(
        f"path migration transaction is incomplete for rewrite: {dependent}" in issue
        for issue in changed_rulespec_receipt_issues(tmp_path)
    )


def test_path_migration_rejects_missing_dependent_replacement_manifest(
    tmp_path: Path,
) -> None:
    receipt, replacement_manifest, dependent_manifest = _write_path_migration_fixture(
        tmp_path
    )
    before = subprocess.check_output(
        ["git", "-C", str(tmp_path), "show", f"HEAD:{dependent_manifest}"],
    )
    (tmp_path / dependent_manifest).write_bytes(before)
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", dependent_manifest],
        check=True,
    )

    assert any(
        "path migration transaction is missing replacement manifest: "
        f"{dependent_manifest}" in issue
        for issue in changed_rulespec_receipt_issues(tmp_path)
    )


def test_changed_apply_receipt_must_match_current_hash(tmp_path: Path) -> None:
    module = "us/policies/income_tax/encoder_guard_fixture.yaml"
    manifest = (
        ".axiom/encoding-manifests/us/policies/income_tax/encoder_guard_fixture.json"
    )
    _initialize_git_fixture(tmp_path)
    _write_rulespec_fixture(tmp_path, module)
    _write_changed_receipt(tmp_path, manifest, {module: "f" * 64})

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{module} content does not match a same-change encoder apply receipt sha256"
    ]


def test_obsolete_v1_receipt_does_not_satisfy_preflight(tmp_path: Path) -> None:
    module = "us/policies/income_tax/encoder_guard_fixture.yaml"
    manifest = (
        ".axiom/encoding-manifests/us/policies/income_tax/encoder_guard_fixture.json"
    )
    _initialize_git_fixture(tmp_path)
    _write_rulespec_fixture(tmp_path, module)
    _write_changed_receipt(tmp_path, manifest, {module: _sha256(tmp_path, module)})
    payload = json.loads((tmp_path / manifest).read_text())
    payload["schema_version"] = "axiom-encode/applied-rulespec/v1"
    (tmp_path / manifest).write_text(json.dumps(payload) + "\n")

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{manifest} is not an encoder apply manifest",
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt",
    ]


def test_manifest_only_change_is_rejected(tmp_path: Path) -> None:
    manifest = ".axiom/encoding-manifests/us/statutes/26/9998.json"
    _initialize_git_fixture(tmp_path)
    _write_changed_receipt(tmp_path, manifest, {})

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{manifest} changed without any protected RuleSpec path; encoding "
        "manifests may be written only by the matching encoder operation"
    ]


def test_path_migration_receipt_only_change_is_rejected(tmp_path: Path) -> None:
    receipt = f".axiom/path-migrations/{'a' * 64}.json"
    _initialize_git_fixture(tmp_path)
    receipt_file = tmp_path / receipt
    receipt_file.parent.mkdir(parents=True)
    receipt_file.write_text("{}\n")

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{receipt} changed without any protected RuleSpec path; "
        "path-migration receipts may be written only by "
        "`axiom-encode migrate-rulespec-paths`"
    ]


def test_changed_receipt_must_identify_pinned_encoder(tmp_path: Path) -> None:
    module = "us/policies/income_tax/encoder_guard_fixture.yaml"
    manifest = (
        ".axiom/encoding-manifests/us/policies/income_tax/encoder_guard_fixture.json"
    )
    _initialize_git_fixture(tmp_path)
    _write_rulespec_fixture(tmp_path, module)
    _write_changed_receipt(tmp_path, manifest, {module: _sha256(tmp_path, module)})
    payload = json.loads((tmp_path / manifest).read_text())
    payload["axiom_encode_git"]["commit"] = "f" * 40
    (tmp_path / manifest).write_text(json.dumps(payload) + "\n")

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{manifest} does not identify the repository-pinned encoder",
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt",
    ]


def test_current_v5_receipt_in_legacy_nested_directory_is_rejected(
    tmp_path: Path,
) -> None:
    module = "us/policies/income_tax/encoder_guard_fixture.yaml"
    manifest = (
        "us/.axiom/encoding-manifests/policies/income_tax/encoder_guard_fixture.json"
    )
    _initialize_git_fixture(tmp_path)
    _write_rulespec_fixture(tmp_path, module)
    _write_changed_receipt(tmp_path, manifest, {module: _sha256(tmp_path, module)})

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{manifest} is not in the canonical root encoding-manifest directory",
        f"{module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt",
    ]


def test_apply_cannot_authorize_deletion_and_retire_cannot_authorize_live_file(
    tmp_path: Path,
) -> None:
    deleted_repo = tmp_path / "deleted"
    deleted_module = "us/statutes/26/9998.yaml"
    deleted_manifest = ".axiom/encoding-manifests/us/statutes/26/9998.json"
    _commit_rulespec_fixtures(deleted_repo, deleted_module)
    (deleted_repo / deleted_module).unlink()
    _write_changed_receipt(
        deleted_repo,
        deleted_manifest,
        {deleted_module: None},
    )

    assert changed_rulespec_receipt_issues(deleted_repo) == [
        f"{deleted_manifest} lists a deletion but is not an "
        "axiom-encode retire receipt",
        f"{deleted_module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt",
    ]

    live_repo = tmp_path / "live"
    live_module = "us/policies/income_tax/encoder_guard_fixture.yaml"
    live_manifest = (
        ".axiom/encoding-manifests/us/policies/income_tax/encoder_guard_fixture.json"
    )
    _initialize_git_fixture(live_repo)
    _write_rulespec_fixture(live_repo, live_module)
    live_hash = _sha256(live_repo, live_module)
    _write_changed_receipt(
        live_repo,
        live_manifest,
        {live_module: live_hash},
        retire=True,
        retired_hashes={live_module: live_hash},
    )

    assert changed_rulespec_receipt_issues(live_repo) == [
        f"{live_manifest} is not an exact retirement v5 receipt",
        f"{live_module} changed but is not listed in a same-change "
        "encoder apply/retire/migration receipt",
    ]


def test_unrelated_deleted_manifest_is_not_hidden_by_valid_apply_receipt(
    tmp_path: Path,
) -> None:
    old_module = "us/statutes/26/9997.yaml"
    old_manifest = ".axiom/encoding-manifests/us/statutes/26/9997.json"
    new_module = "us/policies/income_tax/encoder_guard_fixture.yaml"
    new_manifest = (
        ".axiom/encoding-manifests/us/policies/income_tax/encoder_guard_fixture.json"
    )
    _commit_rulespec_fixtures(tmp_path, old_module)
    _write_changed_receipt(
        tmp_path,
        old_manifest,
        {old_module: _sha256(tmp_path, old_module)},
    )
    _commit_fixture_paths(tmp_path, old_manifest)

    (tmp_path / old_manifest).unlink()
    _write_rulespec_fixture(tmp_path, new_module)
    _write_changed_receipt(
        tmp_path,
        new_manifest,
        {new_module: _sha256(tmp_path, new_module)},
    )

    assert changed_rulespec_receipt_issues(tmp_path) == [
        f"{old_manifest} was deleted without a changed path-migration replacement"
    ]
