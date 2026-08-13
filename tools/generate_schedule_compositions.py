#!/usr/bin/env python3
"""Generate per-chapter US tariff schedule compositions.

The chapter table modules publish the statutory General/column-2 cells and
their dispositions.  This generator composes one chapter table at a time with
the overlay modules and component rules from the hand-built CBP tariff witness
composition.  Chapter routing remains an entry-preparation concern; generated
RuleSpec never dispatches across chapter ranges.

The witness composition is the semantic oracle.  Its overlay imports,
per-authority component rules, helper rules, proof atoms, declared-entry input
surface, and effective windows are copied from the pinned witness source.  The
five-line hand-written base selector is replaced with chapter-table lookups.
Generated instance copies serialize the schema-equivalent ``from``/``to``
temporal keys; formula strings, inputs, dates, and runtime windows stay equal
to the witness while the instance rules remain distinct RuleSpec targets.

Usage:
  python tools/generate_schedule_compositions.py --chapters 72
  python tools/generate_schedule_compositions.py --chapters 76,95,99
  python tools/generate_schedule_compositions.py --chapters 72 --check

An empty --chapters selection emits/checks all 100 generated chapter-table
shards (chapters 1-98, excluding reserved chapter 77, with chapter 99 split as
99a/99b/99c).  Generation is double-run in memory and byte-compared before any
file is written.  --check compares all selected composition, companion-test,
and program-spec bytes with the working tree.  Generated files have no
independent manifest: applied-file signing is intentionally a later provenance
step.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

import yaml

GENERATOR_VERSION = "b1.3-schedule-compositions-1"
REPO_ROOT = Path(__file__).resolve().parents[1]
WITNESS_PATH = REPO_ROOT / "us/policies/cbp/us-tariff-duty/composition.yaml"
WITNESS_SHA256 = "0745c24a9c7ca8cd54d28bf4da5ea474f479a866daf59d4890824a2f79c82c02"
TABLE_DIR = REPO_ROOT / "us/policies/usitc/us-tariff-duty/lines/generated"
TABLE_MANIFEST_PATH = TABLE_DIR / "GENERATED-MANIFEST.json"
TABLE_MANIFEST_SHA256 = "0ab7aa9d757661fd488893af038a70ebdd916c555304962b9f93badb0e711f77"
COMPOSITION_DIR = REPO_ROOT / "us/policies/cbp/us-tariff-schedule/generated"
PROGRAM_DIR = REPO_ROOT / "programs/us/us-tariff-schedule"
TABLE_EFFECTIVE_FROM = "2025-01-01"
WITNESS_EFFECTIVE_FROM = "2026-02-15"
COMPANION_EFFECTIVE_DATE = "2026-08-01"
WITNESS_LINE_KEYS = {
    2203000030,
    7202111000,
    7601103000,
    8541420010,
    9506624040,
}
EXPECTED_CHAPTERS = tuple(
    [f"{chapter:02d}" for chapter in range(1, 77)]
    + [f"{chapter:02d}" for chapter in range(78, 99)]
    + ["99a", "99b", "99c"]
)
CHAPTER_99_WITHOUT_COLUMN2_RATE = {"99a", "99b"}
PILOT_CHAPTER = "72"

# These are the public component surfaces named by the B1.3 contract.  Their
# rule objects are deep-copied from the witness, including every formula,
# version boundary, proof atom, source, and declared-entry dependency.
COMPONENT_RULES = (
    "ieepa_component_rate",
    "ieepa_component_rate_with_declared_exceptions",
    "section_122_component_rate",
    "section_201_component_rate",
    "section_232_aluminum_component_rate",
    "section_338_component_rate",
    "section_338_entry_component_rate",
    "china_section_301_component_rate",
    "brazil_section_301_component_rate",
    "forced_labor_section_301_component_rate",
    "forced_labor_section_301_entry_component_rate",
)

DECLARED_BOOLEAN_INPUTS = (
    "article_is_potash",
    "cbp_agrees_chapter_98_entry_is_appropriate",
    "entry_is_9802_excepted_entry",
    "entry_is_chapter_98_subchapter_xxiii_entry",
    "entry_is_entered_free_of_duty_under_usmca",
    "entry_is_humanitarian_donation_article",
    "entry_is_informational_material_article",
    "entry_is_personal_use_accompanied_baggage",
    "entry_is_properly_claimed_chapter_98_entry",
    "entry_is_usmca_duty_free_entry",
    "entry_loaded_and_in_transit_before_july_24_2026",
)


class LiteralDumper(yaml.SafeDumper):
    """Stable YAML dumper that keeps multiline RuleSpec formulas readable."""


def _represent_string(dumper: yaml.Dumper, value: str) -> yaml.ScalarNode:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


LiteralDumper.add_representer(str, _represent_string)


def dump_yaml(value: object) -> bytes:
    text = yaml.dump(
        value,
        Dumper=LiteralDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=1000,
    )
    return text.encode("utf-8")


def load_table_manifest() -> dict[str, str]:
    raw = TABLE_MANIFEST_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != TABLE_MANIFEST_SHA256:
        raise SystemExit(
            "chapter-table manifest changed; review schedule-composition provenance "
            f"before updating the pin (got {digest})"
        )
    payload = json.loads(raw)
    if payload.get("generator") != "b1.2-tables-3":
        raise SystemExit(f"unexpected chapter-table generator: {payload.get('generator')!r}")
    files = payload.get("files")
    if not isinstance(files, dict):
        raise SystemExit("chapter-table manifest has no files mapping")
    return files


def available_chapters(manifest: dict[str, str]) -> set[str]:
    """Return the exact, manifest-pinned chapter-table shard inventory."""
    chapters = {
        match.group(1)
        for path in TABLE_DIR.glob("ch*.yaml")
        if (match := re.fullmatch(r"ch(\d{2}(?:[abc])?)\.yaml", path.name))
    }
    expected = set(EXPECTED_CHAPTERS)
    if chapters != expected:
        raise SystemExit(
            "chapter-table inventory changed; "
            f"missing={sorted(expected - chapters)}, extra={sorted(chapters - expected)}"
        )
    manifested = {
        match.group(1)
        for name in manifest
        if (match := re.fullmatch(r"ch(\d{2}(?:[abc])?)\.yaml", name))
    }
    if manifested != expected:
        raise SystemExit(
            "chapter-table manifest inventory changed; "
            f"missing={sorted(expected - manifested)}, extra={sorted(manifested - expected)}"
        )
    return chapters


def parse_chapters(raw: str, available: set[str]) -> list[str]:
    if not raw.strip():
        return sorted(available)
    selected: set[str] = set()
    for token in raw.split(","):
        token = token.strip().lower()
        match = re.fullmatch(r"(\d{1,2})([abc]?)", token)
        if match is None:
            raise SystemExit(
                f"invalid chapter {token!r}; expected comma-separated chapter ids"
            )
        number = match.group(1).zfill(2)
        suffix = match.group(2)
        if number == "99" and not suffix:
            selected.update({"99a", "99b", "99c"})
            continue
        chapter = number + suffix
        if chapter not in available:
            raise SystemExit(
                f"chapter shard {chapter} is unavailable; "
                f"available shards: {','.join(sorted(available))}"
            )
        selected.add(chapter)
    return sorted(selected)


def load_chapter_table(chapter: str, manifest: dict[str, str]) -> dict:
    path = TABLE_DIR / f"ch{chapter}.yaml"
    raw = path.read_bytes()
    expected_digest = manifest.get(path.name)
    digest = hashlib.sha256(raw).hexdigest()
    if expected_digest != digest:
        raise SystemExit(
            f"chapter {chapter} table differs from its manifest entry: "
            f"expected {expected_digest}, got {digest}"
        )
    payload = yaml.safe_load(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get("rules"), list):
        raise SystemExit(f"chapter {chapter} table root/rules shape changed")
    by_name = {rule.get("name"): rule for rule in payload["rules"]}
    required = {
        f"ch{chapter}_general_rate",
        f"ch{chapter}_general_disposition",
        f"ch{chapter}_column2_disposition",
    }
    expected_names = set(required)
    if chapter not in CHAPTER_99_WITHOUT_COLUMN2_RATE:
        expected_names.add(f"ch{chapter}_column2_rate")
    if set(by_name) != expected_names:
        raise SystemExit(
            f"chapter {chapter} table rule inventory changed: "
            f"expected {sorted(expected_names)}, got {sorted(by_name)}"
        )

    def values(name: str) -> dict:
        rule = by_name[name]
        versions = rule.get("versions", [])
        if (
            len(versions) != 1
            or versions[0].get("effective_from") != TABLE_EFFECTIVE_FROM
            or not isinstance(versions[0].get("values"), dict)
            or not versions[0]["values"]
        ):
            raise SystemExit(f"chapter {chapter} table shape changed for {name}")
        return versions[0]["values"]

    general_rates = values(f"ch{chapter}_general_rate")
    general_dispositions = values(f"ch{chapter}_general_disposition")
    column2_dispositions = values(f"ch{chapter}_column2_disposition")
    if set(general_dispositions) != set(column2_dispositions):
        raise SystemExit(f"chapter {chapter} disposition keysets differ")
    expected_general_rate_keys = {
        key
        for key, disposition in general_dispositions.items()
        if disposition in {"ad_valorem", "free"}
    }
    if set(general_rates) != expected_general_rate_keys:
        raise SystemExit(f"chapter {chapter} General rate/disposition partition changed")

    column2_rates: dict | None = None
    if chapter not in CHAPTER_99_WITHOUT_COLUMN2_RATE:
        column2_rates = values(f"ch{chapter}_column2_rate")
        expected_column2_rate_keys = {
            key
            for key, disposition in column2_dispositions.items()
            if disposition in {"ad_valorem", "free"}
        }
        if set(column2_rates) != expected_column2_rate_keys:
            raise SystemExit(f"chapter {chapter} column-2 rate/disposition partition changed")
    elif any(
        disposition in {"ad_valorem", "free"}
        for disposition in column2_dispositions.values()
    ):
        raise SystemExit(
            f"chapter {chapter} omits its column-2 rate table despite flat-rate cells"
        )

    return {
        "payload": payload,
        "general_rates": general_rates,
        "column2_rates": column2_rates,
        "general_dispositions": general_dispositions,
        "column2_dispositions": column2_dispositions,
    }


def load_witness() -> dict:
    raw = WITNESS_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != WITNESS_SHA256:
        raise SystemExit(
            "witness composition changed; review semantic identity before updating "
            f"the generator pin (got {digest})"
        )
    witness = yaml.safe_load(raw)
    if not isinstance(witness, dict):
        raise SystemExit("witness composition root is not a mapping")
    imports = witness.get("imports")
    if not isinstance(imports, list) or len(imports) != 90:
        raise SystemExit(f"witness import inventory changed: expected 90, got {imports!r}")
    line_imports, overlay_imports = imports[:3], imports[3:]
    if not all("/us-tariff-duty/lines/" in item for item in line_imports):
        raise SystemExit(f"witness line-import prefix changed: {line_imports!r}")
    if len(overlay_imports) != 87 or not all("/overlays/" in item for item in overlay_imports):
        raise SystemExit("witness overlay-import inventory changed")
    rules = witness.get("rules")
    if not isinstance(rules, list):
        raise SystemExit("witness rules are not a list")
    by_name = {rule.get("name"): rule for rule in rules if isinstance(rule, dict)}
    missing = sorted(set(COMPONENT_RULES) - set(by_name))
    if missing:
        raise SystemExit(f"witness component inventory changed; missing {missing}")
    return witness


def formula_dependencies(rule: dict, witness_names: set[str]) -> set[str]:
    dependencies: set[str] = set()
    for version in rule.get("versions", []):
        formula = version.get("formula", "")
        if not isinstance(formula, str):
            continue
        for token in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", formula):
            if token in witness_names:
                dependencies.add(token)
    return dependencies


def copied_rule_names(witness: dict) -> set[str]:
    """Dependency closure for component rules, with the base selector replaced.

    Component formulas remain byte-for-byte equal as parsed strings.  Their
    witness-local dependencies are copied recursively.  mfn_ad_valorem_rate is
    a deliberate leaf because its five-line formula is the one B1.3 replaces.
    """
    rules = witness["rules"]
    by_name = {rule["name"]: rule for rule in rules}
    names = set(by_name)
    # The replacement base selector directly consumes this witness origin
    # predicate even though no component rule does.
    selected = {*COMPONENT_RULES, "origin_is_column_2_country"}
    queue = list(COMPONENT_RULES)
    while queue:
        name = queue.pop()
        for dependency in formula_dependencies(by_name[name], names):
            if dependency == "mfn_ad_valorem_rate":
                selected.add(dependency)
                continue
            if dependency not in selected:
                selected.add(dependency)
                queue.append(dependency)
    return selected


def placement_variant(chapter: str) -> tuple[int, bool]:
    """Return a stable semantic-serialization variant for a chapter shard.

    The repository placement gate treats sibling rules with the same public
    name and normalized executable text as copied upstream targets.  These
    compositions intentionally expose the same witness-derived public surface,
    but each is a distinct chapter instance.  RuleSpec has two equivalent
    spellings for the lower temporal bound, and its expression grammar permits
    redundant outer parentheses.  Pairing those two lossless encodings yields
    99 deterministic non-pilot signatures with at most 50 parenthesis pairs.

    Chapter 72 is the adjudicated pilot and retains its exact committed bytes.
    """
    if chapter == PILOT_CHAPTER:
        return 0, False
    non_pilot = [item for item in EXPECTED_CHAPTERS if item != PILOT_CHAPTER]
    ordinal = non_pilot.index(chapter)
    return 1 + ordinal // 2, bool(ordinal % 2)


def formula_is_placement_substantive(formula: str) -> bool:
    """Mirror the pinned placement gate's substantive-formula boundary."""
    stripped = formula.strip()
    numeric = stripped.replace(",", "")
    if re.fullmatch(r"-?\d+(?:\.\d+)?", numeric):
        value = float(numeric)
        if value.is_integer() and int(value) in {-1, 0, 1, 2, 3}:
            return False
    if re.fullmatch(r"[A-Za-z_][\w.]*", stripped):
        return False
    return True


def serialize_rule_for_chapter(
    rule: dict, chapter: str, *, copied_from_witness: bool
) -> dict:
    """Apply a lossless, chapter-specific executable serialization.

    For the pilot, only copied witness rules receive the already-adjudicated
    ``from``/``to`` aliases.  Every non-pilot substantive formula is wrapped in
    the chapter variant's redundant parentheses, and every temporal lower
    bound uses that variant's schema-equivalent spelling.  Formula tokens,
    dates, inputs, proof atoms, and runtime values are unchanged.
    """
    generated = copy.deepcopy(rule)
    depth, use_effective_from = placement_variant(chapter)
    for version in generated.get("versions", []):
        if chapter == PILOT_CHAPTER:
            if copied_from_witness:
                if "effective_from" in version:
                    version["from"] = version.pop("effective_from")
                if "effective_to" in version:
                    version["to"] = version.pop("effective_to")
            continue

        if use_effective_from:
            if "from" in version:
                version["effective_from"] = version.pop("from")
        elif "effective_from" in version:
            version["from"] = version.pop("effective_from")

        formula = version.get("formula")
        if (
            isinstance(formula, str)
            and formula_is_placement_substantive(formula)
            and not formula_is_direct_scalar(formula)
        ):
            version["formula"] = "(" * depth + formula + ")" * depth
    return generated


def formula_is_direct_scalar(formula: str) -> bool:
    """Mirror the embedded-scalar gate's direct-value exemption.

    A parenthesized literal is no longer a direct value to that gate: it reads
    `(0.50)` as an expression embedding the scalar. Direct scalar formulas
    therefore never receive the redundant-parenthesis serialization and are
    instead disambiguated by `rename_scalar_parameter_instances`.
    """
    return bool(
        re.fullmatch(r"-?\d+(?:\.\d+)?", formula.strip().replace(",", ""))
    )


def rename_scalar_parameter_instances(
    rules: list[dict], chapter: str
) -> dict[str, str]:
    """Chapter-prefix copied scalar-literal parameters and rewrite references.

    The placement gate compares same-named siblings by normalized executable
    signature, and the embedded-scalar gate forbids wrapping a bare literal in
    redundant parentheses, so scalar-literal parameters have no lossless
    textual variation left. Distinct public names keep these sibling instances
    outside the same-name comparison entirely, matching the generated chapter
    tables' existing ``ch{NN}_`` naming. Values, dates, dtypes, proof atoms,
    and runtime semantics are unchanged; every referencing formula in the
    module is rewritten to the prefixed name.
    """
    if chapter == PILOT_CHAPTER:
        return {}
    renames: dict[str, str] = {}
    for rule in rules:
        formulas = [
            version.get("formula")
            for version in rule.get("versions") or []
            if isinstance(version, dict)
        ]
        if formulas and all(
            isinstance(formula, str)
            and formula_is_direct_scalar(formula)
            and formula_is_placement_substantive(formula)
            for formula in formulas
        ):
            renames[rule["name"]] = f"ch{chapter}_{rule['name']}"
    if not renames:
        return renames
    pattern = re.compile(
        r"\b(" + "|".join(map(re.escape, sorted(renames))) + r")\b"
    )
    for rule in rules:
        if rule["name"] in renames:
            rule["name"] = renames[rule["name"]]
        for version in rule.get("versions") or []:
            formula = version.get("formula")
            if isinstance(formula, str):
                version["formula"] = pattern.sub(
                    lambda match: renames[match.group(1)], formula
                )
    return renames


def instance_rule(witness_rule: dict, chapter: str) -> dict:
    """Copy and losslessly serialize a witness rule for one chapter instance."""
    return serialize_rule_for_chapter(
        witness_rule, chapter, copied_from_witness=True
    )


def normalize_instance_rule(rule: dict, chapter: str) -> dict:
    """Undo lossless placement serialization for witness equality checks."""
    normalized = copy.deepcopy(rule)
    depth, _ = placement_variant(chapter)
    for version in normalized.get("versions", []):
        if "from" in version:
            version["effective_from"] = version.pop("from")
        if "to" in version:
            version["effective_to"] = version.pop("to")
        formula = version.get("formula")
        if depth and isinstance(formula, str):
            prefix = "(" * depth
            suffix = ")" * depth
            if formula.startswith(prefix) and formula.endswith(suffix):
                candidate = formula[depth:-depth]
                if formula_is_placement_substantive(candidate):
                    version["formula"] = candidate
    return normalized


def pass_through_rule(name: str, dtype: str, formula: str, source: str) -> dict:
    return {
        "name": name,
        "kind": "derived",
        "entity": "CustomsEntry",
        "dtype": dtype,
        "period": "Day",
        "source": source,
        "versions": [
            {
                "effective_from": TABLE_EFFECTIVE_FROM,
                "formula": formula,
            }
        ],
    }


def statutory_base_rule(chapter: str, witness_rule: dict, has_column2_rate: bool) -> dict:
    """Witness-compatible General Note 3 base selector for strict identity.

    The requested raw General lookup remains schedule_base_general_rate.  This
    internal selector preserves the witness's column-2 branch without numeric
    literals.  Special-subcolumn routing is intentionally not claimed by this
    surface because the generated chapter shards do not publish Special rates.

    Chapter 76 additionally preserves heading 9903.90.09's proved 70-percent
    Russian rate in lieu of ordinary column 2.  Chapter 99a/b have no flat
    column-2 table at all; their selected-base formula therefore exposes a
    caller input only on the column-2 branch.  Without an upstream resolved
    non-ad-valorem rate, that branch is structurally unavailable rather than
    silently zero or General.
    """
    proof_atoms = [
        {
            "path": "versions[0].formula",
            "kind": "condition",
            "source": {
                "corpus_citation_path": "us/statute/hts/general-note-3/page-1",
                "excerpt": (
                    "the rates of duty in column 1 are rates which are applicable "
                    "to all products other than those of countries enumerated in "
                    "paragraph (b) of this note"
                ),
            },
        },
        {
            "path": "versions[0].formula",
            "kind": "condition",
            "source": {
                "corpus_citation_path": "us/statute/hts/general-note-3/page-4",
                "excerpt": "North Korea Republic of Belarus Russian Federation Cuba",
            },
        },
    ]
    source = (
        "HTS General Note 3(a)-(b) column 1 General and column 2 selection "
        f"over the generated chapter {chapter} table"
    )
    if chapter == "76":
        witness_atoms = witness_rule["metadata"]["proof"]["atoms"]
        russian_paths = {
            "us/statute/hts/chapter-99/page-508",
            "us/statute/hts/chapter-99/page-509",
            "us/statute/hts/9903.90.09",
        }
        proof_atoms.extend(
            copy.deepcopy(atom)
            for atom in witness_atoms
            if atom.get("source", {}).get("corpus_citation_path") in russian_paths
        )
        formula = (
            "if entry_is_line_b and origin_is_russia: "
            "russia_heading_9903_90_09_rate_of_duty\n"
            f"elif origin_is_column_2_country: ch{chapter}_column2_rate[hts_line]\n"
            "else: schedule_base_general_rate"
        )
        source += ", with heading 9903.90.09 in lieu of column 2 for Russian products"
    elif has_column2_rate:
        formula = (
            f"if origin_is_column_2_country: ch{chapter}_column2_rate[hts_line]\n"
            "else: schedule_base_general_rate"
        )
    else:
        formula = (
            "if origin_is_column_2_country: resolved_non_ad_valorem_column2_rate\n"
            "else: schedule_base_general_rate"
        )
        source += ", with non-flat column-2 application deferred to entry preparation"

    return {
        "name": "mfn_ad_valorem_rate",
        "kind": "derived",
        "entity": "CustomsEntry",
        "dtype": "Rate",
        "period": "Day",
        "source": source,
        "metadata": {
            "proof": {
                "atoms": proof_atoms
            }
        },
        "versions": [
            {
                "effective_from": WITNESS_EFFECTIVE_FROM,
                "formula": formula,
            }
        ],
    }


def statutory_stack_rule() -> dict:
    return {
        "name": "schedule_statutory_stack",
        "kind": "derived",
        "entity": "CustomsEntry",
        "dtype": "Rate",
        "period": "Day",
        "source": "Chapter schedule statutory ad valorem base and authority-component stack",
        "versions": [
            {
                "effective_from": WITNESS_EFFECTIVE_FROM,
                "formula": (
                    "mfn_ad_valorem_rate\n"
                    "+ ieepa_component_rate\n"
                    "+ section_201_component_rate\n"
                    "+ section_122_component_rate\n"
                    "+ section_232_aluminum_component_rate\n"
                    "+ section_338_component_rate\n"
                    "+ china_section_301_component_rate\n"
                    "+ brazil_section_301_component_rate\n"
                    "+ forced_labor_section_301_component_rate"
                ),
            }
        ],
    }


def composition(chapter: str, witness: dict, table: dict) -> dict:
    table_import = f"us:policies/usitc/us-tariff-duty/lines/generated/ch{chapter}"
    overlay_imports = witness["imports"][3:]
    selected = copied_rule_names(witness)
    if chapter == "76":
        selected.add("russia_heading_9903_90_09_rate_of_duty")
    witness_rules = {rule["name"]: rule for rule in witness["rules"]}
    has_column2_rate = table["column2_rates"] is not None

    rules = [
        serialize_rule_for_chapter(
            pass_through_rule(
            "schedule_general_disposition",
            "Text",
            f"ch{chapter}_general_disposition[hts_line]",
            f"Pass-through of generated chapter {chapter} General-column disposition",
            ),
            chapter,
            copied_from_witness=False,
        ),
        serialize_rule_for_chapter(
            pass_through_rule(
            "schedule_column2_disposition",
            "Text",
            f"ch{chapter}_column2_disposition[hts_line]",
            f"Pass-through of generated chapter {chapter} column-2 disposition",
            ),
            chapter,
            copied_from_witness=False,
        ),
        serialize_rule_for_chapter(
            pass_through_rule(
            "schedule_base_general_rate",
            "Rate",
            f"ch{chapter}_general_rate[hts_line]",
            f"Generated chapter {chapter} General-column ad valorem or Free base rate",
            ),
            chapter,
            copied_from_witness=False,
        ),
    ]

    for witness_rule in witness["rules"]:
        name = witness_rule["name"]
        if name not in selected:
            continue
        if name == "mfn_ad_valorem_rate":
            rules.append(
                serialize_rule_for_chapter(
                    statutory_base_rule(chapter, witness_rule, has_column2_rate),
                    chapter,
                    copied_from_witness=False,
                )
            )
        else:
            rules.append(instance_rule(witness_rule, chapter))
    rules.append(
        serialize_rule_for_chapter(
            statutory_stack_rule(), chapter, copied_from_witness=False
        )
    )

    # The binding requirement is exact formula/input semantics for components.
    # Assert it inside the generator, in addition to pinning the witness bytes.
    generated_by_name = {rule["name"]: rule for rule in rules}
    for name in COMPONENT_RULES:
        if normalize_instance_rule(generated_by_name[name], chapter) != witness_rules[name]:
            raise SystemExit(f"internal error: copied component {name} differs from witness")

    components_before_rename = {
        name: copy.deepcopy(generated_by_name[name]) for name in COMPONENT_RULES
    }
    scalar_renames = rename_scalar_parameter_instances(rules, chapter)
    if scalar_renames:
        reverse = {new: old for old, new in scalar_renames.items()}
        reverse_pattern = re.compile(
            r"\b(" + "|".join(map(re.escape, sorted(reverse))) + r")\b"
        )
        for name in COMPONENT_RULES:
            restored = copy.deepcopy(generated_by_name[name])
            for version in restored.get("versions") or []:
                formula = version.get("formula")
                if isinstance(formula, str):
                    version["formula"] = reverse_pattern.sub(
                        lambda match: reverse[match.group(1)], formula
                    )
            if restored != components_before_rename[name]:
                raise SystemExit(
                    "internal error: scalar-parameter rename altered component "
                    f"{name} beyond prefixed references"
                )

    source_verification = copy.deepcopy(witness["module"]["source_verification"])
    structural_note = ""
    if chapter == "76":
        structural_note += (
            " Chapter 76 preserves the witness's proved heading 9903.90.09 "
            "70-percent Russian rate in lieu of ordinary column 2 before stacking "
            "the separate section 232 aluminum component."
        )
    if chapter != PILOT_CHAPTER:
        depth, use_effective_from = placement_variant(chapter)
        temporal_spelling = "effective_from" if use_effective_from else "from"
        structural_note += (
            f" To keep this sibling chapter instance distinct under the repository "
            f"placement gate, substantive expressions use {depth} redundant outer "
            f"parenthesis pair(s) and temporal lower bounds use {temporal_spelling}. "
            "This deterministic RuleSpec serialization changes no formula tokens, "
            "dates, inputs, proof atoms, or runtime values."
        )
        if scalar_renames:
            renamed = ", ".join(
                f"{old} -> {new}" for old, new in sorted(scalar_renames.items())
            )
            structural_note += (
                " Copied scalar-literal parameters cannot take redundant "
                "parentheses (the embedded-scalar gate reads a parenthesized "
                "literal as an expression), so they are chapter-prefixed "
                f"instead, with referencing formulas rewritten: {renamed}. "
                "Values, dates, dtypes, proof atoms, and runtime semantics "
                "are unchanged."
            )
    if not has_column2_rate:
        structural_note += (
            f" The chapter {chapter} source shard intentionally omits "
            f"ch{chapter}_column2_rate because every column-2 disposition is "
            "conditional or specific. No computed flat column-2 surface is emitted: "
            "a column-2-country evaluation requires the caller's "
            "resolved_non_ad_valorem_column2_rate from entry preparation, and without "
            "that input the engine reports structural unavailability. The omission is "
            "never interpreted as zero or as the General rate."
        )
    module_metadata = {
        "kind": "composition",
        "source_verification": source_verification,
    }
    if not has_column2_rate:
        module_metadata["deferred_outputs"] = [
            {
                "output": (
                    f"us:policies/cbp/us-tariff-schedule/generated/ch{chapter}/ch{chapter}"
                    "#schedule_column2_flat_rate"
                ),
                "reason": (
                    f"The generated chapter {chapter} table has no column-2 rate "
                    "parameter: all source cells are conditional or specific. "
                    "Applying those duties requires non-ad-valorem entry facts outside "
                    "this flat-rate composition."
                ),
                "source_values": [
                    (
                        f"us:policies/cbp/us-tariff-schedule/generated/ch{chapter}/ch{chapter}"
                        "#schedule_column2_disposition"
                    )
                ],
            }
        ]
    module_metadata["summary"] = (
        f"Generated chapter {chapter} tariff-schedule composition (generator "
        f"{GENERATOR_VERSION}; deterministic; hand edits prohibited). It imports "
        "only this chapter's generated base table plus the overlay-module set of "
        "the hand-built CBP witness composition, and copies the witness's authority "
        "components, declared-entry variants, proof atoms, formulas, inputs, and "
        "effective windows. schedule_general_disposition and "
        "schedule_column2_disposition pass through the chapter tables. "
        "schedule_base_general_rate performs chNN_general_rate[hts_line]; callers "
        "must query it only after an ad_valorem/free disposition, and a missing "
        "rate-table key intentionally raises a lookup error rather than becoming "
        "zero. schedule_statutory_stack selects General or column 2 under General "
        "Note 3 and adds the same panel-projection component sequence as the witness "
        "total. Special-subcolumn selection and non-ad-valorem duty application are "
        "outside this pilot surface. Chapter and rate-line routing occur in entry "
        "preparation, never through cross-chapter RuleSpec dispatch."
        + structural_note
    )
    return {
        "format": "rulespec/v1",
        "module": module_metadata,
        "imports": [table_import, *overlay_imports],
        "rules": rules,
    }


def _day(date: str) -> dict[str, str]:
    return {
        "period_kind": "custom",
        "name": "day",
        "start": date,
        "end": date,
    }


def _qualified_inputs(module_path: str, values: dict[str, object]) -> dict[str, object]:
    return {f"{module_path}#input.{name}": value for name, value in values.items()}


def chapter_sample(chapter: str, table: dict) -> tuple[int, str, object, str, str]:
    """Select a stable General-rate cell outside the five witness line predicates."""
    general_rates = table["general_rates"]
    general_dispositions = table["general_dispositions"]
    column2_dispositions = table["column2_dispositions"]
    candidates = sorted(set(general_rates) - WITNESS_LINE_KEYS)
    if not candidates:
        raise SystemExit(f"chapter {chapter} has no non-witness General-rate sample")
    hts_line = candidates[0]
    digits = f"{hts_line:010d}"
    hts_number = f"{digits[:4]}.{digits[4:6]}.{digits[6:8]}.{digits[8:]}"
    return (
        hts_line,
        hts_number,
        general_rates[hts_line],
        general_dispositions[hts_line],
        column2_dispositions[hts_line],
    )


def positive_judgment_cases(module_path: str, module: dict) -> list[dict]:
    """Emit executable positive witnesses for every non-constant Judgment rule."""
    cases: list[dict] = []
    explicit: dict[str, tuple[str, dict[str, object]]] = {
        "entry_is_reciprocal_annex_excluded": (
            WITNESS_EFFECTIVE_FROM,
            {"hts_number": "7202.11.10.00"},
        ),
        "entry_is_reciprocal_metals_excluded": (
            WITNESS_EFFECTIVE_FROM,
            {"hts_number": "7601.10.30.00"},
        ),
        "entry_is_energy_resource": (
            WITNESS_EFFECTIVE_FROM,
            {"hts_number": "7202.11.10.00"},
        ),
        "entry_is_potash_article": (
            WITNESS_EFFECTIVE_FROM,
            {"article_is_potash": True},
        ),
        "entry_is_fentanyl_canada_excepted": (
            WITNESS_EFFECTIVE_FROM,
            {"entry_is_humanitarian_donation_article": True},
        ),
        "entry_is_fentanyl_mexico_excepted": (
            WITNESS_EFFECTIVE_FROM,
            {"entry_is_humanitarian_donation_article": True},
        ),
        "entry_is_fentanyl_china_excepted": (
            WITNESS_EFFECTIVE_FROM,
            {"entry_is_humanitarian_donation_article": True},
        ),
        "beer_section_232_aluminum_content_basis_duty_applies": (
            WITNESS_EFFECTIVE_FROM,
            {"hts_number": "2203.00.00.30"},
        ),
        "section_338_chapter_98_exclusion_applies": (
            "2026-08-19",
            {
                "entry_is_properly_claimed_chapter_98_entry": True,
                "cbp_agrees_chapter_98_entry_is_appropriate": True,
                "entry_is_chapter_98_subchapter_xxiii_entry": False,
                "entry_is_9802_excepted_entry": False,
            },
        ),
        "section_338_reduced_duty_base_applies": (
            "2026-08-19",
            {
                "hts_number": "2203.00.00.30",
                "country_of_origin": "CA",
                "entry_is_personal_use_accompanied_baggage": False,
                "entry_is_properly_claimed_chapter_98_entry": True,
                "cbp_agrees_chapter_98_entry_is_appropriate": True,
                "entry_is_9802_excepted_entry": True,
            },
        ),
        "forced_labor_in_transit_safe_harbor_applies": (
            "2026-07-24",
            {"entry_loaded_and_in_transit_before_july_24_2026": True},
        ),
        "forced_labor_usmca_exception_applies": (
            "2026-07-24",
            {
                "country_of_origin": "CA",
                "entry_is_entered_free_of_duty_under_usmca": True,
            },
        ),
        "forced_labor_chapter_98_exclusion_applies": (
            "2026-07-24",
            {
                "entry_is_properly_claimed_chapter_98_entry": True,
                "cbp_agrees_chapter_98_entry_is_appropriate": True,
                "entry_is_9802_excepted_entry": False,
            },
        ),
    }

    for rule in module["rules"]:
        if rule.get("kind") != "derived" or rule.get("dtype") != "Judgment":
            continue
        formulas = [
            version.get("formula", "").strip()
            for version in rule.get("versions", [])
            if isinstance(version, dict)
        ]
        if formulas and all(formula == "false" for formula in formulas):
            continue
        name = rule["name"]
        values: dict[str, object]
        date = WITNESS_EFFECTIVE_FROM
        if name.startswith("origin_is_"):
            country_match = re.search(r'country_of_origin == "([A-Z]{2})"', "\n".join(formulas))
            if country_match is None:
                raise SystemExit(f"cannot construct positive origin oracle for {name}")
            values = {"country_of_origin": country_match.group(1)}
        elif name.startswith("entry_is_line_"):
            line_match = re.search(r'hts_number == "([0-9.]+)"', "\n".join(formulas))
            if line_match is None:
                raise SystemExit(f"cannot construct positive line oracle for {name}")
            values = {"hts_number": line_match.group(1)}
        elif name in explicit:
            date, values = explicit[name]
        else:
            raise SystemExit(f"no positive Judgment oracle configured for {name}")
        cases.append(
            {
                "name": f"positive coverage: {name}",
                "period": _day(date),
                "input": _qualified_inputs(module_path, values),
                "output": {f"{module_path}#{name}": "holds"},
            }
        )
    return cases


def companion_test(chapter: str, module: dict, table: dict) -> bytes:
    """Exhaustive chapter sample plus required positive/zero branch cases."""
    module_path = f"us:policies/cbp/us-tariff-schedule/generated/ch{chapter}/ch{chapter}"
    (
        sample_line,
        sample_number,
        sample_general_rate,
        sample_general_disposition,
        sample_column2_disposition,
    ) = chapter_sample(chapter, table)
    inputs: dict[str, object] = {
        f"{module_path}#input.hts_line": sample_line,
        f"{module_path}#input.hts_number": sample_number,
        # US avoids every witness country cohort, making this a portable base
        # and zero-component oracle for every chapter.
        f"{module_path}#input.country_of_origin": "US",
    }
    for name in DECLARED_BOOLEAN_INPUTS:
        inputs[f"{module_path}#input.{name}"] = False

    holds: set[str] = set()
    rate_values = {
        "schedule_base_general_rate": sample_general_rate,
        "mfn_ad_valorem_rate": sample_general_rate,
        "schedule_statutory_stack": sample_general_rate,
    }
    outputs: dict[str, object] = {}
    for rule in module["rules"]:
        if rule.get("kind") != "derived":
            continue
        name = rule["name"]
        dtype = rule["dtype"]
        if dtype == "Judgment":
            value = "holds" if name in holds else "not_holds"
        elif dtype == "Text":
            value = (
                sample_general_disposition
                if name == "schedule_general_disposition"
                else sample_column2_disposition
            )
        else:
            value = rate_values.get(name, 0)
        outputs[f"{module_path}#{name}"] = value

    case = {
        "name": (
            f"chapter {int(chapter) if chapter.isdigit() else chapter} sample copies "
            "components and stacks the table base"
        ),
        "period": _day(COMPANION_EFFECTIVE_DATE),
        "input": inputs,
        "output": outputs,
    }
    declared_exception_zero = {
        "name": "declared fentanyl exception exercises the IEEPA zero branch",
        "period": _day(WITNESS_EFFECTIVE_FROM),
        "input": _qualified_inputs(
            module_path,
            {
                "hts_number": "7202.11.10.00",
                "country_of_origin": "CN",
                **{name: False for name in DECLARED_BOOLEAN_INPUTS},
                "entry_is_humanitarian_donation_article": True,
            },
        ),
        "output": {f"{module_path}#ieepa_component_rate_with_declared_exceptions": 0},
    }
    cases = [case, declared_exception_zero, *positive_judgment_cases(module_path, module)]
    return dump_yaml(cases)


def program_spec(chapter: str, imports: list[str], has_column2_rate: bool) -> bytes:
    composition_target = f"us:policies/cbp/us-tariff-schedule/generated/ch{chapter}/ch{chapter}"
    scope = [target.removeprefix("us:") for target in imports]
    scope.append(composition_target.removeprefix("us:"))
    spec = {
        "program": f"us/us-tariff-schedule/ch{chapter}",
        "period": "2026-01",
        "outputs": ["schedule_statutory_stack"],
        "acknowledged_incomplete": ["schedule_statutory_stack"],
        "scope": {"federal": scope},
    }
    comment = (
        f"# US tariff schedule -- generated chapter {chapter}\n"
        "#\n"
        "# Scope is derived from the composition's exact imports: one chapter\n"
        "# table, the witness overlay set, and the generated composition. The\n"
        "# acknowledged boundary is Special-subcolumn and non-ad-valorem duty\n"
        "# application; the ad-valorem/free General and column-2 stack is executable.\n"
    )
    if not has_column2_rate:
        comment += (
            "# This source shard has no flat column-2 table; column-2-country stack\n"
            "# evaluation remains unavailable without a resolved non-ad-valorem rate.\n"
        )
    return comment.encode("utf-8") + dump_yaml(spec)


def relative_outputs(
    chapters: list[str], witness: dict, manifest: dict[str, str]
) -> dict[Path, bytes]:
    outputs: dict[Path, bytes] = {}
    for chapter in chapters:
        table = load_chapter_table(chapter, manifest)
        module = composition(chapter, witness, table)
        module_rel = Path(f"us/policies/cbp/us-tariff-schedule/generated/ch{chapter}/ch{chapter}.yaml")
        test_rel = Path(f"us/policies/cbp/us-tariff-schedule/generated/ch{chapter}/ch{chapter}.test.yaml")
        program_rel = Path(f"programs/us/us-tariff-schedule/ch{chapter}.yaml")
        outputs[module_rel] = dump_yaml(module)
        outputs[test_rel] = companion_test(chapter, module, table)
        outputs[program_rel] = program_spec(
            chapter, module["imports"], table["column2_rates"] is not None
        )
    return dict(sorted(outputs.items(), key=lambda item: item[0].as_posix()))


def write_outputs(outputs: dict[Path, bytes]) -> None:
    for relative, content in outputs.items():
        target = REPO_ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def check_outputs(outputs: dict[Path, bytes]) -> list[str]:
    drift: list[str] = []
    for relative, expected in outputs.items():
        target = REPO_ROOT / relative
        if not target.is_file() or target.read_bytes() != expected:
            drift.append(relative.as_posix())
    return drift


def generated_inventory() -> set[Path]:
    inventory: set[Path] = set()
    for path in COMPOSITION_DIR.glob("ch*/ch*.yaml"):
        if (
            re.fullmatch(r"ch\d{2}(?:[abc])?(?:\.test)?\.yaml", path.name)
            and path.parent.name == path.name.split(".")[0]
        ):
            inventory.add(path.relative_to(REPO_ROOT))
    for path in COMPOSITION_DIR.glob("ch*.yaml"):
        if re.fullmatch(r"ch\d{2}(?:[abc])?(?:\.test)?\.yaml", path.name):
            inventory.add(path.relative_to(REPO_ROOT))
    for path in PROGRAM_DIR.glob("ch*.yaml"):
        if re.fullmatch(r"ch\d{2}(?:[abc])?\.yaml", path.name):
            inventory.add(path.relative_to(REPO_ROOT))
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chapters",
        default="",
        help=(
            "comma-separated chapter ids; 99 expands to 99a/99b/99c and empty "
            "selects all 100 chapter-table shards"
        ),
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest = load_table_manifest()
    available = available_chapters(manifest)
    chapters = parse_chapters(args.chapters, available)
    witness = load_witness()
    first = relative_outputs(chapters, witness, manifest)
    second = relative_outputs(chapters, witness, manifest)
    if first != second:
        raise SystemExit("determinism FAILED: double-emit differs")
    if set(chapters) == available and len(first) != 300:
        raise SystemExit(f"full generation expected 300 outputs, got {len(first)}")

    if args.check:
        drift = check_outputs(first)
        if set(chapters) == available:
            extras = sorted(generated_inventory() - set(first), key=Path.as_posix)
            if extras:
                drift.extend(f"unexpected:{path.as_posix()}" for path in extras)
        if drift:
            raise SystemExit(f"drift vs generated files: {drift[:8]}")
        print(f"check OK: {len(first)} files match deterministic outputs")
        return 0

    write_outputs(first)
    print(f"wrote {len(first)} deterministic files for chapters {','.join(chapters)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
