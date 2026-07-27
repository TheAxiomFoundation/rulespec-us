# Progress: 7 CFR 273.24(g)

## State

Paragraph (g) is encoded with person-level application and time-limit effects,
the State fiscal-year allocation cap, allocation charging, and
nondiscrimination. The module passes the pinned encoder validation pipeline,
proof validation, and all 17 companion cases. Repository-wide checks and
direct-downstream import-hash maintenance are complete. Final signed-manifest
attestation and remote PR delivery are blocked on unavailable credentials and
network/connector access.

## Done

- Confirmed the assigned slice is 7 CFR 273.24(g), ABAWD State discretionary
  exemptions.
- Confirmed the frozen `programs/` tree and other protected files will not be
  edited.
- Confirmed the branch is `closure/enc-273-24g`, based on `origin/main`.
- Read the `2026-07-09` corpus text for 7 CFR 273.24(g).
- Read the required sibling modules and companion tests for sections 273.9,
  273.10, 273.2(j), and 273.11(c).
- Confirmed paragraph (g) requires:
  - a covered-individual predicate and a person-level State exemption choice;
  - an 8 percent fiscal-year average-monthly allocation cap based on FNS's
    adjusted covered-individual estimate;
  - separate treatment for exemptions provided to an otherwise-exempt person;
  - nondiscriminatory State administration.
- Confirmed paragraph (g) gives no executable formula for FNS's estimate and
  no rounding rule, so the final adjusted estimate will remain an input and
  the allocation output will be decimal-valued.
- Confirmed paragraph (h) carryover/adjustment mechanics and paragraph (i)
  reporting are outside this slice.
- Removed the paragraph (g) deferred output while preserving the unrelated
  paragraph (j) deferral.
- Added the 8 percent parameter, the defined State caseload measure, the
  decimal-valued FNS-adjusted State allocation, and the fiscal-year cap
  compliance judgment.
- Added the covered-individual predicate, State-assignment application
  predicate, and the separate allocation-charge predicate for an exemption
  provided to someone otherwise exempt that month.
- Composed allocation charging from the legally effective exemption predicate,
  so an attempted assignment to a non-covered person neither applies nor
  consumes the State allocation.
- Composed an applied discretionary exemption into the existing ABAWD
  time-limit-inapplicable and time-limit-eligible results.
- Added the paragraph (g)(4) State nondiscrimination judgment.
- Scoped its eight discrimination facts to exemption administration, rather
  than selection alone, so the compliance result covers all treatment of a
  covered individual.
- Added companion coverage for both covered-individual entry branches, every
  exclusion, assigned and unassigned covered recipients, the resulting
  time-limit effect, the otherwise-exempt allocation exception, the exact
  8 percent boundary, and nondiscrimination.
- An independent legal/diff audit found no remaining blocking correctness
  issue after the allocation-charge and nondiscrimination-scope corrections.
- Passed:
  - pinned `axiom-encode` proof validation (25 atoms);
  - pinned `axiom-encode` companion execution (17 cases);
  - pinned encoder CI validation with this worktree supplied explicitly as
    the policy root.
- Identified a pinned CLI routing defect: because this worktree is not named
  `rulespec-*`, the ordinary `validate` entry point resolves absolute legal
  test inputs against a stale sibling checkout. The same pinned validation
  pipeline passes when supplied this worktree as its policy root.
- Updated the directly affected 7 CFR 273.11(c) proof import hash for
  `snap_member_abawd_time_limit_eligible` and assigned the new discretionary
  exemption fact in its four ABAWD-dependent cases.
- Passed the 7 CFR 273.11(c) companion suite (13 cases) and proof validation
  (16 atoms). Its full validator reaches an unrelated baseline failure:
  `origin/main` already pins the 7 CFR 273.10 import to
  `sha256:c0fea2...`, while the unchanged 7 CFR 273.10 file is
  `sha256:f9b9f0...`.
- The deterministic repair/signing helper could not access its local signing
  key because the `agent-secret` keychain is locked; no files were changed by
  the failed helper invocation.
- Recorded the paragraph (g)(3) threshold as an average-monthly ceiling, not
  annual case-months, and accepted FNS's already-adjusted covered-individual
  estimate as an external fact because the regulation does not specify an
  executable FY 1996 quality-control/other-factor estimation method.
- Passed the reverse-index check: 4,232 provisions, 5,068 edges, and 4,483
  modules are current.
- Repository pytest completed with 64 passing tests, one warning, and only the
  expected manifest-drift failure for the two intentionally changed modules.
- The generated-file guard likewise reports only the four changed RuleSpec
  module/test files as awaiting matching signed manifests. Its dry run
  confirms exactly two manifests are required: 7 CFR 273.24 and the directly
  affected 7 CFR 273.11(c).
- Confirmed the branch changes no file under `programs/` or any other
  protected path.
- `git fetch origin main` cannot resolve `github.com` in this environment.
- The connected GitHub attempt to create `closure/enc-273-24g` was canceled;
  no remote branch or PR was created.

## Next

- Restore either `AXIOM_ENCODE_APPLY_SIGNING_KEY` or the missing
  `agent-secrets/keychain-password` login-keychain credential, then refresh
  and sign the two affected manifests.
- Rerun pytest and the generated-file guard; both should clear their sole
  manifest-attestation failure.
- Enable GitHub network access or approve the connected branch-creation
  action, then push `closure/enc-273-24g` and open the required draft PR.
