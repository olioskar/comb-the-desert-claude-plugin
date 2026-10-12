---
name: configure
description: Use when the user wants to configure comb, change comb settings, disable an agent, change which model comb uses, set the base branch, change where reviews are saved, point comb at their directives, or otherwise tweak `.claude/comb.config.json`.
argument-hint: "[scope] [change]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
user-invocable: true
disable-model-invocation: false
---

You help the user edit their comb config conversationally and write the result to the right `comb.config.json` file with correct deep-merge semantics.

## Inputs

You need:

1. **Scope** — `project` (`<project-root>/.claude/comb.config.json`) or `global` (`~/.claude/comb.config.json`).
2. **Change(s)** — what the user wants different from the merged config they have now. The user may pass these in `$ARGUMENTS` or describe them in conversation. One invocation can apply multiple changes.

If either is missing, ask once.

## Step 1: Resolve target file

- **Project root:** `git rev-parse --show-toplevel` (cwd fallback).
- **Project scope:** `<project-root>/.claude/comb.config.json`
- **Global scope:** `~/.claude/comb.config.json`

If the file doesn't exist, you'll create it. If `.claude/` doesn't exist for project scope, create the directory.

## Step 2: Show the user what they have now

Run the merge per `${CLAUDE_PLUGIN_ROOT}/shared/config-loading.md`:

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/comb.py" config
```

Run it from the project root. Its JSON is the **merged effective config**; a `warning:` line names a role the merge dropped. Read the three layer files themselves only to say which layer each non-default key comes from. This is the "before" picture.

Print a short summary of the effective config (not the full JSON dump unless the user asks). Highlight which layer each non-default value is coming from.

## Step 3: Map the user's request to JSON

**Keys and types** are `${CLAUDE_PLUGIN_ROOT}/config/defaults.json`: every configurable key appears there with its default, and the default's JSON type is the key's type. Three things it cannot show, because they are absent by default:

- `agents.<role>` set to `null` **deletes** the role from the palette via merge semantics.
- `agents.<role>.model` and `agents.<role>.effort` are optional per-role overrides (strings) that beat the lane values.
- `effort.<lane>` mirrors `models.*` key for key (`review`, `plan`, `patterns`, `fix.implementer_standard`, `fix.implementer_trivial`, `fix.reviewer`, `the_desert`), one of `low | medium | high | xhigh | max`. Absent by default: dispatched agents run at the session's effort. Needs a Claude Code that takes `effort` on the Agent call (2.1.292 or later).

**Notes** (what the keys mean; paths are relative to the project root):

- `paths.reviews`, `paths.plans`: where review reports and plan folders are written. `paths.base_branch`: the default base for diffs. `paths.patterns`: where the PATTERNS manifest is written and read; `null` disables manifest consumption across review/plan/fix.
- `directives.include_plugin_defaults: false` stops loading the shipped directives; `directives.user_path` is the directory of the user's directive `.md` files.
- `agents.<role>`: a reviewer or writer entry with required `subagent_type` and `when_to_use` strings; a role missing either is dropped at load with a warning.
- `models.review`, `models.plan`, `models.patterns` (scanner and shaver), `models.fix.implementer_standard`, `models.fix.implementer_trivial`, `models.fix.reviewer`, `models.the_desert` (replaces every lane in a sweep).
- `fix.commit_per_item`: commit each item on reviewer PASS. `fix.model_invocation`: let Claude start the fix workflow from a natural-language request through the model-only `fix-auto` skill (`/comb:fix` itself stays user-only).

**Model values:** `sonnet`, `opus`, `haiku`, `fable`, or a full model id. `best`, `inherit`, and `opusplan` are `/model` session aliases, not values the Agent call accepts: refuse them and say so.

**Translation rules** that are not a direct key write:

- **"Disable agent X"** → set `agents.X = null` in the override file (null-as-delete merge semantics). **"Re-enable"** → remove the `null` entry, or re-supply the full agent object for a custom version.
- **"Add a custom agent"** → write `agents.<new-role> = {subagent_type: "...", when_to_use: "..."}` and tell the user that a `subagent_type` other than `comb:` + a shipped agent name is foreign per the delivery contract: its run brief carries the authority sentence and a `Your lens:` line taken from `when_to_use`.
- **"Allow Claude to run fix" / "let the model apply fixes"** → set `fix.model_invocation = true` in the project override (or globally if asked). Say that `/comb:fix` is still user-only; the opt-in routes natural-language requests through the model-only `fix-auto` skill (not a slash command), which runs the same workflow with the same questions and commits.

Everything else is a direct key write: name the key from `defaults.json` (or the three absent-by-default keys above), set the value, and show the diff. Removing an `effort` key returns that lane to the session default.

If the user asks for something outside this schema, say so plainly and stop. Don't invent fields.

## Step 4: Show the diff and confirm

Compute the new on-disk file content for the chosen scope (project or global), preserving keys the user didn't ask to change. Show a unified diff (or the full new file if it's small). Wait for the user's confirmation before writing.

If the user's request would have no effect (the value already matches), tell them and don't write.

## Step 5: Write

Write the new file. Format with 2-space indentation. Pretty-print top-level keys in this order: `paths`, `directives`, `agents`, `models`, `effort`, `fix`. Within `agents`, list roles alphabetically. (Order is purely cosmetic — the plugin doesn't care.)

## Step 6: Verify

- Re-run `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/comb.py" config`. A non-zero exit is a JSON error in the file you just wrote — fail loud. Each `warning:` line is a role the merge dropped (missing `subagent_type` or `when_to_use`): show it to the user, since at runtime that role is skipped.
- Every `effort.*` and `agents.<role>.effort` value is one of `low`, `medium`, `high`, `xhigh`, `max`; warn on anything else (the Agent call rejects it).

## Step 7: Tell the user how to test

Suggest the most relevant smoke test based on what changed:

- Changed `agents.*`, `models.*`, or `effort.*` → "Run `/comb:review` against a small dirty branch and confirm the agent palette, model, and effort assignments match what you set."
- Changed `paths.*` → "Run `/comb:review` and confirm the report lands in the new `paths.reviews` directory."
- Changed `directives.*` → "Run `/comb:review` with a focus brief that mentions one of your directives and confirm it's flagged primary."
- Changed `fix.model_invocation` → "Ask Claude to apply the fixes in your own words and confirm it starts (or refuses, naming the flag) as you set."
- Changed `paths.patterns` or `models.patterns` → "Run `/comb:patterns` and confirm the manifest lands at the new path (or the scanners use the model you set)."

## Ground rules

- Edit the user's config file. Don't touch `${CLAUDE_PLUGIN_ROOT}/config/defaults.json` — it's read-only at runtime.
- Always show the diff before writing.
- One scope per invocation. If the user wants both project and global edits, do it as two passes.
- Keep going until the file is written and verified — don't bail halfway.
- If the user wants to inspect their config without changing it, just do Step 2 and stop.
