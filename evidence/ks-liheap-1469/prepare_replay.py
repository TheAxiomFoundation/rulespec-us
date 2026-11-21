"""Prepare a new local diagnostic replay; never sign, apply, or publish rules.

The historical exports are immutable evidence. This script verifies the exact
PR source pairs, recompiles the income source using an existing pinned engine,
and writes fresh local paths/hashes to a new directory outside the checkout.
It does not convert a rejected draft into an accepted encoding.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys


ENGINE_COMMIT = "89571cc2a938707fd60a5489b951135345697296"
INCOME_PATH = "us-ks/policies/dcf/keesm/2026-01-01/keesm13360.yaml"
BUNDLE = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def require_hash(path: Path, expected: str) -> None:
    if not path.is_file() or digest(path) != expected:
        raise ValueError(f"Missing or changed evidence: {path}")


def expand(value: object, values: dict[str, str]) -> object:
    if isinstance(value, dict):
        return {key: expand(item, values) for key, item in value.items()}
    if isinstance(value, list):
        return [expand(item, values) for item in value]
    if isinstance(value, str):
        for key, replacement in values.items():
            value = value.replace("${" + key + "}", replacement)
        if "${" in value:
            raise ValueError(f"Unresolved replay token: {value}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rulespec-root", type=Path, required=True)
    parser.add_argument("--engine-root", type=Path, required=True)
    parser.add_argument("--oracles-root", type=Path, required=True)
    parser.add_argument("--release-object", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.rulespec_root.resolve(strict=True)
    engine = args.engine_root.resolve(strict=True)
    oracles = args.oracles_root.resolve(strict=True)
    release_path = args.release_object.resolve(strict=True)
    output = args.output.resolve()
    if root.name != "rulespec-us":
        raise ValueError("The canonical policy checkout must be named rulespec-us")
    if output.exists() or output.is_relative_to(root):
        raise ValueError("Output must be a fresh directory outside the policy checkout")

    manifest = json.loads((BUNDLE / "manifest.json").read_text())
    for item in manifest["files"]:
        require_hash(BUNDLE / item["path"], item["sha256"])
    provenance = json.loads((BUNDLE / "provenance.json").read_text())
    for item in provenance["sources"]:
        require_hash(root / item["path"], item["sha256"])
    for item in provenance["oracles"]["patch_files"]:
        require_hash(oracles / item["path"], item["sha256"])
    oracle_commit = subprocess.check_output(
        ["git", "-C", str(oracles), "rev-parse", "HEAD"], text=True
    ).strip()
    if oracle_commit != provenance["oracles"]["base_commit"]:
        raise ValueError("Oracle checkout does not match the archived patch's base")
    if subprocess.run(
        ["git", "-C", str(oracles), "diff", "--quiet", "HEAD", "--"], check=False
    ).returncode:
        raise ValueError("Oracle checkout has tracked changes beyond the archived new files")

    actual_commit = subprocess.check_output(
        ["git", "-C", str(engine), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual_commit != ENGINE_COMMIT:
        raise ValueError("Engine checkout does not match the recorded commit")
    if subprocess.run(
        ["git", "-C", str(engine), "diff", "--quiet", "HEAD", "--"], check=False
    ).returncode:
        raise ValueError("Engine checkout has tracked changes")
    binary = engine / "target/release/axiom-rules-engine"
    build_receipt_path = binary.with_name(binary.name + ".provenance.json")
    build_receipt = json.loads(build_receipt_path.read_text())
    if (
        build_receipt.get("commit") != ENGINE_COMMIT
        or build_receipt.get("working_tree") != "clean"
        or build_receipt.get("repository") != "TheAxiomFoundation/axiom-rules-engine"
    ):
        raise ValueError("A verified build receipt for the pinned engine is required")
    require_hash(binary, build_receipt["binary_sha256"])

    release = json.loads(release_path.read_text())
    corpus = provenance["corpus"]
    require_hash(release_path, corpus["release_object_sha256"])
    content_hash = hashlib.sha256(
        json.dumps(
            release["content"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode()
    ).hexdigest()
    if (
        release["release"] != corpus["release"]
        or release["content_sha256"] != corpus["content_sha256"]
        or content_hash != corpus["content_sha256"]
    ):
        raise ValueError("Supplied release has a different content identity")

    output.mkdir(parents=True)
    artifact = output / "compiled.json"
    command = [
        str(binary), "compile", "--program", str(root / INCOME_PATH),
        "--rulespec-root", str(root), "--output", str(artifact),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    (output / "compile.stdout.txt").write_text(result.stdout)
    (output / "compile.stderr.txt").write_text(result.stderr)
    if result.returncode:
        raise RuntimeError(f"Compilation failed; inspect {output / 'compile.stderr.txt'}")
    # Refuse a concurrent edit rather than blessing bytes different from the PR.
    for item in provenance["sources"]:
        require_hash(root / item["path"], item["sha256"])
    require_hash(binary, build_receipt["binary_sha256"])

    source_hash = digest(root / INCOME_PATH)
    compilation = {
        "kind": "new_local_diagnostic_replay_compilation",
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "compile_command": command,
        "compile_exit_code": 0,
        "candidate_root": str(root),
        "compiled_artifact": str(artifact),
        "compiled_artifact_sha256": digest(artifact),
        "source_sha256": source_hash,
        "copied_source_sha256": source_hash,
        "test_sha256": digest((root / INCOME_PATH).with_suffix(".test.yaml")),
        "engine_git_commit": ENGINE_COMMIT,
        "engine_binary_sha256": digest(binary),
        "encoder_acceptance_status": "not_accepted_ci_rejected",
        "note": "Fresh compilation only. Historical rejection stands; no signing or admission.",
    }
    compilation_path = output / "compilation-receipt.json"
    write_json(compilation_path, compilation)
    acceptance = json.loads((BUNDLE / "historical-income-acceptance.json").read_text())
    acceptance.update({
        "kind": "relocated_historical_rejection_for_local_replay",
        "issues_path": str(BUNDLE / "income-ci-issues.json"),
        "issues_sha256": digest(BUNDLE / "income-ci-issues.json"),
        "note": "Historical CI rejection of this source, not a new acceptance decision. PR companion is the final generated 17-case file; original oracle snapshot companion had 16 cases.",
    })
    acceptance_path = output / "final-acceptance.json"
    write_json(acceptance_path, acceptance)
    values = {
        "RULESPEC_ROOT": str(root), "ENGINE_ROOT": str(engine),
        "REPLAY_OUTPUT": str(output), "CORPUS_RELEASE_OBJECT": str(release_path),
        "COMPILED_SHA256": digest(artifact),
        "COMPILATION_RECEIPT_SHA256": digest(compilation_path),
        "FINAL_ACCEPTANCE_SHA256": digest(acceptance_path),
    }
    template = json.loads((BUNDLE / "oracle-binding.template.json").read_text())
    binding_path = output / "candidate-binding.json"
    write_json(binding_path, expand(template, values))
    print("Prepared a new local replay of the unaccepted income draft.")
    print("The exact historically verified release bytes and content identity were checked.")
    print("This diagnostic replay does not perform new signature admission or production signing.")
    print("Run from " + str(oracles) + ":")
    print(" ".join(map(shlex.quote, [
        sys.executable, "-m", "axiom_oracles.bridges.ks_liheap",
        "--candidate-binding", str(binding_path),
        "--report", str(output / "comparison.json"),
    ])))
    print("Expected exit 2: 199 comparisons, 10 differences, 417 unsupported slots; no execution errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
