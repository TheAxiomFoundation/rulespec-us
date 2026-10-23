#!/usr/bin/env python3
"""Migrate module.source_verification to the shape the pinned engine loads.

axiom-rules-engine (af6e4ea2 and later) rejects any `corpus_citation_paths`
key and accepts only `corpus_citation_path`, `source_sha256` and
`upstream_source_check` inside `module.source_verification`
(`SourceVerification` is `deny_unknown_fields`). Issue #1354: 381 modules still
carried the removed plural list, and 18 carried `source_verification.values`.

This codemod rewrites each such module, and only its `module` block:

- `source_verification.corpus_citation_path` keeps exactly one path. An
  existing singular wins. Otherwise, the plural entry that names the module's
  own provision is used (the encoder derives a module's file path from that
  citation, and the engine stamps it onto every rule as the origin citation).
  Failing that, the first plural entry, the historical primary, is used.
- Every plural entry, in order and including the one kept as the singular,
  moves to `module.source_documents` as its own
  `{corpus_citation_path: ...}` node. Nothing is dropped, so the provision ->
  rules reverse index keeps every edge. This is the convention of
  rulespec-us#1363.
- `source_verification.values` moves unchanged to `module.source_values`,
  which is also the #1363 convention.

The edit is textual so every other byte, including comments and quoting,
survives. After each rewrite the result is re-parsed and must equal the
original document with exactly those moves applied; any other difference
aborts. Running the codemod twice is a no-op.

Usage:
  python tools/migrate_source_verification.py --check   # list modules to migrate
  python tools/migrate_source_verification.py --apply   # rewrite them in place
"""

from __future__ import annotations

import argparse
import copy
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

try:
    _Loader = yaml.CSafeLoader
except AttributeError:  # pragma: no cover - PyYAML without libyaml
    _Loader = yaml.SafeLoader

REPO_ROOT = Path(__file__).resolve().parent.parent
PLURAL = "corpus_citation_paths"
SINGULAR = "corpus_citation_path"
VALUES = "values"
DOCUMENTS = "source_documents"
SOURCE_VALUES = "source_values"
ENGINE_SOURCE_VERIFICATION_FIELDS = frozenset(
    {SINGULAR, "source_sha256", "upstream_source_check"}
)

# For each content root, the corpus document classes axiom-encode files there
# (the inverse of its _RULESPEC_OUTPUT_ROOT_BY_SOURCE_TOKEN). `legislation/`
# and the legacy `manual/` tree keep their own names.
_CITATION_CLASSES = {
    "statutes": ("statute", "statutes"),
    "regulations": ("regulation", "regulations"),
    "policies": ("form", "forms", "guidance", "manual", "manuals", "policies", "policy"),
    "legislation": ("legislation",),
    "manual": ("manual",),
}
_KEY_LINE = re.compile(r"^(?P<indent> *)(?P<key>[A-Za-z_][A-Za-z0-9_]*):(?P<rest>.*)$")
_ITEM_LINE = re.compile(r"^(?P<indent> *)- (?P<value>\S.*?)\s*$")


class MigrationError(ValueError):
    """The module cannot be migrated safely; nothing is written."""


def is_jurisdiction_dir(name: str) -> bool:
    return re.fullmatch(r"[a-z]{2}(?:-[a-z0-9]+)*", name) is not None


def tracked_modules(root: Path) -> list[str]:
    listing = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"], check=True, capture_output=True
    ).stdout.decode("utf-8")
    return sorted(
        path
        for path in listing.split("\0")
        if path
        and path.endswith(".yaml")
        and not path.endswith(".test.yaml")
        and "/" in path
        and is_jurisdiction_dir(path.split("/", 1)[0])
    )


def own_citation_candidates(module_path: str) -> set[str]:
    """Citations whose encoder-derived file path could be `module_path`.

    Inverts the cases of axiom-encode's
    `_source_identifier_to_relative_rulespec_path` that occur here:
    `<j>/<class>/<rest>` maps to `<j>/<root>/<rest>.yaml` for each class the
    encoder files under that root, a dotted leaf maps to a nested directory, and
    a US regulation title `N` maps to `N-cfr`.
    """
    parts = module_path.removesuffix(".yaml").split("/")
    if len(parts) < 3 or parts[1] not in _CITATION_CLASSES:
        return set()
    jurisdiction, root, rest = parts[0], parts[1], parts[2:]
    variants = [rest]
    if jurisdiction == "us" and root == "regulations" and re.fullmatch(r"\d+-cfr", rest[0]):
        variants.append([rest[0].removesuffix("-cfr"), *rest[1:]])
    candidates = set()
    for document_class in _CITATION_CLASSES[root]:
        for tail in variants:
            candidates.add("/".join([jurisdiction, document_class, *tail]))
            if len(tail) >= 2:
                dotted = [*tail[:-2], f"{tail[-2]}.{tail[-1]}"]
                candidates.add("/".join([jurisdiction, document_class, *dotted]))
    return candidates


def choose_singular(module_path: str, singular: str | None, plural: list[str]) -> str:
    if singular:
        return singular
    own = [path for path in plural if path in own_citation_candidates(module_path)]
    if len(own) == 1:
        return own[0]
    return plural[0]


def needs_migration(payload: Any) -> bool:
    verification = _source_verification(payload)
    return isinstance(verification, dict) and (PLURAL in verification or VALUES in verification)


def _source_verification(payload: Any) -> Any:
    if not isinstance(payload, dict) or not isinstance(payload.get("module"), dict):
        return None
    return payload["module"].get("source_verification")


def expected_payload(payload: dict[str, Any], module_path: str) -> dict[str, Any]:
    """The migration's semantic specification, applied to a parsed module."""
    result = copy.deepcopy(payload)
    module = result["module"]
    verification = module["source_verification"]
    plural = verification.pop(PLURAL, None)
    values = verification.pop(VALUES, None)
    if plural is not None:
        verification[SINGULAR] = choose_singular(module_path, verification.get(SINGULAR), plural)
        module[DOCUMENTS] = [{SINGULAR: path} for path in plural]
    if values is not None:
        module[SOURCE_VALUES] = values
    return result


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_blank_or_comment(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def _block_end(lines: list[str], start: int, indent: int) -> int:
    """Index after the block that `lines[start]` (a key at `indent`) opens."""
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if not _is_blank_or_comment(line) and _indent(line) <= indent:
            break
        end += 1
    while end > start + 1 and _is_blank_or_comment(lines[end - 1]):
        end -= 1
    return end


def _child_key_line(lines: list[str], start: int, end: int, key: str) -> int | None:
    """Line of `key` as a direct child of the mapping spanning (start, end)."""
    child_indent = None
    for index in range(start + 1, end):
        line = lines[index]
        if _is_blank_or_comment(line):
            continue
        if child_indent is None:
            child_indent = _indent(line)
        if _indent(line) != child_indent:
            continue
        match = _KEY_LINE.match(line)
        if match and match.group("key") == key:
            return index
    return None


@dataclass
class _Entry:
    key: str
    start: int
    end: int


def _entries(lines: list[str], start: int, end: int, indent: int) -> list[_Entry]:
    """Direct children of the mapping at (start, end), each with its line span."""
    entries: list[_Entry] = []
    for index in range(start + 1, end):
        line = lines[index]
        if _is_blank_or_comment(line):
            continue
        if _indent(line) < indent:
            raise MigrationError(f"line {index + 1} is outdented inside source_verification")
        if _indent(line) == indent:
            match = _KEY_LINE.match(line)
            if match:
                if entries:
                    entries[-1].end = index
                entries.append(_Entry(match.group("key"), index, end))
            elif not line.lstrip().startswith("- "):
                raise MigrationError(f"line {index + 1} is not a mapping key: {line!r}")
    if not entries or entries[0].start != _first_content(lines, start + 1, end):
        raise MigrationError("source_verification does not start with a key")
    return entries


def _first_content(lines: list[str], start: int, end: int) -> int:
    for index in range(start, end):
        if not _is_blank_or_comment(lines[index]):
            return index
    return end


def _plural_items(lines: list[str], entry: _Entry) -> tuple[list[str], int]:
    """Raw scalar text of each plural item, and the items' indentation."""
    header = _KEY_LINE.match(lines[entry.start])
    if header.group("rest").strip():
        raise MigrationError(f"{PLURAL} is not a block sequence")
    items: list[str] = []
    item_indent = None
    for index in range(entry.start + 1, entry.end):
        line = lines[index]
        if _is_blank_or_comment(line):
            if line.strip():
                raise MigrationError(f"comment inside {PLURAL} at line {index + 1}")
            continue
        match = _ITEM_LINE.match(line)
        if not match:
            raise MigrationError(f"{PLURAL} item at line {index + 1} is not a one-line scalar")
        if item_indent is None:
            item_indent = len(match.group("indent"))
        elif len(match.group("indent")) != item_indent:
            raise MigrationError(f"{PLURAL} items are not aligned at line {index + 1}")
        items.append(match.group("value"))
    if not items:
        raise MigrationError(f"{PLURAL} is empty")
    return items, item_indent


def migrate_text(text: str, module_path: str) -> str | None:
    """Return the migrated text, or None when the module needs no migration."""
    payload = yaml.load(text, Loader=_Loader)
    if not needs_migration(payload):
        return None
    module = payload["module"]
    for key in (DOCUMENTS, SOURCE_VALUES):
        if key in module:
            raise MigrationError(f"module already declares {key}")

    lines = text.splitlines(keepends=True)
    module_line = next(
        (index for index, line in enumerate(lines) if re.match(r"^module:\s*$", line)), None
    )
    if module_line is None:
        raise MigrationError("no block-style top-level module: key")
    module_end = _block_end(lines, module_line, 0)
    sv_line = _child_key_line(lines, module_line, module_end, "source_verification")
    if sv_line is None:
        raise MigrationError("no block-style module.source_verification")
    module_indent = _indent(lines[sv_line])
    if _KEY_LINE.match(lines[sv_line]).group("rest").strip():
        raise MigrationError("module.source_verification is not a block mapping")
    sv_end = _block_end(lines, sv_line, module_indent)
    entry_indent = _indent(lines[_first_content(lines, sv_line + 1, sv_end)])
    entries = _entries(lines, sv_line, sv_end, entry_indent)
    by_key = {entry.key: entry for entry in entries}
    if len(by_key) != len(entries):
        raise MigrationError("source_verification repeats a key")

    verification = module["source_verification"]
    plural_entry = by_key.get(PLURAL)
    documents: list[str] = []
    new_verification: list[str] = []
    if plural_entry is not None:
        raw_items, item_indent = _plural_items(lines, plural_entry)
        parsed_items = [yaml.load(item, Loader=_Loader) for item in raw_items]
        if parsed_items != verification[PLURAL]:
            raise MigrationError(f"{PLURAL} items do not round-trip")
        chosen = choose_singular(module_path, verification.get(SINGULAR), verification[PLURAL])
        raw_chosen = raw_items[verification[PLURAL].index(chosen)]
        # Match the file's own list style: items flush with the key (PyYAML's
        # default) or indented under it.
        document_indent = module_indent + (item_indent - entry_indent)
        documents = [" " * module_indent + f"{DOCUMENTS}:\n"] + [
            " " * document_indent + f"- {SINGULAR}: {raw}\n" for raw in raw_items
        ]
    values_block: list[str] = []
    for entry in entries:
        if entry.key == PLURAL:
            if SINGULAR not in by_key:
                new_verification.append(" " * entry_indent + f"{SINGULAR}: {raw_chosen}\n")
            continue
        block = lines[entry.start : entry.end]
        if entry.key == VALUES:
            shift = entry_indent - module_indent
            for line in block:
                if line.strip() and _indent(line) < entry_indent:
                    raise MigrationError("values block is outdented")
            values_block = [
                (line[shift:] if line.strip() else line) for line in block
            ]
            values_block[0] = values_block[0].replace(f"{VALUES}:", f"{SOURCE_VALUES}:", 1)
            continue
        new_verification.extend(block)

    rewritten = (
        lines[:sv_line]
        + documents
        + [lines[sv_line]]
        + new_verification
        + values_block
        + lines[sv_end:]
    )
    migrated = "".join(rewritten)
    if yaml.load(migrated, Loader=_Loader) != expected_payload(payload, module_path):
        raise MigrationError("rewritten module does not match the migration specification")
    if migrated.splitlines(keepends=True)[:module_line] != lines[:module_line]:
        raise MigrationError("rewrite touched lines before the module block")
    tail = len(lines) - module_end
    if tail and migrated.splitlines(keepends=True)[-tail:] != lines[-tail:]:
        raise MigrationError("rewrite touched lines after the module block")
    return migrated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="list modules that need migration")
    mode.add_argument("--apply", action="store_true", help="rewrite them in place")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    pending: list[tuple[str, str]] = []
    failures: list[str] = []
    for module_path in tracked_modules(args.root):
        path = args.root / module_path
        text = path.read_text(encoding="utf-8")
        if PLURAL not in text and "source_verification" not in text:
            continue
        try:
            migrated = migrate_text(text, module_path)
        except MigrationError as error:
            failures.append(f"{module_path}: {error}")
            continue
        if migrated is not None:
            pending.append((module_path, migrated))
    if failures:
        print("Cannot migrate safely:\n  " + "\n  ".join(failures))
        return 1
    if args.check:
        for module_path, _ in pending:
            print(module_path)
        print(f"{len(pending)} module(s) need migration")
        return 1 if pending else 0
    for module_path, migrated in pending:
        (args.root / module_path).write_text(migrated, encoding="utf-8")
    print(f"migrated {len(pending)} module(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
