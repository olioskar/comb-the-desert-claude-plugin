#!/usr/bin/env bash
# Scratch repo with two plan items that touch the same file.
# Regression target: the fix reviewer must diff `git diff HEAD`, never HEAD~1 —
# with per-item commits, HEAD~1 pulls the previous item's commit into item 2's
# review and produces a false scope-violation FAIL.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.com
git config user.name "comb eval"
mkdir -p src plans/plan-for-eval
cat > src/util.js <<'EOF'
function sum(values) {
  let x = 0;
  for (const v of values) x += v;
  return x;
}

function average(values) {
  return sum(values) / values.length;
}

module.exports = { sum, average };
EOF
cat > plans/plan-for-eval/M1-rename-sum-accumulator.md <<'EOF'
# M1 — rename sum accumulator for clarity

**Severity:** Medium
**File(s):** src/util.js:1-5
**Specialty:** code-reviewer

---

## What
Rename the variable `x` in `sum` to `total`.

## Why
`x` says nothing; `total` states the accumulator's role.

## Where
`src/util.js`, function `sum` (lines 1-5).

## How
Before:
```js
function sum(values) {
  let x = 0;
  for (const v of values) x += v;
  return x;
}
```
After:
```js
function sum(values) {
  let total = 0;
  for (const v of values) total += v;
  return total;
}
```

## Expected Outcome
`sum` behaves identically; the accumulator is named `total`.

## Scope
**In scope:** the accumulator variable name inside `sum`.
**Out of scope:** everything else in the file — `average`, exports, formatting.

## Directive citations
None — no policy citation needed.
EOF
cat > plans/plan-for-eval/M2-guard-average-empty-input.md <<'EOF'
# M2 — guard average against empty input

**Severity:** Medium
**File(s):** src/util.js:7-9
**Specialty:** code-reviewer

---

## What
Return `null` from `average` when `values` is empty, instead of `NaN`.

## Why
`sum([]) / 0` is `NaN`, which callers silently propagate.

## Where
`src/util.js`, function `average`.

## How
Before:
```js
function average(values) {
  return sum(values) / values.length;
}
```
After:
```js
function average(values) {
  if (values.length === 0) return null;
  return sum(values) / values.length;
}
```

## Expected Outcome
`average([])` returns `null`; non-empty input is unchanged.

## Scope
**In scope:** the empty-input guard inside `average`.
**Out of scope:** everything else in the file — `sum`, exports, formatting.

## Directive citations
None — no policy citation needed.
EOF
git add -A
git commit -qm "init"
