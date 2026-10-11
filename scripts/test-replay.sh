#!/usr/bin/env bash
# Fixture test for scripts/replay-graders.py: the real graders of two eval cases, replayed
# against synthetic kept-run directories (one passing and one failing fix run, one passing
# non-code run). Deterministic and offline; run by scripts/check-contract.sh.
set -uo pipefail
cd "$(dirname "$0")/.."
F=scripts/fixtures/replay
fail=0
expect() { # <want-exit> <case> <run-dir> <want-substring>...
  local want=$1 case=$2 run=$3; shift 3
  out=$(python3 -I scripts/replay-graders.py "evals/$case" "$F/$run" 2>&1); got=$?
  [ "$got" -eq "$want" ] || { echo "FAIL: $case vs $run exited $got, want $want"; echo "$out"; fail=1; }
  for s in "$@"; do
    grep -qF -- "$s" <<<"$out" || { echo "FAIL: $case vs $run: missing \"$s\""; echo "$out"; fail=1; }
  done
}
expect 0 fix-reviewer-diff-scope fix-pass \
  "✓ two-commits: Bash called 2x" "✓ reviewer-diffs-head: Agent called 2x" \
  "✓ reviewer-never-head-tilde: Agent called 0x" "✓ m1-applied" "✓ m2-applied" \
  "✓ verification-before-commit: Bash called 2x" "✓ head-recorded: Bash called 4x" "✓ tree-checked: Bash called 2x" \
  "replay: fix-reviewer-diff-scope — OK"
expect 1 fix-reviewer-diff-scope fix-fail \
  "✗ two-commits: Bash called 0x" "✗ reviewer-never-head-tilde: Agent called 1x" "✗ m1-applied" \
  "✗ verification-before-commit: Bash called 0x" "✗ head-recorded: Bash called 0x" "✗ tree-checked: Bash called 1x" \
  "replay: fix-reviewer-diff-scope — FAIL"
expect 0 noncode-shortcircuit noncode-pass \
  "✓ announces-shortcircuit" "✓ design-doc-untouched: Write called 0x" "✓ no-edits: Edit called 0x" \
  "✓ no-plan-files: docs/combs/plans/*/*.md absent as expected"
[ "$fail" -eq 0 ] && echo "test-replay: OK"
exit "$fail"
