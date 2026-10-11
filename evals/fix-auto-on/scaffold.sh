#!/usr/bin/env bash
# Scratch repo with one plan item and fix.model_invocation: true: a natural-language
# "apply the fixes" runs the fix workflow. Per-item commits are off so the case does not
# need git (blocked in the macOS eval sandbox).
set -euo pipefail
git init -q -b main .
git config user.email eval@example.com
git config user.name "comb eval"
mkdir -p src plans/plan-for-eval .claude
cat > src/util.js <<'EOF'
function sum(values) {
  let x = 0;
  for (const v of values) x += v;
  return x;
}

module.exports = { sum };
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
**Out of scope:** everything else in the file.

## Directive citations
None — no policy citation needed.
EOF
cat > .claude/comb.config.json <<'EOF2'
{
  "fix": { "model_invocation": true, "commit_per_item": false }
}
EOF2
git add -A
git commit -qm "init"
