VERDICT: REQUEST-CHANGES

# PR 1003 round-3 review

Reviewed live head `3327de19395465dee736061b2d4c33108416d261`
against base `836e74b578a35fdfb30bf828e89510cd894e8300`.
The final GitHub re-fetch showed the same head and the same rewritten body.

The branch was rebased after round 2. `git range-diff` maps the reviewed
round-2 head `d486f0997c62e1d3f1fbc382b0675b853bbcc144` to
`88e9b55c37b15c2f04d2142d45da374c041924fc`, so the exact round-2-only
range reviewed here is:

`88e9b55c37b15c2f04d2142d45da374c041924fc..3327de19395465dee736061b2d4c33108416d261`

| Requested check | Result |
| --- | --- |
| Round-2 residuals | §1401(c) guard and floor fixtures resolved; provenance blocker unresolved |
| Live body vs. head | Fails: provenance and NIIT/SECA oracle claims do not match head evidence |
| Focused gates | Pass |
| CI at head | All three workflows pass |
| Round-2-only regression review | Fails: round-2 commits introduced unsupported proof excerpts |

## Blocking findings

### 1. The §1401(b)(2)(B) provenance claim remains unsupported

The current toolchain pins corpus
`710a326366bd233c40d64ca89b62a07082f13ce3`. At that exact pin, an
exact search finds zero occurrences of the corrected sentence now quoted
by the proof atoms:

> The amounts under clause ... wages (as defined in section 3121(a))
> taken into account in determining the tax imposed by section
> 3101(b)(2) ...

The pinned record instead retains the defective wording that refers to
“wages taken into account” and tax imposed under `3121(b)(2)`, while its
source artifact is headed `26 USC 45A: Indian employment credit`.

Nevertheless,
`us/policies/income_tax/additional_medicare_tax_pipeline.yaml:118-136`
claims the pinned record supplies the decisive sentence and uses the
absent corrected text as a proof excerpt. The same unsupported excerpt
appears at lines 266-267, and the input contract repeats it at lines
423-425. The live PR body likewise says the proof atoms quote the pinned
record's statutory text and characterizes only `source_url` metadata as
broken. That is false: the pinned record text itself does not support the
proof atoms.

Commits `799b5b79` and `6bd4c284` introduced these corrected excerpts in
the round-2-only range without introducing or pinning a corpus record
that contains them. This is a new defect in the round-2 delta as well as
an unresolved round-2 blocker.

The focused proof gate passing does not cure the problem: the validator
accepts the citation-path/proof structure but does not establish that
the excerpt occurs in the pinned corpus text. Resolve this by pinning and
citing a corpus artifact that actually contains the asserted sentence
(or by using a supported fail-closed boundary), then make the policy
comments, proof atoms, contract, and PR body match that evidence.

### 2. The live NIIT/SECA oracle claim is stale for the head input surface

The body says it describes head `3327de19` and states, without a stale
caveat, that the NIIT and SECA campaign grids match PolicyEngine-US
1.767.3 at 6/6.

The committed NIIT and SECA reports are both from rulespec SHA
`f0eaa0cf657a40edfcb5491fde243cd051ec67af`, not this head. More
importantly, all cases in those reports omit inputs newly required by the
head:

- NIIT omits
  `niit_income_categories_are_disjoint_post_classification_amounts`.
- SECA omits `no_foreign_system_exclusive_se_income`.

Those are now required fail-closed attestations. The old reports include
positive NIIT and SECA results, so they cannot be replayed against the
current head without adding the new inputs; they are not evidence of 6/6
at the reviewed input surface. The body acknowledges staleness only for
the Additional Medicare report. Re-run and commit current-head reports,
or explicitly characterize the NIIT/SECA results as historical and not
current-head evidence.

## Round-2 residual probes

The other two requested residuals are genuinely resolved:

- **Ordinary SECA §1401(c) guard:** the domain judgment at
  `self_employment_tax_pipeline.yaml:205-222` consumes
  `no_foreign_system_exclusive_se_income`, and all three public tax
  outputs fail closed at lines 286-395. The
  `seca-foreign-system-boundary-fails-closed` counterexample keeps
  pre-relief income at `46175` while OASDI, HI, and total tax are each
  zero.
- **Operative floor branch:** `seca-floor-below` uses gross `433` to
  produce `399.8755`, asserting the imported §1402(b)(2) output is zero;
  `seca-floor-above` uses gross `434` to produce `400.799`, asserting the
  imported output remains `400.799`. These are valid lower/upper
  straddles of the imported `$400` branch. The fixture explains why exact
  equality cannot be reached through a finite-decimal gross input and
  the `0.9235` factor.

The focused SECA companion suite, including both probes, passes 13/13.

## Focused gates

All focused commands were rerun from the exact head against an isolated
checkout of the current corpus pin:

- `validate --skip-reviewers`: 3/3 roots passed.
- `proof-validate`: 46/46 atoms passed (NIIT 10, SECA 19, Additional
  Medicare 17).
- Pinned-engine companions: 42/42 cases passed (NIIT 15, SECA 13,
  Additional Medicare 14).

The companion suite also passed 42/42 with the engine root used in the
round-2 verdict. Both the full PR diff and the exact round-2-only diff
pass `git diff --check`.

## CI at the reviewed head

All GitHub Actions runs associated with head `3327de19` are terminal and
successful:

- Repository Checks `30124844097` / run 3025: success.
- Source staleness and reverse index `30124843757` / run 1749: success.
- `program-artifacts` `30124843759` / run 1248: success; 33/33 program
  specs built.

## Round-2-only diff conclusion

The 14-commit range has a seven-file net delta. Apart from the unsupported
proof excerpts described above, focused inspection found the new guard,
floor fixtures, refreshed imports, manifests, supersession metadata, and
sorted duplicate-free oracle ledger internally consistent. No
toolchain, workflow, or CODEOWNERS change was introduced.

Because the provenance blocker is still unresolved, the live body
misstates both that provenance and the current-head oracle evidence, and
the round-2 range introduced unsupported proof excerpts, this head is not
approvable.
