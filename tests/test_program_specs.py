"""Program specs under jurisdiction programs/ roots must be valid and every
scope entry must resolve to a module in this repository.

Monorepo-native port of axiom-programs' validate_specs.py: jurisdiction
content lives beside programs/, so the audit needs no external
checkouts. Known gaps are ratcheted through known-dangling.yaml — a
dangling entry not listed there fails, and a listed entry that starts
resolving also fails (remove it once fixed; see axiom-programs#14).
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
def scope_prefix(program: str, scope_name: str) -> str:
    normalized = scope_name.strip()
    if normalized == "federal":
        return "us"
    if normalized == "state":
        return program.split("/", 1)[0]
    return normalized


def spec_paths() -> list[Path]:
    return sorted(ROOT.glob("us*/programs/*/*.yaml"))


def load_allowlist() -> set[tuple[str, str, str]]:
    path = ROOT / "known-dangling.yaml"
    if not path.exists():
        return set()
    payload = yaml.safe_load(path.read_text()) or {}
    return {
        (entry["spec"], entry["scope"], entry["path"])
        for entry in payload.get("entries", [])
    }


def test_program_specs_exist() -> None:
    assert spec_paths(), "jurisdiction programs/ roots contain no specs"


def test_program_specs_are_structurally_valid() -> None:
    problems: list[str] = []
    for spec_path in spec_paths():
        rel = spec_path.relative_to(ROOT).as_posix()
        raw = yaml.safe_load(spec_path.read_text()) or {}
        if not isinstance(raw, dict):
            problems.append(f"{rel}: spec root must be a mapping")
            continue
        if not isinstance(raw.get("program"), str) or not raw.get("program"):
            problems.append(f"{rel}: missing or non-string `program`")
        if "period" not in raw:
            problems.append(f"{rel}: missing `period`")
        outputs = raw.get("outputs")
        if (
            not isinstance(outputs, list)
            or not outputs
            or not all(isinstance(item, str) for item in outputs)
        ):
            problems.append(f"{rel}: `outputs` must be a non-empty list of strings")
        scope = raw.get("scope")
        if scope is not None and not isinstance(scope, dict):
            problems.append(f"{rel}: `scope` must be a mapping")
    assert problems == []


def test_scope_entries_resolve_or_are_allowlisted() -> None:
    allowlist = load_allowlist()
    seen: set[tuple[str, str, str]] = set()
    problems: list[str] = []

    for spec_path in spec_paths():
        rel = spec_path.relative_to(ROOT).as_posix()
        raw = yaml.safe_load(spec_path.read_text()) or {}
        if not isinstance(raw, dict) or not isinstance(raw.get("program"), str):
            continue
        for scope_name, paths in (raw.get("scope") or {}).items():
            prefix = scope_prefix(raw["program"], scope_name)
            jurisdiction = ROOT / prefix
            if not jurisdiction.is_dir():
                problems.append(f"{rel}: no jurisdiction directory {prefix}/")
                continue
            for path in paths or []:
                key = (rel, scope_name, path)
                resolves = (jurisdiction / f"{path}.yaml").exists()
                if not resolves and key not in allowlist:
                    problems.append(
                        f"{rel}: {scope_name}: {path} does not resolve in {prefix}/"
                    )
                if resolves and key in allowlist:
                    problems.append(
                        f"{rel}: {scope_name}: {path} now resolves — remove it "
                        "from known-dangling.yaml"
                    )
                if key in allowlist:
                    seen.add(key)

    problems.extend(
        f"known-dangling.yaml entry matches no spec scope entry (stale): {stale}"
        for stale in sorted(allowlist - seen)
    )
    assert problems == []
