---
name: fix-auto
description: Use when the user themselves asks, in their own words, to apply, run, or execute comb fix instructions (the output of /comb:plan) — "apply the fixes", "run the plan", "execute the instruction files". Not for a dispatch prompt that tells you to execute one instruction file: that is already inside the fix workflow.
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

You are the model-invocable entry to `/comb:fix`. `/comb:fix` itself is user-only (`disable-model-invocation: true`) because it edits code and commits; this skill exists so a project can opt in to letting Claude start that workflow from a natural-language request. It cannot be typed as a slash command; only the model invokes it. It refuses by default: a project opts in with `fix.model_invocation: true` in its `.claude/comb.config.json` (or globally in `~/.claude/comb.config.json`).

## Step 1: Check the gate

Load the merged config per `${CLAUDE_PLUGIN_ROOT}/shared/config-loading.md` and read `fix.model_invocation`. Keep the merged config; the fix workflow's own config step reuses it rather than loading again.

If the value is not exactly the boolean `true`, stop here and say, with the value you observed written as JSON in place of `{value}` (so a string `"true"` keeps its quotes; `unset` when the key is absent):

```
Model invocation of /comb:fix is off for this project (fix.model_invocation: {value}).
Run it yourself:  /comb:fix {instruction folder, if known}
Or enable it:     /comb:configure project "allow Claude to run fix"   (sets fix.model_invocation: true)
```

Do not read or execute the fix workflow when the gate is off.

## Step 2: Run the fix workflow

**Plugin root for the workflow.** The skill file you Read below is not variable-substituted, and the plugin-root placeholder is not a shell variable. In that file the placeholder is written as a dollar sign, an opening brace, the name CLAUDE_PLUGIN_ROOT, and a closing brace. Wherever you see it — in the `manifest.py` command lines, and in every Read target under `shared/`, `directives/`, and `skills/` — replace it with this literal path: `${CLAUDE_PLUGIN_ROOT}`. A `manifest.py` command run with the placeholder unexpanded fails and would silently fall back to delivering the full manifest.

Read `${CLAUDE_PLUGIN_ROOT}/skills/fix/SKILL.md` and execute that workflow exactly as written, with one override: its Step 1 reuses the config loaded above instead of loading again. Its arguments placeholder, written as a dollar sign followed by the word ARGUMENTS, arrives literal because the file came through Read; wherever it appears, use this skill's own arguments, which are: `$ARGUMENTS`. If that is empty, the fix workflow runs with no folder named (its own default under `paths.plans`) and an empty focus brief. Every gate, question, pre-flight check, and commit rule in `/comb:fix` applies unchanged. Do not invoke the Skill tool for it (the model cannot; that is the point of this entry). The gate above is the only thing this skill adds.
