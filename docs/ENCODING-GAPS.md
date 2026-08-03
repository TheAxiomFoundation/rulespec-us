# Encoding gaps

This file records validation gaps that cannot be repaired honestly from the
source text already available to this repository. It does not cover missing
corpus material: modules blocked by source recovery are listed separately in
`data/coverage/awaiting-source-recovery.json`.

## Massachusetts weekly and biweekly conversion factors

`us-ma/regulations/106-cmr/364/340/block-1.yaml` faithfully transcribes the
verbatim source phrases “multiplying weekly amounts by 4.333” and “biweekly
amounts by 2.167.” The numeric-grounding check nevertheless reports both
decimal literals as absent. Narrowing the citations or changing the literals
would misstate the provision, so the existing active validation waiver is
retained with its real validator fingerprint. The waiver is not a substitute
for missing source text and should be removed when decimal grounding accepts
these verbatim values.

No active waiver in `known-validation-gaps.yaml` uses a placeholder
fingerprint or placeholder metadata.
