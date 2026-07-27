# Progress

## State

- Branch: `closure/enc-273-4c`
- Slice: 7 CFR 273.4(c), sponsored-alien income and resource deeming.
- Status: implementation design complete; RuleSpec drafting is next.

## Done

- Read the closure-sprint encoder preamble.
- Read the repository and Colorado agent notes.
- Confirmed the worktree began clean against `origin/main`.
- Loaded the GitNexus exploration and impact-analysis workflows.
- Read the authoritative 7 CFR 273.4 corpus row at expression date
  2026-07-09, including every paragraph of 273.4(c).
- Read the required 273.9, 273.10, 273.2(j), and 273.11(c) modules and all
  companion tests, plus the current 273.4 module and test.
- Traced the existing income-limit, resource-limit, and Colorado
  sponsored-noncitizen encodings for compatible formula and test patterns.
- Chose a nested `us/regulations/7-cfr/273/4/c.yaml` module boundary with a
  companion test and a minimal removal of the satisfied deferral in `4.yaml`.
- Identified two distinct size inputs required by the text: the sponsor
  reference unit for 273.4(c)(2)(i)(B), and the sponsored alien household for
  the 273.4(c)(3)(iv) indigence threshold.
- Confirmed indigence substitutes an adjudicated amount actually provided
  during a renewable 12-month period; it is not a zero-deeming exception.
- Confirmed the initial battery exception is a full 12-month exception, while
  the post-12-month rule excludes only a qualifying batterer's income and
  resources and therefore requires sponsor/spouse component separation.
- Attempted the prescribed GitNexus index. Repository parsing completed, but
  sandboxed registration failed at `~/.gitnexus/registry.json`; the generated
  untracked index was moved intact to
  `/private/tmp/gitnexus-enc-273-4c-a0645b1`, and direct source tracing was
  used as the fallback.

## Next

- Encode the subject predicate, normal deeming period, categorical
  exemptions, indigence and battery branches, and sponsor/spouse formulas.
- Add companion cases covering the normal formula, allocation, every
  exception, and period-ending events with every input fact assigned.
- Remove the satisfied `273.4(c)` deferred output from `4.yaml`.
- Run repository validation, push the branch, and open the required draft PR.
