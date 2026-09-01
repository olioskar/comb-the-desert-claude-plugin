#!/usr/bin/env bash
# Interim behavioral gate while `claude plugin eval` is early-access-gated.
# Runs the structural gates, then two non-interactive help checks.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== structural gates =="
claude plugin validate .
bash scripts/check-contract.sh

echo "== help smoke (non-interactive) =="
out="$(claude -p "/comb:help" --plugin-dir . --allowedTools "Skill Read" 2>&1)" || {
  echo "$out"
  echo "FAIL: /comb:help run errored"
  exit 1
}
echo "$out" | grep -q "comb-the-desert — code-review pipeline" || {
  echo "$out"
  echo "FAIL: /comb:help did not print the overview"
  exit 1
}

out="$(claude -p "/comb:help fix" --plugin-dir . --allowedTools "Skill Read" 2>&1)" || {
  echo "$out"
  echo "FAIL: /comb:help fix run errored"
  exit 1
}
echo "$out" | grep -q "Trivial-only escape hatch" || {
  echo "$out"
  echo "FAIL: /comb:help fix did not print the per-command detail"
  exit 1
}

echo "smoke: OK (structural gates + help lane)."
echo "For a full behavioral pass, run the eval suite once enabled:"
echo "  claude plugin eval . --scaffold"
echo "Or drive /comb:review manually in a scratch repo: claude --plugin-dir $(pwd)"
