"""Reproduce the SNAP lone-minor income bug in PolicyEngine US 1.767.3."""

from importlib.metadata import version

from policyengine_us import Simulation


YEAR = "2026"
MONTH = "2026-01"
ANNUAL_EARNINGS = 217_027.52


def make_simulation(
    age: int, state: str, in_k12: bool | None = None
) -> Simulation:
    person = {
        "age": {YEAR: age},
        "employment_income": {YEAR: ANNUAL_EARNINGS},
        "is_household_head": True,
    }
    if in_k12 is not None:
        person["is_in_k12_school"] = {YEAR: in_k12}

    return Simulation(
        situation={
            "people": {"person": person},
            "families": {"family": {"members": ["person"]}},
            "marital_units": {"marital_unit": {"members": ["person"]}},
            "spm_units": {"spm_unit": {"members": ["person"]}},
            "tax_units": {"tax_unit": {"members": ["person"]}},
            "households": {
                "household": {
                    "members": ["person"],
                    "state_code": {YEAR: state},
                }
            },
        }
    )


def scalar(simulation: Simulation, variable: str, period: str):
    return simulation.calculate(variable, period)[0].item()


def show(
    label: str, age: int, state: str, in_k12: bool | None = None
) -> None:
    simulation = make_simulation(age, state, in_k12)
    variables = {
        "employment_income_annual": ("employment_income", YEAR),
        "is_in_k12_school": ("is_in_k12_school", YEAR),
        "monthly_age": ("monthly_age", MONTH),
        "is_household_head": ("is_household_head", YEAR),
        "is_tax_unit_head": ("is_tax_unit_head", YEAR),
        "is_tax_unit_dependent": ("is_tax_unit_dependent", YEAR),
        "spm_unit_size": ("spm_unit_size", YEAR),
        "snap_unit_size": ("snap_unit_size", MONTH),
        "snap_excluded_child_earner": (
            "snap_excluded_child_earner",
            MONTH,
        ),
        "snap_countable_earner": ("snap_countable_earner", MONTH),
        "snap_earned_income_person": ("snap_earned_income_person", MONTH),
        "snap_earned_income": ("snap_earned_income", MONTH),
        "snap_gross_income": ("snap_gross_income", MONTH),
        "meets_snap_gross_income_test": (
            "meets_snap_gross_income_test",
            MONTH,
        ),
        "snap_net_income": ("snap_net_income", MONTH),
        "meets_snap_net_income_test": (
            "meets_snap_net_income_test",
            MONTH,
        ),
        "is_snap_eligible": ("is_snap_eligible", MONTH),
        "snap": ("snap", MONTH),
    }
    print(f"\n{label}")
    for label_name, (variable, period) in variables.items():
        print(f"{label_name}={scalar(simulation, variable, period)}")


print(f"policyengine-us={version('policyengine-us')}")
print(f"policyengine-core={version('policyengine-core')}")
print(f"spm-calculator={version('spm-calculator')}")
show("AL, age 17, K-12 imputed", 17, "AL")
show("NC, age 15, K-12 imputed", 15, "NC")
show("AL, age 17, K-12 explicitly false", 17, "AL", False)
show("AL, age 18, K-12 imputed", 18, "AL")
