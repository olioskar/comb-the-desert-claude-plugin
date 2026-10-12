#!/usr/bin/env bash
# Fixture test for scripts/comb.py. Runs every subcommand against the fixture
# plugin root, home, and project under scripts/fixtures/comb/ from a temporary
# cwd, normalises paths, and diffs the output against scripts/fixtures/comb/expected/.
# Run with --update to regenerate the expected files.
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)
S="$ROOT/scripts/comb.py"
F="$ROOT/scripts/fixtures/comb"
E="$F/expected"
UPDATE=0; [ "${1:-}" = "--update" ] && UPDATE=1
T=$(mktemp -d "${TMPDIR:-/tmp}/comb-test.XXXXXX")
trap 'rm -rf "$T"' EXIT
OUT="$T/out"; mkdir -p "$OUT" "$E"
TR=$(cd "$T" && pwd -P)   # macOS: $TMPDIR is a symlink into /private
TL=$(cd "$T" && pwd)      # logical path (no doubled slashes from $TMPDIR)
cd "$T"

norm() { sed -E -e 's/[a-z]+-[0-9]{9,}-[0-9a-f]{4}/RUN/g' -e "s#$TR#TMP#g" -e "s#$TL#TMP#g" -e "s#$T#TMP#g" -e "s#$F#FIX#g" -e "s#$ROOT#PLUGIN#g" ; }

P="$F/plugin"; H="$F/home"; R="$F/project"
C=(--plugin-root "$P" --home "$H" --project-root "$R")
run() { name=$1; shift; python3 -I "$S" "$@" 2>&1 | norm > "$OUT/$name.out"; echo "exit=${PIPESTATUS[0]}" >> "$OUT/$name.out"; }

# config: three-layer merge, null deletes, schema warning, bad JSON
run config               config "${C[@]}"
run config-badjson       config --plugin-root "$P" --home "$H" --project-root "$F/badjson"
# resolve: lane model, role model override, coercion, effort, native rule, errors
run resolve-review       resolve --role code-reviewer --lane review "${C[@]}"
run resolve-plan-ours    resolve --role ours --lane plan "${C[@]}"
run resolve-trivial      resolve --role implementer --lane fix.implementer_trivial "${C[@]}"
run resolve-coerce       resolve --role test-auditor --lane review --coerce the_desert "${C[@]}"
run resolve-coerce-plain resolve --role code-reviewer --lane plan --coerce the_desert "${C[@]}"
run resolve-deleted      resolve --role simplifier --lane review "${C[@]}"
run resolve-badlane      resolve --role code-reviewer --lane nope "${C[@]}"
run resolve-badeffort    resolve --role fast --lane plan "${C[@]}"
# directives: listing, primary matching, user directives, plugin defaults off
run directives-none      directives "${C[@]}"
run directives-simpl     directives --brief "keep it simpl" "${C[@]}"
run directives-two       directives --brief "Scope and TEST coverage" "${C[@]}"
run directives-user      directives --brief "velocity" "${C[@]}"
run directives-noplugin  directives --plugin-root "$P" --home "$H" --project-root "$F/noplugin"
run directives-short-positive directives --brief "the api" --plugin-root "$P" --home "$H" --project-root "$F/noplugin"
# brief: the per-run dispatch block, written under the temp cwd's .comb/excerpts
touch ex.md PATTERNS.md
run brief-native-review  brief --skill review --role code-reviewer --run review-1-aaaa --brief "scope and simplicity" --excerpt "$T/ex.md" --manifest "$T/PATTERNS.md" "${C[@]}"
run brief-foreign-plan   brief --skill plan --role ours --run plan-1-bbbb --brief "keep it simpl" --manifest "$T/PATTERNS.md" "${C[@]}"
run brief-fix-impl       brief --skill fix --role implementer --run fix-1-cccc "${C[@]}"
run brief-fix-reviewer   brief --skill fix --role test-auditor --run fix-1-cccc --brief "tests" "${C[@]}"
run brief-mint           brief --skill review --role code-reviewer "${C[@]}"
run brief-missing-manifest brief --skill review --role code-reviewer --run review-1-dddd --manifest "$T/nope.md" "${C[@]}"
run brief-badrun         brief --skill review --role code-reviewer --run "not a stem" "${C[@]}"
run brief-excerpt-no-manifest brief --skill review --role code-reviewer --run review-1-eeee --excerpt "$T/ex.md" "${C[@]}"
# the X-item planner brief of a fix run must not overwrite the implementer brief (same run, same role, other skill)
run brief-plan-same-run  brief --skill plan --role implementer --run fix-1-cccc "${C[@]}"
# a foreign writer configured as the implementer role: authority sentence, lens, implementer intro
run brief-foreign-fix-impl brief --skill fix --role implementer --run fix-1-dddd --plugin-root "$P" --home "$H" --project-root "$F/noplugin"
# report-name: rounds are parsed from filenames, never counted; the prefix is exact
run report-pr            report-name --reviews "$R/reviews" --pr 7
run report-pr70          report-name --reviews "$R/reviews" --pr 70
run report-branch        report-name --reviews "$R/reviews" --branch "feature/foo bar"
run report-branch-main   report-name --reviews "$R/reviews" --branch main
run report-nodir         report-name --reviews "$R/no-such-dir" --pr 1
mkdir -p rvnoperm && chmod 000 rvnoperm
run report-noperm        report-name --reviews "$T/rvnoperm" --pr 1
chmod 755 rvnoperm
# batches: folder shape, write-sets, not-reproduced, disjoint batches of at most three
run batches-code         batches --folder "$R/plans/code"
run batches-revise       batches --folder "$R/plans/revise"
mkdir -p empty-folder
run batches-empty        batches --folder "$T/empty-folder"
run batches-mixed        batches --folder "$R/plans/mixed"
run batches-missing      batches --folder "$R/plans/no-such-folder"
run batches-ceiling      batches --folder "$R/plans/ceiling"
run batches-latin1       batches --folder "$R/plans/latin1"
run batches-tworevise    batches --folder "$R/plans/tworevise"
mkdir -p noperm && cp "$R/plans/code/M1-a.md" noperm/ && chmod 000 noperm/M1-a.md
run batches-noperm       batches --folder "$T/noperm"
chmod 644 noperm/M1-a.md
# findings: the fixed report template as JSON; anything else is count 0, never a traceback
run findings-code        findings --report "$R/reports/code-report.md"
run findings-noncode     findings --report "$R/reports/noncode-report.md"
run findings-prose       findings --report "$R/reports/prose.md"
run findings-missing     findings --report "$R/reports/no-such-report.md"
run findings-old         findings --report "$R/reports/old-report.md"
for b in review-1-aaaa.review.code-reviewer plan-1-bbbb.plan.ours fix-1-cccc.fix.implementer fix-1-cccc.fix.test-auditor fix-1-cccc.plan.implementer fix-1-dddd.fix.implementer; do
  if [ -f ".comb/excerpts/$b.brief.md" ]; then norm < ".comb/excerpts/$b.brief.md" > "$OUT/brief-$b.md"; else echo "MISSING .comb/excerpts/$b.brief.md" > "$OUT/brief-$b.md"; fi
done
[ -f .comb/.gitignore ] && cat .comb/.gitignore > "$OUT/brief-gitignore.out" || echo "MISSING .comb/.gitignore" > "$OUT/brief-gitignore.out"
# manifest.py clean removes a run's briefs (same stem)
python3 -I "$ROOT/scripts/manifest.py" clean --run fix-1-cccc > "$OUT/brief-clean.out" 2>&1
{ ls .comb/excerpts 2>/dev/null | grep -c fix-1-cccc || true; } >> "$OUT/brief-clean.out"

fail=0
for o in "$OUT"/*; do
  n=$(basename "$o")
  if [ "$UPDATE" = 1 ]; then cp "$o" "$E/$n"; continue; fi
  if [ ! -f "$E/$n" ]; then echo "FAIL: no expected file for $n"; fail=1; continue; fi
  if ! diff -u "$E/$n" "$o" > "$T/diff.txt"; then echo "FAIL: $n differs"; cat "$T/diff.txt"; fail=1; fi
done
[ "$UPDATE" = 1 ] && { echo "expected files updated in scripts/fixtures/comb/expected/"; exit 0; }
[ "$fail" = 0 ] && echo "test-comb: OK ($(ls "$E" | wc -l | tr -d ' ') expectations)"
exit $fail
