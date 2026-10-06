# Progress

## State

- Final decision: **REJECT** run `3ca97e28` / session `encode-3ca97e28`.
- The process-supplied signing key was used only by the unchanged `axiom-encode encode --apply` invocation. The key was not printed, logged, hashed, inspected, or rotated; every later diagnostic command explicitly removed it from the child environment.
- The encoder generated an isolated candidate and companion test, but signed apply stopped at deterministic CI validation before copying or signing any policy artifact. The fatal error requires a statute/regulation corpus path or RuleSpec target in `upstream_source_check.checked_paths`; the sole authorized NSF guidance record cannot satisfy that gate without inventing another authority.
- Apply outcome: `apply_requested=true`, `apply_success=false`, `applied_files=[]`, `final_success=false`, `status=apply_blocked_validation`.
- No live rule, companion test, or NSF encoding manifest exists. The `us/` policy tree is unchanged, and `guard-generated` passes.
- Isolated proof, all 10 generated expected-outcome fixtures, the pinned release Rust compile, and all 20 direct-Rust adversaries passed. Those diagnostics establish the candidate's narrow behavior but cannot cure the source-authority/apply failure.
- Full report: `OUTPUT.md`.

## Completed run

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-pappg-24-1-duplicate-review-20260830-codex-195000`.
- Live upstream base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`; base tree: `20a8f964f20b4a4bfdedc239245c5d1dbafe3f29`; local `origin/main` still resolves to that exact base.
- Current detached ledger HEAD: `d920d27abe81712f63d724924a54b6e39a09fdbc`; the only base-to-HEAD files are `PROGRESS.md` and `OUTPUT.md`.
- Fresh isolated run root: `/Users/maxghenis/.axiom-runs/nsf-pappg-duplicate-review.DdJG0Z`.
- Sole official corpus record: `us/guidance/nsf/pappg/24-1/chapter-i/submission-instructions`.
- Same-record primary-source continuation supplied the authorized exact `expression_date: 2024-05-20` plus the already-audited exact official body. Its full-file SHA-256 is `d756536fc5889bae63abe651bacd7cce6c20b457e92d69e8a9b46611dd6dd56e`; the continuation body and corpus body both hash to `3e1a117c4a09679284ee79b0fae5b1f619af6e4cb4c6e6415e16e87a88e8804f` without a trailing newline.
- Non-authoritative adapter scope SHA-256: `ec32063b768542747e883b46c2c26ce5b3be6113622b9b3a8fb3db45d603055a`.
- Encoder: `3869d66d009f52258be35901edbef370e65a399c`, version `0.2.1200`.
- Rust engine: `ffd8213271947b0189a9dd61a055c1e0e78908a0`, release binary SHA-256 `674ca6e70afdccb59c3d6847933bc24b4590105e49db54790f2dcd0bdbbe32d7`.
- Generated isolated candidate SHA-256: `7e5cd93e5a69c2bbf61aee1bed3022edc8cd273cd2c2ac487c5105b694917afc`.
- Generated isolated test SHA-256: `ed582ca5b8d9b93ce2a3d2f37788755bdb0648cac655731e6a63cb8d4394907c`.
- Trace SHA-256: `d61ab316e265ea2b878027355ae9eefb8f1c94bdca990ed183817e5d043563b3`.
- Context-manifest SHA-256: `ee5a84e6fd051958997f18408d4ce4da1e9ffedc6e58db8536a95d2024063815`.
- Compiled artifact SHA-256: `4ea5dcf9a3ec2567be4d16a319e5702b110d1bcac4b94038d4050c9b0227d428`.
- Direct-Rust results SHA-256: `78fa4450472da1acc1e24ec1ef4df2ccac4d69d2ea4b4cb566aaacb89c5cfd1b`.

## Verification

- Candidate surface: exactly one public derived `Judgment`, `review_required`, on `ProposalPair`; nine explicit boolean facts; no relations; pre-effective false version from `0001-01-01`; operative version from `2024-05-20`.
- Proof: pass, 3 atoms, 0 issues.
- Generated expected-outcome fixtures: pass, 1 test file, 10 cases, 1 compiled program, 0 failures; 2 `holds` and 8 `not_holds`.
- Deterministic validation: compile succeeds, CI fails only the higher-authority checked-path gate.
- Pinned Rust: locked/offline release build pass; compile pass; artifact format 2, engine `0.1.0`, one derived output, fast-path compatible.
- Direct Rust: 20/20 pass—7 outcome cases, 5 required-input omission errors, and 8 forbidden-output unknown-rule errors. The wholly pre-effective `2024-05-18..2024-05-19` case returns `not_holds`.
- Generated-file guard: pass, no issues.
- Live paths absent:
  - `us/policies/nsf/pappg/24-1/chapter-i/submission-instructions.yaml`
  - `us/policies/nsf/pappg/24-1/chapter-i/submission-instructions.test.yaml`
  - `us/.axiom/encoding-manifests/policies/nsf/pappg/24-1/chapter-i/submission-instructions.json`

## Final limitation

No further in-scope action can produce acceptable signed output. The validator requires a qualifying higher-authority path while the approved source boundary permits only the one NSF guidance record. Manual edits to generated artifacts, a fabricated checked path, or an unapproved second authority would violate the instructions. PR #631 and all accepted work were left untouched; no commit, push, PR, deployment, or publication occurred.
