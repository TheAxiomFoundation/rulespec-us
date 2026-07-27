# Federal SNAP residual investigation progress

## State

- Active branch: `fed-parity/snap-fed`.
- Starting commit: `1158ba5b248c3cbbfe1768357f03ca43c8b3618e`.
- Worktree started clean and matches the locally cached `origin/main`.
- A fresh fetch was attempted on 2026-07-27 but the sandbox could not resolve
  `github.com`; all work therefore uses the pinned local checkout and corpus.
- Investigation is in the evidence-gathering phase. No rule conclusion has been
  made yet.

## Done

- Loaded the PolicyEngine and PolicyEngine-US analysis guidance.
- Verified the active branch, worktree cleanliness, remotes, and cached base.

## Next

1. Tabulate every candidate residual across AL, MA, NC, SC, and TN and validate
   the requested class definition.
2. Read the retained text for 7 CFR 273.9(a)(2), 273.9(d)(3), and
   273.10(e)(2)(ii)(C), then trace the current federal encodes.
3. Reproduce representative cases in PolicyEngine-US 1.767.3 and isolate which
   rule differences drive the mismatches.
4. Make the smallest legally correct encode and companion-test changes, capture
   mutation evidence, and run the required suites.
5. Write and commit `WORKER-REPORT.md`.
