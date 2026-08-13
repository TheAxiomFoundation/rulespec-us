#!/usr/bin/env bash
set -u

repo=/Users/maxghenis/TheAxiomFoundation/_b1wt/rulespec-us
encode=/Users/maxghenis/TheAxiomFoundation/axiom-encode-perf
evidence="$repo/.b13-pilot-evidence/rollout"
composition_dir="$repo/us/policies/cbp/us-tariff-schedule/generated"

files=()
while IFS= read -r file; do
  files[${#files[@]}]="$file"
done < <(
  find "$composition_dir" -maxdepth 2 -type f \
    -name 'ch*.yaml' ! -name '*.test.yaml' -print | LC_ALL=C sort
)
if [[ ${#files[@]} -ne 100 ]]; then
  printf 'expected 100 composition files, found %s\n' "${#files[@]}" >&2
  exit 2
fi

cd "$encode" || exit 2
set +e
/usr/bin/time -p -o "$evidence/validation-total-time.txt" \
  env \
    AXIOM_CORPUS_REPO="$HOME/TheAxiomFoundation/axiom-corpus-b1-full" \
    UV_CACHE_DIR=/tmp/uv-cache \
  uv run axiom-encode validate --skip-reviewers --json "${files[@]}" \
  >"$evidence/validation-results.json" \
  2>"$evidence/validation-stderr.log"
validate_rc=$?
set -e

printf '%s\n' "$validate_rc" >"$evidence/validation-exit-code.txt"
exit "$validate_rc"
