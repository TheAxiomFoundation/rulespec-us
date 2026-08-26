#!/usr/bin/env python3
"""Generate the grounded Section 338 Canada alcohol incidence and rate surface.

The successor corpus release exposes Proclamation 11046 Annex II as physical
pages and the August 18 temporal successor as a paragraph provision.  It does
not expose Proclamation 11047 or 11048 Annex pages, and Rev-15 predates U.S.
note 51.  This generator therefore emits the complete groundable alcohol list,
the corrected alcohol component, and explicit deferrals for dairy and motor
vehicles.  Source snapshots and the negative corpus finding are hash-pinned.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

import yaml


VERSION = "section-338-canada-1"
SUCCESSOR_RELEASE = "us-rulespec-2026-08-23-canada-338-suspension-union"

RULEMAKING_RELATIVE_PATH = Path(
    "data/corpus/provisions/us/rulemaking/"
    "2026-08-09-rulespec-tariff-rulemaking-union.jsonl"
)
RULEMAKING_SHA256 = "b25c5a42c47683b4f9fc0ad548007d10f97dd8ead629e6d1de872494030e05e0"
SUSPENSION_RELATIVE_PATH = Path(
    "data/corpus/provisions/us/rulemaking/2026-08-18-canada-338-suspension.jsonl"
)
SUSPENSION_SHA256 = "ea27a56ab605ff1dbda1a9b4a9e9bfbb38c8064b3510202d98625b19f461abb5"
REV15_RELATIVE_PATH = Path(
    "data/corpus/provisions/us/statute/2026-08-04-usitc-hts-2026-rev15-notes.jsonl"
)
REV15_SHA256 = "0f3ed7ef2efb64383825db65e615959200770e8511c8d4834b16e02892cb9ec8"

REPO_ROOT = Path(__file__).resolve().parents[1]
INCIDENCE_RELATIVE_DIR = Path(
    "us/policies/usitc/us-tariff-incidence/generated/note51/alcohol"
)
COMPONENT_RELATIVE_PATH = Path(
    "us/policies/cbp/us-tariff-duty/section-338-canada/component-rate.yaml"
)
COMPONENT_TEST_RELATIVE_PATH = COMPONENT_RELATIVE_PATH.with_suffix(".test.yaml")

ANNEX_PAGE_PREFIX = (
    "us/rulemaking/federal-register/2026-07-23/2026-14991/annex-ii/page-"
)
SUSPENSION_CLAUSE_PATH = (
    "us/rulemaking/white-house/2026-08-18/canada-338-suspension/clause-1"
)
MEMBERSHIP_START = (
    "1. Heading 9903.03.12 applies to articles classifiable in the following "
    "provisions of the tariff schedule:"
)
MEMBERSHIP_STOP = "(c) As provided in heading 9903.03.15"
HTS8 = re.compile(r"(?<![\d.])(\d{4}\.\d{2}\.\d{2})(?![\d.])")

ORIGINAL_DATE_EXCERPT = (
    "Effective with respect to goods entered for consumption, or withdrawn "
    "from warehouse for consumption, on or after 12:01 a.m. eastern time on "
    "August 19, 2026"
)
RATE_EXCERPT = "The duty provided in the applicable subheading + 50%"
MEMBERSHIP_EXCERPT = (
    "heading 9903.03.12 imposes an additional ad valorem rate of duty on "
    "imports of products of Canada enumerated in subdivision (b) of this note"
)
SECTION_232_EXCEPTION_EXCERPT = (
    "the additional duties imposed by heading 9903.03.12 shall not apply to:"
)
SECTION_232_SCOPE_EXCERPT = (
    "unless they are subject to import restrictions imposed pursuant to section "
    "232 of the Trade Expansion Act of 1962, as amended (18 U.S.C. 1862)"
)
SUSPENSION_EXCERPT = (
    "The effective date of the additional ad valorem duties imposed in "
    "Proclamations 11046, 11047, and 11048 shall be 12:01 a.m. eastern time "
    "on August 22, 2026."
)
AMENDMENT_EXCERPT = (
    "Accordingly, the chapeau of Annex II of each of Proclamations 11046, "
    "11047, and 11048, is amended by deleting the effective date “August 19, "
    "2026” and inserting “August 22, 2026” in lieu thereof."
)


class LiteralString(str):
    """A YAML string that should be serialized as a literal block."""


class RuleSpecDumper(yaml.SafeDumper):
    """Stable YAML dumper for generated RuleSpec artifacts."""

    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        """Indent block sequences to match the repository's generated style."""
        return super().increase_indent(flow, False)


def _represent_literal(
    dumper: yaml.SafeDumper, value: LiteralString
) -> yaml.nodes.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|")


RuleSpecDumper.add_representer(LiteralString, _represent_literal)


def dump_yaml(value: object) -> bytes:
    return yaml.dump(
        value,
        Dumper=RuleSpecDumper,
        allow_unicode=True,
        sort_keys=False,
        width=100,
    ).encode("utf-8")


def checked_bytes(path: Path, expected_sha256: str) -> bytes:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise SystemExit(
            f"source snapshot changed: {path} (expected {expected_sha256}, got {digest})"
        )
    return raw


def jsonl_records(raw: bytes) -> list[dict]:
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def source_atom(
    *,
    path: str,
    kind: str,
    citation_path: str,
    excerpt: str,
    context: dict | None = None,
) -> dict:
    atom = {
        "path": path,
        "kind": kind,
        "source": {
            "corpus_citation_path": citation_path,
            "excerpt": excerpt,
        },
    }
    if context is not None:
        atom["context"] = context
    return atom


def assert_excerpt(records_by_path: dict[str, dict], path: str, excerpt: str) -> None:
    body = records_by_path[path].get("body") or ""
    if excerpt not in body:
        raise SystemExit(f"verbatim excerpt absent from {path}: {excerpt!r}")


def extract_alcohol_membership(
    records_by_path: dict[str, dict],
) -> dict[int, list[str]]:
    fragments: dict[int, list[str]] = {}
    active = False
    complete = False
    for page_number in range(1, 8):
        citation_path = f"{ANNEX_PAGE_PREFIX}{page_number}"
        body = records_by_path[citation_path].get("body") or ""
        offset = 0
        if not active:
            offset = body.find(MEMBERSHIP_START)
            if offset < 0:
                continue
            offset += len(MEMBERSHIP_START)
            active = True
        end = body.find(MEMBERSHIP_STOP, offset)
        fragment = HTS8.findall(body[offset : end if end >= 0 else len(body)])
        if fragment:
            fragments[page_number] = fragment
        if end >= 0:
            complete = True
            break

    if not active or not complete:
        raise SystemExit(
            "could not delimit Proclamation 11046 Annex II membership list"
        )
    if {page: len(codes) for page, codes in fragments.items()} != {1: 12, 2: 51}:
        raise SystemExit(f"unexpected alcohol page counts: {fragments!r}")
    flattened = [code for codes in fragments.values() for code in codes]
    if len(flattened) != 63 or len(set(flattened)) != 63:
        raise SystemExit("alcohol membership must contain 63 unique HTS-8 atoms")
    return fragments


def incidence_module(page_number: int, codes: list[str]) -> bytes:
    citation_path = f"{ANNEX_PAGE_PREFIX}{page_number}"
    rule_name = f"section_338_alcohol_annex_ii_membership_p{page_number}"
    proof_atoms = [
        source_atom(
            path="versions[0].values",
            kind="parameter",
            citation_path=citation_path,
            excerpt=code,
            context={"subdivision": "51(b)(1)"},
        )
        for code in codes
    ]
    payload = {
        "format": "rulespec/v1",
        "module": {
            "proof_validation": {"required": True},
            "source_verification": {"corpus_citation_path": citation_path},
            "summary": LiteralString(
                f"Generated by {VERSION} deterministically from Proclamation "
                f"11046 Annex II page {page_number}; hand edits prohibited. "
                "The table preserves the August 19 planned membership boundary; "
                "the August 19–21 suspension is enforced by the component-rate "
                "successor versions."
            ),
        },
        "rules": [
            {
                "name": rule_name,
                "kind": "parameter",
                "dtype": "Count",
                "indexed_by": "hts_line",
                "source": (
                    "Proclamation 11046 Annex II, U.S. note 51(b)(1), "
                    f"printed page {page_number}"
                ),
                "metadata": {"proof": {"atoms": proof_atoms}},
                "versions": [
                    {
                        "effective_from": "2026-08-19",
                        "values": {int(code.replace(".", "")): 1 for code in codes},
                    }
                ],
            }
        ],
    }
    return dump_yaml(payload)


def incidence_test(page_number: int, code: str) -> bytes:
    module = (
        "us:policies/usitc/us-tariff-incidence/generated/note51/alcohol/"
        f"page-{page_number}"
    )
    rule_name = f"section_338_alcohol_annex_ii_membership_p{page_number}"
    payload = [
        {
            "name": f"{rule_name} membership-present",
            "period": {
                "period_kind": "custom",
                "name": "day",
                "start": "2026-08-22",
                "end": "2026-08-22",
            },
            "input": {f"{module}#input.hts_line": int(code.replace(".", ""))},
            "output": {f"{module}#{rule_name}": 1},
        }
    ]
    return dump_yaml(payload)


def deferred_outputs() -> list[dict]:
    reason = LiteralString(
        f"The signed {SUCCESSOR_RELEASE} selector has no citable Annex II "
        "page provisions for Proclamation 11047 or 11048. Their retained "
        "Federal Register text substitutes graphic-omission markers for the "
        "lists, and Rev-15 predates U.S. note 51. Verbatim membership/rate "
        "proof atoms require a newly ingested and signed corpus successor."
    )
    return [
        {
            "output": (
                "us:policies/usitc/us-tariff-incidence/generated/note51/dairy"
                "#section_338_dairy_annex_ii_membership"
            ),
            "reason": reason,
        },
        {
            "output": (
                "us:policies/usitc/us-tariff-incidence/generated/note51/"
                "motor-vehicles#section_338_motor_vehicle_annex_ii_membership"
            ),
            "reason": reason,
        },
        {
            "output": (
                "us:policies/cbp/us-tariff-duty/section-338-canada/component-rate"
                "#section_338_dairy_component_rate"
            ),
            "reason": reason,
        },
        {
            "output": (
                "us:policies/cbp/us-tariff-duty/section-338-canada/component-rate"
                "#section_338_motor_vehicle_component_rate"
            ),
            "reason": reason,
        },
    ]


def component_module() -> bytes:
    annex_i_page_1 = (
        "us/rulemaking/federal-register/2026-07-23/2026-14991/annex-i/page-1"
    )
    page_1 = f"{ANNEX_PAGE_PREFIX}1"
    page_2 = f"{ANNEX_PAGE_PREFIX}2"
    page_6 = f"{ANNEX_PAGE_PREFIX}6"
    payload = {
        "format": "rulespec/v1",
        "module": {
            "proof_validation": {"required": True},
            "source_verification": {
                "corpus_citation_paths": [
                    annex_i_page_1,
                    page_1,
                    page_2,
                    page_6,
                    SUSPENSION_CLAUSE_PATH,
                ]
            },
            "deferred_outputs": deferred_outputs(),
            "summary": LiteralString(
                "Proclamation 11046 scheduled a 50-percent additional duty for "
                "listed Canadian alcohol-family articles on August 19, 2026. "
                "The August 18 successor moved collection to August 22. The "
                "scalar remains the July-proclaimed amount, while the component "
                "is explicitly zero August 19–21 and active from August 22 for "
                "listed Canadian articles outside the U.S. note 51(c) Section "
                "232 carveout."
            ),
        },
        "rules": [
            {
                "name": "section_338_alcohol_additional_duty_rate",
                "kind": "parameter",
                "dtype": "Rate",
                "source": (
                    "Proclamation 11046 heading 9903.03.12 additional duty amount"
                ),
                "metadata": {
                    "proof": {
                        "atoms": [
                            source_atom(
                                path="versions[0].formula",
                                kind="parameter",
                                citation_path=page_6,
                                excerpt=RATE_EXCERPT,
                            ),
                            source_atom(
                                path="versions[0].effective_from",
                                kind="effective_period",
                                citation_path=page_1,
                                excerpt=ORIGINAL_DATE_EXCERPT,
                            ),
                        ]
                    }
                },
                "versions": [
                    {
                        "effective_from": "2026-08-19",
                        "formula": LiteralString("0.50"),
                    }
                ],
            },
            {
                "name": "section_338_alcohol_component_rate",
                "kind": "derived",
                "entity": "CustomsEntry",
                "dtype": "Rate",
                "period": "Day",
                "source": (
                    "Proclamation 11046 alcohol component with the August 18 "
                    "effective-date successor and U.S. note 51(c) carveout"
                ),
                "metadata": {
                    "proof": {
                        "atoms": [
                            source_atom(
                                path="versions[0].formula",
                                kind="effective_period",
                                citation_path=SUSPENSION_CLAUSE_PATH,
                                excerpt=AMENDMENT_EXCERPT,
                            ),
                            source_atom(
                                path="versions[1].effective_from",
                                kind="effective_period",
                                citation_path=SUSPENSION_CLAUSE_PATH,
                                excerpt=SUSPENSION_EXCERPT,
                            ),
                            source_atom(
                                path="versions[1].formula",
                                kind="condition",
                                citation_path=page_1,
                                excerpt=MEMBERSHIP_EXCERPT,
                            ),
                            source_atom(
                                path="versions[1].formula",
                                kind="exception",
                                citation_path=annex_i_page_1,
                                excerpt=SECTION_232_SCOPE_EXCERPT,
                            ),
                            source_atom(
                                path="versions[1].formula",
                                kind="exception",
                                citation_path=page_2,
                                excerpt=SECTION_232_EXCEPTION_EXCERPT,
                            ),
                        ]
                    }
                },
                "versions": [
                    {
                        "effective_from": "2026-08-19",
                        "effective_to": "2026-08-21",
                        "formula": LiteralString("0"),
                    },
                    {
                        "effective_from": "2026-08-22",
                        "formula": LiteralString(
                            "if article_product_of_canada\n"
                            "   and section_338_alcohol_annex_ii_membership\n"
                            "   and not article_is_section_232_carveout_under_note_51_c:\n"
                            "  section_338_alcohol_additional_duty_rate\n"
                            "else: 0"
                        ),
                    },
                ],
            },
        ],
    }
    return dump_yaml(payload)


def component_tests() -> bytes:
    module = "us:policies/cbp/us-tariff-duty/section-338-canada/component-rate"

    def case(
        name: str,
        date: str,
        *,
        canada: bool,
        listed: bool,
        section_232: bool,
        component_rate: float,
    ) -> dict:
        return {
            "name": name,
            "period": {
                "period_kind": "custom",
                "name": "day",
                "start": date,
                "end": date,
            },
            "input": {
                f"{module}#input.article_product_of_canada": canada,
                f"{module}#input.section_338_alcohol_annex_ii_membership": listed,
                (
                    f"{module}#input.article_is_section_232_carveout_under_note_51_c"
                ): section_232,
            },
            "output": {
                f"{module}#section_338_alcohol_additional_duty_rate": 0.5,
                f"{module}#section_338_alcohol_component_rate": component_rate,
            },
        }

    return dump_yaml(
        [
            case(
                "planned August 19 start is suspended",
                "2026-08-19",
                canada=True,
                listed=True,
                section_232=False,
                component_rate=0,
            ),
            case(
                "last suspension day remains zero",
                "2026-08-21",
                canada=True,
                listed=True,
                section_232=False,
                component_rate=0,
            ),
            case(
                "delayed August 22 start applies fifty percent",
                "2026-08-22",
                canada=True,
                listed=True,
                section_232=False,
                component_rate=0.5,
            ),
            case(
                "Section 232 carveout remains excluded",
                "2026-08-22",
                canada=True,
                listed=True,
                section_232=True,
                component_rate=0,
            ),
            case(
                "unlisted Canadian article has no component",
                "2026-08-22",
                canada=True,
                listed=False,
                section_232=False,
                component_rate=0,
            ),
            case(
                "listed non-Canadian article has no component",
                "2026-08-22",
                canada=False,
                listed=True,
                section_232=False,
                component_rate=0,
            ),
        ]
    )


def render(corpus_root: Path) -> dict[Path, bytes]:
    rulemaking_raw = checked_bytes(
        corpus_root / RULEMAKING_RELATIVE_PATH, RULEMAKING_SHA256
    )
    suspension_raw = checked_bytes(
        corpus_root / SUSPENSION_RELATIVE_PATH, SUSPENSION_SHA256
    )
    rev15_raw = checked_bytes(corpus_root / REV15_RELATIVE_PATH, REV15_SHA256)

    rulemaking_records = jsonl_records(rulemaking_raw)
    suspension_records = jsonl_records(suspension_raw)
    records_by_path = {
        record["citation_path"]: record
        for record in [*rulemaking_records, *suspension_records]
    }

    required_paths = {
        "us/rulemaking/federal-register/2026-07-23/2026-14991/annex-i/page-1",
        *(f"{ANNEX_PAGE_PREFIX}{number}" for number in range(1, 8)),
        SUSPENSION_CLAUSE_PATH,
    }
    missing = sorted(required_paths - records_by_path.keys())
    if missing:
        raise SystemExit(f"successor corpus paths missing: {missing}")

    for path, excerpt in (
        (
            "us/rulemaking/federal-register/2026-07-23/2026-14991/annex-i/page-1",
            SECTION_232_SCOPE_EXCERPT,
        ),
        (f"{ANNEX_PAGE_PREFIX}1", ORIGINAL_DATE_EXCERPT),
        (f"{ANNEX_PAGE_PREFIX}1", MEMBERSHIP_EXCERPT),
        (f"{ANNEX_PAGE_PREFIX}2", SECTION_232_EXCEPTION_EXCERPT),
        (f"{ANNEX_PAGE_PREFIX}6", RATE_EXCERPT),
        (SUSPENSION_CLAUSE_PATH, SUSPENSION_EXCERPT),
        (SUSPENSION_CLAUSE_PATH, AMENDMENT_EXCERPT),
    ):
        assert_excerpt(records_by_path, path, excerpt)

    rulemaking_text = rulemaking_raw.decode("utf-8")
    rev15_text = rev15_raw.decode("utf-8")
    forbidden_successor_atoms = (
        "9903.03.12",
        "9903.03.13",
        "9903.03.14",
        "U.S. note 51",
    )
    if any(atom in rev15_text for atom in forbidden_successor_atoms):
        raise SystemExit("Rev-15 Note 51 absence changed; review the deferral design")
    if (
        "2026-14992/annex-ii" in rulemaking_text
        or "2026-14997/annex-ii" in rulemaking_text
    ):
        raise SystemExit(
            "dairy/motor Annex pages now exist; remove deferrals and encode them"
        )

    fragments = extract_alcohol_membership(records_by_path)
    rendered: dict[Path, bytes] = {}
    for page_number, codes in fragments.items():
        module_path = INCIDENCE_RELATIVE_DIR / f"page-{page_number}.yaml"
        rendered[module_path] = incidence_module(page_number, codes)
        rendered[module_path.with_suffix(".test.yaml")] = incidence_test(
            page_number, codes[0]
        )
    rendered[COMPONENT_RELATIVE_PATH] = component_module()
    rendered[COMPONENT_TEST_RELATIVE_PATH] = component_tests()
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path(
            os.environ.get(
                "AXIOM_CORPUS_REPO",
                Path.home() / "TheAxiomFoundation/axiom-corpus",
            )
        ),
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    first = render(args.corpus)
    second = render(args.corpus)
    if first != second:
        raise SystemExit("determinism FAILED")

    if args.check:
        drift = [
            str(relative_path)
            for relative_path, expected in first.items()
            if not (REPO_ROOT / relative_path).exists()
            or (REPO_ROOT / relative_path).read_bytes() != expected
        ]
        if drift:
            raise SystemExit(f"drift: {drift}")
        print(f"check OK: {len(first)} files")
        return 0

    for relative_path, content in first.items():
        target = REPO_ROOT / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    print(f"wrote {len(first)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
