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

The configurable schema is:

| Path | Type | Notes |
|---|---|---|
| `paths.reviews` | string | Where review reports are written. Relative to project root. |
| `paths.plans` | string | Where plan docs are written. Relative to project root. |
| `paths.base_branch` | string | Default base branch for diffs (e.g. `main`, `develop`). |
| `paths.patterns` | string | Where the PATTERNS manifest is written/read. Relative to project root. `null` disables manifest consumption across review/plan/fix. |
| `directives.include_plugin_defaults` | boolean | If `false`, plugin's shipped directives are not loaded. |
| `directives.user_path` | string | Path (relative to project root) to user's directive `.md` files. |
| `agents.<role>` | object | Reviewer entry. Required keys: `subagent_type` (string), `when_to_use` (string). Optional: `model` (string, per-agent override), `effort` (string, per-agent override). |
| `agents.<role>` | `null` | **Deletes** the role from the palette via merge semantics. |
| `models.review` | string | Model for review-step agents. |
| `models.plan` | string | Model for plan-step agents. |
| `models.patterns` | string | Model for the pattern-scanner and pattern-shaver agents (`/comb:patterns`, `/comb:patterns --shave`). |
| `models.fix.implementer_standard` | string | Fix-step implementer for non-trivial work. |
| `models.fix.implementer_trivial` | string | Fix-step implementer for trivial work. |
| `models.fix.reviewer` | string | Fix-step internal reviewer. |
| `models.the_desert` | string | Model for the desert orchestrator. |
| `effort.<lane>` | string | Optional. Same keys as `models.*` (`review`, `plan`, `patterns`, `fix.implementer_standard`, `fix.implementer_trivial`, `fix.reviewer`, `the_desert`). One of `low`, `medium`, `high`, `xhigh`, `max`. Absent by default: dispatched agents run at the session's effort. Needs a Claude Code that takes `effort` on the Agent call (2.1.292 or later). |
| `fix.commit_per_item` | boolean | Commit each fix item on reviewer PASS (default `true`). |
| `fix.model_invocation` | boolean | Let Claude start the fix workflow from a natural-language request through the model-only `fix-auto` skill (default `false`; `/comb:fix` itself stays user-only). |

**Translation rules:**

- **"Disable agent X"** → set `agents.X = null` in the override file. (This relies on null-as-delete merge semantics.)
- **"Re-enable agent X"** → remove the `null` entry, OR re-supply the full agent object (`subagent_type` + `when_to_use`) if the user wants a custom version.
- **"Add a custom agent"** → write `agents.<new-role> = {subagent_type: "...", when_to_use: "..."}` and tell the user that a `subagent_type` other than `comb:` + a shipped agent name is foreign per the delivery contract: its run brief carries the authority sentence and a `Your lens:` line taken from `when_to_use`.
- **"Use model M for step S"** → set `models.<step> = "M"` (or the nested `models.fix.*` for fix sub-roles).
- **"Use model M for agent X"** → set `agents.X.model = "M"` (per-agent override beats step-level).
- **"Use effort E for step S / agent X"** → set `effort.<step> = "E"` or `agents.X.effort = "E"`. Removing the key returns that lane to the session default.
- **"Change reviews/plans dir"** → set `paths.<reviews|plans>`.
- **"Change base branch"** → set `paths.base_branch`.
- **"Allow Claude to run fix" / "let the model apply fixes"** → set `fix.model_invocation = true` in the project override (or globally if asked). Say that `/comb:fix` is still user-only; the opt-in routes natural-language requests through the model-only `fix-auto` skill (not a slash command), which runs the same workflow with the same questions and commits.
- **"Change patterns manifest path"** → set `paths.patterns`. Setting it to `null` disables manifest consumption in review/plan/fix.
- **"Use model M for patterns/scanning"** → set `models.patterns = "M"`.
- **"Stop loading plugin directives"** → set `directives.include_plugin_defaults = false`.
- **"Look for my directives in <dir>"** → set `directives.user_path = "<dir>"`.

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
