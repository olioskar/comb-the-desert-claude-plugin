---
name: help
description: Show the comb plugin overview and command list. Use when the user types `/comb:help`, asks "what is comb", "what does comb do", "comb commands", "how do I use comb", or wants a refresher on the plugin. Pass a command name (e.g., `/comb:help fix`) for a deeper look at one command.
argument-hint: "[command-name]"
allowed-tools:
  - Read
user-invocable: true
disable-model-invocation: false
---

You print help for the comb plugin.

## Behavior

- If `$ARGUMENTS` is empty: print the **Overview** below verbatim.
- If `$ARGUMENTS` names a command (`review`, `plan`, `fix`, `the-desert`, `configure`, `help`): print the matching **Per-command** entry verbatim.
- If `$ARGUMENTS` is anything else: print the Overview and add a one-line note: `Note: "{argument}" isn't a comb command. Try one of: review, plan, fix, the-desert, configure.`

Don't paraphrase. The user is asking for the help text — give them the help text.

---

## Overview

```
comb-the-desert — code-review pipeline for Claude Code

A review → plan → fix workflow with configurable reviewer agents and
authoritative project directives.

Commands

  /comb:review       Dispatch 1–5 reviewer agents over a PR, branch, file
                     list, or a spec/design doc. The orchestrator reads the
                     work first and right-sizes the apparatus: code-shaped
                     diffs get the full report (verdict, severity scale,
                     verification); non-code artifacts get a condensed
                     report (flat findings, no verdict). Read-only.

  /comb:plan         Turn each review finding into a self-contained fix
                     instruction file. Read-only.

  /comb:fix          Execute fix instructions: implementer + reviewer
                     per item, parallel batching where safe.

  /comb:the-desert   Run review → plan → fix as one continuous sweep.
                     Opus everywhere. No pauses, no items skipped. On
                     non-code artifacts, stops after review — findings go
                     back into your design conversation, not an autonomous
                     rewrite pass.

  /comb:configure    Edit comb.config.json conversationally — paths,
                     models, enable/disable agents.

  /comb:help         This message. Pass a command name for details.

Focus brief

  Every command accepts free text after the slash. The brief biases
  agent picking and finding priority:

    /comb:review look for spec/plan misalignment
    /comb:the-desert ensure simplicity, scope discipline, TDD coverage

Common workflows

  Iterative:    /comb:review → review the report → /comb:plan →
                approve groupings → /comb:fix
  Full sweep:   /comb:the-desert  (review + plan + fix in one pass)

Config

  Layered, deep-merged in this order (later wins):
    1. plugin defaults  (${CLAUDE_PLUGIN_ROOT}/config/defaults.json)
    2. global override  (~/.claude/comb.config.json)
    3. project override (<project-root>/.claude/comb.config.json)

  Edit interactively: /comb:configure
  Or hand-edit the JSON files above.

For more on a command:  /comb:help <command-name>
```

---

## Per-command

### review

```
/comb:review [scope] [focus brief]

Step 1 of the review → plan → fix workflow.

Inputs
  scope         A PR number, branch name, or explicit file list.
                Defaults to the current branch diffed against
                paths.base_branch (default: main).
  focus brief   Optional free text — biases agent picking and finding
                priority.

What it does
  - Picks 2–5 reviewer agents based on the diff and the focus brief.
  - Dispatches them in parallel against the project's directives.
  - Runs typecheck/tests in parallel.
  - Consolidates findings into a severity-ranked report.

Output
  <paths.reviews>/{pr-N|branch-NAME}-roundN-report.md

Examples
  /comb:review
  /comb:review 774
  /comb:review staging look for spec/plan misalignment
```

### plan

```
/comb:plan [report-path] [focus brief]

Step 2 of the review → plan → fix workflow.

Inputs
  report-path   Path to a review report. Defaults to the most recent
                report in <paths.reviews>.
  focus brief   Optional free text — passed through from /comb:the-desert.

What it does
  - Parses every finding (including Deferred).
  - Suggests groupings for related findings; you decide.
  - Dispatches one planner agent per finding (or group) in parallel.
  - Each agent reads the actual code and writes a self-contained fix
    instruction file.

Output
  <paths.plans>/plan-for-<report-stem>/<code>-<title-slug>.md
  one file per finding (or group)
```

### fix

```
/comb:fix [plan-folder] [focus brief]

Step 3 of the review → plan → fix workflow.

Inputs
  plan-folder   Path to a plan folder produced by /comb:plan.
                Defaults to the most recent plan folder.
  focus brief   Optional free text.

What it does
  - Pre-flight: checks the working tree. If dirty, asks once whether
    to commit existing changes, stash and restore, proceed without
    per-item commits, or abort.
  - Executes each fix instruction with implementer + reviewer per item.
  - Implementer is agents.implementer (default general-purpose).
  - Reviewer specialty is matched to the plan's **Specialty:** header
    (was always test-auditor in v0.4.x).
  - Reviewer evaluates plan-compliance: did the implementer execute the
    plan, and are reported divergences justified?
  - Parallel batching where safe; sequential where instructions overlap
    in scope.
  - Per-item commit on PASS, with the finding code + title in the
    message. Opt out via fix.commit_per_item: false.

Trivial-only escape hatch
  - After 3 implementer failures on a trivial item, the orchestrator
    may apply the fix inline. The reviewer still runs. Standard items
    that hit 3 failures escalate to the user.

Models
  Trivial fixes:    models.fix.implementer_trivial   (default: sonnet)
  Standard fixes:   models.fix.implementer_standard  (default: opus)
  Reviewer:         models.fix.reviewer              (default: opus)

Config knobs
  fix.commit_per_item    (default: true)  per-item commit on PASS
  agents.implementer     (default: general-purpose)  the writer agent
```

### the-desert

```
/comb:the-desert [scope] [focus brief]

Run review → plan → fix as one continuous sweep, opus everywhere,
no pauses.

Inputs
  scope         Same as /comb:review.
  focus brief   Optional free text.

When to use
  - High-stakes branches where you want everything done in one pass.
  - When you trust the focus brief to do the steering.

When not to use
  - When you want a checkpoint between review and plan.
  - When you want to hand-pick which findings get instructions.
```

### configure

```
/comb:configure [scope] [change]

Edit comb.config.json conversationally.

Inputs
  scope    "project" or "global". project edits
           <project-root>/.claude/comb.config.json; global edits
           ~/.claude/comb.config.json. The shipped defaults at
           ${CLAUDE_PLUGIN_ROOT}/config/defaults.json are not editable.
  change   What you want different. Examples:
             "disable test-auditor"
             "use sonnet for plan"
             "change reviews dir to docs/reviews"
             "look for my directives in docs/our-rules"

What it does
  - Shows the merged effective config (so you see what's coming from
    where).
  - Translates the change into a JSON patch.
  - Shows a diff.
  - Writes after you confirm.
  - Verifies the result parses and the schema is sane.
```

### help

```
/comb:help [command-name]

This command. With no argument, prints the overview. With a command
name, prints the deep-dive for that command.
```
