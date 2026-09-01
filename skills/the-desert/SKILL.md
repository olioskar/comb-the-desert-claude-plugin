---
name: the-desert
description: Use when the user wants the full comb pipeline — review → plan → fix — run as one continuous sweep. The user must invoke this explicitly — it executes code changes.
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

Load the merged config per `${CLAUDE_PLUGIN_ROOT}/shared/config-loading.md`. The relevant override:

- `models.the_desert` (default `opus`) overrides every lane default in this run
- **Exception:** explicit `agents.<role>.model` user overrides survive `the-desert` coercion. Only lane defaults are coerced.

## Step 2: Surface relevant directives

Apply the focus-brief matcher in `${CLAUDE_PLUGIN_ROOT}/shared/directive-matching.md`. It records the matched directive paths and flags them as **primary** in agent dispatch prompts under "Directives most relevant to this run"; an empty focus brief flags nothing, and all directives still load normally. The matched-directive flagging carries through review → plan → fix without re-computing.

## Step 3: Run review

Read `${CLAUDE_PLUGIN_ROOT}/skills/review/SKILL.md` and execute that workflow with these overrides. Where the texts conflict, these overrides win. Do not invoke the Skill tool for the sub-command — loading it as a skill would inject its wait-and-present instructions.

Overrides:

- All agents use `models.the_desert`
- Save the report to `paths.reviews` per the standard naming
- **Do NOT present the report and wait** — log the verdict and finding count, then immediately continue

When review finishes, announce one of:

**If review classified the artifact as code-shaped:**

```
[review] Done — {verdict}, {N} findings ({breakdown by severity})
Moving to plan →
```

**If review classified the artifact as non-code:**

```
[review] Done — {N} findings on non-code artifact ({breakdown by label}).
Stopping here — non-code findings belong back in your design conversation, not an autonomous fix pass.
Report: {path}
```

## Step 3.5: Decide whether to continue

Inspect the review's classification (Step 3.5 in `/comb:review`). If **non-code**, stop the-desert here — do not run plan or fix. The review report is the final deliverable for this sweep; the user integrates the findings into their next round of the design conversation. Skip directly to the "After completion" block, omitting the plan/fix summary lines (replace them with `Plan: skipped — non-code artifact` and `Fix: skipped — non-code artifact`).

If **code-shaped**, proceed to Step 4 below as today.

## Step 4: Run plan

Read `${CLAUDE_PLUGIN_ROOT}/skills/plan/SKILL.md` and execute that workflow with these overrides (same mechanism as Step 3 — read the file, do not invoke the Skill tool):

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

Read `${CLAUDE_PLUGIN_ROOT}/skills/fix/SKILL.md` and execute that workflow with these overrides (same mechanism as Step 3 — read the file, do not invoke the Skill tool):

- All implementers use `models.the_desert` — including trivial items (no sonnet downgrade)
- All reviewers use `models.the_desert`
- **Per-item commits per `fix.commit_per_item` (default `true`) apply during the desert sweep.** The `models.the_desert` coercion governs subagent models; commit behavior is unaffected.
- **Execute every item** — nothing is deferred or excluded
- **Every item gets a reviewer** — no "trivial — skipped review". The reviewer role follows `/comb:fix` Step 4e: it is picked from the plan file's `**Specialty:**` header, with model coerced to `models.the_desert` unless an explicit `agents.<role>.model` user override is set.
- **Make grouping decisions yourself** — combine same-file trivial items without asking
- Execution order: Critical → High → Medium → Low → Test gaps → Deferred (now treated as regular items) → Discovered
- Run parallel batches where safe (different writes), sequential otherwise — launch parallel batches per the delivery contract, one Task call per item in a single assistant message.

Track progress as normal. When all items complete, present the full summary.

## Focus brief flow

The focus brief from `$ARGUMENTS` flows through review → plan → fix without re-asking. Every dispatch in every step gets it under `## User focus for this run`.

## After completion

**For code-shaped runs:**

```
[the-desert] Complete

Review: {verdict}, {N} findings
Plan: {N} instruction files
Fix: {N}/{N} items complete, {K} discovered during execution

All items:
  - C1: PASS
  - H1: PASS
  - ...
```

**For code-shaped runs only — Want to run the sequence again?**

Make the recommendation explicit in the prompt — quote the actual severity counts from this round, then state the recommendation. The user still decides; the orchestrator just gives an honest read so they can stop confidently when the round was clean.

Recommendation based on this round's findings:
- Critical / High findings present → yes, run again. The fixes likely warrant a follow-up sweep to verify no regressions.
- Only Medium / Low / Test gaps → judgment call. Run again if a specific Medium might cascade; otherwise the remaining items are usually better handled by a focused human pass than by another full sweep.
- Round was clean (zero findings or only marginal Low items) → stop. Further rounds yield diminishing returns and risk over-correction.

A fresh review will check whether the fixes introduced new issues; it will also surface any Low findings that were below the round-1 threshold.

Wait for the user's response. If yes, start again from review with the same scope. The new review naturally detects whether prior fixes introduced regressions or new issues.

**For non-code short-circuit:**

```
[the-desert] Complete (review-only — non-code artifact)

Review: {N} findings ({breakdown by label})
Plan: skipped — non-code artifact
Fix: skipped — non-code artifact

Report: {path}

The findings are intended to feed your next round of design conversation, not an autonomous rewrite. Skipping the "run again?" prompt — running another sweep on the same spec without changes will produce the same findings.
```

## Ground rules

- **No confirmation prompts.** Don't ask "should I continue?" between steps. Don't ask about groupings or ordering. Decide and move.
- **Nothing is deferred.** Every finding from review gets planned and fixed. "Deferred" is not a valid category in this mode.
- **`models.the_desert` for lane defaults.** Explicit per-agent overrides survive.
- **PATTERNS manifest is inherited, not regenerated.** the-desert inherits manifest loading, the "Project conventions (observed baseline)" dispatch block, and the manifest stance through review/plan/fix — it never runs `/comb:patterns`. Both the commit-based staleness note and the semantic refresh note are **printed log lines, never prompts**, so the no-pause contract holds. `models.the_desert` does **not** coerce `models.patterns` — the guarantee holds because the scanner is never dispatched during the sweep, not via any coercion-skip logic (a future maintainer wiring patterns into the-desert must add the exclusion explicitly).
- **The consolidation gate runs during the sweep.** `/comb:review` Step 7's verification gate asks the user nothing, so the no-pause contract holds. Do not strip it for speed.
- **Only questions:** scope at the start (if ambiguous), the dirty-tree pre-flight question (only when the tree is non-empty per `git status --porcelain`), and "run again?" at the end. Clean tree at start → no pre-flight question, preserving the no-pause contract.
- **All `/comb:review`, `/comb:plan`, `/comb:fix` rules still apply** — read source, fresh agents per item, scope boundaries, 3-failure escalation, parallel when safe. This skill overrides only transitions, model coercion, deferral policy, and confirmation policy.

## Edge case: focus brief contradicts shipped behavior

Same handling as `/comb:review`: surface and ask once before proceeding.
