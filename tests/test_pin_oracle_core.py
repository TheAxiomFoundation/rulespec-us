"""The optimum check against policyengine-core's own YAML runner.

tests/test_pin_runner.py drives the oracle with a stand-in for core's YAML
items. This file runs the real thing where policyengine-core is installed (the
dependency-light test environment skips it): a minimal model, cases
that force, imitate or override a choice, core's `OpenFiscaPlugin`, the
oracle, and `optimum_shown` on what the oracle recorded. Each case is one the
#1844 reviews executed against core, or the legitimate case next to it.
The pinned-tests workflow job installs policyengine-core to run it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

if os.environ.get("AXIOM_PIN_ORACLE_CORE_REQUIRED"):
    import policyengine_core  # noqa: F401 - the workflow requires it, so a missing install fails
else:
    pytest.importorskip("policyengine_core")

TOOLS = Path(__file__).resolve().parents[1] / "tools"

MODEL = textwrap.dedent(
    """\
    import numpy as np
    from policyengine_core.entities import build_entity
    from policyengine_core.enums import Enum
    from policyengine_core.model_api import where
    from policyengine_core.parameters import ParameterNode
    from policyengine_core.periods import MONTH, YEAR
    from policyengine_core.taxbenefitsystems import TaxBenefitSystem
    from policyengine_core.variables import Variable

    Person = build_entity(key="person", plural="people", label="Person", is_person=True)
    Household = build_entity(key="household", plural="households", label="Household",
                             roles=[{"key": "member", "plural": "members", "label": "Member"}])


    class FilingStatus(Enum):
        JOINT = "Joint"
        SEPARATE = "Separate"


    class income(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "income"


    class elects(Variable):
        # The choice: elected above an income of 10, while gov.flag is on.
        value_type = bool
        entity = Person
        definition_period = YEAR
        label = "elects"

        def formula(person, period, parameters):
            return (person("income", period) > 10) & parameters(period).gov.flag


    class checked(Variable):
        value_type = bool
        entity = Person
        definition_period = YEAR
        label = "checked"

        def formula(person, period, parameters):
            return person("income", period) > 5


    class p0(Variable):
        # A choice named like the instance id an axis generates.
        value_type = bool
        entity = Person
        definition_period = YEAR
        label = "p0"


    class always_true(Variable):
        value_type = bool
        entity = Person
        definition_period = YEAR
        label = "always true"

        def formula(person, period, parameters):
            return person("income", period) > -1


    class count(Variable):
        # An integer the model stores exactly, past float32's precision.
        value_type = int
        entity = Person
        definition_period = YEAR
        label = "count"

        def formula(person, period, parameters):
            return person("income", period) * 0 + 16777220


    class monthly_share(Variable):
        value_type = float
        entity = Person
        definition_period = MONTH
        label = "monthly share"

        def formula(person, period, parameters):
            return person("income", period.this_year) * 0 + 0.3


    class monthly_rate(Variable):
        # Always the default (0.0625) in every month; twelve of them sum to 0.75.
        value_type = float
        entity = Person
        definition_period = MONTH
        label = "monthly rate"

        def formula(person, period, parameters):
            return person("income", period.this_year) * 0 + 0.0625


    class bounded_name(Variable):
        # A fixed-length string: core stores it as bytes (dtype |S20).
        value_type = str
        max_length = 20
        entity = Person
        definition_period = YEAR
        label = "bounded name"

        def formula(person, period, parameters):
            return np.full(person.count, "16777220")


    NumericStatus = Enum("NumericStatus", {"0": "Zero", "16777219": "One", "16777220": "Two"})


    class numeric_status(Variable):
        # An enum whose member names are digits, past float32's precision.
        value_type = Enum
        possible_values = NumericStatus
        default_value = NumericStatus["0"]
        entity = Person
        definition_period = YEAR
        label = "numeric status"

        def formula(person, period, parameters):
            return where(person("income", period) > -1, NumericStatus["16777220"], NumericStatus["0"])


    class share(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "share"

        def formula(person, period, parameters):
            return where(person("income", period) > 10, 0.3, 0.5)


    class filing_status(Variable):
        value_type = Enum
        possible_values = FilingStatus
        default_value = FilingStatus.JOINT
        entity = Person
        definition_period = YEAR
        label = "filing status"

        def formula(person, period, parameters):
            return where(person("income", period) > 10, FilingStatus.SEPARATE, FilingStatus.JOINT)


    class MiniSystem(TaxBenefitSystem):
        def __init__(self):
            super().__init__([Person, Household])
            for variable in (income, elects, checked, p0, always_true, count, monthly_share, monthly_rate, numeric_status,
                             bounded_name, share, filing_status):
                self.add_variable(variable)
            self.parameters = ParameterNode("", data={"gov": {"flag": {"values": {"2000-01-01": True}}}})
    """
)

# name -> the YAML case
CASES = {
    "the model chooses": {"input": {"income": 20}, "output": {"elects": True}},
    "forced by input": {"input": {"income": 0, "elects": True}, "output": {"elects": True}},
    "forced through axes": {
        "input": {"people": {"p": {"income": 0}}, "axes": [[{"name": "elects", "count": 1, "min": 1, "max": 1}]]},
        "output": {"elects": True},
    },
    # Core's YAML runner compares within 1e-3 when a case gives no margin.
    "an implicit margin admits the default": {"input": {"income": 0}, "output": {"share": 0.5005}},
    # A margin of 0.99999999 rounds, in float32, to 1, so false passes as true
    # under some numpy versions (the round-2 review's core 3.23.6); under
    # others the case fails as a test. Either way, no pin passes.
    "a boolean margin admits the default": {
        "input": {"income": 0}, "output": {"elects": True}, "absolute_error_margin": 0.99999999,
    },
    "a float32 share the model chose": {"input": {"income": 20}, "output": {"share": 0.3}},
    # 0.500000001 is the default's float32 number, so the case can't tell them apart.
    "an option the default's float32 number": {
        "input": {"income": 0}, "output": {"share": 0.500000001}, "absolute_error_margin": 0,
    },
    # The axis names the instance p0; the output asserts `checked` for it, not the choice p0.
    "an instance named like the choice": {
        "input": {"people": {"p": {"income": 6}}, "axes": [[{"name": "checked", "count": 1, "min": 1, "max": 1}]]},
        "output": {"people": {"p0": {"checked": True}}},
    },
    "a dotted entity id is not a parameter": {"input": {"people": {"person.a": {"income": 20}}}, "output": {"elects": True}},
    "a parameter override": {"input": {"gov.flag": True, "income": 20}, "output": {"elects": True}},
    "an enum the model chose": {"input": {"income": 20}, "output": {"filing_status": "SEPARATE"}},
    "an enum the model did not choose": {"input": {"income": 0}, "output": {"filing_status": "JOINT"}},
    # Round 3 (P1): two entries pin one case on different variables.
    "a case two entries pin": {"input": {"income": 0}, "output": {"always_true": True}},
    # Round 3 (P2): one person chooses and the other doesn't.
    "two people, one chooses": {
        "input": {"people": {"rich": {"income": 20}, "poor": {"income": 0}}},
        "output": {"people": {"rich": {"elects": True}, "poor": {"elects": False}}},
    },
    # Round 3 (P3): an integer is compared exactly, not as float32.
    "an integer past float32": {"input": {"income": 0}, "output": {"count": 16777220}},
    # Round 4 (P1): a monthly variable read at a yearly case period is a sum,
    # not a choice, whether the sum differs from the option or, as twelve
    # defaults do here, equals another option.
    "a monthly choice at a yearly period": {"input": {"income": 0}, "output": {"monthly_share": 3.6}},
    "twelve monthly defaults sum to another option": {"input": {"income": 0}, "output": {"monthly_rate": 0.75}},
    "a monthly choice at a monthly period": {"period": "2026-01", "input": {"income": 0}, "output": {"monthly_share": 0.3}},
    # Round 4 (P1): an enum whose names are digits compares by name.
    "an enum with numeric names": {"input": {"income": 0}, "output": {"numeric_status": "16777220"}},
    # Round 5 (P2): a fixed-length string is recorded as text, not bytes.
    "a fixed-length string": {"input": {"income": 20}, "output": {"income": 20}},
}

# Cases whose test outcome depends on the numpy under core: each must either
# fail as a test (so its pins fail) or pass and be judged as listed below.
MAY_FAIL = {"a boolean margin admits the default"}

# (case name, (variable, chooses, default, instances), shown)
PINS = [
    ("the model chooses", ("elects", True, False, None), True),
    ("forced by input", ("elects", True, False, None), False),
    ("forced through axes", ("elects", True, False, None), False),
    ("an implicit margin admits the default", ("share", "0.5005", "0.5", None), False),
    ("a boolean margin admits the default", ("elects", True, False, None), False),
    ("a float32 share the model chose", ("share", "0.3", "0.5", None), True),
    ("an option the default's float32 number", ("share", "0.500000001", "0.5", None), False),
    ("an instance named like the choice", ("p0", True, False, None), False),
    ("a dotted entity id is not a parameter", ("elects", True, False, None), True),
    ("a parameter override", ("elects", True, False, None), False),
    ("an enum the model chose", ("filing_status", "separate", "joint", None), True),
    ("an enum the model did not choose", ("filing_status", "separate", "joint", None), False),
    ("a case two entries pin", ("elects", True, False, None), False),
    ("a case two entries pin", ("always_true", True, False, None), True),
    ("two people, one chooses", ("elects", True, False, None), False),
    ("two people, one chooses", ("elects", True, False, ("rich",)), True),
    ("two people, one chooses", ("elects", True, False, ("poor",)), False),
    ("two people, one chooses", ("elects", True, False, ("nobody",)), False),
    ("an integer past float32", ("count", "16777219", "0", None), False),
    ("an integer past float32", ("count", "16777220", "0", None), True),
    ("a monthly choice at a yearly period", ("monthly_share", "0.3", "0.5", None), False),
    ("twelve monthly defaults sum to another option", ("monthly_rate", "0.75", "0.0625", None), False),
    ("a monthly choice at a monthly period", ("monthly_share", "0.3", "0.5", None), True),
    ("an enum with numeric names", ("numeric_status", "16777219", "0", None), False),
    ("an enum with numeric names", ("numeric_status", "16777220", "0", None), True),
    ("a fixed-length string", ("bounded_name", "16777220", "0", None), True),
    ("a fixed-length string", ("bounded_name", "16777219", "0", None), False),
]

DRIVER = textwrap.dedent(
    """\
    import json, sys
    import pytest
    from policyengine_core.tools.test_runner import OpenFiscaPlugin
    from minimodel import MiniSystem

    code = pytest.main(["-q", "-p", "axiom_pin_oracle", "-p", "no:cacheprovider", "cases.yaml"],
                       plugins=[OpenFiscaPlugin(MiniSystem(), {})])
    sys.exit(int(code))
    """
)


def _load_runner():
    import importlib.util

    spec = importlib.util.spec_from_file_location("pin_runner_core", TOOLS / "pin_runner.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_the_oracle_reads_what_core_computed(tmp_path):
    runner = _load_runner()
    cases = [{"name": name, "period": 2026, **case} for name, case in CASES.items()]  # a case may give its own period
    (tmp_path / "minimodel.py").write_text(MODEL)
    (tmp_path / "driver.py").write_text(DRIVER)
    (tmp_path / "cases.yaml").write_text(json.dumps(cases))  # JSON is YAML
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join([str(tmp_path), str(TOOLS / "pin_oracle")]),
        "AXIOM_PIN_ORACLE_OUT": str(tmp_path / "oracle.json"),
        "AXIOM_PIN_ORACLE_ROOT": str(tmp_path),
        "AXIOM_PIN_ORACLE_PINS": json.dumps([["cases.yaml", name] for name in CASES]),
        "AXIOM_PIN_ORACLE_CHOICES": json.dumps(sorted({("cases.yaml", name, expect[0]) for name, expect, _ in PINS})),
    }
    process = subprocess.run([sys.executable, "driver.py"], cwd=tmp_path, env=env, capture_output=True, text=True,
                             timeout=600)
    output = process.stdout[-3000:] + process.stderr[-3000:]
    assert (tmp_path / "oracle.json").is_file(), output
    record = json.loads((tmp_path / "oracle.json").read_text())
    items, failed = {}, set()
    for item in record["collected"]:
        phases = record["reports"].get(str(item["index"]), {})
        outcomes = [phases[when]["outcome"] for when in ("setup", "call", "teardown")]
        if outcomes != ["passed"] * 3:
            assert item["name"] in MAY_FAIL, (item["name"], outcomes)
            failed.add(item["name"])
        items[item["name"]] = item
    assert set(items) == set(CASES)
    assert process.returncode == (1 if failed else 0), output
    # The case two entries pin holds one record per variable.
    assert set(items["a case two entries pin"]["choices"]) == {"elects", "always_true"}
    assert items["two people, one chooses"]["choices"]["elects"]["ids"] == ["rich", "poor"]
    assert items["an integer past float32"]["choices"]["count"]["dtype"].startswith("int")
    verdicts = [(name, expect, runner.optimum_shown(items[name], expect)) for name, expect, _ in PINS if name not in failed]
    # Only the pins the model chose show an optimum.
    assert [reason is None for _, _, reason in verdicts] == [shown for name, _, shown in PINS if name not in failed], verdicts
    detail = {(name, expect[0], expect[1], expect[3]): reason for name, expect, reason in verdicts}
    assert "sets elects as an input" in detail[("forced through axes", "elects", True, None)]
    assert "computed share = 0.5" in detail[("an implicit margin admits the default", "share", '0.5005', None)]
    if "a boolean margin admits the default" not in failed:
        assert "computed elects = False" in detail[("a boolean margin admits the default", "elects", True, None)]
    assert "is the default" in detail[("an option the default's float32 number", "share", '0.500000001', None)]
    assert "computed p0 = False" in detail[("an instance named like the choice", "p0", True, None)]
    assert "changes the model (gov.flag)" in detail[("a parameter override", "elects", True, None)]
    assert "computed filing_status = 'JOINT'" in detail[("an enum the model did not choose", "filing_status", 'separate', None)]
    assert "computed elects = False" in detail[("a case two entries pin", "elects", True, None)]
    assert "computed elects = False, not" in detail[("two people, one chooses", "elects", True, None)]
    assert "computed elects = False for poor" in detail[("two people, one chooses", "elects", True, ("poor",))]
    assert "has no instance 'nobody'" in detail[("two people, one chooses", "elects", True, ("nobody",))]
    assert "computed count = 16777220" in detail[("an integer past float32", "count", '16777219', None)]
    assert "defined by month, over 2026" in detail[("a monthly choice at a yearly period", "monthly_share", '0.3', None)]
    assert "defined by month, over 2026" in detail[("twelve monthly defaults sum to another option", "monthly_rate", '0.75', None)]
    assert "computed numeric_status = '16777220'" in detail[("an enum with numeric names", "numeric_status", '16777219', None)]
    bounded = items["a fixed-length string"]["choices"]["bounded_name"]
    assert bounded["computed"] == ["16777220"] and bounded["dtype"].startswith(("|S", "<S")), bounded
    # The record says what it read: the definition period and the period's unit and size.
    yearly = items["a monthly choice at a yearly period"]["choices"]["monthly_share"]
    assert (yearly["definition_period"], yearly["period_unit"], yearly["period_size"]) == ("month", "year", 1)
