---
name: the-desert
description: Run the full comb pipeline — review → plan → fix — as one continuous sweep. No pauses, no items skipped, no confirmations. Opus everywhere. The user must invoke this explicitly — it executes code changes.
argument-hint: "[scope] [focus brief]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - WebFetch
user-invocable: true
disable-model-invocation: true
---

You're running the full comb pipeline as one continuous sweep. No pauses between steps, no items skipped, no confirmations requested. You comb the desert until it's clean.

## How this differs from running each step individually

| Aspect | Individual steps | The Desert |
|---|---|---|
| Transitions | User decides when to move on | Automatic — no pause between steps |
| Deferred items | Excluded from fix by default | **Included** — nothing is deferred |
| Agent models | Mixed (lane defaults) | **`models.the_desert` everywhere** (default opus) |
| User confirmation | Asked between steps and for groupings | **None** — you make all decisions |

## Inputs

Same as `/comb:review`:
1. **Scope** — PR number, branch, or file list
2. **Base branch** — config or `main`
3. **Focus brief** — `$ARGUMENTS`

If scope is ambiguous, ask once. This is the only question you ask.

## Step 1: Load config

Same layered-merge as `/comb:review`. Project root is resolved with `git rev-parse --show-toplevel` (which handles git worktrees correctly). The relevant override:

- `models.the_desert` (default `opus`) overrides every lane default in this run
- **Exception:** explicit `agents.<role>.model` user overrides survive `the-desert` coercion (per spec §7.6). Only lane defaults are coerced.

## Step 2: Surface relevant directives

Lowercase the focus brief and scan it for substring matches against the loaded directive filenames (both plugin defaults at `${CLAUDE_PLUGIN_ROOT}/directives/*.md` and the user's directives at `<project-root>/<directives.user_path>/*.md` if present). Strip the `.md` extension before matching, but match against the *full base name* — so `"scope"` matches `scope-discipline.md`, `"simplicity"` matches `simplicity.md`, and `"copy-paste"` would match a user directive named `copy-paste.md` if present (it doesn't match the shipped `reusability.md` — the matcher is a literal substring check, not a synonym mapper, per spec §8).

Record the matched directive paths. They will be flagged as **primary** in agent dispatch prompts under the heading "Directives most relevant to this run" so agents weight them first. The matched-directive flagging carries through review → plan → fix without re-computing.

If the focus brief is empty, no directives are flagged primary; all directives still load normally.

## Step 3: Run review

Run the `/comb:review` workflow with these overrides:

- All agents use `models.the_desert`
- Save the report to `paths.reviews` per the standard naming
- **Do NOT present the report and wait** — log the verdict and finding count, then immediately continue

When review finishes, announce:

```
[review] Done — {verdict}, {N} findings ({breakdown by severity})
Moving to plan →
```

## Step 4: Run plan

Run the `/comb:plan` workflow with these overrides:

- All agents use `models.the_desert`
- **Include every finding** — Critical, High, Medium, Low, Test gaps, AND Deferred. Nothing is skipped.
- **Make grouping decisions yourself** — if items touch the same file with small scope, group them. Don't ask.
- Save instruction files to `paths.plans` per the standard structure

When plan finishes, announce:

```
[plan] Done — {N} instruction files created
Moving to fix →
```

## Step 5: Run fix

Run the `/comb:fix` workflow with these overrides:

- All implementers use `models.the_desert` — including trivial items (no sonnet downgrade)
- All reviewers use `models.the_desert`
- **Per-item commits per `fix.commit_per_item` (default `true`) apply during the desert sweep.** The `models.the_desert` coercion governs subagent models; commit behavior is unaffected.
- **Execute every item** — nothing is deferred or excluded
- **Every item gets a reviewer** — no "trivial — skipped review". The reviewer is `agents.test-auditor.subagent_type` (default `comb:test-auditor`), per spec §5.3, with model coerced to `models.the_desert` unless an explicit `agents.test-auditor.model` user override is set.
- **Make grouping decisions yourself** — combine same-file trivial items without asking
- Execution order: Critical → High → Medium → Low → Test gaps → Deferred (now treated as regular items) → Discovered
- Run parallel batches where safe (different writes), sequential otherwise — launch parallel batches by issuing multiple Task tool calls in a single assistant message (do not use `run_in_background: true`; that is a Bash-tool parameter and has no effect on the Task tool).

Track progress as normal. When all items complete, present the full summary.

## Focus brief flow

The focus brief from `$ARGUMENTS` flows through review → plan → fix without re-asking. Every dispatch in every step gets it under `## User focus for this run`.

## After completion

```
[the-desert] Complete

Review: {verdict}, {N} findings
Plan: {N} instruction files
Fix: {N}/{N} items complete, {K} discovered during execution

All items:
  - C1: PASS
  - H1: PASS
  - ...

Want to run the sequence again? A fresh review will check if the fixes introduced new issues.
```

Wait for the user's response. If yes, start again from review with the same scope. The new review naturally detects whether prior fixes introduced regressions or new issues.

## Ground rules

- **No confirmation prompts.** Don't ask "should I continue?" between steps. Don't ask about groupings or ordering. Decide and move.
- **Nothing is deferred.** Every finding from review gets planned and fixed. "Deferred" is not a valid category in this mode.
- **`models.the_desert` for lane defaults.** Explicit per-agent overrides survive (spec §7.6).
- **Only questions:** scope at the start (if ambiguous), the dirty-tree pre-flight question (only when the tree is non-empty per `git status --porcelain`), and "run again?" at the end. Clean tree at start → no pre-flight question, preserving the no-pause contract.
- **All `/comb:review`, `/comb:plan`, `/comb:fix` rules still apply** — read source, fresh agents per item, scope boundaries, 3-failure escalation, parallel when safe. This skill overrides only transitions, model coercion, deferral policy, and confirmation policy.

## Edge case: focus brief contradicts shipped behavior

Same handling as `/comb:review`: surface and ask once before proceeding.
