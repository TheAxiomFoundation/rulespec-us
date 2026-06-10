# rulespec-us-ny

New York RuleSpec encodings.

## Contents

- `statutes/`: New York statute RuleSpec YAML, with tests beside each encoding as `.test.yaml`.
- `regulations/`: New York regulation RuleSpec YAML, with tests beside each encoding as `.test.yaml`.
- `policies/`: New York policy RuleSpec YAML, with tests beside each encoding as `.test.yaml`.
- `.github/workflows/repository-checks.yml`: wrapper around the shared RuleSpec validation workflow.

## Conventions

Use RuleSpec YAML for encoded rules. Do not add source text, source registry
sidecars, generated source payloads, singular rule roots, separate
parameter/test fixture files, or generated formula artifacts.

Federal materials belong in `rulespec-us`. New York-administered state and city materials belong here.

## PolicyEngine ECPS SNAP Comparison

Compare the New York SNAP composition against PolicyEngine ECPS (enhanced CPS) records
with the shared `axiom-encode` oracle command:

```bash
uv run --project ../axiom-encode --with policyengine-us --with numpy \
  axiom-encode snap-ecps-compare \
  --jurisdiction us-ny \
  --utility-projection policyengine-type \
  --min-match-rate 0.95
```

The comparison uses PolicyEngine's `snap_normal_allotment`, not top-level
`snap`, because microsimulation `snap` includes take-up adjustments. It compares
against RuleSpec `us:statutes/7/2017/a#snap_regular_month_allotment` because
ECPS does not include application-date facts for initial-month proration.

CI runs a 20-record positive-benefit smoke comparison on pushes and pull
requests. The full New York ECPS comparison runs weekly and can be started
manually from the `PolicyEngine Oracle` GitHub Actions workflow with `full_run`
enabled. The full population run uses a 95 percent match-rate gate because
current PolicyEngine's NY BBCE parameters document unimplemented dependent-care
and earned-income asset conditions, so exact all-row parity would force Axiom
to copy an upstream oracle gap.
