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

# 5. Scripts: manifest.py and comb.py ship, their fixture tests pass, and every consuming
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
if [ ! -f scripts/comb.py ]; then
  echo "FAIL: scripts/comb.py missing"
  fail=1
elif ! python3 -I scripts/comb.py --help >/dev/null 2>&1; then
  echo "FAIL: python3 -I scripts/comb.py --help exits non-zero"
  fail=1
elif ! bash scripts/test-comb.sh >/dev/null 2>&1; then
  echo "FAIL: scripts/test-comb.sh failed (run it for the diff)"
  fail=1
fi
if ! bash scripts/test-replay.sh >/dev/null 2>&1; then
  echo "FAIL: scripts/test-replay.sh failed (run it for the diff)"
  fail=1
fi
for skill in review plan fix; do
  if ! grep -Eq 'manifest\.py"? excerpt' "skills/$skill/SKILL.md"; then
    echo "FAIL: skills/$skill does not invoke manifest.py excerpt"
    fail=1
  fi
done
for cmd in index anchors verify gate apply; do
  if ! grep -Eq "manifest\.py\"? $cmd" skills/patterns/SKILL.md; then
    echo "FAIL: skills/patterns does not invoke manifest.py $cmd"
    fail=1
  fi
done
for skill in review plan fix patterns the-desert fix-auto configure; do
  grep -Fq 'comb.py" config' "skills/$skill/SKILL.md" || { echo "FAIL: skills/$skill does not invoke comb.py config"; fail=1; }
done
for skill in review plan fix; do
  grep -Fq 'comb.py" brief' "skills/$skill/SKILL.md" || { echo "FAIL: skills/$skill does not invoke comb.py brief"; fail=1; }
done
grep -Fq 'comb.py" batches' skills/fix/SKILL.md || { echo "FAIL: skills/fix does not invoke comb.py batches"; fail=1; }
grep -Fq 'comb.py" report-name' skills/review/SKILL.md || { echo "FAIL: skills/review does not invoke comb.py report-name"; fail=1; }
grep -Fq 'comb.py" findings' skills/plan/SKILL.md || { echo "FAIL: skills/plan does not invoke comb.py findings"; fail=1; }
for f in skills/patterns/SKILL.md agents/pattern-scanner.md; do
  grep -Fq 'shared/scan-rules.md' "$f" || { echo "FAIL: $f does not point at shared/scan-rules.md"; fail=1; }
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

# 8. Every comb:* subagent_type in defaults.json has an agent file; every agent file's
#    frontmatter name equals its filename (the native rule in dispatch-delivery.md compares
#    `comb:` + name) and is a default subagent_type somewhere.
while IFS= read -r t; do
  case "$t" in MISSING*) echo "FAIL: defaults.json role(s) without subagent_type: ${t#MISSING }"; fail=1; continue;; esac
  n="${t#comb:}"
  [ -f "agents/$n.md" ] || { echo "FAIL: defaults.json names $t but agents/$n.md is missing"; fail=1; }
done < <(python3 -I -c 'import json,sys
a=json.load(open("config/defaults.json"))["agents"]
bad=[k for k,v in a.items() if not (isinstance(v,dict) and isinstance(v.get("subagent_type"),str))]
if bad: print("MISSING " + " ".join(bad))
[print(v["subagent_type"]) for k,v in a.items() if k not in bad and v["subagent_type"].startswith("comb:")]')
for f in agents/*.md; do
  n=$(basename "$f" .md)
  [ "$(sed -n 's/^name:[[:space:]]*//p' "$f" | head -n 1)" = "$n" ] || { echo "FAIL: agents/$n.md frontmatter name does not equal its filename"; fail=1; }
  grep -qF "\"comb:$n\"" config/defaults.json || { echo "FAIL: agents/$n.md is not a default subagent_type in config/defaults.json"; fail=1; }
done
for n in code-reviewer simplifier silent-failure-hunter test-auditor consistency-auditor; do
  grep -qF "**Confidence**" "agents/$n.md" || { echo "FAIL: agents/$n.md has no Confidence line; review Step 7 treats an omitted field as unverified"; fail=1; }
done
if grep -qF -- "- \`comb:" shared/dispatch-delivery.md; then
  echo "FAIL: dispatch-delivery.md carries a native allowlist; the native rule is by agent name"
  fail=1
fi

# 9. Every "(default: X)" in help equals config/defaults.json (effort lanes are unset by design;
#    agents.<role> compares the subagent_type).
python3 -I - "${HELP_FILE:-skills/help/SKILL.md}" <<'PY' || fail=1
import json, re, sys
cfg = json.load(open("config/defaults.json"))
def get(path):
    cur = cfg
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur: return None
        cur = cur[k]
    return cur
bad = 0
seen = 0
for m in re.finditer(r"<?([a-z_]+(?:\.[a-z_*-]+)+)>?\s+\(default:?\s+([^)—]+?)\s*(?:—[^)]*)?\)", open(sys.argv[1]).read()):
    key, val = m.group(1), m.group(2).strip()
    seen += 1
    if key.startswith("effort.") or key.endswith(".*"):
        if val != "unset": print("FAIL: help says %s default %r; effort lanes are unset" % (key, val)); bad = 1
        continue
    if key.startswith("agents."): key += ".subagent_type"
    actual = get(key)
    actual = json.dumps(actual) if isinstance(actual, bool) else actual
    if actual is None or str(actual) != val:
        print("FAIL: help says %s (default: %s) but defaults.json has %r" % (key, val, actual)); bad = 1
if seen == 0:
    print("FAIL: help-defaults gate matched no '(default: X)' line; the help wording changed"); bad = 1
sys.exit(bad)
PY

if [ "$fail" -eq 0 ]; then
  echo "check-contract: OK"
fi
exit "$fail"
