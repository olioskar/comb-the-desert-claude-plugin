#!/usr/bin/env bash
# Scratch repo whose project config deletes the simplifier role via null-merge.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.com
git config user.name "comb eval"
mkdir -p src .claude
cat > src/math.js <<'EOF'
function add(a, b) {
  return a + b;
}

module.exports = { add };
EOF
cat > .claude/comb.config.json <<'EOF'
{
  "agents": {
    "simplifier": null
  }
}
EOF
git add -A
git commit -qm "init"
git checkout -qb feature
cat > src/math.js <<'EOF'
function add(a, b) {
  return a + b;
}

function subtract(a, b) {
  return a - b;
}

module.exports = { add, subtract };
EOF
git add -A
git commit -qm "add subtract"
