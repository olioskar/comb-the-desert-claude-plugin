---
name: dispatch-delivery
tags: [plan, dispatch, foreign-agent]
runs: 1
max_turns: 60
timeout_seconds: 1800
scaffold_script: scaffold.sh
---

/comb:plan reviews/pr-1-round1-report.md — plan every finding, no grouping questions.
