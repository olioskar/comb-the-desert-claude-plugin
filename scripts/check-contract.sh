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
#    Needles are derived from the live blocks: the longest body line of each shared/*.md
#    (headings and table rows skipped), cut to 60 characters at a word boundary — a body
#    copy carries it, a framing sentence does not. One historical needle guards wording
#    removed in 0.11.0 that must not return.
derive_needle() {
  grep -v '^#' "$1" | grep -v '^|' | awk '{ if (length($0) > length(best)) best=$0 } END { print best }' \
    | sed -E 's/^(.{0,60}[^ ]*).*/\1/'
}
while IFS= read -r needle; do
  [ "${#needle}" -lt 30 ] && { echo "FAIL: derived needle too short to be safe: \"$needle\""; fail=1; continue; }
  if grep -rnF "$needle" skills/ >/dev/null 2>&1; then
    echo "FAIL: shared block re-inlined in a skill: \"$needle\""
    fail=1
  fi
done < <(for f in shared/*.md; do derive_needle "$f"; done)
if grep -rnF "read it and run the commit-based staleness heuristic" skills/ >/dev/null 2>&1; then
  echo "FAIL: pre-0.11.0 manifest-read wording returned to a skill"
  fail=1
fi

# 4. A skill that Reads another skill's body carries the plugin-root expansion paragraph:
#    Read output is not variable-substituted, so the placeholder would reach the shell literally.
while IFS= read -r f; do
  if ! grep -q 'replace it with this literal path: `\${CLAUDE_PLUGIN_ROOT}`' "$f"; then
    echo "FAIL: $f Reads another skill but has no plugin-root expansion paragraph"
    fail=1
  fi
done < <(grep -rl '\${CLAUDE_PLUGIN_ROOT}/skills/[a-z-]*/SKILL\.md' skills/ | sort -u)

# 5. Manifest excerpts: the script ships, its fixture test passes, and every consuming
#    skill invokes it (the orchestrator never reads the manifest).
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

# 6. User-facing facts that have a machine source agree with it.
version=$(python3 -c 'import json;print(json.load(open(".claude-plugin/plugin.json"))["version"])')
if ! grep -qF "v${version}. See [CHANGELOG.md]" README.md; then
  echo "FAIL: README Status line does not say v${version} (plugin.json)"
  fail=1
fi

# 7. .DS_Store is never tracked.
if git ls-files | grep -q '\.DS_Store'; then
  echo "FAIL: .DS_Store is tracked"
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "check-contract: OK"
fi
exit "$fail"
