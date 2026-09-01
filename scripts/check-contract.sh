#!/usr/bin/env bash
# Release-gate greps for the comb plugin's shipped contract.
# Deterministic and offline; run from anywhere.
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0

# 1. No dead spec citations in shipped files (the design spec does not ship).
if grep -rn "spec §\|decision §" skills/ agents/ shared/ directives/ README.md 2>/dev/null; then
  echo "FAIL: dead spec/decision citations found in shipped files"
  fail=1
fi

# 2. Every ${CLAUDE_PLUGIN_ROOT}/shared/*.md reference resolves to a file.
while IFS= read -r ref; do
  rel="${ref#\$\{CLAUDE_PLUGIN_ROOT\}/}"
  if [ ! -f "$rel" ]; then
    echo "FAIL: unresolved shared reference: $ref"
    fail=1
  fi
done < <(grep -rho '\${CLAUDE_PLUGIN_ROOT}/shared/[a-z-]*\.md' skills/ README.md | sort -u)

# 3. No skill re-inlines a shared block (drift re-entry guard).
#    Each needle is the distinctive opener of a block that now lives in shared/.
while IFS= read -r needle; do
  if grep -rn "$needle" skills/ >/dev/null 2>&1; then
    echo "FAIL: shared block re-inlined in a skill: \"$needle\""
    fail=1
  fi
done <<'NEEDLES'
Lowercase the focus brief and scan it for substring matches
This is the codebase's observed convention baseline
Read the layered config in this order
the shipped allowlist is exactly
NEEDLES

# 4. .DS_Store is never tracked.
if git ls-files | grep -q '\.DS_Store'; then
  echo "FAIL: .DS_Store is tracked"
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "check-contract: OK"
fi
exit "$fail"
