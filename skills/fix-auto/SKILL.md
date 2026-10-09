---
name: fix-auto
description: Use when the user asks, in their own words, to apply, run, or execute comb fix instructions (the output of /comb:plan) — "apply the fixes", "run the plan", "execute the instruction files" — instead of typing /comb:fix. Honors fix.model_invocation in comb.config.json; off by default.
argument-hint: "[instruction-folder] [focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - WebFetch
user-invocable: false
disable-model-invocation: false
---

You are the model-invocable entry to `/comb:fix`. `/comb:fix` itself is user-only (`disable-model-invocation: true`) because it edits code and commits; this skill exists so a project can opt in to letting Claude start that workflow from a natural-language request.

## Step 1: Check the gate

Load the merged config per `${CLAUDE_PLUGIN_ROOT}/shared/config-loading.md` and read `fix.model_invocation` (default `false`).

If it is not exactly `true`, stop here and say:

```
Model invocation of /comb:fix is off for this project (fix.model_invocation: false).
Run it yourself:  /comb:fix {instruction folder, if known}
Or enable it:     /comb:configure project "allow Claude to run fix"   (sets fix.model_invocation: true)
```

Do not read or execute the fix workflow when the gate is off.

## Step 2: Run the fix workflow

Read `${CLAUDE_PLUGIN_ROOT}/skills/fix/SKILL.md` and execute that workflow exactly as written, with `$ARGUMENTS` as its arguments. Nothing is overridden: every gate, question, pre-flight check, and commit rule in `/comb:fix` applies unchanged. Do not invoke the Skill tool for it (the model cannot; that is the point of this entry).

## Ground rules

- **The gate is the only thing this skill adds.** Behaviour, output, and questions are `/comb:fix`'s.
- **Off by default.** A project opts in by setting `fix.model_invocation: true` in its `.claude/comb.config.json` (or globally in `~/.claude/comb.config.json`).
