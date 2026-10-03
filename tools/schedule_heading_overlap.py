#!/usr/bin/env python3
"""Fail-closed check: no chapter-99 heading is charged twice for one entry.

The generated chapter compositions stack independent authority components.
A double count happens when two true membership inputs route one entry into
two terms that charge the same chapter-99 heading (HTS 7614.10.10.00 once
paid heading 9903.82.02 through both the section 232 aluminum and steel
components).  This module evaluates the generated RuleSpec directly:

* every chapter-table key, plus every HTS10 membership key and witness
  exemplar mapped to its chapter-table rate line, is classified by
  ``tools/b16_entry_flags.entry_flags``;
* the entry inputs that classification produces (membership inputs and
  the witness exemplar flags) vary by entry; declared-entry booleans and the
  chapter 99a/b resolved column-2 rate are held at fixed values;
* each ``schedule_statutory_stack`` summand, the General Note 3 base
  included, is evaluated at every version-boundary date and for every
  origin class those summands can distinguish on that date;
* every nonzero rate parameter a summand reaches is attributed to the
  chapter-99 headings any of its proof atoms cite
  (``us/statute/hts/99xx.xx.xx``), or to the parameter itself when it cites
  none, and to every mutually exclusive group (``EXCLUSIVE_GROUPS``) whose
  headings or citations its charging atoms (kind ``parameter`` or
  ``formula``) share on that date.  A table cell is charged to the table
  itself, never to the headings its rows cite.

Two nonzero charges attributed to one heading, parameter or exclusive group
for the same entry, date and origin are a double count.  Evaluation errors
(unknown inputs, a referenced rule with no version on a date, a missing cell
in a non-chapter table, unsupported syntax) fail closed; only a missing
chapter-table cell, which the engine also rejects, marks a summand
unavailable for that entry.

The evaluator covers the formula subset the generated modules use:
``if/elif/else`` (inline or parenthesized), ``and``/``or``/``not``,
comparisons, ``+``/``-``/``*``/``/``, literals, names and ``table[key]``.
Subtraction deducts without charging: in ``floor - mfn_ad_valorem_rate`` the
charge is the floor parameter's heading.

Usage:
  python tools/schedule_heading_overlap.py            # check committed chapters
  python tools/schedule_heading_overlap.py --chapters 72,76
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from b16_entry_flags import INCIDENCE_DIR, WITNESS_LINES, entry_flags  # noqa: E402

STACK_RULE = "schedule_statutory_stack"
PROCLAMATION_2026_06960 = "us/rulemaking/federal-register/2026-04-09/2026-06960"


@dataclass(frozen=True)
class ExclusiveGroup:
    """Chapter-99 charges of which one entry may bear at most one."""

    key: str
    effective_from: date
    heading_pattern: re.Pattern
    citations: frozenset[str]
    source: str


EXCLUSIVE_GROUPS = (
    ExclusiveGroup(
        key="section-232-metals",
        effective_from=date(2026, 4, 6),
        heading_pattern=re.compile(r"^9903\.8[25]\.\d\d$"),
        citations=frozenset({PROCLAMATION_2026_06960}),
        source=(
            "FR 2026-06960 clause (9): goods listed under more than one metal 'shall only be "
            "subject once' to the clause (2), (3) or (5) rates, from April 6, 2026; U.S. note "
            "16(a): headings 9903.82.02-9903.82.26 'are mutually exclusive', except as provided "
            "in 9903.82.01, 9903.85.67 and 9903.85.68"
        ),
    ),
)
UNLISTED_ORIGIN = "ZZ"
HEADING_RE = re.compile(r"^us/statute/hts/(99\d\d\.\d\d\.\d\d)$")

try:
    _LOADER = yaml.CSafeLoader
except AttributeError:  # pragma: no cover - pure-Python PyYAML
    _LOADER = yaml.SafeLoader


class CheckError(Exception):
    """The check could not evaluate a formula; the check fails closed."""


class TableKeyMissing(Exception):
    """A chapter-table cell is absent; the engine rejects the lookup too."""


# ---------------------------------------------------------------- parsing

_TOKEN_RE = re.compile(
    r"\s*(?:(?P<num>\d+(?:\.\d+)?)|(?P<str>\"[^\"]*\")"
    r"|(?P<name>[A-Za-z_][A-Za-z0-9_]*)|(?P<op><=|>=|==|!=|[-+*/<>():\[\]]))"
)
_KEYWORDS = {"if", "elif", "else", "and", "or", "not", "true", "false"}
_COMPARISONS = {"<", "<=", ">", ">=", "==", "!="}


def tokenize(text: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    position = 0
    while position < len(text):
        if not text[position:].strip():
            break
        match = _TOKEN_RE.match(text, position)
        if match is None or match.end() == position:
            raise CheckError(f"unsupported formula syntax at {text[position:position + 40]!r}")
        kind = match.lastgroup
        value = match.group(kind)
        if kind == "name" and value in _KEYWORDS:
            kind = "kw"
        tokens.append((kind, value))
        position = match.end()
    return tokens


class _Parser:
    def __init__(self, text: str) -> None:
        self.tokens = tokenize(text)
        self.index = 0

    def peek(self) -> tuple[str, str] | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def take(self, value: str | None = None) -> tuple[str, str]:
        token = self.peek()
        if token is None or (value is not None and token[1] != value):
            raise CheckError(f"expected {value!r}, got {token!r}")
        self.index += 1
        return token

    def at(self, value: str) -> bool:
        token = self.peek()
        return token is not None and token[1] == value and token[0] in {"kw", "op"}

    def parse(self) -> tuple:
        node = self.expression()
        if self.peek() is not None:
            raise CheckError(f"trailing tokens from {self.peek()!r}")
        return node

    def expression(self) -> tuple:
        if self.at("if"):
            self.take("if")
            branches = []
            condition = self.expression()
            self.take(":")
            branches.append((condition, self.expression()))
            while self.at("elif"):
                self.take("elif")
                condition = self.expression()
                self.take(":")
                branches.append((condition, self.expression()))
            self.take("else")
            self.take(":")
            return ("if", tuple(branches), self.expression())
        return self.disjunction()

    def disjunction(self) -> tuple:
        node = self.conjunction()
        while self.at("or"):
            self.take("or")
            node = ("or", node, self.conjunction())
        return node

    def conjunction(self) -> tuple:
        node = self.negation()
        while self.at("and"):
            self.take("and")
            node = ("and", node, self.negation())
        return node

    def negation(self) -> tuple:
        if self.at("not"):
            self.take("not")
            return ("not", self.negation())
        return self.comparison()

    def comparison(self) -> tuple:
        node = self.additive()
        token = self.peek()
        if token is not None and token[0] == "op" and token[1] in _COMPARISONS:
            self.take()
            node = ("cmp", token[1], node, self.additive())
        return node

    def additive(self) -> tuple:
        node = self.multiplicative()
        while self.at("+") or self.at("-"):
            operator = self.take()[1]
            node = (operator, node, self.multiplicative())
        return node

    def multiplicative(self) -> tuple:
        node = self.unary()
        while self.at("*") or self.at("/"):
            operator = self.take()[1]
            node = (operator, node, self.unary())
        return node

    def unary(self) -> tuple:
        if self.at("-"):
            self.take("-")
            return ("neg", self.unary())
        return self.postfix()

    def postfix(self) -> tuple:
        node = self.atom()
        if self.at("["):
            if node[0] != "name":
                raise CheckError("only named tables may be indexed")
            self.take("[")
            key = self.expression()
            self.take("]")
            node = ("index", node[1], key)
        return node

    def atom(self) -> tuple:
        kind, value = self.take()
        if kind == "num":
            return ("lit", Decimal(value))
        if kind == "str":
            return ("lit", value[1:-1])
        if kind == "kw" and value in {"true", "false"}:
            return ("lit", value == "true")
        if kind == "name":
            return ("name", value)
        if value == "(":
            node = self.expression()
            self.take(")")
            return node
        raise CheckError(f"unexpected token {value!r}")


def parse_formula(text: str) -> tuple:
    return _Parser(text).parse()


def _names(node: tuple) -> set[str]:
    kind = node[0]
    if kind == "name":
        return {node[1]}
    if kind == "index":
        return {node[1]} | _names(node[2])
    if kind == "lit":
        return set()
    if kind == "if":
        found: set[str] = set()
        for condition, branch in node[1]:
            found |= _names(condition) | _names(branch)
        return found | _names(node[2])
    return set().union(*(_names(child) for child in node[1:] if isinstance(child, tuple)))


def _rename(node: tuple, mapping) -> tuple:
    kind = node[0]
    if kind == "name":
        return ("name", mapping(node[1]))
    if kind == "index":
        return ("index", mapping(node[1]), _rename(node[2], mapping))
    if kind == "lit":
        return node
    if kind == "if":
        return (
            "if",
            tuple((_rename(c, mapping), _rename(b, mapping)) for c, b in node[1]),
            _rename(node[2], mapping),
        )
    return (kind, *(_rename(child, mapping) if isinstance(child, tuple) else child for child in node[1:]))


# ---------------------------------------------------------------- rules


def _as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _as_decimal(value):
    if isinstance(value, bool) or isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(repr(value))
    return value


@dataclass
class Version:
    start: date
    end: date | None
    ast: tuple | None
    values: dict | None


@dataclass
class Rule:
    name: str
    kind: str
    headings: frozenset[str]
    charging_citations: frozenset[str]
    versions: list[Version]
    canonical: str = ""

    def version_at(self, day: date) -> Version | None:
        for version in self.versions:
            if version.start <= day and (version.end is None or day <= version.end):
                return version
        return None


CHARGING_ATOM_KINDS = frozenset({"parameter", "formula"})


def _citations(rule: dict, kinds: frozenset[str] | None = None) -> frozenset[str]:
    return frozenset(
        path
        for atom in ((rule.get("metadata") or {}).get("proof") or {}).get("atoms") or []
        if (kinds is None or (atom or {}).get("kind") in kinds)
        and (path := ((atom or {}).get("source") or {}).get("corpus_citation_path"))
    )


def _headings(citations: frozenset[str]) -> frozenset[str]:
    return frozenset(match.group(1) for path in citations if (match := HEADING_RE.match(path)))


def build_rule(raw: dict) -> Rule:
    versions = []
    for version in raw.get("versions") or []:
        start = _as_date(version.get("effective_from", version.get("from")))
        end = _as_date(version.get("effective_to", version.get("to")))
        if start is None:
            raise CheckError(f"{raw['name']} has a version without a start date")
        if "values" in version:
            values = {key: _as_decimal(value) for key, value in (version["values"] or {}).items()}
            versions.append(Version(start, end, None, values))
        else:
            formula = version.get("formula")
            if not isinstance(formula, str):
                raise CheckError(f"{raw['name']} has a version without a formula")
            versions.append(Version(start, end, parse_formula(formula), None))
    return Rule(
        raw["name"], raw.get("kind", ""), _headings(_citations(raw)),
        _citations(raw, CHARGING_ATOM_KINDS), versions,
    )


_MODULE_CACHE: dict[Path, dict] = {}


def load_yaml(path: Path) -> dict:
    if path not in _MODULE_CACHE:
        _MODULE_CACHE[path] = yaml.load(path.read_bytes(), Loader=_LOADER)
    return _MODULE_CACHE[path]


def import_path(target: str, repo_root: Path) -> Path:
    if not target.startswith("us:"):
        raise CheckError(f"unsupported import {target!r}")
    return repo_root / "us" / (target.removeprefix("us:") + ".yaml")


# ---------------------------------------------------------------- scope


class Scope:
    """One chapter module plus its imports, with canonical rule identities."""

    def __init__(self, chapter: str, module: dict, repo_root: Path) -> None:
        self.chapter = chapter
        self.rules: dict[str, Rule] = {}
        for raw in module["rules"]:
            self.rules[raw["name"]] = build_rule(raw)
        for target in module.get("imports") or []:
            for raw in load_yaml(import_path(target, repo_root)).get("rules") or []:
                if raw["name"] in self.rules:
                    raise CheckError(f"ch{chapter}: {raw['name']} defined twice in scope")
                self.rules[raw["name"]] = build_rule(raw)
        prefix = f"ch{chapter}_"
        for rule in self.rules.values():
            # Chapter-instance names (tables, prefixed scalar copies) share a
            # canonical spelling across chapters; table values stay in the
            # closure signature, so only identical closures share results.
            rule.canonical = "chNN_" + rule.name[len(prefix):] if rule.name.startswith(prefix) else rule.name
        stack = self.rules.get(STACK_RULE)
        if stack is None or len(stack.versions) != 1 or stack.versions[0].ast is None:
            raise CheckError(f"ch{chapter}: {STACK_RULE} must have one formula version")
        self.summands = self._summands(stack.versions[0].ast)
        self.stack_start = stack.versions[0].start
        self._signature: dict[str, str] = {}
        self.by_canonical = {rule.canonical: rule.name for rule in self.rules.values()}

    @staticmethod
    def _summands(node: tuple) -> list[str]:
        if node[0] == "+":
            return Scope._summands(node[1]) + Scope._summands(node[2])
        if node[0] != "name":
            raise CheckError(f"{STACK_RULE} must be a sum of rule names")
        return [node[1]]

    def closure(self, name: str, day: date | None = None) -> set[str]:
        """Rules reachable from name (on one day, or across all versions)."""
        seen: set[str] = set()
        queue = [name]
        while queue:
            current = queue.pop()
            if current in seen or current not in self.rules:
                continue
            seen.add(current)
            rule = self.rules[current]
            versions = rule.versions if day is None else [v for v in [rule.version_at(day)] if v]
            for version in versions:
                if version.ast is not None:
                    queue.extend(_names(version.ast))
        return seen

    def signature(self, name: str) -> str:
        """Hash of the canonical closure; equal hashes evaluate identically."""
        if name not in self._signature:
            parts = []
            for rule_name in sorted(self.closure(name), key=lambda item: self.rules[item].canonical):
                rule = self.rules[rule_name]
                rename = lambda item: self.rules[item].canonical if item in self.rules else item  # noqa: E731
                versions = []
                for version in rule.versions:
                    body = (
                        repr(_rename(version.ast, rename))
                        if version.ast is not None
                        else hashlib.sha256(repr(sorted(version.values.items())).encode()).hexdigest()
                    )
                    versions.append((str(version.start), str(version.end), body))
                parts.append((rule.canonical, rule.kind, sorted(rule.headings), versions))
            self._signature[name] = hashlib.sha256(repr(parts).encode()).hexdigest()
        return self._signature[name]

    def boundaries(self, names: list[str]) -> list[date]:
        days = {self.stack_start}
        for name in set().union(*(self.closure(item) for item in names)):
            for version in self.rules[name].versions:
                days.add(version.start)
                if version.end is not None:
                    days.add(version.end + timedelta(days=1))
        return sorted(day for day in days if day >= self.stack_start)

    def country_literals(self) -> set[str]:
        found = set()
        for rule in self.rules.values():
            for version in rule.versions:
                if version.ast is not None:
                    found.update(_country_literals(version.ast))
        return found


def _country_literals(node: tuple) -> set[str]:
    if node[0] == "cmp":
        sides = (node[2], node[3])
        if any(side == ("name", "country_of_origin") for side in sides):
            return {side[1] for side in sides if side[0] == "lit" and isinstance(side[1], str)}
    found: set[str] = set()
    if node[0] == "if":
        for condition, branch in node[1]:
            found |= _country_literals(condition) | _country_literals(branch)
        return found | _country_literals(node[2])
    for child in node[1:]:
        if isinstance(child, tuple):
            found |= _country_literals(child)
    return found


# ---------------------------------------------------------------- evaluation


class Context:
    """One entry, date and origin; memoizes rule values with their reads."""

    def __init__(self, scope: Scope, day: date, inputs: dict) -> None:
        self.scope = scope
        self.day = day
        self.inputs = inputs
        self.memo: dict[str, tuple] = {}

    def rule(self, name: str, reads: set[str]) -> tuple:
        if name in self.memo:
            value, charges, rule_reads = self.memo[name]
            reads |= rule_reads
            return value, charges
        rule = self.scope.rules.get(name)
        if rule is None:
            if name not in self.inputs:
                raise CheckError(f"ch{self.scope.chapter}: unmodelled input {name!r}")
            reads.add(name)
            return self.inputs[name], ()
        version = rule.version_at(self.day)
        if version is None:
            raise CheckError(f"ch{self.scope.chapter}: {name} has no version on {self.day}")
        if version.ast is None:
            raise CheckError(f"ch{self.scope.chapter}: table {name} used without an index")
        rule_reads: set[str] = set()
        try:
            value, charges = self.node(version.ast, rule_reads)
        finally:
            # A missing table cell must not hide what this rule read: the
            # caller caches its outcome keyed by these reads.
            reads |= rule_reads
        if rule.kind == "parameter":
            charges = ((rule.canonical, rule.headings, rule.charging_citations, value),)
        self.memo[name] = (value, charges, frozenset(rule_reads))
        return value, charges

    def node(self, node: tuple, reads: set[str]) -> tuple:
        kind = node[0]
        if kind == "lit":
            return node[1], ()
        if kind == "name":
            return self.rule(node[1], reads)
        if kind == "index":
            table = self.scope.rules.get(node[1])
            version = table.version_at(self.day) if table else None
            if version is None or version.values is None:
                raise CheckError(f"ch{self.scope.chapter}: {node[1]} is not a table on {self.day}")
            key, _ = self.node(node[2], reads)
            key = int(key)
            if key not in version.values:
                if table.canonical.startswith("chNN_"):
                    raise TableKeyMissing(f"{node[1]}[{key}]")
                raise CheckError(f"ch{self.scope.chapter}: {node[1]}[{key}] is missing")
            value = version.values[key]
            # A table is one charge identity; its per-row citations do not
            # make every cell charge every heading the table cites.
            return value, ((table.canonical, frozenset(), frozenset(), value),)
        if kind == "if":
            for condition, branch in node[1]:
                if self._truth(condition, reads):
                    return self.node(branch, reads)
            return self.node(node[2], reads)
        if kind == "and":
            return (self._truth(node[1], reads) and self._truth(node[2], reads)), ()
        if kind == "or":
            return (self._truth(node[1], reads) or self._truth(node[2], reads)), ()
        if kind == "not":
            return (not self._truth(node[1], reads)), ()
        if kind == "cmp":
            left, _ = self.node(node[2], reads)
            right, _ = self.node(node[3], reads)
            operator = node[1]
            if operator == "==":
                return left == right, ()
            if operator == "!=":
                return left != right, ()
            left, right = self._number(left), self._number(right)
            return {"<": left < right, "<=": left <= right, ">": left > right, ">=": left >= right}[operator], ()
        if kind == "neg":
            value, charges = self.node(node[1], reads)
            return -self._number(value), charges
        left, left_charges = self.node(node[1], reads)
        right, right_charges = self.node(node[2], reads)
        left, right = self._number(left), self._number(right)
        if kind == "+":
            return left + right, left_charges + right_charges
        if kind == "-":
            return left - right, left_charges
        if kind == "*":
            return left * right, left_charges + right_charges
        if kind == "/":
            return left / right, left_charges + right_charges
        raise CheckError(f"unsupported node {kind!r}")

    def _truth(self, node: tuple, reads: set[str]) -> bool:
        value, _ = self.node(node, reads)
        if not isinstance(value, bool):
            raise CheckError(f"ch{self.scope.chapter}: non-boolean condition {node!r}")
        return value

    def _number(self, value) -> Decimal:
        if isinstance(value, bool) or not isinstance(value, Decimal):
            raise CheckError(f"ch{self.scope.chapter}: non-numeric operand {value!r}")
        return value


def nonzero_charges(charges: tuple) -> tuple:
    return tuple(
        (name, headings, citations) for name, headings, citations, value in charges if value != 0
    )


def charge_keys(name: str, headings: frozenset[str], citations: frozenset[str], day: date) -> frozenset[str]:
    keys = set(headings) or {f"parameter:{name}"}
    for group in EXCLUSIVE_GROUPS:
        if day >= group.effective_from and (
            any(group.heading_pattern.match(heading) for heading in headings)
            or group.citations & citations
        ):
            keys.add(f"group:{group.key}")
    return frozenset(keys)


# ---------------------------------------------------------------- check


@dataclass
class Collision:
    chapter: str
    hts_number: str
    rate_line: int
    day: date
    origin: str
    heading: str
    charges: list

    def __str__(self) -> str:
        detail = "; ".join(f"{summand} via {name}" for summand, name in self.charges)
        return (
            f"ch{self.chapter} {self.hts_number} (rate line {self.rate_line}) {self.day} origin "
            f"{self.origin}: {self.heading} charged {len(self.charges)} times ({detail})"
        )


@dataclass
class Report:
    chapters: int = 0
    entries: int = 0
    contexts: int = 0
    evaluations: int = 0
    unavailable: int = 0
    collisions: list[Collision] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"{self.chapters} chapters, {self.entries} entries, {self.contexts} entry-date-origin "
            f"contexts, {self.evaluations} summand evaluations, {self.unavailable} unavailable "
            f"summand cells, {len(self.collisions)} double-charged headings"
        )


def dotted(digits: int) -> str:
    text = f"{digits:010d}"
    return f"{text[:4]}.{text[4:6]}.{text[6:8]}.{text[8:]}"


def chapter_entries(table_keys: dict[str, set[int]]) -> dict[str, list[tuple[int, str]]]:
    """Every chapter-table key, plus HTS10 membership keys and witness lines
    mapped onto the chapter-table rate line that carries them."""
    owner = {key: chapter for chapter, keys in table_keys.items() for key in keys}
    entries = {chapter: {(key, dotted(key)) for key in keys} for chapter, keys in table_keys.items()}
    extra = {int(digits) for digits in WITNESS_LINES.values()}
    for path in sorted(INCIDENCE_DIR.glob("*.yaml")):
        if path.name.endswith(".test.yaml"):
            continue
        for rule in load_yaml(path).get("rules") or []:
            if rule["name"].endswith("_membership_hts10"):
                for version in rule.get("versions") or []:
                    extra.update(int(key) for key in version.get("values") or {})
    for key in sorted(extra):
        rate_line = key if key in owner else (key // 100) * 100
        if rate_line in owner:
            entries[owner[rate_line]].add((rate_line, dotted(key)))
    return {chapter: sorted(items) for chapter, items in entries.items()}


def origin_classes(
    scope: Scope, summands: list[str], day: date, countries: list[str], inputs: dict, fixed: set[str]
) -> list[str]:
    """Representative origins for the origin distinctions reachable on day.

    Origin probes are evaluated with inputs; one that reads anything beyond
    the fixed inputs and the country could split differently per entry, so
    the check fails closed rather than merge those origins.
    """
    reachable = set().union(*(scope.closure(name, day) for name in summands))
    probes = []
    for name in sorted(reachable):
        version = scope.rules[name].version_at(day)
        if version is None or version.ast is None or "country_of_origin" not in _names(version.ast):
            continue
        probes.append(name)
    seen: dict[tuple, str] = {}
    for country in countries:
        context = Context(scope, day, {**inputs, "country_of_origin": country})
        values = []
        for name in probes:
            reads: set[str] = set()
            value, _ = context.rule(name, reads)
            if not reads <= fixed | {"country_of_origin"}:
                raise CheckError(f"ch{scope.chapter}: origin rule {name} reads entry inputs {sorted(reads - fixed)}")
            values.append(value)
        seen.setdefault(tuple(values), country)
    return sorted(seen.values())


ENTRY_SPECIFIC_INPUTS = frozenset({"hts_line", "hts_number"})


def _evaluate_context(
    scope: Scope,
    summands: list[str],
    signatures: dict[str, str],
    day: date,
    origin: str,
    entry_inputs: dict,
    shared: dict,
    report: Report,
) -> tuple[dict[str, list], bool]:
    """Charges by heading for one entry context, and whether any summand
    result depended on the entry's own HTS number or rate line."""
    context = None
    by_key: dict[str, list] = {}
    entry_specific = False
    for summand in summands:
        slot = shared.setdefault((signatures[summand], day, origin), [])
        result = None
        for read_names, table in slot:
            result = table.get(tuple(entry_inputs[name] for name in read_names))
            if result is not None:
                break
        if result is None:
            if context is None:
                context = Context(scope, day, entry_inputs)
            reads: set[str] = set()
            try:
                _, charges = context.rule(summand, reads)
                result = ("ok", nonzero_charges(charges))
            except TableKeyMissing:
                result = ("unavailable", ())
            read_names = tuple(sorted(reads))
            for known_names, table in slot:
                if known_names == read_names:
                    break
            else:
                table = {}
                slot.append((read_names, table))
            table[tuple(entry_inputs[name] for name in read_names)] = result
            report.evaluations += 1
        if not ENTRY_SPECIFIC_INPUTS.isdisjoint(read_names):
            entry_specific = True
        status, charges = result
        if status == "unavailable":
            report.unavailable += 1
            continue
        for name, headings, citations in charges:
            for key in charge_keys(name, headings, citations, day):
                by_key.setdefault(key, []).append((summand, scope.by_canonical.get(name, name)))
    return by_key, entry_specific


def check_chapters(
    modules: dict[str, dict],
    table_keys: dict[str, set[int]],
    *,
    entry_inputs: tuple[str, ...],
    fixed_inputs: dict,
    repo_root: Path = REPO_ROOT,
) -> Report:
    """Evaluate every entry of every chapter; return all double charges.

    entry_inputs are the b16 entry-preparation flags fed per entry; every
    other caller input comes from fixed_inputs.  Entries with the same flag
    vector share one evaluation per date and origin unless a summand result
    read the entry's HTS number or rate line, in which case each entry is
    evaluated on its own.
    """
    report = Report()
    fixed = {name: _as_decimal(value) for name, value in fixed_inputs.items()}
    entries = chapter_entries(table_keys)
    shared: dict[tuple, list] = {}
    for chapter in sorted(modules):
        scope = Scope(chapter, modules[chapter], repo_root)
        summands = scope.summands
        days = scope.boundaries(summands)
        countries = sorted(scope.country_literals() | {UNLISTED_ORIGIN})
        defaults = {**fixed, **{name: False for name in entry_inputs}}
        classes = {day: origin_classes(scope, summands, day, countries, defaults, set(fixed)) for day in days}
        signatures = {name: scope.signature(name) for name in summands}
        report.chapters += 1
        groups: dict[tuple, list[tuple[int, str]]] = {}
        for rate_line, hts_number in entries.get(chapter, []):
            flags = entry_flags(rate_line, hts_number, UNLISTED_ORIGIN)
            vector = tuple(bool(flags[name]) for name in entry_inputs)
            groups.setdefault(vector, []).append((rate_line, hts_number))
        for vector, members in groups.items():
            report.entries += len(members)
            base_inputs = {**fixed, **dict(zip(entry_inputs, vector))}
            for day in days:
                for origin in classes[day]:
                    def run(rate_line: int, hts_number: str):
                        return _evaluate_context(
                            scope, summands, signatures, day, origin,
                            {**base_inputs, "hts_line": rate_line, "hts_number": hts_number,
                             "country_of_origin": origin},
                            shared, report,
                        )

                    by_key, entry_specific = run(*members[0])
                    outcomes = [(members[0], by_key)]
                    if entry_specific:
                        outcomes += [(member, run(*member)[0]) for member in members[1:]]
                    else:
                        outcomes += [(member, by_key) for member in members[1:]]
                    report.contexts += len(members)
                    for (rate_line, hts_number), charged_by_key in outcomes:
                        for key, charged in sorted(charged_by_key.items()):
                            if len(charged) > 1:
                                report.collisions.append(
                                    Collision(chapter, hts_number, rate_line, day, origin, key, charged)
                                )
    return report


# ---------------------------------------------------------------- CLI


def committed_inputs(chapters: list[str] | None = None) -> tuple[dict, dict]:
    """Committed generated modules and chapter-table keysets."""
    import generate_schedule_compositions as generator

    manifest = generator.load_table_manifest()
    available = generator.available_chapters(manifest)
    selected = sorted(available) if not chapters else chapters
    modules = {}
    table_keys = {}
    for chapter in selected:
        path = generator.COMPOSITION_DIR / f"ch{chapter}" / f"ch{chapter}.yaml"
        modules[chapter] = yaml.load(path.read_bytes(), Loader=_LOADER)
        table = load_yaml(generator.TABLE_DIR / f"ch{chapter}.yaml")
        dispositions = next(
            rule for rule in table["rules"] if rule["name"] == f"ch{chapter}_general_disposition"
        )
        table_keys[chapter] = set(dispositions["versions"][0]["values"])
    return modules, table_keys


def generator_inputs() -> dict:
    import generate_schedule_compositions as generator

    return {
        "entry_inputs": generator.HEADING_CHECK_ENTRY_INPUTS,
        "fixed_inputs": generator.heading_check_fixed_inputs(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--chapters", default="", help="comma-separated shard ids (default: all)")
    args = parser.parse_args()
    chapters = [item.strip() for item in args.chapters.split(",") if item.strip()] or None
    modules, table_keys = committed_inputs(chapters)
    import generate_schedule_compositions as generator

    report = check_chapters(modules, table_keys, **generator_inputs())
    unexpected, stale = generator.split_known_double_charges(report, set(modules))
    for collision in report.collisions[:50]:
        known = (collision.chapter, collision.hts_number, collision.heading)
        entry = generator.KNOWN_DOUBLE_CHARGES.get(known)
        note = f"  [known: {entry['reason']}]" if entry and collision not in unexpected else ""
        print(f"{collision}{note}")
    for key in stale:
        print(f"stale KNOWN_DOUBLE_CHARGES entry: {key}")
    print(report.summary())
    return 1 if unexpected or stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
