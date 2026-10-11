#!/usr/bin/env bash
# Scratch repo with one plan item and NO fix.model_invocation flag: a natural-language
# "apply the fixes" must be refused with the observed value and the /comb:fix command.
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
**Out of scope:** everything else in the file.

## Directive citations
None — no policy citation needed.
EOF
git add -A
git commit -qm "init"
