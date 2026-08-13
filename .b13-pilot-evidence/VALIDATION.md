# B1.3 chapter-72 validation gate

Verdict: **PASS**

Command (run from `~/TheAxiomFoundation/axiom-encode-perf`):

```sh
AXIOM_CORPUS_REPO=$HOME/TheAxiomFoundation/axiom-corpus-b1-full \
UV_CACHE_DIR=/tmp/uv-cache \
uv run axiom-encode validate --skip-reviewers \
  /Users/maxghenis/TheAxiomFoundation/_b1wt/rulespec-us/us/policies/cbp/us-tariff-schedule/generated/ch72.yaml
```

Final output:

```text
File: /Users/maxghenis/TheAxiomFoundation/_b1wt/rulespec-us/us/policies/cbp/us-tariff-schedule/generated/ch72.yaml
CI: ✓
Result: ✓ PASSED
```

The command covers the pinned-engine compile, the 97-case generated companion
oracle, CI/static policy checks, and proof/corpus grounding. Its verbatim output
for the final bytes is in `validate-ch72-final.log`.

The first run is retained in `validate-ch72.log`. It exposed an
upstream-placement conflict with witness-owned instance rules. Selective symbol
imports are unavailable in the pinned engine (a fragment import resolves the
whole witness, including its three legacy line modules), so generated copies
now serialize their unchanged effective windows with RuleSpec's schema aliases
`from`/`to`. Formula strings, input identifiers, dates, proof atoms, and engine
results remain identical. A complete placement scan then reported zero issues.

Repository checks also passed:

```sh
python3 -m pytest tests/test_repository_layout.py tests/test_program_specs.py -q
```

Result: all 12 collected tests passed.
