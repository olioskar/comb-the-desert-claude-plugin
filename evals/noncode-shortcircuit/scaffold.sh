#!/usr/bin/env bash
# Scratch repo whose feature branch changes only a prose design doc.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.com
git config user.name "comb eval"
mkdir -p docs
cat > docs/design.md <<'EOF'
# Widget service — design

## Goal

Expose a widget lookup endpoint.

## Storage

Widgets live in the existing relational store.
EOF
git add -A
git commit -qm "init design doc"
git checkout -qb feature
cat >> docs/design.md <<'EOF'

## Caching

Responses may be cached for a while when the data is not too fresh.
The cache layer should probably be configurable.
EOF
git add -A
git commit -qm "add caching section"
