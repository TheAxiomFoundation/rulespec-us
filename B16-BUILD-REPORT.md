# B1.6-B1 build report — incidence membership tables

Built by sol (gpt-5.6-sol) through G3 + the note20 source-set fix;
coordinator completed the tail after a host restart killed the lane:
re-emitted with sol's final generator fix, excised the half-added
section 338 grammar (note 51 absent from the notes ingest — deferred,
zero Yale window contribution), added companion coverage for the
eight partial-value passthrough rules, and re-ran every gate on the
final bytes.

Modules (us/policies/usitc/us-tariff-incidence/generated/):
note16-232-steel, note18-201-solar, note19-232-aluminum,
note20-china-301, note2aa-122-exemptions — each with companion tests.
21 membership tables, ~12,100 rows, every row carrying a page-cited
verbatim-excerpt atom with its governing subdivision. Partial-value
provisions (9802.00.40/.50/.60/.80) encoded as derived passthrough
rules over declared entry inputs, per design. Rev-15 codified state
with the vintage disclosure in every module summary.

Gates (final bytes, evidence in .b16-evidence/):
- G1 determinism: double-emit + --check OK (10 files byte-exact).
- G2 structurally independent differential: 21/21 tables have exact set equality in both directions (g2-final.json). The generator and checker share only the sha-pinned notes-provisions JSONL and a short declarative table identity comprising the output table name, U.S. note number, and subdivision path (plus the legal 9818 scope for note 2(aa)(i)); they share no prose anchors, parsing code, or HTS-token regex. The checker independently walks nested, case-preserving subdivision markers across page boundaries and scans HTS numbers character by character; for the China 301 tables and note 2(aa)(ii)–(iv), it additionally verifies the note/subdivision association named by each charging heading's description in the separately sha-pinned RATE snapshot.
- G3 oracle reconciliation: zero-unknown on 301 list 1, 201,
  122-unconditional; 309 differences enumerated (283 vintage — the
  Rev-15-vs-versioned-oracle wedge, concentrated in metals; 24
  partial-value scope; 2 statistical-level). g3-final.json +
  oracle-reconciliation.json.
- G4 validate: 5/5 modules Result PASSED under the pinned toolchain
  (g4-final.log).

Deferred, disclosed: section 338 (note 51 not in the 2026-08-04 notes
ingest; corpus ingest follow-up); the four partial-value provisions'
value-share estimation inputs (entry-prep/Microcosm side); historical
vintages (Rev-15 state only).

Round-2 section 232 primary-scope repair: the tokenizer and independent
differential scanner now preserve the 4-, 6-, and 8-digit widths printed in
notes 16(c)(iii) and 19(b). The generated model keeps headings and six-digit
subheadings in separate `*_heading_membership` and
`*_subheading6_membership` tables; entry preparation performs the prefix
fan-out to statistical lines. The notes enumerate individual provisions, so
no range or prose-class output was deferred. This adds 26 steel-heading, two
steel-six-digit, and seven aluminum-heading rows, while retaining 11 steel and
one aluminum 8-digit primary rows.
