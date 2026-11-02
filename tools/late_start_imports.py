#!/usr/bin/env python3
"""Ratchet the dates on which a rule reads an import that has no version.

A late-start import edge is a run of dates on which a version of a rule applies,
that version reads a rule or parameter from another module, and that name has
no version. Issue #1971 names the common shape: the import starts after the rule
version does. A gap between two of the import's versions, or an import that ends
before the rule version does, stops the engine the same way. On any date in the
run the engine picks the rule version and then stops on the import, with
`derived ... has no formula version at ...` or a missing parameter value.
Compilation lowers formulas without looking at dates, so a clean compile does
not rule the gap out, and only a query that reaches the import shows it. That is
how 26 USC 6012 stopped on 26 USC 7703. The encoder's
`temporal-dependency-coverage` validator covers references inside one file and
deliberately stops at imports; this check starts there.

The check is static, so it also covers the modules the pinned engine does not
load, 26 USC 6012 among them, and needs no engine build. It follows
axiom-rules-engine at the pin in `.axiom/workflow-toolchain.toml`:

* Scope. The engine merges every imported module into one namespace, and
  follows those modules' imports too. The engine validates a `#fragment` and
  then drops it, so it does not narrow what a formula sees, and a stored
  composition may not write one. A formula name therefore resolves against the whole import closure.
* Scalars. Modules load the way the engine's serde_yaml reads them, not the way
  PyYAML does. Where the engine reads a string, an unquoted scalar keeps its
  text, so `name: TRUE` names a rule `TRUE`. Where it reads a value, `yes` stays
  a string, and so does an unquoted date. A date must read YYYY-MM-DD. The check
  refuses a module that writes out a tag, `!!merge` among them, rather than
  guess how serde_yaml would read it.
* References. Formula identifiers come from a port of the engine's lexer, so a
  word in a string or comment is not a reference, nor is a called function. The
  engine lexes every rule's formula as one source, so a formula that leaves a
  string open would run into the next rule; the check refuses that module. The
  first argument of `len`, `count_where` or `sum_where` names a relation, and so
  does the object of a field access; neither reads a rule. Only `parameter` and
  `derived` rules carry versions the engine enforces at run time. A derived
  relation carries none, but the engine evaluates its predicate on each date a
  version asks for the relation, so the version reads what the predicate reads,
  as derived rules.
* Namespaces. `kind` does not decide what a name binds to. A rule with `values`
  in any version is a parameter table, of either kind, and its versions without
  `values` do not exist at run time. Otherwise a rule with an `entity`, or with
  a version that is not a lone literal, is derived; the rest are parameters.
  The parser erases parentheses, so `(2)` is a literal, and a leading `-` is an
  operator, so `-2` is not. Parameters of one name merge, and a table of that
  name removes the others.
* Binding. A name in a scalar position binds to a parameter before a derived
  rule, and one in a judgment position binds only to a derived rule. Telling
  most positions apart takes a parser, so a name defined both ways reads both,
  and a parameter read in a judgment position, which lowers to an input, still
  counts. Three positions read derived rules only, which a token can tell: a
  later argument of a relation call, a field, and `period_start` or
  `period_end`. So the check can list a (rule, target) pair that no position
  reaches; `differential` prints each case.
* Provenance. A binding crosses an import when any imported definition feeds
  it. Parameters merge, so a local definition beside an imported one does not
  make the merged name local. The merged name holds every version of each, so
  a local version that ends before an imported one starts leaves a gap.
* Dates. `from` and `to` are aliases of `effective_from` and `effective_to`, and
  a rule with no `versions` may state one version at the top level. A version
  applies from its start through its end, and on each date the engine picks, of
  the versions that apply, the one that starts last. A rule version reads its
  names only on the dates the engine picks it.

A `source_relation` of type `sets` gives a target the versions of a value, in
each root whose lowered program holds both. The check builds that program for
each root. Every entry of a name takes the id of the last rule of that name, of
any kind, that carries one, and the rules of a composition compiled as the root
carry none. Then each relation, in rule order, resolves its target and its
value to the first parameter that carries the id, or else the first derived
rule, and copies the value's versions onto that one target entry. The engine
refuses a root where only one side resolves or the two sides differ in kind,
and the check reads nothing from that root. A formula that reads
the target then meets the value's versions, and the edge names the value.

The check reads each module's own rules under that module's own root. Under a
root that imports the module, the same rules can bind differently: a
composition can supply a name the module never imports, and a `sets` relation
in that root can replace the versions of a name they read. Those bindings are
not the module's import edges, and this check does not gate them.

An edge means a version can read the gap, not that every query does: a formula
may never take the branch that holds the name. The comparison is per version,
not per rule. When a later version of a rule adds a reference to an import that
starts with it, that version cannot read a gap; that shape is the correct way
to encode the change and it is not an edge. Each edge is one run of stop dates
for a (rule, target), merged across the rule's versions and namespaces, given by
its first date and the date the target next has a version.

`differential` checks the static model against the engine, because a static
reimplementation drifts from the engine it describes. It compiles each module,
stored compositions through their own surface, and reads every name the lowered
program binds in the rules that module declares, following each derived
relation a version asks for into its predicate. Those bindings must equal the
static ones by rule, version dates, name, namespace and every version of what
the name binds to. For each name a module declares, the namespaces and versions
the lowered program holds must also equal the static model's, both ways. The
engine reattaches ids by name, so it cannot say which module a colliding name
came from; the static model alone decides whether a binding crosses an import.
The run must also cover the tree: every module needs a result, and every edge a
compiled module. It compiles a scratch copy of the tree with citation metadata
removed: that metadata decides nothing here, and retired forms of it would
otherwise stop the engine from loading most of the references this check exists
to compare.

`tools/known-late-start-imports.txt` lists the edges the repository already
carries, one per line, as
`<rule id>\\t<target id>\\t<first date>\\t<date the target next has a version>`,
tab separated, with `never` when it has none. `check` passes only when the edges
equal that list exactly: an unlisted edge is red, and a listed edge that no
longer holds, or whose dates moved, is red until its line changes in the same
pull request. Against a protected base, a pull request may not add a stop date
to any (rule, name), because regenerating the list would otherwise accept any
edge. The check computes the base's stop dates from the base commit's own
modules, not from its list, and compares by the name a formula reads, so a
repair that moves which module supplies a name can narrow a gap without a
label. A correct date repair can still widen one: it can expose a gap that was
already in the law's encoding, and fail closed where the module used to answer
wrongly. The `late-start-import-accepted` label on the pull request
(`--allow-added`) records that decision.

Subcommands:
  check         compare this checkout's edges with the baseline (the CI gate)
  baseline      print the baseline that exactly matches this checkout
  differential  compare the static references with the pinned engine's

Local use:

  python tools/late_start_imports.py check --base-ref origin/main
  python tools/late_start_imports.py baseline > tools/known-late-start-imports.txt
  python tools/late_start_imports.py differential --engine-src ../axiom-rules-engine \\
      --output /tmp/late-start-differential.jsonl
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from engine_root_load import (  # noqa: E402 - beside this file
    canonical_target,
    select_modules,
    tracked_modules,
)

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

REPO_ROOT = TOOLS.parent
BASELINE_RELATIVE_PATH = Path("tools") / "known-late-start-imports.txt"
HARNESS_EXAMPLE_NAME = "rulespec_import_references"
ACCEPT_LABEL = "late-start-import-accepted"

# Dropped from the scratch tree `differential` compiles. None of these fields
# reaches formula lowering; the engine's corpus contract reads them.
CITATION_KEYS = frozenset({"corpus_citation_path", "corpus_citation_paths", "metadata"})

# The rule kinds the engine lowers to dated program entries (RuleKind::Parameter
# and RuleKind::Derived).
VERSIONED_KINDS = frozenset({"parameter", "derived"})

# The two namespaces a lowered formula reads, whatever a rule's `kind` says.
PARAMETER = "parameter"
DERIVED = "derived"
BOTH = frozenset({PARAMETER, DERIVED})
DERIVED_ONLY = frozenset({DERIVED})

# An effective_to the engine leaves open.
OPEN = date.max

# `differential` refuses a run that compiled less of the tree than this. The
# pinned engine compiled 4,864 of 4,879 modules when this was set.
MINIMUM_COMPILED_SHARE = 0.99

# Keywords. The lexer turns `true` and friends into keyword tokens, so they never
# name a rule.
RESERVED = frozenset(
    {
        "entity",
        "amend",
        "from",
        "to",
        "match",
        "if",
        "elif",
        "else",
        "and",
        "or",
        "not",
        "true",
        "True",
        "false",
        "False",
    }
)

# formula.rs lower_to_scalar reads these as the period's bounds before any rule,
# and lower_to_judgment reads a derived rule of the name first.
PERIOD_BOUNDS = frozenset({"period_start", "period_end"})

# formula.rs lower_to_scalar: the first argument of these calls names a
# relation, and a later argument that is one name reads a derived rule or an
# input, never a parameter.
RELATION_CALLS = frozenset({"len", "count_where", "sum_where"})

BOOLEANS = frozenset({"true", "True", "false", "False"})

# axiom-rules-engine formula.rs Lexer::tokenise, in its order. `skip` yields no
# token, so a word inside it is never a name. A name holding a slash is the
# lexer's Path token: `a/b` is one name, not a division, and a rule may carry it.
# A docstring is skipped too, and runs to the end when nothing closes it; `open`
# is a quote the formula never closes.
TOKEN = re.compile(
    r'''
      (?P<skip>\s+|\#[^\n]*)
    | (?P<docstring>""".*?(?:"""|\Z))
    | (?P<date>\d{4}-\d{2}-\d{2})
    | (?P<literal>\d[\d_]*(?:\.\d[\d_]*)?|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
    | (?P<name>[A-Za-z_][A-Za-z0-9_]*(?:/[A-Za-z_][A-Za-z0-9_]*)*)
    | (?P<open>["'])
    | (?P<other>.)
    ''',
    re.VERBOSE | re.DOTALL,
)

# chrono's NaiveDate parser takes more spellings than this; the check refuses
# them rather than guess.
DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")

# serde_yaml de.rs visit_untagged_scalar, for the scalars it does not keep as a
# string. Rust's integer and float parsers take no `_` and no whitespace.
_NULLS = frozenset({"", "~", "null", "Null", "NULL"})
_TRUES = frozenset({"true", "True", "TRUE"})
_FALSES = frozenset({"false", "False", "FALSE"})
_LEADING_ZERO = re.compile(r"[+-]?0[0-9]+\Z")
_INTEGER = re.compile(r"[+-]?(?:0x[0-9A-Fa-f]+|0o[0-7]+|0b[01]+|[0-9]+)\Z")
_FLOAT = re.compile(r"[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")
_SPECIAL_FLOATS = {
    ".inf": math.inf,
    ".Inf": math.inf,
    ".INF": math.inf,
    "+.inf": math.inf,
    "+.Inf": math.inf,
    "+.INF": math.inf,
    "-.inf": -math.inf,
    "-.Inf": -math.inf,
    "-.INF": -math.inf,
    ".nan": math.nan,
    ".NaN": math.nan,
    ".NAN": math.nan,
}


def plain_scalar(text: str) -> Any:
    """An unquoted YAML scalar as serde_yaml resolves it into a `Value`. YAML 1.2
    has no `yes` and no date type, and digits after a leading zero stay a string."""
    if text in _NULLS:
        return None
    if text in _TRUES:
        return True
    if text in _FALSES:
        return False
    if _LEADING_ZERO.match(text):
        return str(text)
    if _INTEGER.match(text):
        return int(text, 0)
    if text in _SPECIAL_FLOATS:
        return _SPECIAL_FLOATS[text]
    if _FLOAT.match(text) and math.isfinite(float(text)):
        return float(text)
    return str(text)


def number_text(value: float) -> str:
    """serde_yaml Number's Display for a float: ryu's shortest digits, laid out
    the way ryu's `format_finite` lays them out, with `.inf` and `.nan` spelled
    as YAML spells them."""
    if math.isnan(value):
        return ".nan"
    if math.isinf(value):
        return "-.inf" if value < 0 else ".inf"
    sign = "-" if math.copysign(1.0, value) < 0 else ""
    if value == 0:
        return f"{sign}0.0"
    _, digit_tuple, exponent = Decimal(repr(abs(value))).normalize().as_tuple()
    digits = "".join(map(str, digit_tuple))
    length = len(digits)
    point = length + exponent
    if 0 <= exponent and point <= 16:
        return f"{sign}{digits}{'0' * exponent}.0"
    if 0 < point <= 16:
        return f"{sign}{digits[:point]}.{digits[point:]}"
    if -5 < point <= 0:
        return f"{sign}0.{'0' * -point}{digits}"
    mantissa = digits if length == 1 else f"{digits[0]}.{digits[1:]}"
    return f"{sign}{mantissa}e{point - 1}"


class Plain(str):
    """The text of an unquoted scalar. serde_yaml hands a `String` field this text
    as written, so `name: TRUE` names a rule `TRUE`; `value` is what it resolves
    to where the engine reads a `Value`."""

    __slots__ = ()

    @property
    def value(self) -> Any:
        return plain_scalar(self)


def scalar_value(item: Any) -> Any:
    """What serde_yaml reads into a `Value`: an unquoted scalar resolved, and
    anything else as it is."""
    return item.value if isinstance(item, Plain) else item


def string_like(item: Any) -> str | None:
    """rulespec.rs deserialize_optional_string_like: a number or boolean reaches
    the engine as its text, so `-5` lexes as an operator and a 5."""
    value = scalar_value(item)
    if value is None or isinstance(value, str):
        return None if value is None else str(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return number_text(value)
    raise ValueError(f"expected a scalar, got {type(value).__name__}")


_MODELED_TAGS = frozenset(
    {
        "!plain",
        "tag:yaml.org,2002:str",
        "tag:yaml.org,2002:seq",
        "tag:yaml.org,2002:map",
    }
)


class EngineLoader(SafeLoader):
    """Keeps every unquoted scalar's text, and resolves no other. A tag written
    out, `!!merge` among them, is refused rather than guessed: PyYAML applies
    some that serde_yaml ignores."""

    yaml_implicit_resolvers = {None: [("!plain", re.compile(""))]}

    def construct_object(self, node: yaml.Node, deep: bool = False) -> Any:
        if node.tag not in _MODELED_TAGS:
            raise yaml.constructor.ConstructorError(
                None, None, f"the tag {node.tag} is not modeled", node.start_mark
            )
        return super().construct_object(node, deep)

    def flatten_mapping(self, node: yaml.MappingNode) -> None:
        # A plain `<<` resolves to `!plain` and stays an ordinary key, as it does
        # for serde_yaml; only a written-out `!!merge` would merge, and
        # construct_object refuses that tag.
        for key, _ in node.value:
            if key.tag == "tag:yaml.org,2002:merge":
                raise yaml.constructor.ConstructorError(
                    None, None, "a `<<` merge key is not modeled", key.start_mark
                )


EngineLoader.add_constructor("!plain", lambda _, node: Plain(node.value))


class EngineDumper(yaml.SafeDumper):
    """Writes each scalar so serde_yaml reads the value `EngineLoader` read: an
    unquoted null, boolean or number unquoted, and every string quoted. PyYAML
    would leave `1e3` bare, and serde_yaml reads that as a number."""

    yaml_implicit_resolvers = {None: [("!plain", re.compile(""))]}


def _represent_plain(dumper: yaml.SafeDumper, text: Plain) -> yaml.ScalarNode:
    value = text.value
    if isinstance(value, str):
        return dumper.represent_scalar("tag:yaml.org,2002:str", str(text), style='"')
    return dumper.represent_scalar("!plain", "null" if value is None else str(text))


EngineDumper.add_representer(Plain, _represent_plain)
EngineDumper.add_representer(
    str,
    lambda dumper, text: dumper.represent_scalar("tag:yaml.org,2002:str", text, style='"'),
)


Interval = tuple[date, date]


@dataclass(frozen=True, order=True)
class Version:
    start: date
    formula: str = ""
    # effective_to, inclusive; OPEN when the version states none.
    end: date = OPEN


@dataclass(frozen=True)
class Rule:
    name: str
    versions: tuple[Version, ...]
    namespace: str = DERIVED
    table: bool = False

    @property
    def start(self) -> date:
        return min(version.start for version in self.versions)


@dataclass(frozen=True)
class Module:
    imports: tuple[str, ...] = ()
    # The parameter and derived rules, in file order.
    rules: tuple[Rule, ...] = ()
    # (target id, value id) for each `sets` source relation, in file order.
    sets: tuple[tuple[str, str], ...] = ()
    # Every rule name the module declares, of any kind, in file order; the
    # names of `rules` when none are given.
    names: tuple[str, ...] = ()
    # The module states `module.kind`, so the engine compiles it on the composed
    # surface, where its own rules carry no id.
    composition: bool = False
    # (name, predicate formula) for each derived relation.
    relations: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.names:
            object.__setattr__(self, "names", tuple(rule.name for rule in self.rules))


@dataclass(frozen=True, order=True)
class Reference:
    """One rule version reading a name, in the namespace that name binds to."""

    rule: str
    version_start: date
    target: str
    target_start: date
    namespace: str = DERIVED
    # The name the formula reads, when the target is a definition of another
    # name: a `sets` relation's value.
    name: str = ""
    version_end: date = OPEN
    # Each version of what the name binds to, as (from, to), sorted.
    coverage: tuple[Interval, ...] = ()
    # The dates on which the engine picks this rule version.
    window: tuple[Interval, ...] = ()
    # Whether an import declares the name or feeds it.
    crosses: bool = True

    @property
    def read_name(self) -> str:
        """The name the formula reads."""
        return self.name or self.target.split("#", 1)[1]

    def spans(self) -> tuple[tuple[Interval, ...], tuple[Interval, ...]]:
        """(window, coverage), each defaulting to an open run from its start."""
        return (
            self.window or ((self.version_start, OPEN),),
            self.coverage or ((self.target_start, OPEN),),
        )

    def stops(self) -> tuple[Interval, ...]:
        """The dates on which the engine picks this version and the name it reads
        has no version."""
        return subtract(*self.spans())


NEVER = "never"


def _day(day: date) -> str:
    return NEVER if day == OPEN else day.isoformat()


@dataclass(frozen=True, order=True)
class Edge:
    """One baseline entry: a run of dates on which a version of a rule that reads
    a target applies and the target has no version. `start` is the run's first
    date, and `resumes` the date the target next has a version, or OPEN."""

    rule: str
    target: str
    start: date
    resumes: date

    def render(self) -> str:
        return f"{self.rule}\t{self.target}\t{self.start.isoformat()}\t{_day(self.resumes)}"


def _tokens(formula: str) -> list[tuple[str | None, str]]:
    """The tokens the parser sees, each as (TOKEN group, text)."""
    return [
        (match.lastgroup, match[0])
        for match in TOKEN.finditer(formula)
        if match.lastgroup not in ("skip", "docstring")
    ]


def closes_its_strings(formula: str) -> bool:
    """Whether every string and docstring the formula opens also ends in it.

    rulespec.rs writes every rule's formula into one source and lexes it once,
    so an open quote would run into the next rule, which this check reads apart.
    """
    for match in TOKEN.finditer(formula):
        text = match[0]
        if match.lastgroup == "open" or (
            match.lastgroup == "docstring" and not (len(text) >= 6 and text.endswith('"""'))
        ):
            return False
    return True


def _unwrapped(tokens: list[tuple[str | None, str]], index: int) -> tuple[int, int]:
    """The tokens just outside any parentheses wrapped around token `index`: the
    parser erases them before it reads a call or a field."""
    before, after = index - 1, index + 1
    while (
        before >= 0
        and after < len(tokens)
        and tokens[before][1] == "("
        and tokens[after][1] == ")"
    ):
        before -= 1
        after += 1
    return before, after


def _called(tokens: list[tuple[str | None, str]], index: int) -> bool:
    """formula.rs parse_postfix: a name before `(` is a callee. The parser has
    erased any parentheses around it by then, so `(max)(1, 2)` calls `max`."""
    after = _unwrapped(tokens, index)[1]
    return after < len(tokens) and tokens[after][1] == "("


def _relation_call_arguments(
    tokens: list[tuple[str | None, str]],
) -> tuple[set[int], set[int]]:
    """Token indexes of the lone names `len`, `count_where` and `sum_where` take:
    the first names a relation, and the rest read a derived rule or an input."""
    relations: set[int] = set()
    derived: set[int] = set()
    for index, (group, text) in enumerate(tokens):
        if group != "name" or text not in RELATION_CALLS or not _called(tokens, index):
            continue
        opening = _unwrapped(tokens, index)[1]
        arguments: list[list[int]] = [[]]
        depth = 0
        for position in range(opening + 1, len(tokens)):
            symbol = tokens[position][1]
            if symbol in "([" and tokens[position][0] == "other":
                depth += 1
            elif symbol in ")]" and tokens[position][0] == "other":
                if depth == 0:
                    break
                depth -= 1
            elif symbol == "," and depth == 0:
                arguments.append([])
                continue
            arguments[-1].append(position)
        for number, argument in enumerate(arguments):
            names = [position for position in argument if tokens[position][0] == "name"]
            rest = [position for position in argument if tokens[position][1] not in "()"]
            if len(names) == 1 and rest == names:
                (relations if number == 0 else derived).add(names[0])
    return relations, derived


def formula_reads(formula: str) -> tuple[dict[str, frozenset[str]], frozenset[str]]:
    """The names a formula reads, each with the namespaces it can bind in, and
    the names it uses as relations.

    A called name reads nothing. The object of a field access is a relation,
    because formula.rs lowers `rel.field` only inside `len` and `sum`, and the
    field reads a derived rule or an input there. Telling a scalar position from
    a judgment position takes a parser, so any other name can bind both ways.
    """
    tokens = _tokens(formula)
    relation_arguments, derived_arguments = _relation_call_arguments(tokens)
    reads: dict[str, set[str]] = defaultdict(set)
    relations: set[str] = set()
    for index, (group, text) in enumerate(tokens):
        if group != "name" or text in RESERVED or _called(tokens, index):
            continue
        after = _unwrapped(tokens, index)[1]
        if index in relation_arguments or (after < len(tokens) and tokens[after][1] == "."):
            relations.add(text)
            continue
        if (
            index in derived_arguments
            or text in PERIOD_BOUNDS
            or (index > 0 and tokens[index - 1][1] == ".")
        ):
            reads[text] |= DERIVED_ONLY
        else:
            reads[text] |= BOTH
            # A relation predicate's name in a judgment position names its relation.
            relations.add(text)
    return {name: frozenset(spaces) for name, spaces in reads.items()}, frozenset(relations)


def formula_references(formula: str) -> frozenset[str]:
    """The names a formula reads."""
    return frozenset(formula_reads(formula)[0])


def is_literal(formula: str) -> bool:
    """formula.rs is_literal_expr after parsing: one number, string or boolean."""
    tokens = _tokens(formula)
    while len(tokens) > 2 and tokens[0][1] == "(" and tokens[-1][1] == ")":
        tokens = tokens[1:-1]
    return len(tokens) == 1 and (tokens[0][0] == "literal" or tokens[0][1] in BOOLEANS)


def _date(raw: Any, where: str) -> date | None:
    """A `NaiveDate` field: absent or null is None, and any other spelling but
    YYYY-MM-DD is refused."""
    if raw is None or (isinstance(raw, Plain) and raw.value is None):
        return None
    if not isinstance(raw, str) or not DATE.match(raw):
        raise ValueError(f"{where}: {raw!r} is not a YYYY-MM-DD date")
    return date.fromisoformat(raw)


def _raw_text(raw: Any, where: str) -> str:
    """Text the engine writes into the merged formula source as it is: a rule
    name or an entity. A quote or a line break there would change the next rule."""
    text = str(raw)
    if any(mark in text for mark in "\"'\n"):
        raise ValueError(f"{where}: {text!r} holds a quote or a line break")
    return text


def _dated(raw: Iterable[Mapping[str, Any]], where: str) -> tuple[Version, ...]:
    versions = []
    for version in raw:
        start = _date(version.get("effective_from", version.get("from")), where)
        if start is None:
            continue
        end = _date(version.get("effective_to", version.get("to")), where)
        formula = string_like(version.get("formula")) or ""
        if not closes_its_strings(formula):
            raise ValueError(
                f"{where}: the formula from {start} leaves a string open, and the engine"
                " lexes every rule's formula as one source"
            )
        versions.append(Version(start, formula, OPEN if end is None else end))
    return tuple(versions)


def parse_rule(rule: Mapping[str, Any], where: str) -> Rule | None:
    """A rule as the engine lowers it, or None when it holds no version to compare.

    This follows to_program_spec_with_options, is_parameter_table and
    to_indexed_parameter_spec in rulespec.rs and lower_module in formula.rs. A
    version with no date, or a rule with no version, is one the engine refuses.
    """
    if rule.get("kind") not in VERSIONED_KINDS:
        return None
    name = _raw_text(rule["name"], where)
    declared = scalar_value(rule.get("versions")) or []
    tabled = [version for version in declared if scalar_value(version.get("values"))]
    if tabled:
        return Rule(name, _dated(tabled, where), PARAMETER, table=True)
    versions = _dated(declared or [rule], where)
    if not versions:
        return None
    entity = string_like(rule.get("entity"))
    if entity is not None:
        _raw_text(entity, where)
    if entity not in (None, "") or not all(is_literal(item.formula) for item in versions):
        return Rule(name, versions, DERIVED)
    return Rule(name, versions, PARAMETER)


def parse_set(rule: Mapping[str, Any]) -> tuple[str, str] | None:
    """(target id, value id) when a rule states a `sets` relation the engine applies.
    apply_source_relation_sets reads the relation on a rule of any kind."""
    relation = rule.get("source_relation")
    if not isinstance(relation, Mapping) or relation.get("type") != "sets":
        return None
    target, value = ((string_like(relation.get(key)) or "").strip() for key in ("target", "value"))
    return (target, value) if "#" in target and "#" in value and target != value else None


def parse_relation(rule: Mapping[str, Any]) -> tuple[str, str] | None:
    """(name, predicate) for a derived relation. to_derived_relation_spec lowers
    its one formula version as a judgment, and the engine evaluates it on each
    date a rule asks for the relation, whatever that version's date says."""
    if rule.get("kind") != "derived_relation":
        return None
    versions = scalar_value(rule.get("versions")) or [rule]
    formulas = [string_like(version.get("formula")) or "" for version in versions]
    return str(rule["name"]), " ".join(formulas)


def parse_module(text: str, where: str = "<module>") -> Module:
    """The parts of a module that decide its edges; a module with no date to read
    is one the engine refuses, which the engine-root-load gate reports."""
    document = yaml.load(text, Loader=EngineLoader)
    if not isinstance(document, Mapping):
        raise ValueError(f"{where}: not a RuleSpec mapping")
    metadata = scalar_value(document.get("module")) or {}
    for key in ("title", "status"):
        # rulespec.rs write_header puts these after `# ` on one line.
        if "\n" in str(string_like(metadata.get(key)) or ""):
            raise ValueError(f"{where}: module {key} holds a line break")
    rules = scalar_value(document.get("rules")) or []
    parsed = (parse_rule(rule, f"{where} rule {rule.get('name')}") for rule in rules)
    return Module(
        tuple(str(item) for item in scalar_value(document.get("imports")) or ()),
        tuple(rule for rule in parsed if rule is not None),
        tuple(item for item in map(parse_set, rules) if item is not None),
        tuple(str(rule.get("name")) for rule in rules),
        bool(string_like(metadata.get("kind"))),
        tuple(item for item in map(parse_relation, rules) if item is not None),
    )


def load_modules(root: Path) -> dict[str, Module]:
    """Every tracked atomic module, by canonical target."""
    return {
        canonical_target(path): parse_module(
            (root / path).read_text(encoding="utf-8"), path
        )
        for path in tracked_modules(root)
    }


def flattened(target: str, modules: Mapping[str, Module]) -> list[str]:
    """`target` and each module it reaches through imports, in the order the engine
    merges them: each one's imports first, each module once, `target` last.

    An import that resolves to no module is skipped here: the engine refuses
    it, and the engine-root-load gate reports it as `unresolved-import`.
    """
    seen = {target}
    order: list[str] = []

    def visit(current: str) -> None:
        for specifier in modules[current].imports:
            imported = specifier.split("#", 1)[0]
            if imported in modules and imported not in seen:
                seen.add(imported)
                visit(imported)
        order.append(current)

    visit(target)
    return order


def import_closure(target: str, modules: Mapping[str, Module]) -> frozenset[str]:
    """Every module `target` reaches through imports, excluding itself."""
    return frozenset(flattened(target, modules)) - {target}


def _after(day: date) -> date:
    return day if day == OPEN else day + timedelta(days=1)


def merged(intervals: Iterable[Interval]) -> tuple[Interval, ...]:
    """The union of inclusive (from, to) intervals, as sorted disjoint runs."""
    runs: list[list[date]] = []
    for start, end in sorted(intervals):
        if runs and start <= _after(runs[-1][1]):
            runs[-1][1] = max(runs[-1][1], end)
        else:
            runs.append([start, end])
    return tuple((start, end) for start, end in runs)


def windows(versions: Iterable[Version]) -> dict[Version, tuple[Interval, ...]]:
    """model.rs semantics_at: on each date the engine picks, of the versions that
    apply, the one that starts last. A version open at its end runs again where a
    later, ended version stops."""
    versions = list(versions)
    cuts = sorted(
        {version.start for version in versions}
        | {_after(version.end) for version in versions if version.end != OPEN}
    )
    picked: dict[Version, list[Interval]] = defaultdict(list)
    for index, cut in enumerate(cuts):
        applying = [item for item in versions if item.start <= cut <= item.end]
        if not applying:
            continue
        last = cuts[index + 1] - timedelta(days=1) if index + 1 < len(cuts) else OPEN
        picked[max(applying, key=lambda item: item.start)].append((cut, last))
    return {version: merged(runs) for version, runs in picked.items()}


def subtract(intervals: Iterable[Interval], removed: Iterable[Interval]) -> tuple[Interval, ...]:
    """The dates of `intervals` that no interval of `removed` holds, as sorted
    disjoint runs."""
    runs = merged(removed)
    left: list[Interval] = []
    for start, end in merged(intervals):
        day: date | None = start
        for run_start, run_end in runs:
            if run_end < day:
                continue
            if run_start > end:
                break
            if run_start > day:
                left.append((day, run_start - timedelta(days=1)))
            if run_end >= end:
                day = None
                break
            day = run_end + timedelta(days=1)
        if day is not None:
            left.append((day, end))
    return tuple(left)


@dataclass(frozen=True)
class Entry:
    """One parameter or derived entry of a lowered program: the module that
    declared it, the definition whose versions it carries, which a `sets`
    relation may have changed, and those versions under the entry's own name."""

    owner: str
    source: str
    rule: Rule


@dataclass
class Program:
    """A root's parameter and derived entries, in the engine's order."""

    parameters: list[Entry]
    derived: list[Entry]

    def group(self, namespace: str, name: str) -> list[Entry]:
        entries = self.parameters if namespace == PARAMETER else self.derived
        return [entry for entry in entries if entry.rule.name == name]


def program(origin: str, order: list[str], modules: Mapping[str, Module]) -> Program | None:
    """The entries `origin`'s lowered program holds, or None when the engine
    refuses it over a `sets` relation.

    formula.rs lower_module emits scalar parameters in source order, and
    to_program_spec_with_options appends tables after removing scalars of their
    names. apply_rule_ids gives every entry of a name the id of the last rule of
    that name, of any kind, that carries one; a composition's own rules carry
    none. apply_source_relation_sets then finds each id, a parameter before a
    derived rule and the first entry of either, and copies the value entry's
    versions onto the target entry, in rule order. Parameters of one name merge
    later, in compile.rs normalize_parameter_duplicates.
    """
    ids: dict[str, str] = {}
    for owner in order:
        module = modules[owner]
        if owner == origin and module.composition:
            continue
        for name in module.names:
            ids[name] = owner
    scalars: list[Entry] = []
    tables: list[Entry] = []
    derived: list[Entry] = []
    for owner in order:
        for rule in modules[owner].rules:
            entry = Entry(owner, f"{owner}#{rule.name}", rule)
            if rule.namespace == DERIVED:
                derived.append(entry)
            else:
                (tables if rule.table else scalars).append(entry)
    tabled = {entry.rule.name for entry in tables}
    built = Program([entry for entry in scalars if entry.rule.name not in tabled] + tables, derived)

    def find(reference: str) -> tuple[list[Entry], int] | None:
        owner, name = reference.split("#", 1)
        if ids.get(name) != owner:
            return None
        for entries in (built.parameters, built.derived):
            for index, entry in enumerate(entries):
                if entry.rule.name == name:
                    return entries, index
        return None

    for owner in order:
        for target, value in modules[owner].sets:
            found_target, found_value = find(target), find(value)
            if found_target is None and found_value is None:
                continue
            if found_target is None or found_value is None or found_target[0] is not found_value[0]:
                return None
            entries, index = found_target
            source = found_value[0][found_value[1]]
            entries[index] = Entry(
                entries[index].owner,
                source.source,
                replace(source.rule, name=entries[index].rule.name),
            )
    return built


def _coverage(group: list[Entry]) -> tuple[Interval, ...]:
    return tuple(sorted({(item.start, item.end) for entry in group for item in entry.rule.versions}))


def _target(origin: str, group: list[Entry]) -> str:
    """The earliest definition an import supplies, or else this module's own."""
    imported = [
        (entry.rule.start, entry.source)
        for entry in group
        if entry.source.split("#", 1)[0] != origin
    ]
    if imported:
        return min(imported)[1]
    return min(entry.source for entry in group)


def all_references(modules: Mapping[str, Module]) -> set[Reference]:
    """Every (rule version, name) binding, local ones included, for each module
    compiled as its own root. Only derived rules read names: a parameter's
    versions are literals or values. A version also reads what the predicate of
    each derived relation it asks for reads. The coverage is every version of
    what the name binds to, merged parameters together, after the root's `sets`
    relations. The target names the earliest definition an import supplies, and
    this module only when nothing imported does.
    """
    references: set[Reference] = set()
    for origin, module in modules.items():
        order = flattened(origin, modules)
        built = program(origin, order, modules)
        if built is None:
            continue
        predicates: dict[str, list[str]] = defaultdict(list)
        for owner in order:
            for name, predicate in modules[owner].relations:
                predicates[name].append(predicate)
        for rule in module.rules:
            if rule.namespace != DERIVED:
                continue
            own = [entry for entry in built.group(DERIVED, rule.name) if entry.owner == origin]
            if not own:
                continue
            lowered = own[0].rule
            spans = windows(lowered.versions)
            for version in lowered.versions:
                for name, namespaces in _version_reads(version.formula, predicates).items():
                    for namespace in sorted(namespaces):
                        group = built.group(namespace, name)
                        if not group:
                            continue
                        coverage = _coverage(group)
                        target = _target(origin, group)
                        references.add(
                            Reference(
                                f"{origin}#{rule.name}",
                                version.start,
                                target,
                                coverage[0][0],
                                namespace,
                                "" if target.split("#", 1)[1] == name else name,
                                version.end,
                                coverage,
                                spans.get(version, ()),
                                any(
                                    entry.owner != origin
                                    or entry.source.split("#", 1)[0] != origin
                                    for entry in group
                                ),
                            )
                        )
    return references


def _version_reads(
    formula: str, predicates: Mapping[str, list[str]]
) -> dict[str, frozenset[str]]:
    """A formula's reads, and through each derived relation it asks for, what that
    relation's predicate reads. formula.rs lower_judgment_formula lowers a
    predicate with no scalar names, so its names read only derived rules."""
    reads, relations = formula_reads(formula)
    found: dict[str, set[str]] = defaultdict(set)
    for name, namespaces in reads.items():
        found[name] |= namespaces
    pending = [name for name in relations if name in predicates]
    seen = set(pending)
    while pending:
        for predicate in predicates[pending.pop()]:
            inner, inner_relations = formula_reads(predicate)
            for name in inner:
                found[name] |= DERIVED_ONLY
            for name in inner_relations:
                if name in predicates and name not in seen:
                    seen.add(name)
                    pending.append(name)
    return {name: frozenset(namespaces) for name, namespaces in found.items()}


def import_references(modules: Mapping[str, Module]) -> set[Reference]:
    """The bindings an import declares or feeds, which are the ones this check
    owns. A purely local one belongs to the encoder's temporal-dependency-coverage
    validator."""
    return {item for item in all_references(modules) if item.crosses}


def late_start_edges(references: Iterable[Reference]) -> set[Edge]:
    """One edge per (rule, target) and run of dates on which a version of the rule
    that reads the target applies and the target has no version. Runs that touch
    merge, across versions and namespaces, and a merged run resumes on the latest
    date any of its parts does."""
    parts: dict[tuple[str, str], list[tuple[date, date, date]]] = defaultdict(list)
    for reference in references:
        starts = [start for start, _ in merged(reference.spans()[1])]
        for start, end in reference.stops():
            resumes = next((item for item in starts if item > end), OPEN)
            parts[(reference.rule, reference.target)].append((start, end, resumes))
    edges: set[Edge] = set()
    for (rule, target), runs in parts.items():
        runs.sort()
        first, last, resumes = runs[0]
        for start, end, then in runs[1:]:
            if start <= _after(last):
                last, resumes = max(last, end), max(resumes, then)
                continue
            edges.add(Edge(rule, target, first, resumes))
            first, last, resumes = start, end, then
        edges.add(Edge(rule, target, first, resumes))
    return edges


def stop_dates(references: Iterable[Reference]) -> dict[tuple[str, str], tuple[Interval, ...]]:
    """Per (rule, name it reads), the dates on which a version of the rule that
    reads the name applies and the name has no version. The base bound compares
    these, so a repair that changes which module supplies a name compares as the
    same name."""
    found: dict[tuple[str, str], list[Interval]] = defaultdict(list)
    for reference in references:
        found[(reference.rule, reference.read_name)].extend(reference.stops())
    return {key: merged(runs) for key, runs in found.items() if runs}


def widened(
    head: Mapping[tuple[str, str], tuple[Interval, ...]],
    base: Mapping[tuple[str, str], tuple[Interval, ...]],
) -> dict[tuple[str, str], tuple[Interval, ...]]:
    """The stop dates in `head` that `base` does not hold, per (rule, name)."""
    found: dict[tuple[str, str], tuple[Interval, ...]] = {}
    for key, runs in head.items():
        extra = subtract(runs, base.get(key, ()))
        if extra:
            found[key] = extra
    return found


def module_path(rule_id: str) -> str:
    """`us:statutes/26/6012#x` -> `us/statutes/26/6012.yaml`."""
    jurisdiction, rest = rule_id.split("#", 1)[0].split(":", 1)
    return f"{jurisdiction}/{rest}.yaml"


def _baseline_day(raw: str, never: bool = False) -> date:
    if never and raw == NEVER:
        return OPEN
    if not DATE.match(raw):
        raise ValueError(f"not a YYYY-MM-DD date: {raw!r}")
    return date.fromisoformat(raw)


def parse_baseline(text: str) -> set[Edge]:
    entries: set[Edge] = set()
    for number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        fields = raw.split("\t")
        if len(fields) != 4:
            raise ValueError(
                f"baseline line {number} must be "
                f"<rule>\\t<target>\\t<first date>\\t<target resumes>: {raw!r}"
            )
        rule, target, start, resumes = fields
        if "#" not in rule or "#" not in target:
            raise ValueError(f"baseline line {number} does not name two rule ids: {raw!r}")
        try:
            entry = Edge(rule, target, _baseline_day(start), _baseline_day(resumes, never=True))
        except ValueError as error:
            raise ValueError(f"baseline line {number}: {error}") from None
        if entry.start >= entry.resumes:
            raise ValueError(f"baseline line {number} resumes before it starts: {raw!r}")
        if entry in entries:
            raise ValueError(f"baseline line {number} duplicates an earlier entry: {raw!r}")
        entries.add(entry)
    return entries


BASELINE_HEADER = """\
# Runs of dates on which a rule version that reads an import applies and the
# import has no version. On any of them the engine stops on the import, and
# only at run time.
# Format: <rule id>\\t<target id>\\t<first date>\\t<date the target next has a
# version, or never>, sorted.
# Maintained by tools/late_start_imports.py; see that file for the definition.
# The check fails when this list leaves out an edge or a line no longer holds.
# Repair an edge, then regenerate. A pull request may not add stop dates for a
# (rule, name) unless it carries the late-start-import-accepted label.
"""


def render_baseline(entries: Iterable[Edge]) -> str:
    body = "".join(entry.render() + "\n" for entry in sorted(entries))
    return BASELINE_HEADER + body


@dataclass
class Verdict:
    new: set[Edge]
    stale: set[Edge]
    # Stop dates, per (rule, name), that the protected base does not have.
    widened: dict[tuple[str, str], tuple[Interval, ...]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not (self.new or self.stale or self.widened)


def compare(
    edges: set[Edge],
    baseline: set[Edge],
    widened: Mapping[tuple[str, str], tuple[Interval, ...]] | None = None,
) -> Verdict:
    """The gate: edges must equal the baseline, and no (rule, name) may stop on a
    date the protected base did not. A listed edge may change dates, which the
    baseline diff shows, because a repair can narrow or move a gap without
    closing it; it may not widen one without the accepted label."""
    return Verdict(new=edges - baseline, stale=baseline - edges, widened=dict(widened or {}))


def load_modules_at(root: Path, ref: str) -> dict[str, Module]:
    """Every atomic module in commit `ref`, by canonical target, read from git
    objects so the working tree and the baseline file play no part."""
    resolved = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    if resolved.returncode != 0:
        raise SystemExit(f"base ref {ref} is not a commit in {root}")
    commit = resolved.stdout.strip()
    listing = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "-r", "-z", "--name-only", commit],
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    paths = select_modules(path for path in listing.split("\0") if path)
    batch = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"],
        input="".join(f"{commit}:{path}\n" for path in paths).encode("utf-8"),
        check=True,
        capture_output=True,
    ).stdout
    modules: dict[str, Module] = {}
    offset = 0
    for path in paths:
        header_end = batch.index(b"\n", offset)
        header = batch[offset:header_end].decode("utf-8").split()
        if len(header) != 3 or header[1] != "blob":
            raise SystemExit(f"cannot read {path} at {ref}: {' '.join(header)}")
        body = header_end + 1
        size = int(header[2])
        text = batch[body : body + size].decode("utf-8")
        modules[canonical_target(path)] = parse_module(text, path)
        offset = body + size + 1
    return modules


def summarize(edges: set[Edge]) -> str:
    jurisdictions = Counter(edge.rule.split(":", 1)[0] for edge in edges)
    top = ", ".join(f"{name} {count}" for name, count in jurisdictions.most_common(5))
    return (
        f"{len(edges)} late-start import edge(s): "
        f"{len({edge.rule for edge in edges})} rules, "
        f"{len({module_path(edge.rule) for edge in edges})} importing modules, "
        f"{len({module_path(edge.target) for edge in edges})} target modules"
        + (f" ({top})" if top else "")
    )


def _describe(edge: Edge) -> str:
    then = "never has one again" if edge.resumes == OPEN else f"has none until {edge.resumes}"
    return f"{edge.rule} reads {edge.target} from {edge.start}, and that target {then}"


def check(root: Path, baseline_path: Path, base_ref: str | None, allow_added: bool) -> int:
    references = import_references(load_modules(root))
    edges = late_start_edges(references)
    baseline = parse_baseline(baseline_path.read_text(encoding="utf-8"))
    wider: dict[tuple[str, str], tuple[Interval, ...]] = {}
    if base_ref:
        base = stop_dates(import_references(load_modules_at(root, base_ref)))
        wider = widened(stop_dates(references), base)
    verdict = compare(edges, baseline, {} if allow_added else wider)
    print(summarize(edges))
    if verdict.new:
        print(f"\n{len(verdict.new)} edge(s) are not in {baseline_path.name}:")
        for entry in sorted(verdict.new):
            print(f"  {_describe(entry)}")
        print(
            "\nStart the rule version no earlier than its target, give the target a"
            " version for those dates, or read the target only from a version that"
            " applies when the target does. If the dates are the law's, regenerate"
            " the baseline."
        )
    if verdict.stale:
        print(f"\n{len(verdict.stale)} listed edge(s) no longer hold this way:")
        for entry in sorted(verdict.stale):
            print(f"  {entry.render()}")
    if wider:
        print(
            f"\n{len(wider)} rule(s) read a name with no version on dates the base"
            f" {base_ref} does not stop on"
            + (
                f"; the {ACCEPT_LABEL} label accepts them:"
                if allow_added
                else f". A pull request may only shrink these dates unless it carries"
                f" the {ACCEPT_LABEL} label:"
            )
        )
        for (rule, name), runs in sorted(wider.items()):
            print(f"  {rule} reads {name} on {_spans_text(runs)}")
    if verdict.new or verdict.stale:
        print(
            "\nRegenerate with: python tools/late_start_imports.py baseline"
            f" > {BASELINE_RELATIVE_PATH.as_posix()}"
        )
    if verdict.ok:
        print(f"\nLate-start imports match {baseline_path.name}.")
        return 0
    return 1


HARNESS_SOURCE = r"""//! Written by rulespec-us tools/late_start_imports.py; see that file for the
//! contract. Do not edit here: the copy in rulespec-us is the source.
//!
//! usage: rulespec_import_references <absolute rulespec-<cc> root> <module list> <composed scratch dir>
//!
//! The module list holds one root-relative module path per line. Every module
//! yields one JSON line on stdout: its compile error, or the namespaces of the
//! lowered program that hold each rule name the module declares, with the
//! versions each holds, and each name those derived rules' versions read, with
//! the namespace the lowered program bound it to and every version of what that
//! namespace holds. A version that asks for a derived relation also reads what
//! the relation's predicate reads, on the same dates. A module the engine
//! refuses on the atomic surface because it itself declares `module.kind` is
//! compiled from a copy under the scratch directory instead (composed programs
//! must sit outside every root).
//!
//! A module's rules are found by name from its own YAML, read as the engine reads
//! a rule's `name`. Derived names are unique in a program, but ids are not a
//! test: the engine reattaches them by name, so when a parameter and a derived
//! rule share a name both carry the same id, and a composition's own rules take
//! an imported rule's id. `collisions` lists the names held both ways, where a
//! declared name may be an imported rule's, for the caller to weigh.
use std::collections::{BTreeMap, BTreeSet};
use std::io::Write;
use std::path::{Path, PathBuf};

use axiom_rules_engine::compile::{CompileError, CompiledProgramArtifact};
use axiom_rules_engine::rulespec::{CanonicalRuleSpecRoots, RuleSpecError};
use chrono::NaiveDate;
use serde::Deserialize;
use serde_json::{Value, json};

type Span = (NaiveDate, Option<NaiveDate>);

/// Every name a lowered expression reads, by namespace, from its tagged spec,
/// following each derived relation it asks for into that relation's predicate.
fn collect(
    value: &Value,
    predicates: &BTreeMap<String, Value>,
    followed: &mut BTreeSet<String>,
    read: &mut BTreeSet<(&'static str, String)>,
) {
    match value {
        Value::Object(map) => {
            let tagged = match map.get("kind").and_then(Value::as_str) {
                Some("derived") => Some(("derived", "name")),
                Some("parameter_lookup") => Some(("parameter", "parameter")),
                Some("input") => Some(("input", "name")),
                _ => None,
            };
            if let Some((namespace, key)) = tagged
                && let Some(name) = map.get(key).and_then(Value::as_str)
            {
                read.insert((namespace, name.to_string()));
            }
            if let Some(relation) = map.get("relation").and_then(Value::as_str)
                && let Some(predicate) = predicates.get(relation)
                && followed.insert(relation.to_string())
            {
                collect(predicate, predicates, followed, read);
            }
            map.values()
                .for_each(|child| collect(child, predicates, followed, read));
        }
        Value::Array(items) => items
            .iter()
            .for_each(|child| collect(child, predicates, followed, read)),
        _ => {}
    }
}

fn spans<'a>(
    entries: impl Iterator<Item = (&'a str, Span)>,
) -> BTreeMap<&'a str, BTreeSet<Span>> {
    let mut found: BTreeMap<&str, BTreeSet<Span>> = BTreeMap::new();
    for (name, span) in entries {
        found.entry(name).or_default().insert(span);
    }
    found
}

fn spans_json(spans: &BTreeSet<Span>) -> Value {
    Value::Array(
        spans
            .iter()
            .map(|(from, to)| json!([from.to_string(), to.map(|to| to.to_string())]))
            .collect(),
    )
}

#[derive(Deserialize)]
struct NamedRule {
    name: String,
}

#[derive(Deserialize)]
struct Declared {
    #[serde(default)]
    rules: Vec<NamedRule>,
}

/// The rule names a module declares, each read as the engine reads `name`.
fn declared_names(path: &Path) -> BTreeSet<String> {
    let text = std::fs::read_to_string(path).expect("read module");
    let declared: Declared = serde_yaml::from_str(&text).expect("module names its rules");
    declared.rules.into_iter().map(|rule| rule.name).collect()
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 4 {
        eprintln!("usage: rulespec_import_references <root> <module list> <composed scratch dir>");
        std::process::exit(2);
    }
    let root = PathBuf::from(&args[1]);
    let composed_dir = PathBuf::from(&args[3]);
    let roots = match CanonicalRuleSpecRoots::new([&root]) {
        Ok(roots) => roots,
        Err(error) => {
            println!("{}", json!({ "root_error": error.to_string() }));
            std::process::exit(3);
        }
    };
    let list = std::fs::read_to_string(&args[2]).expect("read module list");
    let stdout = std::io::stdout();
    let mut out = std::io::BufWriter::new(stdout.lock());
    for module in list.lines().filter(|line| !line.is_empty()) {
        let (jurisdiction, rest) = module
            .strip_suffix(".yaml")
            .and_then(|stem| stem.split_once('/'))
            .expect("module path");
        let target = format!("{jurisdiction}:{rest}");
        let path = root.join(module);
        let result = match CompiledProgramArtifact::from_rulespec_file(&path, &roots) {
            Err(CompileError::RuleSpec {
                error: RuleSpecError::ModuleKindOnAtomicSurface { path: offender },
                ..
            }) if offender == target => {
                let copy = composed_dir.join(module);
                std::fs::create_dir_all(copy.parent().expect("module path has a parent"))
                    .expect("create composed scratch directory");
                std::fs::copy(&path, &copy).expect("copy composition outside the root");
                CompiledProgramArtifact::from_composed_rulespec_file(&copy, &roots)
            }
            other => other,
        };
        let artifact = match result {
            Ok(artifact) => artifact,
            Err(error) => {
                let line = json!({ "module": module, "ok": false, "error": error.to_string() });
                writeln!(out, "{line}").expect("write result line");
                continue;
            }
        };
        let program = &artifact.program;
        let parameters = spans(program.parameters.iter().flat_map(|parameter| {
            parameter
                .versions
                .iter()
                .map(|v| (parameter.name.as_str(), (v.effective_from, v.effective_to)))
        }));
        let derived = spans(program.derived.iter().flat_map(|rule| {
            rule.versions
                .iter()
                .map(|v| (rule.name.as_str(), (v.effective_from, v.effective_to)))
        }));
        let predicates: BTreeMap<String, Value> = program
            .relations
            .iter()
            .filter_map(|relation| {
                let derivation = relation.derivation.as_ref()?;
                let predicate =
                    serde_json::to_value(&derivation.predicate).expect("predicate as json");
                Some((relation.name.clone(), predicate))
            })
            .collect();
        let collisions: Vec<&str> = parameters
            .keys()
            .filter(|name| derived.contains_key(*name))
            .copied()
            .collect();
        let declared = declared_names(&path);
        let mut rules = Vec::new();
        for name in &declared {
            for (namespace, held) in [("parameter", &parameters), ("derived", &derived)] {
                if let Some(versions) = held.get(name.as_str()) {
                    rules.push(json!({
                        "name": name,
                        "namespace": namespace,
                        "versions": spans_json(versions),
                    }));
                }
            }
        }
        let mut references = Vec::new();
        for rule in program.derived.iter().filter(|rule| declared.contains(&rule.name)) {
            for version in &rule.versions {
                let semantics = serde_json::to_value(&version.semantics).expect("semantics as json");
                let mut read = BTreeSet::new();
                collect(&semantics, &predicates, &mut BTreeSet::new(), &mut read);
                for (namespace, name) in read {
                    let coverage = match namespace {
                        "parameter" => parameters.get(name.as_str()).map(spans_json),
                        "derived" => derived.get(name.as_str()).map(spans_json),
                        _ => None,
                    };
                    if namespace != "input" && coverage.is_none() {
                        panic!("{module}: {} reads {namespace} {name}, which has no version", rule.name);
                    }
                    references.push(json!({
                        "rule": format!("{target}#{}", rule.name),
                        "version_start": version.effective_from.to_string(),
                        "version_end": version.effective_to.map(|end| end.to_string()),
                        "name": name,
                        "namespace": namespace,
                        "coverage": coverage,
                    }));
                }
            }
        }
        let line = json!({
            "module": module,
            "ok": true,
            "rules": rules,
            "references": references,
            "collisions": collisions,
        });
        writeln!(out, "{line}").expect("write result line");
    }
    out.flush().expect("flush results");
}
"""


@dataclass(frozen=True, order=True)
class Binding:
    """One name a rule version reads: the key both models answer for."""

    rule: str
    version_start: date
    name: str
    namespace: str
    target_start: date | None = None
    version_end: date = OPEN
    # Each version of what the name binds to, as (from, to), sorted.
    coverage: tuple[Interval, ...] = ()


@dataclass
class EngineRun:
    """What the harness reported. `collisions` holds `<module>#<name>` ids, and
    `rules` holds (`<module>#<name>`, namespace, versions) for each name a module
    declares that the lowered program holds."""

    results: set[str]
    compiled: set[str]
    refused: dict[str, str]
    bindings: set[Binding]
    inputs: set[Binding]
    collisions: set[str]
    rules: set[tuple[str, str, tuple[Interval, ...]]]


def _spans(raw: Iterable[list[str | None]]) -> tuple[Interval, ...]:
    return tuple(
        sorted(
            (date.fromisoformat(start), OPEN if end is None else date.fromisoformat(end))
            for start, end in raw
        )
    )


def parse_engine_references(lines: Iterable[str]) -> EngineRun:
    run = EngineRun(set(), set(), {}, set(), set(), set(), set())
    for number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        record = json.loads(raw)
        if "root_error" in record:
            raise SystemExit(f"engine refused the checkout as a root: {record['root_error']}")
        if not isinstance(record.get("ok"), bool) or "module" not in record:
            raise SystemExit(f"malformed result on line {number}: {raw}")
        origin = canonical_target(record["module"])
        if origin in run.results:
            raise SystemExit(f"second result for {record['module']} on line {number}")
        run.results.add(origin)
        if not record["ok"]:
            run.refused[origin] = record.get("error", "")
            continue
        run.compiled.add(origin)
        run.collisions.update(f"{origin}#{name}" for name in record["collisions"])
        run.rules.update(
            (f"{origin}#{item['name']}", item["namespace"], _spans(item["versions"]))
            for item in record["rules"]
        )
        for item in record["references"]:
            coverage = _spans(item["coverage"] or ())
            end = item["version_end"]
            binding = Binding(
                item["rule"],
                date.fromisoformat(item["version_start"]),
                item["name"],
                item["namespace"],
                coverage[0][0] if coverage else None,
                OPEN if end is None else date.fromisoformat(end),
                coverage,
            )
            (run.inputs if item["namespace"] == "input" else run.bindings).add(binding)
    return run


def coverage_failures(
    run: EngineRun, tracked: Iterable[str], edges: Iterable[Edge]
) -> list[str]:
    """Why this run cannot vouch for the static model, however well it agreed."""
    expected = {canonical_target(path) for path in tracked}
    failures = []
    if missing := expected - run.results:
        failures.append(f"no result for {len(missing)} module(s): {sorted(missing)[:10]}")
    if unexpected := run.results - expected:
        failures.append(f"results for untracked module(s): {sorted(unexpected)[:10]}")
    if len(run.compiled) < MINIMUM_COMPILED_SHARE * len(expected):
        failures.append(
            f"the engine compiled {len(run.compiled)} of {len(expected)} modules, below"
            f" the {MINIMUM_COMPILED_SHARE:.0%} floor"
        )
    uncovered = sorted(
        edge.rule for edge in edges if edge.rule.split("#", 1)[0] not in run.compiled
    )
    if uncovered:
        failures.append(f"{len(uncovered)} edge(s) in modules the engine refused: {uncovered[:10]}")
    return failures


def _binding(reference: Reference) -> Binding:
    return Binding(
        reference.rule,
        reference.version_start,
        reference.name or reference.target.split("#", 1)[1],
        reference.namespace,
        reference.target_start,
        reference.version_end,
        reference.coverage,
    )


def declared_rules(
    modules: Mapping[str, Module], origins: Iterable[str]
) -> set[tuple[str, str, tuple[Interval, ...]]]:
    """For each module, each name it declares that its lowered program holds: the
    namespace, and every version that namespace holds under the name."""
    found = set()
    for origin in origins:
        built = program(origin, flattened(origin, modules), modules)
        if built is None:
            continue
        for name in set(modules[origin].names):
            for namespace in (PARAMETER, DERIVED):
                if group := built.group(namespace, name):
                    found.add((f"{origin}#{name}", namespace, _coverage(group)))
    return found


@dataclass
class Differences:
    only_engine: set[Binding]
    only_static: set[Binding]
    # Static bindings the model reads by design and the lowered program does
    # not, each where the engine read the same name another way: the other side
    # of a collision, and a parameter read in a judgment position, which lowers
    # to an input.
    over_reported: set[Binding]
    # Declared names the lowered program does not hold as the model does: in
    # that namespace, with those versions.
    missing_rules: set[tuple[str, str, tuple[Interval, ...]]]
    # Declared names the lowered program holds where the model has none.
    extra_rules: set[tuple[str, str, tuple[Interval, ...]]] = field(default_factory=set)


def reference_differences(
    run: EngineRun, static: set[Reference], modules: Mapping[str, Module]
) -> Differences:
    """Compare the two models over the modules the engine compiled.

    The harness reports a derived rule by name, so beside a local parameter of an
    imported derived rule's name it reports the import. The bindings of a name the
    module does not declare as derived say nothing about that module, and the
    rule comparison, which runs both ways, shows whether the model and the
    program agree on which namespaces hold that name.
    """

    def declared(rule: str) -> bool:
        origin, name = rule.split("#", 1)
        return any(
            item.name == name and item.namespace == DERIVED for item in modules[origin].rules
        )

    in_scope = {
        _binding(item) for item in static if item.rule.split("#", 1)[0] in run.compiled
    }
    engine = {item for item in run.bindings if declared(item.rule)}
    reads: dict[tuple[str, date, str], set[str]] = defaultdict(set)
    for item in engine | run.inputs:
        reads[(item.rule, item.version_start, item.name)].add(item.namespace)

    def by_design(item: Binding) -> bool:
        other = reads[(item.rule, item.version_start, item.name)] - {item.namespace}
        collides = f"{item.rule.split('#', 1)[0]}#{item.name}" in run.collisions
        return bool(other - {"input"}) and collides or (
            item.namespace == PARAMETER and "input" in other
        )

    only_static = in_scope - engine
    over_reported = {item for item in only_static if by_design(item)}
    expected = declared_rules(modules, sorted(run.compiled))
    return Differences(
        engine - in_scope,
        only_static - over_reported,
        over_reported,
        expected - run.rules,
        run.rules - expected,
    )


def without_citation_metadata(document: Any) -> Any:
    """A module's executable content: its imports and rules, and `module.kind`."""
    if isinstance(document, list):
        return [without_citation_metadata(item) for item in document]
    if not isinstance(document, dict):
        return document
    return {
        key: without_citation_metadata(value)
        for key, value in document.items()
        if key not in CITATION_KEYS
    }


def write_scratch_root(root: Path, modules: Iterable[str], scratch: Path) -> Path:
    """Copy the modules' executable content to a root the engine will admit."""
    scratch_root = scratch / "rulespec-us"
    for path in modules:
        document = yaml.load((root / path).read_text(encoding="utf-8"), Loader=EngineLoader)
        kind = (scalar_value(document.get("module")) or {}).get("kind")
        document["module"] = {"kind": kind} if string_like(kind) else {}
        document["imports"] = scalar_value(document.get("imports")) or []
        target = scratch_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            yaml.dump(without_citation_metadata(document), Dumper=EngineDumper, sort_keys=False),
            encoding="utf-8",
        )
    return scratch_root


def build_harness(engine_src: Path) -> Path:
    """Build the harness inside an engine checkout, and return the binary."""
    if not (engine_src / "Cargo.toml").is_file():
        raise SystemExit(f"{engine_src} is not an axiom-rules-engine checkout")
    example = engine_src / "examples" / f"{HARNESS_EXAMPLE_NAME}.rs"
    example.parent.mkdir(exist_ok=True)
    example.write_text(HARNESS_SOURCE, encoding="utf-8")
    subprocess.run(
        ["cargo", "build", "--release", "--locked", "--example", HARNESS_EXAMPLE_NAME],
        cwd=engine_src,
        check=True,
    )
    return engine_src / "target" / "release" / "examples" / HARNESS_EXAMPLE_NAME


def run_harness(binary: Path, root: Path, modules: list[str]) -> str:
    """The harness's report on a scratch copy of these modules."""
    with tempfile.TemporaryDirectory(prefix="late-start-imports-") as scratch:
        scratch_path = Path(scratch).resolve()
        scratch_root = write_scratch_root(root, modules, scratch_path)
        module_list = scratch_path / "modules.txt"
        module_list.write_text("".join(f"{module}\n" for module in modules), encoding="utf-8")
        completed = subprocess.run(
            [str(binary), str(scratch_root), str(module_list), str(scratch_path / "composed")],
            check=False,
            capture_output=True,
            text=True,
        )
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        sys.stdout.write(completed.stdout)
        raise SystemExit(f"harness exited {completed.returncode}")
    return completed.stdout


def _span(start: date, end: date) -> str:
    return f"{start}..{'' if end == OPEN else end}"


def _spans_text(spans: Iterable[Interval]) -> str:
    return "[" + ", ".join(_span(*span) for span in spans) + "]"


def differential(engine_src: Path, root: Path, output: Path) -> int:
    root = root.resolve()
    binary = build_harness(engine_src)
    modules = tracked_modules(root)
    report = run_harness(binary, root, modules)
    output.write_text(report, encoding="utf-8")
    run = parse_engine_references(report.splitlines())
    static_modules = load_modules(root)
    static = all_references(static_modules)
    failures = coverage_failures(run, modules, late_start_edges(import_references(static_modules)))
    differences = reference_differences(run, static, static_modules)
    print(
        f"The engine compiled {len(run.compiled)} of {len(modules)} modules without citation "
        f"metadata and bound {len(run.bindings)} names in their own rules."
    )
    for module, error in sorted(run.refused.items())[:20]:
        reason = error.splitlines()[0].rsplit("`: ", 1)[-1] if error else ""
        print(f"  refused {module}: {reason}")
    if run.collisions:
        print(f"{len(run.collisions)} name(s) bound in both namespaces: {sorted(run.collisions)}")
    if differences.over_reported:
        print(f"{len(differences.over_reported)} static binding(s) over-reported by design:")
        for item in sorted(differences.over_reported)[:20]:
            print(f"  {item.rule} {item.version_start} -> {item.namespace} {item.name}")
    for label, items in (
        ("engine", differences.only_engine),
        ("static model", differences.only_static),
    ):
        if items:
            print(f"\n{len(items)} binding(s) only the {label} found:")
            for item in sorted(items, key=str)[:50]:
                print(
                    f"  {item.rule} {_span(item.version_start, item.version_end)} ->"
                    f" {item.namespace} {item.name} {_spans_text(item.coverage)}"
                )
    for label, rules in (
        ("the lowered program does not hold as the model does", differences.missing_rules),
        ("only the lowered program holds", differences.extra_rules),
    ):
        if rules:
            print(f"\n{len(rules)} declared name(s) {label}:")
            for rule, namespace, versions in sorted(rules)[:50]:
                print(f"  {rule} as a {namespace} {_spans_text(versions)}")
    for failure in failures:
        print(f"\nThis run does not cover the tree: {failure}")
    if (
        differences.only_engine
        or differences.only_static
        or differences.missing_rules
        or differences.extra_rules
        or failures
    ):
        return 1
    print("The static bindings equal the engine's.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    check_parser = sub.add_parser("check", help="compare edges with the baseline")
    check_parser.add_argument("--root", type=Path, default=REPO_ROOT)
    check_parser.add_argument("--baseline", type=Path)
    check_parser.add_argument(
        "--base-ref",
        help="protected base commit; no (rule, name) may stop on a date it does not",
    )
    check_parser.add_argument(
        "--allow-added",
        action="store_true",
        help=f"the pull request carries the {ACCEPT_LABEL} label",
    )

    baseline_parser = sub.add_parser("baseline", help="print the baseline matching this checkout")
    baseline_parser.add_argument("--root", type=Path, default=REPO_ROOT)

    differential_parser = sub.add_parser(
        "differential", help="compare static references with the pinned engine's"
    )
    differential_parser.add_argument("--engine-src", type=Path, required=True)
    differential_parser.add_argument("--root", type=Path, default=REPO_ROOT)
    differential_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "check":
        baseline_path = args.baseline or args.root / BASELINE_RELATIVE_PATH
        return check(args.root, baseline_path, args.base_ref, args.allow_added)
    if args.command == "differential":
        return differential(args.engine_src, args.root, args.output)
    edges = late_start_edges(import_references(load_modules(args.root)))
    sys.stdout.write(render_baseline(edges))
    return 0


if __name__ == "__main__":
    sys.exit(main())
