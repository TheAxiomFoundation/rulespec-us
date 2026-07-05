# Progress

## State

Encoding Social Security Title II benefit formulas from `ENCODE_BRIEF.md` on branch `ss-title-ii-benefit-formulas` is complete locally. GitHub publication is blocked by network connectivity in this environment.

## Done

- Read required exemplars:
  - `us/statutes/42/1382/a/1.yaml`
  - `us/statutes/42/1382/a/1.test.yaml`
  - `us/statutes/26/1/h.yaml`
  - `us/policies/ssa/pia-bend-points/2026.yaml`
- Section 1: encoded `us/statutes/42/415/b.yaml` and companion test for AIME, old-age elapsed years/dropout years, highest-year selection, indexing, and whole-dollar AIME rounding.
- Section 2: encoded `us/statutes/42/415/a.yaml` and companion test for the 90% / 32% / 15% PIA formula using the existing 2026 bend points.
- Section 3: encoded `us/statutes/42/415/i.yaml`, added `us/policies/ssa/cola/2026.yaml`, and tested 2.8% COLA application with dime rounding.
- Section 4: encoded `us/statutes/42/416/l.yaml` and companion test for the retirement age schedule from age 65 to 67.
- Section 5: encoded `us/statutes/42/402/q.yaml` and companion test for old-age early claiming reductions, including the 36-month tier break and dime rounding up.
- Section 6: encoded `us/statutes/42/402/w.yaml` and companion test for delayed retirement credits through age 70.
- Final validation: regenerated the reverse index and ran `/opt/homebrew/bin/pytest tests` successfully before each section commit.

## Next

- Push `ss-title-ii-benefit-formulas` and create the draft PR once GitHub connectivity is available.

## Open Questions

- `git fetch`, push, and PR creation against GitHub are blocked in this environment. Push attempts failed with `Could not resolve host: github.com`; the draft PR attempt failed with `error connecting to api.github.com`.
- Local section commits were made through a temporary writable gitdir at `/private/tmp/rulespec-us-ss415-git.nKKfSk` because the worktree's parent gitdir is outside the writable sandbox.
