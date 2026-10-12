#!/usr/bin/env bash
# Experiment E3: three seeded bugs on one branch; the arms differ only in
# effort.review (medium here). Recall (bugs cited) and cost are compared.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.com
git config user.name "comb eval"
mkdir -p src .claude
printf '{ "effort": { "review": "medium" } }\n' > .claude/comb.config.json
cat > src/config.js <<'EOF'
async function readConfig() {
  return { currency: "EUR" };
}

module.exports = { readConfig };
EOF
git add -A && git commit -qm "init"
git checkout -qb feature
cat > src/total.js <<'EOF'
function total(items) {
  let sum = 0;
  for (let i = 0; i <= items.length; i++) {
    sum += items[i].price;
  }
  return sum;
}

module.exports = { total };
EOF
cat > src/load.js <<'EOF'
const fs = require("fs");

function loadOrders(path) {
  try {
    return JSON.parse(fs.readFileSync(path, "utf8"));
  } catch (e) {
    return [];
  }
}

module.exports = { loadOrders };
EOF
cat > src/report.js <<'EOF'
const { readConfig } = require("./config");

async function buildReport(orders) {
  const config = readConfig();
  return { count: orders.length, currency: config.currency };
}

module.exports = { buildReport };
EOF
git add -A && git commit -qm "feat: order totals, loading, and report"
git remote add origin "$PWD" && git fetch -q origin
