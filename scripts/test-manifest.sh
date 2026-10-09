#!/usr/bin/env bash
# Fixture test for scripts/manifest.py. Builds a temporary git repo, creates the
# files the fixture manifests cite, commits, rewrites the fixtures' base-commit
# token, runs every command, and diffs the normalised output against
# scripts/fixtures/expected/. Run with --update to regenerate the expected files.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)
S="$ROOT/scripts/manifest.py"
F="$ROOT/scripts/fixtures"
E="$F/expected"
UPDATE=0; [ "${1:-}" = "--update" ] && UPDATE=1
T=$(mktemp -d "${TMPDIR:-/tmp}/comb-manifest-test.XXXXXX")
trap 'rm -rf "$T"' EXIT
OUT="$T/out"; mkdir -p "$OUT" "$E"

cd "$T"
git init -q -b main . && git config user.email test@example.com && git config user.name "comb test"
while read -r f; do mkdir -p "$(dirname "$f")"; echo "// $f" > "$f"; done < "$F/cited-files.txt"
git add -A && git commit -qm base
SHA=$(git rev-parse --short=8 HEAD)
# the manifest's base-commit rule needs a hex token containing a letter; an
# all-digit short SHA (about 2% of commits) would pick an older stamp instead
while ! echo "$SHA" | grep -q '[a-f]'; do
  echo "// retry" >> src/setupTests.ts && git commit -qam base-retry && SHA=$(git rev-parse --short=8 HEAD)
done
mkdir -p docs/combs
sed "s/BASECOMMIT0/$SHA/" "$F/curated.md" > docs/combs/PATTERNS.md
sed "s/BASECOMMIT0/$SHA/" "$F/template.md" > docs/combs/TEMPLATE.md
echo "// changed" >> src/pages/entity/contact/ContactsPage.tsx
git commit -qam change

norm() { sed -E -e "s/$SHA/BASECOMMIT0/g" -e 's/[a-z]+-[0-9]{9,}-[0-9a-f]{4}/RUN/g' -e 's/^(\*\*Shaved:\*\*) [0-9]{4}-[0-9]{2}-[0-9]{2}/\1 DATE/' -e "s#$T#TMP#g" ; }

run_excerpt() { # name skill manifest touched
  python3 -I "$S" excerpt --skill "$2" --manifest "$3" --touched-from "$F/$4" > "$OUT/$1.log" 2>&1
  ex=$(sed -n 's/^excerpt: //p' "$OUT/$1.log")
  norm < "$OUT/$1.log" | grep -v '^excerpt: ' > "$OUT/$1.out"
  echo "--- excerpt body ---" >> "$OUT/$1.out"
  norm < "$ex" >> "$OUT/$1.out"
}
run_excerpt curated-page   review docs/combs/PATTERNS.md curated.page.touched
run_excerpt curated-pdf    review docs/combs/PATTERNS.md curated.pdf.touched
run_excerpt curated-root   review docs/combs/PATTERNS.md curated.root.touched
run_excerpt curated-stale  review docs/combs/PATTERNS.md curated.stale.touched
run_excerpt curated-test   review docs/combs/PATTERNS.md curated.test.touched
run_excerpt curated-prefix review docs/combs/PATTERNS.md curated.prefixed.touched
run_excerpt template-web   review docs/combs/TEMPLATE.md template.web.touched
run_excerpt template-types plan   docs/combs/TEMPLATE.md template.types.touched
run_excerpt template-report plan  docs/combs/TEMPLATE.md template.report.touched
run_excerpt template-instr fix    docs/combs/TEMPLATE.md template.instruction.touched

# git must not see .comb
if [ -n "$(git status --porcelain -- .comb)" ]; then echo "FAIL: .comb/ visible to git status"; exit 1; fi

python3 -I "$S" index --manifest docs/combs/PATTERNS.md > "$OUT/index.log" 2>&1
IDX=$(sed -n 's/^index: //p' "$OUT/index.log")
norm < "$OUT/index.log" | grep -v '^index: ' > "$OUT/index.out"

set +e
python3 -I "$S" verify --manifest docs/combs/PATTERNS.md --index "$IDX" --edits "$F/edits-pass.json" --out "$T/pass.json" 2>&1 | norm > "$OUT/verify-pass.out"
echo "exit=${PIPESTATUS[0]}" >> "$OUT/verify-pass.out"
set -e
for f in "$F"/edits-fail-*.json "$F"/edits-unusable-*.json; do
  n=$(basename "$f" .json)
  set +e
  python3 -I "$S" verify --manifest docs/combs/PATTERNS.md --index "$IDX" --edits "$f" --out "$T/$n.json" 2>&1 | norm > "$OUT/$n.out"
  echo "exit=${PIPESTATUS[0]}" >> "$OUT/$n.out"
  set -e
done
# the same restated convention may be shaved in two sections in one run (the owner keeps it)
set +e
python3 -I "$S" verify --manifest docs/combs/PATTERNS.md --index "$IDX" --edits "$F/edits-pass-two-dups.json" --out "$T/twodups.json" 2>&1 | norm > "$OUT/verify-two-dups.out"
echo "exit=${PIPESTATUS[0]}" >> "$OUT/verify-two-dups.out"
set -e
# stdin touched text
git diff --name-only HEAD~1 HEAD | python3 -I "$S" excerpt --skill review --manifest docs/combs/PATTERNS.md --touched-from - 2>&1 | norm | grep -v '^excerpt: ' > "$OUT/curated-stdin.out"
# a good file beside an unusable one still yields the good file's passing set
set +e
python3 -I "$S" verify --manifest docs/combs/PATTERNS.md --index "$IDX" --edits "$F/edits-pass.json" "$F/edits-unusable-broken.json" --out "$T/mixed.json" 2>&1 | norm > "$OUT/verify-mixed.out"
echo "exit=${PIPESTATUS[0]}" >> "$OUT/verify-mixed.out"
set -e
# touched text may be a directory of instruction files
mkdir -p "$T/plan" && cp "$F/template.instruction.touched" "$T/plan/M1-x.md" && cp "$F/template.report.touched" "$T/plan/M2-y.md"
python3 -I "$S" excerpt --skill fix --manifest docs/combs/TEMPLATE.md --touched-from "$T/plan" 2>&1 | norm | grep -v '^excerpt: ' > "$OUT/template-dir.out"
python3 -I "$S" gate --manifest docs/combs/PATTERNS.md --edits "$T/pass.json" > "$OUT/gate.out" 2>&1
python3 -I "$S" gate --manifest docs/combs/PATTERNS.md --edits "$T/pass.json" --show "14. Testing conventions" > "$OUT/gate-show.out" 2>&1
python3 -I "$S" filter --edits "$T/pass.json" --skip-class fixed-drift --out "$T/filtered.json" 2>&1 | norm > "$OUT/filter.out"
cp docs/combs/PATTERNS.md "$T/applied.md"
set +e
python3 -I "$S" apply --manifest "$T/applied.md" --index "$IDX" --edits "$T/pass.json" --stamp 2>&1 | norm > "$OUT/apply.out"
echo "exit=${PIPESTATUS[0]}" >> "$OUT/apply.out"
set -e
norm < "$T/applied.md" > "$OUT/applied.md"
# the stamp records the file's true final size
stamped=$(sed -n 's/^\*\*Shaved:\*\* .* → \([0-9]*\) bytes)$/\1/p' "$T/applied.md"); actual=$(wc -c < "$T/applied.md" | tr -d ' ')
[ "$stamped" = "$actual" ] && echo "stamp-size=correct" > "$OUT/stamp-size.out" || echo "stamp-size=WRONG ($stamped vs $actual)" > "$OUT/stamp-size.out"
# second shave on the already-shaved file: fresh index, a fenced edit that passes alone, stamp replaced
python3 -I "$S" index --manifest "$T/applied.md" > "$OUT/index2.log" 2>&1
IDX2=$(sed -n 's/^index: //p' "$OUT/index2.log")
set +e
python3 -I "$S" verify --manifest "$T/applied.md" --index "$IDX2" --edits "$F/edits-pass-fenced.json" --out "$T/pass2.json" 2>&1 | norm > "$OUT/verify-fenced.out"
echo "exit=${PIPESTATUS[0]}" >> "$OUT/verify-fenced.out"
python3 -I "$S" apply --manifest "$T/applied.md" --index "$IDX2" --edits "$T/pass2.json" --stamp 2>&1 | norm > "$OUT/apply2.out"
set -e
{ grep -c '^\*\*Shaved:\*\*' "$T/applied.md" || true; } | sed 's/^/shaved-lines=/' > "$OUT/restamp.out"
RUN2=$(sed -n 's/^run: //p' "$OUT/index2.log"); python3 -I "$S" clean --run "$RUN2" > /dev/null
RUN=$(sed -n 's/^run: //p' "$OUT/index.log")
python3 -I "$S" clean --run "$RUN" | norm > "$OUT/clean.out"
{ ls .comb/excerpts | grep -c "$RUN" || true; } | sed 's/^/leftover=/' >> "$OUT/clean.out"

# measured size for the changelog
ex=$(sed -n 's/^excerpt: //p' "$OUT/curated-page.log"); echo "curated page-diff excerpt: $(wc -c < "$ex" | tr -d ' ') bytes (manifest $(wc -c < docs/combs/PATTERNS.md | tr -d ' ') bytes)"

fail=0
for o in "$OUT"/*.out "$OUT"/applied.md; do
  case "$(basename "$o")" in *.log) continue;; esac
  n=$(basename "$o")
  if [ "$UPDATE" = 1 ]; then cp "$o" "$E/$n"; continue; fi
  if [ ! -f "$E/$n" ]; then echo "FAIL: no expected file for $n"; fail=1; continue; fi
  if ! diff -u "$E/$n" "$o" > "$T/diff.txt"; then echo "FAIL: $n differs"; cat "$T/diff.txt"; fail=1; fi
done
[ "$UPDATE" = 1 ] && { echo "expected files updated in scripts/fixtures/expected/"; exit 0; }
[ "$fail" = 0 ] && echo "test-manifest: OK ($(ls "$E" | wc -l | tr -d ' ') expectations)"
exit $fail
