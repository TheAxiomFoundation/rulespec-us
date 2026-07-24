VERDICT: REQUEST-CHANGES

# Delta re-review — rulespec-us PR #1009

Reviewed exact current head
`8fab0f1e22ae8b177d874808cf257456ecac5452`
(`fed-parity/revproc`) against prior reviewed head
`3e31892d3b64cf63368927b57de1946e63bae196`. The code-level filing-status
blocker is genuinely resolved. The PR is not ready to approve because the
current-base gate requirement remains unmet and the live PR body is materially
false after the correction wave.

## Prior-finding resolution

| Finding # | Prior finding | Resolution | Resolved by | Verified how |
| --- | --- | --- | --- | --- |
| 1 | **Blocking:** three selectors synthesized a module-local filing-status classification and failed open for invalid status codes. | **RESOLVED by removal and explicit deferral.** | `320032a3` removes all three derived selectors and all local filing-status fixtures. Current policy lines 46–67 limit the module to nine per-category parameters and declare the three selected outputs under `deferred_outputs`. `73406660` removes the same three IDs from oracle pending; `8fab0f1e` refreshes the signed-manifest record. | Exact repository search finds each selected-output ID only in its deferral declaration, with no executable, companion, ledger, index, or consumer reference. The pinned `find_tax_filing_status_local_input_issues` check returns **0 rejections**. The module parses to nine rules and three deferred outputs; all nine retained executable rule definitions are byte-for-byte unchanged from the prior head. |
| 2 | **Non-blocking before merge:** the branch and green runs were based on stale `main`; update/rebase and rerun the complete suite. | **UNRESOLVED and now merge-blocking.** | No current-base update landed. | Live GitHub comparison reports the head is 12 commits ahead and **31 behind** `main`, with merge base `ba8c2a0` and live base `b07365d0`. Current-head Repository Checks run `30102126955` failed; waiver-change-guard job `89511228079` reports `new or changed validation waiver approvals must be waiver-only`; generated-guard was skipped. Source/reverse-index passed, and program-artifacts remained in progress at the final check. |

## New findings

1. **BLOCKING — the live PR body does not describe the corrected head or its
   actual gates.**

   - It still claims oracle sync added “+12 outputs, 0 stale.” The current
     module and pending ledger contain nine outputs: base 2,300 → head 2,309,
     exactly **+9 QBI IDs and 0 removed/stale**. The fix wave removed the three
     selected-output IDs.
   - It still claims the “full campaign battery” and generated guard are green.
     Repository Checks are currently failed and generated-guard was skipped.
   - It says this PR retires #1004's runtime-input boundary and that the QBID
     pipeline's threshold inputs become imports of this module. Current head
     explicitly defers all three selected-amount outputs because no upstream
     filing-status classification exists; it only supplies the nine
     per-category parameters.
   - It contains no post-review corrections section explaining the selector
     removal/deferral, the 12 → 9 output correction, or the revised repoint
     boundary.

   **Required:** update the body to state the nine-output scope and selector
   deferral accurately, add the post-review corrections section, and report only
   gates that have actually passed at the current head/current base.

2. **LOW — the fix wave makes `git diff --check` fail.**

   `git diff --check 3e31892d..8fab0f1e` exits 2 because
   `qualified-business-income.yaml:335` adds a blank line at EOF. This is
   non-semantic, but it is a new hygiene regression.

No new legal-value, formula, schema, source, ledger, or manifest-hash defect was
found in the fix wave.

## Requested local verification

- Pinned `axiom-encode` source:
  `3869d66d009f52258be35901edbef370e65a399c` (pyproject version
  `0.2.1200`), loaded from the clean pinned checkout.
- `validate --skip-reviewers`: **PASS**.
- `proof-validate`: **PASS**, 30 atoms.
- Companion with the explicitly requested `~/axiom-rules`: **PASS**, one file /
  three cases. That checkout currently resolves to dirty engine head
  `aa1ff025`, not the declared pin, so I also built exact pinned engine
  `ffd8213271947b0189a9dd61a055c1e0e78908a0` from a temporary archive and
  reran the companion: **PASS**, three of three.
- Pinned `find_tax_filing_status_local_input_issues(policy, companion)`:
  **0 rejections**.

The new companion arithmetic is correct:

| Category | Hand recomputation | Expected width |
| --- | ---: | ---: |
| Joint | 553,500 − 403,500 | 150,000 |
| Married filing separately | 276,775 − 201,775 | 75,000 |
| All other | 276,750 − 201,750 | 75,000 |

All nine published values and the 2026 effective window are unchanged from the
prior source-fidelity review. Policy SHA-256
`082fe85d884e91c736732f7eb793a4ffeb80ef8c4e34eacdc81509997deaa957`
and companion SHA-256
`f979217c69e56ac2596eae010d51ad1b7f8d8b48786431c565e3363a9a24b96c`
match the manifest. Its supersession hash and prior-signature field match the
old manifest. Current-head HMAC verification is not established by CI because
generated-guard was skipped.

GitNexus indexed the exact head (8,998 files, 10,716 nodes, 11,032 edges, 15
processes). The changed policy, companion, and pending ledger are represented
only as file nodes with zero callers or affected processes, so graph analysis
adds no executable blast-radius assurance beyond the direct repository search
and companion execution.

## Approval conditions

1. Update/rebase onto current `main`, regenerate base-sensitive shared artifacts,
   and obtain a complete green current-base suite including generated-guard.
2. Correct the PR body and add the post-review corrections section described
   above.
3. Remove the extra EOF blank line so `git diff --check` is clean.

No PR, branch, comment, review, or remote repository state was changed.
