"""Question files (`<jurisdiction>/questions/**/*.question.yaml`) name real rules and inputs.

A question file (format `axiom-source-question/v1`, defined and run by
`axiom-encode compare-sources --question`) lists the documents that answer one
question: each answer names a module, the rules that decide the question and
the module inputs that each canonical fact maps to. It is a sidecar, not a
RuleSpec module, so no module validator reads it.

This test keeps the names honest offline, in the pytest leg every pull request
runs: when a re-encode renames or removes a rule or an input that a question
file names, the pull request that does it fails here, not a later run of the
compare step. It checks names only; `compare-sources` runs the engine.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
QUESTION_FORMAT = "axiom-source-question/v1"
QUESTION_SUFFIX = ".question.yaml"
# <jurisdiction>:<module path>#<rule> and #input.<slot>, as compare-sources
# names them. Names may hold capitals (`..._subsection_a_10_A_i_VIII`).
_MODULE_REF = (
    r"(?P<jurisdiction>[a-z]{2}(?:-[a-z0-9]+)*):(?P<path>(?:statutes|regulations|policies|legislation)"
    r"(?:/[A-Za-z0-9][A-Za-z0-9._-]*)+)"
)
RULE_REF_RE = re.compile(_MODULE_REF + r"#(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
INPUT_REF_RE = re.compile(_MODULE_REF + r"#input\.(?P<name>[A-Za-z_][A-Za-z0-9_]*)")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sc = _load("source_conflicts", TOOLS / "source_conflicts.py")
hc = _load("household_choices", TOOLS / "household_choices.py")
CTX = sc.RepoContext(root=ROOT, repo="TheAxiomFoundation/rulespec-us")


def question_dirs() -> list[Path]:
    return sorted(path for path in ROOT.glob("*/questions") if path.is_dir() and sc.JURISDICTION_RE.fullmatch(path.parent.name))


def question_files() -> list[Path]:
    return sorted(path for base in question_dirs() for path in base.rglob("*") if path.is_file())


def _module(value: object, pattern: re.Pattern[str], *, label: str, shape: str):
    """(module path, rule names, imported names, formulas, name) or an issue list."""

    match = pattern.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        return [f"{label} must be {shape}."]
    relative = f"{match.group('jurisdiction')}/{match.group('path')}.yaml"
    if not (CTX.module_path_ok(relative) and (ROOT / relative).is_file()):
        return [f"{label} names {relative}, which is not a RuleSpec module in this repository."]
    found = hc._module_rules(ROOT / relative)
    if found is None:
        return [f"{label}: {relative} is not readable YAML."]
    return (relative, *found, match.group("name"))


def rule_issues(value: object, *, label: str) -> list[str]:
    """A rule reference names a rule of an existing module of this repository."""

    found = _module(value, RULE_REF_RE, label=label, shape="<jurisdiction>:<module path>#<rule>")
    if isinstance(found, list):
        return found
    relative, names, _imported, _formulas, name = found
    return [] if name in names else [f"{label}: `{name}` is not a rule of {relative}."]


def input_issues(value: object, *, label: str) -> list[str]:
    """An input reference names a free input that a formula of an existing
    module reads (the screen of tools/household_choices.py axiom_input_issues,
    with capitals allowed in the name)."""

    found = _module(value, INPUT_REF_RE, label=label, shape="<jurisdiction>:<module path>#input.<name>")
    if isinstance(found, list):
        return found
    relative, names, imported, formulas, name = found
    if name in names:
        return [f"{label}: `{name}` is a rule of {relative}, not an input."]
    if name in imported:
        return [f"{label}: `{name}` is imported by {relative}, not an input."]
    word = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")
    if not any(word.search(formula) for formula in formulas):
        return [f"{label}: no formula in {relative} reads `{name}`."]
    return []


def question_issues(path: Path) -> list[str]:
    label = path.relative_to(ROOT).as_posix()
    if not path.name.endswith(QUESTION_SUFFIX):
        return [f"{label}: a file under questions/ must be a `*{QUESTION_SUFFIX}` question file."]
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"{label}: not readable YAML ({exc})."]
    if not isinstance(payload, dict) or payload.get("format") != QUESTION_FORMAT:
        return [f"{label}: format must be {QUESTION_FORMAT}."]
    issues: list[str] = []
    jurisdiction = path.relative_to(ROOT).parts[0]
    if not (isinstance(payload.get("id"), str) and payload["id"].startswith(f"{jurisdiction}:")):
        issues.append(f"{label}.id must start with `{jurisdiction}:`.")
    answers = payload.get("answers")
    if not isinstance(answers, list) or len(answers) < 2:
        return [*issues, f"{label}.answers must list two or more answers."]
    for index, answer in enumerate(answers):
        a_label = f"{label}.answers[{index}]"
        if not isinstance(answer, dict):
            issues.append(f"{a_label} must be a mapping.")
            continue
        module = answer.get("module")
        if not (isinstance(module, str) and CTX.module_path_ok(module) and (ROOT / module).is_file()):
            issues.append(f"{a_label}.module names {module!r}, which is not a RuleSpec module in this repository.")
        for key in ("outputs", "guards"):
            for r_index, ref in enumerate(answer.get(key) or []):
                issues.extend(rule_issues(ref, label=f"{a_label}.{key}[{r_index}]"))
        for fact, ref in (answer.get("inputs") or {}).items():
            issues.extend(input_issues(ref, label=f"{a_label}.inputs.{fact}"))
        for key in ("derived", "fixed"):
            for ref in answer.get(key) or {}:
                issues.extend(input_issues(ref, label=f"{a_label}.{key}[{ref}]"))
    return issues


@pytest.mark.parametrize("path", question_files(), ids=lambda path: path.relative_to(ROOT).as_posix())
def test_question_file_names_real_rules_and_inputs(path: Path) -> None:
    assert question_issues(path) == []


def test_a_renamed_rule_or_input_is_reported() -> None:
    files = question_files()
    if not files:
        pytest.skip("no question files")
    payload = yaml.safe_load(files[0].read_text(encoding="utf-8"))
    answer = payload["answers"][0]
    answer["outputs"] = [answer["outputs"][0] + "_renamed"]
    fact = next(iter(answer["inputs"]))
    answer["inputs"][fact] = answer["inputs"][fact] + "_renamed"
    target = ROOT / files[0].parent.relative_to(ROOT) / "renamed.question.yaml"
    try:
        target.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        issues = question_issues(target)
    finally:
        target.unlink(missing_ok=True)
    assert any("is not a rule of" in issue for issue in issues), issues
    assert any("no formula in" in issue for issue in issues), issues


def test_only_question_files_live_under_questions() -> None:
    stray = [path for path in question_files() if not path.name.endswith(QUESTION_SUFFIX)]
    assert stray == []
