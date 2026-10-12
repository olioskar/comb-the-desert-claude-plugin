#!/usr/bin/env bash
# Experiment E2 (B-2), the 0.8.0 gerrymander scenario: a directive requires
# BEM double-dash modifiers; five components follow it (9 modifiers); btn.css
# uses single-dash modifiers consistently (4). Area-wide that is a minority
# (drift), not a dominant conflict. A scanner that scopes "dominant" to the
# btn component reports a false `## Directive conflicts` entry.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.com
git config user.name "comb eval"
mkdir -p src/styles docs/directives
cat > docs/directives/css.md <<'EOF'
# CSS conventions

## 1. Modifier classes

1.1 A modifier is written BEM-style with a double dash: `.block--modifier`. Single-dash modifiers such as `.block-modifier` are not allowed.
EOF
cat > src/styles/card.css <<'EOF'
.card { padding: 16px; border-radius: 8px; }
.card--active { border: 2px solid #2563eb; }
.card--muted { opacity: 0.6; }
EOF
cat > src/styles/alert.css <<'EOF'
.alert { padding: 12px; }
.alert--error { background: #fee2e2; }
.alert--warning { background: #fef3c7; }
EOF
cat > src/styles/badge.css <<'EOF'
.badge { font-size: 12px; }
.badge--new { background: #dcfce7; }
.badge--count { min-width: 20px; }
EOF
cat > src/styles/nav.css <<'EOF'
.nav { display: flex; }
.nav--open { height: auto; }
.nav--sticky { position: sticky; top: 0; }
EOF
cat > src/styles/panel.css <<'EOF'
.panel { margin: 24px; }
.panel--wide { max-width: 1200px; }
EOF
cat > src/styles/btn.css <<'EOF'
.btn { padding: 8px 16px; border-radius: 4px; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-secondary { background: #e5e7eb; }
.btn-danger { background: #dc2626; color: #fff; }
.btn-large { padding: 12px 24px; }
EOF
git add -A && git commit -qm "init styles"
