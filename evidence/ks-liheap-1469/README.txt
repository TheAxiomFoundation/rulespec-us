Kansas LIHEAP issue 1469: draft encoding and local oracle evidence

This bundle accompanies unsigned, unaccepted generated source pairs. It is
review material for a Draft PR, not production provenance, a signing request,
full-program parity, or automatic integration into the encoder's oracle CI.
Related issue: https://github.com/TheAxiomFoundation/rulespec-us/issues/1469

Observed results

The two real engines compared 199 of 616 case/output slots across 36 of 44 fixtures:
189 agreements, 10 differences, zero execution errors, 417 unsupported slots.
The command deliberately exits 2 for incomplete coverage. oracle-results.json
contains every fixture row, all compared values, all differences and all
unsupported outputs. It is a portable export, not the byte-identical original.

All 10 differences concern ordinary recurring military payments. Annual amounts:
  retired pay: Axiom 24,000, PolicyEngine 0
  survivor annuity: Axiom 9,600, PolicyEngine 0
  combined retired pay + annuity + ordinary pension: Axiom 34,800, PE 1,200
  child survivor annuity: Axiom 9,600, PolicyEngine 0
These produce eight unearned/total-income differences and two income-eligibility
flips. The admitted-source review and Pavel's clarification support counting
these recurring payments; specific combat, burial and other exemptions are
separate conditions. No oracle formula, expectation or generated rule was
edited to erase the differences.

The 35 monthly-limit comparisons agree, conditional on explicitly supplied
upstream household size. The payment slice covers ordinary recurring wages,
pension, military retirement and SBP only. Each nonzero raw source must be
represented exactly once. Nonzero unsupported income and household TANF are
refused; their fixtures remain unsupported. Interest comparisons here check
only zero-interest cases. Period conversion assumes stable monthly income:
annual/12 for raw amounts and monthly*12 for comparison units. This does not
model variable-income timing, 2025 rules, household membership, energy
vulnerability, benefit matrices or final program payments.

Draft acceptance and exact pair identity

Income source SHA256 59044c... is the same source used for the oracle comparison
and final encoder CI rejection. Historical oracle compilation accompanied the
original 16-case companion. This PR includes the final automatically expanded
17-case companion SHA d31106..., byte-identical to the rejected run's output.
The household pair is the original frozen 18-case generated pair; later
interrupted automatic test expansion is not the pair in this PR.
The exact PR pairs were recompiled and tested together: 35 cases, two programs,
zero failures. See pr-companion-validation.json and provenance.json.
Focused repository checks also ran: 25 passed, one failed and one warning.
The derived-rule companion coverage test fails because ten new household
outputs lack direct assertions. See repository-checks.json for the exact
command, names and result. No waiver or validation gate was changed.

Passing generated companions does not settle correctness. Income CI rejected
the draft and independent review identified child self-employment exemption,
gift-condition, unknown income-kind and opaque-exemption defects. Of 77 CI
messages, 68 concern numeric coverage; several appear to treat legal references
or historical details as calculation parameters. Genuine representation,
proof and test-coverage gaps remain. Rejection was not waived and no gate was
weakened. See income-ci-issues.json and income-source-review.json.

Household independent source checks pass 16 of 17 cases. An excluded citizen
college student incorrectly satisfies household alienage eligibility because
the aggregate lacks the membership filter. Full encoder validation was stopped
after this defect was confirmed, during slow automatic positive-test synthesis;
it has no final validator verdict. See household-source-checks.json,
household-source-review.json and household-run-status.json.

Full-program composition also needs source dispositions for the operative
FY2026 matrix, proposed minimum-payment floor and categorical-income precedence.
The FY2026 plan states January 20 through March 31, 2026; the historical issue
extraction's autumn 2025 claim is not established law. See source-dispositions.json.

Evidence identities and limits

manifest.json inventories this unsigned author-prepared bundle. provenance.json
records original-local-evidence SHA256 and exported SHA256 separately. Portable
JSON replaces workstation paths with ${EXPERIMENT}, ${ENGINE_EXPERIMENT} and
${PUBLICATION_ARTIFACTS}; referenced original hashes are historical identities,
not hashes of the exported files. Preserve that distinction when reviewing.
Historical local artifacts, raw model traces, binary compiled artifacts, private
credentials and workstation paths are not committed.

The tested encoder was 0.2.2351 at 414ee42fcf748f9abf637b90d5a7cd320abf1162 with a
local companion-resolution-cache fix. It passed 25 focused real-engine tests and
68 companion/waiver tests; it is described in encoder-cache-validation.json.
The archived oracle bridge had 56 focused tests passing and independent review.
A fresh replay from a separate local oracle clone reproduced all 199 comparisons
and 10 differences with no execution errors. Negative controls reject changed
tracked oracle code, a changed release envelope with unchanged content, the
wrong engine commit, and an existing output directory. See
portable-replay-validation.json.
The bridge is not present in the released/pinned oracle dependency; this bundle
archives its exact three-file patch against axiom-oracles commit
9717404e8cbec52a18d94d279f1bbe88f8c2d41b. It does not update standard encoder CI.

The signed source release was admitted by the historical local encoder:
  us-rulespec-2026-10-27-ks-liheap
  content SHA256 59bdb021da2af10a87aac4ebc9969a9b31c64eacb79c1f34e57709f6ce43c8f8
  corpus commit 0b24480055729191ec5dcc01556bc9c1b0c8eaa7
  https://github.com/TheAxiomFoundation/axiom-corpus/actions/runs/42747046189
  attempt 3, artifact signed-corpus-release-object
Use the retained signed JSON object named
us-rulespec-2026-10-27-ks-liheap-release-object.json. This bundle does not contain
the release or grant source admission. The replay helper requires the exact original artifact file SHA256
c010171f234bfad495eb42538604446590e35012ec9fc89c27b59246edea6b50
and checks its content identity; this binds to the historically verified
artifact, without performing new signature admission. Use the normal trusted
corpus verification procedure for independent signature verification. No private signing or R2 credentials are needed for
this diagnostic replay with an already verified local release.

Reproduce locally

Use explicit local checkouts belonging to TheAxiomFoundation. Choose fresh
scratch locations. Commands below show placeholders, not literal paths.

1. Keep this PR checkout named rulespec-us. Its exact four policy files must
   match provenance.json. Do not hand-edit the generated rules or companions.

2. Prepare an axiom-oracles checkout at
   9717404e8cbec52a18d94d279f1bbe88f8c2d41b. From that checkout run:
     git apply --check /path/to/rulespec-us/evidence/ks-liheap-1469/oracle-bridge.patch
     git apply /path/to/rulespec-us/evidence/ks-liheap-1469/oracle-bridge.patch
   The patch adds only the bridge, fixture and focused tests. It does not alter
   PolicyEngine or any generated rule. Use a separate clean checkout so the
   patch does not overwrite unrelated work.

3. Recreate the development oracle runtime using the exact 96-package lock:
     uv venv --python 3.13 /path/to/scratch/oracle-runtime
     uv pip sync --python /path/to/scratch/oracle-runtime/bin/python \
       --require-hashes /path/to/rulespec-us/evidence/ks-liheap-1469/requirements.lock.txt
   Main packages are policyengine 6.11.1, policyengine-us 2.68.0,
   policyengine-core 3.34.10 and policyengine-taxsim 2.30.0. This is the tested
   development runtime, not a protected admitted runtime or the default lock.

4. Use an axiom-rules-engine checkout at
   89571cc2a938707fd60a5489b951135345697296 and its verified build receipt.
   With the recorded encoder checkout available, its supported binding command
   can build/receipt the engine:
     axiom-encode engine-bind --axiom-rules-engine-path /path/to/axiom-rules-engine \
       --pin 89571cc2a938707fd60a5489b951135345697296
   Do not create or modify a build receipt by hand. The bridge verifies the
   receipt's commit and binary identity during execution. Different platforms
   may produce different binary/artifact hashes; fresh replay receipts record
   their actual bytes, rather than asserting the historical macOS hash.

5. Materialize the tokenized binding and recompile in a fresh directory outside
   the RuleSpec checkout. Use the oracle runtime's Python:
     /path/to/scratch/oracle-runtime/bin/python \
       /path/to/rulespec-us/evidence/ks-liheap-1469/prepare_replay.py \
       --rulespec-root /path/to/rulespec-us \
       --engine-root /path/to/axiom-rules-engine \
       --oracles-root /path/to/axiom-oracles \
       --release-object /path/to/the-verified-release-object.json \
       --output /path/to/scratch/new-ks-replay
   The helper checks bundle, source-pair and bridge hashes, oracle/engine commits
   and tracked cleanliness, and the exact release-object hash. It compiles income,
   retains rejection and writes new compilation/binding receipts. It performs
   no network calls, signing, admission, RuleSpec edits or publication. It
   refuses an existing output directory. It prints the exact replay command.

6. From the patched axiom-oracles checkout execute that printed command:
     /path/to/scratch/oracle-runtime/bin/python -m axiom_oracles.bridges.ks_liheap \
       --candidate-binding /path/to/scratch/new-ks-replay/candidate-binding.json \
       --report /path/to/scratch/new-ks-replay/comparison.json
   Expected: exit 2, 199 compared slots, 10 differences, zero execution errors,
   417 unsupported slots. These results characterize a rejected draft. Preserve
   a different outcome for investigation; do not change inputs to force agreement.

Further encoding must repair the recorded defects through supported generation,
complete missing coverage, and independently review the new exact candidate.
This PR must remain draft until those conditions and protected admission/CI
requirements are satisfied. Nothing in this bundle authorizes a merge.
