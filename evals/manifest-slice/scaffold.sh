#!/usr/bin/env bash
# Scratch repo with a curated-shape PATTERNS manifest (numbered headings,
# **Home:** lines with a {entity} placeholder and a ** glob, basename anchors,
# an emoji-prefixed drift register, a " / " heading, a long provenance line)
# and a one-file branch change under src/pages/entity/order/.
# Regression target: agents receive a per-run excerpt that includes the
# entity-page section and omits pdf and theme; the orchestrator never prints
# the manifest body.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.com
git config user.name "comb eval"
mkdir -p src/pages/entity/contact src/pages/entity/order src/pdf/templates src/theme docs/combs
cat > src/pages/entity/contact/ContactsPage.tsx <<'EOT'
export function ContactsPage() { return null; }
EOT
cat > src/pdf/templates/Invoice.tsx <<'EOT'
export function Invoice() { return null; }
EOT
cat > src/theme/tokens.css <<'EOT'
:root { --demo-space-1: 4px; }
EOT
git add -A && git commit -qm base
SHA=$(git rev-parse --short=8 HEAD)
PROV="**Generated:** 2026-06-08 · **Base:** \`docs/pattern-manifest\` @ \`6aff510f\` (off \`staging\`)"
for i in 1 2 3 4 5 6; do PROV="$PROV · **Patched:** 2026-0$i-01 on \`refactor/step-$i\` (anchors re-based after step $i; the drift-register row was corrected and the token census recounted)"; done
PROV="$PROV · **Regenerated (partial):** 2026-09-30 @ \`$SHA\` via \`/comb:patterns\`"
cat > docs/combs/PATTERNS.md <<EOT
# PATTERNS — demo

$PROV
**Scope:** the canonical UI + data patterns of the demo app.

## How to read this
- **Single home per convention.** Cross-cutting homes: styling → #9.

## Patterns
1. Entity Page · 3. SidePanel / PanelHost · 9. Design system · 12. PDF / reporting

---

## 1. Entity Page

**Canonical reference:** \`src/pages/entity/contact/\` — \`ContactsPage.tsx:1-3\` is the orchestrator.

**Home:** \`src/pages/entity/{entity}/\` — owns \`{Entity}Page.tsx\`, \`{Entity}Body.tsx\`.

- Page is the single state owner — \`ContactsPage.tsx:1\`.

## 3. SidePanel / PanelHost

**Home:**

- Panel screens are registered per entity — \`src/components/sidePanel/PanelHost.tsx:14\`.

## 9. Design system

**Home:** \`src/theme/**\`

- Tokens are CSS custom properties — \`src/theme/tokens.css:1\`.

## 12. PDF / reporting

**Home:** \`src/pdf/**\` — owns PDF rendering.

- Templates are pure functions of typed data — \`src/pdf/templates/Invoice.tsx:1\`.

## Cross-reference map

- **#1 Entity Page** draws tokens from #9.

## ⚠ Drift register — do not propagate (with tracking)

| # | Legacy / drift | Forward canonical | Tracking |
|---|---|---|---|
| 9 | legacy \`components.css\` | \`--demo-*\` tokens | #1015 |
EOT
git add -A && git commit -qm "add PATTERNS manifest"
git checkout -qb feature
cat > src/pages/entity/order/OrdersPage.tsx <<'EOT'
export function OrdersPage() { const data = fetch("/orders"); return null; }
EOT
git add -A && git commit -qm "feat: orders page"
# review Step 2 diffs against origin/<base>; give the scratch repo an origin
git remote add origin "$PWD" && git fetch -q origin
