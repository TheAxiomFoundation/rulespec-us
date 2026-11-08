"""A seeded formula differential: tools/late_start_imports.py against the pinned engine.

Each case puts one formula in a module of its own: as the only derived rule,
as a rule the engine writes another formula after, or as the predicate of a
local derived relation a rule counts. Every module imports a shared library,
and the harness compiles each one as a root. The cases mix hand-picked edges of the
grammar (literal limits, deep nesting, docstrings and strings left open,
wildcard matches, calls, aggregations, odd whitespace) with formulas generated
from the grammar and mutated by a character. For every case the port must
refuse exactly what the engine refuses and bind exactly what the engine binds,
with two documented exceptions:

* compile.rs validate_relation_derivation_graph refuses a root whose relation
  names a relation the program lacks, or whose relations form a cycle. The
  port does not model that refusal, so it reads such a root; the differential
  fails on any edge in a module the engine refuses.
* The port refuses a module whose formula leaves a docstring open before a
  later formula. The engine either refuses it too or compiles it without the
  later rule, and the test checks which.

It leaves out the two shapes the pinned engine crashes on instead of refusing:
nesting past its stack (a sum of 3,001 terms), and a string escaping a
non-ASCII character, where its lexer panics. The unit tests cover the port's
refusal of the second. The same tree then goes through run_harness's scratch
copy, which must report the same thing. These skip unless LATE_START_HARNESS
names the compiled harness, which the engine-differential job builds.
"""

from __future__ import annotations

import importlib.util
import os
import random
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

HARNESS = os.environ.get("LATE_START_HARNESS")
pytestmark = pytest.mark.skipif(not HARNESS, reason="the engine-differential job builds the harness")

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "late_start_imports.py"
_spec = importlib.util.spec_from_file_location("late_start_imports", TOOL_PATH)
lsi = importlib.util.module_from_spec(_spec)
sys.modules["late_start_imports"] = lsi
_spec.loader.exec_module(lsi)

# A backslash before a non-ASCII character: the pinned engine's lexer escapes
# one byte of it and panics slicing from inside it.
ENGINE_PANIC = re.compile(r"\\[^\x00-\x7f]")
GENERATED = 400


def quoted(text: str) -> str:
    """A YAML double-quoted scalar holding exactly this text."""
    import yaml

    return yaml.safe_dump(text, default_style='"', allow_unicode=False, width=10**9).strip()


LIB = """format: rulespec/v1
module: {}
rules:
  - name: p
    kind: parameter
    versions:
      - from: '1990-01-01'
        formula: '1'
  - name: shared
    kind: parameter
    versions:
      - from: '1990-01-01'
        formula: '2'
  - name: d
    kind: derived
    entity: Person
    dtype: Integer
    period: Month
    versions:
      - from: '2000-01-01'
        formula: p + 1
  - name: j
    kind: derived
    entity: Person
    dtype: Judgment
    period: Month
    versions:
      - from: '2000-01-01'
        formula: d > 1
  - name: rel
    kind: data_relation
    data_relation:
      predicate: rel
      arity: 2
  - name: drel
    kind: derived_relation
    derived_relation:
      arity: 2
      source_relation: rel
      current_slot: 1
      related_slot: 0
    versions:
      - effective_from: '2000-01-01'
        formula: j
"""

LIB2 = """format: rulespec/v1
module: {}
rules:
  - name: shared
    kind: derived
    entity: Person
    dtype: Integer
    period: Month
    versions:
      - from: '2010-01-01'
        formula: d * 2
"""

IMPORTS = "imports:\n  - us:statutes/1/lib\n  - us:statutes/1/lib2\n"


def rule_module(dtype: str, formula: str) -> str:
    return (
        "format: rulespec/v1\nmodule: {}\n" + IMPORTS + "rules:\n"
        "  - name: r\n    kind: derived\n    entity: Person\n"
        f"    dtype: {dtype}\n    period: Month\n    versions:\n"
        f"      - from: '2005-01-01'\n        formula: {formula}\n"
    )


def followed_module(dtype: str, formula: str) -> str:
    """The fuzzed rule, then a second derived rule the engine writes after it."""
    return rule_module(dtype, formula) + (
        "  - name: after\n    kind: derived\n    entity: Person\n    dtype: Integer\n"
        "    period: Month\n    versions:\n      - from: '2005-01-01'\n        formula: d + 1\n"
    )


def predicate_module(formula: str, reader: str) -> str:
    return (
        "format: rulespec/v1\nmodule: {}\n" + IMPORTS + "rules:\n"
        "  - name: lsrc\n    kind: data_relation\n    data_relation:\n"
        "      predicate: lsrc\n      arity: 2\n"
        "  - name: lrel\n    kind: derived_relation\n    derived_relation:\n"
        "      arity: 2\n      source_relation: lsrc\n      current_slot: 1\n"
        "      related_slot: 0\n    versions:\n"
        f"      - effective_from: '2000-01-01'\n        formula: {formula}\n"
        "  - name: r\n    kind: derived\n    entity: Person\n    dtype: Integer\n"
        "    period: Month\n    versions:\n"
        f"      - from: '2005-01-01'\n        formula: {reader}\n"
    )


SCALAR_NAMES = ["p", "shared", "d", "j", "x_in", "period_start", "period_end", "rel",
                "drel", "True", "TRUE", "None", "_", "a/b", "p/q/r", "P", "d2"]
JUDGMENT_NAMES = ["j", "d", "shared", "p", "x_in", "true", "false", "True", "False",
                  "TRUE", "rel", "drel", "period_start", "lsrc", "lrel"]
INTS = ["0", "1", "2", "10", "1_000", "007", "1__0", "1_", "9223372036854775807",
        "9223372036854775808", "18446744073709551616"]
FLOATS = ["1.5", "0.0", "1_0.5_0", "3.14159", "1.0", "1.5_", "0.000_1",
          "100000000000000000000000000000.5", "79228162514264337593543950335.0",
          "0.0000000000000000000000000001"]
STRINGS = ["'a'", '"b"', "''", "'a\\'b'", "'\\n'", "'\\q'", '"\\""', "'#'", "'a\\\\'",
           "'x y'", '"it\'s"']
DATES = ["2020-01-01", "1990-12-31", "2020-13-45"]
ONE_ARG = ["ceil", "floor", "sum_over_periods", "max_over_periods", "count_over_periods"]
TWO_ARG = ["days_between", "date_add_days", "date_add_months", "date_add_years",
           "sum_top_n_over_periods"]
BAD_FUNCS = ["abs", "round", "mean_over_periods", "min_over_periods", "exactly_one",
             "input_or_else", "Max", "lookup", "p", "d"]
CMP = ["<", ">", "<=", ">=", "==", "!="]
ODD_CHARS = list("!@$%{};|&\\?~`^") + ["=", ":", ",", ".", "[", "]", "(", ")", "'", '"',
                                         "#", "\x0b", "\xa0", " ", "　", "\x85",
                                         " ", "\x00", "\t", "\r", "\x0c", "/", "-", "_"]
SPACES = [" ", " ", " ", " ", "  ", "\t", "\n", "\r\n", "\r", "\x0c", " # c\n",
          ' """d""" ', "\n    ", "\x0b", "\xa0"]
DTYPES = ["Integer", "Judgment", "judgment", "JUDGMENT", "Boolean", "Bool", "bool",
          "Money", "Decimal", "Rate", "String", "Date", "Foo", "Integer "]


class Gen:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def ws(self) -> str:
        return " " if self.rng.random() < 0.9 else self.rng.choice(SPACES)

    def scalar_atom(self) -> str:
        roll = self.rng.random()
        if roll < 0.45:
            return self.rng.choice(SCALAR_NAMES)
        if roll < 0.7:
            return self.rng.choice(INTS)
        if roll < 0.82:
            return self.rng.choice(FLOATS)
        if roll < 0.9:
            return self.rng.choice(STRINGS)
        if roll < 0.95:
            return self.rng.choice(DATES)
        return self.rng.choice(["true", "false", "True", "False"])

    def judgment_atom(self) -> str:
        return self.rng.choice(JUDGMENT_NAMES)

    def pattern(self) -> str:
        return self.rng.choice(INTS[:6] + FLOATS[:3] + STRINGS[:3] +
                               ["true", "false", "True", "p", "x_in", "d", "period_start",
                                "-1", "(1)", "_"])

    def aggregation(self, depth: int) -> str:
        rng = self.rng
        relation = rng.choice(["rel", "drel", "rel", "x_in", "(rel)", "rel[0]", "p", "lrel",
                               "lsrc"])
        field = rng.choice(["d", "j", "shared", "p", "x_in", "d.e"])
        options = [
            f"len({relation})",
            f"len({relation}.{field})",
            "len()",
            f"len({relation}, {self.scalar(depth - 1)})",
            f"sum({relation}.{field})",
            f"sum({relation})",
            f"sum({relation}.{field}, {self.scalar(depth - 1)})",
            f"count_where({relation}, {rng.choice(JUDGMENT_NAMES)})",
            f"count_where({relation})",
            f"count_where({relation}, {self.judgment(depth - 1)})",
            f"count_where({relation}, j, j)",
            f"sum_where({relation}, {rng.choice(SCALAR_NAMES)}, {rng.choice(JUDGMENT_NAMES)})",
            f"sum_where({relation}, {self.scalar(depth - 1)}, j)",
            f"sum_where({relation}, d)",
        ]
        return rng.choice(options)

    def call(self, depth: int) -> str:
        rng = self.rng
        roll = rng.random()
        if roll < 0.3:
            name, arity = rng.choice(["max", "min"]), rng.choice([0, 1, 2, 3])
        elif roll < 0.55:
            name, arity = rng.choice(ONE_ARG), rng.choice([1, 1, 1, 0, 2])
        elif roll < 0.8:
            name, arity = rng.choice(TWO_ARG), rng.choice([2, 2, 2, 1, 3])
        else:
            name, arity = rng.choice(BAD_FUNCS), rng.choice([0, 1, 2])
        arguments = [self.scalar(depth - 1) for _ in range(arity)]
        return f"{name}({(',' + self.ws()).join(arguments)})"

    def scalar(self, depth: int) -> str:
        rng = self.rng
        if depth <= 0 or rng.random() < 0.25:
            return self.scalar_atom()
        kind = rng.choices(
            ["bin", "neg", "paren", "call", "agg", "index", "cond", "match", "field", "callon",
             "cmp"],
            [30, 5, 8, 14, 10, 6, 6, 5, 2, 2, 3],
        )[0]
        if kind == "bin":
            op = rng.choice(["+", "-", "*", "/"]) if rng.random() < 0.93 else rng.choice(
                CMP + ["and", "or"])
            return f"{self.scalar(depth - 1)}{self.ws()}{op}{self.ws()}{self.scalar(depth - 1)}"
        if kind == "cmp":
            return f"{self.scalar(depth - 1)} {rng.choice(CMP)} {self.scalar(depth - 1)}"
        if kind == "neg":
            return f"-{'' if rng.random() < 0.7 else ' '}{self.scalar(depth - 1)}"
        if kind == "paren":
            return f"({self.scalar(depth - 1)})"
        if kind == "call":
            return self.call(depth)
        if kind == "agg":
            return self.aggregation(depth)
        if kind == "index":
            target = rng.choice(["p", "p", "shared", "d", "x_in", "period_start", "(p)", "p.x",
                                 "j", "p[0]"])
            return f"{target}[{self.scalar(depth - 1)}]"
        if kind == "cond":
            parts = [f"if {self.judgment(depth - 1)}:{self.ws()}{self.scalar(depth - 1)}"]
            for _ in range(rng.choice([0, 0, 1, 2])):
                parts.append(f"elif {self.judgment(depth - 1)}: {self.scalar(depth - 1)}")
            if rng.random() < 0.95:
                parts.append(f"else:{self.ws()}{self.scalar(depth - 1)}")
            text = self.ws().join(parts)
            return f"({text})" if rng.random() < 0.6 else text
        if kind == "match":
            arms = [f"{self.pattern()} => {self.scalar(depth - 1)}"
                    for _ in range(rng.choice([0, 1, 1, 2, 3]))]
            if rng.random() < 0.7:
                arms.append(f"_ => {self.scalar(depth - 1)}")
            if rng.random() < 0.05:
                arms.append(f"{self.pattern()} => {self.scalar(depth - 1)}")
            text = f"match {self.scalar(depth - 1)}:" + "".join(
                self.rng.choice([" ", "\n  ", "\n"]) + arm for arm in arms)
            return f"({text})" if rng.random() < 0.6 else text
        if kind == "field":
            return f"{self.scalar_atom()}.{rng.choice(['d', 'x', 'j', 'p', '1'])}"
        return f"({self.scalar(depth - 1)})({self.scalar(depth - 1)})"

    def judgment(self, depth: int) -> str:
        rng = self.rng
        if depth <= 0 or rng.random() < 0.25:
            return self.judgment_atom()
        kind = rng.choices(
            ["and", "or", "not", "cmp", "exactly_one", "paren", "chain", "scalar", "cond"],
            [15, 12, 10, 25, 6, 8, 3, 3, 3],
        )[0]
        if kind in ("and", "or"):
            word = kind if rng.random() < 0.95 else kind.upper()
            return f"{self.judgment(depth - 1)} {word} {self.judgment(depth - 1)}"
        if kind == "not":
            return f"not {self.judgment(depth - 1)}"
        if kind == "cmp":
            return f"{self.scalar(depth - 1)}{self.ws()}{rng.choice(CMP)}{self.ws()}{self.scalar(depth - 1)}"
        if kind == "exactly_one":
            arguments = [self.judgment(depth - 1) for _ in range(rng.choice([0, 1, 2, 2, 3]))]
            return f"exactly_one({', '.join(arguments)})"
        if kind == "paren":
            return f"({self.judgment(depth - 1)})"
        if kind == "chain":
            return " ".join([self.scalar(0), rng.choice(CMP), self.scalar(0), rng.choice(CMP),
                             self.scalar(0)])
        if kind == "scalar":
            return self.scalar(depth - 1)
        return f"(if {self.judgment(depth - 1)}: {self.judgment(depth - 1)} else: {self.judgment(depth - 1)})"

    def mutate(self, text: str) -> str:
        rng = self.rng
        for _ in range(rng.choice([1, 1, 2])):
            roll = rng.random()
            position = rng.randrange(len(text) + 1)
            if roll < 0.3:
                text = text[:position] + rng.choice(ODD_CHARS) + text[position:]
            elif roll < 0.5 and text:
                position = min(position, len(text) - 1)
                text = text[:position] + text[position + 1:]
            elif roll < 0.65:
                end = min(len(text), position + rng.randrange(1, 6))
                text = text[:end] + text[position:end] + text[end:]
            elif roll < 0.85:
                spaces = [index for index, char in enumerate(text) if char == " "]
                if spaces:
                    index = rng.choice(spaces)
                    text = text[:index] + rng.choice(SPACES + ODD_CHARS[-12:]) + text[index + 1:]
            else:
                text = (rng.choice(["", " ", "\t", "\n", "\x0b", "\xa0", "　", "\x85",
                                    '"""doc"""\n', "# c\n", '"""'])
                        + text
                        + rng.choice(["", " ", "\n", "\x0b", "\xa0", " ", " # c",
                                      '"""', "\n\n"]))
        return text


EDGE_CASES = [
    ("Integer", text) for text in [
        "", " ", "#only a comment", '"""only a docstring"""', '"""unclosed', "1 # trailing",
        '"""a""" 1', '1 """a"""', "1\n", "\t1\t", "\x0b1", "1\x0b", "\xa01", "1\xa0", "　1",
        "1　", "\x851", "1\x85", "1 ", " 1", "1 \x0b 1", "1\r\n+ 1", "\x0c1",
        "a = 1", "p = 1", "(p = 1)", "p == 1", "1 < 2 < 3", "- - 1", "--1", "-(-1)", "1 - -1",
        "2 * -p", "-p[0]", "-len(rel)",
        "match d: 1 => 2 _ => 3", "match d: _ => 3", "match d: 1 => 2", "match d: _ => 3 1 => 2",
        "match d:", "match d: p => 1 _ => 0", "match d: 'a' => 1 _ => 0",
        "match d: true => 1 _ => 0", "match d: -1 => 1 _ => 0", "match d: 1.5 => 1 _ => 0",
        "match d: x_in => 1 _ => 0", "match d: period_start => 1 _ => 0",
        "match j: true => 1 _ => 0", "match d: 1 => match p: 2 => 3 _ => 4 _ => 5",
        "match d: 1 => (match p: 2 => 3 _ => 4) _ => 5", "match d: (1) => 2 _ => 3",
        "match d: 1 => 2 2 => 3", "match d 1 => 2", "match: 1 => 2",
        "if j: 1 else: 2", "if j: 1 elif d > 1: 2 else: 3", "if j: 1", "if d: 1 else: 2",
        "if 1: 1 else: 2", "if j: if j: 1 else: 2 else: 3", "if j: 1 else 2", "if j 1 else: 2",
        "if j: 1 elif j: 2", "1 + if j: 1 else: 2", "1 + (if j: 1 else: 2)",
        "max()", "min()", "max(p)", "max(p, d, 1)", "ceil(p)", "ceil()", "ceil(p, d)",
        "floor(1.5)", "days_between(period_start, period_end)", "date_add_days(period_start, 1)",
        "sum_over_periods(d)", "sum_top_n_over_periods(d, 3)", "mean_over_periods(d)",
        "count_over_periods(j)", "max_over_periods(d)", "len(rel)", "len(rel.d)", "len(drel)",
        "len(rel.x.y)", "len((rel))", "len(rel[0])", "len()", "len(1)", "sum(rel.d)", "sum(rel)",
        "sum((rel).d)", "sum(rel.d.e)", "sum(rel.shared)", "sum(drel.j)", "sum(rel.p)",
        "count_where(rel, j)", "count_where(rel, d)", "count_where(rel, p)",
        "count_where(rel, x_in)", "count_where(rel, 1)", "count_where(rel)",
        "count_where(drel, shared)", "sum_where(rel, d, j)", "sum_where(rel, p, j)",
        "sum_where(rel, d)", "sum_where(rel, shared, shared)", "exactly_one(j, j)",
        "p[0]", "p[d]", "p[p[0]]", "d[0]", "x_in[0]", "period_start[0]", "(p)[0]", "p[0][1]",
        "p.x", "rel.d", "p(1)", "(p)(1)", "p()", "1(2)", "'a'(1)", "f(1)(2)", "max(1)(2)",
        "shared", "shared + 1", "-shared", "shared[0]", "max(shared)", "(shared)",
        "1_000", "1__0", "1_", "1._5", "1.5_", "1.", ".5", "1.5.5", "1e5", "0x10",
        "9223372036854775807", "9223372036854775808", "-9223372036854775808",
        "99999999999999999999.5", "1" + "0" * 40 + ".0", "0.000000000000000000000000000001",
        "79228162514264337593543950335.0", "79228162514264337593543950336.0",
        "2020-01-01", "2020-13-45", "2020-01-01 + 1", "date_add_days(2020-01-01, 1)",
        "2020-1-01", "20200-01-01", "2020_01_01",
        "'a'", '"a"', "'a\\'b'", "'\\n'", "'\\q'", "'unterminated", "'a' + 1", "'a\\",
        "True", "False", "TRUE", "true", "None", "null", "NULL", "and", "or", "not", "if",
        "else", "elif", "match", "entity", "from", "amend", "_", "__", "_x",
        "a/b", "a/b/c", "a/1", "a/ b", "p/q + 1", "p /q", "p/ q", "rel/d",
        "1 => 2", "1 -> 2", "1 != 2", "1 <> 2", "1 ! 2", "1 = 2", "1 == 2", "1 : 2", "1, 2",
        "(1, 2)", "[1]", "a.b.c", "p..x", "p.", ".p", "()", "(", ")", "1)", "(1",
        "(" * 60 + "1" + ")" * 60, "(" * 120 + "1" + ")" * 120, "(" * 400 + "1" + ")" * 400,
        "-" * 150 + "1", "-" * 600 + "1", "max(" * 120 + "1" + ")" * 120,
        "p[" * 150 + "1" + "]" * 150,
        # Literal limits: i64 for an integer token, rust_decimal's 96-bit
        # mantissa for a float token, and CPython's 4,300-digit int() limit.
        "0009223372036854775807", "9_223_372_036_854_775_807", "9_223_372_036_854_775_808",
        "1" * 5000, "0" * 5000 + "7", "9" * 4301, "0" * 4400 + "1",
        "79228162514264337593543950335.4", "79228162514264337593543950335.5",
        "79228162514264337593543950335.49999", "79228162514264337593543950336.0",
        "7922816251426433759354395033_5.5", "7_9228162514264337593543950335.4",
        "0" * 40 + "79228162514264337593543950335.5", "0" * 40 + "79228162514264337593543950335.4",
        "79228162514264337593543950334.9999999999999999999999999999999",
        "1." + "9" * 5000, "0" * 5000 + "1.5", "1" * 5000 + ".5", "0." + "0" * 60 + "1",
        "p + 79228162514264337593543950335.5", "-79228162514264337593543950335.4",
        # Docstrings left open: the last formula the module writes may leave one.
        '1 """', '"""a""', 'p + """b', '"""doc"""\nd"""', 'd """ # c', "'a' \"\"\"",
        '1 """\n"""', '"""\n', '1 \'"""\'', '1 # """',
        # Deep nesting the engine still lowers.
        "(" * 2000 + "1" + ")" * 2000, "p[" * 1000 + "1" + "]" * 1000,
        "-" * 2000 + "1", "1" + " + 1" * 1500, "max(" * 1000 + "1" + ")" * 1000,
    ]
] + [
    ("Judgment", text) for text in [
        "j", "true", "false", "True", "TRUE", "d", "p", "x_in", "shared", "rel", "drel",
        "j and j", "j AND j", "j and not j", "not not j", "not j == d", "not (j == d)",
        "j == j", "d > 1", "d > 1 > 0", "p > 1", "shared > 1", "exactly_one(j, j)",
        "exactly_one(j)", "exactly_one()", "exactly_one(j, d > 1, not j)", "1", "1 + 1",
        "if j: j else: j", "match j: true => true _ => false", "(j)", "((j))", "j or",
        "len(rel) > 0", "count_where(rel, j) > 0", "period_start > 2020-01-01",
        "not " * 300 + "j", "(" * 120 + "j" + ")" * 120, "j" + " and j" * 3000,
        "exactly_one(j, j)(1)", "j[0]", "j.x", "max(1) > 0", "'a' == 'b'",
        "j \"\"\"", "not " * 4000 + "j", "j" + " and j" * 3000, "(" * 1500 + "j" + ")" * 1500,
        "d > 79228162514264337593543950335.5", "d > " + "1" * 5000,
    ]
] + [
    (dtype, text) for dtype in DTYPES for text in ["j", "d + 1", "1"]
]

PREDICATE_EDGES = [
    "j", "d > 1", "shared > 1", "p > 1", "rel", "drel", "lsrc", "lrel", "x_in", "true",
    "not rel", "rel and j", "lsrc or drel", "count_where(rel, j) > 0", "len(lsrc) > 0",
    "len(lrel) > 0", "count_where(drel, j) > 1", "sum(rel.d) > 1", "exactly_one(rel, lsrc)",
    "1", "d", "p", "if j: j else: j", "j and", "period_start > period_end",
]


def generate(rng: random.Random, total: int) -> list[tuple[str, str, str, str]]:
    """(label, kind, dtype or reader, formula)."""
    gen = Gen(rng)
    cases = [(f"edge{index}", "rule", dtype, text) for index, (dtype, text) in enumerate(EDGE_CASES)]
    cases += [(f"pedge{index}r{number}", "predicate", reader, text)
              for index, text in enumerate(PREDICATE_EDGES)
              for number, reader in enumerate(("len(lrel)", "count_where(lrel, j)"))]
    # The same formula with a second formula written after it, for every edge
    # case that holds a quote.
    cases += [(f"aedge{index}", "after", dtype, text)
              for index, (dtype, text) in enumerate(EDGE_CASES) if '"' in text or "'" in text]
    for index in range(total):
        roll = rng.random()
        depth = rng.choice([1, 2, 2, 3, 3, 4, 5])
        if roll < 0.06:
            formula = gen.mutate(gen.scalar(depth))
            cases.append((f"a{index}", "after", "Integer", formula))
            continue
        if roll < 0.15:
            reader = rng.choice(["len(lrel)", "count_where(lrel, j)", "sum(lrel.d)"])
            formula = gen.judgment(depth)
            if rng.random() < 0.2:
                formula = gen.mutate(formula)
            cases.append((f"p{index}", "predicate", reader, formula))
            continue
        judgment = roll < 0.5
        formula = gen.judgment(depth) if judgment else gen.scalar(depth)
        if rng.random() < 0.2:
            formula = gen.mutate(formula)
        dtype = "Judgment" if judgment else "Integer"
        if rng.random() < 0.08:
            dtype = "Integer" if judgment else "Judgment"
        if rng.random() < 0.03:
            dtype = rng.choice(DTYPES)
        cases.append((f"g{index}", "rule", dtype, formula))
    return cases


def write_tree(root: Path, cases) -> list[str]:
    base = root / "us" / "statutes" / "1"
    base.mkdir(parents=True)
    (base / "lib.yaml").write_text(LIB, encoding="utf-8")
    (base / "lib2.yaml").write_text(LIB2, encoding="utf-8")
    paths = ["us/statutes/1/lib.yaml", "us/statutes/1/lib2.yaml"]
    for label, kind, extra, formula in cases:
        writer = {"rule": rule_module, "after": followed_module}.get(kind)
        text = writer(extra, quoted(formula)) if writer else predicate_module(quoted(formula), extra)
        (base / f"{label}.yaml").write_text(text, encoding="utf-8")
        paths.append(f"us/statutes/1/{label}.yaml")
    return paths


def direct_run(root: Path, paths: list[str]) -> "lsi.EngineRun":
    """The harness over the files as written, with no scratch copy."""
    listing = root.parent / "modules.txt"
    listing.write_text("".join(f"{path}\n" for path in paths), encoding="utf-8")
    done = subprocess.run(
        [HARNESS, str(root), str(listing), str(root.parent / "composed")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr[-2000:]
    return lsi.parse_engine_references(done.stdout.splitlines())


def _relation_graph(reason: str) -> bool:
    return "unknown relation dependency" in reason or "cyclic relation dependency" in reason


@pytest.mark.parametrize("seed", [1, 2])
def test_the_port_lowers_each_formula_as_the_engine_does(tmp_path, seed):
    cases = [
        case for case in generate(random.Random(seed), GENERATED) if not ENGINE_PANIC.search(case[3])
    ]
    root = tmp_path / "rulespec-us"
    paths = write_tree(root, cases)
    run = direct_run(root, paths)
    modules, unparsed = {}, {}
    for path in paths:
        target = lsi.canonical_target(path)
        try:
            modules[target] = lsi.parse_module((root / path).read_text(encoding="utf-8"), path)
        except ValueError as error:
            unparsed[target] = str(error)
    model = lsi.static_model(modules)

    def parsed(rule: str) -> bool:
        return rule.split("#", 1)[0] in modules

    parsed_run = lsi.EngineRun(
        {origin for origin in run.results if origin in modules},
        {origin for origin in run.compiled if origin in modules},
        {origin: error for origin, error in run.refused.items() if origin in modules},
        {item for item in run.bindings if parsed(item.rule)},
        {item for item in run.inputs if parsed(item.rule)},
        {item for item in run.collisions if parsed(item)},
        {item for item in run.rules if parsed(item[0])},
    )
    differences = lsi.reference_differences(parsed_run, model.references, modules)
    mismatched = defaultdict(list)
    for item in differences.only_engine | differences.only_static:
        mismatched[item.rule.split("#", 1)[0]].append(item)
    for rule, namespace, versions in differences.missing_rules | differences.extra_rules:
        mismatched[rule.split("#", 1)[0]].append((rule, namespace, versions))

    tally = defaultdict(int)
    disagreements = []
    for path, (label, kind, extra, formula) in zip(paths[2:], cases):
        origin = lsi.canonical_target(path)
        assert origin in run.results, f"no result for {label}"
        engine_ok = origin in run.compiled
        port_ok = origin not in model.fallbacks and origin not in unparsed
        if kind == "after" and "leaves a docstring open" in unparsed.get(origin, ""):
            kept = any(rule == f"{origin}#after" for rule, _, _ in run.rules)
            if engine_ok and kept:
                disagreements.append(("the engine kept the later rule", label, formula))
            tally["open docstring" if engine_ok else "refused"] += 1
        elif engine_ok and port_ok:
            if mismatched.get(origin):
                disagreements.append(("bindings differ", label, formula, mismatched[origin]))
            tally["compiled"] += 1
        elif not engine_ok and not port_ok:
            tally["refused"] += 1
        elif engine_ok:
            disagreements.append(("only the port refuses", label, formula, unparsed.get(origin)))
        elif _relation_graph(run.refused.get(origin, "")):
            tally["relation graph"] += 1
        else:
            disagreements.append(("only the engine refuses", label, formula, run.refused.get(origin)))
    assert disagreements == []
    # The agreement means little unless the cases reach each side of it.
    assert tally["compiled"] > 300 and tally["refused"] > 250 and tally["open docstring"] > 0

    scratch = lsi.parse_engine_references(lsi.run_harness(Path(HARNESS), root, paths).splitlines())
    assert scratch.compiled == run.compiled
    assert scratch.bindings == run.bindings
    assert scratch.rules == run.rules
