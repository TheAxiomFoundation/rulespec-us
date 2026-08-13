# B1.3 pilot gate summary

| Gate | Verdict | Evidence |
|---|---|---|
| Witness identity | PASS, 90/90 cells | `IDENTITY.md`, `identity-diff.csv`, `identity-results.json` |
| Pinned validation | PASS | `VALIDATION.md`, `validate-ch72-final.log` |
| Determinism / `--check` | PASS | `DETERMINISM.md` |
| Import/formula/program structure | PASS | `STRUCTURE.md` |

Local delivery:

- Branch: `b1/schedule-composition-pilot`
- Commit: `04f920099`
- Pushed: no
- Existing RuleSpec modules modified: none
- Generated pilot chapters: 72 only

The execution sandbox permits reading but not writing
`/Users/maxghenis/PolicyEngine`. To put this staged evidence at the requested
durable location from an unrestricted shell:

```sh
mkdir -p "$HOME/PolicyEngine/_tariff-p5/b1/b13-pilot"
rsync -a --exclude __pycache__ \
  /Users/maxghenis/TheAxiomFoundation/_b1wt/rulespec-us/.b13-pilot-evidence/ \
  "$HOME/PolicyEngine/_tariff-p5/b1/b13-pilot/"
```
