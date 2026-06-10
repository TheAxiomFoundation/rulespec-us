# rulespec-us-co

Colorado RuleSpec encodings.

## Contents

- `statutes/`, `regulations/`, or `policies/`: RuleSpec YAML when encoded rules are added.
- `.github/workflows/`: wrapper around the shared RuleSpec validation workflow.

## Conventions

Use RuleSpec YAML under `statutes/`, `regulations/`, or `policies/` for encoded rules. Do not add source text, source registry sidecars, generated source payloads, extracted document snapshots, or wave manifests to Git; source material belongs in the corpus database/object storage.

Jurisdiction-specific materials belong in this repo. Shared federal materials belong in `rulespec-us`.

## PolicyEngine ECPS SNAP Comparison

Compare the Colorado SNAP composition against PolicyEngine ECPS (enhanced CPS) records
with the shared `axiom-encode` oracle command:

```bash
uv run --project ../axiom-encode --with policyengine-us --with numpy \
  axiom-encode snap-ecps-compare \
  --jurisdiction us-co \
  --utility-projection policyengine-type \
  --tolerance 5
```

The comparison uses PolicyEngine's `snap_normal_allotment`, not top-level `snap`,
because microsimulation `snap` includes take-up adjustments. It compares against
RuleSpec `us:statutes/7/2017/a#snap_regular_month_allotment` because ECPS does
not include application-date facts for initial-month proration.

For ECPS parity, `--utility-projection policyengine-type` maps PE's utility
allowance type into the closest Colorado utility facts. This is the oracle mode
for matching PolicyEngine's ECPS SNAP results because ECPS does not reliably
expose the itemized utility facts needed to infer the same allowance. The
default `--utility-projection raw-expenses` mode projects itemized utility
expenses directly and is useful as a diagnostic; current mismatches in that mode
are utility-fact projection gaps, not formula mismatches.

The comparison projects PE's elderly-or-disabled SNAP status onto a related
member fact, and the RuleSpec derives the household-level status through
`member_of_household`. The live RuleSpec computation still derives utility,
medical, child support, dependent care, shelter, eligibility, and allotment
values from the encoded rules.

CI runs a 20-record positive-benefit smoke comparison on pushes and pull
requests. The full Colorado ECPS comparison runs weekly and can be started
manually from the `PolicyEngine Oracle` GitHub Actions workflow with
`full_run` enabled. CI uses a `$5` tolerance because current PolicyEngine data
still returns Colorado HCUA as `$578`, while the encoded current source sets it
at `$594`; the maximum benefit effect is about `$4.80`.
