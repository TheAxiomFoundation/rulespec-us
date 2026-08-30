# 42 U.S.C. § 6605(a) disclosure spine progress

## State

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-6605-disclosure-spine-codex-20260830-a10f`
- Detached base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Scope: atomic attempts for § 6605(a)(1)(A), (a)(1)(B), (a)(1)(C), and (a)(2).
- Candidate custody: only unmodified signed `axiom-encode apply` output may be retained. This progress file is not a candidate artifact.
- Status: source and toolchain custody recorded; no child attempted yet.

## Done

- Verified the detached worktree is clean at the pinned base SHA.
- Located the official USC corpus records and the user-designated encoder and Rust runtime checkouts.
- Pinned official corpus checkout `129dae01c6f7a4787bc7678d4a97a478f3934d9f` and normalized provision file `data/corpus/provisions/us/statute/2026-08-30-proposal-security-title-42.jsonl` (`566a513343f88d5a4944c591ef86464dcd27ea8dce8a4dd730f05efec4f69aa4`).
- Pinned official OLRC archive `data/corpus/sources/us/statute/2026-08-30-proposal-security-title-42/olrc/xml_usc42@119-102.zip` (`31929c28f117362ac8788607242795769b05ed7726f07e4ed3b1786f39655ce7`).
- Recorded exact record hashes for the inherited chapeau and children: (a) `f393aeb80be62f542feb33dd013833f8e7a86a122245aab46c2d99446365e1c2`; (a)(1) `337ec5b8835b6bd10f891eec9ff9ff2c9383316a40452dcd1d026433d86539aa`; (A) `01b103a71ccc08f80284d833cea6b3c07073b69710a9e6a7b981b266043a34a6`; (B) `1a075258cc7cec2b132994c74a285c940fa0a6afff8447ffade1996e19cbc837`; (C) `ca48060f1e4d67db1b2e796e01119d780fe27c9a2fd1fb364bc6b32bacba4ffd`; (2) `a9c35d620656fc0a9859619b311395bff76b915f7ccc5fb3683b67871ce87005`.
- Pinned `axiom-encode` version `0.2.1200` at `3869d66d009f52258be35901edbef370e65a399c` and the real Rust runtime version `0.1.0` at `ffd8213271947b0189a9dd61a055c1e0e78908a0`; both designated checkouts are detached and clean.
- Confirmed the required apply-key environment variable is absent. `agent-secret search` and `agent-secret unlock` currently fail before secret lookup because the dedicated keychain's stored unlock password is unavailable to this shell. No substitute key has been used.

## Next

- Establish the exact signed-manifest, fixture, proof, and direct-Rust validation commands for this pinned toolchain.
- Retry the required `agent-secret get agent/axiom-encode-apply-signing-key axiom-foundation` path before the first apply.
- Attempt each child independently, validate proof and generated fixtures, run direct Rust cases, and accept or roll back at a clean checkpoint.
