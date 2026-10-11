# PATTERNS — anchors-fixture

**Generated:** 2026-10-11 · **Base commit:** `BASECOMMIT0`

## How to read this
- Fixture for `manifest.py anchors`.

## 1. Web pages

**Home:** `src/web/pages/`

- Good full anchor — `src/web/pages/HomePage.tsx:10-20`.
- Beyond end — `src/web/pages/HomePage.tsx:12,60-80`.
- Missing file — `src/web/pages/Nowhere.tsx:3`.
- Basename resolving once — `HomePage.tsx:7`.
- Basename beyond end — `HomePage.tsx:99`.

## 2. Components

**Scope:** `src/web/components/**`, `src/web/legacy/**`

- Ambiguous basename — `Button.tsx:3`.
- Basename not found — `Ghost.tsx:1`.
- No line part is in bounds by definition — `src/web/components/Button.tsx`.

## Maintenance
- `src/web/pages/HomePage.tsx:999` in a global section is never checked.
