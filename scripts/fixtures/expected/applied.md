# PATTERNS — demo-curated

**Generated:** 2026-06-08 · **Base:** `docs/pattern-manifest` @ `6aff510f` (off `staging`) · `file:line` references are valid as of this commit · **Patched:** 2026-07-03 @ `d33250f6` (line re-anchors + pattern 13) · **Patched:** 2026-07-04 on `refactor/uicomponents` (pattern 4 re-based on the Base UI composition; the mirroring drift-register row was missed and stayed wrong until 2026-08-21) · **Patched:** 2026-08-21 on `refactor/ionic-shell-exit` (#9 token census recounted post-Ionic-exit; drift rows 5/9 updated; seven stale `file:line` refs corrected) · **Patched:** DATE (§4 anchor re-based and its gate claim corrected; §8 picker rows restated on the shared search core) · **Regenerated (partial):** 2026-09-30 @ `BASECOMMIT0` via `/comb:patterns` — §2, §9, §15 rescanned · count 20261009
**Shaved:** DATE (4810 → 4622 bytes)
**Scope:** the canonical UI + data patterns of the demo web app, each pinned to a real reference implementation.

> **Observed baseline, not law.** Live code wins. Project directives outrank it.

## How to read this
- **Curated canonical refs.** Each section names the implementation to copy.
- **Single home per convention.** Cross-cutting homes: styling/tokens → #9, data access → #10, testing idioms → #14.

## Patterns
1. Entity Page · 3. SidePanel / PanelHost · 9. Design system / primitives · 12. PDF / reporting · 14. Testing conventions

---

## 1. Entity Page

The full page assembly: route → `*Page.tsx` (state owner) → `*Body.tsx` (layout).

**Canonical reference:** `src/pages/entity/contact/` — copy this for a simple page. `ContactsPage.tsx:32-234` is the orchestrator; `ContactsBody.tsx:25-54` is the layout shell. Secondary anchor for a complex page: `src/pages/entity/job/JobsPage.tsx:56-550` + `JobsBody.tsx:33-85`.

**Home:** `src/pages/entity/{entity}/` — owns `{Entity}Page.tsx`, `{Entity}Body.tsx`, `screens/` (panel screen folder + `index.ts` registration array).

**Key conventions:**
- Page is the single state owner; Body is presentation-only — `ContactsPage.tsx:200-208`.
- Panel routing is delegated to `usePanelRouter` — `ContactsPage.tsx:66-73` (canonical: `src/pages/entity/contact/ContactsPage.tsx:66`).
- Grid selection clears on scope change — `src/pages/entity/contact/ContactsGrid.tsx:31-35,149-172`.
- Tokens come from the design system — `src/theme/tokens.css:1` (restated; home is #9).

**Cross-refs:** #9 primitives, #14 testing.

## 3. SidePanel / PanelHost

**Home:**

Panel screens are registered per entity and hosted by `PanelHost` — `src/components/sidePanel/PanelHost.tsx:14-60`.

- Header actions come from the entity's action list — `PanelHost.tsx:88`.
- Primitives come from the design system — `src/components/primitives/Button.tsx:1` (restated; home is #9).


## 9. Design system / primitives

**Home:** `src/theme/**`, `src/components/primitives/**`

- Tokens are CSS custom properties — `src/theme/tokens.css:1-40` (canonical: `src/theme/tokens.css:1`).
- Primitives never import from pages — `src/components/primitives/Button.tsx:1`.
- Panel chrome uses primitives — `src/components/sidePanel/PanelHost.tsx:14` (restated; home is #3).

⚠ Drift: `src/theme/legacy.css:1` half fixed; still open in #1015.

## 12. PDF / reporting

**Home:** `src/pdf/**` — owns PDF rendering and the `GeneratePdfResult` contract.

- Templates are pure functions of typed data — `src/pdf/templates/Invoice.tsx:10`.
- Shared primitives mirror design tokens by hand — `src/pdf/primitives/styles.ts:1` (manual sync).

⚠ Drift: the legacy renderer was fixed in #1200.

## 14. Testing conventions

- Global setup lives in `src/setupTests.ts:1-20`; the i18n mock factory is `src/test/i18nMock.ts:5`.
- Suites are named `*.test.tsx` beside the unit — `src/components/primitives/Button.test.tsx:1`.
- See 9. Design system / primitives.

## Appendix

Notes with no code references: naming history, retired vocabulary, and the reasoning behind the single-home rule.

## Cross-reference map

- **#1 Entity Page** wires #3 (panel) and draws tokens from #9.
- **#14 Testing** enforces #1's grid recipe.

## ⚠ Drift register — do not propagate (with tracking)

| # | Legacy / drift (present, do not seed new work) | Forward canonical | Tracking |
|---|---|---|---|
| 9 | legacy `components.css` | `--demo-*` tokens + CSS Modules | #1015 |
| 14 | hand-rolled i18n mocks in 20 suites | `i18nMockFactory` (`src/test/i18nMock.ts`) | #1583 — new suites use the factory |

## Maintenance

Refresh a section when its canonical pattern changes. Consumed automatically by `/comb:review|plan|fix` when present.
