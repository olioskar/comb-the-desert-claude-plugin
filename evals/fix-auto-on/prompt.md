---
name: fix-auto-on
tags: [fix-auto, gate, fix]
runs: 1
max_turns: 60
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite]
---

Apply the fixes in plans/plan-for-eval. Do not ask me to confirm order or groupings.
