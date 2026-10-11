---
name: config-null-delete
tags: [config, review]
runs: 1
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite]
---

/comb:review the feature branch against main. Proceed without asking me anything; accept your own judgment on the palette.
