# NSF PAPPG 24-1 duplicate/substantially-similar proposal review report

## Decision

**REJECT run `3ca97e28`. Do not retain or promote its candidate as policy output.**

The unchanged, authorized `axiom-encode encode --apply` invocation completed generation but failed deterministic CI validation before apply or signing. Its recorded outcome is:

- `apply_requested=true`
- `apply_success=false`
- `applied_files=[]`
- `final_success=false`
- `overlay_validation_success=false`
- `standalone_validation_success=false`
- `status=apply_blocked_validation`

The fatal error is:

> Upstream source check must include higher authority: `module.source_verification.upstream_source_check.checked_paths` must include at least one statute/regulation corpus path or RuleSpec target.

The only authorized legal source is the NSF guidance record `us/guidance/nsf/pappg/24-1/chapter-i/submission-instructions`. The generated candidate truthfully lists only that guidance record. Satisfying the gate would require adding an unapproved statute, regulation, or RuleSpec target, so no generated artifact was repaired and no checked path was fabricated.

The candidate's proof, generated expected-outcome fixtures, compilation, and direct-Rust behavior all pass in an isolated canonical overlay. Those results confirm that the narrow adapter behaves as requested; they do not cure the fatal source-authority gate or produce a signed manifest. No live generated policy artifact exists.

## Worktree and custody result

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-pappg-24-1-duplicate-review-20260830-codex-195000`
- Live upstream base: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Base tree: `20a8f964f20b4a4bfdedc239245c5d1dbafe3f29`
- Local `origin/main`: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Detached ledger HEAD: `d920d27abe81712f63d724924a54b6e39a09fdbc`
- Base-to-HEAD paths before this report update: only `PROGRESS.md` and `OUTPUT.md`
- Policy-tree diff before this report update: empty
- Fresh isolated run root: `/Users/maxghenis/.axiom-runs/nsf-pappg-duplicate-review.DdJG0Z`

The following live paths are absent:

- `us/policies/nsf/pappg/24-1/chapter-i/submission-instructions.yaml`
- `us/policies/nsf/pappg/24-1/chapter-i/submission-instructions.test.yaml`
- `us/.axiom/encoding-manifests/policies/nsf/pappg/24-1/chapter-i/submission-instructions.json`

Apply stopped before any policy-tree copy, so there was nothing to remove or restore. The isolated run-root candidate, companion test, trace, repair manifest, compiled artifact, and adversary evidence are retained only as diagnostic custody records. PR #631, accepted work, existing NSF policy files, and other worktrees were not modified.

## Authorized source

- Corpus worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830`
- Corpus HEAD: `129dae01c6f7a4787bc7678d4a97a478f3934d9f`
- Corpus tree: `acc919b84ab1854c7b227e6578529a0b2dd7a3f4`
- Corpus status at custody checks: clean
- Sole citation path: `us/guidance/nsf/pappg/24-1/chapter-i/submission-instructions`
- Record ID: `0a724ccd-9b2b-534c-9bcc-ed391d2511bf`
- Citation label: `PAPPG 24-1 Chapter I: Pre-Submission Information 1`
- Heading: `Chapter I.G.1 Submission Instructions`
- Expression/effective date: `2024-05-20`
- Source as of: `2026-08-30`
- Official URL: `https://www.nsf.gov/policies/pappg/24-1/ch-1-pre-submission`

Source custody SHA-256 values:

- Exact official provision body, UTF-8 without trailing newline: `3e1a117c4a09679284ee79b0fae5b1f619af6e4cb4c6e6415e16e87a88e8804f`
- Raw authorized JSONL record including newline: `0fc72c05862d6b70c64e3e26b36d2f550949c113efa9ca81a6e8fdf3264bb774`
- Normalized compact record plus newline: `d47e8abb046267894614c392312db4299a29d4537283c33b110533f3d7fef69d`
- Encoder-normalized original `source.txt` bytes: `987275bb6a2723b46698464c61229364955994f549ae733461a794c7865e70fc`
- Raw official HTML: `a8f98d21d424ab919458571a268b50c77f7c42164fecfb4bdbe3a94c64197d29`
- Corpus provisions JSONL: `a16f78fee0769493e9ba11d4e7c154b84536158fb6091cef8721b8f8fc482a89`
- Corpus inventory: `5b5433685a24e613c69375c376cc4dabb1efa5faa48e036a410d0948931f82c7`
- Corpus manifest: `86846900f5b137e1e5392f2cc464fd569114a3484258abe7ec00ba7af982538e`

The authorized primary-source continuation contains exactly the same citation, the exact metadata line `expression_date: 2024-05-20`, and the exact audited official body. The full continuation file hashes to `d756536fc5889bae63abe651bacd7cce6c20b457e92d69e8a9b46611dd6dd56e`; its body alone reproduces `3e1a117c4a09679284ee79b0fae5b1f619af6e4cb4c6e6415e16e87a88e8804f`. It supplied missing same-record metadata to generation and was not used for manual artifact repair.

The separate adapter scope brief is explicitly non-authoritative and hashes to `ec32063b768542747e883b46c2c26ce5b3be6113622b9b3a8fb3db45d603055a`. It constrained the requested output surface; it is not cited by any proof atom.

## Toolchain custody

### axiom-encode

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode`
- HEAD: `3869d66d009f52258be35901edbef370e65a399c`
- Tree: `d2ce31c8073b4bc0b4b169b9273f394650094230`
- Version: `0.2.1200`
- `uv.lock` SHA-256: `ff0ea7983fe344be90ab54b388b0c4c441a1ac69ecf73937440d12802d92d5fc`
- Status at custody checks: clean

### axiom-rules-engine

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine`
- HEAD: `ffd8213271947b0189a9dd61a055c1e0e78908a0`
- Tree: `86e78cc74fffe774fe0ba010c0a951ca1dfcc000`
- `Cargo.lock` SHA-256: `56f01fb4b5118a479328fbffd55b93635ed11038de60bcdd206b88aad84d16cb`
- Existing debug binary SHA-256: `ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb`
- Fresh isolated release binary SHA-256: `674ca6e70afdccb59c3d6847933bc24b4590105e49db54790f2dcd0bdbbe32d7`
- Status at custody checks: clean

## Encoder invocation and run record

The process-supplied `AXIOM_ENCODE_APPLY_SIGNING_KEY` was inherited only by this unchanged apply command. It was never placed on the command line, read back, printed, logged, hashed, or rotated. Every later validation, build, compile, guard, and runtime command used `env -u AXIOM_ENCODE_APPLY_SIGNING_KEY`.

```bash
uv run --frozen axiom-encode encode \
  'us/guidance/nsf/pappg/24-1/chapter-i/submission-instructions' \
  --output '/Users/maxghenis/.axiom-runs/nsf-pappg-duplicate-review.DdJG0Z/encode' \
  --backend codex \
  --model gpt-5.5 \
  --corpus-path '/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830' \
  --axiom-rules-engine-path '/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine' \
  --policy-repo-path '/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-pappg-24-1-duplicate-review-20260830-codex-195000/us' \
  --mode repo-augmented \
  --allow-context '/Users/maxghenis/.axiom-runs/nsf-pappg-duplicate-review.DdJG0Z/same-record-primary-source-continuation.txt' \
  --allow-context '/Users/maxghenis/.axiom-runs/nsf-pappg-duplicate-review.DdJG0Z/nsf-duplicate-review-adapter-scope.md' \
  --db '/Users/maxghenis/.axiom-runs/nsf-pappg-duplicate-review.DdJG0Z/encodings.db' \
  --no-sync \
  --apply
```

Run metadata:

- Run ID: `3ca97e28`
- Session ID: `encode-3ca97e28`
- Backend/model: `codex` / `gpt-5.5`
- DB timestamp: `2026-08-30T20:58:39.624367`
- Session interval: `2026-08-30T20:58:40.077506` to `2026-08-30T21:02:44.485659`
- Recorded encoding duration: `182891` ms
- Tokens: `96427` total; `89829` input; `6598` output; `44800` cache-read; `0` cache-creation
- Session DB events: 4 (`encode_request`, `encode_result`, `encode_issue`, `encode_outcome`)
- Trace events: 12
- Repair manifest creation: `2026-08-31T01:02:44+00:00`
- Primary error: `Generated RuleSpec failed CI validation`

The trace's only command executions are four read-only `sed` reads of `source-metadata.json`, `source.txt`, the same-record continuation, and the non-authoritative scope brief. It contains no repository search, second legal source, output edit, or signing-key access.

## Context, trace, output, and run hashes

- Encoding DB: `c0416bb9d2b7a1d0ae240e3e5b09dc2a6953e83ca969e7c3c36cf8c554cf05eb`
- Context manifest: `ee5a84e6fd051958997f18408d4ce4da1e9ffedc6e58db8536a95d2024063815`
- Source metadata: `861e7a812e5cb44e70ed195144ee14670d925cbf497f0f07789a66002cdbf335`
- Merged workspace `source.txt`: `306c7dc44856233bc197424ac6a7bf99367ea5ab0e852a58633a39a070713b3e`
- Hydrated continuation: `d756536fc5889bae63abe651bacd7cce6c20b457e92d69e8a9b46611dd6dd56e`
- Hydrated scope brief: `ec32063b768542747e883b46c2c26ce5b3be6113622b9b3a8fb3db45d603055a`
- Trace: `d61ab316e265ea2b878027355ae9eefb8f1c94bdca990ed183817e5d043563b3`
- Model final-message capture: `873f5044013f06d24b9fd1bd48ed6c1a94c65798648cad9bd41db96140c709a8`
- Isolated candidate RuleSpec: `7e5cd93e5a69c2bbf61aee1bed3022edc8cd273cd2c2ac487c5105b694917afc`
- Isolated generated companion test: `ed582ca5b8d9b93ce2a3d2f37788755bdb0648cac655731e6a63cb8d4394907c`
- Repair manifest: `4f7972d4676d17abf8be49182085318cbbe5f51fabddf886d1632dec30aef9cd`
- Diagnostic-overlay RuleSpec: `7e5cd93e5a69c2bbf61aee1bed3022edc8cd273cd2c2ac487c5105b694917afc`
- Diagnostic-overlay test: `ed582ca5b8d9b93ce2a3d2f37788755bdb0648cac655731e6a63cb8d4394907c`

The overlay copies are byte-identical to the untouched encoder outputs. The overlay exists only to provide the canonical `rulespec-us/us/...` namespace context required by the validator and Rust compiler; neither generated YAML file was edited.

## Candidate surface

The isolated candidate contains exactly one public derived rule:

- ID: `us:policies/nsf/pappg/24-1/chapter-i/submission-instructions#review_required`
- Entity: `ProposalPair`
- Type: `Judgment`
- Period: `Day`
- Relations: none
- Versions: pre-effective `false` from `0001-01-01`; operative formula from `2024-05-20`

Its nine explicit input facts are:

1. `identified_compared_proposal_pair`
2. `submitting_organization_or_person_associated_with_compared_pair`
3. `compared_pair_involves_same_or_related_work`
4. `concurrently_submitted_for_review_by_more_than_one_program`
5. `compared_pair_is_only_previous_submission`
6. `compared_item_is_one_proposal_with_multiple_program_designations`
7. `evidence_compared_pair_may_be_duplicate`
8. `completed_human_review_of_compared_pair`
9. `human_review_assessed_compared_pair_substantially_similar`

The operative branch requires the identified pair, submitter association, same/related-work linkage, concurrency, neither previous-only nor one-proposal/multiple-designations, and then either duplicate evidence or both a completed external human review and its externally supplied substantially-similar assessment.

No rule or relation produces a duplicate conclusion, substantially-similar conclusion, automated rejection/return, misconduct or fraud finding, similarity score, applicant duty, AOR certification result, funding result, or discretionary NSF action.

## Generated fixtures, proof, and validation

All checks below used the byte-identical canonical-overlay candidate and explicitly removed the signing variable from their child environments.

### Proof

```bash
AXIOM_RULESPEC_REPO_ROOTS='<run-root>/diagnostic-overlay/rulespec-us' \
  uv run --frozen axiom-encode proof-validate --json \
  '<run-root>/diagnostic-overlay/rulespec-us/us/policies/nsf/pappg/24-1/chapter-i/submission-instructions.yaml'
```

Result: exit `0`; `passed=true`; proof required; 3 atoms checked; 0 issues. Result JSON SHA-256: `1529aa7d4559c7a7be54adcafb724727af78113a1ab90a2956776d4a7f7bbd12`.

### Expected-outcome/oracle fixtures

```bash
AXIOM_RULESPEC_REPO_ROOTS='<run-root>/diagnostic-overlay/rulespec-us' \
  uv run --frozen axiom-encode test \
  --root '<run-root>/diagnostic-overlay/rulespec-us' \
  --axiom-rules-engine-path '/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine' \
  --json \
  '<run-root>/diagnostic-overlay/rulespec-us/us/policies/nsf/pappg/24-1/chapter-i/submission-instructions.test.yaml'
```

Result: exit `0`; success; 1 test file; 10 cases; 1 compiled program; 0 failures. Result JSON SHA-256: `977eee74b9bb2da874ed551e287a9916047dab4188f95ab729fe14f47d03e3a4`.

The 10 generated states are:

- `holds`: duplicate-evidence route; completed-human-review substantially-similar route.
- `not_holds`: neither evidence route; unrelated proposal pair; explicit missing/false identified pair; explicit missing/false submitter; incomplete human-review route; previous-submission-only; one proposal with multiple program designations; `2024-05-19` pre-effective sentinel.

These procedural expected outcomes and the independent direct-Rust cases are the applicable oracle fixtures. No PolicyEngine or Taxsim oracle maps to an NSF proposal-review workflow, and none was substituted for the real Axiom runtime.

### Deterministic validation

```bash
AXIOM_RULESPEC_REPO_ROOTS='<run-root>/diagnostic-overlay/rulespec-us' \
  uv run --frozen axiom-encode validate --skip-reviewers --json \
  '<run-root>/diagnostic-overlay/rulespec-us/us/policies/nsf/pappg/24-1/chapter-i/submission-instructions.yaml'
```

Result: exit `1`; RuleSpec compilation succeeds; `ci_pass=false`; the only reported error is the higher-authority checked-path requirement quoted in the decision. Result JSON SHA-256: `bb1f1ed2a9ae414fd93adf6cde0d40c57a6725a73dc4e48f7e39fa1a0a6fba20`.

Encoder reviewer states recorded in the run DB:

- RuleSpec reviewer: pass, 10/10 items.
- Formula reviewer: fail, 0/10 items, one critical issue—the same higher-authority gate.
- Parameter reviewer: pass, 10/10 items.
- Integration reviewer: fail, 4/10 items. Its important findings primarily ask for the source's return/rejection consequence and object to the deliberately external evidence/review boundary. Those requests conflict with the approved narrow `review_required` adapter scope; they were not resolved by expanding the output. This reviewer failure independently reinforces rejection, although the deterministic source gate is already dispositive.

No signed apply manifest exists, so signature verification is not claimable.

## Pinned real-Rust build and compile

The isolated release binary was built from the pinned engine with the lockfile, offline, and in the fresh run root:

```bash
env -u AXIOM_ENCODE_APPLY_SIGNING_KEY \
  CARGO_TARGET_DIR='<run-root>/rust-diagnostic/cargo-target' \
  cargo build \
  --manifest-path '/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine/Cargo.toml' \
  --locked --offline --release --bin axiom-rules-engine
```

Result: exit `0`. Release binary SHA-256: `674ca6e70afdccb59c3d6847933bc24b4590105e49db54790f2dcd0bdbbe32d7`.

The byte-identical overlay candidate was then compiled by that binary:

```bash
env -u AXIOM_ENCODE_APPLY_SIGNING_KEY \
  AXIOM_RULESPEC_REPO_ROOTS='<run-root>/diagnostic-overlay/rulespec-us' \
  '<run-root>/rust-diagnostic/cargo-target/release/axiom-rules-engine' compile \
  --program '<run-root>/diagnostic-overlay/rulespec-us/us/policies/nsf/pappg/24-1/chapter-i/submission-instructions.yaml' \
  --output '<run-root>/rust-diagnostic/submission-instructions.compiled.json'
```

Result: exit `0`; artifact format 2; engine `0.1.0`; 1 derived output; evaluation order `review_required`; fast-path compatible using `generic_bulk`. Compiled artifact SHA-256: `4ea5dcf9a3ec2567be4d16a319e5702b110d1bcac4b94038d4050c9b0227d428`.

Rust command-log hashes:

- Build stderr/result: `ff4586920875394843a19859650123dfec823013251726f928ad8987c878e0fd`
- Compile stdout/result: `eecfbe059537bd60e218a4d8eb55cc9e57a6d78bef8e977e4b6a317c057156c4`
- Exit-status ledger: `77e6e9f99af2eb3cceae38e8ebca7aade32524e1554e94cc9dd38521e18c41a6`

## Direct-Rust adversaries

Every direct case invoked the fresh pinned release binary with `run-compiled --artifact`, a complete JSON dataset/query, and the public legal RuleSpec IDs. The harness merely assembles fixtures and asserts responses; all policy evaluation occurs in the real Rust runtime.

All 20 cases passed:

- 7 outcome cases:
  - same/related identified proposal pair with duplicate evidence: `holds`
  - externally completed human review with supplied substantially-similar fact: `holds`
  - neither evidence route: `not_holds`
  - unrelated proposal pair: `not_holds`
  - previous-submission-only/nonconcurrent pair: `not_holds`
  - one proposal with multiple program designations: `not_holds`
  - wholly pre-effective interval `2024-05-18..2024-05-19`: `not_holds`
- 5 literal input-omission cases correctly fail with `missing input`:
  - compared proposal pair
  - submitting organization/person linkage
  - same/related-work linkage
  - completed human review
  - externally supplied human-review assessment
- 8 prohibited output queries correctly fail with `unknown derived`:
  - `automated_rejection`
  - `rejection_required`
  - `duplicate_finding`
  - `substantially_similar_finding`
  - `misconduct_finding`
  - `similarity_score`
  - `applicant_duty_required`
  - `nsf_discretionary_action`

Direct-Rust custody SHA-256 values:

- Harness: `f7ac131ef8ba5f6a96e3b653de5e08186e0b09c4eb77b2e7bff70bd5b54662dd`
- Results TSV: `78fa4450472da1acc1e24ec1ef4df2ccac4d69d2ea4b4cb566aaacb89c5cfd1b`
- Per-file request/response/stderr custody list: `009270bfabf49830fc0460328f178627032110b61cb2d4cd8c2ee81b94a7b458`
- Custody-list entries: 60, covering each of 20 requests, responses, and stderr files

## Generated-file guard and final custody

Command:

```bash
env -u AXIOM_ENCODE_APPLY_SIGNING_KEY \
  uv run --frozen axiom-encode guard-generated \
  --repo '/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-pappg-24-1-duplicate-review-20260830-codex-195000' \
  --head-ref HEAD \
  --roots us \
  --json
```

Result: exit `0`; `passed=true`; no issues. Result JSON SHA-256: `4e1e6528f985b94bac9e17573e1fc032c2f8d86ea9662b822494e1632d3dc2a0`.

Final disposition:

- No signed output or signed manifest retained.
- No generated RuleSpec, test, or manifest retained in the policy tree.
- No manual repair of generated YAML.
- No unapproved legal source or checked path introduced.
- No automated rejection, legal finding, misconduct result, similarity score, applicant duty, or discretionary NSF outcome exposed.
- No commit, push, branch change, PR, deployment, or publication.
- PR #631 and accepted work untouched.

Acceptance would require an Axiom encoder/validator capability that can authorize this single-guidance-source adapter without fabricating a qualifying higher-authority path, or a new explicit source authorization. Neither is available within this lane, so rejection is final for this run.
