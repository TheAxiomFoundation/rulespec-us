"""Report RuleSpec source-hash drift against the pinned signed corpus release.

Report-only companion to ``.github/workflows/source-staleness.yml``. The
workflow installs the axiom-encode commit pinned as
``source_staleness_axiom_encode_ref`` in ``.axiom/workflow-toolchain.toml``,
fetches the signed release object pinned in ``.axiom/toolchain.toml``, and
checks out that release's provisions artifacts at the release's provenance
commit. This script then:

1. scans every jurisdiction root for modules and their
   ``module.source_verification`` blocks;
2. binds the checkout to the pinned release through the encoder's own
   ``load_rulespec_local_corpus_release``, with a verification-only corpus
   release public key (the unsupervised path ``axiom-encode ci`` uses; it
   conveys no signing capability);
3. recomputes each ``source_sha256`` pin with the encoder's
   ``resolved_source_verification_block``, the function that stamps pins, so
   a pin matches exactly when the encoder would stamp the same digest today;
4. runs the encoder's ``check-source-staleness`` entry point once per
   jurisdiction root and records its fail-closed verdict;
5. for every root whose encoder scan completed, checks that the encoder's
   verdict and step 3 agree on every pin (a differential check).

The encoder resolves only bytes listed in the signed release and hash-checks
each provisions file against the release inventory, so drift is measured
against the release pinned in ``.axiom/toolchain.toml``, not corpus main.

Exit status: 0 when every pin matches and every encoder verdict is clean,
1 when the report lists findings, 2 when the report could not be produced.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence

import yaml

try:
    from yaml import CSafeLoader as _SafeLoader
except ImportError:  # pragma: no cover - PyYAML without libyaml
    from yaml import SafeLoader as _SafeLoader


SHA256_RE = re.compile(r"[0-9a-f]{64}")
# The encoder's _IGNORED_RULESPEC_SCAN_NAMES at the pinned ref, so both scans
# see the same files and the differential cannot disagree over a skipped one.
IGNORED_DIR_NAMES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".nox",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "_axiom",
        "__pycache__",
        "node_modules",
        "venv",
    }
)
# The encoder skips a jurisdiction's ProgramSpec root (RULESPEC_COMPOSITION_SPEC_ROOT).
COMPOSITION_SPEC_ROOT = "programs"
TEST_SUFFIXES = (".test.yaml", ".test.yml")
YAML_SUFFIXES = (".yaml", ".yml")
PIN_STATUSES = ("match", "stale", "unresolved", "invalid")
EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_HARNESS_ERROR = 2
MAX_LISTED_ROWS = 200
# The encoder admits a scan root only after `git rev-parse` and
# `git remote get-url` probes with a 2-second timeout. On a loaded host the
# probe times out and the encoder refuses the root with this message; the
# root itself is fine, so the run is retried a bounded number of times.
TRANSIENT_ROOT_REFUSAL = "RuleSpec scan root must be an exact canonical"
ENCODER_ATTEMPTS = 3


@dataclass(frozen=True)
class Pin:
    """One module that declares ``module.source_verification.source_sha256``."""

    path: str
    citation_path: str | None
    pinned_sha: object
    has_plural_citation_field: bool = False


@dataclass
class ScanResult:
    yaml_files: int = 0
    modules: int = 0
    grounded: int = 0
    unpinned: int = 0
    pins: list[Pin] = field(default_factory=list)
    unreadable: list[tuple[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class PinResult:
    path: str
    citation_path: str | None
    status: str
    pinned_sha: str
    current_sha: str | None = None
    detail: str | None = None


@dataclass(frozen=True)
class EncoderVerdict:
    jurisdiction: str
    exit_status: int
    output: str
    attempts: int = 1

    @property
    def headline(self) -> str:
        """First line naming what the encoder concluded or refused."""
        lines = [line for line in self.output.splitlines() if line.strip()]
        for index, line in enumerate(lines):
            if line.startswith("ERROR"):
                follow = lines[index + 1].strip() if index + 1 < len(lines) else ""
                return f"{line} | {follow}" if follow else line
        return lines[-1] if lines else "(no output)"


def jurisdiction_roots(repo_root: Path) -> list[Path]:
    """Return ``rulespec-<country>/<country>[-<part>...]`` roots, lexically.

    The encoder's own identity check shells out to git with a short timeout, so
    discovery uses the directory-name rule alone and never drops a root.
    """
    country = repo_root.name.removeprefix("rulespec-")
    if country == repo_root.name or not re.fullmatch(r"[a-z]{2}", country):
        raise ValueError(f"not a rulespec-<country> checkout: {repo_root}")
    pattern = re.compile(rf"{country}(?:-[a-z0-9]+)*")
    return sorted(
        child
        for child in repo_root.iterdir()
        if child.is_dir() and not child.is_symlink() and pattern.fullmatch(child.name)
    )


def iter_module_files(jurisdiction_root: Path) -> Iterable[Path]:
    """Yield candidate module YAML files in a stable order, skipping tests."""
    for path in sorted(jurisdiction_root.rglob("*")):
        relative = path.relative_to(jurisdiction_root)
        if any(part in IGNORED_DIR_NAMES for part in relative.parts):
            continue
        if relative.parts[0] == COMPOSITION_SPEC_ROOT:
            continue
        if not path.is_file() or path.is_symlink():
            continue
        name = path.name
        if not name.endswith(YAML_SUFFIXES) or name.endswith(TEST_SUFFIXES):
            continue
        yield path


def scan_modules(repo_root: Path, roots: Sequence[Path]) -> ScanResult:
    """Collect every source-hash pin without failing on one bad file.

    The encoder's own scan fails closed on the first unreadable or retired-schema
    file in a root. This scan records such files and keeps going, so one file
    cannot hide every other pin from the report.
    """
    result = ScanResult()
    for jurisdiction_root in roots:
        for path in iter_module_files(jurisdiction_root):
            result.yaml_files += 1
            relative = path.relative_to(repo_root).as_posix()
            try:
                payload = yaml.load(path.read_text(encoding="utf-8"), Loader=_SafeLoader)
            except (OSError, UnicodeError, yaml.YAMLError) as exc:
                result.unreadable.append((relative, f"{type(exc).__name__}: {exc}"))
                continue
            if not isinstance(payload, dict):
                continue
            module = payload.get("module")
            if not isinstance(module, dict):
                continue
            result.modules += 1
            verification = module.get("source_verification")
            if not isinstance(verification, dict):
                continue
            result.grounded += 1
            if "source_sha256" not in verification:
                result.unpinned += 1
                continue
            citation = verification.get("corpus_citation_path")
            result.pins.append(
                Pin(
                    path=relative,
                    citation_path=citation if isinstance(citation, str) else None,
                    pinned_sha=verification.get("source_sha256"),
                    has_plural_citation_field="corpus_citation_paths" in verification,
                )
            )
    return result


def check_pin(pin: Pin, resolve: Callable[[str], str]) -> PinResult:
    """Classify one pin against the encoder's current digest for its citation."""
    pinned = pin.pinned_sha
    pinned_text = pinned if isinstance(pinned, str) else repr(pinned)

    def result(status: str, current: str | None = None, detail: str | None = None):
        return PinResult(pin.path, pin.citation_path, status, pinned_text, current, detail)

    if not isinstance(pinned, str) or SHA256_RE.fullmatch(pinned) is None:
        return result("invalid", detail="source_sha256 is not 64 lowercase hex characters")
    if pin.has_plural_citation_field:
        return result(
            "invalid",
            detail="retired corpus_citation_paths field; the encoder refuses to scan it",
        )
    if pin.citation_path is None:
        return result("invalid", detail="no corpus_citation_path string to resolve")
    try:
        current = resolve(pin.citation_path)
    except ValueError as exc:
        # CorpusResolutionError and InvalidCorpusCitationError are ValueErrors.
        return result("unresolved", detail=f"{type(exc).__name__}: {exc}")
    if current == pinned:
        return result("match", current)
    return result("stale", current)


def check_pins(pins: Iterable[Pin], resolve: Callable[[str], str]) -> list[PinResult]:
    return [check_pin(pin, resolve) for pin in pins]


def overall_exit_status(
    pin_results: Sequence[PinResult],
    verdicts: Sequence[EncoderVerdict],
    disagreements: Sequence[str] = (),
) -> int:
    if disagreements:
        return EXIT_FINDINGS
    if any(item.status != "match" for item in pin_results):
        return EXIT_FINDINGS
    if any(verdict.exit_status != 0 for verdict in verdicts):
        return EXIT_FINDINGS
    return EXIT_CLEAN


NOT_FOUND = "<provision text not found>"


def parse_encoder_findings(output: str, repo_root: Path) -> dict[str, tuple[str, str]]:
    """Map each ``STALE`` module the encoder printed to ``(pinned, current)``."""
    findings: dict[str, tuple[str, str]] = {}
    current_path = None
    fields: dict[str, str] = {}
    for line in output.splitlines() + ["STALE <end>"]:
        if line.startswith("STALE "):
            if current_path is not None:
                findings[current_path] = (fields.get("pinned", ""), fields.get("current", ""))
            raw = line.removeprefix("STALE ").strip()
            try:
                current_path = Path(raw).relative_to(repo_root).as_posix()
            except ValueError:
                current_path = raw
            fields = {}
        elif current_path is not None and line.startswith("  "):
            key, _, value = line.strip().partition(" ")
            fields.setdefault(key, value.strip())
    findings.pop("<end>", None)
    return findings


def scan_completed(verdict: EncoderVerdict) -> bool:
    """True when the encoder scanned the whole root instead of refusing it."""
    lines = [line for line in verdict.output.splitlines() if line.strip()]
    if not lines:
        return False
    last = lines[-1]
    return (
        last.endswith("pinned module(s) are stale.")
        or (last.startswith("All ") and "pinned module(s) match corpus release" in last)
        or last.startswith("No RuleSpec modules found under")
    )


def differential(
    verdicts: Sequence[EncoderVerdict],
    pin_results: Sequence[PinResult],
    repo_root: Path,
) -> tuple[list[str], list[str]]:
    """Compare this report's pin statuses with the encoder's own verdict.

    Returns (roots compared, disagreements). Unpinned modules, which the
    encoder also lists as STALE with a ``<missing>`` pin, are outside the
    comparison; every module that declares ``source_sha256`` is inside it.
    """
    compared: list[str] = []
    disagreements: list[str] = []
    by_root: dict[str, list[PinResult]] = {}
    for item in pin_results:
        by_root.setdefault(item.path.split("/", 1)[0], []).append(item)
    for verdict in verdicts:
        if not scan_completed(verdict):
            continue
        compared.append(verdict.jurisdiction)
        encoder = {
            path: value
            for path, value in parse_encoder_findings(verdict.output, repo_root).items()
            if value[0] != "<missing>"
        }
        ours = {item.path: item for item in by_root.get(verdict.jurisdiction, [])}
        for path in sorted(set(encoder) - set(ours)):
            disagreements.append(f"{path}: encoder lists a pin this report did not find")
        for path, item in sorted(ours.items()):
            flagged = encoder.get(path)
            if item.status == "match":
                expected_ok = flagged is None
            elif item.status == "stale":
                expected_ok = flagged is not None and flagged[1] == item.current_sha
            else:
                expected_ok = flagged is not None and flagged[1] == NOT_FOUND
            if not expected_ok:
                ours_text = item.status + (
                    f" (current {item.current_sha})" if item.current_sha else ""
                )
                theirs = "match" if flagged is None else f"stale (current {flagged[1]})"
                disagreements.append(f"{path}: report says {ours_text}, encoder says {theirs}")
    return compared, disagreements


def summary_line(
    pin_results: Sequence[PinResult],
    verdicts: Sequence[EncoderVerdict],
    compared: Sequence[str],
    disagreements: Sequence[str],
) -> str:
    counts = Counter(item.status for item in pin_results)
    clean = sum(1 for verdict in verdicts if verdict.exit_status == 0)
    return (
        f"{len(pin_results)} pins: "
        + ", ".join(f"{counts.get(status, 0)} {status}" for status in PIN_STATUSES)
        + f"; encoder verdict clean in {clean} of {len(verdicts)} roots"
        + f"; differential compared {len(compared)} roots, {len(disagreements)} disagreements"
    )


def _table_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render_report(
    *,
    release: dict[str, str],
    scan: ScanResult,
    pin_results: Sequence[PinResult],
    verdicts: Sequence[EncoderVerdict],
    compared: Sequence[str] = (),
    disagreements: Sequence[str] = (),
) -> str:
    counts = Counter(item.status for item in pin_results)
    lines = [
        "# Source staleness report",
        "",
        f"- Corpus release: `{release['name']}` (content `{release['content_sha256']}`)",
        f"- Release provenance commit: `{release['commit']}`",
        f"- Signature verified with: `{release['key_label']}`",
        f"- axiom-encode: `{release['encoder_ref']}`",
        "",
        "## Pins",
        "",
        f"- YAML files scanned: {scan.yaml_files}",
        f"- Modules: {scan.modules}",
        f"- Modules with source_verification: {scan.grounded}",
        f"- Pinned (source_sha256 present): {len(scan.pins)}",
        f"- Unpinned (no source_sha256): {scan.unpinned}",
        "",
        "| status | modules |",
        "| --- | --- |",
    ]
    lines += [f"| {status} | {counts.get(status, 0)} |" for status in PIN_STATUSES]
    findings = [item for item in pin_results if item.status != "match"]
    if findings:
        lines += [
            "",
            "| status | module | citation | pinned | current | detail |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for item in findings[:MAX_LISTED_ROWS]:
            lines.append(
                "| "
                + " | ".join(
                    _table_cell(value)
                    for value in (
                        item.status,
                        item.path,
                        item.citation_path,
                        item.pinned_sha,
                        item.current_sha,
                        item.detail,
                    )
                )
                + " |"
            )
        if len(findings) > MAX_LISTED_ROWS:
            lines.append(
                f"\n{len(findings) - MAX_LISTED_ROWS} more finding(s) are in the JSON artifact."
            )
    if scan.unreadable:
        lines += ["", f"Unreadable YAML files: {len(scan.unreadable)}", ""]
        lines += [f"- `{path}`: {reason}" for path, reason in scan.unreadable[:MAX_LISTED_ROWS]]

    failing = [verdict for verdict in verdicts if verdict.exit_status != 0]
    lines += [
        "",
        "## Encoder verdict (`check-source-staleness`, one run per jurisdiction root)",
        "",
        f"- Clean: {len(verdicts) - len(failing)} of {len(verdicts)} jurisdiction roots",
    ]
    if failing:
        reasons = Counter(_verdict_reason(verdict) for verdict in failing)
        lines += ["", "| reason | roots |", "| --- | --- |"]
        lines += [
            f"| {_table_cell(reason)} | {count} |" for reason, count in reasons.most_common()
        ]
        lines += [
            "",
            "<details><summary>Per-root verdicts</summary>",
            "",
            "| root | exit | first finding |",
            "| --- | --- | --- |",
        ]
        lines += [
            f"| {verdict.jurisdiction} | {verdict.exit_status} | {_table_cell(verdict.headline)} |"
            for verdict in failing
        ]
        lines += ["", "</details>"]
    lines += [
        "",
        "## Differential (pin statuses above vs the encoder verdict)",
        "",
        f"- Roots compared (encoder scan completed): {len(compared)} of {len(verdicts)}",
        f"- Disagreements: {len(disagreements)}",
    ]
    lines += [f"  - {_table_cell(item)}" for item in disagreements[:MAX_LISTED_ROWS]]
    return "\n".join(lines) + "\n"


def _verdict_reason(verdict: EncoderVerdict) -> str:
    """Group encoder refusals by their reason, without the per-file location."""
    lines = [line.strip() for line in verdict.output.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if line.startswith("ERROR corpus release:"):
            return "corpus release refused: " + line.removeprefix(
                "ERROR corpus release:"
            ).strip().split(":", 1)[0]
        if line.startswith("ERROR ") and index + 1 < len(lines):
            follow = lines[index + 1]
            if follow.startswith("error"):
                reason = follow.removeprefix("error").strip()
                return "scan refused: " + re.sub(r": \$\..*$", "", reason)
    if any(line.startswith("STALE ") for line in lines):
        return "flags unpinned or stale modules"
    return verdict.headline


def _parse_labeled_key(value: str) -> tuple[str, str]:
    label, separator, key = value.partition("=")
    if not separator or not label or not key:
        raise argparse.ArgumentTypeError("expected LABEL=BASE64_PUBLIC_KEY")
    return label, key


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rulespec-root", type=Path, required=True)
    parser.add_argument("--corpus-path", type=Path, required=True)
    parser.add_argument(
        "--corpus-release-public-key",
        type=_parse_labeled_key,
        action="append",
        default=[],
        help="LABEL=KEY; tried in order until one verifies the release signature.",
    )
    parser.add_argument("--encoder-ref", default="unknown")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--json", dest="json_path", type=Path, required=True)
    return parser


def _harness_error(args: argparse.Namespace, message: str) -> int:
    text = f"# Source staleness report\n\nThe report could not be produced.\n\n{message}\n"
    args.report.write_text(text, encoding="utf-8")
    args.json_path.write_text(
        json.dumps({"harness_error": message}, indent=2) + "\n", encoding="utf-8"
    )
    print(text)
    return EXIT_HARNESS_ERROR


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return _run(args)
    except Exception as exc:  # noqa: BLE001 - any crash means no report
        return _harness_error(args, f"The report crashed: {type(exc).__name__}: {exc}")


def missing_provisions_hint(corpus_root: Path) -> str:
    """Explain a binding failure caused by provisions absent from the checkout.

    Reads the release object only to name missing paths; nothing here is
    trusted, because binding already failed.
    """
    try:
        objects = sorted((corpus_root / "releases").glob("*/*.json"))
        payload = json.loads(objects[0].read_text(encoding="utf-8"))
        paths = [
            artifact["path"]
            for artifact in payload["content"]["artifacts"]
            if artifact.get("artifact_class") == "provisions"
        ]
        missing = [path for path in paths if not (corpus_root / str(path)).is_file()]
        locks = (corpus_root / ".axiom" / "corpus-locks").is_dir()
    except Exception:  # noqa: BLE001 - a hint must never mask the real error
        return ""
    if not missing:
        return ""
    return (
        f"\n\n{len(missing)} of {len(paths)} provisions artifact(s) are not in the corpus "
        f"checkout (first: `{missing[0]}`)"
        + ("; the provenance commit carries `.axiom/corpus-locks/`" if locks else "")
        + ". A release cut after corpus bytes left git needs a staleness encoder pin "
        "that includes axiom-encode#1742 (it places provisions from git objects), and "
        "scopes ingested after the switch also need `axiom-encode corpus-fetch` with "
        "the read-only R2 credentials."
    )


def _run(args: argparse.Namespace) -> int:
    try:
        from axiom_encode.source_hash import (
            resolved_source_verification_block,
            run_check_source_staleness,
        )
        from axiom_encode.toolchain import (
            load_rulespec_local_corpus_release,
            local_corpus_release_verification,
        )
    except ImportError as exc:
        return _harness_error(args, f"axiom-encode is not importable: {exc}")
    if not args.corpus_release_public_key:
        return _harness_error(args, "no --corpus-release-public-key was supplied")

    repo_root = args.rulespec_root.resolve()
    corpus_root = args.corpus_path.resolve()
    try:
        roots = jurisdiction_roots(repo_root)
    except ValueError as exc:
        return _harness_error(args, str(exc))
    if not roots:
        return _harness_error(args, f"no jurisdiction roots under {repo_root}")

    release = None
    key_label = key = None
    refusals = []
    for key_label, key in args.corpus_release_public_key:
        try:
            with local_corpus_release_verification(key):
                release = load_rulespec_local_corpus_release(repo_root, corpus_root)
            break
        except ValueError as exc:
            refusals.append(f"- `{key_label}`: {type(exc).__name__}: {exc}")
    if release is None:
        return _harness_error(
            args,
            "No configured key bound the pinned release:\n\n"
            + "\n".join(refusals)
            + missing_provisions_hint(corpus_root),
        )

    missing = [
        artifact.path
        for artifact in release.artifacts
        if artifact.artifact_class == "provisions"
        and not (release.root / artifact.path).is_file()
    ]
    if missing:
        return _harness_error(
            args,
            f"{len(missing)} provisions artifact(s) of `{release.name}` are not in the "
            f"corpus checkout (first: `{missing[0]}`). A release cut after corpus bytes "
            "left git needs an encoder pin with `axiom-encode corpus-fetch` "
            "(axiom-encode#1742) and read-only R2 credentials.",
        )

    scan = scan_modules(repo_root, roots)
    pin_results = check_pins(
        scan.pins,
        lambda citation: resolved_source_verification_block(release, citation)[
            "source_sha256"
        ],
    )

    verdicts = []
    with local_corpus_release_verification(key):
        for root in roots:
            for attempt in range(1, ENCODER_ATTEMPTS + 1):
                buffer = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buffer):
                        status = run_check_source_staleness(
                            ["--rulespec-root", str(root), "--corpus-path", str(corpus_root)]
                        )
                except Exception:
                    if attempt == ENCODER_ATTEMPTS:
                        raise
                    continue
                output = buffer.getvalue()
                if TRANSIENT_ROOT_REFUSAL not in output:
                    break
            verdicts.append(EncoderVerdict(root.name, int(status), output, attempt))

    compared, disagreements = differential(verdicts, pin_results, repo_root)
    stuck = [verdict.jurisdiction for verdict in verdicts if TRANSIENT_ROOT_REFUSAL in verdict.output]
    stuck_message = (
        f"The encoder refused {len(stuck)} root(s) as noncanonical after "
        f"{ENCODER_ATTEMPTS} attempts: {', '.join(stuck)}. The report below is incomplete."
        if stuck
        else ""
    )
    release_facts = {
        "name": release.name,
        "content_sha256": release.content_sha256,
        "commit": _release_commit(release.release_object_path),
        "key_label": key_label,
        "encoder_ref": args.encoder_ref,
    }
    report = render_report(
        release=release_facts,
        scan=scan,
        pin_results=pin_results,
        verdicts=verdicts,
        compared=compared,
        disagreements=disagreements,
    )
    if stuck_message:
        report = report.replace(
            "# Source staleness report\n",
            f"# Source staleness report\n\n**Harness error.** {stuck_message}\n",
            1,
        )
    args.report.write_text(report, encoding="utf-8")
    harness = {"harness_error": stuck_message, "stuck_roots": stuck} if stuck else {}
    args.json_path.write_text(
        json.dumps(
            {
                **harness,
                "release": release_facts,
                "scan": {
                    "yaml_files": scan.yaml_files,
                    "modules": scan.modules,
                    "grounded": scan.grounded,
                    "pinned": len(scan.pins),
                    "unpinned": scan.unpinned,
                    "unreadable": scan.unreadable,
                },
                "pins": [asdict(item) for item in pin_results],
                "encoder_verdicts": [asdict(verdict) for verdict in verdicts],
                "differential": {"compared": compared, "disagreements": disagreements},
                "summary": summary_line(pin_results, verdicts, compared, disagreements),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(report)
    if stuck:
        return EXIT_HARNESS_ERROR
    return overall_exit_status(pin_results, verdicts, disagreements)


def _release_commit(release_object_path: Path) -> str:
    try:
        payload = json.loads(release_object_path.read_text(encoding="utf-8"))
        return str(payload["content"]["git"]["commit"])
    except (OSError, ValueError, KeyError, TypeError):
        return "unknown"


if __name__ == "__main__":
    sys.exit(main())
