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
done < <(grep -rho '\${CLAUDE_PLUGIN_ROOT}/shared/[a-z-]*\.md' skills/ agents/ README.md | sort -u)

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
Splits the manifest into a header
Derives each area section's scope from two sources
read it and run the commit-based staleness heuristic
NEEDLES

# 5. Manifest excerpts (see 4 below for .DS_Store): the script ships, its fixture test passes, and every
#    consuming skill invokes it (the orchestrator never reads the manifest).
if [ ! -f scripts/manifest.py ]; then
  echo "FAIL: scripts/manifest.py missing"
  fail=1
elif ! python3 -I scripts/manifest.py --help >/dev/null 2>&1; then
  echo "FAIL: python3 -I scripts/manifest.py --help exits non-zero"
  fail=1
elif ! bash scripts/test-manifest.sh >/dev/null 2>&1; then
  echo "FAIL: scripts/test-manifest.sh failed (run it for the diff)"
  fail=1
fi
for skill in review plan fix; do
  if ! grep -Eq 'manifest\.py"? excerpt' "skills/$skill/SKILL.md"; then
    echo "FAIL: skills/$skill does not invoke manifest.py excerpt"
    fail=1
  fi
done
for cmd in index verify gate apply; do
  if ! grep -Eq "manifest\.py\"? $cmd" skills/patterns/SKILL.md; then
    echo "FAIL: skills/patterns does not invoke manifest.py $cmd"
    fail=1
  fi
done


# 4. .DS_Store is never tracked.
if git ls-files | grep -q '\.DS_Store'; then
  echo "FAIL: .DS_Store is tracked"
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "check-contract: OK"
fi
exit "$fail"
