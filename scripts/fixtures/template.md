# PATTERNS — demo-template

**Generated:** 2026-10-01
**Base commit:** BASECOMMIT0
**comb version:** 0.10.0
**Scan areas:** React frontend, API, Shared types

> Observed baseline, not law. comb's reviewers reconcile this against live code
> (live code wins), treat a silent area as a cue to read the code rather than
> permission to do anything, and classify divergence (drift vs. deliberate
> improvement vs. new canonical) before flagging. Project directives outrank
> this manifest. Refresh with `/comb:patterns`.

---

## React frontend

_Scope: `src/web/**`_

### Structural conventions
- Pages own state; bodies are presentation-only — `src/web/pages/HomePage.tsx:12-40` (canonical: `src/web/pages/HomePage.tsx:12`)
- One component per file, PascalCase — `src/web/components/Button.tsx:1`

### Closed sets
- Button variants: `primary`, `secondary`, `danger` — defined at `src/web/components/Button.tsx:4`

### Reuse points
- `useFetch` wraps every read — `src/web/hooks/useFetch.ts:8`
- Error toasts go through `notify()` — `src/web/lib/notify.ts:3` (canonical: `src/web/lib/notify.ts:3`)

⚠ Drift: the legacy form in `src/web/old/Form.tsx:3` — fixed 2026-09-01, file deleted.

## API

_Scope: src/api_

### Structural conventions
- Handlers live one per route file — `src/api/routes/users.ts:1`
- Validation at the boundary with `zod` — `src/api/routes/users.ts:9`, `src/api/routes/orders.ts:11`

### Error handling & async
- Errors are thrown as `ApiError` and mapped once — `src/api/errors.ts:5` (canonical: `src/api/errors.ts:5`)

⚠ Drift: `src/api/legacyClient.ts:10` retired; the v1 routes are still in use.

## Shared types

_Scope: packages/types_

### Naming & vocabulary
- Domain terms are `user`, `order`, `line` — `packages/types/index.ts:1`

### Closed sets
- Order status: `OPEN`, `PAID`, `SHIPPED` — defined at `packages/types/order.ts:3`

## Cross-reference map

- **React frontend** composes with API (via `useFetch`) and Shared types.
- **API** composes with Shared types.

## Drift register

| # | Legacy / drift | Forward canonical | Tracking |
|---|---|---|---|
| 1 | v1 routes under `src/api/v1/` | `src/api/routes/` | #1001 |
