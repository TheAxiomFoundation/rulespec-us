# Progress

## State

- Active: isolated detached `rulespec-us` encoding worktree.
- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-42-19232-e-nonretroactivity-20260830-codex-01`
- Base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f` (`origin/main` as locally resolved).
- Scope: only the 42 U.S.C. § 19232(e) nonretroactivity limitation required by MFTRP certification modules.
- Acceptance posture: retain only unchanged signed encoder output that passes source, proof, generated-fixture, and direct Rust validation; otherwise restore clean.
- Required safe output: a positive limitation judgment such as `subsection_a_certification_is_nonretroactively_inapplicable`; do not decide the underlying subsection (a) certification obligation.
- Required case facts: external identifiers for the evaluated Federal research agency and the actual policy-establishing Federal research agency, whether that policy was actually established, its actual establishment date, and availability of that date. Compare the agency identifiers in the formula; do not replace identity with an assumed universal agency or universal policy date.
- Required logic: after actual-establishment, date-availability, same-agency, and R&D-scope guards, preserve the OR between `(application stage AND application submission date < policy establishment date)` and `(award stage AND award-made date < policy establishment date)`.
- Required temporal versions: an exact neutral `false` sentinel from `0001-01-01`, followed by the operative formula at `2022-08-09`; never backdate the operative formula, start the sentinel only one day before enactment, or drop either version. The pre-enactment fixture must exercise `2022-08-08`.
- Required generated fixtures and direct Rust states: policy date minus/equal/plus one day, application-before, award-before, neither-before, different-agency policy, unavailable/missing establishment date, non-R&D scope, and pre-enactment.

## Done

- Read the Axiom encoder, rules-engine, and `rulespec-us` project instructions.
- Attempted `git fetch origin main`; it failed because this environment could not resolve `github.com`.
- Verified the existing local `origin/main` and detached worktree HEAD both equal the required immutable commit `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`.
- Created and verified a clean, unique detached worktree; no accepted worktree was edited.
- Located the official source file in the designated corpus worktree: `data/corpus/provisions/us/statute/2026-08-30-proposal-security-title-42.jsonl` at corpus commit `129dae01c6f7a4787bc7678d4a97a478f3934d9f`.
- Verified § 19232(e) at `us/statute/42/19232/e`: body SHA-256 `16e0b4bbf48ef9bc1621dff32d3084f3b7b3b7498f8063e305b654efeee81fb6`; canonical JSONL record SHA-256 `7baff4dbf398a587db4a833bdc8c191fef7c49098a13ef3d3349d1e722596be4`.
- Verified inherited § 19232(a) at `us/statute/42/19232/a`: body SHA-256 `ea3241a54755a3f0669c8d7bf16150900d1a4b1f8f2bd5ddf03f6e74d65487a8`; canonical JSONL record SHA-256 `715a8cd0f5effd7978d76c6f1c62592fd3355b80fb67a555cc3f4fb85353c92a`.
- Verified the full source JSONL SHA-256 `566a513343f88d5a4944c591ef86464dcd27ea8dce8a4dd730f05efec4f69aa4`.
- Inspected the unchanged signed § 19232(f) sibling at commit `94160652eb3d4a148d3c632677da8c42818853fa`; it confirms canonical `us/` placement and a two-version false/operative pattern. This task tightens the sentinel to `0001-01-01` so dates earlier than 2022-08-08 do not lose the rule version.
- Rejected the prior unaccepted § 19232(e) attempt in `rulespec-us-19232-base-20260830`: it wrote to singular `statutes/`, encoded the complement (`not_barred`), replaced actual date comparisons with booleans, and began its false sentinel only on 2022-08-08.
- Verified a canonical accepted formula pattern at `us-co/statutes/39/39-22-111.yaml` for comparing two external Text identifiers directly; the generated § 19232(e) formula must use this pattern for same-agency identity.
- Materialized the inherited § 19232(a) body as an untracked encoder-only primary-source continuation at `.axiom/encoding-context/42-19232-a-primary-source.txt`; its parsed continuation body exactly matches the official body SHA-256 `ea3241a54755a3f0669c8d7bf16150900d1a4b1f8f2bd5ddf03f6e74d65487a8`. It will not be retained as a source payload.
- Queried `agent-secret` for the required apply credential. The helper is present, but its login-keychain unlock-password record is currently unavailable; encoding and unsigned validation can proceed while signed apply remains pending.

## Next

- Inspect accepted RuleSpec patterns and the exact encoder/apply/proof/Rust workflow.
- Run actual `axiom-encode` with this progress/acceptance record as context, inspect generated-only candidates, and apply only with the signing key supplied through `agent-secret`.
- Validate source hashes, exact temporal false sentinel, proof, generated fixtures, and direct Rust outcomes at all required boundary and negative cases.
- Maintain this file after each coherent step and write the final committed report to `FINAL_REPORT.md`.
