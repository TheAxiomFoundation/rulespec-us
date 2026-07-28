VERDICT: REQUEST-CHANGES

# PR 1003 round-4 review

## Reviewed state

- PR 1003 live head:
  `50b6ec228dba8279526bd692de85af4659557c78`
- PR 1003 live base:
  `836e74b578a35fdfb30bf828e89510cd894e8300`
- Previously reviewed round-3 head:
  `3327de19395465dee736061b2d4c33108416d261`
- Post-round-3 range:
  `3327de19395465dee736061b2d4c33108416d261..50b6ec228dba8279526bd692de85af4659557c78`
- PR 1004 residual-check head:
  `e25a31417997e27b50ef9d2315d67b9a9036f7b5`

I read the committed `round3-1003-VERDICT.md` and its progress record in
full. `rereview-1003-VERDICT.md` is not present in the repository, reachable
refs, or accessible prior scratchpad locations. I re-fetched PR 1003 from
GitHub after the audit; the live head and body remained the state above.

## Blocking findings

### 1. The live PR 1003 body still does not match the current head

The original Additional-Medicare bullet still claims a locally authored SECA
leg whose section 1401(b)(2)(A)/(B) proof atoms quote the pinned record's full
cross-reference sentence, and it still presents the `$346.725`
coordinated-threshold result. At the current head:

- the unsupported section 1401(b)(2)(B) coordination excerpt is gone;
- the relevant proof atoms are imports, not that quoted statutory sentence;
- `$346.725` survives only in a restoration comment; and
- the positive-SE companion's public SE and combined outputs are both zero.

The appended Round-3 update correctly withdraws the excerpt and describes the
fail-closed implementation, but it does not retract or replace the conflicting
earlier claim.

The live Oracle-evidence paragraph is also false at this head. It says the
Additional-Medicare report re-runs against this head's input surface and that
all six domestic values are unchanged. The committed oracle reports instead
remain historical:

- NIIT and SECA report rulespec SHA
  `f0eaa0cf657a40edfcb5491fde243cd051ec67af` and omit their later required
  attestations.
- Additional Medicare reports rulespec SHA
  `8218c7baff9330cf1eb707bb7d2df87bfb4abcfc`, omits the current foreign-system
  attestation, and reports `$346.725` for the positive-SE case that the current
  head intentionally returns as zero.

This leaves the round-3 stale-oracle/body residual unresolved. Rewrite the
original body sections instead of appending another qualification. The body
must describe the current fail-closed surface and label the old oracle reports
as historical, non-current-head evidence.

### 2. The round-3 commits leave their committed progress record stale

`bulk/fix3-1003/PROGRESS.md` was accurate at `bda6a9b26`, but commit
`50b6ec228` refreshed and re-signed all three surtax manifests without updating
that record. At the current head it still:

- says the apply manifest is intentionally stale and only dry-run signing was
  authorized (lines 9-10);
- expects a manifest-sync failure (lines 48-50);
- says there was no NIIT or ordinary-SECA delta (lines 53-54); and
- asks a keyholder to refresh the manifests (lines 58-59).

The current manifest-sync test passes, and the NIIT, SECA, and Additional
Medicare manifests all changed in the final re-sign. This violates the
maintained `state/done/next` requirement and is a new committed audit defect in
the round-3 range. Update the record to the actual final state.

### 3. The foreign-attestation companion no longer isolates that guard

`amt-foreign-system-boundary-fails-closed` now supplies both:

- `no_foreign_system_exclusive_se_income: false`; and
- positive imported federal self-employment income (`138525`).

The newly added zero-SE conjunct therefore makes the domain false even if the
foreign-attestation conjunct is deleted. The named case would still pass while
the guard it purports to prove is broken. Add a zero-SE,
false-foreign-attestation companion, preferably with taxable wages, that
asserts the wage leg remains observable while the SE and combined outputs fail
closed.

## Previously identified residuals

### PR 1004: resolved at its current head

At `e25a31417997e27b50ef9d2315d67b9a9036f7b5`, the QBI pipeline imports all
nine threshold, range-end, and width parameters from the merged Rev. Proc.
2025-32 module. The local filing-status judgment admits only statuses `0..4`;
the final output fails closed otherwise. The status-9 companion asserts
`not_holds` and a zero deduction and passes. Its focused gates pass:
validation `3/3`, proof atoms `43/43`, and companions `40/40`.

### PR 1003 product/provenance residual: resolved in code

The former corrected `3101(b)(2)` excerpt has no occurrence in the current
module or the pinned corpus. The pin is axiom-corpus
`710a326366bd233c40d64ca89b62a07082f13ce3`; both pinned section-1401 records
have body SHA-256
`6112dcd4fbd396d87c489634d4a0e82c4ac27c2ae67dd8aad65a8ec31036ca6d`.
The operative pinned sentence is, verbatim:

> The amounts under clause (i), (ii), or (iii) (whichever is applicable) of subparagraph (A) shall be reduced (but not below zero) by the amount of wages taken into account in determining the tax imposed under section 3121(b)(2) with respect to the taxpayer.

The current module's scrivener's-error account matches that pinned text
verbatim: the record prints `3121(b)(2)`, not `3101(b)(2)`. This is also the
text shown in the [official section 1401 record](https://uscode.house.gov/view.xhtml?edition=prelim&num=0&req=granuleid%3AUSC-prelim-title26-section1401).
[Treasury Decision 9645](https://www.irs.gov/irb/2013-51_IRB) and the current
[Form 8959 instructions](https://www.irs.gov/instructions/i8959) apply the
coordination using wages subject to Additional Medicare Tax under section
`3101(b)(2)`. From those primary sources, I infer that the module's
scrivener's-error explanation is accurate.

The current code correctly restricts the Additional-Medicare SE domain to both
an affirmative section-1401(c) attestation and zero imported SE income. The
coordination helper, public SE leg, and combined output return zero outside
that domain; the independently valid imported wage leg remains observable.
All six SE-bearing companions assert zero public SE and combined outputs, and
all eight zero-SE companions preserve the wage-only result.

## Focused gates at PR 1003 head

Using the pinned encoder `3869d66d009f52258be35901edbef370e65a399c`,
rules engine `ffd8213271947b0189a9dd61a055c1e0e78908a0`, and corpus
`710a326366bd233c40d64ca89b62a07082f13ce3`:

| Gate | Result |
| --- | --- |
| Canonical validation | `3/3 PASS` |
| Proof validation | `47/47 PASS` (NIIT 10, SECA 19, AMT 18) |
| Companion execution | `42/42 PASS` |
| Encoding-manifest pytest | `3 passed`, one existing warning |
| Current and per-commit diff checks | PASS |
| Current file/output hashes and manifest supersession links | PASS |

The subject PR worktree remained clean. The five post-round-3 commits introduce
no executable or manifest defect, but findings 2 and 3 are new documentation
and test-coverage defects. Together with the unresolved live-body/oracle
finding, they require changes before approval.
