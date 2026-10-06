# 42 U.S.C. § 6605(a) disclosure spine progress

## State

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-6605-disclosure-spine-codex-20260830-a10f`
- Detached base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Scope: atomic attempts for § 6605(a)(1)(A), (a)(1)(B), (a)(1)(C), and (a)(2).
- Candidate custody: only unmodified signed `axiom-encode apply` output may be retained. This progress file is not a candidate artifact.
- Configured final report: `/Users/maxghenis/.codex/tmp/axiom-proposal-security-subfleet-20260830/fps6605-report.md`.
- Status: resumed and re-audited; no child attempted because the required signing key remains unavailable through the mandated secret path.

## Done

- Verified the detached worktree is clean at the pinned base SHA.
- Located the official USC corpus records and the user-designated encoder and Rust runtime checkouts.
- Pinned official corpus checkout `129dae01c6f7a4787bc7678d4a97a478f3934d9f` and normalized provision file `data/corpus/provisions/us/statute/2026-08-30-proposal-security-title-42.jsonl` (`566a513343f88d5a4944c591ef86464dcd27ea8dce8a4dd730f05efec4f69aa4`).
- Pinned official OLRC archive `data/corpus/sources/us/statute/2026-08-30-proposal-security-title-42/olrc/xml_usc42@119-102.zip` (`31929c28f117362ac8788607242795769b05ed7726f07e4ed3b1786f39655ce7`).
- Recorded exact record hashes for the inherited chapeau and children: (a) `f393aeb80be62f542feb33dd013833f8e7a86a122245aab46c2d99446365e1c2`; (a)(1) `337ec5b8835b6bd10f891eec9ff9ff2c9383316a40452dcd1d026433d86539aa`; (A) `01b103a71ccc08f80284d833cea6b3c07073b69710a9e6a7b981b266043a34a6`; (B) `1a075258cc7cec2b132994c74a285c940fa0a6afff8447ffade1996e19cbc837`; (C) `ca48060f1e4d67db1b2e796e01119d780fe27c9a2fd1fb364bc6b32bacba4ffd`; (2) `a9c35d620656fc0a9859619b311395bff76b915f7ccc5fb3683b67871ce87005`.
- Pinned `axiom-encode` version `0.2.1200` at `3869d66d009f52258be35901edbef370e65a399c` and the real Rust runtime version `0.1.0` at `ffd8213271947b0189a9dd61a055c1e0e78908a0`; both designated checkouts are detached and clean.
- Confirmed the required apply-key environment variable is absent. `agent-secret search` and `agent-secret unlock` currently fail before secret lookup because the dedicated keychain's stored unlock password is unavailable to this shell. No substitute key has been used.
- Reconfirmed before this evidence-only edit that the worktree was clean and detached at `dbd40e6b57d2db2d5f6f51e0d8802ec4234a9b49`, whose merge base with the live upstream is exactly `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`; the two commits above that base contain progress evidence only.
- Recovered the original launcher brief from `/Users/maxghenis/.codex/tmp/axiom-proposal-security-subfleet-20260830/6605.md` and the current no-commit resume order from `fast-resume-6605.md`.
- Located the exact designated tool checkouts at `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode` and `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine`.
- Audited the retained `usc42.xml` inside the pinned OLRC archive. Its § 6605 source credit is `Pub. L. 116–283, div. A, title II, § 223, Jan. 1, 2021, 134 Stat. 3470`; the only following note is a codification note and there is no separate effective-date note, amendment history, delayed date, or sunset. The legal start used for an attempted encoding must therefore be `2021-01-01`, with an otherwise-positive `2020-12-31` false sentinel. The normalized `2026-07-12` expression/source-as-of date is custody metadata, not the legal start.
- Confirmed that the pinned encoder resolves an exact child citation to the child body only. Faithful attempts must supply exact official continuation context for the inherited § 6605(a) and § 6605(a)(1) chapeaux (and relevant definitions) through the encoder-supported `Primary source continuation` mechanism; manually splicing or repairing generated YAML remains forbidden.
- Retried `agent-secret search axiom-encode` and the required exact `agent-secret get agent/axiom-encode-apply-signing-key axiom-foundation` command. Both fail before lookup with `agent-secret: missing unlock password. Run: agent-secret init`. Inspection of the helper confirms that `init` refuses to replace an existing keychain whose login-keychain unlock-password record is missing, so it was not run. No direct Keychain fallback or substitute signing key was used.

## Next

- Restore access to `agent/axiom-encode-apply-signing-key` (`axiom-foundation`) through `agent-secret`, or provision `AXIOM_ENCODE_APPLY_SIGNING_KEY` in the authorized task environment, before the first apply.
- Attempt each child independently with `axiom-encode encode --apply` from the canonical `us/` policy root, exact official continuation context, and no manual output edits. Do not use `--apply-target-only` or `--skip-reviewers`. Require distinct agency-duty and individual/entity-duty outputs, the same-agency actual-requirement gate, same-person/application/disclosure/organization linkage, and the `2020-12-31` false sentinel.
- For each signed result, audit the generated YAML/test/manifest bytes and hashes; run strict proof validation, all generated companion fixtures through the pinned Rust engine, and direct compiled-runtime positive, missing-gate, actor/linkage, and pre-effective cases. Reject and remove an entire atomic apply set if semantics, proof, or runtime behavior is unfaithful.
- Replace the stale configured report with the complete custody/run/acceptance report only after the four independent dispositions are final. Do not commit, push, open a PR, deploy, or publish.
