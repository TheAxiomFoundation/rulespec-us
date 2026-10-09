#!/usr/bin/env python3
"""Run household scenarios through a composed and compiled program.

This drives the same path the program-artifacts workflow publishes: compose
a ProgramSpec with the pinned axiom-compose, compile it with the artifact
engine (both via tools/build_program_artifacts.py), then execute requests with
`axiom-rules-engine run-compiled`.

The engine refuses a request that omits any input the queried outputs reach
("missing input ..."), so a scenario must supply every input slot. Slots and
their dtypes are read from the compiled artifact itself: each `kind: input`
node is typed by the expression it sits in (a comparison with a boolean
literal is a Judgment input, a table index an Integer, arithmetic a Decimal),
and scoped to the entity of the rule that reads it. Unset slots get a
type-appropriate zero (False / 0), and a scenario overrides the facts it is
about. This mirrors how consumers (axiom-oracles generic_inputs, finbot's
catalog) fill requests, without depending on either.

Used by tests/test_snap_eligibility_gates.py. Also runnable by hand:

    python tools/program_scenarios.py programs/us-fl/snap/fy-2026.yaml \
        '{"household_size": 1, "snap_countable_financial_resources": 9000}' \
        snap_eligible snap_resource_eligible
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

_BOOL_PARENTS = {"and", "or", "not"}
_NUMERIC_PARENTS = {"add", "sub", "mul", "div", "min", "max", "floor", "ceil", "sum_related"}
_RANK = {"integer": 3, "decimal": 2, "bool": 1}
_RELATED_KINDS = {"count_related", "sum_related"}


def _related_entity(relation: str) -> str:
    """Entity on the member side of a relation this harness can populate."""

    if relation.rsplit(".", 1)[-1] == "member_of_household":
        return "Person"
    return f"related:{relation}"


@dataclass(frozen=True)
class Slot:
    name: str
    entity: str
    dtype: str  # "bool" | "integer" | "decimal"


@dataclass
class Program:
    """A compiled program plus the input slots its rules read."""

    spec: str
    artifact: Path
    slots: dict[str, Slot]
    member_relations: list[str]
    ids: dict[str, str] = field(default_factory=dict)  # bare rule name -> output id


def _literal_kind(node: Any) -> str | None:
    if isinstance(node, Mapping) and node.get("kind") == "literal":
        return (node.get("value") or {}).get("kind")
    return None


def _rule_dtype(dtype: str | None) -> str:
    if dtype in ("judgment", "bool"):
        return "bool"
    if dtype in ("integer", "count"):
        return "integer"
    return "decimal"


def infer_slots(program: Mapping[str, Any]) -> dict[str, Slot]:
    """Every input the program's derived rules read, with entity and dtype."""

    candidates: dict[tuple[str, str], set[str]] = {}

    def note(name: str, entity: str, dtype: str) -> None:
        candidates.setdefault((name, entity), set()).add(dtype)

    def walk(
        node: Any,
        parent: Mapping[str, Any] | None,
        key: str | None,
        rule: Mapping[str, Any],
        entity: str,
    ) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item, parent, key, rule, entity)
            return
        if not isinstance(node, Mapping):
            return
        kind = node.get("kind")
        if kind == "input":
            pk = (parent or {}).get("kind")
            if parent is None:
                note(node["name"], entity, _rule_dtype(rule.get("dtype")))
            elif pk == "comparison":
                other = parent.get("right") if key == "left" else parent.get("left")
                lit = _literal_kind(other)
                if lit == "bool":
                    note(node["name"], entity, "bool")
                elif lit == "integer":
                    note(node["name"], entity, "integer")
                else:
                    note(node["name"], entity, "decimal")
            elif pk == "parameter_lookup" and key == "index":
                note(node["name"], entity, "integer")
            elif pk in _BOOL_PARENTS:
                note(node["name"], entity, "bool")
            elif pk in _NUMERIC_PARENTS:
                note(node["name"], entity, "decimal")
            elif pk == "if" and key in ("then_expr", "else_expr"):
                sibling = parent.get("else_expr" if key == "then_expr" else "then_expr")
                lit = _literal_kind(sibling)
                note(node["name"], entity, "bool" if lit == "bool" else _rule_dtype(rule.get("dtype")))
            elif pk == "if" and key == "condition":
                note(node["name"], entity, "bool")
            else:
                note(node["name"], entity, _rule_dtype(rule.get("dtype")))
            return
        for child_key, child in node.items():
            child_entity = entity
            if kind in _RELATED_KINDS and child_key not in ("relation", "current_slot", "related_slot"):
                # The body of count_related/sum_related is evaluated on the
                # related member, not on the rule's own entity.
                child_entity = _related_entity(node.get("relation", ""))
            walk(child, node if kind else parent, child_key, rule, child_entity)

    for rule in program.get("derived", []):
        walk(rule.get("expr"), None, None, rule, rule["entity"])
    slots: dict[str, Slot] = {}
    for (name, entity), dtypes in sorted(candidates.items()):
        dtype = max(dtypes, key=lambda d: _RANK[d])
        slots[name] = Slot(name=name, entity=entity, dtype=dtype)
    return slots


def _zero(dtype: str) -> Any:
    return False if dtype == "bool" else 0


def _value(dtype: str, value: Any) -> dict[str, Any]:
    if dtype == "bool":
        if not isinstance(value, bool):
            raise TypeError(f"expected a bool, got {value!r}")
        return {"kind": "bool", "value": value}
    if dtype == "integer":
        if isinstance(value, bool) or int(value) != value:
            raise TypeError(f"expected an integer, got {value!r}")
        return {"kind": "integer", "value": int(value)}
    return {"kind": "decimal", "value": str(value)}


def load_corpus(root: Path = ROOT) -> Any:
    """Parse and index the checkout once; reuse it for every build()."""

    from axiom_compose import load_corpus_from_roots

    return load_corpus_from_roots([root])


def build(
    spec: str | Path,
    *,
    engine_bin: str,
    workdir: Path,
    root: Path = ROOT,
    corpus_state: Any = None,
) -> Program:
    """Compose and compile one spec exactly as the program-artifacts workflow does."""

    sys.path.insert(0, str(root / "tools"))
    try:
        import build_program_artifacts as builder
    finally:
        sys.path.pop(0)

    spec_path = Path(spec)
    if not spec_path.is_absolute():
        spec_path = root / spec_path
    name = spec_path.relative_to(root / "programs").with_suffix("").as_posix().replace("/", "-")
    module = workdir / f"{name}.rulespec.yaml"
    artifact = workdir / f"{name}.compiled.json"
    build = builder.SpecBuild(
        spec_path=spec_path.relative_to(root),
        jurisdiction="",
        program_id="",
        period="",
        outputs=[],
        artifact_name=name,
    )
    if corpus_state is None:
        corpus_state = load_corpus(root)
    builder.compose_spec(root, build, module, corpus_state)
    builder.engine_compile(root, module, artifact, engine_bin)
    program = json.loads(artifact.read_text())["program"]
    return Program(
        spec=spec_path.relative_to(root).as_posix(),
        artifact=artifact,
        slots=infer_slots(program),
        member_relations=[
            relation["name"]
            for relation in program.get("relations", [])
            if relation["name"].rsplit(".", 1)[-1] == "member_of_household"
        ],
        ids={rule["name"]: rule.get("id") or rule["name"] for rule in program["derived"]},
    )


def _month(period: str) -> dict[str, str]:
    year, month = (int(part) for part in period.split("-"))
    start = dt.date(year, month, 1)
    end = dt.date(year + (month == 12), month % 12 + 1, 1)
    return {"start": start.isoformat(), "end": end.isoformat()}


def run(
    program: Program,
    households: Iterable[Mapping[str, Any]],
    *,
    outputs: Iterable[str],
    engine_bin: str,
    period: str = "2026-01",
) -> list[dict[str, Any]]:
    """Evaluate several households in one engine request.

    Each household is ``{"facts": {...}, "members": [{...}, ...]}``: facts are
    Household inputs, each member dict holds that Person's inputs. Every other
    slot gets its zero. Returns one ``{output: value}`` dict per household,
    keyed by bare rule name; judgments come back as "holds"/"not_holds".
    """

    interval = _month(period)
    outputs = list(outputs)
    inputs: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    queries: list[dict[str, Any]] = []
    query_period = {"period_kind": "month", **interval}
    households = list(households)
    for h_index, household in enumerate(households, 1):
        hid = f"household:{h_index}"
        facts = dict(household.get("facts") or {})
        members = list(household.get("members") or [{}])
        unknown = {
            name
            for name in [*facts, *(k for member in members for k in member)]
            if name not in program.slots
        }
        if unknown:
            raise KeyError(f"{program.spec}: not input slots of this program: {sorted(unknown)}")
        for slot in program.slots.values():
            if slot.entity == "Person" or slot.entity.startswith("related:"):
                continue
            value = facts.get(slot.name, _zero(slot.dtype))
            inputs.append(
                {
                    "name": f"axiom:{program.artifact.stem}#input.{slot.name}",
                    "entity": slot.entity,
                    "entity_id": hid,
                    "interval": interval,
                    "value": _value(slot.dtype, value),
                }
            )
        for p_index, member in enumerate(members, 1):
            pid = f"person:{h_index}-{p_index}"
            for relation in program.member_relations:
                relations.append({"name": relation, "tuple": [pid, hid], "interval": interval})
            for slot in program.slots.values():
                if slot.entity != "Person":
                    continue
                inputs.append(
                    {
                        "name": f"axiom:{program.artifact.stem}#input.{slot.name}",
                        "entity": "Person",
                        "entity_id": pid,
                        "interval": interval,
                        "value": _value(slot.dtype, member.get(slot.name, _zero(slot.dtype))),
                    }
                )
        queries.append(
            {
                "entity_id": hid,
                "period": query_period,
                "outputs": [program.ids.get(name, name) for name in outputs],
            }
        )
    request = {"mode": "explain", "dataset": {"inputs": inputs, "relations": relations}, "queries": queries}
    result = subprocess.run(
        [engine_bin, "run-compiled", "--artifact", str(program.artifact)],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    response = json.loads(result.stdout)
    back = {output_id: name for name, output_id in program.ids.items()}
    by_household: dict[str, dict[str, Any]] = {}
    for item in response["results"]:
        values = by_household.setdefault(item["entity_id"], {})
        for output_id, value in item["outputs"].items():
            values[back.get(output_id, output_id)] = _scalar(value)
    return [by_household[f"household:{index}"] for index in range(1, len(households) + 1)]


def _scalar(value: Any) -> Any:
    while isinstance(value, Mapping):
        for key in ("value", "outcome", "judgment"):
            if key in value:
                value = value[key]
                break
        else:
            return value
    return value


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    engine_bin = os.environ.get("AXIOM_RULES_ENGINE_BIN")
    if not engine_bin:
        print("AXIOM_RULES_ENGINE_BIN is not set", file=sys.stderr)
        return 2
    spec, facts, outputs = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3:]
    with tempfile.TemporaryDirectory(prefix="program-scenarios-") as tmp:
        program = build(spec, engine_bin=engine_bin, workdir=Path(tmp))
        household = {"facts": facts, "members": [facts.pop("members", {})] if "members" in facts else [{}]}
        print(json.dumps(run(program, [household], outputs=outputs, engine_bin=engine_bin)[0], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
