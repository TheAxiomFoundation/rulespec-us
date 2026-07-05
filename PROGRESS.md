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

## Next

- Section 2: encode `us/statutes/42/415/a.yaml` for the 90% / 32% / 15% PIA formula using the existing 2026 PIA bend-point parameters.

## Open Questions

- `git fetch`, push, and PR creation against GitHub are blocked in this environment by DNS resolution for `github.com`; local section commits are being made through a temporary writable gitdir.
