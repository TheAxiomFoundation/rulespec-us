"""Validate, verify and aggregate the source-conflict register.

`known-source-conflicts.yaml`, at the root of a rulespec repository, records
the places where a jurisdiction's sources disagree (statute against
regulation, regulation against an agency manual, one manual section against
another), the readings each side supports, and the reading adopted. Every
rulespec repository keeps its own register; the Axiom-wide view is generated
by aggregating them (`aggregate`), never kept as a second copy.

Each entry's interpretation core has the field names and status rules of a
RuleSpec `module.interpretations` v1 entry (question, texts, reading,
alternatives, basis, status, ruling, confirmation), so an entry moves into a
module unchanged when its provision is encoded; the module then adds
`affects`. Register-only fields carry what a module cannot: the jurisdiction
and program, provisions not yet in the corpus (`pending_texts`, checked
against pinned snapshots), whether the adopted reading computes or refuses
contested cases (`outcome`), the modules that adopt the entry as
(module path, interpretation id) pairs (`adopted_by`), code outside RuleSpec
that adopts a reading (`implementations`), the tests that pin each reading
(`tests`) and an invented money case (`money_case`).

Three commands:

- `check` (offline; runs inside the required Repository Checks pytest leg via
  tests/test_source_conflicts.py): the schema, the status rules, public-repo
  hygiene, and every reference into this checkout: adopting modules carry the
  entry verbatim as a `module.interpretations` entry whose `affects` names
  real rules, in-repo test files define their pinned tests (a syntactic
  screen, which says nothing about running), and every ruled, confirmed or
  contradicted module interpretation whose texts cite two or more provisions
  (provisions in tension) is registered; an unregistered open one is a
  warning, listed by the workflow. No global id may also be a household
  choice's (household-choices.yaml; tools/household_choices.py), checked by
  one function both files' checks call.
- `verify` (network; the source-conflicts workflow): every `texts` excerpt is
  verbatim at its citation in the pinned corpus release, and every
  `pending_texts` excerpt is verbatim in its pinned snapshot, both judged by
  axiom-encode's own proof-atom matcher; snapshot hashes match; external
  implementations and test files exist at their pinned commits, each test
  file defines its pinned test (the same screen), and each implementation's
  `cites_entry` claim matches the file. Running the pinned tests is
  tools/pin_runner.py's job (the workflow's isolated `pinned-tests` job).
- `aggregate` (network): collect every rulespec repository's register into
  one JSON or Markdown view, checking that global ids are unique and each
  entry's jurisdiction belongs to its repository.

See tools/README.md ("Source-conflict register").
"""

from __future__ import annotations

import argparse
import ast
import bisect
import contextlib
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

REGISTER_FILENAME = "known-source-conflicts.yaml"
# The household-choices file (tools/household_choices.py) sits beside the
# register. Its ids share the register's global-id namespace, so `check` on
# either file refuses an id the other file uses (id_collision_issues).
CHOICES_FILENAME = "household-choices.yaml"
SCHEMA_VERSION = 1
CONTENT_DIRS = ("statutes", "regulations", "policies", "legislation")
ORGANISATION = "TheAxiomFoundation"

KEBAB_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
JURISDICTION_RE = re.compile(r"[a-z]{2}(-[a-z0-9]+)*")
COMMIT_RE = re.compile(r"[0-9a-f]{40}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
REPO_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+")
DECIMAL_RE = re.compile(r"(0|[1-9][0-9]*)(\.[0-9]+)?")
CURRENCY_RE = re.compile(r"[A-Z]{3}")
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
# A canonical corpus citation path: jurisdiction, document class, then one or
# more segments (us/statute/42/403/a/5, uk-babergh/manual/<doc>/page-87).
# `verify` additionally runs axiom-encode's own canonical-path check.
CORPUS_PATH_RE = re.compile(
    r"[a-z]{2}(-[a-z0-9]+)*/[a-z][a-z-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)+"
)
TEST_NAME_RE = re.compile(r"(?P<scope>[A-Za-z_][A-Za-z0-9_]*::)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
INLINE_TAG_RE = re.compile(
    r"(?i)</?(?:a|abbr|b|bdi|bdo|cite|code|data|dfn|e|em|font|fr|i|kbd|mark|q|s|samp"
    r"|small|span|strong|su|sub|sup|time|u|var|wbr)\b[^>]*>"
)
PERIODS = ("once", "week", "month", "year")
STATUSES = ("open", "ruled", "confirmed", "contradicted")
OUTCOMES = ("computed", "refused")
# The principle a consumer's own ruling applies (implementations[].ruling.principle,
# optional). Register-only, so a module interpretation's core is unchanged. These are
# PolicyEngine's: statute over forms, instructions and practice; regulations as law;
# the administering agency's reading on a true tie; the taxpayer's cheapest choice.
PRINCIPLES = ("statute-first", "regulations-are-law", "agency-breaks-ties", "taxpayer-choice")
# A reading reference (`follows`, `adopts`, `pins`) is `reading` (the entry's
# adopted reading) or the `id` of one of its alternatives. Positions are never
# used: inserting or reordering an alternative must not flip a consumer's pick.
ADOPTED_READING = "reading"

# What kind of source a text is. Corpus `texts` take their kind from the
# document class in their citation path (DOCUMENT_CLASS_KINDS); `text_kinds`
# may narrow it to another kind that class allows. `pending_texts` and
# `unpublished_sources` state theirs.
SOURCE_KINDS = (
    "statute",
    "regulation",
    "rulemaking",
    "form",
    "instructions",
    "worksheet",
    "manual",
    "guidance",
    "policy",
    "plan",
    "calculator",
    "agency-practice",
)
# Corpus document class (the second segment of a citation path) -> the kinds a
# text in that class may be; the first is the kind derived when `text_kinds`
# names none. A class without a row fails closed: a text citing it is a
# finding until the class gets a row here, so a new class never silently
# allows every kind. tests/test_source_conflicts.py checks every class the
# corpus uses has a row.
DOCUMENT_CLASS_KINDS: dict[str, tuple[str, ...]] = {
    "statute": ("statute",),
    "regulation": ("regulation",),
    "rulemaking": ("rulemaking",),
    "form": ("form", "instructions", "worksheet"),
    "guidance": ("guidance", "instructions", "calculator", "plan"),
    "manual": ("manual",),
    "policy": ("policy", "manual", "guidance", "plan"),
    "district-plan": ("plan",),
}
# `years.type`: which year the bounds count. `program` needs `years.note`
# saying what the program year is (SNAP's federal fiscal year, a LIHEAP
# program year from October, ...).
YEAR_TYPES = ("calendar", "tax", "federal-fiscal", "state-fiscal", "program")
MIN_YEAR, MAX_YEAR = 1900, 2100
# `conflict`: whether the sources still disagree. `resolved` needs a
# `resolution` (who closed it, when, and a public record) and `years.to`;
# `live` (the default) forbids a `resolution`.
CONFLICT_STATES = ("live", "resolved")
RESOLVERS = ("legislation", "agency")
# An unpublished source (correspondence, a call) is described, never quoted:
# a description may hold at most this many words inside quotation marks, in
# all its quoted spans together (quoted_spans says what a span is).
MAX_QUOTED_WORDS = 4
# The marks the scanner reads: every character Unicode gives the
# Quotation_Mark property (PropList.txt), plus primes and the quotation-mark
# ornaments, which are typed as quotation marks too.
#
# Pass-1 delimiters: each opening mark and the marks that may close it. The
# reversed and same-direction forms (»…«, ›…‹, ”…”, »…») are the usual ones
# in German, Danish, Swedish and Finnish, and „ and ‚ close with either curly
# mark (German „…“, Polish „…”).
_DELIMITERS: dict[str, str] = {
    '"': '"',
    "\u201c": "\u201d",
    "\u201e": "\u201c\u201d",
    "\u201a": "\u2018\u2019",
    "\u201f": "\u201d",
    "\u2e42": "\u201c\u201d",
    "\u00ab": "\u00bb",
    "\u2039": "\u203a",
    "\u201d": "\u201d",
    "\u00bb": "\u00ab\u00bb",
    "\u203a": "\u2039\u203a",
    "\u300c": "\u300d",
    "\u300e": "\u300f",
    "\ufe41": "\ufe42",
    "\ufe43": "\ufe44",
    "\uff62": "\uff63",
    "\u301d": "\u301e\u301f",
    "\uff02": "\uff02",
    "\u2033": "\u2033",
    "\u2036": "\u2033",
    "\u275d": "\u275e",
    "\u2760": "\u275e",
    "\u276e": "\u276f",
    "\U0001f676": "\U0001f677",
    "\U0001f678": "\U0001f676\U0001f677",
}
# These marks also close another pair, so they open only where an opener
# would and before a non-space (_opens_delimited): the inch marks in 6” and
# 6″ open nothing.
_CONTEXT_OPENERS = frozenset("\u201d\u00bb\u203a\u2033")
# Openers that also close another pair (“ closes „, « closes », …).
_ALSO_CLOSES = frozenset(mark for mark in _DELIMITERS if any(mark in closers for opener, closers in _DELIMITERS.items() if opener != mark))
_DELIMITER_CLOSE = {mark: re.compile("[" + re.escape(closers) + "]") for mark, closers in _DELIMITERS.items()}
# Every delimiter mark, opening or closing: the nested reading steps through them.
_DELIMITER_MARKS = frozenset("".join(_DELIMITERS) + "".join(_DELIMITERS.values()))
_DELIMITER_MARK = re.compile("[" + re.escape("".join(sorted(_DELIMITER_MARKS))) + "]")
_DELIMITED_READINGS = ("standard", "strict", "nested")
# Single marks that may open a quotation. Any quotation mark may close the
# single span (_closes_single), so a single quotation closed by a double mark
# (‘…”) still counts.
_SINGLE_OPENERS = frozenset("'\u2018\u2019\uff07\u201b\u2032\u2035\u275b\u275f")
_SINGLE_MARKS = _SINGLE_OPENERS | frozenset("\u275c")
_QUOTATION_MARKS = _DELIMITER_MARKS | _SINGLE_MARKS
# Unicode categories an opening mark may directly follow, besides whitespace
# and a slash: opening brackets (Ps), dashes (Pd) and opening quotation marks
# (Pi).
_BEFORE_OPENER_CATEGORIES = frozenset({"Ps", "Pd", "Pi"})
_PREFIX_MARKS = frozenset("/:\uff1a")  # a slash, a colon, a fullwidth colon
# The prefixes a single opener could follow on main, for the main floor.
_ASCII_BEFORE_OPENER = frozenset(" \t\n\r([{\u2014\u2013-/")


def _opener_prefix(text: str, index: int) -> bool:
    """The mark starts the text or follows whitespace (any Unicode space,
    such as a no-break space), a slash, a colon, an opening bracket, a dash
    or a quotation mark (so ""one" two" nests, and so does said:"…" inside
    a quotation a stray mark left open)."""

    if index == 0:
        return True
    before = text[index - 1]
    return (
        before.isspace() or before in _PREFIX_MARKS or before in _QUOTATION_MARKS
        or unicodedata.category(before) in _BEFORE_OPENER_CATEGORIES
    )


def _word_char(char: str) -> bool:
    """A letter or a decimal digit."""

    return char.isalpha() or unicodedata.category(char) == "Nd"


def _opens_single(text: str, index: int) -> bool:
    """A single mark may open a quotation unless it ends the text or is an
    ambiguous opener (_ambiguous_opener: it directly follows a letter or
    digit). So the apostrophes in "agency's", "the workers'" and 6'7 open
    nothing, while 'one, wrote:'one, ('one, '30 days, ' one and the elided
    year in "the '90s" all may."""

    return index + 1 < len(text) and not _ambiguous_opener(text, index)


def _closes_single(text: str, index: int) -> bool:
    """A mark closes when no letter or decimal digit follows it. The
    apostrophe in "county's", "we’ll" or 6'7 closes nothing, whereas a mark
    after whitespace may close, and so may one before a footnote mark (’¹)."""

    return index + 1 == len(text) or not _word_char(text[index + 1])


def _next_after(positions: Sequence[int], index: int) -> int | None:
    """The first position strictly after index, or None, with O(log n)
    lookups: the one-pass reading and the main floor find each opener's
    closer here."""

    following = bisect.bisect_right(positions, index)
    return positions[following] if following < len(positions) else None


def _starts_a_quotation(text: str, index: int) -> bool:
    """A mark that can both close and open reads as an opener: after an
    opener prefix and before a letter or a digit; or, after the text's start
    or whitespace, before a quotation mark. So the inner marks in "one "two"
    three", ""one" two" and " ""one" two" open, while the closers in
    "wait—"., "workers'",, "four—"[1], «wait—»", «workers'»" and »a "b—"«
    close (« and “ open quotations but close others too). The second known
    limit follows (tools/README.md): a quotation nested inside another, whose
    opening mark could also close the outer one and which doesn't start with
    a letter or digit ("one "[sic] two" three", „one “[sic] two” three”),
    reads as two quotations."""

    if index + 1 >= len(text) or not _opener_prefix(text, index):
        return False
    after = text[index + 1]
    if _word_char(after):
        return True
    return after in _QUOTATION_MARKS and (index == 0 or text[index - 1].isspace())


def _glued(text: str, index: int) -> bool:
    """The mark directly follows a letter or digit (past any combining marks
    on it)."""

    before = index - 1
    while before >= 0 and index - before <= 4 and unicodedata.category(text[before]).startswith("M"):
        before -= 1
    return before >= 0 and text[before].isalnum()


def _ambiguous_opener(text: str, index: int, *, inside: bool = False) -> bool:
    """Whether a mark that could open a quotation is read as not opening
    one, because it could as well close one. This one predicate is both
    known limits (tools/README.md, Quotation examples), and every reading
    asks it:

    - inside a quotation the mark could close (`inside`), it is ambiguous
      unless it starts a quotation (_starts_a_quotation): a letter or digit
      follows it after an opener prefix, or a quotation mark follows it at
      the start or after whitespace. That is the second limit: such a nested
      quotation that doesn't start with a letter or digit ("one "[sic] two"
      three") reads as two quotations;
    - elsewhere, a single mark or a mark that also closes another pair (”
      » › ″ “ « ‹ 🙶) is ambiguous when it directly follows a letter or digit
      (_glued), and ” » › ″, which close the commonest pairs, also when a
      space or the end follows; unless it starts a quotation. That is the
      first limit: x'one …' and x«one …» aren't counted (main's floor still
      reads a glued “).

    Any other mark ("  „  「 …) only opens, so it is never ambiguous."""

    if _starts_a_quotation(text, index):
        return False
    if inside:
        return True
    mark = text[index]
    if mark not in _ALSO_CLOSES and mark not in _SINGLE_OPENERS:
        return False
    if _glued(text, index):
        return True
    return mark in _CONTEXT_OPENERS and (index + 1 == len(text) or text[index + 1].isspace())


def _opens_delimited(text: str, index: int) -> bool:
    """A delimited opener opens unless it is an ambiguous opener
    (_ambiguous_opener). So the inch mark in 6” and the inner closers in
    „a „b“ c“ and »a »b« c« open nothing, while « oui », :«one» and —«one»
    open."""

    return not _ambiguous_opener(text, index)


def _opens_strict(text: str, index: int) -> bool:
    """The strict reading's opener: a delimiter mark that isn't glued to a
    letter or digit (_glued), so the inch mark in 6" opens nothing while
    " one", :"one" and —"one" open."""

    return index + 1 < len(text) and not _glued(text, index)


def _delimited_close(text: str, index: int, reading: str) -> int:
    """Where the delimited quotation opened at index closes, or the end of the
    text when it doesn't: at its first closing mark (standard); at its first
    closing mark that doesn't start a quotation itself (strict,
    _starts_a_quotation, so a stray ‚ before ’one …’ closes at five’, not at
    the opener); or where the marks inside it, nesting like brackets, close
    it (nested). Each search resumes after the mark it passes, so it is
    linear in the region."""

    if reading == "nested":
        return _nested_close(text, index)
    pattern = _DELIMITER_CLOSE[text[index]]
    found = pattern.search(text, index + 1)
    while reading == "strict" and found and not _ambiguous_opener(text, found.start(), inside=True):
        found = pattern.search(text, found.start() + 1)
    return found.start() if found else len(text)


def _nested_close(text: str, index: int) -> int:
    """The nested reading's close: delimited marks nest like brackets, across
    pairs (“…‘…’…”, „…“…”…“, "…"…"…"). A mark that can close the innermost
    open quotation closes it, unless it can open one and reads as an opener
    (_starts_a_quotation), when it opens a quotation inside; any other opener
    inside opens one too."""

    stack = [text[index]]
    position = index + 1
    while (found := _DELIMITER_MARK.search(text, position)) is not None:
        position = found.start()
        mark = found.group()
        opens = mark in _DELIMITERS and _opens_delimited(text, position)
        if mark in _DELIMITERS[stack[-1]] and (not opens or _ambiguous_opener(text, position, inside=True)):
            stack.pop()
            if not stack:
                return position
        elif opens:
            stack.append(mark)
        position += 1
    return len(text)


def _delimited(text: str, reading: str = "standard") -> tuple[list[tuple[int, str]], list[tuple[int, int]]]:
    """Pass 1: delimited quotations, each closed only by its own closers; an
    unclosed one quotes the rest of the text. Returns (spans, regions).

    Three readings (_delimited_close): standard; strict, for marks that aren't
    quotation marks where they stand (an inch mark, 6"; a low mark used as a
    comma), where a mark opens unless it directly follows a letter or digit
    and closes at the first closing mark that doesn't start a quotation
    itself, so 6" and "one two three four five" quotes five words; and
    nested, for a quotation inside a quotation (_nested_close)."""

    spans: list[tuple[int, str]] = []
    regions: list[tuple[int, int]] = []
    index = 0
    while index < len(text):
        mark = text[index]
        if mark in _DELIMITERS and (
            _opens_delimited(text, index) if reading != "strict" else _opens_strict(text, index)
        ):
            close = _delimited_close(text, index, reading)
            spans.append((index, text[index + 1 : close]))
            regions.append((index, min(close + 1, len(text))))
            index = close + 1
        else:
            index += 1
    return spans, regions


def _outside(text: str, regions: list[tuple[int, int]]) -> Iterator[int]:
    """The positions of a text outside its pass-1 regions, in order."""

    index = 0
    for start, end in regions:
        yield from range(index, start)
        index = end
    yield from range(index, len(text))


def _single_span(text: str, regions: list[tuple[int, int]]) -> tuple[int, int] | None:
    """Pass 2, the conservative reading of single marks outside pass-1
    regions: from the first single mark that may open (_opens_single) to the
    last quotation mark after it that may close (_closes_single), or None
    when there is no such pair. A single mark can't be told from an
    apostrophe ('cause, goin', the workers'), so every word between counts."""

    first = last = None
    for index in _outside(text, regions):
        mark = text[index]
        if first is None:
            if mark in _SINGLE_OPENERS and _opens_single(text, index):
                first = index
        elif mark in _QUOTATION_MARKS and _closes_single(text, index):
            last = index
    return (first, last) if first is not None and last is not None else None


def _whole_text_span(text: str, regions: list[tuple[int, int]]) -> tuple[int, int] | None:
    """The single span over the whole text: from the first single mark that
    may open, anywhere, to the last mark after it that may close, where a
    closer is a single mark anywhere or another quotation mark outside
    `regions` (the standard reading's quotations, so the closer of a double
    quotation after it, as in 'approves it' and "the waiver", ends nothing).
    A stray delimiter can't swallow a single quotation's opener (‚x 'one …')."""

    first = last = None
    region_index = 0
    for index, mark in enumerate(text):
        if mark not in _QUOTATION_MARKS:
            continue
        while region_index < len(regions) and regions[region_index][1] <= index:
            region_index += 1
        inside = region_index < len(regions) and regions[region_index][0] <= index
        if first is None:
            if mark in _SINGLE_OPENERS and _opens_single(text, index):
                first = index
        elif (mark in _SINGLE_MARKS or not inside) and _closes_single(text, index):
            last = index
    return (first, last) if first is not None and last is not None else None


def _span_text(text: str, start: int, close: int, regions: list[tuple[int, int]]) -> str:
    """A single span's text, with each pass-1 region inside it one space."""

    pieces: list[str] = []
    cursor = start + 1
    for region_start, region_end in regions:
        if start < region_start < close:
            pieces.extend((text[cursor:region_start], " "))
            cursor = region_end
    pieces.append(text[cursor:close])
    return "".join(pieces)


def _text_outside(text: str, start: int, end: int, regions: list[tuple[int, int]]) -> str:
    """text[start:end], with each part of a pass-1 region in it one space."""

    pieces: list[str] = []
    cursor = start
    for region_start, region_end in regions:
        if region_end <= cursor or region_start >= end:
            continue
        pieces.extend((text[cursor:max(region_start, cursor)], " "))
        cursor = min(region_end, end)
    pieces.append(text[cursor:end])
    return "".join(pieces)


def _opens_single_main(text: str, index: int) -> bool:
    """main's single opener: after an ASCII prefix, before a letter."""

    return index + 1 < len(text) and text[index + 1].isalpha() and (index == 0 or text[index - 1] in _ASCII_BEFORE_OPENER)


def _one_pass_reading(
    text: str, closers: Sequence[int], opens: Callable[[str, int], bool] | None = None
) -> tuple[int, list[str]]:
    """Delimited and single marks read together in one pass, the way the
    scanner read them before the two-pass scan, with this scan's marks: a
    single span runs to the first closing mark after it (`closers`, every one
    in the text), over any delimited mark in between. `opens` is the single
    opener rule (_opens_single by default). Linear apart from the bisection:
    each delimited search ends where the scan resumes."""

    opens = _opens_single if opens is None else opens

    spans: list[str] = []
    index = 0
    while index < len(text):
        mark = text[index]
        if mark in _DELIMITERS and _opens_delimited(text, index):
            close = _delimited_close(text, index, "standard")
            spans.append(text[index + 1 : close])
            index = close + 1
            continue
        if mark in _SINGLE_OPENERS and opens(text, index):
            close = _next_after(closers, index)
            if close is not None:
                spans.append(text[index + 1 : close])
                index = close + 1
                continue
        index += 1
    return sum(_words(span) for span in spans), spans


def _one_pass_words(text: str, closers: Sequence[int]) -> int:
    return _one_pass_reading(text, closers)[0]


_MAIN_DOUBLES = {'"': '"', "\u201c": "\u201d"}


def _main_reading(text: str) -> tuple[int, list[str]]:
    """The spans and count main's scanner gave, frozen as a floor: straight
    and curly doubles and singles pairing in one pass, a single opening after
    an ASCII prefix and closing at the first ' or ’ after it that follows a
    non-space and precedes no letter or digit, and words counted by
    whitespace. The same spans as main; only its linear search for each
    closer is a bisection over the same closers."""

    closers = [
        index for index, mark in enumerate(text)
        if mark in ("'", "\u2019") and index > 0 and not text[index - 1].isspace()
        and (index + 1 == len(text) or not text[index + 1].isalnum())
    ]
    spans: list[str] = []
    index = 0
    while index < len(text):
        mark = text[index]
        if mark in _MAIN_DOUBLES:
            close = text.find(_MAIN_DOUBLES[mark], index + 1)
            close = len(text) if close == -1 else close
            spans.append(text[index + 1 : close])
            index = close + 1
            continue
        if (
            mark in ("'", "\u2018")
            and index + 1 < len(text)
            and text[index + 1].isalpha()
            and (index == 0 or text[index - 1] in _ASCII_BEFORE_OPENER)
        ):
            close = _next_after(closers, index)
            if close is not None:
                spans.append(text[index + 1 : close])
                index = close + 1
                continue
        index += 1
    return sum(len(span.split()) for span in spans), spans


def _main_words(text: str) -> int:
    return _main_reading(text)[0]


def quoted_spans(text: str) -> list[str]:
    """The quoted spans of a text, as the standard reading finds them.

    Pass 1 consumes delimited quotations over the whole text (_DELIMITERS).
    An unclosed delimiter quotes the rest of the text, failing closed.

    Pass 2 reads single marks outside pass-1 regions as one span, from the
    first mark that may open to the last that may close (_single_span). A
    pass-1 region inside it becomes one space, since pass 1 counted its
    words."""

    spans, regions = _delimited(text)
    single = _single_span(text, regions)
    if single is not None:
        spans.append((single[0], _span_text(text, single[0], single[1], regions)))
    return [span for _, span in sorted(spans)]


def _words(span: str) -> int:
    """The words of a span: its tokens holding a letter or digit, so a stray
    mark is no word (the main floor counts by whitespace, as main did)."""

    return sum(1 for token in span.split() if any(char.isalnum() for char in token))


def _readings(text: str) -> Iterator[tuple[int, list[str]]]:
    """Each reading's count and spans: the three delimited readings, each with
    its single span; the single span over the whole text; the one-pass
    reading, under this scan's single openers and main's; and main's."""

    for reading in _DELIMITED_READINGS:
        located, regions = _delimited(text, reading)
        spans = [span for _, span in located]
        single = _single_span(text, regions)
        if single is not None:
            spans.append(_span_text(text, single[0], single[1], regions))
        yield sum(_words(span) for span in spans), spans
    # The single span over the whole text (_whole_text_span): every standard
    # quotation counted on its own, and the span's own text outside them
    # (each quotation inside it a space). A wider span only adds text at its
    # edge, so widening the openers can't lower this count.
    located, regions = _delimited(text)
    single = _whole_text_span(text, regions)
    if single is not None:
        start, close = single
        spans = [span for _, span in located] + [_text_outside(text, start + 1, close, regions)]
        yield sum(_words(span) for span in spans), spans
    every_closer = [index for index, mark in enumerate(text) if mark in _QUOTATION_MARKS and _closes_single(text, index)]
    # The one-pass reading under main's single openers too: a wider opener can
    # take a closer that would have opened a quotation, so this keeps widening
    # from lowering the count.
    yield _one_pass_reading(text, every_closer)
    yield _one_pass_reading(text, every_closer, _opens_single_main)
    yield _main_reading(text)


def quoted_reading(text: str) -> tuple[int, list[str]]:
    """How many words a text holds inside quotation marks, failing closed,
    and the spans of the reading that counts them.

    Delimited quotations count once, in each of three readings (_delimited).
    Single marks can't be told from apostrophes, so they are read
    conservatively: every word from the first single mark that may open to
    the last quotation mark that may close counts (_single_span), outside
    each reading's delimited quotations and over the whole text
    (_whole_text_span, with the parts of the delimited quotations outside
    it). So a quotation of N words opened and closed by single marks at word
    boundaries always counts at least N: in the whole-text reading the first
    opener is at or before it, and the last closer at or after it. A double
    mark may close a single quotation too (‘…”); that case is counted but not
    part of the guarantee, since the same mark may be closing a quotation
    inside it.

    The count is the largest over the delimited readings of their delimited
    words plus that single span, over the whole-text reading, over a
    one-pass reading (under this scan's single openers and main's), and over
    main's count, so this scan refuses whatever main's did. A description
    that quotes with single marks and also has a later apostrophe at a
    word's end (the workers' case) or a second single quotation is read as
    one quotation from the first mark to the last. tools/README.md says to
    quote with one style, "…" or “…”, nesting with «…» if needed and never in
    the same marks: in plain prose with no single mark that may open, each
    delimited reading counts such a quotation exactly (within the scope the
    README states), and main reads those two pairs exactly too.
    """

    return max(_readings(text), key=lambda reading: reading[0])


def quoted_words(text: str) -> int:
    return quoted_reading(text)[0]


# The interpretation core: compared field by field with a module's
# `module.interpretations` entry, and the only fields a module may carry
# besides `id` and `affects`.
INTERPRETATION_CORE = (
    "question",
    "texts",
    "reading",
    "alternatives",
    "basis",
    "status",
    "ruling",
    "confirmation",
)
MODULE_INTERPRETATION_KEYS = frozenset({"id", *INTERPRETATION_CORE, "affects"})
ENTRY_KEYS = frozenset(
    {
        "id",
        "jurisdiction",
        "program",
        *INTERPRETATION_CORE,
        "pending_texts",
        "outcome",
        "adopted_by",
        "implementations",
        "tests",
        "money_case",
        "years",
        "conflict",
        "resolution",
        "text_kinds",
        "unpublished_sources",
        "proposed",
    }
)
# A pull request URL on github.com: proposed implementations name the PR that
# would add the reading, before it merges.
PR_URL_RE = re.compile(r"https://github\.com/(?P<repo>[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+)/pull/[1-9][0-9]*")
REQUIRED_ENTRY_KEYS = (
    "id",
    "jurisdiction",
    "program",
    "question",
    "texts",
    "reading",
    "alternatives",
    "basis",
    "status",
    "outcome",
)

# Public-repo hygiene: the register is published, so it never carries
# decision-queue ids, session ids, local paths or email addresses.
HYGIENE_PATTERNS = (
    (re.compile(r"\bd[0-9]{3,5}\b"), "a decision-queue id"),
    (re.compile(r"\blocal_[0-9a-f]{8}"), "a session id"),
    (re.compile(r"(?:/Users/|/home/|/private/tmp|(?<![\w.])~/)"), "a local path"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z][\w.-]*"), "an email address"),
)


class RegisterError(ValueError):
    """The register file cannot be read as YAML."""


# ---------------------------------------------------------------------------
# Loading


class _NoAliasLoader(yaml.SafeLoader):
    """The register has no use for anchors or aliases, and an alias can make
    a recursive structure, so loading refuses them."""

    def compose_node(self, parent: Any, index: Any) -> Any:
        if self.check_event(yaml.AliasEvent):
            event = self.peek_event()
            raise yaml.YAMLError(f"anchors and aliases are not allowed (alias *{event.anchor} {event.start_mark})")
        if self.check_event(yaml.ScalarEvent, yaml.SequenceStartEvent, yaml.MappingStartEvent):
            event = self.peek_event()
            if event.anchor is not None:
                raise yaml.YAMLError(f"anchors and aliases are not allowed (anchor &{event.anchor} {event.start_mark})")
        return super().compose_node(parent, index)


def parse_register(text: str, *, label: str) -> Any:
    """A register or household-choices file's text, parsed without anchors
    or aliases. Anything YAML cannot read is a RegisterError, including a
    value it cannot construct (a date such as 2026-02-30, an integer too long
    to convert) and nesting too deep to parse."""

    try:
        return yaml.load(text, Loader=_NoAliasLoader)  # a SafeLoader subclass
    except yaml.YAMLError as exc:
        raise RegisterError(f"{label} is not valid UTF-8 YAML without anchors: {exc}") from exc
    except ValueError as exc:
        raise RegisterError(f"{label} holds a value YAML cannot construct: {exc}") from exc
    except RecursionError:
        raise RegisterError(f"{label} nests too deeply to read") from None


def load_register(path: Path) -> Any:
    if not path.is_file() or path.is_symlink():
        raise RegisterError(f"{path} must be a regular file")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RegisterError(f"{path} cannot be read: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise RegisterError(f"{path} is not valid UTF-8 YAML without anchors: {exc}") from exc
    return parse_register(text, label=str(path))


def _recursive(value: Any) -> bool:
    """Does this parsed value contain itself (a YAML alias cycle)?"""

    stack: list[tuple[Any, frozenset[int]]] = [(value, frozenset())]
    while stack:
        item, path = stack.pop()
        if not isinstance(item, (dict, list)):
            continue
        if id(item) in path:
            return True
        children = item.values() if isinstance(item, dict) else item
        stack.extend((child, path | {id(item)}) for child in children)
    return False


def global_id(entry: Mapping[str, Any]) -> str:
    return f"{entry.get('jurisdiction')}:{entry.get('id')}"


def alternative_ids(alternatives: Any) -> list[str]:
    """The ids of an entry's alternatives, in order (non-strings skipped)."""

    if not isinstance(alternatives, list):
        return []
    return [
        alternative["id"]
        for alternative in alternatives
        if isinstance(alternative, dict) and isinstance(alternative.get("id"), str)
    ]


def document_class(corpus_citation_path: str) -> str:
    """us/statute/42/403/a/5 -> statute."""

    return corpus_citation_path.split("/")[1]


def text_kind(entry: Mapping[str, Any], corpus_citation_path: str) -> str | None:
    """The kind of a corpus text: its `text_kinds` override, else its class's
    default; None for a class without a DOCUMENT_CLASS_KINDS row."""

    overrides = entry.get("text_kinds")
    if isinstance(overrides, dict) and isinstance(overrides.get(corpus_citation_path), str):
        return overrides[corpus_citation_path]
    allowed = DOCUMENT_CLASS_KINDS.get(document_class(corpus_citation_path))
    return allowed[0] if allowed else None


# ---------------------------------------------------------------------------
# Field helpers (the interpretation rules mirror axiom-encode's
# _validate_module_interpretations so an entry that passes here passes there)


def _mapping(value: Any, *, label: str, allowed: Iterable[str], issues: list[str]) -> bool:
    if not isinstance(value, dict):
        issues.append(f"{label} must be a mapping.")
        return False
    allowed_set = set(allowed)
    for key in value:
        if key not in allowed_set:
            issues.append(f"{label} has unknown key `{key}`.")
    return True


def _string(value: Any, *, label: str, issues: list[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{label} must be a non-blank string.")
        return False
    return True


def _nonempty_list(value: Any, *, label: str, issues: list[str]) -> bool:
    if not isinstance(value, list) or not value:
        issues.append(f"{label} must be a non-empty list.")
        return False
    return True


def _https_url(value: Any) -> bool:
    if not isinstance(value, str) or re.search(r"\s", value):
        return False
    try:
        parsed = urllib.parse.urlsplit(value)
        _ = parsed.port
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.hostname)


def _real_date(value: Any) -> bool:
    if type(value) is dt.date:  # an unquoted YAML date
        return True
    if isinstance(value, str) and DATE_RE.fullmatch(value):
        with contextlib.suppress(ValueError):
            dt.date.fromisoformat(value)
            return True
    return False


def _relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in value


def _check_record(record: Any, *, label: str, confirmation: bool, issues: list[str], extra: Iterable[str] = ()) -> None:
    allowed = {"by", "date", "record"} | ({"excerpt"} if confirmation else set()) | set(extra)
    if not _mapping(record, label=label, allowed=allowed, issues=issues):
        return
    _string(record.get("by"), label=f"{label}.by", issues=issues)
    if confirmation:
        _string(record.get("excerpt"), label=f"{label}.excerpt", issues=issues)
    if not _real_date(record.get("date")):
        issues.append(f"{label}.date must be a real YYYY-MM-DD date.")
    if (not confirmation or "record" in record) and not _https_url(record.get("record")):
        issues.append(f"{label}.record must be an https URL.")


# The one way the register writes money: $, digits (commas between groups of
# three allowed), and optionally two-digit cents. A sentence may end after it.
DOLLAR_RE = re.compile(r"\$((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]{2})?)(?![0-9A-Za-z_]|[.,][0-9])")
# Anything else that reads as money is refused, so no figure escapes the
# money-case rule by its spelling: "USD 200", "200 dollars", "$ 200", "$.50",
# "$-200", "$1.5k", "US$200".
MONEY_LIKE_RE = re.compile(
    r"(?i)\bUS\$|\$|\bUSD\b|\b[0-9][0-9,.]*\s*(?:dollars?|cents?|bucks)\b|\bUSD\s*[0-9]"
)


def _dollar_values(text: str) -> set[str]:
    """Dollar amounts in text, normalised: "$4,200.00" and "$4,200" -> "4200"."""

    return {
        format(Decimal(match.group(1).replace(",", "")).normalize(), "f") for match in DOLLAR_RE.finditer(text)
    }


def _unsupported_money(text: str) -> list[str]:
    """Spellings of money other than the one DOLLAR_RE accepts."""

    canonical = {match.start() for match in DOLLAR_RE.finditer(text)}
    found = []
    for match in MONEY_LIKE_RE.finditer(text):
        if match.group(0) == "$" and match.start() in canonical:
            continue
        found.append(text[match.start() : match.start() + 12].split("\n")[0])
    return found


def _prose_fields(entry: Mapping[str, Any], label: str) -> Iterator[tuple[str, str]]:
    """The entry's own prose: question, reading, basis and each alternative's
    reading and effect. Source excerpts, citations and records quote others."""

    for key in ("question", "reading", "basis"):
        if isinstance(entry.get(key), str):
            yield f"{label}.{key}", entry[key]
    alternatives = entry.get("alternatives")
    for index, alternative in enumerate(alternatives if isinstance(alternatives, list) else []):
        if isinstance(alternative, dict):
            for key in ("reading", "effect"):
                if isinstance(alternative.get(key), str):
                    yield f"{label}.alternatives[{index}].{key}", alternative[key]
    # Consumer fields: an implementation's basis, the years' note, an
    # unpublished source's description.
    implementations = entry.get("implementations")
    for index, item in enumerate(implementations if isinstance(implementations, list) else []):
        if isinstance(item, dict) and isinstance(item.get("basis"), str):
            yield f"{label}.implementations[{index}].basis", item["basis"]
    years = entry.get("years")
    if isinstance(years, dict) and isinstance(years.get("note"), str):
        yield f"{label}.years.note", years["note"]
    sources = entry.get("unpublished_sources")
    for index, item in enumerate(sources if isinstance(sources, list) else []):
        if isinstance(item, dict) and isinstance(item.get("description"), str):
            yield f"{label}.unpublished_sources[{index}].description", item["description"]


def check_texts(texts: Any, *, label: str, require: bool, issues: list[str]) -> None:
    """`texts`: corpus citations, each a canonical path and an excerpt."""

    if not isinstance(texts, list) or (require and not texts):
        issues.append(f"{label} must be a non-empty list." if require else f"{label} must be a list.")
        return
    for index, text in enumerate(texts):
        text_label = f"{label}[{index}]"
        if not _mapping(text, label=text_label, allowed={"corpus_citation_path", "excerpt"}, issues=issues):
            continue
        path = text.get("corpus_citation_path")
        if _string(path, label=f"{text_label}.corpus_citation_path", issues=issues):
            if CORPUS_PATH_RE.fullmatch(path) is None:
                issues.append(f"{text_label}.corpus_citation_path is not a canonical corpus citation path.")
        _string(text.get("excerpt"), label=f"{text_label}.excerpt", issues=issues)


def check_pending_texts(pending: Any, *, label: str, issues: list[str]) -> list[Any]:
    """`pending_texts`: provisions not yet in the corpus, each checked against a
    pinned snapshot. Returns the items (empty when the field is malformed)."""

    if not _nonempty_list(pending, label=label, issues=issues):
        return []
    for index, item in enumerate(pending):
        p_label = f"{label}[{index}]"
        if not _mapping(item, label=p_label, allowed={"citation", "kind", "url", "snapshot", "excerpt"}, issues=issues):
            continue
        _string(item.get("citation"), label=f"{p_label}.citation", issues=issues)
        if item.get("kind") not in SOURCE_KINDS:
            issues.append(f"{p_label}.kind must be one of {', '.join(SOURCE_KINDS)}.")
        _string(item.get("excerpt"), label=f"{p_label}.excerpt", issues=issues)
        if not _https_url(item.get("url")):
            issues.append(f"{p_label}.url must be an https URL.")
        _check_snapshot(item.get("snapshot"), label=f"{p_label}.snapshot", issues=issues)
    return pending


def cited_corpus_paths(entry: Mapping[str, Any]) -> list[str]:
    """The entry's well-formed corpus citation paths, in order."""

    texts = entry.get("texts") if isinstance(entry.get("texts"), list) else []
    return [
        text["corpus_citation_path"]
        for text in texts
        if isinstance(text, dict)
        and isinstance(text.get("corpus_citation_path"), str)
        and CORPUS_PATH_RE.fullmatch(text["corpus_citation_path"])
    ]


def check_text_kinds(entry: Mapping[str, Any], *, label: str, issues: list[str]) -> None:
    """Every cited document class has a DOCUMENT_CLASS_KINDS row, and each
    `text_kinds` override names a cited path and a kind its class allows."""

    cited_paths = cited_corpus_paths(entry)
    for path in dict.fromkeys(cited_paths):
        if document_class(path) not in DOCUMENT_CLASS_KINDS:
            issues.append(
                f"{label}.texts cites {path}, whose document class `{document_class(path)}` has no "
                "DOCUMENT_CLASS_KINDS row; add one rather than leave its kind open."
            )
    if "text_kinds" not in entry:
        return
    overrides = entry["text_kinds"]
    if not isinstance(overrides, dict) or not overrides:
        issues.append(f"{label}.text_kinds must be a non-empty mapping of corpus citation path to kind.")
        return
    for path, kind in overrides.items():
        k_label = f"{label}.text_kinds[{path}]"
        if path not in cited_paths:
            issues.append(f"{k_label} names a path that is not one of this entry's texts.")
            continue
        allowed = DOCUMENT_CLASS_KINDS.get(document_class(path))
        if kind not in SOURCE_KINDS:
            issues.append(f"{k_label} must be one of {', '.join(SOURCE_KINDS)}.")
        elif allowed is not None and kind not in allowed:
            issues.append(
                f"{k_label} is `{kind}`, but a `{document_class(path)}` path can only be "
                f"{', '.join(allowed)}."
            )


def check_interpretation_core(entry: Mapping[str, Any], *, label: str, require_texts: bool) -> list[str]:
    """The module.interpretations v1 rules, minus `id` and `affects`."""

    issues: list[str] = []
    for name in ("question", "reading", "basis"):
        _string(entry.get(name), label=f"{label}.{name}", issues=issues)
    check_texts(entry.get("texts"), label=f"{label}.texts", require=require_texts, issues=issues)
    alternatives = entry.get("alternatives")
    if _nonempty_list(alternatives, label=f"{label}.alternatives", issues=issues):
        seen_ids: set[str] = set()
        for index, alternative in enumerate(alternatives):
            alt_label = f"{label}.alternatives[{index}]"
            if not _mapping(alternative, label=alt_label, allowed={"id", "reading", "effect"}, issues=issues):
                continue
            alternative_id = alternative.get("id")
            if "id" not in alternative:
                issues.append(f"{alt_label}.id is required; references name an alternative by id, never by position.")
            elif not (isinstance(alternative_id, str) and KEBAB_RE.fullmatch(alternative_id)):
                issues.append(f"{alt_label}.id must match [a-z0-9]+(-[a-z0-9]+)*.")
            elif alternative_id == ADOPTED_READING:
                issues.append(f"{alt_label}.id must not be `{ADOPTED_READING}`, which names the adopted reading.")
            elif alternative_id in seen_ids:
                issues.append(f"{alt_label}.id `{alternative_id}` repeats an earlier alternative's id.")
            else:
                seen_ids.add(alternative_id)
            _string(alternative.get("reading"), label=f"{alt_label}.reading", issues=issues)
            if "effect" in alternative:
                _string(alternative.get("effect"), label=f"{alt_label}.effect", issues=issues)
    status = entry.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        issues.append(f"{label}.status must be open, ruled, confirmed or contradicted.")
    else:
        for field, required in (
            ("ruling", status != "open"),
            ("confirmation", status in {"confirmed", "contradicted"}),
        ):
            if not required:
                if field in entry:
                    issues.append(f"{label}.{field} must be absent when status is `{status}`.")
            elif field not in entry:
                issues.append(f"{label}.{field} must be a mapping when status is `{status}`.")
            else:
                _check_record(entry[field], label=f"{label}.{field}", confirmation=field == "confirmation", issues=issues)
        if status == "contradicted":
            issues.append(
                f"{label}: the publisher contradicted this reading; repair the encoding, move the "
                "old reading into alternatives, and set the new status."
            )
    return issues


# ---------------------------------------------------------------------------
# Repository context


@dataclass(frozen=True)
class RepoContext:
    root: Path
    repo: str  # owner/name of this checkout, e.g. TheAxiomFoundation/rulespec-us

    def jurisdictions(self) -> frozenset[str]:
        return frozenset(
            child.name
            for child in self.root.iterdir()
            if child.is_dir()
            and JURISDICTION_RE.fullmatch(child.name)
            and any((child / marker).is_dir() for marker in CONTENT_DIRS)
        )

    def module_path_ok(self, value: str) -> bool:
        parts = PurePosixPath(value).parts
        return (
            len(parts) >= 3
            and parts[0] in self.jurisdictions()
            and parts[1] in CONTENT_DIRS
            and value.endswith(".yaml")
            and not value.endswith(".test.yaml")
        )


def iter_module_files(root: Path) -> Iterator[Path]:
    for jurisdiction in sorted(root.iterdir()):
        if not (jurisdiction.is_dir() and JURISDICTION_RE.fullmatch(jurisdiction.name)):
            continue
        for marker in CONTENT_DIRS:
            base = jurisdiction / marker
            if base.is_dir():
                yield from sorted(
                    path for path in base.rglob("*.yaml") if not path.name.endswith(".test.yaml")
                )


def module_interpretations(path: Path) -> tuple[list[dict[str, Any]], set[str]] | None:
    """(interpretations, rule names) of one module, or None when it has none."""

    text = path.read_text(encoding="utf-8")
    if "interpretations" not in text:
        return None
    try:
        payload = yaml.safe_load(text)
    except yaml.YAMLError:
        return None
    module = payload.get("module") if isinstance(payload, dict) else None
    entries = module.get("interpretations") if isinstance(module, dict) else None
    if not isinstance(entries, list):
        return None
    rules = payload.get("rules")
    names = (
        {rule["name"] for rule in rules if isinstance(rule, dict) and isinstance(rule.get("name"), str)}
        if isinstance(rules, list)
        else set()
    )
    return [entry for entry in entries if isinstance(entry, dict)], names


def to_module_interpretation(entry: Mapping[str, Any], *, interpretation_id: str, affects: list[str]) -> dict[str, Any]:
    """The module.interpretations entry a register entry becomes when encoded."""

    result: dict[str, Any] = {"id": interpretation_id}
    for name in INTERPRETATION_CORE:
        if name in entry:
            result[name] = entry[name]
    result["affects"] = list(affects)
    return result


def interpretation_core(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {name: entry[name] for name in INTERPRETATION_CORE if name in entry}


def yaml_test_case_names(text: str) -> set[str]:
    """The case names of a YAML test file; none when YAML cannot read it
    (including a value it cannot construct, or nesting too deep)."""

    try:
        payload = yaml.safe_load(text)
    except (yaml.YAMLError, ValueError, RecursionError):
        return set()
    cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(cases, list):
        return set()
    return {case["name"] for case in cases if isinstance(case, dict) and isinstance(case.get("name"), str)}


# A Python test reference is screened by syntax alone, and the screen is not
# evidence that the test runs. It needs a test file (test_*.py) that parses and
# defines the named function: a def at module level, or a def in a body of a
# module-level class for Class::function. Defs under `if`, `try`, `with`, loops
# and `match` count as module level. What pytest actually collects depends on
# import-time code, conftest files, plugins and ini settings, which no screen
# can decide. tools/pin_runner.py asks pytest instead: it runs each pinned test
# at its pinned commit, and only `passed` establishes a pin (see tools/README.md,
# Test references). A parametrized case id ([...]) is refused, because pytest
# builds case ids from more than the file shows.
PYTHON_TEST_FILE_RE = re.compile(r"test_[^/]*\.py")
_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)
_BLOCKS = (ast.If, ast.Try, ast.TryStar, ast.With, ast.AsyncWith, ast.For, ast.AsyncFor, ast.While, ast.Match)


def python_test_file(path: str) -> bool:
    return PYTHON_TEST_FILE_RE.fullmatch(PurePosixPath(path).name) is not None


def _scope_statements(body: list[ast.stmt]) -> Iterator[ast.stmt]:
    """Statements in this scope, including those inside compound statements
    such as if, try, with, loops and match, but not inside defs or classes."""

    stack = list(reversed(body))
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, _BLOCKS):
            nested = [
                *(statement for field in ("body", "orelse", "finalbody") for statement in getattr(node, field, None) or []),
                *(statement for handler in getattr(node, "handlers", None) or [] for statement in handler.body),
                *(statement for case in getattr(node, "cases", None) or [] for statement in case.body),
            ]
            stack.extend(reversed(nested))


def python_test_exists(source: str | bytes, name: str) -> bool:
    """The syntactic screen: does this file define `name` (function, or
    Class::function)? This decides nothing about collection or running."""

    match = TEST_NAME_RE.fullmatch(name)
    if match is None:
        return False
    try:
        tree = ast.parse(source)  # bytes honour a PEP 263 coding cookie
    except (SyntaxError, ValueError, UnicodeDecodeError, MemoryError, RecursionError):
        # CPython's parser raises MemoryError ("source too complex") and
        # RecursionError on deep input; either way the screen fails.
        return False
    body = tree.body
    scope = match.group("scope")
    if scope:
        classes = [node for node in _scope_statements(body) if isinstance(node, ast.ClassDef) and node.name == scope[:-2]]
        if not classes:
            return False
        body = [statement for cls in classes for statement in cls.body]
    return any(isinstance(node, _DEFS) and node.name == match.group("name") for node in _scope_statements(body))


def missing_test(name: str, where: str) -> str:
    """Why a test reference does not resolve, worded for its kind of file."""

    if where.endswith(".py"):
        return (
            f"{name} is not a test function defined in {where}, or the file does not parse "
            "(see tools/README.md, Test references)."
        )
    return f"{name} is not a test case in {where}."


def test_exists(path: str, name: str, data: bytes) -> bool:
    if path.endswith(".py"):
        return python_test_file(path) and python_test_exists(data, name)
    if path.endswith(".yaml"):  # a companion .test.yaml, or another repository's YAML tests
        try:
            return name in yaml_test_case_names(data.decode("utf-8"))
        except UnicodeDecodeError:
            return False
    return False


# ---------------------------------------------------------------------------
# check (offline)


def _walk_strings(value: Any, label: str) -> Iterator[tuple[str, str]]:
    """Every string in a parsed value, in document order, with its label.
    Iterative, so nesting depth is bounded by memory, not the call stack."""

    stack: list[tuple[Any, str]] = [(value, label)]
    while stack:
        item, where = stack.pop()
        if isinstance(item, str):
            yield where, item
        elif isinstance(item, dict):
            stack.extend((child, f"{where}.{key}") for key, child in reversed(list(item.items())))
        elif isinstance(item, list):
            stack.extend((child, f"{where}[{index}]") for index, child in reversed(list(enumerate(item))))


def hygiene_issues(payload: Any, *, root: str = "register", public: str = "the register") -> list[str]:
    issues: list[str] = []
    for label, text in _walk_strings(payload, root):
        # Commit and sha256 fields are hex; skip them so a hash never reads
        # as a decision id.
        if label.endswith((".commit", ".sha256")):
            continue
        for pattern, what in HYGIENE_PATTERNS:
            if pattern.search(text):
                issues.append(f"{label} contains {what}; {public} is public.")
    return issues


def _global_ids(payload: Any) -> dict[str, int]:
    """Global id -> index of its first entry, for entries that have one."""

    ids: dict[str, int] = {}
    entries = payload.get("entries") if isinstance(payload, dict) else None
    for index, entry in enumerate(entries if isinstance(entries, list) else []):
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and isinstance(entry.get("jurisdiction"), str):
            ids.setdefault(global_id(entry), index)
    return ids


def id_collision_issues(root: Path, *, conflicts: Any = None, choices: Any = None) -> list[str]:
    """A global id names one thing: an entry of the register or a household
    choice, never both. Both files' `check` call this, each passing its own
    parsed payload; the other file is read from `root` (an absent file has no
    ids). Then a register entry added later can't take a choice's id, or the
    reverse, without failing the check of the file that changed."""

    issues: list[str] = []
    loaded = {"conflicts": conflicts, "choices": choices}
    for key, filename in (("conflicts", REGISTER_FILENAME), ("choices", CHOICES_FILENAME)):
        if loaded[key] is not None:
            continue
        path = root / filename
        if not (path.exists() or path.is_symlink()):
            loaded[key] = {}
            continue
        try:
            loaded[key] = load_register(path)
        except RegisterError as exc:
            return [f"cannot read {filename} to check that no global id is in both files: {exc}"]
    choice_ids = _global_ids(loaded["choices"])
    for gid, index in _global_ids(loaded["conflicts"]).items():
        if gid in choice_ids:
            issues.append(
                f"`{gid}` is both {REGISTER_FILENAME} entries[{index}] and {CHOICES_FILENAME} "
                f"entries[{choice_ids[gid]}]; a global id names one entry in the two files."
            )
    return issues


def _check_reading_ref(value: Any, *, label: str, alternatives: Any, issues: list[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{label} must be `{ADOPTED_READING}` or the id of one of this entry's alternatives.")
        return False
    if value != ADOPTED_READING and value not in alternative_ids(alternatives):
        issues.append(
            f"{label} names `{value}`, which is neither `{ADOPTED_READING}` nor the id of one of this "
            "entry's alternatives."
        )
        return False
    return True


def _check_years(years: Any, *, label: str, issues: list[str]) -> None:
    if not _mapping(years, label=label, allowed={"from", "to", "type", "note"}, issues=issues):
        return
    start, end = years.get("from"), years.get("to")
    for key, value, required in (("from", start, True), ("to", end, False)):
        if value is None and not required and key not in years:
            continue
        if type(value) is not int or not MIN_YEAR <= value <= MAX_YEAR:
            issues.append(f"{label}.{key} must be a whole year from {MIN_YEAR} to {MAX_YEAR}.")
    if type(start) is int and type(end) is int and end < start:
        issues.append(f"{label}.to ({end}) is before {label}.from ({start}); both bounds are inclusive.")
    year_type = years.get("type")
    if year_type not in YEAR_TYPES:
        issues.append(f"{label}.type must be one of {', '.join(YEAR_TYPES)}.")
    if "note" in years:
        _string(years.get("note"), label=f"{label}.note", issues=issues)
    elif year_type == "program":
        issues.append(f"{label}.note is required when type is `program`: say what the program year is.")


def _check_unpublished_source(item: Any, *, label: str, issues: list[str]) -> None:
    if not _mapping(item, label=label, allowed={"kind", "description", "date"}, issues=issues):
        return
    for key in ("kind", "description", "date"):
        if key not in item:
            issues.append(f"{label}.{key} is required.")
    if "kind" in item and item["kind"] not in SOURCE_KINDS:
        issues.append(f"{label}.kind must be one of {', '.join(SOURCE_KINDS)}.")
    if "date" in item and not _real_date(item["date"]):
        issues.append(f"{label}.date must be a real YYYY-MM-DD date.")
    description = item.get("description")
    if "description" in item and _string(description, label=f"{label}.description", issues=issues):
        if "@" in description:
            issues.append(f"{label}.description contains `@`; describe the source, never give an address.")
        count, spans = quoted_reading(description)
        if count > MAX_QUOTED_WORDS:
            shown = ", ".join(json.dumps(span if len(span) <= 80 else span[:80] + "\u2026", ensure_ascii=False) for span in spans)
            issues.append(
                f"{label}.description quotes more than {MAX_QUOTED_WORDS} words in all ({count}, counted in "
                f"{shown}); an unpublished source is described, never quoted. Describe it instead, or put a "
                f"quotation of at most {MAX_QUOTED_WORDS} words in one style of double quotation marks (\"\u2026\" or "
                "\u201c\u2026\u201d), nesting with \u00ab\u2026\u00bb if needed and never in the same marks; those are counted "
                "exactly in plain prose. Single marks (\u2018\u2026\u2019 too) can't be told from apostrophes, so every word "
                "from the first single mark to the last quotation mark counts."
            )


def _check_snapshot(snapshot: Any, *, label: str, issues: list[str]) -> None:
    if not _mapping(snapshot, label=label, allowed={"repo", "commit", "path", "sha256"}, issues=issues):
        return
    for key in ("repo", "commit", "path", "sha256"):
        if key not in snapshot:
            issues.append(f"{label}.{key} is required.")
    if "repo" in snapshot and not (isinstance(snapshot["repo"], str) and REPO_RE.fullmatch(snapshot["repo"])):
        issues.append(f"{label}.repo must be owner/name.")
    if "commit" in snapshot and not (isinstance(snapshot["commit"], str) and COMMIT_RE.fullmatch(snapshot["commit"])):
        issues.append(f"{label}.commit must be a full lowercase commit SHA.")
    if "path" in snapshot and not _relative_path(snapshot["path"]):
        issues.append(f"{label}.path must be a relative path inside the repository.")
    if "sha256" in snapshot and not (isinstance(snapshot["sha256"], str) and SHA256_RE.fullmatch(snapshot["sha256"])):
        issues.append(f"{label}.sha256 must be a lowercase sha256 digest.")


def _check_external_ref(item: Mapping[str, Any], *, label: str, ctx: RepoContext, issues: list[str]) -> bool:
    """repo/commit/path of a reference; returns True when it points outside."""

    repo = item.get("repo")
    if repo is None:
        if "commit" in item:
            issues.append(f"{label}.commit is only for a file in another repository.")
        return False
    if not (isinstance(repo, str) and REPO_RE.fullmatch(repo)):
        issues.append(f"{label}.repo must be owner/name.")
        return True
    if repo == ctx.repo:
        issues.append(f"{label}.repo names this repository; omit repo and commit for a file here.")
        return False
    if not (isinstance(item.get("commit"), str) and COMMIT_RE.fullmatch(item["commit"])):
        issues.append(f"{label}.commit must be a full lowercase commit SHA.")
    return True


def check_test_location(
    item: Any, *, label: str, ctx: RepoContext, allowed: Iterable[str], issues: list[str]
) -> tuple[bool, str | None, str | None] | None:
    """Where a test reference points: (external, path, name), with path or
    name None when malformed; None when the item is not a mapping. The pins
    are the caller's: the register pins readings, the household-choices file
    pins a default or an optimum."""

    if not _mapping(item, label=label, allowed=allowed, issues=issues):
        return None
    external = _check_external_ref(item, label=label, ctx=ctx, issues=issues)
    path = item.get("path")
    name = item.get("name")
    # Another repository's YAML test cases (PolicyEngine-US's policy tests)
    # count, pinned like any external test; here, a companion test is always
    # .test.yaml.
    suffixes = (".py", ".yaml") if external else (".py", ".test.yaml")
    if isinstance(path, str) and "::" in path:
        issues.append(f"{label}.path {path} contains `::`, which separates a test file from its test name.")
        path = None
    elif not _relative_path(path) or not str(path).endswith(suffixes):
        issues.append(
            f"{label}.path must be a relative "
            + (".py or .yaml path." if external else ".py or .test.yaml path.")
        )
        path = None
    elif str(path).endswith(".py") and not python_test_file(path):
        issues.append(f"{label}.path {path} is not a test file (test_*.py); only a test can pin a reading.")
        path = None
    elif external and str(path).endswith(".yaml") and "tests" not in PurePosixPath(path).parts[:-1]:
        issues.append(
            f"{label}.path {path} is not under a tests directory; another repository's YAML test "
            "file must be one of its tests."
        )
        path = None
    if isinstance(path, str) and path.endswith(".yaml"):
        if not (isinstance(name, str) and name.strip() and "\n" not in name and name == name.strip()):
            issues.append(f"{label}.name must be a YAML test case's name, on one line.")
            name = None
    elif isinstance(name, str) and "[" in name:
        issues.append(
            f"{label}.name {name} names a parametrized case; pin the whole test function "
            "(pytest builds case ids from more than the file shows)."
        )
        name = None
    elif not (isinstance(name, str) and TEST_NAME_RE.fullmatch(name)):
        issues.append(f"{label}.name must be a test function, optionally Class::function.")
        name = None
    return external, path, name


def check_repeated_test(
    item: Mapping[str, Any], path: str | None, name: str | None, *, label: str, seen: set[tuple[Any, Any, Any]], issues: list[str]
) -> None:
    repo_key = item.get("repo") if isinstance(item.get("repo"), str) else repr(item.get("repo"))
    key = (repo_key, path, name)
    if key in seen and None not in key[1:]:
        issues.append(f"{label} repeats {path}::{name}.")
    seen.add(key)


def check_local_test(path: str | None, name: str | None, *, label: str, ctx: RepoContext, issues: list[str]) -> None:
    """A test in this repository exists and defines the named test (a screen)."""

    if not (path and name):
        return
    local = ctx.root / path
    if not local.is_file():
        issues.append(f"{label}.path {path} does not exist in this repository.")
        return
    try:
        data = local.read_bytes()
    except OSError as exc:
        issues.append(f"{label}.path {path} cannot be read: {exc.strerror or exc}.")
        return
    if not test_exists(path, name, data):
        issues.append(f"{label}.name {missing_test(name, path)}")


def check_entry(entry: Any, *, index: int, ctx: RepoContext, jurisdictions: frozenset[str]) -> list[str]:
    location = f"entries[{index}]"
    entry_id = entry.get("id") if isinstance(entry, dict) else None
    label = f"Entry `{entry_id}` ({location})" if isinstance(entry_id, str) and entry_id.strip() else location
    issues: list[str] = []
    if not _mapping(entry, label=label, allowed=ENTRY_KEYS, issues=issues):
        return issues
    for key in REQUIRED_ENTRY_KEYS:
        if key not in entry:
            issues.append(f"{label}.{key} is required.")
    if isinstance(entry_id, str) and KEBAB_RE.fullmatch(entry_id) is None:
        issues.append(f"{label}.id must match [a-z0-9]+(-[a-z0-9]+)*.")
    elif "id" in entry and not isinstance(entry_id, str):
        issues.append(f"{label}.id must be a string.")
    jurisdiction = entry.get("jurisdiction")
    if "jurisdiction" in entry and not (isinstance(jurisdiction, str) and jurisdiction in jurisdictions):
        issues.append(f"{label}.jurisdiction must be a jurisdiction directory of this repository ({', '.join(sorted(jurisdictions))}).")
    program = entry.get("program")
    if "program" in entry and not (isinstance(program, str) and KEBAB_RE.fullmatch(program)):
        issues.append(f"{label}.program must be kebab-case.")

    pending = entry.get("pending_texts", [])
    has_texts = isinstance(entry.get("texts"), list) and bool(entry.get("texts"))
    has_pending = isinstance(pending, list) and bool(pending)
    issues.extend(check_interpretation_core(entry, label=label, require_texts=False))
    if not has_texts and not has_pending:
        issues.append(f"{label} must cite at least one provision in texts or pending_texts.")

    if "pending_texts" in entry:
        pending = check_pending_texts(pending, label=f"{label}.pending_texts", issues=issues)
    check_text_kinds(entry, label=label, issues=issues)

    years = entry.get("years")
    if "years" in entry:
        _check_years(years, label=f"{label}.years", issues=issues)
    conflict = entry.get("conflict", "live")
    if conflict not in CONFLICT_STATES:
        issues.append(f"{label}.conflict must be live or resolved.")
    elif conflict == "resolved":
        if "resolution" not in entry:
            issues.append(f"{label}.resolution is required when conflict is `resolved`.")
        if not (isinstance(years, dict) and "to" in years):
            issues.append(f"{label}.years.to is required when conflict is `resolved`: the last year the sources disagree.")
    elif "resolution" in entry:
        issues.append(f"{label}.resolution must be absent while conflict is `live`; set conflict: resolved.")
    if "resolution" in entry:
        resolution = entry["resolution"]
        r_label = f"{label}.resolution"
        if _mapping(resolution, label=r_label, allowed={"by", "effective", "record"}, issues=issues):
            if resolution.get("by") not in RESOLVERS:
                issues.append(f"{r_label}.by must be legislation or agency.")
            if not _real_date(resolution.get("effective")):
                issues.append(f"{r_label}.effective must be a real YYYY-MM-DD date.")
            if not _https_url(resolution.get("record")):
                issues.append(f"{r_label}.record must be an https URL to a public record.")
    if "unpublished_sources" in entry:
        unpublished = entry["unpublished_sources"]
        if _nonempty_list(unpublished, label=f"{label}.unpublished_sources", issues=issues):
            for u_index, item in enumerate(unpublished):
                _check_unpublished_source(item, label=f"{label}.unpublished_sources[{u_index}]", issues=issues)

    if "proposed" in entry:
        proposed = entry["proposed"]
        if _nonempty_list(proposed, label=f"{label}.proposed", issues=issues):
            for p_index, item in enumerate(proposed):
                p_label = f"{label}.proposed[{p_index}]"
                if not _mapping(item, label=p_label, allowed={"repo", "pr", "path", "follows"}, issues=issues):
                    continue
                repo = item.get("repo")
                if not (isinstance(repo, str) and REPO_RE.fullmatch(repo)):
                    issues.append(f"{p_label}.repo must be owner/name.")
                pr = item.get("pr")
                match = PR_URL_RE.fullmatch(pr) if isinstance(pr, str) else None
                if match is None:
                    issues.append(f"{p_label}.pr must be a github.com pull request URL.")
                elif isinstance(repo, str) and match.group("repo") != repo:
                    issues.append(f"{p_label}.pr is a pull request in {match.group('repo')}, not {repo}.")
                if not _relative_path(item.get("path")):
                    issues.append(f"{p_label}.path must be a relative path inside the repository.")
                _check_reading_ref(item.get("follows"), label=f"{p_label}.follows", alternatives=entry.get("alternatives"), issues=issues)

    outcome = entry.get("outcome")
    if "outcome" in entry and outcome not in OUTCOMES:
        issues.append(f"{label}.outcome must be computed or refused.")

    alternatives = entry.get("alternatives")
    adopted = entry.get("adopted_by", [])
    implementations = entry.get("implementations", [])
    tests = entry.get("tests", [])

    if "adopted_by" in entry:
        if not _nonempty_list(adopted, label=f"{label}.adopted_by", issues=issues):
            adopted = []
        elif has_pending:
            issues.append(
                f"{label} is adopted by a module but still has pending_texts; a module's "
                "interpretation texts must verify against the corpus, so ingest them first."
            )
        seen_pairs: set[tuple[str, str]] = set()
        for a_index, item in enumerate(adopted):
            a_label = f"{label}.adopted_by[{a_index}]"
            if not _mapping(item, label=a_label, allowed={"module", "interpretation"}, issues=issues):
                continue
            module = item.get("module")
            interp = item.get("interpretation")
            if not (isinstance(module, str) and _relative_path(module) and ctx.module_path_ok(module)):
                issues.append(f"{a_label}.module must be a RuleSpec module path in this repository.")
                continue
            if not (isinstance(interp, str) and KEBAB_RE.fullmatch(interp)):
                issues.append(f"{a_label}.interpretation must be a kebab-case interpretation id.")
                continue
            if (module, interp) in seen_pairs:
                issues.append(f"{a_label} repeats ({module}, {interp}).")
            seen_pairs.add((module, interp))
            issues.extend(_check_adopting_module(entry, module=module, interpretation=interp, label=a_label, ctx=ctx))

    if "implementations" in entry:
        if not _nonempty_list(implementations, label=f"{label}.implementations", issues=issues):
            implementations = []
        for i_index, item in enumerate(implementations):
            i_label = f"{label}.implementations[{i_index}]"
            if not _mapping(
                item,
                label=i_label,
                allowed={"repo", "commit", "path", "follows", "adopts", "basis", "ruling", "cites_entry"},
                issues=issues,
            ):
                continue
            if "repo" not in item:
                issues.append(f"{i_label}.repo is required; a RuleSpec module in this repository goes in adopted_by.")
            else:
                _check_external_ref(item, label=i_label, ctx=ctx, issues=issues)
            if not _relative_path(item.get("path")):
                issues.append(f"{i_label}.path must be a relative path inside the repository.")
            _check_reading_ref(item.get("follows"), label=f"{i_label}.follows", alternatives=alternatives, issues=issues)
            # A consumer may adopt a different reading from the entry's own
            # (PolicyEngine-US follows the statute where the entry adopts an
            # agency's practice); it says why, and may cite its own ruling.
            if "adopts" in item:
                _check_reading_ref(item.get("adopts"), label=f"{i_label}.adopts", alternatives=alternatives, issues=issues)
            if "basis" in item:
                _string(item.get("basis"), label=f"{i_label}.basis", issues=issues)
            elif "adopts" in item or "ruling" in item:
                issues.append(f"{i_label}.basis is required with adopts or ruling: say why this consumer adopts that reading.")
            if "ruling" in item:
                _check_record(item["ruling"], label=f"{i_label}.ruling", confirmation=False, issues=issues, extra=("principle",))
                ruling = item["ruling"]
                if isinstance(ruling, dict) and "principle" in ruling and ruling["principle"] not in PRINCIPLES:
                    issues.append(f"{i_label}.ruling.principle must be one of {', '.join(PRINCIPLES)}.")
            if not isinstance(item.get("cites_entry"), bool):
                issues.append(f"{i_label}.cites_entry must be true or false.")

    if "tests" in entry:
        if not _nonempty_list(tests, label=f"{label}.tests", issues=issues):
            tests = []
        seen_tests: set[tuple[Any, Any, Any]] = set()
        for t_index, item in enumerate(tests):
            t_label = f"{label}.tests[{t_index}]"
            located = check_test_location(
                item, label=t_label, ctx=ctx, allowed={"repo", "commit", "path", "name", "pins"}, issues=issues
            )
            if located is None:
                continue
            external, path, name = located
            pins = item.get("pins")
            if not (isinstance(pins, list) and pins):
                issues.append(f"{t_label}.pins must be a non-empty list of `reading` or alternative ids.")
            else:
                for p_index, ref in enumerate(pins):
                    _check_reading_ref(ref, label=f"{t_label}.pins[{p_index}]", alternatives=alternatives, issues=issues)
                if len(set(map(str, pins))) != len(pins):
                    issues.append(f"{t_label}.pins repeats a reading.")
            check_repeated_test(item, path, name, label=t_label, seen=seen_tests, issues=issues)
            if not external:
                check_local_test(path, name, label=t_label, ctx=ctx, issues=issues)

    pinned = {
        ref
        for item in tests or []
        if isinstance(item, dict) and isinstance(item.get("pins"), list)
        for ref in item["pins"]
        if isinstance(ref, str)
    }
    if adopted and "reading" not in pinned:
        issues.append(f"{label} is adopted by a module, so at least one test must pin `reading`.")
    for i_index, item in enumerate(implementations or []):
        follows = item.get("follows") if isinstance(item, dict) else None
        if isinstance(follows, str) and (follows == ADOPTED_READING or follows in alternative_ids(alternatives)) and follows not in pinned:
            issues.append(f"{label}.implementations[{i_index}] follows {follows}, which no test pins.")

    # A public dollar figure needs a pinned test: every $ amount in the entry's
    # own prose must be one its money case (computed by a named test) states.
    money = entry.get("money_case") if isinstance(entry.get("money_case"), dict) else {}
    # Excerpts are the sources' own words and may state any figure; the entry's
    # prose names a threshold without restating it ("above the section 1341
    # threshold"). No lexical test can tell a quoted threshold from a computed
    # amount, so prose amounts are never backed by an excerpt.
    covered = _dollar_values(str(money.get("description", ""))) | _dollar_values(f"${money.get('amount', '')}")
    spelled = list(_prose_fields(entry, label))
    if isinstance(money.get("description"), str):
        spelled.append((f"{label}.money_case.description", money["description"]))
    for field_label, text in spelled:
        for odd in _unsupported_money(text):
            issues.append(
                f"{field_label} writes money as `{odd}`; write it as $ and digits, with commas and cents "
                "where needed (such as $1,234.56), so the money-case rule can see it."
            )
    for field_label, text in _prose_fields(entry, label):
        for amount in sorted(_dollar_values(text) - covered):
            issues.append(
                f"{field_label} states ${amount}, which no money case backs: name it in the money case "
                "(whose computed_by test computes it) or describe the effect without the amount; name a "
                "source's threshold without restating it."
            )

    if "money_case" in entry:
        money = entry["money_case"]
        m_label = f"{label}.money_case"
        if _mapping(money, label=m_label, allowed={"description", "amount", "currency", "period", "computed_by"}, issues=issues):
            _string(money.get("description"), label=f"{m_label}.description", issues=issues)
            # A public amount needs a pinned test that computes it.
            names = [item.get("name") for item in tests or [] if isinstance(item, dict)]
            if money.get("computed_by") not in names or names.count(money.get("computed_by")) != 1:
                issues.append(
                    f"{m_label}.computed_by must name the one test in this entry's `tests` that computes the "
                    "amount; record no amount that no pinned test computes."
                )
            amount = money.get("amount")
            if not (isinstance(amount, str) and DECIMAL_RE.fullmatch(amount)):
                issues.append(f"{m_label}.amount must be a non-negative decimal string such as \"21.00\".")
            if not (isinstance(money.get("currency"), str) and CURRENCY_RE.fullmatch(money["currency"])):
                issues.append(f"{m_label}.currency must be an ISO 4217 code such as USD.")
            if money.get("period") not in PERIODS:
                issues.append(f"{m_label}.period must be one of {', '.join(PERIODS)}.")
    return issues


def _check_adopting_module(entry: Mapping[str, Any], *, module: str, interpretation: str, label: str, ctx: RepoContext) -> list[str]:
    path = ctx.root / module
    if not path.is_file():
        return [f"{label}.module {module} does not exist."]
    found = module_interpretations(path)
    if found is None:
        return [f"{label}: {module} has no module.interpretations entry `{interpretation}`."]
    entries, rule_names = found
    matches = [item for item in entries if item.get("id") == interpretation]
    if not matches:
        return [f"{label}: {module} has no module.interpretations entry `{interpretation}`."]
    carried = matches[0]
    issues = check_module_interpretation(carried, rule_names=rule_names, label=f"{label}: {module}#{interpretation}")
    for name in INTERPRETATION_CORE:
        if carried.get(name) != entry.get(name):
            issues.append(
                f"{label}: {module}#{interpretation} `{name}` differs from the register entry; "
                "the module must carry the entry unchanged."
            )
    return issues


def check_module_interpretation(item: Any, *, rule_names: set[str], label: str) -> list[str]:
    """One module.interpretations v1 entry, by the rules axiom-encode applies
    (tests/test_source_conflicts_properties.py checks the two agree)."""

    issues: list[str] = []
    if not _mapping(item, label=label, allowed=MODULE_INTERPRETATION_KEYS, issues=issues):
        return issues
    interpretation_id = item.get("id")
    if _string(interpretation_id, label=f"{label}.id", issues=issues) and KEBAB_RE.fullmatch(interpretation_id) is None:
        issues.append(f"{label}.id must match [a-z0-9]+(-[a-z0-9]+)*.")
    issues.extend(check_interpretation_core(item, label=label, require_texts=True))
    affects = item.get("affects")
    if _nonempty_list(affects, label=f"{label}.affects", issues=issues):
        for index, name in enumerate(affects):
            if _string(name, label=f"{label}.affects[{index}]", issues=issues) and name not in rule_names:
                issues.append(f"{label} affects `{name}`, which is not a rule in this module.")
    return issues


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def registered_pairs(payload: Any) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    entries = payload.get("entries") if isinstance(payload, dict) else None
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        adopted = entry.get("adopted_by")
        for item in adopted if isinstance(adopted, list) else []:
            if isinstance(item, dict) and isinstance(item.get("module"), str) and isinstance(item.get("interpretation"), str):
                pairs.add((item["module"], item["interpretation"]))
    return pairs


def unregistered_tensions(root: Path, payload: Any) -> tuple[list[str], list[str]]:
    """(failures, warnings) for module interpretations whose texts cite two or
    more provisions but which no entry adopts. Two provisions in tension are a
    source disagreement.

    A ruled, confirmed or contradicted interpretation fails: it comes from a
    human ruling or a publisher's reply, which is when its register entry is
    written. An open one only warns: signed encoder re-encodes carry the module
    and its manifest alone, and may emit open interpretations, so failing on
    them would block every such re-encode until someone added an entry by hand.
    The source-conflicts workflow lists open ones in a tracking issue.
    """

    pairs = registered_pairs(payload)
    failures: list[str] = []
    warnings: list[str] = []
    for path in iter_module_files(root):
        found = module_interpretations(path)
        if found is None:
            continue
        module = path.relative_to(root).as_posix()
        for item in found[0]:
            texts = item.get("texts")
            citations = {
                text.get("corpus_citation_path")
                for text in texts
                if isinstance(text, dict) and isinstance(text.get("corpus_citation_path"), str)
            } if isinstance(texts, list) else set()
            interp = item.get("id")
            if len(citations) >= 2 and (module, interp) not in pairs:
                message = (
                    f"{module}#{interp} ({item.get('status')}) records provisions in tension "
                    f"({', '.join(sorted(citations))}) but is not in {REGISTER_FILENAME}; "
                    "add an entry whose adopted_by names it."
                )
                (warnings if item.get("status") == "open" else failures).append(message)
    return failures, warnings


def check_register(payload: Any, ctx: RepoContext, *, scan_modules: bool = True) -> list[str]:
    issues: list[str] = []
    if not isinstance(payload, dict):
        return [f"{REGISTER_FILENAME} must be a mapping with `version` and `entries`."]
    if _recursive(payload):
        return [f"{REGISTER_FILENAME} contains itself through an alias; anchors and aliases are not allowed."]
    for key in payload:
        if key not in {"version", "entries"}:
            issues.append(f"{REGISTER_FILENAME} has unknown top-level key `{key}`.")
    if payload.get("version") != SCHEMA_VERSION:
        issues.append(f"{REGISTER_FILENAME} version must be {SCHEMA_VERSION}.")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        issues.append(f"{REGISTER_FILENAME} entries must be a list.")
        entries = []
    jurisdictions = ctx.jurisdictions()
    # An entry's identity is its global id, <jurisdiction>:<id>, so two
    # jurisdictions may each have an entry with the same local id.
    seen: dict[str, int] = {}
    for index, entry in enumerate(entries):
        issues.extend(check_entry(entry, index=index, ctx=ctx, jurisdictions=jurisdictions))
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and isinstance(entry.get("jurisdiction"), str):
            gid = global_id(entry)
            if gid in seen:
                issues.append(f"entries[{index}] `{gid}` duplicates entries[{seen[gid]}].")
            seen.setdefault(gid, index)
    issues.extend(hygiene_issues(payload))
    issues.extend(id_collision_issues(ctx.root, conflicts=payload))
    if scan_modules:
        issues.extend(unregistered_tensions(ctx.root, payload)[0])
    return issues


# ---------------------------------------------------------------------------
# Provenance: is a pinned commit shipped code of an allowed repository?

GITHUB_API = "https://api.github.com"
SHIPPED = frozenset({"identical", "behind"})  # compare <default branch>...<commit>


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A renamed or transferred repository answers with a redirect. That is a
    refusal, never permission to read a different repository."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001 - urllib's signature
        raise urllib.error.HTTPError(req.full_url, code, f"redirected to {newurl}", headers, fp)


def github_api(token: str | None = None, base_url: str = GITHUB_API) -> Callable[[str], Any]:
    """GET one GitHub REST path as JSON, without following redirects."""

    opener = urllib.request.build_opener(_NoRedirect)
    answers: dict[str, Any] = {}

    def get(path: str) -> Any:
        if path not in answers:
            request = urllib.request.Request(
                base_url + path, headers={"Accept": "application/vnd.github+json", "User-Agent": "axiom-source-conflicts"}
            )
            if token:
                request.add_header("Authorization", f"Bearer {token}")
            with opener.open(request, timeout=60) as response:
                answers[path] = json.load(response)
        return answers[path]

    return get


def commit_provenance(repo: str, commit: str, get: Callable[[str], Any]) -> dict[str, Any]:
    """Whether `commit` is shipped code of `repo`, asked of GitHub.

    It is when GitHub's canonical name for the repository is exactly `repo`
    (no rename, transfer or redirect), the repository is not a fork, and
    comparing its default branch with the commit says `identical` or
    `behind`, so the commit is reachable from that branch. GitHub serves every
    object of a fork network through the parent's URL, and refs/pull/* holds
    other people's commits, so neither a successful fetch nor a pull-request
    ref says who wrote a commit. Any API failure, including an exhausted rate
    limit, is a refusal. Returns {"shipped": bool, "reason": str | None, ...}.
    """

    record: dict[str, Any] = {"repo": repo, "commit": commit, "shipped": False, "reason": None}
    if not (REPO_RE.fullmatch(repo) and repo.split("/", 1)[1] not in {".", ".."} and COMMIT_RE.fullmatch(commit)):
        record["reason"] = f"{repo}@{commit} is not a repository and full commit SHA"
        return record
    try:
        meta = get(f"/repos/{repo}")
        if not isinstance(meta, Mapping):
            raise ValueError("the repository answer is not a JSON object")
        record["full_name"], record["fork"] = meta.get("full_name"), meta.get("fork")
        if meta.get("full_name") != repo:
            record["reason"] = f"GitHub names this repository {meta.get('full_name')!r}, not {repo!r}"
            return record
        if meta.get("fork") is not False:
            record["reason"] = f"{repo} is a fork (or GitHub did not say it is not)"
            return record
        branch = meta.get("default_branch")
        if not (isinstance(branch, str) and branch):
            raise ValueError("the repository answer names no default branch")
        record["default_branch"] = branch
        compare = get(f"/repos/{repo}/compare/{urllib.parse.quote(branch, safe='/')}...{commit}")
        if not isinstance(compare, Mapping):
            raise ValueError("the compare answer is not a JSON object")
        record["status"] = compare.get("status")
    except urllib.error.HTTPError as exc:
        remaining = exc.headers.get("x-ratelimit-remaining") if exc.headers is not None else None
        if exc.code in (403, 429) and remaining == "0":
            record["reason"] = "GitHub's API rate limit is used up, so the commit's provenance is unknown"
        elif 300 <= exc.code < 400:
            record["reason"] = f"GitHub redirected the request ({exc.code}); the repository was renamed or moved"
        else:
            record["reason"] = f"GitHub answered {exc.code} ({exc.reason})"
        return record
    except (urllib.error.URLError, OSError, ValueError) as exc:
        record["reason"] = f"GitHub's API could not be read: {exc}"
        return record
    if not (isinstance(record["status"], str) and record["status"] in SHIPPED):
        record["reason"] = (
            f"{commit[:12]} is not reachable from {repo}'s default branch {branch!r} "
            f"(compare says {record['status']!r}); pin a commit on that branch"
        )
        return record
    record["shipped"] = True
    return record


# ---------------------------------------------------------------------------
# verify (network)

Fetch = Callable[[str, str, str], bytes]


def github_fetch(token: str | None = None) -> Fetch:
    """Read one file of a public repository at a commit."""

    cache: dict[tuple[str, str, str], bytes] = {}

    def fetch(repo: str, commit: str, path: str) -> bytes:
        key = (repo, commit, path)
        if key not in cache:
            url = (
                f"https://raw.githubusercontent.com/{repo}/{commit}/"
                + urllib.parse.quote(path)
            )
            request = urllib.request.Request(url)
            if token:
                request.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(request, timeout=60) as response:
                cache[key] = response.read()
        return cache[key]

    return fetch


def snapshot_text(data: bytes, path: str) -> str:
    """The text an excerpt is matched against: markup stripped for HTML/XML."""

    text = data.decode("utf-8")
    if path.endswith((".html", ".htm", ".xml")):
        text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
        # Inline markup sits inside words and sentences ("exception<b>'s</b>",
        # eCFR's <E T="03">), so it goes without a trace; any other tag ends a
        # block and becomes a space.
        text = INLINE_TAG_RE.sub("", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
    elif not path.endswith((".txt", ".md")):
        raise ValueError(f"unsupported snapshot type: {path}")
    return re.sub(r"\s+", " ", text).strip()


def encoder_matcher() -> Callable[[str, str], bool]:
    """axiom-encode's proof-atom matcher, the one module validation uses."""

    from axiom_encode.harness.proof_validator import _source_contains_proof_evidence

    def matches(source_text: str, excerpt: str) -> bool:
        return bool(_source_contains_proof_evidence(source_text=source_text, evidence_text=excerpt.strip()))

    return matches


def pinned_corpus_resolver(corpus_path: Path, release: str, content_sha256: str, public_key: str) -> Callable[[str], str | None]:
    """Resolve a citation in the pinned corpus release exactly as validation does."""

    from axiom_encode.corpus_resolver import (
        CorpusSourceNotFoundError,
        LocalCorpusRelease,
        require_canonical_corpus_citation_path,
        resolve_local_corpus_source,
    )

    local = LocalCorpusRelease(name=release, content_sha256=content_sha256, root=corpus_path, public_key=public_key)

    def resolve(citation_path: str) -> str | None:
        require_canonical_corpus_citation_path(citation_path)
        try:
            return resolve_local_corpus_source(citation_path, local).proof_evidence_text
        except CorpusSourceNotFoundError:
            return None

    return resolve


def github_on_default_branch(token: str | None = None) -> Callable[[str, str], bool]:
    """Is a commit shipped code of its repository? The same question
    tools/pin_runner.py asks before fetching (commit_provenance): GitHub's
    canonical name is the pinned one, the repository is not a fork, and the
    commit is reachable from its default branch. False when compare says the
    commit is off that branch; any other refusal (an API failure, a rename, a
    fork) raises ValueError with its reason, which verify reports."""

    get = github_api(token)

    def reachable(repo: str, commit: str) -> bool:
        record = commit_provenance(repo, commit, get)
        if record["shipped"]:
            return True
        if isinstance(record.get("status"), str):
            return False
        raise ValueError(record["reason"])

    return reachable


def cites_global_id(source: str, gid: str) -> bool:
    """Does the file name this global id, as a whole id? A cite of us:a-b (or
    of a household choice extending the id) is not a cite of us:a."""

    return re.search(rf"(?<![A-Za-z0-9:-]){re.escape(gid)}(?![A-Za-z0-9:-])", source) is not None


UNCHECKED_REACHABILITY = "unchecked: default-branch reachability of external commits (no checker given)"
Shipped = Callable[[str, str, str], None]


def shipped_checker(on_default_branch: Callable[[str, str], bool] | None, issues: list[str]) -> Shipped:
    """shipped(label, repo, commit) records an issue unless the commit is
    reachable from its repository's default branch; a no-op without a checker."""

    def shipped(label: str, repo: str, commit: str) -> None:
        if on_default_branch is None:
            return
        try:
            ok = on_default_branch(repo, commit)
        except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
            issues.append(f"{label}: cannot tell whether {repo}@{commit[:12]} is on its default branch: {exc}")
            return
        if not ok:
            issues.append(
                f"{label}: {repo}@{commit[:12]} is not on {repo}'s default branch; pin a commit on it "
                "(after a squash merge, the merge commit), or list an unmerged change under proposed."
            )

    return shipped


def verify_texts(
    entry: Mapping[str, Any], label: str, *, resolve: Callable[[str], str | None] | None,
    matches: Callable[[str, str], bool], issues: list[str],
) -> int:
    """Each corpus text's excerpt is verbatim at its citation in the pinned
    release; returns how many verified."""

    verified = 0
    for t_index, text in enumerate(entry.get("texts") or []):
        t_label = f"{label}.texts[{t_index}]"
        path = text["corpus_citation_path"]
        if resolve is None:
            issues.append(f"{t_label}: not verified; no pinned corpus release was given.")
            continue
        try:
            body = resolve(path)
        except Exception as exc:  # noqa: BLE001 - every resolver failure is a finding
            issues.append(f"{t_label}: {path} could not be resolved in the pinned corpus release: {exc}")
            continue
        if body is None:
            issues.append(f"{t_label}: {path} is not in the pinned corpus release.")
        elif not matches(body, text["excerpt"]):
            issues.append(f"{t_label}: the excerpt is not verbatim at {path} in the pinned corpus release.")
        else:
            verified += 1
    return verified


def verify_pending_texts(
    entry: Mapping[str, Any], label: str, *, fetch: Fetch, matches: Callable[[str, str], bool],
    shipped: Shipped, issues: list[str],
) -> int:
    """Each pending text's snapshot is shipped, has its sha256, and holds the
    excerpt verbatim; returns how many verified."""

    verified = 0
    for p_index, item in enumerate(entry.get("pending_texts") or []):
        p_label = f"{label}.pending_texts[{p_index}]"
        snap = item["snapshot"]
        shipped(p_label, snap["repo"], snap["commit"])
        try:
            data = fetch(snap["repo"], snap["commit"], snap["path"])
        except (urllib.error.URLError, OSError) as exc:
            issues.append(f"{p_label}: cannot read {snap['repo']}@{snap['commit'][:12]}:{snap['path']}: {exc}")
            continue
        actual = hashlib.sha256(data).hexdigest()
        if actual != snap["sha256"]:
            issues.append(f"{p_label}: snapshot sha256 is {actual}, not {snap['sha256']}.")
            continue
        try:
            text = snapshot_text(data, snap["path"])
        except (UnicodeDecodeError, ValueError) as exc:
            issues.append(f"{p_label}: cannot read the snapshot as text: {exc}")
            continue
        if not matches(text, item["excerpt"]):
            issues.append(f"{p_label}: the excerpt is not verbatim in {snap['path']}.")
        else:
            verified += 1
    return verified


def verify_external_tests(
    entry: Mapping[str, Any], label: str, *, fetch: Fetch, shipped: Shipped, issues: list[str]
) -> int:
    """Each external test's commit is shipped and its file defines the pinned
    test (the screen; tools/pin_runner.py runs it); returns how many passed
    the screen. Tests in this repository are checked offline."""

    verified = 0
    for t_index, item in enumerate(entry.get("tests") or []):
        if "repo" not in item:
            continue  # checked offline
        t_label = f"{label}.tests[{t_index}]"
        shipped(t_label, item["repo"], item["commit"])
        try:
            source = fetch(item["repo"], item["commit"], item["path"])
        except (urllib.error.URLError, OSError) as exc:
            issues.append(f"{t_label}: cannot read {item['repo']}@{item['commit'][:12]}:{item['path']}: {exc}")
            continue
        where = f"{item['repo']}@{item['commit'][:12]}:{item['path']}"
        if not test_exists(item["path"], item["name"], source):
            issues.append(f"{t_label}: {missing_test(item['name'], where)}")
        else:
            verified += 1
    return verified


def verify_register(
    payload: Mapping[str, Any],
    *,
    fetch: Fetch,
    matches: Callable[[str, str], bool],
    resolve: Callable[[str], str | None] | None,
    on_default_branch: Callable[[str, str], bool] | None = None,
) -> tuple[list[str], list[str]]:
    """(issues, report lines). `resolve` None skips corpus texts, reported.

    Every external commit (implementations, tests, snapshots) must be reachable
    from its repository's default branch: the register records shipped code and
    published captures, never a pull request's branch, whose commits a squash
    merge leaves off the default branch. `on_default_branch` None skips that
    check, reported."""

    issues: list[str] = []
    report: list[str] = []
    shipped = shipped_checker(on_default_branch, issues)
    if on_default_branch is None:
        report.append(UNCHECKED_REACHABILITY)
    counts = {"texts": 0, "pending_texts": 0, "implementations": 0, "tests": 0}
    for index, entry in enumerate(payload.get("entries") or []):
        label = f"{global_id(entry)} (entries[{index}])"
        counts["texts"] += verify_texts(entry, label, resolve=resolve, matches=matches, issues=issues)
        counts["pending_texts"] += verify_pending_texts(
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
            cites = cites_global_id(source, global_id(entry))
            if cites != item["cites_entry"]:
                issues.append(
                    f"{i_label}: cites_entry is {str(item['cites_entry']).lower()} but the file "
                    f"{'contains' if cites else 'does not contain'} `{global_id(entry)}`."
                )
            else:
                counts["implementations"] += 1
            if not item["cites_entry"]:
                report.append(f"uncited: {i_label} ({item['repo']}:{item['path']}) does not cite {global_id(entry)} yet")
            adopts = item.get("adopts", ADOPTED_READING)
            if item["follows"] != adopts:
                report.append(
                    f"lags: {i_label} follows {item['follows']}, not the reading it adopts ({adopts})"
                )
        for r_index, item in enumerate(entry.get("proposed") or []):
            report.append(
                f"proposed: {label}.proposed[{r_index}] {item.get('pr')} would implement "
                f"{item.get('follows')} in {item.get('repo')}:{item.get('path')} (not counted until merged)"
            )
        for u_index, item in enumerate(entry.get("unpublished_sources") or []):
            report.append(
                f"unverifiable: {label}.unpublished_sources[{u_index}] is unpublished "
                f"({item.get('kind')}: {item.get('description')}, {item.get('date')}); verify cannot check it"
            )
        counts["tests"] += verify_external_tests(entry, label, fetch=fetch, shipped=shipped, issues=issues)
    report.insert(
        0,
        "verified: "
        + ", ".join(f"{count} {name.replace('_', ' ')}" for name, count in counts.items()),
    )
    return issues, report


# ---------------------------------------------------------------------------
# aggregate


def repo_jurisdiction_ok(repo: str, jurisdiction: str) -> bool:
    """rulespec-us holds us and us-*; rulespec-uk holds uk and uk-*."""

    name = repo.rsplit("/", 1)[-1]
    if not name.startswith("rulespec-"):
        return False
    country = name.removeprefix("rulespec-")
    return jurisdiction == country or jurisdiction.startswith(f"{country}-")


def citation_label(path: Any) -> Any:
    """A reader's citation for a US Code or CFR corpus path; others unchanged.

    us/statute/42/403/f/1 -> 42 U.S.C. 403(f)(1); us/regulation/20/404/435 -> 20 CFR 404.435.
    """

    if not isinstance(path, str):
        return path
    parts = path.split("/")
    if len(parts) >= 4 and parts[0] == "us" and parts[1] == "statute" and parts[2].isdigit():
        return f"{parts[2]} U.S.C. {parts[3]}" + "".join(f"({part})" for part in parts[4:])
    if len(parts) >= 5 and parts[0] == "us" and parts[1] == "regulation" and parts[2].isdigit():
        return f"{parts[2]} CFR {parts[3]}.{parts[4]}" + "".join(f"({part})" for part in parts[5:])
    return path


def aggregate(registers: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """One row per entry across repositories; issues for collisions."""

    rows: list[dict[str, Any]] = []
    issues: list[str] = []
    seen: dict[str, str] = {}
    for repo in sorted(registers):
        payload = registers[repo]
        for entry in (payload or {}).get("entries") or []:
            if not isinstance(entry, dict):
                continue
            gid = global_id(entry)
            if gid in seen:
                issues.append(f"{gid} is in both {seen[gid]} and {repo}.")
                continue
            seen[gid] = repo
            if not repo_jurisdiction_ok(repo, str(entry.get("jurisdiction"))):
                issues.append(f"{repo}: {gid} has a jurisdiction outside that repository.")
            texts = entry.get("texts") or []
            pending = entry.get("pending_texts") or []
            rows.append(
                {
                    "global_id": gid,
                    "repository": repo,
                    "jurisdiction": entry.get("jurisdiction"),
                    "program": entry.get("program"),
                    "question": entry.get("question"),
                    "years": entry.get("years"),
                    "conflict": entry.get("conflict", "live"),
                    "status": entry.get("status"),
                    "outcome": entry.get("outcome"),
                    "reading": entry.get("reading"),
                    "alternatives": [
                        {"id": alt.get("id"), "reading": alt.get("reading")}
                        for alt in _as_list(entry.get("alternatives"))
                        if isinstance(alt, dict)
                    ],
                    "sources": list(
                        dict.fromkeys(
                            [citation_label(text.get("corpus_citation_path")) for text in texts if isinstance(text, dict)]
                            + [item.get("citation") for item in pending if isinstance(item, dict)]
                        )
                    ),
                    "source_kinds": sorted(
                        {
                            kind
                            for kind in [
                                text_kind(entry, text["corpus_citation_path"])
                                for text in texts
                                if isinstance(text, dict) and isinstance(text.get("corpus_citation_path"), str)
                                and CORPUS_PATH_RE.fullmatch(text["corpus_citation_path"])
                            ]
                            + [item.get("kind") for item in pending if isinstance(item, dict)]
                            + [
                                item.get("kind")
                                for item in entry.get("unpublished_sources") or []
                                if isinstance(item, dict)
                            ]
                            if isinstance(kind, str)
                        }
                    ),
                    "ruling": entry.get("ruling"),
                    "adopted_by": entry.get("adopted_by") or [],
                    "implementations": [
                        {
                            **{key: item.get(key) for key in ("repo", "path", "follows")},
                            "adopts": item.get("adopts", ADOPTED_READING),
                            "principle": item["ruling"].get("principle") if isinstance(item.get("ruling"), dict) else None,
                        }
                        for item in _as_list(entry.get("implementations"))
                        if isinstance(item, dict)
                    ],
                    "tests": len(entry.get("tests") or []),
                    "money_case": entry.get("money_case"),
                }
            )
    return rows, issues


def _json_default(value: Any) -> str:
    if isinstance(value, dt.date):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def render_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Source conflicts across Axiom registers",
        "",
        f"{len(rows)} entr{'y' if len(rows) == 1 else 'ies'}. Generated by tools/source_conflicts.py aggregate.",
        "",
        "| Global id | Years | Status | Conflict | Outcome | Kinds | Sources | Alternatives | Implementations | Money case |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        money = row.get("money_case") or {}
        size = f"{money.get('amount')} {money.get('currency')}/{money.get('period')}" if money else ""
        sources = "; ".join(str(source) for source in row["sources"])
        years = row.get("years") or {}
        span = (
            f"{years.get('from')}\u2013{years.get('to', '')} ({years.get('type')})" if isinstance(years, dict) and years else ""
        )
        kinds = ", ".join(row.get("source_kinds") or [])
        alternatives = ", ".join(f"`{alt.get('id')}`" for alt in row.get("alternatives") or [])
        # Each consumer: what it follows today, and what it adopts when that differs.
        implementations = "; ".join(
            f"{item.get('repo')}: follows `{item.get('follows')}`"
            + (f", adopts `{item.get('adopts')}`" if item.get("adopts") != item.get("follows") else "")
            for item in row.get("implementations") or []
        )
        lines.append(
            f"| `{row['global_id']}` | {span} | {row['status']} | {row.get('conflict', 'live')} | "
            f"{row['outcome']} | {kinds} | {sources} | {alternatives} | {implementations} | {size} |"
        )
    return "\n".join(lines) + "\n"


def discover_registers(token: str | None, *, filename: str = REGISTER_FILENAME) -> tuple[dict[str, Any], list[str]]:
    """Every active rulespec-<country> repository's register (absent = none),
    or another root file of theirs (`filename`, such as CHOICES_FILENAME),
    read as load_register reads one. A file that can't be read is left out
    and named in the issues, so one repository can't stop the whole view."""

    registers: dict[str, Any] = {}
    issues: list[str] = []
    page = 1
    names: list[tuple[str, str]] = []
    while True:
        url = f"https://api.github.com/orgs/{ORGANISATION}/repos?per_page=100&page={page}&type=public"
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(request, timeout=60) as response:
            batch = json.load(response)
        if not batch:
            break
        names.extend(
            (repo["full_name"], repo["default_branch"])
            for repo in batch
            if not repo.get("archived") and re.fullmatch(r"rulespec-[a-z]{2}(-[a-z0-9]+)*", repo["name"])
        )
        page += 1
    for full_name, branch in sorted(names):
        url = f"https://raw.githubusercontent.com/{full_name}/{branch}/{filename}"
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            continue
        try:
            registers[full_name] = parse_register(data.decode("utf-8"), label=f"{full_name}: {filename}")
        except UnicodeDecodeError as exc:
            issues.append(f"{full_name}: {filename} is not valid UTF-8 YAML without anchors: {exc}")
        except RegisterError as exc:
            issues.append(str(exc))
    return registers, issues


def local_registers(specs: Iterable[str]) -> tuple[dict[str, Any], list[str]]:
    """The aggregate's local files (OWNER/REPO=PATH), read as discovery reads
    them: one that can't be read is left out and named in the issues."""

    registers: dict[str, Any] = {}
    issues: list[str] = []
    for spec in specs:
        repo, _, path = spec.partition("=")
        try:
            registers[repo] = load_register(Path(path))
        except RegisterError as exc:
            issues.append(f"{repo}: {exc}")
    return registers, issues


# ---------------------------------------------------------------------------
# CLI


def _toolchain_pin(root: Path) -> tuple[str, str]:
    import tomllib

    table = tomllib.loads((root / ".axiom" / "toolchain.toml").read_text())["toolchain"]
    return table["axiom_corpus_release"], table["axiom_corpus_release_content_sha256"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="offline schema and in-repo reference checks")
    check.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    check.add_argument("--repo", default=f"{ORGANISATION}/rulespec-us")
    check.add_argument(
        "--warnings-file",
        type=Path,
        help="also write the warnings here, one per line: unregistered open module interpretations",
    )
    verify = sub.add_parser("verify", help="network checks: excerpts, snapshots, external refs")
    verify.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    verify.add_argument("--corpus-path", type=Path, help="axiom-corpus checkout holding the pinned release")
    verify.add_argument("--public-key", default=os.environ.get("AXIOM_CORPUS_RELEASE_PUBLIC_KEY"))
    agg = sub.add_parser("aggregate", help="collect every rulespec repository's register")
    agg.add_argument("--register", action="append", default=[], metavar="OWNER/REPO=PATH", help="use a local file instead of discovery (repeatable)")
    agg.add_argument("--json", type=Path, help="write the rows as JSON")
    agg.add_argument("--markdown", type=Path, help="write a Markdown table")
    args = parser.parse_args(argv)

    if args.command == "check":
        path = args.root / REGISTER_FILENAME
        try:
            payload = load_register(path)
        except RegisterError as exc:
            print(f"source-conflicts: {exc}", file=sys.stderr)
            return 1
        issues = check_register(payload, RepoContext(root=args.root, repo=args.repo))
        warnings = unregistered_tensions(args.root, payload)[1] if isinstance(payload, dict) else []
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        for warning in warnings:
            print(f"warning: {warning}")
        if args.warnings_file is not None:
            args.warnings_file.write_text("".join(f"{warning}\n" for warning in warnings))
        entries = payload.get("entries") if isinstance(payload, dict) else None
        count = len(entries) if isinstance(entries, list) else 0
        print(
            f"{REGISTER_FILENAME}: {count} entr{'y' if count == 1 else 'ies'}, {len(issues)} issue(s), "
            f"{len(warnings)} unregistered open interpretation(s). This screen does not run pinned tests; "
            "tools/pin_runner.py does."
        )
        return 1 if issues else 0

    if args.command == "verify":
        try:
            payload = load_register(args.root / REGISTER_FILENAME)
        except RegisterError as exc:
            print(f"source-conflicts: {exc}", file=sys.stderr)
            return 1
        try:
            matches = encoder_matcher()
        except ImportError as exc:
            print(f"source-conflicts verify needs axiom-encode importable: {exc}", file=sys.stderr)
            return 2
        resolve = None
        if args.corpus_path is not None:
            if not args.public_key:
                print("source-conflicts verify: --public-key (or AXIOM_CORPUS_RELEASE_PUBLIC_KEY) is required with --corpus-path", file=sys.stderr)
                return 2
            release, content_sha256 = _toolchain_pin(args.root)
            resolve = pinned_corpus_resolver(args.corpus_path, release, content_sha256, args.public_key)
        token = os.environ.get("GITHUB_TOKEN")
        issues, report = verify_register(
            payload,
            fetch=github_fetch(token),
            matches=matches,
            resolve=resolve,
            on_default_branch=github_on_default_branch(token),
        )
        for line in report:
            print(line)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        print(f"{len(issues)} issue(s).")
        return 1 if issues else 0

    token = os.environ.get("GITHUB_TOKEN")
    registers, read_issues = local_registers(args.register) if args.register else discover_registers(token)
    rows, issues = aggregate(registers)
    issues = read_issues + issues
    if args.json:
        args.json.write_text(json.dumps(rows, indent=2, default=_json_default) + "\n")
    if args.markdown:
        args.markdown.write_text(render_markdown(rows))
    if not args.json and not args.markdown:
        print(json.dumps(rows, indent=2, default=_json_default))
    for issue in issues:
        print(f"- {issue}", file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
