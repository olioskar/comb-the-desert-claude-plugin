#!/usr/bin/env bash
# Scratch repo with a finished code-shaped review report; /comb:plan dispatches
# the default implementer (general-purpose — foreign per the delivery contract).
# Regression target: directives must reach the planner as paths, never embedded.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.com
git config user.name "comb eval"
mkdir -p src reviews
cat > src/util.js <<'EOF'
function parsePort(raw) {
  return parseInt(raw);
}

module.exports = { parsePort };
EOF
cat > reviews/pr-1-round1-report.md <<'EOF'
# util hardening — Round 1 Review Report

**Branch:** `feature` -> `main`
**Scope:** 1 file, +5 / -0 lines
**Reviewers:** 1 agent (comb:code-reviewer)
**Date:** 2026-09-01

---

## Verification Summary

| Check | Result |
|---|---|
| Tests | none configured |

---

## Verdict: **NEEDS WORK**

One Medium finding on numeric parsing.

---

## Findings by Severity

### Critical
None.

### High
None.

### Medium
**M1 — parseInt without radix accepts unintended bases**
*Source: code-reviewer*
File(s): `src/util.js:2`
**Verified:** Read src/util.js:1-5; confirmed `parseInt(raw)` has no radix argument.

`parsePort` calls `parseInt(raw)` without the radix. A leading-zero string can parse in an unintended base on legacy engines, and `"0x50"` parses as hex. Pass `10` explicitly: `parseInt(raw, 10)`.

### Low
None.

### Test Gaps
None.

### Deferred
None.
EOF
git add -A
git commit -qm "init with review report"
