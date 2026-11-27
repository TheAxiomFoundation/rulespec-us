"""Every tracked module's source metadata has the shape the pinned engine loads.

axiom-rules-engine rejects any `corpus_citation_paths` key anywhere in a
module, and `module.source_verification` is `deny_unknown_fields` over
`corpus_citation_path` (required), `source_sha256` and `upstream_source_check`
(#1354). Additional citations live in `module.source_documents`, one
`corpus_citation_path` per node, and supplemental source values in
`module.source_values`. This test enforces that shape in the required pytest
leg, without an engine build, over every YAML module under a jurisdiction
directory, including trees CI validation does not select.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Iterator

import yaml

try:
    _Loader = yaml.CSafeLoader
except AttributeError:  # pragma: no cover - PyYAML without libyaml
    _Loader = yaml.SafeLoader

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_FIELDS = {"corpus_citation_path", "source_sha256", "upstream_source_check"}


def _modules() -> Iterator[tuple[str, Any]]:
    listing = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"], check=True, capture_output=True
    ).stdout.decode("utf-8")
    for path in sorted(p for p in listing.split("\0") if p):
        head = path.split("/", 1)[0]
        if not (path.endswith(".yaml") and head[:2].isalpha() and head[:2].islower()):
            continue
        if len(head.split("-")[0]) != 2 or path.endswith(".test.yaml"):
            continue
        text = (REPO_ROOT / path).read_text(encoding="utf-8")
        if "corpus_citation" not in text and "source_verification" not in text:
            continue
        yield path, yaml.load(text, Loader=_Loader)


def _plural_locations(value: Any, location: str = "") -> Iterator[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "corpus_citation_paths":
                yield f"{location}/{key}"
            yield from _plural_locations(nested, f"{location}/{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _plural_locations(nested, f"{location}[{index}]")


def test_module_source_metadata_has_the_engine_shape():
    problems: list[str] = []
    checked = 0
    for path, payload in _modules():
        checked += 1
        problems += [f"{path}: removed plural at {where}" for where in _plural_locations(payload)]
        module = payload.get("module") if isinstance(payload, dict) else None
        if not isinstance(module, dict):
            continue
        verification = module.get("source_verification")
        if verification is not None:
            if not isinstance(verification, dict):
                problems.append(f"{path}: source_verification is not a mapping")
                continue
            extra = sorted(set(verification) - ENGINE_FIELDS)
            if extra:
                problems.append(f"{path}: source_verification declares {extra}")
            singular = verification.get("corpus_citation_path")
            if not isinstance(singular, str) or not singular.strip():
                problems.append(f"{path}: source_verification has no corpus_citation_path")
        documents = module.get("source_documents")
        if documents is not None:
            if not isinstance(documents, list) or not documents:
                problems.append(f"{path}: source_documents is not a non-empty list")
                continue
            for index, document in enumerate(documents):
                if not (
                    isinstance(document, dict)
                    and set(document) == {"corpus_citation_path"}
                    and isinstance(document["corpus_citation_path"], str)
                ):
                    problems.append(
                        f"{path}: source_documents[{index}] must be one corpus_citation_path"
                    )
    assert checked > 4000, f"only {checked} modules scanned"
    assert not problems, "\n".join(problems[:40])
