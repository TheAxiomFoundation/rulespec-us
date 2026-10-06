# NSF IN-149 MFTRP certification adapter final report

## Result

**Executable result: rejected; no RuleSpec output retained.**

Three reviewed Codex gpt-5.5 encode --apply invocations with the same encode
arguments were made through the lane-pinned axiom-encode. Each invocation used
a fresh isolated output root, the canonical policy root ending in /us, the
positional IN-149 item 3 source, the unchanged encoding brief, and exactly the
six audited official-text continuations. Only telemetry placement differed:
the third invocation explicitly isolated its run log from process start. Each
model stream failed before returning any tokens or RuleSpec content. The
encoder exhausted its recorded reconnect cycles, recorded
apply_blocked_generation, and reported applied_files=[].

No invocation reached overlay validation, signing, installation, proof,
fixtures, or Rust execution. No generated main file, companion test, apply
manifest, or index mutation exists. Under the unchanged-signed, proven, and
runtime-faithful retention contract, every executable atomic output is
rejected. No unsigned, manually authored, manually repaired, manually
re-signed, mocked, or parallel evaluator was substituted.

## RuleSpec base and worktree custody

- Repository: /Users/maxghenis/TheAxiomFoundation/rulespec-us
- Worktree:
  /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-in149-mftrp-cert-adapter-20260830-codex-b7e4c1
- Worktree mode: detached HEAD; no branch was created or checked out.
- Lane HEAD before this uncommitted report update:
  5bd899c572dc473254579898309994d0cc6396c3
- Lane HEAD tree:
  49eee4fb2a56b50178a85e875c375dd0aa5ad642
- Required and user-confirmed live upstream base:
  d58cc0ce67ad891fde4c9061c86a2091bfdd524f
- Required base tree:
  20a8f964f20b4a4bfdedc239245c5d1dbafe3f29
- Merge base: exactly the required base.
- Local origin/main: exactly the required base.
- Lane relationship to base: zero commits behind and three preparation/report
  commits ahead.
- Preparation commits:
  d4133c5f85f3d965bbc5fb510a19a7cc94438e4f,
  a23e0a063dced7cbef24908e510a3c3312249c91, and
  5bd899c572dc473254579898309994d0cc6396c3.
- The current instruction explicitly confirmed that the live upstream base
  remains the required object. No fetch, rebase, merge, or base substitution
  was performed.
- Existing branches, other worktrees, accepted work, and axiom-corpus PR #631:
  unchanged.
- Commit, push, PR, deploy, publish, and production actions: none.

The lane was clean before the first encode invocation. Encoder 0.2.1200 wrote
the first two run logs under the process working directory by default. Those
two untracked logs were moved, without changing their bytes, into their
matching isolated output roots. The third invocation set
AXIOM_ENCODE_RUN_LOG_DIR to its isolated output root from the start. The lane
was clean again before this report and bulk/PROGRESS.md were updated.

## Official source custody

- Corpus worktree:
  /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/axiom-corpus-federal-proposal-security-20260830
- Corpus commit: 129dae01c6f7a4787bc7678d4a97a478f3934d9f
- Corpus tree: acc919b84ab1854c7b227e6578529a0b2dd7a3f4
- Source-introduction commit:
  e0564d63595bd4fdb043ee77134c94b3dc218ca8
- Provision bundle SHA-256:
  a16f78fee0769493e9ba11d4e7c154b84536158fb6091cef8721b8f8fc482a89
- Inventory SHA-256:
  5b5433685a24e613c69375c376cc4dabb1efa5faa48e036a410d0948931f82c7
- Coverage SHA-256:
  f31dbf081095cdbcf3230ebd810587ab11ecb7914f1babb96300aa4ad00b32a3
- Ingest manifest SHA-256:
  86846900f5b137e1e5392f2cc464fd569114a3484258abe7ec00ba7af982538e
- IN-149 HTML SHA-256:
  b80a6a59dbb102e3371b4eab6e90971562e91e551220c892533b2efb3da9cb8d
- FAQ HTML SHA-256:
  a80e70b6640477ae3f95cc9a54b394a03aac087d1d17e7ff6fb50c774f5fdf41

The seven authorized records all have expression_date 2025-11-24 and
source_as_of 2026-08-30. None has a corpus effective_start or effective_end.
The expression date was not treated as an operative effective date.

| Corpus citation path | Record ID | Exact body SHA-256 |
| --- | --- | --- |
| us/guidance/nsf/important-notice/149-research-security/3 | fbc95392-8ffc-5043-8978-ff07f6610c79 | d5c4c85696d21c370097a702a1c880a0fe5224c4ee8160ddb0eca7ad3b279077 |
| us/guidance/nsf/important-notice/149-research-security/4 | 9ea581fa-b25f-59cd-93f3-0bbf767e9cf4 | 32e6de5335f45b71a7b36dec754fa47be438c21b4fdaca984ce3119915fe3216 |
| us/guidance/nsf/important-notice/149-implementation-faq/question-3 | 737e78d3-50fe-5270-bae3-612a3c273d61 | 85300dd55c066db21e991954e184de8bb397122b553f25cc7399c05d0a6c1d38 |
| us/guidance/nsf/important-notice/149-implementation-faq/question-5 | 6a6ae4e4-c72c-594c-98ed-82502f381595 | 846a41f7b6f5f371cc57011e0b22252f8ee96626fdac29a86b823a61a5d2669c |
| us/guidance/nsf/important-notice/149-implementation-faq/question-6 | 7eb10f8c-8296-5c2a-8f80-e6fbc5b48ac9 | 7421c38e894258b087d2a0c468a488acf3dea9b6ed8a411ae38f0cead6267fd0 |
| us/guidance/nsf/important-notice/149-implementation-faq/question-7 | b8e7df20-be8e-5d01-a8a7-440b1def2cd2 | 5b495b022f84ecd1a1e58e9ae4fefa880a64d97defb0bb14e8172cd3743e259d |
| us/guidance/nsf/important-notice/149-implementation-faq/question-8 | 41e58f51-90cc-5b72-8fb9-e8de0f878789 | fcb3cf23c893c1237dece111578692f4d66750d7e5a00a6be767dfbb0978f777 |

The body hashes are SHA-256 over the exact UTF-8 JSON string contents without
an added terminal newline.

## Source-backed date and scope decisions

- Item 3 makes an actual current MFTRP party ineligible to serve as senior/key
  on an NSF proposal. This is an individual-status rule, not a certification
  rule.
- Item 3 separately covers senior/key service on an NSF award made strictly
  after 2024-05-20. The award edge must use greater-than: 2024-05-20 rejects
  and 2024-05-21 accepts.
- Item 4 and FAQ question 5 separately impose the annual certification duty
  only on a PI or co-PI with at least one linked active NSF award made on or
  after 2024-05-20. That edge must use greater-than-or-equal.
- The senior/key individual proposal certification is linked only to the same
  proposed project.
- The AOR organizational proposal certification is separate from the
  individual's certification and separately requires a complete same-proposal
  senior/key roster, awareness, and compliance.
- FAQ question 7 limits proposal-submission certifications to the proposed
  project. That proposal-only limitation does not extend to the annual
  person-level Research.gov certification.
- FAQ question 8 supplies 2025-12-02 as the general IN-149 effective date.
- FAQ question 3 separately says MFTRP certifications were already in effect
  during the appropriations lapse, but it supplies neither the precise earlier
  proposal-certification start date nor exact lapse bounds.
- Therefore proposal-certification documentation must fail closed through
  2025-12-01 and may first affirm on 2025-12-02. The required 2025-10-09,
  2025-10-10, and 2025-12-01 cases are false; 2025-12-02 is the first definite
  true edge.
- The May 20 award-date cutoff and the December guidance date are distinct.
- No membership, actor type, role, proposal or award linkage, NSF status,
  active status, award date, awareness, compliance, attestation, or annual
  cycle fact may be inferred.

Temporal versions must remain source-specific:

- The proposal-certification documentation outputs require an explicit false
  version through 2025-12-01 and a true version beginning 2025-12-02.
- The 2024-05-20 award dates are eligibility/duty input cutoffs, not invented
  module-effective dates. Their Date table still requires an explicit
  pre-cutoff rejecting state and the strict/inclusive comparison edges stated
  above.
- Item 3 says the participation prohibition is in effect but does not supply
  its historical start date. No earlier true effective version may be
  invented.
- FAQ question 3 says MFTRP certifications predate the 2025-12-02 general
  date, so that general date may not be falsely treated as the start of every
  annual MFTRP duty. Because the authorized records do not supply the precise
  earlier start, any disputed earlier interval must fail closed or be typed
  deferred rather than receive a guessed true version.

No temporal version was generated in these blocked runs. Every required
pre-effective false state and every later accepting state therefore remains
unimplemented and rejected, rather than silently inferred.

The required base has no canonical us:statutes/42/19232 module. The intended
adapter must expose separate fail-closed external individual- and
AOR-responsibility prerequisite facts. It must not import, quote, or recreate a
parallel section 19232 evaluator.

## Prepared input and context custody

- Encoding brief SHA-256:
  fd27bc45a5140c0d549c228ce252badece89148f57d24623e1c52c30dc74d1ab
- Item 4 continuation SHA-256:
  c468b6ced83edac19f44e6c3868a758276baf2f273c68741884016ce79dc8ccf
- FAQ question 3 continuation SHA-256:
  6db55c4fa789759bf6af4f5ab3d51dc09721a43e1616d5ca8275e37c889c6a9f
- FAQ question 5 continuation SHA-256:
  23f39e71f68a8b1c19887df55db41f70f62fd76afe8a24ebc6fdf9128e8c973c
- FAQ question 6 continuation SHA-256:
  20de14f72e53f623750b89a5474021b649a4599fbbeace28d5daed531cc67b82
- FAQ question 7 continuation SHA-256:
  2bdb553f32cdcac8ffa013f88c1332a7aed39bb1eaf84eb7bc1ce5d1abf9071b
- FAQ question 8 continuation SHA-256:
  713a0bd9622e9c4d4753ac3cc7a3fdb11600142053b72dcd5a01af9fde1bcac3

Every isolated workspace copy matched its committed lane input byte-for-byte.
Across all three attempts:

- Context manifest SHA-256:
  97fad085636a38e799b61c8cf2da0e8a37e8c4939e7f4e16f498d6e75a4fd273
- Source metadata SHA-256:
  58c04f7bc2c19f28ff6fb2aa882972452e5e6a5fe1ce54e585819830d36cedbc
- Positional source.txt SHA-256:
  2f234ab1b8601faf834c398c6bd2f4339f896a0faadd97d91e9f56839052d2ba
- Generation prompt SHA-256:
  008742d2935294291762f621d4948ceb80c1a66559526d2eb2121772a03f9066

The context manifest contains exactly seven context files: the unchanged
encoding brief and the six continuation files. Its source metadata records
exactly the seven authorized corpus citation paths. It records item 3 as the
requested and resolved positional source and item 4 plus FAQ questions 3, 5,
6, 7, and 8 as primary-source continuations. No neighboring candidate, other
FAQ question, other source record, or section 19232 RuleSpec was retrieved.

## Axiom toolchain custody

### axiom-encode

- Worktree:
  /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode
- Commit: 3869d66d009f52258be35901edbef370e65a399c
- Tree: d2ce31c8073b4bc0b4b169b9273f394650094230
- Version: 0.2.1200
- uv.lock SHA-256:
  ff0ea7983fe344be90ab54b388b0c4c441a1ac69ecf73937440d12802d92d5fc
- Executable SHA-256:
  6d134a9820f10826d3cb56e1a0df755636cad8543051811acc2f0be102af0173
- Git state before and after the invocations: clean and detached.

This dedicated lane pin, rather than the repository-wide workflow-toolchain
version, controlled all three attempts.

### axiom-rules-engine

- Worktree:
  /Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine
- Commit: ffd8213271947b0189a9dd61a055c1e0e78908a0
- Tree: 86e78cc74fffe774fe0ba010c0a951ca1dfcc000
- Cargo.lock SHA-256:
  56f01fb4b5118a479328fbffd55b93635ed11038de60bcdd206b88aad84d16cb
- Existing debug binary SHA-256:
  ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb
- Git state: clean and detached.

## Sanitized invocation

The final attempt used this command shape. OUT was a newly created isolated
directory. The signing value was inherited only by the unchanged encode
--apply process tree and was never placed on the command line.

~~~bash
AXIOM_ENCODE_RUN_LOG_DIR="$OUT/run-logs" \
"$ENCODER/.venv/bin/axiom-encode" encode \
  us/guidance/nsf/important-notice/149-research-security/3 \
  --source-id us:policies/nsf/important-notice/149-research-security/mftrp-certification-adapter \
  --output "$OUT" \
  --backend codex \
  --model gpt-5.5 \
  --corpus-path "$CORPUS" \
  --axiom-rules-engine-path "$ENGINE" \
  --policy-repo-path "$WORKTREE/us" \
  --mode repo-augmented \
  --allow-context "$WORKTREE/bulk/ENCODING_BRIEF.md" \
  --allow-context "$WORKTREE/bulk/nsf-in149-mftrp-context/01-item-4.txt" \
  --allow-context "$WORKTREE/bulk/nsf-in149-mftrp-context/02-faq-question-3.txt" \
  --allow-context "$WORKTREE/bulk/nsf-in149-mftrp-context/03-faq-question-5.txt" \
  --allow-context "$WORKTREE/bulk/nsf-in149-mftrp-context/04-faq-question-6.txt" \
  --allow-context "$WORKTREE/bulk/nsf-in149-mftrp-context/05-faq-question-7.txt" \
  --allow-context "$WORKTREE/bulk/nsf-in149-mftrp-context/06-faq-question-8.txt" \
  --db "$OUT/encodings.db" \
  --no-sync \
  --apply
~~~

Reviewers were not skipped. apply-target-only was not used. No sync or publish
operation was authorized or attempted.

## Signing custody

- Required environment variable: AXIOM_ENCODE_APPLY_SIGNING_KEY
- Presence check: nonempty for each encode --apply invocation.
- Independent value inspection, printing, logging, hashing, or rotation:
  none.
- Keychain or agent-secret lookup: none; the current instruction supplied the
  approved environment and superseded the prior keychain blocker.
- Alternate signing material: none.
- Manual sign-applied-files invocation: none.

Because generation failed before an apply candidate existed, the run never
reached manifest signing. No apply manifest, signature, applied file, or
key-derived retained artifact was created.

## Run, trace, output, and custody hashes

All attempts occurred on 2026-08-30 in America/New_York. Each trace records
backend codex-exec, provider openai, model gpt-5.5, timed_out=false, 14 events,
10 reconnect/error events, and a final turn.failed transport event.
The contemporaneously observed CLI results were exit code 1 for each process
and reported input, output, cache-read, and reasoning token counts of zero.

| Attempt | Isolated output root | Run/session | Duration | Final outcome |
| --- | --- | --- | ---: | --- |
| 1 | /private/tmp/axiom-encode-nsf-in149-mftrp-20260830-YWbaRb | 545f312a / encode-545f312a | 63,813 ms | apply_blocked_generation |
| 2 | /private/tmp/axiom-encode-nsf-in149-mftrp-retry-20260830-tVuFvn | 199fc3bb / encode-199fc3bb | 73,789 ms | apply_blocked_generation |
| 3 | /private/tmp/axiom-encode-nsf-in149-mftrp-finaltry-20260830-pI1rop | 2c12f1cb / encode-2c12f1cb | 66,011 ms | apply_blocked_generation |

| Run | Trace SHA-256 | Repair manifest SHA-256 | Run-log SHA-256 | Encoding DB SHA-256 |
| --- | --- | --- | --- | --- |
| 545f312a | d91b233a83930ca41a6f366fade1198ab39d908a84c8faab0a167b2704e98c9e | 1b963077fca425b4dc93d30bc94ad39211a679a83ec2984e660c58ca28a75586 | e3350a6b3a5f28d35d6f0c165ebd0405929f78c251559a78d2de3cda9ecff471 | fbc47f243fec72b5c95596d5c4ac12ba05e6d9b0e59bf231f20a6d91ea44a9e7 |
| 199fc3bb | b9b0cd1e6659d38385a64ca41358dc0add03c79d480233d23f791ce4f01b4fea | b6fcfed65526850229318a8b4c64884a18421cef366c8a50fee9eb39b2ec0661 | 80cee398c7717ee5e004b9c1618dba8089822986d48a4480c32160d12827b2af | 3d5093c5db0a38fa3b2e4d501aa41cd00f3fe601fe10287f408809e761023435 |
| 2c12f1cb | 1455110f985ba8e83a9590be7c41b376ab1215ed7d00091aaa3bc69ca2e2c1ee | 647707c61ebdd5e6a1cabbae9b58055eea4f999e1df081dc2f43a70870594927 | f9ef4d5bde76e527e3c263ce340970feae61e378c4ea5cd2e8c240fe0d595f2e | 1cf22eb689dcff5d723edeee767a6583bdfb88951e6e838de2519f7e4dc71629 |

The structured databases record rulespec_content length 0,
standalone_validation_success=false, applied_files=[], final_success=false,
and apply_error equal to the ChatGPT response-stream disconnection. Although
the run-log generation row uses status=passed to mean that the generation
stage returned control to the harness, its reason field contains the transport
error and the apply row is failed. No report treats that row as successful
generation.

Generated main output: absent in every root, so no generated-output hash
exists. Generated companion output: absent. Applied main/test hashes: none.
Apply-manifest and signature hashes: none. Generated-versus-applied equality:
not applicable because neither side exists. Apply auto-repair or auto-deferral
markers: none.

A contemporaneously observed direct reachability diagnostic after the third
failure returned curl exit 6, HTTP code 000, and no remote IP because
chatgpt.com could not be resolved.

## Files and retention decision

Committed preparation/source-contract files preserved byte-for-byte:

- bulk/ENCODING_BRIEF.md
- bulk/nsf-in149-mftrp-context/01-item-4.txt
- bulk/nsf-in149-mftrp-context/02-faq-question-3.txt
- bulk/nsf-in149-mftrp-context/03-faq-question-5.txt
- bulk/nsf-in149-mftrp-context/04-faq-question-6.txt
- bulk/nsf-in149-mftrp-context/05-faq-question-7.txt
- bulk/nsf-in149-mftrp-context/06-faq-question-8.txt

Configured reporting files updated but not committed:

- bulk/PROGRESS.md
- bulk/FINAL_REPORT.md

Failed-run evidence retained outside the worktree includes these exact repair
manifests, whose hashes appear in the custody table above:

- /private/tmp/axiom-encode-nsf-in149-mftrp-20260830-YWbaRb/codex-gpt-5.5/policies/nsf/important-notice/149-research-security/mftrp-certification-adapter.repair.json
- /private/tmp/axiom-encode-nsf-in149-mftrp-retry-20260830-tVuFvn/codex-gpt-5.5/policies/nsf/important-notice/149-research-security/mftrp-certification-adapter.repair.json
- /private/tmp/axiom-encode-nsf-in149-mftrp-finaltry-20260830-pI1rop/codex-gpt-5.5/policies/nsf/important-notice/149-research-security/mftrp-certification-adapter.repair.json

Executable files retained: **none**.

- No us/policies/nsf/important-notice/149-research-security/mftrp-certification-adapter.yaml.
- No adjacent companion .test.yaml.
- No expected signed encoding manifest at
  us/.axiom/encoding-manifests/policies/nsf/important-notice/149-research-security/mftrp-certification-adapter.json.
- No reverse-index mutation.
- No generated temporary candidate copied into the repository.

The generated target and companion were absent before every attempt and after
every failure. Because generation returned zero RuleSpec bytes, there was no
partial atomic bundle to selectively retain and no generated bundle that
needed restoration. Relocating the first two untracked run logs preserved
their hashes exactly and removed the only non-report worktree residue.

## Atomic rule acceptance

| Atomic output | Required distinction | Decision |
| --- | --- | --- |
| Proposal senior/key ineligibility | Actual current MFTRP participation; individual; senior/key; NSF proposal; same-project role link | **REJECT — no signed generated rule** |
| Award senior/key ineligibility | Actual current participation; individual; senior/key; NSF award; same-award link; award date strictly after 2024-05-20 | **REJECT — no signed generated rule** |
| Senior/key individual proposal certification documented | Same senior/key individual and same proposed project; individual attestation; Biographical Sketch and Current and Pending Support channels; external individual section 19232 prerequisite | **REJECT — no signed generated rule** |
| AOR organizational proposal certification documented | Separate AOR actor and same proposal; Cover Sheet; complete roster; all aware; all compliant; separate individual and AOR section 19232 prerequisites | **REJECT — no signed generated rule** |
| Annual PI/co-PI certification duty | Individual PI/co-PI; one linked active NSF award; award date on or after 2024-05-20 | **REJECT — no signed generated rule** |
| Annual Research.gov status certification documented | Annual-duty gates plus Research.gov, submitted participation/non-participation status, and current annual cycle; person-level rather than proposal-level | **REJECT — no signed generated rule** |

Supporting generated structures are also rejected:

- Proposal-certification effective gate with explicit false version through
  2025-12-01 and true version from 2025-12-02: no generated parameter.
- Date-valued 2024-05-20 cutoff selected by an integer parameter table: no
  generated parameter.
- Separate fail-closed external individual and AOR section 19232 prerequisites:
  no generated inputs.
- Raw proposal and award identifiers with generated equality checks: no
  generated linkage formulas.

Actual membership and certification assertions remain conceptually
independent in the accepted encoding brief, including contradictory cases.
There is no executable output that collapses or infers either fact.

## Fixture, proof, oracle, and Rust results

- Generated companion fixture files: 0.
- Generated companion fixture cases: 0.
- Source-backed proof atoms: 0.
- Oracle fixtures: 0.
- Compiled Rust artifacts: 0.
- Direct Rust adversary requests: 0.
- Direct Rust response fixtures: 0.
- Accepted atomic outputs: 0.
- Rejected atomic outputs: 6.

Strict proof validation was not run because the required generated module does
not exist. Companion tests were not run because no companion exists.
guard-generated was not run against a generated diff because no generated
RuleSpec or manifest diff exists.

The pinned real Rust compile command was not run because its --program target
does not exist:

~~~bash
"$ENGINE/target/debug/axiom-rules-engine" compile \
  --program "$WORKTREE/us/policies/nsf/important-notice/149-research-security/mftrp-certification-adapter.yaml" \
  --output "$OUT/direct-rust/mftrp.compiled.json"
~~~

The pinned runtime binary itself was checked directly:

~~~bash
shasum -a 256 "$ENGINE/target/debug/axiom-rules-engine"
# ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb
~~~

Consequently the following run-compiled command had no artifact and was not
invoked:

~~~bash
"$ENGINE/target/debug/axiom-rules-engine" run-compiled \
  --artifact "$OUT/direct-rust/mftrp.compiled.json" \
  < "$OUT/direct-rust/exact-adversary-request.json"
~~~

No handwritten TypeScript, Python, mock, or parallel policy evaluator was used
in its place.

The requested but unexecuted state dimensions remain:

- senior/key versus PI/co-PI versus neither role;
- individual versus AOR actor;
- same versus other proposed project and certification linkage;
- same versus other award linkage;
- NSF versus non-NSF and active versus inactive award;
- award dates 2024-05-19, 2024-05-20, and 2024-05-21;
- actual current membership true, false, and missing;
- each required gate omitted one at a time;
- individual channels, Cover Sheet, Research.gov, wrong channel, and missing
  channel;
- complete versus incomplete roster, awareness, and compliance;
- each external statutory prerequisite true, false, and missing;
- current versus noncurrent annual cycle;
- proposal periods 2025-10-09, 2025-10-10, 2025-12-01, and 2025-12-02;
- actual membership facts contradictory to certification assertions.

No pass is claimed for an unexecuted fixture, proof, oracle, or Rust state.

## Exact unblock condition

The prior keychain blocker is resolved and was not revisited. The remaining
blocker is transport/DNS access from the pinned Codex backend to
chatgpt.com/backend-api/codex/responses.

When that endpoint is resolvable, rerun the sanitized command above with a new
isolated output root and AXIOM_ENCODE_RUN_LOG_DIR inside it. Do not change the
source set, encoding brief, model, backend, toolchain pins, canonical /us root,
or signing path. Retain output only if:

1. generation returns a main file and companion with no repair or auto-deferral
   markers;
2. signed apply reports the generated and applied bytes as identical;
3. the signed manifest and guard-generated pass;
4. strict proof validation reports both passed=true and proof_required=true;
5. every generated companion fixture passes;
6. all requested direct adversaries pass through the pinned real Rust runtime;
7. every atomic output independently satisfies its source, timing, linkage,
   missing-input, and custody contract.

Do not switch to a paid API backend, another model, manual signing, or a
hand-authored evaluator merely to bypass the transport failure.
