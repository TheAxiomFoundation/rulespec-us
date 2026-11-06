"""Validate, verify and aggregate the household-choices file.

`household-choices.yaml`, at the root of a rulespec repository beside the
source-conflict register, records the points where the law lets a household
pick among options and the pick can change tax or benefits: an election
(itemizing), an allocation between spouses, columns or returns, a method,
or the kind of return. The law agrees with itself there, so these are not
source conflicts; the open question is which option a model assumes.

Axiom stays deterministic: a choice is an ordinary input slot of the module
that grants it (`axiom.input`), which the caller supplies. The file holds the
default a caller supplies when the household states nothing, with the
authority for it (`default.basis`), and the objective a household would
pursue (`objective`; the standard is the household's net income for the
year). The simulation layer optimizes: PolicyEngine-US today, Axiom
simulations later. For each consumer the file records how it models the
choice (`implementations[].models`: optimized, candidate-min, convention,
input or absent), what it actually optimizes (`implementations[].objective`),
and the tests that pin its default or its optimum. Comparing the two gives
the worklist of choices to return to (`worklist`).

`statutory_not_choice` lists the near misses an inventory should not raise
again: a "whichever is greater" the statute computes, or a split the statute
fixes. Each names a citation and a note, and needs no tests.

Three commands, as for the register (tools/source_conflicts.py), whose
loader and validators this tool imports:

- `check` (offline; tests/test_household_choices.py runs it in the
  Repository Checks pytest leg): the schema, the domain and default rules,
  the modeling-state rules, public-file hygiene, that no global id is also a
  register entry's (one function, which the register's check calls too), and
  every reference into this checkout: `axiom.input` names a slot a module's
  formula reads, `source_conflict` names a register entry, and in-repo tests
  define their pinned tests (a syntactic screen).
- `verify` (network; the source-conflicts workflow): excerpts and snapshots
  as the register's verify checks them, every external commit is shipped
  code, each implementation's `cites_entry` matches whether its file carries
  `# Household choice <global id>`, and each external test file defines its
  pinned test, and that an implementation naming its decision `variable`
  defines it. It also prints the worklist. tools/pin_runner.py runs the
  pinned tests, and for an `optimum` pin it reads the pin's decision
  variable from the case's own simulation: the model must compute the chosen
  option (`chooses`), which must differ from the default, without the case
  setting the variable as an input or changing the model.
- `aggregate`: collect every rulespec repository's file into one JSON or
  Markdown view. It is deterministic (the same files give byte-identical
  output, in any order) and round-trips (`files_from_view` rebuilds the
  files it read).

See tools/README.md ("Household choices").
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import os
import re
import struct
import sys
import urllib.error
from collections.abc import Callable, Iterator, Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import source_conflicts as sc  # noqa: E402 - beside this file

CHOICES_FILENAME = sc.CHOICES_FILENAME
SCHEMA_VERSION = 1
# Code outside the rulespec repositories cites an entry at the line that
# models it. Axiom modules carry no marker: they are encoder output, and the
# link from Axiom is the entry's `axiom.input`.
MARKER = "Household choice"

# Who the law lets choose. `provider-household` and `state-agency` are the
# unit-derivation RFC's actors (axiom-rules-engine docs/unit-derivation.md
# 4.3); the others name the tax and benefit actors its SNAP examples don't
# reach. `eligible-claimants` is the set of taxpayers who could each claim a
# person (who claims a qualifying child), so it spans tax units.
ACTORS = (
    "taxpayer",
    "spouses-jointly",
    "either-spouse",
    "eligible-claimants",
    "household",
    "provider-household",
    "state-agency",
)
# Where the State agency decides (a delegation), the household optimizes
# nothing: the entry records the agency's convention, an input or nothing.
AGENCY_ACTORS = ("state-agency",)
AGENCY_MODELS = ("convention", "input", "absent")
# The entity each value of the choice belongs to.
ENTITIES = ("person", "marital-unit", "tax-unit", "family", "spm-unit", "household", "benefit-unit")
# Entities and actors whose choice can move more than one tax unit, so the
# objective's scope must be the household.
HOUSEHOLD_ENTITIES = ("family", "spm-unit", "household", "benefit-unit")
HOUSEHOLD_ACTORS = ("eligible-claimants", "household", "provider-household")
DOMAIN_KINDS = ("boolean", "enum", "share", "amount")
DEFAULT_BASES = ("statute", "regulation", "agency", "convention")
# A default with an authority cites a text of that kind.
BASIS_KINDS: dict[str, tuple[str, ...]] = {
    "statute": ("statute",),
    "regulation": ("regulation",),
    "agency": (
        "form", "instructions", "worksheet", "manual", "guidance", "policy", "plan", "calculator", "rulemaking",
        "agency-practice",
    ),
}
STRUCTURES = ("two-way", "finite", "piecewise-linear", "search")
# Structures whose exact optimum is cheap: compare both branches, enumerate
# the options, or evaluate the endpoints and listed kinks.
EXACT_STRUCTURES = ("two-way", "finite", "piecewise-linear")
# `optimized` is the exact optimum, including an implementation that evaluates
# the structure's whole exact set (both branches, every option, or every
# endpoint and listed kink); `candidate-min` is the best of a cheap subset.
MODELS = ("optimized", "candidate-min", "convention", "input", "absent")
OPTIMIZING = ("optimized", "candidate-min")
# An entry's objective is the standard one: the household's net income for
# the year, or, for a choice that moves only tax, total tax (federal, state
# and local), which is the same choice (P4).
MEASURES = ("net-income", "total-tax")
# What an implementation actually optimizes may be narrower.
IMPLEMENTATION_MEASURES = ("net-income", "total-tax", "federal-income-tax", "state-income-tax")
SCOPES = ("tax-unit", "household")
PINS = ("default", "optimum")

ENTRY_KEYS = frozenset(
    {
        "id",
        "jurisdiction",
        "program",
        "question",
        "actor",
        "years",
        "texts",
        "pending_texts",
        "text_kinds",
        "domain",
        "default",
        "objective",
        "multi_year",
        "optimization",
        "axiom",
        "implementations",
        "proposed",
        "tests",
        "source_conflict",
        "full_optimization",
    }
)
REQUIRED_ENTRY_KEYS = ("id", "jurisdiction", "program", "question", "actor", "domain", "default", "objective")
TOP_LEVEL_KEYS = frozenset({"version", "entries", "statutory_not_choice"})
TEST_KEYS = frozenset({"repo", "commit", "path", "name", "pins", "variable", "chooses", "instances"})
VARIABLE_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
OPTION_RE = sc.KEBAB_RE
# `<jurisdiction>:<content dir>/<path>#input.<slot>`, the key a request uses
# for a free input of a compiled module (us:statutes/26/63/c/6#input.<slot>).
AXIOM_INPUT_RE = re.compile(
    r"(?P<jurisdiction>[a-z]{2}(?:-[a-z0-9]+)*):(?P<path>(?:statutes|regulations|policies|legislation)"
    r"(?:/[A-Za-z0-9][A-Za-z0-9._-]*)+)#input\.(?P<slot>[a-z_][a-z0-9_]*)"
)


# ---------------------------------------------------------------------------
# Values in a domain


def _decimal(value: Any) -> Decimal | None:
    """A decimal string ("0.5", "1200") as a Decimal; None otherwise."""

    if isinstance(value, str) and sc.DECIMAL_RE.fullmatch(value):
        return Decimal(value)
    return None


_VALUE_HINT = " (true or false, an option, or a quoted decimal string within the bounds)"


def domain_issues(domain: Any, *, label: str) -> list[str]:
    issues: list[str] = []
    allowed = {"kind", "per", "options", "bounds", "currency", "coupled_with"}
    if not sc._mapping(domain, label=label, allowed=allowed, issues=issues):
        return issues
    kind = domain.get("kind")
    if kind not in DOMAIN_KINDS:
        issues.append(f"{label}.kind must be one of {', '.join(DOMAIN_KINDS)}.")
    if domain.get("per") not in ENTITIES:
        issues.append(f"{label}.per must be one of {', '.join(ENTITIES)}.")
    if kind == "enum":
        options = domain.get("options")
        if not (isinstance(options, list) and len(options) >= 2):
            issues.append(f"{label}.options must list at least two options.")
        else:
            if not all(isinstance(option, str) and OPTION_RE.fullmatch(option) for option in options):
                issues.append(f"{label}.options must be kebab-case strings.")
            elif len(set(options)) != len(options):
                issues.append(f"{label}.options repeats an option.")
    elif "options" in domain:
        issues.append(f"{label}.options is only for an enum.")
    if kind in ("share", "amount"):
        bounds = domain.get("bounds")
        values = [_decimal(bound) for bound in bounds] if isinstance(bounds, list) else []
        if len(values) != 2 or None in values:
            issues.append(f"{label}.bounds must be two non-negative decimal strings, low then high, such as [\"0\", \"1\"].")
        elif not values[0] < values[1]:
            issues.append(f"{label}.bounds must have the low bound below the high bound.")
        elif kind == "share" and values[1] > 1:
            issues.append(f"{label}.bounds of a share must lie within 0 and 1.")
    elif "bounds" in domain:
        issues.append(f"{label}.bounds is only for a share or an amount.")
    if kind == "amount":
        if not (isinstance(domain.get("currency"), str) and sc.CURRENCY_RE.fullmatch(domain["currency"])):
            issues.append(f"{label}.currency must be an ISO 4217 code such as USD.")
    elif "currency" in domain:
        issues.append(f"{label}.currency is only for an amount.")
    return issues


def in_domain(domain: Any, value: Any) -> bool:
    """Is `value` one of the options a (well-formed) domain allows?"""

    if not isinstance(domain, dict):
        return False
    kind = domain.get("kind")
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "enum":
        return isinstance(value, str) and value in (domain.get("options") or [])
    if kind in ("share", "amount"):
        bounds = domain.get("bounds")
        number = _decimal(value)
        low, high = (_decimal(bound) for bound in bounds) if isinstance(bounds, list) and len(bounds) == 2 else (None, None)
        return number is not None and low is not None and high is not None and low <= number <= high
    return False


def same_value(a: Any, b: Any) -> bool:
    """Two domain values are the same option: booleans and strings by
    equality and type; decimal strings by value, or when they round to the
    same float32 number a model would compute ("0.5" is "0.50", and
    "16777217" is "16777216"), since a pin can't tell those apart."""

    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    left, right = _decimal(a), _decimal(b)
    if left is not None and right is not None:
        if left == right:
            return True
        try:
            pack = lambda value: struct.unpack("f", struct.pack("f", float(value)))[0]  # noqa: E731
            return pack(left) == pack(right)
        except (OverflowError, struct.error):
            return False
    return type(a) is type(b) and a == b


# ---------------------------------------------------------------------------
# The objective


def meets_standard(entry_objective: Any, implementation_objective: Any) -> bool:
    """Does an implementation optimize the entry's own objective, or one at
    least as broad? Net income covers total tax; the household covers a tax
    unit."""

    if not (isinstance(entry_objective, Mapping) and isinstance(implementation_objective, Mapping)):
        return False
    wanted, actual = entry_objective.get("measure"), implementation_objective.get("measure")
    measure_ok = actual == "net-income" or (wanted == "total-tax" and actual == "total-tax")
    scope_ok = implementation_objective.get("scope") == "household" or entry_objective.get("scope") == "tax-unit"
    return measure_ok and scope_ok


def _objective_issues(value: Any, *, label: str, measures: tuple[str, ...]) -> list[str]:
    issues: list[str] = []
    if not sc._mapping(value, label=label, allowed={"measure", "scope"}, issues=issues):
        return issues
    if value.get("measure") not in measures:
        issues.append(f"{label}.measure must be one of {', '.join(measures)}.")
    if value.get("scope") not in SCOPES:
        issues.append(f"{label}.scope must be one of {', '.join(SCOPES)}.")
    return issues


# ---------------------------------------------------------------------------
# axiom.input


# A module's declared input (`inputs:`) against the entry's domain: the
# RuleSpec entity that is each domain entity, and the dtypes that can hold
# each kind of value. An entity or dtype outside these tables doesn't match.
RULESPEC_ENTITIES = {
    "Person": "person", "MaritalUnit": "marital-unit", "TaxUnit": "tax-unit", "Family": "family",
    "SPMUnit": "spm-unit", "Household": "household", "BenefitUnit": "benefit-unit",
}
KIND_DTYPES = {
    "boolean": ("Boolean", "Judgment"), "amount": ("Money",), "share": ("Rate", "Decimal", "Number"),
    "enum": ("Text", "String", "Integer"),
}
POLARITIES = ("same", "inverse")


def _module_rules(path: Path) -> tuple[set[str], set[str], list[str]] | None:
    """(rule names, imported names, formula texts) of a module, or None."""

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError, RecursionError):  # ValueError: undecodable, or 2026-02-30
        return None
    if not isinstance(payload, dict):
        return None
    rules = payload.get("rules") if isinstance(payload.get("rules"), list) else []
    names = {rule["name"] for rule in rules if isinstance(rule, dict) and isinstance(rule.get("name"), str)}
    imports = payload.get("imports") if isinstance(payload.get("imports"), list) else []
    imported = {item.rsplit("#", 1)[1] for item in imports if isinstance(item, str) and "#" in item}
    formulas: list[str] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if isinstance(rule.get("formula"), str):
            formulas.append(rule["formula"])
        for version in rule.get("versions") if isinstance(rule.get("versions"), list) else []:
            if isinstance(version, dict) and isinstance(version.get("formula"), str):
                formulas.append(version["formula"])
    return names, imported, formulas


def _declared_inputs(path: Path) -> dict[str, Mapping[str, Any]]:
    """A module's declared inputs (`inputs:`), by name; {} when it has none."""

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError, RecursionError):  # ValueError: undecodable, or 2026-02-30
        return {}
    inputs = payload.get("inputs") if isinstance(payload, dict) else None
    return {
        item["name"]: item
        for item in (inputs if isinstance(inputs, list) else [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }


def axiom_input_issues(value: Any, *, label: str, ctx: sc.RepoContext, domain: Any = None) -> list[str]:
    """An Axiom input slot names a free input that a formula in an existing
    module of this repository reads. A syntactic screen: the slot is a whole
    word in a formula, and is neither a rule of the module nor an import.
    When the module declares the slot under `inputs:`, its entity and dtype
    must fit the entry's domain (`per` and `kind`)."""

    match = AXIOM_INPUT_RE.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        return [f"{label} must be <jurisdiction>:<module path>#input.<slot>, such as us:statutes/26/63/c/6#input.<slot>."]
    relative = f"{match.group('jurisdiction')}/{match.group('path')}.yaml"
    if not (sc._relative_path(relative) and ctx.module_path_ok(relative) and (ctx.root / relative).is_file()):
        return [f"{label} names {relative}, which is not a RuleSpec module in this repository."]
    found = _module_rules(ctx.root / relative)
    if found is None:
        return [f"{label}: {relative} is not readable YAML."]
    names, imported, formulas = found
    slot = match.group("slot")
    if slot in names:
        return [f"{label}: `{slot}` is a rule of {relative}, not an input."]
    if slot in imported:
        return [f"{label}: `{slot}` is imported by {relative}, not an input."]
    word = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(slot)}(?![A-Za-z0-9_])")
    if not any(word.search(formula) for formula in formulas):
        return [f"{label}: no formula in {relative} reads `{slot}`."]
    declared = _declared_inputs(ctx.root / relative).get(slot)
    issues: list[str] = []
    # `domain` is None unless the entry's domain is valid (check_entry reports
    # an invalid one), so its per and kind are known strings here.
    if declared is not None and isinstance(domain, dict):
        entity, dtype = declared.get("entity"), declared.get("dtype")
        if "entity" in declared and (not isinstance(entity, str) or RULESPEC_ENTITIES.get(entity) != domain.get("per")):
            issues.append(f"{label}: {relative} declares `{slot}` on {entity}, not the domain's {domain.get('per')}.")
        if "dtype" in declared and dtype not in KIND_DTYPES.get(domain.get("kind"), ()):
            issues.append(f"{label}: {relative} declares `{slot}` as {dtype}, which can't hold a {domain.get('kind')} choice.")
    return issues


# ---------------------------------------------------------------------------
# check (offline)


def _prose_fields(entry: Mapping[str, Any], label: str) -> Iterator[tuple[str, str]]:
    """The entry's own prose. Excerpts and citations quote others."""

    for key in ("question", "full_optimization"):
        if isinstance(entry.get(key), str):
            yield f"{label}.{key}", entry[key]
    for key, field in (("default", "note"), ("optimization", "candidates"), ("years", "note")):
        value = entry.get(key)
        if isinstance(value, dict) and isinstance(value.get(field), str):
            yield f"{label}.{key}.{field}", value[field]
    implementations = entry.get("implementations")
    for index, item in enumerate(implementations if isinstance(implementations, list) else []):
        if isinstance(item, dict) and isinstance(item.get("basis"), str):
            yield f"{label}.implementations[{index}].basis", item["basis"]


def money_issues(fields: list[tuple[str, str]]) -> list[str]:
    """The file has no money cases, so its prose states no amount: a public
    dollar figure needs a test that computes it (the register's rule)."""

    issues: list[str] = []
    for field_label, text in fields:
        for odd in sc._unsupported_money(text):
            issues.append(f"{field_label} writes money as `{odd}`; describe the effect without an amount.")
        for amount in sorted(sc._dollar_values(text)):
            issues.append(
                f"{field_label} states ${amount}; this file has no money cases, so describe the effect "
                "without an amount."
            )
    return issues


def _cites_kind(entry: Mapping[str, Any], kinds: tuple[str, ...]) -> bool:
    """Does the entry cite a text (corpus or pending) of one of these kinds?"""

    if any(sc.text_kind(entry, path) in kinds for path in sc.cited_corpus_paths(entry)):
        return True
    pending = entry.get("pending_texts")
    return any(isinstance(item, dict) and item.get("kind") in kinds for item in (pending if isinstance(pending, list) else []))


def _consumer_issues(axiom: Mapping[str, Any], *, label: str, ctx: sc.RepoContext, domain: Any) -> list[str]:
    """`axiom.consumers`: input slots that take the same choice, each with its
    polarity (`same`, or `inverse`: true means the other option). Booleans
    only: a consumer of another kind would need a mapping between the slots'
    values, which isn't defined, so it is refused rather than guessed. A
    consumer may sit in the granting module, as a different slot."""

    issues: list[str] = []
    consumers = axiom.get("consumers")
    if isinstance(domain, dict) and domain.get("kind") != "boolean":
        issues.append(
            f"{label} is only for a boolean choice: no mapping between other kinds of slot values is defined, so "
            "list none."
        )
    if not sc._nonempty_list(consumers, label=label, issues=issues):
        return issues
    seen: set[str] = set()
    for c_index, item in enumerate(consumers):
        c_label = f"{label}[{c_index}]"
        if not sc._mapping(item, label=c_label, allowed={"input", "polarity"}, issues=issues):
            continue
        slot = item.get("input")
        issues.extend(axiom_input_issues(slot, label=f"{c_label}.input", ctx=ctx, domain=domain))
        if isinstance(slot, str):
            if slot == axiom.get("input"):
                issues.append(f"{c_label}.input is axiom.input itself; a consumer is a slot in another module.")
            if slot in seen:
                issues.append(f"{c_label}.input repeats a consumer.")
            seen.add(slot)
        if item.get("polarity") not in POLARITIES:
            issues.append(f"{c_label}.polarity must be same or inverse.")
    return issues


def check_entry(
    entry: Any, *, index: int, ctx: sc.RepoContext, jurisdictions: frozenset[str], conflict_ids: frozenset[str],
    choice_ids: frozenset[str],
) -> list[str]:
    location = f"entries[{index}]"
    entry_id = entry.get("id") if isinstance(entry, dict) else None
    label = f"Entry `{entry_id}` ({location})" if isinstance(entry_id, str) and entry_id.strip() else location
    issues: list[str] = []
    if not sc._mapping(entry, label=label, allowed=ENTRY_KEYS, issues=issues):
        return issues
    for key in REQUIRED_ENTRY_KEYS:
        if key not in entry:
            issues.append(f"{label}.{key} is required.")
    if isinstance(entry_id, str) and sc.KEBAB_RE.fullmatch(entry_id) is None:
        issues.append(f"{label}.id must match [a-z0-9]+(-[a-z0-9]+)*.")
    elif "id" in entry and not isinstance(entry_id, str):
        issues.append(f"{label}.id must be a string.")
    jurisdiction = entry.get("jurisdiction")
    if "jurisdiction" in entry and not (isinstance(jurisdiction, str) and jurisdiction in jurisdictions):
        issues.append(f"{label}.jurisdiction must be a jurisdiction directory of this repository ({', '.join(sorted(jurisdictions))}).")
    program = entry.get("program")
    if "program" in entry and not (isinstance(program, str) and sc.KEBAB_RE.fullmatch(program)):
        issues.append(f"{label}.program must be kebab-case.")
    if "question" in entry:
        sc._string(entry.get("question"), label=f"{label}.question", issues=issues)
    actor = entry.get("actor")
    if "actor" in entry and actor not in ACTORS:
        issues.append(f"{label}.actor must be one of {', '.join(ACTORS)}.")

    # The law that grants the choice, checked as the register checks it.
    if "texts" in entry:
        sc.check_texts(entry.get("texts"), label=f"{label}.texts", require=False, issues=issues)
    if "pending_texts" in entry:
        sc.check_pending_texts(entry.get("pending_texts"), label=f"{label}.pending_texts", issues=issues)
    has_texts = isinstance(entry.get("texts"), list) and bool(entry.get("texts"))
    has_pending = isinstance(entry.get("pending_texts"), list) and bool(entry.get("pending_texts"))
    if not has_texts and not has_pending:
        issues.append(f"{label} must cite the provision that grants the choice in texts or pending_texts.")
    sc.check_text_kinds(entry, label=label, issues=issues)
    if "years" in entry:
        sc._check_years(entry.get("years"), label=f"{label}.years", issues=issues)

    domain = entry.get("domain")
    if "domain" in entry:
        issues.extend(domain_issues(domain, label=f"{label}.domain"))
    domain_ok = isinstance(domain, dict) and not domain_issues(domain, label="")
    coupled = domain.get("coupled_with") if isinstance(domain, dict) else None
    if isinstance(domain, dict) and "coupled_with" in domain:
        if not (isinstance(coupled, list) and coupled):
            issues.append(f"{label}.domain.coupled_with must be a non-empty list of global ids in this file.")
        else:
            own = sc.global_id(entry)
            for c_index, gid in enumerate(coupled):
                if not isinstance(gid, str) or gid not in choice_ids or gid == own:
                    issues.append(
                        f"{label}.domain.coupled_with[{c_index}] must be the global id of another entry in "
                        f"{CHOICES_FILENAME}."
                    )
            if len(set(map(str, coupled))) != len(coupled):
                issues.append(f"{label}.domain.coupled_with repeats an entry.")

    default = entry.get("default")
    if "default" in entry and sc._mapping(default, label=f"{label}.default", allowed={"value", "basis", "note"}, issues=issues):
        if "value" not in default:
            issues.append(f"{label}.default.value is required.")
        elif domain_ok and not in_domain(domain, default.get("value")):
            issues.append(f"{label}.default.value is not one of the domain's options{_VALUE_HINT}.")
        basis = default.get("basis")
        if basis not in DEFAULT_BASES:
            issues.append(f"{label}.default.basis must be one of {', '.join(DEFAULT_BASES)}.")
        elif basis == "convention":
            if "note" not in default:
                issues.append(f"{label}.default.note is required for a convention: say what the convention is.")
        elif not _cites_kind(entry, BASIS_KINDS[basis]):
            issues.append(
                f"{label}.default.basis is `{basis}`, so the entry must cite a text of kind "
                f"{' or '.join(BASIS_KINDS[basis])} that sets the default."
            )
        if "note" in default:
            sc._string(default.get("note"), label=f"{label}.default.note", issues=issues)

    objective = entry.get("objective")
    if "objective" in entry:
        issues.extend(_objective_issues(objective, label=f"{label}.objective", measures=MEASURES))
        spans = actor in HOUSEHOLD_ACTORS or (isinstance(domain, dict) and domain.get("per") in HOUSEHOLD_ENTITIES)
        if spans and isinstance(objective, dict) and objective.get("scope") == "tax-unit":
            issues.append(
                f"{label}.objective.scope must be household: this choice can move more than one tax unit "
                "(its actor or its entity spans the household)."
            )
    if "multi_year" in entry and entry["multi_year"] is not True:
        issues.append(
            f"{label}.multi_year must be true when present: it flags a choice that binds later years or "
            "carries amounts forward, optimized one year at a time for now."
        )

    optimization = entry.get("optimization")
    if "optimization" in entry:
        if actor in AGENCY_ACTORS:
            issues.append(f"{label}.optimization must be absent: the State agency decides, so the household optimizes nothing.")
        if sc._mapping(optimization, label=f"{label}.optimization", allowed={"structure", "candidates"}, issues=issues):
            structure = optimization.get("structure")
            if structure not in STRUCTURES:
                issues.append(f"{label}.optimization.structure must be one of {', '.join(STRUCTURES)}.")
            elif domain_ok:
                kind = domain.get("kind")
                options = len(domain.get("options") or []) if kind == "enum" else 2 if kind == "boolean" else None
                if structure == "two-way" and options != 2:
                    issues.append(f"{label}.optimization.structure two-way needs a boolean or a two-option enum.")
                elif structure == "finite" and options is None:
                    issues.append(f"{label}.optimization.structure finite needs a boolean or an enum.")
                elif structure == "piecewise-linear" and kind not in ("share", "amount"):
                    issues.append(f"{label}.optimization.structure piecewise-linear needs a share or an amount.")
            if "candidates" in optimization:
                sc._string(optimization.get("candidates"), label=f"{label}.optimization.candidates", issues=issues)
    if "full_optimization" in entry:
        sc._string(entry.get("full_optimization"), label=f"{label}.full_optimization", issues=issues)

    if "axiom" in entry:
        axiom = entry["axiom"]
        if sc._mapping(axiom, label=f"{label}.axiom", allowed={"input", "consumers"}, issues=issues):
            if "input" not in axiom and "consumers" not in axiom:
                issues.append(f"{label}.axiom needs input, consumers or both.")
            if "input" in axiom:
                issues.extend(
                    axiom_input_issues(axiom.get("input"), label=f"{label}.axiom.input", ctx=ctx, domain=domain if domain_ok else None)
                )
            if "consumers" in axiom:
                issues.extend(
                    _consumer_issues(axiom, label=f"{label}.axiom.consumers", ctx=ctx, domain=domain if domain_ok else None)
                )
    if "source_conflict" in entry:
        value = entry["source_conflict"]
        if not (isinstance(value, str) and value in conflict_ids):
            issues.append(f"{label}.source_conflict must be the global id of an entry in {sc.REGISTER_FILENAME}.")

    implementations = entry.get("implementations", [])
    if "implementations" in entry:
        if not sc._nonempty_list(implementations, label=f"{label}.implementations", issues=issues):
            implementations = []
        for i_index, item in enumerate(implementations):
            i_label = f"{label}.implementations[{i_index}]"
            if not sc._mapping(
                item, label=i_label,
                allowed={"repo", "commit", "path", "models", "objective", "basis", "cites_entry", "variable"},
                issues=issues,
            ):
                continue
            if "variable" in item and not (isinstance(item["variable"], str) and VARIABLE_RE.fullmatch(item["variable"])):
                issues.append(f"{i_label}.variable must name the model variable that holds the choice.")
            if "repo" not in item:
                issues.append(f"{i_label}.repo is required; an Axiom module links through axiom.input.")
            else:
                sc._check_external_ref(item, label=i_label, ctx=ctx, issues=issues)
            if not sc._relative_path(item.get("path")):
                issues.append(f"{i_label}.path must be a relative path inside the repository.")
            models = item.get("models")
            if models not in MODELS:
                issues.append(f"{i_label}.models must be one of {', '.join(MODELS)}.")
            elif actor in AGENCY_ACTORS and models not in AGENCY_MODELS:
                issues.append(f"{i_label}.models must be one of {', '.join(AGENCY_MODELS)}: the State agency decides.")
            elif models in OPTIMIZING:
                if "variable" not in item:
                    issues.append(
                        f"{i_label}.variable is required when models is {models}: name the model variable that "
                        "holds the choice, which its optimum pin reads."
                    )
                if "objective" not in item:
                    issues.append(f"{i_label}.objective is required when models is {models}: say what it optimizes.")
                else:
                    issues.extend(
                        _objective_issues(item["objective"], label=f"{i_label}.objective", measures=IMPLEMENTATION_MEASURES)
                    )
                if not isinstance(optimization, dict):
                    issues.append(f"{i_label} models {models}, so the entry needs optimization.structure.")
                elif models == "optimized" and optimization.get("structure") == "search":
                    issues.append(f"{i_label} models optimized, but the structure is search, which finds no exact optimum.")
                elif models == "candidate-min" and "candidates" not in optimization:
                    issues.append(f"{i_label} models candidate-min, so the entry needs optimization.candidates.")
            elif "objective" in item:
                issues.append(f"{i_label}.objective is only for an implementation that optimizes.")
            if "basis" in item:
                sc._string(item.get("basis"), label=f"{i_label}.basis", issues=issues)
            if not isinstance(item.get("cites_entry"), bool):
                issues.append(f"{i_label}.cites_entry must be true or false.")

    if "proposed" in entry:
        proposed = entry["proposed"]
        if sc._nonempty_list(proposed, label=f"{label}.proposed", issues=issues):
            for p_index, item in enumerate(proposed):
                p_label = f"{label}.proposed[{p_index}]"
                if not sc._mapping(item, label=p_label, allowed={"repo", "pr", "path", "models"}, issues=issues):
                    continue
                repo = item.get("repo")
                if not (isinstance(repo, str) and sc.REPO_RE.fullmatch(repo)):
                    issues.append(f"{p_label}.repo must be owner/name.")
                pr = item.get("pr")
                match = sc.PR_URL_RE.fullmatch(pr) if isinstance(pr, str) else None
                if match is None:
                    issues.append(f"{p_label}.pr must be a github.com pull request URL.")
                elif isinstance(repo, str) and match.group("repo") != repo:
                    issues.append(f"{p_label}.pr is a pull request in {match.group('repo')}, not {repo}.")
                if not sc._relative_path(item.get("path")):
                    issues.append(f"{p_label}.path must be a relative path inside the repository.")
                if item.get("models") not in MODELS:
                    issues.append(f"{p_label}.models must be one of {', '.join(MODELS)}.")
                elif actor in AGENCY_ACTORS and item["models"] not in AGENCY_MODELS:
                    issues.append(f"{p_label}.models must be one of {', '.join(AGENCY_MODELS)}: the State agency decides.")

    tests = entry.get("tests", [])
    if "tests" in entry:
        if not sc._nonempty_list(tests, label=f"{label}.tests", issues=issues):
            tests = []
        seen: set[tuple[Any, Any, Any]] = set()
        for t_index, item in enumerate(tests):
            t_label = f"{label}.tests[{t_index}]"
            located = sc.check_test_location(item, label=t_label, ctx=ctx, allowed=TEST_KEYS, issues=issues)
            if located is None:
                continue
            external, path, name = located
            pins = item.get("pins")
            if not (isinstance(pins, list) and pins and all(isinstance(pin, str) for pin in pins)):
                issues.append(f"{t_label}.pins must be a non-empty list of default or optimum.")
                pins = []
            elif not set(pins) <= set(PINS):
                issues.append(f"{t_label}.pins may name only default and optimum.")
            elif len(set(pins)) != len(pins):
                issues.append(f"{t_label}.pins repeats a pin.")
            elif set(pins) == set(PINS):
                issues.append(f"{t_label} pins both default and optimum; a case showing the optimum differs from the default.")
            if "optimum" in pins:
                if actor in AGENCY_ACTORS:
                    issues.append(f"{t_label} pins optimum, but the State agency decides, so nothing is optimized.")
                if not (external and isinstance(item.get("path"), str) and item["path"].endswith(".yaml")):
                    issues.append(
                        f"{t_label} pins optimum, so it must be another repository's YAML test case: "
                        "tools/pin_runner.py reads the decision variable from the case's own simulation."
                    )
                variable = item.get("variable")
                if not (isinstance(variable, str) and VARIABLE_RE.fullmatch(variable)):
                    issues.append(
                        f"{t_label}.variable must name the model variable that holds the choice; the runner reads it "
                        "from the case's simulation, so the case need not assert it."
                    )
                if "chooses" not in item:
                    issues.append(f"{t_label}.chooses is required with optimum: the option the model must compute.")
                elif domain_ok and not in_domain(domain, item["chooses"]):
                    issues.append(f"{t_label}.chooses is not one of the domain's options{_VALUE_HINT}.")
                elif isinstance(default, dict) and "value" in default and same_value(item["chooses"], default["value"]):
                    issues.append(
                        f"{t_label}.chooses is the default, so the pin is vacuous: use a case where the optimum "
                        "and the default differ."
                    )
                if "instances" in item:
                    instances = item["instances"]
                    if not (
                        isinstance(instances, list)
                        and instances
                        and all(isinstance(each, str) and each.strip() and "\n" not in each for each in instances)
                    ):
                        issues.append(
                            f"{t_label}.instances must be a non-empty list of the case's entity instance ids that "
                            "must compute the chosen option."
                        )
                    elif len(set(instances)) != len(instances):
                        issues.append(f"{t_label}.instances repeats an instance.")
            else:
                for key in ("variable", "chooses", "instances"):
                    if key in item:
                        issues.append(f"{t_label}.{key} is only for an optimum pin.")
            sc.check_repeated_test(item, path, name, label=t_label, seen=seen, issues=issues)
            if not external:
                sc.check_local_test(path, name, label=t_label, ctx=ctx, issues=issues)

    # Every implementation that models the choice is pinned at its own commit:
    # an optimizing one by an optimum case on its decision variable, a
    # convention or input by a case showing it takes the default. One that
    # does not model it needs none.
    pinned = {
        (repr(item.get("repo")), repr(item.get("commit")), pin, repr(item.get("variable")) if pin == "optimum" else None)
        for item in tests or []
        if isinstance(item, dict) and isinstance(item.get("pins"), list)
        for pin in item["pins"]
        if isinstance(pin, str)
    }
    for i_index, item in enumerate(implementations or []):
        if not isinstance(item, dict) or item.get("models") not in MODELS or item["models"] == "absent":
            continue
        optimizing = item["models"] in OPTIMIZING
        needed = "optimum" if optimizing else "default"
        variable = repr(item.get("variable")) if optimizing else None
        if (repr(item.get("repo")), repr(item.get("commit")), needed, variable) not in pinned:
            on = (f" on {item['variable']}" if isinstance(item.get("variable"), str) else " on its decision variable") if optimizing else ""
            issues.append(
                f"{label}.implementations[{i_index}] models {item['models']}, so a test in {item.get('repo')} at the "
                f"same commit must pin {needed}{on}."
            )

    issues.extend(money_issues(list(_prose_fields(entry, label))))
    return issues


def check_statutory(items: Any, *, jurisdictions: frozenset[str]) -> list[str]:
    """Near misses: a computation or split the statute fixes, not a choice."""

    issues: list[str] = []
    label = "statutory_not_choice"
    if not sc._nonempty_list(items, label=label, issues=issues):
        return issues
    seen: set[tuple[Any, Any]] = set()
    for index, item in enumerate(items):
        i_label = f"{label}[{index}]"
        if not sc._mapping(item, label=i_label, allowed={"jurisdiction", "citation", "note"}, issues=issues):
            continue
        if not (isinstance(item.get("jurisdiction"), str) and item["jurisdiction"] in jurisdictions):
            issues.append(f"{i_label}.jurisdiction must be a jurisdiction directory of this repository.")
        sc._string(item.get("citation"), label=f"{i_label}.citation", issues=issues)
        sc._string(item.get("note"), label=f"{i_label}.note", issues=issues)
        key = (item.get("jurisdiction"), item.get("citation"))
        if all(isinstance(part, str) for part in key):  # a malformed one is reported above
            if key in seen:
                issues.append(f"{i_label} repeats {key[1]} for {key[0]}.")
            seen.add(key)
        if isinstance(item.get("note"), str):
            issues.extend(money_issues([(f"{i_label}.note", item["note"])]))
    return issues


def _register_ids(root: Path) -> tuple[frozenset[str], list[str]]:
    path = root / sc.REGISTER_FILENAME
    if not (path.exists() or path.is_symlink()):
        return frozenset(), []
    try:
        return frozenset(sc._global_ids(sc.load_register(path))), []
    except sc.RegisterError as exc:
        return frozenset(), [f"cannot read {sc.REGISTER_FILENAME} to check source_conflict links: {exc}"]


def check_choices(payload: Any, ctx: sc.RepoContext) -> list[str]:
    issues: list[str] = []
    if not isinstance(payload, dict):
        return [f"{CHOICES_FILENAME} must be a mapping with `version` and `entries`."]
    if sc._recursive(payload):
        return [f"{CHOICES_FILENAME} contains itself through an alias; anchors and aliases are not allowed."]
    for key in payload:
        if key not in TOP_LEVEL_KEYS:
            issues.append(f"{CHOICES_FILENAME} has unknown top-level key `{key}`.")
    if payload.get("version") != SCHEMA_VERSION:
        issues.append(f"{CHOICES_FILENAME} version must be {SCHEMA_VERSION}.")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        issues.append(f"{CHOICES_FILENAME} entries must be a list.")
        entries = []
    jurisdictions = ctx.jurisdictions()
    conflict_ids, register_issues = _register_ids(ctx.root)
    issues.extend(register_issues)
    choice_ids = frozenset(sc._global_ids(payload))
    seen: dict[str, int] = {}
    for index, entry in enumerate(entries):
        issues.extend(
            check_entry(
                entry, index=index, ctx=ctx, jurisdictions=jurisdictions, conflict_ids=conflict_ids, choice_ids=choice_ids
            )
        )
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and isinstance(entry.get("jurisdiction"), str):
            gid = sc.global_id(entry)
            if gid in seen:
                issues.append(f"entries[{index}] `{gid}` duplicates entries[{seen[gid]}].")
            seen.setdefault(gid, index)
    # Coupling is mutual: a choice made together with another is listed on both.
    by_id = {
        sc.global_id(entry): entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and isinstance(entry.get("jurisdiction"), str)
    }
    for gid, entry in by_id.items():
        domain = entry.get("domain")
        coupled = domain.get("coupled_with") if isinstance(domain, dict) else None
        for other in coupled if isinstance(coupled, list) else []:
            partner = by_id.get(other) if isinstance(other, str) else None
            partner_domain = partner.get("domain") if isinstance(partner, dict) else None
            back = partner_domain.get("coupled_with") if isinstance(partner_domain, dict) else None
            if partner is not None and other != gid and not (isinstance(back, list) and gid in back):
                issues.append(f"`{gid}` is coupled with `{other}`, but `{other}` does not list `{gid}` in domain.coupled_with.")
    if "statutory_not_choice" in payload:
        issues.extend(check_statutory(payload["statutory_not_choice"], jurisdictions=jurisdictions))
    issues.extend(sc.hygiene_issues(payload, root="household-choices", public=CHOICES_FILENAME))
    issues.extend(sc.id_collision_issues(ctx.root, choices=payload))
    return issues


# ---------------------------------------------------------------------------
# The worklist


def worklist(entry: Mapping[str, Any]) -> list[str]:
    """What is left to return to for one entry (total: aggregate reads other
    repositories' files, checked or not): implementations that
    don't model the choice, that settle for a convention or a candidate set
    where a cheap exact optimum is known, or that optimize a narrower
    objective than the entry's; a choice no implementation is recorded for;
    a choice that binds later years; and a choice with no Axiom input slot
    in the module that grants it, naming the slots other modules take it in."""

    items: list[str] = []
    optimization = entry.get("optimization") if isinstance(entry.get("optimization"), dict) else {}
    structure = optimization.get("structure")
    for item in sc._as_list(entry.get("implementations")):
        if not isinstance(item, dict):
            continue
        repo, models = item.get("repo"), item.get("models")
        if models == "absent":
            items.append(f"{repo} does not model this choice")
        elif models in ("convention", "candidate-min") and structure in EXACT_STRUCTURES:
            items.append(f"{repo} uses {models} where a {structure} comparison finds the exact optimum")
        if models in OPTIMIZING and not meets_standard(entry.get("objective"), item.get("objective")):
            actual = item.get("objective") if isinstance(item.get("objective"), dict) else {}
            wanted = entry.get("objective") if isinstance(entry.get("objective"), dict) else {}
            items.append(
                f"{repo} optimizes {actual.get('measure')} over the {actual.get('scope')}, narrower than "
                f"{wanted.get('measure')} over the {wanted.get('scope')}"
            )
    if not entry.get("implementations"):
        items.append("no implementation recorded")
    if entry.get("multi_year") is True:
        items.append("binds later years or carries amounts forward; optimized one year at a time")
    axiom = entry.get("axiom") if isinstance(entry.get("axiom"), dict) else {}
    if not axiom.get("input"):
        consumers = [
            f"{item.get('input')} ({item.get('polarity')})" for item in sc._as_list(axiom.get("consumers")) if isinstance(item, dict)
        ]
        line = "no Axiom input slot in the module that grants it yet"
        if consumers:
            line += (
                "; other slots take it as an input, so a caller sets them consistently (this lists them; it doesn't "
                f"check that their encodings agree): {', '.join(consumers)}"
            )
        items.append(line)
    return items


# ---------------------------------------------------------------------------
# verify (network)


def defines_class(source: str, name: str) -> bool | None:
    """Does the Python source define `class <name>` in module scope, as a
    model variable is defined? That includes a class inside a module-level
    if, try, with, loop or match, which open no scope; a class in a
    docstring, a comment, or a function or class body doesn't count. None
    when the source doesn't parse."""

    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return None
    return any(isinstance(node, ast.ClassDef) and node.name == name for node in sc._scope_statements(tree.body))


def cites(source: str, gid: str) -> bool:
    """Does the file carry `# Household choice <gid>`, with nothing more of
    an id after it (us:a never matches a cite of us:a-b)?"""

    return re.search(rf"#\s*{MARKER} {re.escape(gid)}(?![A-Za-z0-9:-])", source) is not None


def verify_choices(
    payload: Mapping[str, Any],
    *,
    fetch: sc.Fetch,
    matches: Callable[[str, str], bool],
    resolve: Callable[[str], str | None] | None,
    on_default_branch: Callable[[str, str], bool] | None = None,
) -> tuple[list[str], list[str]]:
    """(issues, report lines), as the register's verify: `resolve` None skips
    corpus texts and `on_default_branch` None skips reachability, both
    reported."""

    issues: list[str] = []
    report: list[str] = []
    shipped = sc.shipped_checker(on_default_branch, issues)
    if on_default_branch is None:
        report.append(sc.UNCHECKED_REACHABILITY)
    counts = {"texts": 0, "pending_texts": 0, "implementations": 0, "tests": 0}
    for index, entry in enumerate(payload.get("entries") or []):
        gid = sc.global_id(entry)
        label = f"{gid} (entries[{index}])"
        counts["texts"] += sc.verify_texts(entry, label, resolve=resolve, matches=matches, issues=issues)
        counts["pending_texts"] += sc.verify_pending_texts(
            entry, label, fetch=fetch, matches=matches, shipped=shipped, issues=issues
        )
        for i_index, item in enumerate(entry.get("implementations") or []):
            i_label = f"{label}.implementations[{i_index}]"
            shipped(i_label, item["repo"], item["commit"])
            try:
                source = fetch(item["repo"], item["commit"], item["path"]).decode("utf-8")
            except (urllib.error.URLError, OSError, UnicodeDecodeError) as exc:
                issues.append(f"{i_label}: cannot read {item['repo']}@{item['commit'][:12]}:{item['path']}: {exc}")
                continue
            found = cites(source, gid)
            if found != item["cites_entry"]:
                issues.append(
                    f"{i_label}: cites_entry is {str(item['cites_entry']).lower()} but the file "
                    f"{'carries' if found else 'does not carry'} `# {MARKER} {gid}`."
                )
            else:
                counts["implementations"] += 1
            if not item["cites_entry"]:
                report.append(f"uncited: {i_label} ({item['repo']}:{item['path']}) does not cite {gid} yet")
            variable = item.get("variable")
            if isinstance(variable, str) and item["path"].endswith(".py"):
                defined = defines_class(source, variable)
                if defined is None:
                    issues.append(f"{i_label}: {item['path']} does not parse as Python, so its `class {variable}` can't be found.")
                elif not defined:
                    issues.append(f"{i_label}: {item['path']} does not define `class {variable}` in module scope.")
            elif isinstance(variable, str):
                report.append(f"unchecked: {i_label} names {variable}, but {item['path']} is not a Python file")
        for r_index, item in enumerate(entry.get("proposed") or []):
            report.append(
                f"proposed: {label}.proposed[{r_index}] {item.get('pr')} would model it as {item.get('models')} in "
                f"{item.get('repo')}:{item.get('path')} (not counted until merged)"
            )
        counts["tests"] += sc.verify_external_tests(entry, label, fetch=fetch, shipped=shipped, issues=issues)
        for line in worklist(entry):
            report.append(f"worklist: {gid}: {line}")
    report.insert(0, "verified: " + ", ".join(f"{count} {name.replace('_', ' ')}" for name, count in counts.items()))
    return issues, report


# ---------------------------------------------------------------------------
# aggregate


def aggregate(files: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """One view of every repository's file: each file's repository and
    version (an empty file too); each entry exactly once, as it is in its
    file, with its repository, global id and worklist; and every
    statutory_not_choice item with its repository. Repositories are read in
    sorted order and entries in file order, so the view depends only on the
    files' contents."""

    repositories: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    statutory: list[dict[str, Any]] = []
    issues: list[str] = []
    seen: dict[str, str] = {}
    for repo in sorted(files):
        payload = files[repo] if isinstance(files[repo], dict) else {}
        repositories.append({"repository": repo, "version": copy.deepcopy(payload.get("version"))})
        for entry in sc._as_list(payload.get("entries")):
            if not isinstance(entry, dict):
                continue
            gid = sc.global_id(entry)
            if gid in seen:
                issues.append(f"{gid} is in both {seen[gid]} and {repo}.")
                continue
            seen[gid] = repo
            if not sc.repo_jurisdiction_ok(repo, str(entry.get("jurisdiction"))):
                issues.append(f"{repo}: {gid} has a jurisdiction outside that repository.")
            rows.append({"global_id": gid, "repository": repo, "entry": copy.deepcopy(entry), "worklist": worklist(entry)})
        for item in sc._as_list(payload.get("statutory_not_choice")):
            if isinstance(item, dict):
                statutory.append({"repository": repo, "item": copy.deepcopy(item)})
    return {"repositories": repositories, "entries": rows, "statutory_not_choice": statutory}, issues


def files_from_view(view: Mapping[str, Any]) -> dict[str, Any]:
    """The files an aggregate view was built from: the inverse of aggregate
    for files that check accepts and whose ids don't collide, empty files
    included."""

    files: dict[str, Any] = {
        row["repository"]: {"version": copy.deepcopy(row.get("version")), "entries": []}
        for row in view.get("repositories") or []
    }
    for row in view.get("entries") or []:
        files.setdefault(row["repository"], {"version": SCHEMA_VERSION, "entries": []})["entries"].append(copy.deepcopy(row["entry"]))
    for row in view.get("statutory_not_choice") or []:
        payload = files.setdefault(row["repository"], {"version": SCHEMA_VERSION, "entries": []})
        payload.setdefault("statutory_not_choice", []).append(copy.deepcopy(row["item"]))
    return files


def render_json(view: Mapping[str, Any]) -> str:
    return json.dumps(view, indent=2, sort_keys=True, default=sc._json_default) + "\n"


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(view: Mapping[str, Any]) -> str:
    rows = view.get("entries") or []
    lines = [
        "# Household choices across Axiom repositories",
        "",
        f"{len(rows)} entr{'y' if len(rows) == 1 else 'ies'}. Generated by tools/household_choices.py aggregate.",
        "",
        "| Global id | Actor | Domain | Default | Implementations | Worklist |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        entry = row["entry"]
        domain = entry.get("domain") if isinstance(entry.get("domain"), dict) else {}
        default = entry.get("default") if isinstance(entry.get("default"), dict) else {}
        implementations = "; ".join(
            f"{item.get('repo')}: {item.get('models')}" for item in sc._as_list(entry.get("implementations")) if isinstance(item, dict)
        )
        value = default.get("value")
        shown = json.dumps(value) if isinstance(value, bool) else value
        lines.append(
            f"| `{row['global_id']}` | {_cell(entry.get('actor'))} | {_cell(domain.get('kind'))} per {_cell(domain.get('per'))} "
            f"| {_cell(shown)} ({_cell(default.get('basis'))}) | {_cell(implementations)} | {_cell('; '.join(row['worklist']))} |"
        )
    statutory = view.get("statutory_not_choice") or []
    if statutory:
        lines += ["", "## Not choices", "", "| Jurisdiction | Citation | Note |", "|---|---|---|"]
        for row in statutory:
            item = row["item"]
            lines.append(f"| {_cell(item.get('jurisdiction'))} | {_cell(item.get('citation'))} | {_cell(item.get('note'))} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="offline schema and in-repo reference checks")
    check.add_argument("--root", type=Path, default=TOOLS.parent)
    check.add_argument("--repo", default=f"{sc.ORGANISATION}/rulespec-us")
    verify = sub.add_parser("verify", help="network checks: excerpts, snapshots, external refs")
    verify.add_argument("--root", type=Path, default=TOOLS.parent)
    verify.add_argument("--corpus-path", type=Path, help="axiom-corpus checkout holding the pinned release")
    verify.add_argument("--public-key", default=os.environ.get("AXIOM_CORPUS_RELEASE_PUBLIC_KEY"))
    agg = sub.add_parser("aggregate", help="collect every rulespec repository's household-choices file")
    agg.add_argument("--file", action="append", default=[], metavar="OWNER/REPO=PATH", help="use a local file instead of discovery (repeatable)")
    agg.add_argument("--json", type=Path, help="write the view as JSON")
    agg.add_argument("--markdown", type=Path, help="write a Markdown table")
    args = parser.parse_args(argv)

    if args.command == "check":
        try:
            payload = sc.load_register(args.root / CHOICES_FILENAME)
        except sc.RegisterError as exc:
            print(f"household-choices: {exc}", file=sys.stderr)
            return 1
        issues = check_choices(payload, sc.RepoContext(root=args.root, repo=args.repo))
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        entries = payload.get("entries") if isinstance(payload, dict) else None
        count = len(entries) if isinstance(entries, list) else 0
        print(
            f"{CHOICES_FILENAME}: {count} entr{'y' if count == 1 else 'ies'}, {len(issues)} issue(s). This screen "
            "does not run pinned tests; tools/pin_runner.py does."
        )
        return 1 if issues else 0

    if args.command == "verify":
        try:
            payload = sc.load_register(args.root / CHOICES_FILENAME)
        except sc.RegisterError as exc:
            print(f"household-choices: {exc}", file=sys.stderr)
            return 1
        try:
            matches = sc.encoder_matcher()
        except ImportError as exc:
            print(f"household-choices verify needs axiom-encode importable: {exc}", file=sys.stderr)
            return 2
        resolve = None
        if args.corpus_path is not None:
            if not args.public_key:
                print("household-choices verify: --public-key (or AXIOM_CORPUS_RELEASE_PUBLIC_KEY) is required with --corpus-path", file=sys.stderr)
                return 2
            release, content_sha256 = sc._toolchain_pin(args.root)
            resolve = sc.pinned_corpus_resolver(args.corpus_path, release, content_sha256, args.public_key)
        token = os.environ.get("GITHUB_TOKEN")
        issues, report = verify_choices(
            payload, fetch=sc.github_fetch(token), matches=matches, resolve=resolve,
            on_default_branch=sc.github_on_default_branch(token),
        )
        for line in report:
            print(line)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        print(f"{len(issues)} issue(s).")
        return 1 if issues else 0

    if args.file:
        files, read_issues = sc.local_registers(args.file)
    else:
        files, read_issues = sc.discover_registers(os.environ.get("GITHUB_TOKEN"), filename=CHOICES_FILENAME)
    view, issues = aggregate(files)
    issues = read_issues + issues
    if args.json:
        args.json.write_text(render_json(view))
    if args.markdown:
        args.markdown.write_text(render_markdown(view))
    if not args.json and not args.markdown:
        print(render_json(view), end="")
    for issue in issues:
        print(f"- {issue}", file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
