# Client fix — Round 1 Review Report

**Branch:** `feat/x` -> `main`
**Scope:** 3 files, +10 / -2 lines
**Reviewers:** 2 agents (code-reviewer, test-auditor)
**Sources:** code-reviewer: 3 reported → 2 kept, 1 merged into M1 · test-auditor: 1 reported → 1 kept
**Date:** 2026-10-12

---

## Verification Summary

| Check | Result |
|---|---|
| Tests | 12/12 passing |

---

## Verdict: **NEEDS WORK**

One High item.

---

## Findings by Severity

### Critical
None.

### High
**H1 — Null check missing on the response body**
*Source: code-reviewer*
File(s): `src/api/client.ts:42`
**Verified:** Read client.ts:38-50; the guard covers status only.

The body can be undefined when the status is 204.

### Medium
**M1 — Duplicate parsing helpers**
*Source: code-reviewer, simplifier*
File(s): `src/api/parse.ts:10-30`, `src/api/legacy.ts:5`
**Verified:** not independently verified — the two helpers were not diffed.

Two helpers parse the same shape.

### Low
None.

### Test Gaps
**T1 — No test for the 204 path**
*Source: test-auditor*
File(s): `src/api/client.test.ts`
**Verified:** Read client.test.ts; no case sends 204.

Add a case.

### Deferred
- Consider extracting the retry policy into `src/api/retry.ts`.
- The logger wraps every call twice (`src/log.ts:7`).
