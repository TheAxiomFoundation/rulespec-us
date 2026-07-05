# Progress

## State

Encoding Social Security Title II benefit formulas from `ENCODE_BRIEF.md` on branch `ss-title-ii-benefit-formulas`.

## Done

- Read required exemplars:
  - `us/statutes/42/1382/a/1.yaml`
  - `us/statutes/42/1382/a/1.test.yaml`
  - `us/statutes/26/1/h.yaml`
  - `us/policies/ssa/pia-bend-points/2026.yaml`
- Section 1: encoded `us/statutes/42/415/b.yaml` and companion test for AIME, old-age elapsed years/dropout years, highest-year selection, indexing, and whole-dollar AIME rounding.
- Section 2: encoded `us/statutes/42/415/a.yaml` and companion test for the 90% / 32% / 15% PIA formula using the existing 2026 bend points.
- Section 3: encoded `us/statutes/42/415/i.yaml`, added `us/policies/ssa/cola/2026.yaml`, and tested 2.8% COLA application with dime rounding.

## Next

- Section 4: encode `us/statutes/42/416/l.yaml` for the retirement age schedule by early-retirement-age year.

## Open Questions

- `git fetch`, push, and PR creation against GitHub are blocked in this environment by DNS resolution for `github.com`; local section commits are being made through a temporary writable gitdir.
