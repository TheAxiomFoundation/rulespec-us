# Chunk 2 taxable-income pipeline progress

## State

The taxable-income compose and its 27-case companion are implemented. The exact
ten-import closure compiles without duplicate rules, excludes the colliding
`us/statutes/26/63/c.yaml` surface, and introduces no local relation. The pinned
companion runner and `validate --skip-reviewers` are green in the working tree.

## Done

- Verified that `origin/main` contains merged Chunk 1 and Atomic PR 0.
- Created the requested worktree and branch because neither existed locally.
- Confirmed the exact taxable-income import set, public output, cases, and commit order.
- Audited the 24-module imported closure: 224 pre-existing executable rules are unique;
  the only relations are the four existing SALT, section 151, and section 170(p)
  relations.
- Added the guarded taxable-income domain, branch deduction total, and
  `federal_taxable_income` final with current non-local import hashes.
- Added all 14 binding section 6.3 grid cases plus 13 companion-only diagnostics,
  including invalid status, all-attestations-false, election mismatch, negative
  wagering loss, all four section 63(c)(6) disqualifiers, and relation orientation.
- Passed 27/27 companion cases and pinned corpus validation with zero findings.

## Next

- Commit the coherent compose/companion step.
- Re-run the pinned gates from a canonical-basename `git archive` root.
- Regenerate and verify the reverse index, add the sorted pending-ledger union,
  and commit those mechanical artifacts.
- Run final gates and write the untracked worker report; leave signing and the
  manifest to the main lane as instructed.
