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
  composition may not write one. A formula name therefore resolves against the
  whole import closure.
* Scalars. Modules load the way the engine's serde_yaml reads them, not the way
  PyYAML does. Where the engine reads a string, an unquoted scalar keeps its
  text, so `name: TRUE` names a rule `TRUE`. Where it reads a value, `yes` stays
  a string, and so does an unquoted date. A date must read YYYY-MM-DD. The check
  refuses a module that writes out a tag, `!!merge` among them, rather than
  guess how serde_yaml would read it.
* Formulas. The check ports the engine's formula lexer, parser and lowering.
  rulespec.rs parses each formula on its own before it lowers any, and refuses
  the module when one does not parse to its end, so the port parses each
  formula alone. A word in a string or comment is not a reference, nor is a
  called function. The engine then lexes every rule's formula again as one
  source, so a formula that leaves a string open would run into the next rule;
  the check refuses that module.
* Namespaces. `kind` does not decide what a name binds to. A rule with `values`
  in any version is a parameter table, of either kind, and its versions without
  `values` do not exist at run time. Otherwise a rule with an `entity`, or with
  a version that is not a lone literal, is derived; the rest are parameters.
  The parser erases parentheses, so `(2)` is a literal, and a leading `-` is an
  operator, so `-2` is not. Parameters of one name merge, and a table of that
  name removes the others. Only `parameter` and `derived` rules carry versions
  the engine enforces at run time.
* Binding. The lowering decides what each name binds to, as lower_to_scalar
  and lower_to_judgment do. A name in a scalar position reads a parameter when
  one of that name exists, and otherwise a derived rule. A name in a judgment
  position (an `if` condition, `and`, `or`, `not`, `exactly_one`, and the whole
  formula of a rule whose dtype is Judgment) reads only a derived rule; a
  parameter there lowers to an input. In a scalar position `period_start` and
  `period_end` read the period. `x[i]` reads the parameter `x`. `len` reads no
  name, and drops the field it may carry. `sum(rel.f)`, `count_where` and
  `sum_where` read their fields and filters as derived rules or inputs. A
  formula the engine refuses to lower falls back to a token reader that reads
  each name it mentions both ways; `differential` fails when a module the
  engine compiles needs that fallback.
* Relations. A version that aggregates over a derived relation reads what the
  relation's predicate reads, as derived rules, on each date it runs. The
  engine evaluates the relation the predicate filters first, and a predicate
  can ask for membership of another relation, so the version reads through the
  whole chain. The check resolves each relation name as rulespec.rs does.
  rewrite_relation_references turns a name a module wrote into that module's
  own relation, `<module>#relation.<name>`. Where an aggregation reads an
  imported derived rule, it may instead take the one relation of that short
  name. rewrite_filtered_entity_member_aliases then sends a member alias to its
  filtered relation in each rule of that relation's entity.
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
relation a version asks for into its predicate and on through the relation it
filters. Those bindings must equal the static ones exactly, by rule, version
dates, name, namespace and every version of what the name binds to. For each
name a module declares, the namespaces and versions the lowered program holds
must also equal the static model's, both ways. The engine reattaches ids by
name, so it cannot say which module a colliding name came from; the static
model alone decides whether a binding crosses an import. The run must also
cover the tree: every module needs a result, every edge a compiled module, and
no module the engine compiled may need the token reader. It compiles a scratch
copy of the tree with citation metadata removed: that metadata decides nothing
here, and retired forms of it would otherwise stop the engine from loading most
of the references this check exists to compare.

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
label. The bound compares modeled stop dates: every date a version can read a
name that has no version there. A version that reads the name only in a branch
no query takes still holds those dates, so a change that makes the branch
reachable adds no stop date; its edge was already on the list. A correct date
repair can still widen a gap: it can expose one that was already in the law's
encoding, and fail closed where the module used to answer wrongly. The
`late-start-import-accepted` label on the pull request (`--allow-added`)
records that decision.

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

# formula.rs parse_dtype: these dtypes lower a rule's formula as a judgment.
JUDGMENT_DTYPES = frozenset({"Judgment", "judgment"})

# model.rs SCALAR_ENTITY: lower_module gives a derived rule with no entity this one.
SCALAR_ENTITY = "Scalar"

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
# input, never a parameter. The token reader uses this.
RELATION_CALLS = frozenset({"len", "count_where", "sum_where"})

# The token groups of formula.rs Lexer::tokenise, in its order, for the token
# reader and for finding a string a formula leaves open. `skip` yields no token,
# so a word inside it is never a name. A name holding a slash is the lexer's
# Path token: `a/b` is one name, not a division, and a rule may carry it. The
# lexer skips a docstring too, which runs to the end when nothing closes it;
# `open` is a quote the formula never closes.
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
    if isinstance(text.value, str):
        return dumper.represent_scalar("tag:yaml.org,2002:str", str(text), style='"')
    # A null, boolean or number keeps the text the module wrote: where the
    # engine reads a string it reads that text, so `name: NULL` stays `NULL`.
    return dumper.represent_scalar("!plain", str(text))


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
    # The rule's `dtype` and `entity` as the engine writes them into the formula
    # source; "" when it states none.
    dtype: str = ""
    entity: str = ""

    @property
    def start(self) -> date:
        return min(version.start for version in self.versions)

    @property
    def judgment(self) -> bool:
        """formula.rs lower_module lowers each version of this rule as a judgment."""
        return self.dtype in JUDGMENT_DTYPES


@dataclass(frozen=True)
class Relation:
    """A `data_relation` or `derived_relation` rule, as to_data_relation_spec and
    to_derived_relation_spec in rulespec.rs read it."""

    name: str
    derived: bool = False
    # The relation a derived relation filters, trimmed; "" when it names none.
    source: str = ""
    # The derived relation's one formula, trimmed: its predicate.
    predicate: str = ""
    # derived_relation.entity and .member_relation, which make `member` an alias
    # of this relation in each rule of that entity.
    entity: str | None = None
    member: str | None = None
    # The engine refuses the derived relation's shape: it states no arity or
    # source, or does not hold exactly one formula. `predicate` then joins
    # every formula it holds, for the token reader.
    refused: bool = False


@dataclass(frozen=True)
class Module:
    imports: tuple[str, ...] = ()
    # The parameter and derived rules, in file order.
    rules: tuple[Rule, ...] = ()
    # (target id, value id) for each `sets` source relation, in file order.
    sets: tuple[tuple[str, str], ...] = ()
    # Every rule name the module declares, of any kind, in file order; the
    # names of `rules` when the caller gives none.
    names: tuple[str, ...] = ()
    # The module states `module.kind`, so the engine compiles it on the composed
    # surface, where its own rules carry no id.
    composition: bool = False
    # Each data and derived relation, in file order.
    relations: tuple[Relation, ...] = ()
    # The names of the rules that state `kind: derived`, which a relation
    # predicate reads as derived rules; the derived-namespace names of `rules`
    # when the caller gives none.
    derived_kinds: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if not self.names:
            object.__setattr__(self, "names", tuple(rule.name for rule in self.rules))
        if self.derived_kinds is None:
            object.__setattr__(
                self,
                "derived_kinds",
                tuple(rule.name for rule in self.rules if rule.namespace == DERIVED),
            )


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


def token_reads(formula: str) -> tuple[dict[str, frozenset[str]], frozenset[str]]:
    """What the token reader says a formula reads, for a formula the engine
    refuses to lower: each name with the namespaces it can bind in, and the
    names it can use as relations.

    It reads more than any lowering could. A called name reads nothing. The
    object of a field access is a relation, and the field reads a derived rule
    or an input. Any other name can bind both ways, and can name a relation.
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


# ---------------------------------------------------------------------------
# A port of formula.rs at the pin: its lexer, its parser, and the part of its
# lowering that decides what a formula reads.
# ---------------------------------------------------------------------------


class FormulaError(ValueError):
    """A formula the engine's lexer, parser or lowering refuses."""


# The byte classes the lexer tests: u8::is_ascii_digit and its siblings.
_DIGITS = frozenset("0123456789")
_IDENT_START = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
_IDENT_CHARS = _IDENT_START | _DIGITS
_ASCII_WHITESPACE = frozenset(" \t\n\x0c\r")
# char::is_whitespace, which str::trim strips.
_RUST_WHITESPACE = (
    "\t\n\x0b\x0c\r \x85\xa0        "
    "        　"
)
# A keyword token's kind is its spelling, with `True` and `False` as `true` and `false`.
_KEYWORDS = {word: word for word in RESERVED} | {"True": "true", "False": "false"}
_PAIRS = frozenset({"=>", "<=", ">=", "==", "!=", "->"})
_SINGLES = frozenset(":,.=+-*/<>()[]")
_ESCAPES = {"\\": "\\", '"': '"', "'": "'", "n": "\n", "r": "\r", "t": "\t"}
_I64_MAX = 2**63 - 1


def rust_trim(text: str) -> str:
    """str::trim."""
    return text.strip(_RUST_WHITESPACE)


def _run(formula: str, position: int, chars: frozenset[str]) -> int:
    while position < len(formula) and formula[position] in chars:
        position += 1
    return position


def _string(formula: str, position: int) -> tuple[str, int]:
    """A quoted string from its opening quote: its value, and where it ends."""
    quote = formula[position]
    position += 1
    parts: list[str] = []
    start = position
    while position < len(formula):
        current = formula[position]
        if current == quote:
            parts.append(formula[start:position])
            return "".join(parts), position + 1
        if current == "\\":
            if position + 1 >= len(formula):
                raise FormulaError("unterminated string")
            parts.append(formula[start:position])
            parts.append(_ESCAPES.get(formula[position + 1], formula[position + 1]))
            position += 2
            start = position
            continue
        position += 1
    raise FormulaError("unterminated string")


def lex(formula: str) -> list[tuple[str, str]]:
    """formula.rs Lexer::tokenise, branch for branch: (kind, text) pairs that end
    with ("eof", ""). An operator's kind is the operator itself."""
    tokens: list[tuple[str, str]] = []
    size = len(formula)
    position = 0
    while position < size:
        if formula.startswith('"""', position):
            close = formula.find('"""', position + 3)
            position = size if close < 0 else close + 3
            continue
        char = formula[position]
        if char == "#":
            newline = formula.find("\n", position)
            position = size if newline < 0 else newline
            continue
        if char in _ASCII_WHITESPACE:
            position += 1
            continue
        if char in _DIGITS:
            chunk = formula[position : position + 10]
            if (
                len(chunk) == 10
                and chunk[4] == chunk[7] == "-"
                and all(item in _DIGITS for index, item in enumerate(chunk) if index not in (4, 7))
            ):
                tokens.append(("date", chunk))
                position += 10
                continue
            end = _run(formula, position, _DIGITS | {"_"})
            kind = "int"
            if end + 1 < size and formula[end] == "." and formula[end + 1] in _DIGITS:
                kind = "float"
                end = _run(formula, end + 1, _DIGITS | {"_"})
            tokens.append((kind, formula[position:end]))
            position = end
            continue
        if char in "\"'":
            value, position = _string(formula, position)
            tokens.append(("string", value))
            continue
        if char in _IDENT_START:
            end = _run(formula, position, _IDENT_CHARS)
            path_end = end
            while (
                path_end + 1 < size
                and formula[path_end] == "/"
                and formula[path_end + 1] in _IDENT_START
            ):
                path_end = _run(formula, path_end + 1, _IDENT_CHARS)
            if path_end > end:
                tokens.append(("path", formula[position:path_end]))
                position = path_end
            else:
                text = formula[position:end]
                tokens.append((_KEYWORDS.get(text, "ident"), text))
                position = end
            continue
        pair = formula[position : position + 2]
        if pair in _PAIRS:
            tokens.append((pair, pair))
            position += 2
            continue
        if char in _SINGLES:
            tokens.append((char, char))
            position += 1
            continue
        raise FormulaError(f"unexpected char {char!r}")
    tokens.append(("eof", ""))
    return tokens


# Nodes are tuples: ("int", digits), ("float", digits), ("str", value),
# ("bool", value), ("var", name), ("bin", operator, left, right), ("neg", x),
# ("not", x), ("call", function, arguments), ("field", object, name),
# ("index", target, index), ("cond", condition, then, else) and
# ("match", subject, ((pattern, result), ...), default or None).
_LITERALS = frozenset({"int", "float", "str", "bool"})
_COMPARISONS = frozenset({"<", ">", "<=", ">=", "==", "!="})
_PATTERN_STARTS = frozenset({"int", "float", "string", "true", "false", "ident"})


class _Parser:
    """formula.rs Parser, from parse_expr down."""

    def __init__(self, tokens: list[tuple[str, str]]) -> None:
        self.tokens = tokens
        self.position = 0

    def kind(self, offset: int = 0) -> str:
        return self.tokens[min(self.position + offset, len(self.tokens) - 1)][0]

    def take(self, kind: str | None = None) -> tuple[str, str]:
        token = self.tokens[min(self.position, len(self.tokens) - 1)]
        if kind is not None and token[0] != kind:
            raise FormulaError(f"expected {kind}, got {token[0]} ({token[1]})")
        self.position += 1
        return token

    def expr(self) -> tuple:
        if self.kind() == "ident" and self.kind(1) == "=":
            raise FormulaError("let-bindings are not supported in RuleSpec formulas yet")
        if self.kind() == "match":
            return self.match()
        if self.kind() == "if":
            return self.cond()
        return self.disjunction()

    def match(self) -> tuple:
        self.take("match")
        subject = self.disjunction()
        self.take(":")
        cases: list[tuple[tuple, tuple]] = []
        default = None
        while self.kind() in _PATTERN_STARTS and self.kind(1) == "=>":
            if default is not None:
                raise FormulaError("a match wildcard arm must be final")
            pattern = self.primary()
            self.take("=>")
            result = self.expr()
            if pattern == ("var", "_"):
                default = result
            else:
                cases.append((pattern, result))
        return ("match", subject, tuple(cases), default)

    def cond(self) -> tuple:
        self.take("if")
        condition = self.disjunction()
        self.take(":")
        then = self.expr()
        return ("cond", condition, then, self.otherwise())

    def otherwise(self) -> tuple:
        """parse_cond's else branch and parse_elif_chain."""
        if self.kind() == "elif":
            self.take()
            condition = self.disjunction()
            self.take(":")
            then = self.expr()
            return ("cond", condition, then, self.otherwise())
        self.take("else")
        self.take(":")
        return self.expr()

    def disjunction(self) -> tuple:
        left = self.conjunction()
        while self.kind() == "or":
            self.take()
            left = ("bin", "or", left, self.conjunction())
        return left

    def conjunction(self) -> tuple:
        left = self.comparison()
        while self.kind() == "and":
            self.take()
            left = ("bin", "and", left, self.comparison())
        return left

    def comparison(self) -> tuple:
        left = self.sum()
        if self.kind() in _COMPARISONS:
            return ("bin", self.take()[0], left, self.sum())
        return left

    def sum(self) -> tuple:
        left = self.product()
        while self.kind() in ("+", "-"):
            left = ("bin", self.take()[0], left, self.product())
        return left

    def product(self) -> tuple:
        left = self.unary()
        while self.kind() in ("*", "/"):
            left = ("bin", self.take()[0], left, self.unary())
        return left

    def unary(self) -> tuple:
        if self.kind() == "-":
            self.take()
            return ("neg", self.unary())
        if self.kind() == "not":
            self.take()
            return ("not", self.unary())
        return self.postfix()

    def postfix(self) -> tuple:
        node = self.primary()
        while True:
            if self.kind() == "(":
                if node[0] != "var":
                    raise FormulaError("can only call named functions")
                self.take()
                arguments = []
                if self.kind() != ")":
                    arguments.append(self.expr())
                    while self.kind() == ",":
                        self.take()
                        arguments.append(self.expr())
                self.take(")")
                node = ("call", node[1], tuple(arguments))
            elif self.kind() == ".":
                self.take()
                node = ("field", node, self.take("ident")[1])
            elif self.kind() == "[":
                self.take()
                index = self.expr()
                self.take("]")
                node = ("index", node, index)
            else:
                return node

    def primary(self) -> tuple:
        kind, text = self.take()
        if kind == "int":
            digits = text.replace("_", "")
            if int(digits) > _I64_MAX:
                raise FormulaError(f"{text} does not fit an i64")
            return ("int", digits)
        if kind == "float":
            return ("float", text.replace("_", ""))
        if kind == "string":
            return ("str", text)
        if kind in ("true", "false"):
            return ("bool", kind == "true")
        if kind in ("ident", "path"):
            return ("var", text)
        if kind == "(":
            node = self.expr()
            self.take(")")
            return node
        raise FormulaError(f"unexpected token in expression: {kind} ({text})")


_PARSED: dict[str, tuple | str] = {}


def parse_formula(formula: str) -> tuple:
    """The expression rulespec.rs compatibility_diagnostics parses from one
    formula: trimmed, one expression, then nothing. The engine refuses a module
    where any formula fails this, before it lowers anything."""
    parsed = _PARSED.get(formula)
    if parsed is None:
        try:
            parser = _Parser(lex(rust_trim(formula)))
            parsed = parser.expr()
            if parser.kind() != "eof":
                raise FormulaError("unexpected trailing token in formula")
        except FormulaError as error:
            parsed = str(error)
        except RecursionError:
            parsed = "the formula nests deeper than this port follows"
        _PARSED[formula] = parsed
    if isinstance(parsed, str):
        raise FormulaError(parsed)
    return parsed


def is_literal(formula: str) -> bool:
    """formula.rs is_literal_expr on the parsed formula: one number, string or
    boolean. A formula that does not parse is none."""
    try:
        return parse_formula(formula)[0] in _LITERALS
    except FormulaError:
        return False


@dataclass(frozen=True)
class Scope:
    """formula.rs LowerCtx: the names each kind of binding can take. lower_module
    gives a rule's formula the program's parameters and derived rules and no
    relation predicates; lower_judgment_formula gives a relation predicate no
    parameters."""

    scalars: frozenset[str] = frozenset()
    derived: frozenset[str] = frozenset()
    relation_predicates: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Aggregation:
    """A `len`, `sum`, `count_where` or `sum_where`: the relation it names, as
    written, and the derived rules its value and filter read, which decide
    whether rewrite_relation_references may take a relation by its short name."""

    relation: str
    derived: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Lowered:
    """What a lowered formula reads: (namespace, name) pairs, the aggregations it
    makes, and the relations whose membership it tests."""

    reads: frozenset[tuple[str, str]] = frozenset()
    aggregations: frozenset[Aggregation] = frozenset()
    members: frozenset[str] = frozenset()


@dataclass
class _Found:
    reads: set[tuple[str, str]] = field(default_factory=set)
    aggregations: set[Aggregation] = field(default_factory=set)
    members: set[str] = field(default_factory=set)


_ONE_ARGUMENT = frozenset(
    {"ceil", "floor", "sum_over_periods", "max_over_periods", "count_over_periods"}
)
_TWO_ARGUMENTS = frozenset(
    {"days_between", "date_add_days", "date_add_months", "date_add_years", "sum_top_n_over_periods"}
)


def _scalar(node: tuple, scope: Scope, found: _Found) -> None:
    """formula.rs lower_to_scalar."""
    kind = node[0]
    if kind in _LITERALS:
        return
    if kind == "var":
        name = node[1]
        if name in PERIOD_BOUNDS:
            return
        if name in scope.scalars:
            found.reads.add((PARAMETER, name))
        elif name in scope.derived:
            found.reads.add((DERIVED, name))
        return
    if kind == "index":
        target = node[1]
        if target[0] != "var":
            raise FormulaError("parameter lookup target must be a named parameter")
        if target[1] not in scope.scalars:
            raise FormulaError(f"`{target[1]}` is not a parameter table")
        found.reads.add((PARAMETER, target[1]))
        _scalar(node[2], scope, found)
        return
    if kind == "bin":
        if node[1] not in ("+", "-", "*", "/"):
            raise FormulaError(f"binary op {node[1]} in scalar position")
        _scalar(node[2], scope, found)
        _scalar(node[3], scope, found)
        return
    if kind == "neg":
        _scalar(node[1], scope, found)
        return
    if kind == "call":
        _call(node[1], node[2], scope, found)
        return
    if kind == "cond":
        _judgment(node[1], scope, found)
        _scalar(node[2], scope, found)
        _scalar(node[3], scope, found)
        return
    if kind == "match":
        _, subject, cases, default = node
        if not cases and default is None:
            raise FormulaError("empty match")
        _scalar(subject, scope, found)
        if default is not None:
            _scalar(default, scope, found)
        for pattern, result in cases:
            _scalar(pattern, scope, found)
            _scalar(result, scope, found)
        return
    if kind == "not":
        raise FormulaError("`not` in scalar position")
    raise FormulaError("bare field access in scalar position not supported")


def _relation_argument(argument: tuple | None, function: str) -> str:
    if argument is None or argument[0] != "var":
        raise FormulaError(f"{function} must name its relation and fields")
    return argument[1]


def _call(function: str, arguments: tuple, scope: Scope, found: _Found) -> None:
    """The calls lower_to_scalar knows. `len` and `sum` read only their first
    argument, and `len` drops the field it may carry."""
    if function in ("max", "min"):
        for argument in arguments:
            _scalar(argument, scope, found)
        return
    if function in _ONE_ARGUMENT or function in _TWO_ARGUMENTS:
        expected = 1 if function in _ONE_ARGUMENT else 2
        if len(arguments) != expected:
            raise FormulaError(f"{function} takes {expected} arg(s)")
        for argument in arguments:
            _scalar(argument, scope, found)
        return
    first = arguments[0] if arguments else None
    if function == "len":
        relation = first[1] if first is not None and first[0] == "field" else first
        found.aggregations.add(Aggregation(_relation_argument(relation, function)))
        return
    if function == "sum":
        if first is None or first[0] != "field":
            raise FormulaError("sum(...) requires a relation field access argument")
        derived = frozenset({first[2]}) & scope.derived
        found.reads.update((DERIVED, name) for name in derived)
        found.aggregations.add(Aggregation(_relation_argument(first[1], function), derived))
        return
    if function in ("count_where", "sum_where"):
        expected = 2 if function == "count_where" else 3
        if len(arguments) != expected:
            raise FormulaError(f"{function} takes {expected} args")
        names = [_relation_argument(argument, function) for argument in arguments]
        derived = frozenset(names[1:]) & scope.derived
        found.reads.update((DERIVED, name) for name in derived)
        found.aggregations.add(Aggregation(names[0], derived))
        return
    raise FormulaError(f"unknown function `{function}`")


def _judgment(node: tuple, scope: Scope, found: _Found) -> None:
    """formula.rs lower_to_judgment."""
    kind = node[0]
    if kind == "bool":
        return
    if kind == "var":
        name = node[1]
        if name in scope.derived:
            found.reads.add((DERIVED, name))
        elif name in scope.relation_predicates:
            found.members.add(name)
        return
    if kind == "bin" and node[1] in ("and", "or"):
        _judgment(node[2], scope, found)
        _judgment(node[3], scope, found)
        return
    if kind == "bin" and node[1] in _COMPARISONS:
        _scalar(node[2], scope, found)
        _scalar(node[3], scope, found)
        return
    if kind == "not":
        _judgment(node[1], scope, found)
        return
    if kind == "call" and node[1] == "exactly_one":
        if len(node[2]) < 2:
            raise FormulaError("exactly_one takes at least 2 arguments")
        for argument in node[2]:
            _judgment(argument, scope, found)
        return
    raise FormulaError(f"{kind} {node[1] if kind in ('bin', 'call') else ''} in judgment position")


def lower_formula(formula: str, scope: Scope, judgment: bool = False) -> Lowered:
    """What the engine reads when it lowers this formula in this scope, as a
    judgment or a scalar. Raises FormulaError where the engine refuses."""
    found = _Found()
    try:
        (_judgment if judgment else _scalar)(parse_formula(formula), scope, found)
    except RecursionError:
        raise FormulaError("the formula nests deeper than this port follows") from None
    return Lowered(frozenset(found.reads), frozenset(found.aggregations), frozenset(found.members))


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
    dtype = string_like(rule.get("dtype")) or ""
    entity = _raw_text(string_like(rule.get("entity")) or "", where)
    declared = scalar_value(rule.get("versions")) or []
    tabled = [version for version in declared if scalar_value(version.get("values"))]
    if tabled:
        return Rule(name, _dated(tabled, where), PARAMETER, True, dtype, entity)
    versions = _dated(declared or [rule], where)
    if not versions:
        return None
    if entity or not all(is_literal(item.formula) for item in versions):
        return Rule(name, versions, DERIVED, False, dtype, entity)
    return Rule(name, versions, PARAMETER, False, dtype, entity)


def parse_set(rule: Mapping[str, Any]) -> tuple[str, str] | None:
    """(target id, value id) when a rule states a `sets` relation the engine applies.
    apply_source_relation_sets reads the relation on a rule of any kind."""
    relation = rule.get("source_relation")
    if not isinstance(relation, Mapping) or relation.get("type") != "sets":
        return None
    target, value = ((string_like(relation.get(key)) or "").strip() for key in ("target", "value"))
    return (target, value) if "#" in target and "#" in value and target != value else None


def _null(item: Any) -> bool:
    return scalar_value(item) is None


def parse_relation(rule: Mapping[str, Any]) -> Relation | None:
    """A data or derived relation, as to_data_relation_spec and
    to_derived_relation_spec read it. The engine lowers a derived relation's one
    formula as a judgment, and evaluates it on each date a rule asks for the
    relation, whatever that formula's dates say."""
    kind = rule.get("kind")
    if kind == "data_relation":
        return Relation(str(rule["name"]))
    if kind != "derived_relation":
        return None
    body = scalar_value(rule.get("derived_relation"))
    body = body if isinstance(body, Mapping) else None
    source = ""
    if body is not None:
        # DerivedRelationRef reads `source` as an alias of `source_relation`.
        given = [body[key] for key in ("source_relation", "source") if key in body]
        if len(given) == 1 and isinstance(given[0], str) and not _null(given[0]):
            source = rust_trim(given[0])
    versions = scalar_value(rule.get("versions")) or []
    if not versions and not (
        _null(rule.get("formula"))
        and _null(rule.get("effective_from", rule.get("from")))
    ):
        # RuleDefinition::effective_versions: one version stated at the top level.
        versions = [rule]
    formulas = [rust_trim(string_like(version.get("formula")) or "") for version in versions]
    arity = scalar_value(body.get("arity")) if body is not None else None
    refused = (
        not isinstance(arity, int)
        or isinstance(arity, bool)
        or arity < 0
        or not source
        or len(formulas) != 1
        or not formulas[0]
    )
    return Relation(
        str(rule["name"]),
        True,
        source,
        " ".join(formulas) if refused else formulas[0],
        string_like(body.get("entity")) if body is not None else None,
        string_like(body.get("member_relation")) if body is not None else None,
        refused,
    )


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
        tuple(str(rule.get("name")) for rule in rules if rule.get("kind") == "derived"),
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
    # The module whose id apply_rule_ids gives every entry of a name.
    ids: dict[str, str] = field(default_factory=dict)

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
    built = Program(
        [entry for entry in scalars if entry.rule.name not in tabled] + tables, derived, ids
    )

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


_NAMESPACED = "#relation."


def _short(relation: str) -> str:
    """The name a module wrote for a relation, without `<module>#relation.`."""
    return relation.split(_NAMESPACED, 1)[-1]


def _relation_origin(relation: str) -> str | None:
    """The module a namespaced relation belongs to, which rewrite_relation_references
    resolves its derivation's names against; None for a bare name."""
    return relation.split(_NAMESPACED, 1)[0] if _NAMESPACED in relation else None


class _Root:
    """What one root's lowered program reads through its relations.

    It holds the scope lower_module gives a rule's formula and the scope
    lower_judgment_formula gives a relation predicate, the relations
    append_missing_relations merges, and the renames rewrite_relation_references
    and rewrite_filtered_entity_member_aliases make to the relations a formula
    names. engine.rs related_entity_ids evaluates a derived relation by
    evaluating the relation it filters and then its predicate on each member, so
    a version reads through every relation it reaches that way.
    """

    def __init__(
        self, origin: str, order: list[str], modules: Mapping[str, Module], built: Program
    ) -> None:
        self.built = built
        self.fell_back = False
        closure = [(owner, modules[owner]) for owner in order]
        self.derived_rules = [
            rule for _, module in closure for rule in module.rules if rule.namespace == DERIVED
        ]
        self.scope = Scope(
            frozenset(
                rule.name
                for _, module in closure
                for rule in module.rules
                if rule.namespace == PARAMETER
            ),
            frozenset(rule.name for rule in self.derived_rules),
        )
        self.predicate_scope = Scope(
            derived=frozenset(name for _, module in closure for name in module.derived_kinds or ()),
            relation_predicates=frozenset(
                relation.name for _, module in closure for relation in module.relations
            ),
        )
        # canonical_relation_id names a relation `<module>#relation.<name>`, or
        # leaves the name bare for a composition compiled as the root, whose own
        # rules carry no origin.
        explicit: list[tuple[str, Relation]] = []
        self.rewrites: dict[tuple[str, str], str] = {}
        for owner, module in closure:
            bare = owner == origin and module.composition
            for relation in module.relations:
                canonical = relation.name if bare else f"{owner}{_NAMESPACED}{relation.name}"
                if not bare:
                    self.rewrites[(owner, relation.name)] = canonical
                explicit.append((canonical, relation))
        canonicals: dict[str, set[str]] = defaultdict(set)
        for (_, name), canonical in self.rewrites.items():
            canonicals[name].add(canonical)
        self.unambiguous = {
            name: next(iter(found)) for name, found in canonicals.items() if len(found) == 1
        }
        self.derived_origins = {
            entry.rule.name: built.ids[entry.rule.name]
            for entry in built.derived
            if entry.rule.name in built.ids
        }
        # append_missing_relations: the first derived relation of a name supplies
        # its derivation.
        self.derivations: dict[str, Relation] = {}
        for canonical, relation in explicit:
            if relation.derived:
                self.derivations.setdefault(canonical, relation)
        self._lowered: dict[Relation, Lowered | None] = {}
        self.aliases: tuple[tuple[str, str, str], ...] = ()
        self.aliases = self._aliases(explicit)

    def _aliases(self, explicit: list[tuple[str, Relation]]) -> tuple[tuple[str, str, str], ...]:
        """rewrite_filtered_entity_member_aliases: (entity, alias, relation) for each
        relation the program still holds after rewrite_relation_references, in the
        program's order, whose derivation names an entity and a member alias."""
        names: list[str] = []
        bare = {canonical for canonical, _ in explicit if _NAMESPACED not in canonical}
        if bare:
            # lower_module emits the relations its aggregations name, sorted,
            # before append_missing_relations adds the explicit ones. Only a bare
            # explicit relation can merge into one of them.
            names = sorted(self._inferred())
        held = set(names)
        for canonical, _ in explicit:
            if canonical not in held:
                held.add(canonical)
                names.append(canonical)
        short_names = {name for _, name in self.rewrites}
        if bare & short_names:
            # rewrite_relation_references drops a relation of a namespaced short
            # name that nothing names after the rewrite.
            used = self._used(names)
            names = [name for name in names if name not in short_names or name in used]
        aliases = []
        for name in names:
            relation = self.derivations.get(name)
            if relation is not None and relation.entity is not None and relation.member is not None:
                aliases.append((relation.entity, relation.member, name))
        return tuple(aliases)

    def _lowered_rules(self) -> Iterable[tuple[Rule, Lowered]]:
        for rule in self.derived_rules:
            for version in rule.versions:
                try:
                    yield rule, lower_formula(version.formula, self.scope, rule.judgment)
                except FormulaError:
                    continue

    def _inferred(self) -> set[str]:
        """The relations lower_module infers: each name an aggregation gives."""
        return {item.relation for _, lowered in self._lowered_rules() for item in lowered.aggregations}

    def _used(self, names: list[str]) -> set[str]:
        """used_relation_names after rewrite_relation_references."""
        used = set()
        for rule, lowered in self._lowered_rules():
            origin = self.built.ids.get(rule.name)
            used.update(self._resolve(item, origin) for item in lowered.aggregations)
        for name in names:
            relation = self.derivations.get(name)
            if relation is None:
                continue
            origin = _relation_origin(name)
            used.add(self._exact(relation.source, origin))
            lowered = self._predicate(relation)
            if lowered is not None:
                used.update(self._resolve(item, origin) for item in lowered.aggregations)
                used.update(self._exact(member, origin) for member in lowered.members)
        return used

    def _exact(self, name: str, origin: str | None) -> str:
        """rewrite_relation_name: the relation of that name the same module declares."""
        if self.rewrites and origin is not None:
            return self.rewrites.get((origin, name), name)
        return name

    def _resolve(
        self, aggregation: Aggregation, origin: str | None, entity: str | None = None
    ) -> str:
        """The relation an aggregation evaluates. rewrite_relation_references takes
        the relation of that name the rule's own module declares, or, when none
        does and the aggregation reads a derived rule of another module, the one
        relation of that name. A member alias then applies to a rule of its
        entity; it never applies inside a relation predicate."""
        name = aggregation.relation
        if self.rewrites and origin is not None:
            exact = self.rewrites.get((origin, name))
            if exact is not None:
                name = exact
            elif _NAMESPACED not in name and any(
                self.derived_origins.get(item, origin) != origin for item in aggregation.derived
            ):
                name = self.unambiguous.get(name, name)
        if entity is not None:
            for alias_entity, alias, target in self.aliases:
                if alias_entity == entity and name == alias:
                    name = target
        return name

    def _predicate(self, relation: Relation) -> Lowered | None:
        """The predicate as to_derived_relation_spec lowers it, or None where the
        engine refuses the relation."""
        if relation not in self._lowered:
            lowered = None
            if not relation.refused:
                try:
                    lowered = lower_formula(relation.predicate, self.predicate_scope, judgment=True)
                except FormulaError:
                    pass
            self._lowered[relation] = lowered
        return self._lowered[relation]

    def _named(self, relations: Iterable[str]) -> list[str]:
        """For the token reader: every derived relation a name could reach."""
        names = set(relations)
        found = [name for name in self.derivations if _short(name) in names]
        return found + [target for _, alias, target in self.aliases if alias in names]

    def _follow(self, pending: list[str], reads: set[tuple[str, str]]) -> None:
        """Add what the engine reads when it evaluates these relations: for each
        derived one, the relation it filters and its predicate, which reads
        derived rules and can test membership of, or aggregate over, others."""
        seen: set[str] = set()
        while pending:
            name = pending.pop()
            relation = self.derivations.get(name)
            if relation is None or name in seen:
                continue
            seen.add(name)
            origin = _relation_origin(name)
            pending.append(self._exact(relation.source, origin))
            lowered = self._predicate(relation)
            if lowered is None:
                self.fell_back = True
                names, relations = token_reads(relation.predicate)
                reads.update((DERIVED, item) for item in names)
                pending.extend(self._named(relations))
                continue
            reads.update(lowered.reads)
            pending.extend(self._resolve(item, origin) for item in lowered.aggregations)
            pending.extend(self._exact(member, origin) for member in lowered.members)

    def version_reads(self, entry: Entry, version: Version) -> set[tuple[str, str]]:
        """(namespace, name) for each name the engine reads when it evaluates this
        version: what its formula binds, and what the relations it asks for read.
        A version `sets` copied keeps the relations its value's module resolved."""
        origin = self.built.ids.get(entry.source.split("#", 1)[1])
        try:
            lowered = lower_formula(version.formula, self.scope, entry.rule.judgment)
        except FormulaError:
            self.fell_back = True
            names, relations = token_reads(version.formula)
            reads = {(space, name) for name, spaces in names.items() for space in spaces}
            self._follow(self._named(relations), reads)
            return reads
        reads = set(lowered.reads)
        entity = entry.rule.entity or SCALAR_ENTITY
        self._follow([self._resolve(item, origin, entity) for item in lowered.aggregations], reads)
        return reads


@dataclass
class StaticModel:
    """Every binding the static model finds, and the roots where it read a
    formula the port refuses with the token reader instead."""

    references: set[Reference]
    fallbacks: set[str] = field(default_factory=set)


def static_model(modules: Mapping[str, Module]) -> StaticModel:
    """Every (rule version, name) binding, local ones included, for each module
    compiled as its own root. Only derived rules read names: a parameter's
    versions are literals or values. A version reads what its formula binds,
    and what the relations it asks for read. The coverage is every version of
    what the name binds to, merged parameters together, after the root's `sets`
    relations. The target names the earliest definition an import supplies, and
    this module only when nothing imported does.
    """
    references: set[Reference] = set()
    fallbacks: set[str] = set()
    for origin, module in modules.items():
        if not any(rule.namespace == DERIVED for rule in module.rules):
            continue
        order = flattened(origin, modules)
        built = program(origin, order, modules)
        if built is None:
            continue
        root = _Root(origin, order, modules, built)
        for rule in module.rules:
            if rule.namespace != DERIVED:
                continue
            own = [entry for entry in built.group(DERIVED, rule.name) if entry.owner == origin]
            if not own:
                continue
            entry = own[0]
            spans = windows(entry.rule.versions)
            for version in entry.rule.versions:
                for namespace, name in sorted(root.version_reads(entry, version)):
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
                                item.owner != origin or item.source.split("#", 1)[0] != origin
                                for item in group
                            ),
                        )
                    )
        if root.fell_back:
            fallbacks.add(origin)
    return StaticModel(references, fallbacks)


def all_references(modules: Mapping[str, Module]) -> set[Reference]:
    """Every binding the static model finds; see static_model."""
    return static_model(modules).references


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
    model = static_model(load_modules(root))
    references = {item for item in model.references if item.crosses}
    edges = late_start_edges(references)
    baseline = parse_baseline(baseline_path.read_text(encoding="utf-8"))
    wider: dict[tuple[str, str], tuple[Interval, ...]] = {}
    if base_ref:
        base = stop_dates(import_references(load_modules_at(root, base_ref)))
        wider = widened(stop_dates(references), base)
    verdict = compare(edges, baseline, {} if allow_added else wider)
    print(summarize(edges))
    if model.fallbacks:
        print(
            f"{len(model.fallbacks)} module(s) hold a formula the engine refuses to lower;"
            " the check reads those formulas with the token reader, which reads each"
            f" name both ways: {sorted(model.fallbacks)[:10]}"
        )
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
//! namespace holds. A version that asks for a derived relation also reads, on
//! the same dates, what engine.rs related_entity_ids evaluates for it: the
//! relation it filters, and so on down the chain, and its predicate, with each
//! relation that predicate asks for. A module the engine
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

/// A derived relation's predicate and the relation it filters, by name.
type Derivations = BTreeMap<String, (Value, String)>;

/// Every name a lowered expression reads, by namespace, from its tagged spec,
/// following each relation it asks for.
fn collect(
    value: &Value,
    derivations: &Derivations,
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
            if let Some(relation) = map.get("relation").and_then(Value::as_str) {
                follow(relation, derivations, followed, read);
            }
            map.values()
                .for_each(|child| collect(child, derivations, followed, read));
        }
        Value::Array(items) => items
            .iter()
            .for_each(|child| collect(child, derivations, followed, read)),
        _ => {}
    }
}

/// engine.rs related_entity_ids: a derived relation evaluates the relation it
/// filters, then its predicate on each member.
fn follow(
    relation: &str,
    derivations: &Derivations,
    followed: &mut BTreeSet<String>,
    read: &mut BTreeSet<(&'static str, String)>,
) {
    if let Some((predicate, source)) = derivations.get(relation)
        && followed.insert(relation.to_string())
    {
        collect(predicate, derivations, followed, read);
        follow(source, derivations, followed, read);
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
        let derivations: Derivations = program
            .relations
            .iter()
            .filter_map(|relation| {
                let derivation = relation.derivation.as_ref()?;
                let predicate =
                    serde_json::to_value(&derivation.predicate).expect("predicate as json");
                Some((relation.name.clone(), (predicate, derivation.source_relation.clone())))
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
                collect(&semantics, &derivations, &mut BTreeSet::new(), &mut read);
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
    run: EngineRun,
    tracked: Iterable[str],
    edges: Iterable[Edge],
    fallbacks: Iterable[str] = (),
) -> list[str]:
    """Why this run cannot vouch for the static model, however well it agreed. A
    module the engine compiled lowers every formula it holds, so the static
    model should have needed the token reader for none of them."""
    expected = {canonical_target(path) for path in tracked}
    failures = []
    if guessed := sorted(set(fallbacks) & run.compiled):
        failures.append(
            f"the port refused a formula in {len(guessed)} module(s) the engine compiled:"
            f" {guessed[:10]}"
        )
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
    # Declared names the lowered program does not hold as the model does: in
    # that namespace, with those versions.
    missing_rules: set[tuple[str, str, tuple[Interval, ...]]] = field(default_factory=set)
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
    expected = declared_rules(modules, sorted(run.compiled))
    return Differences(
        engine - in_scope,
        in_scope - engine,
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
    model = static_model(static_modules)
    edges = late_start_edges(item for item in model.references if item.crosses)
    failures = coverage_failures(run, modules, edges, model.fallbacks)
    differences = reference_differences(run, model.references, static_modules)
    print(
        f"The engine compiled {len(run.compiled)} of {len(modules)} modules without citation "
        f"metadata and bound {len(run.bindings)} names in their own rules."
    )
    for module, error in sorted(run.refused.items())[:20]:
        reason = error.splitlines()[0].rsplit("`: ", 1)[-1] if error else ""
        print(f"  refused {module}: {reason}")
    if run.collisions:
        print(f"{len(run.collisions)} name(s) bound in both namespaces: {sorted(run.collisions)}")
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
