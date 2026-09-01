---
name: fix-reviewer-diff-scope
tags: [fix, reviewer, regression]
runs: 1
max_turns: 80
timeout_seconds: 1800
scaffold_script: scaffold.sh
---

/comb:fix plans/plan-for-eval — execute M1 then M2 in that order. Do not ask me to confirm order or groupings; per-item commits stay on.
