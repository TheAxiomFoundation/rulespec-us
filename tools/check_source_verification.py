"""Reject incompatible provenance metadata in changed encodings; never rewrite it."""
import argparse
from pathlib import Path
import sys
import yaml


def issues(value, path=""):
    found = []
    if isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(issues(child, f"{path}[{index}]"))
    elif isinstance(value, dict):
        if path == "module" and "source_claims" in value:
            found.append("module.source_claims: unsupported; use direct corpus citations in proof source atoms")
        if ".proof.atoms[" in path and "claim" in value:
            found.append(f"{path}.claim: unsupported; retain direct proof source evidence")
        if "corpus_citation_paths" in value:
            found.append(f"{path}: plural corpus_citation_paths is unsupported; preserve each citation in a separate source record")
        if "source_verification" in value:
            source = value["source_verification"]
            location = f"{path}.source_verification"
            if not isinstance(source, dict):
                found.append(f"{location}: expected mapping")
            else:
                if not isinstance(source.get("corpus_citation_path"), str) or not source["corpus_citation_path"].strip():
                    found.append(f"{location}: requires a singular corpus_citation_path")
                for key in source.keys() - {"corpus_citation_path", "source_sha256", "upstream_source_check"}:
                    found.append(f"{location}.{key}: unsupported field; keep supplemental metadata outside source_verification")
        for key, child in value.items():
            found.extend(issues(child, f"{path}.{key}" if path else str(key)))
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths-file", help="NUL-separated list of changed paths")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    paths = args.paths
    if args.paths_file:
        paths += [p for p in Path(args.paths_file).read_text().split("\0") if p]
    failures = []
    for name in paths:
        path = Path(name)
        if not path.is_file() or path.suffix not in {".yaml", ".yml"} or ".test." in path.name:
            continue
        try:
            document = yaml.safe_load(path.read_text())
            if not isinstance(document, dict) or document.get("format") != "rulespec/v1":
                continue
            failures.extend(f"{name}: {message}" for message in issues(document))
        except yaml.YAMLError as error:
            failures.append(f"{name}: invalid YAML: {error}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
