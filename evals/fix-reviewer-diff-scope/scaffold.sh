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
**Finding status:** confirmed — src/util.js:2 declares the accumulator as `x`

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

Check: node -e "const {sum}=require('./src/util.js'); if (sum([1,2,3])!==6) process.exit(1)"

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
**Finding status:** confirmed — src/util.js:8 divides by values.length with no empty guard

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

Check: node -e "const {average}=require('./src/util.js'); if (average([])!==null || average([2,4])!==3) process.exit(1)"

## Scope
**In scope:** the empty-input guard inside `average`.
**Out of scope:** everything else in the file — `sum`, exports, formatting.

## Directive citations
None — no policy citation needed.
EOF
cat > package.json <<'EOF'
{ "name": "eval-fixture", "private": true, "scripts": { "test": "node test.js" } }
EOF
cat > test.js <<'EOF'
const { sum } = require('./src/util.js');
if (sum([1, 2, 3]) !== 6) { console.error('sum broken'); process.exit(1); }
console.log('ok');
EOF
git add -A
git commit -qm "init"
