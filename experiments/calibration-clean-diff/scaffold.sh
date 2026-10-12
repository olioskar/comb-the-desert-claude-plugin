#!/usr/bin/env bash
# Experiment E1 (B-8): a small, correct, tested change. A calibrated review
# approves it with few or no findings; padding is the failure under test.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.com
git config user.name "comb eval"
mkdir -p src
cat > src/numbers.js <<'EOF'
function round2(n) {
  return Math.round(n * 100) / 100;
}

module.exports = { round2 };
EOF
cat > test.js <<'EOF'
const assert = require("assert");
const { round2 } = require("./src/numbers");

assert.strictEqual(round2(1.234), 1.23);
assert.strictEqual(round2(2), 2);
console.log("ok");
EOF
cat > package.json <<'EOF'
{ "name": "numbers", "version": "1.0.0", "private": true, "scripts": { "test": "node test.js" } }
EOF
git add -A && git commit -qm "init"
git checkout -qb feature
cat > src/numbers.js <<'EOF'
function round2(n) {
  return Math.round(n * 100) / 100;
}

/**
 * Limits `value` to the closed range [min, max].
 * Throws TypeError for a non-number or NaN argument, RangeError when min > max.
 */
function clamp(value, min, max) {
  for (const n of [value, min, max]) {
    if (typeof n !== "number" || Number.isNaN(n)) {
      throw new TypeError("clamp expects numbers");
    }
  }
  if (min > max) {
    throw new RangeError("min must not exceed max");
  }
  return Math.min(Math.max(value, min), max);
}

module.exports = { round2, clamp };
EOF
cat > test.js <<'EOF'
const assert = require("assert");
const { round2, clamp } = require("./src/numbers");

assert.strictEqual(round2(1.234), 1.23);
assert.strictEqual(round2(2), 2);

assert.strictEqual(clamp(5, 0, 10), 5);
assert.strictEqual(clamp(-3, 0, 10), 0);
assert.strictEqual(clamp(42, 0, 10), 10);
assert.strictEqual(clamp(0, 0, 10), 0);
assert.strictEqual(clamp(10, 0, 10), 10);
assert.strictEqual(clamp(7, 7, 7), 7);
assert.strictEqual(clamp(1e9, 0, Infinity), 1e9);
assert.throws(() => clamp(1, 10, 0), RangeError);
assert.throws(() => clamp(NaN, 0, 1), TypeError);
assert.throws(() => clamp("5", 0, 10), TypeError);
console.log("ok");
EOF
git add -A && git commit -qm "feat: clamp helper with tests"
git remote add origin "$PWD" && git fetch -q origin
