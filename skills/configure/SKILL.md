---
name: configure
description: Configure the comb plugin — change paths, swap models, enable/disable agents, edit directive settings. Use when the user wants to configure comb, change comb settings, disable an agent, change which model comb uses, set the base branch, change where reviews are saved, or otherwise tweak `.claude/comb.config.json`.
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

Read all three layers and show the **merged effective config** plus which keys are coming from where. This is the "before" picture.

1. `${CLAUDE_PLUGIN_ROOT}/config/defaults.json` — shipped defaults
2. `~/.claude/comb.config.json` — global override (skip if not present)
3. `<project-root>/.claude/comb.config.json` — project override (skip if not present)

**Merge rules** (same as the rest of the plugin):
- Objects: deep-merged
- Arrays: replaced wholesale
- `null` at any depth: removes that key from the merged result
- Invalid JSON in any layer: hard error — abort with a clear message naming the bad file

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
| `agents.<role>` | object | Reviewer entry. Required keys: `subagent_type` (string), `when_to_use` (string). Optional: `model` (string, per-agent override). |
| `agents.<role>` | `null` | **Deletes** the role from the palette via merge semantics. |
| `models.review` | string | Model for review-step agents. |
| `models.plan` | string | Model for plan-step agents. |
| `models.patterns` | string | Model for the pattern-scanner agents during /comb:patterns generation. |
| `models.fix.implementer_standard` | string | Fix-step implementer for non-trivial work. |
| `models.fix.implementer_trivial` | string | Fix-step implementer for trivial work. |
| `models.fix.reviewer` | string | Fix-step internal reviewer. |
| `models.the_desert` | string | Model for the desert orchestrator. |

**Translation rules:**

- **"Disable agent X"** → set `agents.X = null` in the override file. (This relies on null-as-delete merge semantics.)
- **"Re-enable agent X"** → remove the `null` entry, OR re-supply the full agent object (`subagent_type` + `when_to_use`) if the user wants a custom version.
- **"Add a custom agent"** → write `agents.<new-role> = {subagent_type: "...", when_to_use: "..."}` and tell the user that a non-`comb:*` `subagent_type` triggers foreign-agent dispatch (full directive contents embedded in the prompt).
- **"Use model M for step S"** → set `models.<step> = "M"` (or the nested `models.fix.*` for fix sub-roles).
- **"Use model M for agent X"** → set `agents.X.model = "M"` (per-agent override beats step-level).
- **"Change reviews/plans dir"** → set `paths.<reviews|plans>`.
- **"Change base branch"** → set `paths.base_branch`.
- **"Change patterns manifest path"** → set `paths.patterns`. Setting it to `null` disables manifest consumption in review/plan/fix.
- **"Use model M for patterns/scanning"** → set `models.patterns = "M"`.
- **"Stop loading plugin directives"** → set `directives.include_plugin_defaults = false`.
- **"Look for my directives in <dir>"** → set `directives.user_path = "<dir>"`.

If the user asks for something outside this schema, say so plainly and stop. Don't invent fields.

## Step 4: Show the diff and confirm

Compute the new on-disk file content for the chosen scope (project or global), preserving keys the user didn't ask to change. Show a unified diff (or the full new file if it's small). Wait for the user's confirmation before writing.

If the user's request would have no effect (the value already matches), tell them and don't write.

## Step 5: Write

Write the new file. Format with 2-space indentation. Pretty-print top-level keys in this order: `paths`, `directives`, `agents`, `models`. Within `agents`, list roles alphabetically. (Order is purely cosmetic — the plugin doesn't care.)

## Step 6: Verify

- Re-parse the file you just wrote — fail loud on a JSON error.
- For each `agents.<role>` that is an object (not `null`), confirm it has both `subagent_type` and `when_to_use` strings. If not, warn the user — at runtime the bad role will be skipped per the schema-violation rule, but better to flag now.

## Step 7: Tell the user how to test

Suggest the most relevant smoke test based on what changed:

- Changed `agents.*` or `models.*` → "Run `/comb:review` against a small dirty branch and confirm the agent palette and model assignments match what you set."
- Changed `paths.*` → "Run `/comb:review` and confirm the report lands in the new `paths.reviews` directory."
- Changed `directives.*` → "Run `/comb:review` with a focus brief that mentions one of your directives and confirm it's flagged primary."
- Changed `paths.patterns` or `models.patterns` → "Run `/comb:patterns` and confirm the manifest lands at the new path (or the scanners use the model you set)."

## Ground rules

- Edit the user's config file. Don't touch `${CLAUDE_PLUGIN_ROOT}/config/defaults.json` — it's read-only at runtime.
- Always show the diff before writing.
- One scope per invocation. If the user wants both project and global edits, do it as two passes.
- Keep going until the file is written and verified — don't bail halfway.
- If the user wants to inspect their config without changing it, just do Step 2 and stop.
