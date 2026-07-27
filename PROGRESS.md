# PR #1143 blind adversarial review

## State

- Review status: in progress.
- Review worktree: `.git/review-worktrees/pr-1143-6573e95`.
- Review branch: `review/pr-1143-6573e95`.
- GitHub-confirmed PR branch: `fed-parity/addmed-se-leg`.
- Pinned PR head: `6573e95d65e9a64f16bde98b18b24f3f5aff04e0`.
- GitHub-reported base ref/tip: `main` at `49876ad3b4c055b6ecfe17d0c0225490e932d40b`.
- Immutable PR merge base: `6b0773d3f7fa6719f208154f3e609e292ab7abe7`.
- Required corpus commit: `db12795577c5809009168982cf8a72fb58440620`.
- Exact-head execution checkout: `/private/tmp/pr1143-exec.8RO0dw/rulespec-us`.
- Exact-corpus execution checkout: `/private/tmp/pr1143-corpus.q0fghk/axiom-corpus`.
- Exact pinned-engine checkout: `/private/tmp/pr1143-engine.bqyvK3/axiom-rules-engine`.
- Final report: `REVIEW.md`.

## Done

- Verified PR #1143 metadata through the read-only GitHub connector.
- Confirmed the requested branch name and exact 40-character head SHA.
- Preserved the heavily dirty primary checkout by creating this isolated disposable worktree from the exact PR head.
- Established the immutable five-commit PR range
  `6b0773d3f7fa6719f208154f3e609e292ab7abe7..6573e95d65e9a64f16bde98b18b24f3f5aff04e0`.
- Confirmed the local range and GitHub metadata agree on exactly four changed files.
- Created a clean detached execution clone at the exact PR head with canonical
  `rulespec-us` leaf routing.
- Created a clean detached local axiom-corpus clone at exactly
  `db12795577c5809009168982cf8a72fb58440620`.
- Ran pinned-encoder `validate --skip-reviewers --json` against that exact
  corpus checkout: `ci_pass=true`, `all_passed=true`, and `errors=[]`.
- Ran pinned-encoder proof validation: all 17 atoms passed.
- Built the repository-pinned rules engine at
  `ffd8213271947b0189a9dd61a055c1e0e78908a0` from a clean local clone.
- Ran the exact-head companion with that pinned engine: 1 file and all 19
  cases passed.
- Attempted the GitNexus PR-review graph workflow. The repository was not
  indexed; local analysis parsed it but could not register the graph because
  the sandbox denied writing `/Users/maxghenis/.gitnexus/registry.json`.
- Replaced the unavailable graph query with direct symbol/import searches:
  no program or external RuleSpec module imports any changed public pipeline
  output.
- Verified all 12 source-backed proof excerpts verbatim against retained corpus
  text at the required commit; the statutory `3121(b)(2)` scrivener's error is
  mentioned only as documentary context, never used as operative proof.
- Independently recomputed the featured amount:
  `150000 * 0.9235 = 138525`,
  `max(0, 200000 - 100000) = 100000`, and
  `(138525 - 100000) * 0.009 = 346.725`.
- Proved the complete wage-leg rule node is byte-identical to the merge base,
  as is the imported section 3101(b)(2) module.
- Proved all 13 retained cases preserve their full inputs and wage-tax
  expectations. Eight wage-only blocks are byte-identical; five positive-SE
  blocks necessarily update SE expectations, and the former combined
  fail-closed case is renamed while preserving its input and wage result.
- Verified manifest structure, both applied-file hashes, ancestor ordering,
  supersedes linkage, and pinned clean encoder provenance.
- Regenerated/checked the reverse index: current at 4,233 provisions, 5,069
  edges, and 4,483 modules. The manifest/index pytest set passed 9 tests; the
  repository-layout set passed 9 tests.
- Ran the required isolated mutation matrix. Removing wage reduction caused 30
  failures across 10 cases; changing the joint threshold from 250,000 to
  200,000 caused 7 failures across 3 cases; removing the threshold floor caused
  19 failures across 8 cases.
- Restored exact bytes after every mutation and obtained 19/19 target passes
  each time. The broader target + direct wage/SE companion set passed 39/39,
  and the mutation worktree finished clean at the exact PR head.

## Next

- Establish the immutable PR-only range and inspect every changed byte.
- Audit legal fidelity, wage-leg preservation, adversarial cases, manifests, reverse index, and PR history hygiene.
- Run pinned-corpus validation, companion tests, required mutations, and restore-pass checks.
- Write the evidence-backed verdict to `REVIEW.md` and complete this ledger.
